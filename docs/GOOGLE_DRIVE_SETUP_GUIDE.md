# 📁 Google Drive設定ガイド

## 🔐 サービスアカウント権限設定

### 1. Google Driveフォルダの共有設定

Google Driveのフォルダにサービスアカウントを追加する必要があります：

#### 手順1: サービスアカウントのメールアドレスを確認
1. `credentials/service-account.json`ファイルを開く
2. `client_email`フィールドの値を確認
3. 例: `receipt-processor@receipt-processor-20241220.iam.gserviceaccount.com`

#### 手順2: Google Driveフォルダを共有
1. Google Driveで「領収書管理」フォルダを開く
2. 右上の「共有」ボタンをクリック
3. 「ユーザーやグループを追加」をクリック
4. サービスアカウントのメールアドレスを入力
5. 権限を「編集者」に設定
6. 「送信」をクリック

#### 手順3: サブフォルダも共有
以下のフォルダも同様に共有してください：
- `領収書管理/受信箱/`
- `領収書管理/2024/`
- `領収書管理/2025/`
- `領収書管理/エラー/`

### 2. フォルダ構造の確認

推奨フォルダ構造：
```
📁 領収書管理/
  ├── 📁 受信箱/          (監視対象フォルダ)
  ├── 📁 2024/
  │   ├── 📁 01/
  │   ├── 📁 02/
  │   └── ...
  ├── 📁 2025/
  │   ├── 📁 01/
  │   ├── 📁 02/
  │   └── ...
  └── 📁 エラー/
      ├── 📁 形式エラー/
      └── 📁 OCRエラー/
```

### 3. フォルダIDの取得方法

#### 方法1: URLから取得
1. Google Driveでフォルダを開く
2. URLを確認：
   ```
   https://drive.google.com/drive/folders/1ABC...XYZ
   ```
3. `1ABC...XYZ`の部分がフォルダID

#### 方法2: スクリプトで取得
共有設定完了後、以下のコマンドで取得：
```bash
python scripts/get_google_drive_folder_ids.py
```

### 4. 環境変数の設定

取得したフォルダIDを環境変数に設定：

```bash
# Google Drive設定
GOOGLE_DRIVE_MONITOR_FOLDER=受信箱のフォルダID
GOOGLE_DRIVE_PROCESSED_BASE=領収書管理のフォルダID
GOOGLE_DRIVE_ERROR_FOLDER=エラーフォルダのフォルダID
```

## 🧪 設定確認

### 1. 権限確認
```bash
python scripts/list_google_drive_folders.py
```

### 2. フォルダID取得
```bash
python scripts/get_google_drive_folder_ids.py
```

### 3. システムテスト
```bash
python receipt-processor/main.py
```

## 🚨 よくある問題

### "フォルダが見つかりません" エラー
- サービスアカウントがフォルダに共有されているか確認
- フォルダ名が正確か確認
- フォルダが削除されていないか確認

### "Permission denied" エラー
- サービスアカウントの権限が「編集者」以上か確認
- フォルダの共有設定を再確認

### "API quota exceeded" エラー
- Google Drive APIの使用量制限に達している
- しばらく待ってから再試行

## 📞 サポート

問題が解決しない場合は：
1. サービスアカウントのメールアドレスを確認
2. フォルダの共有設定を再確認
3. Google Cloud ConsoleでAPI有効化を確認

