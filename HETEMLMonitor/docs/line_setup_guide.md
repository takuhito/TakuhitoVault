# LINE通知設定ガイド

## 概要
HETEMLサーバ監視システムでLINE通知を使用するための設定手順です。

## 1. LINE Developers アカウントの作成

1. [LINE Developers Console](https://developers.line.biz/console/) にアクセス
2. LINEアカウントでログイン
3. 新しいプロバイダーを作成（初回の場合）

## 2. LINE Bot チャンネルの作成

1. LINE Developers Consoleで「チャンネル」→「新規作成」
2. 「Messaging API」を選択
3. 以下の情報を入力：
   - チャンネル名：`HETEML監視システム`
   - チャンネル説明：`HETEMLサーバのファイル変更通知`
   - カテゴリ：`Business`
   - サブカテゴリ：`Other`

## 3. チャンネルアクセストークンの取得

1. 作成したチャンネルの詳細ページに移動
2. 「Messaging API設定」タブをクリック
3. 「チャンネルアクセストークン（長期）」をコピー
4. このトークンを `.env` ファイルの `LINE_CHANNEL_ACCESS_TOKEN` に設定

## 4. ユーザーIDの取得

### 方法1: LINE Bot を友達追加してIDを取得

1. チャンネル詳細ページの「QRコード」をスキャン
2. LINE Botを友達追加
3. 以下のPythonスクリプトを実行してユーザーIDを取得：

```python
import requests
import json

# LINE Bot の Webhook URL を設定
webhook_url = "https://your-webhook-url.com/line-webhook"

# テストメッセージを送信
def send_test_message():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_CHANNEL_ACCESS_TOKEN'
    }
    
    data = {
        'to': 'YOUR_USER_ID',
        'messages': [
            {
                'type': 'text',
                'text': 'テストメッセージ'
            }
        ]
    }
    
    response = requests.post(
        'https://api.line.me/v2/bot/message/push',
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

# ユーザーIDを取得するには、Webhookで受信したメッセージのイベントを確認
```

### 方法2: LINE Notify を使用（推奨）

LINE Notify を使用すると、より簡単に通知を送信できます：

1. [LINE Notify](https://notify-bot.line.me/ja/) にアクセス
2. 「マイページ」→「トークンを発行する」
3. トークン名：`HETEML監視システム`
4. 通知を送信したいトークルームを選択
5. 発行されたトークンを `.env` ファイルに設定

## 5. 環境変数の設定

`.env` ファイルを以下のように編集：

```bash
# HETEMLサーバ接続情報
HETEML_PASSWORD=your-heteml-password

# LINE通知設定
LINE_CHANNEL_ACCESS_TOKEN=your-line-channel-access-token
LINE_USER_ID=your-line-user-id
```

## 6. テスト実行

設定完了後、以下のコマンドでテスト：

```bash
source venv/bin/activate
python check_connection.py
```

## トラブルシューティング

### よくある問題

1. **チャンネルアクセストークンが無効**
   - トークンが正しくコピーされているか確認
   - チャンネルが有効になっているか確認

2. **ユーザーIDが見つからない**
   - LINE Botを友達追加しているか確認
   - Webhookが正しく設定されているか確認

3. **通知が送信されない**
   - ネットワーク接続を確認
   - LINE APIの制限に達していないか確認

### ログの確認

```bash
tail -f heteml_monitor.log
```

## セキュリティ注意事項

- チャンネルアクセストークンは機密情報です
- `.env` ファイルはGitにコミットしないでください
- 定期的にトークンを更新することを推奨します
