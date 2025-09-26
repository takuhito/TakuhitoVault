#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supermemory Auto-Save Watcher
指定ディレクトリ配下のファイル変更を監視し、内容をsupermemory.aiへ送信します。

env:
  SM_ENABLED=true|false
  SM_PROJECT=NotionWorkflowTools
  SM_WATCH_DIR=/Users/takuhito/NotionWorkflowTools
  SM_MAX_BYTES=40000  # 送信最大バイト
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Set

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except Exception:
    print("watchdog が必要です: pip install watchdog")
    sys.exit(1)

SM_ENABLED = os.getenv("SM_ENABLED", "true").lower() in ("1", "true", "yes")
SM_PROJECT = os.getenv("SM_PROJECT", "NotionWorkflowTools")
SM_WATCH_DIR = os.getenv("SM_WATCH_DIR", "/Users/takuhito/NotionWorkflowTools")
SM_MAX_BYTES = int(os.getenv("SM_MAX_BYTES", "40000"))

SCRIPT_DIR = Path(__file__).resolve().parent
SM_JS = str((SCRIPT_DIR / "sm_add_memory.js").resolve())

IGNORE_DIR_NAMES: Set[str] = {
    ".git", "node_modules", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".DS_Store"
}

ALLOWED_EXT: Set[str] = set()  # 空＝全ファイル対象（除外で制御）


def should_ignore(path: Path) -> bool:
    parts = set(path.parts)
    if parts & IGNORE_DIR_NAMES:
        return True
    return False


def read_tail_bytes(path: Path, max_bytes: int) -> str:
    try:
        data = path.read_bytes()
        if len(data) > max_bytes:
            data = data[-max_bytes:]
            prefix = b"...[truncated]\n"
            data = prefix + data
        return data.decode("utf-8", errors="replace")
    except Exception as e:
        return f"[read error] {e}"


def send_to_supermemory(content: str, title: str = "") -> None:
    if not SM_ENABLED:
        return
    try:
        proc = subprocess.Popen(
            ["node", SM_JS, "--project", SM_PROJECT] + (["--title", title] if title else []),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        proc.communicate(input=content, timeout=60)
    except Exception:
        pass


class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if should_ignore(path):
            return
        if ALLOWED_EXT and path.suffix not in ALLOWED_EXT:
            return
        title = f"File Save: {path}"
        body = f"PATH: {path}\nUPDATED: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n" + read_tail_bytes(path, SM_MAX_BYTES)
        send_to_supermemory(body, title)

    def on_created(self, event):
        if event.is_directory:
            return
        self.on_modified(event)


def main():
    watch_dir = Path(SM_WATCH_DIR)
    if not watch_dir.exists():
        print(f"監視ディレクトリが存在しません: {watch_dir}")
        sys.exit(1)
    observer = Observer()
    observer.schedule(Handler(), str(watch_dir), recursive=True)
    observer.start()
    print(f"[sm_watch_repo] watching {watch_dir} (project={SM_PROJECT})")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()


