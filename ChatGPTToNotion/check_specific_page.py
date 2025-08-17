#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Specific Page - 特定ページの内容確認ツール
"""

import os
import sys
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

def find_page_by_title(title: str) -> str:
    """タイトルでページを検索してIDを取得"""
    try:
        response = notion.databases.query(
            database_id=CHATGPT_DB_ID,
            filter={
                "property": "名前",
                "title": {
                    "contains": title
                }
            }
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
            response = notion.blocks.children.list(
                block_id=page_id,
                start_cursor=start_cursor,
                page_size=100
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
    
    if not blocks:
        print("ブロックが見つかりませんでした。")
        return
    
    for i, block in enumerate(blocks):
        print(f"--- ブロック {i+1} ---")
        print(f"タイプ: {block.get('type')}")
        print(f"ブロックID: {block.get('id')}")
        
        if block.get("type") == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if rich_text:
                content = "".join([rt.get("plain_text", "") for rt in rich_text])
                print(f"内容長: {len(content)} 文字")
                print("内容:")
                print("=" * 50)
                print(content)
                print("=" * 50)
                
                # ゴミ文字の確認
                garbage_chars = ['⬛', '▶️', '◀️', '⚫', 'cite', 'turn0search', '⭐', '**.*']
                found_garbage = []
                for char in garbage_chars:
                    if char in content:
                        found_garbage.append(char)
                
                if found_garbage:
                    print(f"発見されたゴミ文字: {found_garbage}")
                else:
                    print("ゴミ文字は見つかりませんでした。")
            else:
                print("テキストがありません。")
        else:
            print("段落ブロックではありません。")
        
        print()

def main():
    """メイン処理"""
    target_title = "Apple One CM 曲"
    
    print(f"=== 特定ページ内容確認ツール ===")
    print(f"対象ページ: {target_title}")
    print()
    
    page_id = find_page_by_title(target_title)
    if page_id:
        check_page_content(page_id, target_title)
    else:
        print(f"ページ '{target_title}' が見つかりませんでした。")

if __name__ == "__main__":
    main()
