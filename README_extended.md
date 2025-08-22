# Notion Linker 拡張版

## 概要
Notion の複数のデータベースと「DailyJournal」データベースを自動で関連付けるツールです。
以下の5つのデータベースをサポートしています：

1. **支払管理** - 支払予定日とDailyJournalを関連付け
2. **マイリンク** - 完了させた日とDailyJournalを関連付け
3. **YouTube要約** - 日記プロパティとDailyJournalを関連付け
4. **AI Chat管理** - 取得日とDailyJournalを関連付け
5. **行動** - 行動日とDailyJournalを関連付け

各データベースのページに「一致用日付」があり、かつリレーションプロパティが未設定のものを対象に、
DailyJournal 側で同じ「一致用日付」を持つページを検索して関連付けます。該当ページがない場合は
DailyJournal に新規ページ（タイトルのみ）を作成し、その上で関連付けを行います。

## 現在の状況

**✅ 本番運用中**
- launchdサービスで15分間隔で自動実行
- 本番モード（DRY_RUN=false）で動作
- Notionページの実際の更新が実行中

## プロジェクト構造
```
NotionLinker/
├── link_diary.py              # メインスクリプト
├── run_linker.sh              # 手動実行スクリプト
├── run_linker_launchd.sh      # launchd用実行スクリプト
├── requirements.txt           # Python依存関係
├── .env                       # 環境設定（本番用）
├── README_extended.md         # このファイル
├── backups/                   # バックアップファイル
│   └── README.md
├── config/                    # 設定ファイル
│   └── com.tkht.notion-linker.plist
├── docs/                      # ドキュメント
│   ├── title_update_guide.md
│   └── README.md
└── scripts/                   # 開発・メンテナンス用スクリプト
    ├── check_existing_relations.py
    ├── create_missing_journal_pages.py
    ├── merge_duplicate_pages.py
    ├── remove_duplicate_pages.py
    ├── notion_title_updater.py
    └── README.md
```

## セットアップ

### 1. 環境設定ファイルの作成
```bash
cd ~/NotionWorkflowTools/NotionLinker
```

### 2. .env ファイルの設定
以下の内容で `.env` ファイルを作成してください：

```env
# === 基本設定 ===
NOTION_TOKEN=your_notion_integration_token_here
JOURNAL_DB_ID=your_journal_database_id_here
DRY_RUN=false  # 本番モード
```

**実際の設定例:**
```env
NOTION_TOKEN=REDACTED_NOTION
JOURNAL_DB_ID=1f8b061dadf3817b97a7c973adae7fd3
DRY_RUN=false
```

### 3. 依存関係のインストール
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. 初回テスト実行
```bash
./run_linker.sh  # 手動実行でテスト
```

## 本番運用

### launchdサービスでの自動実行

**サービス状態確認:**
```bash
launchctl list | grep notion-linker
```

**ログ確認:**
```bash
# 標準出力ログ
tail -f ~/Library/Logs/notion-linker.out.log

# エラーログ
tail -f ~/Library/Logs/notion-linker.err.log
```

**サービス再起動:**
```bash
launchctl unload ~/Library/LaunchAgents/com.tkht.notion-linker.plist
launchctl load ~/Library/LaunchAgents/com.tkht.notion-linker.plist
```

### 実行タイミング
- **自動実行**: 15分間隔（00分、15分、30分、45分）
- **手動実行**: `./run_linker.sh`

## データベース設定詳細

### 支払管理データベース
- **DB-ID**: 環境変数で設定
- **日付プロパティ**: `支払予定日`
- **リレーションプロパティ**: `日記[予定日]`

### マイリンクデータベース
- **DB-ID**: `1f3b061dadf381c6a903fc15741f7d06`
- **日付プロパティ**: `完了させた日`
- **リレーションプロパティ**: `完了させた日`

### YouTube要約データベース
- **DB-ID**: `205b061dadf3803e83d1f67d8d81a215`
- **日付プロパティ**: `日記`
- **リレーションプロパティ**: `日記`

### AI Chat管理データベース
- **DB-ID**: `1fdb061dadf380f8846df9d89aa6e988`
- **日付プロパティ**: `取得日`
- **リレーションプロパティ**: `取得日`

### 行動データベース
- **DB-ID**: `1feb061dadf380d19988d10d8bf0e56d`
- **日付プロパティ**: `行動日`
- **リレーションプロパティ**: `行動日`

## 動作仕様

### 処理対象
- 各データベースで指定された日付プロパティに値が入っているページ
- リレーションプロパティが未設定または日付が変更されたページ
- 過去90日以内のページ（`RECHECK_DAYS`で調整可能）

### 処理フロー
1. 各データベースのページを順次処理
2. 「一致用日付」プロパティの値を取得
3. DailyJournalで同じ日付のページを検索
4. 該当ページがない場合は新規作成
5. リレーションプロパティを設定

### 日付形式対応
- 「2025-08-18」形式の「一致用日付」に対応
- DailyJournalのタイトル形式「2025-0818」との相互変換対応

## トラブルシュート

### よくあるエラー
- `環境変数が未設定です` → `.env` に必要な値（`NOTION_TOKEN` / `JOURNAL_DB_ID`）を設定
- `プロパティが見つかりません` → データベースのプロパティ名が正しいか確認
- `有効なデータベースがありません` → 各データベースのDB-IDが正しく設定されているか確認
- `launchdサービスが動作しない` → サービスを再起動し、ログを確認

### ログ確認
- 実行ログ: `tail -f ~/Library/Logs/notion-linker.out.log`
- エラーログ: `tail -f ~/Library/Logs/notion-linker.err.log`
- テスト実行: `DRY_RUN=true` で手動実行

## 既存版との違い
- 元の `link_diary.py` は支払管理のみ対応
- 新しい `link_diary.py` は5つのデータベースに対応
- 設定は `.env` ファイルで一元管理
- 各データベースの処理状況を個別に表示
- launchdサービスでの自動実行に対応

## 開発・メンテナンス
- `scripts/` フォルダに開発・メンテナンス用スクリプトがあります
- `docs/` フォルダに詳細なガイドがあります
- `backups/` フォルダに過去のバージョンが保存されています

## 更新履歴

- **v2.0.0**: launchdサービスでの自動実行開始、本番モード移行
- **v1.0.0**: 初回リリース、5つのデータベース対応
