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

## セットアップ

### 1. 環境設定ファイルの作成
```bash
cd ~/NotionWorkflowTools
cp .env.template .env  # テンプレートがない場合は手動で作成
```

### 2. .env ファイルの設定
以下の内容で `.env` ファイルを作成してください：

```env
# === 基本設定 ===
NOTION_TOKEN=your_notion_integration_token_here
JOURNAL_DB_ID=your_journal_database_id_here

# === データベース設定 ===
PAY_DB_ID=your_payment_database_id_here
MYLINK_DB_ID=1f3b061dadf381c6a903fc15741f7d06
YOUTUBE_DB_ID=205b061dadf3803e83d1f67d8d81a215
AICHAT_DB_ID=1fdb061dadf380f8846df9d89aa6e988
ACTION_DB_ID=1feb061dadf380d19988d10d8bf0e56d

# === プロパティ名設定 ===
PROP_MATCH_STR=一致用日付
PROP_JOURNAL_TITLE=タイトル

# 支払管理プロパティ
PROP_PAY_DATE=支払予定日
PROP_REL_TO_JOURNAL=日記[予定日]

# マイリンクプロパティ
PROP_MYLINK_DATE=完了させた日
PROP_MYLINK_REL=完了させた日

# YouTube要約プロパティ
PROP_YOUTUBE_DATE=日記
PROP_YOUTUBE_REL=日記

# AI Chat管理プロパティ
PROP_AICHAT_DATE=取得日
PROP_AICHAT_REL=取得日

# 行動プロパティ
PROP_ACTION_DATE=行動日
PROP_ACTION_REL=行動日

# === 動作設定 ===
DRY_RUN=true
NOTION_TIMEOUT=60
RECHECK_DAYS=90
SLEEP_BETWEEN=0.2
```

### 3. 依存関係のインストール
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. 初回テスト実行
```bash
python link_diary_extended.py  # DRY_RUN=true でテスト実行
```

## 本番運用
- `.env` の `DRY_RUN=false` にして再実行すると、Notion に実際に書き込みます。
- 定期実行する場合は、`com.tkht.notion-linker.plist`（launchd）を使って自動実行可能です。

## データベース設定詳細

### 支払管理データベース
- **DB-ID**: 既存の設定を使用
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
- `プロパティが見つかりません` → `.env` のプロパティ名が実際のDBプロパティ名と一致しているか確認
- `有効なデータベースがありません` → 各データベースのDB-IDが正しく設定されているか確認

### ログ確認
- 実行ログだけ見たい → `.env` で `DRY_RUN=true` を指定
- 特定のデータベースでエラーが発生 → エラーメッセージを確認し、該当DBの設定を見直し

## 既存版との違い
- 元の `link_diary.py` は支払管理のみ対応
- 新しい `link_diary_extended.py` は5つのデータベースに対応
- 設定は `.env` ファイルで一元管理
- 各データベースの処理状況を個別に表示
