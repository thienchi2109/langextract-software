"""
Core data models and interfaces for the automated report extraction system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from abc import ABC, abstractmethod


class FieldType(Enum):
    """Supported field types for extraction schema."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CURRENCY = "currency"


class ProcessingStatus(Enum):
    """Status of file processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExtractionField:
    """Configuration for a single extraction field."""
    name: str
    type: FieldType
    description: str
    optional: bool = False
    number_locale: str = 'vi-VN'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'optional': self.optional,
            'number_locale': self.number_locale
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractionField':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            type=FieldType(data['type']),
            description=data['description'],
            optional=data.get('optional', False),
            number_locale=data.get('number_locale', 'vi-VN')
        )


@dataclass
class ExtractionTemplate:
    """Template configuration for data extraction."""
    name: str
    prompt_description: str
    fields: List[ExtractionField]
    examples: List[Dict[str, Any]] = field(default_factory=list)
    provider: Dict[str, Any] = field(default_factory=dict)
    run_options: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'prompt_description': self.prompt_description,
            'fields': [field.to_dict() for field in self.fields],
            'examples': self.examples,
            'provider': self.provider,
            'run_options': self.run_options
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractionTemplate':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            prompt_description=data['prompt_description'],
            fields=[ExtractionField.from_dict(f) for f in data['fields']],
            examples=data.get('examples', []),
            provider=data.get('provider', {}),
            run_options=data.get('run_options', {})
        )


@dataclass
class ExtractionResult:
    """Result of data extraction from a single file."""
    source_file: str
    extracted_data: Dict[str, Any]
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    status: ProcessingStatus = ProcessingStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'source_file': self.source_file,
            'extracted_data': self.extracted_data,
            'confidence_scores': self.confidence_scores,
            'processing_time': self.processing_time,
            'errors': self.errors,
            'status': self.status.value
        }


@dataclass
class ProcessingSession:
    """Complete processing session with template and results."""
    template: ExtractionTemplate
    files: List[str]
    results: List[ExtractionResult] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    export_path: Optional[str] = None
    
    def get_completed_count(self) -> int:
        """Get number of completed files."""
        return sum(1 for r in self.results if r.status == ProcessingStatus.COMPLETED)
    
    def get_failed_count(self) -> int:
        """Get number of failed files."""
        return sum(1 for r in self.results if r.status == ProcessingStatus.FAILED)


@dataclass
class AppConfig:
    """Application configuration settings."""
    ocr_enabled: bool = True
    ocr_languages: List[str] = field(default_factory=lambda: ['vi', 'en'])
    proofread_enabled: bool = True
    pii_masking_enabled: bool = True
    offline_mode: bool = False
    max_workers: int = 4
    log_level: str = 'INFO'
    ocr_dpi: int = 300
    api_timeout: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'ocr_enabled': self.ocr_enabled,
            'ocr_languages': self.ocr_languages,
            'proofread_enabled': self.proofread_enabled,
            'pii_masking_enabled': self.pii_masking_enabled,
            'offline_mode': self.offline_mode,
            'max_workers': self.max_workers,
            'log_level': self.log_level,
            'ocr_dpi': self.ocr_dpi,
            'api_timeout': self.api_timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create from dictionary."""
        return cls(
            ocr_enabled=data.get('ocr_enabled', True),
            ocr_languages=data.get('ocr_languages', ['vi', 'en']),
            proofread_enabled=data.get('proofread_enabled', True),
            pii_masking_enabled=data.get('pii_masking_enabled', True),
            offline_mode=data.get('offline_mode', False),
            max_workers=data.get('max_workers', 4),
            log_level=data.get('log_level', 'INFO'),
            ocr_dpi=data.get('ocr_dpi', 300),
            api_timeout=data.get('api_timeout', 30)
        )


# Base interfaces for core components

class ProcessorInterface(ABC):
    """Base interface for document processors."""
    
    @abstractmethod
    def process(self, file_path: str) -> str:
        """Process a file and return extracted text."""
        pass
    
    @abstractmethod
    def supports_format(self, file_path: str) -> bool:
        """Check if processor supports the file format."""
        pass


class ExtractorInterface(ABC):
    """Base interface for data extractors."""
    
    @abstractmethod
    def extract(self, text: str, template: ExtractionTemplate) -> ExtractionResult:
        """Extract structured data from text using template."""
        pass


class ExporterInterface(ABC):
    """Base interface for data exporters."""
    
    @abstractmethod
    def export(self, session: ProcessingSession, output_path: str) -> bool:
        """Export processing session results to file."""
        pass


class TemplateManagerInterface(ABC):
    """Base interface for template management."""
    
    @abstractmethod
    def save_template(self, template: ExtractionTemplate) -> bool:
        """Save extraction template."""
        pass
    
    @abstractmethod
    def load_template(self, name: str) -> Optional[ExtractionTemplate]:
        """Load extraction template by name."""
        pass
    
    @abstractmethod
    def list_templates(self) -> List[str]:
        """List available template names."""
        pass
    
    @abstractmethod
    def delete_template(self, name: str) -> bool:
        """Delete template by name."""
        pass


class CredentialManagerInterface(ABC):
    """Base interface for credential management."""
    
    @abstractmethod
    def save_api_key(self, key: str) -> bool:
        """Save API key securely."""
        pass
    
    @abstractmethod
    def load_api_key(self) -> Optional[str]:
        """Load stored API key."""
        pass
    
    @abstractmethod
    def validate_api_key(self, key: str) -> bool:
        """Validate API key by testing access."""
        pass
    
    @abstractmethod
    def delete_api_key(self) -> bool:
        """Delete stored API key."""
        pass


class ProofreaderInterface(ABC):
    """Base interface for text proofreading."""
    
    @abstractmethod
    def proofread(self, text: str) -> str:
        """Proofread and correct Vietnamese text."""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if proofreading is enabled."""
        pass
    
    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable proofreading."""
        pass