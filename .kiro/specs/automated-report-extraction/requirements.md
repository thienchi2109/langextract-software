# Requirements Document

## Introduction

This document outlines the requirements for an automated report extraction software that provides a Windows GUI application for importing various document formats (PDF, DOCX, Excel), configuring dynamic extraction schemas, and generating consolidated Excel reports using langextract and OCR technologies. The system aims to reduce manual report processing time while maintaining data consistency across heterogeneous content sources, with a focus on user-friendly operation for non-technical users.

## Requirements

### Requirement 1

**User Story:** As a business user, I want to import multiple document formats through a drag-and-drop interface, so that I can process various report types without technical complexity.

#### Acceptance Criteria

1. WHEN the user drags files into the application THEN the system SHALL accept PDF, DOCX, XLSX/XLS, and optionally CSV formats
2. WHEN the user clicks "Choose files" button THEN the system SHALL open a file browser dialog supporting multiple file selection
3. WHEN unsupported file formats are imported THEN the system SHALL display clear error messages and skip those files
4. WHEN files are successfully imported THEN the system SHALL display a list of imported files with their formats and status

### Requirement 2

**User Story:** As a data analyst, I want to configure dynamic extraction schemas with field names, descriptions, and data types, so that I can customize extraction for different report types without hardcoded structures.

#### Acceptance Criteria

1. WHEN the user accesses schema configuration THEN the system SHALL provide fields for name, description/context, and data type selection (text/number/date/currency)
2. WHEN the user adds a new field THEN the system SHALL allow specifying field properties and validation rules
3. WHEN the user modifies existing fields THEN the system SHALL update the schema configuration immediately
4. WHEN the user deletes fields THEN the system SHALL remove them from the extraction schema with confirmation
5. WHEN invalid schema configurations are detected THEN the system SHALL display validation errors before processing

### Requirement 3

**User Story:** As a document processor, I want OCR capabilities for scanned PDFs in Vietnamese and English, so that I can extract text from image-based documents.

#### Acceptance Criteria

1. WHEN a PDF contains scanned images THEN the system SHALL use EasyOCR with Vietnamese and English language support
2. WHEN OCR is enabled THEN the system SHALL process documents at 300+ DPI for optimal text recognition
3. WHEN OCR processing fails THEN the system SHALL log errors and continue with available text content
4. WHEN OCR is disabled THEN the system SHALL only extract existing text content from documents

### Requirement 4

**User Story:** As a compliance officer, I want PII masking enabled by default before sending data to external APIs, so that sensitive information is protected during cloud processing.

#### Acceptance Criteria

1. WHEN PII masking is enabled THEN the system SHALL automatically mask account numbers, ID numbers, emails, and phone numbers
2. WHEN text is sent to Gemini API THEN the system SHALL apply PII masking to protect sensitive data
3. WHEN PII masking is applied THEN the system SHALL preserve enough context for accurate extraction
4. WHEN users disable online features THEN the system SHALL process documents completely offline without external API calls

### Requirement 5

**User Story:** As a report generator, I want to extract data using langextract with Gemini API according to my configured schema, so that I can get structured data from unstructured documents.

#### Acceptance Criteria

1. WHEN extraction is initiated THEN the system SHALL use langextract with the configured schema and examples
2. WHEN Gemini API is called THEN the system SHALL send masked text content for processing
3. WHEN extraction completes THEN the system SHALL return structured data matching the schema format
4. WHEN extraction fails THEN the system SHALL log errors per file and continue processing remaining files
5. WHEN preview is requested THEN the system SHALL display extraction results per file and aggregated summary

### Requirement 6

**User Story:** As an end user, I want to export results only to Excel format with proper formatting, so that I can use the data in standard business tools.

#### Acceptance Criteria

1. WHEN export is initiated THEN the system SHALL generate Excel (.xlsx) files only
2. WHEN Excel is generated THEN the system SHALL create a "Data" sheet with extracted information in schema order
3. WHEN summary is requested THEN the system SHALL create a "Summary" sheet with aggregated data by selected grouping field
4. WHEN Excel is formatted THEN the system SHALL include frozen headers, auto-fit columns, and proper data type formatting
5. WHEN export completes THEN the system SHALL save the file to user-specified location

### Requirement 7

**User Story:** As a frequent user, I want to save and load extraction templates, so that I can reuse configurations for similar document types.

#### Acceptance Criteria

1. WHEN template is saved THEN the system SHALL store schema configuration, parser parameters, and OCR settings as JSON
2. WHEN template is loaded THEN the system SHALL restore all configuration settings from the saved template
3. WHEN templates are managed THEN the system SHALL provide options to create, edit, delete, and duplicate templates
4. WHEN template format is invalid THEN the system SHALL display error messages and prevent loading

### Requirement 8

**User Story:** As a security-conscious user, I want clear warnings when data will be sent to external services, so that I can make informed decisions about data privacy.

#### Acceptance Criteria

1. WHEN online features are enabled THEN the system SHALL display a banner warning that text will be sent externally
2. WHEN first using Gemini features THEN the system SHALL require explicit user consent before proceeding
3. WHEN offline mode is selected THEN the system SHALL process documents entirely locally without network calls
4. WHEN API key is required THEN the system SHALL securely store credentials using Windows Credential Manager

### Requirement 9

**User Story:** As a system administrator, I want secure API key management, so that credentials are protected and can be updated when needed.

#### Acceptance Criteria

1. WHEN API key is entered THEN the system SHALL validate the key by testing Gemini API access
2. WHEN API key is saved THEN the system SHALL store it securely using Windows Credential Manager/DPAPI
3. WHEN API key needs updating THEN the system SHALL provide options to change or delete stored credentials
4. WHEN API key is invalid THEN the system SHALL display clear error messages and request re-entry

### Requirement 10

**User Story:** As a data processor, I want comprehensive error handling and logging, so that I can troubleshoot issues and understand processing failures.

#### Acceptance Criteria

1. WHEN files cannot be processed THEN the system SHALL log specific error messages per file
2. WHEN data extraction fails THEN the system SHALL continue processing remaining files and report failures
3. WHEN errors occur THEN the system SHALL display user-friendly messages without exposing sensitive content
4. WHEN logging is active THEN the system SHALL create minimized logs without storing sensitive document content
5. WHEN processing completes THEN the system SHALL provide a summary of successful and failed operations