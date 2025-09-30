# MovableType再構築システム設定ファイル

import os
from dotenv import load_dotenv
from pathlib import Path

# 1) スクリプト直下の .env 2) プロジェクト直下の .env を順に読み込む
current_dir = Path(__file__).resolve().parent
project_root = Path('/Users/takuhito/NotionWorkflowTools')

# .envファイルのパスをデバッグ出力
env_file_1 = current_dir / '.env'
env_file_2 = project_root / '.env'
print(f"DEBUG: Checking .env file 1: {env_file_1} (exists: {env_file_1.exists()})")
print(f"DEBUG: Checking .env file 2: {env_file_2} (exists: {env_file_2.exists()})")

# .envファイルを読み込む
if env_file_1.exists():
    print(f"DEBUG: Loading .env from {env_file_1}")
    load_dotenv(dotenv_path=env_file_1)
if env_file_2.exists():
    print(f"DEBUG: Loading .env from {env_file_2}")
    load_dotenv(dotenv_path=env_file_2, override=False)

# デバッグ: 環境変数の確認
print(f"DEBUG: MT_SITE_URL={os.getenv('MT_SITE_URL')}")
print(f"DEBUG: MT_USERNAME={os.getenv('MT_USERNAME')}")
print(f"DEBUG: MT_PASSWORD={'***' if os.getenv('MT_PASSWORD') else 'None'}")
print(f"DEBUG: MT_BLOG_ID={os.getenv('MT_BLOG_ID')}")
print(f"DEBUG: MT_SITE_NAME={os.getenv('MT_SITE_NAME')}")

# MovableType設定
MT_CONFIG = {
    'site_url': os.getenv('MT_SITE_URL'),
    'username': os.getenv('MT_USERNAME'),
    'password': os.getenv('MT_PASSWORD'),
    'blog_id': os.getenv('MT_BLOG_ID', '1'),  # 再構築対象のブログID
    'site_name': os.getenv('MT_SITE_NAME', 'MovableTypeサイト'),  # サイト名（通知用）
    'timeout': 300,  # 再構築タイムアウト（秒）
}

# 通知設定
NOTIFICATION_CONFIG = {
    'enabled': True,
    'methods': ['email'],  # 通知方法: 'email'
    
    # メール通知設定
    'email': {
        'enabled': True,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': os.getenv('EMAIL_USERNAME'),
        'password': os.getenv('EMAIL_PASSWORD'),
        'from_email': os.getenv('FROM_EMAIL'),
        'to_email': os.getenv('TO_EMAIL'),
        'use_tls': True,
    },
}

# ログ設定
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'file': 'logs/mt_rebuilder.log',
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
}

# 実行設定
EXECUTION_CONFIG = {
    'rebuild_interval_minutes': int(os.getenv('REBUILD_INTERVAL_MINUTES', 5)),
    'max_retry_count': int(os.getenv('MAX_RETRY_COUNT', 3)),
}
