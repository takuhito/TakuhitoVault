# -*- coding: utf-8 -*-
"""
既存のリレーションが正しく設定されているかを確認するスクリプト
"""

import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
JOURNAL_DB_ID = os.getenv("JOURNAL_DB_ID")
if not NOTION_TOKEN or not JOURNAL_DB_ID:
    print("NOTION_TOKEN または JOURNAL_DB_ID が設定されていません。")
    exit(1)

notion = Client(auth=NOTION_TOKEN)

# データベース設定
DATABASES = {
    "マイリンク": {
        "db_id": "1f3b061dadf381c6a903fc15741f7d06",
        "relation_prop": "完了させた日"
    },
    "YouTube要約": {
        "db_id": "205b061dadf3803e83d1f67d8d81a215",
        "relation_prop": "日記"
    },
    "AI Chat管理": {
        "db_id": "1fdb061dadf380f8846df9d89aa6e988",
        "relation_prop": "取得日"
    },
    "行動": {
        "db_id": "1feb061dadf380d19988d10d8bf0e56d",
        "relation_prop": "行動日"
    }
}

def get_prop_val(prop):
    """プロパティの値を取得"""
    t = prop.get("type")
    if t == "date":
        v = prop.get("date")
        return v.get("start") if v else None
    if t == "rich_text":
        return "".join([span.get("plain_text", "") for span in prop.get("rich_text", [])]) or None
    if t == "title":
        return "".join([span.get("plain_text", "") for span in prop.get("title", [])]) or None
    if t == "formula":
        f = prop.get("formula", {})
        typ = f.get("type")
        if typ == "string":
            return f.get("string")
        if typ == "date":
            d = f.get("date") or {}
            return d.get("start")
        return None
    if t == "relation":
        return prop.get("relation") or []
    return None

def check_database_relations(db_name, db_config):
    print(f"\n=== {db_name} データベース ===")
    print(f"DB-ID: {db_config['db_id']}")
    print(f"リレーションプロパティ: {db_config['relation_prop']}")
    
    try:
        # データベースのページを取得（最大10件）
        response = notion.databases.query(
            database_id=db_config['db_id'],
            page_size=10
        )
        
        pages = response.get("results", [])
        print(f"確認対象ページ数: {len(pages)}")
        
        linked_count = 0
        unlinked_count = 0
        
        for i, page in enumerate(pages, 1):
            page_id = page["id"]
            page_title = get_prop_val(page.get("properties", {}).get("名前", {}))
            if not page_title:
                page_title = f"ページ{i}"
            
            # リレーションプロパティを確認
            relation_prop = page.get("properties", {}).get(db_config['relation_prop'], {})
            relation_value = get_prop_val(relation_prop)
            
            # 一致用日付を確認
            match_prop = page.get("properties", {}).get("一致用日付", {})
            match_date = get_prop_val(match_prop)
            
            if relation_value:
                linked_count += 1
                print(f"  ✓ {page_title}: リレーション設定済み")
                if match_date:
                    print(f"    一致用日付: {match_date}")
            else:
                unlinked_count += 1
                print(f"  ✗ {page_title}: リレーション未設定")
                if match_date:
                    print(f"    一致用日付: {match_date}")
        
        print(f"\n結果: {linked_count}件設定済み, {unlinked_count}件未設定")
        
    except Exception as e:
        print(f"エラー: {e}")

def main():
    print("既存のリレーション設定状況を確認中...")
    
    for db_name, db_config in DATABASES.items():
        check_database_relations(db_name, db_config)

if __name__ == "__main__":
    main()
