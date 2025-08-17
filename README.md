# ChatGPT to Notion - チャット履歴自動保存システム

ChatGPTのチャット履歴をNotionデータベースに自動保存し、後日追加されたメッセージも自動で追記するシステムです。

## 📁 プロジェクト構成

```
ChatGPTToNotion/
├── .env                          # 環境変数設定
├── requirements.txt              # Python依存関係
├── venv/                        # Python仮想環境
├── chatgpt_to_notion.py         # メインスクリプト
├── chatgpt_export_helper.py     # エクスポートヘルパー
├── chatgpt_sync.sh              # 自動同期スクリプト
├── setup_chatgpt_sync.py        # セットアップスクリプト
├── com.user.chatgpt-sync.plist  # macOS自動実行設定
├── CHATGPT_README.md            # 詳細ドキュメント
├── chatgpt_sync.log             # 同期ログ
└── sample_chatgpt_export*.json  # サンプルデータ
```

## 🚀 主な機能

- ✅ **チャット履歴の自動保存**: ChatGPTのチャットをNotionに自動保存
- ✅ **ページ本文への保存**: チャット内容をページ本文に完全保存
- ✅ **追加メッセージ対応**: 後日追加されたメッセージを自動検出・追加
- ✅ **日付付き追加表示**: `--- 2025-08-17 追加メッセージ ---` で追加日を明確化
- ✅ **タイムスタンプ表示**: `【ユーザー (2024-01-07 10:00:00)】` で正確な日時を記録
- ✅ **差分検出**: 既存メッセージとの重複を避けた効率的な処理
- ✅ **自動同期**: macOSのlaunchdを使用した定期実行

## 📋 セットアップ

### 1. 環境変数の設定
`.env`ファイルに以下を設定：
```env
NOTION_TOKEN=your_notion_integration_token
CHATGPT_DB_ID=your_notion_database_id
NOTION_TIMEOUT=60
```

### 2. 依存関係のインストール
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 自動同期の設定
```bash
python setup_chatgpt_sync.py
```

## 🔧 使用方法

### 手動実行
```bash
# 仮想環境の有効化
source venv/bin/activate

# チャット履歴の同期
python chatgpt_to_notion.py chatgpt_export.json
```

### 自動同期の開始
```bash
# 自動同期の開始
launchctl start com.user.chatgpt-sync

# ログの確認
tail -f chatgpt_sync.log
```

## 📊 データベース構造

**Notionデータベース「AI Chat管理」の構成：**
- **名前**: チャットタイトル
- **URL**: ChatGPTのURL
- **AI カスタム自動入力**: 空（本文に移動）
- **AI 要約**: 空（Notion AIが自動生成）
- **AI Model**: 使用したモデル（GPT-4、GPT-3.5等）
- **最終更新日時**: 自動更新
- **AI Service Auto**: 自動的にChatGPTとして認識

**ページ本文**: チャットの完全な内容（メッセージ数 + 全対話）

## 📝 運用方法

### 週次エクスポート + 自動同期
1. **毎週日曜日**: ChatGPTからデータをエクスポート
2. **ファイル配置**: エクスポートファイルを`ChatGPTToNotion`フォルダに配置
3. **自動処理**: システムが自動でNotionに同期

### エクスポート手順
1. ChatGPTウェブ版で「設定」→「データコントロール」→「エクスポート」
2. ダウンロードされたファイルを`ChatGPTToNotion`フォルダに移動
3. ファイル名を`chatgpt_export_YYYYMMDD.json`のように変更

## 🔍 トラブルシューティング

### よくある問題
- **Notion API エラー**: データベースがインテグレーションと共有されているか確認
- **環境変数エラー**: `.env`ファイルの設定を確認
- **権限エラー**: スクリプトファイルの実行権限を確認

### ログの確認
```bash
tail -f chatgpt_sync.log
```

## 📚 詳細ドキュメント

詳細な設定方法やトラブルシューティングについては、`CHATGPT_README.md`を参照してください。

## 🤝 サポート

問題が発生した場合は、ログファイルを確認し、必要に応じて手動でスクリプトを実行してデバッグしてください。

---

**ChatGPT to Notion - チャット履歴自動保存システム**  
Version: 1.0  
Last Updated: 2025-08-17

