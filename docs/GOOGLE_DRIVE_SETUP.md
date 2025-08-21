# Google Drive認証情報の設定手順

## 🔑 **サービスアカウントキーの作成**

### 1. Google Cloud Consoleにアクセス
- [Google Cloud Console](https://console.cloud.google.com/)にアクセス
- プロジェクトを選択

### 2. サービスアカウントの作成
1. **IAM と管理** → **サービスアカウント**を選択
2. **サービスアカウントを作成**をクリック
3. 以下の情報を入力：
   - **サービスアカウント名**: `receipt-processor`
   - **説明**: `Receipt processing automation`
4. **作成して続行**をクリック

### 3. 権限の付与
1. **役割**で以下を選択：
   - `Cloud Run 管理者`
   - `サービスアカウント ユーザー`
   - `ストレージ管理者`
2. **完了**をクリック

### 4. キーの作成
1. 作成したサービスアカウントをクリック
2. **キー**タブを選択
3. **鍵を追加** → **新しい鍵を作成**
4. **JSON**を選択
5. **作成**をクリック

### 5. ダウンロードされたJSONファイルの内容
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "receipt-processor@your-project-id.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/receipt-processor%40your-project-id.iam.gserviceaccount.com"
}
```

## 🔧 **GitHub Secretsの設定**

### 1. GitHubリポジトリの設定
1. リポジトリの**Settings**タブをクリック
2. **Secrets and variables** → **Actions**を選択

### 2. 必要なSecretsの設定

#### `GOOGLE_DRIVE_CREDENTIALS`
- **Name**: `GOOGLE_DRIVE_CREDENTIALS`
- **Value**: 上記でダウンロードしたJSONファイルの**完全な内容**
- **重要**: JSONの改行文字も含めて、そのままコピー&ペースト

#### `GCP_SA_KEY`
- **Name**: `GCP_SA_KEY`
- **Value**: 上記のJSONファイルをBase64エンコードした値
- **コマンド**: `base64 -i your-service-account-key.json`

#### `GCP_PROJECT_ID`
- **Name**: `GCP_PROJECT_ID`
- **Value**: Google CloudプロジェクトID

#### `NOTION_TOKEN`
- **Name**: `NOTION_TOKEN`
- **Value**: Notion統合トークン

#### `GEMINI_API_KEY`
- **Name**: `GEMINI_API_KEY`
- **Value**: Gemini APIキー

## ✅ **設定の確認**

### 1. JSONの妥当性チェック
```bash
# JSONファイルが正しいかチェック
python -c "import json; json.load(open('service-account-key.json'))"
```

### 2. GitHub Actionsでの確認
- ワークフロー実行時に詳細なデバッグ情報が表示されます
- JSONの妥当性チェック結果を確認

## 🚨 **よくある問題**

### 1. JSONが不完全
- **症状**: `Expecting value: line 2 column 1 (char 1)`
- **原因**: JSONファイルの内容が不完全または改行が欠けている
- **解決**: 完全なJSONファイルの内容をコピー&ペースト

### 2. 改行文字の問題
- **症状**: JSON解析エラー
- **原因**: GitHub Secretsで改行文字が失われている
- **解決**: JSONファイルをそのままコピー&ペースト

### 3. 権限不足
- **症状**: `403 Forbidden`エラー
- **原因**: サービスアカウントに適切な権限がない
- **解決**: 必要な権限を追加

## 📋 **チェックリスト**

- [ ] Google Cloud Consoleでサービスアカウントを作成
- [ ] 適切な権限を付与
- [ ] JSONキーファイルをダウンロード
- [ ] JSONファイルの内容を確認
- [ ] GitHub Secretsに`GOOGLE_DRIVE_CREDENTIALS`を設定
- [ ] その他の必要なSecretsを設定
- [ ] ワークフローを実行してテスト
