# HETEMLサーバ監視システム開発記録

## 概要
HETEMLサーバ内の `https://www.nbs.or.jp/stages/` フォルダに新しいファイルが追加された際に通知を送信する監視システムの開発記録です。

## 開発タイムライン

### 1. プロジェクト開始（初期要求）
**ユーザー要求**: HETEMLサーバ内の特定フォルダに新しいファイルが追加されたら通知が届く仕組みの制作

**技術要件**:
- SSH接続によるHETEMLサーバ監視
- 新規ファイルの自動検出
- 通知機能（LINE通知を希望）
- ワークスペース内に新しいフォルダで開発

### 2. プロジェクト構造の作成
**作成されたフォルダ**: `HETEMLMonitor/`

**初期ファイル構成**:
- `README.md` - プロジェクト概要
- `requirements.txt` - 依存関係
- `config.example.py` - 設定ファイルテンプレート
- `heteml_monitor.py` - メイン監視システム
- `notifications.py` - 通知機能管理
- `check_connection.py` - 接続テストツール
- `setup.py` - セットアップスクリプト
- `.gitignore` - Git管理除外設定

### 3. 技術設計の決定
**監視方法**: SSH + SFTP接続によるファイル監視
**通知方法**: LINE通知（ユーザー希望）

**主要機能**:
- SSH接続によるHETEMLサーバの監視
- 新規ファイルの自動検出
- 通知機能（メール、Slack、LINE等）
- ログ記録
- 設定可能な監視間隔

### 4. 依存関係のインストール
**問題**: システム全体のPython環境でインストールエラー
**解決**: 仮想環境（venv）を作成して依存関係をインストール

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**修正された依存関係**:
- paramiko==3.4.0 (SSH接続)
- schedule==1.2.0 (定期実行)
- requests==2.31.0 (HTTP通信)
- python-dotenv==1.0.0 (環境変数)
- cryptography==41.0.7 (暗号化)

### 5. 通知方法の変更
**問題**: LINE Notifyのサービス終了
**対応**: メール通知に変更

**代替手段の検討**:
1. LINE Messaging API（推奨）
2. Discord Webhook
3. メール通知（最終選択）
4. Telegram Bot
5. Slack Webhook

**最終決定**: メール通知（Gmailアプリパスワード使用）

### 6. 設定ファイルの作成
**作成された設定ファイル**:
- `config.py` - メイン設定
- `.env` - 環境変数（機密情報）

**設定内容**:
```python
HETEML_CONFIG = {
    'hostname': 'ssh-nbsorjp.heteml.net',
    'port': 2222,
    'username': 'nbsorjp',
    'password': os.getenv('HETEML_PASSWORD'),
}

MONITOR_CONFIG = {
    'target_path': '/path/to/www.nbs.or.jp/stages/',
    'check_interval': 300,
}
```

### 7. HETEMLサーバ接続情報の設定
**ユーザーが設定した情報**:
- ホスト名: `ssh-nbsorjp.heteml.net`
- ポート: `2222`
- ユーザー名: `nbsorjp`
- パスワード: 環境変数で設定

### 8. 監視対象フォルダパスの特定
**問題**: 設定したパスが存在しない
**解決**: サーバ構造の探索

**作成されたスクリプト**:
- `check_folder_structure.py` - フォルダ構造確認
- `explore_server.py` - サーバ構造探索

**発見された正しいパス**:
```
/home/users/0/nbsorjp/web/domain/nbspress.com/nbs.or.jp/stages/
```

### 9. Gmailアプリパスワードの設定
**設定手順**:
1. Googleアカウントで2段階認証を有効化
2. アプリパスワードを生成
3. `.env` ファイルに設定

**設定内容**:
```bash
EMAIL_USERNAME=takuhitofujita@gmail.com
EMAIL_PASSWORD=hfouuedygdvffyru
FROM_EMAIL=takuhitofujita@gmail.com
TO_EMAIL=takuhitofujita+rita@gmail.com
```

### 10. 接続テストの実行
**テスト結果**:
- ✅ SSH接続: 成功
- ✅ SFTP接続: 成功
- ✅ 監視対象フォルダ: 存在確認（261ファイル）
- ✅ メール通知: 成功

### 11. 監視システムの起動
**実行方法**:
```bash
python heteml_monitor.py
```

**動作確認**: 正常に動作開始

### 12. 自動起動の設定
**作成されたファイル**:
- `com.user.heteml-monitor.plist` - launchd設定
- `monitor_control.sh` - 制御スクリプト

**自動起動設定**:
```bash
./monitor_control.sh auto
```

### 13. システム稼働開始
**最終状態**:
- ✅ 監視システム: 実行中
- ✅ HETEMLサーバ接続: 成功
- ✅ 自動起動: 設定完了
- ✅ メール通知: 設定完了

## 技術仕様

### 監視機能
- **監視対象**: `/home/users/0/nbsorjp/web/domain/nbspress.com/nbs.or.jp/stages/`
- **監視間隔**: 5分（300秒）
- **検出方法**: ファイル一覧の差分比較
- **ハッシュ計算**: MD5ハッシュによる変更検出

### 通知機能
- **通知方法**: メール通知（Gmail SMTP）
- **通知内容**: 新規ファイル名、サイズ、更新日時
- **通知タイミング**: 新規ファイル検出時

### セキュリティ
- **認証**: SSHパスワード認証
- **暗号化**: TLS対応SMTP
- **環境変数**: 機密情報の分離管理

## 運用コマンド

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

### 自動起動
```bash
# 自動起動設定
./monitor_control.sh auto

# 自動起動停止
launchctl unload ~/Library/LaunchAgents/com.user.heteml-monitor.plist
```

## ファイル構成

```
HETEMLMonitor/
├── heteml_monitor.py          # メイン監視システム
├── notifications.py           # 通知機能管理
├── check_connection.py        # 接続テスト
├── email_test.py             # メール通知テスト
├── check_folder_structure.py  # フォルダ構造確認
├── explore_server.py         # サーバ構造探索
├── monitor_control.sh        # 制御スクリプト
├── setup.py                  # セットアップスクリプト
├── config.py                 # 設定ファイル
├── config.example.py         # 設定ファイルテンプレート
├── requirements.txt          # 依存関係
├── .env                      # 環境変数（機密情報）
├── .gitignore               # Git管理除外設定
├── com.user.heteml-monitor.plist  # 自動起動設定
├── README.md                 # プロジェクト概要
├── email_setup_guide.md      # メール設定ガイド
├── notification_alternatives.md  # 通知方法代替案
├── line_setup_guide.md       # LINE設定ガイド（参考）
├── line_notify_test.py       # LINE通知テスト（参考）
├── venv/                     # 仮想環境
├── logs/                     # ログディレクトリ
├── backups/                  # バックアップディレクトリ
├── heteml_monitor.log        # メインログファイル
├── monitor.log               # 監視ログファイル
└── file_history.json         # ファイル変更履歴
```

## トラブルシューティング

### よくある問題
1. **SSH接続エラー**: ホスト名、ポート、認証情報の確認
2. **メール通知エラー**: Gmailアプリパスワードの確認
3. **監視対象フォルダエラー**: パスの存在確認
4. **Macスリープ**: スリープ解除後の自動再開

### ログ確認
```bash
tail -f heteml_monitor.log
tail -f monitor.log
```

## 今後の拡張可能性

### 追加機能
- Discord通知
- Slack通知
- LINE Messaging API通知
- ファイル変更通知（新規追加以外）
- Webhook通知
- 複数フォルダ監視

### 改善点
- 監視間隔の動的調整
- 通知頻度の制限
- ファイルフィルタリング機能
- 統計情報の収集
- Web管理画面

## まとめ

HETEMLサーバ監視システムは、SSH接続によるファイル監視とメール通知機能を備えた、安定した監視システムとして完成しました。自動起動機能により、Macの起動後やスリープ解除後に自動で動作し、新規ファイルの追加を検出してメール通知を送信します。

**開発期間**: 1セッション  
**技術スタック**: Python, Paramiko, SMTP, launchd  
**通知方法**: メール通知（Gmail）  
**監視間隔**: 5分  
**自動起動**: 対応済み
