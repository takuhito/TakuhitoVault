#!/bin/bash
set -e
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# venvがあれば使用
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

mkdir -p exports
python3 scripts/import_cursor_chats.py --input ./exports --project NotionWorkflowTools --desc AutoImport --archive

