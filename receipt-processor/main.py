"""
領収書自動処理システム メインファイル（運用最適化版）
"""
import os
import sys
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import setup_logging
from config.settings import (
    validate_settings,
    GOOGLE_DRIVE_MONITOR_FOLDER,
    LOG_LEVEL,
    LOG_FILE,
    GEMINI_API_KEY
)
from google_drive_client import GoogleDriveClient
from vision_client import VisionClient
from gemini_client import GeminiClient
from notion_api_client import NotionClient
from pdf_processor import PDFProcessor
from receipt_parser import ReceiptParser
from file_manager import FileManager

# Phase 4: 運用最適化機能のインポート
from error_handler import ErrorHandler, ErrorCategory, ErrorSeverity, handle_error
from monitoring import ProcessingMonitor, ProcessingStatus, MonitoringContext, global_monitor
from performance_optimizer import PerformanceOptimizer, global_optimizer, performance_optimized, timed_execution
from debug_utils import DebugManager, global_debug_manager, debug_operation, debug_session

@timed_execution
def main():
    """メイン処理（運用最適化版）"""
    session_id = f"main_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # デバッグセッションの開始
    global_debug_manager.enable_debug(session_id)
    
    try:
        # ログ設定の初期化
        logger = setup_logging(LOG_LEVEL, LOG_FILE)
        logger.info("領収書自動処理システム開始（運用最適化版）")
        
        # パフォーマンス監視の開始
        monitor_session = global_monitor.start_processing(session_id)
        
        # 設定の検証
        errors = validate_settings()
        if errors:
            for error in errors:
                logger.error(f"設定エラー: {error}")
            
            global_monitor.end_processing(
                session_id, 
                ProcessingStatus.FAILED,
                error_message=f"設定エラー: {errors}"
            )
            return False
        
        # 各クライアントの初期化（パフォーマンス最適化）
        logger.info("クライアント初期化開始")
        
        try:
            with MonitoringContext(f"{session_id}_init"):
                google_drive_client = GoogleDriveClient()
                vision_client = VisionClient()
                gemini_client = GeminiClient(GEMINI_API_KEY) if GEMINI_API_KEY else None
                notion_client = NotionClient()
                pdf_processor = PDFProcessor()
                receipt_parser = ReceiptParser()
                file_manager = FileManager(google_drive_client)
                
            logger.info("クライアント初期化完了")
            
        except Exception as e:
            error_result = handle_error(
                e, ErrorCategory.CONFIGURATION, 
                {"component": "client_initialization"}, 
                ErrorSeverity.CRITICAL
            )
            logger.error(f"クライアント初期化エラー: {error_result['user_message']}")
            
            global_monitor.end_processing(
                session_id, 
                ProcessingStatus.FAILED,
                error_message=str(e)
            )
            return False
        
        # 新規ファイルの取得（エラーハンドリング強化）
        logger.info("新規ファイル検索開始")
        
        try:
            new_files = google_drive_client.get_new_files(GOOGLE_DRIVE_MONITOR_FOLDER, use_shared_drive=True)
        except Exception as e:
            error_result = handle_error(
                e, ErrorCategory.NETWORK, 
                {"operation": "get_new_files"}, 
                ErrorSeverity.HIGH
            )
            logger.error(f"ファイル取得エラー: {error_result['user_message']}")
            
            global_monitor.end_processing(
                session_id, 
                ProcessingStatus.FAILED,
                error_message=str(e)
            )
            return False
        
        if not new_files:
            logger.info("新規ファイルが見つかりませんでした")
            global_monitor.end_processing(session_id, ProcessingStatus.SUCCESS)
            return True
        
        logger.info(f"新規ファイル数: {len(new_files)}")
        
        # 各ファイルを処理（パフォーマンス最適化とエラーハンドリング）
        success_count = 0
        error_count = 0
        retry_success_count = 0  # 再処理成功カウントの初期化
        
        # パフォーマンス監視の開始
        perf_monitor = global_optimizer.monitor_performance()
        logger.info(f"システム状況: CPU {perf_monitor['metrics'].cpu_usage}%, メモリ {perf_monitor['metrics'].memory_usage}%")
        
        for file_info in new_files:
            file_session_id = f"{session_id}_file_{uuid.uuid4().hex[:8]}"
            
            try:
                with MonitoringContext(file_session_id, file_info.get('name'), file_info.get('size')):
                    success = process_file_optimized(
                        file_info,
                        google_drive_client,
                        vision_client,
                        gemini_client,
                        notion_client,
                        pdf_processor,
                        receipt_parser,
                        file_manager,
                        logger,
                        file_session_id
                    )
                    
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        
            except Exception as e:
                error_result = handle_error(
                    e, ErrorCategory.SYSTEM, 
                    {"file_name": file_info.get('name', 'unknown')}, 
                    ErrorSeverity.MEDIUM
                )
                logger.error(f"ファイル処理エラー: {error_result['user_message']}")
                error_count += 1
            
            # 自動最適化の実行
            if (success_count + error_count) % 5 == 0:  # 5ファイル毎に最適化
                optimization_result = global_optimizer.auto_optimize()
                if optimization_result['optimizations_applied']:
                    logger.info(f"自動最適化実行: {optimization_result['optimizations_applied']}")
        
        # 処理結果のログ出力
        logger.info(f"処理完了 - 成功: {success_count}, エラー: {error_count}")
        
        # 🔍 抜け漏れ防止：処理完了後の検証
        verification_result = None
        final_verification = None
        
        try:
            verification_result = verify_processing_completion(
                new_files, success_count, error_count, 
                google_drive_client, logger
            )
            
            if not verification_result['all_processed']:
                logger.warning(f"⚠️ 未処理ファイル検出: {verification_result['unprocessed_files']}")
                logger.warning(f"⚠️ 抜け漏れ防止のため、未処理ファイルを再処理します")
                
                # 未処理ファイルの再処理
                retry_success_count = 0
                for unprocessed_file in verification_result['unprocessed_files']:
                    try:
                        with MonitoringContext(f"{session_id}_retry_{uuid.uuid4().hex[:8]}", 
                                             unprocessed_file.get('name'), unprocessed_file.get('size')):
                            retry_success = process_file_optimized(
                                unprocessed_file,
                                google_drive_client,
                                vision_client,
                                gemini_client,
                                notion_client,
                                pdf_processor,
                                receipt_parser,
                                file_manager,
                                logger,
                                f"{session_id}_retry"
                            )
                            
                            if retry_success:
                                retry_success_count += 1
                                logger.info(f"再処理成功: {unprocessed_file.get('name')}")
                            else:
                                logger.error(f"再処理失敗: {unprocessed_file.get('name')}")
                                
                    except Exception as e:
                        logger.error(f"再処理エラー: {unprocessed_file.get('name')}, {e}")
                
                logger.info(f"再処理完了 - 成功: {retry_success_count}/{len(verification_result['unprocessed_files'])}")
                
                # 最終検証
                final_verification = verify_processing_completion(
                    new_files, success_count + retry_success_count, error_count, 
                    google_drive_client, logger
                )
                
                if not final_verification['all_processed']:
                    logger.error(f"❌ 抜け漏れが残存: {final_verification['unprocessed_files']}")
                    # エラーフォルダに移動して手動確認を促す
                    for unprocessed_file in final_verification['unprocessed_files']:
                        try:
                            google_drive_client.move_file_to_error_folder(
                                unprocessed_file['id'], 
                                f"未処理ファイル: {unprocessed_file['name']}"
                            )
                            logger.warning(f"未処理ファイルをエラーフォルダに移動: {unprocessed_file['name']}")
                        except Exception as e:
                            logger.error(f"エラーフォルダ移動失敗: {unprocessed_file['name']}, {e}")
                else:
                    logger.info("✅ すべてのファイルが正常に処理されました")
            else:
                logger.info("✅ すべてのファイルが正常に処理されました")
                
        except Exception as e:
            logger.error(f"抜け漏れ検証エラー: {e}")
            verification_result = None
            final_verification = None
        
        # 最終的な監視結果
        final_status = ProcessingStatus.SUCCESS if error_count == 0 else ProcessingStatus.FAILED
        global_monitor.end_processing(
            session_id, 
            final_status,
            confidence_score=success_count / (success_count + error_count) if (success_count + error_count) > 0 else 0
        )
        
        # パフォーマンスレポートの出力
        performance_insights = global_optimizer.get_optimization_recommendations()
        if performance_insights:
            logger.info(f"パフォーマンス推奨事項: {performance_insights}")
        
        # 🔍 抜け漏れ防止：最終レポート
        logger.info("=" * 60)
        logger.info("📊 処理完了レポート")
        logger.info("=" * 60)
        logger.info(f"📁 総ファイル数: {len(new_files)}")
        logger.info(f"✅ 処理成功: {success_count}")
        logger.info(f"❌ 処理失敗: {error_count}")
        logger.info(f"🔄 再処理成功: {retry_success_count}")
        logger.info(f"📈 成功率: {((success_count + retry_success_count) / len(new_files) * 100):.1f}%")
        
        if verification_result:
            logger.info(f"🔍 未処理ファイル: {len(verification_result['unprocessed_files'])}")
            if verification_result['unprocessed_files']:
                logger.warning("⚠️ 未処理ファイル一覧:")
                for unprocessed in verification_result['unprocessed_files']:
                    logger.warning(f"   - {unprocessed.get('name', 'unknown')}")
        else:
            logger.info("🔍 未処理ファイル検証: 実行されませんでした")
        
        # 最終検証結果の表示
        if final_verification:
            logger.info(f"🔍 最終検証 - 未処理ファイル: {len(final_verification['unprocessed_files'])}")
            if final_verification['unprocessed_files']:
                logger.error("❌ 抜け漏れが残存:")
                for unprocessed in final_verification['unprocessed_files']:
                    logger.error(f"   - {unprocessed.get('name', 'unknown')}")
        else:
            logger.info("🔍 最終検証: 実行されませんでした")
        
        logger.info("=" * 60)
        
        return error_count == 0
        
    except Exception as e:
        error_result = handle_error(
            e, ErrorCategory.SYSTEM, 
            {"operation": "main_process"}, 
            ErrorSeverity.CRITICAL
        )
        logger.error(f"システムエラー: {error_result['user_message']}")
        
        global_monitor.end_processing(
            session_id, 
            ProcessingStatus.FAILED,
            error_message=str(e)
        )
        return False
    
    finally:
        # デバッグセッションの終了
        global_debug_manager.disable_debug()

@debug_operation("process_file_optimized")
@performance_optimized()
def process_file_optimized(file_info: Dict[str, Any], google_drive_client: GoogleDriveClient,
                          vision_client: VisionClient, gemini_client: GeminiClient, notion_client: NotionClient,
                          pdf_processor: PDFProcessor, receipt_parser: ReceiptParser,
                          file_manager: FileManager, logger: structlog.BoundLogger,
                          session_id: str) -> bool:
    """
    個別ファイルの処理（運用最適化版）
    
    Args:
        file_info: ファイル情報
        google_drive_client: Google Driveクライアント
        vision_client: Vision APIクライアント
        notion_client: Notionクライアント
        pdf_processor: PDF処理クラス
        receipt_parser: 領収書解析クラス
        file_manager: ファイル管理クラス
        logger: ロガー
        session_id: セッションID
        
    Returns:
        bool: 処理成功時はTrue
    """
    file_id = file_info['id']
    file_name = file_info['name']
    
    logger.info(f"ファイル処理開始: {file_name}")
    
    try:
        # 一時ディレクトリの作成
        temp_dir = file_manager.create_temp_directory()
        local_file_path = os.path.join(temp_dir, file_name)
        
        # ファイルのダウンロード（エラーハンドリング強化）
        try:
            if not google_drive_client.download_file(file_id, local_file_path):
                error_result = handle_error(
                    Exception("ファイルダウンロード失敗"),
                    ErrorCategory.NETWORK,
                    {"file_name": file_name, "file_id": file_id},
                    ErrorSeverity.HIGH
                )
                logger.error(f"ファイルダウンロード失敗: {file_name}")
                return False
        except Exception as e:
            handle_error(e, ErrorCategory.NETWORK, {"file_name": file_name})
            return False
        
        # ファイルの妥当性チェック
        is_valid, error_message = file_manager.validate_file(local_file_path)
        if not is_valid:
            handle_error(
                Exception(f"ファイル妥当性チェック失敗: {error_message}"),
                ErrorCategory.VALIDATION,
                {"file_name": file_name},
                ErrorSeverity.MEDIUM
            )
            logger.error(f"ファイル妥当性チェック失敗: {file_name}, {error_message}")
            file_manager.move_file_to_error_folder(local_file_path)
            return False
        
        # ファイルタイプの判定
        file_type = file_manager.get_file_type(local_file_path)
        
        if file_type == 'pdf':
            # PDFファイルの処理
            success = process_pdf_file_optimized(
                local_file_path, file_name, file_id,
                google_drive_client, vision_client, gemini_client, notion_client,
                pdf_processor, receipt_parser, file_manager, logger, session_id
            )
        elif file_type == 'image':
            # 画像ファイルの処理
            success = process_image_file_optimized(
                local_file_path, file_name, file_id,
                google_drive_client, vision_client, gemini_client, notion_client,
                receipt_parser, file_manager, logger, session_id
            )
        else:
            handle_error(
                Exception(f"未対応のファイルタイプ: {file_type}"),
                ErrorCategory.VALIDATION,
                {"file_name": file_name, "file_type": file_type},
                ErrorSeverity.MEDIUM
            )
            logger.error(f"未対応のファイルタイプ: {file_type}")
            file_manager.move_file_to_error_folder(local_file_path)
            return False
        
        # 一時ディレクトリのクリーンアップ
        file_manager.cleanup_temp_directory()
        
        return success
        
    except Exception as e:
        handle_error(e, ErrorCategory.SYSTEM, {"file_name": file_name})
        logger.error(f"ファイル処理エラー: {file_name}, {e}")
        return False

def process_file(file_info: Dict[str, Any], google_drive_client: GoogleDriveClient,
                vision_client: VisionClient, notion_client: NotionClient,
                pdf_processor: PDFProcessor, receipt_parser: ReceiptParser,
                file_manager: FileManager, logger: structlog.BoundLogger) -> bool:
    """
    個別ファイルの処理
    
    Args:
        file_info: ファイル情報
        google_drive_client: Google Driveクライアント
        vision_client: Vision APIクライアント
        notion_client: Notionクライアント
        pdf_processor: PDF処理クラス
        receipt_parser: 領収書解析クラス
        file_manager: ファイル管理クラス
        logger: ロガー
        
    Returns:
        bool: 処理成功時はTrue
    """
    file_id = file_info['id']
    file_name = file_info['name']
    
    logger.info(f"ファイル処理開始: {file_name}")
    
    try:
        # 一時ディレクトリの作成
        temp_dir = file_manager.create_temp_directory()
        local_file_path = os.path.join(temp_dir, file_name)
        
        # ファイルのダウンロード
        if not google_drive_client.download_file(file_id, local_file_path):
            logger.error(f"ファイルダウンロード失敗: {file_name}")
            return False
        
        # ファイルの妥当性チェック
        is_valid, error_message = file_manager.validate_file(local_file_path)
        if not is_valid:
            logger.error(f"ファイル妥当性チェック失敗: {file_name}, {error_message}")
            file_manager.move_file_to_error_folder(local_file_path)
            return False
        
        # ファイルタイプの判定
        file_type = file_manager.get_file_type(local_file_path)
        
        if file_type == 'pdf':
            # PDFファイルの処理
            success = process_pdf_file(
                local_file_path, file_name, file_id,
                google_drive_client, vision_client, notion_client,
                pdf_processor, receipt_parser, file_manager, logger
            )
        elif file_type == 'image':
            # 画像ファイルの処理
            success = process_image_file(
                local_file_path, file_name, file_id,
                google_drive_client, vision_client, notion_client,
                receipt_parser, file_manager, logger
            )
        else:
            logger.error(f"未対応のファイルタイプ: {file_type}")
            file_manager.move_file_to_error_folder(local_file_path)
            return False
        
        # 一時ディレクトリのクリーンアップ
        file_manager.cleanup_temp_directory()
        
        return success
        
    except Exception as e:
        logger.error(f"ファイル処理エラー: {file_name}, {e}")
        return False

@debug_operation("process_pdf_file_optimized")
@timed_execution
def process_pdf_file_optimized(file_path: str, file_name: str, file_id: str,
                              google_drive_client: GoogleDriveClient, vision_client: VisionClient,
                              gemini_client: GeminiClient, notion_client: NotionClient, 
                              pdf_processor: PDFProcessor, receipt_parser: ReceiptParser, 
                              file_manager: FileManager, logger: structlog.BoundLogger, 
                              session_id: str) -> bool:
    """
    PDFファイルの処理（最適化版）
    
    Args:
        file_path: ファイルパス
        file_name: ファイル名
        file_id: ファイルID
        google_drive_client: Google Driveクライアント
        vision_client: Vision APIクライアント
        gemini_client: Gemini APIクライアント
        notion_client: Notionクライアント
        pdf_processor: PDF処理クラス
        receipt_parser: 領収書解析クラス
        file_manager: ファイル管理クラス
        logger: ロガー
        session_id: セッションID
        
    Returns:
        bool: 処理成功時はTrue
    """
    try:
        logger.info(f"PDF処理開始: {file_name}")
        
        # PDFの妥当性チェック
        if not pdf_processor.validate_pdf(file_path):
            handle_error(
                Exception("PDF妥当性チェック失敗"),
                ErrorCategory.VALIDATION,
                {"file_name": file_name},
                ErrorSeverity.MEDIUM
            )
            logger.error(f"PDF妥当性チェック失敗: {file_name}")
            file_manager.move_file_to_error_folder(file_path)
            return False
        
        # PDFページ数の取得
        page_count = pdf_processor.get_page_count(file_path)
        logger.info(f"PDFページ数: {page_count}")
        
        # 画像への変換
        temp_dir = file_manager.create_temp_directory()
        image_paths = pdf_processor.convert_pdf_to_images(file_path, temp_dir)
        
        if not image_paths:
            handle_error(
                Exception("PDF画像変換失敗"),
                ErrorCategory.FILE_IO,
                {"file_name": file_name, "page_count": page_count},
                ErrorSeverity.HIGH
            )
            logger.error(f"PDF画像変換失敗: {file_name}")
            file_manager.move_file_to_error_folder(file_path)
            return False
        
        logger.info(f"画像変換完了: {len(image_paths)}ページ")
        
        # 🔍 抜け漏れ防止：ページ数チェック
        if len(image_paths) != page_count:
            logger.warning(f"⚠️ ページ数不一致: 期待値{page_count} vs 実際{len(image_paths)}")
            logger.warning(f"⚠️ 抜け漏れの可能性があります")
        
        # 各ページの処理（バッチ処理で最適化）
        created_records = []
        failed_pages = []
        
        # バッチサイズを1に設定（抜け漏れ防止のため）
        batch_size = 1
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_results = []
            
            for j, image_path in enumerate(batch_paths):
                page_num = i + j + 1
                
                try:
                    page_id = process_pdf_page(
                        image_path, page_num, len(image_paths),
                        file_name, file_id, vision_client, gemini_client,
                        receipt_parser, notion_client, logger
                    )
                    
                    if page_id:
                        batch_results.append(page_id)
                        logger.info(f"ページ{page_num}処理成功: {page_id}")
                    else:
                        failed_pages.append(page_num)
                        logger.error(f"ページ{page_num}処理失敗")
                        
                except Exception as e:
                    failed_pages.append(page_num)
                    handle_error(e, ErrorCategory.OCR, {"file_name": file_name, "page_num": page_num})
                    logger.error(f"ページ{page_num}処理エラー: {e}")
            
            created_records.extend([r for r in batch_results if r])
        
        # 🔍 抜け漏れ防止：失敗ページの報告
        if failed_pages:
            logger.warning(f"⚠️ 失敗ページ: {failed_pages}")
            logger.warning(f"⚠️ 総ページ数: {len(image_paths)}, 成功: {len(created_records)}, 失敗: {len(failed_pages)}")
        
        # 処理結果の判定
        if created_records:
            # 成功時：処理済みフォルダに移動
            # PDF処理では現在日時を使用（各ページの日付が異なる可能性があるため）
            file_manager.move_file_to_processed_folder(file_path, datetime.now(), file_id)
            
            logger.info(f"PDF処理完了: {file_name}, 作成レコード数: {len(created_records)}")
            
            # 🔍 抜け漏れ防止：最終確認
            if len(created_records) < len(image_paths):
                logger.warning(f"⚠️ 一部ページの処理に失敗: {len(created_records)}/{len(image_paths)}")
                logger.warning(f"⚠️ 失敗ページ: {failed_pages}")
            
            return True
        else:
            # 失敗時：エラーフォルダに移動
            file_manager.move_file_to_error_folder(file_path)
            logger.error(f"PDF処理失敗: {file_name}")
            return False
            
    except Exception as e:
        handle_error(e, ErrorCategory.SYSTEM, {"file_name": file_name, "operation": "pdf_processing"})
        logger.error(f"PDF処理エラー: {file_name}, {e}")
        file_manager.move_file_to_error_folder(file_path)
        return False

def process_pdf_page(image_path: str, page_num: int, total_pages: int, 
                    file_name: str, file_id: str, vision_client: VisionClient, 
                    gemini_client: GeminiClient, receipt_parser: ReceiptParser, 
                    notion_client: NotionClient, logger: structlog.BoundLogger) -> Optional[str]:
    """PDFページの処理（Gemini優先）"""
    try:
        # Geminiによる領収書解析（優先）
        receipt_data = None
        if gemini_client:
            try:
                receipt_data = gemini_client.extract_receipt_data(image_path)
                if receipt_data:
                    receipt_data['processing_method'] = 'gemini'
                    logger.info(f"Gemini解析成功: ページ{page_num}")
            except Exception as e:
                logger.warning(f"Gemini解析失敗: ページ{page_num}, {e}")
        
        # Geminiが失敗した場合は従来のOCR処理
        if not receipt_data:
            ocr_text = vision_client.extract_text_from_image(image_path)
            if not ocr_text:
                logger.warning(f"OCR処理失敗: ページ{page_num}")
                return None
            
            receipt_data = receipt_parser.parse_receipt_data(ocr_text, image_path)
            receipt_data['processing_method'] = 'vision'
        
        # ページ情報を追加
        receipt_data['page_number'] = page_num
        receipt_data['total_pages'] = total_pages
        receipt_data['original_file_name'] = file_name
        receipt_data['original_file_id'] = file_id
        
        # 日付の処理
        from datetime import datetime
        date_str = receipt_data.get('date')
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                receipt_data['date'] = date_obj
            except:
                receipt_data['date'] = datetime.now()
        else:
            receipt_data['date'] = datetime.now()
        
        # 店舗名の短縮処理
        from utils import extract_store_name_from_text
        store_name = receipt_data.get('store_name')
        short_store_name = extract_store_name_from_text(store_name) if store_name else store_name
        receipt_data['store_name'] = short_store_name
        
        # カテゴリと勘定科目の推測
        from config.mapping import get_category_and_account
        category, account = get_category_and_account(short_store_name)
        receipt_data['category'] = category
        receipt_data['account'] = account
        
        # タイトルの生成
        from utils import generate_title
        total_amount = receipt_data.get('total_amount')
        receipt_data['title'] = generate_title(account, total_amount)
        
        # Notionに保存
        page_id = notion_client.create_receipt_page(receipt_data, image_path)
        if page_id:
            logger.info(f"ページ{page_num}のNotion保存完了: {page_id}")
            return page_id
        else:
            logger.error(f"ページ{page_num}のNotion保存失敗")
            return None
            
    except Exception as e:
        handle_error(e, ErrorCategory.OCR, {"page_num": page_num, "file_name": file_name})
        logger.error(f"ページ{page_num}処理エラー: {e}")
        return None

@debug_operation("process_image_file_optimized")
@timed_execution
def process_image_file_optimized(file_path: str, file_name: str, file_id: str,
                                google_drive_client: GoogleDriveClient, vision_client: VisionClient,
                                gemini_client: GeminiClient, notion_client: NotionClient, 
                                receipt_parser: ReceiptParser, file_manager: FileManager, 
                                logger: structlog.BoundLogger, session_id: str) -> bool:
    """
    画像ファイルの処理（運用最適化版）
    """
    try:
        logger.info(f"画像処理開始: {file_name}")
        
        # Geminiによる領収書解析（優先）またはOCR処理
        try:
            if gemini_client:
                # Geminiで構造化データを直接抽出
                receipt_data = gemini_client.extract_receipt_data(file_path)
                if receipt_data:
                    receipt_data['original_file_name'] = file_name
                    receipt_data['original_file_id'] = file_id
                    receipt_data['processing_method'] = 'gemini'
                    
                    # Geminiデータでタイトル生成
                    from utils import generate_title
                    from datetime import datetime
                    
                    store_name = receipt_data.get('store_name')
                    total_amount = receipt_data.get('total_amount')
                    date_str = receipt_data.get('date')
                    
                    # 日付が文字列の場合はdatetimeオブジェクトに変換
                    if date_str:
                        try:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        except:
                            date_obj = datetime.now()
                    else:
                        date_obj = datetime.now()
                    
                    # receipt_dataにdatetimeオブジェクトを設定
                    receipt_data['date'] = date_obj
                    
                    # 店舗名の短縮処理
                    from utils import extract_store_name_from_text
                    short_store_name = extract_store_name_from_text(store_name) if store_name else store_name
                    receipt_data['store_name'] = short_store_name
                    
                    # カテゴリと勘定科目の推測（短縮後の店舗名で）
                    from config.mapping import get_category_and_account
                    category, account = get_category_and_account(short_store_name)
                    receipt_data['category'] = category
                    receipt_data['account_item'] = account
                    
                    # タイトル生成（勘定科目+金額）
                    receipt_data['title'] = generate_title(account, total_amount)
                    
                    logger.info(f"Gemini解析成功: {short_store_name} - カテゴリ: {category}, 勘定科目: {account}")
                else:
                    # Gemini失敗時は従来のOCR処理にフォールバック
                    logger.warning(f"Gemini解析失敗、OCR処理にフォールバック: {file_name}")
                    ocr_text = vision_client.extract_text_from_image(file_path)
                    if not ocr_text:
                        handle_error(
                            Exception("OCR処理失敗"),
                            ErrorCategory.OCR,
                            {"file_name": file_name},
                            ErrorSeverity.HIGH
                        )
                        logger.error(f"OCR処理失敗: {file_name}")
                        file_manager.move_file_to_error_folder(file_path)
                        return False
                    
                    receipt_data = receipt_parser.parse_receipt_data(ocr_text, file_path)
                    receipt_data['original_file_name'] = file_name
                    receipt_data['original_file_id'] = file_id
                    receipt_data['processing_method'] = 'ocr'
                    
                    # パターン分析の実行
                    pattern_analysis = receipt_parser.analyze_text_patterns(ocr_text)
                    receipt_data['pattern_analysis'] = pattern_analysis
                    
                    # 学習提案の生成
                    learning_suggestions = receipt_parser.get_learning_suggestions(ocr_text, receipt_data)
                    if learning_suggestions:
                        logger.info(f"学習提案: {learning_suggestions}")
            else:
                # Gemini APIキーがない場合は従来のOCR処理
                logger.info(f"Gemini APIキーなし、OCR処理を使用: {file_name}")
                ocr_text = vision_client.extract_text_from_image(file_path)
                if not ocr_text:
                    handle_error(
                        Exception("OCR処理失敗"),
                        ErrorCategory.OCR,
                        {"file_name": file_name},
                        ErrorSeverity.HIGH
                    )
                    logger.error(f"OCR処理失敗: {file_name}")
                    file_manager.move_file_to_error_folder(file_path)
                    return False
                
                receipt_data = receipt_parser.parse_receipt_data(ocr_text, file_path)
                receipt_data['original_file_name'] = file_name
                receipt_data['original_file_id'] = file_id
                receipt_data['processing_method'] = 'ocr'
                
                # パターン分析の実行
                pattern_analysis = receipt_parser.analyze_text_patterns(ocr_text)
                receipt_data['pattern_analysis'] = pattern_analysis
                
                # 学習提案の生成
                learning_suggestions = receipt_parser.get_learning_suggestions(ocr_text, receipt_data)
                if learning_suggestions:
                    logger.info(f"学習提案: {learning_suggestions}")
                
        except Exception as e:
            handle_error(e, ErrorCategory.PARSING, {"file_name": file_name})
            return False
        
        # データの妥当性検証
        try:
            validation_errors = receipt_parser.validate_receipt_data(receipt_data)
            if validation_errors:
                logger.warning(f"データ検証警告: {file_name}, {validation_errors}")
                receipt_data['processing_status'] = '手動確認要'
                receipt_data['validation_errors'] = validation_errors
        except Exception as e:
            handle_error(e, ErrorCategory.VALIDATION, {"file_name": file_name})
        
        # Notionに保存（エラーハンドリング強化）
        try:
            page_id = notion_client.create_receipt_page(receipt_data, file_path)
            if not page_id:
                handle_error(
                    Exception("Notion保存失敗"),
                    ErrorCategory.API,
                    {"file_name": file_name},
                    ErrorSeverity.HIGH
                )
                logger.error(f"Notion保存失敗: {file_name}")
                file_manager.move_file_to_error_folder(file_path)
                return False
        except Exception as e:
            handle_error(e, ErrorCategory.API, {"file_name": file_name})
            return False
        
        # 処理済みフォルダに移動
        if receipt_data.get('date'):
            file_manager.move_file_to_processed_folder(file_path, receipt_data['date'], file_id)
        else:
            file_manager.move_file_to_processed_folder(file_path, datetime.now(), file_id)
        
        logger.info(f"画像処理完了: {file_name}, NotionページID: {page_id}")
        return True
        
    except Exception as e:
        handle_error(e, ErrorCategory.SYSTEM, {"file_name": file_name, "operation": "image_processing"})
        logger.error(f"画像処理エラー: {file_name}, {e}")
        file_manager.move_file_to_error_folder(file_path)
        return False

def process_pdf_file(file_path: str, file_name: str, file_id: str,
                    google_drive_client: GoogleDriveClient, vision_client: VisionClient,
                    notion_client: NotionClient, pdf_processor: PDFProcessor,
                    receipt_parser: ReceiptParser, file_manager: FileManager,
                    logger: structlog.BoundLogger) -> bool:
    """
    PDFファイルの処理
    
    Args:
        file_path: ファイルパス
        file_name: ファイル名
        file_id: ファイルID
        google_drive_client: Google Driveクライアント
        vision_client: Vision APIクライアント
        notion_client: Notionクライアント
        pdf_processor: PDF処理クラス
        receipt_parser: 領収書解析クラス
        file_manager: ファイル管理クラス
        logger: ロガー
        
    Returns:
        bool: 処理成功時はTrue
    """
    try:
        logger.info(f"PDF処理開始: {file_name}")
        
        # PDFの妥当性チェック
        if not pdf_processor.validate_pdf(file_path):
            logger.error(f"PDF妥当性チェック失敗: {file_name}")
            file_manager.move_file_to_error_folder(file_path)
            return False
        
        # PDFを画像に変換
        image_paths = pdf_processor.convert_pdf_to_images(file_path)
        if not image_paths:
            logger.error(f"PDF画像変換失敗: {file_name}")
            file_manager.move_file_to_error_folder(file_path)
            return False
        
        logger.info(f"PDF画像変換完了: {len(image_paths)}ページ")
        
        # 各ページを処理
        created_records = []
        
        for page_num, image_path in enumerate(image_paths, 1):
            try:
                # OCR処理
                ocr_text = vision_client.extract_text_from_image(image_path)
                if not ocr_text:
                    logger.warning(f"OCR処理失敗: ページ{page_num}")
                    continue
                
                # 領収書データの解析
                receipt_data = receipt_parser.parse_receipt_data(ocr_text, image_path)
                
                # ページ情報を追加
                receipt_data['page_number'] = page_num
                receipt_data['total_pages'] = len(image_paths)
                receipt_data['original_file_name'] = file_name
                
                # データの補強
                receipt_data = receipt_parser.enhance_receipt_data(receipt_data)
                
                # Notionに保存
                page_id = notion_client.create_receipt_page(receipt_data)
                if page_id:
                    created_records.append(page_id)
                    logger.info(f"ページ{page_num}のNotion保存完了: {page_id}")
                else:
                    logger.error(f"ページ{page_num}のNotion保存失敗")
                
            except Exception as e:
                logger.error(f"ページ{page_num}処理エラー: {e}")
                continue
        
        # 処理結果の判定
        if created_records:
            # 成功時：処理済みフォルダに移動
            if receipt_data.get('date'):
                file_manager.move_file_to_processed_folder(file_path, receipt_data['date'], file_id)
            else:
                file_manager.move_file_to_processed_folder(file_path, datetime.now(), file_id)
            
            logger.info(f"PDF処理完了: {file_name}, 作成レコード数: {len(created_records)}")
            return True
        else:
            # 失敗時：エラーフォルダに移動
            file_manager.move_file_to_error_folder(file_path)
            logger.error(f"PDF処理失敗: {file_name}")
            return False
            
    except Exception as e:
        logger.error(f"PDF処理エラー: {file_name}, {e}")
        file_manager.move_file_to_error_folder(file_path)
        return False

def process_image_file(file_path: str, file_name: str, file_id: str,
                      google_drive_client: GoogleDriveClient, vision_client: VisionClient,
                      notion_client: NotionClient, receipt_parser: ReceiptParser,
                      file_manager: FileManager, logger: structlog.BoundLogger) -> bool:
    """
    画像ファイルの処理
    
    Args:
        file_path: ファイルパス
        file_name: ファイル名
        file_id: ファイルID
        google_drive_client: Google Driveクライアント
        vision_client: Vision APIクライアント
        notion_client: Notionクライアント
        receipt_parser: 領収書解析クラス
        file_manager: ファイル管理クラス
        logger: ロガー
        
    Returns:
        bool: 処理成功時はTrue
    """
    try:
        logger.info(f"画像処理開始: {file_name}")
        
        # OCR処理
        ocr_text = vision_client.extract_text_from_image(file_path)
        if not ocr_text:
            logger.error(f"OCR処理失敗: {file_name}")
            file_manager.move_file_to_error_folder(file_path)
            return False
        
        # 領収書データの解析
        receipt_data = receipt_parser.parse_receipt_data(ocr_text, file_path)
        receipt_data['original_file_name'] = file_name
        
        # データの補強
        receipt_data = receipt_parser.enhance_receipt_data(receipt_data)
        
        # データの妥当性検証（強化版）
        validation_errors = receipt_parser.validate_receipt_data(receipt_data)
        
        # 金額の妥当性チェック
        total_amount = receipt_data.get('total_amount')
        if total_amount:
            if total_amount < 10:  # 10円未満は異常
                validation_errors.append(f'金額が異常に小さいです: ¥{total_amount}')
            elif total_amount > 100000:  # 10万円超は要確認
                validation_errors.append(f'金額が大きいです: ¥{total_amount:,}')
        
        # 支払い金額との整合性チェック
        payment_amount = receipt_data.get('payment_amount')
        if total_amount and payment_amount:
            if payment_amount < total_amount:
                validation_errors.append(f'支払い金額({payment_amount})が合計金額({total_amount})より小さいです')
            elif payment_amount > total_amount * 10:  # 10倍以上は異常
                validation_errors.append(f'支払い金額({payment_amount})が合計金額({total_amount})の10倍以上です')
        
        if validation_errors:
            logger.warning(f"データ検証警告: {file_name}, {validation_errors}")
            receipt_data['processing_status'] = '手動確認要'
        
        # Notionに保存
        page_id = notion_client.create_receipt_page(receipt_data)
        if not page_id:
            logger.error(f"Notion保存失敗: {file_name}")
            file_manager.move_file_to_error_folder(file_path)
            return False
        
        # 処理済みフォルダに移動
        if receipt_data.get('date'):
            file_manager.move_file_to_processed_folder(file_path, receipt_data['date'])
        else:
            file_manager.move_file_to_processed_folder(file_path, datetime.now())
        
        logger.info(f"画像処理完了: {file_name}, NotionページID: {page_id}")
        return True
        
    except Exception as e:
        logger.error(f"画像処理エラー: {file_name}, {e}")
        file_manager.move_file_to_error_folder(file_path)
        return False

def verify_processing_completion(new_files: List[Dict[str, Any]], processed_count: int, error_count: int,
                                 google_drive_client: GoogleDriveClient, logger: structlog.BoundLogger) -> Dict[str, Any]:
    """
    処理完了後の未処理ファイルの検出と報告を行う。
    
    Args:
        new_files: 新規ファイルのリスト
        processed_count: 処理成功したファイル数
        error_count: 処理失敗したファイル数
        google_drive_client: Google Driveクライアント
        logger: ロガー
        
    Returns:
        Dict[str, Any]: 検証結果
    """
    unprocessed_files = []
    processed_folder_id = google_drive_client.get_processed_folder_id()
    error_folder_id = google_drive_client.get_error_folder_id()
    
    for file_info in new_files:
        file_id = file_info['id']
        file_name = file_info['name']
        
        # 処理済みフォルダまたはエラーフォルダに存在するか確認
        try:
            is_in_processed = google_drive_client.file_exists_in_folder(file_id, processed_folder_id)
            is_in_error = google_drive_client.file_exists_in_folder(file_id, error_folder_id)
            
            if not is_in_processed and not is_in_error:
                unprocessed_files.append(file_info)
                logger.warning(f"未処理ファイル検出: {file_name}")
            else:
                logger.debug(f"処理済みファイル確認: {file_name} (処理済み: {is_in_processed}, エラー: {is_in_error})")
                
        except Exception as e:
            logger.warning(f"ファイル存在確認エラー: {file_name}, {e}")
            unprocessed_files.append(file_info)  # エラーが発生した場合も未処理とみなす
    
    logger.info(f"処理検証完了 - 総ファイル数: {len(new_files)}, 未処理: {len(unprocessed_files)}")
    
    return {
        'all_processed': len(unprocessed_files) == 0,
        'unprocessed_files': unprocessed_files,
        'total_files': len(new_files),
        'processed_files': len(new_files) - len(unprocessed_files)
    }

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
