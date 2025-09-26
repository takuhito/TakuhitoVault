#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CursorのJSONエクスポートを一括取り込みして、
ChatHistoryToNotion/chat_history にRAW Markdownを生成し、続けてNotionへ同期するスクリプト。

前提:
- .env に NOTION_TOKEN / CHATGPT_DB_ID が設定済み
- ChatHistoryToNotion/chat_history_to_notion.py が動作可能

使い方:
  python3 scripts/import_cursor_chats.py --input ./exports --project NotionWorkflowTools --desc AutoImport

入力JSONの想定（最小）:
  {
    "chat_id": "abc123",
    "title": "スレッドタイトル",
    "chat_date": "2025-09-05T10:00:00+09:00",
    "content": "ここに全文Markdown"
  }

※複数ファイル(.json)を一括処理
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
CHAT_DIR = ROOT / 'ChatHistoryToNotion' / 'chat_history'
NOTION_SYNC = ROOT / 'ChatHistoryToNotion' / 'chat_history_to_notion.py'


def ensure_dirs() -> None:
    CHAT_DIR.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Import Cursor JSON exports to RAW chat markdown + Notion sync')
    p.add_argument('--input', required=False, default=str(ROOT / 'exports'), help='JSONフォルダパス')
    p.add_argument('--project', required=False, default='NotionWorkflowTools', help='プロジェクト名')
    p.add_argument('--desc', required=False, default='AutoImport', help='説明（ファイル名用）')
    p.add_argument('--dry-run', action='store_true', help='Notion同期を行わずファイル生成のみ')
    p.add_argument('--archive', action='store_true', help='処理後にJSONをprocessedへ移動')
    return p.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def build_filename(project: str, desc: str, chat_date: str) -> str:
    try:
        dt = datetime.fromisoformat(chat_date.replace('Z', '+00:00'))
    except Exception:
        dt = datetime.now()
    ymd = dt.strftime('%Y%m%d')
    return f"{ymd}_{project}_{desc}.md"


def write_raw_markdown(target: Path, project: str, desc: str, content: str, chat_date: str) -> None:
    created = datetime.now().strftime('%Y年%m月%d日')
    start_iso = ''
    try:
        if chat_date:
            dt = datetime.fromisoformat(chat_date.replace('Z', '+00:00'))
            start_iso = dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        start_iso = ''
    md = (
        f"# チャット履歴（RAW）\n\n"
        f"**日付**: {created}  \n"
        f"**プロジェクト**: {project}  \n"
        f"**説明**: {desc}  \n"
        f"**参加者**: ユーザー、AI アシスタント\n\n"
        f"---\n\n"
        f"## チャット開始\n\n"
        f"**開始時刻**: {start_iso or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"---\n\n"
        f"## チャット内容（全文）\n\n"
        f"{content}\n\n"
        f"---\n\n"
        f"**作成日**: {created}  \n"
        f"**ファイル**: {target.name}\n"
    )
    target.write_text(md, encoding='utf-8')


def sync_to_notion(target: Path) -> None:
    os.system(f"python3 '{NOTION_SYNC}' '{target}'")


def main() -> None:
    args = parse_args()
    ensure_dirs()

    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"入力フォルダがありません: {input_dir}")
        return

    json_files = sorted(input_dir.glob('*.json'))
    if not json_files:
        print(f"JSONが見つかりません: {input_dir}")
        return

    processed_dir = input_dir / 'processed'
    if args.archive:
        processed_dir.mkdir(exist_ok=True)

    for jf in json_files:
        try:
            obj = load_json(jf)
            content = obj.get('content') or ''
            chat_date = obj.get('chat_date') or ''
            project = args.project
            desc = args.desc

            fname = build_filename(project, desc, chat_date)
            target = CHAT_DIR / fname
            write_raw_markdown(target, project, desc, content, chat_date)
            print(f"WROTE: {target}")

            if not args.dry_run:
                sync_to_notion(target)
            if args.archive:
                jf.rename(processed_dir / jf.name)
        except Exception as e:
            print(f"ERROR: {jf} -> {e}")


if __name__ == '__main__':
    main()


