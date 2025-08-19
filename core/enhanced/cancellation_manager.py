"""
Enhanced cancellation management with graceful shutdown and state preservation.

This module provides sophisticated cancellation capabilities including state preservation
for resumable processing, cleanup management, and graceful shutdown coordination.
"""

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from threading import Event, Lock
from typing import List, Dict, Any, Optional, Callable
from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger(__name__)


@dataclass
class ProcessingState:
    """Represents saveable processing state for resumable operations."""
    session_id: str
    batch_id: str
    current_file_index: int
    current_phase: str
    current_file_name: str
    file_list: List[str]
    template_data: Dict[str, Any]
    partial_results: List[Dict[str, Any]]
    processing_metadata: Dict[str, Any]
    timestamp: float
    completion_percentage: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary for JSON storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingState':
        """Deserialize state from dictionary."""
        try:
            return cls(**data)
        except Exception as e:
            logger.error(f"Error deserializing ProcessingState: {e}")
            raise ValueError(f"Invalid state data: {e}")
    
    def get_remaining_files(self) -> List[str]:
        """Get list of files that haven't been processed yet."""
        return self.file_list[self.current_file_index:]
    
    def get_progress_summary(self) -> str:
        """Get human-readable progress summary."""
        return (f"Session {self.session_id}: {self.current_file_index}/{len(self.file_list)} files "
               f"({self.completion_percentage:.1f}% complete)")


@dataclass
class CleanupTask:
    """Represents a cleanup task to be executed on cancellation."""
    name: str
    handler: Callable
    priority: int = 1  # Higher numbers execute first
    timeout_seconds: float = 5.0
    description: str = ""
    
    def __lt__(self, other):
        """Enable sorting by priority (higher first)."""
        return self.priority > other.priority


class CancellationManager(QObject):
    """Manages graceful cancellation with state preservation and cleanup."""
    
    cancellation_requested = Signal(bool)     # save_state flag
    state_saved = Signal(str)                 # file path where state was saved
    cleanup_completed = Signal()
    cancellation_confirmed = Signal(bool)     # final confirmation with success flag
    cleanup_progress = Signal(str, int, int)  # task_name, current, total
    
    def __init__(self, state_directory: str = "processing_states", 
                 graceful_timeout: float = 30.0):
        super().__init__()
        
        # Configuration
        self.state_directory = Path(state_directory)
        self.graceful_timeout = graceful_timeout
        self.max_state_files = 10
        
        # Cancellation control
        self.cancellation_event = Event()
        self.cancellation_lock = Lock()
        self.is_cancellation_requested = False
        self.cancellation_in_progress = False
        
        # Cleanup management
        self.cleanup_tasks: List[CleanupTask] = []
        self.executed_cleanup_tasks: List[str] = []
        
        # State preservation
        self.current_state: Optional[ProcessingState] = None
        self.state_preservation_enabled = True
        self.auto_save_interval = 30.0  # seconds
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_state)
        
        # Ensure state directory exists
        self.state_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"CancellationManager initialized: state_dir={self.state_directory}, "
                   f"timeout={self.graceful_timeout}s")
    
    def request_cancellation(self, save_state: bool = True, 
                           immediate: bool = False) -> bool:
        """Request graceful cancellation with optional state saving."""
        with self.cancellation_lock:
            if self.is_cancellation_requested:
                logger.warning("Cancellation already requested")
                return False
            
            self.is_cancellation_requested = True
            self.cancellation_in_progress = True
        
        try:
            logger.info(f"Cancellation requested: save_state={save_state}, immediate={immediate}")
            
            # Set the cancellation event for worker threads to check
            self.cancellation_event.set()
            
            # Emit cancellation requested signal
            self.cancellation_requested.emit(save_state)
            
            if immediate:
                # Immediate cancellation - skip graceful procedures
                self._execute_immediate_cancellation(save_state)
            else:
                # Graceful cancellation
                self._execute_graceful_cancellation(save_state)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during cancellation request: {e}")
            self.cancellation_in_progress = False
            return False
    
    def is_cancellation_pending(self) -> bool:
        """Check if cancellation has been requested."""
        return self.cancellation_event.is_set()
    
    def can_cancel_now(self) -> bool:
        """Check if it's safe to cancel at current processing point."""
        # This can be overridden by specific implementations
        # For now, we allow cancellation at any time
        return True
    
    def add_cleanup_task(self, name: str, handler: Callable, 
                        priority: int = 1, timeout: float = 5.0,
                        description: str = ""):
        """Add cleanup function to run on cancellation."""
        task = CleanupTask(
            name=name,
            handler=handler,
            priority=priority,
            timeout_seconds=timeout,
            description=description
        )
        
        self.cleanup_tasks.append(task)
        self.cleanup_tasks.sort()  # Sort by priority
        
        logger.debug(f"Added cleanup task: {name} (priority: {priority})")
    
    def remove_cleanup_task(self, name: str) -> bool:
        """Remove a cleanup task by name."""
        for i, task in enumerate(self.cleanup_tasks):
            if task.name == name:
                del self.cleanup_tasks[i]
                logger.debug(f"Removed cleanup task: {name}")
                return True
        return False
    
    def set_current_state(self, state: ProcessingState):
        """Set the current processing state for potential saving."""
        self.current_state = state
        
        # Start auto-save timer if enabled
        if self.state_preservation_enabled and not self.auto_save_timer.isActive():
            self.auto_save_timer.start(int(self.auto_save_interval * 1000))
    
    def save_processing_state(self, state: Optional[ProcessingState] = None) -> str:
        """Save current processing state to disk for later resumption."""
        if not self.state_preservation_enabled:
            logger.info("State preservation is disabled")
            return ""
        
        state_to_save = state or self.current_state
        if not state_to_save:
            logger.warning("No state available to save")
            return ""
        
        try:
            # Generate state file name
            timestamp = int(time.time())
            filename = f"processing_state_{state_to_save.session_id}_{timestamp}.json"
            state_file_path = self.state_directory / filename
            
            # Prepare state data with metadata
            state_data = {
                "version": "1.0",
                "saved_at": time.time(),
                "state": state_to_save.to_dict(),
                "metadata": {
                    "session_id": state_to_save.session_id,
                    "progress": state_to_save.completion_percentage,
                    "current_file": state_to_save.current_file_name,
                    "remaining_files": len(state_to_save.get_remaining_files())
                }
            }
            
            # Save state to file
            with open(state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            # Clean up old state files
            self._cleanup_old_state_files()
            
            logger.info(f"Processing state saved: {state_file_path}")
            self.state_saved.emit(str(state_file_path))
            
            return str(state_file_path)
            
        except Exception as e:
            logger.error(f"Error saving processing state: {e}")
            return ""
    
    def load_processing_state(self, state_file: str) -> Optional[ProcessingState]:
        """Load previously saved processing state."""
        try:
            state_path = Path(state_file)
            if not state_path.exists():
                logger.error(f"State file not found: {state_file}")
                return None
            
            with open(state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate version
            version = data.get("version", "unknown")
            if version != "1.0":
                logger.warning(f"State file version mismatch: {version}")
            
            # Load state
            state_data = data.get("state", {})
            state = ProcessingState.from_dict(state_data)
            
            logger.info(f"Loaded processing state: {state.get_progress_summary()}")
            return state
            
        except Exception as e:
            logger.error(f"Error loading processing state: {e}")
            return None
    
    def list_available_states(self) -> List[Dict[str, Any]]:
        """List all available saved states with metadata."""
        states = []
        
        try:
            for state_file in self.state_directory.glob("processing_state_*.json"):
                try:
                    with open(state_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    metadata = data.get("metadata", {})
                    states.append({
                        "file_path": str(state_file),
                        "session_id": metadata.get("session_id", "unknown"),
                        "saved_at": data.get("saved_at", 0),
                        "progress": metadata.get("progress", 0),
                        "current_file": metadata.get("current_file", ""),
                        "remaining_files": metadata.get("remaining_files", 0),
                        "file_size": state_file.stat().st_size
                    })
                except Exception as e:
                    logger.warning(f"Error reading state file {state_file}: {e}")
            
            # Sort by save time (newest first)
            states.sort(key=lambda x: x["saved_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing state files: {e}")
        
        return states
    
    def delete_state_file(self, state_file: str) -> bool:
        """Delete a saved state file."""
        try:
            state_path = Path(state_file)
            if state_path.exists():
                state_path.unlink()
                logger.info(f"Deleted state file: {state_file}")
                return True
            else:
                logger.warning(f"State file not found: {state_file}")
                return False
        except Exception as e:
            logger.error(f"Error deleting state file: {e}")
            return False
    
    def execute_cleanup(self) -> bool:
        """Execute all registered cleanup handlers in priority order."""
        if not self.cleanup_tasks:
            logger.info("No cleanup tasks to execute")
            self.cleanup_completed.emit()
            return True
        
        logger.info(f"Executing {len(self.cleanup_tasks)} cleanup tasks...")
        successful_tasks = 0
        total_tasks = len(self.cleanup_tasks)
        
        for i, task in enumerate(self.cleanup_tasks):
            try:
                self.cleanup_progress.emit(task.name, i + 1, total_tasks)
                
                logger.debug(f"Executing cleanup task: {task.name}")
                task.handler()
                
                self.executed_cleanup_tasks.append(task.name)
                successful_tasks += 1
                
                logger.debug(f"Cleanup task completed: {task.name}")
                
            except Exception as e:
                logger.error(f"Error in cleanup task {task.name}: {e}")
        
        logger.info(f"Cleanup completed: {successful_tasks}/{total_tasks} tasks successful")
        self.cleanup_completed.emit()
        
        return successful_tasks == total_tasks
    
    def _execute_graceful_cancellation(self, save_state: bool):
        """Execute graceful cancellation procedure."""
        try:
            logger.info("Starting graceful cancellation procedure...")
            
            # Save state if requested and available
            state_file = ""
            if save_state and self.current_state:
                state_file = self.save_processing_state()
            
            # Execute cleanup tasks
            cleanup_success = self.execute_cleanup()
            
            # Final confirmation
            success = cleanup_success and (not save_state or state_file)
            self.cancellation_confirmed.emit(success)
            
            logger.info(f"Graceful cancellation completed: success={success}")
            
        except Exception as e:
            logger.error(f"Error during graceful cancellation: {e}")
            self.cancellation_confirmed.emit(False)
        finally:
            self.cancellation_in_progress = False
    
    def _execute_immediate_cancellation(self, save_state: bool):
        """Execute immediate cancellation procedure."""
        try:
            logger.info("Starting immediate cancellation procedure...")
            
            # Save state if requested (quick save)
            state_file = ""
            if save_state and self.current_state:
                state_file = self.save_processing_state()
            
            # Skip cleanup tasks for immediate cancellation
            logger.info("Skipping cleanup tasks for immediate cancellation")
            
            # Final confirmation
            success = not save_state or bool(state_file)
            self.cancellation_confirmed.emit(success)
            
            logger.info(f"Immediate cancellation completed: success={success}")
            
        except Exception as e:
            logger.error(f"Error during immediate cancellation: {e}")
            self.cancellation_confirmed.emit(False)
        finally:
            self.cancellation_in_progress = False
    
    def _auto_save_state(self):
        """Auto-save current state periodically."""
        if self.current_state and not self.is_cancellation_requested:
            try:
                self.save_processing_state()
                logger.debug("Auto-saved processing state")
            except Exception as e:
                logger.error(f"Error during auto-save: {e}")
    
    def _cleanup_old_state_files(self):
        """Remove old state files to maintain storage limits."""
        try:
            state_files = list(self.state_directory.glob("processing_state_*.json"))
            
            if len(state_files) <= self.max_state_files:
                return
            
            # Sort by modification time (oldest first)
            state_files.sort(key=lambda f: f.stat().st_mtime)
            
            # Remove excess files
            files_to_remove = len(state_files) - self.max_state_files
            for state_file in state_files[:files_to_remove]:
                try:
                    state_file.unlink()
                    logger.debug(f"Removed old state file: {state_file}")
                except Exception as e:
                    logger.warning(f"Error removing old state file {state_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error cleaning up old state files: {e}")
    
    def reset_cancellation(self):
        """Reset cancellation state for new processing session."""
        with self.cancellation_lock:
            self.cancellation_event.clear()
            self.is_cancellation_requested = False
            self.cancellation_in_progress = False
            self.executed_cleanup_tasks.clear()
            
            # Stop auto-save timer
            if self.auto_save_timer.isActive():
                self.auto_save_timer.stop()
        
        logger.debug("Cancellation state reset")
    
    def get_cancellation_status(self) -> Dict[str, Any]:
        """Get current cancellation status and statistics."""
        return {
            "is_requested": self.is_cancellation_requested,
            "in_progress": self.cancellation_in_progress,
            "state_preservation_enabled": self.state_preservation_enabled,
            "cleanup_tasks_count": len(self.cleanup_tasks),
            "executed_cleanup_tasks": self.executed_cleanup_tasks.copy(),
            "current_state_available": self.current_state is not None,
            "state_directory": str(self.state_directory),
            "available_states_count": len(list(self.state_directory.glob("processing_state_*.json")))
        } 