# -*- coding: utf-8 -*-
"""
Notion 重複ページ合体ツール
- 同じタイトルのページが複数ある場合、リレーションやコンテンツを合体して1つのページにまとめる
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
    """ページにコンテンツデータがあるかどうかを判定"""
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
                if relations:
                    return True
    
    # URLプロパティの確認
    url_prop = props.get("URL")
    if url_prop and url_prop.get("url"):
        return True
    
    # 本文コンテンツの確認
    try:
        def _call():
            return notion.blocks.children.list(block_id=page["id"])
        children = with_retry(_call, what="blocks.children.list")
        
        if children.get("results"):
            return True
    except Exception as e:
        print(f"  警告: ページ {page['id']} の子ブロック取得に失敗: {e}")
    
    return False

def get_page_relations(page: Dict[str, Any]) -> Dict[str, List[str]]:
    """ページのリレーションデータを取得"""
    props = page.get("properties", {})
    relations = {}
    
    relation_props = [
        "アカウント", "Technique", "購入アイテム", "記事アイデア一覧", "マイリンク",
        "映画・ドラマ視聴記録", "UberEats配達記録", "Clipping", "🟥支払予定",
        "公開記事一覧", "🟩支払完了", "DB_行動", "AI Chat管理", "YouTube要約"
    ]
    
    for prop_name in relation_props:
        if prop_name in props:
            prop = props[prop_name]
            if prop.get("type") == "relation":
                relation_list = prop.get("relation", [])
                if relation_list:
                    relations[prop_name] = [r["id"] for r in relation_list]
    
    return relations

def get_page_url(page: Dict[str, Any]) -> Optional[str]:
    """ページのURLプロパティを取得"""
    props = page.get("properties", {})
    url_prop = props.get("URL")
    if url_prop and url_prop.get("url"):
        return url_prop.get("url")
    return None

def merge_page_properties(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """複数ページのプロパティを合体"""
    merged_props = {}
    
    # リレーションプロパティの合体
    all_relations = defaultdict(set)
    merged_url = None
    
    for page in pages:
        props = page.get("properties", {})
        
        # リレーションの合体
        for prop_name, relation_ids in get_page_relations(page).items():
            all_relations[prop_name].update(relation_ids)
        
        # URLの取得（最初に見つかったものを使用）
        if not merged_url:
            merged_url = get_page_url(page)
    
    # リレーションプロパティを設定
    for prop_name, relation_ids in all_relations.items():
        merged_props[prop_name] = {
            "relation": [{"id": rid} for rid in relation_ids]
        }
    
    # URLプロパティを設定
    if merged_url:
        merged_props["URL"] = {
            "url": merged_url
        }
    
    return merged_props

def update_page_properties(page_id: str, properties: Dict[str, Any]):
    """ページのプロパティを更新"""
    if DRY_RUN:
        print(f"[DRY-RUN] Update page {page_id} properties")
        return
    
    def _call():
        return notion.pages.update(
            page_id=page_id,
            properties=properties
        )
    return with_retry(_call, what="pages.update")

def copy_page_content(source_page_id: str, target_page_id: str):
    """ページのコンテンツをコピー"""
    if DRY_RUN:
        print(f"[DRY-RUN] Copy content from {source_page_id} to {target_page_id}")
        return
    
    try:
        # ソースページの子ブロックを取得
        def _call():
            return notion.blocks.children.list(block_id=source_page_id)
        children = with_retry(_call, what="blocks.children.list")
        
        if children.get("results"):
            # ターゲットページに子ブロックを追加
            def _call2():
                return notion.blocks.children.append(
                    block_id=target_page_id,
                    children=children["results"]
                )
            with_retry(_call2, what="blocks.children.append")
    except Exception as e:
        print(f"  警告: コンテンツコピーに失敗: {e}")

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

# ---------- 合体ロジック ----------
def find_mergeable_duplicates(pages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """合体可能な重複ページを検出（コンテンツデータがあるページのみ）"""
    title_groups = defaultdict(list)
    
    for page in pages:
        title = get_page_title(page)
        if title and has_content_data(page):  # コンテンツデータがあるページのみ
            title_groups[title].append(page)
    
    # 重複があり、かつ複数のページにコンテンツがあるグループのみを返す
    return {title: pages for title, pages in title_groups.items() 
            if len(pages) > 1 and len([p for p in pages if has_content_data(p)]) > 1}

def select_merge_target(duplicate_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """合体先のページを選択（最初のページを選択）"""
    return duplicate_pages[0]

# ---------- メイン処理 ----------
def main():
    print("== Notion 重複ページ合体ツール ==")
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
    
    # 合体可能な重複を検出
    print("合体可能な重複ページを検出中...")
    mergeable_duplicates = find_mergeable_duplicates(pages)
    
    if not mergeable_duplicates:
        print("合体可能な重複ページは見つかりませんでした。")
        return
    
    print(f"合体対象タイトル数: {len(mergeable_duplicates)}")
    print()
    
    # 合体処理の準備
    merge_operations = []
    
    for title, duplicate_pages in mergeable_duplicates.items():
        print(f"タイトル: {title}")
        print(f"  重複ページ数: {len(duplicate_pages)}")
        
        # 各ページの詳細確認
        for i, page in enumerate(duplicate_pages):
            page_id = page["id"]
            relations = get_page_relations(page)
            url = get_page_url(page)
            has_content = has_content_data(page)
            
            print(f"    ページ{i+1}: {page_id}")
            if relations:
                for rel_name, rel_ids in relations.items():
                    print(f"      リレーション「{rel_name}」: {len(rel_ids)}件")
            else:
                print(f"      リレーション: なし")
            print(f"      URL: {'あり' if url else 'なし'}")
            print(f"      コンテンツ: {'あり' if has_content else 'なし'}")
        
        # 合体先を選択
        target_page = select_merge_target(duplicate_pages)
        source_pages = [p for p in duplicate_pages if p["id"] != target_page["id"]]
        
        # 合体後の予想結果を表示
        print(f"  → 合体後の予想結果:")
        all_relations = defaultdict(set)
        merged_url = None
        
        for page in [target_page] + source_pages:
            for prop_name, relation_ids in get_page_relations(page).items():
                all_relations[prop_name].update(relation_ids)
            if not merged_url:
                merged_url = get_page_url(page)
        
        print(f"    合体先: {target_page['id']}")
        if all_relations:
            for rel_name, rel_ids in all_relations.items():
                print(f"      リレーション「{rel_name}」: {len(rel_ids)}件")
        if merged_url:
            print(f"      URL: あり")
        print(f"      合体元: {len(source_pages)}件")
        
        merge_operations.append({
            "title": title,
            "target_page": target_page,
            "source_pages": source_pages
        })
        
        print()
    
    print(f"=== 統計情報 ===")
    print(f"総ページ数: {len(pages)}")
    print(f"合体対象タイトル数: {len(mergeable_duplicates)}")
    print(f"合体操作数: {len(merge_operations)}")
    
    # 合体対象の詳細統計
    total_source_pages = sum(len(op["source_pages"]) for op in merge_operations)
    total_relations = defaultdict(int)
    
    for operation in merge_operations:
        for page in [operation["target_page"]] + operation["source_pages"]:
            for prop_name, relation_ids in get_page_relations(page).items():
                total_relations[prop_name] += len(relation_ids)
    
    print(f"合体元ページ数: {total_source_pages}")
    print(f"合体後のリレーション数:")
    for rel_name, count in total_relations.items():
        print(f"  {rel_name}: {count}件")
    print()
    
    if DRY_RUN:
        print("DRY_RUN モードのため、実際の合体は行われません。")
        print("実際に合体するには、.env で DRY_RUN=false を設定してください。")
        return
    
    # 実際の合体実行
    print("実際の合体を開始します...")
    confirm = input("続行しますか？ (y/N): ")
    if confirm.lower() != 'y':
        print("キャンセルしました。")
        return
    
    print(f"\n=== 合体の実行 ({len(merge_operations)}件) ===")
    for i, operation in enumerate(merge_operations, 1):
        title = operation["title"]
        target_page = operation["target_page"]
        source_pages = operation["source_pages"]
        
        print(f"[{i}/{len(merge_operations)}] 合体: {title}")
        print(f"  合体先: {target_page['id']}")
        
        # プロパティの合体
        merged_props = merge_page_properties([target_page] + source_pages)
        if merged_props:
            print(f"  プロパティ更新: {list(merged_props.keys())}")
            update_page_properties(target_page["id"], merged_props)
        
        # コンテンツのコピー
        content_copied = 0
        for source_page in source_pages:
            print(f"  コンテンツコピー: {source_page['id']} → {target_page['id']}")
            copy_page_content(source_page["id"], target_page["id"])
            content_copied += 1
        
        # ソースページの削除
        for source_page in source_pages:
            print(f"  削除: {source_page['id']}")
            delete_page(source_page["id"])
        
        print(f"  完了: {len(source_pages)}件のページを合体")
        time.sleep(0.5)  # API制限対策
        print()
    
    print("完了しました。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断しました。")
