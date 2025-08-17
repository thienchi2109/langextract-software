"""
Logging configuration and utilities for the automated report extraction system.
"""

import logging
import logging.handlers
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class PIIMaskingFormatter(logging.Formatter):
    """Custom formatter that masks PII in log messages."""
    
    # Regex patterns for Vietnamese PII
    PII_PATTERNS = {
        'account_number': re.compile(r'\b\d{10,16}\b'),
        'id_number': re.compile(r'\b\d{9,12}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b(?:\+84|0)[1-9]\d{8,9}\b'),
        'api_key': re.compile(r'\b[A-Za-z0-9]{20,}\b')
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with PII masking."""
        # Apply PII masking to the message
        if hasattr(record, 'msg') and record.msg:
            record.msg = self._mask_pii(str(record.msg))
        
        # Apply PII masking to args if present
        if hasattr(record, 'args') and record.args:
            record.args = tuple(self._mask_pii(str(arg)) for arg in record.args)
        
        return super().format(record)
    
    def _mask_pii(self, text: str) -> str:
        """Apply PII masking to text."""
        for pattern_name, pattern in self.PII_PATTERNS.items():
            if pattern_name == 'email':
                # Mask email: user@domain.com -> u***@domain.com
                text = pattern.sub(lambda m: f"{m.group(0)[0]}***@{m.group(0).split('@')[1]}", text)
            elif pattern_name == 'phone':
                # Mask phone: 0123456789 -> 012***6789
                text = pattern.sub(lambda m: f"{m.group(0)[:3]}***{m.group(0)[-4:]}", text)
            else:
                # Mask other patterns with asterisks
                text = pattern.sub(lambda m: '*' * len(m.group(0)), text)
        
        return text


class StructuredFormatter(PIIMaskingFormatter):
    """JSON formatter for structured logging with PII masking."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        config: Optional configuration dictionary with logging settings
    """
    if config is None:
        config = {}
    
    # Default configuration
    log_level = config.get('log_level', 'INFO')
    log_dir = Path(config.get('log_dir', Path.home() / 'AppData' / 'Local' / 'LangExtractor' / 'logs'))
    max_file_size = config.get('max_file_size', 10 * 1024 * 1024)  # 10MB
    backup_count = config.get('backup_count', 5)
    console_logging = config.get('console_logging', True)
    structured_logging = config.get('structured_logging', False)
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # File handler with rotation
    log_file = log_dir / 'langextractor.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # Choose formatter based on configuration
    if structured_logging:
        file_formatter = StructuredFormatter()
    else:
        file_formatter = PIIMaskingFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler (optional)
    if console_logging:
        console_handler = logging.StreamHandler()
        console_formatter = PIIMaskingFormatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, Directory: {log_dir}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra context to log messages."""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)