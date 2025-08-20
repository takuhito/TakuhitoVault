#!/bin/bash

# 本番デプロイスクリプト
set -e

echo "🚀 領収書自動処理システム 本番デプロイ開始"

# 設定値
PROJECT_ID=${1:-"your-project-id"}
REGION="asia-northeast1"
SERVICE_NAME="receipt-processor"

echo "📋 設定確認:"
echo "  プロジェクトID: $PROJECT_ID"
echo "  リージョン: $REGION"
echo "  サービス名: $SERVICE_NAME"

# Google Cloud プロジェクトを設定
echo "🔧 Google Cloud プロジェクト設定..."
gcloud config set project $PROJECT_ID

# 必要なAPIを有効化
echo "🔌 必要なAPIを有効化..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable vision.googleapis.com
gcloud services enable generativelanguageapi.googleapis.com

# サービスアカウントを作成
echo "👤 サービスアカウント作成..."
gcloud iam service-accounts create receipt-processor \
    --display-name="Receipt Processor Service Account" \
    --description="Service account for receipt processing system" \
    || echo "サービスアカウントは既に存在します"

# 必要な権限を付与
echo "🔐 権限設定..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:receipt-processor@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:receipt-processor@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# シークレットを作成（例）
echo "🔑 シークレット作成例..."
echo "以下のコマンドでシークレットを作成してください:"
echo ""
echo "gcloud secrets create notion-token --data-file=<(echo 'YOUR_NOTION_TOKEN')"
echo "gcloud secrets create notion-database-id --data-file=<(echo 'YOUR_DATABASE_ID')"
echo "gcloud secrets create drive-monitor-folder --data-file=<(echo 'YOUR_MONITOR_FOLDER_ID')"
echo "gcloud secrets create drive-processed-base --data-file=<(echo 'YOUR_PROCESSED_BASE_ID')"
echo "gcloud secrets create drive-error-folder --data-file=<(echo 'YOUR_ERROR_FOLDER_ID')"
echo "gcloud secrets create drive-shared-drive-id --data-file=<(echo 'YOUR_SHARED_DRIVE_ID')"
echo "gcloud secrets create gemini-api-key --data-file=<(echo 'YOUR_GEMINI_API_KEY')"
echo ""

# Dockerイメージをビルドしてデプロイ
echo "🐳 Dockerイメージビルド & デプロイ..."
gcloud builds submit --config deploy/cloudbuild.yaml \
    --substitutions PROJECT_ID=$PROJECT_ID

# Cloud Schedulerジョブを作成
echo "📅 Cloud Schedulerジョブ作成..."
gcloud scheduler jobs create http receipt-processor-job \
    --location=$REGION \
    --schedule="0 */6 * * *" \
    --time-zone="Asia/Tokyo" \
    --uri="https://$SERVICE_NAME-$PROJECT_ID.a.run.app/" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body='{"run":"true"}' \
    --oidc-service-account-email="receipt-processor@$PROJECT_ID.iam.gserviceaccount.com" \
    || echo "スケジューラジョブの作成をスキップ（既に存在する可能性があります）"

echo "✅ デプロイ完了!"
echo ""
echo "🔗 Cloud Run サービスURL:"
echo "https://$SERVICE_NAME-$PROJECT_ID.a.run.app/"
echo ""
echo "📊 監視とログ:"
echo "https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/logs?project=$PROJECT_ID"
echo ""
echo "⏰ スケジューラジョブ:"
echo "https://console.cloud.google.com/cloudscheduler?project=$PROJECT_ID"
