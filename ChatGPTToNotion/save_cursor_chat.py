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

def create_notion_page(chat_data):
    """NotionのAI Chat管理データベースにページを作成"""
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

def add_content_to_page(notion, page_id, content):
    """ページにMarkdownコンテンツを追加（プレビュー + ソース）"""
    try:
        children = []
        
        # 1. Markdownプレビューセクション
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "📖 Markdown Preview"
                        }
                    }
                ]
            }
        })
        
        # Markdownプレビュー用のコードブロック（2000文字制限対応）
        content_chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
        for i, chunk in enumerate(content_chunks):
            children.append({
                "object": "block",
                "type": "code",
                "code": {
                    "language": "markdown",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": chunk
                            }
                        }
                    ]
                }
            })
        
        # 2. Markdownソースセクション
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "📝 Markdown Source"
                        }
                    }
                ]
            }
        })
        
        # Markdownソース用のコードブロック（2000文字制限対応）
        for i, chunk in enumerate(content_chunks):
            children.append({
                "object": "block",
                "type": "code",
                "code": {
                    "language": "markdown",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": chunk
                            }
                        }
                    ]
                }
            })
        
        # 3. 構造化されたコンテンツ（見出しと段落）
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "📄 Structured Content"
                        }
                    }
                ]
            }
        })
        
        # コンテンツを構造化して追加
        lines = content.split('\n')
        current_paragraph = []
        
        for line in lines:
            if line.strip() == '':
                # 空行の場合、現在の段落をブロックとして追加
                if current_paragraph:
                    paragraph_text = '\n'.join(current_paragraph)
                    if len(paragraph_text) <= 2000:  # Notion制限
                        children.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": paragraph_text
                                        }
                                    }
                                ]
                            }
                        })
                    current_paragraph = []
            else:
                current_paragraph.append(line)
        
        # 最後の段落を追加
        if current_paragraph:
            paragraph_text = '\n'.join(current_paragraph)
            if len(paragraph_text) <= 2000:  # Notion制限
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": paragraph_text
                                }
                            }
                        ]
                    }
                })
        
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
