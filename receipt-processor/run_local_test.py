#!/usr/bin/env python3
"""
ローカル環境でのテストスクリプト
GitHub Actionsの課金制限を回避してローカルでテスト
"""

import os
import sys
from datetime import datetime

def setup_local_environment():
    """ローカル環境の設定"""
    print("🔧 ローカル環境の設定")
    print("=" * 50)
    
    # 必要な環境変数を手動で設定
    # 実際の値はGitHub Secretsから取得してください
    required_vars = {
        'NOTION_TOKEN': 'your_notion_token_here',
        'GEMINI_API_KEY': 'your_gemini_api_key_here',
        'NOTION_DATABASE_ID': '254b061dadf38042813eeab350aea734',
        'GOOGLE_DRIVE_MONITOR_FOLDER': '1YccjjOWIp4PAQVUY8SVcSvUvkcQ6lo3B',
        'GOOGLE_DRIVE_PROCESSED_BASE': '0AJojvkLIwToKUk9PVA',
        'GOOGLE_DRIVE_ERROR_FOLDER': '1HJrzj1DDoiTmIkNa8tIN3RKnLKs_8Kaf',
        'GOOGLE_DRIVE_SHARED_DRIVE_ID': '0AJojvkLIwToKUk9PVA'
    }
    
    print("📝 以下の環境変数を設定してください：")
    for var, value in required_vars.items():
        print(f"export {var}='{value}'")
    
    print("\n💡 または、.envファイルを作成して設定することもできます")
    print("例：echo 'NOTION_TOKEN=your_token' > .env")

def check_environment():
    """環境変数の確認"""
    print("\n🔍 環境変数の確認")
    print("=" * 50)
    
    required_vars = [
        'NOTION_TOKEN',
        'GEMINI_API_KEY',
        'NOTION_DATABASE_ID',
        'GOOGLE_DRIVE_MONITOR_FOLDER',
        'GOOGLE_DRIVE_PROCESSED_BASE',
        'GOOGLE_DRIVE_ERROR_FOLDER',
        'GOOGLE_DRIVE_SHARED_DRIVE_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'TOKEN' in var or 'KEY' in var:
                masked_value = value[:10] + "..." + value[-10:] if len(value) > 20 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  未設定の環境変数: {missing_vars}")
        print("環境変数を設定してから再実行してください")
        return False
    
    return True

def run_debug_test():
    """デバッグテストの実行"""
    print("\n🧪 デバッグテストの実行")
    print("=" * 50)
    
    try:
        from debug_detailed import main as debug_main
        debug_main()
        return True
    except Exception as e:
        print(f"❌ デバッグテストエラー: {e}")
        return False

def run_main_test():
    """main.pyのテスト実行"""
    print("\n🚀 main.pyのテスト実行")
    print("=" * 50)
    
    try:
        from main import main as main_function
        result = main_function()
        print(f"✅ main.py実行完了: {result}")
        return result
    except Exception as e:
        print(f"❌ main.py実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print(f"🏠 ローカルテスト開始 - {datetime.now()}")
    print("=" * 60)
    
    # 環境変数が設定されていない場合は設定方法を表示
    if not any(os.getenv(var) for var in ['NOTION_TOKEN', 'GEMINI_API_KEY']):
        setup_local_environment()
        print("\n❌ 環境変数が設定されていません")
        print("上記の環境変数を設定してから再実行してください")
        return
    
    # 環境変数の確認
    if not check_environment():
        return
    
    # デバッグテストの実行
    if not run_debug_test():
        print("❌ デバッグテストが失敗しました")
        return
    
    # main.pyのテスト実行
    success = run_main_test()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ローカルテスト完了 - 成功")
    else:
        print("❌ ローカルテスト完了 - 失敗")

if __name__ == "__main__":
    main()
