#!/usr/bin/env python3
"""
ローカル環境用の領収書自動処理システム
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any

from config import validate_settings, GOOGLE_DRIVE_MONITOR_FOLDER
from google_drive_client import GoogleDriveClient
from notion_api_client import NotionClient

def process_receipt_file(file_info: Dict[str, Any], google_drive_client: GoogleDriveClient, notion_client: NotionClient) -> bool:
    """
    領収書ファイルを処理
    
    Args:
        file_info: ファイル情報
        google_drive_client: Google Driveクライアント
        notion_client: Notionクライアント
        
    Returns:
        bool: 処理成功時True
    """
    file_id = file_info['id']
    file_name = file_info['name']
    
    print(f"🔄 処理開始: {file_name}")
    
    try:
        # ファイルをダウンロード
        file_path = google_drive_client.download_file(file_id, file_name)
        if not file_path:
            print(f"❌ ファイルダウンロード失敗: {file_name}")
            return False
        
        # 簡易的な領収書データを作成（実際のOCR処理は省略）
        receipt_data = {
            'store_name': f"店舗名（{file_name}）",
            'date': datetime.now().date(),
            'total_amount': 1000,  # 仮の金額
            'payment_amount': 1000,
            'payment_method': '現金',
            'category': '雑費',
            'notes': f"自動処理: {file_name}",
            'processing_status': '処理済み'
        }
        
        # Notionにページを作成
        page_id = notion_client.create_receipt_page(receipt_data)
        if not page_id:
            print(f"❌ Notionページ作成失敗: {file_name}")
            return False
        
        # 処理済みフォルダに移動
        processed_folder_id = "0AJojvkLIwToKUk9PVA"  # 処理済みフォルダID
        if google_drive_client.move_file(file_id, processed_folder_id):
            print(f"✅ 処理完了: {file_name} -> Notionページ: {page_id}")
            return True
        else:
            print(f"❌ ファイル移動失敗: {file_name}")
            return False
            
    except Exception as e:
        print(f"❌ 処理エラー: {file_name}, {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 ローカル領収書自動処理システム開始")
    print("=" * 60)
    
    # 設定の検証
    errors = validate_settings()
    if errors:
        print("❌ 設定エラー:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    try:
        # クライアントの初期化
        print("🔧 クライアント初期化中...")
        google_drive_client = GoogleDriveClient()
        notion_client = NotionClient()
        
        # Notion接続テスト
        if not notion_client.test_connection():
            print("❌ Notion接続テスト失敗")
            return False
        
        # 新規ファイルの取得
        print("📁 新規ファイル検索中...")
        new_files = google_drive_client.get_new_files()
        
        if not new_files:
            print("📭 処理対象のファイルがありません")
            return True
        
        print(f"📄 処理対象ファイル数: {len(new_files)}")
        
        # ファイルを処理
        success_count = 0
        error_count = 0
        
        for file_info in new_files:
            if process_receipt_file(file_info, google_drive_client, notion_client):
                success_count += 1
            else:
                error_count += 1
        
        print("\n" + "=" * 60)
        print(f"✅ 処理完了 - 成功: {success_count}, 失敗: {error_count}")
        
        return error_count == 0
        
    except Exception as e:
        print(f"❌ システムエラー: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
