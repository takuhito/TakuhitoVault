#!/usr/bin/env python3
"""
MovableTypeログイン詳細デバッグスクリプト
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

def debug_mt_login():
    """MovableTypeログインの詳細デバッグ"""
    load_dotenv()
    
    # 設定読み込み
    mt_url = os.getenv('MT_SITE_URL')
    mt_username = os.getenv('MT_USERNAME')
    mt_password = os.getenv('MT_PASSWORD')
    
    print(f"=== MovableTypeログインデバッグ ===")
    print(f"サイトURL: {mt_url}")
    print(f"ユーザー名: {mt_username}")
    print(f"パスワード: {'***' if mt_password else '未設定'}")
    
    try:
        session = requests.Session()
        
        # 1. ログインページにアクセス
        print("\n1. ログインページにアクセス...")
        response = session.get(mt_url, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンスサイズ: {len(response.text)} bytes")
        
        # レスポンスの一部を表示
        print("\nレスポンスの最初の500文字:")
        print(response.text[:500])
        
        # 2. フォーム要素を確認
        print("\n2. フォーム要素を確認...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # フォームを探す
        forms = soup.find_all('form')
        print(f"見つかったフォーム数: {len(forms)}")
        
        for i, form in enumerate(forms):
            print(f"\nフォーム {i+1}:")
            print(f"  action: {form.get('action', 'N/A')}")
            print(f"  method: {form.get('method', 'N/A')}")
            
            # 入力フィールドを確認
            inputs = form.find_all('input')
            print(f"  入力フィールド数: {len(inputs)}")
            for inp in inputs:
                print(f"    - name: {inp.get('name', 'N/A')}, type: {inp.get('type', 'N/A')}")
        
        # 3. ログイン試行
        print("\n3. ログイン試行...")
        login_data = {
            'username': mt_username,
            'password': mt_password,
            '__mode': 'login'
        }
        
        print(f"送信データ: {login_data}")
        
        response = session.post(mt_url, data=login_data, timeout=30)
        print(f"ログイン後ステータスコード: {response.status_code}")
        print(f"ログイン後レスポンスサイズ: {len(response.text)} bytes")
        
        # ログイン結果を確認
        print("\nログイン結果の最初の500文字:")
        print(response.text[:500])
        
        # 成功/失敗の判定
        success_indicators = ['ログアウト', 'logout', 'dashboard', '管理画面']
        failure_indicators = ['ログイン', 'login', 'エラー', 'error', '失敗']
        
        success_count = sum(1 for indicator in success_indicators if indicator.lower() in response.text.lower())
        failure_count = sum(1 for indicator in failure_indicators if indicator.lower() in response.text.lower())
        
        print(f"\n成功指標の出現回数: {success_count}")
        print(f"失敗指標の出現回数: {failure_count}")
        
        if success_count > failure_count:
            print("✅ ログイン成功の可能性が高い")
        else:
            print("❌ ログイン失敗の可能性が高い")
            
        # 4. セッション情報を確認
        print(f"\n4. セッション情報:")
        print(f"  クッキー数: {len(session.cookies)}")
        for cookie in session.cookies:
            print(f"    - {cookie.name}: {cookie.value[:20]}...")
            
    except Exception as e:
        print(f"❌ エラーが発生: {e}")

if __name__ == "__main__":
    debug_mt_login()
