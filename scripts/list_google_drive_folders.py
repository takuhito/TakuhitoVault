#!/usr/bin/env python3
"""
Google Driveフォルダ一覧表示スクリプト
"""
import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'receipt-processor'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import importlib.util
spec = importlib.util.spec_from_file_location("google_drive_api_client", os.path.join(os.path.dirname(__file__), '..', 'receipt-processor', 'google_drive_client.py'))
google_drive_client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(google_drive_client_module)
GoogleDriveClient = google_drive_client_module.GoogleDriveClient

def list_all_folders():
    """Google Driveの全てのフォルダを一覧表示"""
    
    print("📁 Google Driveフォルダ一覧")
    print("=" * 50)
    
    try:
        drive_client = GoogleDriveClient()
        print("✅ GoogleDriveClient初期化成功")
        
        # ルートフォルダから全てのフォルダを取得
        query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = drive_client.service.files().list(
            q=query, 
            spaces='drive', 
            fields='files(id, name, parents)',
            pageSize=1000
        ).execute()
        
        folders = results.get('files', [])
        
        if not folders:
            print("❌ フォルダが見つかりません")
            return
        
        print(f"📊 見つかったフォルダ数: {len(folders)}")
        print()
        
        # フォルダを名前順にソート
        folders.sort(key=lambda x: x['name'].lower())
        
        print("📋 フォルダ一覧:")
        print("-" * 50)
        
        for folder in folders:
            folder_id = folder['id']
            folder_name = folder['name']
            parents = folder.get('parents', [])
            
            # 親フォルダ情報を取得
            parent_names = []
            for parent_id in parents:
                try:
                    parent = drive_client.service.files().get(fileId=parent_id, fields='name').execute()
                    parent_names.append(parent['name'])
                except:
                    parent_names.append(f"ID:{parent_id}")
            
            parent_info = f" (親: {', '.join(parent_names)})" if parent_names else " (ルート)"
            
            print(f"• {folder_name} (ID: {folder_id}){parent_info}")
        
        # 領収書関連のフォルダを検索
        print(f"\n🔍 領収書関連フォルダ検索:")
        print("-" * 30)
        
        receipt_folders = [f for f in folders if '領収書' in f['name'] or 'receipt' in f['name'].lower()]
        
        if receipt_folders:
            print("✅ 領収書関連フォルダ:")
            for folder in receipt_folders:
                print(f"• {folder['name']} (ID: {folder['id']})")
        else:
            print("❌ 領収書関連フォルダが見つかりません")
        
        return folders
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def search_folder_by_name(folders, search_name):
    """名前でフォルダを検索"""
    if not folders:
        return None
    
    search_name_lower = search_name.lower()
    matches = [f for f in folders if search_name_lower in f['name'].lower()]
    
    if matches:
        print(f"\n🔍 '{search_name}' を含むフォルダ:")
        for folder in matches:
            print(f"• {folder['name']} (ID: {folder['id']})")
        return matches
    else:
        print(f"\n❌ '{search_name}' を含むフォルダが見つかりません")
        return []

if __name__ == "__main__":
    folders = list_all_folders()
    if folders:
        # 領収書関連の検索
        search_folder_by_name(folders, "領収書")
        search_folder_by_name(folders, "receipt")
        search_folder_by_name(folders, "管理")

