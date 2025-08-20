# 領収書自動処理システム

iPhoneでスキャンした領収書を自動でOCR解析し、Notionデータベースに保存するシステムです。

## 概要

このシステムは以下の処理フローで動作します：

```
iPhone (vFlat Scan) 
    ↓ JPG/PNG/PDF（複数ページ対応）
Google Drive (/領収書管理/受信箱/)
    ↓ 定期チェック
GitHub Actions (Python)
    ↓ AI解析 + 日記連携 + PDF処理
Notion Database (領収書管理 DB)
    ↓ 手動CSVエクスポート
Freee (手動インポート)
```

## 機能

- **自動OCR処理**: Google Cloud Vision APIを使用した高精度なテキスト抽出
- **PDF対応**: 複数ページPDFの自動処理
- **データ解析**: 日付、金額、店舗名の自動抽出
- **カテゴリ判定**: 店舗名に基づく自動カテゴリ・勘定科目判定
- **Notion連携**: 自動でNotionデータベースに保存
- **ファイル管理**: 処理済みファイルの自動整理
- **エラーハンドリング**: 処理失敗時の適切なエラー処理

## 技術スタック

- **Python 3.11**
- **Google Drive API**: ファイル管理
- **Google Cloud Vision API**: OCR処理
- **Notion API**: データベース操作
- **GitHub Actions**: 定期実行
- **PyPDF2/pdf2image**: PDF処理

## セットアップ

### 1. 必要なAPIの設定

#### Google Drive API
1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. Google Drive APIを有効化
3. 認証情報を作成（OAuth 2.0クライアントID）
4. `credentials.json`ファイルをダウンロード

#### Google Cloud Vision API
1. Google Cloud ConsoleでVision APIを有効化
2. サービスアカウントキーを作成
3. `vision-credentials.json`ファイルをダウンロード

#### Notion API
1. [Notion Developers](https://developers.notion.com/)でインテグレーションを作成
2. インテグレーショントークンを取得
3. データベースにインテグレーションを追加

### 2. 環境変数の設定

`env.example`を参考に`.env`ファイルを作成：

```bash
# Notion API Settings
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=254b061dadf38042813eeab350aea734

# Google Drive API Settings
GOOGLE_DRIVE_CREDENTIALS_FILE=path_to_your_google_drive_credentials.json
GOOGLE_DRIVE_TOKEN_FILE=path_to_your_google_drive_token.json

# Google Cloud Vision API Settings
GOOGLE_CLOUD_PROJECT_ID=your_google_cloud_project_id
GOOGLE_CLOUD_CREDENTIALS_FILE=path_to_your_google_cloud_credentials.json

# File Processing Settings
GOOGLE_DRIVE_MONITOR_FOLDER=/領収書管理/受信箱/
GOOGLE_DRIVE_PROCESSED_BASE=/領収書管理/
GOOGLE_DRIVE_ERROR_FOLDER=/領収書管理/エラー/

# Processing Settings
MAX_FILE_SIZE=10485760  # 10MB in bytes
MAX_PDF_PAGES=20
SUPPORTED_IMAGE_FORMATS=.jpg,.jpeg,.png
SUPPORTED_PDF_FORMATS=.pdf

# Logging Settings
LOG_LEVEL=INFO
LOG_FILE=receipt_processor.log
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. Google Driveフォルダ構造の作成

以下のフォルダ構造をGoogle Driveに作成：

```
/領収書管理/
├── 受信箱/
├── エラー/
├── 2025/
│   ├── 01/
│   ├── 02/
│   └── ...
└── 2024/
    ├── 12/
    └── ...
```

### 5. Notionデータベースの設定

データベースID: `254b061dadf38042813eeab350aea734`

必要なプロパティ：
- タイトル (Title)
- 発生日 (Date)
- 店舗名 (Text)
- 合計金額 (Number)
- 税抜金額 (Number)
- 消費税 (Number)
- 支払方法 (Select)
- カテゴリ (Multi-select)
- 勘定科目 (Select)
- 備考 (Text)
- ファイル (Files)
- 処理状況 (Select)
- 日記 (Relation)
- 一致用日付 (Formula)
- ページ数 (Number)
- 処理メモ (Text)

## 使用方法

### ローカル実行

```bash
cd receipt-processor
python main.py
```

### GitHub Actions実行

1. GitHub Secretsに必要な環境変数を設定
2. 手動実行または定期実行（毎日午前9時）

## ファイル構造

```
NotionWorkflowTools/
├── .github/
│   └── workflows/
│       └── process_receipts.yml
├── receipt-processor/
│   ├── __init__.py
│   ├── main.py              # メイン処理
│   ├── google_drive_client.py    # Google Drive API
│   ├── vision_client.py     # Vision API
│   ├── notion_client.py     # Notion API
│   ├── pdf_processor.py     # PDF処理
│   ├── receipt_parser.py    # 領収書解析
│   ├── file_manager.py      # ファイル管理
│   └── utils.py             # ユーティリティ
├── config/
│   ├── settings.py          # 設定
│   └── mapping.py           # マッピング設定
├── tests/                   # テストファイル
├── requirements.txt         # 依存関係
├── env.example             # 環境変数テンプレート
└── README.md               # このファイル
```

## 処理フロー

1. **ファイル検出**: Google Driveの監視フォルダから新規ファイルを検出
2. **ファイルダウンロード**: ローカルに一時ダウンロード
3. **ファイル検証**: ファイル形式・サイズの妥当性チェック
4. **OCR処理**: Google Cloud Vision APIでテキスト抽出
5. **データ解析**: 日付・金額・店舗名の抽出とカテゴリ判定
6. **Notion保存**: 解析結果をNotionデータベースに保存
7. **ファイル移動**: 処理済みファイルを年度・月度フォルダに移動
8. **クリーンアップ**: 一時ファイルの削除

## エラーハンドリング

- **ファイル形式エラー**: 未対応ファイル形式の場合はエラーフォルダに移動
- **OCRエラー**: テキスト抽出失敗時は手動確認要としてマーク
- **APIエラー**: 各APIの制限やエラーを適切に処理
- **データ検証**: 抽出データの妥当性をチェック

## カスタマイズ

### カテゴリ・勘定科目の追加

`config/mapping.py`の`STORE_CATEGORY_MAPPING`を編集：

```python
STORE_CATEGORY_MAPPING = {
    '新しい店舗名': ('カテゴリ', '勘定科目'),
    # ...
}
```

### 処理設定の変更

`config/settings.py`で各種設定を変更可能：

- ファイルサイズ制限
- サポートファイル形式
- ログレベル
- など

## トラブルシューティング

### よくある問題

1. **認証エラー**: API認証情報が正しく設定されているか確認
2. **ファイル移動エラー**: Google Driveの権限設定を確認
3. **OCR精度**: 画像の品質や向きを確認
4. **Notion保存エラー**: データベースのプロパティ設定を確認

### ログの確認

```bash
tail -f receipt_processor.log
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要望は、GitHubのIssuesでお知らせください。

## 更新履歴

- v1.0.0: 初回リリース
  - 基本的なOCR処理機能
  - PDF対応
  - Notion連携
  - ファイル管理機能

