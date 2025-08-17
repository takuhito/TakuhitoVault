#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check All Pages Newlines - すべてのページの改行状況をチェック
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

def get_page_blocks(page_id: str) -> List[Dict[str, Any]]:
    """ページのブロックを取得"""
    try:
        response = with_retry(
            lambda: notion.blocks.children.list(
                block_id=page_id,
                page_size=100
            ),
            what="get blocks"
        )
        
        return response.get("results", [])
        
    except Exception as e:
        print(f"ブロック取得エラー: {e}")
        return []

def check_page_newlines(page: Dict[str, Any]) -> Dict[str, Any]:
    """ページの改行状況をチェック"""
    page_id = page.get("id")
    title = page.get("properties", {}).get("名前", {}).get("title", [])
    title_text = title[0].get("plain_text", "タイトルなし") if title else "タイトルなし"
    
    blocks = get_page_blocks(page_id)
    
    # 改行状況を分析
    total_blocks = len(blocks)
    empty_blocks = 0
    content_blocks = 0
    has_proper_newlines = False
    
    # メッセージ数とユーザー名の間に改行があるかチェック
    message_count_found = False
    user_found = False
    newline_between = False
    
    for i, block in enumerate(blocks):
        block_type = block.get("type")
        
        if block_type == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            
            if not rich_text:  # 空のブロック（改行）
                empty_blocks += 1
            else:
                content_blocks += 1
                text_content = rich_text[0].get("plain_text", "")
                
                # メッセージ数の検出
                if "📊 メッセージ数:" in text_content:
                    message_count_found = True
                
                # ユーザー名の検出
                if "【ユーザー" in text_content:
                    user_found = True
                    # 前のブロックが空かチェック
                    if i > 0 and blocks[i-1].get("type") == "paragraph":
                        prev_rich_text = blocks[i-1].get("paragraph", {}).get("rich_text", [])
                        if not prev_rich_text:
                            newline_between = True
    
    # 適切な改行があるか判定
    if message_count_found and user_found and newline_between:
        has_proper_newlines = True
    
    return {
        "title": title_text,
        "page_id": page_id,
        "total_blocks": total_blocks,
        "empty_blocks": empty_blocks,
        "content_blocks": content_blocks,
        "has_proper_newlines": has_proper_newlines,
        "message_count_found": message_count_found,
        "user_found": user_found,
        "newline_between": newline_between
    }

def main():
    """メイン処理"""
    print("=== すべてのページの改行状況をチェック ===")
    
    # すべてのページを取得
    print("ページ一覧を取得中...")
    pages = get_all_pages()
    print(f"取得したページ数: {len(pages)}")
    print()
    
    # 各ページの改行状況をチェック
    results = []
    proper_newlines_count = 0
    improper_newlines_count = 0
    
    for i, page in enumerate(pages, 1):
        print(f"[{i}/{len(pages)}] チェック中: {page.get('properties', {}).get('名前', {}).get('title', [{}])[0].get('plain_text', 'タイトルなし')}")
        
        result = check_page_newlines(page)
        results.append(result)
        
        if result["has_proper_newlines"]:
            proper_newlines_count += 1
        else:
            improper_newlines_count += 1
        
        # API制限を避ける
        time.sleep(0.1)
    
    print()
    print("=== チェック結果 ===")
    print(f"総ページ数: {len(pages)}")
    print(f"改行が正しいページ数: {proper_newlines_count}")
    print(f"改行が不適切なページ数: {improper_newlines_count}")
    print()
    
    # 改行が不適切なページの詳細
    if improper_newlines_count > 0:
        print("=== 改行が不適切なページ ===")
        for result in results:
            if not result["has_proper_newlines"]:
                print(f"- {result['title']}")
                print(f"  ブロック数: {result['total_blocks']} (空: {result['empty_blocks']}, 内容: {result['content_blocks']})")
                print(f"  メッセージ数: {'✓' if result['message_count_found'] else '✗'}")
                print(f"  ユーザー名: {'✓' if result['user_found'] else '✗'}")
                print(f"  改行: {'✓' if result['newline_between'] else '✗'}")
                print()
    
    # 結果をファイルに保存
    import json
    with open("newlines_check_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"詳細結果を newlines_check_result.json に保存しました。")

if __name__ == "__main__":
    main()
