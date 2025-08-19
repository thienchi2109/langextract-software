"""
Advanced memory optimization and profiling for LangExtractor.

This module provides comprehensive memory management including garbage collection
optimization, memory leak detection, and intelligent memory usage patterns.
"""

import gc
import logging
import psutil
import sys
import time
import weakref
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Set
from threading import Lock
from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """Configuration for memory optimization."""
    gc_threshold_0: int = 1000     # Generation 0 GC threshold
    gc_threshold_1: int = 15       # Generation 1 GC threshold  
    gc_threshold_2: int = 15       # Generation 2 GC threshold
    gc_auto_collect: bool = True   # Enable automatic garbage collection
    max_memory_percent: float = 75.0  # Max memory usage before cleanup
    memory_check_interval: float = 30.0  # Memory check interval (seconds)
    enable_profiling: bool = False  # Enable detailed memory profiling
    leak_detection: bool = True    # Enable memory leak detection
    large_object_threshold: int = 1024 * 1024  # 1MB threshold for large objects


@dataclass
class MemoryMetrics:
    """Memory usage metrics and statistics."""
    timestamp: float
    memory_usage_mb: float
    memory_percent: float
    available_mb: float
    gc_generation_0: int
    gc_generation_1: int
    gc_generation_2: int
    gc_collections: int
    reference_count: int
    large_objects: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'timestamp': self.timestamp,
            'memory_usage_mb': self.memory_usage_mb,
            'memory_percent': self.memory_percent,
            'available_mb': self.available_mb,
            'gc_generation_0': self.gc_generation_0,
            'gc_generation_1': self.gc_generation_1,
            'gc_generation_2': self.gc_generation_2,
            'gc_collections': self.gc_collections,
            'reference_count': self.reference_count,
            'large_objects': self.large_objects
        }


class MemoryProfiler:
    """Advanced memory profiling and analysis."""
    
    def __init__(self):
        self.tracked_objects: Dict[str, weakref.WeakSet] = {}
        self.allocation_history: List[Dict[str, Any]] = []
        self.leak_candidates: Set[int] = set()
        self.profiling_enabled = False
        
    def track_object(self, obj: Any, category: str = "general"):
        """Track an object for memory profiling."""
        if not self.profiling_enabled:
            return
            
        if category not in self.tracked_objects:
            self.tracked_objects[category] = weakref.WeakSet()
        
        try:
            self.tracked_objects[category].add(obj)
            
            # Record allocation
            allocation = {
                'timestamp': time.time(),
                'category': category,
                'object_id': id(obj),
                'object_type': type(obj).__name__,
                'size': sys.getsizeof(obj)
            }
            self.allocation_history.append(allocation)
            
            # Keep history manageable
            if len(self.allocation_history) > 10000:
                self.allocation_history = self.allocation_history[-5000:]
                
        except (TypeError, ReferenceError):
            # Object not trackable
            pass
    
    def get_tracked_counts(self) -> Dict[str, int]:
        """Get count of tracked objects by category."""
        counts = {}
        for category, obj_set in self.tracked_objects.items():
            counts[category] = len(obj_set)
        return counts
    
    def detect_potential_leaks(self) -> List[Dict[str, Any]]:
        """Detect potential memory leaks."""
        if not self.profiling_enabled:
            return []
        
        current_time = time.time()
        leak_candidates = []
        
        # Look for objects that have been alive for a long time
        for allocation in self.allocation_history:
            age = current_time - allocation['timestamp']
            if age > 300:  # Objects alive for more than 5 minutes
                leak_candidates.append({
                    'object_id': allocation['object_id'],
                    'category': allocation['category'],
                    'type': allocation['object_type'],
                    'age_seconds': age,
                    'size': allocation['size']
                })
        
        return leak_candidates
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get comprehensive memory usage summary."""
        tracked_counts = self.get_tracked_counts()
        leak_candidates = self.detect_potential_leaks()
        
        return {
            'tracked_objects': tracked_counts,
            'total_tracked': sum(tracked_counts.values()),
            'allocation_history_size': len(self.allocation_history),
            'potential_leaks': len(leak_candidates),
            'profiling_enabled': self.profiling_enabled
        }


class MemoryOptimizer(QObject):
    """Advanced memory optimization and management."""
    
    memory_warning = Signal(str)
    memory_critical = Signal(str, float)  # message, memory_percent
    memory_optimized = Signal(str, float)  # optimization_action, memory_freed_mb
    gc_completed = Signal(int)  # objects_collected
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        super().__init__()
        self.config = config or MemoryConfig()
        self.profiler = MemoryProfiler()
        self.metrics_history: List[MemoryMetrics] = []
        self.optimization_lock = Lock()
        
        # Memory monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_memory_usage)
        
        # GC statistics tracking
        self.last_gc_stats = gc.get_stats()
        self.gc_count_before = gc.get_count()
        
        # Object pools for reuse
        self.string_pool: Dict[str, str] = {}
        self.buffer_pool: List[bytearray] = []
        
        self._setup_gc_optimization()
        logger.info("MemoryOptimizer initialized")
    
    def _setup_gc_optimization(self):
        """Configure garbage collection for optimal performance."""
        if self.config.gc_auto_collect:
            # Set optimized GC thresholds
            gc.set_threshold(
                self.config.gc_threshold_0,
                self.config.gc_threshold_1, 
                self.config.gc_threshold_2
            )
            logger.info(f"GC thresholds set: {gc.get_threshold()}")
        else:
            # Disable automatic GC for manual control
            gc.disable()
            logger.info("Automatic garbage collection disabled")
    
    def start_monitoring(self):
        """Start continuous memory monitoring."""
        interval_ms = int(self.config.memory_check_interval * 1000)
        self.monitor_timer.start(interval_ms)
        
        if self.config.enable_profiling:
            self.profiler.profiling_enabled = True
        
        logger.info(f"Memory monitoring started (interval: {self.config.memory_check_interval}s)")
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self.monitor_timer.stop()
        self.profiler.profiling_enabled = False
        logger.info("Memory monitoring stopped")
    
    def _check_memory_usage(self):
        """Check current memory usage and trigger optimization if needed."""
        try:
            metrics = self.get_memory_metrics()
            self.metrics_history.append(metrics)
            
            # Keep metrics history manageable
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-500:]
            
            # Check for memory pressure
            if metrics.memory_percent > self.config.max_memory_percent:
                self._handle_memory_pressure(metrics)
            elif metrics.memory_percent > self.config.max_memory_percent * 0.8:
                self.memory_warning.emit(
                    f"Memory usage high: {metrics.memory_percent:.1f}%"
                )
        
        except Exception as e:
            logger.error(f"Error during memory check: {e}")
    
    def _handle_memory_pressure(self, metrics: MemoryMetrics):
        """Handle high memory usage situations."""
        with self.optimization_lock:
            logger.warning(f"Memory pressure detected: {metrics.memory_percent:.1f}%")
            
            self.memory_critical.emit(
                f"Critical memory usage: {metrics.memory_percent:.1f}%",
                metrics.memory_percent
            )
            
            # Trigger aggressive optimization
            freed_mb = self.optimize_memory(aggressive=True)
            
            if freed_mb > 0:
                self.memory_optimized.emit(
                    "Emergency memory cleanup",
                    freed_mb
                )
            
            logger.info(f"Memory pressure handling completed, freed: {freed_mb:.1f}MB")
    
    def get_memory_metrics(self) -> MemoryMetrics:
        """Get current comprehensive memory metrics."""
        # System memory info
        memory = psutil.virtual_memory()
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # GC information
        gc_stats = gc.get_stats()
        gc_count = gc.get_count()
        
        # Reference counting
        ref_count = sys.getrefcount(None)  # Approximate reference count
        
        # Large object detection
        large_objects = self._count_large_objects()
        
        return MemoryMetrics(
            timestamp=time.time(),
            memory_usage_mb=process_memory.rss / (1024 * 1024),
            memory_percent=memory.percent,
            available_mb=memory.available / (1024 * 1024),
            gc_generation_0=gc_count[0],
            gc_generation_1=gc_count[1],
            gc_generation_2=gc_count[2],
            gc_collections=sum(stat['collections'] for stat in gc_stats),
            reference_count=ref_count,
            large_objects=large_objects
        )
    
    def _count_large_objects(self) -> int:
        """Count objects larger than threshold."""
        if not self.config.enable_profiling:
            return 0
        
        large_count = 0
        for obj in gc.get_objects():
            try:
                if sys.getsizeof(obj) > self.config.large_object_threshold:
                    large_count += 1
            except (TypeError, AttributeError):
                continue
        
        return large_count
    
    def optimize_memory(self, aggressive: bool = False) -> float:
        """Perform memory optimization and return freed memory in MB."""
        initial_memory = psutil.Process().memory_info().rss
        
        try:
            # Clear internal caches
            self._clear_caches()
            
            # Optimize string pool
            self._optimize_string_pool()
            
            # Clear buffer pool if needed
            if aggressive:
                self._clear_buffer_pool()
            
            # Force garbage collection
            collected = self._force_gc()
            
            # Calculate freed memory
            final_memory = psutil.Process().memory_info().rss
            freed_mb = (initial_memory - final_memory) / (1024 * 1024)
            
            if collected > 0:
                self.gc_completed.emit(collected)
            
            logger.info(f"Memory optimization completed: freed {freed_mb:.1f}MB, collected {collected} objects")
            return freed_mb
            
        except Exception as e:
            logger.error(f"Error during memory optimization: {e}")
            return 0.0
    
    def _clear_caches(self):
        """Clear internal caches to free memory."""
        # Clear metrics history if needed
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-50:]
        
        # Clear profiler history
        if self.profiler.allocation_history:
            self.profiler.allocation_history = self.profiler.allocation_history[-1000:]
    
    def _optimize_string_pool(self):
        """Optimize the string pool by removing unused strings."""
        if len(self.string_pool) > 1000:
            # Keep only recent strings
            self.string_pool.clear()
    
    def _clear_buffer_pool(self):
        """Clear the buffer pool to free memory."""
        self.buffer_pool.clear()
    
    def _force_gc(self) -> int:
        """Force garbage collection and return number of collected objects."""
        # Get initial object count
        initial_objects = len(gc.get_objects())
        
        # Force collection of all generations
        collected_0 = gc.collect(0)
        collected_1 = gc.collect(1)
        collected_2 = gc.collect(2)
        
        total_collected = collected_0 + collected_1 + collected_2
        
        # Get final object count
        final_objects = len(gc.get_objects())
        actual_collected = max(0, initial_objects - final_objects)
        
        logger.debug(f"GC completed: {total_collected} collected, {actual_collected} freed")
        return actual_collected
    
    def get_string_from_pool(self, text: str) -> str:
        """Get string from pool to reduce memory usage."""
        if text in self.string_pool:
            return self.string_pool[text]
        
        # Limit pool size
        if len(self.string_pool) > 10000:
            self._optimize_string_pool()
        
        self.string_pool[text] = text
        return text
    
    def get_buffer_from_pool(self, size: int) -> bytearray:
        """Get buffer from pool or create new one."""
        # Look for suitable buffer in pool
        for i, buffer in enumerate(self.buffer_pool):
            if len(buffer) >= size:
                # Remove from pool and return
                return self.buffer_pool.pop(i)
        
        # Create new buffer
        return bytearray(size)
    
    def return_buffer_to_pool(self, buffer: bytearray):
        """Return buffer to pool for reuse."""
        if len(self.buffer_pool) < 100:  # Limit pool size
            # Clear buffer content
            buffer[:] = b'\x00' * len(buffer)
            self.buffer_pool.append(buffer)
    
    def track_object(self, obj: Any, category: str = "general"):
        """Track object for memory profiling."""
        if self.config.enable_profiling:
            self.profiler.track_object(obj, category)
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive memory optimization report."""
        current_metrics = self.get_memory_metrics()
        profiler_summary = self.profiler.get_memory_summary()
        
        # Calculate trends
        if len(self.metrics_history) >= 2:
            recent_trend = (
                self.metrics_history[-1].memory_usage_mb - 
                self.metrics_history[-2].memory_usage_mb
            )
        else:
            recent_trend = 0.0
        
        return {
            'current_metrics': current_metrics.to_dict(),
            'profiler_summary': profiler_summary,
            'memory_trend_mb': recent_trend,
            'optimization_config': {
                'gc_thresholds': gc.get_threshold(),
                'gc_enabled': gc.isenabled(),
                'max_memory_percent': self.config.max_memory_percent,
                'profiling_enabled': self.config.enable_profiling
            },
            'pool_stats': {
                'string_pool_size': len(self.string_pool),
                'buffer_pool_size': len(self.buffer_pool)
            },
            'gc_stats': gc.get_stats()
        } 