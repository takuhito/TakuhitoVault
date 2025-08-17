#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix All Test Pages - テスト用の3ページすべてを正しい改行で修正
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

def create_page_with_proper_formatting(title: str, content_data: Dict[str, Any]) -> str:
    """適切なフォーマットでページを作成"""
    try:
        # バックアップデータからコンテンツを取得
        content = content_data.get("content", "")
        
        # 改行を適切に処理
        lines = content.split('\n')
        children = []
        
        for line in lines:
            line = line.strip()
            if line:  # 空でない行
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": line
                                }
                            }
                        ]
                    }
                })
            else:  # 空行（改行）は必ず追加
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": []
                    }
                })
        
        # セクション区切りの前後に追加の改行を挿入
        final_children = []
        for i, child in enumerate(children):
            final_children.append(child)
            
            # セクション区切りの後に追加の改行を挿入
            if i < len(children) - 1:
                current_text = ""
                if child.get("paragraph", {}).get("rich_text"):
                    current_text = child["paragraph"]["rich_text"][0].get("text", {}).get("content", "")
                
                next_text = ""
                if children[i+1].get("paragraph", {}).get("rich_text"):
                    next_text = children[i+1]["paragraph"]["rich_text"][0].get("text", {}).get("content", "")
                
                # セクション区切りのパターンを検出
                section_patterns = [
                    r'^電車での移動:$',
                    r'^車での移動:$',
                    r'^注意点:$',
                    r'^[^:]+:$',
                ]
                
                is_section_start = any(re.match(pattern, next_text) for pattern in section_patterns)
                
                # セクション区切りの前後に追加の改行を挿入
                if is_section_start:
                    # セクション区切りの前に追加の改行
                    final_children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": []
                        }
                    })
        
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
                children=final_children
            ),
            what="create page"
        )
        
        return response.get("id")
        
    except Exception as e:
        print(f"ページ作成エラー: {e}")
        return None

def load_backup_data(filename: str) -> List[Dict[str, Any]]:
    """バックアップファイルを読み込み"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"バックアップファイル読み込みエラー: {e}")
        return []

def main():
    """メイン処理"""
    print("=== テスト用の3ページすべてを修正 ===")
    
    # バックアップファイルを探す
    backup_files = [f for f in os.listdir('.') if f.startswith('pages_backup_') and f.endswith('.json')]
    
    if not backup_files:
        print("バックアップファイルが見つかりませんでした。")
        return
    
    # 最新のバックアップファイルを使用
    backup_file = sorted(backup_files)[-1]
    print(f"使用するバックアップファイル: {backup_file}")
    
    # バックアップデータを読み込み
    backup_data = load_backup_data(backup_file)
    if not backup_data:
        print("バックアップデータの読み込みに失敗しました。")
        return
    
    # テスト用の3ページを処理
    test_titles = ["横須賀 常光寺 ルート", "データに基づく提案", "Conversation Summary"]
    
    for title in test_titles:
        print(f"\n=== {title} を処理中 ===")
        
        # バックアップデータから該当するページを探す
        page_data = None
        for data in backup_data:
            if data.get("title") == title:
                page_data = data
                break
        
        if not page_data:
            print(f"バックアップデータに '{title}' が見つかりませんでした。")
            continue
        
        # 既存のページを削除
        existing_page_id = find_page_by_title(title)
        if existing_page_id:
            print(f"既存のページを削除中: {title}")
            if delete_page(existing_page_id):
                print("ページを削除しました")
                time.sleep(1)  # 削除の反映を待つ
            else:
                print("ページの削除に失敗しました")
                continue
        
        # 新しいページを作成
        print(f"新しいページを作成中: {title}")
        new_page_id = create_page_with_proper_formatting(title, page_data)
        
        if new_page_id:
            print(f"ページを作成しました: {new_page_id}")
        else:
            print("ページの作成に失敗しました")
        
        time.sleep(1)  # API制限を避ける
    
    print(f"\n=== 修正完了 ===")
    print("✅ テスト用の3ページすべてが正しい改行で修正されました！")
    print("Notionで確認してください。")

if __name__ == "__main__":
    main()
