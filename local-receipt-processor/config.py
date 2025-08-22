"""
ローカル環境用の設定ファイル
"""

import os
from typing import List

# 環境変数の読み込み
def load_env_from_file():
    """環境変数ファイルから読み込み"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# 環境変数を読み込み
load_env_from_file()

# Notion設定
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID', '254b061dadf38042813eeab350aea734')

# Google Drive設定
GOOGLE_DRIVE_CREDENTIALS_FILE = os.getenv('GOOGLE_DRIVE_CREDENTIALS_FILE', '../credentials/service-account.json')
GOOGLE_DRIVE_MONITOR_FOLDER = os.getenv('GOOGLE_DRIVE_MONITOR_FOLDER', '1YccjjOWIp4PAQVUY8SVcSvUvkcQ6lo3B')
GOOGLE_DRIVE_PROCESSED_BASE = os.getenv('GOOGLE_DRIVE_PROCESSED_BASE', '0AJojvkLIwToKUk9PVA')
GOOGLE_DRIVE_ERROR_FOLDER = os.getenv('GOOGLE_DRIVE_ERROR_FOLDER', '1HJrzj1DDoiTmIkNa8tIN3RKnLKs_8Kaf')
GOOGLE_DRIVE_SHARED_DRIVE_ID = os.getenv('GOOGLE_DRIVE_SHARED_DRIVE_ID', '0AJojvkLIwToKUk9PVA')

# Gemini設定
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# ログ設定
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'receipt_processor.log')

# ファイル処理設定
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '10485760'))  # 10MB
SUPPORTED_IMAGE_FORMATS = os.getenv('SUPPORTED_IMAGE_FORMATS', '.jpg,.jpeg,.png').split(',')
SUPPORTED_PDF_FORMATS = os.getenv('SUPPORTED_PDF_FORMATS', '.pdf').split(',')

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

def validate_settings() -> List[str]:
    """設定の検証"""
    errors = []
    
    if not NOTION_TOKEN:
        errors.append("NOTION_TOKENが設定されていません")
    
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEYが設定されていません")
    
    if not os.path.exists(GOOGLE_DRIVE_CREDENTIALS_FILE):
        errors.append(f"Google Drive認証ファイルが見つかりません: {GOOGLE_DRIVE_CREDENTIALS_FILE}")
    
    return errors
