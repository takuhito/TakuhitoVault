# -*- coding: utf-8 -*-
"""
データベースのプロパティ構造を確認するスクリプト
"""

import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    print("NOTION_TOKEN が設定されていません。")
    exit(1)

notion = Client(auth=NOTION_TOKEN)

# データベースID
DATABASES = {
    "マイリンク": "1f3b061dadf381c6a903fc15741f7d06",
    "YouTube要約": "205b061dadf3803e83d1f67d8d81a215",
    "AI Chat管理": "1fdb061dadf380f8846df9d89aa6e988",
    "行動": "1feb061dadf380d19988d10d8bf0e56d"
}

def check_database_properties(db_name, db_id):
    print(f"\n=== {db_name} データベース ===")
    print(f"DB-ID: {db_id}")
    
    try:
        # データベースの情報を取得
        database = notion.databases.retrieve(database_id=db_id)
        properties = database.get("properties", {})
        
        print("プロパティ一覧:")
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "unknown")
            print(f"  - {prop_name} ({prop_type})")
            
            # 日付型またはリレーション型の場合は詳細を表示
            if prop_type in ["date", "relation"]:
                print(f"    → 型: {prop_type}")
                if prop_type == "relation":
                    relation_info = prop_info.get("relation", {})
                    print(f"    → 関連先DB: {relation_info.get('database_id', 'N/A')}")
        
    except Exception as e:
        print(f"エラー: {e}")

def main():
    print("データベースのプロパティ構造を確認中...")
    
    for db_name, db_id in DATABASES.items():
        check_database_properties(db_name, db_id)

if __name__ == "__main__":
    main()
