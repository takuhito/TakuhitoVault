# HETEMLサーバ監視システム

## 概要
HETEMLサーバ内の `https://www.nbs.or.jp/stages/` フォルダに新しいファイルが追加された際にメール通知を送信する監視システムです。

## 機能
- SSH接続によるHETEMLサーバの監視
- 新規ファイルの自動検出
- メール通知機能（Gmail、Outlook等対応）
- ログ記録
- 設定可能な監視間隔
- 自動起動機能

## 必要な環境
- Python 3.8以上
- SSH接続可能なHETEMLサーバ
- メール通知設定（Gmail推奨）

## クイックスタート

### 1. 依存関係のインストール
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 設定ファイルの作成
```bash
cp config.example.py config.py
# config.py を編集してHETEMLサーバの接続情報を設定
```

### 3. 環境変数の設定
```bash
# .env ファイルを編集
HETEML_PASSWORD=your-heteml-password
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
TO_EMAIL=recipient@example.com
```

### 4. 接続テスト
```bash
./scripts/check_connection.py
```

### 5. 監視システム開始
```bash
./monitor_control.sh start
```

## 使用方法

### 基本操作
```bash
# 監視システム開始
./monitor_control.sh start

# 監視システム停止
./monitor_control.sh stop

# 監視システム再起動
./monitor_control.sh restart

# 状態確認
./monitor_control.sh status

# ログ確認
./monitor_control.sh logs

# 接続テスト
./monitor_control.sh test
```

### 自動起動設定
```bash
# 自動起動設定
./monitor_control.sh auto
```

## プロジェクト構造

```
HETEMLMonitor/
├── heteml_monitor.py          # メイン監視システム
├── notifications.py           # 通知機能管理
├── config.py                 # 設定ファイル
├── config.example.py         # 設定ファイルテンプレート
├── requirements.txt          # 依存関係
├── monitor_control.sh        # 制御スクリプト
├── com.user.heteml-monitor.plist  # 自動起動設定
├── .env                      # 環境変数（機密情報）
├── .gitignore               # Git管理除外設定
├── scripts/                  # ユーティリティスクリプト
│   ├── check_connection.py   # 接続テスト
│   ├── email_test.py        # メール通知テスト
│   └── ...
├── docs/                     # ドキュメント
│   ├── README.md            # 詳細な使用方法
│   ├── email_setup_guide.md # メール設定ガイド
│   ├── CHAT_SUMMARY.md      # 開発記録
│   └── ...
├── logs/                     # ログファイル
├── backups/                  # バックアップファイル
└── venv/                     # 仮想環境
```

## 設定項目

### HETEMLサーバ接続設定
- ホスト名
- SSHポート（通常は22）
- ユーザー名
- パスワードまたは秘密鍵
- 監視対象フォルダパス

### 監視設定
- 監視間隔（秒）
- ファイルパターン
- 除外パターン

### メール通知設定
- Gmail アプリパスワード（推奨）
- その他のメールサービス設定

## トラブルシューティング

### よくある問題

1. **SSH接続エラー**
   - ホスト名とポートを確認
   - ユーザー名とパスワードを確認
   - ファイアウォール設定を確認

2. **メール通知が送信されない**
   - メール設定が正しく設定されているか確認
   - アプリパスワードが正しいか確認
   - メール通知テストを実行

3. **監視対象フォルダが見つからない**
   - フォルダパスを確認
   - アクセス権限を確認

### ログの確認
```bash
tail -f logs/heteml_monitor.log
```

## セキュリティ

- パスワードは環境変数で管理
- 設定ファイルはGit管理から除外
- SSH秘密鍵認証に対応

## 詳細ドキュメント

詳細な使用方法や設定方法については、`docs/` フォルダ内のドキュメントを参照してください。

- [詳細な使用方法](docs/README.md)
- [メール設定ガイド](docs/email_setup_guide.md)
- [開発記録](docs/CHAT_SUMMARY.md)

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
