# 本番デプロイガイド

## 🚀 本番デプロイ手順

### 1. 事前準備

#### 必要なアカウント・サービス
- [ ] Google Cloud Platform アカウント
- [ ] Notion API トークン
- [ ] GitHub アカウント
- [ ] Google Drive API アクセス

#### 必要なツール
- [ ] Google Cloud CLI (`gcloud`)
- [ ] Docker
- [ ] Git

### 2. Google Cloud Platform 設定

#### プロジェクト作成
```bash
# プロジェクト作成
gcloud projects create receipt-processor-20241220

# プロジェクト設定
gcloud config set project receipt-processor-20241220
```

#### 必要なAPIの有効化
```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  vision.googleapis.com \
  drive.googleapis.com \
  secretmanager.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

#### サービスアカウント作成
```bash
# サービスアカウント作成
gcloud iam service-accounts create receipt-processor \
  --display-name="Receipt Processor Service Account"

# 必要な権限の付与
gcloud projects add-iam-policy-binding receipt-processor-20241220 \
  --member="serviceAccount:receipt-processor@receipt-processor-20241220.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding receipt-processor-20241220 \
  --member="serviceAccount:receipt-processor@receipt-processor-20241220.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding receipt-processor-20241220 \
  --member="serviceAccount:receipt-processor@receipt-processor-20241220.iam.gserviceaccount.com" \
  --role="roles/vision.user"

gcloud projects add-iam-policy-binding receipt-processor-20241220 \
  --member="serviceAccount:receipt-processor@receipt-processor-20241220.iam.gserviceaccount.com" \
  --role="roles/drive.readonly"
```

#### サービスアカウントキーの作成
```bash
# キーファイルの作成
gcloud iam service-accounts keys create credentials/service-account.json \
  --iam-account=receipt-processor@receipt-processor-20241220.iam.gserviceaccount.com
```

### 3. Notion API 設定

#### Notion Integration の作成
1. [Notion Developers](https://developers.notion.com/) にアクセス
2. "New integration" をクリック
3. 以下の設定で作成：
   - Name: Receipt Processor
   - Associated workspace: あなたのワークスペース
   - Capabilities: Read content, Update content, Insert content

#### データベースの作成
1. Notionで新しいデータベースを作成
2. 以下のプロパティを追加：
   - 日付 (Date)
   - 店舗名 (Text)
   - 金額 (Number)
   - カテゴリ (Select)
   - 勘定科目 (Select)
   - 信頼度スコア (Number)
   - 処理ステータス (Select)
   - 元ファイル名 (Text)

#### データベースの共有
1. データベースページで "Share" をクリック
2. 作成したIntegrationを追加
3. データベースIDをコピー（URLの最後の部分）

### 4. Google Drive 設定

#### フォルダ構造の作成
```
Google Drive/
└── 領収書管理/
    ├── 受信箱/
    ├── 処理済み/
    └── エラー/
```

#### フォルダIDの取得
1. 各フォルダを開く
2. URLからフォルダIDをコピー
3. 例: `https://drive.google.com/drive/folders/1ABC123DEF456` → `1ABC123DEF456`

### 5. 環境変数の設定

#### .env ファイルの更新
```bash
# 現在の.envファイルをバックアップ
cp .env .env.backup

# 新しい.envファイルを作成
cat > .env << 'EOF'
# Google Cloud Platform設定
GOOGLE_CLOUD_PROJECT=receipt-processor-20241220
GOOGLE_CLOUD_REGION=asia-northeast1
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json

# Notion設定
NOTION_TOKEN=your_actual_notion_token_here
NOTION_DATABASE_ID=your_actual_database_id_here

# Google Drive設定
GOOGLE_DRIVE_MONITOR_FOLDER=your_monitor_folder_id_here
GOOGLE_DRIVE_PROCESSED_BASE=your_processed_folder_id_here
GOOGLE_DRIVE_ERROR_FOLDER=your_error_folder_id_here

# ログ設定
LOG_LEVEL=INFO
LOG_FILE=./logs/receipt-processor.log

# 処理設定
MAX_CONCURRENT_PROCESSES=4
BATCH_SIZE=10
CONFIDENCE_THRESHOLD=0.7
EOF
```

### 6. GitHub Secrets 設定

#### 必要なSecrets
GitHubリポジトリの Settings > Secrets and variables > Actions で以下を設定：

```
GOOGLE_CLOUD_CREDENTIALS: サービスアカウントキーのJSON内容
GOOGLE_CLOUD_PROJECT: receipt-processor-20241220
GOOGLE_CLOUD_REGION: asia-northeast1
GOOGLE_APPLICATION_CREDENTIALS: ./credentials/service-account.json
NOTION_TOKEN: あなたのNotionトークン
GOOGLE_DRIVE_MONITOR_FOLDER: 監視フォルダID
NOTION_DATABASE_ID: データベースID
```

### 7. 本番デプロイ実行

#### 自動デプロイ（推奨）
```bash
# GitHubにプッシュ
git add .
git commit -m "本番デプロイ準備完了"
git push origin main

# GitHub Actionsが自動的にデプロイを実行
```

#### 手動デプロイ
```bash
# デプロイスクリプト実行
./deploy.sh production
```

### 8. デプロイ後の確認

#### サービスURLの確認
```bash
# Cloud Runサービスの確認
gcloud run services list --region=asia-northeast1

# サービスURLの取得
gcloud run services describe receipt-processor \
  --region=asia-northeast1 \
  --format="value(status.url)"
```

#### ログの確認
```bash
# リアルタイムログ
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=receipt-processor"

# エラーログ
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=10
```

#### 動作テスト
1. Google Driveの監視フォルダにテスト画像をアップロード
2. 30秒以内にNotionデータベースにレコードが作成されることを確認
3. 処理済みフォルダにファイルが移動されることを確認

### 9. 監視・アラート設定

#### Cloud Monitoring アラート
```bash
# エラー率アラートの作成
gcloud alpha monitoring policies create \
  --policy-from-file=monitoring/error-rate-alert.yaml
```

#### ログベースアラート
```bash
# エラーログアラートの作成
gcloud logging sinks create error-alert \
  bigquery.googleapis.com/projects/receipt-processor-20241220/datasets/logs \
  --log-filter="resource.type=cloud_run_revision AND severity>=ERROR"
```

### 10. 運用開始

#### スケジュール実行の確認
- GitHub Actionsの "process-receipts" ジョブが毎日午前9時に実行されることを確認
- 手動実行も可能（GitHub Actions > Actions > receipt-processor > Run workflow）

#### 定期メンテナンス
- 週次: ログの確認、エラー率の確認
- 月次: 依存関係の更新、セキュリティパッチの適用
- 四半期: システム全体の見直し

## 🔧 トラブルシューティング

### よくある問題

#### 1. 認証エラー
```bash
# サービスアカウントの確認
gcloud auth list

# 認証の再実行
gcloud auth activate-service-account --key-file=credentials/service-account.json
```

#### 2. API制限エラー
```bash
# API使用量の確認
gcloud compute regions describe asia-northeast1 --format="value(quotas)"

# クォータの増加申請
gcloud compute regions describe asia-northeast1 --format="value(quotas[].limit)"
```

#### 3. メモリ不足エラー
```bash
# Cloud Runのリソース設定を調整
gcloud run services update receipt-processor \
  --region=asia-northeast1 \
  --memory=4Gi \
  --cpu=2
```

### ロールバック手順
```bash
# 前のリビジョンに戻す
gcloud run services update-traffic receipt-processor \
  --region=asia-northeast1 \
  --to-revisions=receipt-processor-00001=100
```

## 📞 サポート

問題が発生した場合は以下を確認：

1. [運用ガイド](./OPERATION_GUIDE.md)
2. [トラブルシューティングガイド](./TROUBLESHOOTING.md)
3. GitHub Issues
4. Google Cloud Support

---

**最終更新**: 2024年1月20日  
**バージョン**: 1.0.0

