#!/usr/bin/env python3
"""
統合監視システム
全プロジェクト（HETEMLMonitor、NotionLinker、MovableTypeRebuilder）の状態を監視し、
問題を検出して自動復旧を実行する
"""

import os
import sys
import time
import json
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# プロジェクトルートのパス
PROJECT_ROOT = Path("/Users/takuhito/NotionWorkflowTools")

class ServiceMonitor:
    """サービス監視クラス"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.config = self._load_config()
        self.services = {
            'heteml_monitor': {
                'name': 'HETEMLMonitor',
                'plist': 'com.user.heteml-monitor.plist',
                'log_dir': PROJECT_ROOT / 'HETEMLMonitor' / 'logs',
                'check_interval': 300,  # 5分
                'last_check': None,
                'status': 'unknown'
            },
            'notion_linker': {
                'name': 'NotionLinker',
                'plist': 'com.tkht.notion-linker.plist',
                'log_dir': Path('/Users/takuhito/Library/Logs'),
                'check_interval': 900,  # 15分
                'last_check': None,
                'status': 'unknown'
            },
            'movabletype_rebuilder': {
                'name': 'MovableTypeRebuilder',
                'plist': 'com.user.movabletype-rebuilder.plist',
                'log_dir': PROJECT_ROOT / 'MovableTypeRebuilder' / 'logs',
                'check_interval': 86400,  # 24時間（毎月1日のみ実行）
                'last_check': None,
                'status': 'unknown'
            }
        }
    
    def _setup_logger(self):
        """ロガーの設定"""
        log_dir = PROJECT_ROOT / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('ServiceMonitor')
        logger.setLevel(logging.INFO)
        
        # ファイルハンドラー
        fh = logging.FileHandler(log_dir / 'service_monitor.log')
        fh.setLevel(logging.INFO)
        
        # コンソールハンドラー
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def _load_config(self):
        """設定ファイルの読み込み"""
        config_file = PROJECT_ROOT / 'config' / 'monitor_config.json'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # デフォルト設定
            return {
                'email': {
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'username': os.getenv('EMAIL_USERNAME'),
                    'password': os.getenv('EMAIL_PASSWORD'),
                    'from_email': os.getenv('FROM_EMAIL'),
                    'to_email': os.getenv('TO_EMAIL')
                },
                'notification': {
                    'enabled': True,
                    'check_interval': 300  # 5分
                }
            }
    
    def check_launchd_service(self, service_name, plist_name):
        """launchdサービスの状態確認"""
        try:
            # launchctl print でサービスの詳細情報を取得
            result = subprocess.run(
                ['launchctl', 'print', f'gui/$(id -u)/{plist_name}'],
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # 状態の解析
                if 'state = running' in output:
                    return 'running'
                elif 'state = not running' in output:
                    return 'stopped'
                else:
                    return 'unknown'
            else:
                return 'error'
                
        except Exception as e:
            self.logger.error(f"launchd service check error for {service_name}: {e}")
            return 'error'
    
    def check_log_files(self, service_name, log_dir):
        """ログファイルの確認"""
        try:
            if not log_dir.exists():
                return {'status': 'no_logs', 'message': 'ログディレクトリが存在しません'}
            
            # 最近のログファイルを確認
            log_files = list(log_dir.glob('*.log'))
            if not log_files:
                return {'status': 'no_logs', 'message': 'ログファイルが存在しません'}
            
            # 最新のログファイルを取得
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            log_age = time.time() - latest_log.stat().st_mtime
            
            # ログファイルの内容を確認
            with open(latest_log, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # エラーの検出
            error_indicators = ['error', 'Error', 'ERROR', 'failed', 'Failed', 'FAILED']
            has_errors = any(indicator in content for indicator in error_indicators)
            
            return {
                'status': 'ok' if not has_errors else 'error',
                'latest_log': latest_log.name,
                'log_age': log_age,
                'has_errors': has_errors,
                'message': 'エラーが検出されました' if has_errors else '正常'
            }
            
        except Exception as e:
            self.logger.error(f"Log check error for {service_name}: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def restart_service(self, service_name, plist_name):
        """サービスの再起動"""
        try:
            self.logger.info(f"Restarting {service_name}...")
            
            # plistファイルのパスを取得
            plist_path = Path.home() / 'Library' / 'LaunchAgents' / f'{plist_name}.plist'
            
            if not plist_path.exists():
                # プロジェクト内のplistファイルを探す
                project_plist_path = PROJECT_ROOT / 'config' / f'{plist_name}.plist'
                if project_plist_path.exists():
                    plist_path = project_plist_path
                else:
                    self.logger.error(f"plist file not found for {service_name}")
                    return False
            
            # サービスを停止
            unload_result = subprocess.run(
                ['launchctl', 'unload', str(plist_path)], 
                capture_output=True, text=True
            )
            self.logger.info(f"Unload result for {service_name}: {unload_result.returncode}")
            time.sleep(2)
            
            # サービスを開始
            load_result = subprocess.run(
                ['launchctl', 'load', str(plist_path)], 
                capture_output=True, text=True
            )
            
            if load_result.returncode == 0:
                self.logger.info(f"{service_name} restarted successfully")
                return True
            else:
                self.logger.error(f"Failed to restart {service_name}: {load_result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Restart error for {service_name}: {e}")
            return False
    
    def send_notification(self, subject, message):
        """通知の送信"""
        if not self.config['notification']['enabled']:
            return
        
        try:
            email_config = self.config['email']
            
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = f"[統合監視] {subject}"
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
            
            self.logger.info(f"Notification sent: {subject}")
            
        except Exception as e:
            self.logger.error(f"Notification error: {e}")
    
    def check_service(self, service_key, service_info):
        """個別サービスの確認"""
        service_name = service_info['name']
        plist_name = service_info['plist']
        log_dir = service_info['log_dir']
        
        self.logger.info(f"Checking {service_name}...")
        
        # launchdサービスの状態確認
        launchd_status = self.check_launchd_service(service_name, plist_name)
        
        # ログファイルの確認
        log_status = self.check_log_files(service_name, log_dir)
        
        # 状態の判定
        if launchd_status == 'running' and log_status['status'] == 'ok':
            status = 'healthy'
        elif launchd_status == 'stopped':
            status = 'stopped'
        elif log_status['status'] == 'error':
            status = 'error'
        else:
            status = 'unknown'
        
        # 状態の更新
        self.services[service_key]['status'] = status
        self.services[service_key]['last_check'] = datetime.now()
        
        # 問題の検出と復旧
        if status in ['stopped', 'error']:
            self.logger.warning(f"{service_name} has issues: {status}")
            
            # 自動復旧の実行
            if self.restart_service(service_name, plist_name):
                # 再起動後の確認
                time.sleep(5)
                new_status = self.check_launchd_service(service_name, plist_name)
                if new_status == 'running':
                    self.logger.info(f"{service_name} recovered successfully")
                    self.send_notification(
                        f"{service_name} 自動復旧完了",
                        f"{service_name} の問題を検出し、自動復旧を実行しました。\n"
                        f"現在の状態: {new_status}\n"
                        f"復旧時刻: {datetime.now()}"
                    )
                else:
                    self.logger.error(f"{service_name} recovery failed")
                    self.send_notification(
                        f"{service_name} 自動復旧失敗",
                        f"{service_name} の問題を検出しましたが、自動復旧に失敗しました。\n"
                        f"現在の状態: {new_status}\n"
                        f"手動での確認が必要です。"
                    )
            else:
                self.send_notification(
                    f"{service_name} 復旧失敗",
                    f"{service_name} の問題を検出しましたが、復旧に失敗しました。\n"
                    f"手動での確認が必要です。"
                )
        
        return {
            'service': service_name,
            'launchd_status': launchd_status,
            'log_status': log_status,
            'overall_status': status
        }
    
    def run_monitoring_cycle(self):
        """監視サイクルの実行"""
        self.logger.info("Starting monitoring cycle...")
        
        results = []
        current_time = datetime.now()
        
        for service_key, service_info in self.services.items():
            # チェック間隔の確認
            if (service_info['last_check'] is None or 
                (current_time - service_info['last_check']).total_seconds() >= service_info['check_interval']):
                
                result = self.check_service(service_key, service_info)
                results.append(result)
        
        # 結果の要約
        healthy_count = sum(1 for r in results if r['overall_status'] == 'healthy')
        total_count = len(results)
        
        self.logger.info(f"Monitoring cycle completed: {healthy_count}/{total_count} services healthy")
        
        # 全体の状態通知
        if healthy_count < total_count:
            self.send_notification(
                "サービス監視アラート",
                f"監視対象サービスの一部に問題があります。\n"
                f"正常: {healthy_count}/{total_count}\n\n"
                f"詳細:\n" + "\n".join([
                    f"- {r['service']}: {r['overall_status']}"
                    for r in results
                ])
            )
        
        return results
    
    def run_continuous_monitoring(self):
        """継続的な監視"""
        self.logger.info("Starting continuous monitoring...")
        
        while True:
            try:
                self.run_monitoring_cycle()
                time.sleep(self.config['notification']['check_interval'])
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(60)  # エラー時は1分待機

def main():
    """メイン関数"""
    monitor = ServiceMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        monitor.run_continuous_monitoring()
    else:
        # 1回だけ実行
        results = monitor.run_monitoring_cycle()
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))

if __name__ == '__main__':
    main()
