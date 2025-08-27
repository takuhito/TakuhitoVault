# HETEMLMonitor

HETEMLサーバのファイル監視システム - ローカル版とGitHub Actions版の両方を提供

## 🚀 概要

HETEMLサーバ内の指定フォルダに新しいファイルが追加された際に通知を送信する監視システムです。ローカル版とGitHub Actions版の両方を提供し、24時間365日の継続的な監視を実現します。

## ✨ 特徴

- **24時間監視**: GitHub Actions版でMacのスリープ中も監視継続
- **通知区別**: ローカル版とGitHub版で通知を区別
- **冗長性**: 一方が停止しても他方で監視継続
- **多様な通知**: メール、LINE、Slack通知に対応
- **ファイル変更検出**: 新規、変更、削除されたファイルを検出

## 📊 システム構成

| バージョン | 実行環境 | 実行頻度 | 通知タイトル | 用途 |
|------------|----------|----------|--------------|------|
| **ローカル版** | Mac | 5分ごと | "HETEMLサーバ監視通知" | リアルタイム監視 |
| **GitHub Actions版** | GitHub | 6時間ごと | "[GitHub Actions] HETEMLサーバ監視通知" | 24時間監視 |

## 🛠️ セットアップ

### ローカル版

1. **依存関係のインストール**
   ```bash
   cd HETEMLMonitor
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **設定ファイルの作成**
   ```bash
   cp config.example.py config.py
   # config.pyを編集してHETEMLサーバ情報を設定
   ```

3. **実行**
   ```bash
   python heteml_monitor.py
   ```

### GitHub Actions版

1. **GitHub Secretsの設定**
   - `HETEML_PASSWORD`: HETEMLサーバのSSHパスワード
   - `EMAIL_USERNAME`: メール送信用のユーザー名
   - `EMAIL_PASSWORD`: メール送信用のパスワード
   - `FROM_EMAIL`: 送信元メールアドレス
   - `TO_EMAIL`: 送信先メールアドレス

2. **自動実行開始**
   - ワークフローファイルが配置されると自動で6時間ごとに実行

## 📁 ファイル構成

```
HETEMLMonitor/
├── 📄 heteml_monitor.py                    # ローカル版メインスクリプト
├── 📄 heteml_monitor_github_action.py      # GitHub Actions版メインスクリプト
├── 📄 notifications.py                     # 通知管理モジュール
├── 📄 config.py                           # 設定ファイル（ローカル用）
├── 📄 config.example.py                   # 設定ファイルテンプレート
├── 📄 requirements.txt                    # Python依存関係
├── 📄 README.md                           # このファイル
├── 📄 README_GITHUB_ACTIONS.md            # GitHub Actions版README
├── 📄 monitor_control.sh                  # ローカル版制御スクリプト
├── 📄 setup.py                           # セットアップスクリプト
├── 📄 com.user.heteml-monitor.plist      # launchd設定（ローカル用）
├── 📄 .gitignore                         # Git除外設定
│
├── 📁 .github/workflows/
│   └── 📄 heteml-monitor.yml             # GitHub Actionsワークフロー
│
├── 📁 docs/                              # 詳細ドキュメント
│   ├── 📄 GITHUB_ACTIONS_SETUP.md        # GitHub Actionsセットアップガイド
│   ├── 📄 LOCAL_VS_GITHUB.md             # ローカル版とGitHub版の比較
│   ├── 📄 PROJECT_SUMMARY.md             # プロジェクト詳細メモ
│   └── 📄 README.md                      # ドキュメント概要
│
├── 📁 scripts/                           # テスト・ユーティリティスクリプト
│   ├── 📄 test_github_action.py          # GitHub Actions版テスト
│   ├── 📄 test_simple.py                 # シンプルテスト
│   ├── 📄 test_minimal.py                # 最小限テスト
│   ├── 📄 test_basic.py                  # 基本テスト
│   ├── 📄 test_hello.py                  # Hello Worldテスト
│   └── 📄 check_connection.py            # 接続確認スクリプト
│
├── 📁 logs/                              # ログファイル（ローカル用）
├── 📁 backups/                           # バックアップファイル
└── 📁 venv/                              # Python仮想環境
```

## 🔧 技術仕様

### 監視機能
- **SSH/SFTP接続**: paramikoライブラリ使用
- **ファイル検出**: 新しいファイル、変更されたファイル、削除されたファイル
- **ハッシュ比較**: MD5ハッシュでファイル変更を検出
- **履歴管理**: JSONファイルでファイル履歴を保存

### 通知機能
- **メール通知**: SMTP経由（Gmail対応）
- **LINE通知**: LINE Notify API
- **Slack通知**: Slack Webhook
- **通知区別**: ローカル版とGitHub版でメッセージを区別

## 📊 実行結果例

### 成功した実行例
- **実行時間**: 1分27秒（GitHub Actions版）
- **発見ファイル**: 15個のHTMLファイル
- **通知**: メール送信成功
- **ログ**: 詳細な実行ログ

### 監視対象ファイル例
```
/home/users/0/nbsorjp/web/domain/nbspress.com/nbs.or.jp/stages/
├── _archive.html
├── list2011.html
├── stages-index_20170825.html
├── index.html
├── list.html
└── ... (その他HTMLファイル)
```

## 💰 コスト

- **ローカル版**: 無料（電気代のみ）
- **GitHub Actions版**: $4/月（GitHub Pro）
- **総コスト**: $4/月

## 🔍 トラブルシューティング

### よくある問題

1. **SSH接続エラー**
   - ホスト名とポートを確認
   - ユーザー名とパスワードを確認

2. **メール通知が送信されない**
   - メール設定が正しく設定されているか確認
   - アプリパスワードが正しいか確認

3. **GitHub Actions制限エラー**
   - GitHub Proにアップグレード（$4/月）

### ログの確認

**ローカル版**:
```bash
tail -f HETEMLMonitor/heteml_monitor.log
```

**GitHub Actions版**:
- GitHub Actions画面の実行ログを確認

## 📚 詳細ドキュメント

詳細な情報は `docs/` フォルダ内のドキュメントを参照してください：

- **[セットアップガイド](docs/GITHUB_ACTIONS_SETUP.md)** - GitHub Actions版の詳細セットアップ
- **[比較ドキュメント](docs/LOCAL_VS_GITHUB.md)** - ローカル版とGitHub版の比較
- **[プロジェクト詳細](docs/PROJECT_SUMMARY.md)** - 技術仕様とトラブルシューティング

## 🎯 プロジェクト成果

### 達成した目標
- ✅ 24時間365日の監視システム構築
- ✅ ローカル版とGitHub版の併用
- ✅ 通知の区別機能
- ✅ 安定した運用開始

### 技術的成果
- ✅ SSH/SFTP接続の自動化
- ✅ GitHub Actionsの活用
- ✅ エラーハンドリングの実装
- ✅ 段階的なデバッグ手法

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. **ログ確認**: 実行ログで詳細確認
2. **設定確認**: 環境変数と設定ファイル
3. **接続確認**: SSH接続のテスト
4. **通知確認**: 通知設定のテスト

詳細なトラブルシューティングは `docs/PROJECT_SUMMARY.md` を参照してください。

---

**作成日**: 2025年8月27日  
**最終更新**: 2025年8月27日  
**バージョン**: 1.0.0
