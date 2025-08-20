"""
ファイル管理機能
"""
import os
import shutil
import structlog
from typing import List, Optional, Tuple
from datetime import datetime

from utils import (
    validate_file_extension,
    sanitize_filename,
    get_year_month_folder_path,
    create_processing_metadata
)
from config.settings import (
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_PDF_FORMATS,
    MAX_FILE_SIZE,
    GOOGLE_DRIVE_PROCESSED_BASE,
    GOOGLE_DRIVE_ERROR_FOLDER
)

logger = structlog.get_logger()

class FileManager:
    """ファイル管理クラス"""
    
    def __init__(self, google_drive_client=None):
        self.google_drive_client = google_drive_client
        self.temp_dir = None
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        ファイルの妥当性をチェック
        
        Args:
            file_path: ファイルパス
            
        Returns:
            Tuple[bool, str]: (妥当性, エラーメッセージ)
        """
        try:
            # ファイルの存在確認
            if not os.path.exists(file_path):
                return False, "ファイルが存在しません"
            
            # ファイルサイズの確認
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "ファイルが空です"
            
            if file_size > MAX_FILE_SIZE:
                return False, f"ファイルサイズが上限を超えています: {file_size} > {MAX_FILE_SIZE}"
            
            # ファイル拡張子の確認
            filename = os.path.basename(file_path)
            if not validate_file_extension(filename, SUPPORTED_IMAGE_FORMATS + SUPPORTED_PDF_FORMATS):
                return False, f"未対応のファイル形式です: {filename}"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"ファイル検証エラー: {e}"
    
    def get_file_type(self, file_path: str) -> str:
        """
        ファイルタイプを判定
        
        Args:
            file_path: ファイルパス
            
        Returns:
            str: ファイルタイプ（'image', 'pdf', 'unknown'）
        """
        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(filename.lower())
        
        if ext in SUPPORTED_IMAGE_FORMATS:
            return 'image'
        elif ext in SUPPORTED_PDF_FORMATS:
            return 'pdf'
        else:
            return 'unknown'
    
    def create_temp_directory(self) -> str:
        """
        一時ディレクトリを作成
        
        Returns:
            str: 作成されたディレクトリパス
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_dir = os.path.join('/tmp', f'receipt_processor_{timestamp}')
            os.makedirs(temp_dir, exist_ok=True)
            
            self.temp_dir = temp_dir
            logger.info(f"一時ディレクトリ作成: {temp_dir}")
            return temp_dir
            
        except Exception as e:
            logger.error(f"一時ディレクトリ作成エラー: {e}")
            raise
    
    def cleanup_temp_directory(self) -> None:
        """
        一時ディレクトリを削除
        """
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"一時ディレクトリ削除: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"一時ディレクトリ削除エラー: {e}")
    
    def move_file_to_processed_folder(self, file_path: str, date: datetime, file_id: str = None) -> Optional[str]:
        """
        処理済みファイルを年度・月度フォルダに移動（一時的に無効化）
        
        Args:
            file_path: ファイルパス
            date: 領収書の日付
            file_id: Google DriveファイルID（オプション）
            
        Returns:
            Optional[str]: 移動先パス、失敗時はNone
        """
        try:
            # 一時的にファイル移動を無効化（ファイルIDの問題を解決するため）
            logger.warning(f"ファイル移動を一時的に無効化: {file_path}")
            logger.warning(f"本来の移動先: {get_year_month_folder_path(date)}")
            
            # 移動先パスを返すが、実際の移動は行わない
            year_month_path = get_year_month_folder_path(date)
            destination_folder = year_month_path.strip('/')
            
            logger.info(f"ファイル移動をスキップ: {file_path} -> {destination_folder}")
            return destination_folder
                
        except Exception as e:
            logger.error(f"ファイル移動エラー: {e}")
            return None
    
    def move_file_to_error_folder(self, file_path: str) -> Optional[str]:
        """
        エラーファイルをエラーフォルダに移動
        
        Args:
            file_path: ファイルパス
            
        Returns:
            Optional[str]: 移動先パス、失敗時はNone
        """
        try:
            if self.google_drive_client:
                # Google Driveに移動
                return self._move_file_in_google_drive(file_path, GOOGLE_DRIVE_ERROR_FOLDER)
            else:
                # ローカルファイルシステムに移動
                return self._move_file_locally(file_path, GOOGLE_DRIVE_ERROR_FOLDER)
                
        except Exception as e:
            logger.error(f"エラーファイル移動エラー: {e}")
            return None
    
    def _move_file_in_google_drive(self, file_path: str, destination_folder: str, file_id: str = None) -> Optional[str]:
        """
        Google Drive内でファイルを移動
        
        Args:
            file_path: ファイルパス
            destination_folder: 移動先フォルダ
            file_id: Google DriveファイルID（オプション）
            
        Returns:
            Optional[str]: 移動先パス、失敗時はNone
        """
        try:
            # ファイルIDを取得
            if not file_id:
                file_id = self._get_file_id_from_path(file_path)
                if not file_id:
                    logger.error(f"ファイルIDが見つかりません: {file_path}")
                    return None
            
            # 移動先フォルダIDを取得または作成
            destination_folder_id = self.google_drive_client.create_folder_structure(destination_folder)
            if not destination_folder_id:
                logger.error(f"移動先フォルダの作成に失敗: {destination_folder}")
                return None
            
            # ファイルを移動
            success = self.google_drive_client.move_file(file_id, destination_folder_id)
            if success:
                logger.info(f"Google Driveファイル移動完了: {file_path} -> {destination_folder}")
                return destination_folder
            else:
                logger.error(f"Google Driveファイル移動失敗: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Google Driveファイル移動エラー: {e}")
            return None
    
    def _move_file_locally(self, file_path: str, destination_folder: str) -> Optional[str]:
        """
        ローカルファイルシステムでファイルを移動
        
        Args:
            file_path: ファイルパス
            destination_folder: 移動先フォルダ
            
        Returns:
            Optional[str]: 移動先パス、失敗時はNone
        """
        try:
            # 移動先ディレクトリを作成
            os.makedirs(destination_folder, exist_ok=True)
            
            # ファイル名をサニタイズ
            filename = os.path.basename(file_path)
            safe_filename = sanitize_filename(filename)
            
            # 重複ファイル名の処理
            destination_path = os.path.join(destination_folder, safe_filename)
            destination_path = self._handle_duplicate_filename(destination_path)
            
            # ファイルを移動
            shutil.move(file_path, destination_path)
            
            logger.info(f"ローカルファイル移動完了: {file_path} -> {destination_path}")
            return destination_path
            
        except Exception as e:
            logger.error(f"ローカルファイル移動エラー: {e}")
            return None
    
    def _handle_duplicate_filename(self, file_path: str) -> str:
        """
        重複ファイル名を処理
        
        Args:
            file_path: ファイルパス
            
        Returns:
            str: 重複を回避したファイルパス
        """
        if not os.path.exists(file_path):
            return file_path
        
        # ファイル名と拡張子を分離
        base_path, ext = os.path.splitext(file_path)
        counter = 1
        
        # 重複しないファイル名を見つけるまでループ
        while os.path.exists(file_path):
            new_path = f"{base_path}_{counter}{ext}"
            file_path = new_path
            counter += 1
        
        return file_path
    
    def _get_file_id_from_path(self, file_path: str) -> Optional[str]:
        """
        ファイルパスからファイルIDを取得（簡易実装）
        
        Args:
            file_path: ファイルパス
            
        Returns:
            Optional[str]: ファイルID
        """
        # 実際の実装では、ファイルパスとファイルIDのマッピングを管理する必要があります
        # ここでは簡易的な実装として、ファイル名から推測します
        filename = os.path.basename(file_path)
        
        # ファイルIDのキャッシュやマッピングテーブルを実装する必要があります
        # 現在はNoneを返して、実際のファイルID管理は別途実装が必要です
        logger.warning(f"ファイルID取得機能は未実装です: {filename}")
        return None
    
    def _copy_to_inbox_processed(self, file_id: str) -> bool:
        """
        受信箱の処理済みフォルダにコピー
        
        Args:
            file_id: Google DriveファイルID
            
        Returns:
            bool: 成功時はTrue
        """
        try:
            # 受信箱の処理済みフォルダIDを取得または作成
            inbox_processed_folder = "受信箱/処理済み"
            destination_folder_id = self.google_drive_client.create_folder_structure(inbox_processed_folder)
            
            if destination_folder_id:
                # ファイルをコピー
                success = self.google_drive_client.copy_file(file_id, destination_folder_id)
                if success:
                    logger.info(f"受信箱処理済みフォルダにコピー完了: {file_id}")
                    return True
                else:
                    logger.error(f"受信箱処理済みフォルダへのコピー失敗: {file_id}")
                    return False
            else:
                logger.error(f"受信箱処理済みフォルダの作成失敗")
                return False
                
        except Exception as e:
            logger.error(f"受信箱処理済みフォルダコピーエラー: {e}")
            return False
    
    def create_backup(self, file_path: str, backup_dir: str) -> Optional[str]:
        """
        ファイルのバックアップを作成
        
        Args:
            file_path: ファイルパス
            backup_dir: バックアップディレクトリ
            
        Returns:
            Optional[str]: バックアップファイルパス、失敗時はNone
        """
        try:
            # バックアップディレクトリを作成
            os.makedirs(backup_dir, exist_ok=True)
            
            # バックアップファイル名を生成
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(file_path)
            backup_filename = f"{timestamp}_{filename}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # ファイルをコピー
            shutil.copy2(file_path, backup_path)
            
            logger.info(f"バックアップ作成完了: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"バックアップ作成エラー: {e}")
            return None
    
    def get_file_metadata(self, file_path: str) -> dict:
        """
        ファイルのメタデータを取得
        
        Args:
            file_path: ファイルパス
            
        Returns:
            dict: ファイルメタデータ
        """
        try:
            stat = os.stat(file_path)
            
            metadata = {
                'filename': os.path.basename(file_path),
                'file_size': stat.st_size,
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'file_type': self.get_file_type(file_path),
                'file_extension': os.path.splitext(file_path)[1].lower(),
                'absolute_path': os.path.abspath(file_path)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"ファイルメタデータ取得エラー: {e}")
            return {}
    
    def list_processed_files(self, base_dir: str, date: datetime) -> List[str]:
        """
        処理済みファイルのリストを取得
        
        Args:
            base_dir: ベースディレクトリ
            date: 日付
            
        Returns:
            List[str]: ファイルパスのリスト
        """
        try:
            year_month_path = get_year_month_folder_path(date)
            target_dir = os.path.join(base_dir, year_month_path.strip('/'))
            
            if not os.path.exists(target_dir):
                return []
            
            files = []
            for filename in os.listdir(target_dir):
                file_path = os.path.join(target_dir, filename)
                if os.path.isfile(file_path):
                    files.append(file_path)
            
            logger.info(f"処理済みファイル数: {len(files)}")
            return files
            
        except Exception as e:
            logger.error(f"処理済みファイルリスト取得エラー: {e}")
            return []
    
    def archive_old_files(self, base_dir: str, days_old: int = 365) -> int:
        """
        古いファイルをアーカイブ
        
        Args:
            base_dir: ベースディレクトリ
            days_old: アーカイブ対象の日数
            
        Returns:
            int: アーカイブされたファイル数
        """
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            archived_count = 0
            
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_stat = os.stat(file_path)
                    file_date = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_date < cutoff_date:
                        # アーカイブディレクトリに移動
                        archive_dir = os.path.join(base_dir, 'archive', file_date.strftime('%Y'))
                        os.makedirs(archive_dir, exist_ok=True)
                        
                        archive_path = os.path.join(archive_dir, file)
                        archive_path = self._handle_duplicate_filename(archive_path)
                        
                        shutil.move(file_path, archive_path)
                        archived_count += 1
                        logger.debug(f"ファイルアーカイブ: {file_path} -> {archive_path}")
            
            logger.info(f"アーカイブ完了: {archived_count}ファイル")
            return archived_count
            
        except Exception as e:
            logger.error(f"ファイルアーカイブエラー: {e}")
            return 0
