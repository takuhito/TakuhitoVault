# メール通知設定ガイド

## 概要
HETEMLサーバ監視システムでメール通知を使用するための設定手順です。

## 1. Gmailを使用する場合（推奨）

### Gmailアプリパスワードの設定

1. **2段階認証を有効にする**
   - Googleアカウント設定 → セキュリティ
   - 「2段階認証プロセス」を有効化

2. **アプリパスワードを生成**
   - Googleアカウント設定 → セキュリティ
   - 「アプリパスワード」を選択
   - 「アプリを選択」→「その他（カスタム名）」
   - 名前を入力（例：「HETEML監視システム」）
   - 生成された16文字のパスワードをコピー

3. **環境変数の設定**
   ```bash
   # .env ファイル
   EMAIL_USERNAME=your-email@gmail.com
   EMAIL_PASSWORD=your-16-character-app-password
   FROM_EMAIL=your-email@gmail.com
   TO_EMAIL=recipient@example.com
   ```

## 2. その他のメールサービス

### Outlook/Hotmail
```bash
# .env ファイル
EMAIL_USERNAME=your-email@outlook.com
EMAIL_PASSWORD=your-password
FROM_EMAIL=your-email@outlook.com
TO_EMAIL=recipient@example.com
```

### Yahoo!メール
```bash
# .env ファイル
EMAIL_USERNAME=your-email@yahoo.co.jp
EMAIL_PASSWORD=your-app-password
FROM_EMAIL=your-email@yahoo.co.jp
TO_EMAIL=recipient@example.com
```

### 独自ドメインのメールサーバー
```bash
# .env ファイル
EMAIL_USERNAME=your-email@yourdomain.com
EMAIL_PASSWORD=your-password
FROM_EMAIL=your-email@yourdomain.com
TO_EMAIL=recipient@example.com
```

## 3. 設定ファイルの更新

`config.py` でSMTPサーバー設定を変更：

```python
# Gmail
'email': {
    'enabled': True,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'use_tls': True,
},

# Outlook
'email': {
    'enabled': True,
    'smtp_server': 'smtp-mail.outlook.com',
    'smtp_port': 587,
    'use_tls': True,
},

# Yahoo!
'email': {
    'enabled': True,
    'smtp_server': 'smtp.mail.yahoo.co.jp',
    'smtp_port': 587,
    'use_tls': True,
},
```

## 4. テスト実行

設定完了後、以下のコマンドでテスト：

```bash
source venv/bin/activate
python check_connection.py
```

## 5. メール通知のテスト

```bash
source venv/bin/activate
python email_test.py
```

## トラブルシューティング

### よくある問題

1. **認証エラー**
   - ユーザー名とパスワードが正しいか確認
   - Gmailの場合はアプリパスワードを使用
   - 2段階認証が有効になっているか確認

2. **SMTP接続エラー**
   - SMTPサーバー名とポートが正しいか確認
   - ファイアウォールでSMTPポートがブロックされていないか確認

3. **送信エラー**
   - FROM_EMAILとTO_EMAILが正しく設定されているか確認
   - メールアドレスの形式が正しいか確認

### エラーメッセージと対処法

- **535 Authentication failed**: パスワードが間違っている
- **550 Relaying not allowed**: SMTPサーバーの設定を確認
- **Connection refused**: ポート番号またはサーバー名を確認

## セキュリティ注意事項

- アプリパスワードは機密情報です
- `.env` ファイルはGitにコミットしないでください
- 定期的にパスワードを更新することを推奨します
- 送信先メールアドレスは信頼できるもののみに設定

## メール通知のカスタマイズ

### 件名の変更
`notifications.py` の `send_email` メソッドで件名を変更できます：

```python
def send_email(self, message: str, subject: Optional[str] = None) -> bool:
    # subject パラメータで件名を指定
    msg['Subject'] = subject or "HETEMLサーバ監視通知"
```

### メール本文のフォーマット
HTMLメールを使用する場合は、`MIMEText` の第2引数を `'html'` に変更：

```python
msg.attach(MIMEText(message, 'html', 'utf-8'))
```

## 複数宛先への送信

複数のメールアドレスに送信する場合：

```bash
# .env ファイル
TO_EMAIL=recipient1@example.com,recipient2@example.com
```

または、コードで複数宛先を設定：

```python
to_emails = ['recipient1@example.com', 'recipient2@example.com']
msg['To'] = ', '.join(to_emails)
```

## まとめ

メール通知は最も確実で設定も簡単な通知方法です。Gmailのアプリパスワードを使用することで、安全かつ確実に通知を受信できます。
