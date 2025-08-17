"""
PII Masking module for protecting sensitive information before cloud processing.

This module provides functionality to mask Vietnamese PII formats including:
- Account numbers (bank accounts, credit cards)
- ID numbers (CMND/CCCD)
- Email addresses
- Phone numbers

The masking preserves enough context for accurate extraction while protecting sensitive data.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .exceptions import LangExtractorError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


@dataclass
class MaskingPattern:
    """Configuration for a PII masking pattern."""
    name: str
    pattern: re.Pattern
    replacement: str
    description: str


class PIIMasker:
    """
    Handles masking of Personally Identifiable Information (PII) for Vietnamese formats.
    
    This class provides methods to mask sensitive information before sending data
    to external APIs while preserving enough context for accurate extraction.
    """
    
    def __init__(self):
        """Initialize the PII masker with Vietnamese-specific patterns."""
        self._patterns = self._initialize_patterns()
        self._enabled = True
        
    def _initialize_patterns(self) -> Dict[str, MaskingPattern]:
        """Initialize regex patterns for Vietnamese PII formats."""
        patterns = {}
        
        # Vietnamese bank account numbers (typically 8-20 digits)
        patterns['account_numbers'] = MaskingPattern(
            name='account_numbers',
            pattern=re.compile(r'\b\d{8,20}\b'),
            replacement=lambda m: self._mask_account_number(m.group()),
            description='Vietnamese bank account numbers'
        )
        
        # Vietnamese ID numbers (CMND: 9 digits, CCCD: 12 digits)
        patterns['id_numbers'] = MaskingPattern(
            name='id_numbers',
            pattern=re.compile(r'\b(?:\d{9}|\d{12})\b'),
            replacement=lambda m: self._mask_id_number(m.group()),
            description='Vietnamese CMND/CCCD numbers'
        )
        
        # Email addresses
        patterns['emails'] = MaskingPattern(
            name='emails',
            pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            replacement=lambda m: self._mask_email(m.group()),
            description='Email addresses'
        )
        
        # Vietnamese phone numbers (various formats)
        patterns['phone_numbers'] = MaskingPattern(
            name='phone_numbers',
            pattern=re.compile(r'\b(?:\+84|84|0)(?:[1-9]\d{8,9})\b'),
            replacement=lambda m: self._mask_phone_number(m.group()),
            description='Vietnamese phone numbers'
        )
        
        return patterns
    
    def _mask_account_number(self, account_number: str) -> str:
        """
        Mask account number by showing first 2 and last 2 digits.
        
        Args:
            account_number: The account number to mask
            
        Returns:
            Masked account number (e.g., "12****89")
        """
        if len(account_number) < 4:
            return '*' * len(account_number)
        
        return account_number[:2] + '*' * (len(account_number) - 4) + account_number[-2:]
    
    def _mask_id_number(self, id_number: str) -> str:
        """
        Mask ID number by showing first 2 and last 2 digits.
        
        Args:
            id_number: The ID number to mask
            
        Returns:
            Masked ID number (e.g., "12****89")
        """
        if len(id_number) < 4:
            return '*' * len(id_number)
        
        return id_number[:2] + '*' * (len(id_number) - 4) + id_number[-2:]
    
    def _mask_email(self, email: str) -> str:
        """
        Mask email by showing first 2 characters of username and domain.
        
        Args:
            email: The email address to mask
            
        Returns:
            Masked email (e.g., "jo****@ex****.com")
        """
        try:
            username, domain = email.split('@')
            
            # Mask username
            if len(username) <= 2:
                masked_username = '*' * len(username)
            else:
                masked_username = username[:2] + '*' * (len(username) - 2)
            
            # Mask domain (keep first 2 chars and TLD)
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                main_domain = domain_parts[0]
                tld = '.'.join(domain_parts[1:])
                
                if len(main_domain) <= 2:
                    masked_domain = '*' * len(main_domain) + '.' + tld
                else:
                    masked_domain = main_domain[:2] + '*' * (len(main_domain) - 2) + '.' + tld
            else:
                masked_domain = domain[:2] + '*' * max(0, len(domain) - 2)
            
            return f"{masked_username}@{masked_domain}"
        except ValueError:
            # Invalid email format, mask the whole thing
            return '*' * len(email)
    
    def _mask_phone_number(self, phone_number: str) -> str:
        """
        Mask phone number by showing country code and last 2 digits.
        
        Args:
            phone_number: The phone number to mask
            
        Returns:
            Masked phone number (e.g., "+84****89" or "0****89")
        """
        if phone_number.startswith('+84'):
            return '+84' + '*' * (len(phone_number) - 5) + phone_number[-2:]
        elif phone_number.startswith('84'):
            return '84' + '*' * (len(phone_number) - 4) + phone_number[-2:]
        elif phone_number.startswith('0'):
            return '0' + '*' * (len(phone_number) - 3) + phone_number[-2:]
        else:
            # Fallback for unexpected format
            return phone_number[:2] + '*' * (len(phone_number) - 4) + phone_number[-2:]
    
    def mask_account_numbers(self, text: str) -> str:
        """
        Mask account numbers in the given text.
        
        Args:
            text: Text containing potential account numbers
            
        Returns:
            Text with account numbers masked
        """
        if not self._enabled:
            return text
            
        pattern = self._patterns['account_numbers']
        return pattern.pattern.sub(pattern.replacement, text)
    
    def mask_id_numbers(self, text: str) -> str:
        """
        Mask Vietnamese ID numbers (CMND/CCCD) in the given text.
        
        Args:
            text: Text containing potential ID numbers
            
        Returns:
            Text with ID numbers masked
        """
        if not self._enabled:
            return text
            
        pattern = self._patterns['id_numbers']
        return pattern.pattern.sub(pattern.replacement, text)
    
    def mask_emails(self, text: str) -> str:
        """
        Mask email addresses in the given text.
        
        Args:
            text: Text containing potential email addresses
            
        Returns:
            Text with email addresses masked
        """
        if not self._enabled:
            return text
            
        pattern = self._patterns['emails']
        return pattern.pattern.sub(pattern.replacement, text)
    
    def mask_phone_numbers(self, text: str) -> str:
        """
        Mask Vietnamese phone numbers in the given text.
        
        Args:
            text: Text containing potential phone numbers
            
        Returns:
            Text with phone numbers masked
        """
        if not self._enabled:
            return text
            
        pattern = self._patterns['phone_numbers']
        return pattern.pattern.sub(pattern.replacement, text)
    
    def mask_for_cloud(self, text: str) -> str:
        """
        Apply all masking rules to prepare text for cloud processing.
        
        This method applies all PII masking patterns while preserving enough
        context for accurate extraction by AI models.
        
        Args:
            text: Original text that may contain PII
            
        Returns:
            Text with all PII masked for safe cloud processing
            
        Raises:
            LangExtractorError: If masking fails due to invalid input
        """
        if not isinstance(text, str):
            raise LangExtractorError(
                "Invalid input type for PII masking",
                category=ErrorCategory.VALIDATION_ERROR,
                severity=ErrorSeverity.HIGH,
                details={"expected": "str", "received": type(text).__name__}
            )
        
        if not self._enabled:
            logger.info("PII masking is disabled, returning original text")
            return text
        
        try:
            masked_text = text
            
            # Apply all masking patterns in order
            masked_text = self.mask_account_numbers(masked_text)
            masked_text = self.mask_id_numbers(masked_text)
            masked_text = self.mask_emails(masked_text)
            masked_text = self.mask_phone_numbers(masked_text)
            
            # Log masking statistics (without revealing actual content)
            original_length = len(text)
            masked_length = len(masked_text)
            mask_count = text.count('*') - masked_text.count('*')
            
            logger.info(
                f"PII masking completed: {original_length} -> {masked_length} chars, "
                f"applied {abs(mask_count)} masks"
            )
            
            return masked_text
            
        except Exception as e:
            logger.error(f"PII masking failed: {e}")
            raise LangExtractorError(
                "Failed to apply PII masking",
                category=ErrorCategory.VALIDATION_ERROR,
                severity=ErrorSeverity.HIGH,
                details={"error": str(e)}
            ) from e
    
    def enable_masking(self) -> None:
        """Enable PII masking (default state)."""
        self._enabled = True
        logger.info("PII masking enabled")
    
    def disable_masking(self) -> None:
        """Disable PII masking for offline processing."""
        self._enabled = False
        logger.warning("PII masking disabled - ensure offline processing only")
    
    def is_enabled(self) -> bool:
        """Check if PII masking is currently enabled."""
        return self._enabled
    
    def get_pattern_info(self) -> Dict[str, str]:
        """
        Get information about available masking patterns.
        
        Returns:
            Dictionary mapping pattern names to descriptions
        """
        return {name: pattern.description for name, pattern in self._patterns.items()}
    
    def test_patterns(self, test_data: Dict[str, List[str]]) -> Dict[str, List[Tuple[str, str]]]:
        """
        Test masking patterns against provided test data.
        
        Args:
            test_data: Dictionary mapping pattern names to lists of test strings
            
        Returns:
            Dictionary mapping pattern names to lists of (original, masked) tuples
        """
        results = {}
        
        for pattern_name, test_strings in test_data.items():
            if pattern_name not in self._patterns:
                logger.warning(f"Unknown pattern: {pattern_name}")
                continue
                
            pattern_results = []
            for test_string in test_strings:
                if pattern_name == 'account_numbers':
                    masked = self.mask_account_numbers(test_string)
                elif pattern_name == 'id_numbers':
                    masked = self.mask_id_numbers(test_string)
                elif pattern_name == 'emails':
                    masked = self.mask_emails(test_string)
                elif pattern_name == 'phone_numbers':
                    masked = self.mask_phone_numbers(test_string)
                else:
                    masked = test_string
                
                pattern_results.append((test_string, masked))
            
            results[pattern_name] = pattern_results
        
        return results