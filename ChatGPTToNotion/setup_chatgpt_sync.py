# -*- coding: utf-8 -*-
"""
ChatGPT to Notion セットアップスクリプト
ChatGPTチャット履歴自動同期システムの初期セットアップを行います。
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Pythonバージョンチェック"""
    if sys.version_info < (3, 7):
        print("エラー: Python 3.7以上が必要です。")
        return False
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} を確認しました。")
    return True

def setup_virtual_environment():
    """仮想環境のセットアップ"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("仮想環境は既に存在します。")
        return True
    
    print("仮想環境を作成中...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("仮想環境を作成しました。")
        return True
    except subprocess.CalledProcessError as e:
        print(f"仮想環境作成エラー: {e}")
        return False

def install_dependencies():
    """依存関係のインストール"""
    print("依存関係をインストール中...")
    
    # 仮想環境のPythonパスを取得
    if os.name == 'nt':  # Windows
        python_path = "venv/Scripts/python.exe"
    else:  # macOS/Linux
        python_path = "venv/bin/python"
    
    try:
        subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([python_path, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("依存関係のインストールが完了しました。")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依存関係インストールエラー: {e}")
        return False

def create_env_file():
    """環境変数ファイルの作成"""
    env_file = Path(".env")
    
    if env_file.exists():
        print(".envファイルは既に存在します。")
        return True
    
    print(".envファイルを作成中...")
    
    env_content = """# ChatGPT to Notion 設定ファイル

# Notion API設定
NOTION_TOKEN=your_notion_integration_token_here
CHATGPT_DB_ID=your_chatgpt_database_id_here

# 実行モード（true: テスト実行、false: 本番実行）
DRY_RUN=true

# API設定
NOTION_TIMEOUT=60

# プロパティ名設定（必要に応じて変更）
PROP_TITLE=タイトル
PROP_CHAT_ID=チャットID
PROP_CREATED_AT=作成日時
PROP_UPDATED_AT=更新日時
PROP_CONTENT=内容
PROP_MODEL=モデル
PROP_MESSAGE_COUNT=メッセージ数
"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(".envファイルを作成しました。")
        print("NOTION_TOKENとCHATGPT_DB_IDを設定してください。")
        return True
    except Exception as e:
        print(f".envファイル作成エラー: {e}")
        return False

def create_sample_data():
    """サンプルデータの作成"""
    print("サンプルデータを作成中...")
    
    try:
        subprocess.run([sys.executable, "chatgpt_export_helper.py", "sample"], check=True)
        print("サンプルデータを作成しました。")
        return True
    except subprocess.CalledProcessError as e:
        print(f"サンプルデータ作成エラー: {e}")
        return False

def setup_launchd():
    """launchdのセットアップ"""
    print("launchdのセットアップ中...")
    
    plist_file = Path("com.user.chatgpt-sync.plist")
    if not plist_file.exists():
        print("launchd設定ファイルが見つかりません。")
        return False
    
    # ユーザーのホームディレクトリのLaunchAgentsディレクトリにコピー
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(exist_ok=True)
    
    target_plist = launch_agents_dir / "com.user.chatgpt-sync.plist"
    
    try:
        import shutil
        shutil.copy2(plist_file, target_plist)
        print(f"launchd設定ファイルをコピーしました: {target_plist}")
        
        # launchdに登録
        subprocess.run(["launchctl", "load", str(target_plist)], check=True)
        print("launchdに登録しました。")
        return True
    except Exception as e:
        print(f"launchdセットアップエラー: {e}")
        return False

def print_next_steps():
    """次のステップの説明"""
    print("\n" + "="*60)
    print("セットアップ完了！")
    print("="*60)
    print("\n次のステップ:")
    print("1. .envファイルを編集して以下を設定:")
    print("   - NOTION_TOKEN: Notion統合トークン")
    print("   - CHATGPT_DB_ID: ChatGPTデータベースID")
    print("\n2. Notionデータベースを作成:")
    print("   python chatgpt_to_notion.py --create-db <親ページID>")
    print("\n3. テスト実行:")
    print("   python chatgpt_to_notion.py sample_chatgpt_export.json")
    print("\n4. 本番実行:")
    print("   .envファイルでDRY_RUN=falseに設定")
    print("   python chatgpt_to_notion.py <エクスポートファイル>")
    print("\n5. 自動同期の開始:")
    print("   launchctl start com.user.chatgpt-sync")
    print("\n6. ログの確認:")
    print("   tail -f chatgpt_sync.log")
    print("\n" + "="*60)

def main():
    """メイン処理"""
    print("ChatGPT to Notion セットアップスクリプト")
    print("="*50)
    
    # 各ステップを実行
    steps = [
        ("Pythonバージョンチェック", check_python_version),
        ("仮想環境セットアップ", setup_virtual_environment),
        ("依存関係インストール", install_dependencies),
        ("環境変数ファイル作成", create_env_file),
        ("サンプルデータ作成", create_sample_data),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"エラー: {step_name}に失敗しました。")
            sys.exit(1)
    
    # launchdセットアップ（オプション）
    print("\nlaunchdセットアップ（オプション）...")
    setup_launchd()
    
    print_next_steps()

if __name__ == "__main__":
    main()
