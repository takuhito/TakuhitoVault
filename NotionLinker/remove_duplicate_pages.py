# -*- coding: utf-8 -*-
"""
Notion 重複ページ削除ツール
- 同じタイトルのページが複数ある場合、リレーションプロパティに何も入力されていないページを削除
- 安全のため、DRY_RUN モードで事前確認可能
"""

import os, sys, time, random
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import defaultdict

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError, RequestTimeoutError
except Exception:
    print("notion-client がありません。`pip install -r requirements.txt` を実行してください。")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
JOURNAL_DB_ID = os.getenv("JOURNAL_DB_ID")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")  # デフォルトはDRY_RUN
NOTION_TIMEOUT = int(os.getenv("NOTION_TIMEOUT", "60"))

if not NOTION_TOKEN or not JOURNAL_DB_ID:
    print("環境変数 NOTION_TOKEN / JOURNAL_DB_ID が未設定です。.env を確認。")
    sys.exit(1)

# Notion クライアント
notion = Client(auth=NOTION_TOKEN, timeout_ms=int(NOTION_TIMEOUT * 1000))

# ---------- リトライ付きAPI呼び出しユーティリティ ----------
def with_retry(fn, *, max_attempts=4, base_delay=1.0, what="api"):
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

# ---------- データベース操作 ----------
def iter_database_pages(database_id: str):
    """データベース内の全ページを取得"""
    start_cursor = None
    while True:
        def _call():
            payload = {"database_id": database_id, "page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor
            return notion.databases.query(**payload)
        res = with_retry(_call, what="databases.query")
        for r in res.get("results", []):
            yield r
        if not res.get("has_more"):
            break
        start_cursor = res.get("next_cursor")

def get_page_title(page: Dict[str, Any]) -> Optional[str]:
    """ページのタイトルを取得"""
    props = page.get("properties", {})
    title_prop = props.get("タイトル")
    if not title_prop:
        return None
    
    title_content = title_prop.get("title", [])
    if not title_content:
        return None
    
    return "".join([span.get("plain_text", "") for span in title_content])

def has_content_data(page: Dict[str, Any]) -> bool:
    """ページにコンテンツデータがあるかどうかを判定（リレーション、URL、本文など）"""
    props = page.get("properties", {})
    
    # リレーションプロパティのリスト
    relation_props = [
        "アカウント", "Technique", "購入アイテム", "記事アイデア一覧", "マイリンク",
        "映画・ドラマ視聴記録", "UberEats配達記録", "Clipping", "🟥支払予定",
        "公開記事一覧", "🟩支払完了", "DB_行動", "AI Chat管理", "YouTube要約"
    ]
    
    # リレーションデータの確認
    for prop_name in relation_props:
        if prop_name in props:
            prop = props[prop_name]
            if prop.get("type") == "relation":
                relations = prop.get("relation", [])
                if relations:  # リレーションが存在する
                    return True
    
    # URLプロパティの確認
    url_prop = props.get("URL")
    if url_prop and url_prop.get("url"):
        return True
    
    # 本文コンテンツの確認（ページの子ブロックを取得）
    try:
        def _call():
            return notion.blocks.children.list(block_id=page["id"])
        children = with_retry(_call, what="blocks.children.list")
        
        if children.get("results"):
            return True
    except Exception as e:
        print(f"  警告: ページ {page['id']} の子ブロック取得に失敗: {e}")
    
    return False

def delete_page(page_id: str):
    """ページを削除（アーカイブ）"""
    if DRY_RUN:
        print(f"[DRY-RUN] Delete page {page_id}")
        return
    
    def _call():
        return notion.pages.update(
            page_id=page_id,
            archived=True
        )
    return with_retry(_call, what="pages.delete")

# ---------- 重複検出・削除ロジック ----------
def find_duplicates(pages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """同じタイトルのページをグループ化"""
    title_groups = defaultdict(list)
    
    for page in pages:
        title = get_page_title(page)
        if title:
            title_groups[title].append(page)
    
    # 重複があるグループのみを返す
    return {title: pages for title, pages in title_groups.items() if len(pages) > 1}

def select_pages_to_keep(duplicate_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """保持するページを選択（コンテンツデータがあるページを優先）"""
    pages_with_content = []
    pages_without_content = []
    
    for page in duplicate_pages:
        if has_content_data(page):
            pages_with_content.append(page)
        else:
            pages_without_content.append(page)
    
    # コンテンツデータがあるページがある場合はそれらを保持
    if pages_with_content:
        return pages_with_content
    
    # コンテンツデータがないページのみの場合は、最新の1つを保持
    return [duplicate_pages[0]] if duplicate_pages else []

# ---------- メイン処理 ----------
def main():
    print("== Notion 重複ページ削除ツール ==")
    print(f"DRY_RUN: {DRY_RUN}")
    print(f"対象データベース: {JOURNAL_DB_ID}")
    print()
    
    # 全ページを取得
    print("ページを取得中...")
    pages = list(iter_database_pages(JOURNAL_DB_ID))
    if not pages:
        print("対象ページはありません。")
        return
    
    print(f"総ページ数: {len(pages)}")
    print()
    
    # 重複を検出
    print("重複ページを検出中...")
    duplicates = find_duplicates(pages)
    
    if not duplicates:
        print("重複ページは見つかりませんでした。")
        return
    
    print(f"重複タイトル数: {len(duplicates)}")
    print()
    
    # 削除対象を決定
    pages_to_delete = []
    pages_to_keep = []
    
    for title, duplicate_pages in duplicates.items():
        print(f"タイトル: {title}")
        print(f"  重複ページ数: {len(duplicate_pages)}")
        
        # コンテンツデータの確認
        for i, page in enumerate(duplicate_pages):
            has_content = has_content_data(page)
            page_id = page["id"]
            print(f"    ページ{i+1}: {page_id} (コンテンツ: {'あり' if has_content else 'なし'})")
        
        # 保持するページを選択
        keep_pages = select_pages_to_keep(duplicate_pages)
        delete_pages = [p for p in duplicate_pages if p not in keep_pages]
        
        pages_to_keep.extend(keep_pages)
        pages_to_delete.extend(delete_pages)
        
        print(f"  保持: {len(keep_pages)}件, 削除: {len(delete_pages)}件")
        if keep_pages:
            print(f"    保持理由: コンテンツデータあり")
        else:
            print(f"    保持理由: 最新の1件を保持")
        print()
    
    print(f"=== 統計情報 ===")
    print(f"総ページ数: {len(pages)}")
    print(f"重複タイトル数: {len(duplicates)}")
    print(f"保持するページ数: {len(pages_to_keep)}")
    print(f"削除するページ数: {len(pages_to_delete)}")
    print()
    
    if not pages_to_delete:
        print("削除対象のページはありません。")
        return
    
    if DRY_RUN:
        print("DRY_RUN モードのため、実際の削除は行われません。")
        print("実際に削除するには、.env で DRY_RUN=false を設定してください。")
        return
    
    # 実際の削除実行
    print("実際の削除を開始します...")
    confirm = input("続行しますか？ (y/N): ")
    if confirm.lower() != 'y':
        print("キャンセルしました。")
        return
    
    print(f"\n=== 削除の実行 ({len(pages_to_delete)}件) ===")
    for i, page in enumerate(pages_to_delete, 1):
        page_id = page["id"]
        title = get_page_title(page)
        print(f"[{i}/{len(pages_to_delete)}] 削除: {title} ({page_id})")
        delete_page(page_id)
        time.sleep(0.2)  # API制限対策
    
    print("\n完了しました。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断しました。")
