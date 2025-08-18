# Notion Linker 復元版

## 概要（説明）
Notion の「支払管理」データベースと「DailyJournal」データベースを自動で関連付けるツールです。
支払管理DBのページに「支払予定日」があり、かつ「日記[予定日]」が未設定のものを対象に、
DailyJournal 側で同じ「一致用日付」を持つページを検索して関連付けます。該当ページがない場合は
DailyJournal に新規ページ（タイトルのみ）を作成し、その上で関連付けを行います。

- 外部サービス（Make/Zapier）不要、Notion API のみで動作
- .env で DB の各プロパティ名やトークンを指定可能
- DRY_RUN=true のときは実際の書き込みを行わず動作ログのみ表示

## セットアップ
```bash
cd ~/NotionLinker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env .env.backup  # 念のためバックアップ
# .env の NOTION_TOKEN / PAY_DB_ID / JOURNAL_DB_ID を自分の値に設定
# 必要に応じて PROP_*（プロパティ名）を自分の環境に合わせて調整
python link_diary.py  # 初回は DRY_RUN=true でテスト実行
```

## 本番運用
- .env の `DRY_RUN=false` にして再実行すると、Notion に実際に書き込みます。
- 定期実行する場合は、`com.tkht.notion-linker.plist`（launchd）を使って 30 分おき等で自動実行可能です。

## トラブルシュート
- `環境変数が未設定です` と表示される → .env に必要な値（NOTION_TOKEN / PAY_DB_ID / JOURNAL_DB_ID）を設定してください。
- プロパティが見つからないエラー → .env の PROP_* 名称が実際のDBプロパティ名と一致しているか確認してください。
- 実行ログだけ見たい → .env で `DRY_RUN=true` を指定してください。
