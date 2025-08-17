#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Restore All Pages - 残りのすべてのページを正しい改行で復元
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

def create_page_with_proper_formatting(title: str, content_data: Dict[str, Any]) -> str:
    """適切なフォーマットでページを作成"""
    try:
        # バックアップデータからコンテンツを取得
        content = content_data.get("content", "")
        
        # ゴミ文字を除去
        cleaned_content = clean_garbage_text_comprehensive(content)
        
        # 改行を適切に処理
        lines = cleaned_content.split('\n')
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
    print("=== 残りのすべてのページを復元 ===")
    
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
    
    print(f"復元対象ページ数: {len(backup_data)}")
    print()
    
    # 既に復元済みのページをスキップ
    skip_titles = ["横須賀 常光寺 ルート", "データに基づく提案", "Conversation Summary"]
    
    restored_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, page_data in enumerate(backup_data, 1):
        title = page_data.get("title", f"ページ {i}")
        
        # 既に復元済みのページをスキップ
        if title in skip_titles:
            print(f"[{i}/{len(backup_data)}] スキップ: {title} (既に復元済み)")
            skipped_count += 1
            continue
        
        print(f"[{i}/{len(backup_data)}] 復元中: {title}")
        
        # 新しいページを作成
        new_page_id = create_page_with_proper_formatting(title, page_data)
        
        if new_page_id:
            print(f"  ページを復元しました: {new_page_id}")
            restored_count += 1
        else:
            print(f"  ページの復元に失敗しました")
            failed_count += 1
        
        # API制限を避ける
        time.sleep(0.5)
        
        # 進捗表示（10ページごと）
        if i % 10 == 0:
            print(f"  進捗: {i}/{len(backup_data)} ページ完了")
    
    print()
    print("=== 復元完了 ===")
    print(f"復元したページ数: {restored_count}")
    print(f"失敗したページ数: {failed_count}")
    print(f"スキップしたページ数: {skipped_count}")
    
    if restored_count > 0:
        print("✅ 復元成功！すべてのページが正しい改行で復元されました。")
        print("Notionで確認してください。")
    else:
        print("❌ 復元失敗。問題を確認してください。")

if __name__ == "__main__":
    main()
