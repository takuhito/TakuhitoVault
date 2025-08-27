# HETEMLサーバ監視システム設定ファイル
# このファイルを config.py にコピーして編集してください

import os
from dotenv import load_dotenv

load_dotenv()

# HETEMLサーバ接続設定
HETEML_CONFIG = {
    'hostname': 'ssh-nbsorjp.heteml.net',  # HETEMLサーバのホスト名
    'port': 2222,                           # SSHポート（HETEMLは通常2222）
    'username': 'nbsorjp',                  # SSHユーザー名
    'password': os.getenv('HETEML_PASSWORD'),  # SSHパスワード（環境変数から取得）
    'key_filename': None,                 # SSH秘密鍵ファイルパス（使用する場合）
    'timeout': 30,                        # 接続タイムアウト（秒）
}

# 監視設定
MONITOR_CONFIG = {
    'target_path': '/home/users/0/nbsorjp/web/domain/nbspress.com/nbs.or.jp/stages/',  # 監視対象フォルダパス
    'check_interval': 300,                # 監視間隔（秒）
    'file_pattern': '*',                  # 監視するファイルパターン
    'exclude_patterns': ['.*', '*.tmp'],  # 除外するファイルパターン
}

# 通知設定
NOTIFICATION_CONFIG = {
    'enabled': True,
    'methods': ['email', 'slack'],        # 通知方法: 'email', 'slack', 'line'
    
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
    
    # Slack通知設定
    'slack': {
        'enabled': True,
        'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
        'channel': '#notifications',
    },
    
    # LINE通知設定
    'line': {
        'enabled': False,
        'channel_access_token': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
        'user_id': os.getenv('LINE_USER_ID'),
    },
}

# ログ設定
LOG_CONFIG = {
    'level': 'INFO',
    'file': 'heteml_monitor.log',
    'max_size': 10 * 1024 * 1024,        # 10MB
    'backup_count': 5,
}

# データベース設定（ファイル変更履歴保存用）
DB_CONFIG = {
    'enabled': True,
    'file': 'file_history.json',
}
