#!/usr/bin/env python3
"""
MovableType再構築機能テストスクリプト
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

def test_rebuild_function():
    """再構築機能のテスト"""
    load_dotenv()
    
    # 設定読み込み
    mt_url = os.getenv('MT_SITE_URL')
    mt_username = os.getenv('MT_USERNAME')
    mt_password = os.getenv('MT_PASSWORD')
    mt_blog_id = os.getenv('MT_BLOG_ID', '45')
    mt_site_name = os.getenv('MT_SITE_NAME', '公演カレンダー')
    
    print(f"=== MovableType再構築機能テスト ===")
    print(f"対象サイト: {mt_site_name} (blog_id: {mt_blog_id})")
    
    try:
        session = requests.Session()
        
        # 1. ログイン試行
        print("\n1. ログイン試行...")
        login_data = {
            'username': mt_username,
            'password': mt_password,
            '__mode': 'login'
        }
        
        response = session.post(mt_url, data=login_data, timeout=30)
        print(f"ログイン後ステータスコード: {response.status_code}")
        
        # 2. 再構築ページへのアクセス
        print("\n2. 再構築ページへのアクセス...")
        rebuild_url = f"{mt_url}?__mode=rebuild&blog_id={mt_blog_id}"
        response = session.get(rebuild_url, timeout=30)
        print(f"再構築ページステータスコード: {response.status_code}")
        print(f"レスポンスサイズ: {len(response.text)} bytes")
        
        # 3. 再構築ページの内容確認
        print("\n3. 再構築ページの内容確認...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # フォームを探す
        forms = soup.find_all('form')
        print(f"見つかったフォーム数: {len(forms)}")
        
        rebuild_forms = []
        for i, form in enumerate(forms):
            action = form.get('action', '')
            if 'rebuild' in action.lower():
                rebuild_forms.append(form)
                print(f"再構築フォーム {len(rebuild_forms)}:")
                print(f"  action: {action}")
                print(f"  method: {form.get('method', 'N/A')}")
                
                # 入力フィールドを確認
                inputs = form.find_all('input')
                for inp in inputs:
                    name = inp.get('name', 'N/A')
                    value = inp.get('value', 'N/A')
                    if 'blog_id' in name or 'type' in name:
                        print(f"    - {name}: {value}")
        
        # 4. 再構築ボタンの確認
        print("\n4. 再構築ボタンの確認...")
        rebuild_buttons = soup.find_all('input', {'type': 'submit'})
        print(f"再構築ボタン数: {len(rebuild_buttons)}")
        
        for i, button in enumerate(rebuild_buttons):
            value = button.get('value', 'N/A')
            if '再構築' in value or 'rebuild' in value.lower():
                print(f"  再構築ボタン {i+1}: {value}")
        
        # 5. エラーメッセージの確認
        print("\n5. エラーメッセージの確認...")
        error_indicators = ['エラー', 'error', '権限', 'permission', 'アクセス拒否', 'access denied']
        found_errors = []
        
        for indicator in error_indicators:
            if indicator.lower() in response.text.lower():
                found_errors.append(indicator)
        
        if found_errors:
            print(f"見つかったエラー: {', '.join(found_errors)}")
        else:
            print("エラーメッセージは見つかりませんでした")
        
        # 6. 成功メッセージの確認
        print("\n6. 成功メッセージの確認...")
        success_indicators = ['再構築', 'rebuild', '完了', 'complete', 'success']
        found_success = []
        
        for indicator in success_indicators:
            if indicator.lower() in response.text.lower():
                found_success.append(indicator)
        
        if found_success:
            print(f"見つかった成功指標: {', '.join(found_success)}")
        else:
            print("成功指標は見つかりませんでした")
        
        # 7. レスポンスの一部を表示
        print("\n7. レスポンスの一部:")
        print(response.text[:1000])
        
    except Exception as e:
        print(f"❌ エラーが発生: {e}")

if __name__ == "__main__":
    test_rebuild_function()
