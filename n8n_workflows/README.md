# n8nでNotionLinkerを実行する方法

## 概要
n8nを使用してNotionLinkerを自動実行・管理するワークフローです。

## セットアップ

### 1. n8nの起動
```bash
n8n start
```
ブラウザで `http://localhost:5678` にアクセス

### 2. ワークフローのインポート
1. n8nのWebインターフェースを開く
2. 「Import from file」をクリック
3. 以下のファイルをインポート：
   - `notion_linker_workflow.json` - 6時間ごと自動実行
   - `manual_notion_linker_workflow.json` - 手動実行

## ワークフロー構成

### 自動実行ワークフロー（6時間ごと）
```
[Schedule Trigger] → [Execute Command] → [If Condition] → [Success/Error Notification]
```

**ノード説明：**
- **Schedule Trigger**: 6時間ごとに実行（0時、6時、12時、18時）
- **Execute Command**: NotionLinkerスクリプトを実行
- **If Condition**: 実行結果をチェック（終了コード0=成功）
- **Success/Error Notification**: 結果に応じた通知

### 手動実行ワークフロー
```
[Manual Trigger] → [Execute Command] → [If Condition] → [Success/Error Notification]
```

**ノード説明：**
- **Manual Trigger**: 手動でワークフローを開始
- その他のノードは自動実行と同じ

## 使用方法

### 自動実行の有効化
1. 自動実行ワークフローを開く
2. 「Active」トグルをONにする
3. 毎日午前6時に自動実行される

### 手動実行
1. 手動実行ワークフローを開く
2. 「Execute Workflow」ボタンをクリック
3. 実行結果が表示される

## カスタマイズ

### 実行時間の変更
Schedule Triggerノードの設定でcron式を変更：
- `0 6 * * *` → 毎日6時
- `0 */2 * * *` → 2時間おき
- `0 0 * * 1` → 毎週月曜日

### 通知の追加
Success/Error Notificationノードを以下のノードに置き換え：
- **Slack**: Slack通知
- **Email**: メール通知
- **Webhook**: カスタム通知

### 条件分岐の追加
If Conditionノードの後に追加の処理を配置：
- エラー時の自動リトライ
- 特定条件でのみ実行
- ログファイルの保存

## トラブルシュート

### よくある問題

**1. NotionLinkerが実行されない**
- NotionLinkerのパスが正しいか確認
- 実行権限があるか確認
- .envファイルが存在するか確認

**2. エラーが発生する**
- n8nのログを確認
- NotionLinkerのログを確認
- 環境変数が正しく設定されているか確認

**3. 通知が届かない**
- 通知ノードの設定を確認
- 通知先の認証情報を確認

### ログの確認
```bash
# n8nのログ
tail -f ~/.n8n/logs/n8n.log

# NotionLinkerのログ
tail -f /Users/takuhito/NotionWorkflowTools/NotionLinker/logs/
```

## メリット

### launchdとの比較
| 機能 | launchd | n8n |
|------|---------|-----|
| 自動実行 | ✅ | ✅ |
| 手動実行 | ❌ | ✅ |
| ビジュアル管理 | ❌ | ✅ |
| エラーハンドリング | 基本 | 高度 |
| 通知機能 | ❌ | ✅ |
| ログ管理 | 基本 | 高度 |
| 条件分岐 | ❌ | ✅ |

### n8nの利点
1. **ビジュアル管理**: ワークフローの可視化
2. **柔軟な実行**: 手動・自動・条件付き実行
3. **エラーハンドリング**: 失敗時の自動リトライ
4. **通知機能**: 実行結果の即座な確認
5. **拡張性**: 他のサービスとの連携が容易

## 次のステップ

1. **通知の設定**: Slackやメール通知を追加
2. **監視の強化**: 実行時間の監視・アラート
3. **他のワークフローとの連携**: チャット履歴同期など
4. **クラウド展開**: n8n Cloudでの運用検討
