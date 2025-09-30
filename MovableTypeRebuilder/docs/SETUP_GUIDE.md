# MovableType Rebuilder セットアップガイド

## 1. 前提条件

- Python 3.8以上
- MovableTypeサイトへの管理者アクセス権限
- メール通知用のSMTP設定（Gmail推奨）

## 2. 初期セットアップ

### 2.1 依存関係のインストール

```bash
cd MovableTypeRebuilder
pip install -r requirements.txt
```

### 2.2 環境変数の設定

```bash
cp env.example .env
```

`.env`ファイルを編集して以下の設定を行います：

```env
# MovableType設定
MT_SITE_URL=https://your-movabletype-site.com
MT_USERNAME=your_username
MT_PASSWORD=Z9MSNPSknzmr

# メール通知設定
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
TO_EMAIL=recipient@example.com

# 実行設定
REBUILD_INTERVAL_MINUTES=5
MAX_RETRY_COUNT=3
LOG_LEVEL=INFO
```

## 3. 接続テスト

設定が完了したら、接続テストを実行します：

```bash
python test_mt_connection.py
```

このテストで以下が確認されます：
- MovableTypeサイトへの接続
- ログイン認証
- 管理画面アクセス
- 再構築機能の利用可能性

## 4. ローカル実行の設定

### 4.1 launchdスケジューラーの設定

```bash
./setup_local_scheduler.sh
```

このスクリプトは以下を実行します：
- plistファイルのパス更新
- launchdサービスへの登録
- ログディレクトリの作成

### 4.2 手動テスト実行

```bash
# 通常実行
python mt_rebuilder.py

# テスト実行
python mt_rebuilder.py --test

# スケジュール実行（デバッグ用）
python mt_rebuilder.py --schedule
```

## 5. GitHub Actions移行

### 5.1 リポジトリシークレットの設定

GitHubリポジトリの設定で以下のシークレットを設定：

- `MT_SITE_URL`
- `MT_USERNAME`
- `MT_PASSWORD`
- `EMAIL_USERNAME`
- `EMAIL_PASSWORD`
- `FROM_EMAIL`
- `TO_EMAIL`

### 5.2 ワークフローの有効化

`.github/workflows/movabletype-rebuild.yml`が自動的に有効になります。

### 5.3 手動実行

GitHub Actionsのページから「MovableType Monthly Rebuild」ワークフローを手動実行できます。

## 6. ログと監視

### 6.1 ログファイル

- `logs/mt_rebuilder_YYYYMMDD.log`: 実行ログ
- `logs/launchd_stdout.log`: launchd標準出力
- `logs/launchd_stderr.log`: launchd標準エラー

### 6.2 メール通知

実行結果がメールに通知されます：
- ✅ 成功: 再構築が正常に完了
- ❌ 失敗: エラーが発生

## 7. トラブルシューティング

### 7.1 よくある問題

**ログイン失敗**
- 認証情報を確認
- MovableTypeのセッション設定を確認

**再構築失敗**
- MovableTypeの権限設定を確認
- サイトの設定を確認

**通知が送信されない**
- メール設定を確認
- SMTPサーバーの設定を確認
- アプリパスワード（Gmailの場合）を確認

### 7.2 デバッグ方法

```bash
# 詳細ログで実行
LOG_LEVEL=DEBUG python mt_rebuilder.py --test

# 接続テスト
python test_mt_connection.py
```

### 7.3 サービス管理

```bash
# サービス停止
launchctl unload ~/Library/LaunchAgents/com.user.movabletype-rebuilder.plist

# サービス開始
launchctl load ~/Library/LaunchAgents/com.user.movabletype-rebuilder.plist

# サービス状態確認
launchctl list | grep movabletype
```

## 8. カスタマイズ

### 8.1 実行スケジュールの変更

`com.user.movabletype-rebuilder.plist`を編集してスケジュールを変更できます。

### 8.2 通知内容のカスタマイズ

`mt_rebuilder.py`の`send_line_notification`メソッドを編集して通知内容をカスタマイズできます。

### 8.3 エラーハンドリングの追加

`mt_rebuilder.py`にリトライ機能やエラー処理を追加できます。

## 9. セキュリティ

- 認証情報は環境変数で管理
- `.env`ファイルはGitにコミットしない
- ログファイルには機密情報が含まれないよう注意

## 10. サポート

問題が発生した場合は、以下を確認してください：
1. ログファイルの内容
2. 接続テストの結果
3. 環境変数の設定
4. MovableTypeサイトの設定
