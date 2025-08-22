#!/usr/bin/env python3
"""
簡易テストスクリプト - 基本的な機能テスト
"""

import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def quick_test():
    """簡易テスト"""
    print("🔍 簡易テスト開始")
    print("=" * 40)
    
    # 1. 環境変数チェック
    print("1. 環境変数チェック")
    required = ['NOTION_TOKEN', 'GEMINI_API_KEY', 'NOTION_DATABASE_ID', 'GOOGLE_DRIVE_MONITOR_FOLDER']
    for var in required:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: SET")
        else:
            print(f"  ❌ {var}: NOT SET")
    
    # 2. モジュールインポートテスト
    print("\n2. モジュールインポートテスト")
    modules = ['google_drive_client', 'notion_api_client', 'gemini_client', 'receipt_parser']
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}: OK")
        except Exception as e:
            print(f"  ❌ {module}: {e}")
    
    # 3. Google Drive接続テスト
    print("\n3. Google Drive接続テスト")
    try:
        from google_drive_client import GoogleDriveClient
        client = GoogleDriveClient()
        print("  ✅ GoogleDriveClient: OK")
        
        # 監視フォルダのファイル数を確認
        monitor_folder = os.getenv('GOOGLE_DRIVE_MONITOR_FOLDER')
        if monitor_folder:
            files = client.get_new_files()
            print(f"  📁 監視フォルダ内ファイル数: {len(files)}")
            if files:
                for file in files[:3]:  # 最初の3ファイルのみ表示
                    print(f"    - {file['name']}")
                if len(files) > 3:
                    print(f"    ... 他 {len(files) - 3} ファイル")
        else:
            print("  ❌ GOOGLE_DRIVE_MONITOR_FOLDER not set")
            
    except Exception as e:
        print(f"  ❌ Google Drive: {e}")
    
    # 4. Notion接続テスト
    print("\n4. Notion接続テスト")
    try:
        from notion_api_client import NotionClient
        client = NotionClient()
        print("  ✅ NotionClient: OK")
        
        # データベースの存在確認
        database_id = os.getenv('NOTION_DATABASE_ID')
        if database_id:
            try:
                database = client.client.databases.retrieve(database_id)
                print(f"  📊 データベース: {database.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            except Exception as e:
                print(f"  ❌ データベースアクセス: {e}")
        else:
            print("  ❌ NOTION_DATABASE_ID not set")
            
    except Exception as e:
        print(f"  ❌ Notion: {e}")
    
    print("\n" + "=" * 40)
    print("簡易テスト完了")

if __name__ == "__main__":
    quick_test()
