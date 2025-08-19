"""
Intelligent processing queue with batching, prioritization, and dynamic scaling.

This module provides advanced job queue management with complexity estimation,
priority handling, and automatic scaling based on system resources.
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from queue import PriorityQueue, Queue, Empty
from threading import Lock, Event
from typing import List, Dict, Any, Optional, Callable, Tuple
from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger(__name__)


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingJob:
    """Represents a processing job with metadata and priority."""
    job_id: str
    file_path: str
    priority: JobPriority = JobPriority.NORMAL
    estimated_complexity: float = 1.0    # relative processing complexity (1.0 = baseline)
    estimated_duration: float = 60.0     # estimated duration in seconds
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 2
    
    # Job execution data
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    worker_id: Optional[str] = None
    
    def __lt__(self, other):
        """Enable priority queue sorting (higher priority and older jobs first)."""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at
    
    @property
    def processing_time(self) -> float:
        """Get actual processing time if completed."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0
    
    @property
    def wait_time(self) -> float:
        """Get time spent waiting in queue."""
        start_time = self.started_at or time.time()
        return start_time - self.created_at
    
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries and self.status == JobStatus.FAILED


@dataclass
class QueueStatistics:
    """Statistics for queue performance monitoring."""
    total_jobs_processed: int = 0
    successful_jobs: int = 0
    failed_jobs: int = 0
    cancelled_jobs: int = 0
    average_processing_time: float = 0.0
    average_wait_time: float = 0.0
    throughput_jobs_per_hour: float = 0.0
    current_queue_size: int = 0
    active_workers: int = 0
    total_workers: int = 0


class ComplexityEstimator:
    """Estimates processing complexity for different file types and sizes."""
    
    # Base complexity factors by file extension
    COMPLEXITY_FACTORS = {
        '.pdf': 1.0,      # baseline
        '.docx': 0.8,     # easier than PDF
        '.doc': 0.9,      # slightly harder than DOCX
        '.xlsx': 0.7,     # spreadsheets are generally easier
        '.xls': 0.8,      # older Excel format
        '.txt': 0.3,      # plain text is easiest
        '.rtf': 0.6,      # rich text format
        '.odt': 0.8,      # OpenDocument text
        '.ods': 0.7,      # OpenDocument spreadsheet
    }
    
    # File size complexity multipliers (MB)
    SIZE_MULTIPLIERS = [
        (1, 1.0),         # < 1MB: normal
        (5, 1.2),         # 1-5MB: slightly harder
        (10, 1.5),        # 5-10MB: moderately harder
        (50, 2.0),        # 10-50MB: much harder
        (float('inf'), 3.0)  # > 50MB: very hard
    ]
    
    def estimate_complexity(self, file_path: str) -> float:
        """Estimate processing complexity for a file."""
        try:
            path = Path(file_path)
            
            # Get base complexity from file extension
            extension = path.suffix.lower()
            base_complexity = self.COMPLEXITY_FACTORS.get(extension, 1.2)  # Default slightly higher
            
            # Get file size in MB
            if path.exists():
                size_mb = path.stat().st_size / (1024 * 1024)
            else:
                size_mb = 5.0  # Default assumption
            
            # Apply size multiplier
            size_multiplier = 1.0
            for threshold, multiplier in self.SIZE_MULTIPLIERS:
                if size_mb <= threshold:
                    size_multiplier = multiplier
                    break
            
            complexity = base_complexity * size_multiplier
            
            logger.debug(f"Estimated complexity for {file_path}: {complexity:.2f} "
                        f"(base: {base_complexity}, size: {size_mb:.1f}MB, multiplier: {size_multiplier})")
            
            return complexity
            
        except Exception as e:
            logger.warning(f"Error estimating complexity for {file_path}: {e}")
            return 1.5  # Conservative default
    
    def estimate_duration(self, complexity: float, baseline_seconds: float = 60.0) -> float:
        """Estimate processing duration based on complexity."""
        return baseline_seconds * complexity


class ProcessingQueue(QObject):
    """Intelligent processing queue with dynamic scaling and prioritization."""
    
    job_queued = Signal(str)                    # job_id
    job_started = Signal(str, str)              # job_id, worker_id
    job_completed = Signal(str, bool, str)      # job_id, success, result_or_error
    queue_stats_updated = Signal(QueueStatistics)
    scaling_recommendation = Signal(str, int)   # action, new_worker_count
    batch_completed = Signal(str, int, int)     # batch_id, successful, total
    
    def __init__(self, max_workers: int = 3, min_workers: int = 1):
        super().__init__()
        
        # Queue configuration
        self.max_workers = max_workers
        self.min_workers = min_workers
        self.current_workers = min_workers
        
        # Job management
        self.job_queue = PriorityQueue()
        self.active_jobs: Dict[str, ProcessingJob] = {}
        self.completed_jobs: Dict[str, ProcessingJob] = {}
        self.job_lock = Lock()
        
        # Thread pool for workers
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ProcessingWorker")
        self.active_futures: Dict[str, Future] = {}
        
        # Batch management
        self.current_batch_id: Optional[str] = None
        self.batch_jobs: Dict[str, List[str]] = {}  # batch_id -> job_ids
        
        # Performance tracking
        self.complexity_estimator = ComplexityEstimator()
        self.statistics = QueueStatistics()
        self.performance_history: List[ProcessingJob] = []
        
        # Auto-scaling
        self.auto_scaling_enabled = True
        self.scaling_check_interval = 10.0  # seconds
        self.scaling_timer = QTimer()
        self.scaling_timer.timeout.connect(self._check_scaling_needs)
        
        # Statistics update timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_statistics)
        
        # Shutdown control
        self.shutdown_requested = Event()
        
        logger.info(f"ProcessingQueue initialized: {min_workers}-{max_workers} workers")
    
    def start_queue(self):
        """Start the processing queue and monitoring."""
        if self.auto_scaling_enabled:
            self.scaling_timer.start(int(self.scaling_check_interval * 1000))
        
        self.stats_timer.start(5000)  # Update stats every 5 seconds
        logger.info("Processing queue started")
    
    def stop_queue(self, wait_for_completion: bool = True):
        """Stop the processing queue gracefully."""
        logger.info("Stopping processing queue...")
        
        # Stop timers
        self.scaling_timer.stop()
        self.stats_timer.stop()
        
        # Signal shutdown
        self.shutdown_requested.set()
        
        if wait_for_completion:
            # Wait for active jobs to complete
            self._wait_for_active_jobs()
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=wait_for_completion)
        
        logger.info("Processing queue stopped")
    
    def add_job(self, file_path: str, priority: JobPriority = JobPriority.NORMAL,
                job_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a single job to the queue."""
        if job_id is None:
            job_id = f"job_{int(time.time() * 1000)}_{len(self.active_jobs)}"
        
        # Estimate complexity and duration
        complexity = self.complexity_estimator.estimate_complexity(file_path)
        duration = self.complexity_estimator.estimate_duration(complexity)
        
        # Create job
        job = ProcessingJob(
            job_id=job_id,
            file_path=file_path,
            priority=priority,
            estimated_complexity=complexity,
            estimated_duration=duration,
            metadata=metadata or {}
        )
        
        # Add to queue
        with self.job_lock:
            job.status = JobStatus.QUEUED
            self.job_queue.put(job)
            self.active_jobs[job_id] = job
        
        self.job_queued.emit(job_id)
        logger.debug(f"Added job to queue: {job_id} (priority: {priority.name}, complexity: {complexity:.2f})")
        
        return job_id
    
    def add_batch(self, file_paths: List[str], batch_id: Optional[str] = None,
                  priority: JobPriority = JobPriority.NORMAL,
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add multiple jobs as a batch."""
        if batch_id is None:
            batch_id = f"batch_{int(time.time() * 1000)}"
        
        job_ids = []
        for i, file_path in enumerate(file_paths):
            job_id = f"{batch_id}_job_{i}"
            job_metadata = (metadata or {}).copy()
            job_metadata.update({"batch_id": batch_id, "batch_index": i})
            
            actual_job_id = self.add_job(file_path, priority, job_id, job_metadata)
            job_ids.append(actual_job_id)
        
        self.batch_jobs[batch_id] = job_ids
        self.current_batch_id = batch_id
        
        logger.info(f"Added batch to queue: {batch_id} ({len(file_paths)} jobs)")
        return batch_id
    
    def process_next_job(self) -> bool:
        """Process the next job in the queue."""
        try:
            # Get next job from queue (non-blocking)
            job = self.job_queue.get_nowait()
            
            if self.shutdown_requested.is_set():
                # Put job back if shutting down
                self.job_queue.put(job)
                return False
            
            # Submit job to thread pool
            future = self.thread_pool.submit(self._execute_job, job)
            self.active_futures[job.job_id] = future
            
            # Update job status
            with self.job_lock:
                job.status = JobStatus.RUNNING
                job.started_at = time.time()
            
            self.job_started.emit(job.job_id, f"worker_{len(self.active_futures)}")
            
            return True
            
        except Empty:
            # No jobs in queue
            return False
        except Exception as e:
            logger.error(f"Error processing next job: {e}")
            return False
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a specific job."""
        with self.job_lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                
                if job.status == JobStatus.QUEUED:
                    # Remove from queue (this is tricky with PriorityQueue)
                    job.status = JobStatus.CANCELLED
                    job.completed_at = time.time()
                    return True
                elif job.status == JobStatus.RUNNING:
                    # Cancel running job
                    if job_id in self.active_futures:
                        future = self.active_futures[job_id]
                        cancelled = future.cancel()
                        if cancelled:
                            job.status = JobStatus.CANCELLED
                            job.completed_at = time.time()
                        return cancelled
        
        return False
    
    def cancel_batch(self, batch_id: str) -> int:
        """Cancel all jobs in a batch. Returns number of cancelled jobs."""
        if batch_id not in self.batch_jobs:
            return 0
        
        cancelled_count = 0
        for job_id in self.batch_jobs[batch_id]:
            if self.cancel_job(job_id):
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} jobs in batch {batch_id}")
        return cancelled_count
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.job_queue.qsize()
    
    def get_active_job_count(self) -> int:
        """Get number of currently running jobs."""
        return len([job for job in self.active_jobs.values() if job.status == JobStatus.RUNNING])
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get status of a specific job."""
        with self.job_lock:
            if job_id in self.active_jobs:
                return self.active_jobs[job_id].status
            elif job_id in self.completed_jobs:
                return self.completed_jobs[job_id].status
        return None
    
    def get_batch_progress(self, batch_id: str) -> Dict[str, Any]:
        """Get progress information for a batch."""
        if batch_id not in self.batch_jobs:
            return {"error": "Batch not found"}
        
        job_ids = self.batch_jobs[batch_id]
        status_counts = {status: 0 for status in JobStatus}
        total_jobs = len(job_ids)
        
        with self.job_lock:
            for job_id in job_ids:
                job = self.active_jobs.get(job_id) or self.completed_jobs.get(job_id)
                if job:
                    status_counts[job.status] += 1
        
        completed = status_counts[JobStatus.COMPLETED]
        failed = status_counts[JobStatus.FAILED]
        cancelled = status_counts[JobStatus.CANCELLED]
        finished = completed + failed + cancelled
        
        return {
            "batch_id": batch_id,
            "total_jobs": total_jobs,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "running": status_counts[JobStatus.RUNNING],
            "queued": status_counts[JobStatus.QUEUED],
            "progress_percentage": (finished / total_jobs * 100) if total_jobs > 0 else 0,
            "is_complete": finished == total_jobs
        }
    
    def _execute_job(self, job: ProcessingJob) -> Any:
        """Execute a single job (runs in worker thread)."""
        try:
            logger.debug(f"Executing job: {job.job_id}")
            
            # This is where the actual processing would happen
            # For now, we'll simulate processing based on complexity
            processing_time = job.estimated_duration * (0.8 + 0.4 * job.estimated_complexity)
            
            # Simulate processing with cancellation checks
            start_time = time.time()
            while time.time() - start_time < processing_time:
                if self.shutdown_requested.is_set():
                    raise InterruptedError("Processing cancelled due to shutdown")
                time.sleep(min(1.0, processing_time / 10))  # Check every second or 10% of duration
            
            # Simulate success/failure based on complexity
            import random
            success_probability = max(0.7, 1.0 - (job.estimated_complexity - 1.0) * 0.2)
            success = random.random() < success_probability
            
            if success:
                result = f"Processed {job.file_path} successfully"
                self._complete_job(job, True, result)
                return result
            else:
                error = f"Processing failed for {job.file_path} (simulated failure)"
                self._complete_job(job, False, error)
                raise Exception(error)
                
        except Exception as e:
            error_msg = str(e)
            self._complete_job(job, False, error_msg)
            raise
    
    def _complete_job(self, job: ProcessingJob, success: bool, result_or_error: str):
        """Mark job as completed and update statistics."""
        with self.job_lock:
            job.completed_at = time.time()
            job.status = JobStatus.COMPLETED if success else JobStatus.FAILED
            
            if success:
                job.result = result_or_error
            else:
                job.error = result_or_error
            
            # Move to completed jobs
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
            self.completed_jobs[job.job_id] = job
            
            # Remove from active futures
            if job.job_id in self.active_futures:
                del self.active_futures[job.job_id]
            
            # Add to performance history
            self.performance_history.append(job)
            if len(self.performance_history) > 100:  # Keep last 100 jobs
                self.performance_history.pop(0)
        
        # Emit completion signal
        self.job_completed.emit(job.job_id, success, result_or_error)
        
        # Check if batch is complete
        self._check_batch_completion(job)
        
        logger.debug(f"Completed job: {job.job_id} ({'success' if success else 'failed'})")
    
    def _check_batch_completion(self, completed_job: ProcessingJob):
        """Check if a batch is complete and emit signal if so."""
        batch_id = completed_job.metadata.get("batch_id")
        if not batch_id or batch_id not in self.batch_jobs:
            return
        
        progress = self.get_batch_progress(batch_id)
        if progress["is_complete"]:
            successful = progress["completed"]
            total = progress["total_jobs"]
            self.batch_completed.emit(batch_id, successful, total)
            logger.info(f"Batch completed: {batch_id} ({successful}/{total} successful)")
    
    def _wait_for_active_jobs(self, timeout: float = 30.0):
        """Wait for all active jobs to complete."""
        start_time = time.time()
        while self.active_futures and (time.time() - start_time) < timeout:
            time.sleep(0.5)
        
        if self.active_futures:
            logger.warning(f"Timeout waiting for {len(self.active_futures)} active jobs")
    
    def _check_scaling_needs(self):
        """Check if worker count should be scaled up or down."""
        if not self.auto_scaling_enabled:
            return
        
        queue_size = self.get_queue_size()
        active_jobs = self.get_active_job_count()
        current_workers = self.current_workers
        
        # Scale up if queue is building up
        if queue_size > current_workers * 2 and current_workers < self.max_workers:
            new_workers = min(self.max_workers, current_workers + 1)
            self._scale_workers(new_workers)
            self.scaling_recommendation.emit("scale_up", new_workers)
        
        # Scale down if workers are idle
        elif queue_size == 0 and active_jobs < current_workers // 2 and current_workers > self.min_workers:
            new_workers = max(self.min_workers, current_workers - 1)
            self._scale_workers(new_workers)
            self.scaling_recommendation.emit("scale_down", new_workers)
    
    def _scale_workers(self, new_worker_count: int):
        """Scale the worker count to the specified number."""
        if new_worker_count == self.current_workers:
            return
        
        logger.info(f"Scaling workers: {self.current_workers} -> {new_worker_count}")
        self.current_workers = new_worker_count
        
        # ThreadPoolExecutor doesn't support dynamic scaling, so we recreate it
        # In a production environment, you might want a more sophisticated approach
        if not self.active_futures:  # Only recreate if no active jobs
            self.thread_pool.shutdown(wait=False)
            self.thread_pool = ThreadPoolExecutor(
                max_workers=new_worker_count, 
                thread_name_prefix="ProcessingWorker"
            )
    
    def _update_statistics(self):
        """Update queue statistics."""
        with self.job_lock:
            completed_jobs = list(self.completed_jobs.values())
            active_jobs = list(self.active_jobs.values())
        
        # Calculate statistics
        total_processed = len(completed_jobs)
        successful = len([job for job in completed_jobs if job.status == JobStatus.COMPLETED])
        failed = len([job for job in completed_jobs if job.status == JobStatus.FAILED])
        cancelled = len([job for job in completed_jobs if job.status == JobStatus.CANCELLED])
        
        # Calculate averages from recent history
        recent_jobs = self.performance_history[-50:]  # Last 50 jobs
        if recent_jobs:
            avg_processing_time = sum(job.processing_time for job in recent_jobs) / len(recent_jobs)
            avg_wait_time = sum(job.wait_time for job in recent_jobs) / len(recent_jobs)
            
            # Calculate throughput (jobs per hour)
            if recent_jobs:
                time_span = recent_jobs[-1].completed_at - recent_jobs[0].created_at
                if time_span > 0:
                    throughput = len(recent_jobs) / (time_span / 3600)  # jobs per hour
                else:
                    throughput = 0.0
            else:
                throughput = 0.0
        else:
            avg_processing_time = 0.0
            avg_wait_time = 0.0
            throughput = 0.0
        
        # Update statistics
        self.statistics = QueueStatistics(
            total_jobs_processed=total_processed,
            successful_jobs=successful,
            failed_jobs=failed,
            cancelled_jobs=cancelled,
            average_processing_time=avg_processing_time,
            average_wait_time=avg_wait_time,
            throughput_jobs_per_hour=throughput,
            current_queue_size=self.get_queue_size(),
            active_workers=len(self.active_futures),
            total_workers=self.current_workers
        )
        
        self.queue_stats_updated.emit(self.statistics)
    
    def get_statistics(self) -> QueueStatistics:
        """Get current queue statistics."""
        return self.statistics 