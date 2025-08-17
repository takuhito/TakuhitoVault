# -*- coding: utf-8 -*-
"""
ChatGPT to Notion - チャット履歴自動保存ツール
ChatGPTのチャット履歴をNotionデータベースに自動保存するツールです。
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError, RequestTimeoutError
except Exception:
    print("notion-client がありません。`pip install -r requirements.txt` を実行してください。")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

# 環境変数
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
CHATGPT_DB_ID = os.getenv("CHATGPT_DB_ID")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes")
NOTION_TIMEOUT = int(os.getenv("NOTION_TIMEOUT", "60"))

# プロパティ名
PROP_TITLE = os.getenv("PROP_TITLE", "名前")
PROP_CHAT_ID = os.getenv("PROP_CHAT_ID", "URL")
PROP_CREATED_AT = os.getenv("PROP_CREATED_AT", "最終更新日時")
PROP_UPDATED_AT = os.getenv("PROP_UPDATED_AT", "最終更新日時")
PROP_CONTENT = os.getenv("PROP_CONTENT", "AI カスタム自動入力")
PROP_MODEL = os.getenv("PROP_MODEL", "AI Model")
PROP_MESSAGE_COUNT = os.getenv("PROP_MESSAGE_COUNT", "Tags")

if not NOTION_TOKEN or not CHATGPT_DB_ID:
    print("環境変数 NOTION_TOKEN / CHATGPT_DB_ID が未設定です。.env を確認してください。")
    sys.exit(1)

# Notionクライアント
notion = Client(auth=NOTION_TOKEN, timeout_ms=int(NOTION_TIMEOUT * 1000))

def with_retry(fn, *, max_attempts=4, base_delay=1.0, what="api"):
    """リトライ付きAPI呼び出し"""
    import random
    attempt = 0
    while True:
        try:
            return fn()
        except RequestTimeoutError as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            delay = base_delay * (2 ** (attempt-1)) + random.uniform(0, 0.5)
            print(f"[RETRY] Timeout on {what}. retry {attempt}/{max_attempts} in {delay:.1f}s")
            time.sleep(delay)
        except APIResponseError as e:
            if getattr(e, "code", "") == "rate_limited":
                attempt += 1
                retry_after = float(getattr(e, "headers", {}).get("Retry-After", 1)) if hasattr(e, "headers") else 1.0
                delay = max(retry_after, base_delay * (2 ** (attempt-1))) + random.uniform(0, 0.5)
                print(f"[RETRY] rate_limited on {what}. retry {attempt}/{max_attempts} in {delay:.1f}s")
                time.sleep(delay)
                if attempt < max_attempts:
                    continue
            raise

def get_prop_val(prop: Dict[str, Any]) -> Optional[Any]:
    """プロパティ値の取得"""
    t = prop.get("type")
    if t == "date":
        v = prop.get("date")
        return v.get("start") if v else None
    if t == "rich_text":
        return "".join([span.get("plain_text", "") for span in prop.get("rich_text", [])]) or None
    if t == "title":
        return "".join([span.get("plain_text", "") for span in prop.get("title", [])]) or None
    if t == "number":
        return prop.get("number")
    if t == "select":
        s = prop.get("select")
        return s.get("name") if s else None
    if t == "multi_select":
        return [option.get("name") for option in prop.get("multi_select", [])]
    if t == "url":
        return prop.get("url")
    if t == "last_edited_time":
        return prop.get("last_edited_time")
    return None

def clean_garbage_text(text: str) -> str:
    """適切にゴミ文字のみを除去（必要なテキストは保持）"""
    import re
    
    # 特定のゴミ文字パターンのみを除去（改行は保持）
    patterns_to_remove = [
        r'⬛▶️cite⭐turn0search\d+◀️⬛',  # ⬛▶️cite⭐turn0search0◀️⬛ など
        r'⬛⚫',  # ⬛⚫
        r'▶️.*?⬛◀️',  # ▶️...⬛◀️ で囲まれた部分
        r'▶️',  # 単独の▶️
        r'⬛',  # 単独の⬛
        r'◀️',  # 単独の◀️
        r'⚫',  # 単独の⚫
        r'cite',  # cite文字列
        r'turn0search\d+',  # turn0search0, turn0search1 など
        r'⭐',  # ⭐
        r'cite⭐',  # cite⭐
        r'⭐turn0search\d+',  # ⭐turn0search0 など
        r'\*\*\.\*',  # **.** パターン
        r'_\s*\*\*\.\*',  # _ **.** パターン
    ]
    
    cleaned_text = text
    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    # 改行を保持しながら、過度な空白行のみを整理
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
    
    # 行頭行末の空白を除去（改行は保持）
    cleaned_text = re.sub(r'^\s+|\s+$', '', cleaned_text, flags=re.MULTILINE)
    
    return cleaned_text.strip()

def extract_messages_from_mapping(mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
    """mappingフィールドからメッセージを抽出"""
    messages = []
    
    for message_id, message_data in mapping.items():
        if message_id == "client-created-root":
            continue
            
        message = message_data.get("message")
        if not message:
            continue
            
        author = message.get("author", {})
        role = author.get("role", "unknown")
        
        # システムメッセージはスキップ
        if role == "system":
            continue
            
        content_obj = message.get("content", {})
        content_type = content_obj.get("content_type", "")
        
        # テキストコンテンツを抽出
        if content_type == "text":
            parts = content_obj.get("parts", [])
            text_content = ""
            for part in parts:
                if isinstance(part, str):
                    text_content += part
                elif isinstance(part, dict) and part.get("type") == "text":
                    text_content += part.get("text", "")
            
            # ゴミ文字を除去
            text_content = clean_garbage_text(text_content)
            
            if text_content.strip():
                messages.append({
                    "role": role,
                    "content": text_content,
                    "timestamp": message.get("create_time")
                })
        
        # マルチモーダルテキストコンテンツを抽出
        elif content_type == "multimodal_text":
            parts = content_obj.get("parts", [])
            text_content = ""
            for part in parts:
                if part.get("content_type") == "text":
                    text_content += part.get("text", "")
                elif part.get("content_type") == "audio_transcription":
                    text_content += part.get("text", "")
            
            # ゴミ文字を除去
            text_content = clean_garbage_text(text_content)
            
            if text_content.strip():
                messages.append({
                    "role": role,
                    "content": text_content,
                    "timestamp": message.get("create_time")
                })
    
    return messages

def format_chat_content(messages: List[Dict[str, Any]]) -> str:
    """チャット内容をフォーマット"""
    if not messages:
        return "チャット内容なし"
    
    # メッセージ数情報を追加
    message_count = len(messages)
    content_parts = [f"📊 メッセージ数: {message_count}\n"]
    
    for i, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        
        if content:
            # ロールを日本語に変換
            role_jp = {
                "user": "ユーザー",
                "assistant": "アシスタント",
                "system": "システム"
            }.get(role, role)
            
            # タイムスタンプをフォーマット
            time_str = ""
            if timestamp:
                try:
                    # Unix timestampをdatetimeに変換
                    if isinstance(timestamp, (int, float)):
                        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    else:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = f" ({dt.strftime('%Y-%m-%d %H:%M:%S')})"
                except:
                    pass
            
            content_parts.append(f"【{role_jp}{time_str}】\n{content}")
    
    return "\n\n".join(content_parts)

def find_existing_chat(chat_id: str) -> Optional[str]:
    """既存のチャットページを検索"""
    try:
        print(f"  チャットID '{chat_id}' で検索中...")
        response = with_retry(
            lambda: notion.databases.query(
                database_id=CHATGPT_DB_ID,
                filter={
                    "property": PROP_CHAT_ID,
                    "url": {"equals": f"https://chat.openai.com/c/{chat_id}"}
                }
            ),
            what="query existing chat"
        )
        
        results = response.get("results", [])
        if results:
            print(f"  既存ページ発見: {results[0]['id']}")
            return results[0]["id"]
        else:
            print(f"  既存ページなし")
        return None
    except Exception as e:
        print(f"既存チャット検索エラー: {e}")
        return None

def create_chat_page(chat_data: Dict[str, Any]) -> str:
    """チャットページを作成"""
    chat_id = chat_data.get("id", "")
    title = chat_data.get("title", "無題のチャット")
    created_at = chat_data.get("create_time")
    updated_at = chat_data.get("update_time")
    model = chat_data.get("default_model_slug", "ChatGPT")
    
    # 新しい形式（mapping）と古い形式（messages）の両方に対応
    messages = []
    if "mapping" in chat_data:
        messages = extract_messages_from_mapping(chat_data["mapping"])
    else:
        messages = chat_data.get("messages", [])
    
    message_count = len(messages)
    
    # チャット内容をフォーマット
    content = format_chat_content(messages)
    
    # ChatGPTのURLを生成（チャットIDから一貫したURLを生成）
    if chat_id:
        chat_url = f"https://chat.openai.com/c/{chat_id}"
    else:
        # IDがない場合は最初のメッセージの内容からハッシュを生成
        first_message = messages[0] if messages else {}
        content = f"{first_message.get('role', '')}:{first_message.get('content', '')}"
        chat_url = f"https://chat.openai.com/c/{hashlib.md5(content.encode('utf-8')).hexdigest()}"
    
    properties = {
        PROP_TITLE: {"title": [{"text": {"content": title}}]},
        PROP_CHAT_ID: {"url": chat_url},
        PROP_CONTENT: {"rich_text": []},  # 空にする
        PROP_MODEL: {"multi_select": [{"name": model}]}
    }
    
    # ページの本文コンテンツを作成
    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }
                ]
            }
        }
    ]
    
    if DRY_RUN:
        print(f"[DRY_RUN] チャットページ作成: {title}")
        return "dry_run_page_id"
    
    try:
        response = with_retry(
            lambda: notion.pages.create(
                parent={"database_id": CHATGPT_DB_ID},
                properties=properties,
                children=children
            ),
            what="create chat page"
        )
        page_id = response["id"]
        print(f"チャットページ作成完了: {title} -> {page_id}")
        return page_id
    except Exception as e:
        print(f"チャットページ作成エラー: {e}")
        raise

def update_chat_page(page_id: str, chat_data: Dict[str, Any]):
    """チャットページを更新"""
    title = chat_data.get("title", "無題のチャット")
    updated_at = chat_data.get("updated_at")
    model = chat_data.get("model", "ChatGPT")
    messages = chat_data.get("messages", [])
    message_count = len(messages)
    
    # チャット内容をフォーマット
    content = format_chat_content(messages)
    
    properties = {
        PROP_TITLE: {"title": [{"text": {"content": title}}]},
        PROP_CONTENT: {"rich_text": []},  # 空にする
        PROP_MODEL: {"multi_select": [{"name": model}]}
    }
    
    if DRY_RUN:
        print(f"[DRY_RUN] チャットページ更新: {title}")
        return
    
    try:
        # プロパティを更新
        with_retry(
            lambda: notion.pages.update(
                page_id=page_id,
                properties=properties
            ),
            what="update chat page properties"
        )
        
        # 既存のブロックを削除
        try:
            existing_blocks = with_retry(
                lambda: notion.blocks.children.list(block_id=page_id),
                what="get existing blocks"
            )
            
            for block in existing_blocks.get("results", []):
                with_retry(
                    lambda: notion.blocks.delete(block_id=block["id"]),
                    what="delete existing block"
                )
        except Exception as e:
            print(f"既存ブロック削除エラー: {e}")
        
        # 新しい本文コンテンツを追加
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }
        ]
        
        with_retry(
            lambda: notion.blocks.children.append(
                block_id=page_id,
                children=children
            ),
            what="update chat page content"
        )
        
        print(f"チャットページ更新完了: {title}")
    except Exception as e:
        print(f"チャットページ更新エラー: {e}")
        raise

def append_new_messages_to_page(page_id: str, new_messages: List[Dict[str, Any]]):
    """ページに新しいメッセージを追加"""
    if not new_messages:
        return
    
    # 新しいメッセージをフォーマット
    content_parts = []
    for msg in new_messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        
        if content:
            # ロールを日本語に変換
            role_jp = {
                "user": "ユーザー",
                "assistant": "アシスタント",
                "system": "システム"
            }.get(role, role)
            
            # タイムスタンプをフォーマット
            time_str = ""
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = f" ({dt.strftime('%Y-%m-%d %H:%M:%S')})"
                except:
                    pass
            
            content_parts.append(f"【{role_jp}{time_str}】\n{content}")
    
    new_content = "\n\n".join(content_parts)
    
    # 現在の日付を取得
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 新しいブロックを追加
    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"\n\n--- {current_date} 追加メッセージ ---\n{new_content}"
                        }
                    }
                ]
            }
        }
    ]
    
    try:
        with_retry(
            lambda: notion.blocks.children.append(
                block_id=page_id,
                children=children
            ),
            what="append new messages"
        )
        print(f"新しいメッセージを追加しました: {len(new_messages)}件")
    except Exception as e:
        print(f"メッセージ追加エラー: {e}")
        raise

def update_chat_page_properties(page_id: str, chat_data: Dict[str, Any]):
    """チャットページのプロパティのみを更新"""
    title = chat_data.get("title", "無題のチャット")
    model = chat_data.get("model", "ChatGPT")
    messages = chat_data.get("messages", [])
    message_count = len(messages)
    
    properties = {
        PROP_TITLE: {"title": [{"text": {"content": title}}]},
        PROP_MODEL: {"multi_select": [{"name": model}]}
    }
    
    if DRY_RUN:
        print(f"[DRY_RUN] プロパティ更新: {title}")
        return
    
    try:
        with_retry(
            lambda: notion.pages.update(
                page_id=page_id,
                properties=properties
            ),
            what="update chat page properties"
        )
        print(f"プロパティ更新完了: {title}")
    except Exception as e:
        print(f"プロパティ更新エラー: {e}")
        raise

def process_chatgpt_export_file(file_path: str):
    """ChatGPTエクスポートファイルを処理"""
    print(f"ファイル処理中: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            chats = data
        elif isinstance(data, dict) and "conversations" in data:
            chats = data["conversations"]
        else:
            print(f"サポートされていないファイル形式: {file_path}")
            return
        
        print(f"{len(chats)}個のチャットを処理中...")
        
        for i, chat in enumerate(chats, 1):
            try:
                chat_id = chat.get("id", "")
                if not chat_id:
                    # IDがない場合は最初のメッセージの内容からハッシュを生成
                    first_message = new_messages[0] if new_messages else {}
                    content = f"{first_message.get('role', '')}:{first_message.get('content', '')}"
                    chat_id = hashlib.md5(content.encode('utf-8')).hexdigest()
                new_messages = chat.get("messages", [])
                
                # 既存ページを検索
                existing_page_id = find_existing_chat(chat_id)
                
                if existing_page_id:
                    print(f"[{i}/{len(chats)}] 既存チャット確認: {chat.get('title', '無題')}")
                    
                    # 新しいメッセージがあるかチェック（簡易版：メッセージ数の増加で判定）
                    existing_page = with_retry(
                        lambda: notion.pages.retrieve(page_id=existing_page_id),
                        what="retrieve existing page"
                    )
                    
                    # 既存ページの内容を取得
                    existing_blocks = with_retry(
                        lambda: notion.blocks.children.list(block_id=existing_page_id),
                        what="get existing blocks"
                    )
                    
                    # 既存のメッセージ数を推定（簡易版）
                    existing_message_count = 0
                    for block in existing_blocks.get("results", []):
                        if block.get("type") == "paragraph":
                            rich_text = block.get("paragraph", {}).get("rich_text", [])
                            content = "".join([text.get("plain_text", "") for text in rich_text])
                            if "【ユーザー" in content or "【アシスタント" in content:
                                # 【の数をカウントしてメッセージ数を推定
                                message_count = content.count("【")
                                existing_message_count = max(existing_message_count, message_count)
                    
                    print(f"  既存メッセージ数: {existing_message_count}, 新しいメッセージ数: {len(new_messages)}")
                    
                    # 新しいメッセージがあるかチェック
                    if len(new_messages) > existing_message_count:
                        new_messages_only = new_messages[existing_message_count:]
                        print(f"  新しいメッセージを検出: {len(new_messages_only)}件")
                        append_new_messages_to_page(existing_page_id, new_messages_only)
                        
                        # プロパティも更新（メッセージ数など）
                        update_chat_page_properties(existing_page_id, chat)
                    else:
                        print(f"  新しいメッセージなし")
                else:
                    print(f"[{i}/{len(chats)}] 新規作成: {chat.get('title', '無題')}")
                    create_chat_page(chat)
                
                time.sleep(0.5)  # API制限対策
                
            except Exception as e:
                print(f"チャット処理エラー: {e}")
                continue
        
        print("処理完了")
        
    except Exception as e:
        print(f"ファイル処理エラー: {e}")

def main():
    """メイン処理"""
    print("ChatGPT to Notion - チャット履歴自動保存ツール")
    print(f"DRY_RUN: {DRY_RUN}")
    print(f"データベースID: {CHATGPT_DB_ID}")
    
    if len(sys.argv) < 2:
        print("使用方法: python chatgpt_to_notion.py <ChatGPTエクスポートファイル>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"ファイルが見つかりません: {file_path}")
        sys.exit(1)
    process_chatgpt_export_file(file_path)

if __name__ == "__main__":
    main()
