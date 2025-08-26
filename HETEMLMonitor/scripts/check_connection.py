#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HETEMLサーバ接続テストスクリプト
設定が正しく動作するかテストします。
"""

import sys
import os
from datetime import datetime

# 設定ファイルのインポート
try:
    from config import HETEML_CONFIG, MONITOR_CONFIG
except ImportError:
    print("設定ファイルが見つかりません。config.example.pyをconfig.pyにコピーして編集してください。")
    sys.exit(1)

def test_ssh_connection():
    """SSH接続のテスト"""
    print("🔍 SSH接続テストを開始します...")
    
    try:
        import paramiko
        
        # SSHクライアントの作成
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 接続設定
        config = HETEML_CONFIG
        connect_kwargs = {
            'hostname': config['hostname'],
            'port': config['port'],
            'username': config['username'],
            'timeout': config['timeout']
        }
        
        # パスワードまたは秘密鍵で認証
        if config.get('password'):
            connect_kwargs['password'] = config['password']
        elif config.get('key_filename'):
            connect_kwargs['key_filename'] = config['key_filename']
        
        print(f"接続先: {config['hostname']}:{config['port']}")
        print(f"ユーザー: {config['username']}")
        
        # 接続実行
        ssh_client.connect(**connect_kwargs)
        print("✅ SSH接続に成功しました！")
        
        # SFTP接続のテスト
        sftp_client = ssh_client.open_sftp()
        print("✅ SFTP接続に成功しました！")
        
        # 監視対象フォルダの存在確認
        target_path = MONITOR_CONFIG['target_path']
        try:
            sftp_client.stat(target_path)
            print(f"✅ 監視対象フォルダが存在します: {target_path}")
            
            # ファイル一覧の取得テスト
            files = sftp_client.listdir(target_path)
            print(f"✅ フォルダ内のファイル数: {len(files)}")
            
            if files:
                print("📁 ファイル一覧（最初の10件）:")
                for i, filename in enumerate(files[:10], 1):
                    print(f"  {i}. {filename}")
                if len(files) > 10:
                    print(f"  ... 他 {len(files) - 10} ファイル")
            
        except FileNotFoundError:
            print(f"❌ 監視対象フォルダが見つかりません: {target_path}")
            print("フォルダパスを確認してください。")
        
        # 接続を閉じる
        sftp_client.close()
        ssh_client.close()
        
        return True
        
    except Exception as e:
        print(f"❌ SSH接続に失敗しました: {e}")
        print("\n🔧 トラブルシューティング:")
        print("1. ホスト名が正しいか確認してください")
        print("2. SSHポートが正しいか確認してください（通常は22）")
        print("3. ユーザー名とパスワードが正しいか確認してください")
        print("4. HETEMLサーバでSSH接続が有効になっているか確認してください")
        print("5. ファイアウォールでSSHポートがブロックされていないか確認してください")
        return False

def test_notification():
    """通知機能のテスト"""
    print("\n🔍 通知機能テストを開始します...")
    
    try:
        from notifications import NotificationManager
        
        notification_manager = NotificationManager()
        test_message = f"🧪 HETEMLサーバ監視システムのテスト通知\n\nテスト時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nこれはテスト通知です。"
        
        # 各通知方法をテスト
        results = notification_manager.send_notification(test_message)
        
        for method, success in results.items():
            if success:
                print(f"✅ {method}通知テストに成功しました")
            else:
                print(f"❌ {method}通知テストに失敗しました")
        
        return True
        
    except Exception as e:
        print(f"❌ 通知機能テストに失敗しました: {e}")
        return False

def show_config_info():
    """設定情報の表示"""
    print("📋 現在の設定情報:")
    print(f"  サーバ: {HETEML_CONFIG['hostname']}:{HETEML_CONFIG['port']}")
    print(f"  ユーザー: {HETEML_CONFIG['username']}")
    print(f"  監視対象: {MONITOR_CONFIG['target_path']}")
    print(f"  監視間隔: {MONITOR_CONFIG['check_interval']}秒")
    print()

def main():
    """メイン関数"""
    print("🚀 HETEMLサーバ監視システム - 接続テスト")
    print("=" * 50)
    
    show_config_info()
    
    # SSH接続テスト
    ssh_success = test_ssh_connection()
    
    # 通知機能テスト
    notification_success = test_notification()
    
    print("\n" + "=" * 50)
    print("📊 テスト結果:")
    print(f"  SSH接続: {'✅ 成功' if ssh_success else '❌ 失敗'}")
    print(f"  通知機能: {'✅ 成功' if notification_success else '❌ 失敗'}")
    
    if ssh_success and notification_success:
        print("\n🎉 すべてのテストに成功しました！")
        print("監視システムを開始できます: python heteml_monitor.py")
    else:
        print("\n⚠️  一部のテストに失敗しました。")
        print("設定を確認してから再実行してください。")

if __name__ == "__main__":
    main()
