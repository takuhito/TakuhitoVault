#!/bin/bash

# Notion Linker 拡張版実行スクリプト
# 4つの新しいデータベース（マイリンク、YouTube要約、AI Chat管理、行動）に対応

set -e

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 仮想環境の確認とアクティベート
if [ ! -d "venv" ]; then
    echo "仮想環境が見つかりません。作成します..."
    python3 -m venv venv
fi

# 仮想環境をアクティベート
source venv/bin/activate

# 依存関係の確認
if [ ! -f "requirements.txt" ]; then
    echo "requirements.txt が見つかりません。"
    exit 1
fi

# 依存関係のインストール（必要に応じて）
echo "依存関係を確認中..."
pip install -r requirements.txt

# .env ファイルの確認
if [ ! -f ".env" ]; then
    echo "警告: .env ファイルが見つかりません。"
    echo "README_extended.md を参考に .env ファイルを作成してください。"
    echo "初回実行時は DRY_RUN=true でテストすることをお勧めします。"
    echo ""
    echo "launchdでの自動実行のため、.envファイルなしでも続行します。"
fi

# 実行前の確認
echo "=== Notion Linker 拡張版実行前確認 ==="
echo "現在の時刻: $(date)"
echo "実行ディレクトリ: $(pwd)"
echo "Python バージョン: $(python --version)"
echo ""

# DRY_RUN の確認
if grep -q "DRY_RUN=true" .env 2>/dev/null; then
    echo "⚠️  テストモード（DRY_RUN=true）で実行します"
    echo "   実際の書き込みは行われません"
    echo ""
else
    echo "⚠️  本番モード（DRY_RUN=false）で実行します"
    echo "   Notion に実際に書き込みが行われます"
    echo ""
    echo "launchdでの自動実行のため、本番モードでも続行します。"
fi

# 実行
echo "=== Notion Linker 拡張版実行開始 ==="
python link_diary.py

echo ""
echo "=== 実行完了 ==="
echo "完了時刻: $(date)"
