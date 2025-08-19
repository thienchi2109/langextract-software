"""
Advanced retry management with configurable policies and error classification.

This module provides intelligent retry mechanisms for handling transient failures
in document processing operations.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Callable, Any, Type, Optional
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of errors for retry decisions."""
    TEMPORARY = "temporary"      # Network, API timeouts - should retry
    PERMANENT = "permanent"      # File not found, permissions - no retry
    CRITICAL = "critical"        # Memory errors, system failures - stop processing


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    backoff_factor: float = 2.0      # exponential backoff multiplier
    base_delay: float = 1.0          # initial delay in seconds
    max_delay: float = 60.0          # maximum delay cap
    retry_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        ConnectionError, TimeoutError, OSError
    ])
    jitter: bool = True              # add randomness to prevent thundering herd
    
    def __post_init__(self):
        """Validate policy configuration."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.backoff_factor < 1.0:
            raise ValueError("backoff_factor must be at least 1.0")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")


@dataclass
class RetryAttempt:
    """Record of a retry attempt."""
    attempt_number: int
    timestamp: float
    error: str
    delay_before_retry: float
    operation_name: str


class ErrorClassifier:
    """Classifies errors for intelligent retry decisions."""
    
    def classify_error(self, error: Exception) -> ErrorType:
        """Classify error as TEMPORARY, PERMANENT, or CRITICAL."""
        # Network and connection issues - usually temporary
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorType.TEMPORARY
            
        # File system issues - usually permanent
        if isinstance(error, (FileNotFoundError, PermissionError, IsADirectoryError)):
            return ErrorType.PERMANENT
            
        # System resource issues - critical
        if isinstance(error, (MemoryError, SystemExit, KeyboardInterrupt)):
            return ErrorType.CRITICAL
            
        # API and HTTP errors - check status codes if available
        if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            status_code = error.response.status_code
            if 500 <= status_code < 600:  # Server errors - temporary
                return ErrorType.TEMPORARY
            elif 400 <= status_code < 500:  # Client errors - permanent
                return ErrorType.PERMANENT
                
        # Default to temporary for unknown errors
        return ErrorType.TEMPORARY


class RetryManager(QObject):
    """Manages retry policies and error recovery."""
    
    retry_attempted = Signal(str, int, str)  # operation_name, attempt_number, error_msg
    retry_exhausted = Signal(str, str)       # operation_name, final_error
    retry_succeeded = Signal(str, int)       # operation_name, attempts_used
    
    def __init__(self, policy: Optional[RetryPolicy] = None):
        super().__init__()
        self.policy = policy or RetryPolicy()
        self.classifier = ErrorClassifier()
        self.attempt_history: Dict[str, List[RetryAttempt]] = {}
        
        logger.info(f"RetryManager initialized with policy: max_attempts={self.policy.max_attempts}")
    
    def execute_with_retry(self, operation: Callable, operation_name: str, 
                          *args, **kwargs) -> Any:
        """Execute operation with retry logic and exponential backoff."""
        attempt = 1
        last_error = None
        
        while attempt <= self.policy.max_attempts:
            try:
                logger.debug(f"Executing {operation_name}, attempt {attempt}")
                result = operation(*args, **kwargs)
                
                if attempt > 1:
                    self.retry_succeeded.emit(operation_name, attempt - 1)
                    logger.info(f"Operation {operation_name} succeeded after {attempt - 1} retries")
                
                return result
                
            except Exception as error:
                last_error = error
                
                # Record the attempt
                retry_attempt = RetryAttempt(
                    attempt_number=attempt,
                    timestamp=time.time(),
                    error=str(error),
                    delay_before_retry=0.0,
                    operation_name=operation_name
                )
                
                if operation_name not in self.attempt_history:
                    self.attempt_history[operation_name] = []
                self.attempt_history[operation_name].append(retry_attempt)
                
                # Classify error to determine if we should retry
                error_type = self.classifier.classify_error(error)
                should_retry = self.should_retry(error, attempt, error_type)
                
                logger.warning(f"Operation {operation_name} failed (attempt {attempt}): {error}")
                logger.debug(f"Error classified as: {error_type}, should_retry: {should_retry}")
                
                # Emit retry attempted signal
                self.retry_attempted.emit(operation_name, attempt, str(error))
                
                if not should_retry or attempt >= self.policy.max_attempts:
                    # No more retries
                    self.retry_exhausted.emit(operation_name, str(error))
                    logger.error(f"Operation {operation_name} failed permanently after {attempt} attempts")
                    raise error
                
                # Calculate delay and wait before next attempt
                delay = self.calculate_delay(attempt)
                retry_attempt.delay_before_retry = delay
                
                logger.info(f"Retrying {operation_name} in {delay:.2f} seconds...")
                time.sleep(delay)
                attempt += 1
        
        # This should never be reached, but just in case
        if last_error:
            raise last_error
        else:
            raise RuntimeError(f"Operation {operation_name} failed with unknown error")
    
    def should_retry(self, error: Exception, attempt: int, error_type: ErrorType) -> bool:
        """Determine if error should be retried based on policy and error type."""
        # Never retry critical errors
        if error_type == ErrorType.CRITICAL:
            return False
            
        # Never retry permanent errors
        if error_type == ErrorType.PERMANENT:
            return False
            
        # Check if we've exceeded max attempts
        if attempt >= self.policy.max_attempts:
            return False
            
        # Check if this exception type is configured for retry
        if self.policy.retry_exceptions:
            for exc_type in self.policy.retry_exceptions:
                if isinstance(error, exc_type):
                    return True
            return False  # Exception type not in retry list
        
        # If no specific exceptions configured, retry temporary errors
        return error_type == ErrorType.TEMPORARY
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt with exponential backoff."""
        # Base exponential backoff
        delay = self.policy.base_delay * (self.policy.backoff_factor ** (attempt - 1))
        
        # Apply maximum delay cap
        delay = min(delay, self.policy.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.policy.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            jitter = random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay + jitter)
        
        return delay
    
    def get_attempt_history(self, operation_name: Optional[str] = None) -> Dict[str, List[RetryAttempt]]:
        """Get retry attempt history for analysis."""
        if operation_name:
            return {operation_name: self.attempt_history.get(operation_name, [])}
        return self.attempt_history.copy()
    
    def clear_history(self, operation_name: Optional[str] = None):
        """Clear retry attempt history."""
        if operation_name:
            self.attempt_history.pop(operation_name, None)
        else:
            self.attempt_history.clear()
        logger.debug(f"Cleared retry history for: {operation_name or 'all operations'}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get retry statistics for monitoring."""
        total_operations = len(self.attempt_history)
        total_attempts = sum(len(attempts) for attempts in self.attempt_history.values())
        
        failed_operations = sum(1 for attempts in self.attempt_history.values() 
                               if attempts and attempts[-1].attempt_number >= self.policy.max_attempts)
        
        return {
            "total_operations": total_operations,
            "total_attempts": total_attempts, 
            "failed_operations": failed_operations,
            "success_rate": (total_operations - failed_operations) / max(total_operations, 1),
            "average_attempts": total_attempts / max(total_operations, 1)
        } 