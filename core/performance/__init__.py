"""
Performance optimization module for LangExtractor.

This module provides advanced performance optimizations including:
- Memory management and garbage collection
- CPU utilization optimization  
- I/O operation optimization
- Batch processing improvements
- Caching mechanisms
- Resource pooling
"""

from .memory_optimizer import MemoryOptimizer, MemoryProfiler, MemoryConfig
from .batch_processor import BatchProcessor, BatchConfig, BatchJob
from .cache_manager import CacheManager, CacheConfig, CacheStats
from .resource_pool import ResourcePool, PoolConfig, ResourceManager
from .performance_monitor import PerformanceMonitor, PerformanceMetrics, BenchmarkResults

__all__ = [
    # Memory optimization
    'MemoryOptimizer',
    'MemoryProfiler', 
    'MemoryConfig',
    
    # Batch processing
    'BatchProcessor',
    'BatchConfig',
    'BatchJob',
    
    # Caching
    'CacheManager',
    'CacheConfig',
    'CacheStats',
    
    # Resource pooling
    'ResourcePool',
    'PoolConfig',
    'ResourceManager',
    
    # Performance monitoring
    'PerformanceMonitor',
    'PerformanceMetrics',
    'BenchmarkResults',
]

__version__ = "1.0.0" 