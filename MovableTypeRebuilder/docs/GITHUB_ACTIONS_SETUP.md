# GitHub Actions移行ガイド

## 概要
MovableType再構築システムをGitHub Actionsに移行するための設定手順です。

**注意**: このGitHub Actions版はバックアップ版として設計されています。
- ローカル版（毎月1日0:01）がメイン実行
- GitHub Actions版（毎月1日0:05）がバックアップ実行
- ローカル版が失敗した場合の保険として機能

## 1. GitHub Secretsの設定

GitHubリポジトリの設定で以下のシークレットを設定してください：

### MovableType設定
- `MT_SITE_URL`: MovableTypeサイトのURL
  - 例: `https://nbspress.com/mt/mt.cgi`
- `MT_USERNAME`: MovableType管理者ユーザー名
  - 例: `admin`
- `MT_PASSWORD`: MovableType管理者パスワード
  - 例: `Z9MSNPSknzmr`
- `MT_BLOG_ID`: 再構築対象のブログID
  - 例: `45`
- `MT_SITE_NAME`: サイト名（通知用）
  - 例: `公演カレンダー`

### メール通知設定
- `EMAIL_USERNAME`: メール送信用のユーザー名
  - 例: `your-email@gmail.com`
- `EMAIL_PASSWORD`: メール送信用のアプリパスワード
  - 例: `your-16-character-app-password`
- `FROM_EMAIL`: 送信元メールアドレス
  - 例: `your-email@gmail.com`
- `TO_EMAIL`: 送信先メールアドレス
  - 例: `recipient@example.com`

## 2. Secrets設定手順

1. GitHubリポジトリページにアクセス
2. Settings → Secrets and variables → Actions
3. "New repository secret"をクリック
4. 上記の各シークレットを追加

## 3. ワークフローの有効化

1. Actionsタブに移動
2. "MovableType Monthly Rebuild"ワークフローを選択
3. "Run workflow"で手動実行テスト

## 4. 実行スケジュール

- **自動実行**: 毎月1日の0:05 日本時間（バックアップ版）
- **手動実行**: いつでも可能
- **タイムアウト**: 30分

## 5. 通知内容

### 成功時
```
件名: [GitHub Actions] MovableType再構築結果 - 公演カレンダー - ✅ 成功

内容:
[GitHub Actions] MovableType再構築結果

対象サイト: 公演カレンダー (blog_id: 45)
✅ 成功
時刻: 2025-08-28T16:53:12.359730
メッセージ: 公演カレンダー (blog_id: 45) の再構築が正常に完了しました

---
MovableType再構築システム (GitHub Actions版)
```

### 失敗時
```
件名: [GitHub Actions] MovableType再構築結果 - 公演カレンダー - ❌ 失敗

内容:
[GitHub Actions] MovableType再構築結果

対象サイト: 公演カレンダー (blog_id: 45)
❌ 失敗
時刻: 2025-08-28T16:53:12.359730
メッセージ: エラー内容

---
MovableType再構築システム (GitHub Actions版)
```

## 6. ログとアーティファクト

### ログファイル
- GitHub Actionsの実行ログで詳細を確認
- ログファイルがアーティファクトとして保存される

### アーティファクト
- 実行ログファイル（30日間保存）
- ダウンロードして詳細確認可能

## 7. トラブルシューティング

### よくある問題

**ログイン失敗**
- MovableTypeの認証情報を確認
- パスワードが正しいか確認

**メール通知失敗**
- Gmailアプリパスワードを確認
- 2段階認証が有効か確認

**タイムアウト**
- 再構築に時間がかかりすぎている
- MovableTypeサーバーの負荷を確認

### デバッグ方法

1. **手動実行テスト**
   - Actionsタブで手動実行
   - ログを詳細確認

2. **ローカルテスト**
   ```bash
   cd MovableTypeRebuilder
   python mt_rebuilder_github_action.py
   ```

3. **設定確認**
   - GitHub Secretsが正しく設定されているか確認
   - 環境変数が正しく読み込まれているか確認

## 8. ローカル版との違い

| 項目 | ローカル版 | GitHub Actions版 |
|------|------------|------------------|
| 実行環境 | Mac | Ubuntu |
| 実行頻度 | 毎月1日0:01 | 毎月1日0:05 |
| 役割 | メイン実行 | バックアップ実行 |
| 通知タイトル | MovableType再構築通知 | [GitHub Actions] MovableType再構築通知 |
| ログ保存 | ローカルファイル | GitHub Actionsログ |
| 手動実行 | `python mt_rebuilder.py` | GitHub Actions UI |

## 9. 移行完了確認

1. ✅ GitHub Secrets設定完了
2. ✅ 手動実行テスト成功
3. ✅ メール通知受信確認
4. ✅ 自動実行スケジュール確認

移行が完了したら、ローカル版のスケジューラーを停止できます：

```bash
launchctl unload ~/Library/LaunchAgents/com.user.movabletype-rebuilder.plist
```
