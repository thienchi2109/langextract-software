"""
Processing orchestrator for coordinating extraction pipeline with real-time updates.

This module provides the ProcessingOrchestrator class that coordinates all processing
steps and provides real-time updates to the GUI charts during processing.
"""

import logging
import time
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
from threading import Thread, Event
from PySide6.QtCore import QObject, Signal, QTimer, Slot

from .models import (
    ExtractionResult, ProcessingSession, ExtractionTemplate, 
    ProcessingStatus, FieldType
)
from .ingestor import Ingestor
from .extractor import Extractor
from .aggregator import Aggregator

logger = logging.getLogger(__name__)


@dataclass
class ProcessingProgress:
    """Progress information for processing updates."""
    current_file: int
    total_files: int
    current_file_name: str
    status: str
    elapsed_time: float
    estimated_remaining: float


class ProcessingOrchestrator(QObject):
    """
    Orchestrates the complete processing pipeline with real-time updates.
    
    Provides:
    - Multi-step processing pipeline coordination
    - Real-time progress updates
    - Results streaming to GUI components
    - Error handling and recovery
    - Cancellation support
    
    Signals:
        progress_updated: Emitted with ProcessingProgress when progress changes
        file_completed: Emitted with ExtractionResult when a file is processed
        session_updated: Emitted with updated ProcessingSession
        processing_completed: Emitted when all processing is done
        processing_error: Emitted when an error occurs
    """
    
    progress_updated = Signal(ProcessingProgress)
    file_completed = Signal(ExtractionResult)
    session_updated = Signal(object)  # ProcessingSession
    processing_completed = Signal(object)  # ProcessingSession
    processing_error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Processing components
        self.ingestor = Ingestor()
        self.extractor = None  # Will be initialized when needed
        self.aggregator = None  # Will be initialized when needed
        
        # Processing state
        self.current_session: Optional[ProcessingSession] = None
        self.is_processing = False
        self.should_cancel = Event()
        self.processing_thread: Optional[Thread] = None
        
        # Progress tracking
        self.start_time: Optional[float] = None
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._emit_progress_update)
        
        logger.info("ProcessingOrchestrator initialized")
    
    def start_processing(self, files: List[str], template: ExtractionTemplate) -> bool:
        """
        Start processing files with the given template.
        
        Args:
            files: List of file paths to process
            template: Extraction template to use
            
        Returns:
            True if processing started successfully, False otherwise
        """
        if self.is_processing:
            logger.warning("Processing already in progress")
            return False
        
        try:
            # Initialize components with template
            self.extractor = Extractor()
            self.aggregator = Aggregator(template)
            
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
            
            # Start processing in background thread
            self.processing_thread = Thread(
                target=self._process_files_worker,
                args=(files, template),
                daemon=True
            )
            self.processing_thread.start()
            
            # Start progress timer for regular updates
            self.progress_timer.start(1000)  # Update every second
            
            logger.info(f"Started processing {len(files)} files")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start processing: {e}", exc_info=True)
            self.processing_error.emit(f"Failed to start processing: {str(e)}")
            return False
    
    def cancel_processing(self):
        """Cancel the current processing operation."""
        if not self.is_processing:
            return
        
        logger.info("Cancelling processing...")
        self.should_cancel.set()
    
    def _process_files_worker(self, files: List[str], template: ExtractionTemplate):
        """Worker method that runs in background thread."""
        try:
            total_files = len(files)
            
            for i, file_path in enumerate(files):
                if self.should_cancel.is_set():
                    logger.info("Processing cancelled by user")
                    break
                
                try:
                    # Process single file
                    result = self._process_single_file(file_path, template)
                    
                    # Add to session
                    if self.current_session:
                        self.current_session.results.append(result)
                    
                    # Emit signals for real-time updates
                    self.file_completed.emit(result)
                    if self.current_session:
                        self.session_updated.emit(self.current_session)
                    
                    logger.debug(f"Completed processing: {file_path}")
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}", exc_info=True)
                    
                    # Create error result
                    error_result = ExtractionResult(
                        source_file=file_path,
                        extracted_data={},
                        confidence_scores={},
                        processing_time=0.0,
                        errors=[str(e)],
                        status=ProcessingStatus.FAILED
                    )
                    
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
            # Clean up from the main thread safely
            from PySide6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(
                self, "_cleanup_from_main_thread",
                Qt.QueuedConnection
            )
    
    @Slot()
    def _cleanup_from_main_thread(self):
        """Clean up processing state from main thread (Qt slot)."""
        self.is_processing = False
        if self.progress_timer.isActive():
            self.progress_timer.stop()
    
    def _process_single_file(self, file_path: str, template: ExtractionTemplate) -> ExtractionResult:
        """Process a single file and return the extraction result."""
        start_time = time.time()
        
        try:
            # Check for cancellation before starting
            if self.should_cancel.is_set():
                return ExtractionResult(
                    source_file=file_path,
                    extracted_data={},
                    confidence_scores={},
                    processing_time=0.0,
                    errors=["Processing cancelled by user"],
                    status=ProcessingStatus.CANCELLED
                )
            
            # Step 1: Ingest file (with OCR support) - Add timeout
            logger.info(f"Starting ingestion for: {file_path}")
            try:
                # Add timeout for ingestion (5 minutes max)
                import threading
                
                text_content = None
                ingestion_error = None
                
                def ingest_worker():
                    nonlocal text_content, ingestion_error
                    try:
                        text_content = self.ingestor.process(file_path)
                    except Exception as e:
                        ingestion_error = e
                
                # Run ingestion with timeout
                ingest_thread = threading.Thread(target=ingest_worker, daemon=True)
                ingest_thread.start()
                ingest_thread.join(timeout=300.0)  # 5 minute timeout
                
                if ingest_thread.is_alive():
                    raise Exception(f"File ingestion timed out after 5 minutes: {file_path}")
                
                if ingestion_error:
                    raise ingestion_error
                    
                if not text_content or not text_content.strip():
                    raise Exception("No text content extracted from file")
                    
            except Exception as e:
                logger.error(f"Ingestion failed for {file_path}: {str(e)}")
                raise
            
            # Check for cancellation after ingestion
            if self.should_cancel.is_set():
                return ExtractionResult(
                    source_file=file_path,
                    extracted_data={},
                    confidence_scores={},
                    processing_time=time.time() - start_time,
                    errors=["Processing cancelled by user"],
                    status=ProcessingStatus.CANCELLED
                )
            
            # Step 2: Extract data using LangExtract - Add timeout
            logger.info(f"Starting extraction for: {file_path}")
            try:
                if self.extractor:
                    # Add timeout for extraction (3 minutes max)
                    extracted_data = None
                    confidence_scores = None
                    extraction_error = None
                    
                    def extract_worker():
                        nonlocal extracted_data, confidence_scores, extraction_error
                        try:
                            extraction_result = self.extractor.extract(text_content, template)
                            extracted_data = extraction_result.extracted_data
                            confidence_scores = extraction_result.confidence_scores
                        except Exception as e:
                            extraction_error = e
                    
                    # Run extraction with timeout
                    extract_thread = threading.Thread(target=extract_worker, daemon=True)
                    extract_thread.start()
                    extract_thread.join(timeout=180.0)  # 3 minute timeout
                    
                    if extract_thread.is_alive():
                        raise Exception(f"Data extraction timed out after 3 minutes: {file_path}")
                    
                    if extraction_error:
                        raise extraction_error
                        
                else:
                    # Fallback to simulation if extractor not available
                    extracted_data = self._simulate_extraction(text_content, template)
                    confidence_scores = self._simulate_confidence_scores(template)
                    
            except Exception as e:
                logger.error(f"Extraction failed for {file_path}: {str(e)}")
                raise
            
            processing_time = time.time() - start_time
            
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
            error_msg = str(e)
            logger.error(f"Processing failed for {file_path}: {error_msg}")
            
            return ExtractionResult(
                source_file=file_path,
                extracted_data={},
                confidence_scores={},
                processing_time=processing_time,
                errors=[error_msg],
                status=ProcessingStatus.FAILED
            )
    
    def _simulate_extraction(self, text: str, template: ExtractionTemplate) -> Dict[str, Any]:
        """Simulate data extraction for demo purposes."""
        # This is a simplified simulation
        # In real implementation, this would use the actual Extractor
        
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
    
    def _emit_progress_update(self):
        """Emit progress update signal."""
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
    
    def get_current_session(self) -> Optional[ProcessingSession]:
        """Get the current processing session."""
        return self.current_session
    
    def is_processing_active(self) -> bool:
        """Check if processing is currently active."""
        return self.is_processing 