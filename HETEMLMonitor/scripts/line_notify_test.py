#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LINE通知テストスクリプト
LINE通知が正しく動作するかテストします。
"""

import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

def test_line_notify():
    """LINE Notify を使用した通知テスト"""
    print("🔍 LINE Notify テストを開始します...")
    
    # LINE Notify トークンの取得
    line_notify_token = os.getenv('LINE_NOTIFY_TOKEN')
    
    if not line_notify_token:
        print("❌ LINE_NOTIFY_TOKEN が設定されていません")
        print("LINE Notify でトークンを発行して .env ファイルに設定してください")
        return False
    
    try:
        # LINE Notify API でメッセージ送信
        headers = {
            'Authorization': f'Bearer {line_notify_token}'
        }
        
        test_message = f"""
🧪 HETEMLサーバ監視システム - LINE通知テスト

テスト時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ LINE通知が正常に動作しています！
HETEMLサーバの監視システムが準備完了です。
        """.strip()
        
        data = {
            'message': test_message
        }
        
        response = requests.post(
            'https://notify-api.line.me/api/notify',
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            print("✅ LINE Notify テストに成功しました！")
            print("LINEアプリで通知を確認してください。")
            return True
        else:
            print(f"❌ LINE Notify テストに失敗しました: {response.status_code}")
            print(f"エラー内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ LINE Notify テスト中にエラーが発生: {e}")
        return False

def test_line_messaging_api():
    """LINE Messaging API を使用した通知テスト"""
    print("\n🔍 LINE Messaging API テストを開始します...")
    
    # LINE Messaging API の設定
    channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    user_id = os.getenv('LINE_USER_ID')
    
    if not channel_access_token:
        print("❌ LINE_CHANNEL_ACCESS_TOKEN が設定されていません")
        return False
    
    if not user_id:
        print("❌ LINE_USER_ID が設定されていません")
        return False
    
    try:
        # LINE Messaging API でメッセージ送信
        headers = {
            'Authorization': f'Bearer {channel_access_token}',
            'Content-Type': 'application/json'
        }
        
        test_message = f"""
🧪 HETEMLサーバ監視システム - LINE Messaging API テスト

テスト時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ LINE Messaging API が正常に動作しています！
HETEMLサーバの監視システムが準備完了です。
        """.strip()
        
        data = {
            'to': user_id,
            'messages': [
                {
                    'type': 'text',
                    'text': test_message
                }
            ]
        }
        
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            print("✅ LINE Messaging API テストに成功しました！")
            print("LINEアプリで通知を確認してください。")
            return True
        else:
            print(f"❌ LINE Messaging API テストに失敗しました: {response.status_code}")
            print(f"エラー内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ LINE Messaging API テスト中にエラーが発生: {e}")
        return False

def show_setup_instructions():
    """設定手順の表示"""
    print("\n📋 LINE通知の設定手順:")
    print("=" * 50)
    print("1. LINE Notify を使用する場合（推奨）:")
    print("   - https://notify-bot.line.me/ja/ にアクセス")
    print("   - トークンを発行")
    print("   - .env ファイルに LINE_NOTIFY_TOKEN=your-token を追加")
    print()
    print("2. LINE Messaging API を使用する場合:")
    print("   - https://developers.line.biz/console/ でBotチャンネル作成")
    print("   - チャンネルアクセストークンを取得")
    print("   - ユーザーIDを取得")
    print("   - .env ファイルに設定を追加")
    print()
    print("詳細は line_setup_guide.md を参照してください")

def main():
    """メイン関数"""
    print("🚀 HETEMLサーバ監視システム - LINE通知テスト")
    print("=" * 50)
    
    # 環境変数の確認
    line_notify_token = os.getenv('LINE_NOTIFY_TOKEN')
    channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    
    if not line_notify_token and not channel_access_token:
        print("❌ LINE通知の設定が見つかりません")
        show_setup_instructions()
        return
    
    # LINE Notify テスト
    if line_notify_token:
        notify_success = test_line_notify()
    else:
        print("⚠️  LINE Notify トークンが設定されていません")
        notify_success = False
    
    # LINE Messaging API テスト
    if channel_access_token:
        api_success = test_line_messaging_api()
    else:
        print("⚠️  LINE Messaging API トークンが設定されていません")
        api_success = False
    
    print("\n" + "=" * 50)
    print("📊 テスト結果:")
    print(f"  LINE Notify: {'✅ 成功' if notify_success else '❌ 失敗'}")
    print(f"  LINE Messaging API: {'✅ 成功' if api_success else '❌ 失敗'}")
    
    if notify_success or api_success:
        print("\n🎉 LINE通知の設定が完了しました！")
        print("監視システムを開始できます: python heteml_monitor.py")
    else:
        print("\n⚠️  LINE通知の設定に問題があります")
        show_setup_instructions()

if __name__ == "__main__":
    main()
