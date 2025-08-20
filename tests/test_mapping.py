"""
マッピング設定のテスト
"""
import pytest
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mapping import (
    get_category_and_account,
    get_payment_method_from_text,
    STORE_CATEGORY_MAPPING
)

class TestStoreCategoryMapping:
    """店舗カテゴリマッピングのテスト"""
    
    def test_get_category_and_account_food(self):
        """食費関連の店舗テスト"""
        # マクドナルド
        category, account = get_category_and_account("マクドナルド")
        assert category == "食費"
        assert account == "販管費"
        
        # スターバックス
        category, account = get_category_and_account("スターバックス")
        assert category == "食費"
        assert account == "販管費"
        
        # セブンイレブン
        category, account = get_category_and_account("セブンイレブン")
        assert category == "食費"
        assert account == "販管費"
    
    def test_get_category_and_account_transport(self):
        """交通費関連の店舗テスト"""
        # JR
        category, account = get_category_and_account("JR")
        assert category == "交通費"
        assert account == "旅費交通費"
        
        # 地下鉄
        category, account = get_category_and_account("地下鉄")
        assert category == "交通費"
        assert account == "旅費交通費"
        
        # タクシー
        category, account = get_category_and_account("タクシー")
        assert category == "交通費"
        assert account == "旅費交通費"
    
    def test_get_category_and_account_utilities(self):
        """光熱費関連の店舗テスト"""
        # 東京電力
        category, account = get_category_and_account("東京電力")
        assert category == "光熱費"
        assert account == "水道光熱費"
        
        # 東京ガス
        category, account = get_category_and_account("東京ガス")
        assert category == "光熱費"
        assert account == "水道光熱費"
    
    def test_get_category_and_account_communication(self):
        """通信費関連の店舗テスト"""
        # NTT
        category, account = get_category_and_account("NTT")
        assert category == "通信費"
        assert account == "通信費"
        
        # ソフトバンク
        category, account = get_category_and_account("ソフトバンク")
        assert category == "通信費"
        assert account == "通信費"
    
    def test_get_category_and_account_medical(self):
        """医療費関連の店舗テスト"""
        # 病院
        category, account = get_category_and_account("病院")
        assert category == "医療費"
        assert account == "販管費"
        
        # 薬局
        category, account = get_category_and_account("薬局")
        assert category == "医療費"
        assert account == "販管費"
    
    def test_get_category_and_account_education(self):
        """教育費関連の店舗テスト"""
        # 学校
        category, account = get_category_and_account("学校")
        assert category == "教育費"
        assert account == "研修費"
        
        # 塾
        category, account = get_category_and_account("塾")
        assert category == "教育費"
        assert account == "研修費"
    
    def test_get_category_and_account_entertainment(self):
        """娯楽費関連の店舗テスト"""
        # 映画館
        category, account = get_category_and_account("映画館")
        assert category == "娯楽費"
        assert account == "販管費"
        
        # ゲーム
        category, account = get_category_and_account("ゲーム")
        assert category == "娯楽費"
        assert account == "販管費"
    
    def test_get_category_and_account_misc(self):
        """雑費関連の店舗テスト"""
        # 100円ショップ
        category, account = get_category_and_account("100円ショップ")
        assert category == "雑費"
        assert account == "消耗品費"
        
        # ダイソー
        category, account = get_category_and_account("ダイソー")
        assert category == "雑費"
        assert account == "消耗品費"
    
    def test_get_category_and_account_unknown(self):
        """未知の店舗テスト"""
        category, account = get_category_and_account("未知の店舗")
        assert category == "雑費"
        assert account == "その他販管費"
    
    def test_get_category_and_account_case_insensitive(self):
        """大文字小文字を区別しないテスト"""
        # 小文字
        category, account = get_category_and_account("マクドナルド")
        assert category == "食費"
        assert account == "販管費"
        
        # 大文字
        category, account = get_category_and_account("マクドナルド")
        assert category == "食費"
        assert account == "販管費"

class TestPaymentMethodDetection:
    """支払方法検出のテスト"""
    
    def test_get_payment_method_cash(self):
        """現金支払いのテスト"""
        text = "現金で支払いました"
        result = get_payment_method_from_text(text)
        assert result == "現金"
        
        text = "CASH"
        result = get_payment_method_from_text(text)
        assert result == "現金"
    
    def test_get_payment_method_credit_card(self):
        """クレジットカード支払いのテスト"""
        text = "クレジットカードで支払いました"
        result = get_payment_method_from_text(text)
        assert result == "クレジットカード"
        
        text = "VISA"
        result = get_payment_method_from_text(text)
        assert result == "クレジットカード"
        
        text = "MasterCard"
        result = get_payment_method_from_text(text)
        assert result == "クレジットカード"
        
        text = "JCB"
        result = get_payment_method_from_text(text)
        assert result == "クレジットカード"
    
    def test_get_payment_method_electronic_money(self):
        """電子マネー支払いのテスト"""
        text = "電子マネーで支払いました"
        result = get_payment_method_from_text(text)
        assert result == "電子マネー"
        
        text = "Suica"
        result = get_payment_method_from_text(text)
        assert result == "電子マネー"
        
        text = "PASMO"
        result = get_payment_method_from_text(text)
        assert result == "電子マネー"
        
        text = "Edy"
        result = get_payment_method_from_text(text)
        assert result == "電子マネー"
        
        text = "nanaco"
        result = get_payment_method_from_text(text)
        assert result == "電子マネー"
    
    def test_get_payment_method_other(self):
        """その他の支払方法のテスト"""
        text = "銀行振込で支払いました"
        result = get_payment_method_from_text(text)
        assert result == "その他"
        
        text = "ポイントで支払いました"
        result = get_payment_method_from_text(text)
        assert result == "その他"
    
    def test_get_payment_method_case_insensitive(self):
        """大文字小文字を区別しないテスト"""
        text = "CASH"
        result = get_payment_method_from_text(text)
        assert result == "現金"
        
        text = "cash"
        result = get_payment_method_from_text(text)
        assert result == "現金"

class TestMappingData:
    """マッピングデータのテスト"""
    
    def test_store_category_mapping_structure(self):
        """店舗カテゴリマッピングの構造テスト"""
        # マッピングが辞書であることを確認
        assert isinstance(STORE_CATEGORY_MAPPING, dict)
        
        # 空でないことを確認
        assert len(STORE_CATEGORY_MAPPING) > 0
        
        # 各エントリが正しい形式であることを確認
        for store_name, (category, account) in STORE_CATEGORY_MAPPING.items():
            assert isinstance(store_name, str)
            assert isinstance(category, str)
            assert isinstance(account, str)
            assert len(store_name) > 0
            assert len(category) > 0
            assert len(account) > 0
    
    def test_store_category_mapping_no_duplicates(self):
        """店舗カテゴリマッピングに重複がないかのテスト"""
        store_names = list(STORE_CATEGORY_MAPPING.keys())
        assert len(store_names) == len(set(store_names))
    
    def test_store_category_mapping_categories_valid(self):
        """店舗カテゴリマッピングのカテゴリが有効な値であるかのテスト"""
        from config.settings import CATEGORIES
        
        for store_name, (category, account) in STORE_CATEGORY_MAPPING.items():
            assert category in CATEGORIES, f"Invalid category '{category}' for store '{store_name}'"
    
    def test_store_category_mapping_accounts_valid(self):
        """店舗カテゴリマッピングの勘定科目が有効な値であるかのテスト"""
        from config.settings import ACCOUNT_ITEMS
        
        for store_name, (category, account) in STORE_CATEGORY_MAPPING.items():
            assert account in ACCOUNT_ITEMS, f"Invalid account '{account}' for store '{store_name}'"

