#!/usr/bin/env bash
# 実行+通知（osascriptを安全に呼ぶ版）
set -euo pipefail
cd "$HOME/NotionLinker"

# .env を反映
if [ -f ".env" ]; then
    echo "Loading .env file..."
    set -a
    source .env
    set +a
    echo "NOTION_TOKEN loaded: ${NOTION_TOKEN:0:10}..."
else
    echo "ERROR: .env file not found!"
    exit 1
fi

source venv/bin/activate

ts="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[$ts] Running link_diary.py ..."

out="$HOME/Library/Logs/notion-linker.last.out"
err="$HOME/Library/Logs/notion-linker.last.err"
mkdir -p "$HOME/Library/Logs"

set +e
python link_diary.py >"$out" 2>"$err"
status=$?
set -e

# 標準出力にも反映
cat "$out"
[ -s "$err" ] && cat "$err" >&2

notify_osascript () {
  # argv経由で渡すことでクォート問題を回避
  local title="$1"; shift
  local subtitle="$1"; shift
  local body="$1"; shift
  /usr/bin/osascript - "$title" "$subtitle" "$body" <<'OSA'
on run argv
  set t to item 1 of argv
  set s to item 2 of argv
  set b to item 3 of argv
  display notification b with title t subtitle s
end run
OSA
}

notify_slack () {
  [ -z "${SLACK_WEBHOOK:-}" ] && return 0
  /usr/bin/curl -s -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"[Notion Linker] ${1//\"/\\\"}\"}" \
    "$SLACK_WEBHOOK" >/dev/null 2>&1 || true
}

if [ $status -ne 0 ]; then
  short_err="$(head -n 5 "$err" | tr -d '\r' | tr '\n' ' ')"
  [ -z "$short_err" ] && short_err="失敗（詳細はログ参照）"
  notify_osascript "Notion Linker" "失敗しました" "$short_err"
  notify_slack "失敗: $short_err"
  exit $status
else
  last_line="$(tail -n 1 "$out" | tr -d '\r')"
  [ -z "$last_line" ] && last_line="完了"
  notify_osascript "Notion Linker" "成功" "$last_line"
  notify_slack "成功: $last_line"
  # 成功時は直近エラーログを空にして古いエラー表示の混在を防ぐ
  : > "$err"
fi
