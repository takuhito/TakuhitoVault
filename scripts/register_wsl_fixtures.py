#!/usr/bin/env python3
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

try:
    from notion_client import Client  # type: ignore
except Exception as e:
    print("notion_client が見つかりません。'pip install notion-client python-dotenv' を先に実行してください。")
    raise


def load_env():
    if load_dotenv:
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.local"))
    # Fallback to environment only if dotenv is not available


def jst_iso(dt_str: str) -> str:
    """Return ISO8601 with +09:00 from input 'YYYY-MM-DD HH:MM' (JST)."""
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    # Append +09:00 timezone offset explicitly
    return dt.strftime("%Y-%m-%dT%H:%M:00+09:00")


def add_two_hours_iso_end(start_val: str) -> str:
    """Compute end ISO string (+2h) from a Notion date.start value.
    Supports formats with milliseconds and timezone offset like '+09:00' or 'Z'.
    """
    try:
        if start_val.endswith("Z"):
            # Try milliseconds then seconds
            try:
                base_dt = datetime.strptime(start_val, "%Y-%m-%dT%H:%M:%S.%fZ")
            except Exception:
                base_dt = datetime.strptime(start_val, "%Y-%m-%dT%H:%M:%SZ")
            end_dt = base_dt + timedelta(hours=2)
            return end_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"  # keep millis precision
        else:
            offset = start_val[-6:]
            base = start_val[:-6]
            # Try milliseconds then seconds
            try:
                base_dt = datetime.strptime(base, "%Y-%m-%dT%H:%M:%S.%f")
            except Exception:
                base_dt = datetime.strptime(base, "%Y-%m-%dT%H:%M:%S")
            end_dt = base_dt + timedelta(hours=2)
            return end_dt.strftime("%Y-%m-%dT%H:%M:%S") + offset
    except Exception:
        # As a fallback, return start_val unchanged (caller may skip)
        return start_val


def build_fixtures() -> List[Dict[str, Any]]:
    """Hard-coded early-season fixtures for 2025/26 WSL (JST times).

    Note: Sources gathered from public listings; times may change. Update as needed.
    """
    source_footboom = "https://www.footboom1.com/jp/football/team/manchester-city-women"
    source_lfc = "https://www.liverpoolfc.com/ja/news/revealed-liverpool-fc-womens-wsl-fixture-list-2025-26"

    rows = [
        {"date": "2025-09-05 11:30", "opponent": "チェルシー", "home": False, "source": source_footboom},
        {"date": "2025-09-12 11:30", "opponent": "ブライトン＆ホーヴ・アルビオン", "home": True, "source": source_footboom},
        {"date": "2025-09-19 11:30", "opponent": "トッテナム・ホットスパー", "home": False, "source": source_footboom},
        {"date": "2025-09-24 11:00", "opponent": "エヴァートン", "home": True, "source": source_footboom},
        {"date": "2025-09-28 04:00", "opponent": "ロンドン・シティ・ライオネッセス", "home": True, "source": source_footboom},
        {"date": "2025-10-03 11:00", "opponent": "アーセナル", "home": True, "source": source_footboom},
        {"date": "2025-10-12 06:00", "opponent": "リヴァプール", "home": False, "source": source_lfc},
        {"date": "2025-10-19 06:00", "opponent": "ニューカッスル・ユナイテッド", "home": False, "source": source_footboom},
        {"date": "2025-11-02 05:00", "opponent": "ウェストハム・ユナイテッド", "home": True, "source": source_footboom},
        {"date": "2025-11-09 07:00", "opponent": "エヴァートン", "home": False, "source": source_footboom},
    ]

    fixtures: List[Dict[str, Any]] = []
    for r in rows:
        start_iso = jst_iso(r["date"])  # JST
        # End time = start + 2h (soccer rule per user's convention)
        start_dt = datetime.strptime(r["date"], "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(hours=2)
        end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:00+09:00")

        time_text = start_dt.strftime("%H:%M")
        title = f"⚽️{time_text} WSL マンチェスター・シティ vs {r['opponent']}"  # emoji + time (no space)
        location = "ホーム" if r["home"] else "アウェイ"

        fixtures.append(
            {
                "title": title,
                "start": start_iso,
                "end": end_iso,
                "opponent": r["opponent"],
                "location": location,
                "url": r["source"],
            }
        )

    return fixtures


def find_existing_by_title(notion: Client, db_id: str, title_text: str) -> str:
    try:
        resp = notion.databases.query(
            **{
                "database_id": db_id,
                "filter": {
                    "property": "名前",
                    "title": {"equals": title_text},
                },
                "page_size": 1,
            }
        )
        results = resp.get("results", [])
        if results:
            return results[0]["id"]
        return ""
    except Exception:
        return ""


def create_or_skip(notion: Client, db_id: str, fixture: Dict[str, Any], dry_run: bool = True, update_existing: bool = False) -> str:
    existing = find_existing_by_title(notion, db_id, fixture["title"])
    if existing:
        if update_existing:
            if dry_run:
                print(f"DRY-RUN update 作成日: {fixture['title']} -> {existing}")
                return existing
            notion.pages.update(
                **{
                    "page_id": existing,
                    "properties": {
                        "開始時刻": {"date": {"start": fixture["start"], "end": fixture["end"]}},
                        "作成日": {"date": {"start": fixture["start"], "end": fixture["end"]}},
                    },
                }
            )
            print(f"UPDATED 作成日: {fixture['title']} -> {existing}")
            return existing
        else:
            print(f"SKIP (exists): {fixture['title']} -> {existing}")
            return existing

    props: Dict[str, Any] = {
        "名前": {
            "title": [{"text": {"content": fixture["title"]}}]
        },
        "開始時刻": {
            "date": {"start": fixture["start"], "end": fixture["end"]}
        },
        "終了時刻": {
            "date": {"start": fixture["end"]}
        },
        "作成日": {
            "date": {"start": fixture["start"], "end": fixture["end"]}
        },
        "カテゴリ": {
            "multi_select": [{"name": "スポーツ観戦"}]
        },
        "URL": {
            "url": fixture["url"]
        },
    }

    if dry_run:
        print(f"DRY-RUN create: {fixture['title']} ({fixture['start']} -> {fixture['end']})")
        return ""

    created = notion.pages.create(parent={"database_id": db_id}, properties=props)
    page_id = created.get("id", "")
    print(f"CREATED: {fixture['title']} -> {page_id}")
    return page_id


def main():
    # Flags
    dry_run = True
    update_existing = False
    if "--run" in sys.argv or "--no-dry-run" in sys.argv or "--execute" in sys.argv:
        dry_run = False
    if "--update" in sys.argv or "--update-existing" in sys.argv:
        update_existing = True

    load_env()
    notion_token = os.getenv("NOTION_TOKEN")
    action_db_id = os.getenv("ACTION_DB_ID", "1feb061dadf380d19988d10d8bf0e56d")
    if not notion_token:
        print("環境変数 NOTION_TOKEN が未設定です。.env を確認してください。")
        sys.exit(1)
    if not action_db_id:
        print("環境変数 ACTION_DB_ID が未設定です。.env を確認してください。")
        sys.exit(1)

    notion = Client(auth=notion_token)

    # Optional quick-fix: update Chelsea match time explicitly if requested
    if "--fix-chelsea" in sys.argv:
        chelsea_page_id = os.getenv("CHELSEA_PAGE_ID", "265b061d-adf3-81ea-b612-e324fd4c4407")
        start_dt = datetime.strptime("2025-09-06 03:30", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(hours=2)
        start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:00+09:00")
        end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:00+09:00")
        new_title = "⚽️03:30 WSL マンチェスター・シティ vs チェルシー"
        if dry_run:
            print(f"DRY-RUN Chelsea update: {new_title} {start_iso} -> {end_iso}")
        else:
            notion.pages.update(
                **{
                    "page_id": chelsea_page_id,
                    "properties": {
                        "名前": {"title": [{"text": {"content": new_title}}]},
                        "開始時刻": {"date": {"start": start_iso, "end": end_iso}},
                        "終了時刻": {"date": {"start": end_iso}},
                        "作成日": {"date": {"start": start_iso, "end": end_iso}},
                    },
                }
            )
            print(f"UPDATED Chelsea: {new_title} -> {chelsea_page_id}")
        print(f"Done. chelsea_only=True, dry_run={dry_run}")
        return

    # Bulk JST correction for already created pages (adjust -8h from previous entries)
    if "--bulk-fix-jst" in sys.argv:
        corrections = [
            {"old": "⚽️11:30 WSL マンチェスター・シティ vs ブライトン＆ホーヴ・アルビオン", "start": "2025-09-13 03:30"},
            {"old": "⚽️11:30 WSL マンチェスター・シティ vs トッテナム・ホットスパー", "start": "2025-09-20 03:30"},
            {"old": "⚽️11:00 WSL マンチェスター・シティ vs エヴァートン", "start": "2025-09-25 03:00"},
            {"old": "⚽️04:00 WSL マンチェスター・シティ vs ロンドン・シティ・ライオネッセス", "start": "2025-09-27 20:00"},
            {"old": "⚽️11:00 WSL マンチェスター・シティ vs アーセナル", "start": "2025-10-04 03:00"},
            {"old": "⚽️06:00 WSL マンチェスター・シティ vs リヴァプール", "start": "2025-10-11 22:00"},
            {"old": "⚽️06:00 WSL マンチェスター・シティ vs ニューカッスル・ユナイテッド", "start": "2025-10-18 22:00"},
            {"old": "⚽️05:00 WSL マンチェスター・シティ vs ウェストハム・ユナイテッド", "start": "2025-11-01 21:00"},
            {"old": "⚽️07:00 WSL マンチェスター・シティ vs エヴァートン", "start": "2025-11-08 23:00"},
        ]
        updated = 0
        for c in corrections:
            # find page by old title
            resp = notion.databases.query(
                **{
                    "database_id": action_db_id,
                    "filter": {"property": "名前", "title": {"equals": c["old"]}},
                    "page_size": 1,
                }
            )
            results = resp.get("results", [])
            if not results:
                print(f"NOT FOUND (skip): {c['old']}")
                continue
            page_id = results[0]["id"]

            start_dt = datetime.strptime(c["start"], "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(hours=2)
            start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:00+09:00")
            end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:00+09:00")
            time_text = start_dt.strftime("%H:%M")
            # new opponent text: extract from old title suffix after 'vs '
            opponent = c["old"].split(" vs ", 1)[1]
            new_title = f"⚽️{time_text} WSL マンチェスター・シティ vs {opponent}"

            if dry_run:
                print(f"DRY-RUN UPDATE: {c['old']} -> {new_title} ({start_iso}→{end_iso})")
            else:
                notion.pages.update(
                    **{
                        "page_id": page_id,
                        "properties": {
                            "名前": {"title": [{"text": {"content": new_title}}]},
                            "開始時刻": {"date": {"start": start_iso, "end": end_iso}},
                            "終了時刻": {"date": {"start": end_iso}},
                            "作成日": {"date": {"start": start_iso, "end": end_iso}},
                        },
                    }
                )
                print(f"UPDATED: {new_title} -> {page_id}")
                updated += 1
            time.sleep(0.2)
        print(f"Done. bulk_fix_jst updated={updated}, dry_run={dry_run}")
        return

    # Set duration on 開始時刻 for all WSL Man City entries by deriving end from start
    if "--set-duration" in sys.argv or "--force-duration" in sys.argv:
        updated = 0
        start_cursor = None
        while True:
            q = {
                "database_id": action_db_id,
                "filter": {"property": "名前", "title": {"contains": "WSL マンチェスター・シティ vs "}},
                "page_size": 50,
            }
            if start_cursor:
                q["start_cursor"] = start_cursor
            resp = notion.databases.query(**q)
            for page in resp.get("results", []):
                pid = page["id"]
                props = page.get("properties", {})
                date_obj = props.get("開始時刻", {}).get("date") or {}
                start_val = date_obj.get("start")
                if not start_val:
                    continue
                # If end already exists and looks valid, skip unless force-duration
                if date_obj.get("end") and "--force-duration" not in sys.argv:
                    continue
                try:
                    end_val = add_two_hours_iso_end(start_val)
                except Exception:
                    continue
                if dry_run:
                    print(f"DRY-RUN duration: {pid} set end={end_val}")
                else:
                    notion.pages.update(
                        **{
                            "page_id": pid,
                            "properties": {
                                "開始時刻": {"date": {"start": start_val, "end": end_val}},
                                "作成日": {"date": {"start": start_val, "end": end_val}},
                            },
                        }
                    )
                    updated += 1
                    time.sleep(0.1)
            start_cursor = resp.get("next_cursor")
            if not resp.get("has_more"):
                break
        print(f"Done. set-duration updated={updated}, dry_run={dry_run}")
        return

    # Debug: list titles and start/end in 開始時刻
    if "--debug-list" in sys.argv:
        start_cursor = None
        total = 0
        while True:
            q = {
                "database_id": action_db_id,
                "filter": {"property": "名前", "title": {"contains": "WSL マンチェスター・シティ vs "}},
                "page_size": 50,
            }
            if start_cursor:
                q["start_cursor"] = start_cursor
            resp = notion.databases.query(**q)
            for page in resp.get("results", []):
                props = page.get("properties", {})
                title_rich = props.get("名前", {}).get("title", [])
                title_text = "".join([t.get("plain_text") or t.get("text", {}).get("content", "") for t in title_rich])
                date_obj = props.get("開始時刻", {}).get("date") or {}
                s = date_obj.get("start")
                e = date_obj.get("end")
                print(f"LIST: {title_text} | start={s} end={e}")
                total += 1
            start_cursor = resp.get("next_cursor")
            if not resp.get("has_more"):
                break
        print(f"Done. debug-list count={total}")
        return

    fixtures = build_fixtures()
    created_count = 0
    for fx in fixtures:
        page_id = create_or_skip(notion, action_db_id, fx, dry_run=dry_run, update_existing=update_existing)
        if page_id:
            created_count += 1
        time.sleep(0.25)

    print(f"Done. created_count_or_updated={created_count}, dry_run={dry_run}, update_existing={update_existing}")


if __name__ == "__main__":
    main()


