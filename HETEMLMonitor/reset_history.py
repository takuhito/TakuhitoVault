#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ファイル履歴リセットスクリプト
既存のファイル履歴をクリアして、新規ファイルのみを検出するようにする
"""

import os
import json
from datetime import datetime

def reset_file_history():
    """ファイル履歴をリセット"""
    history_file = 'file_history.json'
    
    print("🔄 ファイル履歴をリセット中...")
    
    # バックアップを作成
    if os.path.exists(history_file):
        backup_file = f"file_history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.rename(history_file, backup_file)
        print(f"✅ バックアップ作成: {backup_file}")
    
    # 空の履歴ファイルを作成
    empty_history = {
        "files": [],
        "hashes": {},
        "last_updated": datetime.now().isoformat()
    }
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(empty_history, f, ensure_ascii=False, indent=2)
    
    print("✅ ファイル履歴をリセットしました")
    print("📝 次回実行時は全てのファイルが新規ファイルとして検出されます")

if __name__ == "__main__":
    reset_file_history()
