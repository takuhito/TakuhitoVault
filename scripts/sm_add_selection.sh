#!/bin/zsh
# Save current clipboard content to supermemory.ai via MCP
# Usage:
#   pbcopy < file.txt; ./scripts/sm_add_selection.sh "Optional Title"

set -euo pipefail

PROJECT_NAME=${SM_PROJECT:-NotionWorkflowTools}
TITLE=${1:-}
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)

if ! command -v node >/dev/null 2>&1; then
  echo "node not found" >&2
  exit 1
fi

CONTENT=$(pbpaste || true)
if [ -z "$CONTENT" ]; then
  echo "clipboard is empty" >&2
  exit 2
fi

if [ -n "$TITLE" ]; then
  PRINTF_TITLE=(--title "$TITLE")
else
  PRINTF_TITLE=()
fi

print -r -- "$CONTENT" | node "$SCRIPT_DIR/sm_add_memory.js" --project "$PROJECT_NAME" ${PRINTF_TITLE[@]:-}

echo "Saved clipboard selection to supermemory.ai"


