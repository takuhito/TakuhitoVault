# Scripts

このフォルダには、プロジェクトで使用する各種スクリプトが含まれています。

## スクリプト一覧

### チャット履歴管理
- **`save_chat_history.sh`** - チャット履歴を自動保存するスクリプト

### プロジェクト設定
- **`setup_complete.py`** - プロジェクトの完全セットアップ
- **`setup_google_drive.py`** - Google Drive APIの設定
- **`setup_notion_database.py`** - Notionデータベースの設定

### ユーティリティ
- **`check_notion_properties.py`** - Notionプロパティの確認
- **`get_google_drive_folder_ids.py`** - Google DriveフォルダIDの取得
- **`list_google_drive_folders.py`** - Google Driveフォルダ一覧の表示
- **`test_google_drive_access.py`** - Google Driveアクセステスト

### デプロイメント
- **`deploy.sh`** - デプロイメントスクリプト

## 使用方法

### チャット履歴の保存
```bash
# 基本的な使用方法
./scripts/save_chat_history.sh

# プロジェクト名を指定
./scripts/save_chat_history.sh "HETEMLMonitor"

# プロジェクト名と説明を指定
./scripts/save_chat_history.sh "HETEMLMonitor" "GitHub_Actions_Setup"
```

### プロジェクト設定
```bash
# 完全セットアップ
python scripts/setup_complete.py

# Google Drive設定
python scripts/setup_google_drive.py

# Notion設定
python scripts/setup_notion_database.py
```

### ユーティリティ
```bash
# Notionプロパティ確認
python scripts/check_notion_properties.py

# Google DriveフォルダID取得
python scripts/get_google_drive_folder_ids.py
```

## 注意事項

- スクリプトを実行する前に、必要な依存関係がインストールされていることを確認してください
- 環境変数や設定ファイルが正しく設定されていることを確認してください
- チャット履歴保存スクリプトは、macOSでファイルを自動的に開く機能があります

---

**更新日**: 2025年8月27日
