#!/usr/bin/env python3
"""
MovableType接続テストスクリプト
MovableTypeサイトへの接続とログインをテストします
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

def test_mt_connection():
    """MovableType接続テスト"""
    load_dotenv()
    
    # 設定読み込み
    mt_url = os.getenv('MT_SITE_URL')
    mt_username = os.getenv('MT_USERNAME')
    mt_password = os.getenv('MT_PASSWORD')
    mt_blog_id = os.getenv('MT_BLOG_ID', '1')
    mt_site_name = os.getenv('MT_SITE_NAME', 'MovableTypeサイト')
    
    if not all([mt_url, mt_username, mt_password]):
        print("❌ 必要な環境変数が設定されていません")
        print("MT_SITE_URL, MT_USERNAME, MT_PASSWORD を設定してください")
        return False
    
    print(f"🔗 MovableTypeサイト: {mt_url}")
    print(f"👤 ユーザー名: {mt_username}")
    print(f"📝 対象サイト: {mt_site_name} (blog_id: {mt_blog_id})")
    
    try:
        session = requests.Session()
        
        # 1. サイトアクセステスト
        print("\n1. サイトアクセステスト...")
        response = session.get(mt_url, timeout=30)
        response.raise_for_status()
        print("✅ サイトアクセス成功")
        
        # 2. ログインページアクセス
        print("\n2. ログインページアクセス...")
        login_url = f"{mt_url}/mt.cgi"
        response = session.get(login_url, timeout=30)
        response.raise_for_status()
        print("✅ ログインページアクセス成功")
        
        # 3. ログインテスト
        print("\n3. ログインテスト...")
        login_data = {
            'username': mt_username,
            'password': mt_password,
            '__mode': 'login'
        }
        
        response = session.post(login_url, data=login_data, timeout=30)
        response.raise_for_status()
        
        # ログイン成功の確認
        if 'ログアウト' in response.text or 'logout' in response.text.lower():
            print("✅ ログイン成功")
            
            # 4. 管理画面アクセステスト
            print("\n4. 管理画面アクセステスト...")
            admin_url = f"{mt_url}/mt.cgi?__mode=dashboard"
            response = session.get(admin_url, timeout=30)
            response.raise_for_status()
            print("✅ 管理画面アクセス成功")
            
            # 5. 再構築ページアクセステスト
            print("\n5. 再構築ページアクセステスト...")
            rebuild_url = f"{mt_url}/mt.cgi?__mode=rebuild"
            response = session.get(rebuild_url, timeout=30)
            response.raise_for_status()
            print("✅ 再構築ページアクセス成功")
            
            return True
        else:
            print("❌ ログイン失敗")
            print("認証情報を確認してください")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー: サイトにアクセスできません")
        return False
    except requests.exceptions.Timeout:
        print("❌ タイムアウト: リクエストがタイムアウトしました")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTPエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def test_rebuild_trigger():
    """再構築トリガーテスト（実際には実行しない）"""
    load_dotenv()
    
    mt_url = os.getenv('MT_SITE_URL')
    mt_username = os.getenv('MT_USERNAME')
    mt_password = os.getenv('MT_PASSWORD')
    
    try:
        session = requests.Session()
        
        # ログイン
        login_url = f"{mt_url}/mt.cgi"
        login_data = {
            'username': mt_username,
            'password': mt_password,
            '__mode': 'login'
        }
        
        response = session.post(login_url, data=login_data, timeout=30)
        response.raise_for_status()
        
        if 'ログアウト' in response.text or 'logout' in response.text.lower():
            print("\n6. 再構築トリガーテスト（ドライラン）...")
            
            # 再構築ページの内容を確認
            rebuild_url = f"{mt_url}/mt.cgi?__mode=rebuild"
            response = session.get(rebuild_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 再構築関連の要素を確認
            rebuild_forms = soup.find_all('form', {'action': lambda x: x and 'rebuild' in x})
            rebuild_buttons = soup.find_all('input', {'type': 'submit', 'value': lambda x: x and '再構築' in x})
            
            if rebuild_forms or rebuild_buttons:
                print("✅ 再構築機能が利用可能です")
                return True
            else:
                print("⚠️  再構築機能が見つかりません")
                print("MovableTypeの設定を確認してください")
                return False
        else:
            print("❌ ログインに失敗したため、再構築テストをスキップ")
            return False
            
    except Exception as e:
        print(f"❌ 再構築テストエラー: {e}")
        return False

def main():
    """メイン関数"""
    print("=== MovableType接続テスト ===")
    
    # 基本接続テスト
    if test_mt_connection():
        print("\n✅ 基本接続テスト成功")
        
        # 再構築機能テスト
        if test_rebuild_trigger():
            print("\n✅ 再構築機能テスト成功")
            print("\n🎉 すべてのテストが成功しました！")
            print("MovableType再構築ツールが正常に動作するはずです。")
        else:
            print("\n⚠️  再構築機能テストに問題があります")
            print("MovableTypeの設定を確認してください。")
    else:
        print("\n❌ 接続テストに失敗しました")
        print("設定を確認してから再実行してください。")
        sys.exit(1)

if __name__ == "__main__":
    main()
