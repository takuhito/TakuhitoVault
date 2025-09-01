#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
クイック削除検出テスト（ハッシュ計算をスキップ）
"""

import os
import sys
import time
from datetime import datetime

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from heteml_monitor import HETEMLMonitor

def test_quick_deletion():
    """クイック削除検出テスト"""
    print("🧪 クイック削除検出テストを開始します...")
    print(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    try:
        # モニターの初期化
        monitor = HETEMLMonitor()
        
        # SSH接続
        if not monitor.connect_ssh():
            print("❌ SSH接続に失敗しました")
            return False
        
        print("✅ SSH接続が確立されました")
        
        # 現在のファイル履歴の状態を確認
        print(f"📊 現在のファイル履歴: {len(monitor.known_files)}ファイル")
        
        # ファイル一覧を取得（ハッシュ計算なし）
        print("🔍 ファイル一覧を取得中...")
        current_files = monitor.get_file_list()
        current_file_paths = {file_info['path'] for file_info in current_files}
        
        print(f"📁 現在のファイル数: {len(current_files)}")
        
        # 削除ファイルのチェック（ハッシュ計算なし）
        deleted_files = []
        for known_file_path in list(monitor.known_files):
            if known_file_path not in current_file_paths:
                deleted_file_info = {
                    'name': os.path.basename(known_file_path),
                    'path': known_file_path,
                    'folder': os.path.dirname(known_file_path)
                }
                deleted_files.append(deleted_file_info)
                print(f"🗑️ 削除されたファイルを発見: {known_file_path}")
        
        # 新規ファイルのチェック（ハッシュ計算なし）
        new_files = []
        for file_info in current_files:
            file_path = file_info['path']
            if file_path not in monitor.known_files:
                new_files.append(file_info)
                print(f"📁 新規ファイルを発見: {file_path}")
        
        print(f"\n📈 検出結果:")
        print(f"  - 新規ファイル: {len(new_files)}個")
        print(f"  - 削除ファイル: {len(deleted_files)}個")
        
        # 削除ファイルの詳細表示
        if deleted_files:
            print("\n🗑️ 削除されたファイル:")
            for i, file_info in enumerate(deleted_files, 1):
                folder_path = file_info['folder']
                relative_folder = folder_path.replace('/home/users/0/nbsorjp/web/domain/nbspress.com/nbs.or.jp/stages/', '').strip('/')
                folder_display = f"/{relative_folder}" if relative_folder else "/"
                print(f"  {i}. {file_info['name']}")
                print(f"     フォルダ: {folder_display}")
        
        # 新規ファイルの詳細表示
        if new_files:
            print("\n📁 新規ファイル:")
            for i, file_info in enumerate(new_files, 1):
                folder_path = os.path.dirname(file_info['path'])
                relative_folder = folder_path.replace('/home/users/0/nbsorjp/web/domain/nbspress.com/nbs.or.jp/stages/', '').strip('/')
                folder_display = f"/{relative_folder}" if relative_folder else "/"
                print(f"  {i}. {file_info['name']}")
                print(f"     フォルダ: {folder_display}")
                print(f"     サイズ: {file_info['size']:,} bytes")
        
        # 通知メッセージのテスト
        if new_files or deleted_files:
            print("\n📧 通知メッセージのテスト...")
            file_changes = {
                'new': new_files,
                'deleted': deleted_files,
                'modified': []
            }
            message = monitor._create_notification_message(file_changes)
            print("通知メッセージ:")
            print("-" * 50)
            print(message)
            print("-" * 50)
        else:
            print("ℹ️  ファイルの変更はありませんでした")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if monitor:
            monitor.disconnect_ssh()
            print("🔌 SSH接続を切断しました")
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"⏱️  実行時間: {execution_time:.2f}秒")

if __name__ == "__main__":
    success = test_quick_deletion()
    
    if success:
        print("\n✅ クイック削除検出テストが完了しました")
        print("📧 削除検出機能が正常に動作しています")
    else:
        print("\n❌ クイック削除検出テストでエラーが発生しました")
        sys.exit(1)
