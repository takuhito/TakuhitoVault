# ローカル領収書自動処理システム

Google Driveの監視フォルダに配置された領収書画像を自動でNotionデータベースに登録するシステムです。

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成して以下の環境変数を設定してください：

```bash
# Notion設定
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=254b061dadf38042813eeab350aea734

# Gemini設定（オプション）
GEMINI_API_KEY=your_gemini_api_key_here

# Google Drive設定
GOOGLE_DRIVE_MONITOR_FOLDER=1YccjjOWIp4PAQVUY8SVcSvUvkcQ6lo3B
GOOGLE_DRIVE_PROCESSED_BASE=0AJojvkLIwToKUk9PVA
GOOGLE_DRIVE_ERROR_FOLDER=1HJrzj1DDoiTmIkNa8tIN3RKnLKs_8Kaf
GOOGLE_DRIVE_SHARED_DRIVE_ID=0AJojvkLIwToKUk9PVA
```

### 3. Google Drive認証ファイルの配置

`../credentials/service-account.json`にGoogle Drive APIのサービスアカウントキーを配置してください。

## 使用方法

### 基本的な実行

```bash
python main.py
```

### テスト実行

```bash
python test.py
```

## 機能

- Google Drive監視フォルダから新規ファイルを自動取得
- 領収書画像の処理（簡易版）
- Notionデータベースへの自動登録
- 処理済みファイルの自動移動

## 注意事項

- このシステムはローカル環境でのみ動作します
- GitHub Actionsは使用しません
- 実際のOCR処理は簡易版のため、手動での確認が必要です
