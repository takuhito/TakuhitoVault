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
        """監視対象フォルダのファイル一覧を取得（再帰的）"""
        try:
            target_path = MONITOR_CONFIG['target_path']
            file_pattern = MONITOR_CONFIG['file_pattern']
            exclude_patterns = MONITOR_CONFIG['exclude_patterns']
            
            # SFTPでファイル一覧を再帰的に取得
            files = []
            self._scan_directory_recursive(target_path, files, file_pattern, exclude_patterns)
            
            self.logger.debug(f"ファイル一覧を取得しました: {len(files)}ファイル")
            return files
            
        except Exception as e:
            self.logger.error(f"ファイル一覧の取得に失敗: {e}")
            return []
    
    def _scan_directory_recursive(self, current_path: str, files: List[Dict], file_pattern: str, exclude_patterns: List[str]):
        """ディレクトリを再帰的にスキャン"""
        try:
            for item in self.sftp_client.listdir_attr(current_path):
                filename = item.filename
                full_path = f"{current_path}/{filename}"
                
                # 除外パターンのチェック
                if any(self._matches_pattern(filename, pattern) for pattern in exclude_patterns):
                    continue
                
                # ディレクトリかどうかをチェック
                if item.st_mode & 0o40000:  # ディレクトリの場合
                    # サブディレクトリを再帰的にスキャン
                    self._scan_directory_recursive(full_path, files, file_pattern, exclude_patterns)
                else:
                    # ファイルの場合
                    # ファイルパターンのチェック
                    if not self._matches_pattern(filename, file_pattern):
                        continue
                    
                    file_info = {
                        'name': filename,
                        'size': item.st_size,
                        'mtime': item.st_mtime,
                        'path': full_path
                    }
                    files.append(file_info)
                    
        except Exception as e:
            self.logger.warning(f"ディレクトリスキャンエラー {current_path}: {e}")
    
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
    
    def check_file_changes(self) -> Dict[str, List[Dict]]:
        """ファイルの変更をチェック（新規・削除・変更）"""
        current_files = self.get_file_list()
        current_file_paths = {file_info['path'] for file_info in current_files}
        
        new_files = []
        deleted_files = []
        modified_files = []
        
        # 初回実行時（履歴が空の場合）は既存ファイルを履歴に追加するだけで通知しない
        is_first_run = len(self.known_files) == 0
        
        if is_first_run:
            self.logger.info(f"初回実行: {len(current_files)}個の既存ファイルを履歴に追加します（通知なし）")
        
        # 新規ファイルと変更ファイルのチェック
        for file_info in current_files:
            filename = file_info['name']
            file_path = file_info['path']
            
            # ファイル名ではなく完全パスを使用して識別
            if file_path not in self.known_files:
                # 初回実行時はハッシュ計算をスキップしてパフォーマンスを向上
                if is_first_run:
                    file_hash = ""  # 初回はハッシュ計算をスキップ
                    self.logger.debug(f"初回実行: 既存ファイルを履歴に追加: {file_path}")
                else:
                    # 2回目以降はハッシュ計算を実行
                    file_hash = self.get_file_hash(file_path)
                    file_info['hash'] = file_hash
                    new_files.append(file_info)
                    self.logger.info(f"新規ファイルを発見: {file_path}")
                
                # 常に完全パスで履歴更新
                self.known_files.add(file_path)
                self.file_hashes[file_path] = file_hash
            else:
                # 既存ファイルの変更チェック
                if not is_first_run:
                    current_hash = self.get_file_hash(file_path)
                    stored_hash = self.file_hashes.get(file_path, "")
                    
                    if current_hash != stored_hash and stored_hash != "":
                        file_info['hash'] = current_hash
                        file_info['old_hash'] = stored_hash
                        modified_files.append(file_info)
                        self.logger.info(f"ファイルが変更されました: {file_path}")
                        self.file_hashes[file_path] = current_hash
        
        # 削除ファイルのチェック
        if not is_first_run:
            for known_file_path in list(self.known_files):
                if known_file_path not in current_file_paths:
                    # 削除されたファイルの情報を取得
                    deleted_file_info = {
                        'name': os.path.basename(known_file_path),
                        'path': known_file_path,
                        'folder': os.path.dirname(known_file_path)
                    }
                    deleted_files.append(deleted_file_info)
                    self.logger.info(f"ファイルが削除されました: {known_file_path}")
                    
                    # 履歴から削除
                    self.known_files.discard(known_file_path)
                    self.file_hashes.pop(known_file_path, None)
        
        if is_first_run:
            self.logger.info(f"初回実行完了: {len(self.known_files)}件の履歴を追加しました")
        
        return {
            'new': new_files,
            'deleted': deleted_files,
            'modified': modified_files
        }
    
    def send_notifications(self, file_changes: Dict[str, List[Dict]]):
        """通知の送信"""
        new_files = file_changes.get('new', [])
        deleted_files = file_changes.get('deleted', [])
        modified_files = file_changes.get('modified', [])
        
        if not new_files and not deleted_files and not modified_files:
            return
        
        # 通知メッセージの作成
        message = self._create_notification_message(file_changes)
        
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
    
    def _create_notification_message(self, file_changes: Dict[str, List[Dict]]) -> str:
        """通知メッセージの作成"""
        new_files = file_changes.get('new', [])
        deleted_files = file_changes.get('deleted', [])
        modified_files = file_changes.get('modified', [])
        
        # 通知タイトルの決定
        if new_files and deleted_files and modified_files:
            title = "🔔 HETEMLサーバでファイルの変更を検出しました"
        elif new_files and deleted_files:
            title = "🔔 HETEMLサーバでファイルの追加・削除を検出しました"
        elif new_files and modified_files:
            title = "🔔 HETEMLサーバでファイルの追加・変更を検出しました"
        elif deleted_files and modified_files:
            title = "🔔 HETEMLサーバでファイルの削除・変更を検出しました"
        elif new_files:
            title = "🔔 HETEMLサーバで新規ファイルを発見しました"
        elif deleted_files:
            title = "🔔 HETEMLサーバでファイルの削除を検出しました"
        elif modified_files:
            title = "🔔 HETEMLサーバでファイルの変更を検出しました"
        else:
            title = "🔔 HETEMLサーバでファイルの変更を検出しました"
        
        message = f"{title}\n\n"
        message += f"監視対象: {MONITOR_CONFIG['target_path']}\n"
        message += f"検出時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 新規ファイル
        if new_files:
            message += f"📁 新規ファイル ({len(new_files)}件):\n"
            for i, file_info in enumerate(new_files, 1):
                folder_path = os.path.dirname(file_info['path'])
                relative_folder = folder_path.replace(MONITOR_CONFIG['target_path'], '').strip('/')
                folder_display = f"/{relative_folder}" if relative_folder else "/"
                
                message += f"{i}. {file_info['name']}\n"
                message += f"   フォルダ: {folder_display}\n"
                message += f"   サイズ: {file_info['size']:,} bytes\n"
                message += f"   更新日時: {datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 削除ファイル
        if deleted_files:
            message += f"🗑️ 削除ファイル ({len(deleted_files)}件):\n"
            for i, file_info in enumerate(deleted_files, 1):
                folder_path = file_info['folder']
                relative_folder = folder_path.replace(MONITOR_CONFIG['target_path'], '').strip('/')
                folder_display = f"/{relative_folder}" if relative_folder else "/"
                
                message += f"{i}. {file_info['name']}\n"
                message += f"   フォルダ: {folder_display}\n\n"
        
        # 変更ファイル
        if modified_files:
            message += f"✏️ 変更ファイル ({len(modified_files)}件):\n"
            for i, file_info in enumerate(modified_files, 1):
                folder_path = os.path.dirname(file_info['path'])
                relative_folder = folder_path.replace(MONITOR_CONFIG['target_path'], '').strip('/')
                folder_display = f"/{relative_folder}" if relative_folder else "/"
                
                message += f"{i}. {file_info['name']}\n"
                message += f"   フォルダ: {folder_display}\n"
                message += f"   サイズ: {file_info['size']:,} bytes\n"
                message += f"   更新日時: {datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return message
    
    def monitor_once(self):
        """1回の監視実行"""
        try:
            if not self.connect_ssh():
                return
            
            file_changes = self.check_file_changes()
            
            if file_changes['new'] or file_changes['deleted'] or file_changes['modified']:
                self.send_notifications(file_changes)
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
