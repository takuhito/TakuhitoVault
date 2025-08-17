#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Force Clean Page - 特定ページの強制クリーンアップツール
指定したページから確実にゴミ文字を削除します。
"""

import os
import sys
import re
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

def clean_garbage_text(text: str) -> str:
    """ゴミ文字（謎の絵文字や不要な文字列）を除去"""
    # より強力なパターンマッチング
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
        r'cite⭐',  # cite⭐
        r'⭐turn0search\d+',  # ⭐turn0search0 など
    ]
    
    cleaned_text = text
    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    # 複数の空白行を1行に統一
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
    
    # 行頭行末の空白を除去
    cleaned_text = re.sub(r'^\s+|\s+$', '', cleaned_text, flags=re.MULTILINE)
    
    return cleaned_text.strip()

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

def create_new_block(page_id: str, content: str) -> bool:
    """新しいブロックを作成"""
    try:
        with_retry(
            lambda: notion.blocks.children.append(
                block_id=page_id,
                children=[
                    {
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
                ]
            ),
            what="create new block"
        )
        return True
    except Exception as e:
        print(f"ブロック作成エラー: {e}")
        return False

def force_clean_page(page_id: str, page_title: str):
    """ページを強制的にクリーンアップ（ブロックを削除して再作成）"""
    print(f"強制クリーンアップ中: {page_title}")
    
    blocks = get_page_blocks(page_id)
    cleaned_blocks = []
    
    # 各ブロックの内容をクリーンアップ
    for block in blocks:
        if block.get("type") == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if rich_text:
                current_text = "".join([rt.get("plain_text", "") for rt in rich_text])
                cleaned_text = clean_garbage_text(current_text)
                
                if cleaned_text and cleaned_text != current_text:
                    cleaned_blocks.append(cleaned_text)
                    print(f"  クリーンアップ: {len(current_text)} → {len(cleaned_text)} 文字")
                elif cleaned_text:
                    cleaned_blocks.append(cleaned_text)
    
    if cleaned_blocks:
        print(f"  削除予定ブロック数: {len(blocks)}")
        print(f"  作成予定ブロック数: {len(cleaned_blocks)}")
        
        # 既存のブロックを全て削除
        for block in blocks:
            if block.get("type") == "paragraph":
                if delete_block(block["id"]):
                    print(f"  ブロック削除: {block['id']}")
                time.sleep(0.1)
        
        # クリーンアップされた内容で新しいブロックを作成
        for i, content in enumerate(cleaned_blocks):
            if create_new_block(page_id, content):
                print(f"  ブロック作成: {i+1}/{len(cleaned_blocks)}")
            time.sleep(0.1)
        
        print(f"  強制クリーンアップ完了")
        return True
    else:
        print(f"  クリーンアップ不要でした")
        return False

def main():
    """メイン処理"""
    print("=== 特定ページの強制クリーンアップツール ===")
    
    # 対象ページのタイトル
    target_title = "横須賀 常光寺 ルート"
    
    # ページを検索
    print(f"ページを検索中: {target_title}")
    page_id = find_page_by_title(target_title)
    
    if page_id:
        print(f"ページID: {page_id}")
        print()
        
        # 強制クリーンアップ実行
        force_clean_page(page_id, target_title)
    else:
        print("ページが見つかりませんでした。")

if __name__ == "__main__":
    main()
