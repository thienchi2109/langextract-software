# Core processing components package

from .keychain import KeychainManager
from .pii_masker import PIIMasker
from .proofreader import Proofreader
from .models import (
    FieldType, ProcessingStatus, ExtractionField, ExtractionTemplate,
    ExtractionResult, ProcessingSession, AppConfig,
    ProcessorInterface, ExtractorInterface, ExporterInterface,
    TemplateManagerInterface, CredentialManagerInterface, ProofreaderInterface
)
from .exceptions import (
    LangExtractorError, FileAccessError, OCRProcessingError, APIError,
    ExtractionError, ExportError, ConfigurationError, ValidationError,
    CredentialError, APIValidationError, ErrorCategory, ErrorSeverity,
    handle_error
)

__all__ = [
    # Credential Management
    'KeychainManager',
    
    # PII Protection
    'PIIMasker',
    
    # Text Proofreading
    'Proofreader',
    
    # Data Models
    'FieldType', 'ProcessingStatus', 'ExtractionField', 'ExtractionTemplate',
    'ExtractionResult', 'ProcessingSession', 'AppConfig',
    
    # Interfaces
    'ProcessorInterface', 'ExtractorInterface', 'ExporterInterface',
    'TemplateManagerInterface', 'CredentialManagerInterface', 'ProofreaderInterface',
    
    # Exceptions
    'LangExtractorError', 'FileAccessError', 'OCRProcessingError', 'APIError',
    'ExtractionError', 'ExportError', 'ConfigurationError', 'ValidationError',
    'CredentialError', 'APIValidationError', 'ErrorCategory', 'ErrorSeverity',
    'handle_error'
]