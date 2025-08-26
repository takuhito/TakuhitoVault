#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
メール通知テストスクリプト
メール通知が正しく動作するかテストします。
"""

import os
import sys
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

def test_email_connection():
    """メールサーバー接続テスト"""
    print("🔍 メールサーバー接続テストを開始します...")
    
    # 環境変数の取得
    smtp_server = 'smtp.gmail.com'  # デフォルトはGmail
    smtp_port = 587
    username = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')
    
    if not username or not password:
        print("❌ EMAIL_USERNAME または EMAIL_PASSWORD が設定されていません")
        print(".env ファイルにメール設定を追加してください")
        return False
    
    try:
        # SMTPサーバーへの接続テスト
        print(f"接続先: {smtp_server}:{smtp_port}")
        print(f"ユーザー: {username}")
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        # 認証テスト
        server.login(username, password)
        print("✅ SMTP認証に成功しました！")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ 認証に失敗しました")
        print("以下を確認してください：")
        print("1. ユーザー名とパスワードが正しいか")
        print("2. Gmailの場合はアプリパスワードを使用しているか")
        print("3. 2段階認証が有効になっているか")
        return False
        
    except smtplib.SMTPConnectError:
        print("❌ SMTPサーバーに接続できませんでした")
        print("以下を確認してください：")
        print("1. インターネット接続")
        print("2. SMTPサーバー名とポート番号")
        print("3. ファイアウォール設定")
        return False
        
    except Exception as e:
        print(f"❌ 接続テスト中にエラーが発生: {e}")
        return False

def test_email_send():
    """メール送信テスト"""
    print("\n🔍 メール送信テストを開始します...")
    
    # 環境変数の取得
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    username = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')
    from_email = os.getenv('FROM_EMAIL')
    to_email = os.getenv('TO_EMAIL')
    
    if not all([username, password, from_email, to_email]):
        print("❌ メール設定が不完全です")
        print("以下が設定されているか確認してください：")
        print("- EMAIL_USERNAME")
        print("- EMAIL_PASSWORD")
        print("- FROM_EMAIL")
        print("- TO_EMAIL")
        return False
    
    try:
        # メールの作成
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "🧪 HETEMLサーバ監視システム - メール通知テスト"
        
        # テストメッセージの作成
        test_message = f"""
🧪 HETEMLサーバ監視システム - メール通知テスト

テスト時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ メール通知が正常に動作しています！
HETEMLサーバの監視システムが準備完了です。

このメールが受信できれば、メール通知の設定は正常です。
        """.strip()
        
        msg.attach(MIMEText(test_message, 'plain', 'utf-8'))
        
        # SMTPサーバーへの接続と送信
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        
        # 送信
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        print("✅ メール送信テストに成功しました！")
        print(f"送信先: {to_email}")
        print("メールボックスでテストメールを確認してください。")
        return True
        
    except Exception as e:
        print(f"❌ メール送信テストに失敗しました: {e}")
        return False

def show_email_config():
    """メール設定の表示"""
    print("📋 現在のメール設定:")
    print(f"  SMTPサーバー: smtp.gmail.com:587")
    print(f"  ユーザー名: {os.getenv('EMAIL_USERNAME', '未設定')}")
    print(f"  送信元: {os.getenv('FROM_EMAIL', '未設定')}")
    print(f"  送信先: {os.getenv('TO_EMAIL', '未設定')}")
    print()

def show_setup_instructions():
    """設定手順の表示"""
    print("\n📋 メール通知の設定手順:")
    print("=" * 50)
    print("1. Gmailを使用する場合（推奨）:")
    print("   - Googleアカウントで2段階認証を有効化")
    print("   - アプリパスワードを生成")
    print("   - .env ファイルに設定を追加")
    print()
    print("2. その他のメールサービス:")
    print("   - メールサーバー情報を確認")
    print("   - config.py でSMTP設定を変更")
    print("   - .env ファイルに認証情報を追加")
    print()
    print("詳細は email_setup_guide.md を参照してください")

def main():
    """メイン関数"""
    print("🚀 HETEMLサーバ監視システム - メール通知テスト")
    print("=" * 50)
    
    # メール設定の表示
    show_email_config()
    
    # 環境変数の確認
    email_username = os.getenv('EMAIL_USERNAME')
    email_password = os.getenv('EMAIL_PASSWORD')
    
    if not email_username or not email_password:
        print("❌ メール通知の設定が見つかりません")
        show_setup_instructions()
        return
    
    # 接続テスト
    connection_success = test_email_connection()
    
    # 送信テスト
    if connection_success:
        send_success = test_email_send()
    else:
        print("⚠️  接続テストに失敗したため、送信テストをスキップします")
        send_success = False
    
    print("\n" + "=" * 50)
    print("📊 テスト結果:")
    print(f"  SMTP接続: {'✅ 成功' if connection_success else '❌ 失敗'}")
    print(f"  メール送信: {'✅ 成功' if send_success else '❌ 失敗'}")
    
    if connection_success and send_success:
        print("\n🎉 メール通知の設定が完了しました！")
        print("監視システムを開始できます: python heteml_monitor.py")
    else:
        print("\n⚠️  メール通知の設定に問題があります")
        show_setup_instructions()

if __name__ == "__main__":
    main()
