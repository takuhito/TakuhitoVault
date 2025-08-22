#!/usr/bin/env python3
"""
詳細デバッグスクリプト - 問題の根本原因を特定
"""

import os
import sys
import json
from datetime import datetime

def print_section(title):
    """セクション区切りを表示"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_environment_variables():
    """環境変数の詳細チェック"""
    print_section("環境変数チェック")
    
    required_vars = [
        'NOTION_TOKEN',
        'GEMINI_API_KEY', 
        'NOTION_DATABASE_ID',
        'GOOGLE_DRIVE_MONITOR_FOLDER',
        'GOOGLE_DRIVE_PROCESSED_BASE',
        'GOOGLE_DRIVE_ERROR_FOLDER',
        'GOOGLE_DRIVE_SHARED_DRIVE_ID'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 機密情報は一部マスク
            if 'TOKEN' in var or 'KEY' in var:
                masked_value = value[:10] + "..." + value[-10:] if len(value) > 20 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")

def test_google_drive_connection():
    """Google Drive接続テスト"""
    print_section("Google Drive接続テスト")
    
    try:
        from google_drive_client import GoogleDriveClient
        print("✅ GoogleDriveClient import successful")
        
        client = GoogleDriveClient()
        print("✅ GoogleDriveClient initialization successful")
        
        # 監視フォルダの情報を取得
        monitor_folder_id = os.getenv('GOOGLE_DRIVE_MONITOR_FOLDER')
        if monitor_folder_id:
            print(f"📁 Monitor folder ID: {monitor_folder_id}")
            
            # フォルダの存在確認
            try:
                folder_info = client.service.files().get(fileId=monitor_folder_id).execute()
                print(f"✅ Monitor folder exists: {folder_info.get('name', 'Unknown')}")
                
                # フォルダ内のファイルを取得
                query = f"'{monitor_folder_id}' in parents and trashed=false"
                results = client.service.files().list(q=query).execute()
                files = results.get('files', [])
                
                print(f"📄 Files in monitor folder: {len(files)}")
                for file in files:
                    print(f"  - {file['name']} ({file['id']}) - {file.get('mimeType', 'unknown')}")
                    
            except Exception as e:
                print(f"❌ Error accessing monitor folder: {e}")
        else:
            print("❌ GOOGLE_DRIVE_MONITOR_FOLDER not set")
            
    except Exception as e:
        print(f"❌ Google Drive connection error: {e}")
        import traceback
        traceback.print_exc()

def test_notion_connection():
    """Notion接続テスト"""
    print_section("Notion接続テスト")
    
    try:
        from notion_api_client import NotionClient
        print("✅ NotionClient import successful")
        
        client = NotionClient()
        print("✅ NotionClient initialization successful")
        
        # データベースの存在確認
        database_id = os.getenv('NOTION_DATABASE_ID')
        if database_id:
            print(f"📊 Database ID: {database_id}")
            
            try:
                # データベース情報を取得
                database = client.client.databases.retrieve(database_id)
                print(f"✅ Database exists: {database.get('title', [{}])[0].get('plain_text', 'Unknown')}")
                
                # データベース内のページ数を確認
                response = client.client.databases.query(database_id=database_id)
                pages = response.get('results', [])
                print(f"📄 Pages in database: {len(pages)}")
                
            except Exception as e:
                print(f"❌ Error accessing database: {e}")
        else:
            print("❌ NOTION_DATABASE_ID not set")
            
    except Exception as e:
        print(f"❌ Notion connection error: {e}")
        import traceback
        traceback.print_exc()

def test_main_execution():
    """main.pyの実行テスト"""
    print_section("main.py実行テスト")
    
    try:
        print("🔄 Importing main module...")
        import main
        print("✅ main module imported successfully")
        
        print("🔄 Checking main function...")
        if hasattr(main, 'main'):
            print("✅ main function found")
            
            print("🔄 Executing main function...")
            result = main.main()
            print(f"✅ main function executed, result: {result}")
            
        else:
            print("❌ main function not found")
            
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
        import traceback
        traceback.print_exc()

def check_file_structure():
    """ファイル構造の確認"""
    print_section("ファイル構造確認")
    
    current_dir = os.getcwd()
    print(f"📂 Current directory: {current_dir}")
    
    files = os.listdir('.')
    print(f"📄 Files in current directory: {len(files)}")
    
    python_files = [f for f in files if f.endswith('.py')]
    print(f"🐍 Python files: {python_files}")

def main():
    """メイン関数"""
    print(f"🚀 Detailed Debug Session - {datetime.now()}")
    
    check_file_structure()
    check_environment_variables()
    test_google_drive_connection()
    test_notion_connection()
    test_main_execution()
    
    print_section("デバッグセッション完了")

if __name__ == "__main__":
    main()
