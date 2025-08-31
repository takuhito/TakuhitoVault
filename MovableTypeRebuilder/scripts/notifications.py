#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知管理モジュール
メール通知を統合管理します。
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# 設定ファイルのインポート
try:
    from config import NOTIFICATION_CONFIG
except ImportError:
    NOTIFICATION_CONFIG = {}

class NotificationManager:
    """通知管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.config = NOTIFICATION_CONFIG
    
    def send_email(self, message: str, subject: Optional[str] = None) -> bool:
        """メール通知の送信（ローカル版用）"""
        if not self.config.get('email', {}).get('enabled', False):
            self.logger.debug("メール通知が無効です")
            return False
        
        try:
            email_config = self.config['email']
            
            # メールの作成
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = subject or "[ローカル版] MovableType再構築通知"
            
            # 本文の追加
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # SMTPサーバーへの接続と送信
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            
            if email_config.get('use_tls', False):
                server.starttls()
            
            # 認証
            server.login(email_config['username'], email_config['password'])
            
            # 送信
            text = msg.as_string()
            server.sendmail(email_config['from_email'], email_config['to_email'], text)
            server.quit()
            
            self.logger.info("メール通知を送信しました")
            return True
            
        except Exception as e:
            self.logger.error(f"メール通知の送信に失敗: {e}")
            return False
    
    def send_email_github_action(self, message: str, subject: Optional[str] = None) -> bool:
        """メール通知の送信（GitHub Actions版用）"""
        if not self.config.get('email', {}).get('enabled', False):
            self.logger.debug("メール通知が無効です")
            return False
        
        try:
            email_config = self.config['email']
            
            # メールの作成
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = subject or "[GitHub Actions] MovableType再構築通知"
            
            # 本文の追加
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # SMTPサーバーへの接続と送信
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            
            if email_config.get('use_tls', False):
                server.starttls()
            
            # 認証
            server.login(email_config['username'], email_config['password'])
            
            # 送信
            text = msg.as_string()
            server.sendmail(email_config['from_email'], email_config['to_email'], text)
            server.quit()
            
            self.logger.info("GitHub Actions版メール通知を送信しました")
            return True
            
        except Exception as e:
            self.logger.error(f"GitHub Actions版メール通知の送信に失敗: {e}")
            return False
