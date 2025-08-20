#!/usr/bin/env python3
"""
Notionデータベース設定スクリプト
"""
import os
import sys
import json
from typing import Dict, Any, Optional
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import NOTION_TOKEN, NOTION_DATABASE_ID
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'receipt-processor'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import importlib.util
spec = importlib.util.spec_from_file_location("notion_api_client", os.path.join(os.path.dirname(__file__), '..', 'receipt-processor', 'notion_api_client.py'))
notion_client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notion_client_module)
ReceiptNotionClient = notion_client_module.NotionClient

def setup_notion_database():
    """Notionデータベースの設定と確認"""
    
    print("🔧 Notionデータベース設定開始")
    print("=" * 50)
    
    # 1. トークンの確認
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKENが設定されていません")
        print("📝 以下の手順で設定してください：")
        print("1. https://www.notion.so/my-integrations にアクセス")
        print("2. 'New integration'をクリック")
        print("3. 名前を'Receipt Processor'に設定")
        print("4. Capabilitiesで'Read content', 'Update content', 'Insert content'を選択")
        print("5. Internal Integration Tokenをコピー")
        print("6. .envファイルに NOTION_TOKEN=your_token_here を追加")
        return False
    
    print("✅ NOTION_TOKEN: 設定済み")
    
    # 2. データベースIDの確認
    if not NOTION_DATABASE_ID:
        print("❌ NOTION_DATABASE_IDが設定されていません")
        print("📝 データベースIDを設定してください")
        return False
    
    print(f"✅ NOTION_DATABASE_ID: {NOTION_DATABASE_ID}")
    
    # 3. NotionClientの初期化
    try:
        notion_client = ReceiptNotionClient()
        print("✅ NotionClient初期化成功")
    except Exception as e:
        print(f"❌ NotionClient初期化失敗: {e}")
        return False
    
    # 4. データベースの存在確認
    try:
        database_info = notion_client.get_database_info()
        print("✅ データベース接続成功")
        print(f"📊 データベース名: {database_info.get('title', 'Unknown')}")
        print(f"📊 プロパティ数: {len(database_info.get('properties', {}))}")
    except Exception as e:
        print(f"❌ データベース接続失敗: {e}")
        print("📝 以下の手順でデータベースを作成してください：")
        print("1. Notionで新しいページを作成")
        print("2. '/database'と入力してデータベースを作成")
        print("3. 必要なプロパティを設定（後述）")
        print("4. Integrationを接続")
        print("5. データベースURLからIDを取得")
        return False
    
    # 5. 必要なプロパティの確認
    required_properties = [
        '店舗名', '日付', '金額', 'カテゴリ', '勘定科目', 
        '商品一覧', '処理状況', '信頼度'
    ]
    
    existing_properties = list(database_info.get('properties', {}).keys())
    missing_properties = [prop for prop in required_properties if prop not in existing_properties]
    
    if missing_properties:
        print(f"⚠️  不足しているプロパティ: {missing_properties}")
        print("📝 以下のプロパティを手動で追加してください：")
        for prop in missing_properties:
            prop_type = get_property_type(prop)
            print(f"  - {prop} ({prop_type})")
    else:
        print("✅ 必要なプロパティ: 全て設定済み")
    
    # 6. テストデータの作成
    print("\n🧪 テストデータ作成中...")
    try:
        test_data = create_test_data()
        result = notion_client.create_receipt_record(test_data)
        if result:
            print("✅ テストデータ作成成功")
            print(f"📝 ページID: {result}")
            
            # テストデータの削除
            try:
                notion_client.delete_page(result)
                print("✅ テストデータ削除完了")
            except:
                print("⚠️  テストデータの削除に失敗しました（手動で削除してください）")
        else:
            print("❌ テストデータ作成失敗")
    except Exception as e:
        print(f"❌ テストデータ作成エラー: {e}")
    
    print("\n🎉 Notionデータベース設定完了！")
    return True

def get_property_type(property_name: str) -> str:
    """プロパティ名に基づいて適切なタイプを返す"""
    property_types = {
        '店舗名': 'Title',
        '日付': 'Date', 
        '金額': 'Number',
        'カテゴリ': 'Select',
        '勘定科目': 'Select',
        '商品一覧': 'Rich text',
        '処理状況': 'Select',
        '信頼度': 'Number'
    }
    return property_types.get(property_name, 'Text')

def create_test_data() -> Dict[str, Any]:
    """テスト用のデータを作成"""
    return {
        'store_name': 'テスト店舗',
        'date': datetime.now().date(),
        'total_amount': 1000.0,
        'category': '食費',
        'account_item': '現金',
        'items': 'テスト商品 1000円',
        'processing_status': '未処理',
        'confidence_score': 0.95,
        'file_name': 'test_receipt.jpg',
        'file_url': 'https://example.com/test.jpg'
    }

def create_database_template():
    """データベーステンプレートの作成ガイド"""
    print("\n📋 データベーステンプレート作成ガイド")
    print("=" * 50)
    
    template = {
        "properties": {
            "店舗名": {
                "type": "title",
                "title": {}
            },
            "日付": {
                "type": "date",
                "date": {}
            },
            "金額": {
                "type": "number",
                "number": {
                    "format": "number_with_commas"
                }
            },
            "カテゴリ": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "食費", "color": "blue"},
                        {"name": "交通費", "color": "green"},
                        {"name": "雑費", "color": "gray"},
                        {"name": "光熱費", "color": "yellow"},
                        {"name": "通信費", "color": "purple"},
                        {"name": "医療費", "color": "red"},
                        {"name": "教育費", "color": "orange"},
                        {"name": "娯楽費", "color": "pink"},
                        {"name": "その他", "color": "brown"}
                    ]
                }
            },
            "勘定科目": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "現金", "color": "green"},
                        {"name": "普通預金", "color": "blue"},
                        {"name": "クレジットカード", "color": "purple"},
                        {"name": "電子マネー", "color": "orange"},
                        {"name": "その他", "color": "gray"}
                    ]
                }
            },
            "商品一覧": {
                "type": "rich_text",
                "rich_text": {}
            },
            "処理状況": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "未処理", "color": "red"},
                        {"name": "処理済み", "color": "green"},
                        {"name": "エラー", "color": "yellow"},
                        {"name": "手動確認要", "color": "orange"}
                    ]
                }
            },
            "信頼度": {
                "type": "number",
                "number": {
                    "format": "percent"
                }
            }
        }
    }
    
    print("以下のJSONテンプレートを使用してデータベースを作成してください：")
    print(json.dumps(template, indent=2, ensure_ascii=False))
    
    return template

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "template":
        create_database_template()
    else:
        setup_notion_database()
