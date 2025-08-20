# 🚀 領収書自動処理システム - 本番運用版

## ✨ システム概要

AIを活用した自動領収書処理システムです。vFlatアプリでスキャンした領収書を自動的に：

- 📱 **Google Drive受信箱**から自動取得
- 🤖 **Gemini AI**で高精度データ抽出 
- 📋 **Notion**で自動データベース化
- 📁 **月別フォルダ**で自動整理
- 🔄 **抜け漏れ防止**機能搭載

## 🏗️ アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   vFlat App     │ ──▶│  Google Drive   │ ──▶│  Cloud Run      │
│  (iPhone scan)  │    │   (受信箱)       │    │  (処理システム)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐              │
                       │   Cloud         │◀─────────────┤
                       │   Scheduler     │              │
                       │  (6時間毎実行)   │              │
                       └─────────────────┘              │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Notion      │◀───│   Gemini AI     │◀───│  処理結果通知    │
│   (Database)    │    │ (データ抽出)     │    │ (ログ・監視)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 技術スタック

- **Backend**: Python 3.11
- **AI**: Google Gemini 1.5 Flash
- **OCR**: Google Cloud Vision API (フォールバック)
- **Database**: Notion API
- **Storage**: Google Drive (共有ドライブ)
- **Infrastructure**: Google Cloud Run
- **Scheduling**: Google Cloud Scheduler
- **CI/CD**: GitHub Actions
- **Containerization**: Docker

## 📊 処理性能

- **精度**: 80-90% (AI判定 + 抜け漏れ防止)
- **処理速度**: 約10-15秒/ファイル
- **対応形式**: PDF, JPG, PNG
- **同時処理**: 1ファイル (安定性重視)
- **自動復旧**: 失敗時の自動再処理

## 🌟 主要機能

### 1. 🎯 高精度データ抽出
- **店舗名**: 住所・法人格除去で短縮
- **金額**: 商品金額と支払金額の正確な区別
- **日付**: 自動フォーマット変換
- **カテゴリ**: 自動分類と勘定科目推定

### 2. 🔄 抜け漏れ防止システム
- **自動検証**: 処理完了後の未処理ファイル検出
- **自動再処理**: 失敗ファイルの自動リトライ
- **エラー移動**: 最終的な未処理ファイルのエラーフォルダ移動
- **詳細レポート**: 処理状況の完全可視化

### 3. 📁 自動ファイル管理
- **月別整理**: 日付に基づく自動フォルダ分類
- **JPG保存**: PDF → JPG変換で個別保存
- **リンク生成**: NotionからGoogle Driveへの直接リンク
- **重複防止**: ファイル名の自動調整

### 4. 🤖 AI処理の最適化
- **Gemini優先**: 高精度AI処理を第一選択
- **Vision フォールバック**: Gemini失敗時の自動切り替え
- **構造解析**: レシート全体の文脈理解
- **計算検証**: 金額の整合性チェック

## 🚀 デプロイ手順

### 1. 前提条件
```bash
# Google Cloud CLI インストール
curl https://sdk.cloud.google.com | bash

# Dockerインストール (Mac)
brew install docker

# プロジェクト作成
gcloud projects create your-project-id
gcloud config set project your-project-id
```

### 2. 一括デプロイ
```bash
# リポジトリクローン
git clone https://github.com/your-username/NotionWorkflowTools.git
cd NotionWorkflowTools

# デプロイ実行
./scripts/deploy.sh your-project-id
```

### 3. シークレット設定
```bash
# 認証情報の設定
gcloud secrets create notion-token --data-file=<(echo 'YOUR_TOKEN')
gcloud secrets create gemini-api-key --data-file=<(echo 'YOUR_API_KEY')
# ... 他のシークレット
```

## 📈 運用監視

### 🔍 ログ監視
```bash
# リアルタイムログ
gcloud logs tail projects/your-project-id/logs/run.googleapis.com%2Fstdout

# エラーログフィルタ
gcloud logs read "severity>=ERROR" --limit=50
```

### 📊 メトリクス
- **成功率**: 処理成功率の追跡
- **処理時間**: パフォーマンス監視
- **エラー率**: 異常検知
- **リソース使用率**: コスト最適化

### 🚨 アラート設定
- **処理失敗**: 連続失敗時の通知
- **リソース枯渇**: CPU/メモリ使用率警告  
- **API制限**: 各種API制限の監視
- **コスト**: 予算超過アラート

## 💰 運用コスト

### 月額推定費用 (小規模利用)
- **Cloud Run**: $5-15
- **Cloud Storage**: $1-5  
- **Vision API**: $2-8
- **Gemini API**: 無料枠内
- **合計**: 約$8-30/月

### コスト最適化
- **ゼロスケーリング**: 未使用時のコスト削減
- **API効率化**: バッチ処理による呼び出し削減
- **ストレージ最適化**: 画像圧縮と古いファイル削除

## 🔐 セキュリティ

### 認証・認可
- **サービスアカウント**: 最小権限設定
- **Secret Manager**: 機密情報の安全管理
- **内部アクセス**: 外部からの直接アクセス禁止
- **ログ監査**: 全アクセスの記録

### データ保護
- **暗号化**: 転送時・保存時の暗号化
- **アクセス制御**: ロールベース権限管理
- **バックアップ**: 自動データバックアップ
- **復旧手順**: 災害復旧計画

## 🛠️ トラブルシューティング

### よくある問題と解決法

1. **Gemini API制限**
   ```bash
   # フォールバック確認
   gcloud logs read "Gemini解析失敗" --limit=10
   ```

2. **メモリ不足**
   ```bash
   # メモリ増加
   gcloud run services update receipt-processor --memory 4Gi
   ```

3. **タイムアウト**
   ```bash
   # タイムアウト延長
   gcloud run services update receipt-processor --timeout 900
   ```

4. **ファイル移動失敗**
   ```bash
   # 権限確認
   gcloud projects get-iam-policy your-project-id
   ```

## 📞 サポート

### 緊急時対応
1. **システム停止**: Cloud Runサービスの再起動
2. **データ復旧**: バックアップからの復元
3. **API制限**: 代替手段への切り替え
4. **権限エラー**: サービスアカウント権限の確認

### 改善要望
- **GitHub Issues**: バグ報告・機能要望
- **Pull Request**: コード改善提案
- **ドキュメント**: 使用方法の質問

## 📈 今後の拡張予定

### Phase 1: 精度向上
- [ ] カスタムAIモデルの学習
- [ ] 店舗固有パターンの学習
- [ ] OCR精度の向上

### Phase 2: 機能拡張  
- [ ] 複数通貨対応
- [ ] 領収書以外の帳票対応
- [ ] 自動仕訳入力

### Phase 3: 統合強化
- [ ] 会計ソフト直接連携
- [ ] 承認ワークフロー
- [ ] モバイルアプリ開発

---

**📝 更新履歴**
- 2025-08-20: 本番運用版リリース
- 2025-08-20: 抜け漏れ防止機能追加
- 2025-08-20: Gemini AI統合完了

**🚀 本番運用開始: 2025年8月20日**
