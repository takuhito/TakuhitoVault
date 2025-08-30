#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知管理モジュール
メール、Slack、LINE通知を統合管理します。
"""

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import requests

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
            msg['Subject'] = subject or "HETEMLサーバ監視通知"
            
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
            msg['Subject'] = subject or "[GitHub Actions] HETEMLサーバ監視通知"
            
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
    
    def send_slack(self, message: str) -> bool:
        """Slack通知の送信"""
        if not self.config.get('slack', {}).get('enabled', False):
            self.logger.debug("Slack通知が無効です")
            return False
        
        try:
            slack_config = self.config['slack']
            webhook_url = slack_config['webhook_url']
            
            # Slackメッセージの作成
            slack_message = {
                "text": message,
                "channel": slack_config.get('channel', '#general')
            }
            
            # Webhookで送信
            response = requests.post(webhook_url, json=slack_message)
            response.raise_for_status()
            
            self.logger.info("Slack通知を送信しました")
            return True
            
        except Exception as e:
            self.logger.error(f"Slack通知の送信に失敗: {e}")
            return False
    
    def send_line(self, message: str) -> bool:
        """LINE通知の送信"""
        if not self.config.get('line', {}).get('enabled', False):
            self.logger.debug("LINE通知が無効です")
            return False
        
        try:
            # まずLINE Notifyを試行
            line_notify_token = os.getenv('LINE_NOTIFY_TOKEN')
            if line_notify_token:
                return self._send_line_notify(message, line_notify_token)
            
            # LINE Notifyがない場合はLINE Messaging APIを使用
            line_config = self.config['line']
            
            # LINE Messaging APIで送信
            headers = {
                'Authorization': f"Bearer {line_config['channel_access_token']}",
                'Content-Type': 'application/json'
            }
            
            data = {
                'to': line_config['user_id'],
                'messages': [
                    {
                        'type': 'text',
                        'text': message
                    }
                ]
            }
            
            response = requests.post(
                'https://api.line.me/v2/bot/message/push',
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            self.logger.info("LINE通知を送信しました")
            return True
            
        except Exception as e:
            self.logger.error(f"LINE通知の送信に失敗: {e}")
            return False
    
    def _send_line_notify(self, message: str, token: str) -> bool:
        """LINE Notify を使用した通知送信"""
        try:
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            data = {
                'message': message
            }
            
            response = requests.post(
                'https://notify-api.line.me/api/notify',
                headers=headers,
                data=data
            )
            response.raise_for_status()
            
            self.logger.info("LINE Notify通知を送信しました")
            return True
            
        except Exception as e:
            self.logger.error(f"LINE Notify通知の送信に失敗: {e}")
            return False
    
    def send_notification(self, message: str, methods: Optional[list] = None) -> dict:
        """指定された方法で通知を送信"""
        if methods is None:
            methods = self.config.get('methods', [])
        
        results = {}
        
        for method in methods:
            if method == 'email':
                results['email'] = self.send_email(message)
            elif method == 'slack':
                results['slack'] = self.send_slack(message)
            elif method == 'line':
                results['line'] = self.send_line(message)
        
        return results
