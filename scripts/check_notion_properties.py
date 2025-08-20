#!/usr/bin/env python3
"""
既存のNotionデータベースのプロパティ構造を確認するスクリプト
"""
import os
import sys
import json

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'receipt-processor'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import importlib.util
spec = importlib.util.spec_from_file_location("notion_api_client", os.path.join(os.path.dirname(__file__), '..', 'receipt-processor', 'notion_api_client.py'))
notion_client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notion_client_module)
ReceiptNotionClient = notion_client_module.NotionClient

def check_database_properties():
    """データベースのプロパティ構造を確認"""
    
    print("🔍 既存データベースのプロパティ構造確認")
    print("=" * 50)
    
    try:
        notion_client = ReceiptNotionClient()
        database_info = notion_client.get_database_info()
        
        print(f"📊 データベース名: {database_info.get('title', 'Unknown')}")
        print(f"📊 プロパティ数: {len(database_info.get('properties', {}))}")
        print()
        
        properties = database_info.get('properties', {})
        
        print("📋 既存のプロパティ一覧:")
        print("-" * 40)
        
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get('type', 'unknown')
            print(f"• {prop_name} ({prop_type})")
            
            # Selectタイプの場合はオプションも表示
            if prop_type == 'select' and 'select' in prop_info:
                options = prop_info['select'].get('options', [])
                if options:
                    print(f"  オプション: {[opt.get('name', '') for opt in options]}")
            
            # Multi-selectタイプの場合はオプションも表示
            elif prop_type == 'multi_select' and 'multi_select' in prop_info:
                options = prop_info['multi_select'].get('options', [])
                if options:
                    print(f"  オプション: {[opt.get('name', '') for opt in options]}")
        
        print()
        
        # 必要なプロパティとの比較
        required_properties = {
            '店舗名': 'title',
            '日付': 'date', 
            '金額': 'number',
            'カテゴリ': 'select',
            '勘定科目': 'select',
            '商品一覧': 'rich_text',
            '処理状況': 'select',
            '信頼度': 'number'
        }
        
        print("📋 必要なプロパティとの比較:")
        print("-" * 40)
        
        missing_properties = []
        type_mismatches = []
        
        for required_name, required_type in required_properties.items():
            if required_name in properties:
                actual_type = properties[required_name].get('type', 'unknown')
                if actual_type != required_type:
                    type_mismatches.append((required_name, required_type, actual_type))
                    print(f"⚠️  {required_name}: 期待={required_type}, 実際={actual_type}")
                else:
                    print(f"✅ {required_name}: {required_type}")
            else:
                missing_properties.append(required_name)
                print(f"❌ {required_name}: {required_type} (不足)")
        
        print()
        
        if missing_properties:
            print("📝 不足しているプロパティの追加方法:")
            for prop_name in missing_properties:
                prop_type = required_properties[prop_name]
                print(f"• {prop_name} ({prop_type})")
        
        if type_mismatches:
            print("\n📝 タイプの不一致があるプロパティ:")
            for prop_name, expected_type, actual_type in type_mismatches:
                print(f"• {prop_name}: {actual_type} → {expected_type} に変更が必要")
        
        # 既存のプロパティ名のマッピング提案
        print("\n📋 既存プロパティとのマッピング提案:")
        print("-" * 40)
        
        existing_names = list(properties.keys())
        
        for required_name, required_type in required_properties.items():
            if required_name not in properties:
                # 類似名を探す
                similar_names = [name for name in existing_names 
                               if any(word in name.lower() for word in required_name.lower().split())]
                
                if similar_names:
                    print(f"• {required_name} → {similar_names[0]} (類似名)")
                else:
                    print(f"• {required_name} → 新規作成が必要")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    check_database_properties()
