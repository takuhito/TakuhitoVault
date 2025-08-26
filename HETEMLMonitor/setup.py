#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HETEMLサーバ監視システム セットアップスクリプト
"""

import os
import sys
import shutil
from pathlib import Path

def create_config_file():
    """設定ファイルの作成"""
    if os.path.exists('config.py'):
        print("設定ファイルは既に存在します。")
        response = input("上書きしますか？ (y/N): ")
        if response.lower() != 'y':
            return False
    
    if os.path.exists('config.example.py'):
        shutil.copy('config.example.py', 'config.py')
        print("✅ 設定ファイルを作成しました: config.py")
        print("📝 設定ファイルを編集してください:")
        print("   - HETEMLサーバの接続情報")
        print("   - 監視対象フォルダパス")
        print("   - 通知設定")
        return True
    else:
        print("❌ config.example.pyが見つかりません")
        return False

def create_env_file():
    """環境変数ファイルの作成"""
    env_file = '.env'
    if os.path.exists(env_file):
        print("環境変数ファイルは既に存在します。")
        return True
    
    env_content = """# HETEMLサーバ監視システム 環境変数
# このファイルに機密情報を設定してください

# HETEMLサーバ接続情報
HETEML_PASSWORD=your-heteml-password

# メール通知設定
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
TO_EMAIL=recipient@example.com

# Slack通知設定
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# LINE通知設定
LINE_CHANNEL_ACCESS_TOKEN=your-line-channel-access-token
LINE_USER_ID=your-line-user-id
"""
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ 環境変数ファイルを作成しました: .env")
    print("📝 環境変数ファイルを編集してください:")
    print("   - HETEMLサーバのパスワード")
    print("   - 通知サービスの認証情報")
    return True

def install_dependencies():
    """依存関係のインストール"""
    print("📦 依存関係をインストールしています...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 依存関係のインストールが完了しました")
            return True
        else:
            print(f"❌ 依存関係のインストールに失敗しました: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 依存関係のインストール中にエラーが発生: {e}")
        return False

def create_directories():
    """必要なディレクトリの作成"""
    directories = ['logs', 'backups']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ ディレクトリを作成しました: {directory}")

def show_next_steps():
    """次のステップの表示"""
    print("\n" + "=" * 50)
    print("🎉 セットアップが完了しました！")
    print("\n📋 次のステップ:")
    print("1. config.py を編集してHETEMLサーバの接続情報を設定")
    print("2. .env ファイルを編集して通知サービスの認証情報を設定")
    print("3. 接続テストを実行: python check_connection.py")
    print("4. 監視システムを開始: python heteml_monitor.py")
    print("\n📚 詳細な設定方法は README.md を参照してください")

def main():
    """メイン関数"""
    print("🚀 HETEMLサーバ監視システム セットアップ")
    print("=" * 50)
    
    # 依存関係のインストール
    if not install_dependencies():
        print("❌ セットアップを中止します")
        return
    
    # 設定ファイルの作成
    if not create_config_file():
        print("❌ 設定ファイルの作成に失敗しました")
        return
    
    # 環境変数ファイルの作成
    create_env_file()
    
    # ディレクトリの作成
    create_directories()
    
    # 次のステップの表示
    show_next_steps()

if __name__ == "__main__":
    main()
