"""
ユーティリティ関数のテスト
"""
import pytest
import sys
import os
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# receipt-processorディレクトリをPythonパスに追加
receipt_processor_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'receipt-processor')
sys.path.append(receipt_processor_path)

from utils import (
    extract_date_from_text,
    extract_amount_from_text,
    extract_store_name_from_text,
    generate_title,
    get_year_month_folder_path,
    validate_file_extension,
    sanitize_filename
)

class TestDateExtraction:
    """日付抽出のテスト"""
    
    def test_extract_date_standard_format(self):
        """標準的な日付形式のテスト"""
        text = "2024年1月15日 マクドナルド 合計: 1,200円"
        result = extract_date_from_text(text)
        assert result == datetime(2024, 1, 15)
    
    def test_extract_date_without_year(self):
        """年なしの日付形式のテスト"""
        text = "1月15日 スターバックス 合計: 500円"
        result = extract_date_from_text(text)
        current_year = datetime.now().year
        assert result == datetime(current_year, 1, 15)
    
    def test_extract_date_dash_format(self):
        """ハイフン区切りの日付形式のテスト"""
        text = "2024-01-15 セブンイレブン 合計: 300円"
        result = extract_date_from_text(text)
        assert result == datetime(2024, 1, 15)
    
    def test_extract_date_no_date(self):
        """日付がない場合のテスト"""
        text = "マクドナルド 合計: 1,200円"
        result = extract_date_from_text(text)
        assert result is None

class TestAmountExtraction:
    """金額抽出のテスト"""
    
    def test_extract_amount_standard_format(self):
        """標準的な金額形式のテスト"""
        text = "合計: 1,200円"
        result = extract_amount_from_text(text)
        assert result == 1200.0
    
    def test_extract_amount_with_colon(self):
        """コロン付きの金額形式のテスト"""
        text = "合計：1,200円"
        result = extract_amount_from_text(text)
        assert result == 1200.0
    
    def test_extract_amount_tax_included(self):
        """税込表示の金額形式のテスト"""
        text = "税込: 1,320円"
        result = extract_amount_from_text(text)
        assert result == 1320.0
    
    def test_extract_amount_yen_symbol(self):
        """円記号付きの金額形式のテスト"""
        text = "¥1,200"
        result = extract_amount_from_text(text)
        assert result == 1200.0
    
    def test_extract_amount_no_amount(self):
        """金額がない場合のテスト"""
        text = "マクドナルド 店舗情報"
        result = extract_amount_from_text(text)
        assert result is None

class TestStoreNameExtraction:
    """店舗名抽出のテスト"""
    
    def test_extract_store_name_simple(self):
        """シンプルな店舗名のテスト"""
        text = "マクドナルド\n2024年1月15日\n合計: 1,200円"
        result = extract_store_name_from_text(text)
        assert result == "マクドナルド"
    
    def test_extract_store_name_with_spaces(self):
        """スペース付きの店舗名のテスト"""
        text = "スターバックス コーヒー\n2024年1月15日\n合計: 500円"
        result = extract_store_name_from_text(text)
        assert result == "スターバックス コーヒー"
    
    def test_extract_store_name_no_store(self):
        """店舗名がない場合のテスト"""
        text = "2024年1月15日\n合計: 1,200円"
        result = extract_store_name_from_text(text)
        assert result is None

class TestTitleGeneration:
    """タイトル生成のテスト"""
    
    def test_generate_title_standard(self):
        """標準的なタイトル生成のテスト"""
        date = datetime(2024, 1, 15)
        store_name = "マクドナルド"
        result = generate_title(date, store_name)
        assert result == "2024-01-15_マクドナルド"
    
    def test_generate_title_with_special_chars(self):
        """特殊文字を含むタイトル生成のテスト"""
        date = datetime(2024, 1, 15)
        store_name = "スターバックス コーヒー"
        result = generate_title(date, store_name)
        assert result == "2024-01-15_スターバックス コーヒー"

class TestFolderPathGeneration:
    """フォルダパス生成のテスト"""
    
    def test_get_year_month_folder_path(self):
        """年度・月度フォルダパス生成のテスト"""
        date = datetime(2024, 1, 15)
        result = get_year_month_folder_path(date)
        assert result == "/2024/01/"
    
    def test_get_year_month_folder_path_single_digit(self):
        """1桁の月のフォルダパス生成のテスト"""
        date = datetime(2024, 3, 5)
        result = get_year_month_folder_path(date)
        assert result == "/2024/03/"

class TestFileValidation:
    """ファイル検証のテスト"""
    
    def test_validate_file_extension_valid(self):
        """有効なファイル拡張子のテスト"""
        filename = "receipt.jpg"
        supported_formats = ['.jpg', '.jpeg', '.png']
        result = validate_file_extension(filename, supported_formats)
        assert result is True
    
    def test_validate_file_extension_invalid(self):
        """無効なファイル拡張子のテスト"""
        filename = "receipt.txt"
        supported_formats = ['.jpg', '.jpeg', '.png']
        result = validate_file_extension(filename, supported_formats)
        assert result is False
    
    def test_validate_file_extension_case_insensitive(self):
        """大文字小文字を区別しないテスト"""
        filename = "receipt.JPG"
        supported_formats = ['.jpg', '.jpeg', '.png']
        result = validate_file_extension(filename, supported_formats)
        assert result is True

class TestFilenameSanitization:
    """ファイル名サニタイゼーションのテスト"""
    
    def test_sanitize_filename_simple(self):
        """シンプルなファイル名のサニタイゼーション"""
        filename = "receipt.jpg"
        result = sanitize_filename(filename)
        assert result == "receipt.jpg"
    
    def test_sanitize_filename_with_spaces(self):
        """スペースを含むファイル名のサニタイゼーション"""
        filename = "receipt file.jpg"
        result = sanitize_filename(filename)
        assert result == "receipt_file.jpg"
    
    def test_sanitize_filename_with_special_chars(self):
        """特殊文字を含むファイル名のサニタイゼーション"""
        filename = "receipt<file>.jpg"
        result = sanitize_filename(filename)
        assert result == "receipt_file_.jpg"
    
    def test_sanitize_filename_with_multiple_spaces(self):
        """複数のスペースを含むファイル名のサニタイゼーション"""
        filename = "receipt   file.jpg"
        result = sanitize_filename(filename)
        assert result == "receipt_file.jpg"
