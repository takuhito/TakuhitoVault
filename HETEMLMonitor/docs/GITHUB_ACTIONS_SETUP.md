# HETEMLMonitor GitHub Actions版 セットアップガイド

このガイドでは、HETEMLMonitorをGitHub Actionsで実行するための設定方法を説明します。

## 概要

GitHub Actions版では、ローカルマシンではなくGitHubのサーバー上でHETEMLサーバの監視を実行します。これにより、24時間365日の継続的な監視が可能になります。

## メリット

- **24時間監視**: ローカルマシンの電源に依存しない
- **自動実行**: スケジュールに従って自動実行
- **ログ保存**: 実行ログがGitHubに保存される
- **通知統合**: LINE、メール、Slack通知に対応

## セットアップ手順

### 1. GitHub Secretsの設定

リポジトリの設定画面で以下のシークレットを設定してください：

#### 必須設定
- `HETEML_PASSWORD`: HETEMLサーバのSSHパスワード
- `EMAIL_USERNAME`: メール送信用のユーザー名（Gmail等）
- `EMAIL_PASSWORD`: メール送信用のパスワード
- `FROM_EMAIL`: 送信元メールアドレス
- `TO_EMAIL`: 送信先メールアドレス

#### オプション設定
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE通知用のチャンネルアクセストークン
- `LINE_USER_ID`: LINE通知用のユーザーID

### 2. 設定ファイルの確認

`HETEMLMonitor/config.example.py`の内容を確認し、必要に応じて編集してください：

```python
# HETEMLサーバ接続設定
HETEML_CONFIG = {
    'hostname': 'ssh-nbsorjp.heteml.net',  # あなたのHETEMLサーバのホスト名
    'port': 2222,                           # SSHポート
    'username': 'nbsorjp',                  # SSHユーザー名
    'password': os.getenv('HETEML_PASSWORD'),
    'timeout': 30,
}

# 監視設定
MONITOR_CONFIG = {
    'target_path': '/home/users/0/nbsorjp/web/domain/nbspress.com/nbs.or.jp/stages/',
    'check_interval': 300,                  # GitHub Actionsでは無視されます
    'file_pattern': '*',
    'exclude_patterns': ['.*', '*.tmp'],
}
```

### 3. ワークフローの有効化

`.github/workflows/heteml-monitor.yml`ファイルが正しく配置されていることを確認してください。

## 実行スケジュール

デフォルトでは1時間ごとに実行されます。スケジュールを変更する場合は、`.github/workflows/heteml-monitor.yml`の`cron`設定を編集してください：

```yaml
schedule:
  # 1時間ごと（デフォルト）
  - cron: '0 * * * *'
  
  # 30分ごと
  - cron: '*/30 * * * *'
  
  # 2時間ごと
  - cron: '0 */2 * * *'
  
  # 6時間ごと
  - cron: '0 */6 * * *'
```

## 手動実行

GitHub Actionsの画面から「Run workflow」ボタンをクリックすることで、手動で監視を実行できます。

## ログの確認

実行ログは以下の場所で確認できます：

1. **GitHub Actions画面**: 各実行の詳細ログ
2. **Artifacts**: 実行後にダウンロード可能なログファイル

## トラブルシューティング

### よくある問題

#### 1. SSH接続エラー
- HETEMLサーバのホスト名、ポート、ユーザー名が正しいか確認
- パスワードが正しく設定されているか確認

#### 2. 通知が送信されない
- メール設定（SMTPサーバー、ポート、認証情報）を確認
- LINE通知の場合は、チャンネルアクセストークンとユーザーIDを確認

#### 3. ファイル履歴が保存されない
- GitHub Actions環境では、実行ごとに新しい環境が作成されるため、履歴は一時的なものです
- 永続的な履歴が必要な場合は、外部ストレージ（GitHubリポジトリ内のファイル等）を使用してください

### デバッグ方法

1. **ログの確認**: GitHub Actionsの実行ログで詳細なエラー情報を確認
2. **手動実行**: 手動でワークフローを実行して問題を特定
3. **設定テスト**: ローカル環境で設定をテストしてからGitHub Actionsに移行

## セキュリティ考慮事項

- **シークレット管理**: パスワードやトークンは必ずGitHub Secretsで管理
- **最小権限**: 必要最小限の権限のみを付与
- **定期的な更新**: パスワードやトークンは定期的に更新

## カスタマイズ

### 通知メッセージのカスタマイズ

`heteml_monitor_github_action.py`の`send_notifications`メソッドを編集することで、通知メッセージの形式を変更できます。

### 監視対象の拡張

複数のフォルダを監視したい場合は、`MONITOR_CONFIG`に複数のパスを設定し、ループ処理を追加してください。

## サポート

問題が発生した場合は、以下の情報を含めて報告してください：

- GitHub Actionsの実行ログ
- 設定ファイルの内容（機密情報は除く）
- 発生しているエラーメッセージ
- 期待される動作
