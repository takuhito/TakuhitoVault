#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Reports → Notion「日記」 自動同期スクリプト

機能:
- 指定したMarkdownファイル（/Users/takuhito/Documents/daily-reports/*.md）を読み取り
- ファイル名の日付 (YYYY-MM-DD.md) から Notion「日記」データベースのページ名 (YYYY-MMDD) を決定
- ページを検索し、無ければ作成。既存なら本文ブロックを全削除して置き換え
- MarkdownはネイティブNotionブロック（heading_1/2/3, bulleted_list_item, paragraph, divider）に変換

必要な環境変数 (.env):
- NOTION_TOKEN
- JOURNAL_DB_ID  … 「日記」DB-ID
- PROP_JOURNAL_TITLE (任意, 既定: タイトル)

使い方:
  python3 scripts/sync_daily_report.py --file /Users/takuhito/Documents/daily-reports/2025-09-01.md
"""

from __future__ import annotations

import os
import re
import sys
import time
import random
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError, RequestTimeoutError
except Exception:
    print("notion-client が見つかりません。`pip install notion-client python-dotenv` を実行してください。")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


# --- 環境変数読み込み ---
if load_dotenv:
    load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
JOURNAL_DB_ID = os.getenv("JOURNAL_DB_ID")
PROP_JOURNAL_TITLE = os.getenv("PROP_JOURNAL_TITLE", "タイトル")
NOTION_TIMEOUT = int(os.getenv("NOTION_TIMEOUT", "60"))

if not NOTION_TOKEN or not JOURNAL_DB_ID:
    print("環境変数 NOTION_TOKEN / JOURNAL_DB_ID が未設定です。.env を確認してください。")
    sys.exit(1)

notion = Client(auth=NOTION_TOKEN, timeout_ms=int(NOTION_TIMEOUT * 1000))


def resolve_journal_db_id() -> str:
    """環境変数が無い/無効な場合に、Notionのsearchで『日記』DBを自動特定。"""
    global JOURNAL_DB_ID
    if JOURNAL_DB_ID:
        # まず存在確認。404なら検索にフォールバック
        try:
            with_retry(lambda: notion.databases.retrieve(database_id=JOURNAL_DB_ID), what="databases.retrieve")
            return JOURNAL_DB_ID
        except Exception:
            pass

    # Search APIでデータベース検索
    res = with_retry(
        lambda: notion.search(query="日記", filter={"property": "object", "value": "database"}, page_size=10),
        what="search 日記 database",
    )
    for obj in res.get("results", []):
        if obj.get("object") == "database":
            # タイトルのテキストを取り出す
            title_arr = obj.get("title", [])
            title_text = "".join([t.get("plain_text", "") for t in title_arr])
            if title_text.strip() == "日記":
                JOURNAL_DB_ID = obj.get("id")
                return JOURNAL_DB_ID

    # 見つからない場合は最初のデータベースを返す（暫定）
    if res.get("results"):
        JOURNAL_DB_ID = res["results"][0].get("id")
        return JOURNAL_DB_ID

    raise RuntimeError("Notionで『日記』データベースが見つかりません。JOURNAL_DB_IDを.envに設定してください。")


# ---------- リトライ付きAPIユーティリティ ----------
def with_retry(fn, *, max_attempts: int = 4, base_delay: float = 1.0, what: str = "api"):
    attempt = 0
    while True:
        try:
            return fn()
        except RequestTimeoutError:
            attempt += 1
            if attempt >= max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            print(f"[RETRY] Timeout on {what}. retry {attempt}/{max_attempts} in {delay:.1f}s")
            time.sleep(delay)
        except APIResponseError as e:
            # レート制限は待って再試行
            if getattr(e, "code", "") == "rate_limited":
                attempt += 1
                retry_after = float(getattr(e, "headers", {}).get("Retry-After", 1)) if hasattr(e, "headers") else 1.0
                delay = max(retry_after, base_delay * (2 ** (attempt - 1))) + random.uniform(0, 0.5)
                print(f"[RETRY] rate_limited on {what}. retry {attempt}/{max_attempts} in {delay:.1f}s")
                time.sleep(delay)
                if attempt < max_attempts:
                    continue
            raise


# ---------- Markdown → Notion ブロック変換（シンプル版, 箇条書き・見出し対応） ----------
def _inline_rich_text(text: str) -> List[Dict[str, Any]]:
    """非常に簡易な**bold**対応のリッチテキスト生成。"""
    if "**" not in text:
        return [{"type": "text", "text": {"content": text}}]
    parts = text.split("**")
    rich: List[Dict[str, Any]] = []
    for i, part in enumerate(parts):
        if not part:
            continue
        if i % 2 == 0:
            rich.append({"type": "text", "text": {"content": part}})
        else:
            rich.append({"type": "text", "text": {"content": part}, "annotations": {"bold": True}})
    return rich


def parse_daily_markdown_to_blocks(content: str, max_blocks: int = 90) -> List[Dict[str, Any]]:
    """日報用MarkdownをネイティブNotionブロックへ変換。

    対応:
      - # / ## / ### 見出し
      - --- 区切り線
      - - から始まる箇条書き（連続行を個別のbulleted_list_itemに）
      - それ以外は段落
    """
    blocks: List[Dict[str, Any]] = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if not line:
            i += 1
            continue

        if line.startswith("# "):
            text = line[2:].strip()
            blocks.append({"type": "heading_1", "heading_1": {"rich_text": _inline_rich_text(text)}})
            i += 1
            continue
        if line.startswith("## "):
            text = line[3:].strip()
            blocks.append({"type": "heading_2", "heading_2": {"rich_text": _inline_rich_text(text)}})
            i += 1
            continue
        if line.startswith("### "):
            text = line[4:].strip()
            blocks.append({"type": "heading_3", "heading_3": {"rich_text": _inline_rich_text(text)}})
            i += 1
            continue
        if line == "---":
            blocks.append({"type": "divider", "divider": {}})
            i += 1
            continue

        # 箇条書き（連続行）
        if line.startswith("- "):
            while i < len(lines) and lines[i].strip().startswith("- "):
                item_text = lines[i].strip()[2:].strip()
                blocks.append({"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": _inline_rich_text(item_text)}})
                i += 1
            continue

        # 通常段落（空行まで結合）
        para_lines: List[str] = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("- "):
            para_lines.append(lines[i])
            i += 1
        paragraph_text = "\n".join(para_lines).strip()
        if paragraph_text:
            blocks.append({"type": "paragraph", "paragraph": {"rich_text": _inline_rich_text(paragraph_text)}})

        if len(blocks) >= max_blocks:
            break

    return blocks


# ---------- Notion 日記ページ操作 ----------
def date_title_from_filename(path: Path) -> str:
    """ファイル名から日付を抽出し YYYY-MMDD へ。

    許容:
      - 末尾が .md の通常形式: 2025-09-01.md
      - 文字列中に YYYY-MM-DD が含まれていればOK
    """
    name = path.name
    # 1) まず厳密形式
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})\\.md$", name)
    if not m:
        # 2) どこかに日付が含まれる場合
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", name)
    if not m:
        raise ValueError(f"無効なファイル名: {name}")
    y, mth, d = m.groups()
    return f"{y}-{mth}{d}"


def find_or_create_journal_page(title_text: str) -> str:
    # タイトル一致で検索
    def _query():
        return notion.databases.query(
            **{
                "database_id": JOURNAL_DB_ID,
                "filter": {"property": PROP_JOURNAL_TITLE, "title": {"equals": title_text}},
                "page_size": 1,
            }
        )
    res = with_retry(_query, what="journal.query")
    arr = res.get("results", [])
    if arr:
        return arr[0]["id"]

    # 無ければ作成
    props = {PROP_JOURNAL_TITLE: {"title": [{"type": "text", "text": {"content": title_text}}]}}
    def _create():
        return notion.pages.create(parent={"database_id": JOURNAL_DB_ID}, properties=props)
    created = with_retry(_create, what="pages.create")
    return created["id"]


def replace_page_children(page_id: str, children: List[Dict[str, Any]]):
    # 既存の子ブロックを全削除
    try:
        listing = with_retry(lambda: notion.blocks.children.list(block_id=page_id), what="blocks.list")
        for b in listing.get("results", []):
            with_retry(lambda b_id=b["id"]: notion.blocks.delete(block_id=b_id), what="blocks.delete")
    except Exception as e:
        print(f"既存ブロック削除エラー: {e}")

    # 追加（Notionは1回に100ブロックまで）
    idx = 0
    while idx < len(children):
        chunk = children[idx : idx + 90]
        with_retry(lambda: notion.blocks.children.append(block_id=page_id, children=chunk), what="blocks.append")
        idx += len(chunk)


# ---------- メイン処理 ----------
def sync_daily_report(file_path: Path):
    if not file_path.exists():
        print(f"対象ファイルが存在しません: {file_path}")
        return

    title_text = date_title_from_filename(file_path)
    content = file_path.read_text(encoding="utf-8")
    blocks = parse_daily_markdown_to_blocks(content)

    # DB-IDの自動解決（未設定時）
    global JOURNAL_DB_ID
    JOURNAL_DB_ID = resolve_journal_db_id()

    page_id = find_or_create_journal_page(title_text)
    replace_page_children(page_id, blocks)
    print(f"同期完了: {file_path.name} → Notion『日記』: {title_text} ({page_id})")


def main():
    parser = argparse.ArgumentParser(description="Daily Reports → Notion『日記』 同期")
    parser.add_argument("--file", required=True, help="Markdownファイルの絶対パス (YYYY-MM-DD.md)")
    args = parser.parse_args()

    path = Path(args.file)
    sync_daily_report(path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("中断しました。")

