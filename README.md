# Automated Report Extraction System

A Windows desktop application for extracting structured data from various document formats using OCR and AI-powered extraction.

## Project Structure

```
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── gui/                   # GUI components
│   └── __init__.py
├── core/                  # Core processing components
│   ├── __init__.py
│   ├── models.py          # Data models and interfaces
│   ├── logging_config.py  # Logging configuration
│   ├── exceptions.py      # Error handling framework
│   └── utils.py           # Utility functions
└── assets/                # Assets and resources
    └── __init__.py
```

## Core Components

### Data Models (`core/models.py`)
- `ExtractionField`: Configuration for extraction fields
- `ExtractionTemplate`: Template for data extraction
- `ExtractionResult`: Results from processing a single file
- `ProcessingSession`: Complete processing session data
- `AppConfig`: Application configuration settings

### Base Interfaces
- `ProcessorInterface`: Base for document processors
- `ExtractorInterface`: Base for data extractors
- `ExporterInterface`: Base for data exporters
- `TemplateManagerInterface`: Base for template management
- `CredentialManagerInterface`: Base for credential management

### Error Handling (`core/exceptions.py`)
- Custom exception hierarchy with error categories
- User-friendly error messages with suggestions
- Structured error logging with PII masking

### Logging (`core/logging_config.py`)
- PII masking in log messages
- Structured JSON logging option
- Rotating log files with configurable size limits
- Context-aware logging

### Utilities (`core/utils.py`)
- Configuration management
- File path validation
- File type detection
- Safe JSON operations

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```

## Configuration

The application stores configuration and data in:
- Windows: `%USERPROFILE%\AppData\Local\LangExtractor\`

## Features

- Support for PDF, DOCX, Excel document formats
- OCR processing for scanned documents (Vietnamese/English)
- AI-powered data extraction using Gemini API
- PII masking for privacy protection
- Template-based extraction configuration
- Excel export with formatted output
- Comprehensive error handling and logging