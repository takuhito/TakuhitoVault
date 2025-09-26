# NotionWorkflowTools

Notionと連携したワークフロー自動化ツール群

## プロジェクト概要

このプロジェクトは、Notionを中心としたワークフロー自動化のための各種ツールを提供します。

## 主要コンポーネント

### ✅ HETEMLMonitor (完了)
- **概要**: HETEMLサーバーのファイル監視システム
- **機能**: 
  - 再帰的ディレクトリ監視
  - ファイル変更検知（新規、削除、変更）
  - 詳細通知（Email、Slack、LINE）
  - ローカル版のみ運用（GitHub Actions版は開発中止）
- **状態**: 本番運用中

### ✅ ChatGPTToNotion (完了)
- **概要**: ChatGPT/Cursorチャット履歴のNotion保存
- **機能**: MarkdownからNotionブロックへの変換、既存ページ更新
- **状態**: 本番運用中

### ✅ ChatHistoryToNotion (完了)
- **概要**: チャット履歴ファイルの自動Notion転送
- **機能**: 定期的なMarkdownファイル監視と転送
- **状態**: 本番運用中

### ✅ MovableTypeRebuilder (完了)
- **概要**: MovableTypeサイトの定期再構築
- **機能**: 毎月1日00:01に自動実行
- **状態**: 本番運用中

### ✅ NotionLinker (完了)
- **概要**: Notionページのリンク管理
- **機能**: ページ間の関連性管理
- **状態**: 本番運用中

### 🔄 n8n Workflows (新規追加)
- **概要**: n8nを使用したワークフロー自動化
- **機能**: 
  - NotionLinkerの自動実行・手動実行
  - ビジュアルワークフロー管理
  - エラーハンドリング・通知機能
- **状態**: セットアップ完了、運用準備中
- **場所**: `n8n_workflows/`

## 環境設定

### 必要な環境変数
```bash
# .envファイルに設定
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id
# その他プロジェクト固有の設定
```

### 環境変数の同期
```bash
# ルートの.envファイルを全プロジェクトに同期
./sync_env_files.sh
```

## セットアップ

1. リポジトリをクローン
2. 各プロジェクトの依存関係をインストール
3. 環境変数を設定
4. 必要に応じてlaunchdサービスを設定

## 運用状況

- **ローカル版**: 全ツールが正常動作
- **GitHub Actions**: HETEMLMonitorのみ開発中止
- **定期実行**: MovableTypeRebuilder（毎月1日）
- **監視**: HETEMLMonitor（30分間隔）

## 技術スタック

- Python 3.x
- Notion API
- SFTP/SSH (paramiko)
- launchd (macOS)
- Markdown解析・変換
- n8n (ワークフロー自動化)

## ライセンス

MIT License

## 更新履歴

- 2025/01/09: n8n Workflows追加、NotionLinker自動化ワークフロー作成
- 2025/09/01: HETEMLMonitor GitHub Actions版開発中止、プロジェクト整理完了
- 2025/08/29: 全プロジェクトの基本機能完了
- 2025/08/28: プロジェクト基盤構築

