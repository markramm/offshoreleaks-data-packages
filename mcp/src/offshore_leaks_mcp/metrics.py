"""Performance monitoring and metrics collection for the offshore leaks server."""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for individual query execution."""

    query_type: str
    execution_time_ms: float
    result_count: int
    success: bool
    error_type: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    memory_usage_mb: Optional[float] = None
    parameters_count: int = 0


@dataclass
class SystemMetrics:
    """System-level performance metrics."""

    cpu_usage_percent: float
    memory_usage_mb: float
    memory_usage_percent: float
    disk_usage_mb: float
    network_connections: int
    active_queries: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DatabaseMetrics:
    """Database-specific metrics."""

    connection_pool_size: int
    active_connections: int
    connection_errors: int
    avg_query_time_ms: float
    slow_queries_count: int
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """Centralized metrics collection and analysis."""

    def __init__(self, retention_hours: int = 24, max_samples: int = 10000):
        """Initialize metrics collector."""
        self.retention_hours = retention_hours
        self.max_samples = max_samples

        # Query metrics storage
        self.query_metrics: deque = deque(maxlen=max_samples)
        self.system_metrics: deque = deque(maxlen=max_samples)
        self.database_metrics: deque = deque(maxlen=max_samples)

        # Real-time counters
        self.query_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.total_queries = 0
        self.total_errors = 0

        # Performance tracking
        self.query_times = defaultdict(list)
        self.slow_query_threshold_ms = 5000  # 5 seconds
        self.slow_queries = deque(maxlen=100)

        # Session tracking
        self.start_time = datetime.now()
        self.active_queries = set()

    def record_query_start(self, query_id: str, query_type: str) -> None:
        """Record the start of a query execution."""
        self.active_queries.add(query_id)
        logger.debug(f"Query started: {query_id} ({query_type})")

    def record_query_completion(self, metrics: QueryMetrics) -> None:
        """Record completion of a query with metrics."""
        # Remove from active queries if it was tracked
        query_id = f"{metrics.query_type}_{metrics.timestamp.isoformat()}"
        self.active_queries.discard(query_id)

        # Store metrics
        self.query_metrics.append(metrics)

        # Update counters
        self.query_counts[metrics.query_type] += 1
        self.total_queries += 1

        if not metrics.success:
            self.error_counts[metrics.error_type or "unknown"] += 1
            self.total_errors += 1

        # Track query times for analysis
        self.query_times[metrics.query_type].append(metrics.execution_time_ms)

        # Keep only recent query times (last 100 per type)
        if len(self.query_times[metrics.query_type]) > 100:
            self.query_times[metrics.query_type] = self.query_times[metrics.query_type][
                -100:
            ]

        # Track slow queries
        if metrics.execution_time_ms > self.slow_query_threshold_ms:
            self.slow_queries.append(metrics)

        logger.debug(
            f"Query completed: {metrics.query_type} in {metrics.execution_time_ms:.2f}ms"
        )

    def record_system_metrics(self, metrics: SystemMetrics) -> None:
        """Record system performance metrics."""
        self.system_metrics.append(metrics)
        self._cleanup_old_metrics()

    def record_database_metrics(self, metrics: DatabaseMetrics) -> None:
        """Record database performance metrics."""
        self.database_metrics.append(metrics)

    def get_query_statistics(self, time_window_hours: int = 1) -> dict[str, Any]:
        """Get query performance statistics for a time window."""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        # Filter recent queries
        recent_queries = [q for q in self.query_metrics if q.timestamp >= cutoff_time]

        if not recent_queries:
            return {"message": "No queries in the specified time window"}

        # Calculate statistics
        total_queries = len(recent_queries)
        successful_queries = sum(1 for q in recent_queries if q.success)
        failed_queries = total_queries - successful_queries

        query_types = defaultdict(list)
        for query in recent_queries:
            query_types[query.query_type].append(query.execution_time_ms)

        # Calculate averages and percentiles
        type_stats = {}
        for query_type, times in query_types.items():
            times.sort()
            count = len(times)
            type_stats[query_type] = {
                "count": count,
                "avg_time_ms": sum(times) / count,
                "min_time_ms": min(times),
                "max_time_ms": max(times),
                "p50_time_ms": times[count // 2] if count > 0 else 0,
                "p95_time_ms": times[int(count * 0.95)] if count > 0 else 0,
                "p99_time_ms": times[int(count * 0.99)] if count > 0 else 0,
            }

        return {
            "time_window_hours": time_window_hours,
            "summary": {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "failed_queries": failed_queries,
                "success_rate": (
                    (successful_queries / total_queries) * 100
                    if total_queries > 0
                    else 0
                ),
                "avg_execution_time_ms": sum(
                    q.execution_time_ms for q in recent_queries
                )
                / total_queries,
            },
            "by_query_type": type_stats,
            "slow_queries": len(
                [
                    q
                    for q in recent_queries
                    if q.execution_time_ms > self.slow_query_threshold_ms
                ]
            ),
        }

    def get_system_performance(self, time_window_hours: int = 1) -> dict[str, Any]:
        """Get system performance metrics."""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        recent_metrics = [m for m in self.system_metrics if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {"message": "No system metrics in the specified time window"}

        # Calculate averages
        cpu_values = [m.cpu_usage_percent for m in recent_metrics]
        memory_values = [m.memory_usage_mb for m in recent_metrics]
        memory_percent_values = [m.memory_usage_percent for m in recent_metrics]

        return {
            "time_window_hours": time_window_hours,
            "cpu": {
                "avg_usage_percent": sum(cpu_values) / len(cpu_values),
                "max_usage_percent": max(cpu_values),
                "min_usage_percent": min(cpu_values),
            },
            "memory": {
                "avg_usage_mb": sum(memory_values) / len(memory_values),
                "max_usage_mb": max(memory_values),
                "min_usage_mb": min(memory_values),
                "avg_usage_percent": sum(memory_percent_values)
                / len(memory_percent_values),
            },
            "active_queries": len(self.active_queries),
            "total_samples": len(recent_metrics),
        }

    def get_database_performance(self) -> dict[str, Any]:
        """Get database performance metrics."""
        if not self.database_metrics:
            return {"message": "No database metrics available"}

        latest = self.database_metrics[-1]

        return {
            "connection_pool": {
                "total_size": latest.connection_pool_size,
                "active_connections": latest.active_connections,
                "utilization_percent": (
                    (latest.active_connections / latest.connection_pool_size) * 100
                    if latest.connection_pool_size > 0
                    else 0
                ),
            },
            "performance": {
                "avg_query_time_ms": latest.avg_query_time_ms,
                "slow_queries_count": latest.slow_queries_count,
            },
            "errors": {
                "connection_errors": latest.connection_errors,
            },
            "timestamp": latest.timestamp.isoformat(),
        }

    def get_error_analysis(self, time_window_hours: int = 24) -> dict[str, Any]:
        """Get error analysis and patterns."""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        recent_errors = [
            q
            for q in self.query_metrics
            if q.timestamp >= cutoff_time and not q.success
        ]

        if not recent_errors:
            return {"message": "No errors in the specified time window"}

        # Group errors by type
        error_types = defaultdict(int)
        error_by_hour = defaultdict(int)

        for error in recent_errors:
            error_types[error.error_type or "unknown"] += 1
            hour_key = error.timestamp.strftime("%Y-%m-%d %H:00")
            error_by_hour[hour_key] += 1

        # Find error patterns
        most_common_error = max(error_types.items(), key=lambda x: x[1])

        return {
            "time_window_hours": time_window_hours,
            "summary": {
                "total_errors": len(recent_errors),
                "error_rate_percent": (len(recent_errors) / max(self.total_queries, 1))
                * 100,
                "most_common_error": most_common_error[0],
                "most_common_error_count": most_common_error[1],
            },
            "error_types": dict(error_types),
            "errors_by_hour": dict(error_by_hour),
        }

    def get_comprehensive_report(self) -> dict[str, Any]:
        """Get a comprehensive performance report."""
        uptime = datetime.now() - self.start_time

        return {
            "server_info": {
                "uptime_seconds": uptime.total_seconds(),
                "uptime_human": str(uptime),
                "start_time": self.start_time.isoformat(),
            },
            "query_statistics": self.get_query_statistics(time_window_hours=1),
            "system_performance": self.get_system_performance(time_window_hours=1),
            "database_performance": self.get_database_performance(),
            "error_analysis": self.get_error_analysis(time_window_hours=24),
            "slow_queries": {
                "count": len(self.slow_queries),
                "threshold_ms": self.slow_query_threshold_ms,
                "recent_slow_queries": [
                    {
                        "query_type": q.query_type,
                        "execution_time_ms": q.execution_time_ms,
                        "timestamp": q.timestamp.isoformat(),
                        "result_count": q.result_count,
                    }
                    for q in list(self.slow_queries)[-10:]  # Last 10 slow queries
                ],
            },
            "current_state": {
                "active_queries": len(self.active_queries),
                "total_queries_processed": self.total_queries,
                "total_errors": self.total_errors,
                "success_rate_percent": (
                    (self.total_queries - self.total_errors)
                    / max(self.total_queries, 1)
                )
                * 100,
            },
        }

    def _cleanup_old_metrics(self) -> None:
        """Remove old metrics beyond retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

        # Clean query metrics
        while self.query_metrics and self.query_metrics[0].timestamp < cutoff_time:
            self.query_metrics.popleft()

        # Clean system metrics
        while self.system_metrics and self.system_metrics[0].timestamp < cutoff_time:
            self.system_metrics.popleft()

        # Clean database metrics
        while (
            self.database_metrics and self.database_metrics[0].timestamp < cutoff_time
        ):
            self.database_metrics.popleft()

    def reset_metrics(self) -> None:
        """Reset all metrics (useful for testing or maintenance)."""
        self.query_metrics.clear()
        self.system_metrics.clear()
        self.database_metrics.clear()
        self.query_counts.clear()
        self.error_counts.clear()
        self.total_queries = 0
        self.total_errors = 0
        self.query_times.clear()
        self.slow_queries.clear()
        self.active_queries.clear()
        self.start_time = datetime.now()


class SystemMonitor:
    """System resource monitoring."""

    def __init__(self):
        """Initialize system monitor."""
        self.process = None
        self._setup_process_monitoring()

    def _setup_process_monitoring(self) -> None:
        """Setup process monitoring using psutil if available."""
        try:
            import os

            import psutil

            self.process = psutil.Process(os.getpid())
            self.psutil_available = True
        except ImportError:
            self.psutil_available = False
            logger.warning("psutil not available - system monitoring will be limited")

    def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        if self.psutil_available and self.process:
            try:
                # Get process-specific metrics
                memory_info = self.process.memory_info()
                cpu_percent = self.process.cpu_percent()

                # Get system-wide metrics
                import psutil

                system_memory = psutil.virtual_memory()

                # Count network connections (Neo4j connections)
                connections = len(
                    [
                        conn
                        for conn in self.process.connections()
                        if conn.laddr.port != 22  # Exclude SSH
                    ]
                )

                return SystemMetrics(
                    cpu_usage_percent=cpu_percent,
                    memory_usage_mb=memory_info.rss / 1024 / 1024,  # Convert to MB
                    memory_usage_percent=(memory_info.rss / system_memory.total) * 100,
                    disk_usage_mb=0,  # TODO: Implement disk usage monitoring
                    network_connections=connections,
                    active_queries=0,  # Will be updated by MetricsCollector
                )
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")

        # Fallback metrics when psutil is not available
        return SystemMetrics(
            cpu_usage_percent=0.0,
            memory_usage_mb=0.0,
            memory_usage_percent=0.0,
            disk_usage_mb=0.0,
            network_connections=0,
            active_queries=0,
        )


class PerformanceMonitor:
    """High-level performance monitoring coordinator."""

    def __init__(self, collection_interval: int = 60):
        """Initialize performance monitor."""
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor()
        self.collection_interval = collection_interval
        self._monitoring_task = None
        self._running = False

    async def start_monitoring(self) -> None:
        """Start background monitoring task."""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Performance monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                # Collect system metrics
                system_metrics = self.system_monitor.get_current_metrics()
                self.metrics_collector.record_system_metrics(system_metrics)

                # Sleep until next collection
                await asyncio.sleep(self.collection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.collection_interval)

    def record_query_metrics(self, metrics: QueryMetrics) -> None:
        """Record query performance metrics."""
        self.metrics_collector.record_query_completion(metrics)

    def get_performance_report(self) -> dict[str, Any]:
        """Get comprehensive performance report."""
        return self.metrics_collector.get_comprehensive_report()

    def get_query_statistics(self, time_window_hours: int = 1) -> dict[str, Any]:
        """Get query performance statistics."""
        return self.metrics_collector.get_query_statistics(time_window_hours)

    def get_system_performance(self, time_window_hours: int = 1) -> dict[str, Any]:
        """Get system performance metrics."""
        return self.metrics_collector.get_system_performance(time_window_hours)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Decorator for automatic query metrics collection
def monitor_query_performance(query_type: str):
    """Decorator to automatically collect query performance metrics."""

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_type = None
                result_count = 0

                try:
                    result = await func(*args, **kwargs)
                    if hasattr(result, "results") and hasattr(
                        result.results, "__len__"
                    ):
                        result_count = len(result.results)
                    elif hasattr(result, "__len__"):
                        result_count = len(result)
                    return result
                except Exception as e:
                    success = False
                    error_type = type(e).__name__
                    raise
                finally:
                    execution_time = (time.time() - start_time) * 1000  # Convert to ms

                    metrics = QueryMetrics(
                        query_type=query_type,
                        execution_time_ms=execution_time,
                        result_count=result_count,
                        success=success,
                        error_type=error_type,
                        parameters_count=len(kwargs),
                    )

                    performance_monitor.record_query_metrics(metrics)

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_type = None
                result_count = 0

                try:
                    result = func(*args, **kwargs)
                    if hasattr(result, "__len__"):
                        result_count = len(result)
                    return result
                except Exception as e:
                    success = False
                    error_type = type(e).__name__
                    raise
                finally:
                    execution_time = (time.time() - start_time) * 1000  # Convert to ms

                    metrics = QueryMetrics(
                        query_type=query_type,
                        execution_time_ms=execution_time,
                        result_count=result_count,
                        success=success,
                        error_type=error_type,
                        parameters_count=len(kwargs),
                    )

                    performance_monitor.record_query_metrics(metrics)

            return sync_wrapper

    return decorator
