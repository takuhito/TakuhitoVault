"""
PDF処理機能
"""
import os
import structlog
from typing import List, Optional, Dict, Any
from PyPDF2 import PdfReader
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
import tempfile
import concurrent.futures
from datetime import datetime

from config.settings import MAX_PDF_PAGES

logger = structlog.get_logger()

class PDFProcessor:
    """PDF処理クラス"""
    
    def __init__(self):
        self.max_pages = MAX_PDF_PAGES
        self.max_workers = 4  # 並列処理のワーカー数
    
    def convert_pdf_to_images(self, pdf_path: str, output_dir: str = None) -> List[str]:
        """
        PDFを画像に変換
        
        Args:
            pdf_path: PDFファイルパス
            output_dir: 出力ディレクトリ（省略時は一時ディレクトリ）
            
        Returns:
            List[str]: 生成された画像ファイルパスのリスト
        """
        try:
            # PDFのページ数を確認
            page_count = self.get_pdf_page_count(pdf_path)
            if page_count > self.max_pages:
                logger.warning(f"PDFページ数が上限を超えています: {page_count} > {self.max_pages}")
                page_count = self.max_pages
            
            # 出力ディレクトリの設定
            if output_dir is None:
                output_dir = tempfile.mkdtemp()
            
            os.makedirs(output_dir, exist_ok=True)
            
            # 複数ページの場合は並列処理を使用
            if page_count > 1:
                return self._convert_pdf_to_images_parallel(pdf_path, output_dir, page_count)
            else:
                return self._convert_pdf_to_images_single(pdf_path, output_dir, page_count)
            
        except Exception as e:
            logger.error(f"PDF変換エラー: {e}")
            return []
    
    def _convert_pdf_to_images_single(self, pdf_path: str, output_dir: str, page_count: int) -> List[str]:
        """単一ページまたは逐次処理でのPDF変換"""
        try:
            # PDFを画像に変換
            images = convert_from_path(
                pdf_path,
                dpi=300,  # 高解像度で変換
                fmt='JPEG',
                output_folder=output_dir,
                output_file='page',
                first_page=1,
                last_page=page_count
            )
            
            # 生成された画像ファイルパスを取得
            image_paths = []
            for i, image in enumerate(images, 1):
                image_filename = f"page_{i:03d}.jpg"
                image_path = os.path.join(output_dir, image_filename)
                
                # 画像を保存
                image.save(image_path, 'JPEG', quality=95)
                image_paths.append(image_path)
                
                logger.info(f"PDFページ {i} を画像に変換: {image_path}")
            
            logger.info(f"PDF変換完了: {len(image_paths)}ページ")
            return image_paths
            
        except Exception as e:
            logger.error(f"PDF変換エラー: {e}")
            return []
    
    def _convert_pdf_to_images_parallel(self, pdf_path: str, output_dir: str, page_count: int) -> List[str]:
        """並列処理でのPDF変換（ページ単位）"""
        try:
            image_paths = []
            
            # 各ページを個別に並列処理
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_page = {
                    executor.submit(self._convert_single_page, pdf_path, output_dir, page_num): page_num
                    for page_num in range(1, page_count + 1)
                }
                
                for future in concurrent.futures.as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        page_path = future.result()
                        if page_path:
                            image_paths.append(page_path)
                            logger.info(f"ページ {page_num} 変換完了: {page_path}")
                    except Exception as e:
                        logger.error(f"ページ {page_num} 変換エラー: {e}")
            
            # ページ順にソート
            image_paths.sort(key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))
            
            logger.info(f"並列PDF変換完了: {len(image_paths)}ページ（期待値: {page_count}）")
            return image_paths
            
        except Exception as e:
            logger.error(f"並列PDF変換エラー: {e}")
            # 並列処理が失敗した場合は逐次処理にフォールバック
            logger.info("逐次処理にフォールバック")
            return self._convert_pdf_to_images_single(pdf_path, output_dir, page_count)
    
    def _convert_single_page(self, pdf_path: str, output_dir: str, page_num: int) -> Optional[str]:
        """単一ページを変換"""
        try:
            images = convert_from_path(
                pdf_path,
                dpi=300,
                fmt='JPEG',
                first_page=page_num,
                last_page=page_num
            )
            
            if images:
                image = images[0]  # 1ページのみなので最初の要素
                image_filename = f"page_{page_num:03d}.jpg"
                image_path = os.path.join(output_dir, image_filename)
                
                image.save(image_path, 'JPEG', quality=95)
                logger.debug(f"PDFページ {page_num} を画像に変換: {image_path}")
                return image_path
            else:
                logger.warning(f"ページ {page_num} の変換に失敗: 画像が生成されませんでした")
                return None
                
        except Exception as e:
            logger.error(f"ページ {page_num} 変換エラー: {e}")
            return None
    
    def _convert_pdf_chunk(self, pdf_path: str, output_dir: str, start_page: int, end_page: int) -> List[str]:
        """PDFの特定範囲のページを変換"""
        try:
            images = convert_from_path(
                pdf_path,
                dpi=300,
                fmt='JPEG',
                output_folder=output_dir,
                output_file='page',
                first_page=start_page,
                last_page=end_page
            )
            
            image_paths = []
            for i, image in enumerate(images, start_page):
                image_filename = f"page_{i:03d}.jpg"
                image_path = os.path.join(output_dir, image_filename)
                
                image.save(image_path, 'JPEG', quality=95)
                image_paths.append(image_path)
                
                logger.debug(f"PDFページ {i} を画像に変換: {image_path}")
            
            return image_paths
            
        except Exception as e:
            logger.error(f"チャンク変換エラー (ページ {start_page}-{end_page}): {e}")
            return []
    
    def convert_pdf_bytes_to_images(self, pdf_bytes: bytes, output_dir: str = None) -> List[str]:
        """
        PDFバイトデータを画像に変換
        
        Args:
            pdf_bytes: PDFのバイトデータ
            output_dir: 出力ディレクトリ（省略時は一時ディレクトリ）
            
        Returns:
            List[str]: 生成された画像ファイルパスのリスト
        """
        try:
            # 出力ディレクトリの設定
            if output_dir is None:
                output_dir = tempfile.mkdtemp()
            
            os.makedirs(output_dir, exist_ok=True)
            
            # PDFを画像に変換
            images = convert_from_bytes(
                pdf_bytes,
                dpi=300,  # 高解像度で変換
                fmt='JPEG',
                output_folder=output_dir,
                output_file='page'
            )
            
            # ページ数制限を適用
            if len(images) > self.max_pages:
                logger.warning(f"PDFページ数が上限を超えています: {len(images)} > {self.max_pages}")
                images = images[:self.max_pages]
            
            # 生成された画像ファイルパスを取得
            image_paths = []
            for i, image in enumerate(images, 1):
                image_filename = f"page_{i:03d}.jpg"
                image_path = os.path.join(output_dir, image_filename)
                
                # 画像を保存
                image.save(image_path, 'JPEG', quality=95)
                image_paths.append(image_path)
                
                logger.info(f"PDFページ {i} を画像に変換: {image_path}")
            
            logger.info(f"PDF変換完了: {len(image_paths)}ページ")
            return image_paths
            
        except Exception as e:
            logger.error(f"PDF変換エラー: {e}")
            return []
    
    def get_pdf_page_count(self, pdf_path: str) -> int:
        """
        PDFのページ数を取得
        
        Args:
            pdf_path: PDFファイルパス
            
        Returns:
            int: ページ数
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                page_count = len(reader.pages)
                logger.info(f"PDFページ数: {page_count}")
                return page_count
                
        except Exception as e:
            logger.error(f"PDFページ数取得エラー: {e}")
            return 0
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        PDFのページ数を取得
        
        Args:
            pdf_path: PDFファイルパス
            
        Returns:
            int: ページ数
        """
        try:
            from PyPDF2 import PdfReader
            
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                page_count = len(reader.pages)
                logger.info(f"PDFページ数取得: {pdf_path}, ページ数: {page_count}")
                return page_count
                
        except Exception as e:
            logger.error(f"PDFページ数取得エラー: {pdf_path}, {e}")
            return 0
    
    def get_pdf_metadata(self, pdf_path: str) -> Optional[dict]:
        """
        PDFのメタデータを取得
        
        Args:
            pdf_path: PDFファイルパス
            
        Returns:
            Optional[dict]: メタデータ、失敗時はNone
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                metadata = reader.metadata
                
                if metadata:
                    # メタデータを辞書形式に変換
                    result = {}
                    for key, value in metadata.items():
                        if value:
                            # バイト文字列の場合はデコード
                            if isinstance(value, bytes):
                                try:
                                    result[key] = value.decode('utf-8')
                                except UnicodeDecodeError:
                                    result[key] = str(value)
                            else:
                                result[key] = str(value)
                    
                    logger.info(f"PDFメタデータ取得完了: {len(result)}項目")
                    return result
                else:
                    logger.warning("PDFメタデータが見つかりませんでした")
                    return None
                    
        except Exception as e:
            logger.error(f"PDFメタデータ取得エラー: {e}")
            return None
    
    def validate_pdf(self, pdf_path: str) -> bool:
        """
        PDFファイルの妥当性をチェック
        
        Args:
            pdf_path: PDFファイルパス
            
        Returns:
            bool: 妥当な場合はTrue
        """
        try:
            # ファイルの存在確認
            if not os.path.exists(pdf_path):
                logger.error(f"PDFファイルが存在しません: {pdf_path}")
                return False
            
            # ファイルサイズの確認
            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                logger.error(f"PDFファイルが空です: {pdf_path}")
                return False
            
            # 最小サイズチェック（PDFヘッダー + 最小コンテンツ）
            if file_size < 100:
                logger.error(f"PDFファイルが小さすぎます: {pdf_path}, サイズ: {file_size} bytes")
                return False
            
            # PDFヘッダーの確認
            with open(pdf_path, 'rb') as file:
                header = file.read(8)  # より多くのバイトを読み取り
                if not header.startswith(b'%PDF'):
                    logger.error(f"PDFヘッダーが不正です: {pdf_path}, ヘッダー: {header}")
                    return False
                
                # PDFバージョンの確認
                try:
                    version_str = header[4:8].decode('ascii')
                    version = float(version_str)
                    if version < 1.0 or version > 2.0:
                        logger.warning(f"PDFバージョンが非標準です: {pdf_path}, バージョン: {version}")
                except (ValueError, UnicodeDecodeError):
                    logger.warning(f"PDFバージョンの解析に失敗: {pdf_path}")
            
            # PDFリーダーで開けるかテスト
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                page_count = len(reader.pages)
                if page_count == 0:
                    logger.error(f"PDFにページがありません: {pdf_path}")
                    return False
                
                # 暗号化チェック
                if reader.is_encrypted:
                    logger.error(f"PDFが暗号化されています: {pdf_path}")
                    return False
                
                # 破損チェック（最初のページを読み取りテスト）
                try:
                    first_page = reader.pages[0]
                    # ページの基本情報を取得してテスト
                    if hasattr(first_page, 'mediabox'):
                        mediabox = first_page.mediabox
                        if mediabox.width <= 0 or mediabox.height <= 0:
                            logger.warning(f"PDFページサイズが不正です: {pdf_path}")
                except Exception as e:
                    logger.error(f"PDFページの読み取りに失敗: {pdf_path}, エラー: {e}")
                    return False
            
            logger.info(f"PDF妥当性チェック完了: {pdf_path}, ページ数: {page_count}")
            return True
            
        except Exception as e:
            logger.error(f"PDF妥当性チェックエラー: {pdf_path}, エラー: {e}")
            return False
    
    def handle_pdf_conversion_error(self, pdf_path: str, error: Exception) -> Dict[str, Any]:
        """
        PDF変換エラーの詳細分析と対処法の提案
        
        Args:
            pdf_path: PDFファイルパス
            error: 発生したエラー
            
        Returns:
            Dict[str, Any]: エラー分析結果と対処法
        """
        error_info = {
            'file_path': pdf_path,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'suggestions': []
        }
        
        # エラータイプに基づく対処法の提案
        if 'Permission' in str(error) or 'access' in str(error).lower():
            error_info['suggestions'].append("ファイルのアクセス権限を確認してください")
            error_info['suggestions'].append("ファイルが他のプロセスで使用されていないか確認してください")
        
        elif 'corrupt' in str(error).lower() or 'damaged' in str(error).lower():
            error_info['suggestions'].append("PDFファイルが破損している可能性があります")
            error_info['suggestions'].append("元のファイルから再ダウンロードしてください")
        
        elif 'encrypted' in str(error).lower() or 'password' in str(error).lower():
            error_info['suggestions'].append("PDFが暗号化されています")
            error_info['suggestions'].append("パスワードを解除してから処理してください")
        
        elif 'memory' in str(error).lower() or 'out of memory' in str(error).lower():
            error_info['suggestions'].append("メモリ不足の可能性があります")
            error_info['suggestions'].append("PDFのページ数を減らすか、画像解像度を下げてください")
        
        elif 'timeout' in str(error).lower():
            error_info['suggestions'].append("処理がタイムアウトしました")
            error_info['suggestions'].append("PDFのサイズを小さくするか、ページ数を減らしてください")
        
        else:
            error_info['suggestions'].append("一般的なPDF処理エラーです")
            error_info['suggestions'].append("ファイル形式を確認してください")
            error_info['suggestions'].append("別のPDFビューアでファイルを開いて確認してください")
        
        logger.error(f"PDF変換エラー分析: {error_info}")
        return error_info
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDFファイルの詳細情報を取得
        
        Args:
            pdf_path: PDFファイルパス
            
        Returns:
            Dict[str, Any]: PDF情報
        """
        try:
            info = {
                'file_path': pdf_path,
                'file_size': 0,
                'page_count': 0,
                'is_encrypted': False,
                'pdf_version': None,
                'metadata': None,
                'error': None
            }
            
            # ファイルサイズ
            if os.path.exists(pdf_path):
                info['file_size'] = os.path.getsize(pdf_path)
            
            # PDF情報
            with open(pdf_path, 'rb') as file:
                # バージョン情報
                header = file.read(8)
                if header.startswith(b'%PDF'):
                    try:
                        version_str = header[4:8].decode('ascii')
                        info['pdf_version'] = float(version_str)
                    except (ValueError, UnicodeDecodeError):
                        info['pdf_version'] = 'unknown'
                
                # PDFリーダーで詳細情報を取得
                file.seek(0)
                reader = PdfReader(file)
                
                info['page_count'] = len(reader.pages)
                info['is_encrypted'] = reader.is_encrypted
                
                # メタデータ
                if reader.metadata:
                    info['metadata'] = {}
                    for key, value in reader.metadata.items():
                        if value:
                            if isinstance(value, bytes):
                                try:
                                    info['metadata'][key] = value.decode('utf-8')
                                except UnicodeDecodeError:
                                    info['metadata'][key] = str(value)
                            else:
                                info['metadata'][key] = str(value)
            
            logger.info(f"PDF情報取得完了: {pdf_path}")
            return info
            
        except Exception as e:
            info['error'] = str(e)
            logger.error(f"PDF情報取得エラー: {pdf_path}, エラー: {e}")
            return info
    
    def optimize_image(self, image_path: str, max_width: int = 1920, max_height: int = 1080) -> bool:
        """
        画像を最適化（リサイズ・圧縮）
        
        Args:
            image_path: 画像ファイルパス
            max_width: 最大幅
            max_height: 最大高さ
            
        Returns:
            bool: 成功時はTrue
        """
        try:
            with Image.open(image_path) as img:
                # 現在のサイズを取得
                width, height = img.size
                
                # リサイズが必要かチェック
                if width > max_width or height > max_height:
                    # アスペクト比を保持してリサイズ
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    
                    # 最適化された画像を保存
                    img.save(image_path, 'JPEG', quality=85, optimize=True)
                    logger.info(f"画像最適化完了: {image_path}")
                else:
                    logger.info(f"画像最適化不要: {image_path}")
                
                return True
                
        except Exception as e:
            logger.error(f"画像最適化エラー: {e}")
            return False
    
    def optimize_images_batch(self, image_paths: List[str], max_width: int = 1920, max_height: int = 1080) -> Dict[str, bool]:
        """
        複数画像の一括最適化
        
        Args:
            image_paths: 画像ファイルパスのリスト
            max_width: 最大幅
            max_height: 最大高さ
            
        Returns:
            Dict[str, bool]: 各画像の最適化結果
        """
        results = {}
        
        # 並列処理で画像を最適化
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(self.optimize_image, path, max_width, max_height): path
                for path in image_paths
            }
            
            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    results[path] = result
                except Exception as e:
                    logger.error(f"画像最適化エラー: {path}, {e}")
                    results[path] = False
        
        success_count = sum(1 for result in results.values() if result)
        logger.info(f"画像一括最適化完了: {success_count}/{len(image_paths)}成功")
        
        return results
    
    def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """
        一時ファイルを削除
        
        Args:
            file_paths: 削除するファイルパスのリスト
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"一時ファイル削除: {file_path}")
            except Exception as e:
                logger.warning(f"一時ファイル削除エラー: {file_path}, {e}")
    
    def merge_images_to_pdf(self, image_paths: List[str], output_path: str) -> bool:
        """
        複数の画像をPDFに結合
        
        Args:
            image_paths: 画像ファイルパスのリスト
            output_path: 出力PDFパス
            
        Returns:
            bool: 成功時はTrue
        """
        try:
            images = []
            for image_path in image_paths:
                if os.path.exists(image_path):
                    image = Image.open(image_path)
                    # RGBに変換（RGBAの場合は背景を白に）
                    if image.mode == 'RGBA':
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        background.paste(image, mask=image.split()[-1])
                        images.append(background)
                    else:
                        images.append(image.convert('RGB'))
            
            if images:
                # 最初の画像をベースにしてPDFを作成
                images[0].save(
                    output_path,
                    'PDF',
                    save_all=True,
                    append_images=images[1:],
                    resolution=300.0
                )
                
                logger.info(f"画像PDF結合完了: {output_path}")
                return True
            else:
                logger.error("結合する画像がありません")
                return False
                
        except Exception as e:
            logger.error(f"画像PDF結合エラー: {e}")
            return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        処理統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        return {
            'max_pages': self.max_pages,
            'max_workers': self.max_workers,
            'timestamp': datetime.now().isoformat()
        }
