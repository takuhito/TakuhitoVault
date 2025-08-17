#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Restore Page Properties - ページのプロパティ（AI Model、URL）を復元
"""

import os
import sys
import json
import time
from typing import List, Dict, Any

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError, RequestTimeoutError
except Exception:
    print("notion-client がありません。`pip install -r requirements.txt` を実行してください。")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

# 環境変数
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
CHATGPT_DB_ID = os.getenv("CHATGPT_DB_ID")
NOTION_TIMEOUT = int(os.getenv("NOTION_TIMEOUT", "60"))

if not NOTION_TOKEN or not CHATGPT_DB_ID:
    print("環境変数 NOTION_TOKEN / CHATGPT_DB_ID が未設定です。.env を確認してください。")
    sys.exit(1)

# Notionクライアント
notion = Client(auth=NOTION_TOKEN, timeout_ms=int(NOTION_TIMEOUT * 1000))

def with_retry(fn, *, max_attempts=4, base_delay=1.0, what="api"):
    """リトライ付きAPI呼び出し"""
    import random
    attempt = 0
    while True:
        try:
            return fn()
        except RequestTimeoutError as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            delay = base_delay * (2 ** (attempt-1)) + random.uniform(0, 0.5)
            print(f"[RETRY] Timeout on {what}. retry {attempt}/{max_attempts} in {delay:.1f}s")
            time.sleep(delay)
        except APIResponseError as e:
            if getattr(e, "code", "") == "rate_limited":
                attempt += 1
                retry_after = float(getattr(e, "headers", {}).get("Retry-After", 1)) if hasattr(e, "headers") else 1.0
                delay = max(retry_after, base_delay * (2 ** (attempt-1))) + random.uniform(0, 0.5)
                print(f"[RETRY] rate_limited on {what}. retry {attempt}/{max_attempts} in {delay:.1f}s")
                time.sleep(delay)
                if attempt < max_attempts:
                    continue
            raise

def get_all_pages() -> List[Dict[str, Any]]:
    """データベース内のすべてのページを取得"""
    all_pages = []
    start_cursor = None
    
    while True:
        try:
            response = with_retry(
                lambda: notion.databases.query(
                    database_id=CHATGPT_DB_ID,
                    start_cursor=start_cursor,
                    page_size=100
                ),
                what="get pages"
            )
            
            pages = response.get("results", [])
            all_pages.extend(pages)
            
            # 次のページがあるかチェック
            next_cursor = response.get("next_cursor")
            if not next_cursor:
                break
                
            start_cursor = next_cursor
            time.sleep(0.1)  # API制限を避ける
            
        except Exception as e:
            print(f"ページ取得エラー: {e}")
            break
    
    return all_pages

def find_page_by_title(title: str) -> str:
    """タイトルでページを検索"""
    try:
        response = with_retry(
            lambda: notion.databases.query(
                database_id=CHATGPT_DB_ID,
                filter={
                    "property": "名前",
                    "title": {
                        "equals": title
                    }
                }
            ),
            what="find page"
        )
        
        results = response.get("results", [])
        if results:
            return results[0]["id"]
        return None
        
    except Exception as e:
        print(f"ページ検索エラー: {e}")
        return None

def update_page_properties(page_id: str, properties: Dict[str, Any]) -> bool:
    """ページのプロパティを更新"""
    try:
        with_retry(
            lambda: notion.pages.update(
                page_id=page_id,
                properties=properties
            ),
            what="update page properties"
        )
        return True
    except Exception as e:
        print(f"ページプロパティ更新エラー: {e}")
        return False

def load_backup_data(filename: str) -> List[Dict[str, Any]]:
    """バックアップファイルを読み込み"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"バックアップファイル読み込みエラー: {e}")
        return []

def main():
    """メイン処理"""
    print("=== ページのプロパティ（AI Model、URL）を復元 ===")
    
    # バックアップファイルを探す
    backup_files = [f for f in os.listdir('.') if f.startswith('pages_backup_') and f.endswith('.json')]
    
    if not backup_files:
        print("バックアップファイルが見つかりませんでした。")
        return
    
    # 最新のバックアップファイルを使用
    backup_file = sorted(backup_files)[-1]
    print(f"使用するバックアップファイル: {backup_file}")
    
    # バックアップデータを読み込み
    backup_data = load_backup_data(backup_file)
    if not backup_data:
        print("バックアップデータの読み込みに失敗しました。")
        return
    
    # バックアップデータからタイトルで検索
    backup_dict = {page.get("title"): page for page in backup_data}
    
    # 現在のページを取得
    print("現在のページ一覧を取得中...")
    current_pages = get_all_pages()
    print(f"取得したページ数: {len(current_pages)}")
    
    updated_count = 0
    failed_count = 0
    
    for i, page in enumerate(current_pages, 1):
        title = page.get("properties", {}).get("名前", {}).get("title", [])
        title_text = title[0].get("plain_text", "タイトルなし") if title else "タイトルなし"
        
        print(f"[{i}/{len(current_pages)}] 処理中: {title_text}")
        
        # バックアップデータから該当ページを取得
        if title_text not in backup_dict:
            print(f"  バックアップデータにページが見つかりませんでした")
            failed_count += 1
            continue
        
        backup_page = backup_dict[title_text]
        
        # 復元するプロパティを準備
        properties_to_update = {}
        
        # AI Modelプロパティを復元
        if "ai_model" in backup_page:
            ai_model = backup_page["ai_model"]
            if ai_model:
                properties_to_update["AI Model"] = {
                    "multi_select": [
                        {"name": ai_model}
                    ]
                }
        
        # URLプロパティを復元
        if "url" in backup_page:
            url = backup_page["url"]
            if url:
                properties_to_update["URL"] = {
                    "url": url
                }
        
        # プロパティが存在する場合のみ更新
        if properties_to_update:
            page_id = page.get("id")
            if update_page_properties(page_id, properties_to_update):
                print(f"  プロパティを更新しました")
                updated_count += 1
            else:
                print(f"  プロパティの更新に失敗しました")
                failed_count += 1
        else:
            print(f"  復元するプロパティがありませんでした")
        
        # API制限を避ける
        time.sleep(0.1)
        
        # 進捗表示（10ページごと）
        if i % 10 == 0:
            print(f"  進捗: {i}/{len(current_pages)} ページ完了")
    
    print()
    print("=== 復元完了 ===")
    print(f"更新したページ数: {updated_count}")
    print(f"失敗したページ数: {failed_count}")
    
    if updated_count > 0:
        print("✅ ページプロパティの復元成功！")
        print("Notionで確認してください。")
    else:
        print("❌ 復元失敗。問題を確認してください。")

if __name__ == "__main__":
    main()
