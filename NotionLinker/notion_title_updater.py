# -*- coding: utf-8 -*-
"""
Notion 日記タイトル一括変更ツール
- 「2025-08-16」形式 → 「2025-0816」形式に変更
- DRY_RUN モードで事前確認可能
"""

import os, sys, time, random
from datetime import datetime
from typing import Optional, Dict, Any, List
import re

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError, RequestTimeoutError
except Exception:
    print("notion-client がありません。`pip install -r requirements.txt` を実行してください。")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
JOURNAL_DB_ID = os.getenv("JOURNAL_DB_ID")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")  # デフォルトはDRY_RUN
NOTION_TIMEOUT = int(os.getenv("NOTION_TIMEOUT", "60"))

if not NOTION_TOKEN or not JOURNAL_DB_ID:
    print("環境変数 NOTION_TOKEN / JOURNAL_DB_ID が未設定です。.env を確認。")
    sys.exit(1)

# Notion クライアント
notion = Client(auth=NOTION_TOKEN, timeout_ms=int(NOTION_TIMEOUT * 1000))

# ---------- リトライ付きAPI呼び出しユーティリティ ----------
def with_retry(fn, *, max_attempts=4, base_delay=1.0, what="api"):
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

# ---------- タイトル変換関数 ----------
def convert_title_format(old_title: str) -> str:
    """
    「2025-08-16」形式を「2025-0816」形式に変換
    """
    # 正規表現で「YYYY-MM-DD」形式を検出
    pattern = r'^(\d{4})-(\d{2})-(\d{2})$'
    match = re.match(pattern, old_title)
    
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}{day}"
    
    return old_title  # パターンに一致しない場合はそのまま返す

def needs_title_update(title: str) -> bool:
    """
    タイトルが更新が必要かどうかを判定
    「2025-XX-XX」形式（ハイフンあり）の場合は更新が必要
    """
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(pattern, title))

def extract_date_from_title(title: str) -> Optional[str]:
    """
    タイトルから日付を抽出
    「2025-0816」形式から「2025-08-16」形式の日付を生成
    """
    # 「2025-0816」形式を検出
    pattern = r'^(\d{4})-(\d{2})(\d{2})$'
    match = re.match(pattern, title)
    
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"
    
    # 「2025-08-16」形式を検出
    pattern2 = r'^(\d{4})-(\d{2})-(\d{2})$'
    match2 = re.match(pattern2, title)
    
    if match2:
        year, month, day = match2.groups()
        return f"{year}-{month}-{day}"
    
    return None

# ---------- データベース操作 ----------
def iter_database_pages(database_id: str):
    """データベース内の全ページを取得"""
    start_cursor = None
    while True:
        def _call():
            payload = {"database_id": database_id, "page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor
            return notion.databases.query(**payload)
        res = with_retry(_call, what="databases.query")
        for r in res.get("results", []):
            yield r
        if not res.get("has_more"):
            break
        start_cursor = res.get("next_cursor")

def get_page_title(page: Dict[str, Any]) -> Optional[str]:
    """ページのタイトルを取得"""
    props = page.get("properties", {})
    title_prop = props.get("タイトル")  # または実際のプロパティ名
    if not title_prop:
        return None
    
    title_content = title_prop.get("title", [])
    if not title_content:
        return None
    
    return "".join([span.get("plain_text", "") for span in title_content])

def update_page_title_and_date(page_id: str, new_title: str, date_value: Optional[str] = None):
    """ページのタイトルと日付を更新"""
    if DRY_RUN:
        print(f"[DRY-RUN] Update page {page_id}: title = '{new_title}', date = '{date_value}'")
        return
    
    properties = {
        "タイトル": {
            "title": [
                {
                    "type": "text",
                    "text": {"content": new_title}
                }
            ]
        }
    }
    
    # 日付プロパティも更新
    if date_value:
        properties["日付"] = {
            "date": {
                "start": date_value
            }
        }
    
    def _call():
        return notion.pages.update(
            page_id=page_id,
            properties=properties
        )
    return with_retry(_call, what="pages.update")

# ---------- メイン処理 ----------
def main():
    print("== Notion 日記タイトル一括変更ツール ==")
    print(f"DRY_RUN: {DRY_RUN}")
    print(f"対象データベース: {JOURNAL_DB_ID}")
    print()
    
    # 全ページを取得
    pages = list(iter_database_pages(JOURNAL_DB_ID))
    if not pages:
        print("対象ページはありません。")
        return
    
    print(f"対象ページ数: {len(pages)}")
    print()
    
    # モード選択
    print("実行モードを選択してください:")
    print("1. タイトル変更 + 日付設定（新規変更対象のみ）")
    print("2. 日付プロパティ修正（既に変更済みで日付が空のページ）")
    print("3. 両方実行")
    
    mode = input("モードを選択 (1/2/3): ").strip()
    if mode not in ['1', '2', '3']:
        print("無効な選択です。終了します。")
        return
    
    # 変更対象を確認
    target_pages = []
    date_fix_pages = []
    unchanged_count = 0
    empty_count = 0
    
    for page in pages:
        page_id = page["id"]
        current_title = get_page_title(page)
        
        if not current_title:
            empty_count += 1
            continue
        
        # 日付プロパティの確認
        props = page.get("properties", {})
        date_prop = props.get("日付", {})
        current_date = date_prop.get("date", {}).get("start") if date_prop.get("date") else None
        
        # 更新が必要かどうかを判定
        if needs_title_update(current_title):
            new_title = convert_title_format(current_title)
            date_value = extract_date_from_title(new_title)
            target_pages.append({
                "page_id": page_id,
                "old_title": current_title,
                "new_title": new_title,
                "date_value": date_value
            })
            print(f"[CHANGE] {current_title} → {new_title} (日付: {date_value})")
        else:
            # 既に変更済みで日付が空の場合
            if not current_date and extract_date_from_title(current_title):
                date_value = extract_date_from_title(current_title)
                date_fix_pages.append({
                    "page_id": page_id,
                    "title": current_title,
                    "date_value": date_value
                })
                print(f"[DATE_FIX] {current_title} (日付設定: {date_value})")
            else:
                unchanged_count += 1
                print(f"[SKIP] {current_title} (既に変更済みまたは形式が異なる)")
    
    print()
    print(f"=== 統計情報 ===")
    print(f"総ページ数: {len(pages)}")
    print(f"タイトル変更対象ページ数: {len(target_pages)}")
    print(f"日付修正対象ページ数: {len(date_fix_pages)}")
    print(f"既に変更済みページ数: {unchanged_count}")
    print(f"タイトルが空のページ数: {empty_count}")
    print()
    
    if mode in ['1', '3'] and not target_pages:
        print("タイトル変更対象のページはありません。")
    
    if mode in ['2', '3'] and not date_fix_pages:
        print("日付修正対象のページはありません。")
    
    if not target_pages and not date_fix_pages:
        print("すべてのページが既に適切な形式になっているか、変更不要な形式です。")
        return
    
    if DRY_RUN:
        print("\nDRY_RUN モードのため、実際の変更は行われません。")
        print("実際に変更するには、.env で DRY_RUN=false を設定してください。")
        return
    
    # 実際の変更実行
    print("\n実際の変更を開始します...")
    confirm = input("続行しますか？ (y/N): ")
    if confirm.lower() != 'y':
        print("キャンセルしました。")
        return
    
    # タイトル変更の実行
    if mode in ['1', '3'] and target_pages:
        print(f"\n=== タイトル変更の実行 ({len(target_pages)}件) ===")
        for i, target in enumerate(target_pages, 1):
            print(f"[{i}/{len(target_pages)}] {target['old_title']} → {target['new_title']} (日付: {target['date_value']})")
            update_page_title_and_date(target['page_id'], target['new_title'], target['date_value'])
            time.sleep(0.2)  # API制限対策
    
    # 日付修正の実行
    if mode in ['2', '3'] and date_fix_pages:
        print(f"\n=== 日付修正の実行 ({len(date_fix_pages)}件) ===")
        for i, fix_target in enumerate(date_fix_pages, 1):
            print(f"[{i}/{len(date_fix_pages)}] {fix_target['title']} (日付設定: {fix_target['date_value']})")
            update_page_title_and_date(fix_target['page_id'], fix_target['title'], fix_target['date_value'])
            time.sleep(0.2)  # API制限対策
    
    print("\n完了しました。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断しました。")
