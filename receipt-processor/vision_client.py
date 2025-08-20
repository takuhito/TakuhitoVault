"""
Google Cloud Vision API クライアント
"""
import os
import structlog
from typing import Dict, List, Optional
from google.cloud import vision
from google.oauth2 import service_account

from config.settings import GOOGLE_CLOUD_CREDENTIALS_FILE

logger = structlog.get_logger()

class VisionClient:
    """Google Cloud Vision API クライアント"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Vision APIクライアントの初期化"""
        try:
            if GOOGLE_CLOUD_CREDENTIALS_FILE and os.path.exists(GOOGLE_CLOUD_CREDENTIALS_FILE):
                credentials = service_account.Credentials.from_service_account_file(
                    GOOGLE_CLOUD_CREDENTIALS_FILE
                )
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
            else:
                # デフォルトの認証情報を使用
                self.client = vision.ImageAnnotatorClient()
            
            logger.info("Google Cloud Vision API クライアント初期化完了")
            
        except Exception as e:
            logger.error(f"Vision API クライアント初期化エラー: {e}")
            raise
    
    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        画像からテキストを抽出（OCR）
        
        Args:
            image_path: 画像ファイルパス
            
        Returns:
            Optional[str]: 抽出されたテキスト、失敗時はNone
        """
        try:
            # 画像ファイルを読み込み
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            # Vision APIリクエストを作成
            image = vision.Image(content=content)
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                logger.error(f"Vision API エラー: {response.error.message}")
                return None
            
            # テキストを抽出
            texts = response.text_annotations
            if texts:
                extracted_text = texts[0].description
                logger.info(f"テキスト抽出完了: {len(extracted_text)}文字")
                return extracted_text
            else:
                logger.warning("テキストが見つかりませんでした")
                return None
                
        except Exception as e:
            logger.error(f"テキスト抽出エラー: {e}")
            return None
    
    def extract_text_from_bytes(self, image_bytes: bytes) -> Optional[str]:
        """
        画像バイトデータからテキストを抽出（OCR）
        
        Args:
            image_bytes: 画像のバイトデータ
            
        Returns:
            Optional[str]: 抽出されたテキスト、失敗時はNone
        """
        try:
            # Vision APIリクエストを作成
            image = vision.Image(content=image_bytes)
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                logger.error(f"Vision API エラー: {response.error.message}")
                return None
            
            # テキストを抽出
            texts = response.text_annotations
            if texts:
                extracted_text = texts[0].description
                logger.info(f"テキスト抽出完了: {len(extracted_text)}文字")
                return extracted_text
            else:
                logger.warning("テキストが見つかりませんでした")
                return None
                
        except Exception as e:
            logger.error(f"テキスト抽出エラー: {e}")
            return None
    
    def detect_document_text(self, image_path: str) -> Optional[Dict]:
        """
        文書テキスト検出（より高精度なOCR）
        
        Args:
            image_path: 画像ファイルパス
            
        Returns:
            Optional[Dict]: 検出結果、失敗時はNone
        """
        try:
            # 画像ファイルを読み込み
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            # Vision APIリクエストを作成
            image = vision.Image(content=content)
            response = self.client.document_text_detection(image=image)
            
            if response.error.message:
                logger.error(f"Vision API エラー: {response.error.message}")
                return None
            
            # 結果を解析
            document = response.full_text_annotation
            
            if document:
                # テキストとページ情報を抽出
                result = {
                    'text': document.text,
                    'pages': []
                }
                
                for page in document.pages:
                    page_info = {
                        'width': page.width,
                        'height': page.height,
                        'blocks': []
                    }
                    
                    for block in page.blocks:
                        block_info = {
                            'confidence': block.confidence,
                            'text': ''
                        }
                        
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                word_text = ''.join([
                                    symbol.text for symbol in word.symbols
                                ])
                                block_info['text'] += word_text
                        
                        page_info['blocks'].append(block_info)
                    
                    result['pages'].append(page_info)
                
                logger.info(f"文書テキスト検出完了: {len(result['text'])}文字")
                return result
            else:
                logger.warning("文書テキストが見つかりませんでした")
                return None
                
        except Exception as e:
            logger.error(f"文書テキスト検出エラー: {e}")
            return None
    
    def detect_text_with_bounds(self, image_path: str) -> Optional[List[Dict]]:
        """
        テキストとその位置情報を検出
        
        Args:
            image_path: 画像ファイルパス
            
        Returns:
            Optional[List[Dict]]: テキストと位置情報のリスト、失敗時はNone
        """
        try:
            # 画像ファイルを読み込み
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            # Vision APIリクエストを作成
            image = vision.Image(content=content)
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                logger.error(f"Vision API エラー: {response.error.message}")
                return None
            
            # テキストと位置情報を抽出
            text_annotations = response.text_annotations[1:]  # 最初の要素は全体のテキスト
            
            results = []
            for text in text_annotations:
                vertices = []
                for vertex in text.bounding_poly.vertices:
                    vertices.append({
                        'x': vertex.x,
                        'y': vertex.y
                    })
                
                results.append({
                    'text': text.description,
                    'confidence': getattr(text, 'confidence', 0.0),
                    'bounds': vertices
                })
            
            logger.info(f"テキスト位置情報検出完了: {len(results)}個のテキスト要素")
            return results
            
        except Exception as e:
            logger.error(f"テキスト位置情報検出エラー: {e}")
            return None
    
    def analyze_image_properties(self, image_path: str) -> Optional[Dict]:
        """
        画像のプロパティを分析
        
        Args:
            image_path: 画像ファイルパス
            
        Returns:
            Optional[Dict]: 画像プロパティ、失敗時はNone
        """
        try:
            # 画像ファイルを読み込み
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            # Vision APIリクエストを作成
            image = vision.Image(content=content)
            response = self.client.image_properties(image=image)
            
            if response.error.message:
                logger.error(f"Vision API エラー: {response.error.message}")
                return None
            
            # プロパティを解析
            properties = response.image_properties_annotation
            
            if properties:
                # 主要な色を抽出
                dominant_colors = []
                for color_info in properties.dominant_colors.colors:
                    color = color_info.color
                    dominant_colors.append({
                        'red': color.red,
                        'green': color.green,
                        'blue': color.blue,
                        'alpha': color.alpha,
                        'score': color_info.score,
                        'pixel_fraction': color_info.pixel_fraction
                    })
                
                result = {
                    'dominant_colors': dominant_colors
                }
                
                logger.info(f"画像プロパティ分析完了: {len(dominant_colors)}個の主要色")
                return result
            else:
                logger.warning("画像プロパティが見つかりませんでした")
                return None
                
        except Exception as e:
            logger.error(f"画像プロパティ分析エラー: {e}")
            return None

