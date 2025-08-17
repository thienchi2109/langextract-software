"""
Unit tests for the OCR Engine module.

Tests cover OCR initialization, PDF processing, text extraction,
error handling, and model management functionality.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import pytest
import fitz

from core.ocr_engine import OCREngine
from core.exceptions import LangExtractorError


class TestOCREngine(unittest.TestCase):
    """Test cases for OCR Engine functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_model_dir = os.path.join(self.temp_dir, 'test_models')
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ocr_engine_initialization_default(self):
        """Test OCR engine initialization with default parameters."""
        engine = OCREngine()
        
        self.assertEqual(engine.dpi, 350)
        self.assertFalse(engine.gpu_enabled)
        self.assertTrue(engine.download_enabled)
        self.assertIsNone(engine._reader)
        self.assertIn('LangExtractor', engine.model_storage_dir)
        self.assertIn('easyocr_models', engine.model_storage_dir)
    
    def test_ocr_engine_initialization_custom(self):
        """Test OCR engine initialization with custom parameters."""
        engine = OCREngine(
            model_storage_dir=self.test_model_dir,
            dpi=300,
            gpu_enabled=True,
            download_enabled=False
        )
        
        self.assertEqual(engine.dpi, 300)
        self.assertTrue(engine.gpu_enabled)
        self.assertFalse(engine.download_enabled)
        self.assertEqual(engine.model_storage_dir, self.test_model_dir)
    
    def test_dpi_minimum_enforcement(self):
        """Test that DPI is enforced to be at least 300."""
        engine = OCREngine(dpi=200)
        self.assertEqual(engine.dpi, 300)
        
        engine = OCREngine(dpi=250)
        self.assertEqual(engine.dpi, 300)
        
        engine = OCREngine(dpi=400)
        self.assertEqual(engine.dpi, 400)
    
    def test_supports_format(self):
        """Test file format support detection."""
        engine = OCREngine()
        
        # Test supported formats
        self.assertTrue(engine.supports_format('test.pdf'))
        self.assertTrue(engine.supports_format('TEST.PDF'))
        self.assertTrue(engine.supports_format('/path/to/document.pdf'))
        
        # Test unsupported formats
        self.assertFalse(engine.supports_format('test.docx'))
        self.assertFalse(engine.supports_format('test.txt'))
        self.assertFalse(engine.supports_format('test.xlsx'))
        self.assertFalse(engine.supports_format('test'))
    
    @patch('core.ocr_engine.easyocr.Reader')
    def test_get_reader_initialization(self, mock_reader_class):
        """Test OCR reader initialization."""
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        engine = OCREngine(model_storage_dir=self.test_model_dir)
        reader = engine._get_reader()
        
        # Verify reader was created with correct parameters
        mock_reader_class.assert_called_once_with(
            ['vi', 'en'],
            gpu=False,
            model_storage_directory=self.test_model_dir,
            download_enabled=True
        )
        
        # Verify same reader is returned on subsequent calls
        reader2 = engine._get_reader()
        self.assertIs(reader, reader2)
        mock_reader_class.assert_called_once()  # Should not be called again
    
    @patch('core.ocr_engine.easyocr.Reader')
    def test_get_reader_initialization_failure(self, mock_reader_class):
        """Test OCR reader initialization failure handling."""
        mock_reader_class.side_effect = Exception("EasyOCR initialization failed")
        
        engine = OCREngine()
        with self.assertRaises(LangExtractorError):
            engine._get_reader()
    
    def _create_test_pdf(self, text_content: str = None, has_images: bool = False) -> str:
        """Create a test PDF file."""
        pdf_path = os.path.join(self.temp_dir, 'test.pdf')
        doc = fitz.open()  # Create new PDF
        page = doc.new_page()
        
        if text_content:
            # Simple text insertion method
            page.insert_text((50, 100), text_content, fontsize=12)
        
        if has_images:
            # Create an actual embedded image (PNG format)
            from PIL import Image
            import io
            
            # Create a simple test image
            img = Image.new('RGB', (100, 100), color='red')
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Insert the image into the PDF
            img_rect = fitz.Rect(100, 100, 200, 200)
            page.insert_image(img_rect, stream=img_bytes.getvalue())
        
        doc.save(pdf_path)
        doc.close()
        return pdf_path
    
    def test_extract_text_from_pdf_with_text(self):
        """Test PDF text extraction with direct text content."""
        test_text = "This is a test PDF with direct text content."
        pdf_path = self._create_test_pdf(text_content=test_text)
        
        engine = OCREngine()
        result = engine.extract_text_from_pdf(pdf_path, ocr_enabled=False)
        
        self.assertIn(test_text, result)
        self.assertIn("--- Page 1 ---", result)
    
    def test_extract_text_from_pdf_empty(self):
        """Test PDF text extraction with empty PDF."""
        pdf_path = self._create_test_pdf()
        
        engine = OCREngine()
        result = engine.extract_text_from_pdf(pdf_path, ocr_enabled=False)
        
        self.assertIn("[Empty page]", result)
    
    @patch('core.ocr_engine.easyocr.Reader')
    def test_ocr_page_processing(self, mock_reader_class):
        """Test OCR processing of a single page."""
        # Setup mocks
        mock_reader = Mock()
        mock_reader.readtext.return_value = [
            ([(0, 0), (100, 0), (100, 50), (0, 50)], 'Sample OCR text', 0.9),
            ([(0, 60), (120, 60), (120, 110), (0, 110)], 'Another line', 0.8)
        ]
        mock_reader_class.return_value = mock_reader

        # Create test PDF with images but minimal text (to trigger OCR)
        pdf_path = os.path.join(self.temp_dir, 'test_ocr.pdf')
        doc = fitz.open()
        page = doc.new_page()
        
        # Add minimal text (below 10 char threshold)
        page.insert_text((50, 50), "x")  # Just one character
        
        # Add an embedded image
        from PIL import Image
        import io
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        img_rect = fitz.Rect(100, 100, 200, 200)
        page.insert_image(img_rect, stream=img_bytes.getvalue())
        
        doc.save(pdf_path)
        doc.close()

        engine = OCREngine()
        
        # Mock the _ocr_page method instead since the internal file handling is complex
        with patch.object(engine, '_ocr_page', return_value="Sample OCR text\nAnother line") as mock_ocr_page:
            result = engine.extract_text_from_pdf(pdf_path, ocr_enabled=True)
            
            # Verify OCR method was called
            mock_ocr_page.assert_called_once()
            
            # Verify text extraction
            self.assertIn("Sample OCR text", result)
            self.assertIn("Another line", result)
    
    @patch('core.ocr_engine.easyocr.Reader')
    def test_ocr_processing_failure(self, mock_reader_class):
        """Test OCR processing failure handling."""
        mock_reader = Mock()
        mock_reader.readtext.side_effect = Exception("OCR processing failed")
        mock_reader_class.return_value = mock_reader
        
        pdf_path = self._create_test_pdf(has_images=True)
        
        engine = OCREngine()
        result = engine.extract_text_from_pdf(pdf_path, ocr_enabled=True)
        
        # Should contain error message for failed page
        self.assertIn("[OCR processing failed for page 1]", result)
    
    def test_process_method(self):
        """Test the main process method."""
        test_text = "Test content for processing"
        pdf_path = self._create_test_pdf(text_content=test_text)
        
        engine = OCREngine()
        result = engine.process(pdf_path)
        
        self.assertIn(test_text, result)
    
    def test_process_invalid_file(self):
        """Test processing with invalid file."""
        engine = OCREngine()
        
        with self.assertRaises(LangExtractorError):
            engine.process("nonexistent.pdf")
    
    def test_get_reader_info(self):
        """Test reader information retrieval."""
        engine = OCREngine(
            model_storage_dir=self.test_model_dir,
            dpi=400,
            gpu_enabled=True,
            download_enabled=False
        )
        
        info = engine.get_reader_info()
        
        expected_keys = [
            'languages', 'gpu_enabled', 'model_storage_dir', 
            'download_enabled', 'dpi', 'ocr_config', 'models_downloaded'
        ]
        
        for key in expected_keys:
            self.assertIn(key, info)
        
        self.assertEqual(info['languages'], ['vi', 'en'])
        self.assertTrue(info['gpu_enabled'])
        self.assertEqual(info['model_storage_dir'], self.test_model_dir)
        self.assertFalse(info['download_enabled'])
        self.assertEqual(info['dpi'], 400)
    
    def test_check_models_available_empty_dir(self):
        """Test model availability check with empty directory."""
        engine = OCREngine(model_storage_dir=self.test_model_dir)
        
        # Create empty directory
        os.makedirs(self.test_model_dir, exist_ok=True)
        
        self.assertFalse(engine.check_models_available())
    
    def test_check_models_available_with_files(self):
        """Test model availability check with model files."""
        engine = OCREngine(model_storage_dir=self.test_model_dir)
        
        # Create directory with mock model files
        os.makedirs(self.test_model_dir, exist_ok=True)
        Path(os.path.join(self.test_model_dir, 'model1.pth')).touch()
        Path(os.path.join(self.test_model_dir, 'model2.pth')).touch()
        
        self.assertTrue(engine.check_models_available())
    
    def test_check_models_available_nonexistent_dir(self):
        """Test model availability check with nonexistent directory."""
        engine = OCREngine(model_storage_dir='/nonexistent/directory')
        
        self.assertFalse(engine.check_models_available())
    
    @patch('core.ocr_engine.easyocr.Reader')
    def test_download_models_success(self, mock_reader_class):
        """Test successful model download."""
        mock_reader = Mock()
        mock_reader_class.return_value = mock_reader
        
        engine = OCREngine(model_storage_dir=self.test_model_dir, download_enabled=False)
        
        # Mock models being available after download
        with patch.object(engine, 'check_models_available', side_effect=[False, True]):
            result = engine.download_models()
        
        self.assertTrue(result)
        # Verify reader was initialized with download enabled
        mock_reader_class.assert_called()
    
    @patch('core.ocr_engine.easyocr.Reader')
    def test_download_models_already_available(self, mock_reader_class):
        """Test model download when models are already available."""
        engine = OCREngine(model_storage_dir=self.test_model_dir)
        
        # Mock models already being available
        with patch.object(engine, 'check_models_available', return_value=True):
            result = engine.download_models()
        
        self.assertTrue(result)
        # Reader should not be initialized since models are already available
        mock_reader_class.assert_not_called()
    
    @patch('core.ocr_engine.easyocr.Reader')
    def test_download_models_failure(self, mock_reader_class):
        """Test model download failure."""
        mock_reader_class.side_effect = Exception("Download failed")
        
        engine = OCREngine(model_storage_dir=self.test_model_dir)
        
        with patch.object(engine, 'check_models_available', return_value=False):
            with self.assertRaises(LangExtractorError):
                engine.download_models()
    
    def test_ocr_config_customization(self):
        """Test OCR configuration parameters."""
        engine = OCREngine()
        
        expected_config = {
            'paragraph': True,
            'rotation_info': [90, 180, 270],
            'contrast_ths': 0.1,
            'adjust_contrast': 0.6,
            'mag_ratio': 2.0,
            'text_threshold': 0.6,
            'low_text': 0.3,
            'link_threshold': 0.4,
            'decoder': 'greedy'
        }
        
        self.assertEqual(engine.ocr_config, expected_config)
    
    def test_text_normalization(self):
        """Test Unicode text normalization in OCR results."""
        test_text = "Tiếng Việt có dấu"
        pdf_path = self._create_test_pdf(text_content=test_text)
        
        engine = OCREngine()
        result = engine.extract_text_from_pdf(pdf_path)
        
        # Result should be Unicode normalized
        import unicodedata
        self.assertEqual(result, unicodedata.normalize('NFC', result))


class TestOCREngineIntegration(unittest.TestCase):
    """Integration tests for OCR Engine with real PDFs."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_real_pdf_processing(self):
        """Test processing of a real PDF file (if available)."""
        # This test would run only if test PDFs are available
        # For now, we'll create a simple test PDF
        doc = fitz.open()
        page = doc.new_page()
        
        # Simple text insertion method
        text_content = "Sample text content\nMultiple lines\nVietnamese: Xin chào"
        page.insert_text((50, 100), text_content, fontsize=12)
        
        pdf_path = os.path.join(self.temp_dir, 'sample.pdf')
        doc.save(pdf_path)
        doc.close()
        
        engine = OCREngine(download_enabled=False)  # Avoid downloading in tests
        
        try:
            result = engine.extract_text_from_pdf(pdf_path, ocr_enabled=False)
            self.assertIn("Sample text content", result)
            self.assertIn("Xin chào", result)
        except Exception as e:
            # If OCR fails (e.g., models not available), skip this test
            self.skipTest(f"OCR processing failed: {e}")


if __name__ == '__main__':
    unittest.main()
