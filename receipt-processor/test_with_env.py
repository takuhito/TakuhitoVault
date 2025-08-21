#!/usr/bin/env python3
"""
環境変数を設定してテストするスクリプト
"""

import os
import sys

def set_test_environment():
    """テスト用の環境変数を設定"""
    # 実際の値はGitHub Secretsから取得する必要があります
    test_env = {
        'NOTION_TOKEN': 'your_notion_token_here',
        'GEMINI_API_KEY': 'your_gemini_api_key_here',
        'NOTION_DATABASE_ID': '254b061dadf38042813eeab350aea734',
        'GOOGLE_DRIVE_MONITOR_FOLDER': '1YccjjOWIp4PAQVUY8SVcSvUvkcQ6lo3B',
        'GOOGLE_DRIVE_PROCESSED_BASE': '0AJojvkLIwToKUk9PVA',
        'GOOGLE_DRIVE_ERROR_FOLDER': '1HJrzj1DDoiTmIkNa8tIN3RKnLKs_8Kaf',
        'GOOGLE_DRIVE_SHARED_DRIVE_ID': '0AJojvkLIwToKUk9PVA'
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
        print(f"Set {key} = {value}")

def test_google_drive_files():
    """Google Driveのファイルを確認"""
    print("\n=== Testing Google Drive Files ===")
    
    try:
        from google_drive_client import GoogleDriveClient
        client = GoogleDriveClient()
        
        # 監視フォルダのファイルを取得
        files = client.get_new_files()
        print(f"Found {len(files)} files in monitor folder")
        
        if files:
            print("Files in monitor folder:")
            for file in files:
                print(f"  - {file['name']} ({file['id']}) - {file.get('mimeType', 'unknown')}")
        else:
            print("No files found in monitor folder")
            
    except Exception as e:
        print(f"Error: {e}")

def test_main_execution():
    """main.pyの実行をテスト"""
    print("\n=== Testing main.py execution ===")
    
    try:
        # main.pyをインポートして実行
        import main
        print("main.py imported successfully")
        
        # main.pyのmain関数を実行
        if hasattr(main, 'main'):
            main.main()
            print("main.py executed successfully")
        else:
            print("main.py does not have a main function")
            
    except Exception as e:
        print(f"Error executing main.py: {e}")

def main():
    """メイン関数"""
    print("🧪 Testing with environment variables")
    print("=" * 50)
    
    set_test_environment()
    test_google_drive_files()
    test_main_execution()
    
    print("\n" + "=" * 50)
    print("Test completed")

if __name__ == "__main__":
    main()
