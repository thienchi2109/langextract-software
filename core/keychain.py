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
            # Store the key securely first (without validation to avoid hanging)
            keyring.set_password(self.SERVICE_NAME, self.API_KEY_USERNAME, key.strip())
            logger.info("API key stored successfully in Windows Credential Manager")
            
            # Then try validation in background (non-blocking)
            try:
                is_valid = self._quick_validate_api_key(key.strip())
                if is_valid:
                    logger.info("API key validation successful")
                else:
                    logger.warning("API key validation failed - key may be invalid")
            except Exception as e:
                logger.warning(f"API key validation failed but key was saved: {str(e)}")
                # Don't fail the save operation due to validation issues
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save API key: {str(e)}")
            raise CredentialError(f"Failed to save API key: {str(e)}")
    
    def _quick_validate_api_key(self, key: str) -> bool:
        """
        Quick validation of API key without hanging.
        
        Args:
            key: The API key to validate
            
        Returns:
            bool: True if key appears valid, False otherwise
        """
        if not key or len(key.strip()) < 10:
            return False
            
        # Basic format check for Gemini API keys
        key = key.strip()
        if not key.startswith('AIza') and not key.startswith('AIza'):
            logger.warning("API key doesn't appear to be in Gemini format")
            return False
            
        logger.info("API key format appears valid")
        return True
    
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
            
            # Configure for minimal response with timeout
            generation_config = GenerationConfig(
                max_output_tokens=5,  # Minimal response
                temperature=0.1,
            )
            
            # Add timeout to prevent hanging
            import signal
            import threading
            
            def timeout_handler():
                raise TimeoutError("API validation timeout after 10 seconds")
            
            # Use threading for timeout instead of signal (Windows compatible)
            result = [False]
            error = [None]
            
            def validate_worker():
                try:
                    response = model.generate_content(
                        test_prompt,
                        generation_config=generation_config
                    )
                    
                    # Check if we got a valid response
                    if response and response.text:
                        result[0] = True
                        logger.info("API key validation successful")
                    else:
                        logger.warning("API key validation failed - no response text")
                        
                except Exception as e:
                    error[0] = e
            
            # Run validation in thread with timeout
            validation_thread = threading.Thread(target=validate_worker, daemon=True)
            validation_thread.start()
            validation_thread.join(timeout=10.0)  # 10 second timeout
            
            if validation_thread.is_alive():
                logger.warning("API key validation timed out after 10 seconds")
                return False
                
            if error[0]:
                raise error[0]
                
            return result[0]
                
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            raise APIValidationError(f"API validation failed: {str(e)}")
    
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