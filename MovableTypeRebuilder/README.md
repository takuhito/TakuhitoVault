# MovableType Rebuilder

MovableTypeウェブサイトの月次再構築を自動化するツールです。

## 機能

- 毎月1日の0:01にMovableTypeサイトの再構築を自動実行
- 再構築の成功/失敗をメール通知
- ローカル実行とGitHub Actions対応

## プロジェクト構造

```
MovableTypeRebuilder/
├── README.md                    # プロジェクト概要
├── requirements.txt             # Python依存関係
├── .env.example                 # 環境変数設定例
├── config.py                    # 設定ファイル
├── scripts/                     # 実行スクリプト
│   ├── mt_rebuilder.py         # メインスクリプト（ローカル版）
│   ├── mt_rebuilder_github_action.py # GitHub Actions版
│   ├── notifications.py        # メール通知モジュール
│   ├── debug_mt_login.py       # ログインデバッグ
│   ├── test_mt_connection.py   # 接続テスト
│   ├── test_email_notification.py # メール通知テスト
│   └── test_rebuild_function.py # 再構築機能テスト
├── docs/                        # ドキュメント
│   ├── SETUP_GUIDE.md          # ローカル版セットアップガイド
│   └── GITHUB_ACTIONS_SETUP.md # GitHub Actions移行ガイド
├── scheduler/                   # スケジューラー設定
│   ├── setup_local_scheduler.sh # ローカルスケジューラー設定
│   └── com.user.movabletype-rebuilder.plist # launchd設定
└── logs/                        # ログディレクトリ
```

## セットアップ

1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

2. 設定ファイルの作成
```bash
cp .env.example .env
# .envファイルを編集して必要な設定を行う
```

3. ローカル実行の設定
```bash
# launchd用のplistファイルを設定
./scheduler/setup_local_scheduler.sh
```

## 使用方法

### ローカル実行
```bash
python scripts/mt_rebuilder.py
```

### 手動実行（テスト用）
```bash
python scripts/mt_rebuilder.py --test
```

## 設定項目

- `MT_SITE_URL`: MovableTypeサイトのURL
- `MT_USERNAME`: MovableType管理者ユーザー名
- `MT_PASSWORD`: MovableType管理者パスワード
- `EMAIL_USERNAME`: メール送信用のユーザー名
- `EMAIL_PASSWORD`: メール送信用のパスワード
- `FROM_EMAIL`: 送信元メールアドレス
- `TO_EMAIL`: 送信先メールアドレス

## ログ

実行ログは以下の場所に保存されます：
- `logs/`: 実行ログファイル
- メール: 実行結果の通知

## GitHub Actions移行

ローカルでの動作確認後、`.github/workflows/`ディレクトリ内のワークフローファイルを使用してGitHub Actionsに移行できます。

詳細なセットアップ手順は `docs/GITHUB_ACTIONS_SETUP.md` を参照してください。
