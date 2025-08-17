#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Chat Date Property - データベースに「チャット日時」プロパティを追加
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

def add_chat_date_property_to_database():
    """データベースに「チャット日時」プロパティを追加"""
    try:
        response = with_retry(
            lambda: notion.databases.update(
                database_id=CHATGPT_DB_ID,
                properties={
                    "チャット日時": {
                        "date": {}
                    }
                }
            ),
            what="add chat date property"
        )
        print("✅ 「チャット日時」プロパティをデータベースに追加しました")
        return True
    except Exception as e:
        print(f"❌ プロパティ追加エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("=== データベースに「チャット日時」プロパティを追加 ===")
    
    # プロパティを追加
    if add_chat_date_property_to_database():
        print("✅ 完了！Notionで確認してください。")
    else:
        print("❌ 失敗しました。")

if __name__ == "__main__":
    main()
