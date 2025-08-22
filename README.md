# NotionWorkflowTools

Notionデータベース間のリレーションを自動設定するツール群です。

## 概要

このプロジェクトは以下の機能を提供します：

- **NotionLinker**: 複数のNotionデータベース間で日付に基づくリレーションを自動設定
- **ChatGPTToNotion**: ChatGPTの会話履歴をNotionに自動保存

## 現在の状況

**⚠️ 重要なお知らせ**

- **領収書自動処理システム**: 開発を中止し、関連ファイルを削除しました
- **GitHub Actions**: 無料枠制限により停止し、ローカル実行に移行しました
- **NotionLinker**: ローカルのlaunchdサービスで15分間隔で動作中

## 動作中のシステム

### NotionLinker

複数のNotionデータベース間で日付に基づくリレーションを自動設定します。

**対応データベース:**
- 支払管理
- マイリンク
- YouTube要約
- AI Chat管理
- 行動

**実行方法:**
- **自動実行**: launchdサービスで15分間隔（00分、15分、30分、45分）
- **手動実行**: `NotionLinker/run_linker.sh`

**設定:**
```bash
# NotionLinker/.env
NOTION_TOKEN=your_notion_token
JOURNAL_DB_ID=your_journal_db_id
DRY_RUN=false  # 本番モード
```

## 技術スタック

- **Python 3.13**
- **Notion API**: データベース操作
- **launchd**: macOSの定期実行サービス
- **python-dotenv**: 環境変数管理

## セットアップ

### 1. 必要なAPIの設定

#### Notion API
1. [Notion Developers](https://developers.notion.com/)でインテグレーションを作成
2. インテグレーショントークンを取得
3. 各データベースにインテグレーションを追加

### 2. 環境変数の設定

`NotionLinker/.env`ファイルを作成：

```bash
NOTION_TOKEN=your_notion_integration_token_here
JOURNAL_DB_ID=your_journal_database_id_here
DRY_RUN=false
```

### 3. 依存関係のインストール

```bash
cd NotionLinker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. launchdサービスの設定

```bash
# サービスをロード
launchctl load ~/Library/LaunchAgents/com.tkht.notion-linker.plist

# 状態確認
launchctl list | grep notion-linker
```

## ファイル構造

```
NotionWorkflowTools/
├── NotionLinker/           # メインのNotion連携ツール
│   ├── link_diary.py       # メイン処理
│   ├── run_linker.sh       # 実行スクリプト
│   ├── run_linker_launchd.sh # launchd用スクリプト
│   ├── requirements.txt    # 依存関係
│   └── .env               # 環境変数
├── ChatGPTToNotion/        # ChatGPT連携ツール
├── scripts/               # 各種セットアップスクリプト
├── config/               # 設定ファイル
├── docs/                 # ドキュメント
└── README.md             # このファイル
```

## ログの確認

```bash
# 標準出力ログ
tail -f ~/Library/Logs/notion-linker.out.log

# エラーログ
tail -f ~/Library/Logs/notion-linker.err.log
```

## トラブルシューティング

### よくある問題

1. **launchdサービスが動作しない**
   - サービスを再起動: `launchctl unload && launchctl load`
   - ログを確認: `tail -f ~/Library/Logs/notion-linker.err.log`

2. **環境変数エラー**
   - `.env`ファイルの設定を確認
   - 仮想環境が正しくアクティベートされているか確認

3. **Notion APIエラー**
   - トークンの有効性を確認
   - データベースの権限設定を確認

## 更新履歴

- v2.0.0: 領収書処理システムを削除、NotionLinkerのみに集約
- v1.0.0: 初回リリース

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

