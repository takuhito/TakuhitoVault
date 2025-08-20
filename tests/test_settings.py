"""
設定ファイルのテスト
"""
import pytest
import os
import tempfile
from unittest.mock import patch
import importlib

# プロジェクトルートをパスに追加
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSettingsValidation:
    """設定検証のテスト"""
    
    def test_validate_settings_all_valid(self):
        """全ての設定が有効な場合のテスト"""
        with patch.dict(os.environ, {
            'NOTION_TOKEN': 'test_token',
            'NOTION_DATABASE_ID': 'test_db_id',
            'GOOGLE_DRIVE_CREDENTIALS_FILE': 'test_credentials.json',
            'GOOGLE_CLOUD_PROJECT_ID': 'test_project',
            'GOOGLE_CLOUD_CREDENTIALS_FILE': 'test_vision_credentials.json'
        }):
            # 設定モジュールを再読み込み
            import config.settings
            importlib.reload(config.settings)
            errors = config.settings.validate_settings()
            assert len(errors) == 0
    
    def test_validate_settings_missing_all(self):
        """全ての設定が不足している場合のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            # 設定モジュールを再読み込み
            import config.settings
            importlib.reload(config.settings)
            errors = config.settings.validate_settings()
            assert len(errors) == 4  # NOTION_DATABASE_IDはデフォルト値があるため4つ
            assert "NOTION_TOKENが設定されていません" in errors
            assert "GOOGLE_DRIVE_CREDENTIALS_FILEが設定されていません" in errors
            assert "GOOGLE_CLOUD_PROJECT_IDが設定されていません" in errors
            assert "GOOGLE_CLOUD_CREDENTIALS_FILEが設定されていません" in errors
    
    def test_validate_settings_partial_missing(self):
        """一部の設定が不足している場合のテスト"""
        with patch.dict(os.environ, {
            'NOTION_TOKEN': 'test_token',
            'GOOGLE_DRIVE_CREDENTIALS_FILE': 'test_credentials.json'
        }):
            # 設定モジュールを再読み込み
            import config.settings
            importlib.reload(config.settings)
            errors = config.settings.validate_settings()
            assert len(errors) == 2  # NOTION_DATABASE_IDはデフォルト値があるため2つ
            assert "GOOGLE_CLOUD_PROJECT_IDが設定されていません" in errors
            assert "GOOGLE_CLOUD_CREDENTIALS_FILEが設定されていません" in errors

class TestPaymentMethods:
    """支払方法のテスト"""
    
    def test_payment_methods_contains_expected_values(self):
        """支払方法に期待される値が含まれているかのテスト"""
        from config.settings import PAYMENT_METHODS
        expected_methods = ['現金', 'クレジットカード', '電子マネー', 'その他']
        for method in expected_methods:
            assert method in PAYMENT_METHODS
    
    def test_payment_methods_no_duplicates(self):
        """支払方法に重複がないかのテスト"""
        from config.settings import PAYMENT_METHODS
        assert len(PAYMENT_METHODS) == len(set(PAYMENT_METHODS))

class TestCategories:
    """カテゴリのテスト"""
    
    def test_categories_contains_expected_values(self):
        """カテゴリに期待される値が含まれているかのテスト"""
        from config.settings import CATEGORIES
        expected_categories = [
            '食費', '交通費', '雑費', '光熱費', '通信費',
            '医療費', '教育費', '娯楽費', 'その他'
        ]
        for category in expected_categories:
            assert category in CATEGORIES
    
    def test_categories_no_duplicates(self):
        """カテゴリに重複がないかのテスト"""
        from config.settings import CATEGORIES
        assert len(CATEGORIES) == len(set(CATEGORIES))

class TestProcessingStatus:
    """処理状況のテスト"""
    
    def test_processing_status_contains_expected_values(self):
        """処理状況に期待される値が含まれているかのテスト"""
        from config.settings import PROCESSING_STATUS
        expected_statuses = ['未処理', '処理済み', 'エラー', '手動確認要']
        for status in expected_statuses:
            assert status in PROCESSING_STATUS
    
    def test_processing_status_no_duplicates(self):
        """処理状況に重複がないかのテスト"""
        from config.settings import PROCESSING_STATUS
        assert len(PROCESSING_STATUS) == len(set(PROCESSING_STATUS))

class TestAccountItems:
    """勘定科目のテスト"""
    
    def test_account_items_contains_expected_values(self):
        """勘定科目に期待される値が含まれているかのテスト"""
        from config.settings import ACCOUNT_ITEMS
        expected_accounts = [
            '現金', '普通預金', '売上', '販管費', 'その他販管費'
        ]
        for account in expected_accounts:
            assert account in ACCOUNT_ITEMS
    
    def test_account_items_no_duplicates(self):
        """勘定科目に重複がないかのテスト"""
        from config.settings import ACCOUNT_ITEMS
        assert len(ACCOUNT_ITEMS) == len(set(ACCOUNT_ITEMS))
    
    def test_account_items_contains_freee_accounts(self):
        """Freee準拠の勘定科目が含まれているかのテスト"""
        from config.settings import ACCOUNT_ITEMS
        # Freeeの主要な勘定科目をチェック
        freee_accounts = [
            '現金', '普通預金', '売上', '売上原価', '販管費',
            '人件費', '水道光熱費', '通信費', '旅費交通費'
        ]
        for account in freee_accounts:
            assert account in ACCOUNT_ITEMS
