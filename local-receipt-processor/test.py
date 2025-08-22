#!/usr/bin/env python3
"""
ローカル環境用のテストスクリプト
"""

import os
import sys
from datetime import datetime

def test_environment():
    """環境変数のテスト"""
    print("🔍 環境変数テスト")
    print("=" * 40)
    
    required_vars = [
        'NOTION_TOKEN',
        'GEMINI_API_KEY',
        'NOTION_DATABASE_ID',
        'GOOGLE_DRIVE_MONITOR_FOLDER'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'TOKEN' in var or 'KEY' in var:
                masked_value = value[:10] + "..." + value[-10:] if len(value) > 20 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")

def test_imports():
    """モジュールインポートテスト"""
    print("\n🔍 モジュールインポートテスト")
    print("=" * 40)
    
    modules = ['config', 'google_drive_client', 'notion_api_client']
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}: OK")
        except Exception as e:
            print(f"❌ {module}: {e}")

def test_google_drive():
    """Google Drive接続テスト"""
    print("\n🔍 Google Drive接続テスト")
    print("=" * 40)
    
    try:
        from google_drive_client import GoogleDriveClient
        client = GoogleDriveClient()
        print("✅ GoogleDriveClient: OK")
        
        # 監視フォルダのファイル数を確認
        files = client.get_new_files()
        print(f"📁 監視フォルダ内ファイル数: {len(files)}")
        
    except Exception as e:
        print(f"❌ Google Drive: {e}")

def test_notion():
    """Notion接続テスト"""
    print("\n🔍 Notion接続テスト")
    print("=" * 40)
    
    try:
        from notion_api_client import NotionClient
        client = NotionClient()
        print("✅ NotionClient: OK")
        
        # 接続テスト
        if client.test_connection():
            print("✅ Notion接続: OK")
        else:
            print("❌ Notion接続: FAILED")
            
    except Exception as e:
        print(f"❌ Notion: {e}")

def main():
    """メイン関数"""
    print(f"🧪 ローカルテスト開始 - {datetime.now()}")
    print("=" * 60)
    
    test_environment()
    test_imports()
    test_google_drive()
    test_notion()
    
    print("\n" + "=" * 60)
    print("テスト完了")

if __name__ == "__main__":
    main()
