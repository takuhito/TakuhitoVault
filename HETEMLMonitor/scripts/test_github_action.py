#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HETEMLMonitor GitHub Action版のテストスクリプト
ローカル環境でGitHub Action版の動作をテストします。
"""

import os
import sys
import json
from pathlib import Path

# HETEMLMonitorディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_config_loading():
    """設定ファイルの読み込みテスト"""
    print("🔧 設定ファイルの読み込みテスト...")
    
    try:
        from config import HETEML_CONFIG, MONITOR_CONFIG, NOTIFICATION_CONFIG
        print("✅ 設定ファイルの読み込みに成功")
        
        # 設定内容の表示
        print(f"  HETEMLサーバ: {HETEML_CONFIG.get('hostname', 'N/A')}")
        print(f"  監視対象パス: {MONITOR_CONFIG.get('target_path', 'N/A')}")
        print(f"  通知方法: {NOTIFICATION_CONFIG.get('methods', [])}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 設定ファイルの読み込みに失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 設定エラー: {e}")
        return False

def test_notification_manager():
    """通知マネージャーのテスト"""
    print("\n🔔 通知マネージャーのテスト...")
    
    try:
        from notifications import NotificationManager
        
        manager = NotificationManager()
        print("✅ 通知マネージャーの初期化に成功")
        
        # 設定の確認
        config = manager.config
        print(f"  メール通知: {'有効' if config.get('email', {}).get('enabled') else '無効'}")
        print(f"  LINE通知: {'有効' if config.get('line', {}).get('enabled') else '無効'}")
        print(f"  Slack通知: {'有効' if config.get('slack', {}).get('enabled') else '無効'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 通知マネージャーのテストに失敗: {e}")
        return False

def test_github_action_monitor():
    """GitHub Action版モニターのテスト"""
    print("\n🚀 GitHub Action版モニターのテスト...")
    
    try:
        from heteml_monitor_github_action import HETEMLMonitorGitHubAction
        
        monitor = HETEMLMonitorGitHubAction()
        print("✅ GitHub Action版モニターの初期化に成功")
        
        # ファイル履歴の確認
        print(f"  既知のファイル数: {len(monitor.known_files)}")
        print(f"  ファイルハッシュ数: {len(monitor.file_hashes)}")
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub Action版モニターのテストに失敗: {e}")
        return False

def test_environment_variables():
    """環境変数のテスト"""
    print("\n🌍 環境変数のテスト...")
    
    required_vars = [
        'HETEML_PASSWORD',
        'EMAIL_USERNAME', 
        'EMAIL_PASSWORD',
        'FROM_EMAIL',
        'TO_EMAIL'
    ]
    
    optional_vars = [
        'LINE_CHANNEL_ACCESS_TOKEN',
        'LINE_USER_ID'
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"  ✅ {var}: 設定済み")
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            print(f"  ✅ {var}: 設定済み")
    
    if missing_required:
        print(f"  ❌ 必須環境変数が不足: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"  ⚠️  オプション環境変数が未設定: {', '.join(missing_optional)}")
    
    print("✅ 環境変数のテスト完了")
    return True

def test_file_structure():
    """ファイル構造のテスト"""
    print("\n📁 ファイル構造のテスト...")
    
    required_files = [
        'heteml_monitor_github_action.py',
        'config.py',
        'notifications.py',
        'requirements.txt'
    ]
    
    missing_files = []
    
    for file in required_files:
        file_path = Path(__file__).parent.parent / file
        if file_path.exists():
            print(f"  ✅ {file}: 存在")
        else:
            print(f"  ❌ {file}: 存在しない")
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 必要なファイルが不足: {', '.join(missing_files)}")
        return False
    
    print("✅ ファイル構造のテスト完了")
    return True

def test_dependencies():
    """依存関係のテスト"""
    print("\n📦 依存関係のテスト...")
    
    required_packages = [
        'paramiko',
        'requests',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}: インストール済み")
        except ImportError:
            print(f"  ❌ {package}: 未インストール")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 必要なパッケージが不足: {', '.join(missing_packages)}")
        print("  以下のコマンドでインストールしてください:")
        print(f"  pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 依存関係のテスト完了")
    return True

def main():
    """メイン関数"""
    print("🧪 HETEMLMonitor GitHub Action版 テスト開始\n")
    
    tests = [
        ("ファイル構造", test_file_structure),
        ("依存関係", test_dependencies),
        ("環境変数", test_environment_variables),
        ("設定ファイル", test_config_loading),
        ("通知マネージャー", test_notification_manager),
        ("GitHub Action版モニター", test_github_action_monitor),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}のテストでエラーが発生: {e}")
            results.append((test_name, False))
    
    # 結果の表示
    print("\n" + "="*50)
    print("📊 テスト結果")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n合計: {passed}/{total} テストが成功")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました！")
        print("GitHub Actionsでの実行準備が完了しています。")
        return True
    else:
        print("⚠️  一部のテストが失敗しました。")
        print("上記のエラーを修正してから再実行してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
