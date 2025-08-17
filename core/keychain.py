"""
Secure credential management using Windows Credential Manager.
"""

import logging
import json
from typing import Optional
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logging.warning("keyring library not available. Credential storage will be disabled.")

from .models import CredentialManagerInterface
from .exceptions import CredentialError, APIValidationError


logger = logging.getLogger(__name__)


class KeychainManager(CredentialManagerInterface):
    """
    Secure credential management using Windows Credential Manager via keyring library.
    
    This class handles secure storage, retrieval, and validation of API keys
    using the Windows Credential Manager through the keyring library.
    """
    
    SERVICE_NAME = "LangExtractor"
    API_KEY_USERNAME = "gemini_api_key"
    
    def __init__(self):
        """Initialize the KeychainManager."""
        if not KEYRING_AVAILABLE:
            raise CredentialError(
                "keyring library is required for credential management. "
                "Please install it with: pip install keyring"
            )
        
        # Set keyring backend to Windows Credential Manager if available
        try:
            # Try different possible Windows backend locations
            try:
                import keyring.backends.Windows
                keyring.set_keyring(keyring.backends.Windows.WinVaultKeyring())
                logger.info("Using Windows Credential Manager for secure storage")
            except (ImportError, AttributeError):
                # Try alternative import path
                try:
                    from keyring.backends import Windows
                    keyring.set_keyring(Windows.WinVaultKeyring())
                    logger.info("Using Windows Credential Manager for secure storage")
                except (ImportError, AttributeError):
                    logger.warning("Windows Credential Manager not available, using default keyring backend")
        except Exception as e:
            logger.warning(f"Could not set Windows keyring backend: {e}, using default backend")
    
    def save_api_key(self, key: str) -> bool:
        """
        Save API key securely using Windows Credential Manager.
        
        Args:
            key: The API key to store
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            CredentialError: If storage fails
        """
        if not key or not key.strip():
            raise CredentialError("API key cannot be empty")
        
        try:
            # Validate the key before storing
            if not self.validate_api_key(key):
                raise CredentialError("Invalid API key - validation failed")
            
            # Store the key securely
            keyring.set_password(self.SERVICE_NAME, self.API_KEY_USERNAME, key.strip())
            logger.info("API key stored successfully in Windows Credential Manager")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save API key: {str(e)}")
            raise CredentialError(f"Failed to save API key: {str(e)}")
    
    def load_api_key(self) -> Optional[str]:
        """
        Load stored API key from Windows Credential Manager.
        
        Returns:
            Optional[str]: The stored API key, or None if not found
            
        Raises:
            CredentialError: If retrieval fails
        """
        try:
            key = keyring.get_password(self.SERVICE_NAME, self.API_KEY_USERNAME)
            if key:
                logger.debug("API key retrieved from Windows Credential Manager")
                return key.strip()
            else:
                logger.debug("No API key found in Windows Credential Manager")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load API key: {str(e)}")
            raise CredentialError(f"Failed to load API key: {str(e)}")
    
    def validate_api_key(self, key: str) -> bool:
        """
        Validate API key by testing Gemini API access.
        
        Args:
            key: The API key to validate
            
        Returns:
            bool: True if key is valid, False otherwise
            
        Raises:
            APIValidationError: If validation fails due to API issues
        """
        if not key or not key.strip():
            return False
        
        try:
            # Configure Gemini API with the key
            genai.configure(api_key=key.strip())
            
            # Test the API with a simple request
            model = genai.GenerativeModel('gemini-pro')
            
            # Use a minimal test prompt
            test_prompt = "Hello"
            
            # Configure for minimal response
            generation_config = GenerationConfig(
                max_output_tokens=10,
                temperature=0.1,
            )
            
            # Make test request with timeout
            response = model.generate_content(
                test_prompt,
                generation_config=generation_config
            )
            
            # Check if we got a valid response
            if response and response.text:
                logger.info("API key validation successful")
                return True
            else:
                logger.warning("API key validation failed - no response text")
                return False
                
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            # Don't raise exception for validation failures, just return False
            # This allows the application to handle invalid keys gracefully
            return False
    
    def delete_api_key(self) -> bool:
        """
        Delete stored API key from Windows Credential Manager.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            CredentialError: If deletion fails
        """
        try:
            # Check if key exists first
            existing_key = keyring.get_password(self.SERVICE_NAME, self.API_KEY_USERNAME)
            if not existing_key:
                logger.debug("No API key found to delete")
                return True
            
            # Delete the key
            keyring.delete_password(self.SERVICE_NAME, self.API_KEY_USERNAME)
            logger.info("API key deleted successfully from Windows Credential Manager")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete API key: {str(e)}")
            raise CredentialError(f"Failed to delete API key: {str(e)}")
    
    def has_api_key(self) -> bool:
        """
        Check if an API key is stored.
        
        Returns:
            bool: True if API key exists, False otherwise
        """
        try:
            key = self.load_api_key()
            return key is not None and len(key.strip()) > 0
        except CredentialError:
            return False
    
    def get_masked_api_key(self) -> Optional[str]:
        """
        Get a masked version of the stored API key for display purposes.
        
        Returns:
            Optional[str]: Masked API key (e.g., "AIza****xyz"), or None if not found
        """
        try:
            key = self.load_api_key()
            if not key:
                return None
            
            # Mask the middle part of the key, showing first 4 and last 3 characters
            if len(key) > 7:
                return f"{key[:4]}{'*' * (len(key) - 7)}{key[-3:]}"
            else:
                return "*" * len(key)
                
        except CredentialError:
            return None