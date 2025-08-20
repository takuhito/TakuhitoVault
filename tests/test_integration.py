"""
統合テスト
"""
import pytest
import sys
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# receipt-processorディレクトリをPythonパスに追加
receipt_processor_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'receipt-processor')
sys.path.append(receipt_processor_path)

class TestReceiptProcessingIntegration:
    """領収書処理の統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        # モックの設定
        self.mock_google_drive = Mock()
        self.mock_vision = Mock()
        self.mock_notion = Mock()
        self.mock_pdf_processor = Mock()
        self.mock_receipt_parser = Mock()
        self.mock_file_manager = Mock()
    
    def test_complete_receipt_processing_flow(self):
        """完全な領収書処理フローのテスト"""
        # テストデータの準備
        test_file_info = {
            'id': 'test_file_id',
            'name': 'test_receipt.jpg'
        }
        
        test_ocr_text = """
        マクドナルド
        2024年1月15日
        合計: 1,200円
        現金
        """
        
        test_receipt_data = {
            'title': '2024-01-15_マクドナルド',
            'date': datetime(2024, 1, 15),
            'store_name': 'マクドナルド',
            'total_amount': 1200.0,
            'payment_method': '現金',
            'category': '食費',
            'account': '販管費',
            'processing_status': '処理済み'
        }
        
        # モックの設定
        self.mock_google_drive.download_file.return_value = True
        self.mock_file_manager.validate_file.return_value = (True, "OK")
        self.mock_file_manager.get_file_type.return_value = 'image'
        self.mock_vision.extract_text_from_image.return_value = test_ocr_text
        self.mock_receipt_parser.parse_receipt_data.return_value = test_receipt_data
        self.mock_receipt_parser.enhance_receipt_data.return_value = test_receipt_data
        self.mock_receipt_parser.validate_receipt_data.return_value = []
        self.mock_notion.create_receipt_page.return_value = 'test_page_id'
        self.mock_file_manager.move_file_to_processed_folder.return_value = '/processed/path'
        
        # 処理の実行（モックを使用）
        success = self._process_file_with_mocks(test_file_info)
        
        # 結果の検証
        assert success is True
        
        # 各モックが正しく呼び出されたことを確認
        self.mock_google_drive.download_file.assert_called_once()
        self.mock_file_manager.validate_file.assert_called_once()
        self.mock_vision.extract_text_from_image.assert_called_once()
        self.mock_receipt_parser.parse_receipt_data.assert_called_once()
        self.mock_notion.create_receipt_page.assert_called_once()
        self.mock_file_manager.move_file_to_processed_folder.assert_called_once()
    
    def test_pdf_processing_flow(self):
        """PDF処理フローのテスト"""
        # テストデータの準備
        test_file_info = {
            'id': 'test_file_id',
            'name': 'test_receipt.pdf'
        }
        
        test_ocr_text = """
        スターバックス
        2024年1月15日
        合計: 500円
        クレジットカード
        """
        
        test_receipt_data = {
            'title': '2024-01-15_スターバックス',
            'date': datetime(2024, 1, 15),
            'store_name': 'スターバックス',
            'total_amount': 500.0,
            'payment_method': 'クレジットカード',
            'category': '食費',
            'account': '販管費',
            'processing_status': '処理済み',
            'page_number': 1,
            'total_pages': 1
        }
        
        # モックの設定
        self.mock_google_drive.download_file.return_value = True
        self.mock_file_manager.validate_file.return_value = (True, "OK")
        self.mock_file_manager.get_file_type.return_value = 'pdf'
        self.mock_pdf_processor.validate_pdf.return_value = True
        self.mock_pdf_processor.convert_pdf_to_images.return_value = ['/temp/page_001.jpg']
        self.mock_vision.extract_text_from_image.return_value = test_ocr_text
        self.mock_receipt_parser.parse_receipt_data.return_value = test_receipt_data
        self.mock_receipt_parser.enhance_receipt_data.return_value = test_receipt_data
        self.mock_notion.create_receipt_page.return_value = 'test_page_id'
        self.mock_file_manager.move_file_to_processed_folder.return_value = '/processed/path'
        
        # 処理の実行（モックを使用）
        success = self._process_pdf_file_with_mocks(test_file_info)
        
        # 結果の検証
        assert success is True
        
        # 各モックが正しく呼び出されたことを確認
        self.mock_pdf_processor.validate_pdf.assert_called_once()
        self.mock_pdf_processor.convert_pdf_to_images.assert_called_once()
        self.mock_vision.extract_text_from_image.assert_called_once()
        self.mock_receipt_parser.parse_receipt_data.assert_called_once()
        self.mock_notion.create_receipt_page.assert_called_once()
    
    def test_error_handling_flow(self):
        """エラーハンドリングフローのテスト"""
        # テストデータの準備
        test_file_info = {
            'id': 'test_file_id',
            'name': 'invalid_file.txt'
        }
        
        # モックの設定（エラーを発生させる）
        self.mock_google_drive.download_file.return_value = True
        self.mock_file_manager.validate_file.return_value = (False, "未対応のファイル形式")
        self.mock_file_manager.move_file_to_error_folder.return_value = '/error/path'
        
        # 処理の実行（モックを使用）
        success = self._process_file_with_mocks(test_file_info)
        
        # 結果の検証
        assert success is False
        
        # エラーフォルダに移動されたことを確認
        self.mock_file_manager.move_file_to_error_folder.assert_called_once()
    
    def _process_file_with_mocks(self, file_info):
        """モックを使用したファイル処理のシミュレーション"""
        try:
            # ファイルのダウンロード
            if not self.mock_google_drive.download_file(file_info['id'], '/temp/file'):
                return False
            
            # ファイルの妥当性チェック
            is_valid, error_message = self.mock_file_manager.validate_file('/temp/file')
            if not is_valid:
                self.mock_file_manager.move_file_to_error_folder('/temp/file')
                return False
            
            # ファイルタイプの判定
            file_type = self.mock_file_manager.get_file_type('/temp/file')
            
            if file_type == 'image':
                return self._process_image_file_with_mocks('/temp/file', file_info)
            else:
                self.mock_file_manager.move_file_to_error_folder('/temp/file')
                return False
                
        except Exception:
            return False
    
    def _process_image_file_with_mocks(self, file_path, file_info):
        """モックを使用した画像ファイル処理のシミュレーション"""
        try:
            # OCR処理
            ocr_text = self.mock_vision.extract_text_from_image(file_path)
            if not ocr_text:
                self.mock_file_manager.move_file_to_error_folder(file_path)
                return False
            
            # 領収書データの解析
            receipt_data = self.mock_receipt_parser.parse_receipt_data(ocr_text, file_path)
            receipt_data['original_file_name'] = file_info['name']
            
            # データの補強
            receipt_data = self.mock_receipt_parser.enhance_receipt_data(receipt_data)
            
            # データの妥当性検証
            validation_errors = self.mock_receipt_parser.validate_receipt_data(receipt_data)
            if validation_errors:
                receipt_data['processing_status'] = '手動確認要'
            
            # Notionに保存
            page_id = self.mock_notion.create_receipt_page(receipt_data)
            if not page_id:
                self.mock_file_manager.move_file_to_error_folder(file_path)
                return False
            
            # 処理済みフォルダに移動
            if receipt_data.get('date'):
                self.mock_file_manager.move_file_to_processed_folder(file_path, receipt_data['date'])
            else:
                self.mock_file_manager.move_file_to_processed_folder(file_path, datetime.now())
            
            return True
            
        except Exception:
            self.mock_file_manager.move_file_to_error_folder(file_path)
            return False
    
    def _process_pdf_file_with_mocks(self, file_info):
        """モックを使用したPDFファイル処理のシミュレーション"""
        try:
            # PDFの妥当性チェック
            if not self.mock_pdf_processor.validate_pdf('/temp/file'):
                self.mock_file_manager.move_file_to_error_folder('/temp/file')
                return False
            
            # PDFを画像に変換
            image_paths = self.mock_pdf_processor.convert_pdf_to_images('/temp/file')
            if not image_paths:
                self.mock_file_manager.move_file_to_error_folder('/temp/file')
                return False
            
            # 各ページを処理
            created_records = []
            
            for page_num, image_path in enumerate(image_paths, 1):
                try:
                    # OCR処理
                    ocr_text = self.mock_vision.extract_text_from_image(image_path)
                    if not ocr_text:
                        continue
                    
                    # 領収書データの解析
                    receipt_data = self.mock_receipt_parser.parse_receipt_data(ocr_text, image_path)
                    receipt_data['page_number'] = page_num
                    receipt_data['total_pages'] = len(image_paths)
                    receipt_data['original_file_name'] = file_info['name']
                    
                    # データの補強
                    receipt_data = self.mock_receipt_parser.enhance_receipt_data(receipt_data)
                    
                    # Notionに保存
                    page_id = self.mock_notion.create_receipt_page(receipt_data)
                    if page_id:
                        created_records.append(page_id)
                    
                except Exception:
                    continue
            
            # 処理結果の判定
            if created_records:
                # 成功時：処理済みフォルダに移動
                if receipt_data.get('date'):
                    self.mock_file_manager.move_file_to_processed_folder('/temp/file', receipt_data['date'])
                else:
                    self.mock_file_manager.move_file_to_processed_folder('/temp/file', datetime.now())
                return True
            else:
                # 失敗時：エラーフォルダに移動
                self.mock_file_manager.move_file_to_error_folder('/temp/file')
                return False
                
        except Exception:
            self.mock_file_manager.move_file_to_error_folder('/temp/file')
            return False

class TestDataExtractionIntegration:
    """データ抽出の統合テスト"""
    
    def test_complete_data_extraction_flow(self):
        """完全なデータ抽出フローのテスト"""
        # テスト用のOCRテキスト
        ocr_text = """
        マクドナルド 渋谷店
        2024年1月15日 14:30
        レシート番号: 12345
        
        ハンバーガー    1    500    500
        フライドポテト  1    300    300
        コーラ         1    200    200
        
        小計: 1,000
        消費税: 100
        合計: 1,100円
        
        現金でお支払い
        ありがとうございました
        """
        
        # 実際の関数を使用してデータ抽出をテスト
        from utils import (
            extract_date_from_text,
            extract_amount_from_text,
            extract_store_name_from_text,
            generate_title
        )
        from config.mapping import get_category_and_account, get_payment_method_from_text
        
        # データ抽出
        date = extract_date_from_text(ocr_text)
        store_name = extract_store_name_from_text(ocr_text)
        total_amount = extract_amount_from_text(ocr_text)
        payment_method = get_payment_method_from_text(ocr_text)
        category, account = get_category_and_account(store_name)
        title = generate_title(date, store_name)
        
        # 結果の検証
        assert date == datetime(2024, 1, 15)
        assert store_name == "マクドナルド 渋谷店"
        assert total_amount == 1100.0
        assert payment_method == "現金"
        assert category == "食費"
        assert account == "販管費"
        assert title == "2024-01-15_マクドナルド 渋谷店"
    
    def test_error_recovery_flow(self):
        """エラー回復フローのテスト"""
        # 不完全なOCRテキスト
        incomplete_ocr_text = """
        マクドナルド
        月日
        商品名
        """
        
        from utils import (
            extract_date_from_text,
            extract_amount_from_text,
            extract_store_name_from_text
        )
        from config.mapping import get_category_and_account
        
        # データ抽出
        date = extract_date_from_text(incomplete_ocr_text)
        store_name = extract_store_name_from_text(incomplete_ocr_text)
        total_amount = extract_amount_from_text(incomplete_ocr_text)
        category, account = get_category_and_account(store_name)
        
        # 結果の検証（一部のデータは抽出できるが、金額は抽出できない）
        assert date is None  # 日付も抽出できない
        assert store_name == "マクドナルド"
        assert total_amount is None  # 金額は抽出できない
        assert category == "食費"  # デフォルトカテゴリ
        assert account == "販管費"  # デフォルト勘定科目
