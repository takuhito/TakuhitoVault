#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Newlines Force - 強制的に改行を挿入
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

def delete_block(block_id: str) -> bool:
    """ブロックを削除"""
    try:
        with_retry(
            lambda: notion.blocks.delete(block_id=block_id),
            what="delete block"
        )
        return True
    except Exception as e:
        print(f"ブロック削除エラー: {e}")
        return False

def append_block_after(page_id: str, after_block_id: str, content: str) -> bool:
    """指定したブロックの後に新しいブロックを追加"""
    try:
        block_data = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }
                ]
            }
        }
        
        with_retry(
            lambda: notion.blocks.children.append(
                block_id=page_id,
                children=[block_data],
                after=after_block_id
            ),
            what="append block"
        )
        return True
    except Exception as e:
        print(f"ブロック追加エラー: {e}")
        return False

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

def fix_newlines_for_page(page_id: str, page_title: str):
    """ページの改行を修正"""
    print(f"=== 改行修正: {page_title} ===")
    print(f"ページID: {page_id}")
    print()
    
    blocks = get_page_blocks(page_id)
    if not blocks:
        print("ブロックが見つかりませんでした。")
        return
    
    print("現在のブロック数:", len(blocks))
    
    # 改行を挿入する位置を特定
    newline_positions = []
    
    for i, block in enumerate(blocks):
        if block.get("type") == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if rich_text:
                content = "".join([rt.get("plain_text", "") for rt in rich_text])
                
                # セクション区切りのパターンを検出
                section_patterns = [
                    r'^電車での移動:$',
                    r'^車での移動:$',
                    r'^注意点:$',
                    r'^[^:]+:$',
                ]
                
                # セクション区切りが含まれているかチェック
                for pattern in section_patterns:
                    if re.search(pattern, content):
                        print(f"セクション区切りを検出 [{i+1}]: {content}")
                        newline_positions.append(i)
                        break
                
                # 特定の文章の後に改行を挿入
                if "ご自宅から横須賀市の常光寺まで、明日11:00に到着するためのルートをご案内いたします。以下の情報を参考にしてください。" in content:
                    print(f"導入文を検出 [{i+1}]: {content}")
                    newline_positions.append(i)
                
                if "藤沢駅から横須賀駅までの電車の乗り換え案内は、NAVITIMEなどの乗り換え案内サービスで確認できます。" in content:
                    print(f"電車情報を検出 [{i+1}]: {content}")
                    newline_positions.append(i)
                
                if "藤沢市から横須賀市への車でのルート検索も、NAVITIMEなどのルート検索サービスで確認できます。" in content:
                    print(f"車情報を検出 [{i+1}]: {content}")
                    newline_positions.append(i)
    
    print(f"\n改行を挿入する位置: {newline_positions}")
    
    if not newline_positions:
        print("改行を挿入する位置が見つかりませんでした。")
        return
    
    # 改行を挿入（後ろから挿入してインデックスがずれないようにする）
    inserted_count = 0
    for pos in reversed(newline_positions):
        if pos < len(blocks):
            block_id = blocks[pos]["id"]
            print(f"位置 {pos+1} の後に改行を挿入中...")
            
            if append_empty_block_after(page_id, block_id):
                inserted_count += 1
                print(f"  改行を挿入しました")
            else:
                print(f"  改行の挿入に失敗しました")
            
            time.sleep(0.5)  # API制限を避ける
    
    print(f"\n=== 改行修正完了 ===")
    print(f"挿入した改行数: {inserted_count}")
    print("Notionで確認してください。")

def main():
    """メイン処理"""
    print("=== 強制的な改行挿入 ===")
    
    # 横須賀 常光寺 ルートのページを検索
    page_title = "横須賀 常光寺 ルート"
    page_id = find_page_by_title(page_title)
    
    if not page_id:
        print(f"ページ '{page_title}' が見つかりませんでした。")
        return
    
    fix_newlines_for_page(page_id, page_title)

if __name__ == "__main__":
    main()
