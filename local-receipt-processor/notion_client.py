"""
ローカル環境用のNotion API クライアント
"""

import os
from typing import Dict, Any, Optional
from notion_client import Client

from config import NOTION_TOKEN, NOTION_DATABASE_ID

class NotionClient:
    """Notion API クライアント"""
    
    def __init__(self):
        if not NOTION_TOKEN:
            raise ValueError("NOTION_TOKENが設定されていません")
        
        self.client = Client(auth=NOTION_TOKEN)
        self.database_id = NOTION_DATABASE_ID
        print("✅ Notion API クライアント初期化完了")
    
    def create_receipt_page(self, receipt_data: Dict[str, Any]) -> Optional[str]:
        """
        領収書ページを作成
        
        Args:
            receipt_data: 領収書データ
            
        Returns:
            Optional[str]: 作成されたページID
        """
        try:
            properties = self._build_properties(receipt_data)
            
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties
            }
            
            response = self.client.pages.create(**page_data)
            page_id = response['id']
            
            print(f"✅ Notionページ作成完了: {page_id}")
            return page_id
            
        except Exception as e:
            print(f"❌ Notionページ作成エラー: {e}")
            return None
    
    def _build_properties(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        プロパティを構築
        
        Args:
            receipt_data: 領収書データ
            
        Returns:
            Dict[str, Any]: Notionプロパティ
        """
        properties = {}
        
        # 店舗名
        if 'store_name' in receipt_data:
            properties["店舗名"] = {
                "title": [
                    {
                        "text": {
                            "content": receipt_data['store_name']
                        }
                    }
                ]
            }
        
        # 日付
        if 'date' in receipt_data:
            properties["日付"] = {
                "date": {
                    "start": receipt_data['date'].isoformat() if hasattr(receipt_data['date'], 'isoformat') else receipt_data['date']
                }
            }
        
        # 合計金額
        if 'total_amount' in receipt_data:
            properties["合計金額"] = {
                "number": float(receipt_data['total_amount'])
            }
        
        # 支払い金額
        if 'payment_amount' in receipt_data:
            properties["支払い金額"] = {
                "number": float(receipt_data['payment_amount'])
            }
        
        # 支払方法
        if 'payment_method' in receipt_data:
            properties["支払方法"] = {
                "select": {
                    "name": receipt_data['payment_method']
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
        
        return properties
    
    def get_database_info(self) -> Optional[Dict[str, Any]]:
        """
        データベース情報を取得
        
        Returns:
            Optional[Dict[str, Any]]: データベース情報
        """
        try:
            response = self.client.databases.retrieve(database_id=self.database_id)
            return response
        except Exception as e:
            print(f"❌ データベース情報取得エラー: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        接続テスト
        
        Returns:
            bool: 接続成功時True
        """
        try:
            database = self.get_database_info()
            if database:
                print(f"✅ Notion接続成功: {database.get('title', [{}])[0].get('plain_text', 'Unknown')}")
                return True
            else:
                print("❌ Notion接続失敗")
                return False
        except Exception as e:
            print(f"❌ Notion接続テストエラー: {e}")
            return False
