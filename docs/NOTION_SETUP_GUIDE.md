# 📝 Notion Integration設定ガイド

## 🔑 Notion Integration作成手順

### 1. Notion Developersページにアクセス
1. [Notion Developers](https://www.notion.so/my-integrations) にアクセス
2. ログイン（既存のNotionアカウントで）

### 2. 新しいIntegrationを作成
1. "New integration"ボタンをクリック
2. 以下の情報を入力：
   - **Name**: `Receipt Processor`
   - **Associated workspace**: あなたのワークスペースを選択
   - **Capabilities**: 以下を全てチェック
     - ✅ Read content
     - ✅ Update content  
     - ✅ Insert content

### 3. Integration Tokenを取得
1. Integration作成後、**Internal Integration Token**をコピー
2. このトークンは `secret_` で始まる文字列です

### 4. 既存データベースにIntegrationを接続
1. 既存の「領収書管理」データベースページを開く
2. 右上の「...」メニューをクリック
3. "Connections" → "Connect to"を選択
4. 作成した`Receipt Processor` Integrationを選択

### 5. 環境変数の設定
`.env`ファイルまたは`env.production`ファイルを編集：

```bash
# Notion API Settings
NOTION_TOKEN=REDACTED_SECRET
NOTION_DATABASE_ID=254b061dadf38042813eeab350aea734
```

## 🔍 データベースプロパティ確認

既存のデータベースに以下のプロパティがあることを確認してください：

| プロパティ名 | タイプ | 必須 |
|-------------|--------|------|
| 店舗名 | Title | ✅ |
| 日付 | Date | ✅ |
| 金額 | Number | ✅ |
| カテゴリ | Select | ✅ |
| 勘定科目 | Select | ✅ |
| 商品一覧 | Rich text | ✅ |
| 処理状況 | Select | ✅ |
| 信頼度 | Number | ✅ |

### 不足しているプロパティの追加方法
1. データベースページで「+ Add a property」をクリック
2. 必要なプロパティタイプを選択
3. プロパティ名を設定
4. Selectタイプの場合は、オプションを追加

## 🧪 接続テスト

設定完了後、以下のコマンドでテスト：

```bash
python scripts/setup_notion_database.py
```

成功すると以下のメッセージが表示されます：
```
✅ データベース接続成功
✅ 必要なプロパティ: 全て設定済み
✅ テストデータ作成成功
```

## 🚨 よくある問題

### "API token is invalid" エラー
- Integration Tokenが正しくコピーされているか確認
- トークンが `secret_` で始まっているか確認
- 環境変数ファイルが正しく読み込まれているか確認

### "Database not found" エラー
- データベースIDが正しいか確認
- Integrationがデータベースに接続されているか確認
- データベースが存在するか確認

### "Permission denied" エラー
- Integrationに適切な権限が付与されているか確認
- データベースがIntegrationに共有されているか確認

## 📞 サポート

問題が解決しない場合は：
1. Notion DevelopersページでIntegrationの設定を確認
2. データベースの共有設定を確認
3. ログファイルで詳細なエラー情報を確認

