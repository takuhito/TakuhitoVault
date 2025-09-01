#!/bin/bash
# .envファイル同期スクリプト
# ルートの.envファイルを各サブディレクトリに同期

ROOT_ENV="/Users/takuhito/NotionWorkflowTools/.env"

if [ ! -f "$ROOT_ENV" ]; then
    echo "❌ ルートの.envファイルが見つかりません: $ROOT_ENV"
    exit 1
fi

echo "🔄 .envファイルを同期中..."

# 各サブディレクトリに.envファイルを同期
cp "$ROOT_ENV" "/Users/takuhito/NotionWorkflowTools/ChatGPTToNotion/.env"
cp "$ROOT_ENV" "/Users/takuhito/NotionWorkflowTools/ChatHistoryToNotion/.env"
cp "$ROOT_ENV" "/Users/takuhito/NotionWorkflowTools/NotionLinker/.env"
cp "$ROOT_ENV" "/Users/takuhito/NotionWorkflowTools/MovableTypeRebuilder/.env"
cp "$ROOT_ENV" "/Users/takuhito/NotionWorkflowTools/HETEMLMonitor/.env"

echo "✅ .envファイルの同期が完了しました"
echo "📁 同期先:"
echo "   - ChatGPTToNotion/.env"
echo "   - ChatHistoryToNotion/.env"
echo "   - NotionLinker/.env"
echo "   - MovableTypeRebuilder/.env"
echo "   - HETEMLMonitor/.env"
