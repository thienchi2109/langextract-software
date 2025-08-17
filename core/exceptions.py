"""
Custom exceptions and error handling for the automated report extraction system.
"""

from typing import Optional, Dict, Any, List
from enum import Enum


class ErrorCategory(Enum):
    """Categories of errors that can occur in the system."""
    FILE_ACCESS = "file_access"
    OCR_PROCESSING = "ocr_processing"
    API_ERROR = "api_error"
    EXTRACTION_ERROR = "extraction_error"
    EXPORT_ERROR = "export_error"
    CONFIGURATION_ERROR = "configuration_error"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LangExtractorError(Exception):
    """Base exception class for all application errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.suggestions = suggestions or []
        self.original_error = original_error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
            'details': self.details,
            'suggestions': self.suggestions,
            'original_error': str(self.original_error) if self.original_error else None
        }
    
    def get_user_message(self) -> str:
        """Get user-friendly error message."""
        base_message = self.message
        if self.suggestions:
            suggestions_text = "\n".join(f"• {suggestion}" for suggestion in self.suggestions)
            return f"{base_message}\n\nSuggestions:\n{suggestions_text}"
        return base_message


class FileAccessError(LangExtractorError):
    """Error accessing or reading files."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        suggestions = [
            "Check if the file exists and is accessible",
            "Verify file permissions",
            "Ensure the file is not open in another application",
            "Try copying the file to a different location"
        ]
        
        details = {"file_path": file_path} if file_path else {}
        
        super().__init__(
            message=message,
            category=ErrorCategory.FILE_ACCESS,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            suggestions=suggestions,
            original_error=original_error
        )


class OCRProcessingError(LangExtractorError):
    """Error during OCR processing."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        page_number: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        suggestions = [
            "Check if the document contains readable text",
            "Try increasing the OCR DPI setting",
            "Ensure EasyOCR models are properly installed",
            "Verify the document is not corrupted"
        ]
        
        details = {}
        if file_path:
            details["file_path"] = file_path
        if page_number is not None:
            details["page_number"] = page_number
        
        super().__init__(
            message=message,
            category=ErrorCategory.OCR_PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            suggestions=suggestions,
            original_error=original_error
        )


class APIError(LangExtractorError):
    """Error communicating with external APIs."""
    
    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        suggestions = [
            "Check your internet connection",
            "Verify your API key is valid and has sufficient quota",
            "Try again in a few minutes (rate limiting)",
            "Consider using offline mode if available"
        ]
        
        details = {}
        if api_name:
            details["api_name"] = api_name
        if status_code:
            details["status_code"] = status_code
        if response_data:
            details["response_data"] = response_data
        
        severity = ErrorSeverity.HIGH if status_code and status_code >= 500 else ErrorSeverity.MEDIUM
        
        super().__init__(
            message=message,
            category=ErrorCategory.API_ERROR,
            severity=severity,
            details=details,
            suggestions=suggestions,
            original_error=original_error
        )


class ExtractionError(LangExtractorError):
    """Error during data extraction."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        field_name: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        suggestions = [
            "Check if the document contains the expected data",
            "Review the extraction template configuration",
            "Verify field descriptions are clear and specific",
            "Consider adding examples to the template"
        ]
        
        details = {}
        if file_path:
            details["file_path"] = file_path
        if field_name:
            details["field_name"] = field_name
        
        super().__init__(
            message=message,
            category=ErrorCategory.EXTRACTION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            suggestions=suggestions,
            original_error=original_error
        )


class ExportError(LangExtractorError):
    """Error during data export."""
    
    def __init__(
        self,
        message: str,
        output_path: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        suggestions = [
            "Check if you have write permissions to the output directory",
            "Ensure there is sufficient disk space",
            "Verify the output file is not open in another application",
            "Try exporting to a different location"
        ]
        
        details = {"output_path": output_path} if output_path else {}
        
        super().__init__(
            message=message,
            category=ErrorCategory.EXPORT_ERROR,
            severity=ErrorSeverity.HIGH,
            details=details,
            suggestions=suggestions,
            original_error=original_error
        )


class ConfigurationError(LangExtractorError):
    """Error in application configuration."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        suggestions = [
            "Check the configuration file format",
            "Verify all required settings are present",
            "Reset to default configuration if needed",
            "Check the application documentation"
        ]
        
        details = {"config_key": config_key} if config_key else {}
        
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION_ERROR,
            severity=ErrorSeverity.HIGH,
            details=details,
            suggestions=suggestions,
            original_error=original_error
        )


class ValidationError(LangExtractorError):
    """Error in data validation."""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        original_error: Optional[Exception] = None
    ):
        suggestions = [
            "Check the input data format",
            "Verify field types match the schema",
            "Review validation rules",
            "Check for missing required fields"
        ]
        
        details = {}
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            details["field_value"] = str(field_value)
        
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            suggestions=suggestions,
            original_error=original_error
        )


class CredentialError(LangExtractorError):
    """Error in credential management."""
    
    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None
    ):
        suggestions = [
            "Check if Windows Credential Manager is accessible",
            "Verify the keyring library is properly installed",
            "Try running the application as administrator",
            "Restart the application and try again"
        ]
        
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION_ERROR,
            severity=ErrorSeverity.HIGH,
            suggestions=suggestions,
            original_error=original_error
        )


class APIValidationError(LangExtractorError):
    """Error validating API credentials."""
    
    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        suggestions = [
            "Verify your API key is correct",
            "Check if your API key has sufficient quota",
            "Ensure you have internet connectivity",
            "Try generating a new API key from the provider"
        ]
        
        details = {"api_name": api_name} if api_name else {}
        
        super().__init__(
            message=message,
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.HIGH,
            details=details,
            suggestions=suggestions,
            original_error=original_error
        )


def handle_error(
    error: Exception,
    logger,
    context: Optional[Dict[str, Any]] = None
) -> LangExtractorError:
    """
    Handle and convert generic exceptions to LangExtractorError.
    
    Args:
        error: The original exception
        logger: Logger instance for error logging
        context: Additional context information
        
    Returns:
        LangExtractorError instance
    """
    context = context or {}
    
    # If it's already a LangExtractorError, just log and return
    if isinstance(error, LangExtractorError):
        logger.error(f"Application error: {error.message}", extra=error.to_dict())
        return error
    
    # Convert common exception types
    if isinstance(error, FileNotFoundError):
        lang_error = FileAccessError(
            message=f"File not found: {str(error)}",
            file_path=context.get('file_path'),
            original_error=error
        )
    elif isinstance(error, PermissionError):
        lang_error = FileAccessError(
            message=f"Permission denied: {str(error)}",
            file_path=context.get('file_path'),
            original_error=error
        )
    elif isinstance(error, ConnectionError):
        lang_error = APIError(
            message=f"Network connection error: {str(error)}",
            api_name=context.get('api_name'),
            original_error=error
        )
    elif isinstance(error, ValueError):
        lang_error = ValidationError(
            message=f"Invalid value: {str(error)}",
            field_name=context.get('field_name'),
            field_value=context.get('field_value'),
            original_error=error
        )
    else:
        # Generic error handling
        lang_error = LangExtractorError(
            message=f"Unexpected error: {str(error)}",
            category=ErrorCategory.CONFIGURATION_ERROR,
            severity=ErrorSeverity.HIGH,
            details=context,
            suggestions=["Please report this error to support"],
            original_error=error
        )
    
    # Create a copy of the error dict without 'message' to avoid logging conflicts
    error_dict = lang_error.to_dict()
    error_dict.pop('message', None)  # Remove message to avoid conflict with logging
    logger.error(f"Handled error: {lang_error.message}", extra=error_dict)
    return lang_error