#!/bin/bash

# MovableType Rebuilder ローカルスケジューラーセットアップスクリプト

set -e

echo "=== MovableType Rebuilder ローカルスケジューラーセットアップ ==="

# 現在のディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_FILE="$SCRIPT_DIR/com.user.movabletype-rebuilder.plist"

# plistファイルのパスを現在のディレクトリに更新
echo "plistファイルのパスを更新中..."
sed -i.bak "s|/Users/takuhito/NotionWorkflowTools/MovableTypeRebuilder|$SCRIPT_DIR|g" "$PLIST_FILE"

# ログディレクトリを作成
echo "ログディレクトリを作成中..."
mkdir -p "$SCRIPT_DIR/logs"

# launchdにplistファイルをコピー
echo "launchdにplistファイルをコピー中..."
cp "$PLIST_FILE" ~/Library/LaunchAgents/

# launchdサービスを読み込み
echo "launchdサービスを読み込み中..."
launchctl load ~/Library/LaunchAgents/com.user.movabletype-rebuilder.plist

echo "=== セットアップ完了 ==="
echo "サービス名: com.user.movabletype-rebuilder"
echo "実行スケジュール: 毎月1日の0:01"
echo ""
echo "管理コマンド:"
echo "  サービス停止: launchctl unload ~/Library/LaunchAgents/com.user.movabletype-rebuilder.plist"
echo "  サービス開始: launchctl load ~/Library/LaunchAgents/com.user.movabletype-rebuilder.plist"
echo "  サービス状態確認: launchctl list | grep movabletype"
echo ""
echo "ログファイル:"
echo "  - $SCRIPT_DIR/logs/launchd_stdout.log"
echo "  - $SCRIPT_DIR/logs/launchd_stderr.log"
echo "  - $SCRIPT_DIR/logs/mt_rebuilder_YYYYMMDD.log"
