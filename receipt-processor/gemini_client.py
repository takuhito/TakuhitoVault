import os
import json
import structlog
from typing import Dict, Any, Optional
from google.generativeai import GenerativeModel
import google.generativeai as genai

logger = structlog.get_logger(__name__)

class GeminiClient:
    """Gemini APIクライアント"""
    
    def __init__(self, api_key: str):
        """
        Geminiクライアントを初期化
        
        Args:
            api_key: Gemini APIキー
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Gemini Pro Visionモデルを使用
        self.model = GenerativeModel('gemini-1.5-flash')
        
        # 領収書解析用のプロンプト
        self.receipt_prompt = """
あなたは領収書の専門家です。以下の領収書画像を分析して、構造化されたデータを抽出してください。

抽出すべき情報：
1. 店舗名（住所は含めない）
2. 日付（YYYY-MM-DD形式）
3. 合計金額（数字のみ）
4. 商品明細（商品名と価格のリスト）
5. 税額（消費税など）
6. 支払い方法

出力形式（JSON）：
{
    "store_name": "店舗名（住所なし）",
    "date": "YYYY-MM-DD",
    "total_amount": 数値,
    "tax_amount": 数値,
    "payment_method": "支払い方法",
    "items": [
        {
            "name": "商品名",
            "price": 数値,
            "quantity": 数値
        }
    ],
    "confidence": 0.0-1.0,
    "notes": "抽出に関する注意事項"
}

重要事項：
- 店舗名からは住所を除去してください
- 金額は数字のみで出力してください（例：1972、10077）
- 合計金額は最も大きく目立つ金額を優先してください
- レジの表示や小計は商品代として認識しないでください
- 日付が見つからない場合はnullを設定してください
- 信頼度は抽出の確信度を0.0-1.0で評価してください
- 日本語で出力してください
- 金額の認識には特に注意を払い、正確な数値を抽出してください

レシート構造解析の重要事項：
1. レシート全体の構造を理解してください：
   - 商品明細とその金額
   - 小計・税額・合計の関係
   - 支払い方法と支払い金額
   - おつりの計算

2. 金額の意味を正確に区別してください：
   - 「合計」「TOTAL」「税込」の近く = 商品の合計金額
   - 「お支払い」「支払い」の近く = 実際の支払い金額
   - 「おつり」「お釣り」の近く = おつり金額
   - 大きな数字でも、それが何の金額かを文脈で判断

3. 計算の整合性を確認してください：
   - 支払い金額 - 合計金額 = おつり金額
   - 商品合計 + 消費税 = 税込合計
   - 異常な計算結果があれば注意してください

4. 金額の優先順位：
   - 商品合計金額を最優先で抽出
   - 支払い金額は商品金額として扱わない
   - おつりは商品金額として扱わない

勘定科目判定の注意事項：
1. ガソリンスタンド（apollo、エネオス等）→ 交通費/車両費
2. ガス・電気・水道（東京ガス、東京電力等）→ 光熱費/水道光熱費
3. ホームセンター（DCM、カインズ等）→ 雑費/消耗品費
4. コンビニ・スーパー → 食費/販管費
5. 病院・薬局 → 医療費/販管費
"""

    def extract_receipt_data(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        領収書画像から構造化データを抽出
        
        Args:
            image_path: 画像ファイルパス
            
        Returns:
            Optional[Dict[str, Any]]: 抽出されたデータ、失敗時はNone
        """
        try:
            logger.info(f"Gemini領収書解析開始: {image_path}")
            
            # 画像を読み込み
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Geminiに画像とプロンプトを送信
            response = self.model.generate_content([
                self.receipt_prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])
            
            # レスポンスからJSONを抽出
            response_text = response.text.strip()
            
            # JSON部分を抽出（```json と ``` で囲まれている場合）
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            # JSONをパース
            receipt_data = json.loads(json_text)
            
            logger.info(f"Gemini領収書解析完了: {receipt_data.get('store_name', 'Unknown')} - ¥{receipt_data.get('total_amount', 0):,}")
            return receipt_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Gemini JSON解析エラー: {e}")
            logger.error(f"レスポンス: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Gemini領収書解析エラー: {e}")
            return None

    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        画像からテキストを抽出（従来のOCR互換メソッド）
        
        Args:
            image_path: 画像ファイルパス
            
        Returns:
            Optional[str]: 抽出されたテキスト、失敗時はNone
        """
        try:
            logger.info(f"Geminiテキスト抽出開始: {image_path}")
            
            # 画像を読み込み
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # シンプルなテキスト抽出プロンプト
            prompt = "この画像に含まれるテキストをすべて抽出してください。改行は保持してください。"
            
            response = self.model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])
            
            extracted_text = response.text.strip()
            logger.info(f"Geminiテキスト抽出完了: {len(extracted_text)}文字")
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Geminiテキスト抽出エラー: {e}")
            return None

