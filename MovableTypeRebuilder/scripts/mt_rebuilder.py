#!/usr/bin/env python3
"""
MovableType Rebuilder
MovableTypeウェブサイトの月次再構築を自動化するツール
"""

import os
import sys
import time
import logging
import argparse
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

# 設定ファイルのインポート
try:
    # スクリプトディレクトリから親ディレクトリのconfig.pyを読み込む
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import MT_CONFIG, NOTIFICATION_CONFIG, LOG_CONFIG, EXECUTION_CONFIG
    from notifications import NotificationManager
except ImportError:
    print("設定ファイルが見つかりません。config.pyを確認してください。")
    sys.exit(1)

# ログ設定
def setup_logging():
    """ログ設定を初期化"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"mt_rebuilder_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

class MovableTypeRebuilder:
    """MovableType再構築クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logging()
        
        # 設定読み込み
        self.mt_url = MT_CONFIG['site_url']
        self.mt_username = MT_CONFIG['username']
        self.mt_password = MT_CONFIG['password']
        self.mt_blog_id = MT_CONFIG['blog_id']
        self.mt_site_name = MT_CONFIG['site_name']
        
        # 実行設定
        self.rebuild_interval = EXECUTION_CONFIG['rebuild_interval_minutes']
        self.max_retry = EXECUTION_CONFIG['max_retry_count']
        
        # 初期化チェック
        self._validate_config()
        
        # クライアント初期化
        self.session = requests.Session()
        self.notification_manager = NotificationManager()
        
    def _validate_config(self):
        """設定の妥当性をチェック"""
        required_configs = ['site_url', 'username', 'password', 'blog_id']
        missing_configs = [config for config in required_configs if not MT_CONFIG.get(config)]
        
        if missing_configs:
            raise ValueError(f"必要な設定が不足しています: {', '.join(missing_configs)}")
        
        # blog_idが数値であることを確認
        try:
            int(self.mt_blog_id)
        except ValueError:
            raise ValueError(f"blog_idは数値である必要があります: {self.mt_blog_id}")
    
    def login_to_mt(self) -> bool:
        """MovableTypeにログイン"""
        try:
            self.logger.info("MovableTypeにログイン中...")
            
            # ログインページにアクセスしてセッションを確立
            login_url = f"{self.mt_url}/mt.cgi"
            login_data = {
                'username': self.mt_username,
                'password': self.mt_password,
                '__mode': 'login'
            }
            
            response = self.session.post(login_url, data=login_data, timeout=30)
            response.raise_for_status()
            
            # ログイン成功の確認（より柔軟な判定）
            success_indicators = ['ログアウト', 'logout', 'dashboard', '管理画面', '完了']
            failure_indicators = ['ログイン', 'login', 'エラー', 'error', '失敗', '認証']
            
            success_count = sum(1 for indicator in success_indicators if indicator.lower() in response.text.lower())
            failure_count = sum(1 for indicator in failure_indicators if indicator.lower() in response.text.lower())
            
            # クッキーが設定されているかも確認
            has_cookies = len(self.session.cookies) > 0
            
            if success_count > failure_count or has_cookies:
                self.logger.info("ログイン成功")
                return True
            else:
                self.logger.error("ログイン失敗: 認証情報が正しくない可能性があります")
                return False
                
        except Exception as e:
            self.logger.error(f"ログインエラー: {e}")
            return False
    
    def trigger_rebuild(self) -> Dict[str, Any]:
        """サイト再構築を実行"""
        try:
            self.logger.info("サイト再構築を開始...")
            
            # 再構築URL
            rebuild_url = f"{self.mt_url}/mt.cgi"
            rebuild_data = {
                '__mode': 'rebuild',
                'blog_id': self.mt_blog_id,  # 設定されたブログID
                'type': 'all'
            }
            
            # 再構築実行
            response = self.session.post(rebuild_url, data=rebuild_data, timeout=300)
            response.raise_for_status()
            
            # 結果の解析
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 成功メッセージの確認
            success_indicators = ['再構築が完了しました', 'rebuild completed', 'success']
            is_success = any(indicator in response.text for indicator in success_indicators)
            
            if is_success:
                self.logger.info(f"再構築成功: {self.mt_site_name} (blog_id: {self.mt_blog_id})")
                return {
                    'success': True,
                    'message': f'{self.mt_site_name} (blog_id: {self.mt_blog_id}) の再構築が正常に完了しました',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                self.logger.warning("再構築結果が不明: レスポンスを確認してください")
                return {
                    'success': False,
                    'message': '再構築結果が確認できませんでした',
                    'timestamp': datetime.now().isoformat(),
                    'response_text': response.text[:500]  # 最初の500文字のみ
                }
                
        except Exception as e:
            self.logger.error(f"再構築エラー: {e}")
            return {
                'success': False,
                'message': f'再構築中にエラーが発生しました: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def send_email_notification(self, result: Dict[str, Any]):
        """メール通知を送信"""
        try:
            status = "✅ 成功" if result['success'] else "❌ 失敗"
            subject = f"MovableType再構築結果 - {self.mt_site_name} - {status}"
            
            message = f"""
MovableType再構築結果

対象サイト: {self.mt_site_name} (blog_id: {self.mt_blog_id})
{status}
時刻: {result['timestamp']}
メッセージ: {result['message']}

---
MovableType再構築システム
            """.strip()
            
            self.notification_manager.send_email(message, subject)
            self.logger.info("メール通知を送信しました")
            
        except Exception as e:
            self.logger.error(f"メール通知エラー: {e}")
    
    def execute_rebuild(self) -> Dict[str, Any]:
        """再構築を実行（ログイン→再構築→通知）"""
        self.logger.info("=== MovableType再構築開始 ===")
        
        # ログイン
        if not self.login_to_mt():
            result = {
                'success': False,
                'message': 'MovableTypeへのログインに失敗しました',
                'timestamp': datetime.now().isoformat()
            }
        else:
            # 再構築実行
            result = self.trigger_rebuild()
        
        # 通知送信
        self.send_email_notification(result)
        
        self.logger.info("=== MovableType再構築完了 ===")
        return result
    
    def run_scheduled_rebuild(self):
        """スケジュール実行"""
        self.logger.info("スケジュール実行を開始")
        
        # 毎月1日の0:01に実行
        schedule.every().month.at("00:01").do(self.execute_rebuild)
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック
    
    def run_test(self):
        """テスト実行"""
        self.logger.info("テスト実行を開始")
        result = self.execute_rebuild()
        self.logger.info(f"テスト結果: {result}")
        return result

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='MovableType再構築ツール')
    parser.add_argument('--test', action='store_true', help='テスト実行')
    parser.add_argument('--schedule', action='store_true', help='スケジュール実行')
    args = parser.parse_args()
    
    try:
        rebuilder = MovableTypeRebuilder()
        
        if args.test:
            rebuilder.run_test()
        elif args.schedule:
            rebuilder.run_scheduled_rebuild()
        else:
            # 通常実行
            rebuilder.execute_rebuild()
            
    except Exception as e:
        logging.error(f"実行エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
