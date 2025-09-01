# HETEMLMonitor プロジェクト詳細メモ

## 📋 プロジェクト概要

HETEMLサーバのファイル監視システムを構築し、ローカル版とGitHub Actions版の両方を実装しました。

### 🎯 目標
- **24時間監視**: Macのスリープ中も監視継続
- **通知区別**: ローカル版とGitHub版で通知を区別
- **冗長性**: 一方が停止しても他方で監視継続
- **再帰的監視**: stagesフォルダ内の全てのファイル（サブフォルダ、サブサブフォルダを含む）を監視

## 🏗️ システム構成

### ローカル版 (Mac)
- **ファイル**: `heteml_monitor.py`
- **実行頻度**: 5分ごと
- **通知タイトル**: "HETEMLサーバ監視通知"
- **用途**: リアルタイム監視、開発時

### GitHub Actions版
- **ファイル**: `heteml_monitor_github_action.py`
- **実行頻度**: 6時間ごと
- **通知タイトル**: "[GitHub Actions] HETEMLサーバ監視通知"
- **用途**: 24時間監視、本番環境

## 📁 ファイル構成

```
HETEMLMonitor/
├── 📄 heteml_monitor.py                    # ローカル版メインスクリプト
├── 📄 heteml_monitor_github_action.py      # GitHub Actions版メインスクリプト
├── 📄 notifications.py                     # 通知管理モジュール
├── 📄 config.py                           # 設定ファイル（ローカル用）
├── 📄 config.example.py                   # 設定ファイルテンプレート
├── 📄 requirements.txt                    # Python依存関係
├── 📄 README.md                           # プロジェクト概要
├── 📄 README_GITHUB_ACTIONS.md            # GitHub Actions版README
├── 📄 monitor_control.sh                  # ローカル版制御スクリプト
├── 📄 setup.py                           # セットアップスクリプト
├── 📄 com.user.heteml-monitor.plist      # launchd設定（ローカル用）
├── 📄 .gitignore                         # Git除外設定
│
├── 📁 .github/workflows/
│   └── 📄 heteml-monitor.yml             # GitHub Actionsワークフロー
│
├── 📁 docs/
│   ├── 📄 GITHUB_ACTIONS_SETUP.md        # GitHub Actionsセットアップガイド
│   ├── 📄 LOCAL_VS_GITHUB.md             # ローカル版とGitHub版の比較
│   ├── 📄 PROJECT_SUMMARY.md             # このファイル
│   └── 📄 README.md                      # ドキュメント概要
│
├── 📁 scripts/
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
- **再帰的監視**: サブフォルダ、サブサブフォルダまで全てのファイルを監視

### 通知機能
- **メール通知**: SMTP経由（Gmail対応）
- **LINE通知**: LINE Notify API
- **Slack通知**: Slack Webhook
- **通知区別**: ローカル版とGitHub版でメッセージを区別

### 設定管理
- **ローカル版**: `config.py`で直接設定
- **GitHub Actions版**: GitHub Secretsで環境変数管理
- **環境変数**: dotenvライブラリで管理

## 🚀 セットアップ手順

### ローカル版
1. `config.example.py`を`config.py`にコピー
2. 設定を編集（HETEMLサーバ情報、通知設定）
3. `pip install -r requirements.txt`
4. `python heteml_monitor.py`で実行

### GitHub Actions版
1. GitHub Secretsの設定
2. ワークフローファイルの配置
3. 自動実行開始

## 📊 実行結果

### 成功した実行例
- **実行時間**: 1分27秒
- **発見ファイル**: 15個のHTMLファイル
- **通知**: メール送信成功
- **ログ**: 詳細な実行ログ

### 監視対象ファイル
```
/home/users/0/nbsorjp/web/domain/nbspress.com/nbs.or.jp/stages/
├── _archive.html
├── list2011.html
├── stages-index_20170825.html
├── list_20120817.html
├── list2011_20110316.html
├── stages-index_20180304.html
├── 0index.html
├── stages-index__.html
├── index.html
├── list2011_20120817.html
├── stages-index.html
├── list.html
├── stages-index-old.html
├── stages-archives.html
└── archive.html
```

## 🔍 トラブルシューティング

### 発生した問題と解決策

1. **GitHub Actions制限エラー**
   - **問題**: 無料プランの2,000分制限
   - **解決**: GitHub Proにアップグレード（$4/月）

2. **ワークフローファイル配置エラー**
   - **問題**: `.github/workflows/`ディレクトリが認識されない
   - **解決**: リポジトリルートに正しく配置

3. **actions/upload-artifact非推奨エラー**
   - **問題**: v3が非推奨になった
   - **解決**: v4にアップデート

4. **SFTPClient existsメソッドエラー**
   - **問題**: `exists`メソッドが存在しない
   - **解決**: `stat`メソッドで例外処理に変更

5. **ホスト名解決エラー**
   - **問題**: 設定ファイルのホスト名が間違っている
   - **解決**: 正しいHETEMLサーバ情報に修正

## 💰 コスト

### GitHub Pro
- **月額**: $4（約600円）
- **Actions制限**: 3,000分/月
- **現在の使用量**: 約7,440分/月（6時間ごと実行）

### 運用コスト
- **ローカル版**: 無料（電気代のみ）
- **GitHub Actions版**: $4/月
- **総コスト**: $4/月

## 📈 パフォーマンス

### 実行時間
- **ローカル版**: 数秒
- **GitHub Actions版**: 約1分27秒

### 監視頻度
- **ローカル版**: 5分ごと（高頻度）
- **GitHub Actions版**: 6時間ごと（安定性重視）

### 通知速度
- **ローカル版**: 即座
- **GitHub Actions版**: 実行完了後

## 🔒 セキュリティ

### 認証情報管理
- **ローカル版**: `config.py`で管理
- **GitHub Actions版**: GitHub Secretsで管理
- **推奨**: 定期的なパスワード更新

### アクセス制御
- **SSH接続**: パスワード認証
- **ファイルアクセス**: 読み取り専用
- **ログ管理**: 機密情報を除外

## 📝 今後の改善案

### 機能拡張
1. **Webhook通知**: カスタムWebhook対応
2. **データベース連携**: 外部DBでの履歴管理
3. **監視対象拡張**: 複数フォルダ監視
4. **レポート機能**: 定期レポート生成

### パフォーマンス改善
1. **並列処理**: 複数ファイルの同時処理
2. **キャッシュ機能**: 不要な再計算を削減
3. **差分監視**: 変更部分のみの検出

### 運用改善
1. **監視ダッシュボード**: Web UI
2. **アラート設定**: 重要度別通知
3. **バックアップ機能**: 自動バックアップ

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

### 運用成果
- ✅ Macスリープ中の監視継続
- ✅ リアルタイム通知
- ✅ コスト効率の良い運用
- ✅ 冗長性の確保

## 📞 サポート

### 問題発生時の対応
1. **ログ確認**: 実行ログで詳細確認
2. **設定確認**: 環境変数と設定ファイル
3. **接続確認**: SSH接続のテスト
4. **通知確認**: 通知設定のテスト

### 連絡先
- **GitHub Issues**: プロジェクトのIssuesで報告
- **ドキュメント**: `docs/`フォルダ内のガイド参照

---

**作成日**: 2025年8月27日  
**最終更新**: 2025年8月27日  
**バージョン**: 1.0.0
