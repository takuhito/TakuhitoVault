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

#### 完全自動化（推奨）
```bash
# 引数なしで実行 - すべて自動検出
./scripts/save_chat_history.sh
```

#### 手動指定
```bash
# プロジェクト名と説明を手動指定
./scripts/save_chat_history.sh "HETEMLMonitor" "GitHub_Actions_Setup"

# チャット内容ファイルを指定
./scripts/save_chat_history.sh "HETEMLMonitor" "GitHub_Actions_Setup" "chat_content.txt"
```

#### 自動機能
- **プロジェクト自動検出**: 現在のディレクトリ構造からプロジェクト名を自動検出
- **クリップボード自動取得**: macOSのクリップボードからチャット内容を自動取得
- **ファイル読み込み**: 指定されたファイルからチャット内容を読み込み
- **成果自動生成**: チャット内容から成果を自動検出・生成
- **技術的詳細自動生成**: 使用技術、解決問題、学んだことを自動生成
- **テンプレート自動作成**: 構造化されたMarkdownテンプレートを自動作成
- **ファイル自動オープン**: 作成されたファイルを自動的に開く

#### 自動検出されるプロジェクト
- **HETEMLMonitor**: HETEMLMonitorディレクトリが存在する場合
- **ChatGPTToNotion**: ChatGPTToNotionディレクトリが存在する場合
- **NotionLinker**: NotionLinkerディレクトリが存在する場合
- **NotionWorkflowTools**: 上記以外の場合

#### 使用手順（完全自動化）
1. **チャット内容をコピー**: チャットの内容をクリップボードにコピー
2. **スクリプト実行**: `./scripts/save_chat_history.sh`（引数なし）
3. **自動処理完了**: すべての情報が自動的に検出・生成・保存される
4. **必要に応じて編集**: 成果、技術的詳細、次のステップを編集
5. **保存**: ファイルを保存

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
- クリップボードからの自動取得は、macOSの`pbpaste`コマンドを使用します
- ファイルから読み込む場合は、ファイルパスを正確に指定してください
- プロジェクト自動検出は、現在のディレクトリ構造に基づいて行われます

---

**更新日**: 2025年8月28日
