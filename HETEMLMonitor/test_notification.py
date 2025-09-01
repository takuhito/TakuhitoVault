#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知テストスクリプト
新規ファイル検出時の通知をテスト
"""

import os
import sys
from datetime import datetime

# 設定ファイルのインポート
try:
    from config import HETEML_CONFIG, MONITOR_CONFIG, NOTIFICATION_CONFIG
except ImportError:
    print("設定ファイルが見つかりません。")
    sys.exit(1)

from heteml_monitor import HETEMLMonitor

def test_notification():
    """通知テスト"""
    print("🔔 通知テスト開始")
    print(f"監視対象: {MONITOR_CONFIG['target_path']}")
    print(f"通知方法: {NOTIFICATION_CONFIG.get('methods', [])}")
    print("-" * 50)
    
    try:
        # 監視システムの初期化
        monitor = HETEMLMonitor()
        
        # 1回だけ監視実行
        print("📡 監視実行中...")
        monitor.monitor_once()
        
        print("✅ 監視実行完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_notification()
