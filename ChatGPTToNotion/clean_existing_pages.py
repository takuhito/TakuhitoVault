#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean Existing Pages - 既存ページのゴミ文字削除ツール
既にNotionに取り込まれたページから謎の絵文字や不要な文字列を削除します。
"""

import os
import sys
import re
import time
from typing import List, Dict, Any
from datetime import datetime

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

def clean_garbage_text(text: str) -> str:
    """ゴミ文字（謎の絵文字や不要な文字列）を除去"""
    # 謎の絵文字パターンを除去
    patterns_to_remove = [
        r'⬛▶️cite⭐turn0search\d+◀️⬛',  # ⬛▶️cite⭐turn0search0◀️⬛ など
        r'⬛⚫',  # ⬛⚫
        r'▶️.*?⬛◀️',  # ▶️...⬛◀️ で囲まれた部分
        r'▶️',  # 単独の▶️
        r'⬛',  # 単独の⬛
        r'◀️',  # 単独の◀️
        r'⚫',  # 単独の⚫
        r'cite',  # cite文字列
        r'turn0search\d+',  # turn0search0, turn0search1 など
        r'⭐',  # ⭐
    ]
    
    cleaned_text = text
    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, '', cleaned_text)
    
    # 複数の空白行を1行に統一
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
    
    # 行頭行末の空白を除去
    cleaned_text = re.sub(r'^\s+|\s+$', '', cleaned_text, flags=re.MULTILINE)
    
    return cleaned_text.strip()

def has_garbage_text(text: str) -> bool:
    """テキストにゴミ文字が含まれているかチェック"""
    garbage_patterns = [
        r'⬛', r'▶️', r'◀️', r'⚫', r'cite', r'turn0search\d+', r'⭐'
    ]
    
    for pattern in garbage_patterns:
        if re.search(pattern, text):
            return True
    return False

def get_all_pages() -> List[Dict[str, Any]]:
    """データベース内の全ページを取得"""
    pages = []
    start_cursor = None
    
    while True:
        try:
            response = with_retry(
                lambda: notion.databases.query(
                    database_id=CHATGPT_DB_ID,
                    start_cursor=start_cursor,
                    page_size=100
                ),
                what="query database"
            )
            
            pages.extend(response.get("results", []))
            
            if not response.get("has_more"):
                break
                
            start_cursor = response.get("next_cursor")
            
        except Exception as e:
            print(f"ページ取得エラー: {e}")
            break
    
    return pages

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

def update_block_content(block_id: str, new_content: str):
    """ブロックの内容を更新"""
    try:
        with_retry(
            lambda: notion.blocks.update(
                block_id=block_id,
                paragraph={
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": new_content
                            }
                        }
                    ]
                }
            ),
            what="update block"
        )
        return True
    except Exception as e:
        print(f"ブロック更新エラー: {e}")
        return False

def clean_page_content(page_id: str, page_title: str) -> bool:
    """ページの内容をクリーンアップ"""
    print(f"ページをクリーンアップ中: {page_title}")
    
    blocks = get_page_blocks(page_id)
    cleaned_count = 0
    
    for block in blocks:
        if block.get("type") == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if rich_text:
                # 現在のテキストを取得
                current_text = "".join([rt.get("plain_text", "") for rt in rich_text])
                
                # ゴミ文字が含まれているかチェック
                if has_garbage_text(current_text):
                    # クリーンアップ
                    cleaned_text = clean_garbage_text(current_text)
                    
                    # 内容が変わった場合のみ更新
                    if cleaned_text != current_text:
                        if update_block_content(block["id"], cleaned_text):
                            cleaned_count += 1
                            print(f"  ブロック {block['id']} をクリーンアップしました")
                        time.sleep(0.1)  # API制限を避ける
    
    if cleaned_count > 0:
        print(f"  {cleaned_count}個のブロックをクリーンアップしました")
        return True
    else:
        print("  クリーンアップ不要でした")
        return False

def main():
    """メイン処理"""
    print("=== 既存ページのゴミ文字削除ツール ===")
    print(f"データベースID: {CHATGPT_DB_ID}")
    print()
    
    # 全ページを取得
    print("ページ一覧を取得中...")
    pages = get_all_pages()
    print(f"取得したページ数: {len(pages)}")
    print()
    
    # 各ページを処理
    cleaned_pages = 0
    for i, page in enumerate(pages, 1):
        page_id = page["id"]
        
        # ページタイトルを取得
        title_prop = page.get("properties", {}).get("名前", {})
        title = ""
        if title_prop.get("type") == "title":
            title_parts = title_prop.get("title", [])
            title = "".join([part.get("plain_text", "") for part in title_parts])
        
        if not title:
            title = f"ページ {i}"
        
        print(f"[{i}/{len(pages)}] {title}")
        
        # ページをクリーンアップ
        if clean_page_content(page_id, title):
            cleaned_pages += 1
        
        print()
        time.sleep(0.5)  # API制限を避ける
    
    print(f"=== 処理完了 ===")
    print(f"クリーンアップしたページ数: {cleaned_pages}/{len(pages)}")

if __name__ == "__main__":
    main()
