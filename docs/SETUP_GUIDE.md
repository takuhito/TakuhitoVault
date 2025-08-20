# 🚀 領収書自動処理システム セットアップガイド

## 📋 必要な準備

### 1. Notion API設定

#### 1.1 Notion Integration作成
1. [Notion Developers](https://www.notion.so/my-integrations)にアクセス
2. "New integration"をクリック
3. 以下を設定：
   - **Name**: `Receipt Processor`
   - **Associated workspace**: あなたのワークスペースを選択
   - **Capabilities**: Read content, Update content, Insert content

#### 1.2 Notionデータベース作成
1. Notionで新しいページを作成
2. `/database`と入力してデータベースを作成
3. 以下のプロパティを設定：

| プロパティ名 | タイプ | 説明 |
|-------------|--------|------|
| 店舗名 | Title | 店舗名（タイトル） |
| 日付 | Date | 購入日 |
| 金額 | Number | 合計金額 |
| カテゴリ | Select | 費用カテゴリ |
| 勘定科目 | Select | Freee勘定科目 |
| 商品一覧 | Rich text | 購入商品詳細 |
| 処理状況 | Select | 処理ステータス |
| 信頼度 | Number | データ抽出信頼度 |

#### 1.3 Integration連携
1. データベースページで`...`メニューをクリック
2. "Connections" → "Connect to"を選択
3. 作成したIntegration(`Receipt Processor`)を選択

#### 1.4 必要な情報取得
- **NOTION_TOKEN**: Integration設定ページの"Internal Integration Token"
- **NOTION_DATABASE_ID**: データベースURLの`/`と`?`の間の32文字の文字列

### 2. Google Drive設定

#### 2.1 フォルダ構造作成
```
📁 領収書処理
  ├── 📁 新規ファイル（監視対象）
  ├── 📁 処理済み
  │   ├── 📁 2024
  │   └── 📁 2025
  └── 📁 エラー
```

#### 2.2 フォルダID取得
1. 各フォルダをブラウザで開く
2. URLから以下のIDを取得：
   - **GOOGLE_DRIVE_MONITOR_FOLDER**: 新規ファイルフォルダのID
   - **GOOGLE_DRIVE_PROCESSED_BASE**: 処理済みフォルダのID  
   - **GOOGLE_DRIVE_ERROR_FOLDER**: エラーフォルダのID

例: `https://drive.google.com/drive/folders/1ABC...XYZ` → `1ABC...XYZ`

### 3. Google Cloud設定

#### 3.1 サービスアカウントキー
既に作成済みのサービスアカウントキーを使用します：
- ファイル: `credentials/service-account.json`

### 4. GitHub Secrets設定

GitHubリポジトリで以下のSecretsを設定：

#### 4.1 Secrets設定手順
1. GitHubリポジトリページで "Settings" → "Secrets and variables" → "Actions"
2. "New repository secret"で以下を追加：

| Secret名 | 値 | 説明 |
|---------|---|------|
| `GOOGLE_CLOUD_CREDENTIALS` | `credentials/service-account.json`の内容 | GCPサービスアカウント |
| `GOOGLE_CLOUD_PROJECT` | `receipt-processor-20241220` | GCPプロジェクトID |
| `NOTION_TOKEN` | `secret_xxx...` | Notion API Token |
| `NOTION_DATABASE_ID` | `abc123...` | NotionデータベースID |
| `GOOGLE_DRIVE_MONITOR_FOLDER` | `1ABC...XYZ` | 監視フォルダID |
| `GOOGLE_DRIVE_PROCESSED_BASE` | `1DEF...UVW` | 処理済みフォルダID |
| `GOOGLE_DRIVE_ERROR_FOLDER` | `1GHI...RST` | エラーフォルダID |

## 🎯 デプロイ方法

### 方法1: GitHub Actions（推奨）

#### 自動実行
- **スケジュール**: 毎日午前9時に自動実行
- **手動実行**: GitHub Actionsページから手動トリガー可能

#### 手順
1. 上記のSecretsを全て設定
2. コードをGitHubにプッシュ：
```bash
git add .
git commit -m "本番デプロイ設定完了"
git push origin main
```
3. GitHub ActionsのWorkflowが自動実行されます

### 方法2: ローカル実行

#### 環境変数設定
`.env.production`ファイルを編集：
```bash
cp .env.production .env
# .envファイルを編集して実際の値を設定
```

#### 実行
```bash
# 仮想環境の有効化
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 依存関係インストール
pip install -r requirements.txt

# 実行
python receipt-processor/main.py
```

## 🔍 テスト手順

### 1. 初回テスト
1. Google Driveの監視フォルダにテスト用領収書をアップロード
2. 処理が正常に実行されることを確認
3. Notionデータベースにデータが追加されることを確認

### 2. ログ確認
- **GitHub Actions**: Actionsページでログを確認
- **ローカル**: `logs/receipt-processor.log`を確認

## 🚨 トラブルシューティング

### よくある問題

#### 1. "Permission denied" エラー
- Notion Integrationがデータベースに接続されているか確認
- Google Driveフォルダの共有設定を確認

#### 2. "File not found" エラー  
- フォルダIDが正しいか確認
- サービスアカウントにフォルダへのアクセス権があるか確認

#### 3. OCR精度が低い
- 画像の解像度を上げる
- ファイル形式をPDFに変更

### サポート
- ログファイルの詳細情報を確認
- エラーメッセージを基に`docs/OPERATION_GUIDE.md`を参照

## 🎉 運用開始

全ての設定が完了したら：
1. テスト実行で動作確認
2. 定期実行の確認
3. 監視・アラートの設定
4. バックアップ戦略の実施

これで領収書の自動処理システムが稼働開始します！

