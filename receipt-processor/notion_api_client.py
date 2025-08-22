"""
Notion API クライアント
"""
import os
import structlog
from typing import Dict, List, Optional, Any
from notion_client import Client
from notion_client.errors import APIResponseError

from config.settings import NOTION_TOKEN, NOTION_DATABASE_ID

logger = structlog.get_logger()

class NotionClient:
    """Notion API クライアント"""
    
    def __init__(self):
        self.client = None
        self.database_id = NOTION_DATABASE_ID
        self._initialize_client()
    
    def _initialize_client(self):
        """Notion APIクライアントの初期化"""
        try:
            if not NOTION_TOKEN:
                raise ValueError("NOTION_TOKENが設定されていません")
            
            self.client = Client(auth=NOTION_TOKEN)
            logger.info("Notion API クライアント初期化完了")
            
        except Exception as e:
            logger.error(f"Notion API クライアント初期化エラー: {e}")
            raise
    
    def create_receipt_page(self, receipt_data: Dict[str, Any], image_path: str = None) -> Optional[str]:
        """
        領収書ページを作成
        
        Args:
            receipt_data: 領収書データ
            image_path: 画像ファイルパス（オプション）
            
        Returns:
            Optional[str]: 作成されたページID、失敗時はNone
        """
        try:
            # プロパティの構築
            properties = self._build_page_properties(receipt_data)
            
            # ページ作成リクエスト
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties
            }
            
            # Google Driveリンクを本文に追加
            if image_path and os.path.exists(image_path):
                filename = os.path.basename(image_path)
                
                # JPGファイルをGoogle Driveにアップロード（改良版）
                try:
                    from google_drive_client import GoogleDriveClient
                    from utils import get_year_month_folder_path
                    from datetime import datetime
                    drive_client = GoogleDriveClient()
                    
                    # 年度・月度フォルダにアップロード
                    year_month_path = get_year_month_folder_path(receipt_data.get('date', datetime.now()))
                    destination_folder = year_month_path.strip('/')
                    
                    # フォルダIDを取得または作成
                    folder_id = drive_client.create_folder_structure(destination_folder)
                    
                    if folder_id:
                        # JPGファイルをアップロード（共有ドライブ対応）
                        uploaded_file_id = drive_client.upload_file(image_path, folder_id, filename, use_shared_drive=True)
                        
                        if uploaded_file_id:
                            drive_link = f"https://drive.google.com/file/d/{uploaded_file_id}/view"
                            # 本文にリンクを追加
                            page_data["children"] = [
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {
                                                    "content": f"📎 領収書画像: ",
                                                    "link": None
                                                }
                                            },
                                            {
                                                "type": "text",
                                                "text": {
                                                    "content": filename,
                                                    "link": {
                                                        "url": drive_link
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                            logger.info(f"JPGファイルをアップロードしてリンクを追加: {filename} -> {uploaded_file_id}")
                        else:
                            # アップロード失敗時は元のPDFファイルのリンクにフォールバック
                            original_file_id = receipt_data.get('original_file_id')
                            if original_file_id:
                                page_number = filename.replace('page_', '').replace('.jpg', '')
                                drive_link = f"https://drive.google.com/file/d/{original_file_id}/view"
                                
                                page_data["children"] = [
                                    {
                                        "object": "block",
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "type": "text",
                                                    "text": {
                                                        "content": f"📎 PDFファイル（{page_number}ページ目）: ",
                                                        "link": None
                                                    }
                                                },
                                                {
                                                    "type": "text",
                                                    "text": {
                                                        "content": "元のPDFファイル",
                                                        "link": {
                                                            "url": drive_link
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                                logger.info(f"JPGアップロード失敗、PDFリンクにフォールバック: {filename}")
                            else:
                                # 最後の手段：ファイル名のみ
                                page_data["children"] = [
                                    {
                                        "object": "block",
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "type": "text",
                                                    "text": {
                                                        "content": f"📎 画像ファイル: {filename} (アップロード失敗)",
                                                        "link": None
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                    else:
                        logger.error(f"フォルダIDの取得に失敗: {destination_folder}")
                        # フォルダ作成失敗時はファイル名のみ
                        page_data["children"] = [
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {
                                                "content": f"📎 画像ファイル: {filename} (フォルダ作成失敗)",
                                                "link": None
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                        
                except Exception as e:
                    logger.error(f"JPGファイルアップロードエラー: {e}")
                    # エラー時は元のPDFファイルのリンクにフォールバック
                    try:
                        original_file_id = receipt_data.get('original_file_id')
                        if original_file_id:
                            page_number = filename.replace('page_', '').replace('.jpg', '')
                            drive_link = f"https://drive.google.com/file/d/{original_file_id}/view"
                            
                            page_data["children"] = [
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {
                                                    "content": f"📎 PDFファイル（{page_number}ページ目）: ",
                                                    "link": None
                                                }
                                            },
                                            {
                                                "type": "text",
                                                "text": {
                                                    "content": "元のPDFファイル",
                                                    "link": {
                                                        "url": drive_link
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                            logger.info(f"エラー時PDFリンクフォールバック: {filename}")
                        else:
                            # 最後の手段：ファイル名のみ
                            page_data["children"] = [
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {
                                                    "content": f"📎 画像ファイル: {filename} (エラー)",
                                                    "link": None
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                    except:
                        # 完全なフォールバック
                        page_data["children"] = [
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {
                                                "content": f"📎 画像ファイル: {filename}",
                                                "link": None
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
            
            # ファイルがある場合は追加（従来の方法）
            elif 'file_path' in receipt_data and receipt_data['file_path']:
                page_data["children"] = self._build_file_block(receipt_data['file_path'])
            
            response = self.client.pages.create(**page_data)
            page_id = response["id"]
            
            logger.info(f"領収書ページ作成完了: {page_id}")
            return page_id
            
        except APIResponseError as e:
            logger.error(f"Notion API エラー: {e}")
            return None
        except Exception as e:
            logger.error(f"ページ作成エラー: {e}")
            return None
    
    def _build_page_properties(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ページプロパティを構築
        
        Args:
            receipt_data: 領収書データ
            
        Returns:
            Dict[str, Any]: Notionページプロパティ
        """
        properties = {}
        
        # タイトル
        if 'title' in receipt_data:
            properties["タイトル"] = {
                "title": [
                    {
                        "text": {
                            "content": receipt_data['title']
                        }
                    }
                ]
            }
        
        # 発生日
        if 'date' in receipt_data and receipt_data['date']:
            try:
                # 日付が文字列の場合はdatetimeオブジェクトに変換
                if isinstance(receipt_data['date'], str):
                    from datetime import datetime
                    date_obj = datetime.strptime(receipt_data['date'], '%Y-%m-%d')
                else:
                    date_obj = receipt_data['date']
                
                properties["発生日"] = {
                    "date": {
                        "start": date_obj.strftime('%Y-%m-%d')
                    }
                }
            except Exception as e:
                logger.warning(f"日付処理エラー: {receipt_data['date']}, {e}")
                # 日付処理に失敗した場合は現在の日付を使用
                from datetime import datetime
            properties["発生日"] = {
                "date": {
                        "start": datetime.now().strftime('%Y-%m-%d')
                }
            }
        
        # 店舗名
        if 'store_name' in receipt_data:
            properties["店舗名"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": receipt_data['store_name']
                        }
                    }
                ]
            }
        
        # 合計金額
        if 'total_amount' in receipt_data and receipt_data['total_amount']:
            properties["合計金額"] = {
                "number": float(receipt_data['total_amount'])
            }
        
        # 税抜金額
        if 'amount_without_tax' in receipt_data and receipt_data['amount_without_tax']:
            properties["税抜金額"] = {
                "number": float(receipt_data['amount_without_tax'])
            }
        
        # 消費税
        if 'tax_amount' in receipt_data and receipt_data['tax_amount']:
            properties["消費税"] = {
                "number": float(receipt_data['tax_amount'])
            }
        
        # 支払方法
        if 'payment_method' in receipt_data and receipt_data['payment_method']:
            # 支払い方法の値を検証
            valid_payment_methods = ['現金', 'クレジットカード', '電子マネー', 'その他']
            payment_method = receipt_data['payment_method']
            
            # 有効な支払い方法かチェック
            if payment_method in valid_payment_methods:
            properties["支払方法"] = {
                "select": {
                        "name": payment_method
                    }
                }
            else:
                # 無効な場合は「その他」に設定
                properties["支払方法"] = {
                    "select": {
                        "name": "その他"
                }
            }
        
        # カテゴリ
        if 'category' in receipt_data:
            properties["カテゴリ"] = {
                "multi_select": [
                    {
                        "name": receipt_data['category']
                    }
                ]
            }
        
        # 勘定科目
        if 'account' in receipt_data:
            properties["勘定科目"] = {
                "select": {
                    "name": receipt_data['account']
                }
            }
        
        # 備考
        if 'notes' in receipt_data:
            properties["備考"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": receipt_data['notes']
                        }
                    }
                ]
            }
        
        # 処理状況
        processing_status = receipt_data.get('processing_status', '未処理')
        properties["処理状況"] = {
            "select": {
                "name": processing_status
            }
        }
        
        # ページ数（PDFの場合）
        if 'page_number' in receipt_data:
            properties["ページ数"] = {
                "number": receipt_data['page_number']
            }
        
        # 処理メモ
        if 'processing_notes' in receipt_data:
            properties["処理メモ"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": receipt_data['processing_notes']
                        }
                    }
                ]
            }
        
        return properties
    
    def get_database_info(self) -> Dict[str, Any]:
        """データベース情報を取得"""
        try:
            response = self.client.databases.retrieve(database_id=self.database_id)
            return response
        except Exception as e:
            logger.error(f"データベース情報取得エラー: {e}")
            raise
    
    def create_receipt_record(self, receipt_data: Dict[str, Any], image_path: str = None) -> Optional[str]:
        """領収書レコードを作成（新しいプロパティ構造用）"""
        try:
            properties = self._build_receipt_properties(receipt_data)
            
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties
            }
            
            # 画像がある場合は添付
            if image_path and os.path.exists(image_path):
                try:
                    # 画像をNotionにアップロード
                    image_url = self._upload_image_to_notion(image_path)
                    if image_url:
                        page_data["children"] = [
                            {
                                "object": "block",
                                "type": "image",
                                "image": {
                                    "type": "external",
                                    "external": {
                                        "url": image_url
                                    }
                                }
                            }
                        ]
                        logger.info(f"画像添付準備完了: {image_path}")
                except Exception as e:
                    logger.warning(f"画像添付エラー: {e}")
            
            response = self.client.pages.create(**page_data)
            page_id = response["id"]
            
            logger.info(f"領収書レコード作成完了: {page_id}")
            return page_id
            
        except Exception as e:
            logger.error(f"レコード作成エラー: {e}")
            return None
    
    def _build_receipt_properties(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """既存のデータベース構造に適応したプロパティを構築"""
        properties = {}
        
        # タイトル（店舗名）
        if 'store_name' in receipt_data:
            properties["タイトル"] = {
                "title": [
                    {
                        "text": {
                            "content": receipt_data['store_name']
                        }
                    }
                ]
            }
        
        # 発生日（日付）
        if 'date' in receipt_data and receipt_data['date']:
            properties["発生日"] = {
                "date": {
                    "start": receipt_data['date'].strftime('%Y-%m-%d')
                }
            }
        
        # 合計金額
        if 'total_amount' in receipt_data and receipt_data['total_amount']:
            properties["合計金額"] = {
                "number": float(receipt_data['total_amount'])
            }
        
        # カテゴリ（multi_select）
        if 'category' in receipt_data:
            properties["カテゴリ"] = {
                "multi_select": [
                    {
                        "name": receipt_data['category']
                    }
                ]
            }
        
        # 勘定科目
        if 'account_item' in receipt_data:
            properties["勘定科目"] = {
                "select": {
                    "name": receipt_data['account_item']
                }
            }
        
        # 備考（商品一覧として使用）
        if 'items' in receipt_data:
            properties["備考"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": receipt_data['items']
                        }
                    }
                ]
            }
        
        # 処理状況
        processing_status = receipt_data.get('processing_status', '未処理')
        properties["処理状況"] = {
            "select": {
                "name": processing_status
            }
        }
        
        # 処理メモ（信頼度として使用）
        if 'confidence_score' in receipt_data:
            properties["処理メモ"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": f"信頼度: {receipt_data['confidence_score']:.2f}"
                        }
                    }
                ]
            }
        
        return properties
    
    def _upload_image_to_notion(self, image_path: str) -> Optional[str]:
        """画像をNotionにアップロード（圧縮版）"""
        try:
            from PIL import Image
            import io
            
            # 画像を開いて圧縮
            with Image.open(image_path) as img:
                # RGBに変換（RGBAの場合は背景を白に）
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # サイズを制限（最大800x800）
                max_size = (800, 800)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # 圧縮してJPEGとして保存
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=60, optimize=True)
                compressed_data = buffer.getvalue()
            
            # ファイル名を取得
            filename = os.path.basename(image_path)
            
            # base64エンコード
            import base64
            base64_data = base64.b64encode(compressed_data).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{base64_data}"
            
            logger.info(f"画像アップロード完了（圧縮版）: {filename}, サイズ: {len(compressed_data)} bytes")
            return data_uri
            
        except Exception as e:
            logger.error(f"画像アップロードエラー: {e}")
            return None
    
    def delete_page(self, page_id: str) -> bool:
        """ページを削除"""
        try:
            self.client.pages.update(page_id, archived=True)
            logger.info(f"ページ削除完了: {page_id}")
            return True
        except Exception as e:
            logger.error(f"ページ削除エラー: {e}")
            return False
    
    def _build_file_block(self, file_path: str) -> List[Dict[str, Any]]:
        """
        ファイルブロックを構築
        
        Args:
            file_path: ファイルパス
            
        Returns:
            List[Dict[str, Any]]: ファイルブロックのリスト
        """
        # 現在のNotion APIでは、ファイルの直接アップロードは
        # 外部URLまたはNotion内のファイルIDが必要です
        # ここでは外部ファイルとして扱います
        
        return [
            {
                "object": "block",
                "type": "file",
                "file": {
                    "type": "external",
                    "external": {
                        "url": f"file://{file_path}"  # 実際の運用では適切なURLに変更
                    }
                }
            }
        ]
    
    def update_page(self, page_id: str, properties: Dict[str, Any]) -> bool:
        """
        ページを更新
        
        Args:
            page_id: ページID
            properties: 更新するプロパティ
            
        Returns:
            bool: 成功時はTrue
        """
        try:
            self.client.pages.update(page_id=page_id, properties=properties)
            logger.info(f"ページ更新完了: {page_id}")
            return True
            
        except APIResponseError as e:
            logger.error(f"Notion API エラー: {e}")
            return False
        except Exception as e:
            logger.error(f"ページ更新エラー: {e}")
            return False
    
    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        ページを取得
        
        Args:
            page_id: ページID
            
        Returns:
            Optional[Dict[str, Any]]: ページデータ、失敗時はNone
        """
        try:
            response = self.client.pages.retrieve(page_id=page_id)
            return response
            
        except APIResponseError as e:
            logger.error(f"Notion API エラー: {e}")
            return None
        except Exception as e:
            logger.error(f"ページ取得エラー: {e}")
            return None
    
    def query_database(self, filter_criteria: Optional[Dict] = None, 
                      sort_criteria: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        """
        データベースをクエリ
        
        Args:
            filter_criteria: フィルタ条件
            sort_criteria: ソート条件
            
        Returns:
            List[Dict[str, Any]]: 検索結果
        """
        try:
            query_params = {}
            
            if filter_criteria:
                query_params["filter"] = filter_criteria
            
            if sort_criteria:
                query_params["sorts"] = sort_criteria
            
            response = self.client.databases.query(
                database_id=self.database_id,
                **query_params
            )
            
            results = response.get("results", [])
            logger.info(f"データベースクエリ完了: {len(results)}件")
            
            return results
            
        except APIResponseError as e:
            logger.error(f"Notion API エラー: {e}")
            return []
        except Exception as e:
            logger.error(f"データベースクエリエラー: {e}")
            return []
    
    def get_database_schema(self) -> Optional[Dict[str, Any]]:
        """
        データベースのスキーマを取得
        
        Returns:
            Optional[Dict[str, Any]]: データベーススキーマ、失敗時はNone
        """
        try:
            response = self.client.databases.retrieve(database_id=self.database_id)
            return response
            
        except APIResponseError as e:
            logger.error(f"Notion API エラー: {e}")
            return None
        except Exception as e:
            logger.error(f"データベーススキーマ取得エラー: {e}")
            return None
    
    def add_comment_to_page(self, page_id: str, comment_text: str) -> bool:
        """
        ページにコメントを追加
        
        Args:
            page_id: ページID
            comment_text: コメントテキスト
            
        Returns:
            bool: 成功時はTrue
        """
        try:
            self.client.comments.create(
                parent={"page_id": page_id},
                rich_text=[
                    {
                        "text": {
                            "content": comment_text
                        }
                    }
                ]
            )
            
            logger.info(f"コメント追加完了: {page_id}")
            return True
            
        except APIResponseError as e:
            logger.error(f"Notion API エラー: {e}")
            return False
        except Exception as e:
            logger.error(f"コメント追加エラー: {e}")
            return False
    
    def archive_page(self, page_id: str) -> bool:
        """
        ページをアーカイブ
        
        Args:
            page_id: ページID
            
        Returns:
            bool: 成功時はTrue
        """
        try:
            self.client.pages.update(page_id=page_id, archived=True)
            logger.info(f"ページアーカイブ完了: {page_id}")
            return True
            
        except APIResponseError as e:
            logger.error(f"Notion API エラー: {e}")
            return False
        except Exception as e:
            logger.error(f"ページアーカイブエラー: {e}")
            return False
