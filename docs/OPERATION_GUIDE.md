# 領収書自動処理システム 運用ガイド

## 概要

このドキュメントは、領収書自動処理システムの運用に関する詳細な手順とベストプラクティスを説明します。

## システム構成

### アーキテクチャ
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   iPhone vFlat  │    │   Google Drive  │    │  GitHub Actions │
│     Scan App    │───▶│   Monitor       │───▶│   CI/CD         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Notion DB     │◀───│  Receipt        │◀───│  Google Cloud   │
│   (Freee Export)│    │  Processor      │    │  Run            │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### コンポーネント
- **Google Drive**: 領収書ファイルの監視・保存
- **Google Cloud Vision API**: OCR処理
- **Google Cloud Run**: メイン処理エンジン
- **Notion API**: データベース保存
- **GitHub Actions**: CI/CD・スケジュール実行

## デプロイメント手順

### 1. 事前準備

#### Google Cloud Platform設定
```bash
# プロジェクトの作成
gcloud projects create receipt-processor-YYYYMMDD

# 必要なAPIの有効化
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  vision.googleapis.com \
  drive.googleapis.com \
  secretmanager.googleapis.com

# サービスアカウントの作成
gcloud iam service-accounts create receipt-processor \
  --display-name="Receipt Processor Service Account"

# 必要な権限の付与
gcloud projects add-iam-policy-binding receipt-processor-YYYYMMDD \
  --member="serviceAccount:receipt-processor@receipt-processor-YYYYMMDD.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding receipt-processor-YYYYMMDD \
  --member="serviceAccount:receipt-processor@receipt-processor-YYYYMMDD.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### GitHub Secrets設定
以下のシークレットをGitHubリポジトリに設定：

```
GOOGLE_CLOUD_CREDENTIALS: サービスアカウントキー（JSON）
GOOGLE_CLOUD_PROJECT: プロジェクトID
GOOGLE_CLOUD_REGION: リージョン（asia-northeast1）
GOOGLE_APPLICATION_CREDENTIALS: サービスアカウントキーファイルパス
NOTION_TOKEN: Notion APIトークン
GOOGLE_DRIVE_MONITOR_FOLDER: 監視フォルダID
NOTION_DATABASE_ID: NotionデータベースID
```

### 2. 初回デプロイ

```bash
# リポジトリのクローン
git clone https://github.com/your-username/NotionWorkflowTools.git
cd NotionWorkflowTools

# 環境変数の設定
export PROJECT_ID=receipt-processor-YYYYMMDD
export REGION=asia-northeast1

# Dockerイメージのビルド・プッシュ
docker build -t gcr.io/$PROJECT_ID/receipt-processor:latest .
docker push gcr.io/$PROJECT_ID/receipt-processor:latest

# Cloud Runへのデプロイ
gcloud run deploy receipt-processor \
  --image gcr.io/$PROJECT_ID/receipt-processor:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_DRIVE_MONITOR_FOLDER=receipts,NOTION_DATABASE_ID=your-database-id"
```

### 3. シークレット管理

```bash
# Google Cloud Secret Managerにシークレットを保存
echo -n "your-notion-token" | \
  gcloud secrets create notion-token --data-file=-

echo -n "your-database-id" | \
  gcloud secrets create notion-database-id --data-file=-

# Cloud Runにシークレットをマウント
gcloud run services update receipt-processor \
  --region $REGION \
  --update-secrets="NOTION_TOKEN=notion-token:latest,NOTION_DATABASE_ID=notion-database-id:latest"
```

## 運用監視

### 1. ログ監視

#### Cloud Logging
```bash
# リアルタイムログの確認
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=receipt-processor"

# エラーログの検索
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=50
```

#### カスタムメトリクス
- 処理成功率
- 処理時間
- エラー発生率
- ファイル処理数

### 2. アラート設定

#### Cloud Monitoring
```yaml
# エラー率アラート
displayName: "Receipt Processor Error Rate"
conditions:
  - displayName: "Error rate > 5%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="receipt-processor"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0.05
      duration: 300s
```

### 3. パフォーマンス監視

#### システムメトリクス
- CPU使用率
- メモリ使用率
- リクエスト数
- レスポンス時間

#### 自動スケーリング
```bash
# スケーリング設定の確認
gcloud run services describe receipt-processor --region=$REGION --format="value(spec.template.metadata.annotations)"
```

## トラブルシューティング

### よくある問題と対処法

#### 1. OCR処理エラー
**症状**: Vision APIからのエラー
**対処法**:
```bash
# API使用量の確認
gcloud logging read "resource.type=api AND protoPayload.serviceName=vision.googleapis.com"

# クォータの確認
gcloud compute regions describe $REGION --format="value(quotas)"
```

#### 2. Notion API接続エラー
**症状**: Notionデータベースへの保存失敗
**対処法**:
```bash
# トークンの有効性確認
curl -H "Authorization: Bearer $NOTION_TOKEN" \
  https://api.notion.com/v1/users/me

# データベース権限の確認
curl -H "Authorization: Bearer $NOTION_TOKEN" \
  https://api.notion.com/v1/databases/$NOTION_DATABASE_ID
```

#### 3. Google Drive接続エラー
**症状**: ファイルの取得・移動失敗
**対処法**:
```bash
# サービスアカウントの権限確認
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:receipt-processor"

# Drive API使用量の確認
gcloud logging read "resource.type=api AND protoPayload.serviceName=drive.googleapis.com"
```

### デバッグ手順

#### 1. ローカルデバッグ
```bash
# 環境変数の設定
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
export NOTION_TOKEN="your-notion-token"
export GOOGLE_DRIVE_MONITOR_FOLDER="folder-id"
export NOTION_DATABASE_ID="database-id"

# デバッグモードで実行
cd receipt-processor
python -m debug_utils
python main.py
```

#### 2. ログ分析
```bash
# 構造化ログの解析
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.session_id:*" \
  --format="table(timestamp,jsonPayload.session_id,jsonPayload.operation_name,jsonPayload.duration)"
```

## メンテナンス

### 定期メンテナンス

#### 1. 週次メンテナンス
- ログファイルのローテーション
- 一時ファイルのクリーンアップ
- パフォーマンスメトリクスの確認

#### 2. 月次メンテナンス
- 依存関係の更新
- セキュリティパッチの適用
- バックアップの確認

#### 3. 四半期メンテナンス
- システム全体の見直し
- パフォーマンス最適化
- 新機能の検討

### バックアップ戦略

#### 1. 設定バックアップ
```bash
# Cloud Run設定のエクスポート
gcloud run services describe receipt-processor --region=$REGION > backup/service-config.yaml

# シークレットのバックアップ
gcloud secrets versions list notion-token --format="value(name)" > backup/secret-versions.txt
```

#### 2. データバックアップ
- Notionデータベースの定期エクスポート
- Google Driveフォルダの同期
- ログデータの長期保存

## セキュリティ

### アクセス制御
- 最小権限の原則
- サービスアカウントの権限管理
- APIキーの定期的なローテーション

### 監査ログ
```bash
# アクセスログの確認
gcloud logging read "resource.type=cloud_run_revision AND protoPayload.methodName:*" \
  --format="table(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail)"
```

## パフォーマンス最適化

### 1. 自動最適化
- システム負荷に応じた自動スケーリング
- キャッシュの活用
- 並列処理の最適化

### 2. 手動最適化
```bash
# パフォーマンス分析
gcloud run services describe receipt-processor --region=$REGION \
  --format="value(spec.template.spec.containerConcurrency,spec.template.spec.timeoutSeconds)"

# リソース使用量の確認
gcloud monitoring metrics list --filter="metric.type:run.googleapis.com"
```

## 緊急時対応

### 1. システム停止
```bash
# サービスの停止
gcloud run services update receipt-processor --region=$REGION --no-traffic

# 緊急時の復旧
gcloud run services update receipt-processor --region=$REGION --to-revisions=receipt-processor-00001
```

### 2. データ復旧
- バックアップからの復元
- 手動でのデータ移行
- 整合性チェックの実行

## 連絡先・サポート

### 緊急時連絡先
- システム管理者: admin@example.com
- 開発チーム: dev@example.com
- 運用チーム: ops@example.com

### ドキュメント
- [技術仕様書](./TECHNICAL_SPEC.md)
- [API仕様書](./API_SPEC.md)
- [トラブルシューティングガイド](./TROUBLESHOOTING.md)

