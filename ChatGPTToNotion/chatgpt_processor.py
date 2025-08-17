#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGPT Processor - 圧縮ファイル自動処理ツール
ChatGPTのエクスポートファイル（圧縮形式含む）を自動で処理します。
"""

import os
import sys
import json
import zipfile
import tarfile
import shutil
from pathlib import Path
from datetime import datetime
import glob

def extract_archive(archive_path: str, extract_dir: str = None) -> str:
    """圧縮ファイルを解凍"""
    if extract_dir is None:
        extract_dir = os.path.dirname(archive_path)
    
    archive_name = os.path.basename(archive_path)
    base_name = os.path.splitext(archive_name)[0]
    
    # 解凍先ディレクトリを作成
    extract_path = os.path.join(extract_dir, f"extracted_{base_name}")
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    os.makedirs(extract_path)
    
    print(f"圧縮ファイルを解凍中: {archive_path}")
    
    try:
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        elif archive_path.endswith(('.tar.gz', '.tgz')):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_path)
        elif archive_path.endswith('.tar'):
            with tarfile.open(archive_path, 'r') as tar_ref:
                tar_ref.extractall(extract_path)
        else:
            raise ValueError(f"サポートされていない圧縮形式: {archive_path}")
        
        print(f"解凍完了: {extract_path}")
        return extract_path
    
    except Exception as e:
        print(f"解凍エラー: {e}")
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        raise

def find_json_files(directory: str) -> list:
    """ディレクトリ内のJSONファイルを検索"""
    json_files = []
    
    # 直接のJSONファイル
    json_files.extend(glob.glob(os.path.join(directory, "*.json")))
    
    # サブディレクトリ内のJSONファイル
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    return json_files

def validate_chatgpt_export(json_file: str) -> bool:
    """ChatGPTエクスポートファイルかどうかを検証"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # ChatGPTエクスポートファイルの構造をチェック
        if isinstance(data, list):
            # リスト形式の場合、各要素に必要なフィールドがあるかチェック
            for item in data:
                if not isinstance(item, dict):
                    return False
                # 新しい形式: mappingフィールドがあるかチェック
                if 'mapping' in item:
                    return True
                # 古い形式: messagesフィールドがあるかチェック
                if 'messages' in item:
                    return True
            return False
        
        elif isinstance(data, dict):
            # 辞書形式の場合、conversationsフィールドがあるかチェック
            if 'conversations' in data:
                return True
            # または直接messagesフィールドがあるかチェック
            if 'messages' in data:
                return True
            # またはconversations.jsonファイルの場合（ファイル名で判定）
            if json_file.endswith('conversations.json'):
                return True
        
        return False
    
    except Exception as e:
        print(f"JSONファイル検証エラー ({json_file}): {e}")
        return False

def process_chatgpt_export(file_path: str) -> str:
    """ChatGPTエクスポートファイルを処理"""
    print(f"ファイル処理中: {file_path}")
    
    # 圧縮ファイルかどうかをチェック
    if file_path.endswith(('.zip', '.tar.gz', '.tgz', '.tar')):
        print("圧縮ファイルを検出しました。解凍を開始します...")
        extract_dir = extract_archive(file_path)
        
        # 解凍されたディレクトリ内のJSONファイルを検索
        json_files = find_json_files(extract_dir)
        
        if not json_files:
            raise ValueError(f"解凍されたディレクトリ内にJSONファイルが見つかりません: {extract_dir}")
        
        # ChatGPTエクスポートファイルを特定
        chatgpt_files = [f for f in json_files if validate_chatgpt_export(f)]
        
        if not chatgpt_files:
            raise ValueError(f"ChatGPTエクスポートファイルが見つかりません: {extract_dir}")
        
        if len(chatgpt_files) > 1:
            print(f"複数のChatGPTファイルが見つかりました。最初のファイルを使用します: {chatgpt_files[0]}")
        
        return chatgpt_files[0]
    
    else:
        # 通常のJSONファイルの場合
        if not validate_chatgpt_export(file_path):
            raise ValueError(f"ChatGPTエクスポートファイルではありません: {file_path}")
        
        return file_path

def main():
    """メイン処理"""
    print("ChatGPT Processor - 圧縮ファイル自動処理ツール")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("使用方法: python chatgpt_processor.py <ファイルまたはディレクトリ>")
        print("例: python chatgpt_processor.py chatgpt_export.zip")
        print("例: python chatgpt_processor.py .")
        sys.exit(1)
    
    target = sys.argv[1]
    
    try:
        if os.path.isfile(target):
            # 単一ファイルの処理
            json_file = process_chatgpt_export(target)
            print(f"処理可能なJSONファイル: {json_file}")
            
            # chatgpt_to_notion.pyを呼び出し
            print("\nNotionへの同期を開始します...")
            os.system(f"python chatgpt_to_notion.py '{json_file}'")
            
        elif os.path.isdir(target):
            # ディレクトリ内のファイルを処理
            print(f"ディレクトリ内のファイルを検索中: {target}")
            
            # 圧縮ファイルを検索
            archive_files = []
            for ext in ['*.zip', '*.tar.gz', '*.tgz', '*.tar']:
                archive_files.extend(glob.glob(os.path.join(target, ext)))
            
            # JSONファイルを検索
            json_files = glob.glob(os.path.join(target, "*.json"))
            
            all_files = archive_files + json_files
            
            if not all_files:
                print(f"処理可能なファイルが見つかりません: {target}")
                sys.exit(1)
            
            print(f"処理可能なファイル: {len(all_files)}件")
            
            for file_path in all_files:
                try:
                    print(f"\n--- {os.path.basename(file_path)} を処理中 ---")
                    json_file = process_chatgpt_export(file_path)
                    print(f"処理可能なJSONファイル: {json_file}")
                    
                    # chatgpt_to_notion.pyを呼び出し
                    print("Notionへの同期を開始します...")
                    os.system(f"python chatgpt_to_notion.py '{json_file}'")
                    
                except Exception as e:
                    print(f"ファイル処理エラー ({file_path}): {e}")
                    continue
        
        else:
            print(f"ファイルまたはディレクトリが見つかりません: {target}")
            sys.exit(1)
    
    except Exception as e:
        print(f"処理エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

