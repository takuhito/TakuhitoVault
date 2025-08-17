#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Missing Newlines - 不足している改行を追加
"""

import os
import sys
import json
import time
import re
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

def get_page_blocks(page_id: str) -> List[Dict[str, Any]]:
    """ページのブロックを取得"""
    try:
        response = with_retry(
            lambda: notion.blocks.children.list(block_id=page_id),
            what="get blocks"
        )
        
        return response.get("results", [])
        
    except Exception as e:
        print(f"ブロック取得エラー: {e}")
        return []

def append_empty_block_after(page_id: str, after_block_id: str) -> bool:
    """指定したブロックの後に空行ブロックを追加"""
    try:
        block_data = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": []
            }
        }
        
        with_retry(
            lambda: notion.blocks.children.append(
                block_id=page_id,
                children=[block_data],
                after=after_block_id
            ),
            what="append empty block"
        )
        return True
    except Exception as e:
        print(f"空行ブロック追加エラー: {e}")
        return False

def add_missing_newlines(page_id: str, page_title: str):
    """不足している改行を追加"""
    print(f"=== 不足している改行を追加: {page_title} ===")
    print(f"ページID: {page_id}")
    print()
    
    blocks = get_page_blocks(page_id)
    if not blocks:
        print("ブロックが見つかりませんでした。")
        return
    
    print("現在のブロック数:", len(blocks))
    
    # 改行を追加する位置を特定
    newline_positions = []
    
    for i, block in enumerate(blocks):
        if block.get("type") == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if rich_text:
                content = "".join([rt.get("plain_text", "") for rt in rich_text])
                
                # メッセージ数の後に改行を追加
                if "📊 メッセージ数: 2" in content and "【ユーザー" in content:
                    print(f"メッセージ数ブロックを検出 [{i+1}]: {content}")
                    newline_positions.append(i)
                
                # ユーザーメッセージの後に改行を追加（アシスタントの前）
                if "【アシスタント" in content:
                    print(f"アシスタントブロックを検出 [{i+1}]: {content}")
                    newline_positions.append(i)
    
    print(f"\n改行を追加する位置: {newline_positions}")
    
    if not newline_positions:
        print("改行を追加する位置が見つかりませんでした。")
        return
    
    # 改行を追加（後ろから追加してインデックスがずれないようにする）
    inserted_count = 0
    for pos in reversed(newline_positions):
        if pos < len(blocks):
            block_id = blocks[pos]["id"]
            print(f"位置 {pos+1} の後に改行を2回追加中...")
            
            # 2回の改行を追加
            success_count = 0
            for _ in range(2):
                if append_empty_block_after(page_id, block_id):
                    success_count += 1
                    time.sleep(0.3)  # API制限を避ける
                else:
                    print(f"  改行の追加に失敗しました")
                    break
            
            if success_count == 2:
                inserted_count += 2
                print(f"  改行を2回追加しました")
            else:
                print(f"  改行の追加が不完全でした（{success_count}/2）")
            
            time.sleep(0.5)  # API制限を避ける
    
    print(f"\n=== 改行追加完了 ===")
    print(f"追加した改行数: {inserted_count}")
    print("Notionで確認してください。")

def main():
    """メイン処理"""
    print("=== 不足している改行を追加 ===")
    
    # 横須賀 常光寺 ルートのページを検索
    page_title = "横須賀 常光寺 ルート"
    page_id = find_page_by_title(page_title)
    
    if not page_id:
        print(f"ページ '{page_title}' が見つかりませんでした。")
        return
    
    add_missing_newlines(page_id, page_title)

if __name__ == "__main__":
    main()
