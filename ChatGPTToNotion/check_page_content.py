#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Page Content - ページ内容確認ツール
指定したページの現在の内容を確認します。
"""

import os
import sys
import json
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
    import time
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

def find_page_by_title(title: str) -> str:
    """タイトルでページを検索してIDを取得"""
    try:
        response = with_retry(
            lambda: notion.databases.query(
                database_id=CHATGPT_DB_ID,
                filter={
                    "property": "名前",
                    "title": {
                        "contains": title
                    }
                }
            ),
            what="search page by title"
        )
        
        results = response.get("results", [])
        if results:
            return results[0]["id"]
        else:
            print(f"ページ '{title}' が見つかりませんでした。")
            return None
            
    except Exception as e:
        print(f"ページ検索エラー: {e}")
        return None

def get_page_blocks(page_id: str) -> List[Dict[str, Any]]:
    """ページの全ブロックを取得"""
    blocks = []
    start_cursor = None
    
    while True:
        try:
            response = with_retry(
                lambda: notion.blocks.children.list(
                    block_id=page_id,
                    start_cursor=start_cursor,
                    page_size=100
                ),
                what="get page blocks"
            )
            
            blocks.extend(response.get("results", []))
            
            if not response.get("has_more"):
                break
                
            start_cursor = response.get("next_cursor")
            
        except Exception as e:
            print(f"ブロック取得エラー: {e}")
            break
    
    return blocks

def check_page_content(page_id: str, page_title: str):
    """ページの内容を確認"""
    print(f"=== ページ内容確認: {page_title} ===")
    print(f"ページID: {page_id}")
    print()
    
    blocks = get_page_blocks(page_id)
    print(f"ブロック数: {len(blocks)}")
    print()
    
    for i, block in enumerate(blocks, 1):
        print(f"--- ブロック {i} ---")
        print(f"タイプ: {block.get('type')}")
        print(f"ID: {block.get('id')}")
        
        if block.get("type") == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if rich_text:
                text_content = "".join([rt.get("plain_text", "") for rt in rich_text])
                print(f"内容長: {len(text_content)} 文字")
                print("内容:")
                print("=" * 50)
                print(text_content)
                print("=" * 50)
                
                # ゴミ文字の検出
                garbage_patterns = [
                    r'⬛', r'▶️', r'◀️', r'⚫', r'cite', r'turn0search\d+', r'⭐'
                ]
                
                found_garbage = []
                for pattern in garbage_patterns:
                    import re
                    if re.search(pattern, text_content):
                        found_garbage.append(pattern)
                
                if found_garbage:
                    print(f"⚠️  検出されたゴミ文字: {found_garbage}")
                else:
                    print("✅ ゴミ文字は検出されませんでした")
            else:
                print("内容: 空")
        else:
            print(f"内容: {block}")
        
        print()

def main():
    """メイン処理"""
    print("=== ページ内容確認ツール ===")
    
    # 対象ページのタイトル
    target_title = "横須賀 常光寺 ルート"
    
    # ページを検索
    print(f"ページを検索中: {target_title}")
    page_id = find_page_by_title(target_title)
    
    if page_id:
        # ページ内容を確認
        check_page_content(page_id, target_title)
    else:
        print("ページが見つかりませんでした。")

if __name__ == "__main__":
    main()
