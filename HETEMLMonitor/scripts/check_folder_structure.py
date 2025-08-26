#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HETEMLサーバのフォルダ構造確認スクリプト
実際のフォルダパスを確認します。
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

def check_folder_structure():
    """フォルダ構造の確認"""
    print("🔍 HETEMLサーバのフォルダ構造を確認しています...")
    
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
        
        # ルートディレクトリの確認
        print("\n📁 ルートディレクトリの内容:")
        stdin, stdout, stderr = ssh_client.exec_command('ls -la /')
        root_contents = stdout.read().decode('utf-8')
        print(root_contents)
        
        # /web ディレクトリの確認
        print("\n📁 /web ディレクトリの内容:")
        stdin, stdout, stderr = ssh_client.exec_command('ls -la /web')
        web_contents = stdout.read().decode('utf-8')
        print(web_contents)
        
        # /web/domain ディレクトリの確認
        print("\n📁 /web/domain ディレクトリの内容:")
        stdin, stdout, stderr = ssh_client.exec_command('ls -la /web/domain')
        domain_contents = stdout.read().decode('utf-8')
        print(domain_contents)
        
        # nbspress.com ディレクトリの確認
        print("\n📁 /web/domain/nbspress.com ディレクトリの内容:")
        stdin, stdout, stderr = ssh_client.exec_command('ls -la /web/domain/nbspress.com')
        nbspress_contents = stdout.read().decode('utf-8')
        print(nbspress_contents)
        
        # nbs.or.jp ディレクトリの確認
        print("\n📁 /web/domain/nbspress.com/nbs.or.jp ディレクトリの内容:")
        stdin, stdout, stderr = ssh_client.exec_command('ls -la /web/domain/nbspress.com/nbs.or.jp')
        nbs_contents = stdout.read().decode('utf-8')
        print(nbs_contents)
        
        # stages ディレクトリの確認
        print("\n📁 /web/domain/nbspress.com/nbs.or.jp/stages ディレクトリの内容:")
        stdin, stdout, stderr = ssh_client.exec_command('ls -la /web/domain/nbspress.com/nbs.or.jp/stages')
        stages_contents = stdout.read().decode('utf-8')
        print(stages_contents)
        
        # 代替パスの確認
        print("\n🔍 代替パスの確認:")
        alternative_paths = [
            '/web/domain/nbs.or.jp/stages/',
            '/web/domain/nbspress.com/stages/',
            '/web/nbs.or.jp/stages/',
            '/web/stages/',
            '/home/nbsorjp/public_html/stages/',
            '/home/nbsorjp/www/stages/',
        ]
        
        for path in alternative_paths:
            stdin, stdout, stderr = ssh_client.exec_command(f'test -d "{path}" && echo "存在します" || echo "存在しません"')
            result = stdout.read().decode('utf-8').strip()
            print(f"  {path}: {result}")
        
        ssh_client.close()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def main():
    """メイン関数"""
    print("🚀 HETEMLサーバフォルダ構造確認")
    print("=" * 50)
    
    check_folder_structure()

if __name__ == "__main__":
    main()
