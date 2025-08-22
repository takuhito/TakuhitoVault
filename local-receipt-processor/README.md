# ローカル領収書自動処理システム

Google Driveの監視フォルダに配置された領収書画像を自動でNotionデータベースに登録するシステムです。

## 🚀 クイックスタート

### 1. 自動セットアップ

```bash
./run.sh
```

このスクリプトが以下を自動で実行します：
- 仮想環境の作成
- 依存関係のインストール
- システムテストの実行

### 2. 手動セットアップ

#### 依存関係のインストール

```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境をアクティベート
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

#### 環境変数の設定

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

#### Google Drive認証ファイルの配置

`../credentials/service-account.json`にGoogle Drive APIのサービスアカウントキーを配置してください。

## 📋 使用方法

### 基本的な実行

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# メイン処理を実行
python main.py
```

### テスト実行

```bash
# 簡易テスト（APIキーなしでも実行可能）
python simple_test.py

# 完全テスト（APIキーが必要）
python test.py
```

## 🔧 システム構成

```
local-receipt-processor/
├── config.py              # 設定ファイル
├── google_drive_client.py # Google Drive APIクライアント
├── notion_api_client.py   # Notion APIクライアント
├── main.py               # メイン処理スクリプト
├── test.py               # 完全テストスクリプト
├── simple_test.py        # 簡易テストスクリプト
├── run.sh                # 自動セットアップスクリプト
├── requirements.txt      # 依存関係
├── .env                  # 環境変数（要作成）
└── README.md            # このファイル
```

## 🎯 機能

- ✅ **Google Drive監視** - 指定フォルダから新規ファイルを自動取得
- ✅ **ファイル処理** - 領収書画像のダウンロードと処理
- ✅ **Notion連携** - データベースへの自動登録
- ✅ **ファイル管理** - 処理済みファイルの自動移動
- ✅ **ローカル環境** - GitHub Actionsに依存しない
- ✅ **エラーハンドリング** - 処理失敗時の適切な対応

## 📝 注意事項

- このシステムはローカル環境でのみ動作します
- GitHub Actionsは使用しません
- 実際のOCR処理は簡易版のため、手動での確認が必要です
- APIキーは適切に管理し、`.env`ファイルをGitにコミットしないでください

## 🔍 トラブルシューティング

### よくある問題

1. **仮想環境が見つからない**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **依存関係のインストールエラー**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **認証ファイルが見つからない**
   - `../credentials/service-account.json`が存在することを確認
   - Google Cloud Consoleでサービスアカウントキーをダウンロード

4. **APIキーが無効**
   - GitHub Secretsから正しい値を取得
   - `.env`ファイルの値を更新

### ログの確認

処理の詳細ログは`receipt_processor.log`に出力されます。
