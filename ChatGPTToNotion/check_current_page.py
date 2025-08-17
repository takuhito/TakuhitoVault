#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Current Page - 現在のページの内容を確認
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

def check_page_content(page_id: str, page_title: str):
    """ページの内容を確認"""
    print(f"=== ページ内容確認: {page_title} ===")
    print(f"ページID: {page_id}")
    print()
    
    blocks = get_page_blocks(page_id)
    if not blocks:
        print("ブロックが見つかりませんでした。")
        return
    
    print("現在のブロック構造:")
    print("=" * 50)
    
    for i, block in enumerate(blocks):
        block_type = block.get("type", "unknown")
        print(f"[{i+1}] タイプ: {block_type}")
        
        if block_type == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if rich_text:
                content = "".join([rt.get("plain_text", "") for rt in rich_text])
                print(f"    内容: {repr(content)}")
                print(f"    長さ: {len(content)} 文字")
            else:
                print("    内容: [空行]")
        else:
            print(f"    その他のタイプ: {block_type}")
        
        print()
    
    print("=" * 50)
    print("改行の分析:")
    
    # 改行の分析
    empty_blocks = 0
    content_blocks = 0
    
    for i, block in enumerate(blocks):
        if block.get("type") == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if not rich_text:
                empty_blocks += 1
                print(f"  空行ブロック [{i+1}]: 改行として機能")
            else:
                content_blocks += 1
                content = "".join([rt.get("plain_text", "") for rt in rich_text])
                print(f"  内容ブロック [{i+1}]: {content[:50]}{'...' if len(content) > 50 else ''}")
    
    print(f"\n総ブロック数: {len(blocks)}")
    print(f"内容ブロック数: {content_blocks}")
    print(f"空行ブロック数: {empty_blocks}")
    
    # セクション区切りの検出
    print("\nセクション区切りの検出:")
    section_patterns = [
        r'^電車での移動:$',
        r'^車での移動:$',
        r'^注意点:$',
        r'^[^:]+:$',
    ]
    
    for i, block in enumerate(blocks):
        if block.get("type") == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if rich_text:
                content = "".join([rt.get("plain_text", "") for rt in rich_text])
                import re
                for pattern in section_patterns:
                    if re.match(pattern, content):
                        print(f"  セクション区切り [{i+1}]: {content}")
                        # 前後のブロックを確認
                        if i > 0:
                            prev_block = blocks[i-1]
                            prev_rich_text = prev_block.get("paragraph", {}).get("rich_text", [])
                            print(f"    前のブロック [{i}]: {'空行' if not prev_rich_text else '内容あり'}")
                        if i < len(blocks) - 1:
                            next_block = blocks[i+1]
                            next_rich_text = next_block.get("paragraph", {}).get("rich_text", [])
                            print(f"    次のブロック [{i+2}]: {'空行' if not next_rich_text else '内容あり'}")

def main():
    """メイン処理"""
    print("=== 現在のページ内容確認 ===")
    
    # 横須賀 常光寺 ルートのページを検索
    page_title = "横須賀 常光寺 ルート"
    page_id = find_page_by_title(page_title)
    
    if not page_id:
        print(f"ページ '{page_title}' が見つかりませんでした。")
        return
    
    check_page_content(page_id, page_title)

if __name__ == "__main__":
    main()
