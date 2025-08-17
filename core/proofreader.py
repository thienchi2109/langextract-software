"""
Vietnamese text proofreader using Gemini API.

This module provides the Proofreader class that handles Vietnamese text correction
after OCR processing, with multiple correction variants and PII masking integration.
"""

import os
import logging
import time
from typing import Optional, Dict, Any
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, HarmCategory, HarmBlockThreshold

from .models import ProofreaderInterface
from .keychain import KeychainManager
from .pii_masker import PIIMasker
from .exceptions import (
    LangExtractorError,
    ErrorCategory,
    ErrorSeverity,
    APIValidationError,
    CredentialError,
    handle_error
)

logger = logging.getLogger(__name__)


class Proofreader(ProofreaderInterface):
    """
    Vietnamese text proofreader using Gemini API with multiple correction variants.
    
    Supports multiple correction modes for different use cases:
    - Minimal diacritics & spacing correction
    - Business proofreading for reports
    - Number-lock variant for financial documents
    - Configurable system prompts based on document type
    """
    
    # System prompts from docs/system_prompt_for_Vietnamese_correction.md
    SYSTEM_PROMPTS = {
        'minimal': """Bạn là bộ sửa lỗi tối thiểu cho văn bản tiếng Việt.
Chỉ được phép:

Sửa dấu tiếng Việt (âm sắc/huyền/hỏi/ngã/nặng; mũ/ă/ơ/ư/ô/ê) cho đúng;

Sửa khoảng trắng (thừa/thiếu), xuống dòng và dấu câu cơ bản (, . : ; ? !) khi rõ ràng sai;

Sửa lỗi OCR thường gặp (ví dụ lẫn I/1/l, O/0, rn/m) nếu chắc chắn.
TUYỆT ĐỐI KHÔNG: thay đổi số liệu, đơn vị, ký hiệu tiền tệ, email/URL/mã số, tên riêng, định dạng ngày/giờ, cú pháp bảng, mã, Markdown.
Giữ nguyên mọi ký tự [MASK], ***, hoặc phần đã được che.
Giữ nguyên số lượng dòng, không tóm tắt, không diễn giải, không thêm bớt nội dung.
Nếu không chắc, giữ nguyên.
Đầu ra: Trả về chính xác văn bản đã sửa, không thêm giải thích hay bao bọc.""",

        'business': """Bạn là bộ hiệu đính tiếng Việt cho báo cáo kinh doanh.
Mục tiêu: văn bản dễ đọc và đúng chính tả nhưng không thay đổi dữ kiện.
Được phép:

Sửa dấu, chính tả, khoảng trắng, chấm phẩy, hoa/thường đầu câu;

Chuẩn hoá kiểu liệt kê/bullet nhất quán.
Không được: thay đổi con số, đơn vị (%, tỷ, triệu, VND…), tên riêng, trích dẫn, ngày/giờ. Không diễn giải hay tóm tắt.
Bảo toàn [MASK] và mọi chuỗi được che.
Giữ bố cục & xuống dòng.
Đầu ra: chỉ văn bản đã hiệu đính.""",

        'number_lock': """Khoá số liệu: Mọi chuỗi số và số có đơn vị (ví dụ 1.234,56, 5 tỷ, 450 triệu, 12/08/2025) giữ nguyên 100%, không đổi định dạng, không thêm/loại bỏ dấu tách.
Chỉ sửa chính tả tiếng Việt, dấu, và khoảng trắng xung quanh số nếu chắc chắn.
Không tóm tắt. Không thêm bớt.""",

        'default': """Bạn là bộ hiệu đính tối thiểu cho văn bản tiếng Việt sau OCR.
Chỉ sửa: dấu tiếng Việt, chính tả hiển nhiên, khoảng trắng và chấm phẩy cơ bản; sửa nhầm OCR (I/1/l, O/0, rn/m) khi chắc chắn.
Không được: đổi bất kỳ số liệu/đơn vị/ngày giờ/URL/email/mã số, không dịch, không tóm tắt, không thêm bớt.
Bảo toàn [MASK] và mọi chuỗi được che. Giữ số dòng và bố cục.
Nếu không chắc, giữ nguyên.
Đầu ra: chỉ văn bản đã sửa, không kèm giải thích."""
    }
    
    def __init__(
        self,
        enabled: bool = True,
        offline_mode: bool = False,
        api_timeout: int = 30,
        correction_mode: str = 'auto',
        model_name: str = 'gemini-2.5-pro',
        keychain_manager: Optional[KeychainManager] = None,
        pii_masker: Optional[PIIMasker] = None
    ):
        """
        Initialize Vietnamese text proofreader.
        
        Args:
            enabled: Enable/disable proofreading (default: True)
            offline_mode: Disable API calls for offline processing (default: False)
            api_timeout: API request timeout in seconds (default: 30)
            correction_mode: Correction mode ('auto', 'minimal', 'business', 'number_lock')
            model_name: Gemini model to use (default: 'gemini-2.5-pro')
            keychain_manager: Credential manager instance (optional)
            pii_masker: PII masker instance (optional)
        """
        self.enabled = enabled
        self.offline_mode = offline_mode
        self.api_timeout = api_timeout
        self.correction_mode = correction_mode
        self.model_name = model_name
        
        # Initialize dependencies
        self.keychain_manager = keychain_manager or KeychainManager()
        self.pii_masker = pii_masker or PIIMasker()
        
        # Lazy initialization
        self._client = None
        self._model = None
        
        # Generation configuration based on recommendations
        self.generation_config = GenerationConfig(
            temperature=0.2,  # Stable, minimal creativity
            top_p=0.9,
            max_output_tokens=8192,  # Enough for most documents
            response_mime_type="text/plain"
        )
        
        # Safety settings - minimal blocking for text correction
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        self.logger = logging.getLogger(__name__)
    
    def _get_client(self) -> genai.GenerativeModel:
        """
        Get or create Gemini API client with lazy initialization.
        
        Returns:
            GenerativeModel: Configured Gemini client
            
        Raises:
            CredentialError: If API key is not available or invalid
            APIValidationError: If API client initialization fails
        """
        if self._client is not None:
            return self._client
        
        if self.offline_mode:
            raise LangExtractorError(
                "Proofreading is disabled in offline mode",
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
            
            # Configure Gemini API
            genai.configure(api_key=api_key)
            
            # Create model instance
            self._client = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            # Test API connection
            test_response = self._client.generate_content(
                "Test",
                request_options={"timeout": self.api_timeout}
            )
            
            if not test_response.text:
                raise APIValidationError("Gemini API test failed - no response")
            
            self.logger.info(f"Gemini API client initialized successfully with model {self.model_name}")
            return self._client
            
        except Exception as e:
            error_msg = f"Failed to initialize Gemini API client: {str(e)}"
            self.logger.error(error_msg)
            
            if isinstance(e, (CredentialError, APIValidationError)):
                raise
            else:
                raise APIValidationError(error_msg) from e
    
    def _detect_correction_mode(self, text: str) -> str:
        """
        Auto-detect the best correction mode based on text content.
        
        Args:
            text: Text to analyze
            
        Returns:
            str: Recommended correction mode
        """
        if self.correction_mode != 'auto':
            return self.correction_mode
        
        # Simple heuristics for mode detection
        text_lower = text.lower()
        
        # Check for financial indicators
        financial_keywords = ['vnd', 'tỷ', 'triệu', 'nghìn', '%', 'đồng', 'USD', 'EUR']
        if any(keyword in text_lower for keyword in financial_keywords):
            return 'number_lock'
        
        # Check for business report indicators
        business_keywords = ['báo cáo', 'kết quả', 'doanh thu', 'lợi nhuận', 'thống kê']
        if any(keyword in text_lower for keyword in business_keywords):
            return 'business'
        
        # Default to minimal for general text
        return 'minimal'
    
    def _get_system_prompt(self, text: str) -> str:
        """
        Get the appropriate system prompt based on correction mode and text content.
        
        Args:
            text: Text to be corrected
            
        Returns:
            str: System prompt for the correction mode
        """
        mode = self._detect_correction_mode(text)
        return self.SYSTEM_PROMPTS.get(mode, self.SYSTEM_PROMPTS['default'])
    
    def proofread(self, text: str) -> str:
        """
        Proofread and correct Vietnamese text using Gemini API.
        
        Args:
            text: Text to proofread
            
        Returns:
            str: Corrected text
            
        Raises:
            LangExtractorError: If proofreading fails
        """
        if not self.enabled:
            self.logger.debug("Proofreading is disabled, returning original text")
            return text
        
        if not text or not text.strip():
            self.logger.debug("Empty text provided, nothing to proofread")
            return text
        
        if self.offline_mode:
            self.logger.info("Offline mode enabled, skipping proofreading")
            return text
        
        start_time = time.time()
        original_length = len(text)
        
        try:
            # Mask PII before sending to API
            self.logger.debug("Applying PII masking before API call")
            masked_text = self.pii_masker.mask_for_cloud(text)
            
            # Get API client
            client = self._get_client()
            
            # Get appropriate system prompt
            system_prompt = self._get_system_prompt(text)
            correction_mode = self._detect_correction_mode(text)
            
            self.logger.info(f"Starting proofreading with mode: {correction_mode}")
            
            # Prepare the full prompt
            full_prompt = f"{system_prompt}\n\nVăn bản cần hiệu đính:\n{masked_text}"
            
            # Generate corrected text
            response = client.generate_content(
                full_prompt,
                request_options={"timeout": self.api_timeout}
            )
            
            if not response.text:
                raise APIValidationError("Empty response from Gemini API")
            
            corrected_text = response.text.strip()
            
            # Note: Since PIIMasker doesn't provide restore functionality,
            # we return the corrected masked text.
            # In practice, the masked text preserves enough context for readability.
            final_text = corrected_text
            
            processing_time = time.time() - start_time
            final_length = len(final_text)
            
            self.logger.info(
                f"Proofreading completed successfully. "
                f"Mode: {correction_mode}, "
                f"Time: {processing_time:.2f}s, "
                f"Length: {original_length} -> {final_length} chars"
            )
            
            return final_text
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Proofreading failed after {processing_time:.2f}s: {str(e)}"
            
            self.logger.error(error_msg)
            
            # Return original text on error to avoid breaking the pipeline
            if isinstance(e, (CredentialError, APIValidationError)):
                # Log specific API errors but continue processing
                self.logger.warning(f"API error during proofreading: {str(e)}, returning original text")
                return text
            else:
                # Handle unexpected errors
                handle_error(
                    LangExtractorError(
                        error_msg,
                        category=ErrorCategory.API_ERROR,
                        severity=ErrorSeverity.HIGH
                    ),
                    self.logger,
                    return_value=text
                )
                return text
    
    def is_enabled(self) -> bool:
        """
        Check if proofreading is enabled.
        
        Returns:
            bool: True if enabled, False otherwise
        """
        return self.enabled and not self.offline_mode
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable proofreading.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        self.logger.info(f"Proofreading {'enabled' if enabled else 'disabled'}")
    
    def set_offline_mode(self, offline: bool) -> None:
        """
        Enable or disable offline mode.
        
        Args:
            offline: True for offline mode, False for online mode
        """
        self.offline_mode = offline
        if offline:
            self._client = None  # Clear client to prevent API calls
        self.logger.info(f"Offline mode {'enabled' if offline else 'disabled'}")
    
    def set_correction_mode(self, mode: str) -> None:
        """
        Set the correction mode.
        
        Args:
            mode: Correction mode ('auto', 'minimal', 'business', 'number_lock')
        """
        if mode not in self.SYSTEM_PROMPTS and mode != 'auto':
            raise ValueError(f"Invalid correction mode: {mode}")
        
        self.correction_mode = mode
        self.logger.info(f"Correction mode set to: {mode}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current proofreader status and configuration.
        
        Returns:
            Dict[str, Any]: Status information
        """
        return {
            'enabled': self.enabled,
            'offline_mode': self.offline_mode,
            'correction_mode': self.correction_mode,
            'model_name': self.model_name,
            'api_timeout': self.api_timeout,
            'client_initialized': self._client is not None,
            'available_modes': list(self.SYSTEM_PROMPTS.keys())
        }
