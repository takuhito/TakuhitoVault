#!/usr/bin/env python3
"""
Google Driveアクセステストスクリプト
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

def test_google_drive_access():
    """Google Driveアクセスの詳細テスト"""
    
    print("🔍 Google Driveアクセステスト")
    print("=" * 50)
    
    try:
        drive_client = GoogleDriveClient()
        print("✅ GoogleDriveClient初期化成功")
        
        # 1. サービスアカウント情報の確認
        print("\n📋 サービスアカウント情報:")
        print("-" * 30)
        
        # サービスアカウントファイルからメールアドレスを取得
        import json
        with open('credentials/service-account.json', 'r') as f:
            service_account = json.load(f)
        
        client_email = service_account.get('client_email', 'Unknown')
        project_id = service_account.get('project_id', 'Unknown')
        
        print(f"• プロジェクトID: {project_id}")
        print(f"• サービスアカウント: {client_email}")
        
        # 2. 基本的なAPIアクセステスト
        print("\n🧪 基本的なAPIアクセステスト:")
        print("-" * 30)
        
        try:
            # ファイル一覧を取得（制限付き）
            results = drive_client.service.files().list(
                pageSize=10,
                fields="files(id, name, mimeType)"
            ).execute()
            
            files = results.get('files', [])
            print(f"✅ ファイル一覧取得成功: {len(files)}件")
            
            if files:
                print("📋 見つかったファイル:")
                for file in files:
                    file_type = "フォルダ" if file['mimeType'] == 'application/vnd.google-apps.folder' else "ファイル"
                    print(f"  • {file['name']} ({file_type}) - ID: {file['id']}")
            else:
                print("⚠️  ファイルが見つかりません")
                
        except Exception as e:
            print(f"❌ ファイル一覧取得失敗: {e}")
        
        # 3. フォルダ検索テスト
        print("\n🔍 フォルダ検索テスト:")
        print("-" * 30)
        
        search_terms = ['領収書', 'receipt', '管理', 'error', 'エラー']
        
        for term in search_terms:
            try:
                query = f"name contains '{term}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                results = drive_client.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name)',
                    pageSize=10
                ).execute()
                
                folders = results.get('files', [])
                if folders:
                    print(f"✅ '{term}' を含むフォルダ: {len(folders)}件")
                    for folder in folders:
                        print(f"  • {folder['name']} (ID: {folder['id']})")
                else:
                    print(f"❌ '{term}' を含むフォルダ: 見つかりません")
                    
            except Exception as e:
                print(f"❌ '{term}' 検索エラー: {e}")
        
        # 4. 権限テスト
        print("\n🔐 権限テスト:")
        print("-" * 30)
        
        try:
            # ルートフォルダの情報を取得
            root_info = drive_client.service.files().get(fileId='root').execute()
            print(f"✅ ルートフォルダアクセス成功: {root_info.get('name', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ ルートフォルダアクセス失敗: {e}")
        
        # 5. 共有設定の確認
        print("\n📝 共有設定確認:")
        print("-" * 30)
        print("以下の手順で共有設定を確認してください:")
        print("1. Google Driveで「領収書管理」フォルダを開く")
        print("2. 右上の「共有」ボタンをクリック")
        print("3. 以下のメールアドレスが表示されているか確認:")
        print(f"   {client_email}")
        print("4. 権限が「編集者」以上になっているか確認")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    test_google_drive_access()

