"""
System resource monitoring and optimization for enhanced processing performance.

This module provides real-time monitoring of memory, CPU, and disk usage with
automatic scaling recommendations and resource management.
"""

import logging
import psutil
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """Configuration for resource usage limits and thresholds."""
    max_memory_percent: float = 80.0      # 80% of available RAM
    max_cpu_percent: float = 90.0         # 90% CPU usage
    thread_scale_factor: float = 1.5      # scaling multiplier for thread count
    memory_check_interval: float = 5.0    # monitoring interval in seconds
    disk_space_threshold_mb: float = 1000 # minimum free disk space in MB
    warning_threshold_percent: float = 70.0  # warn when approaching limits
    
    def __post_init__(self):
        """Validate resource limits configuration."""
        if not 0 < self.max_memory_percent <= 100:
            raise ValueError("max_memory_percent must be between 0 and 100")
        if not 0 < self.max_cpu_percent <= 100:
            raise ValueError("max_cpu_percent must be between 0 and 100")
        if self.thread_scale_factor < 1.0:
            raise ValueError("thread_scale_factor must be at least 1.0")


@dataclass
class ResourceMetrics:
    """Current system resource usage metrics."""
    memory_usage_mb: float
    memory_percent: float
    memory_available_mb: float
    cpu_usage_percent: float
    disk_free_mb: float
    disk_usage_percent: float
    thread_count: int
    timestamp: float
    
    def is_memory_critical(self, limits: ResourceLimits) -> bool:
        """Check if memory usage is critical."""
        return self.memory_percent > limits.max_memory_percent
        
    def is_memory_warning(self, limits: ResourceLimits) -> bool:
        """Check if memory usage is approaching warning threshold."""
        return self.memory_percent > limits.warning_threshold_percent
        
    def is_cpu_critical(self, limits: ResourceLimits) -> bool:
        """Check if CPU usage is critical."""
        return self.cpu_usage_percent > limits.max_cpu_percent
        
    def is_cpu_warning(self, limits: ResourceLimits) -> bool:
        """Check if CPU usage is approaching warning threshold."""
        return self.cpu_usage_percent > limits.warning_threshold_percent
        
    def is_disk_critical(self, limits: ResourceLimits) -> bool:
        """Check if available disk space is critical."""
        return self.disk_free_mb < limits.disk_space_threshold_mb
        
    def get_resource_status(self, limits: ResourceLimits) -> str:
        """Get overall resource status string."""
        statuses = []
        
        if self.is_memory_critical(limits):
            statuses.append("MEMORY_CRITICAL")
        elif self.is_memory_warning(limits):
            statuses.append("MEMORY_WARNING")
            
        if self.is_cpu_critical(limits):
            statuses.append("CPU_CRITICAL")
        elif self.is_cpu_warning(limits):
            statuses.append("CPU_WARNING")
            
        if self.is_disk_critical(limits):
            statuses.append("DISK_CRITICAL")
            
        return ", ".join(statuses) if statuses else "NORMAL"


class ResourceMonitor(QObject):
    """Monitors system resources and provides optimization recommendations."""
    
    resource_warning = Signal(str)          # warning message
    resource_critical = Signal(str)        # critical alert message
    metrics_updated = Signal(ResourceMetrics)
    scaling_recommendation = Signal(str, int)  # action, recommended_value
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        super().__init__()
        self.limits = limits or ResourceLimits()
        self.metrics_history: List[ResourceMetrics] = []
        self.monitoring_timer = QTimer()
        self.monitoring_timer.timeout.connect(self._check_resources)
        self.is_monitoring = False
        
        # Resource baselines for comparison
        self.baseline_memory_mb = None
        self.baseline_cpu_percent = None
        
        logger.info(f"ResourceMonitor initialized with limits: "
                   f"memory={self.limits.max_memory_percent}%, "
                   f"cpu={self.limits.max_cpu_percent}%")
    
    def start_monitoring(self):
        """Start periodic resource monitoring."""
        if self.is_monitoring:
            logger.warning("Resource monitoring already started")
            return
            
        # Set baseline metrics
        self._set_baseline_metrics()
        
        # Start monitoring timer
        interval_ms = int(self.limits.memory_check_interval * 1000)
        self.monitoring_timer.start(interval_ms)
        self.is_monitoring = True
        
        logger.info(f"Started resource monitoring (interval: {self.limits.memory_check_interval}s)")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        if not self.is_monitoring:
            return
            
        self.monitoring_timer.stop()
        self.is_monitoring = False
        logger.info("Stopped resource monitoring")
    
    def get_current_metrics(self) -> ResourceMetrics:
        """Get real-time system resource usage."""
        try:
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_usage_mb = (memory.total - memory.available) / (1024 * 1024)
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # CPU metrics (average over short interval)
            cpu_usage_percent = psutil.cpu_percent(interval=0.1)
            
            # Disk metrics for the current working directory
            disk = psutil.disk_usage('.')
            disk_free_mb = disk.free / (1024 * 1024)
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Thread count for current process
            current_process = psutil.Process()
            thread_count = current_process.num_threads()
            
            metrics = ResourceMetrics(
                memory_usage_mb=memory_usage_mb,
                memory_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                cpu_usage_percent=cpu_usage_percent,
                disk_free_mb=disk_free_mb,
                disk_usage_percent=disk_usage_percent,
                thread_count=thread_count,
                timestamp=time.time()
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting resource metrics: {e}")
            # Return safe default metrics
            return ResourceMetrics(
                memory_usage_mb=0,
                memory_percent=0,
                memory_available_mb=1000,
                cpu_usage_percent=0,
                disk_free_mb=1000,
                disk_usage_percent=0,
                thread_count=1,
                timestamp=time.time()
            )
    
    def _check_resources(self):
        """Internal method called by timer to check resources."""
        metrics = self.get_current_metrics()
        
        # Store metrics history (keep last 100 entries)
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)
        
        # Emit metrics update signal
        self.metrics_updated.emit(metrics)
        
        # Check for warnings and critical conditions
        self._check_warning_conditions(metrics)
        
        # Check for scaling recommendations
        self._check_scaling_recommendations(metrics)
        
        logger.debug(f"Resource check: Memory={metrics.memory_percent:.1f}%, "
                    f"CPU={metrics.cpu_usage_percent:.1f}%, "
                    f"Disk={metrics.disk_free_mb:.0f}MB free")
    
    def _check_warning_conditions(self, metrics: ResourceMetrics):
        """Check for warning and critical resource conditions."""
        status = metrics.get_resource_status(self.limits)
        
        if "CRITICAL" in status:
            if metrics.is_memory_critical(self.limits):
                message = (f"Memory usage critical: {metrics.memory_percent:.1f}% "
                          f"(limit: {self.limits.max_memory_percent}%)")
                self.resource_critical.emit(message)
                logger.warning(message)
                
            if metrics.is_cpu_critical(self.limits):
                message = (f"CPU usage critical: {metrics.cpu_usage_percent:.1f}% "
                          f"(limit: {self.limits.max_cpu_percent}%)")
                self.resource_critical.emit(message)
                logger.warning(message)
                
            if metrics.is_disk_critical(self.limits):
                message = (f"Disk space critical: {metrics.disk_free_mb:.0f}MB free "
                          f"(threshold: {self.limits.disk_space_threshold_mb}MB)")
                self.resource_critical.emit(message)
                logger.warning(message)
                
        elif "WARNING" in status:
            if metrics.is_memory_warning(self.limits):
                message = (f"Memory usage high: {metrics.memory_percent:.1f}% "
                          f"(warning at: {self.limits.warning_threshold_percent}%)")
                self.resource_warning.emit(message)
                
            if metrics.is_cpu_warning(self.limits):
                message = (f"CPU usage high: {metrics.cpu_usage_percent:.1f}% "
                          f"(warning at: {self.limits.warning_threshold_percent}%)")
                self.resource_warning.emit(message)
    
    def _check_scaling_recommendations(self, metrics: ResourceMetrics):
        """Check if scaling recommendations should be made."""
        if len(self.metrics_history) < 3:
            return  # Need some history for trend analysis
            
        # Check if we should scale down due to high resource usage
        if metrics.is_memory_critical(self.limits) or metrics.is_cpu_critical(self.limits):
            recommended_threads = max(1, int(metrics.thread_count * 0.7))  # Reduce by 30%
            self.scaling_recommendation.emit("scale_down", recommended_threads)
            logger.info(f"Recommending scale down to {recommended_threads} threads")
            
        # Check if we can scale up based on low resource usage and trend
        elif self._should_scale_up(metrics):
            recommended_threads = int(metrics.thread_count * self.limits.thread_scale_factor)
            self.scaling_recommendation.emit("scale_up", recommended_threads)
            logger.info(f"Recommending scale up to {recommended_threads} threads")
    
    def _should_scale_up(self, current_metrics: ResourceMetrics) -> bool:
        """Determine if we should recommend scaling up."""
        if len(self.metrics_history) < 5:
            return False
            
        # Check recent average resource usage
        recent_metrics = self.metrics_history[-5:]
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)
        
        # Scale up if both memory and CPU are consistently low
        memory_headroom = avg_memory < (self.limits.warning_threshold_percent * 0.8)  # 80% of warning
        cpu_headroom = avg_cpu < (self.limits.warning_threshold_percent * 0.8)
        
        return memory_headroom and cpu_headroom and current_metrics.thread_count < 8  # Max 8 threads
    
    def _set_baseline_metrics(self):
        """Set baseline metrics for comparison."""
        metrics = self.get_current_metrics()
        self.baseline_memory_mb = metrics.memory_usage_mb
        self.baseline_cpu_percent = metrics.cpu_usage_percent
        logger.info(f"Set resource baselines: Memory={self.baseline_memory_mb:.0f}MB, "
                   f"CPU={self.baseline_cpu_percent:.1f}%")
    
    def get_optimal_thread_count(self) -> int:
        """Calculate optimal thread count based on current system load."""
        if not self.metrics_history:
            return 2  # Safe default
            
        current_metrics = self.metrics_history[-1]
        
        # Base thread count on CPU cores and current load
        cpu_count = psutil.cpu_count(logical=True)
        
        # Conservative approach: start with CPU count
        optimal_threads = cpu_count
        
        # Adjust based on current resource usage
        if current_metrics.memory_percent > self.limits.warning_threshold_percent:
            optimal_threads = max(1, optimal_threads // 2)  # Reduce if memory constrained
            
        if current_metrics.cpu_usage_percent > self.limits.warning_threshold_percent:
            optimal_threads = max(1, int(optimal_threads * 0.7))  # Reduce if CPU constrained
            
        # Cap at reasonable maximum
        optimal_threads = min(optimal_threads, 8)
        
        logger.debug(f"Optimal thread count calculated: {optimal_threads} "
                    f"(CPU cores: {cpu_count}, Current usage: "
                    f"Memory={current_metrics.memory_percent:.1f}%, "
                    f"CPU={current_metrics.cpu_usage_percent:.1f}%)")
        
        return optimal_threads
    
    def should_scale_down(self) -> bool:
        """Determine if processing should be scaled down due to resource pressure."""
        if not self.metrics_history:
            return False
            
        current_metrics = self.metrics_history[-1]
        return (current_metrics.is_memory_critical(self.limits) or 
                current_metrics.is_cpu_critical(self.limits) or
                current_metrics.is_disk_critical(self.limits))
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get comprehensive resource usage summary."""
        if not self.metrics_history:
            return {"status": "no_data"}
            
        current = self.metrics_history[-1]
        
        # Calculate averages over recent history
        recent_count = min(10, len(self.metrics_history))
        recent_metrics = self.metrics_history[-recent_count:]
        
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)
        
        return {
            "current": {
                "memory_percent": current.memory_percent,
                "memory_usage_mb": current.memory_usage_mb,
                "memory_available_mb": current.memory_available_mb,
                "cpu_percent": current.cpu_usage_percent,
                "disk_free_mb": current.disk_free_mb,
                "thread_count": current.thread_count,
            },
            "averages": {
                "memory_percent": avg_memory,
                "cpu_percent": avg_cpu,
            },
            "status": current.get_resource_status(self.limits),
            "recommendations": {
                "optimal_thread_count": self.get_optimal_thread_count(),
                "should_scale_down": self.should_scale_down(),
            },
            "limits": {
                "max_memory_percent": self.limits.max_memory_percent,
                "max_cpu_percent": self.limits.max_cpu_percent,
                "warning_threshold": self.limits.warning_threshold_percent,
            }
        } 