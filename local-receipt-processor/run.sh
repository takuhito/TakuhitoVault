#!/bin/bash

# ローカル領収書自動処理システム実行スクリプト

echo "🚀 ローカル領収書自動処理システム"
echo "=================================="

# 仮想環境の確認
if [ ! -d "venv" ]; then
    echo "❌ 仮想環境が見つかりません。作成します..."
    python3 -m venv venv
fi

# 仮想環境をアクティベート
echo "🔧 仮想環境をアクティベート中..."
source venv/bin/activate

# 依存関係の確認
if [ ! -f "venv/lib/python*/site-packages/notion_client" ]; then
    echo "📦 依存関係をインストール中..."
    pip install -r requirements.txt
fi

# 環境変数ファイルの確認
if [ ! -f ".env" ]; then
    echo "❌ .envファイルが見つかりません"
    echo "GitHub Secretsから取得した値を設定してください"
    exit 1
fi

# 認証ファイルの確認
if [ ! -f "../credentials/service-account.json" ]; then
    echo "❌ Google Drive認証ファイルが見つかりません"
    echo "../credentials/service-account.json を配置してください"
    exit 1
fi

# テスト実行
echo "🧪 システムテスト実行中..."
python simple_test.py

echo ""
echo "✅ 準備完了！"
echo "📝 実際のAPIキーを設定してから以下を実行してください："
echo "   python main.py"
