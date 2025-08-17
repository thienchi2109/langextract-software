"""
Unit tests for PII masking functionality.

Tests cover Vietnamese PII formats including account numbers, ID numbers,
emails, and phone numbers with various edge cases and validation scenarios.
"""

import pytest
from unittest.mock import patch, MagicMock

from core.pii_masker import PIIMasker, MaskingPattern
from core.exceptions import LangExtractorError


class TestPIIMasker:
    """Test cases for PIIMasker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.masker = PIIMasker()
    
    def test_initialization(self):
        """Test PIIMasker initialization."""
        assert self.masker.is_enabled() is True
        patterns = self.masker.get_pattern_info()
        
        expected_patterns = {
            'account_numbers', 'id_numbers', 'emails', 'phone_numbers'
        }
        assert set(patterns.keys()) == expected_patterns
        
        # Check pattern descriptions
        assert 'Vietnamese bank account numbers' in patterns['account_numbers']
        assert 'Vietnamese CMND/CCCD numbers' in patterns['id_numbers']
        assert 'Email addresses' in patterns['emails']
        assert 'Vietnamese phone numbers' in patterns['phone_numbers']


class TestAccountNumberMasking:
    """Test cases for account number masking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.masker = PIIMasker()
    
    def test_mask_account_numbers_valid_formats(self):
        """Test masking of valid Vietnamese bank account numbers."""
        test_cases = [
            # Standard bank account formats
            ("Account: 12345678", "Account: 12****78"),
            ("STK 123456789012", "STK 12********12"),
            ("Số tài khoản: 1234567890123456", "Số tài khoản: 12************56"),
            ("TK: 12345678901234567890", "TK: 12****************90"),  # Max length
            
            # Multiple accounts in text
            ("TK1: 12345678 và TK2: 987654321", "TK1: 12****78 và TK2: 98*****21"),
            
            # Edge cases
            ("12345678", "12****78"),  # Minimum length (8 digits)
            ("1234567890123456789", "12***************89"),  # Maximum length (19 digits)
            ("12345678901234567890", "12****************90"),  # Maximum length (20 digits)
        ]
        
        for original, expected in test_cases:
            result = self.masker.mask_account_numbers(original)
            assert result == expected, f"Failed for: {original}"
    
    def test_mask_account_numbers_edge_cases(self):
        """Test edge cases for account number masking."""
        # Too short (less than 8 digits)
        result = self.masker.mask_account_numbers("Account: 1234567")
        assert result == "Account: 1234567"  # Should not be masked
        
        # Too long (more than 20 digits)
        result = self.masker.mask_account_numbers("123456789012345678901")
        assert result == "123456789012345678901"  # Should not be masked
        
        # Non-digit characters
        result = self.masker.mask_account_numbers("Account: 123456A8")
        assert result == "Account: 123456A8"  # Should not be masked
        
        # Empty string
        result = self.masker.mask_account_numbers("")
        assert result == ""
    
    def test_mask_account_number_helper_method(self):
        """Test the helper method for masking individual account numbers."""
        # Normal cases
        assert self.masker._mask_account_number("12345678") == "12****78"
        assert self.masker._mask_account_number("123456789012") == "12********12"
        
        # Short numbers
        assert self.masker._mask_account_number("123") == "***"
        assert self.masker._mask_account_number("12") == "**"
        assert self.masker._mask_account_number("1") == "*"


class TestIDNumberMasking:
    """Test cases for Vietnamese ID number masking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.masker = PIIMasker()
    
    def test_mask_id_numbers_valid_formats(self):
        """Test masking of valid Vietnamese ID numbers."""
        test_cases = [
            # CMND format (9 digits)
            ("CMND: 123456789", "CMND: 12*****89"),
            ("Số CMND 987654321", "Số CMND 98*****21"),
            
            # CCCD format (12 digits)
            ("CCCD: 123456789012", "CCCD: 12********12"),
            ("Căn cước: 987654321098", "Căn cước: 98********98"),
            
            # Multiple IDs in text
            ("CMND: 123456789 và CCCD: 123456789012", 
             "CMND: 12*****89 và CCCD: 12********12"),
            
            # Just the numbers
            ("123456789", "12*****89"),
            ("123456789012", "12********12"),
        ]
        
        for original, expected in test_cases:
            result = self.masker.mask_id_numbers(original)
            assert result == expected, f"Failed for: {original}"
    
    def test_mask_id_numbers_edge_cases(self):
        """Test edge cases for ID number masking."""
        # Wrong length (not 9 or 12 digits)
        result = self.masker.mask_id_numbers("CMND: 12345678")  # 8 digits
        assert result == "CMND: 12345678"  # Should not be masked
        
        result = self.masker.mask_id_numbers("CCCD: 1234567890")  # 10 digits
        assert result == "CCCD: 1234567890"  # Should not be masked
        
        # Non-digit characters
        result = self.masker.mask_id_numbers("CMND: 12345678A")
        assert result == "CMND: 12345678A"  # Should not be masked
        
        # Empty string
        result = self.masker.mask_id_numbers("")
        assert result == ""
    
    def test_mask_id_number_helper_method(self):
        """Test the helper method for masking individual ID numbers."""
        # Normal cases
        assert self.masker._mask_id_number("123456789") == "12*****89"
        assert self.masker._mask_id_number("123456789012") == "12********12"
        
        # Short numbers
        assert self.masker._mask_id_number("1234") == "1234"  # Too short, not masked
        assert self.masker._mask_id_number("123") == "***"
        assert self.masker._mask_id_number("12") == "**"


class TestEmailMasking:
    """Test cases for email address masking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.masker = PIIMasker()
    
    def test_mask_emails_valid_formats(self):
        """Test masking of valid email addresses."""
        test_cases = [
            # Standard email formats
            ("Email: john.doe@example.com", "Email: jo******@ex*****.com"),
            ("Contact: admin@company.vn", "Contact: ad***@co*****.vn"),
            ("user123@gmail.com", "us*****@gm***.com"),
            
            # Multiple emails
            ("john@test.com and jane@example.org", 
             "jo**@te**.com and ja**@ex*****.org"),
            
            # Complex domains
            ("user@subdomain.example.com", "us**@su*******.example.com"),
            ("test@example.co.uk", "te**@ex*****.co.uk"),
            
            # Short usernames
            ("a@test.com", "*@te**.com"),
            ("ab@test.com", "**@te**.com"),
        ]
        
        for original, expected in test_cases:
            result = self.masker.mask_emails(original)
            assert result == expected, f"Failed for: {original}"
    
    def test_mask_emails_edge_cases(self):
        """Test edge cases for email masking."""
        # Invalid email formats
        result = self.masker.mask_emails("not-an-email")
        assert result == "not-an-email"  # Should not be masked
        
        result = self.masker.mask_emails("missing@domain")
        assert result == "missing@domain"  # Should not be masked (no TLD)
        
        # Empty string
        result = self.masker.mask_emails("")
        assert result == ""
    
    def test_mask_email_helper_method(self):
        """Test the helper method for masking individual emails."""
        # Normal cases
        assert self.masker._mask_email("john@example.com") == "jo**@ex*****.com"
        assert self.masker._mask_email("a@test.com") == "*@te**.com"
        
        # Complex domains
        assert self.masker._mask_email("user@sub.example.com") == "us**@su*.example.com"
        
        # Invalid format
        assert self.masker._mask_email("invalid-email") == "*************"


class TestPhoneNumberMasking:
    """Test cases for Vietnamese phone number masking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.masker = PIIMasker()
    
    def test_mask_phone_numbers_valid_formats(self):
        """Test masking of valid Vietnamese phone numbers."""
        test_cases = [
            # International format with +84
            ("Phone: +84123456789", "Phone: +84*******89"),
            ("Liên hệ: +84987654321", "Liên hệ: +84*******21"),
            
            # International format with 84
            ("84123456789", "84*******89"),
            ("84987654321", "84*******21"),
            
            # National format with 0
            ("0123456789", "0*******89"),
            ("0987654321", "0*******21"),
            ("01234567890", "0********90"),  # 11 digits
            
            # Multiple phone numbers
            ("SĐT: 0123456789 hoặc +84987654321", 
             "SĐT: 0*******89 hoặc +84*******21"),
        ]
        
        for original, expected in test_cases:
            result = self.masker.mask_phone_numbers(original)
            assert result == expected, f"Failed for: {original}"
    
    def test_mask_phone_numbers_edge_cases(self):
        """Test edge cases for phone number masking."""
        # Invalid formats
        result = self.masker.mask_phone_numbers("Phone: 123456")  # Too short
        assert result == "Phone: 123456"  # Should not be masked
        
        result = self.masker.mask_phone_numbers("Phone: 01234567890123")  # Too long
        assert result == "Phone: 01234567890123"  # Should not be masked
        
        # Invalid prefixes
        result = self.masker.mask_phone_numbers("Phone: 1123456789")
        assert result == "Phone: 1123456789"  # Should not be masked
        
        # Empty string
        result = self.masker.mask_phone_numbers("")
        assert result == ""
    
    def test_mask_phone_number_helper_method(self):
        """Test the helper method for masking individual phone numbers."""
        # Different formats
        assert self.masker._mask_phone_number("+84123456789") == "+84*******89"
        assert self.masker._mask_phone_number("84123456789") == "84*******89"
        assert self.masker._mask_phone_number("0123456789") == "0*******89"
        
        # Edge case - unexpected format
        assert self.masker._mask_phone_number("123456789") == "12*****89"


class TestMaskForCloud:
    """Test cases for the main mask_for_cloud method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.masker = PIIMasker()
    
    def test_mask_for_cloud_comprehensive(self):
        """Test comprehensive masking with all PII types."""
        original_text = """
        Thông tin khách hàng:
        - Họ tên: Nguyễn Văn A
        - CMND: 123456789
        - Email: nguyen.van.a@example.com
        - SĐT: 0987654321
        - Tài khoản: 12345678901234
        - CCCD: 123456789012
        - Liên hệ: admin@company.vn hoặc +84123456789
        """
        
        result = self.masker.mask_for_cloud(original_text)
        
        # Check that all PII types are masked
        assert "12*****89" in result  # CMND
        assert "12********12" in result  # CCCD
        assert "ng**********@ex*****.com" in result  # Email
        assert "09******21" in result  # Phone
        assert "12**********34" in result  # Account
        assert "ad***@co*****.vn" in result  # Second email
        assert "+84*******89" in result  # International phone
        
        # Check that non-PII content is preserved
        assert "Thông tin khách hàng:" in result
        assert "Nguyễn Văn A" in result  # Name should not be masked
    
    def test_mask_for_cloud_preserves_context(self):
        """Test that masking preserves enough context for extraction."""
        original_text = "Chuyển khoản từ TK 12345678 đến email john@example.com số tiền 1,000,000 VND"
        result = self.masker.mask_for_cloud(original_text)
        
        # Context should be preserved
        assert "Chuyển khoản từ TK" in result
        assert "đến email" in result
        assert "số tiền 1,000,000 VND" in result
        
        # PII should be masked
        assert "12****78" in result
        assert "jo**@ex*****.com" in result
    
    def test_mask_for_cloud_disabled(self):
        """Test that masking can be disabled."""
        original_text = "CMND: 123456789, Email: test@example.com"
        
        self.masker.disable_masking()
        result = self.masker.mask_for_cloud(original_text)
        
        assert result == original_text  # Should be unchanged
        assert not self.masker.is_enabled()
    
    def test_mask_for_cloud_invalid_input(self):
        """Test error handling for invalid input."""
        with pytest.raises(LangExtractorError) as exc_info:
            self.masker.mask_for_cloud(123)  # Not a string
        
        assert "Invalid input type" in str(exc_info.value)
    
    @patch('core.pii_masker.logger')
    def test_mask_for_cloud_logging(self, mock_logger):
        """Test that masking operations are logged properly."""
        text = "CMND: 123456789"
        self.masker.mask_for_cloud(text)
        
        # Check that info log was called
        mock_logger.info.assert_called()
        log_message = mock_logger.info.call_args[0][0]
        assert "PII masking completed" in log_message
    
    def test_mask_for_cloud_empty_string(self):
        """Test masking of empty string."""
        result = self.masker.mask_for_cloud("")
        assert result == ""
    
    def test_mask_for_cloud_no_pii(self):
        """Test masking of text with no PII."""
        original_text = "This is a normal text without any sensitive information."
        result = self.masker.mask_for_cloud(original_text)
        assert result == original_text


class TestMaskingControl:
    """Test cases for masking enable/disable functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.masker = PIIMasker()
    
    def test_enable_disable_masking(self):
        """Test enabling and disabling masking."""
        # Initially enabled
        assert self.masker.is_enabled() is True
        
        # Disable masking
        self.masker.disable_masking()
        assert self.masker.is_enabled() is False
        
        # Re-enable masking
        self.masker.enable_masking()
        assert self.masker.is_enabled() is True
    
    @patch('core.pii_masker.logger')
    def test_enable_disable_logging(self, mock_logger):
        """Test that enable/disable operations are logged."""
        self.masker.disable_masking()
        mock_logger.warning.assert_called_with(
            "PII masking disabled - ensure offline processing only"
        )
        
        self.masker.enable_masking()
        mock_logger.info.assert_called_with("PII masking enabled")
    
    def test_disabled_masking_behavior(self):
        """Test that all masking methods respect the disabled state."""
        text_with_pii = "CMND: 123456789, Email: test@example.com, Phone: 0987654321"
        
        self.masker.disable_masking()
        
        # All individual masking methods should return original text
        assert self.masker.mask_account_numbers(text_with_pii) == text_with_pii
        assert self.masker.mask_id_numbers(text_with_pii) == text_with_pii
        assert self.masker.mask_emails(text_with_pii) == text_with_pii
        assert self.masker.mask_phone_numbers(text_with_pii) == text_with_pii
        assert self.masker.mask_for_cloud(text_with_pii) == text_with_pii


class TestPatternTesting:
    """Test cases for pattern testing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.masker = PIIMasker()
    
    def test_test_patterns(self):
        """Test the pattern testing functionality."""
        test_data = {
            'account_numbers': ['12345678', '123456789012'],
            'id_numbers': ['123456789', '123456789012'],
            'emails': ['test@example.com', 'user@domain.vn'],
            'phone_numbers': ['0987654321', '+84123456789']
        }
        
        results = self.masker.test_patterns(test_data)
        
        # Check that all patterns were tested
        assert set(results.keys()) == set(test_data.keys())
        
        # Check account numbers
        account_results = results['account_numbers']
        assert len(account_results) == 2
        assert account_results[0] == ('12345678', '12****78')
        assert account_results[1] == ('123456789012', '12********12')
        
        # Check ID numbers
        id_results = results['id_numbers']
        assert len(id_results) == 2
        assert id_results[0] == ('123456789', '12*****89')
        assert id_results[1] == ('123456789012', '12********12')
        
        # Check emails
        email_results = results['emails']
        assert len(email_results) == 2
        assert email_results[0] == ('test@example.com', 'te**@ex*****.com')
        assert email_results[1] == ('user@domain.vn', 'us**@do****.vn')
        
        # Check phone numbers
        phone_results = results['phone_numbers']
        assert len(phone_results) == 2
        assert phone_results[0] == ('0987654321', '0*******21')
        assert phone_results[1] == ('+84123456789', '+84*******89')
    
    def test_test_patterns_unknown_pattern(self):
        """Test pattern testing with unknown pattern name."""
        test_data = {
            'unknown_pattern': ['test123']
        }
        
        with patch('core.pii_masker.logger') as mock_logger:
            results = self.masker.test_patterns(test_data)
            
            # Should return empty results for unknown pattern
            assert results == {}
            
            # Should log warning
            mock_logger.warning.assert_called_with("Unknown pattern: unknown_pattern")


class TestIntegration:
    """Integration tests for PIIMasker with realistic scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.masker = PIIMasker()
    
    def test_vietnamese_document_processing(self):
        """Test processing a realistic Vietnamese document."""
        document_text = """
        THÔNG TIN KHÁCH HÀNG
        
        Họ và tên: Trần Thị Bình
        Số CMND: 123456789
        Số CCCD: 987654321012
        Địa chỉ email: tran.thi.binh@gmail.com
        Số điện thoại: 0987654321
        Số tài khoản ngân hàng: 12345678901234
        
        THÔNG TIN GIAO DỊCH
        
        Chuyển khoản từ TK 12345678901234 đến TK 98765432109876
        Số tiền: 5,000,000 VND
        Nội dung: Thanh toán hóa đơn tháng 12/2023
        
        Liên hệ hỗ trợ: support@bank.vn hoặc hotline +84123456789
        """
        
        result = self.masker.mask_for_cloud(document_text)
        
        # Verify all PII is masked
        assert "12*****89" in result  # CMND
        assert "98********12" in result  # CCCD
        assert "tr***********@gm***.com" in result  # Email
        assert "09******21" in result  # Phone
        assert "12**********34" in result  # Account 1
        assert "98**********76" in result  # Account 2
        assert "su*****@ba**.vn" in result  # Support email
        assert "+84*******89" in result  # Hotline
        
        # Verify context is preserved
        assert "THÔNG TIN KHÁCH HÀNG" in result
        assert "Trần Thị Bình" in result  # Name not masked
        assert "5,000,000 VND" in result  # Amount not masked
        assert "Thanh toán hóa đơn tháng 12/2023" in result  # Description not masked
    
    def test_mixed_language_document(self):
        """Test processing document with mixed Vietnamese and English."""
        document_text = """
        Customer Information / Thông tin khách hàng:
        
        Name / Tên: John Nguyen
        ID Number / Số CMND: 123456789
        Email: john.nguyen@company.com
        Phone / SĐT: +84987654321
        Bank Account / Tài khoản: 12345678901234
        
        Please contact us at support@company.com or call 0123456789
        Vui lòng liên hệ qua email admin@congty.vn hoặc gọi +84123456789
        """
        
        result = self.masker.mask_for_cloud(document_text)
        
        # Verify all PII is masked regardless of language context
        assert "12*****89" in result
        assert "jo*********@co*****.com" in result
        assert "+84*******21" in result
        assert "12**********34" in result
        assert "su*****@co*****.com" in result
        assert "01******89" in result
        assert "ad***@co****.vn" in result
        assert "+84*******89" in result
        
        # Verify bilingual context is preserved
        assert "Customer Information / Thông tin khách hàng:" in result
        assert "John Nguyen" in result
        assert "Please contact us at" in result
        assert "Vui lòng liên hệ qua email" in result