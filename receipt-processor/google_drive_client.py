"""
Google Drive API クライアント
"""
import os
import json
import structlog
from typing import List, Dict, Optional, Tuple
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io

from config.settings import (
    GOOGLE_DRIVE_CREDENTIALS_FILE,
    GOOGLE_DRIVE_TOKEN_FILE,
    GOOGLE_DRIVE_MONITOR_FOLDER,
    GOOGLE_DRIVE_PROCESSED_BASE,
    GOOGLE_DRIVE_ERROR_FOLDER
)

logger = structlog.get_logger()

class GoogleDriveClient:
    """Google Drive API クライアント"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    def __init__(self):
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Google Drive APIの認証（サービスアカウント使用）"""
        try:
            from google.oauth2 import service_account
            
            # サービスアカウントキーを使用
            creds = service_account.Credentials.from_service_account_file(
                GOOGLE_DRIVE_CREDENTIALS_FILE, 
                scopes=self.SCOPES
            )
            
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Google Drive API認証完了（サービスアカウント）")
            
        except Exception as e:
            logger.error(f"Google Drive API認証エラー: {e}")
            raise
    
    def get_folder_id(self, folder_path: str) -> Optional[str]:
        """
        フォルダパスからフォルダIDを取得
        
        Args:
            folder_path: フォルダパス（例: /領収書管理/受信箱/）
            
        Returns:
            Optional[str]: フォルダID、見つからない場合はNone
        """
        try:
            # パスを分割
            path_parts = [part for part in folder_path.split('/') if part]
            
            current_id = 'root'  # ルートフォルダから開始
            
            for folder_name in path_parts:
                # フォルダを検索
                query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{current_id}' in parents and trashed=false"
                results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                files = results.get('files', [])
                
                if not files:
                    logger.warning(f"フォルダが見つかりません: {folder_name}")
                    return None
                
                current_id = files[0]['id']
            
            return current_id
            
        except Exception as e:
            logger.error(f"フォルダID取得エラー: {e}")
            return None
    
    def create_folder(self, folder_name: str, parent_id: str = 'root') -> Optional[str]:
        """
        フォルダを作成
        
        Args:
            folder_name: フォルダ名
            parent_id: 親フォルダID
            
        Returns:
            Optional[str]: 作成されたフォルダID、失敗時はNone
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
            
            logger.info(f"フォルダ作成完了: {folder_name} (ID: {folder_id})")
            return folder_id
            
        except Exception as e:
            logger.error(f"フォルダ作成エラー: {e}")
            return None
    
    def ensure_folder_path(self, folder_path: str) -> Optional[str]:
        """
        フォルダパスが存在することを確認し、必要に応じて作成
        
        Args:
            folder_path: フォルダパス
            
        Returns:
            Optional[str]: フォルダID、失敗時はNone
        """
        # まず既存のフォルダを確認
        folder_id = self.get_folder_id(folder_path)
        if folder_id:
            return folder_id
        
        # フォルダが存在しない場合は作成
        path_parts = [part for part in folder_path.split('/') if part]
        current_id = 'root'
        
        for folder_name in path_parts:
            # 現在のレベルでフォルダを検索
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{current_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                current_id = files[0]['id']
            else:
                # フォルダが存在しない場合は作成
                current_id = self.create_folder(folder_name, current_id)
                if not current_id:
                    return None
        
        return current_id
    
    def get_new_files(self, folder_id: str, use_shared_drive: bool = True) -> List[Dict]:
        """
        指定フォルダ内の新規ファイルを取得（共有ドライブ対応）
        
        Args:
            folder_id: 監視フォルダID
            use_shared_drive: 共有ドライブを使用するかどうか
            
        Returns:
            List[Dict]: 新規ファイルのリスト
        """
        try:
            # ファイルを検索（フォルダ以外）
            query = f"'{folder_id}' in parents and mimeType!='application/vnd.google-apps.folder' and trashed=false"
            
            if use_shared_drive:
                results = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name, mimeType, size, createdTime, modifiedTime)',
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
            else:
                results = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name, mimeType, size, createdTime, modifiedTime)'
                ).execute()
            
            files = results.get('files', [])
            logger.info(f"監視フォルダ内のファイル数: {len(files)}")
            
            return files
            
        except Exception as e:
            logger.error(f"新規ファイル取得エラー: {e}")
            return []
    
    def download_file(self, file_id: str, local_path: str) -> bool:
        """
        ファイルをダウンロード
        
        Args:
            file_id: Google DriveのファイルID
            local_path: ローカル保存パス
            
        Returns:
            bool: 成功時はTrue
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                logger.debug(f"ダウンロード進捗: {int(status.progress() * 100)}%")
            
            # ファイルに保存
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())
            
            logger.info(f"ファイルダウンロード完了: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"ファイルダウンロードエラー: {e}")
            return False
    
    def upload_file(self, local_path: str, folder_id: str, filename: str = None) -> Optional[str]:
        """
        ファイルをアップロード
        
        Args:
            local_path: ローカルファイルパス
            folder_id: アップロード先フォルダID
            filename: アップロード時のファイル名（省略時は元ファイル名）
            
        Returns:
            Optional[str]: アップロードされたファイルID、失敗時はNone
        """
        try:
            if filename is None:
                filename = os.path.basename(local_path)
            
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(local_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"ファイルアップロード完了: {filename} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            logger.error(f"ファイルアップロードエラー: {e}")
            return None
    
    def move_file(self, file_id: str, destination_folder_id: str) -> bool:
        """
        ファイルを移動
        
        Args:
            file_id: 移動するファイルID
            destination_folder_id: 移動先フォルダID
            
        Returns:
            bool: 成功時はTrue
        """
        try:
            # ファイルの現在の親フォルダを取得
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents', []))
            
            # ファイルを新しいフォルダに移動
            file = self.service.files().update(
                fileId=file_id,
                addParents=destination_folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
            logger.info(f"ファイル移動完了: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"ファイル移動エラー: {e}")
            return False
    
    def copy_file(self, file_id: str, destination_folder_id: str) -> bool:
        """
        ファイルをコピー
        
        Args:
            file_id: コピーするファイルID
            destination_folder_id: コピー先フォルダID
            
        Returns:
            bool: 成功時はTrue
        """
        try:
            # ファイル情報を取得
            file_info = self.service.files().get(fileId=file_id, fields='name').execute()
            file_name = file_info.get('name', 'unknown')
            
            # コピー先でのファイル名（処理済み_元のファイル名）
            copy_name = f"処理済み_{file_name}"
            
            # ファイルをコピー
            copied_file = self.service.files().copy(
                fileId=file_id,
                body={
                    'name': copy_name,
                    'parents': [destination_folder_id]
                }
            ).execute()
            
            logger.info(f"ファイルコピー完了: {file_id} -> {copied_file.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"ファイルコピーエラー: {e}")
            return False
    
    def delete_file(self, file_id: str) -> bool:
        """
        ファイルを削除（ゴミ箱に移動）
        
        Args:
            file_id: 削除するファイルID
            
        Returns:
            bool: 成功時はTrue
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"ファイル削除完了: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"ファイル削除エラー: {e}")
            return False
    
    def get_folder_id_by_path(self, folder_path: str) -> Optional[str]:
        """フォルダパスからフォルダIDを取得（エイリアス）"""
        return self.get_folder_id(folder_path)
    
    def create_folder_structure(self, folder_path: str, use_shared_drive: bool = True) -> Optional[str]:
        """フォルダ構造を作成（共有ドライブ対応）"""
        try:
            from config.settings import GOOGLE_DRIVE_SHARED_DRIVE_ID
            
            path_parts = [part for part in folder_path.split('/') if part]
            
            # 共有ドライブを使用する場合
            if use_shared_drive and GOOGLE_DRIVE_SHARED_DRIVE_ID:
                current_id = GOOGLE_DRIVE_SHARED_DRIVE_ID
            else:
                current_id = 'root'
            
            for folder_name in path_parts:
                # 既存のフォルダを確認
                query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{current_id}' in parents and trashed=false"
                
                if use_shared_drive and GOOGLE_DRIVE_SHARED_DRIVE_ID:
                    results = self.service.files().list(
                        q=query, 
                        spaces='drive', 
                        fields='files(id, name)',
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True
                    ).execute()
                else:
                    results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                
                files = results.get('files', [])
                
                if files:
                    current_id = files[0]['id']
                else:
                    # フォルダを作成
                    folder_metadata = {
                        'name': folder_name,
                        'mimeType': 'application/vnd.google-apps.folder',
                        'parents': [current_id]
                    }
                    
                    if use_shared_drive and GOOGLE_DRIVE_SHARED_DRIVE_ID:
                        folder = self.service.files().create(
                            body=folder_metadata, 
                            fields='id',
                            supportsAllDrives=True,
                            supportsTeamDrives=True
                        ).execute()
                    else:
                        folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                    
                    current_id = folder.get('id')
                    logger.info(f"フォルダ作成: {folder_name} (ID: {current_id})")
            
            return current_id
            
        except Exception as e:
            logger.error(f"フォルダ構造作成エラー: {e}")
            return None
    
    def upload_file(self, file_path: str, folder_id: str, filename: str = None, use_shared_drive: bool = True) -> Optional[str]:
        """
        ファイルをアップロード（共有ドライブ対応）
        
        Args:
            file_path: アップロードするファイルのパス
            folder_id: アップロード先フォルダID
            filename: アップロード後のファイル名（オプション）
            use_shared_drive: 共有ドライブを使用するかどうか
            
        Returns:
            Optional[str]: アップロードされたファイルID、失敗時はNone
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"ファイルが存在しません: {file_path}")
                return None
            
            # ファイル名を決定
            if not filename:
                filename = os.path.basename(file_path)
            
            # MIMEタイプを決定
            mime_type = 'application/octet-stream'  # デフォルト
            if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                mime_type = 'image/jpeg'
            elif filename.lower().endswith('.png'):
                mime_type = 'image/png'
            elif filename.lower().endswith('.pdf'):
                mime_type = 'application/pdf'
            
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            # 共有ドライブ対応のアップロード
            if use_shared_drive:
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id',
                    supportsAllDrives=True,
                    supportsTeamDrives=True
                ).execute()
            else:
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
            
            file_id = file.get('id')
            logger.info(f"ファイルアップロード完了: {filename} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            logger.error(f"ファイルアップロードエラー: {e}")
            return None

    def upload_text_file(self, content: str, filename: str, folder_id: str = None) -> Optional[str]:
        """テキストファイルをアップロード"""
        try:
            file_metadata = {
                'name': filename,
                'mimeType': 'text/plain'
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(io.BytesIO(content.encode()), mimetype='text/plain', resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"テキストファイルアップロード完了: {filename} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            logger.error(f"テキストファイルアップロードエラー: {e}")
            return None
    
    def move_file_to_error_folder(self, file_id: str, error_message: str = "") -> bool:
        """
        ファイルをエラーフォルダに移動（共有ドライブ対応）
        
        Args:
            file_id: ファイルID
            error_message: エラーメッセージ
            
        Returns:
            bool: 移動成功時はTrue
        """
        try:
            from config.settings import GOOGLE_DRIVE_ERROR_FOLDER
            
            # エラーフォルダIDを取得
            error_folder_id = GOOGLE_DRIVE_ERROR_FOLDER
            
            # 現在の親フォルダを取得
            current_parents = self._get_parent_folders(file_id)
            
            # ファイルを移動
            file = self.service.files().update(
                fileId=file_id,
                addParents=error_folder_id,
                removeParents=current_parents,
                fields='id, name',
                supportsAllDrives=True,
                supportsTeamDrives=True
            ).execute()
            
            logger.info(f"ファイルをエラーフォルダに移動: {file.get('name')}")
            return True
            
        except Exception as e:
            logger.error(f"エラーフォルダ移動失敗: {e}")
            return False
    
    def file_exists_in_folder(self, file_id: str, folder_id: str) -> bool:
        """
        指定されたフォルダ内にファイルが存在するかチェック
        
        Args:
            file_id: ファイルID
            folder_id: フォルダID
            
        Returns:
            bool: 存在する場合はTrue
        """
        try:
            # ファイルの親フォルダを取得
            file = self.service.files().get(
                fileId=file_id,
                fields='parents'
            ).execute()
            
            parents = file.get('parents', [])
            return folder_id in parents
            
        except Exception as e:
            logger.error(f"ファイル存在確認エラー: {e}")
            return False
    
    def get_processed_folder_id(self) -> str:
        """
        処理済みフォルダのIDを取得
        
        Returns:
            str: 処理済みフォルダID
        """
        from config.settings import GOOGLE_DRIVE_PROCESSED_BASE
        return GOOGLE_DRIVE_PROCESSED_BASE
    
    def get_error_folder_id(self) -> str:
        """
        エラーフォルダのIDを取得
        
        Returns:
            str: エラーフォルダID
        """
        from config.settings import GOOGLE_DRIVE_ERROR_FOLDER
        return GOOGLE_DRIVE_ERROR_FOLDER

    def _get_parent_folders(self, file_id: str) -> List[str]:
        """
        ファイルの親フォルダIDを取得
        
        Args:
            file_id: ファイルID
            
        Returns:
            List[str]: 親フォルダIDのリスト
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='parents'
            ).execute()
            
            parents = file.get('parents', [])
            return parents
            
        except Exception as e:
            logger.error(f"親フォルダ取得エラー: {file_id}, {e}")
            return []
