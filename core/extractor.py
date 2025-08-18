"""
Data extractor using langextract library with Gemini backend.

This module provides the Extractor class that handles structured data extraction
from text using AI-powered extraction with PII masking and validation.
"""

import logging
import time
from typing import Optional, Dict, Any, List
import langextract as lx

from .models import ExtractorInterface, ExtractionTemplate, ExtractionResult, FieldType, ProcessingStatus
from .keychain import KeychainManager
from .pii_masker import PIIMasker
from .exceptions import (
    LangExtractorError,
    ErrorCategory,
    ErrorSeverity,
    APIValidationError,
    CredentialError,
    ValidationError
)

logger = logging.getLogger(__name__)


class Extractor(ExtractorInterface):
    """
    Data extractor using langextract library with Gemini backend.
    
    Provides structured data extraction from text using AI models with:
    - Dynamic schema processing from templates
    - PII masking for cloud processing
    - Comprehensive error handling and validation
    - Performance optimization for large documents
    """
    
    def __init__(
        self,
        model_id: str = 'gemini-2.5-flash',
        api_timeout: int = 30,
        offline_mode: bool = False,
        max_workers: int = 4,
        max_char_buffer: int = 8000,
        extraction_passes: int = 1,
        keychain_manager: Optional[KeychainManager] = None,
        pii_masker: Optional[PIIMasker] = None
    ):
        """
        Initialize data extractor.
        
        Args:
            model_id: Gemini model to use (default: 'gemini-2.5-flash')
            api_timeout: API request timeout in seconds (default: 30)
            offline_mode: Disable API calls for offline processing (default: False)
            max_workers: Maximum parallel workers for large documents (default: 4)
            max_char_buffer: Maximum characters per chunk (default: 8000)
            extraction_passes: Number of extraction passes for better recall (default: 1)
            keychain_manager: Credential manager instance (optional)
            pii_masker: PII masker instance (optional)
        """
        self.model_id = model_id
        self.api_timeout = api_timeout
        self.offline_mode = offline_mode
        self.max_workers = max_workers
        self.max_char_buffer = max_char_buffer
        self.extraction_passes = extraction_passes
        
        # Initialize dependencies
        self.keychain_manager = keychain_manager or KeychainManager()
        self.pii_masker = pii_masker or PIIMasker()
        
        # Initialize logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Cache for API key
        self._api_key = None
        
        self.logger.info(f"Extractor initialized with model: {self.model_id}")
    
    def _get_api_key(self) -> str:
        """
        Get API key with caching and validation.
        
        Returns:
            str: Valid API key
            
        Raises:
            CredentialError: If API key is not available or invalid
        """
        if self._api_key is not None:
            return self._api_key
        
        if self.offline_mode:
            raise LangExtractorError(
                "Data extraction is disabled in offline mode",
                category=ErrorCategory.API_ERROR,
                severity=ErrorSeverity.LOW
            )
        
        try:
            # Load API key from keychain
            api_key = self.keychain_manager.load_api_key()
            if not api_key:
                raise CredentialError(
                    "Gemini API key not found. Please configure API key first."
                )
            
            # Validate API key
            if not self.keychain_manager.validate_api_key(api_key):
                raise CredentialError(
                    "Invalid Gemini API key. Please check your configuration."
                )
            
            self._api_key = api_key
            self.logger.info("API key loaded and validated successfully")
            return self._api_key
            
        except Exception as e:
            if isinstance(e, (CredentialError, LangExtractorError)):
                raise
            raise CredentialError(f"Failed to load API key: {str(e)}")
    
    def _convert_template_to_langextract(self, template: ExtractionTemplate) -> tuple:
        """
        Convert ExtractionTemplate to langextract format.
        
        Args:
            template: Extraction template configuration
            
        Returns:
            tuple: (prompt_description, examples) for langextract
            
        Raises:
            ValidationError: If template format is invalid
        """
        try:
            # Use template's prompt description
            prompt_description = template.prompt_description
            
            # Convert examples if available
            examples = []
            for example_data in template.examples:
                if not isinstance(example_data, dict):
                    continue
                
                # Extract text and extractions from example
                text = example_data.get('text', '')
                extractions_data = example_data.get('extractions', [])
                
                # Convert extractions to langextract format
                extractions = []
                for ext_data in extractions_data:
                    if isinstance(ext_data, dict):
                        extraction = lx.data.Extraction(
                            extraction_class=ext_data.get('field_name', 'unknown'),
                            extraction_text=ext_data.get('value', ''),
                            attributes=ext_data.get('attributes', {})
                        )
                        extractions.append(extraction)
                
                # Create langextract example
                if text and extractions:
                    example = lx.data.ExampleData(
                        text=text,
                        extractions=extractions
                    )
                    examples.append(example)
            
            # If no examples provided, create a basic example from field definitions
            if not examples:
                self.logger.warning("No examples found in template, creating basic example")
                # Create a minimal example based on field definitions
                sample_extractions = []
                for field in template.fields[:3]:  # Limit to first 3 fields
                    extraction = lx.data.Extraction(
                        extraction_class=field.name,
                        extraction_text=f"sample_{field.name}",
                        attributes={"type": field.type.value, "description": field.description}
                    )
                    sample_extractions.append(extraction)
                
                if sample_extractions:
                    example = lx.data.ExampleData(
                        text="Sample text for extraction",
                        extractions=sample_extractions
                    )
                    examples.append(example)
            
            self.logger.info(f"Converted template with {len(examples)} examples")
            return prompt_description, examples
            
        except Exception as e:
            raise ValidationError(
                f"Failed to convert template to langextract format: {str(e)}",
                details={"template_name": template.name}
            )
    
    def _validate_extraction_result(self, result: Any, template: ExtractionTemplate) -> Dict[str, Any]:
        """
        Validate and convert langextract result to our format.
        
        Args:
            result: Raw result from langextract
            template: Original extraction template
            
        Returns:
            Dict[str, Any]: Validated extracted data
            
        Raises:
            ValidationError: If result validation fails
        """
        try:
            extracted_data = {}
            confidence_scores = {}
            
            # Handle langextract result format
            if hasattr(result, 'extractions') and result.extractions:
                for extraction in result.extractions:
                    field_name = extraction.extraction_class
                    field_value = extraction.extraction_text
                    
                    # Find corresponding field in template
                    template_field = None
                    for field in template.fields:
                        if field.name == field_name:
                            template_field = field
                            break
                    
                    if template_field:
                        # Type conversion based on field type
                        try:
                            if template_field.type == FieldType.NUMBER:
                                # Try to convert to number
                                if '.' in field_value or ',' in field_value:
                                    field_value = float(field_value.replace(',', '.'))
                                else:
                                    field_value = int(field_value)
                            elif template_field.type == FieldType.CURRENCY:
                                # Extract numeric value from currency
                                import re
                                numeric_match = re.search(r'[\d,\.]+', field_value)
                                if numeric_match:
                                    field_value = float(numeric_match.group().replace(',', '.'))
                            # TEXT and DATE types keep as string for now
                            
                        except (ValueError, TypeError):
                            self.logger.warning(f"Failed to convert field {field_name} to {template_field.type}")
                            # Keep original value if conversion fails
                    
                    extracted_data[field_name] = field_value
                    
                    # Add confidence score if available
                    if hasattr(extraction, 'confidence'):
                        confidence_scores[field_name] = extraction.confidence
                    else:
                        confidence_scores[field_name] = 0.8  # Default confidence
            
            # Check for required fields
            for field in template.fields:
                if not field.optional and field.name not in extracted_data:
                    self.logger.warning(f"Required field '{field.name}' not found in extraction")
            
            self.logger.info(f"Validated extraction with {len(extracted_data)} fields")
            return extracted_data, confidence_scores
            
        except Exception as e:
            raise ValidationError(
                f"Failed to validate extraction result: {str(e)}",
                details={"template_name": template.name}
            )
    
    def _chunk_text_if_needed(self, text: str) -> List[str]:
        """
        Split large text into chunks if needed for better processing.

        Args:
            text: Input text to potentially chunk

        Returns:
            List[str]: List of text chunks
        """
        if len(text) <= self.max_char_buffer:
            return [text]

        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space

            if current_length + word_length > self.max_char_buffer and current_chunk:
                # Save current chunk and start new one
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length

        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        self.logger.info(f"Split text into {len(chunks)} chunks for processing")
        return chunks

    def _merge_chunk_results(self, chunk_results: List[Any]) -> tuple:
        """
        Merge results from multiple text chunks.

        Args:
            chunk_results: List of langextract results from chunks

        Returns:
            tuple: (merged_extracted_data, merged_confidence_scores)
        """
        merged_data = {}
        merged_confidence = {}

        for result in chunk_results:
            if hasattr(result, 'extractions') and result.extractions:
                for extraction in result.extractions:
                    field_name = extraction.extraction_class
                    field_value = extraction.extraction_text

                    # Merge strategy: keep highest confidence value
                    confidence = getattr(extraction, 'confidence', 0.8)

                    if field_name not in merged_data or merged_confidence.get(field_name, 0) < confidence:
                        merged_data[field_name] = field_value
                        merged_confidence[field_name] = confidence

        self.logger.info(f"Merged {len(chunk_results)} chunk results into {len(merged_data)} fields")
        return merged_data, merged_confidence

    def extract(self, text: str, template: ExtractionTemplate) -> ExtractionResult:
        """
        Extract structured data from text using template.

        Args:
            text: Input text to extract data from
            template: Extraction template configuration

        Returns:
            ExtractionResult: Extraction results with data and metadata

        Raises:
            LangExtractorError: If extraction fails
            ValidationError: If input validation fails
            APIValidationError: If API call fails
        """
        start_time = time.time()

        try:
            # Input validation
            if not isinstance(text, str) or not text.strip():
                raise ValidationError("Input text cannot be empty")

            if not isinstance(template, ExtractionTemplate):
                raise ValidationError("Invalid template format")

            if not template.fields:
                raise ValidationError("Template must have at least one field")

            self.logger.info(f"Starting extraction with template: {template.name}")

            # Apply PII masking before cloud processing
            if self.pii_masker and not self.offline_mode:
                self.logger.debug("Applying PII masking before API call")
                masked_text = self.pii_masker.mask_for_cloud(text)
            else:
                masked_text = text

            # Convert template to langextract format
            prompt_description, examples = self._convert_template_to_langextract(template)

            # Get API key
            api_key = self._get_api_key()

            # Check if text needs chunking for large documents
            text_chunks = self._chunk_text_if_needed(masked_text)

            if len(text_chunks) == 1:
                # Single chunk processing
                self.logger.info(f"Processing single chunk with model: {self.model_id}")

                result = lx.extract(
                    text_or_documents=masked_text,
                    prompt_description=prompt_description,
                    examples=examples,
                    model_id=self.model_id,
                    api_key=api_key,
                    max_workers=self.max_workers,
                    max_char_buffer=self.max_char_buffer,
                    extraction_passes=self.extraction_passes
                )

                # Validate and convert result
                extracted_data, confidence_scores = self._validate_extraction_result(result, template)
            else:
                # Multi-chunk processing
                self.logger.info(f"Processing {len(text_chunks)} chunks with model: {self.model_id}")

                chunk_results = []
                for i, chunk in enumerate(text_chunks):
                    self.logger.debug(f"Processing chunk {i+1}/{len(text_chunks)}")

                    chunk_result = lx.extract(
                        text_or_documents=chunk,
                        prompt_description=prompt_description,
                        examples=examples,
                        model_id=self.model_id,
                        api_key=api_key,
                        max_workers=1,  # Process chunks sequentially to avoid rate limits
                        max_char_buffer=self.max_char_buffer,
                        extraction_passes=1  # Single pass per chunk
                    )
                    chunk_results.append(chunk_result)

                # Merge results from all chunks
                raw_data, raw_confidence = self._merge_chunk_results(chunk_results)

                # Create a mock result object for validation
                class MockResult:
                    def __init__(self, data, confidence):
                        self.extractions = []
                        for field_name, value in data.items():
                            extraction = type('Extraction', (), {
                                'extraction_class': field_name,
                                'extraction_text': value,
                                'confidence': confidence.get(field_name, 0.8)
                            })()
                            self.extractions.append(extraction)

                mock_result = MockResult(raw_data, raw_confidence)
                extracted_data, confidence_scores = self._validate_extraction_result(mock_result, template)

            processing_time = time.time() - start_time

            # Create extraction result
            extraction_result = ExtractionResult(
                source_file="text_input",
                extracted_data=extracted_data,
                confidence_scores=confidence_scores,
                processing_time=processing_time,
                errors=[],
                status=ProcessingStatus.COMPLETED
            )

            self.logger.info(f"Extraction completed successfully in {processing_time:.2f}s")
            return extraction_result

        except Exception as e:
            processing_time = time.time() - start_time

            # Create failed result
            extraction_result = ExtractionResult(
                source_file="text_input",
                extracted_data={},
                confidence_scores={},
                processing_time=processing_time,
                errors=[str(e)],
                status=ProcessingStatus.FAILED
            )

            if isinstance(e, (LangExtractorError, ValidationError, APIValidationError)):
                self.logger.error(f"Extraction failed: {str(e)}")
                extraction_result.errors = [str(e)]
                return extraction_result
            else:
                self.logger.error(f"Unexpected error during extraction: {str(e)}")
                raise LangExtractorError(
                    f"Extraction failed: {str(e)}",
                    category=ErrorCategory.PROCESSING_ERROR,
                    severity=ErrorSeverity.HIGH
                )
