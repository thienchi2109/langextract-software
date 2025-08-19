"""
Test suite for Vietnamese text proofreader using Gemini API.

Tests proofreading functionality with mocked API responses, PII masking integration,
enable/disable functionality, and error handling scenarios.
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch, MagicMock
import logging
import time

from core.proofreader import Proofreader
from core.models import ProofreaderInterface
from core.keychain import KeychainManager
from core.pii_masker import PIIMasker
from core.exceptions import (
    LangExtractorError,
    CredentialError,
    APIValidationError,
    ErrorCategory,
    ErrorSeverity
)


class TestProofreader:
    """Test cases for the Proofreader class."""
    
    @pytest.fixture
    def mock_keychain(self):
        """Mock KeychainManager for testing."""
        keychain = Mock(spec=KeychainManager)
        keychain.load_api_key.return_value = "test_api_key_12345"
        keychain.validate_api_key.return_value = True
        return keychain
    
    @pytest.fixture
    def mock_pii_masker(self):
        """Mock PIIMasker for testing."""
        pii_masker = Mock(spec=PIIMasker)
        pii_masker.mask_for_cloud.return_value = "masked text"
        return pii_masker
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Mock Gemini API client."""
        mock_response = Mock()
        mock_response.text = "Corrected Vietnamese text"
        
        mock_client = Mock()
        mock_client.generate_content.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def proofreader(self, mock_keychain, mock_pii_masker):
        """Create Proofreader instance with mocked dependencies."""
        return Proofreader(
            enabled=True,
            offline_mode=False,
            keychain_manager=mock_keychain,
            pii_masker=mock_pii_masker
        )
    
    def test_interface_implementation(self, proofreader):
        """Test that Proofreader implements ProofreaderInterface."""
        assert isinstance(proofreader, ProofreaderInterface)
        
        # Test required methods exist
        assert hasattr(proofreader, 'proofread')
        assert hasattr(proofreader, 'is_enabled')
        assert hasattr(proofreader, 'set_enabled')
    
    def test_initialization_default_parameters(self):
        """Test Proofreader initialization with default parameters."""
        proofreader = Proofreader()
        
        assert proofreader.enabled is True
        assert proofreader.offline_mode is False
        assert proofreader.api_timeout == 30
        assert proofreader.correction_mode == 'auto'
        assert proofreader.model_name == 'gemini-2.5-pro'
        assert proofreader._client is None  # Lazy initialization
    
    def test_initialization_custom_parameters(self, mock_keychain, mock_pii_masker):
        """Test Proofreader initialization with custom parameters."""
        proofreader = Proofreader(
            enabled=False,
            offline_mode=True,
            api_timeout=60,
            correction_mode='business',
            model_name='gemini-2.5-pro',
            keychain_manager=mock_keychain,
            pii_masker=mock_pii_masker
        )
        
        assert proofreader.enabled is False
        assert proofreader.offline_mode is True
        assert proofreader.api_timeout == 60
        assert proofreader.correction_mode == 'business'
        assert proofreader.model_name == 'gemini-2.5-pro'
        assert proofreader.keychain_manager is mock_keychain
        assert proofreader.pii_masker is mock_pii_masker
    
    def test_system_prompts_configuration(self):
        """Test that all system prompts are correctly configured."""
        prompts = Proofreader.SYSTEM_PROMPTS
        
        assert 'minimal' in prompts
        assert 'business' in prompts
        assert 'number_lock' in prompts
        assert 'default' in prompts
        
        # Test minimal prompt content
        minimal_prompt = prompts['minimal']
        assert 'dấu tiếng Việt' in minimal_prompt
        assert 'TUYỆT ĐỐI KHÔNG' in minimal_prompt
        assert '[MASK]' in minimal_prompt
        
        # Test business prompt content
        business_prompt = prompts['business']
        assert 'báo cáo kinh doanh' in business_prompt
        assert 'không thay đổi dữ kiện' in business_prompt
        assert 'VND' in business_prompt
    
    @patch('core.proofreader.genai')
    def test_get_client_success(self, mock_genai, proofreader, mock_keychain):
        """Test successful Gemini API client initialization."""
        # Setup mock
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Test response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Test client initialization
        client = proofreader._get_client()
        
        assert client is mock_model
        assert proofreader._client is mock_model
        mock_keychain.load_api_key.assert_called_once()
        mock_genai.configure.assert_called_once_with(api_key="test_api_key_12345")
    
    @patch('core.proofreader.genai')
    def test_get_client_no_api_key(self, mock_genai, proofreader, mock_keychain):
        """Test client initialization failure when no API key is available."""
        mock_keychain.load_api_key.return_value = None
        
        with pytest.raises(CredentialError) as exc_info:
            proofreader._get_client()
        
        assert "API key not found" in str(exc_info.value)
        mock_genai.configure.assert_not_called()
    
    def test_get_client_offline_mode(self, proofreader):
        """Test that client initialization raises error in offline mode."""
        proofreader.offline_mode = True
        
        with pytest.raises(LangExtractorError) as exc_info:
            proofreader._get_client()
        
        assert "offline mode" in str(exc_info.value)
        assert exc_info.value.category == ErrorCategory.API_ERROR
    
    @patch('core.proofreader.genai')
    def test_get_client_api_test_failure(self, mock_genai, proofreader, mock_keychain):
        """Test client initialization failure when API test fails."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = ""  # Empty response indicates failure
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        with pytest.raises(APIValidationError) as exc_info:
            proofreader._get_client()
        
        assert "API test failed" in str(exc_info.value)
    
    def test_detect_correction_mode_auto_financial(self, proofreader):
        """Test auto-detection of number_lock mode for financial text."""
        financial_text = "Doanh thu năm 2024 đạt 15.5 tỷ VND, tăng 12% so với năm trước."
        mode = proofreader._detect_correction_mode(financial_text)
        assert mode == 'number_lock'
    
    def test_detect_correction_mode_auto_business(self, proofreader):
        """Test auto-detection of business mode for business reports."""
        business_text = "Báo cáo kết quả kinh doanh quý IV cho thấy lợi nhuận tăng trường."
        mode = proofreader._detect_correction_mode(business_text)
        assert mode == 'business'
    
    def test_detect_correction_mode_auto_minimal(self, proofreader):
        """Test auto-detection defaults to minimal mode for general text."""
        general_text = "Đây là một đoạn văn bản thông thường không có từ khóa đặc biệt."
        mode = proofreader._detect_correction_mode(general_text)
        assert mode == 'minimal'
    
    def test_detect_correction_mode_manual(self, proofreader):
        """Test that manual mode setting overrides auto-detection."""
        proofreader.correction_mode = 'business'
        financial_text = "Doanh thu 10 tỷ VND"
        mode = proofreader._detect_correction_mode(financial_text)
        assert mode == 'business'  # Should not auto-detect to 'number_lock'
    
    def test_get_system_prompt(self, proofreader):
        """Test system prompt selection based on text content."""
        # Test financial text gets number_lock prompt
        financial_text = "Tổng doanh thu: 25.7 tỷ VND"
        prompt = proofreader._get_system_prompt(financial_text)
        assert "Khoá số liệu" in prompt
        
        # Test business text gets business prompt
        business_text = "Báo cáo kết quả kinh doanh"
        prompt = proofreader._get_system_prompt(business_text)
        assert "báo cáo kinh doanh" in prompt
    
    @patch('core.proofreader.genai')
    def test_proofread_success(self, mock_genai, proofreader, mock_keychain, mock_pii_masker):
        """Test successful proofreading with PII masking."""
        # Setup mocks
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Corrected Vietnamese text"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        test_text = "Văn bản cần hiệu đính với lỗi chính tả."
        result = proofreader.proofread(test_text)
        
        # Verify PII masking was applied
        mock_pii_masker.mask_for_cloud.assert_called_once_with(test_text)
        
        # Verify API call was made (twice: once for test, once for actual proofreading)
        assert mock_model.generate_content.call_count == 2
        
        assert result == "Corrected Vietnamese text"
    
    def test_proofread_disabled(self, proofreader):
        """Test that proofreading returns original text when disabled."""
        proofreader.enabled = False
        test_text = "Original text"
        
        result = proofreader.proofread(test_text)
        
        assert result == test_text
    
    def test_proofread_offline_mode(self, proofreader):
        """Test that proofreading returns original text in offline mode."""
        proofreader.offline_mode = True
        test_text = "Original text"
        
        result = proofreader.proofread(test_text)
        
        assert result == test_text
    
    def test_proofread_empty_text(self, proofreader):
        """Test proofreading with empty or whitespace-only text."""
        assert proofreader.proofread("") == ""
        assert proofreader.proofread("   ") == "   "
        assert proofreader.proofread(None) == None
    
    @patch('core.proofreader.genai')
    def test_proofread_api_error_fallback(self, mock_genai, proofreader, mock_keychain):
        """Test that proofreading falls back to original text on API errors."""
        # Setup mock to raise an exception
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model
        
        test_text = "Original text"
        result = proofreader.proofread(test_text)
        
        # Should return original text on error
        assert result == test_text
    
    @patch('core.proofreader.genai')
    def test_proofread_credential_error_fallback(self, mock_genai, proofreader, mock_keychain):
        """Test proofreading fallback when credentials are invalid."""
        mock_keychain.load_api_key.return_value = None
        
        test_text = "Original text"
        result = proofreader.proofread(test_text)
        
        # Should return original text on credential error
        assert result == test_text
    
    @patch('core.proofreader.genai')
    def test_proofread_without_pii_mapping(self, mock_genai, proofreader, mock_keychain, mock_pii_masker):
        """Test proofreading when PII masking doesn't change the text."""
        # Setup mocks
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Corrected text"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Clean text without PII
        mock_pii_masker.mask_for_cloud.return_value = "clean text"
        
        test_text = "Clean text without PII"
        result = proofreader.proofread(test_text)
        
        # Verify masking was called
        mock_pii_masker.mask_for_cloud.assert_called_once_with(test_text)
        
        assert result == "Corrected text"
    
    def test_is_enabled(self, proofreader):
        """Test is_enabled method."""
        assert proofreader.is_enabled() is True
        
        proofreader.enabled = False
        assert proofreader.is_enabled() is False
        
        proofreader.enabled = True
        proofreader.offline_mode = True
        assert proofreader.is_enabled() is False
    
    def test_set_enabled(self, proofreader):
        """Test set_enabled method."""
        proofreader.set_enabled(False)
        assert proofreader.enabled is False
        
        proofreader.set_enabled(True)
        assert proofreader.enabled is True
    
    def test_set_offline_mode(self, proofreader):
        """Test set_offline_mode method."""
        # Initialize client first
        proofreader._client = Mock()
        
        proofreader.set_offline_mode(True)
        assert proofreader.offline_mode is True
        assert proofreader._client is None  # Should clear client
        
        proofreader.set_offline_mode(False)
        assert proofreader.offline_mode is False
    
    def test_set_correction_mode_valid(self, proofreader):
        """Test setting valid correction modes."""
        proofreader.set_correction_mode('business')
        assert proofreader.correction_mode == 'business'
        
        proofreader.set_correction_mode('auto')
        assert proofreader.correction_mode == 'auto'
    
    def test_set_correction_mode_invalid(self, proofreader):
        """Test setting invalid correction mode raises error."""
        with pytest.raises(ValueError) as exc_info:
            proofreader.set_correction_mode('invalid_mode')
        
        assert "Invalid correction mode" in str(exc_info.value)
    
    def test_get_status(self, proofreader):
        """Test get_status method returns correct information."""
        status = proofreader.get_status()
        
        assert isinstance(status, dict)
        assert 'enabled' in status
        assert 'offline_mode' in status
        assert 'correction_mode' in status
        assert 'model_name' in status
        assert 'api_timeout' in status
        assert 'client_initialized' in status
        assert 'available_modes' in status
        
        assert status['enabled'] is True
        assert status['offline_mode'] is False
        assert status['correction_mode'] == 'auto'
        assert status['model_name'] == 'gemini-2.5-pro'
        assert status['client_initialized'] is False
        assert isinstance(status['available_modes'], list)
    
    @patch('core.proofreader.time')
    @patch('core.proofreader.genai')
    def test_proofread_performance_logging(self, mock_genai, mock_time, proofreader, mock_keychain, mock_pii_masker):
        """Test that proofreading logs performance metrics."""
        # Setup time mock
        mock_time.time.side_effect = [0.0, 1.5]  # 1.5 second processing time
        
        # Setup API mock
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Corrected text"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        with mock.patch.object(proofreader.logger, 'info') as mock_log:
            proofreader.proofread("Test text")
            
            # Verify performance logging
            mock_log.assert_called()
            log_calls = [call.args[0] for call in mock_log.call_args_list]
            assert any("1.50s" in call for call in log_calls)
    
    @patch('core.proofreader.genai')
    def test_api_timeout_configuration(self, mock_genai, mock_keychain, mock_pii_masker):
        """Test that API timeout is properly configured."""
        proofreader = Proofreader(
            api_timeout=60,
            keychain_manager=mock_keychain,
            pii_masker=mock_pii_masker
        )
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Corrected text"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        proofreader.proofread("Test text")
        
        # Verify timeout was passed to API call (called twice: test + proofread)
        assert mock_model.generate_content.call_count == 2
        call_args = mock_model.generate_content.call_args_list
        assert call_args[0][1]['request_options']['timeout'] == 60
        assert call_args[1][1]['request_options']['timeout'] == 60


class TestProofreaderIntegration:
    """Integration tests for Proofreader with real dependencies."""
    
    def test_integration_with_ingestor(self):
        """Test that Proofreader integrates correctly with Ingestor."""
        from core.ingestor import Ingestor
        
        # Create ingestor with proofreading enabled
        ingestor = Ingestor(
            ocr_enabled=False,  # Disable OCR for simplicity
            proofreading_enabled=True,
            proofreading_mode='minimal'
        )
        
        # Verify proofreader configuration
        assert ingestor.proofreading_enabled is True
        assert ingestor.proofreading_mode == 'minimal'
        assert ingestor._proofreader is None  # Lazy initialization
        
        # Test lazy loading
        proofreader = ingestor._get_proofreader()
        assert isinstance(proofreader, Proofreader)
        assert proofreader.enabled is True
        assert proofreader.correction_mode == 'minimal'
    
    def test_integration_with_pii_masker(self):
        """Test integration with real PIIMasker."""
        from core.pii_masker import PIIMasker
        from core.keychain import KeychainManager
        
        # Create real dependencies but with mocked API
        pii_masker = PIIMasker()
        keychain = Mock(spec=KeychainManager)
        keychain.load_api_key.return_value = None  # Force offline behavior
        
        proofreader = Proofreader(
            enabled=True,
            offline_mode=True,  # Avoid API calls
            keychain_manager=keychain,
            pii_masker=pii_masker
        )
        
        # Test with text containing PII
        text_with_pii = "Liên hệ: email@example.com hoặc 0123456789"
        result = proofreader.proofread(text_with_pii)
        
        # Should return original text in offline mode
        assert result == text_with_pii


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
