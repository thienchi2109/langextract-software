"""
OCR Engine for processing scanned PDF documents.

This module provides the OCREngine class that handles OCR processing using EasyOCR
for Vietnamese and English text extraction from scanned PDF pages.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import unicodedata

# Document processing libraries
import fitz  # PyMuPDF
import easyocr

from .models import ProcessorInterface
from .exceptions import (
    LangExtractorError,
    ErrorCategory,
    ErrorSeverity,
    handle_error
)


logger = logging.getLogger(__name__)


class OCREngine(ProcessorInterface):
    """
    OCR Engine for processing scanned PDF documents using EasyOCR.
    
    Supports Vietnamese and English text extraction with configurable DPI settings
    and model download management for offline operation.
    """
    
    def __init__(
        self,
        model_storage_dir: Optional[str] = None,
        dpi: int = 350,
        gpu_enabled: bool = False,
        download_enabled: bool = True
    ):
        """
        Initialize OCR Engine.
        
        Args:
            model_storage_dir: Directory to store EasyOCR models (default: system location)
            dpi: DPI setting for PDF page conversion (default: 350, minimum: 300)
            gpu_enabled: Enable GPU acceleration if available (default: False)
            download_enabled: Allow model downloads on first run (default: True)
        """
        self.dpi = max(dpi, 300)  # Enforce minimum 300 DPI as per requirements
        self.gpu_enabled = gpu_enabled
        self.download_enabled = download_enabled
        
        # Set model storage directory
        if model_storage_dir is None:
            self.model_storage_dir = os.path.join(
                os.environ.get('PROGRAMDATA', 'C:/ProgramData'),
                'LangExtractor',
                'easyocr_models'
            )
        else:
            self.model_storage_dir = model_storage_dir
            
        # Ensure model directory exists
        Path(self.model_storage_dir).mkdir(parents=True, exist_ok=True)
        
        self._reader = None
        self.logger = logging.getLogger(__name__)
        
        # OCR configuration
        self.ocr_config = {
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
    
    def _get_reader(self) -> easyocr.Reader:
        """
        Get or initialize EasyOCR reader with lazy loading.
        
        Returns:
            Initialized EasyOCR reader instance
            
        Raises:
            LangExtractorError: If reader initialization fails
        """
        if self._reader is None:
            try:
                self.logger.info("Initializing EasyOCR reader for Vietnamese and English...")
                
                self._reader = easyocr.Reader(
                    ['vi', 'en'],
                    gpu=self.gpu_enabled,
                    model_storage_directory=self.model_storage_dir,
                    download_enabled=self.download_enabled
                )
                
                self.logger.info(f"EasyOCR reader initialized successfully. Models stored in: {self.model_storage_dir}")
                
            except Exception as e:
                raise handle_error(
                    e,
                    self.logger,
                    context={'operation': 'ocr_reader_initialization', 'model_dir': self.model_storage_dir}
                )
        
        return self._reader
    
    def supports_format(self, file_path: str) -> bool:
        """
        Check if OCR engine supports the file format.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file is a PDF (OCR engine specifically for PDF processing)
        """
        return file_path.lower().endswith('.pdf')
    
    def process(self, file_path: str) -> str:
        """
        Process a PDF file and extract text using OCR.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted and normalized text content
            
        Raises:
            LangExtractorError: For PDF processing or OCR errors
        """
        try:
            return self.extract_text_from_pdf(file_path)
        except Exception as e:
            raise handle_error(
                e,
                self.logger,
                context={'file_path': file_path, 'operation': 'ocr_processing'}
            )
    
    def extract_text_from_pdf(self, pdf_path: str, ocr_enabled: bool = True) -> str:
        """
        Extract text from PDF using direct text extraction and OCR fallback.
        
        Args:
            pdf_path: Path to the PDF file
            ocr_enabled: Whether to use OCR for image-based pages (default: True)
            
        Returns:
            Extracted text content
            
        Raises:
            LangExtractorError: For PDF processing errors
        """
        try:
            doc = fitz.open(pdf_path)
            text_content = []
            ocr_pages = 0
            
            self.logger.info(f"Processing PDF: {pdf_path} ({len(doc)} pages)")
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Try direct text extraction first
                direct_text = page.get_text("text")
                
                # Check if page has meaningful text content (lower threshold for testing/smaller docs)
                if direct_text and len(direct_text.strip()) > 10:
                    text_content.append(f"--- Page {page_num + 1} ---\n{direct_text}")
                    self.logger.debug(f"Page {page_num + 1}: Used direct text extraction")
                    continue
                
                # Check if page has images (potential scanned content)
                image_list = page.get_images()
                
                # If there's some text but no images, use the text even if it's short
                if direct_text.strip() and not image_list:
                    text_content.append(f"--- Page {page_num + 1} ---\n{direct_text}")
                    self.logger.debug(f"Page {page_num + 1}: Used direct text extraction (short text)")
                    continue
                
                # If no images and no text - empty page
                if not image_list:
                    text_content.append(f"--- Page {page_num + 1} ---\n[Empty page]")
                    continue
                
                # Page has images but little/no text - use OCR if enabled
                if ocr_enabled:
                    ocr_text = self._ocr_page(page, page_num + 1)
                    text_content.append(f"--- Page {page_num + 1} ---\n{ocr_text}")
                    ocr_pages += 1
                    self.logger.debug(f"Page {page_num + 1}: Used OCR extraction")
                else:
                    text_content.append(
                        f"--- Page {page_num + 1} ---\n"
                        f"[Page contains {len(image_list)} images but OCR is disabled]"
                    )
            
            doc.close()
            
            # Combine all text and normalize
            full_text = "\n\n".join(text_content)
            normalized_text = unicodedata.normalize('NFC', full_text)
            
            self.logger.info(
                f"PDF processing completed: {len(normalized_text)} characters extracted. "
                f"OCR used on {ocr_pages} pages."
            )
            
            return normalized_text
            
        except Exception as e:
            raise handle_error(
                e,
                self.logger,
                context={'file_path': pdf_path, 'operation': 'pdf_ocr_processing'}
            )
    
    def _ocr_page(self, page: fitz.Page, page_num: int) -> str:
        """
        Perform OCR on a single PDF page.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number for logging
            
        Returns:
            Extracted text from the page
            
        Raises:
            LangExtractorError: For OCR processing errors
        """
        temp_image_path = None
        
        try:
            # Convert page to image with specified DPI
            pixmap = page.get_pixmap(dpi=self.dpi)
            
            # Create temporary file for the image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_image_path = temp_file.name
                pixmap.save(temp_image_path)
            
            pixmap = None  # Free memory
            
            # Perform OCR
            reader = self._get_reader()
            ocr_results = reader.readtext(temp_image_path, **self.ocr_config)
            
            # Extract text from OCR results
            page_text = "\n".join([result[1] for result in ocr_results if result[1].strip()])
            
            self.logger.debug(
                f"OCR on page {page_num}: extracted {len(page_text)} characters "
                f"from {len(ocr_results)} text regions"
            )
            
            return page_text
            
        except Exception as e:
            self.logger.warning(f"OCR failed on page {page_num}: {e}")
            return f"[OCR processing failed for page {page_num}]"
            
        finally:
            # Clean up temporary image file
            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    os.unlink(temp_image_path)
                except OSError:
                    self.logger.warning(f"Could not delete temporary file: {temp_image_path}")
    
    def get_reader_info(self) -> Dict[str, Any]:
        """
        Get information about the OCR reader configuration.
        
        Returns:
            Dictionary with reader configuration details
        """
        return {
            'languages': ['vi', 'en'],
            'gpu_enabled': self.gpu_enabled,
            'model_storage_dir': self.model_storage_dir,
            'download_enabled': self.download_enabled,
            'dpi': self.dpi,
            'ocr_config': self.ocr_config.copy(),
            'models_downloaded': os.path.exists(self.model_storage_dir) and bool(os.listdir(self.model_storage_dir))
        }
    
    def check_models_available(self) -> bool:
        """
        Check if EasyOCR models are available locally.
        
        Returns:
            True if models are available, False otherwise
        """
        models_dir = Path(self.model_storage_dir)
        return models_dir.exists() and bool(list(models_dir.glob('*')))
    
    def download_models(self) -> bool:
        """
        Download EasyOCR models if not already available.
        
        Returns:
            True if models were downloaded or already available
            
        Raises:
            LangExtractorError: If model download fails
        """
        try:
            if self.check_models_available():
                self.logger.info("EasyOCR models already available")
                return True
            
            self.logger.info("Downloading EasyOCR models...")
            
            # Initialize reader with download enabled
            old_download_setting = self.download_enabled
            self.download_enabled = True
            self._reader = None  # Force reinitialization
            
            # This will trigger model download
            self._get_reader()
            
            # Restore original setting
            self.download_enabled = old_download_setting
            
            if self.check_models_available():
                self.logger.info("EasyOCR models downloaded successfully")
                return True
            else:
                raise LangExtractorError(
                    "Model download completed but models not found",
                    category=ErrorCategory.CONFIGURATION,
                    severity=ErrorSeverity.HIGH
                )
                
        except Exception as e:
            raise handle_error(
                e,
                self.logger,
                context={'operation': 'model_download', 'model_dir': self.model_storage_dir}
            )
