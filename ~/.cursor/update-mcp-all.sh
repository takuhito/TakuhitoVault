#!/bin/bash

# 全クライアントのMCP設定を一括更新するスクリプト

echo "=== MCP設定一括更新スクリプト ==="
echo ""

# 設定ファイルの場所
CURSOR_CONFIG="$HOME/.cursor/mcp.json"
VSCODE_CONFIG="$HOME/.vscode/settings.json"
CLAUDE_CONFIG="$HOME/.claude/mcp.json"
GEMINI_CONFIG="$HOME/.gemini/mcp.json"

# プロジェクト名
PROJECT_NAME="NotionWorkflowTools"

echo "プロジェクト名: $PROJECT_NAME"
echo ""

# 1. Cursor設定の更新
if [ -f "$CURSOR_CONFIG" ]; then
    echo "✅ Cursor設定を更新中..."
    sed -i '' "s/x-sm-project:default/x-sm-project:$PROJECT_NAME/g" "$CURSOR_CONFIG"
    echo "   Cursor設定更新完了"
else
    echo "❌ Cursor設定ファイルが見つかりません: $CURSOR_CONFIG"
fi

# 2. VSCode設定の更新
if [ -f "$VSCODE_CONFIG" ]; then
    echo "✅ VSCode設定を更新中..."
    sed -i '' "s/x-sm-project:default/x-sm-project:$PROJECT_NAME/g" "$VSCODE_CONFIG"
    echo "   VSCode設定更新完了"
else
    echo "❌ VSCode設定ファイルが見つかりません: $VSCODE_CONFIG"
fi

# 3. Claude Desktop設定の更新
if [ -f "$CLAUDE_CONFIG" ]; then
    echo "✅ Claude Desktop設定を更新中..."
    sed -i '' "s/x-sm-project:default/x-sm-project:$PROJECT_NAME/g" "$CLAUDE_CONFIG"
    echo "   Claude Desktop設定更新完了"
else
    echo "❌ Claude Desktop設定ファイルが見つかりません: $CLAUDE_CONFIG"
fi

# 4. Gemini CLI設定の更新
if [ -f "$GEMINI_CONFIG" ]; then
    echo "✅ Gemini CLI設定を更新中..."
    sed -i '' "s/x-sm-project:default/x-sm-project:$PROJECT_NAME/g" "$GEMINI_CONFIG"
    echo "   Gemini CLI設定更新完了"
else
    echo "❌ Gemini CLI設定ファイルが見つかりません: $GEMINI_CONFIG"
fi

echo ""
echo "=== 更新完了 ==="
echo ""
echo "次のステップ:"
echo "1. 各クライアントを再起動"
echo "2. MCPサーバーの動作確認"
echo "3. プロジェクト固有の記憶機能のテスト"
echo ""
echo "設定ファイルの場所:"
echo "  Cursor: $CURSOR_CONFIG"
echo "  VSCode: $VSCODE_CONFIG"
echo "  Claude Desktop: $CLAUDE_CONFIG"
echo "  Gemini CLI: $GEMINI_CONFIG"
