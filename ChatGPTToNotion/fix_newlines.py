#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Newlines - 改行修正
復元されたページの改行を修正します。
"""

import os
import sys
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

def get_recent_pages() -> List[Dict[str, Any]]:
    """最近作成されたページを取得"""
    try:
        response = with_retry(
            lambda: notion.databases.query(
                database_id=CHATGPT_DB_ID,
                page_size=10,
                sorts=[
                    {
                        "property": "最終更新日時",
                        "direction": "descending"
                    }
                ]
            ),
            what="query recent pages"
        )
        
        return response.get("results", [])
        
    except Exception as e:
        print(f"ページ取得エラー: {e}")
        return []

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

def update_block_content(block_id: str, new_content: str) -> bool:
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

def format_content_with_newlines(content: str) -> str:
    """改行を適切に保持してコンテンツをフォーマット"""
    # 改行を保持しながら、適切にフォーマット
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            formatted_lines.append(line)
        else:
            # 空行は改行として保持
            formatted_lines.append('')
    
    # 連続する空行を2つに制限
    result = []
    prev_empty = False
    for line in formatted_lines:
        if line == '':
            if not prev_empty:
                result.append(line)
            prev_empty = True
        else:
            result.append(line)
            prev_empty = False
    
    return '\n'.join(result)

def main():
    """メイン処理"""
    print("=== 改行修正 ===")
    
    # 最近作成されたページを取得
    pages = get_recent_pages()
    print(f"取得したページ数: {len(pages)}")
    
    if not pages:
        print("ページが見つかりませんでした。")
        return
    
    fixed_count = 0
    
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
        
        print(f"[{i}/{len(pages)}] 確認中: {title}")
        
        # ページの内容を取得
        blocks = get_page_blocks(page_id)
        if blocks:
            block = blocks[0]
            if block.get("type") == "paragraph":
                rich_text = block.get("paragraph", {}).get("rich_text", [])
                if rich_text:
                    current_content = "".join([rt.get("plain_text", "") for rt in rich_text])
                    
                    # 改行を適切にフォーマット
                    formatted_content = format_content_with_newlines(current_content)
                    
                    # 内容が変わった場合のみ更新
                    if formatted_content != current_content:
                        if update_block_content(block["id"], formatted_content):
                            print(f"  改行を修正しました")
                            fixed_count += 1
                        else:
                            print(f"  改行の修正に失敗しました")
                    else:
                        print(f"  改行は正常でした")
        
        time.sleep(0.2)
        print()
    
    print()
    print("=== 修正完了 ===")
    print(f"修正したページ数: {fixed_count}")

if __name__ == "__main__":
    main()
