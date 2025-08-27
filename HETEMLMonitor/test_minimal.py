#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小限のテストスクリプト
最も基本的な動作のみを確認します。
"""

import os
import sys

def main():
    """メイン関数"""
    print("🔍 最小限テスト開始")
    
    # 1. 基本的なPython動作
    print("✅ Python動作確認")
    
    # 2. ディレクトリ確認
    print(f"📁 現在のディレクトリ: {os.getcwd()}")
    
    # 3. ファイル一覧（最初の5個のみ）
    try:
        files = os.listdir('.')
        print(f"📄 ファイル数: {len(files)}")
        for i, file in enumerate(files[:5]):
            print(f"  {i+1}. {file}")
        if len(files) > 5:
            print(f"  ... 他 {len(files)-5} ファイル")
    except Exception as e:
        print(f"❌ ファイル一覧エラー: {e}")
    
    # 4. 環境変数確認（設定されているもののみ）
    print("🌍 設定済み環境変数:")
    env_vars = ['HETEML_PASSWORD', 'EMAIL_USERNAME', 'EMAIL_PASSWORD', 'FROM_EMAIL', 'TO_EMAIL']
    set_count = 0
    for var in env_vars:
        if os.getenv(var):
            set_count += 1
    print(f"  ✅ {set_count}/{len(env_vars)} 個の環境変数が設定済み")
    
    # 5. config.pyの存在確認
    config_exists = os.path.exists('config.py')
    print(f"📄 config.py: {'✅ 存在' if config_exists else '❌ 存在しない'}")
    
    print("✅ 最小限テスト完了")
    return True

if __name__ == "__main__":
    try:
        success = main()
        print("🎉 テスト成功")
        sys.exit(0)
    except Exception as e:
        print(f"💥 エラー: {e}")
        sys.exit(1)
