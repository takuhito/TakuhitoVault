#!/usr/bin/env python3
"""
MovableType再構築システム - GitHub Actions版
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

# 設定ファイルのインポート
try:
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

class MovableTypeRebuilderGitHubAction:
    """MovableType再構築クラス - GitHub Actions版"""
    
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
        self.session = None
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
            import requests
            self.session = requests.Session()
            
            # User-Agentヘッダーを設定
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            self.logger.info("MovableTypeにログイン中...")
            self.logger.info(f"ログインURL: {self.mt_url}")
            self.logger.info(f"ユーザー名: {self.mt_username}")
            self.logger.info(f"パスワード: {'***' if self.mt_password else '未設定'}")
            
            # まずログインページにGETでアクセスしてセッションを確立
            login_page_url = self.mt_url
            self.logger.info(f"ログインページにアクセス: {login_page_url}")
            
            response = self.session.get(login_page_url, timeout=30)
            response.raise_for_status()
            
            # ログインフォームをPOSTで送信
            login_url = self.mt_url
            login_data = {
                'username': self.mt_username,
                'password': self.mt_password,
                '__mode': 'login'
            }
            
            self.logger.info(f"ログインデータ送信: {login_url}")
            response = self.session.post(login_url, data=login_data, timeout=30)
            response.raise_for_status()
            
            # デバッグ情報をログに出力
            self.logger.info(f"レスポンスステータス: {response.status_code}")
            self.logger.info(f"クッキー数: {len(self.session.cookies)}")
            self.logger.info(f"レスポンスサイズ: {len(response.text)} bytes")
            
            # レスポンスの一部をログに出力（デバッグ用）
            response_preview = response.text[:500]
            self.logger.info(f"レスポンスプレビュー: {response_preview}")
            
            # ログイン成功の確認（より柔軟な判定）
            success_indicators = ['ログアウト', 'logout', 'dashboard', '管理画面', '完了']
            failure_indicators = ['ログイン', 'login', 'エラー', 'error', '失敗', '認証']
            
            success_count = sum(1 for indicator in success_indicators if indicator.lower() in response.text.lower())
            failure_count = sum(1 for indicator in failure_indicators if indicator.lower() in response.text.lower())
            
            # クッキーが設定されているかも確認
            has_cookies = len(self.session.cookies) > 0
            
            self.logger.info(f"成功指標: {success_count}, 失敗指標: {failure_count}, クッキー: {has_cookies}")
            
            if success_count > failure_count or has_cookies:
                self.logger.info("ログイン成功")
                return True
            else:
                self.logger.error("ログイン失敗: 認証情報が正しくない可能性があります")
                self.logger.error(f"詳細: 成功指標={success_count}, 失敗指標={failure_count}, クッキー={has_cookies}")
                return False
                
        except Exception as e:
            self.logger.error(f"ログインエラー: {e}")
            return False
    
    def trigger_rebuild(self) -> Dict[str, Any]:
        """サイト再構築を実行"""
        try:
            from bs4 import BeautifulSoup
            
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
        """メール通知を送信（GitHub Actions版）"""
        try:
            status = "✅ 成功" if result['success'] else "❌ 失敗"
            subject = f"[GitHub Actions] MovableType再構築結果 - {self.mt_site_name} - {status}"
            
            message = f"""
[GitHub Actions] MovableType再構築結果

対象サイト: {self.mt_site_name} (blog_id: {self.mt_blog_id})
{status}
時刻: {result['timestamp']}
メッセージ: {result['message']}

---
MovableType再構築システム (GitHub Actions版)
            """.strip()
            
            self.notification_manager.send_email_github_action(message, subject)
            self.logger.info("GitHub Actions版メール通知を送信しました")
            
        except Exception as e:
            self.logger.error(f"メール通知エラー: {e}")
    
    def execute_rebuild(self) -> Dict[str, Any]:
        """再構築を実行（ログイン→再構築→通知）"""
        self.logger.info("=== MovableType再構築開始 (GitHub Actions版) ===")
        
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
        
        self.logger.info("=== MovableType再構築完了 (GitHub Actions版) ===")
        return result

def main():
    """メイン関数"""
    try:
        rebuilder = MovableTypeRebuilderGitHubAction()
        result = rebuilder.execute_rebuild()
        
        if result['success']:
            print("✅ MovableType再構築が成功しました")
            sys.exit(0)
        else:
            print("❌ MovableType再構築が失敗しました")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
