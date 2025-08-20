#!/usr/bin/env python3
"""
Google Drive設定スクリプト
"""
import os
import sys
import json
from typing import Dict, Any, List, Optional

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'receipt-processor'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import importlib.util
spec = importlib.util.spec_from_file_location("google_drive_api_client", os.path.join(os.path.dirname(__file__), '..', 'receipt-processor', 'google_drive_client.py'))
google_drive_client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(google_drive_client_module)
GoogleDriveClient = google_drive_client_module.GoogleDriveClient

from config.settings import (
    GOOGLE_DRIVE_CREDENTIALS_FILE, 
    GOOGLE_DRIVE_MONITOR_FOLDER,
    GOOGLE_DRIVE_PROCESSED_BASE,
    GOOGLE_DRIVE_ERROR_FOLDER
)

def setup_google_drive():
    """Google Drive設定の確認とセットアップ"""
    
    print("🔧 Google Drive設定開始")
    print("=" * 50)
    
    # 1. 認証情報ファイルの確認
    if not GOOGLE_DRIVE_CREDENTIALS_FILE or not os.path.exists(GOOGLE_DRIVE_CREDENTIALS_FILE):
        print("❌ Google Drive認証情報ファイルが見つかりません")
        print("📝 以下の手順で設定してください：")
        print("1. Google Cloud Consoleでサービスアカウントキーを作成")
        print("2. credentials/service-account.jsonとして保存")
        print("3. .envファイルでGOOGLE_DRIVE_CREDENTIALS_FILEを設定")
        return False
    
    print(f"✅ 認証情報ファイル: {GOOGLE_DRIVE_CREDENTIALS_FILE}")
    
    # 2. GoogleDriveClientの初期化
    try:
        drive_client = GoogleDriveClient()
        print("✅ GoogleDriveClient初期化成功")
    except Exception as e:
        print(f"❌ GoogleDriveClient初期化失敗: {e}")
        return False
    
    # 3. フォルダ構造の確認と作成
    folders_to_check = [
        ("監視フォルダ", GOOGLE_DRIVE_MONITOR_FOLDER),
        ("処理済みフォルダ", GOOGLE_DRIVE_PROCESSED_BASE),
        ("エラーフォルダ", GOOGLE_DRIVE_ERROR_FOLDER)
    ]
    
    folder_ids = {}
    
    for folder_name, folder_path in folders_to_check:
        print(f"\n📁 {folder_name}の確認中...")
        
        try:
            # フォルダの存在確認
            folder_id = drive_client.get_folder_id_by_path(folder_path)
            
            if folder_id:
                print(f"✅ {folder_name}: 存在確認済み (ID: {folder_id})")
                folder_ids[folder_name] = folder_id
            else:
                print(f"⚠️  {folder_name}: フォルダが見つかりません")
                print(f"📝 パス: {folder_path}")
                
                # フォルダ作成の提案
                create = input(f"{folder_name}を作成しますか？ (y/n): ").lower().strip()
                if create == 'y':
                    try:
                        new_folder_id = drive_client.create_folder_structure(folder_path)
                        if new_folder_id:
                            print(f"✅ {folder_name}作成完了 (ID: {new_folder_id})")
                            folder_ids[folder_name] = new_folder_id
                        else:
                            print(f"❌ {folder_name}作成失敗")
                    except Exception as e:
                        print(f"❌ {folder_name}作成エラー: {e}")
                else:
                    print(f"⚠️  {folder_name}の作成をスキップしました")
                    
        except Exception as e:
            print(f"❌ {folder_name}確認エラー: {e}")
    
    # 4. 権限の確認
    print("\n🔐 権限確認中...")
    try:
        # テストファイルの作成
        test_content = "テストファイル"
        test_file_id = drive_client.upload_text_file(
            test_content, 
            "test_permission.txt", 
            folder_ids.get("監視フォルダ")
        )
        
        if test_file_id:
            print("✅ 書き込み権限: 確認済み")
            
            # テストファイルの削除
            drive_client.delete_file(test_file_id)
            print("✅ 削除権限: 確認済み")
        else:
            print("❌ 書き込み権限: エラー")
            
    except Exception as e:
        print(f"❌ 権限確認エラー: {e}")
    
    # 5. 設定情報の出力
    print("\n📋 設定情報")
    print("=" * 30)
    
    for folder_name, folder_id in folder_ids.items():
        print(f"{folder_name}: {folder_id}")
    
    # 6. .envファイル更新の提案
    if folder_ids:
        print("\n📝 .envファイルの更新が必要な場合:")
        for folder_name, folder_id in folder_ids.items():
            env_var = get_env_variable_name(folder_name)
            print(f"{env_var}={folder_id}")
    
    print("\n🎉 Google Drive設定完了！")
    return True

def get_env_variable_name(folder_name: str) -> str:
    """フォルダ名から環境変数名を取得"""
    mapping = {
        "監視フォルダ": "GOOGLE_DRIVE_MONITOR_FOLDER",
        "処理済みフォルダ": "GOOGLE_DRIVE_PROCESSED_BASE", 
        "エラーフォルダ": "GOOGLE_DRIVE_ERROR_FOLDER"
    }
    return mapping.get(folder_name, folder_name.upper())

def create_folder_structure_guide():
    """フォルダ構造作成ガイド"""
    print("\n📋 Google Driveフォルダ構造作成ガイド")
    print("=" * 50)
    
    structure = """
📁 領収書管理/
  ├── 📁 受信箱/          (監視対象フォルダ)
  ├── 📁 処理済み/
  │   ├── 📁 2024/
  │   └── 📁 2025/
  └── 📁 エラー/
      ├── 📁 形式エラー/
      └── 📁 OCRエラー/
"""
    
    print("推奨フォルダ構造:")
    print(structure)
    
    print("手動作成手順:")
    print("1. Google Driveで'領収書管理'フォルダを作成")
    print("2. 上記のサブフォルダを作成")
    print("3. サービスアカウントにフォルダを共有")
    print("4. フォルダIDを取得して.envファイルに設定")
    
    return structure

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "guide":
        create_folder_structure_guide()
    else:
        setup_google_drive()
