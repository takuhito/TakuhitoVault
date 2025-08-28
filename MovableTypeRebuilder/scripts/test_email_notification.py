#!/usr/bin/env python3
"""
MovableType再構築システム - メール通知テストスクリプト
"""

import os
import sys
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def test_email_connection():
    """メール接続テスト"""
    print("🔍 メール接続テストを開始します...")
    
    # 環境変数の取得
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    username = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')
    
    if not username or not password:
        print("❌ メール認証情報が設定されていません")
        print("EMAIL_USERNAME と EMAIL_PASSWORD を設定してください")
        return False
    
    try:
        # SMTPサーバーへの接続テスト
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.quit()
        
        print("✅ メール接続テストに成功しました！")
        return True
        
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
        msg['Subject'] = "🧪 MovableType再構築システム - メール通知テスト"
        
        # テストメッセージの作成
        test_message = f"""
🧪 MovableType再構築システム - メール通知テスト

テスト時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ メール通知が正常に動作しています！
MovableType再構築システムが準備完了です。

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
        print(f"❌ メール送信テストに失敗: {e}")
        return False

def main():
    """メイン関数"""
    print("=== MovableType再構築システム - メール通知テスト ===")
    
    # 環境変数の読み込み
    load_dotenv()
    
    # 接続テスト
    if test_email_connection():
        # 送信テスト
        if test_email_send():
            print("\n🎉 すべてのテストが成功しました！")
            print("MovableType再構築システムのメール通知が正常に動作します。")
        else:
            print("\n❌ メール送信テストに失敗しました")
            sys.exit(1)
    else:
        print("\n❌ メール接続テストに失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main()
