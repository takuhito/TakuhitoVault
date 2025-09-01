#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor チャット履歴をNotionの「AI Chat管理」に保存するスクリプト
"""

import os
import sys
import json
import logging
from datetime import datetime
from notion_client import Client

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Notion設定
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
AI_CHAT_DATABASE_ID = "1fdb061d-adf3-80f8-846d-f9d89aa6e988"

def find_existing_page(chat_data):
    """既存のページを検索"""
    try:
        notion = Client(auth=NOTION_TOKEN)
        
        # チャットIDで検索
        chat_id = chat_data.get('chat_id', '')
        if chat_id:
            response = notion.databases.query(
                database_id=AI_CHAT_DATABASE_ID,
                filter={
                    "property": "URL",
                    "url": {
                        "contains": chat_id
                    }
                }
            )
            
            if response['results']:
                return response['results'][0]['id']
        
        # タイトルで検索
        title = chat_data.get('title', '')
        if title:
            response = notion.databases.query(
                database_id=AI_CHAT_DATABASE_ID,
                filter={
                    "property": "名前",
                    "title": {
                        "contains": title
                    }
                }
            )
            
            if response['results']:
                return response['results'][0]['id']
        
        return None
        
    except Exception as e:
        logger.error(f"既存ページ検索エラー: {e}")
        return None

def update_notion_page(page_id, chat_data):
    """既存のNotionページを更新"""
    try:
        notion = Client(auth=NOTION_TOKEN)
        
        # チャット日時の設定
        chat_date = chat_data.get('chat_date', '2025-09-01')
        
        # プロパティの設定
        properties = {
            "名前": {
                "title": [
                    {
                        "text": {
                            "content": chat_data.get('title', 'Cursor Chat')
                        }
                    }
                ]
            },
            "チャット日時": {
                "date": {
                    "start": chat_date
                }
            },
            "AI Model": {
                "multi_select": [
                    {
                        "name": chat_data.get('ai_model', 'Cursor')
                    }
                ]
            }
        }
        
        # タグがある場合は追加
        if 'tags' in chat_data and chat_data['tags']:
            properties["Tags"] = {
                "multi_select": [
                    {"name": tag} for tag in chat_data['tags']
                ]
            }
        
        # ページ更新
        notion.pages.update(
            page_id=page_id,
            properties=properties
        )
        
        logger.info(f"Notionページを更新しました: {page_id}")
        
        # 既存のブロックを削除
        try:
            existing_blocks = notion.blocks.children.list(block_id=page_id)
            for block in existing_blocks.get("results", []):
                notion.blocks.delete(block_id=block["id"])
        except Exception as e:
            logger.warning(f"既存ブロック削除エラー: {e}")
        
        # ページにコンテンツを追加
        if 'content' in chat_data:
            add_content_to_page(notion, page_id, chat_data['content'])
        
        return page_id
        
    except Exception as e:
        logger.error(f"Notionページの更新に失敗: {e}")
        return None

def create_notion_page(chat_data):
    """NotionのAI Chat管理データベースにページを作成または更新"""
    try:
        # 既存のページを検索
        existing_page_id = find_existing_page(chat_data)
        
        if existing_page_id:
            logger.info(f"既存のページを更新します: {existing_page_id}")
            return update_notion_page(existing_page_id, chat_data)
        else:
            logger.info("新しいページを作成します")
            return create_new_notion_page(chat_data)
        
    except Exception as e:
        logger.error(f"Notionページの処理に失敗: {e}")
        return None

def create_new_notion_page(chat_data):
    """新しいNotionページを作成"""
    try:
        notion = Client(auth=NOTION_TOKEN)
        
        # チャット日時の設定
        chat_date = chat_data.get('chat_date', '2025-09-01')
        
        # プロパティの設定
        properties = {
            "名前": {
                "title": [
                    {
                        "text": {
                            "content": chat_data.get('title', 'Cursor Chat')
                        }
                    }
                ]
            },
            "チャット日時": {
                "date": {
                    "start": chat_date
                }
            },
            "AI Model": {
                "multi_select": [
                    {
                        "name": chat_data.get('ai_model', 'Cursor')
                    }
                ]
            }
        }
        
        # タグがある場合は追加
        if 'tags' in chat_data and chat_data['tags']:
            properties["Tags"] = {
                "multi_select": [
                    {"name": tag} for tag in chat_data['tags']
                ]
            }
        
        # ページ作成
        page = notion.pages.create(
            parent={"database_id": AI_CHAT_DATABASE_ID},
            properties=properties
        )
        
        logger.info(f"Notionページを作成しました: {page['id']}")
        
        # ページにコンテンツを追加
        if 'content' in chat_data:
            add_content_to_page(notion, page['id'], chat_data['content'])
        
        return page['id']
        
    except Exception as e:
        logger.error(f"Notionページの作成に失敗: {e}")
        return None

def parse_markdown_to_blocks(content: str, max_blocks: int = 90):
    """MarkdownコンテンツをNotionブロックに変換（既存の高機能版を使用）"""
    all_blocks = []
    current_blocks = []
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 空行
        if not line:
            i += 1
            continue
        
        # 見出し1 (# タイトル) - 新しいページの開始点
        if line.startswith('# '):
            # 現在のブロックが最大数に達している場合、新しいページを開始
            if len(current_blocks) >= max_blocks:
                all_blocks.append(current_blocks)
                current_blocks = []
            
            text = line[2:].strip()
            current_blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            })
            i += 1
            continue
        
        # 見出し2 (## タイトル)
        if line.startswith('## '):
            text = line[3:].strip()
            current_blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            })
            i += 1
            continue
        
        # 見出し3 (### タイトル)
        if line.startswith('### '):
            text = line[4:].strip()
            current_blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            })
            i += 1
            continue
        
        # 区切り線 (---)
        if line == '---':
            current_blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
            i += 1
            continue
        
        # ユーザー発言 (ユーザー: で始まる行) - 太字の処理より先に実行
        if line.startswith('**ユーザー**:') or line.startswith('ユーザー:'):
            # ユーザー: の部分を除去してテキストを取得
            user_text = line.replace('**ユーザー**:', '').replace('ユーザー:', '').strip()
            
            # コールアウトブロックを作成（背景茶色 + アイコン）
            current_blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": user_text}}],
                    "icon": {"type": "emoji", "emoji": "💬"},
                    "color": "brown_background"
                }
            })
            i += 1
            continue
        
        # 太字 (**テキスト**) - ユーザー発言の処理より後に実行
        if '**' in line:
            # 太字の処理
            rich_text = []
            parts = line.split('**')
            for j, part in enumerate(parts):
                if j % 2 == 0:  # 通常テキスト
                    if part:
                        rich_text.append({"type": "text", "text": {"content": part}})
                else:  # 太字テキスト
                    rich_text.append({
                        "type": "text", 
                        "text": {"content": part},
                        "annotations": {"bold": True}
                    })
            
            current_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": rich_text}
            })
            i += 1
            continue
        
        # 通常の段落
        # 複数行の段落を収集
        paragraph_lines = []
        while i < len(lines) and lines[i].strip():
            paragraph_lines.append(lines[i])
            i += 1
        
        if paragraph_lines:
            # 段落内のユーザー発言チェック
            has_user_speech = any(line.startswith('**ユーザー**:') or line.startswith('ユーザー:') for line in paragraph_lines)
            
            if has_user_speech:
                # ユーザー発言を含む段落は、ユーザー部分をコールアウトに変換
                for line in paragraph_lines:
                    if line.startswith('**ユーザー**:') or line.startswith('ユーザー:'):
                        user_text = line.replace('**ユーザー**:', '').replace('ユーザー:', '').strip()
                        current_blocks.append({
                            "object": "block",
                            "type": "callout",
                            "callout": {
                                "rich_text": [{"type": "text", "text": {"content": user_text}}],
                                "icon": {"type": "emoji", "emoji": "💬"},
                                "color": "brown_background"
                            }
                        })
                    else:
                        # 通常のテキスト処理
                        rich_text = []
                        if '**' in line:
                            parts = line.split('**')
                            for j, part in enumerate(parts):
                                if j % 2 == 0:  # 通常テキスト
                                    if part:
                                        rich_text.append({"type": "text", "text": {"content": part}})
                                else:  # 太字テキスト
                                    rich_text.append({
                                        "type": "text", 
                                        "text": {"content": part},
                                        "annotations": {"bold": True}
                                    })
                        else:
                            rich_text = [{"type": "text", "text": {"content": line}}]
                        
                        current_blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {"rich_text": rich_text}
                        })
            else:
                # 通常の段落処理（ユーザー発言なし）
                paragraph_text = '\n'.join(paragraph_lines)
                rich_text = []
                
                if '**' in paragraph_text:
                    parts = paragraph_text.split('**')
                    for j, part in enumerate(parts):
                        if j % 2 == 0:  # 通常テキスト
                            if part:
                                rich_text.append({"type": "text", "text": {"content": part}})
                        else:  # 太字テキスト
                            rich_text.append({
                                "type": "text", 
                                "text": {"content": part},
                                "annotations": {"bold": True}
                            })
                else:
                    rich_text = [{"type": "text", "text": {"content": paragraph_text}}]
                
                current_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": rich_text}
                })
            
            # ブロック数制限チェック（段落追加後）
            if len(current_blocks) >= max_blocks:
                all_blocks.append(current_blocks)
                current_blocks = []
        
        i += 1
    
    # 最後のブロックを追加
    if current_blocks:
        all_blocks.append(current_blocks)
    
    return all_blocks

def add_content_to_page(notion, page_id, content):
    """ページにMarkdownコンテンツを追加（チャットのやり取り部分のルール適用）"""
    try:
        children = []
        
        # チャットのやり取り部分を抽出して適切にフォーマット
        chat_section = extract_chat_section(content)
        if chat_section:
            # チャットのやり取り部分を【ユーザー】【アシスタント】形式で追加
            children.extend(format_chat_messages(chat_section))
        
        # その他のMarkdownコンテンツを追加
        other_content = extract_other_content(content)
        if other_content:
            all_rendered_blocks = parse_markdown_to_blocks(other_content)
            if all_rendered_blocks:
                children.extend(all_rendered_blocks[0])
        
        # ブロックを追加（Notion APIの制限により100ブロックずつ）
        batch_size = 100
        for i in range(0, len(children), batch_size):
            batch = children[i:i + batch_size]
            notion.blocks.children.append(
                block_id=page_id,
                children=batch
            )
            logger.info(f"コンテンツブロックを追加しました: {len(batch)}個")
        
    except Exception as e:
        logger.error(f"コンテンツの追加に失敗: {e}")

def extract_chat_section(content):
    """チャットのやり取り部分を抽出"""
    lines = content.split('\n')
    chat_lines = []
    in_chat_section = False
    
    for line in lines:
        if line.strip() == "## 実際のチャット履歴":
            in_chat_section = True
            continue
        elif line.strip().startswith("## ") and in_chat_section:
            break
        elif in_chat_section:
            chat_lines.append(line)
    
    return '\n'.join(chat_lines)

def extract_other_content(content):
    """チャット以外のコンテンツを抽出"""
    lines = content.split('\n')
    other_lines = []
    in_chat_section = False
    
    for line in lines:
        if line.strip() == "## 実際のチャット履歴":
            in_chat_section = True
            continue
        elif line.strip().startswith("## ") and in_chat_section:
            in_chat_section = False
            other_lines.append(line)
        elif not in_chat_section:
            other_lines.append(line)
    
    return '\n'.join(other_lines)

def format_chat_messages(chat_content):
    """チャットメッセージを【ユーザー】【アシスタント】形式でフォーマット"""
    blocks = []
    lines = chat_content.split('\n')
    current_message = []
    current_role = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("### ユーザー:"):
            # 前のメッセージを保存
            if current_message and current_role:
                blocks.append(create_message_block(current_role, '\n'.join(current_message)))
            current_role = "user"
            current_message = [line.replace("### ユーザー:", "").strip()]
        elif line.startswith("### アシスタント:"):
            # 前のメッセージを保存
            if current_message and current_role:
                blocks.append(create_message_block(current_role, '\n'.join(current_message)))
            current_role = "assistant"
            current_message = [line.replace("### アシスタント:", "").strip()]
        else:
            if current_message is not None:
                current_message.append(line)
    
    # 最後のメッセージを保存
    if current_message and current_role:
        blocks.append(create_message_block(current_role, '\n'.join(current_message)))
    
    return blocks

def create_message_block(role, content):
    """メッセージブロックを作成"""
    role_jp = "ユーザー" if role == "user" else "アシスタント"
    
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": f"【{role_jp}】\n{content}"
                    }
                }
            ]
        }
    }

def main():
    """メイン関数"""
    if not NOTION_TOKEN:
        logger.error("NOTION_TOKEN環境変数が設定されていません")
        sys.exit(1)
    
    # JSONファイルを読み込み
    json_file = "cursor_chat_2025_09_01.json"
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            chat_data = json.load(f)
        
        logger.info(f"チャットデータを読み込みました: {json_file}")
        
        # Notionページを作成
        page_id = create_notion_page(chat_data)
        
        if page_id:
            logger.info(f"✅ チャット履歴をNotionに保存しました")
            logger.info(f"ページID: {page_id}")
        else:
            logger.error("❌ チャット履歴の保存に失敗しました")
            sys.exit(1)
            
    except FileNotFoundError:
        logger.error(f"ファイルが見つかりません: {json_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSONファイルの読み込みに失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
