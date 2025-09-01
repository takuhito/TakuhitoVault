#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新規ファイル通知テストスクリプト
履歴がある状態で新規ファイルを検出して通知をテスト
"""

import os
import sys
import time
import logging
from datetime import datetime

# 設定ファイルのインポート
try:
    from config import HETEML_CONFIG, MONITOR_CONFIG, NOTIFICATION_CONFIG
except ImportError:
    print("設定ファイルが見つかりません。")
    sys.exit(1)

from heteml_monitor import HETEMLMonitor

def test_new_file_notification():
    """新規ファイル通知テスト"""
    print("🔔 新規ファイル通知テスト開始")
    print(f"監視対象: {MONITOR_CONFIG['target_path']}")
    print(f"通知方法: {NOTIFICATION_CONFIG.get('methods', [])}")
    print("-" * 50)
    
    try:
        # 監視システムの初期化
        monitor = HETEMLMonitor()
        
        # 現在のファイル履歴を確認
        print(f"📊 現在の履歴ファイル数: {len(monitor.known_files)}")
        
        # 監視実行
        print("\n📡 監視実行中...")
        start_time = time.time()
        monitor.monitor_once()
        end_time = time.time()
        print(f"⏱️  実行時間: {end_time - start_time:.2f}秒")
        
        print("\n✅ テスト完了")
        print("📧 メール通知が送信された場合は、受信トレイを確認してください")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_file_notification()
