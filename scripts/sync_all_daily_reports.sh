#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")/.."

REPORT_DIR="/Users/takuhito/Documents/daily-reports"

for f in "$REPORT_DIR"/*.md; do
  [ -e "$f" ] || continue
  base="$(basename "$f")"
  if [[ ! "$base" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$ ]]; then
    continue
  fi
  echo "Sync: $f"
  python3 scripts/sync_daily_report.py --file "$f"
done

echo "All daily reports synced."

