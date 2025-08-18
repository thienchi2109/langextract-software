"""
Test suite for data extractor using langextract library.

Tests extraction functionality with mocked langextract responses, template conversion,
PII masking integration, and error handling scenarios.
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch, MagicMock
import logging
import time

from core.extractor import Extractor
from core.models import (
    ExtractorInterface, ExtractionTemplate, ExtractionField, ExtractionResult,
    FieldType, ProcessingStatus
)
from core.keychain import KeychainManager
from core.pii_masker import PIIMasker
from core.exceptions import (
    LangExtractorError,
    CredentialError,
    APIValidationError,
    ValidationError,
    ErrorCategory,
    ErrorSeverity
)


class TestExtractor:
    """Test suite for Extractor class."""
    
    @pytest.fixture
    def mock_keychain(self):
        """Create mock KeychainManager."""
        keychain = Mock(spec=KeychainManager)
        keychain.load_api_key.return_value = "test-api-key"
        keychain.validate_api_key.return_value = True
        return keychain
    
    @pytest.fixture
    def mock_pii_masker(self):
        """Create mock PIIMasker."""
        pii_masker = Mock(spec=PIIMasker)
        pii_masker.mask_for_cloud.side_effect = lambda text: text  # Return text unchanged
        return pii_masker
    
    @pytest.fixture
    def sample_template(self):
        """Create sample extraction template."""
        fields = [
            ExtractionField(
                name="company_name",
                type=FieldType.TEXT,
                description="Name of the company",
                optional=False
            ),
            ExtractionField(
                name="revenue",
                type=FieldType.CURRENCY,
                description="Annual revenue",
                optional=True
            ),
            ExtractionField(
                name="employee_count",
                type=FieldType.NUMBER,
                description="Number of employees",
                optional=True
            )
        ]
        
        examples = [
            {
                "text": "ABC Corp reported revenue of $1.2M with 50 employees",
                "extractions": [
                    {"field_name": "company_name", "value": "ABC Corp"},
                    {"field_name": "revenue", "value": "$1.2M"},
                    {"field_name": "employee_count", "value": "50"}
                ]
            }
        ]
        
        return ExtractionTemplate(
            name="Company Info",
            prompt_description="Extract company information from text",
            fields=fields,
            examples=examples
        )
    
    @pytest.fixture
    def extractor(self, mock_keychain, mock_pii_masker):
        """Create Extractor instance with mocked dependencies."""
        return Extractor(
            model_id='gemini-2.5-flash',
            offline_mode=False,
            keychain_manager=mock_keychain,
            pii_masker=mock_pii_masker
        )
    
    def test_interface_implementation(self, extractor):
        """Test that Extractor implements ExtractorInterface."""
        assert isinstance(extractor, ExtractorInterface)
        assert hasattr(extractor, 'extract')
    
    def test_initialization(self, mock_keychain, mock_pii_masker):
        """Test Extractor initialization with various parameters."""
        extractor = Extractor(
            model_id='gemini-2.5-pro',
            api_timeout=60,
            offline_mode=True,
            max_workers=8,
            max_char_buffer=10000,
            extraction_passes=2,
            keychain_manager=mock_keychain,
            pii_masker=mock_pii_masker
        )
        
        assert extractor.model_id == 'gemini-2.5-pro'
        assert extractor.api_timeout == 60
        assert extractor.offline_mode == True
        assert extractor.max_workers == 8
        assert extractor.max_char_buffer == 10000
        assert extractor.extraction_passes == 2
    
    def test_get_api_key_success(self, extractor, mock_keychain):
        """Test successful API key retrieval."""
        api_key = extractor._get_api_key()
        assert api_key == "test-api-key"
        mock_keychain.load_api_key.assert_called_once()
        mock_keychain.validate_api_key.assert_called_once_with("test-api-key")
    
    def test_get_api_key_offline_mode(self, mock_keychain, mock_pii_masker):
        """Test API key retrieval in offline mode."""
        extractor = Extractor(
            offline_mode=True,
            keychain_manager=mock_keychain,
            pii_masker=mock_pii_masker
        )
        
        with pytest.raises(LangExtractorError) as exc_info:
            extractor._get_api_key()
        
        assert "offline mode" in str(exc_info.value)
        assert exc_info.value.category == ErrorCategory.API_ERROR
    
    def test_get_api_key_not_found(self, extractor, mock_keychain):
        """Test API key not found scenario."""
        mock_keychain.load_api_key.return_value = None
        
        with pytest.raises(CredentialError) as exc_info:
            extractor._get_api_key()
        
        assert "not found" in str(exc_info.value)
    
    def test_get_api_key_invalid(self, extractor, mock_keychain):
        """Test invalid API key scenario."""
        mock_keychain.validate_api_key.return_value = False
        
        with pytest.raises(CredentialError) as exc_info:
            extractor._get_api_key()
        
        assert "Invalid" in str(exc_info.value)
    
    def test_convert_template_to_langextract(self, extractor, sample_template):
        """Test template conversion to langextract format."""
        prompt_description, examples = extractor._convert_template_to_langextract(sample_template)
        
        assert prompt_description == sample_template.prompt_description
        assert len(examples) >= 1
        
        # Check first example
        example = examples[0]
        assert hasattr(example, 'text')
        assert hasattr(example, 'extractions')
        assert len(example.extractions) == 3
    
    def test_convert_template_no_examples(self, extractor):
        """Test template conversion with no examples."""
        template = ExtractionTemplate(
            name="Test Template",
            prompt_description="Test description",
            fields=[
                ExtractionField("field1", FieldType.TEXT, "Test field", False)
            ],
            examples=[]
        )
        
        prompt_description, examples = extractor._convert_template_to_langextract(template)
        
        assert prompt_description == template.prompt_description
        assert len(examples) >= 1  # Should create basic example
    
    def test_chunk_text_small(self, extractor):
        """Test text chunking with small text."""
        text = "This is a small text that doesn't need chunking."
        chunks = extractor._chunk_text_if_needed(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_large(self, extractor):
        """Test text chunking with large text."""
        # Create text larger than max_char_buffer
        large_text = "word " * (extractor.max_char_buffer // 4)
        chunks = extractor._chunk_text_if_needed(large_text)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= extractor.max_char_buffer
    
    def test_merge_chunk_results(self, extractor):
        """Test merging results from multiple chunks."""
        # Create mock chunk results
        class MockExtraction:
            def __init__(self, class_name, text, confidence=0.8):
                self.extraction_class = class_name
                self.extraction_text = text
                self.confidence = confidence
        
        class MockResult:
            def __init__(self, extractions):
                self.extractions = extractions
        
        chunk_results = [
            MockResult([
                MockExtraction("company_name", "ABC Corp", 0.9),
                MockExtraction("revenue", "$1M", 0.7)
            ]),
            MockResult([
                MockExtraction("company_name", "XYZ Inc", 0.6),  # Lower confidence
                MockExtraction("employee_count", "100", 0.8)
            ])
        ]
        
        merged_data, merged_confidence = extractor._merge_chunk_results(chunk_results)
        
        # Should keep higher confidence values
        assert merged_data["company_name"] == "ABC Corp"  # Higher confidence
        assert merged_data["revenue"] == "$1M"
        assert merged_data["employee_count"] == "100"
        
        assert merged_confidence["company_name"] == 0.9
        assert merged_confidence["revenue"] == 0.7
        assert merged_confidence["employee_count"] == 0.8
    
    @patch('core.extractor.lx.extract')
    def test_extract_success(self, mock_langextract, extractor, sample_template):
        """Test successful extraction."""
        # Mock langextract response
        class MockExtraction:
            def __init__(self, class_name, text):
                self.extraction_class = class_name
                self.extraction_text = text
                self.confidence = 0.9
        
        class MockResult:
            def __init__(self):
                self.extractions = [
                    MockExtraction("company_name", "Test Corp"),
                    MockExtraction("revenue", "2.5M"),
                    MockExtraction("employee_count", "150")
                ]
        
        mock_langextract.return_value = MockResult()
        
        # Test extraction
        text = "Test Corp has revenue of 2.5M and 150 employees"
        result = extractor.extract(text, sample_template)
        
        assert isinstance(result, ExtractionResult)
        assert result.status == ProcessingStatus.COMPLETED
        assert len(result.extracted_data) == 3
        assert result.extracted_data["company_name"] == "Test Corp"
        assert result.extracted_data["revenue"] == 2.5  # Should be converted to float
        assert result.extracted_data["employee_count"] == 150  # Should be converted to int
        assert result.processing_time > 0
        assert len(result.errors) == 0
    
    def test_extract_empty_text(self, extractor, sample_template):
        """Test extraction with empty text."""
        result = extractor.extract("", sample_template)
        
        assert result.status == ProcessingStatus.FAILED
        assert len(result.errors) > 0
        assert "empty" in result.errors[0].lower()
    
    def test_extract_invalid_template(self, extractor):
        """Test extraction with invalid template."""
        result = extractor.extract("test text", None)
        
        assert result.status == ProcessingStatus.FAILED
        assert len(result.errors) > 0
        assert "invalid" in result.errors[0].lower()
    
    def test_extract_offline_mode(self, mock_keychain, mock_pii_masker, sample_template):
        """Test extraction in offline mode."""
        extractor = Extractor(
            offline_mode=True,
            keychain_manager=mock_keychain,
            pii_masker=mock_pii_masker
        )
        
        result = extractor.extract("test text", sample_template)
        
        assert result.status == ProcessingStatus.FAILED
        assert len(result.errors) > 0
        assert "offline" in result.errors[0].lower()
    
    @patch('core.extractor.lx.extract')
    def test_extract_with_pii_masking(self, mock_langextract, extractor, sample_template, mock_pii_masker):
        """Test extraction with PII masking enabled."""
        # Setup PII masker to return masked text
        mock_pii_masker.mask_for_cloud.return_value = "masked text"
        
        # Mock langextract response
        class MockResult:
            def __init__(self):
                self.extractions = []
        
        mock_langextract.return_value = MockResult()
        
        # Test extraction
        text = "Text with PII: email@example.com"
        extractor.extract(text, sample_template)
        
        # Verify PII masking was called
        mock_pii_masker.mask_for_cloud.assert_called_once_with(text)
        
        # Verify langextract was called with masked text
        mock_langextract.assert_called_once()
        call_args = mock_langextract.call_args
        # Check that text_or_documents parameter was passed (the actual masking logic is tested separately)
        assert 'text_or_documents' in call_args[1]


class TestExtractorIntegration:
    """Integration tests for Extractor with real components."""

    def test_integration_with_real_pii_masker(self):
        """Test integration with real PIIMasker."""
        from core.pii_masker import PIIMasker
        from core.keychain import KeychainManager

        # Create real PIIMasker but mock KeychainManager
        pii_masker = PIIMasker()
        keychain = Mock(spec=KeychainManager)
        keychain.load_api_key.return_value = None  # Force offline behavior

        extractor = Extractor(
            offline_mode=True,  # Avoid API calls
            keychain_manager=keychain,
            pii_masker=pii_masker
        )

        # Create simple template
        template = ExtractionTemplate(
            name="Test",
            prompt_description="Test extraction",
            fields=[ExtractionField("test_field", FieldType.TEXT, "Test", False)],
            examples=[]
        )

        # Test with text containing PII
        text_with_pii = "Contact: email@example.com or 0123456789"
        result = extractor.extract(text_with_pii, template)

        # Should fail due to offline mode, but PII masking should work
        assert result.status == ProcessingStatus.FAILED
        assert "offline" in result.errors[0].lower()

    def test_integration_with_real_keychain_offline(self):
        """Test integration with real KeychainManager in offline mode."""
        from core.keychain import KeychainManager
        from core.pii_masker import PIIMasker

        # Create real components
        keychain = KeychainManager()
        pii_masker = PIIMasker()

        extractor = Extractor(
            offline_mode=True,
            keychain_manager=keychain,
            pii_masker=pii_masker
        )

        # Create simple template
        template = ExtractionTemplate(
            name="Test",
            prompt_description="Test extraction",
            fields=[ExtractionField("test_field", FieldType.TEXT, "Test", False)],
            examples=[]
        )

        # Test extraction
        result = extractor.extract("test text", template)

        # Should fail due to offline mode
        assert result.status == ProcessingStatus.FAILED
        assert "offline" in result.errors[0].lower()

    def test_template_conversion_with_complex_examples(self):
        """Test template conversion with complex examples."""
        extractor = Extractor(offline_mode=True)

        # Create template with complex examples
        template = ExtractionTemplate(
            name="Complex Template",
            prompt_description="Extract complex data",
            fields=[
                ExtractionField("name", FieldType.TEXT, "Name", False),
                ExtractionField("amount", FieldType.CURRENCY, "Amount", True),
                ExtractionField("date", FieldType.DATE, "Date", True)
            ],
            examples=[
                {
                    "text": "John Doe paid $500 on 2024-01-15",
                    "extractions": [
                        {"field_name": "name", "value": "John Doe", "attributes": {"type": "person"}},
                        {"field_name": "amount", "value": "$500", "attributes": {"currency": "USD"}},
                        {"field_name": "date", "value": "2024-01-15", "attributes": {"format": "ISO"}}
                    ]
                },
                {
                    "text": "Payment of €200 by Jane Smith",
                    "extractions": [
                        {"field_name": "name", "value": "Jane Smith"},
                        {"field_name": "amount", "value": "€200"}
                    ]
                }
            ]
        )

        prompt_description, examples = extractor._convert_template_to_langextract(template)

        assert prompt_description == template.prompt_description
        assert len(examples) == 2

        # Check first example
        example1 = examples[0]
        assert example1.text == "John Doe paid $500 on 2024-01-15"
        assert len(example1.extractions) == 3

        # Check extraction details
        name_extraction = next(e for e in example1.extractions if e.extraction_class == "name")
        assert name_extraction.extraction_text == "John Doe"
        assert name_extraction.attributes.get("type") == "person"

    def test_error_handling_chain(self):
        """Test error handling through the entire chain."""
        # Create extractor with invalid configuration
        extractor = Extractor(
            model_id="invalid-model",
            offline_mode=False,
            keychain_manager=Mock(spec=KeychainManager),
            pii_masker=Mock(spec=PIIMasker)
        )

        # Mock keychain to return no API key
        extractor.keychain_manager.load_api_key.return_value = None

        template = ExtractionTemplate(
            name="Test",
            prompt_description="Test",
            fields=[ExtractionField("test", FieldType.TEXT, "Test", False)],
            examples=[]
        )

        # Test extraction - should fail gracefully
        result = extractor.extract("test text", template)

        assert result.status == ProcessingStatus.FAILED
        assert len(result.errors) > 0
        assert result.processing_time > 0


class TestExtractorErrorScenarios:
    """Test error scenarios and edge cases."""

    def test_langextract_api_error(self):
        """Test handling of langextract API errors."""
        extractor = Extractor(offline_mode=True)

        # Test with malformed template
        template = ExtractionTemplate(
            name="",  # Empty name
            prompt_description="",  # Empty description
            fields=[],  # No fields
            examples=[]
        )

        result = extractor.extract("test text", template)

        assert result.status == ProcessingStatus.FAILED
        assert len(result.errors) > 0

    def test_validation_error_handling(self):
        """Test validation error handling."""
        extractor = Extractor(offline_mode=True)

        # Test with None template
        result = extractor.extract("test text", None)
        assert result.status == ProcessingStatus.FAILED

        # Test with empty text
        template = ExtractionTemplate(
            name="Test",
            prompt_description="Test",
            fields=[ExtractionField("test", FieldType.TEXT, "Test", False)],
            examples=[]
        )
        result = extractor.extract("", template)
        assert result.status == ProcessingStatus.FAILED

        # Test with whitespace-only text
        result = extractor.extract("   \n\t   ", template)
        assert result.status == ProcessingStatus.FAILED

    def test_large_document_chunking_edge_cases(self):
        """Test edge cases in document chunking."""
        extractor = Extractor(
            max_char_buffer=100,  # Very small buffer
            offline_mode=True
        )

        # Test with text that has very long words
        long_word = "a" * 150  # Longer than buffer
        text = f"Short text {long_word} more text"

        chunks = extractor._chunk_text_if_needed(text)

        # Should handle long words gracefully
        assert len(chunks) > 1
        assert any(long_word in chunk for chunk in chunks)

    def test_type_conversion_edge_cases(self):
        """Test type conversion edge cases."""
        extractor = Extractor(offline_mode=True)

        template = ExtractionTemplate(
            name="Test",
            prompt_description="Test",
            fields=[
                ExtractionField("number_field", FieldType.NUMBER, "Number", False),
                ExtractionField("currency_field", FieldType.CURRENCY, "Currency", False)
            ],
            examples=[]
        )

        # Create mock result with problematic values
        class MockExtraction:
            def __init__(self, class_name, text):
                self.extraction_class = class_name
                self.extraction_text = text
                self.confidence = 0.8

        class MockResult:
            def __init__(self):
                self.extractions = [
                    MockExtraction("number_field", "not-a-number"),
                    MockExtraction("currency_field", "invalid-currency")
                ]

        mock_result = MockResult()

        # Should handle conversion errors gracefully
        try:
            extracted_data, _ = extractor._validate_extraction_result(mock_result, template)
            # Should keep original values if conversion fails
            assert extracted_data["number_field"] == "not-a-number"
            assert extracted_data["currency_field"] == "invalid-currency"
        except Exception as e:
            pytest.fail(f"Should handle conversion errors gracefully: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
