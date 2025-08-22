"""
ローカル環境用のGoogle Drive API クライアント
"""

import os
import json
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

from config import GOOGLE_DRIVE_CREDENTIALS_FILE, GOOGLE_DRIVE_MONITOR_FOLDER

class GoogleDriveClient:
    """Google Drive API クライアント"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    def __init__(self):
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Google Drive APIの認証"""
        try:
            # サービスアカウントキーを使用
            creds = service_account.Credentials.from_service_account_file(
                GOOGLE_DRIVE_CREDENTIALS_FILE, 
                scopes=self.SCOPES
            )
            
            self.service = build('drive', 'v3', credentials=creds)
            print("✅ Google Drive API認証完了")
            
        except Exception as e:
            print(f"❌ Google Drive API認証エラー: {e}")
            raise
    
    def get_new_files(self, folder_id: str = None) -> List[Dict]:
        """
        監視フォルダ内の新規ファイルを取得
        
        Args:
            folder_id: 監視フォルダID（指定しない場合は設定値を使用）
            
        Returns:
            List[Dict]: ファイル情報のリスト
        """
        if folder_id is None:
            folder_id = GOOGLE_DRIVE_MONITOR_FOLDER
        
        try:
            # フォルダ内のファイルを取得
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields='files(id,name,mimeType,createdTime,size)'
            ).execute()
            
            files = results.get('files', [])
            print(f"📁 監視フォルダ内ファイル数: {len(files)}")
            
            return files
            
        except Exception as e:
            print(f"❌ ファイル取得エラー: {e}")
            return []
    
    def download_file(self, file_id: str, file_name: str) -> Optional[str]:
        """
        ファイルをダウンロード
        
        Args:
            file_id: ファイルID
            file_name: ファイル名
            
        Returns:
            Optional[str]: ダウンロードしたファイルのパス
        """
        try:
            # 一時ディレクトリを作成
            temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            file_path = os.path.join(temp_dir, file_name)
            
            # ファイルをダウンロード
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"📥 ダウンロード進捗: {int(status.progress() * 100)}%")
            
            # ファイルに保存
            with open(file_path, 'wb') as f:
                f.write(fh.getvalue())
            
            print(f"✅ ファイルダウンロード完了: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ ファイルダウンロードエラー: {e}")
            return None
    
    def move_file(self, file_id: str, destination_folder_id: str) -> bool:
        """
        ファイルを移動
        
        Args:
            file_id: ファイルID
            destination_folder_id: 移動先フォルダID
            
        Returns:
            bool: 移動成功時True
        """
        try:
            # ファイルを新しいフォルダに移動
            file = self.service.files().update(
                fileId=file_id,
                addParents=destination_folder_id,
                removeParents=GOOGLE_DRIVE_MONITOR_FOLDER,
                fields='id, parents'
            ).execute()
            
            print(f"✅ ファイル移動完了: {file_id}")
            return True
            
        except Exception as e:
            print(f"❌ ファイル移動エラー: {e}")
            return False
    
    def get_folder_info(self, folder_id: str) -> Optional[Dict]:
        """
        フォルダ情報を取得
        
        Args:
            folder_id: フォルダID
            
        Returns:
            Optional[Dict]: フォルダ情報
        """
        try:
            folder = self.service.files().get(fileId=folder_id).execute()
            return folder
        except Exception as e:
            print(f"❌ フォルダ情報取得エラー: {e}")
            return None
