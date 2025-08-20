"""
領収書自動処理システム 設定ファイル
"""
import os
from typing import List
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Notion設定
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID', '254b061dadf38042813eeab350aea734')

# Google Drive設定（共有ドライブ対応）
GOOGLE_DRIVE_CREDENTIALS_FILE = os.getenv('GOOGLE_DRIVE_CREDENTIALS_FILE')
GOOGLE_DRIVE_TOKEN_FILE = os.getenv('GOOGLE_DRIVE_TOKEN_FILE')
GOOGLE_DRIVE_MONITOR_FOLDER = os.getenv('GOOGLE_DRIVE_MONITOR_FOLDER', '/領収書管理/受信箱/')
GOOGLE_DRIVE_PROCESSED_BASE = os.getenv('GOOGLE_DRIVE_PROCESSED_BASE', '/領収書管理/')
GOOGLE_DRIVE_ERROR_FOLDER = os.getenv('GOOGLE_DRIVE_ERROR_FOLDER', '/領収書管理/エラー/')
GOOGLE_DRIVE_SHARED_DRIVE_ID = os.getenv('GOOGLE_DRIVE_SHARED_DRIVE_ID')

# Google Cloud Vision設定
GOOGLE_CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
GOOGLE_CLOUD_CREDENTIALS_FILE = os.getenv('GOOGLE_CLOUD_CREDENTIALS_FILE')

# Gemini設定
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# ファイル処理設定
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '10485760'))  # 10MB
MAX_PDF_PAGES = int(os.getenv('MAX_PDF_PAGES', '20'))
SUPPORTED_IMAGE_FORMATS = os.getenv('SUPPORTED_IMAGE_FORMATS', '.jpg,.jpeg,.png').split(',')
SUPPORTED_PDF_FORMATS = os.getenv('SUPPORTED_PDF_FORMATS', '.pdf').split(',')

# ログ設定
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'receipt_processor.log')

# 支払方法オプション
PAYMENT_METHODS = [
    '現金',
    'クレジットカード',
    '電子マネー',
    'その他'
]

# カテゴリオプション
CATEGORIES = [
    '食費',
    '交通費',
    '雑費',
    '光熱費',
    '通信費',
    '医療費',
    '教育費',
    '娯楽費',
    'その他'
]

# 処理状況オプション
PROCESSING_STATUS = [
    '未処理',
    '処理済み',
    'エラー',
    '手動確認要'
]

# Freee準拠勘定科目
ACCOUNT_ITEMS = [
    '現金',
    '普通預金',
    '当座預金',
    '定期預金',
    '売掛金',
    '買掛金',
    '前払金',
    '前受金',
    '仮払金',
    '仮受金',
    '立替金',
    '預り金',
    '未払金',
    '未収金',
    '売上',
    '売上原価',
    '売上総利益',
    '販管費',
    '人件費',
    '給料手当',
    '法定福利費',
    '福利厚生費',
    '外注費',
    '地代家賃',
    '水道光熱費',
    '通信費',
    '旅費交通費',
    '車両費',
    '修繕費',
    '消耗品費',
    '事務用品費',
    '広告宣伝費',
    '接待交際費',
    '会議費',
    '研修費',
    '保険料',
    '租税公課',
    '減価償却費',
    'その他販管費',
    '営業外収益',
    '営業外費用',
    '特別利益',
    '特別損失',
    '法人税等'
]

def validate_settings() -> List[str]:
    """設定の妥当性を検証し、エラーメッセージのリストを返す"""
    errors = []
    
    if not NOTION_TOKEN:
        errors.append("NOTION_TOKENが設定されていません")
    
    if not NOTION_DATABASE_ID:
        errors.append("NOTION_DATABASE_IDが設定されていません")
    
    if not GOOGLE_DRIVE_CREDENTIALS_FILE:
        errors.append("GOOGLE_DRIVE_CREDENTIALS_FILEが設定されていません")
    
    if not GOOGLE_CLOUD_PROJECT_ID:
        errors.append("GOOGLE_CLOUD_PROJECT_IDが設定されていません")
    
    if not GOOGLE_CLOUD_CREDENTIALS_FILE:
        errors.append("GOOGLE_CLOUD_CREDENTIALS_FILEが設定されていません")
    
    return errors
