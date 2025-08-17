"""
Unit tests for KeychainManager credential management functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import keyring
from core.keychain import KeychainManager
from core.exceptions import CredentialError, APIValidationError


class TestKeychainManager:
    """Test cases for KeychainManager class."""
    
    @pytest.fixture
    def keychain_manager(self):
        """Create a KeychainManager instance for testing."""
        with patch('core.keychain.KEYRING_AVAILABLE', True):
            with patch('keyring.set_keyring'):
                return KeychainManager()
    
    @pytest.fixture
    def mock_keyring(self):
        """Mock keyring functions."""
        with patch('keyring.set_password') as mock_set, \
             patch('keyring.get_password') as mock_get, \
             patch('keyring.delete_password') as mock_delete:
            yield {
                'set_password': mock_set,
                'get_password': mock_get,
                'delete_password': mock_delete
            }
    
    @pytest.fixture
    def mock_genai(self):
        """Mock Google Generative AI."""
        with patch('google.generativeai.configure') as mock_configure, \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            # Setup mock model and response
            mock_response = Mock()
            mock_response.text = "Hello response"
            
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            yield {
                'configure': mock_configure,
                'model_class': mock_model_class,
                'model': mock_model,
                'response': mock_response
            }
    
    def test_init_success(self):
        """Test successful initialization."""
        with patch('core.keychain.KEYRING_AVAILABLE', True):
            with patch('keyring.set_keyring'):
                manager = KeychainManager()
                assert manager.SERVICE_NAME == "LangExtractor"
                assert manager.API_KEY_USERNAME == "gemini_api_key"
    
    def test_init_keyring_not_available(self):
        """Test initialization when keyring is not available."""
        with patch('core.keychain.KEYRING_AVAILABLE', False):
            with pytest.raises(CredentialError) as exc_info:
                KeychainManager()
            assert "keyring library is required" in str(exc_info.value)
    
    def test_save_api_key_success(self, keychain_manager, mock_keyring, mock_genai):
        """Test successful API key saving."""
        test_key = "test-api-key-123"
        
        # Mock successful validation
        mock_genai['response'].text = "Hello response"
        
        result = keychain_manager.save_api_key(test_key)
        
        assert result is True
        mock_keyring['set_password'].assert_called_once_with(
            "LangExtractor", "gemini_api_key", test_key
        )
        mock_genai['configure'].assert_called_with(api_key=test_key)
    
    def test_save_api_key_empty(self, keychain_manager):
        """Test saving empty API key raises error."""
        with pytest.raises(CredentialError) as exc_info:
            keychain_manager.save_api_key("")
        assert "API key cannot be empty" in str(exc_info.value)
        
        with pytest.raises(CredentialError) as exc_info:
            keychain_manager.save_api_key("   ")
        assert "API key cannot be empty" in str(exc_info.value)
    
    def test_save_api_key_invalid(self, keychain_manager, mock_genai):
        """Test saving invalid API key raises error."""
        test_key = "invalid-key"
        
        # Mock failed validation
        mock_genai['model'].generate_content.side_effect = Exception("Invalid API key")
        
        with pytest.raises(CredentialError) as exc_info:
            keychain_manager.save_api_key(test_key)
        assert "Invalid API key - validation failed" in str(exc_info.value)
    
    def test_save_api_key_keyring_error(self, keychain_manager, mock_keyring, mock_genai):
        """Test handling keyring storage errors."""
        test_key = "test-api-key-123"
        
        # Mock successful validation but failed storage
        mock_genai['response'].text = "Hello response"
        mock_keyring['set_password'].side_effect = Exception("Storage failed")
        
        with pytest.raises(CredentialError) as exc_info:
            keychain_manager.save_api_key(test_key)
        assert "Failed to save API key" in str(exc_info.value)
    
    def test_load_api_key_success(self, keychain_manager, mock_keyring):
        """Test successful API key loading."""
        test_key = "test-api-key-123"
        mock_keyring['get_password'].return_value = test_key
        
        result = keychain_manager.load_api_key()
        
        assert result == test_key
        mock_keyring['get_password'].assert_called_once_with(
            "LangExtractor", "gemini_api_key"
        )
    
    def test_load_api_key_not_found(self, keychain_manager, mock_keyring):
        """Test loading when no API key is stored."""
        mock_keyring['get_password'].return_value = None
        
        result = keychain_manager.load_api_key()
        
        assert result is None
    
    def test_load_api_key_with_whitespace(self, keychain_manager, mock_keyring):
        """Test loading API key with whitespace is stripped."""
        test_key = "  test-api-key-123  "
        mock_keyring['get_password'].return_value = test_key
        
        result = keychain_manager.load_api_key()
        
        assert result == "test-api-key-123"
    
    def test_load_api_key_keyring_error(self, keychain_manager, mock_keyring):
        """Test handling keyring retrieval errors."""
        mock_keyring['get_password'].side_effect = Exception("Retrieval failed")
        
        with pytest.raises(CredentialError) as exc_info:
            keychain_manager.load_api_key()
        assert "Failed to load API key" in str(exc_info.value)
    
    def test_validate_api_key_success(self, keychain_manager, mock_genai):
        """Test successful API key validation."""
        test_key = "valid-api-key"
        mock_genai['response'].text = "Hello response"
        
        result = keychain_manager.validate_api_key(test_key)
        
        assert result is True
        mock_genai['configure'].assert_called_once_with(api_key=test_key)
        mock_genai['model'].generate_content.assert_called_once()
    
    def test_validate_api_key_empty(self, keychain_manager):
        """Test validation of empty API key."""
        assert keychain_manager.validate_api_key("") is False
        assert keychain_manager.validate_api_key("   ") is False
        assert keychain_manager.validate_api_key(None) is False
    
    def test_validate_api_key_api_error(self, keychain_manager, mock_genai):
        """Test validation when API call fails."""
        test_key = "invalid-api-key"
        mock_genai['model'].generate_content.side_effect = Exception("API Error")
        
        result = keychain_manager.validate_api_key(test_key)
        
        assert result is False
    
    def test_validate_api_key_no_response_text(self, keychain_manager, mock_genai):
        """Test validation when API returns no text."""
        test_key = "test-api-key"
        mock_genai['response'].text = None
        
        result = keychain_manager.validate_api_key(test_key)
        
        assert result is False
    
    def test_delete_api_key_success(self, keychain_manager, mock_keyring):
        """Test successful API key deletion."""
        mock_keyring['get_password'].return_value = "existing-key"
        
        result = keychain_manager.delete_api_key()
        
        assert result is True
        mock_keyring['delete_password'].assert_called_once_with(
            "LangExtractor", "gemini_api_key"
        )
    
    def test_delete_api_key_not_found(self, keychain_manager, mock_keyring):
        """Test deletion when no API key exists."""
        mock_keyring['get_password'].return_value = None
        
        result = keychain_manager.delete_api_key()
        
        assert result is True
        mock_keyring['delete_password'].assert_not_called()
    
    def test_delete_api_key_keyring_error(self, keychain_manager, mock_keyring):
        """Test handling keyring deletion errors."""
        mock_keyring['get_password'].return_value = "existing-key"
        mock_keyring['delete_password'].side_effect = Exception("Deletion failed")
        
        with pytest.raises(CredentialError) as exc_info:
            keychain_manager.delete_api_key()
        assert "Failed to delete API key" in str(exc_info.value)
    
    def test_has_api_key_true(self, keychain_manager, mock_keyring):
        """Test has_api_key when key exists."""
        mock_keyring['get_password'].return_value = "test-key"
        
        result = keychain_manager.has_api_key()
        
        assert result is True
    
    def test_has_api_key_false(self, keychain_manager, mock_keyring):
        """Test has_api_key when no key exists."""
        mock_keyring['get_password'].return_value = None
        
        result = keychain_manager.has_api_key()
        
        assert result is False
    
    def test_has_api_key_empty_string(self, keychain_manager, mock_keyring):
        """Test has_api_key when key is empty string."""
        mock_keyring['get_password'].return_value = "   "
        
        result = keychain_manager.has_api_key()
        
        assert result is False
    
    def test_has_api_key_error(self, keychain_manager, mock_keyring):
        """Test has_api_key when keyring error occurs."""
        mock_keyring['get_password'].side_effect = Exception("Error")
        
        result = keychain_manager.has_api_key()
        
        assert result is False
    
    def test_get_masked_api_key_success(self, keychain_manager, mock_keyring):
        """Test getting masked API key."""
        test_key = "AIzaSyDXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        mock_keyring['get_password'].return_value = test_key
        
        result = keychain_manager.get_masked_api_key()
        
        expected = "AIza" + "*" * (len(test_key) - 7) + "XXX"
        assert result == expected
    
    def test_get_masked_api_key_short(self, keychain_manager, mock_keyring):
        """Test getting masked API key for short key."""
        test_key = "short"
        mock_keyring['get_password'].return_value = test_key
        
        result = keychain_manager.get_masked_api_key()
        
        assert result == "*" * len(test_key)
    
    def test_get_masked_api_key_not_found(self, keychain_manager, mock_keyring):
        """Test getting masked API key when none exists."""
        mock_keyring['get_password'].return_value = None
        
        result = keychain_manager.get_masked_api_key()
        
        assert result is None
    
    def test_get_masked_api_key_error(self, keychain_manager, mock_keyring):
        """Test getting masked API key when error occurs."""
        mock_keyring['get_password'].side_effect = Exception("Error")
        
        result = keychain_manager.get_masked_api_key()
        
        assert result is None


class TestKeychainManagerIntegration:
    """Integration tests for KeychainManager."""
    
    @pytest.fixture
    def keychain_manager(self):
        """Create a KeychainManager instance for integration testing."""
        with patch('core.keychain.KEYRING_AVAILABLE', True):
            with patch('keyring.set_keyring'):
                return KeychainManager()
    
    @pytest.fixture
    def mock_genai(self):
        """Mock Google Generative AI."""
        with patch('google.generativeai.configure') as mock_configure, \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            # Setup mock model and response
            mock_response = Mock()
            mock_response.text = "Hello response"
            
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            yield {
                'configure': mock_configure,
                'model_class': mock_model_class,
                'model': mock_model,
                'response': mock_response
            }
    
    def test_full_workflow_success(self, keychain_manager, mock_genai):
        """Test complete workflow: save, load, validate, delete."""
        test_key = "test-integration-key"
        
        # Mock successful validation
        mock_genai['response'].text = "Hello response"
        
        with patch('keyring.set_password') as mock_set, \
             patch('keyring.get_password') as mock_get, \
             patch('keyring.delete_password') as mock_delete:
            
            # Test save
            mock_get.return_value = None  # No existing key
            result = keychain_manager.save_api_key(test_key)
            assert result is True
            mock_set.assert_called_once()
            
            # Test load
            mock_get.return_value = test_key
            loaded_key = keychain_manager.load_api_key()
            assert loaded_key == test_key
            
            # Test has_api_key
            assert keychain_manager.has_api_key() is True
            
            # Test masked key
            masked = keychain_manager.get_masked_api_key()
            assert masked is not None
            assert "*" in masked
            
            # Test delete
            result = keychain_manager.delete_api_key()
            assert result is True
            mock_delete.assert_called_once()
    
    def test_validation_with_different_responses(self, keychain_manager, mock_genai):
        """Test validation with various API response scenarios."""
        test_key = "test-key"
        
        # Test successful response
        mock_genai['response'].text = "Valid response"
        assert keychain_manager.validate_api_key(test_key) is True
        
        # Test empty response
        mock_genai['response'].text = ""
        assert keychain_manager.validate_api_key(test_key) is False
        
        # Test None response
        mock_genai['response'].text = None
        assert keychain_manager.validate_api_key(test_key) is False
        
        # Test exception during API call
        mock_genai['model'].generate_content.side_effect = Exception("Network error")
        assert keychain_manager.validate_api_key(test_key) is False


if __name__ == "__main__":
    pytest.main([__file__])