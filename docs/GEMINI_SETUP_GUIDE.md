# Gemini API 設定ガイド

## 概要

Gemini APIを使用することで、領収書の構造化データ抽出精度が大幅に向上します。従来のOCR処理に比べて、以下の利点があります：

- **高精度な店舗名抽出**: 住所を自動的に除去
- **構造化データの直接抽出**: JSON形式で店舗名、日付、金額、商品明細を取得
- **日本語対応**: 日本語の領収書に特化した処理
- **コンテキスト理解**: 領収書の構造を理解した適切なデータ抽出

## 1. Gemini APIキーの取得

### 1.1 Google AI Studioにアクセス
1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン

### 1.2 APIキーの作成
1. 「Create API Key」をクリック
2. APIキーが生成されます
3. 生成されたAPIキーをコピーして保存

## 2. 環境変数の設定

### 2.1 .envファイルの作成
プロジェクトルートに`.env`ファイルを作成し、以下の内容を追加：

```bash
# Gemini API Settings
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2.2 実際のAPIキーを設定
`your_gemini_api_key_here`を実際のAPIキーに置き換えてください。

## 3. 依存関係のインストール

```bash
pip install google-generativeai==0.8.3
```

## 4. 動作確認

### 4.1 テスト実行
```bash
python receipt-processor/main.py
```

### 4.2 ログの確認
Geminiが正常に動作している場合、以下のようなログが表示されます：

```
Gemini領収書解析開始: /path/to/image.jpg
Gemini解析成功: 店舗名
```

## 5. フォールバック機能

Gemini APIキーが設定されていない場合や、Gemini処理が失敗した場合は、自動的に従来のOCR処理（Google Cloud Vision API）にフォールバックします。

## 6. 処理方法の確認

Notionページの`処理メモ`欄に、使用された処理方法が記録されます：
- `gemini`: Gemini APIを使用
- `ocr`: Google Cloud Vision APIを使用

## 7. トラブルシューティング

### 7.1 APIキーエラー
```
Gemini APIキーなし、OCR処理を使用: filename.jpg
```
→ APIキーが正しく設定されているか確認してください。

### 7.2 JSON解析エラー
```
Gemini JSON解析エラー: ...
```
→ Geminiのレスポンス形式に問題がある場合があります。この場合は自動的にOCR処理にフォールバックします。

## 8. パフォーマンス

- **Gemini処理**: より高精度だが、処理時間が若干長い
- **OCR処理**: 高速だが、精度が低い場合がある

システムは自動的に最適な処理方法を選択します。

## 9. セキュリティ

- APIキーは環境変数として管理
- ローカルファイルとして保存されることはありません
- 本番環境では適切なシークレット管理を使用してください

