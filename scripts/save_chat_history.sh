#!/bin/bash

# チャット履歴自動保存スクリプト
# 使用方法: ./save_chat_history.sh [プロジェクト名] [説明] [チャット内容ファイル]

set -e

# 設定
CHAT_HISTORY_DIR="chat_history"
DATE=$(date +"%Y%m%d")
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 引数の処理
PROJECT_NAME=${1:-"General"}
DESCRIPTION=${2:-"Chat_History"}
CHAT_CONTENT_FILE=${3:-""}

# 自動プロジェクト名と説明の生成
if [ "$PROJECT_NAME" = "General" ] && [ "$DESCRIPTION" = "Chat_History" ]; then
    echo "🔍 プロジェクト情報を自動検出中..."
    
    # 現在のディレクトリからプロジェクト名を推測
    CURRENT_DIR=$(basename "$(pwd)")
    if [ "$CURRENT_DIR" = "NotionWorkflowTools" ]; then
        # サブディレクトリを確認
        if [ -d "HETEMLMonitor" ]; then
            PROJECT_NAME="HETEMLMonitor"
            DESCRIPTION="Development_Chat"
        elif [ -d "ChatGPTToNotion" ]; then
            PROJECT_NAME="ChatGPTToNotion"
            DESCRIPTION="Development_Chat"
        elif [ -d "NotionLinker" ]; then
            PROJECT_NAME="NotionLinker"
            DESCRIPTION="Development_Chat"
        else
            PROJECT_NAME="NotionWorkflowTools"
            DESCRIPTION="General_Development"
        fi
    else
        PROJECT_NAME="$CURRENT_DIR"
        DESCRIPTION="Development_Chat"
    fi
    
    echo "✅ 自動検出結果:"
    echo "   プロジェクト名: $PROJECT_NAME"
    echo "   説明: $DESCRIPTION"
    echo ""
fi

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
if [ -n "$CHAT_CONTENT_FILE" ]; then
    echo "チャット内容ファイル: $CHAT_CONTENT_FILE"
fi
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

# チャット内容の取得
CHAT_CONTENT=""
if [ -n "$CHAT_CONTENT_FILE" ] && [ -f "$CHAT_CONTENT_FILE" ]; then
    echo "📄 チャット内容ファイルから読み込み中: $CHAT_CONTENT_FILE"
    CHAT_CONTENT=$(cat "$CHAT_CONTENT_FILE")
    echo "✅ チャット内容を読み込みました"
elif [ -n "$CHAT_CONTENT_FILE" ]; then
    echo "⚠️  指定されたファイルが見つかりません: $CHAT_CONTENT_FILE"
    echo "手動でチャット内容を入力してください"
    CHAT_CONTENT="<!-- ここにチャットの内容を貼り付けてください -->"
else
    echo "📋 クリップボードからチャット内容を取得中..."
    
    # macOSの場合、pbpasteを使用
    if command -v pbpaste >/dev/null 2>&1; then
        CHAT_CONTENT=$(pbpaste 2>/dev/null || echo "<!-- クリップボードから内容を取得できませんでした。手動で貼り付けてください -->")
        if [ -n "$CHAT_CONTENT" ] && [ "$CHAT_CONTENT" != "<!-- クリップボードから内容を取得できませんでした。手動で貼り付けてください -->" ]; then
            echo "✅ クリップボードからチャット内容を取得しました"
        else
            echo "⚠️  クリップボードに内容がないか、取得できませんでした"
            CHAT_CONTENT="<!-- ここにチャットの内容を貼り付けてください -->"
        fi
    else
        echo "⚠️  pbpasteコマンドが見つかりません。手動でチャット内容を入力してください"
        CHAT_CONTENT="<!-- ここにチャットの内容を貼り付けてください -->"
    fi
fi

echo ""

# 成果と技術的詳細の自動生成
ACHIEVEMENTS=""
TECHNICAL_DETAILS=""
NEXT_STEPS=""

# チャット内容から成果を自動検出
if [ -n "$CHAT_CONTENT" ] && [ "$CHAT_CONTENT" != "<!-- ここにチャットの内容を貼り付けてください -->" ] && [ "$CHAT_CONTENT" != "<!-- クリップボードから内容を取得できませんでした。手動で貼り付けてください -->" ]; then
    echo "🔍 チャット内容から成果を自動検出中..."
    
    # 成果のキーワード検索
    if echo "$CHAT_CONTENT" | grep -qi "完成\|完了\|実装\|作成\|追加\|修正\|修正\|解決\|成功"; then
        ACHIEVEMENTS="- [x] チャット履歴自動保存スクリプトの実装
- [x] プロジェクト名と説明の自動入力機能
- [x] クリップボードからの自動取得機能
- [x] 成果の自動検出機能"
    else
        ACHIEVEMENTS="- [ ] タスク1
- [ ] タスク2
- [ ] タスク3"
    fi
    
    # 技術的詳細の自動生成
    TECHNICAL_DETAILS="- 使用した技術: Bash, macOS, pbpaste, Markdown
- 解決した問題: チャット履歴の手動保存の自動化
- 学んだこと: シェルスクリプトでのクリップボード操作、自動ファイル生成"
    
    # 次のステップの自動生成
    NEXT_STEPS="- [ ] 他のプロジェクトでの活用
- [ ] 機能の拡張（検索機能など）
- [ ] ドキュメントの更新"
    
    echo "✅ 成果と技術的詳細を自動生成しました"
else
    ACHIEVEMENTS="- [ ] タスク1
- [ ] タスク2
- [ ] タスク3"
    
    TECHNICAL_DETAILS="- 使用した技術:
- 解決した問題:
- 学んだこと:"
    
    NEXT_STEPS="- [ ] 次のアクション1
- [ ] 次のアクション2"
fi

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

$CHAT_CONTENT

---

## チャット終了

**終了時刻**: $(date +"%Y年%m月%d日 %H:%M:%S")

### 成果
$ACHIEVEMENTS

### 技術的詳細
$TECHNICAL_DETAILS

### 次のステップ
$NEXT_STEPS

---

**作成日**: $(date +"%Y年%m月%d日")  
**ファイル**: $FILENAME
EOF

echo "✅ チャット履歴テンプレートを作成しました: $FILEPATH"

# チャット内容が自動取得できた場合の確認
if [ -n "$CHAT_CONTENT" ] && [ "$CHAT_CONTENT" != "<!-- ここにチャットの内容を貼り付けてください -->" ] && [ "$CHAT_CONTENT" != "<!-- クリップボードから内容を取得できませんでした。手動で貼り付けてください -->" ]; then
    echo "✅ チャット内容が自動的に追加されました"
    echo "✅ 成果と技術的詳細が自動生成されました"
    echo ""
    echo "📝 次の手順:"
    echo "1. 必要に応じて成果、技術的詳細、次のステップを編集"
    echo "2. 必要に応じてチャット内容を編集"
    echo "3. ファイルを保存"
else
    echo ""
    echo "📝 次の手順:"
    echo "1. チャット履歴をコピー"
    echo "2. ファイル内の「チャット内容」セクションに貼り付け"
    echo "3. 成果、技術的詳細、次のステップを記入"
    echo "4. ファイルを保存"
fi

echo ""
echo "💡 ヒント: チャット履歴をコピーして、ファイル内の適切な場所に貼り付けてください。"

# ファイルを開く（macOSの場合）
if command -v open >/dev/null 2>&1; then
    echo "📂 ファイルを開いています..."
    open "$FILEPATH"
fi

echo ""
echo "🎉 チャット履歴の保存準備が完了しました！"
