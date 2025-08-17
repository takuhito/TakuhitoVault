#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Set Chat Dates - チャット内容から日時を抽出して「チャット日時」プロパティに設定
"""

import os
import sys
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

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
            what="get page blocks"
        )
        return response.get("results", [])
    except Exception as e:
        print(f"ブロック取得エラー: {e}")
        return []

def extract_chat_date_from_content(content: str) -> Optional[str]:
    """チャット内容から日時を抽出"""
    # パターン1: 【ユーザー (YYYY-MM-DD HH:MM:SS)】
    pattern1 = r'【ユーザー\s*\((\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\)】'
    match1 = re.search(pattern1, content)
    if match1:
        return match1.group(1)
    
    # パターン2: 【アシスタント (YYYY-MM-DD HH:MM:SS)】
    pattern2 = r'【アシスタント\s*\((\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\)】'
    match2 = re.search(pattern2, content)
    if match2:
        return match2.group(1)
    
    # パターン3: --- YYYY-MM-DD 追加メッセージ ---
    pattern3 = r'---\s*(\d{4}-\d{2}-\d{2})\s+追加メッセージ\s+---'
    match3 = re.search(pattern3, content)
    if match3:
        return f"{match3.group(1)} 00:00:00"
    
    return None

def parse_date_string(date_str: str) -> Optional[str]:
    """日時文字列をISO形式に変換"""
    try:
        # YYYY-MM-DD HH:MM:SS 形式を解析
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.isoformat() + "Z"
    except ValueError:
        try:
            # YYYY-MM-DD 形式を解析
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.isoformat() + "Z"
        except ValueError:
            print(f"日時解析エラー: {date_str}")
            return None

def update_page_chat_date(page_id: str, date_iso: str) -> bool:
    """ページのチャット日時を更新"""
    try:
        with_retry(
            lambda: notion.pages.update(
                page_id=page_id,
                properties={
                    "チャット日時": {
                        "date": {
                            "start": date_iso
                        }
                    }
                }
            ),
            what="update chat date"
        )
        return True
    except Exception as e:
        print(f"チャット日時更新エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("=== チャット日時を「チャット日時」プロパティに設定 ===")
    
    # 現在のページを取得
    print("現在のページ一覧を取得中...")
    current_pages = get_all_pages()
    print(f"取得したページ数: {len(current_pages)}")
    
    updated_count = 0
    failed_count = 0
    no_date_count = 0
    
    for i, page in enumerate(current_pages, 1):
        title = page.get("properties", {}).get("名前", {}).get("title", [])
        title_text = title[0].get("plain_text", "タイトルなし") if title else "タイトルなし"
        
        print(f"[{i}/{len(current_pages)}] 処理中: {title_text}")
        
        # ページのブロックを取得
        page_id = page.get("id")
        blocks = get_page_blocks(page_id)
        
        # ブロックからコンテンツを抽出
        content = ""
        for block in blocks:
            if block.get("type") == "paragraph":
                rich_text = block.get("paragraph", {}).get("rich_text", [])
                for text in rich_text:
                    content += text.get("plain_text", "")
                content += "\n"
        
        # チャット日時を抽出
        chat_date = extract_chat_date_from_content(content)
        
        if chat_date:
            # 日時をISO形式に変換
            date_iso = parse_date_string(chat_date)
            
            if date_iso:
                # チャット日時を更新
                if update_page_chat_date(page_id, date_iso):
                    print(f"  チャット日時を設定しました: {chat_date}")
                    updated_count += 1
                else:
                    print(f"  チャット日時の設定に失敗しました")
                    failed_count += 1
            else:
                print(f"  日時形式が不正です: {chat_date}")
                failed_count += 1
        else:
            print(f"  チャット日時が見つかりませんでした")
            no_date_count += 1
        
        # API制限を避ける
        time.sleep(0.1)
        
        # 進捗表示（10ページごと）
        if i % 10 == 0:
            print(f"  進捗: {i}/{len(current_pages)} ページ完了")
    
    print()
    print("=== 設定完了 ===")
    print(f"設定したページ数: {updated_count}")
    print(f"失敗したページ数: {failed_count}")
    print(f"日時が見つからなかったページ数: {no_date_count}")
    
    if updated_count > 0:
        print("✅ チャット日時の設定成功！")
        print("Notionで確認してください。")
    else:
        print("❌ 設定失敗。問題を確認してください。")

if __name__ == "__main__":
    main()
