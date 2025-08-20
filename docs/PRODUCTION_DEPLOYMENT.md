# 本番環境デプロイガイド

## 🚀 クイックスタート

### 1. 前提条件

- Google Cloud Platform アカウント
- gcloud CLI インストール済み
- Docker インストール済み
- 課金アカウント設定済み

### 2. 初回セットアップ

```bash
# 1. リポジトリをクローン
git clone https://github.com/your-username/NotionWorkflowTools.git
cd NotionWorkflowTools

# 2. Google Cloud プロジェクトを作成
gcloud projects create your-project-id
gcloud config set project your-project-id

# 3. デプロイスクリプトを実行
./scripts/deploy.sh your-project-id
```

### 3. シークレット設定

以下のコマンドでシークレットを設定してください：

```bash
# Notion設定
gcloud secrets create notion-token --data-file=<(echo 'REDACTED_NOTION')
gcloud secrets create notion-database-id --data-file=<(echo '254b061dadf38042813eeab350aea734')

# Google Drive設定
gcloud secrets create drive-monitor-folder --data-file=<(echo '1YccjjOWIp4PAQVUY8SVcSvUvkcQ6lo3B')
gcloud secrets create drive-processed-base --data-file=<(echo '0AJojvkLIwToKUk9PVA')
gcloud secrets create drive-error-folder --data-file=<(echo '1HJrzj1DDoiTmIkNa8tIN3RKnLKs_8Kaf')
gcloud secrets create drive-shared-drive-id --data-file=<(echo '0AJojvkLIwToKUk9PVA')

# Gemini API設定
gcloud secrets create gemini-api-key --data-file=<(echo 'AIzaSyBe7UyOwcdznz-mr3oWRpW5Juwa3CZMa5I')

# Google認証ファイル（サービスアカウント）
gcloud secrets create service-account-key --data-file=path/to/your/service-account.json
```

### 4. 手動デプロイ

```bash
# Dockerイメージをビルド
gcloud builds submit --config deploy/cloudbuild.yaml

# サービスをデプロイ
gcloud run deploy receipt-processor \
    --image gcr.io/your-project-id/receipt-processor:latest \
    --region asia-northeast1 \
    --platform managed \
    --memory 2Gi \
    --cpu 1 \
    --timeout 900 \
    --max-instances 1 \
    --min-instances 0 \
    --no-allow-unauthenticated
```

## 📅 定期実行設定

システムは6時間毎に自動実行されます：

```bash
# スケジューラジョブの確認
gcloud scheduler jobs list --location=asia-northeast1

# 手動実行
gcloud scheduler jobs run receipt-processor-job --location=asia-northeast1
```

## 📊 監視とログ

### Cloud Loggingでログを確認

```bash
# リアルタイムログの表示
gcloud logs tail projects/your-project-id/logs/run.googleapis.com%2Fstdout

# エラーログのフィルタリング
gcloud logs read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=50
```

### Cloud Runメトリクス

- CPU使用率
- メモリ使用率  
- リクエスト数
- エラー率

## 🔧 トラブルシューティング

### よくある問題

1. **メモリ不足エラー**
   ```bash
   gcloud run services update receipt-processor --memory 4Gi --region asia-northeast1
   ```

2. **タイムアウトエラー**
   ```bash
   gcloud run services update receipt-processor --timeout 900 --region asia-northeast1
   ```

3. **権限エラー**
   ```bash
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:receipt-processor@your-project-id.iam.gserviceaccount.com" \
       --role="roles/secretmanager.secretAccessor"
   ```

### ログレベルの調整

環境変数 `LOG_LEVEL` を設定してログレベルを調整：

```bash
gcloud run services update receipt-processor \
    --set-env-vars LOG_LEVEL=DEBUG \
    --region asia-northeast1
```

## 🔄 CI/CDパイプライン

### GitHub Actionsの設定

1. GitHubリポジトリのSecretsに以下を追加：
   - `GCP_PROJECT_ID`: Google CloudプロジェクトID
   - `GCP_SA_KEY`: サービスアカウントキー（JSON形式）

2. mainブランチへのプッシュで自動デプロイが実行されます

### 手動デプロイ

```bash
# 最新のコードでデプロイ
git push origin main
```

## 💰 コスト最適化

### リソース設定の推奨値

- **CPU**: 1 vCPU
- **メモリ**: 2GB
- **最大インスタンス数**: 1
- **最小インスタンス数**: 0（コスト削減）
- **タイムアウト**: 900秒

### 推定月額コスト

- Cloud Run: 約$5-15/月
- Cloud Storage: 約$1-5/月  
- Cloud Logging: 約$1-3/月
- Cloud Scheduler: 無料枠内

## 🚨 アラート設定

### Cloud Monitoringアラート

```bash
# エラー率アラート
gcloud alpha monitoring policies create \
    --policy-from-file=monitoring/error-rate-alert.yaml

# メモリ使用率アラート  
gcloud alpha monitoring policies create \
    --policy-from-file=monitoring/memory-usage-alert.yaml
```

### 通知設定

- Slack通知
- メール通知
- SMS通知（重要なアラートのみ）

## 📈 スケーリング

### 負荷に応じた自動スケーリング

```bash
# 最大インスタンス数を増加
gcloud run services update receipt-processor \
    --max-instances 5 \
    --region asia-northeast1
```

### パフォーマンス監視

- レスポンス時間
- スループット
- エラー率
- リソース使用率

## 🔐 セキュリティ

### ベストプラクティス

1. **最小権限の原則**: 必要最小限の権限のみ付与
2. **シークレット管理**: Secret Managerを使用
3. **ネットワーク制限**: 内部アクセスのみ許可
4. **ログ監視**: 不審なアクセスの検出

### 定期的なセキュリティ監査

```bash
# セキュリティスキャン
gcloud beta container images scan IMAGE_URL

# 権限の確認
gcloud projects get-iam-policy your-project-id
```

## 📞 サポート

問題が発生した場合：

1. **ログを確認**: Cloud Loggingでエラー詳細を確認
2. **監視メトリクス**: Cloud Monitoringで異常を検出
3. **GitHub Issues**: バグレポートや機能要望
4. **ドキュメント**: 追加のヘルプとガイド

---

**注意**: 本番環境では定期的なバックアップとモニタリングを実施してください。
