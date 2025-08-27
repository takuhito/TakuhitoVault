#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HETEMLサーバ監視システム - GitHub Action版
HETEMLサーバ内の指定フォルダに新しいファイルが追加された際に通知を送信します。
GitHub Actions環境に最適化されています。
"""

import os
import sys
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Set, Optional
import paramiko
from pathlib import Path

# 設定ファイルのインポート
try:
    print("📁 設定ファイルを読み込み中...")
    from config import (
        HETEML_CONFIG, 
        MONITOR_CONFIG, 
        NOTIFICATION_CONFIG, 
        LOG_CONFIG, 
        DB_CONFIG
    )
    print("✅ 設定ファイルの読み込みに成功しました")
except ImportError as e:
    print(f"❌ 設定ファイルの読み込みに失敗: {e}")
    print("config.example.pyをconfig.pyにコピーして編集してください。")
    sys.exit(1)
except Exception as e:
    print(f"❌ 設定ファイルで予期しないエラー: {e}")
    sys.exit(1)

# 通知モジュールのインポート
from notifications import NotificationManager

class HETEMLMonitorGitHubAction:
    """HETEMLサーバ監視クラス - GitHub Action版"""
    
    def __init__(self):
        """初期化"""
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.ssh_client = None
        self.sftp_client = None
        self.known_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}
        self.notification_manager = NotificationManager()
        
        # GitHub Actions環境でのファイル履歴保存場所
        self.history_file = os.path.join(
            os.environ.get('GITHUB_WORKSPACE', '.'),
            'HETEMLMonitor',
            'file_history.json'
        )
        
        # 既存のファイル履歴を読み込み
        self.load_file_history()
        
    def setup_logging(self):
        """ログ設定 - GitHub Actions環境用"""
        log_config = LOG_CONFIG
        
        # GitHub Actions環境では標準出力にログを出力
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    def load_file_history(self):
        """ファイル履歴の読み込み"""
        if DB_CONFIG.get('enabled', False) and os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.known_files = set(data.get('files', []))
                    self.file_hashes = data.get('hashes', {})
                self.logger.info(f"ファイル履歴を読み込みました: {len(self.known_files)}ファイル")
            except Exception as e:
                self.logger.error(f"ファイル履歴の読み込みに失敗: {e}")
                
    def save_file_history(self):
        """ファイル履歴の保存"""
        if DB_CONFIG.get('enabled', False):
            try:
                # ディレクトリが存在しない場合は作成
                os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
                
                data = {
                    'files': list(self.known_files),
                    'hashes': self.file_hashes,
                    'last_updated': datetime.now().isoformat()
                }
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.logger.debug("ファイル履歴を保存しました")
            except Exception as e:
                self.logger.error(f"ファイル履歴の保存に失敗: {e}")
    
    def connect_ssh(self) -> bool:
        """SSH接続の確立"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 接続設定
            config = HETEML_CONFIG
            connect_kwargs = {
                'hostname': config['hostname'],
                'port': config['port'],
                'username': config['username'],
                'timeout': config['timeout']
            }
            
            # パスワードまたは秘密鍵で認証
            if config.get('password'):
                connect_kwargs['password'] = config['password']
            elif config.get('key_filename'):
                connect_kwargs['key_filename'] = config['key_filename']
            
            self.ssh_client.connect(**connect_kwargs)
            self.sftp_client = self.ssh_client.open_sftp()
            
            self.logger.info("SSH接続が確立されました")
            return True
            
        except Exception as e:
            self.logger.error(f"SSH接続に失敗: {e}")
            return False
    
    def disconnect_ssh(self):
        """SSH接続の切断"""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()
        self.logger.debug("SSH接続を切断しました")
    
    def get_file_hash(self, file_path: str) -> str:
        """ファイルのハッシュ値を取得"""
        try:
            with self.sftp_client.open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            self.logger.error(f"ファイルハッシュの取得に失敗 {file_path}: {e}")
            return ""
    
    def list_files(self) -> List[str]:
        """監視対象フォルダ内のファイル一覧を取得"""
        try:
            target_path = MONITOR_CONFIG['target_path']
            file_pattern = MONITOR_CONFIG['file_pattern']
            exclude_patterns = MONITOR_CONFIG.get('exclude_patterns', [])
            
            # SFTPでファイル一覧を取得
            files = []
            for item in self.sftp_client.listdir_attr(target_path):
                if item.filename.startswith('.'):
                    continue
                    
                # 除外パターンのチェック
                if any(pattern in item.filename for pattern in exclude_patterns):
                    continue
                
                file_path = os.path.join(target_path, item.filename)
                if self.sftp_client.stat(file_path).st_mode & 0o40000:  # ディレクトリ
                    continue
                    
                files.append(file_path)
            
            return files
            
        except Exception as e:
            self.logger.error(f"ファイル一覧の取得に失敗: {e}")
            return []
    
    def check_new_files(self) -> List[str]:
        """新しいファイルをチェック"""
        current_files = set(self.list_files())
        new_files = []
        
        for file_path in current_files:
            if file_path not in self.known_files:
                # 新しいファイルを発見
                new_files.append(file_path)
                self.known_files.add(file_path)
                
                # ハッシュ値を保存
                file_hash = self.get_file_hash(file_path)
                if file_hash:
                    self.file_hashes[file_path] = file_hash
                    
                self.logger.info(f"新しいファイルを発見: {file_path}")
        
        return new_files
    
    def check_modified_files(self) -> List[str]:
        """変更されたファイルをチェック"""
        modified_files = []
        
        for file_path in self.known_files:
            if not self.sftp_client.exists(file_path):
                # ファイルが削除された
                self.known_files.discard(file_path)
                self.file_hashes.pop(file_path, None)
                self.logger.info(f"ファイルが削除されました: {file_path}")
                continue
            
            # ハッシュ値を比較
            current_hash = self.get_file_hash(file_path)
            stored_hash = self.file_hashes.get(file_path, "")
            
            if current_hash and current_hash != stored_hash:
                modified_files.append(file_path)
                self.file_hashes[file_path] = current_hash
                self.logger.info(f"ファイルが変更されました: {file_path}")
        
        return modified_files
    
    def send_notifications(self, new_files: List[str], modified_files: List[str]):
        """通知を送信"""
        if not new_files and not modified_files:
            return
        
        # 通知メッセージの作成
        message_parts = []
        
        if new_files:
            message_parts.append("🆕 新しいファイル:")
            for file_path in new_files:
                filename = os.path.basename(file_path)
                message_parts.append(f"  • {filename}")
        
        if modified_files:
            message_parts.append("📝 変更されたファイル:")
            for file_path in modified_files:
                filename = os.path.basename(file_path)
                message_parts.append(f"  • {filename}")
        
        message = "\n".join(message_parts)
        
        # GitHub Actions版であることを明示するメッセージを追加
        github_message = f"[GitHub Actions版] {message}"
        
        # 各通知方法で送信
        success_count = 0
        
        # メール通知（GitHub版用のタイトル）
        if self.notification_manager.send_email_github_action(github_message):
            success_count += 1
        
        if self.notification_manager.send_line(github_message):
            success_count += 1
        
        if self.notification_manager.send_slack(github_message):
            success_count += 1
        
        if success_count > 0:
            self.logger.info(f"通知を送信しました（{success_count}件成功）")
        else:
            self.logger.warning("通知の送信に失敗しました")
    
    def run_monitoring(self):
        """監視を実行"""
        self.logger.info("HETEMLサーバ監視を開始します")
        
        # SSH接続
        if not self.connect_ssh():
            self.logger.error("SSH接続に失敗したため監視を終了します")
            return False
        
        try:
            # 新しいファイルと変更されたファイルをチェック
            new_files = self.check_new_files()
            modified_files = self.check_modified_files()
            
            # 通知を送信
            if new_files or modified_files:
                self.send_notifications(new_files, modified_files)
            else:
                self.logger.info("新しいファイルや変更はありませんでした")
            
            # ファイル履歴を保存
            self.save_file_history()
            
            return True
            
        except Exception as e:
            self.logger.error(f"監視中にエラーが発生: {e}")
            return False
        
        finally:
            self.disconnect_ssh()

def main():
    """メイン関数"""
    try:
        print("🚀 HETEMLMonitor GitHub Action版を開始します...")
        print(f"現在のディレクトリ: {os.getcwd()}")
        print(f"Pythonバージョン: {sys.version}")
        
        # 環境変数の確認（機密情報は除く）
        env_vars = ['HETEML_PASSWORD', 'EMAIL_USERNAME', 'EMAIL_PASSWORD', 'FROM_EMAIL', 'TO_EMAIL']
        for var in env_vars:
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: 設定済み")
            else:
                print(f"❌ {var}: 未設定")
        
        monitor = HETEMLMonitorGitHubAction()
        success = monitor.run_monitoring()
        
        if success:
            print("✅ HETEML監視が正常に完了しました")
            sys.exit(0)
        else:
            print("❌ HETEML監視でエラーが発生しました")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
