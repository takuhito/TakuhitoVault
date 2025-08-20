#!/bin/bash

# 領収書自動処理システム デプロイスクリプト
# 使用方法: ./deploy.sh [環境名]

set -e

# 色付きログ関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# 環境設定
ENVIRONMENT=${1:-production}
PROJECT_ID="receipt-processor-20241220"
REGION="asia-northeast1"
SERVICE_NAME="receipt-processor"

log_info "🚀 領収書自動処理システム デプロイ開始"
log_info "環境: $ENVIRONMENT"
log_info "プロジェクト: $PROJECT_ID"
log_info "リージョン: $REGION"

# 1. 前提条件チェック
log_info "📋 前提条件チェック中..."

# Python環境チェック
if ! command -v python3 &> /dev/null; then
    log_error "Python3 がインストールされていません"
    exit 1
fi

# Docker環境チェック
if ! command -v docker &> /dev/null; then
    log_warn "Docker がインストールされていません。ローカル実行モードで進めます。"
    DOCKER_MODE=false
else
    DOCKER_MODE=true
    log_info "Docker 環境確認完了"
fi

# Google Cloud CLIチェック
if ! command -v gcloud &> /dev/null; then
    log_warn "Google Cloud CLI がインストールされていません。ローカル実行モードで進めます。"
    CLOUD_MODE=false
else
    CLOUD_MODE=true
    log_info "Google Cloud CLI 環境確認完了"
fi

# 2. 依存関係インストール
log_info "📦 依存関係インストール中..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 3. テスト実行
log_info "🧪 テスト実行中..."
cd tests
python3 -m pytest -v --tb=short
cd ..

# 4. 環境変数チェック
log_info "🔧 環境変数チェック中..."
if [ ! -f ".env" ]; then
    log_warn ".env ファイルが見つかりません。env.example をコピーして設定してください。"
    cp env.example .env
    log_info "env.example を .env にコピーしました。設定を編集してください。"
    exit 1
fi

# 環境変数を読み込み
source .env

# 5. 設定検証
log_info "✅ 設定検証中..."
cd receipt-processor
python3 -c "
import sys
sys.path.append('..')
from config.settings import validate_settings
errors = validate_settings()
if errors:
    print('設定エラー:')
    for error in errors:
        print(f'  - {error}')
    sys.exit(1)
print('設定検証完了')
"
cd ..

# 6. ローカル実行テスト
log_info "🔍 ローカル実行テスト中..."
cd receipt-processor
timeout 30s python3 main.py || true
cd ..

# 7. Dockerビルド（Docker利用可能な場合）
if [ "$DOCKER_MODE" = true ]; then
    log_info "🐳 Dockerイメージビルド中..."
    docker build -t $SERVICE_NAME:$ENVIRONMENT .
    log_info "Dockerイメージビルド完了: $SERVICE_NAME:$ENVIRONMENT"
fi

# 8. Google Cloud デプロイ（Cloud CLI利用可能な場合）
if [ "$CLOUD_MODE" = true ]; then
    log_info "☁️ Google Cloud デプロイ中..."
    
    # プロジェクト設定
    gcloud config set project $PROJECT_ID
    
    # 必要なAPIを有効化
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        vision.googleapis.com \
        drive.googleapis.com \
        secretmanager.googleapis.com
    
    # Dockerイメージをプッシュ
    if [ "$DOCKER_MODE" = true ]; then
        gcloud auth configure-docker
        docker tag $SERVICE_NAME:$ENVIRONMENT gcr.io/$PROJECT_ID/$SERVICE_NAME:$ENVIRONMENT
        docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:$ENVIRONMENT
    fi
    
    # Cloud Runにデプロイ
    gcloud run deploy $SERVICE_NAME \
        --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$ENVIRONMENT \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --set-env-vars="GOOGLE_DRIVE_MONITOR_FOLDER=$GOOGLE_DRIVE_MONITOR_FOLDER,NOTION_DATABASE_ID=$NOTION_DATABASE_ID" \
        --memory 2Gi \
        --cpu 1 \
        --max-instances 10
    
    log_info "✅ Google Cloud Run デプロイ完了"
    log_info "サービスURL: https://$SERVICE_NAME-$REGION-$PROJECT_ID.a.run.app"
else
    log_warn "Google Cloud CLI が利用できないため、ローカル実行モードで完了"
    log_info "本番デプロイには Google Cloud CLI のインストールが必要です"
fi

# 9. デプロイ完了
log_info "🎉 デプロイ完了！"
log_info ""
log_info "次のステップ:"
log_info "1. .env ファイルで環境変数を設定"
log_info "2. Google Cloud CLI をインストール（本番デプロイ用）"
log_info "3. サービスアカウントキーを設定"
log_info "4. GitHub Secrets を設定"
log_info ""
log_info "詳細は docs/OPERATION_GUIDE.md を参照してください"

