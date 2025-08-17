#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix All Pages Properly - すべてのページを正しく修正
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
        r'[\ue200-\ue2ff]',  # 制御文字（\ue200など）
        
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

def format_content_with_proper_newlines(content: str) -> str:
    """適切な改行処理でコンテンツをフォーマット"""
    # メッセージ数とユーザー名を分離
    content = re.sub(r'(📊 メッセージ数: \d+)(【ユーザー)', r'\1\n\n\2', content)
    
    # ユーザーとアシスタントの間に改行を追加
    content = re.sub(r'(【ユーザー[^】]*】)([^【\n])', r'\1\n\2', content)
    content = re.sub(r'(【アシスタント[^】]*】)([^【\n])', r'\1\n\2', content)
    
    # セクション区切りのパターンを検出して、適切な改行を追加
    section_patterns = [
        r'^電車での移動:$',
        r'^車での移動:$',
        r'^注意点:$',
        r'^[^:]+:$',
    ]
    
    lines = content.split('\n')
    formatted_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
            
        formatted_lines.append(line)
        
        # セクション区切りの前後に追加の改行を挿入
        is_section = any(re.match(pattern, line) for pattern in section_patterns)
        if is_section:
            # セクション区切りの前に改行を追加
            if i > 0 and lines[i-1].strip():
                formatted_lines.insert(-1, '')
            # セクション区切りの後に改行を追加
            if i < len(lines) - 1 and lines[i+1].strip():
                formatted_lines.append('')
    
    return '\n'.join(formatted_lines)

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
        
        # ゴミ文字を除去
        cleaned_content = clean_garbage_text_comprehensive(content)
        
        # 適切な改行処理
        formatted_content = format_content_with_proper_newlines(cleaned_content)
        
        # 改行を明示的に処理
        lines = formatted_content.split('\n')
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
    print("=== すべてのページを正しく修正 ===")
    
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
    
    print(f"修正対象ページ数: {len(backup_data)}")
    print()
    
    # 既に正しく修正されているページをスキップ
    skip_titles = ["横須賀 常光寺 ルート", "データに基づく提案", "Conversation Summary"]
    
    fixed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, page_data in enumerate(backup_data, 1):
        title = page_data.get("title", f"ページ {i}")
        
        # 既に正しく修正されているページをスキップ
        if title in skip_titles:
            print(f"[{i}/{len(backup_data)}] スキップ: {title} (既に修正済み)")
            skipped_count += 1
            continue
        
        print(f"[{i}/{len(backup_data)}] 修正中: {title}")
        
        # 既存のページを削除
        existing_page_id = find_page_by_title(title)
        if existing_page_id:
            print(f"  既存のページを削除中...")
            if delete_page(existing_page_id):
                print(f"  ページを削除しました")
                time.sleep(1)  # 削除の反映を待つ
            else:
                print(f"  ページの削除に失敗しました")
                failed_count += 1
                continue
        
        # 新しいページを作成
        print(f"  新しいページを作成中...")
        new_page_id = create_page_with_proper_formatting(title, page_data)
        
        if new_page_id:
            print(f"  ページを作成しました: {new_page_id}")
            fixed_count += 1
        else:
            print(f"  ページの作成に失敗しました")
            failed_count += 1
        
        # API制限を避ける
        time.sleep(0.5)
        
        # 進捗表示（10ページごと）
        if i % 10 == 0:
            print(f"  進捗: {i}/{len(backup_data)} ページ完了")
    
    print()
    print("=== 修正完了 ===")
    print(f"修正したページ数: {fixed_count}")
    print(f"失敗したページ数: {failed_count}")
    print(f"スキップしたページ数: {skipped_count}")
    
    if fixed_count > 0:
        print("✅ 修正成功！すべてのページが正しく修正されました。")
        print("Notionで確認してください。")
    else:
        print("❌ 修正失敗。問題を確認してください。")

if __name__ == "__main__":
    main()
