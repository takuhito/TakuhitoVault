#!/usr/bin/env python3
"""
統合セットアップスクリプト
"""
import os
import sys
import subprocess
from typing import Dict, Any, List

def run_setup_script(script_name: str, args: List[str] = None) -> bool:
    """セットアップスクリプトを実行"""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ スクリプトが見つかりません: {script_path}")
        return False
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ スクリプト実行エラー: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ スクリプト実行例外: {e}")
        return False

def check_environment():
    """環境の確認"""
    print("🔍 環境確認中...")
    print("=" * 50)
    
    # Python バージョン確認
    python_version = sys.version_info
    print(f"✅ Python バージョン: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 必要なディレクトリの確認
    required_dirs = ['receipt-processor', 'config', 'credentials', 'scripts']
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ ディレクトリ: {dir_name}")
        else:
            print(f"❌ ディレクトリ: {dir_name} (見つかりません)")
    
    # 環境変数ファイルの確認
    env_files = ['.env', 'env.production', 'env.example']
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"✅ 環境変数ファイル: {env_file}")
        else:
            print(f"⚠️  環境変数ファイル: {env_file} (見つかりません)")
    
    print()

def setup_notion():
    """Notion設定"""
    print("📝 Notion設定開始")
    print("=" * 30)
    
    # テンプレートの表示
    if run_setup_script('setup_notion_database.py', ['template']):
        print("\n📋 上記のテンプレートを使用してNotionデータベースを作成してください")
        print("手順:")
        print("1. Notionで新しいページを作成")
        print("2. '/database'と入力")
        print("3. 上記のプロパティを設定")
        print("4. Integrationを接続")
        print("5. データベースIDを取得")
        
        input("\nデータベース作成が完了したらEnterを押してください...")
        
        # データベース設定の確認
        return run_setup_script('setup_notion_database.py')
    else:
        print("❌ Notionテンプレート生成に失敗しました")
        return False

def setup_google_drive():
    """Google Drive設定"""
    print("\n📁 Google Drive設定開始")
    print("=" * 30)
    
    # フォルダ構造ガイドの表示
    if run_setup_script('setup_google_drive.py', ['guide']):
        print("\n📋 上記のフォルダ構造をGoogle Driveに作成してください")
        print("手順:")
        print("1. Google Driveで'領収書管理'フォルダを作成")
        print("2. サブフォルダを作成")
        print("3. サービスアカウントにフォルダを共有")
        print("4. フォルダIDを取得")
        
        input("\nフォルダ作成が完了したらEnterを押してください...")
        
        # Google Drive設定の確認
        return run_setup_script('setup_google_drive.py')
    else:
        print("❌ Google Driveガイド生成に失敗しました")
        return False

def create_env_file():
    """環境変数ファイルの作成"""
    print("\n⚙️  環境変数ファイル設定")
    print("=" * 30)
    
    env_template = """# Notion API Settings
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=your_database_id_here

# Google Drive API Settings
GOOGLE_DRIVE_CREDENTIALS_FILE=credentials/service-account.json
GOOGLE_DRIVE_TOKEN_FILE=credentials/token.json

# Google Cloud Vision API Settings
GOOGLE_CLOUD_PROJECT_ID=receipt-processor-20241220
GOOGLE_CLOUD_CREDENTIALS_FILE=credentials/service-account.json

# File Processing Settings
GOOGLE_DRIVE_MONITOR_FOLDER=your_monitor_folder_id_here
GOOGLE_DRIVE_PROCESSED_BASE=your_processed_folder_id_here
GOOGLE_DRIVE_ERROR_FOLDER=your_error_folder_id_here

# Processing Settings
MAX_FILE_SIZE=10485760
MAX_PDF_PAGES=20
SUPPORTED_IMAGE_FORMATS=.jpg,.jpeg,.png
SUPPORTED_PDF_FORMATS=.pdf

# Logging Settings
LOG_LEVEL=INFO
LOG_FILE=receipt_processor.log

# Performance Settings
MAX_WORKERS=4
BATCH_SIZE=5
CACHE_ENABLED=true

# Monitoring Settings
MONITORING_ENABLED=true
DEBUG_MODE=false
"""
    
    env_file_path = '.env'
    
    if os.path.exists(env_file_path):
        overwrite = input(f"{env_file_path}が既に存在します。上書きしますか？ (y/n): ").lower().strip()
        if overwrite != 'y':
            print("⚠️  環境変数ファイルの作成をスキップしました")
            return True
    
    try:
        with open(env_file_path, 'w', encoding='utf-8') as f:
            f.write(env_template)
        print(f"✅ 環境変数ファイル作成完了: {env_file_path}")
        print("📝 実際の値を設定してください")
        return True
    except Exception as e:
        print(f"❌ 環境変数ファイル作成エラー: {e}")
        return False

def run_tests():
    """テストの実行"""
    print("\n🧪 テスト実行")
    print("=" * 30)
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 'tests/', '-v'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            print("✅ テスト成功")
            print(result.stdout)
            return True
        else:
            print("❌ テスト失敗")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 領収書自動処理システム 統合セットアップ")
    print("=" * 60)
    
    # 環境確認
    check_environment()
    
    # セットアップ手順
    setup_steps = [
        ("環境変数ファイル作成", create_env_file),
        ("Notion設定", setup_notion),
        ("Google Drive設定", setup_google_drive),
        ("テスト実行", run_tests)
    ]
    
    success_count = 0
    
    for step_name, step_func in setup_steps:
        print(f"\n{'='*60}")
        print(f"📋 ステップ: {step_name}")
        print(f"{'='*60}")
        
        try:
            if step_func():
                print(f"✅ {step_name}: 完了")
                success_count += 1
            else:
                print(f"❌ {step_name}: 失敗")
                retry = input("このステップをスキップして続行しますか？ (y/n): ").lower().strip()
                if retry != 'y':
                    print("セットアップを中止します")
                    return False
        except KeyboardInterrupt:
            print("\n⚠️  ユーザーによって中断されました")
            return False
        except Exception as e:
            print(f"❌ {step_name}で予期しないエラー: {e}")
            return False
    
    # 結果表示
    print(f"\n{'='*60}")
    print("🎉 セットアップ完了")
    print(f"{'='*60}")
    print(f"✅ 成功: {success_count}/{len(setup_steps)}")
    
    if success_count == len(setup_steps):
        print("\n🎯 全ての設定が完了しました！")
        print("次のステップ:")
        print("1. .envファイルに実際の値を設定")
        print("2. python receipt-processor/main.py でテスト実行")
        print("3. GitHub Actionsで自動化設定")
    else:
        print("\n⚠️  一部の設定が失敗しました")
        print("失敗したステップを手動で完了してください")
    
    return success_count == len(setup_steps)

if __name__ == "__main__":
    main()

