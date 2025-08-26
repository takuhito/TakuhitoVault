#!/bin/bash

# HETEMLサーバ監視システム 制御スクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/heteml_monitor.py"
LOG_FILE="$SCRIPT_DIR/monitor.log"

# 色付きメッセージ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 関数
show_help() {
    echo "HETEMLサーバ監視システム 制御スクリプト"
    echo ""
    echo "使用方法: $0 [コマンド]"
    echo ""
    echo "コマンド:"
    echo "  start     - 監視システムを開始"
    echo "  stop      - 監視システムを停止"
    echo "  restart   - 監視システムを再起動"
    echo "  status    - 監視システムの状態を確認"
    echo "  logs      - ログを表示"
    echo "  test      - 接続テストを実行"
    echo "  auto      - 自動起動を設定"
    echo "  help      - このヘルプを表示"
}

start_monitor() {
    echo -e "${GREEN}監視システムを開始しています...${NC}"
    
    # 既存プロセスを確認
    if pgrep -f heteml_monitor > /dev/null; then
        echo -e "${YELLOW}監視システムは既に実行中です${NC}"
        return 1
    fi
    
    # 仮想環境をアクティベートして監視システムを開始
    cd "$SCRIPT_DIR"
    source venv/bin/activate
    nohup python "$MONITOR_SCRIPT" > "$LOG_FILE" 2>&1 &
    
    sleep 2
    if pgrep -f heteml_monitor > /dev/null; then
        echo -e "${GREEN}✅ 監視システムが開始されました${NC}"
        echo "ログファイル: $LOG_FILE"
    else
        echo -e "${RED}❌ 監視システムの開始に失敗しました${NC}"
        return 1
    fi
}

stop_monitor() {
    echo -e "${YELLOW}監視システムを停止しています...${NC}"
    
    if pkill -f heteml_monitor; then
        echo -e "${GREEN}✅ 監視システムが停止されました${NC}"
    else
        echo -e "${YELLOW}監視システムは実行されていません${NC}"
    fi
}

restart_monitor() {
    echo -e "${YELLOW}監視システムを再起動しています...${NC}"
    stop_monitor
    sleep 2
    start_monitor
}

show_status() {
    echo -e "${GREEN}監視システムの状態:${NC}"
    
    if pgrep -f heteml_monitor > /dev/null; then
        echo -e "${GREEN}✅ 実行中${NC}"
        echo "プロセスID: $(pgrep -f heteml_monitor)"
        echo "ログファイル: $LOG_FILE"
        
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "最新のログ:"
            tail -5 "$LOG_FILE"
        fi
    else
        echo -e "${RED}❌ 停止中${NC}"
    fi
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo -e "${GREEN}ログファイルの内容:${NC}"
        tail -f "$LOG_FILE"
    else
        echo -e "${YELLOW}ログファイルが見つかりません${NC}"
    fi
}

run_test() {
    echo -e "${GREEN}接続テストを実行しています...${NC}"
    cd "$SCRIPT_DIR"
    source venv/bin/activate
    python check_connection.py
}

setup_auto() {
    echo -e "${GREEN}自動起動を設定しています...${NC}"
    
    # plistファイルをコピー
    cp "$SCRIPT_DIR/com.user.heteml-monitor.plist" ~/Library/LaunchAgents/
    
    # launchdに登録
    launchctl load ~/Library/LaunchAgents/com.user.heteml-monitor.plist
    
    echo -e "${GREEN}✅ 自動起動が設定されました${NC}"
    echo "Mac起動時に自動で監視システムが開始されます"
}

# メイン処理
case "$1" in
    start)
        start_monitor
        ;;
    stop)
        stop_monitor
        ;;
    restart)
        restart_monitor
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        run_test
        ;;
    auto)
        setup_auto
        ;;
    help|*)
        show_help
        ;;
esac
