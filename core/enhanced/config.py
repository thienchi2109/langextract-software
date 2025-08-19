"""
Configuration management for enhanced ProcessingOrchestrator features.

This module provides configuration classes and management for all enhanced
processing features including retry policies, resource limits, and feature toggles.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from pathlib import Path

from .retry_manager import RetryPolicy
from .resource_monitor import ResourceLimits

logger = logging.getLogger(__name__)


@dataclass
class ProgressConfig:
    """Configuration for enhanced progress reporting."""
    detailed_progress_enabled: bool = True
    progress_update_interval: float = 0.5    # seconds between updates
    performance_metrics_enabled: bool = True
    phase_tracking_enabled: bool = True
    eta_calculation_enabled: bool = True
    throughput_tracking_enabled: bool = True
    
    def __post_init__(self):
        """Validate progress configuration."""
        if self.progress_update_interval < 0.1:
            raise ValueError("progress_update_interval must be at least 0.1 seconds")
        if self.progress_update_interval > 10.0:
            raise ValueError("progress_update_interval should not exceed 10 seconds")


@dataclass
class CancellationConfig:
    """Configuration for enhanced cancellation features."""
    state_preservation_enabled: bool = True
    graceful_cancellation_timeout: float = 30.0  # seconds to wait for graceful shutdown
    auto_cleanup_enabled: bool = True
    save_state_by_default: bool = True
    state_file_directory: str = "processing_states"
    max_state_files: int = 10  # maximum number of state files to keep
    
    def __post_init__(self):
        """Validate cancellation configuration."""
        if self.graceful_cancellation_timeout < 1.0:
            raise ValueError("graceful_cancellation_timeout must be at least 1 second")
        if self.max_state_files < 1:
            raise ValueError("max_state_files must be at least 1")


@dataclass
class QueueConfig:
    """Configuration for processing queue management."""
    max_concurrent_files: int = 3
    intelligent_batching_enabled: bool = True
    priority_processing_enabled: bool = False
    complexity_estimation_enabled: bool = True
    auto_scaling_enabled: bool = True
    min_workers: int = 1
    max_workers: int = 8
    
    def __post_init__(self):
        """Validate queue configuration."""
        if not 1 <= self.max_concurrent_files <= 16:
            raise ValueError("max_concurrent_files must be between 1 and 16")
        if not 1 <= self.min_workers <= self.max_workers:
            raise ValueError("min_workers must be between 1 and max_workers")
        if self.max_workers > 16:
            raise ValueError("max_workers should not exceed 16")


@dataclass
class EnhancedConfig:
    """Master configuration for all enhanced features."""
    
    # Global enhancement toggle
    enhanced_mode_enabled: bool = True
    
    # Component configurations
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    progress_config: ProgressConfig = field(default_factory=ProgressConfig)
    cancellation_config: CancellationConfig = field(default_factory=CancellationConfig)
    queue_config: QueueConfig = field(default_factory=QueueConfig)
    
    # Feature toggles
    retry_enabled: bool = True
    resource_monitoring_enabled: bool = True
    detailed_progress_enabled: bool = True
    enhanced_cancellation_enabled: bool = True
    intelligent_queue_enabled: bool = True
    
    # Logging and debugging
    enhanced_logging_enabled: bool = True
    performance_profiling_enabled: bool = False
    debug_mode: bool = False
    
    def __post_init__(self):
        """Validate the complete configuration."""
        # If enhanced mode is disabled, disable all individual features
        if not self.enhanced_mode_enabled:
            self.retry_enabled = False
            self.resource_monitoring_enabled = False
            self.detailed_progress_enabled = False
            self.enhanced_cancellation_enabled = False
            self.intelligent_queue_enabled = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        def convert_dataclass(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return asdict(obj)
            return obj
            
        return {
            "enhanced_mode_enabled": self.enhanced_mode_enabled,
            "retry_policy": asdict(self.retry_policy),
            "resource_limits": asdict(self.resource_limits),
            "progress_config": asdict(self.progress_config),
            "cancellation_config": asdict(self.cancellation_config),
            "queue_config": asdict(self.queue_config),
            "retry_enabled": self.retry_enabled,
            "resource_monitoring_enabled": self.resource_monitoring_enabled,
            "detailed_progress_enabled": self.detailed_progress_enabled,
            "enhanced_cancellation_enabled": self.enhanced_cancellation_enabled,
            "intelligent_queue_enabled": self.intelligent_queue_enabled,
            "enhanced_logging_enabled": self.enhanced_logging_enabled,
            "performance_profiling_enabled": self.performance_profiling_enabled,
            "debug_mode": self.debug_mode,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedConfig':
        """Create configuration from dictionary."""
        try:
            # Extract component configurations
            retry_policy = RetryPolicy(**data.get("retry_policy", {}))
            resource_limits = ResourceLimits(**data.get("resource_limits", {}))
            progress_config = ProgressConfig(**data.get("progress_config", {}))
            cancellation_config = CancellationConfig(**data.get("cancellation_config", {}))
            queue_config = QueueConfig(**data.get("queue_config", {}))
            
            # Create main configuration
            config = cls(
                enhanced_mode_enabled=data.get("enhanced_mode_enabled", True),
                retry_policy=retry_policy,
                resource_limits=resource_limits,
                progress_config=progress_config,
                cancellation_config=cancellation_config,
                queue_config=queue_config,
                retry_enabled=data.get("retry_enabled", True),
                resource_monitoring_enabled=data.get("resource_monitoring_enabled", True),
                detailed_progress_enabled=data.get("detailed_progress_enabled", True),
                enhanced_cancellation_enabled=data.get("enhanced_cancellation_enabled", True),
                intelligent_queue_enabled=data.get("intelligent_queue_enabled", True),
                enhanced_logging_enabled=data.get("enhanced_logging_enabled", True),
                performance_profiling_enabled=data.get("performance_profiling_enabled", False),
                debug_mode=data.get("debug_mode", False),
            )
            
            return config
            
        except Exception as e:
            logger.error(f"Error creating config from dict: {e}")
            logger.info("Using default configuration")
            return cls()
    
    def get_active_features(self) -> List[str]:
        """Get list of currently active enhanced features."""
        features = []
        
        if not self.enhanced_mode_enabled:
            return ["basic_mode"]
            
        if self.retry_enabled:
            features.append("retry_management")
        if self.resource_monitoring_enabled:
            features.append("resource_monitoring")
        if self.detailed_progress_enabled:
            features.append("detailed_progress")
        if self.enhanced_cancellation_enabled:
            features.append("enhanced_cancellation")
        if self.intelligent_queue_enabled:
            features.append("intelligent_queue")
            
        return features if features else ["enhanced_mode_disabled"]
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings/errors."""
        warnings = []
        
        # Check for potential performance issues
        if (self.queue_config.max_concurrent_files > 6 and 
            self.resource_limits.max_memory_percent > 85):
            warnings.append("High concurrent files with high memory limit may cause system strain")
            
        if (self.progress_config.progress_update_interval < 0.5 and 
            self.progress_config.performance_metrics_enabled):
            warnings.append("Frequent progress updates with metrics may impact performance")
            
        if self.retry_policy.max_attempts > 5:
            warnings.append("High retry attempts may significantly increase processing time")
            
        if self.queue_config.max_workers > 8:
            warnings.append("Very high worker count may cause resource contention")
            
        # Check for configuration conflicts
        if not self.enhanced_mode_enabled and any([
            self.retry_enabled, self.resource_monitoring_enabled,
            self.detailed_progress_enabled, self.enhanced_cancellation_enabled,
            self.intelligent_queue_enabled
        ]):
            warnings.append("Enhanced features enabled but enhanced_mode_enabled is False")
            
        return warnings


class EnhancedConfigManager:
    """Manages enhanced configuration persistence and validation."""
    
    DEFAULT_CONFIG_FILE = "enhanced_config.json"
    CONFIG_VERSION = "1.0"
    
    @staticmethod
    def get_config_path(config_file: Optional[str] = None) -> Path:
        """Get the full path for the configuration file."""
        filename = config_file or EnhancedConfigManager.DEFAULT_CONFIG_FILE
        
        # Try to use a user-specific config directory
        config_dir = Path.home() / ".langextractor"
        config_dir.mkdir(exist_ok=True)
        
        return config_dir / filename
    
    @staticmethod
    def load_config(config_file: Optional[str] = None) -> EnhancedConfig:
        """Load configuration from file or create default."""
        config_path = EnhancedConfigManager.get_config_path(config_file)
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Check version compatibility
                version = data.get("version", "unknown")
                if version != EnhancedConfigManager.CONFIG_VERSION:
                    logger.warning(f"Config version mismatch: {version} vs {EnhancedConfigManager.CONFIG_VERSION}")
                
                # Load configuration
                config_data = data.get("config", {})
                config = EnhancedConfig.from_dict(config_data)
                
                logger.info(f"Loaded enhanced configuration from: {config_path}")
                return config
            else:
                logger.info("No enhanced configuration file found, using defaults")
                return EnhancedConfig()
                
        except Exception as e:
            logger.error(f"Error loading enhanced configuration: {e}")
            logger.info("Using default enhanced configuration")
            return EnhancedConfig()
    
    @staticmethod
    def save_config(config: EnhancedConfig, config_file: Optional[str] = None):
        """Save configuration to persistent storage."""
        config_path = EnhancedConfigManager.get_config_path(config_file)
        
        try:
            # Validate configuration before saving
            warnings = config.validate()
            if warnings:
                logger.warning(f"Configuration warnings: {warnings}")
            
            # Prepare data for saving
            save_data = {
                "version": EnhancedConfigManager.CONFIG_VERSION,
                "config": config.to_dict(),
                "metadata": {
                    "saved_at": str(Path(__file__).stat().st_mtime),
                    "active_features": config.get_active_features(),
                    "warnings": warnings
                }
            }
            
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved enhanced configuration to: {config_path}")
            
        except Exception as e:
            logger.error(f"Error saving enhanced configuration: {e}")
            raise
    
    @staticmethod
    def validate_config(config: EnhancedConfig) -> List[str]:
        """Validate configuration and return list of warnings/errors."""
        return config.validate()
    
    @staticmethod
    def create_default_config_file(config_file: Optional[str] = None):
        """Create a default configuration file with comments."""
        config_path = EnhancedConfigManager.get_config_path(config_file)
        
        if config_path.exists():
            logger.info(f"Configuration file already exists: {config_path}")
            return
        
        default_config = EnhancedConfig()
        EnhancedConfigManager.save_config(default_config, config_file)
        logger.info(f"Created default enhanced configuration: {config_path}")
    
    @staticmethod
    def reset_to_defaults(config_file: Optional[str] = None):
        """Reset configuration to defaults."""
        config_path = EnhancedConfigManager.get_config_path(config_file)
        
        try:
            if config_path.exists():
                # Backup existing config
                backup_path = config_path.with_suffix('.backup.json')
                config_path.rename(backup_path)
                logger.info(f"Backed up existing config to: {backup_path}")
            
            # Create new default config
            default_config = EnhancedConfig()
            EnhancedConfigManager.save_config(default_config, config_file)
            logger.info("Reset enhanced configuration to defaults")
            
        except Exception as e:
            logger.error(f"Error resetting configuration: {e}")
            raise
    
    @staticmethod
    def get_config_summary(config: EnhancedConfig) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            "enhanced_mode": config.enhanced_mode_enabled,
            "active_features": config.get_active_features(),
            "retry_attempts": config.retry_policy.max_attempts,
            "max_memory_percent": config.resource_limits.max_memory_percent,
            "max_cpu_percent": config.resource_limits.max_cpu_percent,
            "max_workers": config.queue_config.max_workers,
            "progress_interval": config.progress_config.progress_update_interval,
            "warnings": config.validate()
        } 