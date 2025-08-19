"""
Multi-level progress tracking with performance analytics for enhanced processing.

This module provides detailed progress reporting across multiple levels (batch, file, phase)
with real-time performance metrics and ETA calculations.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger(__name__)


class ProcessingPhase(Enum):
    """Enumeration of processing phases with weights."""
    INGESTION = ("Ingestion", 0.2, "Reading document content")
    OCR = ("OCR", 0.3, "Optical character recognition") 
    EXTRACTION = ("Extraction", 0.4, "AI data extraction")
    VALIDATION = ("Validation", 0.1, "Data validation and cleanup")
    
    def __init__(self, name: str, weight: float, description: str):
        self.phase_name = name
        self.weight = weight
        self.description = description


@dataclass
class ProcessingRecord:
    """Record of a completed processing operation."""
    file_path: str
    phase: ProcessingPhase
    start_time: float
    end_time: float
    processing_time: float
    success: bool
    field_count: int = 0
    confidence_scores: List[float] = field(default_factory=list)
    error_message: Optional[str] = None
    
    @property
    def avg_confidence(self) -> float:
        """Get average confidence score."""
        return sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0.0


@dataclass
class DetailedProgress:
    """Comprehensive progress information with performance metrics."""
    
    # Multi-level progress tracking
    batch_progress: float              # 0.0 - 1.0 (overall batch completion)
    current_file_index: int           # index of file being processed
    total_files: int                  # total number of files in batch
    current_file_progress: float      # 0.0 - 1.0 (current file completion)
    current_phase: ProcessingPhase    # current processing phase
    current_file_name: str            # name of current file
    
    # Performance metrics  
    throughput_docs_per_min: float    # documents processed per minute
    throughput_fields_per_sec: float  # fields extracted per second
    avg_processing_time: float        # average time per document (seconds)
    
    # ETA calculations
    eta_current_file_seconds: float   # estimated completion time for current file
    eta_batch_completion_seconds: float # estimated completion time for entire batch
    
    # Resource usage (from ResourceMonitor integration)
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    # Quality metrics
    success_rate: float = 1.0         # percentage of successful extractions
    avg_confidence_score: float = 0.0 # average confidence of extractions
    
    # Timing information
    elapsed_time: float = 0.0         # total elapsed time
    start_time: float = 0.0           # batch start time
    
    def get_progress_percentage(self) -> float:
        """Get overall progress as percentage (0-100)."""
        return self.batch_progress * 100.0
    
    def get_eta_formatted(self) -> str:
        """Get formatted ETA string."""
        if self.eta_batch_completion_seconds <= 0:
            return "Calculating..."
            
        eta_minutes = int(self.eta_batch_completion_seconds // 60)
        eta_seconds = int(self.eta_batch_completion_seconds % 60)
        
        if eta_minutes > 0:
            return f"{eta_minutes}m {eta_seconds}s"
        else:
            return f"{eta_seconds}s"
    
    def get_throughput_summary(self) -> str:
        """Get formatted throughput summary."""
        return f"{self.throughput_docs_per_min:.1f} docs/min, {self.throughput_fields_per_sec:.1f} fields/sec"


class ProgressTracker(QObject):
    """Tracks detailed processing progress with performance analytics."""
    
    detailed_progress_updated = Signal(DetailedProgress)
    phase_changed = Signal(str, str)          # phase_name, file_name
    performance_alert = Signal(str)           # performance degradation alerts
    milestone_reached = Signal(str, float)    # milestone_name, progress_value
    
    def __init__(self):
        super().__init__()
        
        # Progress state
        self.start_time = 0.0
        self.current_batch_size = 0
        self.current_file_index = 0
        self.current_phase = ProcessingPhase.INGESTION
        self.current_file_name = ""
        self.current_file_progress = 0.0
        
        # Performance tracking
        self.processing_history: List[ProcessingRecord] = []
        self.phase_timings: Dict[ProcessingPhase, List[float]] = {
            phase: [] for phase in ProcessingPhase
        }
        
        # Performance baselines and thresholds
        self.baseline_docs_per_min = 0.0
        self.performance_degradation_threshold = 0.5  # 50% slower than baseline
        
        # Update timer for regular progress emissions
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._emit_progress_update)
        self.progress_update_interval = 500  # 500ms default
        
        # Milestones for progress notifications
        self.milestones = [0.25, 0.5, 0.75, 0.9]  # 25%, 50%, 75%, 90%
        self.reached_milestones = set()
        
        logger.info("ProgressTracker initialized")
    
    def start_batch_tracking(self, total_files: int, file_names: List[str]):
        """Start tracking a new batch of files."""
        self.start_time = time.time()
        self.current_batch_size = total_files
        self.current_file_index = 0
        self.current_file_progress = 0.0
        self.current_phase = ProcessingPhase.INGESTION
        self.current_file_name = file_names[0] if file_names else ""
        
        # Reset tracking state
        self.processing_history.clear()
        self.reached_milestones.clear()
        
        # Start progress updates
        self.progress_timer.start(self.progress_update_interval)
        
        logger.info(f"Started batch tracking: {total_files} files")
    
    def stop_batch_tracking(self):
        """Stop tracking the current batch."""
        self.progress_timer.stop()
        
        # Calculate final statistics
        total_time = time.time() - self.start_time
        successful_files = sum(1 for record in self.processing_history if record.success)
        
        logger.info(f"Completed batch tracking: {successful_files}/{self.current_batch_size} files "
                   f"in {total_time:.1f}s")
    
    def update_file_progress(self, file_index: int, file_name: str, 
                           phase: ProcessingPhase, progress: float,
                           metrics: Optional[Dict[str, Any]] = None):
        """Update progress for specific file and processing phase."""
        # Update current state
        self.current_file_index = file_index
        self.current_file_name = file_name
        old_phase = self.current_phase
        self.current_phase = phase
        self.current_file_progress = max(0.0, min(1.0, progress))
        
        # Emit phase change signal if phase changed
        if old_phase != phase:
            self.phase_changed.emit(phase.phase_name, file_name)
            logger.debug(f"Phase changed to {phase.phase_name} for {file_name}")
        
        # Update performance metrics if provided
        if metrics:
            self._update_performance_metrics(metrics)
        
        # Check for milestones
        self._check_milestones()
    
    def record_file_completion(self, file_path: str, phase: ProcessingPhase,
                             processing_time: float, success: bool,
                             field_count: int = 0, confidence_scores: List[float] = None,
                             error_message: Optional[str] = None):
        """Record completion of a file processing phase."""
        record = ProcessingRecord(
            file_path=file_path,
            phase=phase,
            start_time=time.time() - processing_time,
            end_time=time.time(),
            processing_time=processing_time,
            success=success,
            field_count=field_count,
            confidence_scores=confidence_scores or [],
            error_message=error_message
        )
        
        self.processing_history.append(record)
        self.phase_timings[phase].append(processing_time)
        
        # Check for performance degradation
        self._check_performance_degradation()
        
        logger.debug(f"Recorded {phase.phase_name} completion: {file_path} "
                    f"({'success' if success else 'failed'}) in {processing_time:.2f}s")
    
    def calculate_advanced_eta(self) -> Tuple[float, float]:
        """Calculate ETA using weighted averages and trend analysis."""
        if not self.processing_history or self.current_batch_size == 0:
            return 0.0, 0.0
        
        # Calculate remaining work
        completed_files = len(set(record.file_path for record in self.processing_history 
                                if record.success))
        remaining_files = self.current_batch_size - completed_files
        
        if remaining_files <= 0:
            return 0.0, 0.0
        
        # Calculate average time per file using recent history (weighted)
        recent_records = self.processing_history[-20:]  # Last 20 operations
        if not recent_records:
            return 60.0, remaining_files * 60.0  # Default estimate
        
        # Group by file and calculate total time per file
        file_times = {}
        for record in recent_records:
            if record.file_path not in file_times:
                file_times[record.file_path] = 0.0
            file_times[record.file_path] += record.processing_time
        
        if not file_times:
            return 60.0, remaining_files * 60.0
        
        # Calculate weighted average (more recent files have higher weight)
        avg_time_per_file = sum(file_times.values()) / len(file_times)
        
        # Adjust for current file progress
        current_file_eta = avg_time_per_file * (1.0 - self.current_file_progress)
        
        # Calculate batch ETA
        batch_eta = current_file_eta + (remaining_files - 1) * avg_time_per_file
        
        return current_file_eta, batch_eta
    
    def calculate_batch_progress(self) -> float:
        """Calculate overall batch progress using phase weights."""
        if self.current_batch_size == 0:
            return 0.0
        
        # Calculate completed files progress
        completed_files = len(set(record.file_path for record in self.processing_history 
                                if record.success))
        completed_progress = completed_files / self.current_batch_size
        
        # Calculate current file progress weighted by phase
        current_file_weighted_progress = 0.0
        for phase in ProcessingPhase:
            if phase.value <= self.current_phase.value:
                if phase == self.current_phase:
                    current_file_weighted_progress += phase.weight * self.current_file_progress
                else:
                    current_file_weighted_progress += phase.weight
        
        # Combine completed files and current file progress
        current_file_contribution = current_file_weighted_progress / self.current_batch_size
        total_progress = completed_progress + current_file_contribution
        
        return min(1.0, total_progress)
    
    def calculate_performance_metrics(self) -> Dict[str, float]:
        """Calculate current performance metrics."""
        if not self.processing_history:
            return {
                "throughput_docs_per_min": 0.0,
                "throughput_fields_per_sec": 0.0,
                "avg_processing_time": 0.0,
                "success_rate": 1.0,
                "avg_confidence_score": 0.0
            }
        
        elapsed_time = time.time() - self.start_time
        
        # Calculate throughput
        completed_files = len(set(record.file_path for record in self.processing_history 
                                if record.success))
        docs_per_min = (completed_files / max(elapsed_time / 60, 0.1))
        
        # Calculate fields per second
        total_fields = sum(record.field_count for record in self.processing_history)
        fields_per_sec = total_fields / max(elapsed_time, 0.1)
        
        # Calculate average processing time
        processing_times = [record.processing_time for record in self.processing_history]
        avg_processing_time = sum(processing_times) / len(processing_times)
        
        # Calculate success rate
        total_operations = len(self.processing_history)
        successful_operations = sum(1 for record in self.processing_history if record.success)
        success_rate = successful_operations / total_operations
        
        # Calculate average confidence
        all_confidences = []
        for record in self.processing_history:
            all_confidences.extend(record.confidence_scores)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        return {
            "throughput_docs_per_min": docs_per_min,
            "throughput_fields_per_sec": fields_per_sec,
            "avg_processing_time": avg_processing_time,
            "success_rate": success_rate,
            "avg_confidence_score": avg_confidence
        }
    
    def _emit_progress_update(self):
        """Emit detailed progress update signal."""
        # Calculate current progress and metrics
        batch_progress = self.calculate_batch_progress()
        eta_current, eta_batch = self.calculate_advanced_eta()
        performance_metrics = self.calculate_performance_metrics()
        
        # Create detailed progress object
        progress = DetailedProgress(
            batch_progress=batch_progress,
            current_file_index=self.current_file_index,
            total_files=self.current_batch_size,
            current_file_progress=self.current_file_progress,
            current_phase=self.current_phase,
            current_file_name=self.current_file_name,
            throughput_docs_per_min=performance_metrics["throughput_docs_per_min"],
            throughput_fields_per_sec=performance_metrics["throughput_fields_per_sec"],
            avg_processing_time=performance_metrics["avg_processing_time"],
            eta_current_file_seconds=eta_current,
            eta_batch_completion_seconds=eta_batch,
            success_rate=performance_metrics["success_rate"],
            avg_confidence_score=performance_metrics["avg_confidence_score"],
            elapsed_time=time.time() - self.start_time,
            start_time=self.start_time
        )
        
        # Emit the update
        self.detailed_progress_updated.emit(progress)
    
    def _update_performance_metrics(self, metrics: Dict[str, Any]):
        """Update performance metrics from external sources."""
        # This can be used to integrate resource monitor data
        pass
    
    def _check_milestones(self):
        """Check if any progress milestones have been reached."""
        current_progress = self.calculate_batch_progress()
        
        for milestone in self.milestones:
            if current_progress >= milestone and milestone not in self.reached_milestones:
                self.reached_milestones.add(milestone)
                milestone_name = f"{int(milestone * 100)}% Complete"
                self.milestone_reached.emit(milestone_name, current_progress)
                logger.info(f"Milestone reached: {milestone_name}")
    
    def _check_performance_degradation(self):
        """Check for performance degradation and emit alerts."""
        if len(self.processing_history) < 5:  # Need some history
            return
        
        current_metrics = self.calculate_performance_metrics()
        
        # Set baseline if not set
        if self.baseline_docs_per_min == 0.0:
            self.baseline_docs_per_min = current_metrics["throughput_docs_per_min"]
            return
        
        # Check for significant performance degradation
        current_throughput = current_metrics["throughput_docs_per_min"]
        if current_throughput < self.baseline_docs_per_min * self.performance_degradation_threshold:
            degradation_percent = (1 - current_throughput / self.baseline_docs_per_min) * 100
            alert_message = (f"Performance degradation detected: {degradation_percent:.1f}% "
                           f"slower than baseline ({current_throughput:.1f} vs "
                           f"{self.baseline_docs_per_min:.1f} docs/min)")
            self.performance_alert.emit(alert_message)
            logger.warning(alert_message)
    
    def set_progress_update_interval(self, interval_ms: int):
        """Set the progress update interval in milliseconds."""
        self.progress_update_interval = interval_ms
        if self.progress_timer.isActive():
            self.progress_timer.stop()
            self.progress_timer.start(interval_ms)
    
    def get_phase_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for each processing phase."""
        stats = {}
        
        for phase in ProcessingPhase:
            timings = self.phase_timings[phase]
            if timings:
                stats[phase.phase_name] = {
                    "count": len(timings),
                    "avg_time": sum(timings) / len(timings),
                    "min_time": min(timings),
                    "max_time": max(timings),
                    "total_time": sum(timings)
                }
            else:
                stats[phase.phase_name] = {
                    "count": 0,
                    "avg_time": 0.0,
                    "min_time": 0.0,
                    "max_time": 0.0,
                    "total_time": 0.0
                }
        
        return stats
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get comprehensive processing summary."""
        if not self.processing_history:
            return {"status": "no_data"}
        
        performance_metrics = self.calculate_performance_metrics()
        phase_stats = self.get_phase_statistics()
        
        return {
            "batch_info": {
                "total_files": self.current_batch_size,
                "current_file_index": self.current_file_index,
                "batch_progress": self.calculate_batch_progress(),
                "elapsed_time": time.time() - self.start_time
            },
            "performance": performance_metrics,
            "phase_statistics": phase_stats,
            "quality_metrics": {
                "success_rate": performance_metrics["success_rate"],
                "avg_confidence": performance_metrics["avg_confidence_score"]
            },
            "milestones_reached": list(self.reached_milestones)
        } 