# -*- coding: utf-8 -*-
"""
Notion 日記ページ自動生成ツール
- 2025年8月16日以降から2027年3月末日までで、日記のページが作成されていない日のページを自動生成
- 安全のため、DRY_RUN モードで事前確認可能
"""

import os, sys, time, random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set

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
    title_prop = props.get("タイトル")
    if not title_prop:
        return None
    
    title_content = title_prop.get("title", [])
    if not title_content:
        return None
    
    return "".join([span.get("plain_text", "") for span in title_content])

def extract_date_from_title(title: str) -> Optional[datetime]:
    """タイトルから日付を抽出"""
    import re
    
    # 「2025-0816」形式を検出
    pattern = r'^(\d{4})-(\d{2})(\d{2})$'
    match = re.match(pattern, title)
    
    if match:
        year, month, day = match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            return None
    
    # 「2025-08-16」形式を検出
    pattern2 = r'^(\d{4})-(\d{2})-(\d{2})$'
    match2 = re.match(pattern2, title)
    
    if match2:
        year, month, day = match2.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            return None
    
    return None

def create_journal_page(date: datetime) -> Dict[str, Any]:
    """日記ページを作成"""
    # タイトル形式: 「2025-0816」
    title = date.strftime("%Y-%m%d")
    # 日付形式: 「2025-08-16」
    date_str = date.strftime("%Y-%m-%d")
    
    if DRY_RUN:
        print(f"[DRY-RUN] Create page: title={title}, date={date_str}")
        return {"id": f"dry-run-{title}"}
    
    properties = {
        "タイトル": {
            "title": [
                {
                    "type": "text",
                    "text": {"content": title}
                }
            ]
        },
        "日付": {
            "date": {
                "start": date_str
            }
        }
    }
    
    def _call():
        return notion.pages.create(
            parent={"database_id": JOURNAL_DB_ID},
            properties=properties
        )
    return with_retry(_call, what="pages.create")

# ---------- 日付生成・検証ロジック ----------
def generate_date_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    """指定期間の日付リストを生成"""
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    return dates

def get_existing_dates(pages: List[Dict[str, Any]]) -> Set[datetime]:
    """既存のページから日付を抽出"""
    existing_dates = set()
    
    for page in pages:
        title = get_page_title(page)
        if title:
            date = extract_date_from_title(title)
            if date:
                existing_dates.add(date)
    
    return existing_dates

def find_missing_dates(start_date: datetime, end_date: datetime, existing_dates: Set[datetime]) -> List[datetime]:
    """不足している日付を検出"""
    all_dates = generate_date_range(start_date, end_date)
    missing_dates = [date for date in all_dates if date not in existing_dates]
    return missing_dates

# ---------- メイン処理 ----------
def main():
    print("== Notion 日記ページ自動生成ツール ==")
    print(f"DRY_RUN: {DRY_RUN}")
    print(f"対象データベース: {JOURNAL_DB_ID}")
    print()
    
    # 期間設定
    start_date = datetime(2025, 8, 16)
    end_date = datetime(2027, 3, 31)
    
    print(f"対象期間: {start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}")
    print()
    
    # 既存ページを取得
    print("既存ページを取得中...")
    pages = list(iter_database_pages(JOURNAL_DB_ID))
    print(f"既存ページ数: {len(pages)}")
    
    # 既存の日付を抽出
    print("既存日付を分析中...")
    existing_dates = get_existing_dates(pages)
    print(f"既存日付数: {len(existing_dates)}")
    
    # 不足している日付を検出
    print("不足日付を検出中...")
    missing_dates = find_missing_dates(start_date, end_date, existing_dates)
    
    if not missing_dates:
        print("不足している日付はありません。すべての日付のページが既に存在します。")
        return
    
    print(f"不足日付数: {len(missing_dates)}")
    print()
    
    # 不足日付の詳細表示
    print("=== 不足している日付 ===")
    for i, date in enumerate(missing_dates[:10], 1):  # 最初の10件を表示
        print(f"{i:3d}. {date.strftime('%Y-%m-%d')} ({date.strftime('%Y-%m%d')})")
    
    if len(missing_dates) > 10:
        print(f"... 他 {len(missing_dates) - 10} 件")
    
    print()
    print(f"=== 統計情報 ===")
    print(f"対象期間: {start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}")
    print(f"総日数: {(end_date - start_date).days + 1}")
    print(f"既存ページ数: {len(existing_dates)}")
    print(f"不足日付数: {len(missing_dates)}")
    print(f"作成予定ページ数: {len(missing_dates)}")
    print()
    
    if DRY_RUN:
        print("DRY_RUN モードのため、実際の作成は行われません。")
        print("実際に作成するには、.env で DRY_RUN=false を設定してください。")
        return
    
    # 実際の作成実行
    print("実際のページ作成を開始します...")
    confirm = input("続行しますか？ (y/N): ")
    if confirm.lower() != 'y':
        print("キャンセルしました。")
        return
    
    print(f"\n=== ページ作成の実行 ({len(missing_dates)}件) ===")
    created_count = 0
    error_count = 0
    
    for i, date in enumerate(missing_dates, 1):
        try:
            print(f"[{i}/{len(missing_dates)}] 作成: {date.strftime('%Y-%m-%d')} ({date.strftime('%Y-%m%d')})")
            result = create_journal_page(date)
            created_count += 1
            print(f"  成功: {result['id']}")
        except Exception as e:
            error_count += 1
            print(f"  エラー: {e}")
        
        time.sleep(0.2)  # API制限対策
        
        # 進捗表示（10件ごと）
        if i % 10 == 0:
            print(f"  進捗: {i}/{len(missing_dates)} ({i/len(missing_dates)*100:.1f}%)")
    
    print()
    print("=== 作成完了 ===")
    print(f"作成成功: {created_count}件")
    print(f"作成失敗: {error_count}件")
    print(f"合計: {created_count + error_count}件")
    
    if error_count > 0:
        print("\n注意: 一部のページの作成に失敗しました。")
        print("エラーの詳細を確認して、必要に応じて再実行してください。")
    
    print("\n完了しました。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断しました。")
