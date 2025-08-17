# ChatGPT to Notion - チャット履歴自動保存システム

ChatGPTデスクトップアプリのチャット履歴をNotionデータベースに自動保存するシステムです。

## 概要

このシステムは以下の機能を提供します：

- **自動データ取得**: ChatGPTデスクトップアプリからチャット履歴を自動取得
- **Notion同期**: 取得したチャット履歴をNotionデータベースに自動保存
- **重複防止**: 既存のチャットは更新、新しいチャットは新規作成
- **定期実行**: 30分おきに自動同期（launchd使用）
- **ログ機能**: 実行ログの詳細記録

## システム構成

```
ChatGPTToNotion/
├── chatgpt_to_notion.py          # メイン同期スクリプト
├── chatgpt_export_helper.py      # ChatGPTデータ取得ヘルパー
├── chatgpt_processor.py          # 圧縮ファイル処理スクリプト
├── chatgpt_sync.sh               # 自動同期シェルスクリプト
├── setup_chatgpt_sync.py         # セットアップスクリプト
├── com.user.chatgpt-sync.plist   # launchd設定ファイル
├── requirements.txt              # Python依存関係
└── CHATGPT_README.md            # このファイル
```

## セットアップ手順

### 1. 初期セットアップ

```bash
# セットアップスクリプトを実行
python setup_chatgpt_sync.py
```

このスクリプトは以下を自動実行します：
- Pythonバージョンチェック
- 仮想環境作成
- 依存関係インストール
- 環境変数ファイル作成
- サンプルデータ作成
- launchd設定

### 2. Notion API設定

1. [Notion Developers](https://developers.notion.com/) で統合を作成
2. 必要な権限を設定：
   - Read content
   - Update content
   - Insert content
3. 統合トークンを取得

### 3. 環境変数設定

`.env`ファイルを編集：

```env
# Notion API設定
NOTION_TOKEN=your_notion_integration_token_here
CHATGPT_DB_ID=your_chatgpt_database_id_here

# 実行モード（true: テスト実行、false: 本番実行）
DRY_RUN=true

# API設定
NOTION_TIMEOUT=60

# プロパティ名設定（必要に応じて変更）
PROP_TITLE=タイトル
PROP_CHAT_ID=チャットID
PROP_CREATED_AT=作成日時
PROP_UPDATED_AT=更新日時
PROP_CONTENT=内容
PROP_MODEL=モデル
PROP_MESSAGE_COUNT=メッセージ数
```

### 4. Notionデータベース作成

```bash
# 親ページIDを指定してデータベースを作成
python chatgpt_to_notion.py --create-db <親ページID>
```

作成されたデータベースIDを`.env`ファイルの`CHATGPT_DB_ID`に設定してください。

## 使用方法

### 手動実行

#### テスト実行（DRY_RUN=true）

```bash
# サンプルデータでテスト
python chatgpt_to_notion.py sample_chatgpt_export.json

# 実際のエクスポートファイルでテスト
python chatgpt_export_helper.py export
python chatgpt_to_notion.py chatgpt_export_YYYYMMDD_HHMMSS.json
```

#### 本番実行（DRY_RUN=false）

```bash
# .envファイルでDRY_RUN=falseに設定後
python chatgpt_to_notion.py chatgpt_export_YYYYMMDD_HHMMSS.json
```

### 自動同期

#### 開始

```bash
# launchdで自動同期を開始
launchctl start com.user.chatgpt-sync
```

#### 停止

```bash
# 自動同期を停止
launchctl stop com.user.chatgpt-sync
```

#### 状態確認

```bash
# 実行状態を確認
launchctl list | grep chatgpt-sync
```

### ログ確認

```bash
# リアルタイムログ確認
tail -f chatgpt_sync.log

# 最新のログを表示
tail -20 chatgpt_sync.log
```

## データベース構造

Notionデータベースには以下のプロパティが作成されます：

| プロパティ名 | タイプ | 説明 |
|-------------|--------|------|
| タイトル | Title | チャットのタイトル |
| チャットID | Text | チャットの一意識別子 |
| 作成日時 | Date | チャット作成日時 |
| 更新日時 | Date | チャット最終更新日時 |
| 内容 | Text | チャット内容の要約 |
| モデル | Select | 使用したGPTモデル |
| メッセージ数 | Number | チャット内のメッセージ数 |

## ファイル形式

### 入力ファイル形式

ChatGPTエクスポートファイルは以下の形式をサポート：

```json
{
  "export_date": "2024-01-01T10:00:00Z",
  "source": "ChatGPT Desktop App",
  "conversations": [
    {
      "id": "chat-id-1",
      "title": "チャットタイトル",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T11:00:00Z",
      "model": "GPT-4",
      "messages": [
        {
          "role": "user",
          "content": "ユーザーメッセージ",
          "timestamp": "2024-01-01T10:00:00Z"
        },
        {
          "role": "assistant",
          "content": "アシスタントメッセージ",
          "timestamp": "2024-01-01T10:01:00Z"
        }
      ]
    }
  ]
}
```

## トラブルシューティング

### よくある問題

#### 1. ChatGPTデータが取得できない

**原因**: ChatGPTデスクトップアプリのデータが暗号化されている
**解決策**: 
- ChatGPTデスクトップアプリから手動でエクスポート
- エクスポートしたJSONファイルを使用

#### 2. Notion APIエラー

**原因**: 権限不足またはトークン無効
**解決策**:
- Notion統合の権限を確認
- トークンを再生成
- データベースに統合を追加

#### 3. 重複実行エラー

**原因**: 前回の実行が完了していない
**解決策**:
```bash
# ロックファイルを削除
rm chatgpt_sync.lock
```

#### 4. launchdが動作しない

**原因**: 設定ファイルのパスが間違っている
**解決策**:
```bash
# launchdを再登録
launchctl unload ~/Library/LaunchAgents/com.user.chatgpt-sync.plist
launchctl load ~/Library/LaunchAgents/com.user.chatgpt-sync.plist
```

### ログの確認

```bash
# システムログを確認
log show --predicate 'process == "chatgpt_sync"' --last 1h

# アプリケーションログを確認
tail -f chatgpt_sync.log
```

## カスタマイズ

### 同期間隔の変更

`com.user.chatgpt-sync.plist`の`StartInterval`を変更：

```xml
<key>StartInterval</key>
<integer>3600</integer>  <!-- 1時間おき -->
```

### プロパティ名の変更

`.env`ファイルの`PROP_*`設定を変更：

```env
PROP_TITLE=チャット名
PROP_CONTENT=チャット内容
```

### データベース構造の変更

`chatgpt_to_notion.py`の`create_chatgpt_database`関数を編集。

## セキュリティ

- Notionトークンは`.env`ファイルに保存
- `.env`ファイルはGitにコミットしない
- ログファイルには機密情報が含まれる可能性があるため注意

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## サポート

問題が発生した場合は、以下を確認してください：

1. ログファイル（`chatgpt_sync.log`）
2. 環境変数設定（`.env`）
3. Notion API権限
4. ChatGPTデスクトップアプリの状態

## 更新履歴

- v1.0.0: 初期リリース
  - ChatGPTデータ取得機能
  - Notion同期機能
  - 自動実行機能
  - ログ機能
