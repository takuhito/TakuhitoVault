# セットアップガイド

## 🚀 クイックセットアップ

### 1. 自動セットアップ（推奨）

```bash
./run.sh
```

### 2. 手動セットアップ

```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境をアクティベート
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

## 🔑 APIキーの設定

### GitHub Secretsから取得

1. GitHubのリポジトリページにアクセス
2. Settings → Secrets and variables → Actions
3. 以下のSecretsを確認・コピー：
   - `NOTION_TOKEN`
   - `GEMINI_API_KEY`
   - `NOTION_DATABASE_ID`
   - `GOOGLE_DRIVE_MONITOR_FOLDER`

### .envファイルの更新

`.env`ファイルを以下のように更新してください：

```bash
# Notion設定
NOTION_TOKEN=REDACTED_SECRET
NOTION_DATABASE_ID=254b061dadf38042813eeab350aea734

# Gemini設定（オプション）
GEMINI_API_KEY=AIzaSyCxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Drive設定
GOOGLE_DRIVE_MONITOR_FOLDER=1YccjjOWIp4PAQVUY8SVcSvUvkcQ6lo3B
GOOGLE_DRIVE_PROCESSED_BASE=0AJojvkLIwToKUk9PVA
GOOGLE_DRIVE_ERROR_FOLDER=1HJrzj1DDoiTmIkNa8tIN3RKnLKs_8Kaf
GOOGLE_DRIVE_SHARED_DRIVE_ID=0AJojvkLIwToKUk9PVA
```

## 🧪 テスト実行

### 1. 簡易テスト（APIキーなしでも実行可能）

```bash
python simple_test.py
```

### 2. デモ実行（APIキーなしでも実行可能）

```bash
python demo.py
```

### 3. 完全テスト（APIキーが必要）

```bash
python test.py
```

## 🚀 実際の実行

APIキーを設定した後、以下のコマンドで実際の処理を実行：

```bash
python main.py
```

## 📋 動作確認

### 正常な動作例

```
🚀 ローカル領収書自動処理システム開始
============================================================
🔧 クライアント初期化中...
✅ Google Drive API認証完了
✅ Notion API クライアント初期化完了
✅ Notion接続成功: 領収書管理データベース
📁 新規ファイル検索中...
📄 処理対象ファイル数: 2
🔄 処理開始: receipt_001.jpg
📥 ダウンロード進捗: 100%
✅ ファイルダウンロード完了: temp/receipt_001.jpg
✅ Notionページ作成完了: abc123def456
✅ ファイル移動完了: receipt_001.jpg
✅ 処理完了: receipt_001.jpg -> Notionページ: abc123def456
============================================================
✅ 処理完了 - 成功: 2, 失敗: 0
```

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. 環境変数が読み込まれない

**症状**: `NOTION_TOKEN: NOT SET`

**解決方法**:
```bash
# .envファイルが存在することを確認
ls -la .env

# 環境変数を手動で設定
export NOTION_TOKEN="your_token_here"
```

#### 2. Google Drive認証エラー

**症状**: `Google Drive API認証エラー`

**解決方法**:
```bash
# 認証ファイルの存在確認
ls -la ../credentials/service-account.json

# ファイルサイズの確認
wc -c ../credentials/service-account.json
```

#### 3. Notion API認証エラー

**症状**: `API token is invalid`

**解決方法**:
- GitHub Secretsから正しいトークンを取得
- `.env`ファイルの値を更新
- Notionのインテグレーション設定を確認

#### 4. モジュールインポートエラー

**症状**: `No module named 'xxx'`

**解決方法**:
```bash
# 仮想環境をアクティベート
source venv/bin/activate

# 依存関係を再インストール
pip install -r requirements.txt
```

## 📞 サポート

問題が解決しない場合は、以下を確認してください：

1. **ログファイル**: `receipt_processor.log`
2. **環境変数**: `echo $NOTION_TOKEN`
3. **認証ファイル**: `ls -la ../credentials/`
4. **Python環境**: `python --version`

## 🎯 次のステップ

1. ✅ システムのセットアップ
2. ✅ APIキーの設定
3. ✅ テストの実行
4. 🎯 実際の処理の実行
5. 🎯 定期的な実行の設定（cron等）
