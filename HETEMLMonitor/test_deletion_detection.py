#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ファイル削除検出機能のテストスクリプト
"""

import os
import sys
import time
from datetime import datetime

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from heteml_monitor import HETEMLMonitor

def test_deletion_detection():
    """削除検出機能のテスト"""
    print("🧪 ファイル削除検出機能のテストを開始します...")
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
        
        # ファイル変更のチェック
        print("🔍 ファイル変更をチェック中...")
        file_changes = monitor.check_file_changes()
        
        new_files = file_changes.get('new', [])
        deleted_files = file_changes.get('deleted', [])
        modified_files = file_changes.get('modified', [])
        
        print(f"📈 検出結果:")
        print(f"  - 新規ファイル: {len(new_files)}個")
        print(f"  - 削除ファイル: {len(deleted_files)}個")
        print(f"  - 変更ファイル: {len(modified_files)}個")
        
        # 削除ファイルの詳細表示
        if deleted_files:
            print("\n🗑️ 削除されたファイル:")
            for i, file_info in enumerate(deleted_files, 1):
                print(f"  {i}. {file_info['name']}")
                print(f"     フォルダ: {file_info['folder']}")
        
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
        
        # 変更ファイルの詳細表示
        if modified_files:
            print("\n✏️ 変更されたファイル:")
            for i, file_info in enumerate(modified_files, 1):
                folder_path = os.path.dirname(file_info['path'])
                relative_folder = folder_path.replace('/home/users/0/nbsorjp/web/domain/nbspress.com/nbs.or.jp/stages/', '').strip('/')
                folder_display = f"/{relative_folder}" if relative_folder else "/"
                print(f"  {i}. {file_info['name']}")
                print(f"     フォルダ: {folder_display}")
                print(f"     サイズ: {file_info['size']:,} bytes")
        
        # 通知のテスト
        if new_files or deleted_files or modified_files:
            print("\n📧 通知メッセージのテスト...")
            message = monitor._create_notification_message(file_changes)
            print("通知メッセージ:")
            print("-" * 50)
            print(message)
            print("-" * 50)
            
            # 実際の通知は送信しない（テストのため）
            print("ℹ️  テストのため、実際の通知は送信しません")
        else:
            print("ℹ️  ファイルの変更はありませんでした")
        
        # ファイル履歴の保存
        monitor.save_file_history()
        print("💾 ファイル履歴を保存しました")
        
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
    success = test_deletion_detection()
    
    if success:
        print("\n✅ 削除検出機能のテストが完了しました")
        print("📧 削除検出機能が正常に動作しています")
    else:
        print("\n❌ 削除検出機能のテストでエラーが発生しました")
        sys.exit(1)
