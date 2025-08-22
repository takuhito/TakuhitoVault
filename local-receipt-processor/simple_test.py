#!/usr/bin/env python3
"""
簡易テストスクリプト - APIキーなしでも動作確認
"""

import os
import sys
from datetime import datetime

def test_basic_imports():
    """基本的なインポートテスト"""
    print("🔍 基本的なインポートテスト")
    print("=" * 40)
    
    try:
        import config
        print("✅ config: OK")
    except Exception as e:
        print(f"❌ config: {e}")
    
    try:
        import google_drive_client
        print("✅ google_drive_client: OK")
    except Exception as e:
        print(f"❌ google_drive_client: {e}")
    
    try:
        import notion_api_client
        print("✅ notion_api_client: OK")
    except Exception as e:
        print(f"❌ notion_api_client: {e}")

def test_config_loading():
    """設定ファイルの読み込みテスト"""
    print("\n🔍 設定ファイル読み込みテスト")
    print("=" * 40)
    
    try:
        from config import (
            NOTION_TOKEN, NOTION_DATABASE_ID, GEMINI_API_KEY,
            GOOGLE_DRIVE_MONITOR_FOLDER, GOOGLE_DRIVE_PROCESSED_BASE,
            GOOGLE_DRIVE_ERROR_FOLDER, GOOGLE_DRIVE_SHARED_DRIVE_ID
        )
        
        print(f"✅ NOTION_TOKEN: {'SET' if NOTION_TOKEN else 'NOT SET'}")
        print(f"✅ NOTION_DATABASE_ID: {NOTION_DATABASE_ID}")
        print(f"✅ GEMINI_API_KEY: {'SET' if GEMINI_API_KEY else 'NOT SET'}")
        print(f"✅ GOOGLE_DRIVE_MONITOR_FOLDER: {GOOGLE_DRIVE_MONITOR_FOLDER}")
        print(f"✅ GOOGLE_DRIVE_PROCESSED_BASE: {GOOGLE_DRIVE_PROCESSED_BASE}")
        print(f"✅ GOOGLE_DRIVE_ERROR_FOLDER: {GOOGLE_DRIVE_ERROR_FOLDER}")
        print(f"✅ GOOGLE_DRIVE_SHARED_DRIVE_ID: {GOOGLE_DRIVE_SHARED_DRIVE_ID}")
        
    except Exception as e:
        print(f"❌ 設定読み込みエラー: {e}")

def test_google_drive_credentials():
    """Google Drive認証ファイルの確認"""
    print("\n🔍 Google Drive認証ファイル確認")
    print("=" * 40)
    
    from config import GOOGLE_DRIVE_CREDENTIALS_FILE
    
    if os.path.exists(GOOGLE_DRIVE_CREDENTIALS_FILE):
        print(f"✅ 認証ファイル存在: {GOOGLE_DRIVE_CREDENTIALS_FILE}")
        
        # ファイルサイズを確認
        file_size = os.path.getsize(GOOGLE_DRIVE_CREDENTIALS_FILE)
        print(f"📄 ファイルサイズ: {file_size} bytes")
        
        # ファイルの内容を確認（最初の数行）
        try:
            with open(GOOGLE_DRIVE_CREDENTIALS_FILE, 'r') as f:
                first_line = f.readline().strip()
                if first_line.startswith('{'):
                    print("✅ JSON形式の認証ファイル")
                else:
                    print("❌ JSON形式ではありません")
        except Exception as e:
            print(f"❌ ファイル読み込みエラー: {e}")
    else:
        print(f"❌ 認証ファイルが見つかりません: {GOOGLE_DRIVE_CREDENTIALS_FILE}")

def test_google_drive_client_init():
    """Google Driveクライアントの初期化テスト"""
    print("\n🔍 Google Driveクライアント初期化テスト")
    print("=" * 40)
    
    try:
        from google_drive_client import GoogleDriveClient
        client = GoogleDriveClient()
        print("✅ GoogleDriveClient初期化: OK")
        
        # 基本的なメソッドの存在確認
        if hasattr(client, 'get_new_files'):
            print("✅ get_new_filesメソッド: OK")
        else:
            print("❌ get_new_filesメソッド: 見つかりません")
            
        if hasattr(client, 'download_file'):
            print("✅ download_fileメソッド: OK")
        else:
            print("❌ download_fileメソッド: 見つかりません")
            
        if hasattr(client, 'move_file'):
            print("✅ move_fileメソッド: OK")
        else:
            print("❌ move_fileメソッド: 見つかりません")
            
    except Exception as e:
        print(f"❌ GoogleDriveClient初期化エラー: {e}")

def test_notion_client_init():
    """Notionクライアントの初期化テスト"""
    print("\n🔍 Notionクライアント初期化テスト")
    print("=" * 40)
    
    try:
        from notion_api_client import NotionClient
        client = NotionClient()
        print("✅ NotionClient初期化: OK")
        
        # 基本的なメソッドの存在確認
        if hasattr(client, 'create_receipt_page'):
            print("✅ create_receipt_pageメソッド: OK")
        else:
            print("❌ create_receipt_pageメソッド: 見つかりません")
            
        if hasattr(client, 'test_connection'):
            print("✅ test_connectionメソッド: OK")
        else:
            print("❌ test_connectionメソッド: 見つかりません")
            
    except Exception as e:
        print(f"❌ NotionClient初期化エラー: {e}")

def test_main_module():
    """メインモジュールのテスト"""
    print("\n🔍 メインモジュールテスト")
    print("=" * 40)
    
    try:
        import main
        print("✅ mainモジュール: OK")
        
        if hasattr(main, 'main'):
            print("✅ main関数: OK")
        else:
            print("❌ main関数: 見つかりません")
            
        if hasattr(main, 'process_receipt_file'):
            print("✅ process_receipt_file関数: OK")
        else:
            print("❌ process_receipt_file関数: 見つかりません")
            
    except Exception as e:
        print(f"❌ mainモジュールエラー: {e}")

def main():
    """メイン関数"""
    print(f"🧪 簡易テスト開始 - {datetime.now()}")
    print("=" * 60)
    
    test_basic_imports()
    test_config_loading()
    test_google_drive_credentials()
    test_google_drive_client_init()
    test_notion_client_init()
    test_main_module()
    
    print("\n" + "=" * 60)
    print("簡易テスト完了")
    print("\n💡 次のステップ:")
    print("1. GitHub Secretsから実際のAPIキーを取得")
    print("2. .envファイルの値を実際の値に置き換え")
    print("3. python test.py で完全なテストを実行")

if __name__ == "__main__":
    main()
