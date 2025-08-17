#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Format and Cleanup - 書式修正とクリーンアップツール
改行を保持しながらページを修正し、他のページのゴミ文字も確認します。
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

def clean_garbage_text_properly(text: str) -> str:
    """適切にゴミ文字のみを除去（改行は保持）"""
    # 特定のゴミ文字パターンのみを除去（改行は保持）
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
        r'\*\*\.\*',  # **.** パターン
        r'_\s*\*\*\.\*',  # _ **.** パターン
    ]
    
    cleaned_text = text
    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    # 改行を保持しながら、過度な空白行のみを整理
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
    
    # 行頭行末の空白を除去（改行は保持）
    cleaned_text = re.sub(r'^\s+|\s+$', '', cleaned_text, flags=re.MULTILINE)
    
    return cleaned_text.strip()

def has_garbage_text(text: str) -> bool:
    """テキストにゴミ文字が含まれているかチェック"""
    garbage_patterns = [
        r'⬛', r'▶️', r'◀️', r'⚫', r'cite', r'turn0search\d+', r'⭐', r'\*\*\.\*'
    ]
    
    for pattern in garbage_patterns:
        if re.search(pattern, text):
            return True
    return False

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

def fix_yokosuka_page(page_id: str):
    """横須賀 常光寺 ルートページを正しい書式で修正"""
    print("横須賀 常光寺 ルートページを修正中...")
    
    # 正しい書式の内容
    correct_content = """📊 メッセージ数: 2

【ユーザー (2025-03-29 04:46:09)】
自宅から横須賀の常光寺までのルート、明日11:00に到着したい。

【アシスタント (2025-03-29 04:46:11)】
ご自宅から横須賀市の常光寺まで、明日11:00に到着するためのルートをご案内いたします。以下の情報を参考にしてください。

**電車での移動:**
藤沢駅から横須賀駅までの電車の乗り換え案内は、NAVITIMEなどの乗り換え案内サービスで確認できます。

**車での移動:**
藤沢市から横須賀市への車でのルート検索も、NAVITIMEなどのルート検索サービスで確認できます。

**注意点:**
- **交通状況:** 週末や祝日は道路が混雑する可能性があります。余裕を持った出発をおすすめします。
- **天候:** 天候によって交通状況が変わることがありますので、事前に天気予報を確認してください。
- **駐車場:** 常光寺周辺の駐車場情報を事前に確認し、必要に応じて予約を検討してください。

最新の時刻表やルート情報は、公式の交通機関のウェブサイトやアプリでご確認ください。安全で快適なご旅行をお祈りしております。"""
    
    blocks = get_page_blocks(page_id)
    if blocks:
        block = blocks[0]
        if block.get("type") == "paragraph":
            if update_block_content(block["id"], correct_content):
                print("  横須賀ページを正しい書式で修正しました")
                return True
            else:
                print("  横須賀ページの修正に失敗しました")
                return False
    return False

def check_and_fix_other_pages():
    """他のページのゴミ文字を確認して修正"""
    print("他のページのゴミ文字を確認中...")
    
    # 全ページを取得
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
        
        # 横須賀ページはスキップ
        if "横須賀 常光寺 ルート" in title:
            continue
        
        print(f"[{i}/{len(pages)}] 確認中: {title}")
        
        blocks = get_page_blocks(page_id)
        page_fixed = False
        
        for block in blocks:
            if block.get("type") == "paragraph":
                rich_text = block.get("paragraph", {}).get("rich_text", [])
                if rich_text:
                    current_text = "".join([rt.get("plain_text", "") for rt in rich_text])
                    
                    # ゴミ文字が含まれているかチェック
                    if has_garbage_text(current_text):
                        # クリーンアップ
                        cleaned_text = clean_garbage_text_properly(current_text)
                        
                        # 内容が変わった場合のみ更新
                        if cleaned_text != current_text:
                            if update_block_content(block["id"], cleaned_text):
                                print(f"  ブロック {block['id']} を修正しました")
                                page_fixed = True
                            time.sleep(0.1)  # API制限を避ける
        
        if page_fixed:
            fixed_count += 1
            print(f"  ページ '{title}' を修正しました")
        
        time.sleep(0.2)  # API制限を避ける
    
    print(f"修正したページ数: {fixed_count}")
    return fixed_count

def main():
    """メイン処理"""
    print("=== 書式修正とクリーンアップツール ===")
    
    # 1. 横須賀ページを修正
    print("1. 横須賀 常光寺 ルートページを修正中...")
    yokosuka_page_id = find_page_by_title("横須賀 常光寺 ルート")
    if yokosuka_page_id:
        fix_yokosuka_page(yokosuka_page_id)
    else:
        print("横須賀ページが見つかりませんでした。")
    
    print()
    
    # 2. 他のページのゴミ文字を確認して修正
    print("2. 他のページのゴミ文字を確認して修正中...")
    fixed_count = check_and_fix_other_pages()
    
    print()
    print(f"=== 処理完了 ===")
    print(f"修正したページ数: {fixed_count}")

if __name__ == "__main__":
    main()
