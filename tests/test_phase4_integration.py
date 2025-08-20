"""
Phase 4: 運用最適化機能の統合テスト
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# receipt-processorディレクトリをPythonパスに追加
receipt_processor_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'receipt-processor')
sys.path.append(receipt_processor_path)

from error_handler import ErrorHandler, ErrorCategory, ErrorSeverity, handle_error
from monitoring import ProcessingMonitor, ProcessingStatus, MonitoringContext, global_monitor
from performance_optimizer import PerformanceOptimizer, global_optimizer, performance_optimized
from debug_utils import DebugManager, global_debug_manager, debug_operation, debug_session

class TestErrorHandling:
    """エラーハンドリング機能のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        self.error_handler = ErrorHandler()
    
    def test_handle_error_basic(self):
        """基本的なエラーハンドリングのテスト"""
        error = ValueError("テストエラー")
        result = self.error_handler.handle_error(
            error, 
            ErrorCategory.VALIDATION, 
            {"test_context": "value"}
        )
        
        assert "error_id" in result
        assert result["should_retry"] is not None
        assert result["fallback_action"] is not None
        assert result["user_message"] is not None
        assert "technical_details" in result
    
    def test_error_severity_levels(self):
        """エラー重要度レベルのテスト"""
        error = Exception("重大エラー")
        
        # 重大エラー
        result_critical = self.error_handler.handle_error(
            error, ErrorCategory.SYSTEM, severity=ErrorSeverity.CRITICAL
        )
        assert "重大なエラー" in result_critical["user_message"]
        
        # 軽微エラー
        result_low = self.error_handler.handle_error(
            error, ErrorCategory.VALIDATION, severity=ErrorSeverity.LOW
        )
        assert result_low["user_message"] is not None
    
    def test_recovery_strategies(self):
        """回復戦略のテスト"""
        network_error = ConnectionError("ネットワークエラー")
        result = self.error_handler.handle_error(
            network_error, ErrorCategory.NETWORK
        )
        
        assert result["retry_count"] >= 0
        assert result["retry_delay"] >= 0
        assert result["fallback_action"] is not None
    
    def test_error_statistics(self):
        """エラー統計のテスト"""
        for i in range(3):
            error = Exception(f"テストエラー{i}")
            self.error_handler.handle_error(error, ErrorCategory.VALIDATION)
        
        summary = self.error_handler.get_error_summary(hours=1)
        assert summary["total_errors"] >= 3
        assert "validation" in summary["category_breakdown"]
        assert summary["recommendations"] is not None

class TestProcessingMonitoring:
    """処理監視機能のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        self.monitor = ProcessingMonitor()
    
    def test_monitoring_session(self):
        """監視セッションのテスト"""
        session_id = "test_session"
        
        # 処理開始
        metrics = self.monitor.start_processing(session_id, "test.pdf", 1024)
        assert metrics.status == ProcessingStatus.PROCESSING
        assert metrics.file_path == "test.pdf"
        assert metrics.file_size == 1024
        
        # 処理終了
        final_metrics = self.monitor.end_processing(
            session_id, ProcessingStatus.SUCCESS, 0.95, 5
        )
        assert final_metrics.status == ProcessingStatus.SUCCESS
        assert final_metrics.confidence_score == 0.95
        assert final_metrics.extraction_count == 5
        assert final_metrics.duration_seconds is not None
    
    def test_monitoring_context_manager(self):
        """監視コンテキストマネージャーのテスト"""
        session_id = "context_test"
        
        # 正常終了
        with MonitoringContext(session_id, "test.pdf", 2048):
            pass  # 正常処理をシミュレート
        
        # エラー終了
        try:
            with MonitoringContext(session_id + "_error", "error.pdf"):
                raise ValueError("テストエラー")
        except ValueError:
            pass  # エラーを無視
        
        # 監視結果の確認
        status = self.monitor.get_real_time_status()
        assert status["active_sessions"] == 0  # 全て終了済み
    
    def test_hourly_report(self):
        """時間別レポートのテスト"""
        # テストデータの作成
        for i in range(5):
            session_id = f"hourly_test_{i}"
            self.monitor.start_processing(session_id)
            status = ProcessingStatus.SUCCESS if i % 2 == 0 else ProcessingStatus.FAILED
            self.monitor.end_processing(session_id, status, 0.8)
        
        report = self.monitor.get_hourly_report(hours=1)
        assert report["total_processed"] >= 5
        assert "summary" in report
        assert "hourly_breakdown" in report
    
    def test_performance_insights(self):
        """パフォーマンス洞察のテスト"""
        # 成功率の低いデータを作成
        for i in range(10):
            session_id = f"insight_test_{i}"
            self.monitor.start_processing(session_id)
            status = ProcessingStatus.FAILED  # 全て失敗
            self.monitor.end_processing(session_id, status)
        
        insights = self.monitor.get_performance_insights()
        assert "insights" in insights
        assert "recommendations" in insights
        assert len(insights["insights"]) > 0

class TestPerformanceOptimization:
    """パフォーマンス最適化機能のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        self.optimizer = PerformanceOptimizer()
    
    def test_system_metrics(self):
        """システムメトリクス取得のテスト"""
        metrics = self.optimizer.get_system_metrics()
        
        assert hasattr(metrics, 'cpu_usage')
        assert hasattr(metrics, 'memory_usage')
        assert hasattr(metrics, 'disk_usage')
        assert hasattr(metrics, 'optimization_level')
        assert 0 <= metrics.cpu_usage <= 100
        assert 0 <= metrics.memory_usage <= 100
    
    def test_optimization_levels(self):
        """最適化レベルのテスト"""
        levels = ["conservative", "balanced", "aggressive"]
        
        for level in levels:
            self.optimizer.set_optimization_level(level)
            assert self.optimizer.optimization_level == level
        
        # 無効なレベルのテスト
        with pytest.raises(ValueError):
            self.optimizer.set_optimization_level("invalid")
    
    def test_cache_functionality(self):
        """キャッシュ機能のテスト"""
        # キャッシュに保存
        self.optimizer.cache_result("test_key", "test_value", ttl=3600)
        
        # キャッシュから取得（ヒット）
        result = self.optimizer.get_cached_result("test_key")
        assert result == "test_value"
        assert self.optimizer.cache_hits == 1
        
        # 存在しないキーでの取得（ミス）
        result = self.optimizer.get_cached_result("nonexistent_key")
        assert result is None
        assert self.optimizer.cache_misses == 1
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_auto_optimization(self, mock_memory, mock_cpu):
        """自動最適化のテスト"""
        # 高CPU使用率をシミュレート
        mock_cpu.return_value = 95.0
        mock_memory.return_value.percent = 50.0
        
        result = self.optimizer.auto_optimize()
        assert "optimizations_applied" in result
        assert "metrics_after" in result
    
    def test_performance_optimized_decorator(self):
        """パフォーマンス最適化デコレータのテスト"""
        @performance_optimized()
        def test_function(x, y):
            return x + y
        
        result = test_function(2, 3)
        assert result == 5
    
    def test_batch_processing(self):
        """バッチ処理のテスト"""
        def simple_task():
            return "completed"
        
        tasks = [simple_task for _ in range(5)]
        results = self.optimizer.batch_process(tasks, batch_size=2)
        
        assert len(results) == 5
        assert all(result == "completed" for result in results)

class TestDebugUtils:
    """デバッグユーティリティのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        self.debug_manager = DebugManager()
    
    def test_debug_session_lifecycle(self):
        """デバッグセッションのライフサイクルテスト"""
        session_id = "debug_test_session"
        
        # デバッグ開始
        self.debug_manager.enable_debug(session_id)
        assert self.debug_manager.debug_enabled is True
        assert self.debug_manager.current_session is not None
        assert self.debug_manager.current_session.session_id == session_id
        
        # 操作ログ
        self.debug_manager.log_operation(
            "test_operation",
            {"input": "test"},
            {"output": "result"}
        )
        assert len(self.debug_manager.current_session.operations) == 1
        
        # エラーログ
        test_error = ValueError("テストエラー")
        self.debug_manager.log_error(test_error, {"context": "test"})
        assert len(self.debug_manager.current_session.errors) == 1
        
        # パフォーマンスログ
        self.debug_manager.log_performance("test_operation", 1.5)
        assert "test_operation" in self.debug_manager.current_session.performance_data
        
        # デバッグ終了
        self.debug_manager.disable_debug()
        assert self.debug_manager.debug_enabled is False
        assert len(self.debug_manager.debug_history) == 1
    
    def test_debug_session_context_manager(self):
        """デバッグセッションコンテキストマネージャーのテスト"""
        with debug_session("context_test") as debug_mgr:
            assert debug_mgr.debug_enabled is True
            debug_mgr.log_operation("context_operation")
        
        # コンテキスト終了後は自動的に無効化される
        assert global_debug_manager.debug_enabled is False
    
    def test_debug_operation_decorator(self):
        """デバッグ操作デコレータのテスト"""
        global_debug_manager.enable_debug("decorator_test")
        
        @debug_operation("test_decorated_function")
        def test_function(x, y):
            return x * y
        
        result = test_function(3, 4)
        assert result == 12
        
        # 操作がログされているか確認
        assert len(global_debug_manager.current_session.operations) >= 1
        
        global_debug_manager.disable_debug()
    
    def test_debug_summary(self):
        """デバッグサマリーのテスト"""
        session_id = "summary_test"
        self.debug_manager.enable_debug(session_id)
        
        # テストデータの追加
        self.debug_manager.log_operation("op1")
        self.debug_manager.log_operation("op2")
        self.debug_manager.log_operation("op1")  # 重複操作
        self.debug_manager.log_performance("op1", 2.0)
        
        self.debug_manager.disable_debug()
        
        summary = self.debug_manager.get_debug_summary(session_id)
        assert summary["session_id"] == session_id
        assert summary["operation_count"] == 3
        assert summary["most_frequent_operation"] == "op1"
        assert summary["average_operation_time"] == 2.0
    
    def test_debug_report_export(self):
        """デバッグレポートエクスポートのテスト"""
        session_id = "export_test"
        self.debug_manager.enable_debug(session_id)
        self.debug_manager.log_operation("export_operation")
        self.debug_manager.disable_debug()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_file = f.name
        
        try:
            self.debug_manager.export_debug_report(export_file, session_id)
            assert os.path.exists(export_file)
            
            # ファイル内容の確認
            with open(export_file, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
                assert "summary" in data
                assert "detailed_operations" in data
                assert "recommendations" in data
        finally:
            if os.path.exists(export_file):
                os.unlink(export_file)

class TestIntegratedFunctionality:
    """統合機能のテスト"""
    
    def test_error_monitoring_integration(self):
        """エラーハンドリングと監視の統合テスト"""
        session_id = "integration_test"
        
        # 監視開始
        global_monitor.start_processing(session_id)
        
        # エラー発生
        error = ConnectionError("ネットワーク接続エラー")
        error_result = handle_error(
            error, ErrorCategory.NETWORK, 
            {"session_id": session_id}
        )
        
        # 監視終了（エラー）
        global_monitor.end_processing(
            session_id, ProcessingStatus.FAILED, 
            error_message=str(error)
        )
        
        # 結果確認
        assert error_result["should_retry"] is not None
        
        status = global_monitor.get_real_time_status()
        assert status["active_sessions"] == 0
    
    def test_performance_debug_integration(self):
        """パフォーマンス最適化とデバッグの統合テスト"""
        with debug_session("perf_debug_test") as debug_mgr:
            # パフォーマンス最適化機能のテスト
            @performance_optimized()
            @debug_operation("optimized_function")
            def test_optimized_function(data):
                return len(data) * 2
            
            result = test_optimized_function("test_data")
            assert result == 18  # len("test_data") * 2 = 9 * 2
            
            # デバッグログが記録されているか確認
            assert len(debug_mgr.current_session.operations) >= 1
    
    def test_full_system_simulation(self):
        """フルシステムシミュレーションテスト"""
        session_id = "full_system_test"
        
        # デバッグセッション開始
        global_debug_manager.enable_debug(session_id)
        
        try:
            # 監視開始
            global_monitor.start_processing(session_id, "test.pdf", 2048)
            
            # パフォーマンス監視
            metrics = global_optimizer.get_system_metrics()
            assert metrics.optimization_level is not None
            
            # 成功処理のシミュレート
            global_monitor.end_processing(
                session_id, ProcessingStatus.SUCCESS, 
                confidence_score=0.95, extraction_count=3
            )
            
            # 結果確認
            status = global_monitor.get_real_time_status()
            insights = global_optimizer.get_optimization_recommendations()
            debug_summary = global_debug_manager.get_debug_summary()
            
            assert status is not None
            assert insights is not None
            assert debug_summary is not None
            
        finally:
            global_debug_manager.disable_debug()

