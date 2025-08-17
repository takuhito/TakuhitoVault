# -*- coding: utf-8 -*-
"""
ChatGPT Export Helper - ChatGPTデスクトップアプリデータ取得ヘルパー
ChatGPTデスクトップアプリからチャット履歴を取得するためのヘルパーツールです。
"""

import os
import sys
import json
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

def find_chatgpt_data_dir() -> Optional[Path]:
    """ChatGPTデスクトップアプリのデータディレクトリを検索"""
    possible_paths = [
        Path.home() / "Library" / "Application Support" / "com.openai.chat",
        Path.home() / "Library" / "Application Support" / "ChatGPT",
        Path.home() / "AppData" / "Roaming" / "ChatGPT",
        Path.home() / ".config" / "ChatGPT"
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"ChatGPTデータディレクトリ発見: {path}")
            return path
    
    print("ChatGPTデータディレクトリが見つかりませんでした。")
    return None

def find_conversations_dir(data_dir: Path) -> Optional[Path]:
    """会話データディレクトリを検索"""
    # conversations-v3-* パターンのディレクトリを検索
    for item in data_dir.iterdir():
        if item.is_dir() and item.name.startswith("conversations-v3-"):
            print(f"会話データディレクトリ発見: {item}")
            return item
    
    print("会話データディレクトリが見つかりませんでした。")
    return None

def export_chatgpt_data(output_file: str = "chatgpt_export.json"):
    """ChatGPTデータをエクスポート"""
    print("ChatGPTデータエクスポート開始...")
    
    data_dir = find_chatgpt_data_dir()
    if not data_dir:
        print("ChatGPTデータディレクトリが見つかりません。")
        return False
    
    conversations_dir = find_conversations_dir(data_dir)
    if not conversations_dir:
        print("会話データディレクトリが見つかりません。")
        return False
    
    # データファイルをコピーして解析を試行
    temp_dir = Path("temp_chatgpt_data")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # データファイルをコピー
        for data_file in conversations_dir.glob("*.data"):
            shutil.copy2(data_file, temp_dir / data_file.name)
        
        print(f"{len(list(temp_dir.glob('*.data')))}個のデータファイルをコピーしました。")
        
        # データファイルの解析を試行
        conversations = []
        
        for data_file in temp_dir.glob("*.data"):
            try:
                # ファイルの内容を確認
                with open(data_file, 'rb') as f:
                    content = f.read()
                
                # 暗号化されているかチェック
                if content.startswith(b'\x27\xdb\x60\xa5'):  # 暗号化されたデータの特徴
                    print(f"暗号化されたデータファイル: {data_file.name}")
                    continue
                
                # JSONとして解析を試行
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict):
                        conversations.append(data)
                    elif isinstance(data, list):
                        conversations.extend(data)
                    
                    print(f"成功: {data_file.name}")
                    
                except (json.JSONDecodeError, UnicodeDecodeError):
                    print(f"JSON解析失敗: {data_file.name}")
                    continue
                    
            except Exception as e:
                print(f"ファイル処理エラー {data_file.name}: {e}")
                continue
        
        if conversations:
            # エクスポートファイルに保存
            export_data = {
                "export_date": datetime.now().isoformat(),
                "source": "ChatGPT Desktop App",
                "conversations": conversations
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"エクスポート完了: {output_file}")
            print(f"会話数: {len(conversations)}")
            return True
        else:
            print("解析可能な会話データが見つかりませんでした。")
            return False
            
    finally:
        # 一時ファイルを削除
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def create_sample_export():
    """サンプルエクスポートファイルを作成"""
    sample_data = {
        "export_date": datetime.now().isoformat(),
        "source": "Sample Data",
        "conversations": [
            {
                "id": "sample-chat-1",
                "title": "サンプルチャット1",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T11:00:00Z",
                "model": "GPT-4",
                "messages": [
                    {
                        "role": "user",
                        "content": "こんにちは、ChatGPTについて教えてください。",
                        "timestamp": "2024-01-01T10:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "ChatGPTは、OpenAIが開発した大規模言語モデルです。自然言語での対話が可能で、様々なタスクを支援できます。",
                        "timestamp": "2024-01-01T10:01:00Z"
                    }
                ]
            },
            {
                "id": "sample-chat-2",
                "title": "プログラミングの質問",
                "created_at": "2024-01-02T14:00:00Z",
                "updated_at": "2024-01-02T15:30:00Z",
                "model": "GPT-3.5",
                "messages": [
                    {
                        "role": "user",
                        "content": "Pythonでファイルを読み込む方法を教えてください。",
                        "timestamp": "2024-01-02T14:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "Pythonでファイルを読み込むには、`open()`関数を使用します。例：`with open('file.txt', 'r') as f: content = f.read()`",
                        "timestamp": "2024-01-02T14:01:00Z"
                    }
                ]
            }
        ]
    }
    
    with open("sample_chatgpt_export.json", 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    print("サンプルエクスポートファイルを作成しました: sample_chatgpt_export.json")

def main():
    """メイン処理"""
    print("ChatGPT Export Helper")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python chatgpt_export_helper.py export [出力ファイル名]")
        print("  python chatgpt_export_helper.py sample")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "export":
        output_file = sys.argv[2] if len(sys.argv) > 2 else "chatgpt_export.json"
        success = export_chatgpt_data(output_file)
        if success:
            print(f"\nエクスポートが完了しました: {output_file}")
            print("このファイルを chatgpt_to_notion.py で処理できます。")
        else:
            print("\nエクスポートに失敗しました。")
            print("ChatGPTデスクトップアプリがインストールされているか確認してください。")
    
    elif command == "sample":
        create_sample_export()
        print("\nサンプルファイルを作成しました。")
        print("このファイルで chatgpt_to_notion.py の動作をテストできます。")
    
    else:
        print(f"不明なコマンド: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
