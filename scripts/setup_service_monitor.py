#!/usr/bin/env python3
"""
統合監視システムのセットアップスクリプト
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def setup_service_monitor():
    """統合監視システムのセットアップ"""
    
    # プロジェクトルートのパス
    project_root = Path("/Users/takuhito/NotionWorkflowTools")
    
    print("=== 統合監視システムのセットアップ ===")
    
    # 1. 必要なディレクトリの作成
    print("1. 必要なディレクトリを作成中...")
    (project_root / 'logs').mkdir(exist_ok=True)
    (project_root / 'config').mkdir(exist_ok=True)
    
    # 2. 設定ファイルの作成
    print("2. 設定ファイルを作成中...")
    config_file = project_root / 'config' / 'monitor_config.json'
    
    if not config_file.exists():
        config = {
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
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"設定ファイルを作成しました: {config_file}")
    else:
        print(f"設定ファイルは既に存在します: {config_file}")
    
    # 3. launchdサービスの設定
    print("3. launchdサービスを設定中...")
    
    # plistファイルのパス
    plist_source = project_root / 'config' / 'com.user.service-monitor.plist'
    plist_dest = Path.home() / 'Library' / 'LaunchAgents' / 'com.user.service-monitor.plist'
    
    if plist_source.exists():
        # plistファイルをコピー
        import shutil
        shutil.copy2(plist_source, plist_dest)
        print(f"plistファイルをコピーしました: {plist_dest}")
        
        # 権限を設定
        os.chmod(plist_dest, 0o644)
        print("plistファイルの権限を設定しました")
        
        # 既存のサービスを停止
        try:
            subprocess.run(['launchctl', 'unload', str(plist_dest)], 
                         capture_output=True, check=False)
            print("既存のサービスを停止しました")
        except:
            pass
        
        # 新しいサービスを開始
        try:
            result = subprocess.run(['launchctl', 'load', str(plist_dest)], 
                                  capture_output=True, text=True, check=True)
            print("統合監視サービスを開始しました")
        except subprocess.CalledProcessError as e:
            print(f"サービスの開始に失敗しました: {e}")
            print(f"エラー出力: {e.stderr}")
            return False
    else:
        print(f"plistファイルが見つかりません: {plist_source}")
        return False
    
    # 4. サービスの状態確認
    print("4. サービスの状態を確認中...")
    try:
        result = subprocess.run(
            ['launchctl', 'list', 'com.user.service-monitor'],
            capture_output=True, text=True, check=True
        )
        print("統合監視サービスが正常に登録されました")
        print(f"サービス情報:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"サービスの確認に失敗しました: {e}")
        return False
    
    # 5. テスト実行
    print("5. 監視システムをテスト実行中...")
    try:
        result = subprocess.run(
            [sys.executable, str(project_root / 'scripts' / 'monitor_all_services.py')],
            capture_output=True, text=True, check=True, timeout=30
        )
        print("テスト実行が完了しました")
        print("結果:")
        print(result.stdout)
    except subprocess.TimeoutExpired:
        print("テスト実行がタイムアウトしました（正常です）")
    except subprocess.CalledProcessError as e:
        print(f"テスト実行に失敗しました: {e}")
        print(f"エラー出力: {e.stderr}")
        return False
    
    print("\n=== セットアップ完了 ===")
    print("統合監視システムが正常にセットアップされました。")
    print("5分間隔で全サービスの監視が開始されます。")
    print(f"ログファイル: {project_root / 'logs' / 'service_monitor.log'}")
    
    return True

def check_service_status():
    """サービスの状態確認"""
    print("\n=== 現在のサービス状態 ===")
    
    services = [
        ('HETEMLMonitor', 'com.user.heteml-monitor'),
        ('NotionLinker', 'com.tkht.notion-linker'),
        ('MovableTypeRebuilder', 'com.user.movabletype-rebuilder'),
        ('統合監視', 'com.user.service-monitor')
    ]
    
    for service_name, plist_name in services:
        try:
            result = subprocess.run(
                ['launchctl', 'list', plist_name],
                capture_output=True, text=True, check=True
            )
            print(f"{service_name}: 登録済み")
        except subprocess.CalledProcessError:
            print(f"{service_name}: 未登録")

def main():
    """メイン関数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        check_service_status()
    else:
        if setup_service_monitor():
            check_service_status()
        else:
            print("セットアップに失敗しました。")
            sys.exit(1)

if __name__ == '__main__':
    main()
