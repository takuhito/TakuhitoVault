# HETEMLMonitor GitHub Actions版

HETEMLサーバのファイル監視をGitHub Actionsで実行するバージョンです。

## 🚀 特徴

- **24時間監視**: ローカルマシンに依存しない継続的な監視
- **自動実行**: スケジュールに従った自動実行
- **通知統合**: LINE、メール、Slack通知に対応
- **ログ保存**: GitHub Actionsでの実行ログ保存
- **手動実行**: 必要に応じて手動で実行可能

## 📋 必要な設定

### GitHub Secrets

リポジトリの設定画面で以下のシークレットを設定してください：

#### 必須
- `HETEML_PASSWORD`: HETEMLサーバのSSHパスワード
- `EMAIL_USERNAME`: メール送信用のユーザー名
- `EMAIL_PASSWORD`: メール送信用のパスワード
- `FROM_EMAIL`: 送信元メールアドレス
- `TO_EMAIL`: 送信先メールアドレス

#### オプション
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE通知用のチャンネルアクセストークン
- `LINE_USER_ID`: LINE通知用のユーザーID

## ⚙️ セットアップ

1. **設定ファイルの確認**
   ```bash
   # config.example.pyの内容を確認
   cat HETEMLMonitor/config.example.py
   ```

2. **ワークフローの確認**
   ```bash
   # GitHub Actionsワークフローファイルの確認
   cat .github/workflows/heteml-monitor.yml
   ```

3. **GitHub Secretsの設定**
   - リポジトリのSettings → Secrets and variables → Actions
   - 上記の必須シークレットを設定

## 🕐 実行スケジュール

デフォルトでは1時間ごとに実行されます：

```yaml
schedule:
  - cron: '0 * * * *'  # 1時間ごと
```

スケジュール変更例：
- `*/30 * * * *` - 30分ごと
- `0 */2 * * *` - 2時間ごと
- `0 */6 * * *` - 6時間ごと

## 📊 監視内容

- **新しいファイルの検出**: 監視対象フォルダに追加されたファイル
- **ファイル変更の検出**: 既存ファイルの内容変更
- **ファイル削除の検出**: 削除されたファイル

## 🔔 通知機能

### メール通知
- Gmail、Outlook等のSMTPサーバーに対応
- 日本語メッセージ対応

### LINE通知
- LINE Notify APIを使用
- リアルタイム通知

### Slack通知
- Slack Webhookを使用
- チャンネル指定可能

## 📝 ログとデバッグ

### ログの確認方法

1. **GitHub Actions画面**
   - Actionsタブ → HETEML Monitor → 実行履歴
   - 各実行の詳細ログを確認

2. **Artifacts**
   - 実行後にダウンロード可能
   - 7日間保存

### デバッグ方法

```bash
# 手動実行でテスト
# GitHub Actions画面の「Run workflow」ボタンを使用

# ローカル環境でのテスト
cd HETEMLMonitor
python heteml_monitor_github_action.py
```

## 🛠️ カスタマイズ

### 監視対象の変更

`config.py`の`MONITOR_CONFIG`を編集：

```python
MONITOR_CONFIG = {
    'target_path': '/path/to/your/folder',  # 監視対象パス
    'file_pattern': '*',                    # ファイルパターン
    'exclude_patterns': ['.*', '*.tmp'],    # 除外パターン
}
```

### 通知メッセージのカスタマイズ

`heteml_monitor_github_action.py`の`send_notifications`メソッドを編集：

```python
def send_notifications(self, new_files, modified_files):
    # カスタムメッセージ形式
    message = f"🔍 監視結果\n"
    if new_files:
        message += f"新規: {len(new_files)}件\n"
    if modified_files:
        message += f"変更: {len(modified_files)}件\n"
    # ...
```

## 🔒 セキュリティ

- **シークレット管理**: パスワードやトークンはGitHub Secretsで管理
- **最小権限**: 必要最小限の権限のみを付与
- **定期的な更新**: 認証情報の定期更新を推奨

## 📚 詳細ドキュメント

- [セットアップガイド](docs/GITHUB_ACTIONS_SETUP.md)
- [トラブルシューティング](docs/GITHUB_ACTIONS_SETUP.md#トラブルシューティング)
- [カスタマイズ方法](docs/GITHUB_ACTIONS_SETUP.md#カスタマイズ)

## 🤝 サポート

問題が発生した場合は、以下の情報を含めて報告してください：

- GitHub Actionsの実行ログ
- 設定内容（機密情報は除く）
- エラーメッセージ
- 期待される動作

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。
