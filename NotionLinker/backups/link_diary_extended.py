# -*- coding: utf-8 -*-
"""
Notion Linker 拡張版（4つの新しいデータベース対応）
- 既存の「支払管理」データベースに加えて、4つの新しいデータベースをサポート
- マイリンク、YouTube要約、AI Chat管理、行動の各データベースとDailyJournalを関連付け
- 既存リンクの付け替え対応
- Notion API のタイムアウト/レート制限時に自動リトライ
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

# 基本設定
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
JOURNAL_DB_ID = os.getenv("JOURNAL_DB_ID")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes")
NOTION_TIMEOUT = int(os.getenv("NOTION_TIMEOUT", "60"))  # 秒

# データベース設定
DATABASES = {
    "支払管理": {
        "db_id": os.getenv("PAY_DB_ID"),
        "date_prop": os.getenv("PROP_PAY_DATE", "支払予定日"),
        "relation_prop": os.getenv("PROP_REL_TO_JOURNAL", "日記[予定日]")
    },
    "マイリンク": {
        "db_id": os.getenv("MYLINK_DB_ID", "1f3b061dadf381c6a903fc15741f7d06"),
        "date_prop": os.getenv("PROP_MYLINK_DATE", "完了させた日"),
        "relation_prop": os.getenv("PROP_MYLINK_REL", "完了させた日")
    },
    "YouTube要約": {
        "db_id": os.getenv("YOUTUBE_DB_ID", "205b061dadf3803e83d1f67d8d81a215"),
        "date_prop": os.getenv("PROP_YOUTUBE_DATE", "日記"),
        "relation_prop": os.getenv("PROP_YOUTUBE_REL", "日記")
    },
    "AI Chat管理": {
        "db_id": os.getenv("AICHAT_DB_ID", "1fdb061dadf380f8846df9d89aa6e988"),
        "date_prop": os.getenv("PROP_AICHAT_DATE", "取得日"),
        "relation_prop": os.getenv("PROP_AICHAT_REL", "取得日")
    },
    "行動": {
        "db_id": os.getenv("ACTION_DB_ID", "1feb061dadf380d19988d10d8bf0e56d"),
        "date_prop": os.getenv("PROP_ACTION_DATE", "行動日"),
        "relation_prop": os.getenv("PROP_ACTION_REL", "行動日")
    }
}

# 共通プロパティ名
PROP_MATCH_STR = os.getenv("PROP_MATCH_STR", "一致用日付")
PROP_JOURNAL_TITLE = os.getenv("PROP_JOURNAL_TITLE", "タイトル")

RECHECK_DAYS = int(os.getenv("RECHECK_DAYS", "90"))
SLEEP_BETWEEN = float(os.getenv("SLEEP_BETWEEN", "0.2"))

# 必須設定の確認
if not NOTION_TOKEN or not JOURNAL_DB_ID:
    print("環境変数 NOTION_TOKEN / JOURNAL_DB_ID が未設定です。.env を確認。")
    sys.exit(1)

# 有効なデータベースのみフィルタ
ACTIVE_DATABASES = {}
for name, config in DATABASES.items():
    if config["db_id"]:
        ACTIVE_DATABASES[name] = config
    else:
        print(f"[WARN] {name}のDB-IDが未設定です。スキップします。")

if not ACTIVE_DATABASES:
    print("有効なデータベースがありません。.env でDB-IDを設定してください。")
    sys.exit(1)

# --- Notion クライアント（タイムアウト指定）
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
    # まず一致用日付プロパティで検索
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
    if arr:
        return arr[0]
    
    # 一致用日付で見つからない場合、タイトルで検索
    import re
    pattern = r'^(\d{4})-(\d{2})-(\d{2})$'
    match = re.match(pattern, match_text)
    if match:
        year, month, day = match.groups()
        title_format = f"{year}-{month}{day}"
        
        def _call2():
            return notion.databases.query(
                **{
                    "database_id": JOURNAL_DB_ID,
                    "filter": {"property": PROP_JOURNAL_TITLE, "title": {"equals": title_format}},
                    "page_size": 1,
                }
            )
        res2 = with_retry(_call2, what="journal.query")
        arr2 = res2.get("results", [])
        if arr2:
            return arr2[0]
    
    return None

def create_journal_page(match_text: str) -> Dict[str, Any]:
    import re
    pattern = r'^(\d{4})-(\d{2})-(\d{2})$'
    match = re.match(pattern, match_text)
    if match:
        year, month, day = match.groups()
        title_format = f"{year}-{month}{day}"
    else:
        title_format = match_text
    
    props = {
        PROP_JOURNAL_TITLE: {"title": [{"type": "text", "text": {"content": title_format}}]},
    }
    if DRY_RUN:
        print(f"[DRY-RUN] Create Journal page: title={title_format} (from {match_text})")
        return {"id": "dry-run-journal-id"}
    def _call():
        return notion.pages.create(**{"parent": {"database_id": JOURNAL_DB_ID}, "properties": props})
    return with_retry(_call, what="pages.create")

def set_relation(page_id: str, journal_page_id: str, relation_prop: str):
    if DRY_RUN:
        print(f"[DRY-RUN] Set relation: {page_id} -> {journal_page_id} (prop: {relation_prop})")
        return
    def _call():
        return notion.pages.update(
            **{"page_id": page_id, "properties": {relation_prop: {"relation": [{"id": journal_page_id}]}}}
        )
    with_retry(_call, what="pages.update")

def retrieve_page(page_id: str) -> Dict[str, Any]:
    def _call():
        return notion.pages.retrieve(page_id=page_id)
    return with_retry(_call, what="pages.retrieve")

# ---------- データベース処理 ----------
def process_database(db_name: str, db_config: Dict[str, str]):
    print(f"\n=== {db_name} データベース処理開始 ===")
    
    # 日付プロパティが入っているページを期間制限で取得
    filter_obj = {"property": db_config["date_prop"], "date": {"is_not_empty": True}}
    if RECHECK_DAYS and RECHECK_DAYS > 0:
        since = (datetime.now(timezone.utc) - timedelta(days=RECHECK_DAYS)).date().isoformat()
        filter_obj = {
            "and": [
                {"property": db_config["date_prop"], "date": {"is_not_empty": True}},
                {"property": db_config["date_prop"], "date": {"on_or_after": since}},
            ]
        }

    pages = list(iter_database_pages(db_config["db_id"], filter_obj))
    if not pages:
        print(f"{db_name}: 対象ページはありません。")
        return

    print(f"{db_name}: 対象ページ数: {len(pages)}")
    processed_count = 0
    
    for i, page in enumerate(pages, 1):
        page_id = page["id"]

        # 期待マッチ文字列
        try:
            match_prop = get_page_prop(page, PROP_MATCH_STR)
        except KeyError as e:
            print(f"[WARN] {e}; スキップ: {page_id}")
            continue
        match_text = get_prop_val(match_prop)
        if not match_text:
            # フォールバック：日付から生成
            date_iso = get_prop_val(get_page_prop(page, db_config["date_prop"]))
            match_text = date_iso[:10] if date_iso and len(date_iso) >= 10 else None
        if not match_text:
            print(f"[{i}/{len(pages)}] 一致用日付が空でスキップ")
            continue

        # 既存リレーション確認
        rel_prop = get_page_prop(page, db_config["relation_prop"])
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
            
            # 日付形式の比較
            import re
            def normalize_date(date_str):
                if not date_str:
                    return None
                pattern = r'^(\d{4})-(\d{2})(\d{2})$'
                match = re.match(pattern, date_str)
                if match:
                    year, month, day = match.groups()
                    return f"{year}-{month}-{day}"
                return date_str
            
            normalized_jmatch = normalize_date(jmatch)
            normalized_match_text = normalize_date(match_text)
            
            if normalized_jmatch != normalized_match_text:
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
        print(f"  リレーション設定: {page_id} -> {new_id}")
        set_relation(page_id, new_id, db_config["relation_prop"])
        processed_count += 1
        time.sleep(SLEEP_BETWEEN)

    print(f"{db_name}: {processed_count}件処理完了")

# ---------- メイン ----------
def main():
    print("== Notion Linker 拡張版: 4つの新しいデータベース対応 ==")
    print(f"有効なデータベース: {', '.join(ACTIVE_DATABASES.keys())}")
    
    for db_name, db_config in ACTIVE_DATABASES.items():
        try:
            process_database(db_name, db_config)
        except Exception as e:
            print(f"[ERROR] {db_name}の処理中にエラーが発生: {e}")
            continue

    print("\n全てのデータベースの処理が完了しました。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断しました。")
