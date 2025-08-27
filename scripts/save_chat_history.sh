#!/bin/bash

# チャット履歴自動保存スクリプト
# 使用方法: ./save_chat_history.sh [プロジェクト名] [説明]

set -e

# 設定
CHAT_HISTORY_DIR="chat_history"
DATE=$(date +"%Y%m%d")
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 引数の処理
PROJECT_NAME=${1:-"General"}
DESCRIPTION=${2:-"Chat_History"}

# ファイル名の生成
FILENAME="${DATE}_${PROJECT_NAME}_${DESCRIPTION}.md"

# チャット履歴ディレクトリの作成
mkdir -p "$CHAT_HISTORY_DIR"

# ファイルパスの設定
FILEPATH="$CHAT_HISTORY_DIR/$FILENAME"

echo "=== チャット履歴保存スクリプト ==="
echo "日付: $DATE"
echo "プロジェクト: $PROJECT_NAME"
echo "説明: $DESCRIPTION"
echo "ファイル名: $FILENAME"
echo "保存先: $FILEPATH"
echo ""

# ファイルが既に存在する場合の処理
if [ -f "$FILEPATH" ]; then
    echo "⚠️  ファイルが既に存在します: $FILEPATH"
    echo "新しいファイル名を生成します..."
    
    # タイムスタンプ付きのファイル名を生成
    FILENAME="${DATE}_${PROJECT_NAME}_${DESCRIPTION}_${TIMESTAMP}.md"
    FILEPATH="$CHAT_HISTORY_DIR/$FILENAME"
    echo "新しいファイル名: $FILENAME"
fi

echo ""
echo "チャット履歴を保存中..."
echo ""

# チャット履歴のテンプレートを作成
cat > "$FILEPATH" << EOF
# チャット履歴

**日付**: $(date +"%Y年%m月%d日")  
**プロジェクト**: $PROJECT_NAME  
**説明**: $DESCRIPTION  
**参加者**: ユーザー、AI アシスタント

---

## チャット開始

**開始時刻**: $(date +"%Y年%m月%d日 %H:%M:%S")

---

## チャット内容

<!-- ここにチャットの内容を貼り付けてください -->

---

## チャット終了

**終了時刻**: $(date +"%Y年%m月%d日 %H:%M:%S")

### 成果
- [ ] タスク1
- [ ] タスク2
- [ ] タスク3

### 技術的詳細
- 使用した技術:
- 解決した問題:
- 学んだこと:

### 次のステップ
- [ ] 次のアクション1
- [ ] 次のアクション2

---

**作成日**: $(date +"%Y年%m月%d日")  
**ファイル**: $FILENAME
EOF

echo "✅ チャット履歴テンプレートを作成しました: $FILEPATH"
echo ""
echo "📝 次の手順:"
echo "1. チャット履歴をコピー"
echo "2. ファイル内の「チャット内容」セクションに貼り付け"
echo "3. 成果、技術的詳細、次のステップを記入"
echo "4. ファイルを保存"
echo ""
echo "💡 ヒント: チャット履歴をコピーして、ファイル内の適切な場所に貼り付けてください。"

# ファイルを開く（macOSの場合）
if command -v open >/dev/null 2>&1; then
    echo "📂 ファイルを開いています..."
    open "$FILEPATH"
fi

echo ""
echo "🎉 チャット履歴の保存準備が完了しました！"
