#!/bin/bash

# 現在のCursorウィンドウからチャット全文をコピーし、RAWで保存→Notion同期まで自動実行
# 依存: osascript(macOS), pbpaste, Python(venv任意)

set -e

PROJECT_NAME=${1:-"NotionWorkflowTools"}
DESCRIPTION=${2:-"AutoSaved_Chat"}

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CHAT_DIR="$ROOT_DIR/ChatHistoryToNotion/chat_history"
SCRIPT_DIR="$ROOT_DIR/scripts"

mkdir -p "$CHAT_DIR"

ATTEMPTS=5
OK=false
for i in $(seq 1 $ATTEMPTS); do
  echo "+ (${i}/${ATTEMPTS}) Cursor を前面化しメニューから全文コピー"
  osascript <<'OSA'
  tell application "Cursor" to activate
  delay 0.8
  tell application "System Events"
    tell process "Cursor"
      -- フォーカスをエディタ領域へ移すためにクリック（中央近辺）
      try
        set frontWin to front window
        set {xPos, yPos} to position of frontWin
        set {w, h} to size of frontWin
        set cx to xPos + (w / 2)
        set cy to yPos + (h / 2)
        click at {cx, cy}
      end try
      delay 0.2
      -- メニューから選択: 編集 > すべてを選択
      try
        click menu item "Select All" of menu 1 of menu bar item "Edit" of menu bar 1
      on error
        keystroke "a" using {command down}
      end try
      delay 0.3
      -- メニューからコピー
      try
        click menu item "Copy" of menu 1 of menu bar item "Edit" of menu bar 1
      on error
        keystroke "c" using {command down}
      end try
    end tell
  end tell
OSA
  echo "+ クリップボード長チェック"
  CLIP_LEN=$(pbpaste | python3 -c 'import sys; data=sys.stdin.read(); print(len(data))')
  if [ "${CLIP_LEN}" -ge 200 ]; then
    OK=true
    break
  fi
  echo "  - 現在の長さ: ${CLIP_LEN} chars。チャット画面が前面で本文にフォーカスがあるか確認します。再試行します。"
  sleep 1.5
done

if [ "$OK" != "true" ]; then
  echo "❌ クリップボードの内容が短すぎます(${CLIP_LEN} chars)。保存を中断します。" >&2
  echo "   チャット画面がアクティブか確認し、再実行してください。" >&2
  exit 2
fi

echo "+ 保存(RAW)"
ALLOW_OVERWRITE=true "$SCRIPT_DIR/save_chat_history.sh" "$PROJECT_NAME" "$DESCRIPTION" "" raw

YMD=$(date +%Y%m%d)
FNAME="${YMD}_${PROJECT_NAME}_${DESCRIPTION}.md"
TARGET_PATH="$CHAT_DIR/$FNAME"
if [ ! -f "$TARGET_PATH" ]; then
  # タイムスタンプ付きの場合にフォールバック
  TARGET_PATH=$(ls -1t "$CHAT_DIR" | grep "^${YMD}_${PROJECT_NAME}_${DESCRIPTION}.*\.md$" | head -n1 | sed "s#^#$CHAT_DIR/#")
fi
echo "+ Notion 同期: $(basename "$TARGET_PATH")"

# venvがあれば使用
if [ -f "$ROOT_DIR/venv/bin/activate" ]; then
  # shellcheck disable=SC1090
  source "$ROOT_DIR/venv/bin/activate"
fi

python3 "$ROOT_DIR/ChatHistoryToNotion/chat_history_to_notion.py" "$TARGET_PATH"

echo "DONE: $(basename "$TARGET_PATH") をNotionへ同期しました。"


