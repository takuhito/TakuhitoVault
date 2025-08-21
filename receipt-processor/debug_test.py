#!/usr/bin/env python3
"""
デバッグ用テストスクリプト
"""

import os
import sys
from pathlib import Path

def test_environment():
    """環境変数のテスト"""
    print("=== Environment Variables Test ===")
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
        status = "SET" if value else "NOT SET"
        print(f"{var}: {status}")
        if value and len(value) > 20:
            print(f"  Value: {value[:20]}...")
        elif value:
            print(f"  Value: {value}")

def test_imports():
    """モジュールのインポートテスト"""
    print("\n=== Module Import Test ===")
    
    try:
        import notion_api_client
        print("✅ notion_api_client imported successfully")
    except Exception as e:
        print(f"❌ notion_api_client import failed: {e}")
    
    try:
        import google_drive_client
        print("✅ google_drive_client imported successfully")
    except Exception as e:
        print(f"❌ google_drive_client import failed: {e}")
    
    try:
        import gemini_client
        print("✅ gemini_client imported successfully")
    except Exception as e:
        print(f"❌ gemini_client import failed: {e}")
    
    try:
        import receipt_parser
        print("✅ receipt_parser imported successfully")
    except Exception as e:
        print(f"❌ receipt_parser import failed: {e}")

def test_google_drive_connection():
    """Google Drive接続テスト"""
    print("\n=== Google Drive Connection Test ===")
    
    try:
        from google_drive_client import GoogleDriveClient
        client = GoogleDriveClient()
        
        # 監視フォルダの存在確認
        monitor_folder = os.getenv('GOOGLE_DRIVE_MONITOR_FOLDER')
        if monitor_folder:
            try:
                files = client.get_new_files()
                print(f"✅ Google Drive connection successful")
                print(f"   Found {len(files)} files in monitor folder")
                for file in files:
                    print(f"   - {file['name']} ({file['id']})")
            except Exception as e:
                print(f"❌ Failed to get files: {e}")
        else:
            print("❌ GOOGLE_DRIVE_MONITOR_FOLDER not set")
            
    except Exception as e:
        print(f"❌ Google Drive client initialization failed: {e}")

def test_notion_connection():
    """Notion接続テスト"""
    print("\n=== Notion Connection Test ===")
    
    try:
        from notion_api_client import NotionAPIClient
        client = NotionAPIClient()
        
        # データベースの存在確認
        database_id = os.getenv('NOTION_DATABASE_ID')
        if database_id:
            try:
                # データベースの情報を取得
                print("✅ Notion connection successful")
                print(f"   Database ID: {database_id}")
            except Exception as e:
                print(f"❌ Failed to access database: {e}")
        else:
            print("❌ NOTION_DATABASE_ID not set")
            
    except Exception as e:
        print(f"❌ Notion client initialization failed: {e}")

def test_gemini_connection():
    """Gemini接続テスト"""
    print("\n=== Gemini Connection Test ===")
    
    try:
        from gemini_client import GeminiClient
        client = GeminiClient()
        print("✅ Gemini client initialized successfully")
    except Exception as e:
        print(f"❌ Gemini client initialization failed: {e}")

def main():
    """メイン関数"""
    print("🔍 Receipt Processor Debug Test")
    print("=" * 50)
    
    test_environment()
    test_imports()
    test_google_drive_connection()
    test_notion_connection()
    test_gemini_connection()
    
    print("\n" + "=" * 50)
    print("Debug test completed")

if __name__ == "__main__":
    main()
