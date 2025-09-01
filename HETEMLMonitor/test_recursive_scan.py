#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
再帰的監視のテストスクリプト
特定のファイルが検出されるかを確認
"""

import os
import sys
import time
from datetime import datetime

# 設定ファイルのインポート
try:
    from config import HETEML_CONFIG, MONITOR_CONFIG
except ImportError:
    print("設定ファイルが見つかりません。")
    sys.exit(1)

import paramiko

def test_recursive_scan():
    """再帰的スキャンのテスト"""
    print("🔍 再帰的スキャンテスト開始")
    print(f"監視対象: {MONITOR_CONFIG['target_path']}")
    print(f"検索対象: TEST-file-01.png")
    print("-" * 50)
    
    try:
        # SSH接続
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        config = HETEML_CONFIG
        connect_kwargs = {
            'hostname': config['hostname'],
            'port': config['port'],
            'username': config['username'],
            'timeout': config['timeout']
        }
        
        if config.get('password'):
            connect_kwargs['password'] = config['password']
        
        print(f"接続中: {config['hostname']}:{config['port']}")
        ssh_client.connect(**connect_kwargs)
        print("✅ SSH接続成功")
        
        # SFTP接続
        sftp_client = ssh_client.open_sftp()
        print("✅ SFTP接続成功")
        
        # 再帰的スキャンのテスト
        target_path = MONITOR_CONFIG['target_path']
        found_files = []
        target_file = "TEST-file-01.png"
        
        def scan_recursive(current_path, depth=0):
            """再帰的スキャン"""
            indent = "  " * depth
            try:
                items = sftp_client.listdir_attr(current_path)
                for item in items:
                    filename = item.filename
                    full_path = f"{current_path}/{filename}"
                    
                    # 除外パターンのチェック
                    if filename.startswith('.'):
                        continue
                    
                    if item.st_mode & 0o40000:  # ディレクトリ
                        print(f"{indent}📁 {filename}/")
                        scan_recursive(full_path, depth + 1)
                    else:  # ファイル
                        print(f"{indent}📄 {filename}")
                        if filename == target_file:
                            found_files.append(full_path)
                            print(f"{indent}🎯 ターゲットファイル発見: {full_path}")
                            
            except Exception as e:
                print(f"{indent}❌ エラー: {e}")
        
        print("\n📂 ディレクトリ構造をスキャン中...")
        start_time = time.time()
        scan_recursive(target_path)
        end_time = time.time()
        
        print(f"\n⏱️  スキャン時間: {end_time - start_time:.2f}秒")
        print(f"🎯 発見されたファイル数: {len(found_files)}")
        
        if found_files:
            print("\n✅ ターゲットファイルが見つかりました:")
            for file_path in found_files:
                print(f"  - {file_path}")
        else:
            print(f"\n❌ ターゲットファイル '{target_file}' が見つかりませんでした")
        
        # 接続を閉じる
        sftp_client.close()
        ssh_client.close()
        print("\n✅ テスト完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    test_recursive_scan()
