"""
パフォーマンス最適化機能
"""
import structlog
import time
import threading
import queue
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import psutil
import gc
from functools import wraps
from dataclasses import dataclass

logger = structlog.get_logger()

@dataclass
class OptimizationMetrics:
    """最適化メトリクス"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    processing_queue_size: int
    active_threads: int
    optimization_level: str

class PerformanceOptimizer:
    """パフォーマンス最適化クラス"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(32, (psutil.cpu_count() or 1) + 4)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=min(4, psutil.cpu_count() or 1))
        self.task_queue = queue.Queue()
        self.optimization_level = "balanced"  # conservative, balanced, aggressive
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.performance_history = []
        
    def set_optimization_level(self, level: str):
        """最適化レベルを設定"""
        if level not in ["conservative", "balanced", "aggressive"]:
            raise ValueError("Invalid optimization level")
        
        self.optimization_level = level
        logger.info(f"最適化レベルを{level}に設定しました")
        
        # レベルに応じた設定調整
        if level == "conservative":
            self.max_workers = min(4, psutil.cpu_count() or 1)
        elif level == "balanced":
            self.max_workers = min(8, (psutil.cpu_count() or 1) * 2)
        elif level == "aggressive":
            self.max_workers = min(16, (psutil.cpu_count() or 1) * 4)
    
    def get_system_metrics(self) -> OptimizationMetrics:
        """システムメトリクスを取得"""
        return OptimizationMetrics(
            cpu_usage=psutil.cpu_percent(interval=1),
            memory_usage=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage('/').percent,
            network_io=sum(psutil.net_io_counters()[:2]),  # bytes_sent + bytes_recv
            processing_queue_size=self.task_queue.qsize(),
            active_threads=threading.active_count(),
            optimization_level=self.optimization_level
        )
    
    def monitor_performance(self) -> Dict[str, Any]:
        """パフォーマンスを監視"""
        metrics = self.get_system_metrics()
        self.performance_history.append({
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        })
        
        # 履歴を最新100件に制限
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # パフォーマンス警告の生成
        warnings = []
        if metrics.cpu_usage > 80:
            warnings.append("CPU使用率が高くなっています")
        if metrics.memory_usage > 85:
            warnings.append("メモリ使用率が高くなっています")
        if metrics.disk_usage > 90:
            warnings.append("ディスク使用率が高くなっています")
        
        return {
            "metrics": metrics,
            "warnings": warnings,
            "cache_stats": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
            }
        }
    
    def auto_optimize(self) -> Dict[str, Any]:
        """自動最適化を実行"""
        metrics = self.get_system_metrics()
        optimizations_applied = []
        
        # CPU使用率に基づく最適化
        if metrics.cpu_usage > 90:
            self._reduce_worker_count()
            optimizations_applied.append("ワーカー数を削減")
        elif metrics.cpu_usage < 30 and self.optimization_level == "aggressive":
            self._increase_worker_count()
            optimizations_applied.append("ワーカー数を増加")
        
        # メモリ使用率に基づく最適化
        if metrics.memory_usage > 85:
            self._clear_cache()
            gc.collect()
            optimizations_applied.append("キャッシュクリアとガベージコレクション実行")
        
        # キューサイズに基づく最適化
        if metrics.processing_queue_size > 100:
            self._process_queue_batch()
            optimizations_applied.append("キューのバッチ処理実行")
        
        logger.info(f"自動最適化完了: {optimizations_applied}")
        
        return {
            "optimizations_applied": optimizations_applied,
            "metrics_after": self.get_system_metrics()
        }
    
    def _reduce_worker_count(self):
        """ワーカー数を削減"""
        new_count = max(2, self.max_workers - 2)
        if new_count != self.max_workers:
            self.max_workers = new_count
            # 新しいThreadPoolExecutorを作成
            self.thread_pool.shutdown(wait=False)
            self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
    
    def _increase_worker_count(self):
        """ワーカー数を増加"""
        max_allowed = psutil.cpu_count() * 4
        new_count = min(max_allowed, self.max_workers + 2)
        if new_count != self.max_workers:
            self.max_workers = new_count
            # 新しいThreadPoolExecutorを作成
            self.thread_pool.shutdown(wait=False)
            self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
    
    def _clear_cache(self):
        """キャッシュをクリア"""
        old_size = len(self.cache)
        self.cache.clear()
        logger.info(f"{old_size}件のキャッシュエントリをクリアしました")
    
    def _process_queue_batch(self):
        """キューのバッチ処理"""
        batch_size = min(50, self.task_queue.qsize())
        tasks = []
        
        for _ in range(batch_size):
            try:
                task = self.task_queue.get_nowait()
                tasks.append(task)
            except queue.Empty:
                break
        
        if tasks:
            logger.info(f"{len(tasks)}件のタスクをバッチ処理します")
    
    def cache_result(self, key: str, value: Any, ttl: int = 3600):
        """結果をキャッシュ"""
        expiry = time.time() + ttl
        self.cache[key] = {
            "value": value,
            "expiry": expiry
        }
    
    def get_cached_result(self, key: str) -> Optional[Any]:
        """キャッシュから結果を取得"""
        if key in self.cache:
            cached_item = self.cache[key]
            if time.time() < cached_item["expiry"]:
                self.cache_hits += 1
                return cached_item["value"]
            else:
                # 期限切れのエントリを削除
                del self.cache[key]
        
        self.cache_misses += 1
        return None
    
    def process_with_optimization(self, func: Callable, *args, **kwargs):
        """最適化を適用して関数を実行"""
        # キャッシュキーの生成
        cache_key = self._generate_cache_key(func.__name__, args, kwargs)
        
        # キャッシュヒットの確認
        cached_result = self.get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # システムメトリクスに基づく実行方法の決定
        metrics = self.get_system_metrics()
        
        if metrics.cpu_usage > 80:
            # 高CPU使用率時は同期実行
            result = func(*args, **kwargs)
        else:
            # 通常時は非同期実行
            future = self.thread_pool.submit(func, *args, **kwargs)
            result = future.result()
        
        # 結果をキャッシュ
        self.cache_result(cache_key, result)
        
        return result
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """キャッシュキーを生成"""
        import hashlib
        key_data = f"{func_name}_{str(args)}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def batch_process(self, tasks: List[Callable], batch_size: int = 10) -> List[Any]:
        """バッチ処理を実行"""
        results = []
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            
            # バッチ処理の実行
            futures = [self.thread_pool.submit(task) for task in batch]
            batch_results = [future.result() for future in futures]
            results.extend(batch_results)
            
            # システム負荷の確認
            metrics = self.get_system_metrics()
            if metrics.cpu_usage > 85 or metrics.memory_usage > 85:
                logger.warning("システム負荷が高いため、処理を一時停止します")
                time.sleep(2)
        
        return results
    
    def get_optimization_recommendations(self) -> List[str]:
        """最適化提案を取得"""
        recommendations = []
        metrics = self.get_system_metrics()
        
        if metrics.cpu_usage > 80:
            recommendations.append("CPU使用率が高いため、並列度を下げることを推奨します")
        
        if metrics.memory_usage > 85:
            recommendations.append("メモリ使用率が高いため、キャッシュサイズを小さくすることを推奨します")
        
        if self.cache_hits / (self.cache_hits + self.cache_misses) < 0.3:
            recommendations.append("キャッシュヒット率が低いため、キャッシュ戦略の見直しを推奨します")
        
        if metrics.processing_queue_size > 50:
            recommendations.append("処理キューが溜まっているため、ワーカー数の増加を推奨します")
        
        return recommendations
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        self._clear_cache()
        logger.info("パフォーマンス最適化リソースをクリーンアップしました")

# グローバル最適化インスタンス
global_optimizer = PerformanceOptimizer()

def performance_optimized(cache_ttl: int = 3600):
    """パフォーマンス最適化デコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return global_optimizer.process_with_optimization(func, *args, **kwargs)
        return wrapper
    return decorator

def timed_execution(func):
    """実行時間計測デコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} 実行時間: {execution_time:.2f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} エラー（実行時間: {execution_time:.2f}秒）: {e}")
            raise
    return wrapper

