#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HETEMLサーバの構造探索スクリプト
実際のディレクトリ構造を確認します。
"""

import os
import paramiko
from dotenv import load_dotenv

# 設定ファイルのインポート
try:
    from config import HETEML_CONFIG
except ImportError:
    print("設定ファイルが見つかりません。")
    exit(1)

load_dotenv()

def explore_server():
    """サーバの構造を探索"""
    print("🔍 HETEMLサーバの構造を探索しています...")
    
    try:
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
        
        # パスワードで認証
        if config.get('password'):
            connect_kwargs['password'] = config['password']
        
        print(f"接続先: {config['hostname']}:{config['port']}")
        print(f"ユーザー: {config['username']}")
        
        # 接続実行
        ssh_client.connect(**connect_kwargs)
        print("✅ SSH接続に成功しました！")
        
        # ホームディレクトリの確認
        print("\n📁 ホームディレクトリの内容:")
        stdin, stdout, stderr = ssh_client.exec_command('ls -la ~')
        home_contents = stdout.read().decode('utf-8')
        print(home_contents)
        
        # 現在のディレクトリの確認
        print("\n📁 現在のディレクトリ:")
        stdin, stdout, stderr = ssh_client.exec_command('pwd')
        current_dir = stdout.read().decode('utf-8').strip()
        print(f"現在のディレクトリ: {current_dir}")
        
        # 一般的なWebディレクトリの確認
        print("\n🔍 一般的なWebディレクトリの確認:")
        web_dirs = [
            '~/public_html',
            '~/www',
            '~/htdocs',
            '~/web',
            '~/html',
            '/var/www',
            '/var/www/html',
            '/usr/local/apache2/htdocs',
            '/home/nbsorjp/public_html',
            '/home/nbsorjp/www',
        ]
        
        for web_dir in web_dirs:
            stdin, stdout, stderr = ssh_client.exec_command(f'test -d "{web_dir}" && echo "存在します" || echo "存在しません"')
            result = stdout.read().decode('utf-8').strip()
            print(f"  {web_dir}: {result}")
        
        # ドメイン関連ディレクトリの検索
        print("\n🔍 ドメイン関連ディレクトリの検索:")
        search_commands = [
            'find ~ -name "*nbs*" -type d 2>/dev/null | head -10',
            'find ~ -name "*stage*" -type d 2>/dev/null | head -10',
            'find /var -name "*nbs*" -type d 2>/dev/null | head -10',
            'find /var -name "*stage*" -type d 2>/dev/null | head -10',
        ]
        
        for cmd in search_commands:
            print(f"\n実行コマンド: {cmd}")
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            result = stdout.read().decode('utf-8').strip()
            if result:
                print(result)
            else:
                print("  見つかりませんでした")
        
        # ファイルシステムの確認
        print("\n📁 ファイルシステムの確認:")
        stdin, stdout, stderr = ssh_client.exec_command('df -h')
        df_result = stdout.read().decode('utf-8')
        print(df_result)
        
        # プロセス確認（Webサーバー）
        print("\n🔍 Webサーバープロセスの確認:")
        stdin, stdout, stderr = ssh_client.exec_command('ps aux | grep -E "(apache|httpd|nginx)" | head -5')
        web_processes = stdout.read().decode('utf-8')
        print(web_processes)
        
        ssh_client.close()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def main():
    """メイン関数"""
    print("🚀 HETEMLサーバ構造探索")
    print("=" * 50)
    
    explore_server()

if __name__ == "__main__":
    main()
