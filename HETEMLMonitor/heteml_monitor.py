#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HETEMLサーバ監視システム
HETEMLサーバ内の指定フォルダに新しいファイルが追加された際に通知を送信します。
"""

import os
import sys
import time
import json
import logging
import hashlib
import schedule
from datetime import datetime
from typing import Dict, List, Set, Optional
import paramiko
from pathlib import Path

# 設定ファイルのインポート
try:
    from config import (
        HETEML_CONFIG, 
        MONITOR_CONFIG, 
        NOTIFICATION_CONFIG, 
        LOG_CONFIG, 
        DB_CONFIG
    )
except ImportError:
    print("設定ファイルが見つかりません。config.example.pyをconfig.pyにコピーして編集してください。")
    sys.exit(1)

# 通知モジュールのインポート
from notifications import NotificationManager

class HETEMLMonitor:
    """HETEMLサーバ監視クラス"""
    
    def __init__(self):
        """初期化"""
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.ssh_client = None
        self.sftp_client = None
        self.known_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}
        self.notification_manager = NotificationManager()
        self.history_file = DB_CONFIG.get('file', 'file_history.json')
        
        # 既存のファイル履歴を読み込み
        self.load_file_history()
        
    def setup_logging(self):
        """ログ設定"""
        log_config = LOG_CONFIG
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config['file'], encoding='utf-8'),
                logging.StreamHandler()
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
            
            self.logger.info(f"HETEMLサーバに接続しました: {config['hostname']}")
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
    
    def get_file_list(self) -> List[Dict]:
        """監視対象フォルダのファイル一覧を取得"""
        try:
            target_path = MONITOR_CONFIG['target_path']
            file_pattern = MONITOR_CONFIG['file_pattern']
            exclude_patterns = MONITOR_CONFIG['exclude_patterns']
            
            # SFTPでファイル一覧を取得
            files = []
            for item in self.sftp_client.listdir_attr(target_path):
                filename = item.filename
                
                # 除外パターンのチェック
                if any(self._matches_pattern(filename, pattern) for pattern in exclude_patterns):
                    continue
                
                # ファイルパターンのチェック
                if not self._matches_pattern(filename, file_pattern):
                    continue
                
                file_info = {
                    'name': filename,
                    'size': item.st_size,
                    'mtime': item.st_mtime,
                    'path': f"{target_path}/{filename}"
                }
                files.append(file_info)
            
            self.logger.debug(f"ファイル一覧を取得しました: {len(files)}ファイル")
            return files
            
        except Exception as e:
            self.logger.error(f"ファイル一覧の取得に失敗: {e}")
            return []
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """ファイル名がパターンにマッチするかチェック"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def get_file_hash(self, file_path: str) -> str:
        """ファイルのハッシュ値を取得"""
        try:
            # SFTPでファイルを一時的にダウンロードしてハッシュ計算
            with self.sftp_client.open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            self.logger.error(f"ファイルハッシュの取得に失敗 {file_path}: {e}")
            return ""
    
    def check_new_files(self) -> List[Dict]:
        """新規ファイルをチェック"""
        current_files = self.get_file_list()
        new_files = []
        
        for file_info in current_files:
            filename = file_info['name']
            file_path = file_info['path']
            
            if filename not in self.known_files:
                # 新規ファイルを発見
                file_hash = self.get_file_hash(file_path)
                file_info['hash'] = file_hash
                new_files.append(file_info)
                
                self.known_files.add(filename)
                self.file_hashes[filename] = file_hash
                
                self.logger.info(f"新規ファイルを発見: {filename}")
        
        return new_files
    
    def send_notifications(self, new_files: List[Dict]):
        """通知の送信"""
        if not new_files:
            return
        
        # 通知メッセージの作成
        message = self._create_notification_message(new_files)
        
        # 各通知方法で送信
        for method in NOTIFICATION_CONFIG.get('methods', []):
            try:
                if method == 'email':
                    self.notification_manager.send_email(message)
                elif method == 'slack':
                    self.notification_manager.send_slack(message)
                elif method == 'line':
                    self.notification_manager.send_line(message)
                    
            except Exception as e:
                self.logger.error(f"{method}通知の送信に失敗: {e}")
    
    def _create_notification_message(self, new_files: List[Dict]) -> str:
        """通知メッセージの作成"""
        message = f"🔔 HETEMLサーバで新規ファイルを発見しました\n\n"
        message += f"監視対象: {MONITOR_CONFIG['target_path']}\n"
        message += f"発見時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for i, file_info in enumerate(new_files, 1):
            message += f"{i}. {file_info['name']}\n"
            message += f"   サイズ: {file_info['size']:,} bytes\n"
            message += f"   更新日時: {datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return message
    
    def monitor_once(self):
        """1回の監視実行"""
        try:
            if not self.connect_ssh():
                return
            
            new_files = self.check_new_files()
            
            if new_files:
                self.send_notifications(new_files)
                self.save_file_history()
            
        except Exception as e:
            self.logger.error(f"監視実行中にエラーが発生: {e}")
        finally:
            self.disconnect_ssh()
    
    def start_monitoring(self):
        """監視の開始"""
        interval = MONITOR_CONFIG['check_interval']
        self.logger.info(f"HETEMLサーバ監視を開始します (間隔: {interval}秒)")
        
        # 初回実行
        self.monitor_once()
        
        # 定期実行のスケジュール設定
        schedule.every(interval).seconds.do(self.monitor_once)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("監視を停止します")
            self.save_file_history()

def main():
    """メイン関数"""
    monitor = HETEMLMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
