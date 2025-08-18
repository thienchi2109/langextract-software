# Implementation Plan

- [x] 1. Set up project structure and core interfaces
  - Create directory structure for gui/, core/, and assets/ components
  - Define base interfaces and data classes for templates, results, and configuration
  - Set up logging configuration and error handling framework
  - _Requirements: 10.1, 10.3_

- [x] 2. Implement secure credential management
  - Create KeychainManager class using Windows Credential Manager
  - Implement API key storage, retrieval, and deletion methods
  - Add API key validation by testing Gemini API access
  - Write unit tests for credential security functionality
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 3. Create configuration and template management system
  - Implement AppConfig dataclass with default settings
  - Create TemplateManager for saving/loading extraction templates as JSON
  - Add template validation and error handling for corrupted templates
  - Write unit tests for configuration and template operations
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 4. Build PII masking system
  - Create PIIMasker class with regex patterns for Vietnamese PII formats
  - Implement masking methods for account numbers, ID numbers, emails, and phone numbers
  - Add mask_for_cloud method that applies all masking rules while preserving context
  - Write comprehensive unit tests for all PII masking patterns
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 5. Implement document ingestion system
  - Create Ingestor class with format detection capabilities
  - Implement PDF text extraction using PyMuPDF with fallback detection
  - Add DOCX text extraction using python-docx for paragraphs and tables
  - Implement Excel processing with table-to-text conversion for natural language
  - Write unit tests for each document format processing
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 6. Build OCR engine integration
  - Create OCREngine class with EasyOCR initialization for Vietnamese and English
  - Implement PDF page-to-image conversion for scanned documents
  - Add OCR text extraction with configurable DPI and confidence settings
  - Create model download management for first-time setup
  - Write unit tests for OCR functionality with sample images
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 7. Implement Gemini API integration for proofreading
  - Create Proofreader class with Gemini API client setup
  - Implement Vietnamese text correction with system prompts
  - Add enable/disable toggle for offline processing mode
  - Integrate PII masking before sending text to API
  - Write unit tests with mocked API responses
  - _Requirements: 4.2, 8.3_

- [x] 8. Build langextract integration for data extraction
  - Create Extractor class using langextract library with Gemini backend
  - Implement dynamic schema processing from template configuration
  - Add extraction result validation and error handling
  - Integrate with PII masking for cloud processing
  - Write unit tests for extraction with sample templates and text
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 9. Create data aggregation and validation system
  - Implement Aggregator class for collecting and validating extraction results
  - Add data type conversion and validation based on schema field types
  - Create summary statistics calculation for aggregated data
  - Implement error collection and reporting per file
  - Write unit tests for data aggregation and validation logic
  - _Requirements: 5.5, 10.2_

- [ ] 10. Build Excel export functionality
  - Create ExcelExporter class using pandas and xlsxwriter
  - Implement Data sheet generation with schema-ordered columns
  - Add Summary sheet creation with grouping and aggregation
  - Implement Excel formatting with frozen headers and auto-fit columns
  - Write unit tests for Excel generation with sample data
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 11. Create main window GUI framework
  - Implement MainWindow class using PySide6 with drag-drop interface
  - Add file list display with format detection and status indicators
  - Create progress tracking with cancellation support
  - Implement basic menu structure and toolbar
  - Write GUI tests for main window functionality
  - _Requirements: 1.1, 1.2, 1.4_

- [ ] 12. Build schema editor interface
  - Create SchemaEditor dialog for dynamic field configuration
  - Implement add/edit/delete field functionality with validation
  - Add data type selection (text/number/date/currency) with locale options
  - Create field description and optional flag configuration
  - Write GUI tests for schema editing operations
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 13. Implement preview panel functionality
  - Create PreviewPanel widget for displaying extraction results
  - Add per-file preview with extracted data and confidence scores
  - Implement summary preview with aggregated statistics
  - Add highlighting for missing or low-confidence extractions
  - Write GUI tests for preview functionality
  - _Requirements: 5.5_

- [ ] 14. Create settings and security dialogs
  - Implement SettingsDialog for OCR, API, and processing configuration
  - Add API key management interface with secure input and validation
  - Create privacy warning banners for cloud processing features
  - Implement offline mode toggle with feature restrictions
  - Write GUI tests for settings and security interfaces
  - _Requirements: 8.1, 8.2, 8.3, 9.1, 9.3_

- [ ] 15. Build processing pipeline orchestration
  - Create ProcessingOrchestrator to coordinate all processing steps
  - Implement multi-threaded file processing with progress reporting
  - Add error handling and recovery for failed files
  - Create cancellation support for long-running operations
  - Write integration tests for complete processing pipeline
  - _Requirements: 10.1, 10.2, 10.5_

- [ ] 16. Implement template management UI
  - Add template save/load functionality to schema editor
  - Create template gallery interface for browsing saved templates
  - Implement template import/export with validation
  - Add template deletion with confirmation dialogs
  - Write GUI tests for template management operations
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 17. Add comprehensive error handling and logging
  - Implement structured logging with PII masking in log messages
  - Add user-friendly error dialogs with actionable suggestions
  - Create error recovery mechanisms for common failure scenarios
  - Implement log file rotation and cleanup
  - Write tests for error handling and logging functionality
  - _Requirements: 10.1, 10.3, 10.4_

- [ ] 18. Build application packaging and deployment
  - Create PyInstaller configuration for Windows executable
  - Add EasyOCR model bundling for offline installation
  - Implement first-run setup wizard for model downloads and API configuration
  - Create installer with proper Windows integration
  - Test deployment on clean Windows 10/11 systems
  - _Requirements: 3.4, 9.1_

- [ ] 19. Implement performance optimizations
  - Add multi-threading for file processing and API calls
  - Implement memory management for large document processing
  - Add progress reporting and cancellation for long operations
  - Optimize OCR processing with configurable quality settings
  - Write performance tests and benchmarking
  - _Requirements: 10.5_

- [ ] 20. Create comprehensive test suite and validation
  - Build test data set with various document formats and content types
  - Implement end-to-end integration tests for complete workflows
  - Add accuracy validation against manually labeled ground truth data
  - Create performance benchmarks for throughput and memory usage
  - Write user acceptance test scenarios and validation scripts
  - _Requirements: 10.4, 10.5_