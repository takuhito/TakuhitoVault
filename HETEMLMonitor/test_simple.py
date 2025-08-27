#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプルなテストスクリプト
GitHub Actions環境での基本的な動作を確認します。
"""

import os
import sys

def main():
    """メイン関数"""
    print("🧪 シンプルテスト開始")
    print(f"現在のディレクトリ: {os.getcwd()}")
    print(f"Pythonバージョン: {sys.version}")
    
    # ファイル一覧
    print("\n📁 ファイル一覧:")
    try:
        files = os.listdir('.')
        for file in files:
            print(f"  - {file}")
    except Exception as e:
        print(f"❌ ファイル一覧取得エラー: {e}")
    
    # 環境変数の確認
    print("\n🌍 環境変数の確認:")
    env_vars = ['HETEML_PASSWORD', 'EMAIL_USERNAME', 'EMAIL_PASSWORD', 'FROM_EMAIL', 'TO_EMAIL']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: 設定済み")
        else:
            print(f"  ❌ {var}: 未設定")
    
    # 設定ファイルの確認
    print("\n📄 設定ファイルの確認:")
    try:
        if os.path.exists('config.py'):
            print("  ✅ config.py: 存在")
            with open('config.py', 'r') as f:
                content = f.read()
                print(f"  📏 ファイルサイズ: {len(content)} 文字")
        else:
            print("  ❌ config.py: 存在しない")
    except Exception as e:
        print(f"  ❌ 設定ファイル確認エラー: {e}")
    
    # 依存関係の確認
    print("\n📦 依存関係の確認:")
    try:
        import paramiko
        print("  ✅ paramiko: インストール済み")
    except ImportError:
        print("  ❌ paramiko: 未インストール")
    
    try:
        import requests
        print("  ✅ requests: インストール済み")
    except ImportError:
        print("  ❌ requests: 未インストール")
    
    try:
        from dotenv import load_dotenv
        print("  ✅ python-dotenv: インストール済み")
    except ImportError:
        print("  ❌ python-dotenv: 未インストール")
    
    print("\n✅ シンプルテスト完了")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("🎉 テスト成功")
            sys.exit(0)
        else:
            print("❌ テスト失敗")
            sys.exit(1)
    except Exception as e:
        print(f"💥 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
