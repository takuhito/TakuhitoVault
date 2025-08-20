# GitHub Actions での NotionWorkflowTools 実行

## 概要
GitHub Actionsを使用してNotionWorkflowToolsをクラウド上で定期実行する方法です。

## 設定手順

### 1. GitHub Secrets の設定

GitHubリポジトリの **Settings > Secrets and variables > Actions** で以下のシークレットを設定してください：

#### 必須設定
```
NOTION_TOKEN=REDACTED_NOTION
JOURNAL_DB_ID=1f8b061dadf3817b97a7c973adae7fd3
PAY_DB_ID=1f6b061dadf38008852bfdf0b2679cc2
```

#### 新しいデータベース設定
```
MYLINK_DB_ID=1f3b061dadf381c6a903fc15741f7d06
YOUTUBE_DB_ID=205b061dadf3803e83d1f67d8d81a215
AICHAT_DB_ID=1fdb061dadf380f8846df9d89aa6e988
ACTION_DB_ID=1feb061dadf380d19988d10d8bf0e56d
```

#### プロパティ名設定
```
PROP_PAY_DATE=支払予定日
PROP_REL_TO_JOURNAL=日記[予定日]
PROP_MYLINK_REL=完了させた日
PROP_YOUTUBE_REL=日記
PROP_AICHAT_REL=取得日
PROP_ACTION_REL=行動日
PROP_MATCH_STR=一致用日付
PROP_JOURNAL_TITLE=タイトル
```

#### 動作設定
```
DRY_RUN=false
NOTION_TIMEOUT=60
RECHECK_DAYS=90
SLEEP_BETWEEN=0.2
```

### 2. ワークフローの動作

#### 実行タイミング
- **定期実行**: 毎時00分と30分（UTC時間）
  - 日本時間では毎時09分と39分
- **手動実行**: GitHubのActionsタブから手動実行可能
- **コード変更時**: 関連ファイルが変更された時に自動実行

#### 実行環境
- **OS**: Ubuntu Latest
- **Python**: 3.11
- **実行場所**: GitHubのクラウド環境

### 3. 実行状況の確認

#### GitHub Actions ページ
1. リポジトリの **Actions** タブにアクセス
2. **Notion Linker** ワークフローを選択
3. 実行履歴とログを確認

#### ログの確認
- 各実行の詳細ログを確認可能
- 実行結果はアーティファクトとして保存（7日間）

### 4. メリット

#### ✅ 利点
- **無料**: GitHubの無料枠で利用可能
- **クラウド実行**: ローカル環境に依存しない
- **定期実行**: 自動的に30分ごとに実行
- **ログ管理**: 実行履歴とログの保存
- **手動実行**: 必要に応じて手動実行可能
- **iPhone対応**: ブラウザから実行状況確認可能

#### ⚠️ 制限事項
- **実行時間**: 月2000分の制限（無料枠）
- **同時実行**: 1つのワークフローは同時に1つまで
- **環境変数**: シークレットとして管理が必要

### 5. トラブルシュート

#### よくある問題
1. **シークレット未設定**: 必要な環境変数が設定されていない
2. **実行失敗**: Notion APIのエラーやネットワーク問題
3. **タイムアウト**: 大量データ処理時の時間制限

#### 対処法
- GitHub Actionsのログを確認
- シークレットの設定を再確認
- 手動実行でテスト

### 6. ローカル環境との併用

GitHub Actionsとローカルのlaunchdを併用することで：
- **冗長性**: どちらかが失敗しても他方が動作
- **柔軟性**: 必要に応じて実行方法を選択
- **監視**: 複数の実行環境で動作確認

## 設定完了後

設定が完了すると、GitHub Actionsが自動的に開始されます。初回実行は手動で行うことをお勧めします。
