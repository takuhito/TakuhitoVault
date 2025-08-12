
# -*- coding: utf-8 -*-
"""
Notion Linker（再リンク対応 + リトライ/タイムアウト強化版）
- 既存リンクの付け替え対応
- Notion API のタイムアウト/レート制限時に自動リトライ
- タイムアウト秒数は環境変数 NOTION_TIMEOUT で調整（既定 60）
"""

import os, sys, time, random
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError, RequestTimeoutError
except Exception:
    print("notion-client がありません。`pip install -r requirements.txt` を実行してください。")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PAY_DB_ID = os.getenv("PAY_DB_ID")
JOURNAL_DB_ID = os.getenv("JOURNAL_DB_ID")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes")
NOTION_TIMEOUT = int(os.getenv("NOTION_TIMEOUT", "60"))  # 秒

# プロパティ名
PROP_PAY_DATE = os.getenv("PROP_PAY_DATE", "支払予定日")
PROP_MATCH_STR = os.getenv("PROP_MATCH_STR", "一致用日付")
PROP_REL_TO_JOURNAL = os.getenv("PROP_REL_TO_JOURNAL", "日記[予定日]")
PROP_JOURNAL_TITLE = os.getenv("PROP_JOURNAL_TITLE", "タイトル")

RECHECK_DAYS = int(os.getenv("RECHECK_DAYS", "90"))
SLEEP_BETWEEN = float(os.getenv("SLEEP_BETWEEN", "0.2"))

if not NOTION_TOKEN or not PAY_DB_ID or not JOURNAL_DB_ID:
    print("環境変数 NOTION_TOKEN / PAY_DB_ID / JOURNAL_DB_ID が未設定です。.env を確認。")
    sys.exit(1)

# --- Notion クライアント（タイムアウト指定）
# 秒 → ミリ秒に変換して timeout_ms を使う
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
            # レート制限など
            if getattr(e, "code", "") == "rate_limited":
                attempt += 1
                retry_after = float(getattr(e, "headers", {}).get("Retry-After", 1)) if hasattr(e, "headers") else 1.0
                delay = max(retry_after, base_delay * (2 ** (attempt-1))) + random.uniform(0, 0.5)
                print(f"[RETRY] rate_limited on {what}. retry {attempt}/{max_attempts} in {delay:.1f}s")
                time.sleep(delay)
                if attempt < max_attempts:
                    continue
            raise

# ---------- 値取り出し ----------
def get_prop_val(prop: Dict[str, Any]) -> Optional[Any]:
    t = prop.get("type")
    if t == "date":
        v = prop.get("date")
        return v.get("start") if v else None
    if t == "rich_text":
        return "".join([span.get("plain_text", "") for span in prop.get("rich_text", [])]) or None
    if t == "title":
        return "".join([span.get("plain_text", "") for span in prop.get("title", [])]) or None
    if t == "formula":
        f = prop.get("formula", {})
        typ = f.get("type")
        if typ == "string":
            return f.get("string")
        if typ == "number":
            return f.get("number")
        if typ == "boolean":
            return f.get("boolean")
        if typ == "date":
            d = f.get("date") or {}
            return d.get("start")
        return None
    if t == "relation":
        return prop.get("relation") or []
    return None

def get_page_prop(page: Dict[str, Any], prop_name: str) -> Dict[str, Any]:
    props = page.get("properties", {})
    if prop_name not in props:
        raise KeyError(f"プロパティ '{prop_name}' が見つかりません")
    return props[prop_name]

# ---------- DB操作 ----------
def iter_database_pages(database_id: str, filter_obj: Optional[Dict[str, Any]] = None):
    start_cursor = None
    while True:
        def _call():
            payload = {"database_id": database_id, "page_size": 100}
            if filter_obj:
                payload["filter"] = filter_obj
            if start_cursor:
                payload["start_cursor"] = start_cursor
            return notion.databases.query(**payload)
        res = with_retry(_call, what="databases.query")
        for r in res.get("results", []):
            yield r
        if not res.get("has_more"):
            break
        start_cursor = res.get("next_cursor")

def find_journal_by_match(match_text: str) -> Optional[Dict[str, Any]]:
    def _call():
        return notion.databases.query(
            **{
                "database_id": JOURNAL_DB_ID,
                "filter": {"property": PROP_MATCH_STR, "rich_text": {"equals": match_text}},
                "page_size": 1,
            }
        )
    res = with_retry(_call, what="journal.query")
    arr = res.get("results", [])
    return arr[0] if arr else None

def create_journal_page(match_text: str) -> Dict[str, Any]:
    props = {
        PROP_JOURNAL_TITLE: {"title": [{"type": "text", "text": {"content": match_text}}]},
        # 一致用日付は formula 想定のため書かない
    }
    if DRY_RUN:
        print(f"[DRY-RUN] Create Journal page: title={match_text}")
        return {"id": "dry-run-journal-id"}
    def _call():
        return notion.pages.create(**{"parent": {"database_id": JOURNAL_DB_ID}, "properties": props})
    return with_retry(_call, what="pages.create")

def set_relation(pay_page_id: str, journal_page_id: str):
    if DRY_RUN:
        print(f"[DRY-RUN] Set relation: {pay_page_id} -> {journal_page_id}")
        return
    def _call():
        return notion.pages.update(
            **{"page_id": pay_page_id, "properties": {PROP_REL_TO_JOURNAL: {"relation": [{"id": journal_page_id}]}}}
        )
    with_retry(_call, what="pages.update")

def retrieve_page(page_id: str) -> Dict[str, Any]:
    def _call():
        return notion.pages.retrieve(page_id=page_id)
    return with_retry(_call, what="pages.retrieve")

# ---------- メイン ----------
def main():
    print("== Notion Linker: 再リンク + リトライ版 ==")
    # 支払予定日が入っているページを期間制限で取得
    filter_obj = {"property": PROP_PAY_DATE, "date": {"is_not_empty": True}}
    if RECHECK_DAYS and RECHECK_DAYS > 0:
        since = (datetime.now(timezone.utc) - timedelta(days=RECHECK_DAYS)).date().isoformat()
        filter_obj = {
            "and": [
                {"property": PROP_PAY_DATE, "date": {"is_not_empty": True}},
                {"property": PROP_PAY_DATE, "date": {"on_or_after": since}},
            ]
        }

    pages = list(iter_database_pages(PAY_DB_ID, filter_obj))
    if not pages:
        print("対象ページはありません。")
        return

    print(f"対象ページ数: {len(pages)}")
    for i, page in enumerate(pages, 1):
        pay_page_id = page["id"]

        # 期待マッチ文字列
        try:
            match_prop = get_page_prop(page, PROP_MATCH_STR)
        except KeyError as e:
            print(f"[WARN] {e}; スキップ: {pay_page_id}")
            continue
        match_text = get_prop_val(match_prop)
        if not match_text:
            # フォールバック：日付から生成
            date_iso = get_prop_val(get_page_prop(page, PROP_PAY_DATE))
            match_text = date_iso[:10] if date_iso and len(date_iso) >= 10 else None
        if not match_text:
            print(f"[{i}/{len(pages)}] 一致用日付が空でスキップ")
            continue

        # 既存リレーション確認
        rel_prop = get_page_prop(page, PROP_REL_TO_JOURNAL)
        current_rel = get_prop_val(rel_prop)

        needs_link = False
        reason = "未リンク"
        if not current_rel:
            needs_link = True
        else:
            j_id = current_rel[0]["id"]
            jpage = retrieve_page(j_id)
            jprops = jpage.get("properties", {})
            jmatch = None
            if PROP_MATCH_STR in jprops:
                jmatch = get_prop_val(jprops[PROP_MATCH_STR])
            if not jmatch and PROP_JOURNAL_TITLE in jprops:
                jmatch = get_prop_val(jprops[PROP_JOURNAL_TITLE])
            if jmatch != match_text:
                needs_link = True
                reason = f"日付変更（現在:{jmatch}→期待:{match_text}）"

        if not needs_link:
            print(f"[{i}/{len(pages)}] 変更なし（スキップ）")
            continue

        print(f"[{i}/{len(pages)}] match='{match_text}' → DailyJournal を検索（理由:{reason}）")
        journal = find_journal_by_match(match_text)
        if not journal:
            print("  該当なし → 作成")
            journal = create_journal_page(match_text)

        new_id = journal["id"]
        print(f"  リレーション設定: {pay_page_id} -> {new_id}")
        set_relation(pay_page_id, new_id)
        time.sleep(SLEEP_BETWEEN)

    print("完了しました。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断しました。")
