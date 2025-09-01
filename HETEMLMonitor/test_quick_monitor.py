#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
クイック監視テストスクリプト
初回実行で履歴を作成し、2回目で新規ファイルを検出
"""

import os
import sys
import time
from datetime import datetime

# 設定ファイルのインポート
try:
    from config import HETEML_CONFIG, MONITOR_CONFIG, NOTIFICATION_CONFIG
except ImportError:
    print("設定ファイルが見つかりません。")
    sys.exit(1)

from heteml_monitor import HETEMLMonitor

def test_quick_monitor():
    """クイック監視テスト"""
    print("🚀 クイック監視テスト開始")
    print(f"監視対象: {MONITOR_CONFIG['target_path']}")
    print(f"通知方法: {NOTIFICATION_CONFIG.get('methods', [])}")
    print("-" * 50)
    
    try:
        # 監視システムの初期化
        monitor = HETEMLMonitor()
        
        # 1回目: 初回実行（履歴作成のみ）
        print("📡 1回目実行: 履歴作成中...")
        start_time = time.time()
        monitor.monitor_once()
        end_time = time.time()
        print(f"⏱️  1回目実行時間: {end_time - start_time:.2f}秒")
        
        # 2回目: 新規ファイル検出テスト
        print("\n📡 2回目実行: 新規ファイル検出テスト...")
        start_time = time.time()
        monitor.monitor_once()
        end_time = time.time()
        print(f"⏱️  2回目実行時間: {end_time - start_time:.2f}秒")
        
        print("\n✅ テスト完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quick_monitor()
