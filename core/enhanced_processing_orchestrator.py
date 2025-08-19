"""
Enhanced ProcessingOrchestrator with enterprise-grade features.

This module provides the main EnhancedProcessingOrchestrator class that integrates
all enhanced components while maintaining 100% backward compatibility with the
existing ProcessingOrchestrator interface.
"""

import logging
import time
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import asdict
from threading import Thread, Event
from PySide6.QtCore import QObject, Signal, QTimer

# Import existing core components
from .models import (
    ExtractionResult, ProcessingSession, ExtractionTemplate, 
    ProcessingStatus, FieldType
)
from .ingestor import Ingestor
from .extractor import Extractor
from .aggregator import Aggregator

# Import enhanced components
from .enhanced import (
    EnhancedConfig, EnhancedConfigManager,
    RetryManager, ResourceMonitor, ProgressTracker, 
    CancellationManager, ProcessingQueue,
    ProcessingPhase, ProcessingState, DetailedProgress,
    JobPriority, JobStatus
)

# Import basic progress for backward compatibility
from .processing_orchestrator import ProcessingProgress

logger = logging.getLogger(__name__)


class EnhancedProcessingOrchestrator(QObject):
    """
    Enhanced version of ProcessingOrchestrator with enterprise features.
    
    Maintains 100% backward compatibility with the original ProcessingOrchestrator
    while adding advanced features like retry management, resource monitoring,
    detailed progress tracking, graceful cancellation, and intelligent queuing.
    """
    
    # Existing signals (maintained for 100% backward compatibility)
    progress_updated = Signal(ProcessingProgress)
    file_completed = Signal(ExtractionResult)  
    session_updated = Signal(object)
    processing_completed = Signal(object)
    processing_error = Signal(str)
    
    # New enhanced signals (only emitted if enhanced_mode=True)
    detailed_progress_updated = Signal(DetailedProgress)
    resource_warning = Signal(str)
    resource_critical = Signal(str)
    retry_attempted = Signal(str, int, str)      # operation_name, attempt_number, error_msg
    retry_succeeded = Signal(str, int)           # operation_name, attempts_used
    cancellation_confirmed = Signal(bool)        # success flag
    performance_alert = Signal(str)
    milestone_reached = Signal(str, float)       # milestone_name, progress_value
    state_saved = Signal(str)                    # state_file_path
    scaling_recommendation = Signal(str, int)    # action, new_worker_count
    
    def __init__(self, parent=None, enhanced_mode: bool = True, 
                 config: Optional[EnhancedConfig] = None):
        super().__init__(parent)
        
        # Load configuration
        self.config = config or EnhancedConfigManager.load_config()
        self.enhanced_mode = enhanced_mode and self.config.enhanced_mode_enabled
        
        # Initialize existing components (unchanged for compatibility)
        self.ingestor = Ingestor()
        self.extractor = None 
        self.aggregator = None
        
        # Initialize enhanced components (only if enhanced mode enabled)
        if self.enhanced_mode:
            self._initialize_enhanced_components()
        else:
            # Set to None for basic mode
            self.retry_manager = None
            self.resource_monitor = None
            self.progress_tracker = None
            self.cancellation_manager = None
            self.processing_queue = None
        
        # Initialize existing state (unchanged for compatibility)
        self.current_session: Optional[ProcessingSession] = None
        self.is_processing = False
        self.should_cancel = Event()
        self.processing_thread: Optional[Thread] = None
        
        # Enhanced state
        self.session_id: Optional[str] = None
        self.current_batch_id: Optional[str] = None
        
        # Progress tracking for compatibility
        self.start_time: Optional[float] = None
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._emit_progress_update)
        
        # Setup signal connections
        if self.enhanced_mode:
            self._setup_enhanced_connections()
        
        logger.info(f"EnhancedProcessingOrchestrator initialized: enhanced_mode={self.enhanced_mode}")
    
    def _initialize_enhanced_components(self):
        """Initialize all enhanced components."""
        # Retry management
        if self.config.retry_enabled:
            self.retry_manager = RetryManager(self.config.retry_policy)
        else:
            self.retry_manager = None
        
        # Resource monitoring
        if self.config.resource_monitoring_enabled:
            self.resource_monitor = ResourceMonitor(self.config.resource_limits)
        else:
            self.resource_monitor = None
        
        # Progress tracking
        if self.config.detailed_progress_enabled:
            self.progress_tracker = ProgressTracker()
            if self.config.progress_config.progress_update_interval:
                interval_ms = int(self.config.progress_config.progress_update_interval * 1000)
                self.progress_tracker.set_progress_update_interval(interval_ms)
        else:
            self.progress_tracker = None
        
        # Cancellation management
        if self.config.enhanced_cancellation_enabled:
            self.cancellation_manager = CancellationManager(
                state_directory=self.config.cancellation_config.state_file_directory,
                graceful_timeout=self.config.cancellation_config.graceful_cancellation_timeout
            )
        else:
            self.cancellation_manager = None
        
        # Processing queue
        if self.config.intelligent_queue_enabled:
            self.processing_queue = ProcessingQueue(
                max_workers=self.config.queue_config.max_workers,
                min_workers=self.config.queue_config.min_workers
            )
        else:
            self.processing_queue = None
        
        logger.info("Enhanced components initialized")
    
    def _setup_enhanced_connections(self):
        """Setup signal connections for enhanced components."""
        # Retry manager signals
        if self.retry_manager:
            self.retry_manager.retry_attempted.connect(self.retry_attempted.emit)
            self.retry_manager.retry_succeeded.connect(self.retry_succeeded.emit)
        
        # Resource monitor signals
        if self.resource_monitor:
            self.resource_monitor.resource_warning.connect(self.resource_warning.emit)
            self.resource_monitor.resource_critical.connect(self.resource_critical.emit)
            self.resource_monitor.scaling_recommendation.connect(self.scaling_recommendation.emit)
        
        # Progress tracker signals
        if self.progress_tracker:
            self.progress_tracker.detailed_progress_updated.connect(self.detailed_progress_updated.emit)
            self.progress_tracker.performance_alert.connect(self.performance_alert.emit)
            self.progress_tracker.milestone_reached.connect(self.milestone_reached.emit)
        
        # Cancellation manager signals
        if self.cancellation_manager:
            self.cancellation_manager.cancellation_confirmed.connect(self.cancellation_confirmed.emit)
            self.cancellation_manager.state_saved.connect(self.state_saved.emit)
        
        # Processing queue signals
        if self.processing_queue:
            self.processing_queue.scaling_recommendation.connect(self.scaling_recommendation.emit)
    
    def start_processing(self, files: List[str], template: ExtractionTemplate,
                        resume_state: Optional[ProcessingState] = None) -> bool:
        """
        Start processing files with the given template.
        
        Enhanced version with optional state resumption.
        Maintains compatibility with original start_processing method.
        """
        if self.is_processing:
            logger.warning("Processing already in progress")
            return False
        
        try:
            # Generate session ID
            self.session_id = str(uuid.uuid4())
            
            # Initialize components with template
            self.extractor = Extractor()
            self.aggregator = Aggregator(template)
            
            # Handle state resumption
            if resume_state and self.enhanced_mode:
                files = resume_state.get_remaining_files()
                logger.info(f"Resuming processing from state: {resume_state.get_progress_summary()}")
            
            # Create processing session
            self.current_session = ProcessingSession(
                template=template,
                files=files,
                results=[],
                summary_stats={},
                export_path=""
            )
            
            # Reset state
            self.should_cancel.clear()
            self.is_processing = True
            self.start_time = time.time()
            
            # Initialize enhanced components for this session
            if self.enhanced_mode:
                self._start_enhanced_processing(files, template, resume_state)
            
            # Start processing in background thread
            self.processing_thread = Thread(
                target=self._process_files_worker,
                args=(files, template),
                daemon=True
            )
            self.processing_thread.start()
            
            # Start progress timer for regular updates (compatibility)
            self.progress_timer.start(1000)  # Update every second
            
            logger.info(f"Started processing {len(files)} files (session: {self.session_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start processing: {e}", exc_info=True)
            self.processing_error.emit(f"Failed to start processing: {str(e)}")
            return False
    
    def _start_enhanced_processing(self, files: List[str], template: ExtractionTemplate,
                                 resume_state: Optional[ProcessingState] = None):
        """Start enhanced processing components."""
        # Start resource monitoring
        if self.resource_monitor:
            self.resource_monitor.start_monitoring()
        
        # Start progress tracking
        if self.progress_tracker:
            file_names = [str(f) for f in files]
            self.progress_tracker.start_batch_tracking(len(files), file_names)
        
        # Setup cancellation state
        if self.cancellation_manager:
            self.cancellation_manager.reset_cancellation()
            
            # Create processing state for saving
            processing_state = ProcessingState(
                session_id=self.session_id,
                batch_id=self.current_batch_id or self.session_id,
                current_file_index=0,
                current_phase=ProcessingPhase.INGESTION.phase_name,
                current_file_name=files[0] if files else "",
                file_list=files,
                template_data=asdict(template),
                partial_results=[],
                processing_metadata={
                    "start_time": self.start_time,
                    "enhanced_mode": True,
                    "config_summary": self.config.get_active_features()
                },
                timestamp=time.time(),
                completion_percentage=0.0
            )
            
            self.cancellation_manager.set_current_state(processing_state)
        
        # Start processing queue
        if self.processing_queue:
            self.processing_queue.start_queue()
            
            # Add batch to queue
            self.current_batch_id = self.processing_queue.add_batch(
                files, 
                priority=JobPriority.NORMAL,
                metadata={"session_id": self.session_id, "template": template.name}
            )
    
    def cancel_processing(self, save_state: bool = True) -> bool:
        """Cancel the current processing operation with enhanced features."""
        if not self.is_processing:
            logger.warning("No processing in progress to cancel")
            return False
        
        if self.enhanced_mode and self.cancellation_manager:
            # Enhanced cancellation with state preservation
            logger.info("Requesting enhanced cancellation...")
            return self.cancellation_manager.request_cancellation(save_state=save_state)
        else:
            # Basic cancellation (original behavior)
            logger.info("Cancelling processing...")
            self.should_cancel.set()
            return True
    
    def cancel_processing_immediate(self) -> bool:
        """Cancel processing immediately without graceful shutdown."""
        if self.enhanced_mode and self.cancellation_manager:
            return self.cancellation_manager.request_cancellation(save_state=False, immediate=True)
        else:
            self.should_cancel.set()
            return True
    
    def load_and_resume_processing(self, state_file: str) -> bool:
        """Load a saved state and resume processing."""
        if not self.enhanced_mode or not self.cancellation_manager:
            logger.error("State resumption requires enhanced mode with cancellation manager")
            return False
        
        try:
            # Load processing state
            state = self.cancellation_manager.load_processing_state(state_file)
            if not state:
                return False
            
            # Create template from saved data
            template_data = state.template_data
            template = ExtractionTemplate(**template_data)
            
            # Resume processing
            return self.start_processing(state.file_list, template, resume_state=state)
            
        except Exception as e:
            logger.error(f"Error resuming from state: {e}")
            return False
    
    def _process_files_worker(self, files: List[str], template: ExtractionTemplate):
        """Enhanced worker method that runs in background thread."""
        try:
            total_files = len(files)
            
            for i, file_path in enumerate(files):
                # Check for cancellation
                if self._check_cancellation():
                    logger.info("Processing cancelled by user")
                    break
                
                try:
                    # Update progress tracker
                    if self.progress_tracker:
                        self.progress_tracker.update_file_progress(
                            i, file_path, ProcessingPhase.INGESTION, 0.0
                        )
                    
                    # Process single file with enhanced features
                    result = self._process_single_file_enhanced(file_path, template, i)
                    
                    # Add to session
                    if self.current_session:
                        self.current_session.results.append(result)
                    
                    # Update progress tracker with completion
                    if self.progress_tracker:
                        field_count = len(result.extracted_data)
                        confidence_scores = list(result.confidence_scores.values())
                        self.progress_tracker.record_file_completion(
                            file_path,
                            ProcessingPhase.VALIDATION,
                            result.processing_time,
                            result.status == ProcessingStatus.COMPLETED,
                            field_count,
                            confidence_scores
                        )
                    
                    # Emit signals for real-time updates
                    self.file_completed.emit(result)
                    if self.current_session:
                        self.session_updated.emit(self.current_session)
                    
                    logger.debug(f"Completed processing: {file_path}")
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}", exc_info=True)
                    
                    # Create error result
                    error_result = self._create_error_result(file_path, str(e))
                    
                    if self.current_session:
                        self.current_session.results.append(error_result)
                    
                    self.file_completed.emit(error_result)
                    if self.current_session:
                        self.session_updated.emit(self.current_session)
            
            # Processing completed
            self._finalize_processing()
            
        except Exception as e:
            logger.error(f"Critical error in processing worker: {e}", exc_info=True)
            self.processing_error.emit(f"Critical processing error: {str(e)}")
        finally:
            self._cleanup_processing()
    
    def _process_single_file_enhanced(self, file_path: str, template: ExtractionTemplate, 
                                    file_index: int) -> ExtractionResult:
        """Process a single file with enhanced features."""
        start_time = time.time()
        
        try:
            # Update progress: Ingestion phase
            if self.progress_tracker:
                self.progress_tracker.update_file_progress(
                    file_index, file_path, ProcessingPhase.INGESTION, 0.0
                )
            
            # Step 1: Ingest file (with OCR support)
            if self.retry_manager and self.config.retry_enabled:
                text_content = self.retry_manager.execute_with_retry(
                    self.ingestor.process, "file_ingestion", file_path
                )
            else:
                text_content = self.ingestor.process(file_path)
            
            if not text_content or not text_content.strip():
                raise Exception("No text content extracted from file")
            
            # Update progress: OCR phase completed
            if self.progress_tracker:
                self.progress_tracker.update_file_progress(
                    file_index, file_path, ProcessingPhase.OCR, 1.0
                )
            
            # Update progress: Extraction phase
            if self.progress_tracker:
                self.progress_tracker.update_file_progress(
                    file_index, file_path, ProcessingPhase.EXTRACTION, 0.0
                )
            
            # Step 2: Extract data using LangExtract
            if self.extractor:
                if self.retry_manager and self.config.retry_enabled:
                    extraction_result = self.retry_manager.execute_with_retry(
                        self.extractor.extract, "data_extraction", text_content, template
                    )
                else:
                    extraction_result = self.extractor.extract(text_content, template)
                
                extracted_data = extraction_result.extracted_data
                confidence_scores = extraction_result.confidence_scores
            else:
                # Fallback to simulation if extractor not available
                extracted_data = self._simulate_extraction(text_content, template)
                confidence_scores = self._simulate_confidence_scores(template)
            
            # Update progress: Validation phase
            if self.progress_tracker:
                self.progress_tracker.update_file_progress(
                    file_index, file_path, ProcessingPhase.VALIDATION, 0.5
                )
            
            processing_time = time.time() - start_time
            
            # Complete validation
            if self.progress_tracker:
                self.progress_tracker.update_file_progress(
                    file_index, file_path, ProcessingPhase.VALIDATION, 1.0
                )
            
            return ExtractionResult(
                source_file=file_path,
                extracted_data=extracted_data,
                confidence_scores=confidence_scores,
                processing_time=processing_time,
                errors=[],
                status=ProcessingStatus.COMPLETED
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return self._create_error_result(file_path, str(e), processing_time)
    
    def _create_error_result(self, file_path: str, error_message: str, 
                           processing_time: float = 0.0) -> ExtractionResult:
        """Create an error result for a failed file."""
        return ExtractionResult(
            source_file=file_path,
            extracted_data={},
            confidence_scores={},
            processing_time=processing_time,
            errors=[error_message],
            status=ProcessingStatus.FAILED
        )
    
    def _check_cancellation(self) -> bool:
        """Check if cancellation has been requested."""
        if self.enhanced_mode and self.cancellation_manager:
            return self.cancellation_manager.is_cancellation_pending()
        else:
            return self.should_cancel.is_set()
    
    def _finalize_processing(self):
        """Finalize processing and emit completion signal."""
        if self.current_session:
            # Calculate final summary stats using aggregator
            if self.aggregator and self.current_session.results:
                try:
                    summary_stats = self.aggregator.aggregate_results(self.current_session.results)
                    self.current_session.summary_stats = summary_stats
                except Exception as e:
                    logger.error(f"Error calculating summary stats: {e}")
            
            self.processing_completed.emit(self.current_session)
            logger.info(f"Processing completed: {len(self.current_session.results)} files processed")
        
        # Stop enhanced components
        if self.enhanced_mode:
            if self.progress_tracker:
                self.progress_tracker.stop_batch_tracking()
            
            if self.resource_monitor:
                self.resource_monitor.stop_monitoring()
            
            if self.processing_queue:
                self.processing_queue.stop_queue(wait_for_completion=False)
    
    def _cleanup_processing(self):
        """Clean up processing state."""
        self.is_processing = False
        self.progress_timer.stop()
        
        if self.enhanced_mode and self.cancellation_manager:
            # Reset cancellation state for next session
            self.cancellation_manager.reset_cancellation()
    
    def _emit_progress_update(self):
        """Emit basic progress update signal for backward compatibility."""
        if not self.current_session or not self.start_time:
            return
        
        total_files = len(self.current_session.files)
        completed_files = len(self.current_session.results)
        elapsed_time = time.time() - self.start_time
        
        # Estimate remaining time
        if completed_files > 0:
            avg_time_per_file = elapsed_time / completed_files
            remaining_files = total_files - completed_files
            estimated_remaining = avg_time_per_file * remaining_files
        else:
            estimated_remaining = 0.0
        
        # Current file info
        current_file_name = ""
        if completed_files < total_files:
            current_file_name = self.current_session.files[completed_files]
        
        progress = ProcessingProgress(
            current_file=completed_files,
            total_files=total_files,
            current_file_name=current_file_name,
            status="Processing...",
            elapsed_time=elapsed_time,
            estimated_remaining=estimated_remaining
        )
        
        self.progress_updated.emit(progress)
    
    # Simulation methods (inherited from original orchestrator)
    def _simulate_extraction(self, text: str, template: ExtractionTemplate) -> Dict[str, Any]:
        """Simulate data extraction for demo purposes."""
        import random
        
        extracted_data = {}
        
        for field in template.fields:
            # Simulate extraction success rate
            if random.random() > 0.3:  # 70% success rate
                if field.type == FieldType.TEXT:
                    extracted_data[field.name] = f"Sample {field.name}"
                elif field.type == FieldType.NUMBER:
                    extracted_data[field.name] = random.randint(100, 10000)
                elif field.type == FieldType.CURRENCY:
                    extracted_data[field.name] = random.randint(1000000, 50000000)
                elif field.type == FieldType.DATE:
                    extracted_data[field.name] = "2024-Q4"
        
        return extracted_data
    
    def _simulate_confidence_scores(self, template: ExtractionTemplate) -> Dict[str, float]:
        """Simulate confidence scores for demo purposes."""
        import random
        
        confidence_scores = {}
        
        for field in template.fields:
            # Simulate confidence score
            confidence_scores[field.name] = random.uniform(0.5, 0.98)
        
        return confidence_scores
    
    # Public methods for enhanced features
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """Get comprehensive enhanced statistics."""
        if not self.enhanced_mode:
            return {"enhanced_mode": False}
        
        stats = {"enhanced_mode": True}
        
        if self.retry_manager:
            stats["retry_statistics"] = self.retry_manager.get_statistics()
        
        if self.resource_monitor:
            stats["resource_summary"] = self.resource_monitor.get_resource_summary()
        
        if self.progress_tracker:
            stats["processing_summary"] = self.progress_tracker.get_processing_summary()
        
        if self.cancellation_manager:
            stats["cancellation_status"] = self.cancellation_manager.get_cancellation_status()
        
        if self.processing_queue:
            stats["queue_statistics"] = self.processing_queue.get_statistics()
        
        return stats
    
    def get_available_saved_states(self) -> List[Dict[str, Any]]:
        """Get list of available saved processing states."""
        if self.enhanced_mode and self.cancellation_manager:
            return self.cancellation_manager.list_available_states()
        return []
    
    # Compatibility methods (unchanged from original)
    def get_current_session(self) -> Optional[ProcessingSession]:
        """Get the current processing session."""
        return self.current_session
    
    def is_processing_active(self) -> bool:
        """Check if processing is currently active."""
        return self.is_processing 