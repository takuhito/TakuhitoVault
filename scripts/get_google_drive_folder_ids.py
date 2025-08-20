#!/usr/bin/env python3
"""
Google DriveフォルダID取得スクリプト
"""
import os
import sys
import json

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'receipt-processor'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import importlib.util
spec = importlib.util.spec_from_file_location("google_drive_api_client", os.path.join(os.path.dirname(__file__), '..', 'receipt-processor', 'google_drive_client.py'))
google_drive_client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(google_drive_client_module)
GoogleDriveClient = google_drive_client_module.GoogleDriveClient

def get_folder_ids():
    """既存のフォルダからIDを取得"""
    
    print("🔍 Google DriveフォルダID取得")
    print("=" * 50)
    
    try:
        drive_client = GoogleDriveClient()
        print("✅ GoogleDriveClient初期化成功")
        
        # 取得するフォルダパス
        folders_to_check = [
            ("監視フォルダ", "領収書管理/受信箱"),
            ("処理済みベースフォルダ", "領収書管理"),
            ("エラーフォルダ", "領収書管理/エラー")
        ]
        
        folder_ids = {}
        
        for folder_name, folder_path in folders_to_check:
            print(f"\n📁 {folder_name}の確認中...")
            print(f"パス: {folder_path}")
            
            try:
                folder_id = drive_client.get_folder_id(folder_path)
                
                if folder_id:
                    print(f"✅ {folder_name}: {folder_id}")
                    folder_ids[folder_name] = folder_id
                else:
                    print(f"❌ {folder_name}: フォルダが見つかりません")
                    
            except Exception as e:
                print(f"❌ {folder_name}確認エラー: {e}")
        
        # 結果表示
        print(f"\n📋 取得結果")
        print("=" * 30)
        
        if folder_ids:
            print("✅ 取得できたフォルダID:")
            for folder_name, folder_id in folder_ids.items():
                print(f"• {folder_name}: {folder_id}")
            
            # 環境変数設定例
            print(f"\n📝 環境変数設定例:")
            print("=" * 30)
            
            env_mapping = {
                "監視フォルダ": "GOOGLE_DRIVE_MONITOR_FOLDER",
                "処理済みベースフォルダ": "GOOGLE_DRIVE_PROCESSED_BASE", 
                "エラーフォルダ": "GOOGLE_DRIVE_ERROR_FOLDER"
            }
            
            for folder_name, folder_id in folder_ids.items():
                env_var = env_mapping.get(folder_name)
                if env_var:
                    print(f"{env_var}={folder_id}")
            
            # .envファイル更新の提案
            print(f"\n📝 .envファイル更新用:")
            print("=" * 30)
            for folder_name, folder_id in folder_ids.items():
                env_var = env_mapping.get(folder_name)
                if env_var:
                    print(f"{env_var}={folder_id}")
                    
        else:
            print("❌ フォルダIDが取得できませんでした")
            print("フォルダパスを確認してください")
        
        return folder_ids
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def test_folder_access(folder_ids):
    """フォルダアクセステスト"""
    if not folder_ids:
        return
    
    print(f"\n🧪 フォルダアクセステスト")
    print("=" * 30)
    
    try:
        drive_client = GoogleDriveClient()
        
        for folder_name, folder_id in folder_ids.items():
            print(f"📁 {folder_name}のアクセステスト...")
            
            try:
                # フォルダ情報を取得
                folder_info = drive_client.service.files().get(fileId=folder_id).execute()
                print(f"✅ {folder_name}: アクセス成功 ({folder_info.get('name', 'Unknown')})")
                
            except Exception as e:
                print(f"❌ {folder_name}: アクセス失敗 - {e}")
                
    except Exception as e:
        print(f"❌ アクセステストエラー: {e}")

if __name__ == "__main__":
    folder_ids = get_folder_ids()
    if folder_ids:
        test_folder_access(folder_ids)

