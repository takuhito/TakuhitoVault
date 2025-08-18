# 設定ファイル

このフォルダには、NotionLinkerのシステム設定ファイルが保存されています。

## ファイル一覧

### launchd設定ファイル
- `com.tkht.notion-linker.plist` - macOSのlaunchd用設定ファイル（自動実行用）

## 使用方法

### launchd設定のインストール
```bash
# 設定ファイルをlaunchdに登録
launchctl load config/com.tkht.notion-linker.plist
```

### launchd設定の削除
```bash
# 設定ファイルをlaunchdから削除
launchctl unload config/com.tkht.notion-linker.plist
```

## 注意事項
- この設定ファイルはmacOSの自動実行機能を使用します
- システム全体に影響するため、慎重に操作してください
