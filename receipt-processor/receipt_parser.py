"""
領収書解析機能
"""
import re
import structlog
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime
import json

from utils import (
    extract_date_from_text,
    extract_amount_from_text,
    extract_store_name_from_text,
    generate_title
)
from config.mapping import get_category_and_account, get_payment_method_from_text

logger = structlog.get_logger()

class ReceiptParser:
    """領収書解析クラス"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.enhanced_patterns = self._load_enhanced_patterns()
    
    def _load_enhanced_patterns(self) -> Dict[str, List[str]]:
        """高度な解析パターンを読み込み"""
        return {
            'store_name_enhanced': [
                r'^(.+?)(?:店|支店|本店|営業所|オフィス|事務所)',
                r'(?:店舗|店名|会社名|企業名)[：:]\s*(.+)',
                r'^(.+?)(?:\s+株式会社|\s+有限会社|\s+合同会社)',
                r'(?:株式会社|有限会社|合同会社)\s*(.+)',
            ],
            'amount_enhanced': [
                r'合計[：:]\s*([0-9,]+)',
                r'総計[：:]\s*([0-9,]+)',
                r'請求金額[：:]\s*([0-9,]+)',
                r'支払金額[：:]\s*([0-9,]+)',
                r'お支払い[：:]\s*([0-9,]+)',
                r'ご請求[：:]\s*([0-9,]+)',
            ],
            'date_enhanced': [
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'(\d{1,2})月(\d{1,2})日',
                r'(\d{4})-(\d{1,2})-(\d{1,2})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
                r'(\d{1,2})/(\d{1,2})',
            ],
            'items_enhanced': [
                r'^(.+?)\s+(\d+)\s+([0-9,]+)\s+([0-9,]+)$',
                r'^(.+?)\s+([0-9,]+)\s+([0-9,]+)$',
                r'^(.+?)\s+(\d+)\s+([0-9,]+)$',
            ]
        }
    
    def parse_receipt_data(self, ocr_text: str, file_path: str = None) -> Dict[str, Any]:
        """
        OCR結果から領収書データを解析（改善版）
        
        Args:
            ocr_text: OCRで抽出されたテキスト
            file_path: 元ファイルパス（オプション）
            
        Returns:
            Dict[str, Any]: 解析された領収書データ
        """
        try:
            logger.info("領収書データ解析開始（改善版）")
            
            # テキストの前処理
            processed_text = self._preprocess_text(ocr_text)
            
            # 基本データの抽出（改善版）
            date = self._extract_date_enhanced(processed_text)
            store_name = self._extract_store_name_enhanced(processed_text)
            total_amount = self._extract_total_amount_enhanced(processed_text)
            
            # 詳細解析
            parsed_data = {
                'date': date,
                'store_name': store_name or '不明',
                'total_amount': total_amount,
                'amount_without_tax': self._extract_amount_without_tax(processed_text),
                'tax_amount': self._extract_tax_amount(processed_text),
                'payment_method': get_payment_method_from_text(processed_text),
                'items': self._extract_items_enhanced(processed_text),
                'receipt_number': self._extract_receipt_number(processed_text),
                'cashier_info': self._extract_cashier_info(processed_text),
                'confidence_score': self._calculate_confidence_score_enhanced(processed_text, date, store_name, total_amount),
                'processing_notes': self._generate_processing_notes(processed_text, date, store_name, total_amount),
                'text_quality_score': self._calculate_text_quality_score(processed_text),
                'extraction_metadata': self._generate_extraction_metadata(processed_text)
            }
            
            # カテゴリと勘定科目の判定（改善版）
            if store_name:
                category, account = self._get_category_and_account_enhanced(store_name, total_amount, parsed_data['items'])
                parsed_data['category'] = category
                parsed_data['account'] = account
            else:
                parsed_data['category'] = '雑費'
                parsed_data['account'] = 'その他販管費'
            
            # タイトルの生成（勘定科目+金額）
            if store_name:
                category, account = self._get_category_and_account_enhanced(store_name, total_amount, parsed_data['items'])
                parsed_data['title'] = generate_title(account, total_amount)
            else:
                parsed_data['title'] = f"領収書_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # ファイルパスがある場合は追加
            if file_path:
                parsed_data['file_path'] = file_path
            
            logger.info(f"領収書データ解析完了（改善版）: {parsed_data['title']}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"領収書データ解析エラー（改善版）: {e}")
            return self._create_fallback_data(ocr_text, file_path)
    
    def _preprocess_text(self, text: str) -> str:
        """テキストの前処理"""
        # 改行文字の正規化
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 複数の空白を単一の空白に
        text = re.sub(r'\s+', ' ', text)
        
        # 行の前後の空白を削除
        lines = [line.strip() for line in text.split('\n')]
        
        # 空行を削除
        lines = [line for line in lines if line]
        
        return '\n'.join(lines)
    
    def _extract_date_enhanced(self, text: str) -> Optional[datetime]:
        """改善された日付抽出"""
        # 基本の日付抽出を試行
        date = extract_date_from_text(text)
        if date:
            return date
        
        # 高度なパターンで日付を抽出
        for pattern in self.enhanced_patterns['date_enhanced']:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        if len(match.group(1)) == 4:  # YYYY-MM-DD
                            year, month, day = match.groups()
                        else:  # MM/DD/YYYY
                            month, day, year = match.groups()
                    else:  # MM/DD
                        month, day = match.groups()
                        year = datetime.now().year
                    
                    return datetime(int(year), int(month), int(day))
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_store_name_enhanced(self, text: str) -> Optional[str]:
        """改善された店舗名抽出"""
        # 基本の店舗名抽出を試行
        store_name = extract_store_name_from_text(text)
        if store_name:
            return store_name
        
        # 高度なパターンで店舗名を抽出
        for pattern in self.enhanced_patterns['store_name_enhanced']:
            match = re.search(pattern, text)
            if match:
                store_name = match.group(1).strip()
                if len(store_name) > 2:  # 短すぎる名前は除外
                    return store_name
        
        return None
    
    def _extract_total_amount_enhanced(self, text: str) -> Optional[float]:
        """改善された合計金額抽出（構造理解版）"""
        # 基本の金額抽出を試行
        amount = extract_amount_from_text(text)
        if amount:
            return amount
        
        # レシート構造を理解した金額抽出
        structured_amounts = self._extract_structured_amounts(text)
        if structured_amounts:
            return structured_amounts.get('total_amount')
        
        # 従来のパターンマッチング（フォールバック）
        for pattern in self.enhanced_patterns['amount_enhanced']:
            match = re.search(pattern, text)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount_value = float(amount_str)
                    
                    # 金額の妥当性チェック
                    if amount_value > 0 and amount_value < 1000000:
                        return amount_value
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_structured_amounts(self, text: str) -> Optional[Dict[str, float]]:
        """レシート構造を理解した金額抽出"""
        try:
            amounts = {}
            
            # 商品合計金額の抽出（最優先）
            total_patterns = [
                r'合計[：:]\s*([0-9,]+)',
                r'TOTAL[：:]\s*([0-9,]+)',
                r'税込[：:]\s*([0-9,]+)',
                r'商品合計[：:]\s*([0-9,]+)',
            ]
            
            for pattern in total_patterns:
                match = re.search(pattern, text)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    amounts['total_amount'] = float(amount_str)
                    break
            
            # 支払い金額の抽出
            payment_patterns = [
                r'お支払い[：:]\s*([0-9,]+)',
                r'支払い[：:]\s*([0-9,]+)',
                r'現金[：:]\s*([0-9,]+)',
            ]
            
            for pattern in payment_patterns:
                match = re.search(pattern, text)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    amounts['payment_amount'] = float(amount_str)
                    break
            
            # おつり金額の抽出
            change_patterns = [
                r'おつり[：:]\s*([0-9,]+)',
                r'お釣り[：:]\s*([0-9,]+)',
                r'つり[：:]\s*([0-9,]+)',
            ]
            
            for pattern in change_patterns:
                match = re.search(pattern, text)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    amounts['change_amount'] = float(amount_str)
                    break
            
            # 計算の整合性チェック
            if self._validate_amount_calculation(amounts):
                return amounts
            
            return amounts if amounts.get('total_amount') else None
            
        except Exception as e:
            logger.error(f"構造化金額抽出エラー: {e}")
            return None
    
    def _validate_amount_calculation(self, amounts: Dict[str, float]) -> bool:
        """金額計算の整合性を検証"""
        try:
            total = amounts.get('total_amount')
            payment = amounts.get('payment_amount')
            change = amounts.get('change_amount')
            
            # 支払い金額とおつりの計算チェック
            if total and payment and change:
                calculated_change = payment - total
                if abs(calculated_change - change) < 1:  # 1円未満の誤差は許容
                    logger.info(f"金額計算整合性確認: 支払い{payment} - 合計{total} = おつり{change}")
                    return True
            
            return True  # 計算できない場合はTrue（エラーではない）
            
        except Exception as e:
            logger.error(f"金額計算検証エラー: {e}")
            return False
    
    def _extract_amount_without_tax(self, text: str) -> Optional[float]:
        """
        税抜金額を抽出
        
        Args:
            text: OCRテキスト
            
        Returns:
            Optional[float]: 税抜金額
        """
        # 税抜金額のパターン
        patterns = [
            r'税抜[：:]\s*([0-9,]+)',
            r'税抜\s*([0-9,]+)',
            r'小計[：:]\s*([0-9,]+)',
            r'小計\s*([0-9,]+)',
            r'商品合計[：:]\s*([0-9,]+)',
            r'商品合計\s*([0-9,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    return float(amount_str)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_tax_amount(self, text: str) -> Optional[float]:
        """
        消費税額を抽出
        
        Args:
            text: OCRテキスト
            
        Returns:
            Optional[float]: 消費税額
        """
        # 消費税のパターン
        patterns = [
            r'消費税[：:]\s*([0-9,]+)',
            r'消費税\s*([0-9,]+)',
            r'税額[：:]\s*([0-9,]+)',
            r'税額\s*([0-9,]+)',
            r'内税[：:]\s*([0-9,]+)',
            r'内税\s*([0-9,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    return float(amount_str)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_items_enhanced(self, text: str) -> List[Dict[str, Any]]:
        """
        商品明細を抽出（改善版）
        
        Args:
            text: OCRテキスト
            
        Returns:
            List[Dict[str, Any]]: 商品明細のリスト
        """
        items = []
        
        # 行ごとに解析
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 改善された商品明細パターン
            for pattern in self.enhanced_patterns['items_enhanced']:
                match = re.match(pattern, line)
                if match:
                    try:
                        groups = match.groups()
                        if len(groups) == 4:  # 商品名 + 数量 + 単価 + 金額
                            item_name = groups[0].strip()
                            quantity = int(groups[1])
                            unit_price = float(groups[2].replace(',', ''))
                            total_price = float(groups[3].replace(',', ''))
                        elif len(groups) == 3:
                            if groups[1].isdigit():  # 商品名 + 数量 + 金額
                                item_name = groups[0].strip()
                                quantity = int(groups[1])
                                unit_price = None
                                total_price = float(groups[2].replace(',', ''))
                            else:  # 商品名 + 単価 + 金額
                                item_name = groups[0].strip()
                                quantity = 1
                                unit_price = float(groups[1].replace(',', ''))
                                total_price = float(groups[2].replace(',', ''))
                        else:
                            continue
                        
                        # 明らかに商品でない行を除外
                        if self._is_valid_item_name(item_name):
                            items.append({
                                'name': item_name,
                                'quantity': quantity,
                                'unit_price': unit_price,
                                'total_price': total_price
                            })
                    except (ValueError, TypeError):
                        continue
        
        return items
    
    def _is_valid_item_name(self, item_name: str) -> bool:
        """商品名が有効かどうかを判定"""
        # 明らかに商品でないキーワード
        invalid_keywords = [
            '合計', '小計', '税抜', '税込', '消費税', '内税', '外税',
            '支払', 'お支払い', 'ご請求', '請求', 'レシート', '伝票',
            '店舗', '店名', '会社名', '企業名', '担当', 'レジ', '店員',
            '日付', '時間', '時刻', '番号', 'No', '№'
        ]
        
        # 短すぎる名前は除外
        if len(item_name) < 2:
            return False
        
        # 無効なキーワードを含む場合は除外
        for keyword in invalid_keywords:
            if keyword in item_name:
                return False
        
        return True
    
    def _calculate_confidence_score_enhanced(self, text: str, date: datetime, 
                                           store_name: str, total_amount: float) -> float:
        """
        解析結果の信頼度スコアを計算（改善版）
        
        Args:
            text: OCRテキスト
            date: 抽出された日付
            store_name: 抽出された店舗名
            total_amount: 抽出された金額
            
        Returns:
            float: 信頼度スコア（0.0-1.0）
        """
        score = 0.0
        total_checks = 0
        
        # 日付の存在
        if date:
            score += 1.0
        total_checks += 1
        
        # 店舗名の存在
        if store_name and store_name != '不明':
            score += 1.0
        total_checks += 1
        
        # 金額の存在
        if total_amount:
            score += 1.0
        total_checks += 1
        
        # レシート番号の存在
        if self._extract_receipt_number(text):
            score += 0.5
        total_checks += 1
        
        # 商品明細の存在
        items = self._extract_items_enhanced(text)
        if items:
            score += 0.5
            # 商品明細の詳細度によるボーナス
            if len(items) >= 3:
                score += 0.2
        total_checks += 1
        
        # テキストの長さ（短すぎる場合は信頼度を下げる）
        if len(text) < 50:
            score -= 0.5
        elif len(text) > 500:
            score += 0.2
        total_checks += 1
        
        # テキスト品質スコア
        quality_score = self._calculate_text_quality_score(text)
        score += quality_score * 0.3
        total_checks += 1
        
        return max(0.0, min(1.0, score / total_checks))
    
    def _generate_processing_notes(self, text: str, date: datetime, 
                                 store_name: str, total_amount: float) -> str:
        """
        処理メモを生成
        
        Args:
            text: OCRテキスト
            date: 抽出された日付
            store_name: 抽出された店舗名
            total_amount: 抽出された金額
            
        Returns:
            str: 処理メモ
        """
        notes = []
        
        if not date:
            notes.append("日付の抽出に失敗")
        
        if not store_name or store_name == '不明':
            notes.append("店舗名の抽出に失敗")
        
        if not total_amount:
            notes.append("金額の抽出に失敗")
        
        # テキストの長さチェック
        if len(text) < 50:
            notes.append("テキストが短すぎる可能性")
        
        # 特殊文字のチェック
        if re.search(r'[^\w\s\.,\-\(\)￥¥]', text):
            notes.append("特殊文字が含まれている")
        
        if notes:
            return "; ".join(notes)
        else:
            return "正常に解析完了"
    
    def _create_fallback_data(self, ocr_text: str, file_path: str = None) -> Dict[str, Any]:
        """
        フォールバックデータを作成
        
        Args:
            ocr_text: OCRテキスト
            file_path: ファイルパス
            
        Returns:
            Dict[str, Any]: フォールバックデータ
        """
        return {
            'date': None,
            'store_name': '不明',
            'total_amount': None,
            'amount_without_tax': None,
            'tax_amount': None,
            'payment_method': 'その他',
            'items': [],
            'receipt_number': None,
            'cashier_info': None,
            'confidence_score': 0.0,
            'processing_notes': '解析に失敗しました。手動で確認してください。',
            'text_quality_score': 0.0,
            'extraction_metadata': self._generate_extraction_metadata(ocr_text),
            'category': '雑費',
            'account': 'その他販管費',
            'title': f"領収書_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'file_path': file_path
        }
    
    def analyze_text_patterns(self, text: str) -> Dict[str, Any]:
        """
        テキストパターンを分析して学習データを生成
        
        Args:
            text: OCRテキスト
            
        Returns:
            Dict[str, Any]: パターン分析結果
        """
        analysis = {
            'text_length': len(text),
            'line_count': len(text.split('\n')),
            'digit_patterns': self._analyze_digit_patterns(text),
            'date_patterns': self._analyze_date_patterns(text),
            'amount_patterns': self._analyze_amount_patterns(text),
            'store_patterns': self._analyze_store_patterns(text),
            'item_patterns': self._analyze_item_patterns(text),
            'confidence_factors': self._analyze_confidence_factors(text)
        }
        
        return analysis
    
    def _analyze_digit_patterns(self, text: str) -> Dict[str, Any]:
        """数字パターンを分析"""
        digits = re.findall(r'\d+', text)
        return {
            'total_digits': len(digits),
            'digit_groups': len(set(digits)),
            'common_lengths': self._get_common_lengths(digits),
            'amount_like_numbers': len([d for d in digits if len(d) >= 3 and len(d) <= 6])
        }
    
    def _analyze_date_patterns(self, text: str) -> Dict[str, Any]:
        """日付パターンを分析"""
        date_patterns = [
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{1,2}月\d{1,2}日',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}/\d{1,2}'
        ]
        
        found_patterns = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                found_patterns.append({
                    'pattern': pattern,
                    'count': len(matches),
                    'matches': matches
                })
        
        return {
            'total_dates': sum(p['count'] for p in found_patterns),
            'pattern_types': found_patterns
        }
    
    def _analyze_amount_patterns(self, text: str) -> Dict[str, Any]:
        """金額パターンを分析"""
        amount_patterns = [
            r'[0-9,]+円',
            r'[0-9,]+\s*円',
            r'合計[：:]\s*[0-9,]+',
            r'小計[：:]\s*[0-9,]+',
            r'税抜[：:]\s*[0-9,]+',
            r'税込[：:]\s*[0-9,]+'
        ]
        
        found_patterns = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            if matches:
                found_patterns.append({
                    'pattern': pattern,
                    'count': len(matches),
                    'matches': matches
                })
        
        return {
            'total_amounts': sum(p['count'] for p in found_patterns),
            'pattern_types': found_patterns
        }
    
    def _analyze_store_patterns(self, text: str) -> Dict[str, Any]:
        """店舗名パターンを分析"""
        store_indicators = [
            '店', '支店', '本店', '営業所', 'オフィス', '事務所',
            '株式会社', '有限会社', '合同会社', '店舗', '店名'
        ]
        
        found_indicators = []
        for indicator in store_indicators:
            if indicator in text:
                found_indicators.append(indicator)
        
        return {
            'total_indicators': len(found_indicators),
            'indicators': found_indicators
        }
    
    def _analyze_item_patterns(self, text: str) -> Dict[str, Any]:
        """商品明細パターンを分析"""
        lines = text.split('\n')
        item_like_lines = []
        
        for line in lines:
            # 商品らしい行の特徴をチェック
            if (len(line) > 5 and 
                re.search(r'\d+', line) and 
                not any(keyword in line for keyword in ['合計', '小計', '税抜', '税込'])):
                item_like_lines.append(line)
        
        return {
            'total_item_like_lines': len(item_like_lines),
            'sample_lines': item_like_lines[:5]  # 最初の5行をサンプルとして保存
        }
    
    def _analyze_confidence_factors(self, text: str) -> Dict[str, Any]:
        """信頼度要因を分析"""
        factors = {
            'has_date': bool(extract_date_from_text(text)),
            'has_store': bool(extract_store_name_from_text(text)),
            'has_amount': bool(extract_amount_from_text(text)),
            'has_items': len(self._extract_items_enhanced(text)) > 0,
            'text_length_appropriate': 100 <= len(text) <= 2000,
            'has_japanese': len(re.findall(r'[あ-んア-ン]', text)) >= 10,
            'has_digits': len(re.findall(r'\d', text)) >= 5
        }
        
        return factors
    
    def _get_common_lengths(self, items: List[str]) -> Dict[int, int]:
        """共通の長さを取得"""
        length_counts = {}
        for item in items:
            length = len(item)
            length_counts[length] = length_counts.get(length, 0) + 1
        return length_counts
    
    def get_learning_suggestions(self, text: str, parsed_data: Dict[str, Any]) -> List[str]:
        """
        学習提案を生成
        
        Args:
            text: OCRテキスト
            parsed_data: 解析結果
            
        Returns:
            List[str]: 学習提案のリスト
        """
        suggestions = []
        
        # 信頼度が低い場合の提案
        if parsed_data.get('confidence_score', 0) < 0.5:
            suggestions.append("信頼度が低いため、手動確認を推奨します")
        
        # 店舗名が不明の場合の提案
        if parsed_data.get('store_name') == '不明':
            suggestions.append("店舗名の抽出に失敗しました。OCR精度の向上が必要です")
        
        # 金額が抽出できない場合の提案
        if not parsed_data.get('total_amount'):
            suggestions.append("金額の抽出に失敗しました。金額表記のパターン学習が必要です")
        
        # 商品明細が少ない場合の提案
        if len(parsed_data.get('items', [])) < 2:
            suggestions.append("商品明細の抽出が不十分です。明細行のパターン学習が必要です")
        
        # テキスト品質が低い場合の提案
        if parsed_data.get('text_quality_score', 0) < 0.3:
            suggestions.append("テキスト品質が低いため、画像品質の向上を検討してください")
        
        return suggestions
    
    def validate_receipt_data(self, data: Dict[str, Any]) -> List[str]:
        """
        領収書データの妥当性を検証
        
        Args:
            data: 領収書データ
            
        Returns:
            List[str]: エラーメッセージのリスト
        """
        errors = []
        
        # 必須項目のチェック
        if not data.get('date'):
            errors.append("日付が設定されていません")
        
        if not data.get('store_name') or data['store_name'] == '不明':
            errors.append("店舗名が設定されていません")
        
        if not data.get('total_amount'):
            errors.append("合計金額が設定されていません")
        
        # 金額の妥当性チェック
        if data.get('total_amount') and data.get('amount_without_tax') and data.get('tax_amount'):
            calculated_total = data['amount_without_tax'] + data['tax_amount']
            if abs(calculated_total - data['total_amount']) > 1:  # 1円の誤差は許容
                errors.append("金額の整合性が取れていません")
        
        # 信頼度スコアのチェック
        if data.get('confidence_score', 0) < self.confidence_threshold:
            errors.append("解析信頼度が低いです")
        
        return errors
    
    def enhance_receipt_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        領収書データを補強・改善
        
        Args:
            data: 元の領収書データ
            
        Returns:
            Dict[str, Any]: 補強されたデータ
        """
        enhanced_data = data.copy()
        
        # 金額が不明な場合の推定
        if not enhanced_data.get('total_amount') and enhanced_data.get('items'):
            total = sum(item.get('total_price', 0) for item in enhanced_data['items'])
            if total > 0:
                enhanced_data['total_amount'] = total
                enhanced_data['processing_notes'] = (enhanced_data.get('processing_notes', '') + 
                                                   "; 金額を商品明細から推定")
        
        # 税抜金額の推定
        if enhanced_data.get('total_amount') and not enhanced_data.get('amount_without_tax'):
            # 10%の消費税と仮定
            estimated_tax = enhanced_data['total_amount'] * 0.1
            enhanced_data['amount_without_tax'] = enhanced_data['total_amount'] - estimated_tax
            enhanced_data['tax_amount'] = estimated_tax
            enhanced_data['processing_notes'] = (enhanced_data.get('processing_notes', '') + 
                                               "; 税抜金額を推定")
        
        # 店舗名の改善
        if enhanced_data.get('store_name') == '不明' and enhanced_data.get('items'):
            # 商品名から店舗を推定
            item_names = [item.get('name', '') for item in enhanced_data['items']]
            store_keywords = self._extract_store_keywords(item_names)
            if store_keywords:
                enhanced_data['store_name'] = store_keywords
                enhanced_data['processing_notes'] = (enhanced_data.get('processing_notes', '') + 
                                                   "; 店舗名を商品から推定")
        
        return enhanced_data
    
    def _extract_store_keywords(self, item_names: List[str]) -> Optional[str]:
        """
        商品名から店舗キーワードを抽出
        
        Args:
            item_names: 商品名のリスト
            
        Returns:
            Optional[str]: 店舗キーワード
        """
        # 商品名から店舗を推定するロジック
        store_keywords = {
            'マクドナルド': ['ハンバーガー', 'フライドポテト', 'マック'],
            'スターバックス': ['コーヒー', 'ラテ', 'フラペチーノ'],
            'セブンイレブン': ['おにぎり', 'サンドイッチ', 'コンビニ'],
            'ローソン': ['おにぎり', 'サンドイッチ', 'コンビニ'],
        }
        
        for store, keywords in store_keywords.items():
            for item_name in item_names:
                for keyword in keywords:
                    if keyword.lower() in item_name.lower():
                        return store
        
        return None
    
    def _calculate_text_quality_score(self, text: str) -> float:
        """テキスト品質スコアを計算"""
        score = 0.0
        
        # 文字数の適切性
        if 100 <= len(text) <= 2000:
            score += 0.3
        elif len(text) > 2000:
            score += 0.2
        
        # 改行数の適切性
        line_count = len(text.split('\n'))
        if 5 <= line_count <= 50:
            score += 0.3
        elif line_count > 50:
            score += 0.2
        
        # 数字の存在（金額や日付の可能性）
        digit_count = len(re.findall(r'\d', text))
        if digit_count >= 5:
            score += 0.2
        
        # 日本語文字の存在
        japanese_count = len(re.findall(r'[あ-んア-ン]', text))
        if japanese_count >= 10:
            score += 0.2
        
        return min(1.0, score)
    
    def _generate_extraction_metadata(self, text: str) -> Dict[str, Any]:
        """抽出メタデータを生成"""
        return {
            'text_length': len(text),
            'line_count': len(text.split('\n')),
            'digit_count': len(re.findall(r'\d', text)),
            'japanese_char_count': len(re.findall(r'[あ-んア-ン]', text)),
            'extraction_timestamp': datetime.now().isoformat(),
            'parser_version': '2.0'
        }
    
    def _get_category_and_account_enhanced(self, store_name: str, total_amount: float, 
                                         items: List[Dict[str, Any]]) -> Tuple[str, str]:
        """改善されたカテゴリと勘定科目の判定"""
        # 基本の判定を取得
        category, account = get_category_and_account(store_name)
        
        # 金額による補正
        if total_amount:
            if total_amount < 1000:
                # 小額の場合は雑費の可能性が高い
                if category == '雑費':
                    account = 'その他販管費'
            elif total_amount > 10000:
                # 高額の場合は経費の可能性が高い
                if category in ['雑費', 'その他']:
                    category = '経費'
                    account = 'その他販管費'
        
        # 商品明細による補正
        if items:
            # 食品系の商品が多い場合
            food_keywords = ['コーヒー', 'ランチ', '弁当', 'パン', '飲料', 'スナック']
            food_count = sum(1 for item in items if any(keyword in item['name'] for keyword in food_keywords))
            if food_count >= len(items) * 0.5:
                category = '食費'
                account = '福利厚生費'
            
            # 交通系の商品が多い場合
            transport_keywords = ['電車', 'バス', 'タクシー', '運賃', '切符']
            transport_count = sum(1 for item in items if any(keyword in item['name'] for keyword in transport_keywords))
            if transport_count >= len(items) * 0.5:
                category = '交通費'
                account = '旅費交通費'
        
        return category, account
    
    def _extract_receipt_number(self, text: str) -> Optional[str]:
        """
        レシート番号を抽出
        
        Args:
            text: OCRテキスト
            
        Returns:
            Optional[str]: レシート番号
        """
        # レシート番号のパターン
        patterns = [
            r'レシート[№No\.]*[：:]\s*([A-Z0-9\-]+)',
            r'伝票[№No\.]*[：:]\s*([A-Z0-9\-]+)',
            r'番号[：:]\s*([A-Z0-9\-]+)',
            r'No\.\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_cashier_info(self, text: str) -> Optional[str]:
        """
        レジ担当者情報を抽出
        
        Args:
            text: OCRテキスト
            
        Returns:
            Optional[str]: レジ担当者情報
        """
        # レジ担当者のパターン
        patterns = [
            r'担当[：:]\s*(.+)',
            r'レジ[：:]\s*(.+)',
            r'店員[：:]\s*(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return None
