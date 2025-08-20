"""
デバッグ・テストユーティリティ
"""
import structlog
import json
import os
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import traceback
from dataclasses import dataclass, asdict
from contextlib import contextmanager

logger = structlog.get_logger()

@dataclass
class DebugSession:
    """デバッグセッション情報"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    operations: List[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = None
    performance_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.operations is None:
            self.operations = []
        if self.errors is None:
            self.errors = []
        if self.performance_data is None:
            self.performance_data = {}

class DebugManager:
    """デバッグ管理クラス"""
    
    def __init__(self):
        self.debug_enabled = False
        self.current_session: Optional[DebugSession] = None
        self.debug_history: List[DebugSession] = []
        self.debug_output_dir = "debug_output"
        self._ensure_debug_dir()
    
    def _ensure_debug_dir(self):
        """デバッグ出力ディレクトリを作成"""
        if not os.path.exists(self.debug_output_dir):
            os.makedirs(self.debug_output_dir)
    
    def enable_debug(self, session_id: str = None):
        """デバッグモードを有効化"""
        if session_id is None:
            session_id = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.debug_enabled = True
        self.current_session = DebugSession(
            session_id=session_id,
            start_time=datetime.now()
        )
        
        logger.info(f"デバッグモード有効化: {session_id}")
    
    def disable_debug(self):
        """デバッグモードを無効化"""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.debug_history.append(self.current_session)
            
            # デバッグセッションをファイルに保存
            self._save_debug_session(self.current_session)
            
            logger.info(f"デバッグモード無効化: {self.current_session.session_id}")
            self.current_session = None
        
        self.debug_enabled = False
    
    def log_operation(self, operation_name: str, inputs: Dict[str, Any] = None, 
                     outputs: Dict[str, Any] = None, metadata: Dict[str, Any] = None):
        """操作をログに記録"""
        if not self.debug_enabled or not self.current_session:
            return
        
        operation_data = {
            "timestamp": datetime.now().isoformat(),
            "operation_name": operation_name,
            "inputs": inputs or {},
            "outputs": outputs or {},
            "metadata": metadata or {}
        }
        
        self.current_session.operations.append(operation_data)
        
        logger.debug(
            f"操作ログ: {operation_name}",
            session_id=self.current_session.session_id,
            operation_count=len(self.current_session.operations)
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """エラーをログに記録"""
        if not self.debug_enabled or not self.current_session:
            return
        
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "context": context or {}
        }
        
        self.current_session.errors.append(error_data)
        
        logger.error(
            f"エラーログ: {type(error).__name__}",
            session_id=self.current_session.session_id,
            error_count=len(self.current_session.errors)
        )
    
    def log_performance(self, operation_name: str, duration: float, 
                       additional_metrics: Dict[str, Any] = None):
        """パフォーマンスデータをログに記録"""
        if not self.debug_enabled or not self.current_session:
            return
        
        if operation_name not in self.current_session.performance_data:
            self.current_session.performance_data[operation_name] = []
        
        perf_data = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "additional_metrics": additional_metrics or {}
        }
        
        self.current_session.performance_data[operation_name].append(perf_data)
    
    def _save_debug_session(self, session: DebugSession):
        """デバッグセッションをファイルに保存"""
        filename = f"{session.session_id}.json"
        filepath = os.path.join(self.debug_output_dir, filename)
        
        # dataclassをdictに変換（datetimeの処理込み）
        session_dict = asdict(session)
        session_dict["start_time"] = session.start_time.isoformat()
        if session.end_time:
            session_dict["end_time"] = session.end_time.isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"デバッグセッションを保存: {filepath}")
    
    def get_debug_summary(self, session_id: str = None) -> Dict[str, Any]:
        """デバッグサマリーを取得"""
        target_session = None
        
        if session_id:
            target_session = next(
                (s for s in self.debug_history if s.session_id == session_id), 
                None
            )
        elif self.current_session:
            target_session = self.current_session
        elif self.debug_history:
            target_session = self.debug_history[-1]
        
        if not target_session:
            return {"message": "デバッグセッションが見つかりません"}
        
        duration = None
        if target_session.end_time:
            duration = (target_session.end_time - target_session.start_time).total_seconds()
        
        return {
            "session_id": target_session.session_id,
            "start_time": target_session.start_time.isoformat(),
            "end_time": target_session.end_time.isoformat() if target_session.end_time else None,
            "duration_seconds": duration,
            "operation_count": len(target_session.operations),
            "error_count": len(target_session.errors),
            "performance_operations": list(target_session.performance_data.keys()),
            "most_frequent_operation": self._get_most_frequent_operation(target_session),
            "average_operation_time": self._get_average_operation_time(target_session)
        }
    
    def _get_most_frequent_operation(self, session: DebugSession) -> Optional[str]:
        """最頻出操作を取得"""
        if not session.operations:
            return None
        
        operation_counts = {}
        for op in session.operations:
            name = op["operation_name"]
            operation_counts[name] = operation_counts.get(name, 0) + 1
        
        return max(operation_counts.items(), key=lambda x: x[1])[0]
    
    def _get_average_operation_time(self, session: DebugSession) -> Optional[float]:
        """平均操作時間を取得"""
        all_durations = []
        for perf_list in session.performance_data.values():
            all_durations.extend([p["duration"] for p in perf_list])
        
        return sum(all_durations) / len(all_durations) if all_durations else None
    
    def export_debug_report(self, output_file: str, session_id: str = None):
        """デバッグレポートをエクスポート"""
        summary = self.get_debug_summary(session_id)
        
        target_session = None
        if session_id:
            target_session = next(
                (s for s in self.debug_history if s.session_id == session_id), 
                None
            )
        elif self.current_session:
            target_session = self.current_session
        elif self.debug_history:
            target_session = self.debug_history[-1]
        
        if not target_session:
            logger.error("エクスポート対象のセッションが見つかりません")
            return
        
        report_data = {
            "export_timestamp": datetime.now().isoformat(),
            "summary": summary,
            "detailed_operations": target_session.operations,
            "errors": target_session.errors,
            "performance_data": target_session.performance_data,
            "recommendations": self._generate_debug_recommendations(target_session)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"デバッグレポートをエクスポート: {output_file}")
    
    def _generate_debug_recommendations(self, session: DebugSession) -> List[str]:
        """デバッグ推奨事項を生成"""
        recommendations = []
        
        if len(session.errors) > 0:
            recommendations.append(f"{len(session.errors)}件のエラーが発生しています。エラーハンドリングの改善を検討してください。")
        
        if session.performance_data:
            slow_operations = []
            for op_name, perf_list in session.performance_data.items():
                avg_duration = sum(p["duration"] for p in perf_list) / len(perf_list)
                if avg_duration > 10:  # 10秒以上
                    slow_operations.append(op_name)
            
            if slow_operations:
                recommendations.append(f"以下の操作が時間を要しています: {', '.join(slow_operations)}")
        
        return recommendations

# グローバルデバッグマネージャー
global_debug_manager = DebugManager()

@contextmanager
def debug_session(session_id: str = None):
    """デバッグセッションコンテキストマネージャー"""
    global_debug_manager.enable_debug(session_id)
    try:
        yield global_debug_manager
    finally:
        global_debug_manager.disable_debug()

def debug_operation(operation_name: str):
    """操作デバッグデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # 入力をログ
            inputs = {
                "args": str(args)[:1000],  # 長すぎる場合は切り詰め
                "kwargs": str(kwargs)[:1000]
            }
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 出力をログ
                outputs = {"result": str(result)[:1000]}
                
                global_debug_manager.log_operation(operation_name, inputs, outputs)
                global_debug_manager.log_performance(operation_name, duration)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                global_debug_manager.log_error(e, {"operation": operation_name, "inputs": inputs})
                global_debug_manager.log_performance(operation_name, duration, {"error": True})
                
                raise
        
        return wrapper
    return decorator

class TestDataGenerator:
    """テストデータ生成クラス"""
    
    @staticmethod
    def generate_sample_receipt_text() -> str:
        """サンプル領収書テキストを生成"""
        return """
        マクドナルド 渋谷店
        2024年1月15日 14:30
        レシート番号: 12345
        
        ハンバーガー 1 500 500
        フライドポテト 1 300 300
        コーラ 1 200 200
        
        小計: 1000
        消費税: 100
        合計: 1100円
        
        担当: 田中
        現金でお支払い
        """
    
    @staticmethod
    def generate_test_pdf_content() -> bytes:
        """テスト用PDFコンテンツを生成"""
        # 簡易的なPDFヘッダー
        return b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\nxref\n0 2\ntrailer\n<<\n/Size 2\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF'
    
    @staticmethod
    def generate_test_image_metadata() -> Dict[str, Any]:
        """テスト用画像メタデータを生成"""
        return {
            "width": 1920,
            "height": 1080,
            "format": "JPEG",
            "size_bytes": 256000,
            "quality": 95
        }

class PerformanceTester:
    """パフォーマンステストクラス"""
    
    @staticmethod
    def benchmark_function(func: Callable, iterations: int = 100, *args, **kwargs) -> Dict[str, float]:
        """関数のベンチマークを実行"""
        durations = []
        
        for _ in range(iterations):
            start_time = time.time()
            func(*args, **kwargs)
            duration = time.time() - start_time
            durations.append(duration)
        
        return {
            "min_duration": min(durations),
            "max_duration": max(durations),
            "avg_duration": sum(durations) / len(durations),
            "total_duration": sum(durations),
            "iterations": iterations
        }
    
    @staticmethod
    def stress_test(func: Callable, duration_seconds: int = 60, *args, **kwargs) -> Dict[str, Any]:
        """ストレステストを実行"""
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        iteration_count = 0
        errors = []
        durations = []
        
        while time.time() < end_time:
            iteration_start = time.time()
            try:
                func(*args, **kwargs)
                iteration_count += 1
            except Exception as e:
                errors.append(str(e))
            
            durations.append(time.time() - iteration_start)
        
        actual_duration = time.time() - start_time
        
        return {
            "test_duration": actual_duration,
            "iterations": iteration_count,
            "errors": len(errors),
            "error_rate": len(errors) / (iteration_count + len(errors)) if (iteration_count + len(errors)) > 0 else 0,
            "avg_iteration_time": sum(durations) / len(durations) if durations else 0,
            "iterations_per_second": iteration_count / actual_duration if actual_duration > 0 else 0
        }

