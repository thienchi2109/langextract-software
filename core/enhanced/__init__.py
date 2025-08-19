"""
Enhanced ProcessingOrchestrator components for enterprise-grade document processing.

This package provides advanced features for the ProcessingOrchestrator including:
- Intelligent retry mechanisms with error classification
- Real-time resource monitoring and auto-scaling
- Multi-level progress reporting with performance metrics
- Enhanced cancellation with state preservation
- Configurable processing queue management

Usage:
    from core.enhanced import EnhancedConfig, EnhancedConfigManager
    from core.enhanced import RetryManager, ResourceMonitor
    from core.enhanced import ProgressTracker, CancellationManager, ProcessingQueue
    
    # Load configuration
    config = EnhancedConfigManager.load_config()
    
    # Create enhanced components
    retry_manager = RetryManager(config.retry_policy)
    resource_monitor = ResourceMonitor(config.resource_limits)
    progress_tracker = ProgressTracker()
    cancellation_manager = CancellationManager()
    processing_queue = ProcessingQueue(max_workers=config.queue_config.max_workers)
"""

# Core configuration
from .config import (
    EnhancedConfig,
    EnhancedConfigManager,
    ProgressConfig,
    CancellationConfig,
    QueueConfig
)

# Retry management
from .retry_manager import (
    RetryManager,
    RetryPolicy,
    RetryAttempt,
    ErrorType,
    ErrorClassifier
)

# Resource monitoring
from .resource_monitor import (
    ResourceMonitor,
    ResourceLimits,
    ResourceMetrics
)

# Progress tracking
from .progress_tracker import (
    ProgressTracker,
    ProcessingPhase,
    ProcessingRecord,
    DetailedProgress
)

# Cancellation management
from .cancellation_manager import (
    CancellationManager,
    ProcessingState,
    CleanupTask
)

# Processing queue
from .processing_queue import (
    ProcessingQueue,
    ProcessingJob,
    JobPriority,
    JobStatus,
    QueueStatistics,
    ComplexityEstimator
)

__all__ = [
    # Configuration
    'EnhancedConfig',
    'EnhancedConfigManager', 
    'ProgressConfig',
    'CancellationConfig',
    'QueueConfig',
    
    # Retry management
    'RetryManager',
    'RetryPolicy',
    'RetryAttempt',
    'ErrorType',
    'ErrorClassifier',
    
    # Resource monitoring
    'ResourceMonitor',
    'ResourceLimits',
    'ResourceMetrics',
    
    # Progress tracking
    'ProgressTracker',
    'ProcessingPhase',
    'ProcessingRecord',
    'DetailedProgress',
    
    # Cancellation management
    'CancellationManager',
    'ProcessingState',
    'CleanupTask',
    
    # Processing queue
    'ProcessingQueue',
    'ProcessingJob',
    'JobPriority',
    'JobStatus',
    'QueueStatistics',
    'ComplexityEstimator',
]

__version__ = "1.0.0" 