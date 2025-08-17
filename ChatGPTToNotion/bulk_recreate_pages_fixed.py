#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bulk Recreate Pages Fixed - 修正版全ページ一括再作成ツール
プロパティ形式を正しく設定して全ページを再作成します。
"""

import os
import sys
import re
import time
import json
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

def clean_garbage_text_comprehensive(text: str) -> str:
    """包括的なゴミ文字除去（改行は保持）"""
    # 様々なゴミ文字パターンを除去
    patterns_to_remove = [
        # 基本的なゴミ文字
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
        
        # 追加のゴミ文字パターン
        r'video',  # video文字列
        r'turn\d+search\d+',  # turn1search14 など
        r'search\d+',  # search14 など
        r'turn\d+',  # turn1 など
        
        # 特殊な空白文字や制御文字
        r'[\u200B-\u200D\uFEFF]',  # ゼロ幅文字
        r'[\u2060-\u2064\u206A-\u206F]',  # その他の制御文字
        
        # 不要な記号の組み合わせ
        r'[⬛⚫▶️◀️]+',  # 複数の記号の連続
    ]
    
    cleaned_text = text
    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    # 改行を保持しながら、過度な空白行のみを整理
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
    
    # 行頭行末の空白を除去（改行は保持）
    cleaned_text = re.sub(r'^\s+|\s+$', '', cleaned_text, flags=re.MULTILINE)
    
    # 連続する空白を1つに統一（改行は保持）
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
    
    return cleaned_text.strip()

def get_all_pages() -> List[Dict[str, Any]]:
    """データベースの全ページを取得"""
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

def delete_page(page_id: str) -> bool:
    """ページを削除（アーカイブ）"""
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

def create_clean_page(title: str, content: str, original_properties: Dict[str, Any]) -> str:
    """クリーンなページを作成"""
    try:
        # プロパティを正しい形式で設定
        page_properties = {}
        
        # タイトル（名前）
        page_properties["名前"] = {
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": title
                    }
                }
            ]
        }
        
        # URL（チャットID）
        if "URL" in original_properties:
            url_prop = original_properties["URL"]
            if url_prop.get("type") == "url" and url_prop.get("url"):
                page_properties["URL"] = {
                    "url": url_prop["url"]
                }
        
        # 最終更新日時（last_edited_time）
        if "最終更新日時" in original_properties:
            last_edited_prop = original_properties["最終更新日時"]
            if last_edited_prop.get("type") == "last_edited_time" and last_edited_prop.get("last_edited_time"):
                page_properties["最終更新日時"] = {
                    "last_edited_time": last_edited_prop["last_edited_time"]
                }
        
        # AI カスタム自動入力（空にする）
        page_properties["AI カスタム自動入力"] = {
            "rich_text": []
        }
        
        # AI 要約（空にする）
        page_properties["AI 要約"] = {
            "rich_text": []
        }
        
        # AI Model
        if "AI Model" in original_properties:
            model_prop = original_properties["AI Model"]
            if model_prop.get("type") == "multi_select" and model_prop.get("multi_select"):
                page_properties["AI Model"] = {
                    "multi_select": model_prop["multi_select"]
                }
        
        # ページ作成
        response = with_retry(
            lambda: notion.pages.create(
                parent={"database_id": CHATGPT_DB_ID},
                properties=page_properties,
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
            what="create page"
        )
        
        return response.get("id")
        
    except Exception as e:
        print(f"ページ作成エラー: {e}")
        return None

def backup_pages_to_file(pages: List[Dict[str, Any]], filename: str):
    """ページデータをファイルにバックアップ"""
    backup_data = []
    
    for page in pages:
        page_id = page["id"]
        
        # ページタイトルを取得
        title_prop = page.get("properties", {}).get("名前", {})
        title = ""
        if title_prop.get("type") == "title":
            title_parts = title_prop.get("title", [])
            title = "".join([part.get("plain_text", "") for part in title_parts])
        
        # ページの内容を取得
        blocks = get_page_blocks(page_id)
        content = ""
        if blocks:
            for block in blocks:
                if block.get("type") == "paragraph":
                    rich_text = block.get("paragraph", {}).get("rich_text", [])
                    if rich_text:
                        content += "".join([rt.get("plain_text", "") for rt in rich_text])
        
        backup_data.append({
            "id": page_id,
            "title": title,
            "content": content,
            "properties": page.get("properties", {})
        })
    
    # ファイルに保存
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print(f"バックアップを保存しました: {filename}")

def main():
    """メイン処理"""
    print("=== 修正版全ページ一括再作成ツール ===")
    print("⚠️  注意: この処理により、現在のページは全て削除され、クリーンな状態で再作成されます。")
    print()
    
    # 確認
    confirm = input("続行しますか？ (yes/no): ")
    if confirm.lower() != 'yes':
        print("処理を中止しました。")
        return
    
    print()
    print("1. 現在のページをバックアップ中...")
    pages = get_all_pages()
    print(f"取得したページ数: {len(pages)}")
    
    # バックアップファイルを作成
    backup_filename = f"pages_backup_{int(time.time())}.json"
    backup_pages_to_file(pages, backup_filename)
    
    print()
    print("2. ページを削除して再作成中...")
    
    recreated_count = 0
    failed_count = 0
    
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
        
        print(f"[{i}/{len(pages)}] 処理中: {title}")
        
        # ページの内容を取得
        blocks = get_page_blocks(page_id)
        content = ""
        if blocks:
            for block in blocks:
                if block.get("type") == "paragraph":
                    rich_text = block.get("paragraph", {}).get("rich_text", [])
                    if rich_text:
                        content += "".join([rt.get("plain_text", "") for rt in rich_text])
        
        # 内容をクリーンアップ
        if content:
            original_length = len(content)
            cleaned_content = clean_garbage_text_comprehensive(content)
            cleaned_length = len(cleaned_content)
            
            print(f"  元の内容長: {original_length} 文字")
            print(f"  クリーンアップ後: {cleaned_length} 文字")
            
            if original_length != cleaned_length:
                print(f"  内容が変更されました")
        
        # ページを削除
        if delete_page(page_id):
            print(f"  既存ページを削除しました")
            
            # 新しいページを作成
            new_page_id = create_clean_page(title, cleaned_content, page.get("properties", {}))
            if new_page_id:
                print(f"  新しいページを作成しました: {new_page_id}")
                recreated_count += 1
            else:
                print(f"  新しいページの作成に失敗しました")
                failed_count += 1
        else:
            print(f"  ページの削除に失敗しました")
            failed_count += 1
        
        # API制限を避ける
        time.sleep(0.5)
        print()
    
    print()
    print("=== 処理完了 ===")
    print(f"再作成したページ数: {recreated_count}")
    print(f"失敗したページ数: {failed_count}")
    print(f"バックアップファイル: {backup_filename}")
    print()
    print("⚠️  注意: バックアップファイルは安全のため保持されています。")
    print("問題がなければ、後で削除しても構いません。")

if __name__ == "__main__":
    main()
