#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recreate Page - ページ再作成ツール
指定したページを削除して、クリーンアップされた内容で再作成します。
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
        r'[^\x00-\x7F]+',  # 非ASCII文字（絵文字など）を除去
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

def get_page_properties(page_id: str) -> Dict[str, Any]:
    """ページのプロパティを取得"""
    try:
        response = with_retry(
            lambda: notion.pages.retrieve(page_id=page_id),
            what="get page properties"
        )
        return response.get("properties", {})
    except Exception as e:
        print(f"プロパティ取得エラー: {e}")
        return {}

def delete_page(page_id: str) -> bool:
    """ページを削除"""
    try:
        with_retry(
            lambda: notion.pages.update(
                page_id=page_id,
                archived=True
            ),
            what="delete page"
        )
        return True
    except Exception as e:
        print(f"ページ削除エラー: {e}")
        return False

def create_clean_page(title: str, content: str, properties: Dict[str, Any]) -> str:
    """クリーンアップされた内容で新しいページを作成"""
    try:
        # プロパティから必要な情報を抽出
        chat_id = None
        model = "ChatGPT"
        
        # URLプロパティからチャットIDを取得
        url_prop = properties.get("URL", {})
        if url_prop.get("type") == "url":
            url = url_prop.get("url", "")
            if url and "chat.openai.com/c/" in url:
                chat_id = url.split("/c/")[-1]
        
        # AI Modelプロパティからモデルを取得
        model_prop = properties.get("AI Model", {})
        if model_prop.get("type") == "multi_select":
            model_values = model_prop.get("multi_select", [])
            if model_values:
                model = model_values[0].get("name", "ChatGPT")
        
        # 新しいページを作成
        response = with_retry(
            lambda: notion.pages.create(
                parent={"database_id": CHATGPT_DB_ID},
                properties={
                    "名前": {"title": [{"text": {"content": title}}]},
                    "URL": {"url": f"https://chat.openai.com/c/{chat_id}" if chat_id else ""},
                    "AI カスタム自動入力": {"rich_text": []},
                    "AI Model": {"multi_select": [{"name": model}]}
                },
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
            what="create clean page"
        )
        
        return response["id"]
        
    except Exception as e:
        print(f"ページ作成エラー: {e}")
        return None

def recreate_page(page_id: str, page_title: str):
    """ページを再作成"""
    print(f"ページ再作成中: {page_title}")
    
    # 現在のページの内容を取得
    blocks = get_page_blocks(page_id)
    properties = get_page_properties(page_id)
    
    # 内容を結合してクリーンアップ
    original_content = ""
    for block in blocks:
        if block.get("type") == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            if rich_text:
                text_content = "".join([rt.get("plain_text", "") for rt in rich_text])
                original_content += text_content + "\n\n"
    
    # クリーンアップ
    cleaned_content = clean_garbage_text(original_content)
    
    print(f"  元の内容長: {len(original_content)} 文字")
    print(f"  クリーンアップ後: {len(cleaned_content)} 文字")
    
    if cleaned_content != original_content:
        print("  内容が変更されました")
        
        # 既存ページを削除
        if delete_page(page_id):
            print("  既存ページを削除しました")
            time.sleep(1)  # 削除完了を待つ
            
            # 新しいページを作成
            new_page_id = create_clean_page(page_title, cleaned_content, properties)
            if new_page_id:
                print(f"  新しいページを作成しました: {new_page_id}")
                return True
            else:
                print("  新しいページの作成に失敗しました")
                return False
        else:
            print("  既存ページの削除に失敗しました")
            return False
    else:
        print("  内容に変更はありませんでした")
        return False

def main():
    """メイン処理"""
    print("=== ページ再作成ツール ===")
    
    # 対象ページのタイトル
    target_title = "横須賀 常光寺 ルート"
    
    # ページを検索
    print(f"ページを検索中: {target_title}")
    page_id = find_page_by_title(target_title)
    
    if page_id:
        print(f"ページID: {page_id}")
        print()
        
        # ページを再作成
        if recreate_page(page_id, target_title):
            print("ページ再作成が完了しました。")
        else:
            print("ページ再作成に失敗しました。")
    else:
        print("ページが見つかりませんでした。")

if __name__ == "__main__":
    main()
