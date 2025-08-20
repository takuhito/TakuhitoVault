"""
処理状況監視・可視化機能
"""
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import time
from dataclasses import dataclass, asdict
from enum import Enum

logger = structlog.get_logger()

class ProcessingStatus(Enum):
    """処理ステータス"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    SKIPPED = "skipped"

@dataclass
class ProcessingMetrics:
    """処理メトリクス"""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    confidence_score: Optional[float] = None
    extraction_count: Optional[int] = None
    error_message: Optional[str] = None

class ProcessingMonitor:
    """処理監視クラス"""
    
    def __init__(self):
        self.processing_history: List[ProcessingMetrics] = []
        self.current_sessions: Dict[str, ProcessingMetrics] = {}
        self.performance_stats = {
            "total_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "average_processing_time": 0.0,
            "average_confidence_score": 0.0
        }
    
    def start_processing(self, session_id: str, file_path: str = None, file_size: int = None) -> ProcessingMetrics:
        """処理開始を記録"""
        metrics = ProcessingMetrics(
            start_time=datetime.now(),
            status=ProcessingStatus.PROCESSING,
            file_path=file_path,
            file_size=file_size
        )
        
        self.current_sessions[session_id] = metrics
        
        logger.info(
            "処理開始",
            session_id=session_id,
            file_path=file_path,
            file_size=file_size
        )
        
        return metrics
    
    def end_processing(self, session_id: str, status: ProcessingStatus, 
                      confidence_score: float = None, extraction_count: int = None,
                      error_message: str = None) -> ProcessingMetrics:
        """処理終了を記録"""
        if session_id not in self.current_sessions:
            logger.warning(f"不明なセッションID: {session_id}")
            return None
        
        metrics = self.current_sessions[session_id]
        metrics.end_time = datetime.now()
        metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.status = status
        metrics.confidence_score = confidence_score
        metrics.extraction_count = extraction_count
        metrics.error_message = error_message
        
        # 履歴に追加
        self.processing_history.append(metrics)
        
        # 現在のセッションから削除
        del self.current_sessions[session_id]
        
        # 統計を更新
        self._update_performance_stats(metrics)
        
        logger.info(
            "処理完了",
            session_id=session_id,
            status=status.value,
            duration=metrics.duration_seconds,
            confidence_score=confidence_score
        )
        
        return metrics
    
    def _update_performance_stats(self, metrics: ProcessingMetrics):
        """パフォーマンス統計を更新"""
        self.performance_stats["total_files"] += 1
        
        if metrics.status == ProcessingStatus.SUCCESS:
            self.performance_stats["successful_files"] += 1
        elif metrics.status == ProcessingStatus.FAILED:
            self.performance_stats["failed_files"] += 1
        
        # 平均処理時間の更新
        if metrics.duration_seconds:
            total_time = (self.performance_stats["average_processing_time"] * 
                         (self.performance_stats["total_files"] - 1) + 
                         metrics.duration_seconds)
            self.performance_stats["average_processing_time"] = total_time / self.performance_stats["total_files"]
        
        # 平均信頼度スコアの更新
        if metrics.confidence_score:
            successful_files = self.performance_stats["successful_files"]
            if successful_files > 1:
                total_confidence = (self.performance_stats["average_confidence_score"] * 
                                  (successful_files - 1) + 
                                  metrics.confidence_score)
                self.performance_stats["average_confidence_score"] = total_confidence / successful_files
            else:
                self.performance_stats["average_confidence_score"] = metrics.confidence_score
    
    def get_real_time_status(self) -> Dict[str, Any]:
        """リアルタイム処理状況を取得"""
        return {
            "current_time": datetime.now().isoformat(),
            "active_sessions": len(self.current_sessions),
            "processing_sessions": [
                {
                    "session_id": session_id,
                    "file_path": metrics.file_path,
                    "start_time": metrics.start_time.isoformat(),
                    "duration": (datetime.now() - metrics.start_time).total_seconds()
                }
                for session_id, metrics in self.current_sessions.items()
            ],
            "performance_stats": self.performance_stats
        }
    
    def get_hourly_report(self, hours: int = 24) -> Dict[str, Any]:
        """時間別レポートを取得"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.processing_history 
            if m.start_time > cutoff_time
        ]
        
        # 時間別集計
        hourly_stats = {}
        for metrics in recent_metrics:
            hour_key = metrics.start_time.strftime('%Y-%m-%d %H:00')
            if hour_key not in hourly_stats:
                hourly_stats[hour_key] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "avg_duration": 0.0,
                    "avg_confidence": 0.0
                }
            
            hourly_stats[hour_key]["total"] += 1
            if metrics.status == ProcessingStatus.SUCCESS:
                hourly_stats[hour_key]["success"] += 1
            elif metrics.status == ProcessingStatus.FAILED:
                hourly_stats[hour_key]["failed"] += 1
            
            if metrics.duration_seconds:
                hourly_stats[hour_key]["avg_duration"] = (
                    (hourly_stats[hour_key]["avg_duration"] * (hourly_stats[hour_key]["total"] - 1) +
                     metrics.duration_seconds) / hourly_stats[hour_key]["total"]
                )
            
            if metrics.confidence_score and metrics.status == ProcessingStatus.SUCCESS:
                success_count = hourly_stats[hour_key]["success"]
                if success_count > 1:
                    hourly_stats[hour_key]["avg_confidence"] = (
                        (hourly_stats[hour_key]["avg_confidence"] * (success_count - 1) +
                         metrics.confidence_score) / success_count
                    )
                else:
                    hourly_stats[hour_key]["avg_confidence"] = metrics.confidence_score
        
        return {
            "period_hours": hours,
            "total_processed": len(recent_metrics),
            "hourly_breakdown": hourly_stats,
            "summary": self._generate_report_summary(recent_metrics)
        }
    
    def _generate_report_summary(self, metrics_list: List[ProcessingMetrics]) -> Dict[str, Any]:
        """レポートサマリーを生成"""
        if not metrics_list:
            return {"message": "処理データがありません"}
        
        success_count = sum(1 for m in metrics_list if m.status == ProcessingStatus.SUCCESS)
        failed_count = sum(1 for m in metrics_list if m.status == ProcessingStatus.FAILED)
        
        durations = [m.duration_seconds for m in metrics_list if m.duration_seconds]
        confidences = [m.confidence_score for m in metrics_list if m.confidence_score]
        
        return {
            "success_rate": (success_count / len(metrics_list)) * 100,
            "failure_rate": (failed_count / len(metrics_list)) * 100,
            "avg_processing_time": sum(durations) / len(durations) if durations else 0,
            "min_processing_time": min(durations) if durations else 0,
            "max_processing_time": max(durations) if durations else 0,
            "avg_confidence_score": sum(confidences) / len(confidences) if confidences else 0,
            "min_confidence_score": min(confidences) if confidences else 0,
            "max_confidence_score": max(confidences) if confidences else 0
        }
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """パフォーマンス洞察を取得"""
        insights = []
        
        # 成功率の評価
        if self.performance_stats["total_files"] > 0:
            success_rate = (self.performance_stats["successful_files"] / 
                           self.performance_stats["total_files"]) * 100
            
            if success_rate < 70:
                insights.append("成功率が低下しています。設定やデータ品質を確認してください。")
            elif success_rate > 95:
                insights.append("処理が安定しています。")
        
        # 処理時間の評価
        avg_time = self.performance_stats["average_processing_time"]
        if avg_time > 60:
            insights.append("処理時間が長くなっています。パフォーマンス最適化を検討してください。")
        elif avg_time < 10:
            insights.append("処理が高速で実行されています。")
        
        # 信頼度スコアの評価
        avg_confidence = self.performance_stats["average_confidence_score"]
        if avg_confidence < 0.7:
            insights.append("信頼度スコアが低めです。OCR設定や画像品質を確認してください。")
        elif avg_confidence > 0.9:
            insights.append("高い信頼度で処理されています。")
        
        return {
            "insights": insights,
            "recommendations": self._generate_performance_recommendations(),
            "performance_stats": self.performance_stats
        }
    
    def _generate_performance_recommendations(self) -> List[str]:
        """パフォーマンス改善提案を生成"""
        recommendations = []
        
        total_files = self.performance_stats["total_files"]
        if total_files == 0:
            return ["まだ処理データがありません。"]
        
        success_rate = (self.performance_stats["successful_files"] / total_files) * 100
        
        if success_rate < 80:
            recommendations.append("成功率向上のため、入力データの品質改善を検討してください。")
        
        if self.performance_stats["average_processing_time"] > 30:
            recommendations.append("処理時間短縮のため、並列処理の活用を検討してください。")
        
        if self.performance_stats["average_confidence_score"] < 0.8:
            recommendations.append("信頼度向上のため、OCRパラメータの調整を検討してください。")
        
        return recommendations
    
    def export_metrics(self, file_path: str, hours: int = 24):
        """メトリクスをファイルにエクスポート"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "real_time_status": self.get_real_time_status(),
            "hourly_report": self.get_hourly_report(hours),
            "performance_insights": self.get_performance_insights(),
            "detailed_metrics": [
                asdict(m) for m in self.processing_history[-100:]  # 最新100件
            ]
        }
        
        # datetime オブジェクトを文字列に変換
        for metric in export_data["detailed_metrics"]:
            if metric["start_time"]:
                metric["start_time"] = metric["start_time"].isoformat()
            if metric["end_time"]:
                metric["end_time"] = metric["end_time"].isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"メトリクスをエクスポートしました: {file_path}")
    
    def clear_old_metrics(self, days: int = 7):
        """古いメトリクスをクリア"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        old_count = len(self.processing_history)
        self.processing_history = [
            m for m in self.processing_history 
            if m.start_time > cutoff_time
        ]
        
        cleared_count = old_count - len(self.processing_history)
        if cleared_count > 0:
            logger.info(f"{cleared_count}件の古いメトリクスをクリアしました")

# グローバル監視インスタンス
global_monitor = ProcessingMonitor()

class MonitoringContext:
    """監視コンテキストマネージャー"""
    
    def __init__(self, session_id: str, file_path: str = None, file_size: int = None):
        self.session_id = session_id
        self.file_path = file_path
        self.file_size = file_size
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        global_monitor.start_processing(self.session_id, self.file_path, self.file_size)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # 正常終了
            global_monitor.end_processing(self.session_id, ProcessingStatus.SUCCESS)
        else:
            # エラー終了
            error_message = str(exc_val) if exc_val else "Unknown error"
            global_monitor.end_processing(
                self.session_id, 
                ProcessingStatus.FAILED, 
                error_message=error_message
            )
        return False  # 例外を再発生させる

