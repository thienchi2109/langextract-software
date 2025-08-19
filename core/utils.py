"""
Utility functions for the automated report extraction system.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from core.exceptions import ConfigurationError, ValidationError
from core.models import AppConfig


def get_app_data_dir() -> Path:
    """Get the application data directory."""
    app_data = Path.home() / 'AppData' / 'Local' / 'LangExtractor'
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data


def get_templates_dir() -> Path:
    """Get the templates directory."""
    templates_dir = get_app_data_dir() / 'templates'
    templates_dir.mkdir(parents=True, exist_ok=True)
    return templates_dir


def get_config_file() -> Path:
    """Get the configuration file path."""
    return get_app_data_dir() / 'config.json'


def load_config() -> AppConfig:
    """
    Load application configuration from file.
    
    Returns:
        AppConfig instance with loaded or default settings
    """
    config_file = get_config_file()
    
    if not config_file.exists():
        # Return default configuration
        return AppConfig()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return AppConfig.from_dict(config_data)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ConfigurationError(
            message=f"Failed to load configuration: {str(e)}",
            config_key="config.json",
            original_error=e
        )


def save_config(config: AppConfig) -> None:
    """
    Save application configuration to file.
    
    Args:
        config: AppConfig instance to save
    """
    config_file = get_config_file()
    
    try:
        # Ensure parent directory exists
        ensure_directory_exists(config_file.parent)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
    except (OSError, TypeError) as e:
        raise ConfigurationError(
            message=f"Failed to save configuration: {str(e)}",
            config_key="config.json",
            original_error=e
        )


# Aliases for compatibility
load_app_config = load_config
save_app_config = save_config


def validate_file_path(file_path: str, must_exist: bool = True) -> Path:
    """
    Validate and convert file path to Path object.
    
    Args:
        file_path: File path string
        must_exist: Whether the file must exist
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If path is invalid
    """
    if not file_path or not isinstance(file_path, str):
        raise ValidationError(
            message="File path must be a non-empty string",
            field_name="file_path",
            field_value=file_path
        )
    
    path = Path(file_path)
    
    if must_exist and not path.exists():
        raise ValidationError(
            message=f"File does not exist: {file_path}",
            field_name="file_path",
            field_value=file_path
        )
    
    return path


def get_supported_file_extensions() -> Dict[str, List[str]]:
    """
    Get supported file extensions by category.
    
    Returns:
        Dictionary mapping categories to file extensions
    """
    return {
        'pdf': ['.pdf'],
        'docx': ['.docx', '.doc'],
        'excel': ['.xlsx', '.xls'],
        'csv': ['.csv'],
        'text': ['.txt']
    }


def detect_file_type(file_path: str) -> Optional[str]:
    """
    Detect file type based on extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File type category or None if unsupported
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    
    supported_extensions = get_supported_file_extensions()
    
    for file_type, extensions in supported_extensions.items():
        if extension in extensions:
            return file_type
    
    return None


def is_supported_file(file_path: str) -> bool:
    """
    Check if file is supported for processing.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file is supported
    """
    return detect_file_type(file_path) is not None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = 'untitled'
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def ensure_directory_exists(directory: Path) -> None:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        directory: Directory path
        
    Raises:
        ConfigurationError: If directory cannot be created
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ConfigurationError(
            message=f"Failed to create directory: {directory}",
            config_key=str(directory),
            original_error=e
        )


def safe_json_load(file_path: Path) -> Dict[str, Any]:
    """
    Safely load JSON file with error handling.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded JSON data
        
    Raises:
        ConfigurationError: If file cannot be loaded
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise ConfigurationError(
            message=f"Failed to load JSON file: {file_path}",
            config_key=str(file_path),
            original_error=e
        )


def safe_json_save(data: Dict[str, Any], file_path: Path) -> None:
    """
    Safely save data to JSON file with error handling.
    
    Args:
        data: Data to save
        file_path: Path to JSON file
        
    Raises:
        ConfigurationError: If file cannot be saved
    """
    try:
        # Ensure parent directory exists
        ensure_directory_exists(file_path.parent)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (OSError, json.JSONEncodeError) as e:
        raise ConfigurationError(
            message=f"Failed to save JSON file: {file_path}",
            config_key=str(file_path),
            original_error=e
        )