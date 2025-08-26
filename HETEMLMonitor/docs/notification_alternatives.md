# LINE通知の代替手段ガイド

## 概要
LINE Notifyのサービス終了に伴い、HETEMLサーバ監視システムで使用できる通知方法の代替手段をご紹介します。

## 1. LINE Messaging API（推奨）

### 特徴
- LINE公式のBot API
- 豊富な機能（テキスト、画像、ボタン等）
- 安定したサービス

### 設定手順
1. [LINE Developers Console](https://developers.line.biz/console/) にアクセス
2. 新しいプロバイダーを作成
3. Messaging APIチャンネルを作成
4. チャンネルアクセストークンを取得
5. Botを友達追加してユーザーIDを取得

### 設定例
```bash
# .env ファイル
LINE_CHANNEL_ACCESS_TOKEN=your-channel-access-token
LINE_USER_ID=your-user-id
```

## 2. Discord Webhook

### 特徴
- 無料で利用可能
- 簡単な設定
- 豊富な通知オプション

### 設定手順
1. Discordサーバーで通知用チャンネルを作成
2. チャンネル設定 → 連携サービス → Webhook
3. Webhook URLをコピー

### 実装例
```python
def send_discord_notification(message: str, webhook_url: str):
    data = {
        'content': message
    }
    requests.post(webhook_url, json=data)
```

## 3. Slack Webhook

### 特徴
- ビジネス用途に適している
- 豊富な統合機能
- 無料プランあり

### 設定手順
1. Slackワークスペースで通知用チャンネルを作成
2. アプリ → Incoming Webhooks
3. Webhook URLを生成

## 4. メール通知

### 特徴
- 最も確実な通知方法
- 設定が簡単
- スマートフォンでも受信可能

### 設定例（Gmail）
```bash
# .env ファイル
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
TO_EMAIL=recipient@example.com
```

## 5. Telegram Bot

### 特徴
- 無料で利用可能
- 簡単な設定
- 豊富な機能

### 設定手順
1. @BotFather にメッセージを送信
2. 新しいBotを作成
3. Bot Tokenを取得
4. Botを友達追加してチャットIDを取得

### 実装例
```python
def send_telegram_notification(message: str, bot_token: str, chat_id: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message
    }
    requests.post(url, json=data)
```

## 6. Pushover

### 特徴
- プッシュ通知に特化
- 一度の購入で永続利用
- 複数デバイス対応

### 設定手順
1. [Pushover](https://pushover.net/) でアカウント作成
2. アプリケーションを作成
3. User KeyとAPI Tokenを取得

## 7. IFTTT（If This Then That）

### 特徴
- 様々なサービスと連携可能
- 簡単な設定
- 無料プランあり

### 設定手順
1. IFTTTアカウントを作成
2. Webhookトリガーを作成
3. アクション（LINE、メール等）を設定

## 推奨順位

1. **LINE Messaging API** - 最も安定したLINE通知
2. **Discord Webhook** - 簡単で確実
3. **メール通知** - 最も確実
4. **Telegram Bot** - 無料で機能豊富
5. **Slack Webhook** - ビジネス用途

## 実装方法

### 新しい通知方法を追加する場合

1. `notifications.py` に新しいメソッドを追加
2. `config.py` に設定を追加
3. テストスクリプトを作成

### 例：Discord通知の追加

```python
def send_discord(self, message: str) -> bool:
    """Discord通知の送信"""
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        return False
    
    try:
        data = {'content': message}
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
        return True
    except Exception as e:
        self.logger.error(f"Discord通知の送信に失敗: {e}")
        return False
```

## 設定ファイルの更新

新しい通知方法を追加する場合は、`config.py` を更新してください：

```python
NOTIFICATION_CONFIG = {
    'enabled': True,
    'methods': ['discord', 'email'],  # 使用する通知方法
    
    'discord': {
        'enabled': True,
        'webhook_url': os.getenv('DISCORD_WEBHOOK_URL'),
    },
    
    'email': {
        'enabled': True,
        # メール設定...
    },
}
```

## まとめ

LINE Notifyの代替として、以下をお勧めします：

1. **LINE Messaging API** - LINEを使い続けたい場合
2. **Discord Webhook** - 簡単で確実な通知
3. **メール通知** - 最も確実な方法

どの方法を選択されるかお知らせください。実装のお手伝いをいたします。
