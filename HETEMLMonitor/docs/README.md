# HETEMLサーバ監視システム

## 概要
HETEMLサーバ内の `https://www.nbs.or.jp/stages/` フォルダに新しいファイルが追加された際にメール通知を送信する監視システムです。

## 機能
- SSH接続によるHETEMLサーバの監視
- 新規ファイルの自動検出
- メール通知機能（Gmail、Outlook等対応）
- ログ記録
- 設定可能な監視間隔

## 必要な環境
- Python 3.8以上
- SSH接続可能なHETEMLサーバ
- メール通知設定（Gmail推奨）

## セットアップ

### 1. 依存関係のインストール
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 設定ファイルの作成
```bash
cp config.example.py config.py
```

### 3. 設定の編集
- `config.py` - HETEMLサーバの接続情報を設定
- `.env` - LINE通知の認証情報を設定

### 4. メール通知の設定
詳細は `email_setup_guide.md` を参照してください。

#### 簡単な設定手順（Gmail推奨）:
1. Googleアカウントで2段階認証を有効化
2. アプリパスワードを生成
3. `.env` ファイルにメール設定を追加

## 使用方法

### 接続テスト
```bash
source venv/bin/activate
python check_connection.py
```

### メール通知テスト
```bash
source venv/bin/activate
python email_test.py
```

### 監視開始
```bash
source venv/bin/activate
python heteml_monitor.py
```

### バックグラウンド実行
```bash
source venv/bin/activate
nohup python heteml_monitor.py > monitor.log 2>&1 &
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

## ログとファイル

### ログファイル
- `heteml_monitor.log` - メインログ
- `logs/` - ログディレクトリ

### データファイル
- `file_history.json` - ファイル変更履歴
- `backups/` - バックアップディレクトリ

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
tail -f heteml_monitor.log
```

## セキュリティ

- パスワードは環境変数で管理
- 設定ファイルはGit管理から除外
- SSH秘密鍵認証に対応

## サポート

問題が発生した場合は、以下を確認してください：
1. ログファイルの内容
2. 設定ファイルの設定
3. ネットワーク接続
4. メール通知の設定
