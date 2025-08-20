# NotionWorkflowTools Workspace

このワークスペースは、Notionとの連携を行う複数のプロジェクトを管理するためのリポジトリです。

## 📁 プロジェクト構成

```
NotionWorkflowTools/             # メインワークスペース
├── NotionLinker/               # NotionLinkerプロジェクト
│   ├── link_diary.py           # 日記リンク機能
│   ├── create_missing_journal_pages.py
│   ├── merge_duplicate_pages.py
│   ├── remove_duplicate_pages.py
│   ├── notion_title_updater.py
│   ├── run_linker.sh           # 実行スクリプト
│   ├── requirements.txt        # Python依存関係
│   └── README.txt              # 詳細ドキュメント
├── ChatGPTToNotion/            # ChatGPT to Notionプロジェクト
│   ├── chatgpt_to_notion.py    # メインスクリプト
│   ├── chatgpt_export_helper.py
│   ├── chatgpt_sync.sh         # 自動同期スクリプト
│   ├── setup_chatgpt_sync.py   # セットアップスクリプト
│   ├── requirements.txt        # Python依存関係
│   └── CHATGPT_README.md       # 詳細ドキュメント
├── venv/                       # 共有Python仮想環境
└── README.md                   # このファイル
```

## 🚀 プロジェクト概要

### 1. NotionLinker
Notionデータベースの管理と最適化を行うツール群です。

**主な機能：**
- 日記ページの自動リンク作成
- 重複ページの検出・統合
- ページタイトルの一括更新
- 不足ページの自動作成

**詳細：** `NotionLinker/README.txt` を参照

### 2. ChatGPTToNotion
ChatGPTのチャット履歴をNotionデータベースに自動保存するシステムです。

**主な機能：**
- チャット履歴の自動保存
- 追加メッセージの自動検出・追加
- タイムスタンプ付きの正確な記録
- macOS自動同期

**詳細：** `ChatGPTToNotion/CHATGPT_README.md` を参照

## 🔧 セットアップ

### 共通環境の準備
```bash
# Python仮想環境の作成
python3 -m venv venv
source venv/bin/activate

# 共通依存関係のインストール
pip install requests python-dotenv
```

### 各プロジェクトのセットアップ

#### NotionLinker
```bash
cd NotionLinker
pip install -r requirements.txt
```

#### ChatGPTToNotion
```bash
cd ChatGPTToNotion
pip install -r requirements.txt
```

## 📋 使用方法

### NotionLinkerの実行
```bash
cd NotionLinker
./run_linker.sh
```

### ChatGPTToNotionの実行
```bash
cd ChatGPTToNotion
python chatgpt_to_notion.py chatgpt_export.json
```

## 🔑 環境変数

各プロジェクトで必要な環境変数を設定してください：

### NotionLinker
```env
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_database_id
```

### ChatGPTToNotion
```env
NOTION_TOKEN=your_notion_integration_token
CHATGPT_DB_ID=your_notion_database_id
NOTION_TIMEOUT=60
```

## 📚 ドキュメント

- **NotionLinker詳細**: `NotionLinker/README.txt`
- **ChatGPTToNotion詳細**: `ChatGPTToNotion/CHATGPT_README.md`
- **WARP設定**: `WARP.md`

## 🤝 サポート

各プロジェクトの詳細ドキュメントを参照するか、ログファイルを確認してトラブルシューティングを行ってください。

---

**NotionWorkflowTools Workspace**  
Version: 2.0  
Last Updated: 2025-01-20

