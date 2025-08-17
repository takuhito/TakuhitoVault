#!/bin/bash

# ChatGPT to Notion 自動同期スクリプト
# このスクリプトは定期的にChatGPTのチャット履歴をNotionに同期します

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# ログファイル
LOG_FILE="chatgpt_sync.log"
LOCK_FILE="chatgpt_sync.lock"

# ロックファイルチェック（重複実行防止）
if [ -f "$LOCK_FILE" ]; then
    echo "$(date): 既に実行中のため終了します" >> "$LOG_FILE"
    exit 1
fi

# ロックファイル作成
touch "$LOCK_FILE"

# ログ開始
echo "$(date): ChatGPT同期開始" >> "$LOG_FILE"

# 仮想環境のアクティベート
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "$(date): 仮想環境をアクティベートしました" >> "$LOG_FILE"
else
    echo "$(date): エラー: 仮想環境が見つかりません" >> "$LOG_FILE"
    rm -f "$LOCK_FILE"
    exit 1
fi

# 環境変数ファイルの確認
if [ ! -f ".env" ]; then
    echo "$(date): エラー: .envファイルが見つかりません" >> "$LOG_FILE"
    rm -f "$LOCK_FILE"
    exit 1
fi

# ChatGPTエクスポートファイルの検索（圧縮ファイル含む）
echo "$(date): ChatGPTエクスポートファイルを検索中..." >> "$LOG_FILE"

# 最新のエクスポートファイルを検索（圧縮ファイル含む）
LATEST_EXPORT=$(find . -name "chatgpt_export_*" -type f -mtime -7 2>/dev/null | sort -r | head -1)

if [ -n "$LATEST_EXPORT" ]; then
    echo "$(date): エクスポートファイル発見: $LATEST_EXPORT" >> "$LOG_FILE"
    
    # 圧縮ファイルかどうかをチェック
    if [[ "$LATEST_EXPORT" == *.zip ]] || [[ "$LATEST_EXPORT" == *.tar.gz ]] || [[ "$LATEST_EXPORT" == *.tgz ]] || [[ "$LATEST_EXPORT" == *.tar ]]; then
        echo "$(date): 圧縮ファイルを検出: $LATEST_EXPORT" >> "$LOG_FILE"
        # 圧縮ファイル処理スクリプトを使用
        python chatgpt_processor.py "$LATEST_EXPORT" >> "$LOG_FILE" 2>&1
    else
        # 通常のJSONファイル
        echo "$(date): Notion同期開始" >> "$LOG_FILE"
        python chatgpt_to_notion.py "$LATEST_EXPORT" >> "$LOG_FILE" 2>&1
    fi
    
    if [ $? -eq 0 ]; then
        echo "$(date): 同期完了" >> "$LOG_FILE"
        
        # 古いエクスポートファイルを削除（7日以上古いもの）
        find . -name "chatgpt_export_*" -mtime +7 -delete 2>/dev/null
    else
        echo "$(date): エラー: Notion同期に失敗しました" >> "$LOG_FILE"
    fi
else
    echo "$(date): 新しいエクスポートファイルが見つかりません" >> "$LOG_FILE"
fi

# ロックファイル削除
rm -f "$LOCK_FILE"

echo "$(date): ChatGPT同期終了" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"
