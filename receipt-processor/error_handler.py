"""
統合エラーハンドリング機能
"""
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import traceback
import json

logger = structlog.get_logger()

class ErrorSeverity(Enum):
    """エラーの重要度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ErrorCategory(Enum):
    """エラーのカテゴリ"""
    NETWORK = "network"
    API = "api"
    FILE_IO = "file_io"
    OCR = "ocr"
    PARSING = "parsing"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"

class ErrorHandler:
    """統合エラーハンドリングクラス"""
    
    def __init__(self):
        self.error_log = []
        self.error_counts = {}
        self.recovery_strategies = self._initialize_recovery_strategies()
    
    def _initialize_recovery_strategies(self) -> Dict[ErrorCategory, Dict[str, Any]]:
        """回復戦略の初期化"""
        return {
            ErrorCategory.NETWORK: {
                "retry_count": 3,
                "retry_delay": 5,
                "fallback_action": "cache_for_later"
            },
            ErrorCategory.API: {
                "retry_count": 2,
                "retry_delay": 10,
                "fallback_action": "use_alternative_api"
            },
            ErrorCategory.FILE_IO: {
                "retry_count": 1,
                "retry_delay": 2,
                "fallback_action": "skip_file"
            },
            ErrorCategory.OCR: {
                "retry_count": 1,
                "retry_delay": 0,
                "fallback_action": "manual_review"
            },
            ErrorCategory.PARSING: {
                "retry_count": 0,
                "retry_delay": 0,
                "fallback_action": "use_fallback_parser"
            },
            ErrorCategory.VALIDATION: {
                "retry_count": 0,
                "retry_delay": 0,
                "fallback_action": "mark_for_review"
            },
            ErrorCategory.CONFIGURATION: {
                "retry_count": 0,
                "retry_delay": 0,
                "fallback_action": "use_default_config"
            },
            ErrorCategory.SYSTEM: {
                "retry_count": 1,
                "retry_delay": 5,
                "fallback_action": "graceful_shutdown"
            }
        }
    
    def handle_error(self, error: Exception, category: ErrorCategory, 
                    context: Dict[str, Any] = None, severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Dict[str, Any]:
        """
        エラーを処理し、適切な対応を返す
        
        Args:
            error: 発生したエラー
            category: エラーのカテゴリ
            context: エラーが発生した文脈情報
            severity: エラーの重要度
            
        Returns:
            Dict[str, Any]: エラー処理結果と推奨アクション
        """
        error_info = self._create_error_info(error, category, context, severity)
        self._log_error(error_info)
        self._update_error_statistics(category)
        
        # 回復戦略の決定
        recovery_action = self._determine_recovery_action(category, error_info)
        
        return {
            "error_id": error_info["error_id"],
            "should_retry": recovery_action["should_retry"],
            "retry_count": recovery_action["retry_count"],
            "retry_delay": recovery_action["retry_delay"],
            "fallback_action": recovery_action["fallback_action"],
            "user_message": recovery_action["user_message"],
            "technical_details": error_info
        }
    
    def _create_error_info(self, error: Exception, category: ErrorCategory, 
                          context: Dict[str, Any], severity: ErrorSeverity) -> Dict[str, Any]:
        """エラー情報を作成"""
        error_id = f"{category.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.error_log)}"
        
        return {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "category": category.value,
            "severity": severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "context": context or {},
            "system_info": self._get_system_info()
        }
    
    def _log_error(self, error_info: Dict[str, Any]):
        """エラーをログに記録"""
        self.error_log.append(error_info)
        
        # 構造化ログに出力
        if error_info["severity"] in ["critical", "high"]:
            logger.error(
                "高重要度エラー発生",
                error_id=error_info["error_id"],
                category=error_info["category"],
                error_type=error_info["error_type"],
                error_message=error_info["error_message"]
            )
        else:
            logger.warning(
                "エラー発生",
                error_id=error_info["error_id"],
                category=error_info["category"],
                error_type=error_info["error_type"]
            )
    
    def _update_error_statistics(self, category: ErrorCategory):
        """エラー統計を更新"""
        category_key = category.value
        if category_key not in self.error_counts:
            self.error_counts[category_key] = {
                "total": 0,
                "today": 0,
                "last_occurrence": None
            }
        
        self.error_counts[category_key]["total"] += 1
        self.error_counts[category_key]["today"] += 1
        self.error_counts[category_key]["last_occurrence"] = datetime.now().isoformat()
    
    def _determine_recovery_action(self, category: ErrorCategory, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """回復アクションを決定"""
        strategy = self.recovery_strategies.get(category, {})
        
        # エラー頻度による調整
        error_count = self.error_counts.get(category.value, {}).get("total", 0)
        should_retry = error_count <= strategy.get("retry_count", 0)
        
        return {
            "should_retry": should_retry,
            "retry_count": strategy.get("retry_count", 0),
            "retry_delay": strategy.get("retry_delay", 0),
            "fallback_action": strategy.get("fallback_action", "manual_review"),
            "user_message": self._generate_user_message(category, error_info, should_retry)
        }
    
    def _generate_user_message(self, category: ErrorCategory, error_info: Dict[str, Any], should_retry: bool) -> str:
        """ユーザー向けメッセージを生成"""
        severity = error_info["severity"]
        
        if severity == "critical":
            return "システムで重大なエラーが発生しました。管理者にお問い合わせください。"
        elif severity == "high":
            return "処理中にエラーが発生しました。自動で修復を試みます。"
        elif should_retry:
            return "一時的なエラーが発生しました。自動で再試行します。"
        else:
            return "処理中に問題が発生しました。手動での確認が必要です。"
    
    def _get_system_info(self) -> Dict[str, Any]:
        """システム情報を取得"""
        import os
        import platform
        import psutil
        
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "working_directory": os.getcwd()
        }
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """エラーサマリーを取得"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent_errors = [
            error for error in self.error_log
            if datetime.fromisoformat(error["timestamp"]).timestamp() > cutoff_time
        ]
        
        # カテゴリ別集計
        category_counts = {}
        severity_counts = {}
        
        for error in recent_errors:
            category = error["category"]
            severity = error["severity"]
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "period_hours": hours,
            "total_errors": len(recent_errors),
            "category_breakdown": category_counts,
            "severity_breakdown": severity_counts,
            "most_frequent_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None,
            "critical_errors": [e for e in recent_errors if e["severity"] == "critical"],
            "recommendations": self._generate_recommendations(category_counts, severity_counts)
        }
    
    def _generate_recommendations(self, category_counts: Dict[str, int], 
                                 severity_counts: Dict[str, int]) -> List[str]:
        """改善提案を生成"""
        recommendations = []
        
        if severity_counts.get("critical", 0) > 0:
            recommendations.append("重大エラーが発生しています。システム設定を確認してください。")
        
        if category_counts.get("network", 0) > 5:
            recommendations.append("ネットワークエラーが頻発しています。接続を確認してください。")
        
        if category_counts.get("ocr", 0) > 3:
            recommendations.append("OCRエラーが多発しています。画像品質を確認してください。")
        
        if sum(category_counts.values()) > 10:
            recommendations.append("エラーが多発しています。システムの健全性を確認してください。")
        
        return recommendations
    
    def export_error_log(self, file_path: str, hours: int = 24):
        """エラーログをファイルにエクスポート"""
        summary = self.get_error_summary(hours)
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "summary": summary,
            "detailed_errors": [
                error for error in self.error_log
                if datetime.fromisoformat(error["timestamp"]).timestamp() > 
                (datetime.now().timestamp() - hours * 3600)
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"エラーログをエクスポートしました: {file_path}")

# グローバルエラーハンドラーインスタンス
global_error_handler = ErrorHandler()

def handle_error(error: Exception, category: ErrorCategory, 
                context: Dict[str, Any] = None, severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Dict[str, Any]:
    """グローバルエラーハンドリング関数"""
    return global_error_handler.handle_error(error, category, context, severity)

