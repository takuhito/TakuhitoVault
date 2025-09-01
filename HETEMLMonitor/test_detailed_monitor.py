#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細監視テストスクリプト
デバッグレベルで詳細なログを出力
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

def test_detailed_monitor():
    """詳細監視テスト"""
    print("🔍 詳細監視テスト開始")
    print(f"監視対象: {MONITOR_CONFIG['target_path']}")
    print(f"通知方法: {NOTIFICATION_CONFIG.get('methods', [])}")
    print("-" * 50)
    
    # ログレベルをDEBUGに設定
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        # 監視システムの初期化
        monitor = HETEMLMonitor()
        
        # 現在のファイル履歴を確認
        print(f"📊 現在の履歴ファイル数: {len(monitor.known_files)}")
        
        # 1回だけ監視実行
        print("\n📡 監視実行中...")
        start_time = time.time()
        monitor.monitor_once()
        end_time = time.time()
        print(f"⏱️  実行時間: {end_time - start_time:.2f}秒")
        
        print("\n✅ テスト完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_detailed_monitor()
