#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recreate With Correct Newlines - 正しい改行でページを再作成
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

def create_page_with_correct_newlines(title: str) -> str:
    """正しい改行でページを作成"""
    try:
        # 正しい改行でコンテンツを構築
        children = [
            # メッセージ数
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "📊 メッセージ数: 2"
                            }
                        }
                    ]
                }
            },
            # 空行1
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            },
            # 空行2
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            },
            # ユーザーメッセージ
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "【ユーザー (2025-03-29 04:46:09)】"
                            }
                        }
                    ]
                }
            },
            # ユーザーの質問
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "自宅から横須賀の常光寺までのルート、明日11:00に到着したい。"
                            }
                        }
                    ]
                }
            },
            # 空行1
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            },
            # 空行2
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            },
            # アシスタント
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "【アシスタント (2025-03-29 04:46:11)】"
                            }
                        }
                    ]
                }
            },
            # アシスタントの回答
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "ご自宅から横須賀市の常光寺まで、明日11:00に到着するためのルートをご案内いたします。以下の情報を参考にしてください。"
                            }
                        }
                    ]
                }
            },
            # 空行1
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            },
            # 空行2
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            },
            # 電車での移動
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "**電車での移動:**"
                            }
                        }
                    ]
                }
            },
            # 電車の説明
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "藤沢駅から横須賀駅までの電車の乗り換え案内は、NAVITIMEなどの乗り換え案内サービスで確認できます。"
                            }
                        }
                    ]
                }
            },
            # 空行1
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            },
            # 空行2
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            },
            # 車での移動
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "**車での移動:**"
                            }
                        }
                    ]
                }
            },
            # 車の説明
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "藤沢市から横須賀市への車でのルート検索も、NAVITIMEなどのルート検索サービスで確認できます。"
                            }
                        }
                    ]
                }
            },
            # 空行1
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            },
            # 空行2
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": []
                }
            },
            # 注意点
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "**注意点:**"
                            }
                        }
                    ]
                }
            },
            # 交通状況
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "- **交通状況:** 週末や祝日は道路が混雑する可能性があります。余裕を持った出発をおすすめします。"
                            }
                        }
                    ]
                }
            },
            # 天候
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "- **天候:** 天候によって交通状況が変わることがありますので、事前に天気予報を確認してください。"
                            }
                        }
                    ]
                }
            },
            # 駐車場
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "- **駐車場:** 常光寺周辺の駐車場情報を事前に確認し、必要に応じて予約を検討してください。"
                            }
                        }
                    ]
                }
            },
            # 最後の文章
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "最新の時刻表やルート情報は、公式の交通機関のウェブサイトやアプリでご確認ください。安全で快適なご旅行をお祈りしております。"
                            }
                        }
                    ]
                }
            }
        ]
        
        # ページ作成
        response = with_retry(
            lambda: notion.pages.create(
                parent={"database_id": CHATGPT_DB_ID},
                properties={
                    "名前": {
                        "title": [
                            {
                                "type": "text",
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                },
                children=children
            ),
            what="create page"
        )
        
        return response.get("id")
        
    except Exception as e:
        print(f"ページ作成エラー: {e}")
        return None

def main():
    """メイン処理"""
    print("=== 正しい改行でページを再作成 ===")
    
    # 横須賀 常光寺 ルートのページを検索
    page_title = "横須賀 常光寺 ルート"
    page_id = find_page_by_title(page_title)
    
    if page_id:
        print(f"既存のページを削除中: {page_title}")
        if delete_page(page_id):
            print("ページを削除しました")
            time.sleep(1)  # 削除の反映を待つ
        else:
            print("ページの削除に失敗しました")
            return
    
    print(f"新しいページを作成中: {page_title}")
    new_page_id = create_page_with_correct_newlines(page_title)
    
    if new_page_id:
        print(f"ページを作成しました: {new_page_id}")
        print("✅ 正しい改行でページが作成されました！")
        print("Notionで確認してください。")
    else:
        print("❌ ページの作成に失敗しました。")

if __name__ == "__main__":
    main()
