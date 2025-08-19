"""
Settings Dialog cho LangExtractor.

Quản lý:
- API key cho Gemini (LangExtract)
- Cài đặt OCR (ngôn ngữ, quality)
- Cài đặt xử lý (offline mode, threads)
- Privacy và security settings
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel,
    QLineEdit, QPushButton, QCheckBox, QComboBox, QSpinBox, QGroupBox,
    QFormLayout, QMessageBox, QFrame, QTextEdit, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QPixmap

from core.keychain import KeychainManager
from core.models import AppConfig

logger = logging.getLogger(__name__)


class APIKeyTestThread(QThread):
    """Thread để test API key không block UI."""
    
    test_completed = Signal(bool, str)  # success, message
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        
    def run(self):
        """Test API key."""
        try:
            # Test với một request đơn giản
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Hello")
            
            if response and response.text:
                self.test_completed.emit(True, "API key hợp lệ!")
            else:
                self.test_completed.emit(False, "API key không phản hồi đúng")
                
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg:
                self.test_completed.emit(False, "API key không hợp lệ")
            elif "PERMISSION_DENIED" in error_msg:
                self.test_completed.emit(False, "API key không có quyền truy cập")
            elif "QUOTA_EXCEEDED" in error_msg:
                self.test_completed.emit(False, "Đã vượt quá quota API")
            else:
                self.test_completed.emit(False, f"Lỗi test API: {error_msg}")


class APIKeyWidget(QWidget):
    """Widget để quản lý API key một cách an toàn."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.keychain_manager = KeychainManager()
        self.test_thread = None
        self.save_thread = None # Added for save_api_key
        self.setup_ui()
        self.load_current_key()
        
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Info header
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        
        info_label = QLabel("🔑 Cài đặt API Key")
        info_label.setStyleSheet("font-weight: bold; color: #1976d2; font-size: 12pt;")
        info_layout.addWidget(info_label)
        
        info_text = QLabel(
            "API key Gemini cần thiết để sử dụng LangExtract AI extraction.\n"
            "Lấy API key miễn phí tại: https://aistudio.google.com/app/apikey"
        )
        info_text.setStyleSheet("color: #1976d2;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_frame)
        
        # API Key input
        key_group = QGroupBox("API Key")
        key_layout = QFormLayout(key_group)
        
        # Input field
        input_layout = QHBoxLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Nhập Gemini API key...")
        self.api_key_input.textChanged.connect(self.on_key_changed)
        input_layout.addWidget(self.api_key_input)
        
        # Show/hide button
        self.show_key_btn = QPushButton("👁️")
        self.show_key_btn.setFixedSize(30, 30)
        self.show_key_btn.setToolTip("Hiện/ẩn API key")
        self.show_key_btn.clicked.connect(self.toggle_key_visibility)
        input_layout.addWidget(self.show_key_btn)
        
        key_layout.addRow("API Key:", input_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("🧪 Test API Key")
        self.test_btn.clicked.connect(self.test_api_key)
        self.test_btn.setEnabled(False)
        button_layout.addWidget(self.test_btn)
        
        self.save_btn = QPushButton("💾 Lưu")
        self.save_btn.clicked.connect(self.save_api_key)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        self.clear_btn = QPushButton("🗑️ Xóa")
        self.clear_btn.clicked.connect(self.clear_api_key)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        key_layout.addRow(button_layout)
        
        # Status area
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        key_layout.addRow("Trạng thái:", self.status_label)
        
        # Progress bar for testing
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        key_layout.addRow(self.progress_bar)
        
        layout.addWidget(key_group)
        
        # Privacy warning
        privacy_frame = QFrame()
        privacy_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3e0;
                border: 1px solid #ff9800;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        privacy_layout = QVBoxLayout(privacy_frame)
        
        privacy_title = QLabel("🔒 Bảo mật & Quyền riêng tư")
        privacy_title.setStyleSheet("font-weight: bold; color: #f57c00;")
        privacy_layout.addWidget(privacy_title)
        
        privacy_text = QLabel(
            "• API key được mã hóa và lưu trong Windows Credential Manager\n"
            "• Dữ liệu được PII masking trước khi gửi lên cloud\n"
            "• Có thể sử dụng offline mode để xử lý hoàn toàn local"
        )
        privacy_text.setStyleSheet("color: #f57c00;")
        privacy_layout.addWidget(privacy_text)
        
        layout.addWidget(privacy_frame)
        layout.addStretch()
        
    def load_current_key(self):
        """Load API key hiện tại (nếu có)."""
        try:
            api_key = self.keychain_manager.load_api_key()
            if api_key:
                self.api_key_input.setText(api_key)
                self.status_label.setText("✅ API key đã được lưu")
                self.status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
            else:
                self.status_label.setText("❌ Chưa có API key")
                self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        except Exception as e:
            self.status_label.setText(f"⚠️ Lỗi load API key: {str(e)}")
            self.status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
            logger.error(f"Error loading API key: {e}")
            
    def on_key_changed(self):
        """Handle API key text changes."""
        has_key = bool(self.api_key_input.text().strip())
        self.test_btn.setEnabled(has_key)
        self.save_btn.setEnabled(has_key)
        
        if not has_key:
            self.status_label.setText("")
            
    def toggle_key_visibility(self):
        """Toggle API key visibility."""
        if self.api_key_input.echoMode() == QLineEdit.Password:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
            self.show_key_btn.setText("🙈")
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.show_key_btn.setText("👁️")
            
    def test_api_key(self):
        """Test API key."""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            return
            
        self.test_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("🧪 Đang test API key...")
        self.status_label.setStyleSheet("color: #2196f3; font-weight: bold;")
        
        # Start test in background thread
        self.test_thread = APIKeyTestThread(api_key)
        self.test_thread.test_completed.connect(self.on_test_completed)
        self.test_thread.start()
        
    def on_test_completed(self, success: bool, message: str):
        """Handle test completion."""
        self.progress_bar.setVisible(False)
        self.test_btn.setEnabled(True)
        
        if success:
            self.status_label.setText(f"✅ {message}")
            self.status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        else:
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
            
        self.test_thread = None
        
    def save_api_key(self):
        """Save API key."""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            return
        
        # Disable save button to prevent double clicks
        self.save_btn.setEnabled(False)
        self.test_btn.setEnabled(False)
        self.status_label.setText("🔄 Đang lưu và xác thực API key...")
        self.status_label.setStyleSheet("color: #2196f3; font-weight: bold;")
        
        # Run validation and saving in background thread
        from PySide6.QtCore import QThread
        
        class SaveWorker(QThread):
            finished_signal = Signal(bool, str)
            
            def __init__(self, keychain_manager, api_key):
                super().__init__()
                self.keychain_manager = keychain_manager
                self.api_key = api_key
            
            def run(self):
                try:
                    self.keychain_manager.save_api_key(self.api_key)
                    self.finished_signal.emit(True, "API key đã được lưu an toàn")
                except Exception as e:
                    self.finished_signal.emit(False, str(e))
        
        def on_save_completed(success: bool, message: str):
            # Re-enable buttons
            self.save_btn.setEnabled(True)
            has_key = bool(self.api_key_input.text().strip())
            self.test_btn.setEnabled(has_key)
            
            if success:
                self.status_label.setText(f"✅ {message}")
                self.status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
                
                QMessageBox.information(
                    self, "Thành công",
                    "API key đã được lưu an toàn vào Windows Credential Manager"
                )
            else:
                self.status_label.setText(f"❌ Lỗi lưu API key: {message}")
                self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
                
                QMessageBox.critical(
                    self, "Lỗi",
                    f"Không thể lưu API key: {message}"
                )
            
            # Clean up thread
            self.save_thread = None
        
        # Start save worker thread
        self.save_thread = SaveWorker(self.keychain_manager, api_key)
        self.save_thread.finished_signal.connect(on_save_completed)
        self.save_thread.start()
            
    def clear_api_key(self):
        """Clear API key."""
        reply = QMessageBox.question(
            self, "Xác nhận",
            "Bạn có chắc muốn xóa API key đã lưu?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.keychain_manager.delete_api_key()
                self.api_key_input.clear()
                self.status_label.setText("✅ API key đã được xóa")
                self.status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
                
                QMessageBox.information(
                    self, "Thành công",
                    "API key đã được xóa"
                )
                
            except Exception as e:
                self.status_label.setText(f"❌ Lỗi xóa API key: {str(e)}")
                self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")


class OCRSettingsWidget(QWidget):
    """Widget cho cài đặt OCR."""
    
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # OCR Enable
        ocr_group = QGroupBox("Cài đặt OCR")
        ocr_layout = QFormLayout(ocr_group)
        
        self.ocr_enabled_cb = QCheckBox("Bật OCR cho PDF scan")
        self.ocr_enabled_cb.setToolTip("Sử dụng OCR để đọc text từ PDF scan/hình ảnh")
        ocr_layout.addRow(self.ocr_enabled_cb)
        
        # Languages
        self.languages_combo = QComboBox()
        self.languages_combo.addItems([
            "Vietnamese + English",
            "Vietnamese only", 
            "English only",
            "Auto detect"
        ])
        self.languages_combo.setToolTip("Ngôn ngữ cho OCR")
        ocr_layout.addRow("Ngôn ngữ:", self.languages_combo)
        
        # DPI/Quality
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(150, 600)
        self.dpi_spin.setValue(300)
        self.dpi_spin.setSuffix(" DPI")
        self.dpi_spin.setToolTip("Độ phân giải cho OCR (cao hơn = chính xác hơn nhưng chậm hơn)")
        ocr_layout.addRow("Chất lượng:", self.dpi_spin)
        
        layout.addWidget(ocr_group)
        
        # Performance
        perf_group = QGroupBox("Hiệu suất")
        perf_layout = QFormLayout(perf_group)
        
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 8)
        self.max_workers_spin.setValue(4)
        self.max_workers_spin.setToolTip("Số threads xử lý song song")
        perf_layout.addRow("Số threads:", self.max_workers_spin)
        
        layout.addWidget(perf_group)
        layout.addStretch()
        
    def load_settings(self):
        """Load settings từ config."""
        self.ocr_enabled_cb.setChecked(self.config.ocr_enabled)
        
        # Language mapping - use tuples instead of lists for dictionary keys
        lang_map = {
            ('en', 'vi'): 0,  # Vietnamese + English (sorted)
            ('vi',): 1,       # Vietnamese only
            ('en',): 2        # English only
        }
        lang_key = tuple(sorted(self.config.ocr_languages))
        index = lang_map.get(lang_key, 0)
        self.languages_combo.setCurrentIndex(index)
        
        self.max_workers_spin.setValue(self.config.max_workers)
        
    def save_settings(self):
        """Save settings to config."""
        self.config.ocr_enabled = self.ocr_enabled_cb.isChecked()
        
        # Language mapping
        lang_options = [
            ['vi', 'en'],
            ['vi'],
            ['en'],
            ['vi', 'en']  # Auto = both
        ]
        self.config.ocr_languages = lang_options[self.languages_combo.currentIndex()]
        self.config.max_workers = self.max_workers_spin.value()


class PrivacySettingsWidget(QWidget):
    """Widget cho cài đặt privacy và security."""
    
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Privacy options
        privacy_group = QGroupBox("Quyền riêng tư")
        privacy_layout = QVBoxLayout(privacy_group)
        
        self.pii_masking_cb = QCheckBox("Bật PII masking trước khi gửi cloud")
        self.pii_masking_cb.setToolTip(
            "Tự động che giấu thông tin nhạy cảm (CMND, email, SĐT) trước khi gửi lên AI"
        )
        privacy_layout.addWidget(self.pii_masking_cb)
        
        self.offline_mode_cb = QCheckBox("Chế độ offline (không sử dụng AI cloud)")
        self.offline_mode_cb.setToolTip(
            "Xử lý hoàn toàn offline, không gửi dữ liệu lên cloud"
        )
        privacy_layout.addWidget(self.offline_mode_cb)
        
        self.proofreading_cb = QCheckBox("Bật proofreading (sửa lỗi OCR)")
        self.proofreading_cb.setToolTip("Sử dụng AI để sửa lỗi OCR trước khi extract")
        privacy_layout.addWidget(self.proofreading_cb)
        
        layout.addWidget(privacy_group)
        
        # Warning
        warning_frame = QFrame()
        warning_frame.setStyleSheet("""
            QFrame {
                background-color: #ffebee;
                border: 1px solid #f44336;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        warning_layout = QVBoxLayout(warning_frame)
        
        warning_title = QLabel("⚠️ Lưu ý quan trọng")
        warning_title.setStyleSheet("font-weight: bold; color: #d32f2f;")
        warning_layout.addWidget(warning_title)
        
        warning_text = QLabel(
            "• Chế độ offline sẽ tắt tất cả tính năng AI extraction\n"
            "• PII masking bảo vệ dữ liệu nhạy cảm nhưng có thể ảnh hưởng độ chính xác\n"
            "• Proofreading cải thiện chất lượng OCR nhưng tốn thêm API calls"
        )
        warning_text.setStyleSheet("color: #d32f2f;")
        warning_layout.addWidget(warning_text)
        
        layout.addWidget(warning_frame)
        layout.addStretch()
        
    def load_settings(self):
        """Load settings."""
        self.pii_masking_cb.setChecked(self.config.pii_masking_enabled)
        self.offline_mode_cb.setChecked(self.config.offline_mode)
        self.proofreading_cb.setChecked(self.config.proofread_enabled)
        
    def save_settings(self):
        """Save settings."""
        self.config.pii_masking_enabled = self.pii_masking_cb.isChecked()
        self.config.offline_mode = self.offline_mode_cb.isChecked()
        self.config.proofread_enabled = self.proofreading_cb.isChecked()


class SettingsDialog(QDialog):
    """Dialog chính cho settings."""
    
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
        self.setup_styling()
        
    def setup_ui(self):
        """Setup UI."""
        self.setWindowTitle("Cài đặt LangExtractor")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Title
        title_label = QLabel("⚙️ Cài đặt LangExtractor")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #333;")
        layout.addWidget(title_label)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # API Key tab
        self.api_key_widget = APIKeyWidget()
        self.tab_widget.addTab(self.api_key_widget, "🔑 API Key")
        
        # OCR tab
        self.ocr_widget = OCRSettingsWidget(self.config)
        self.tab_widget.addTab(self.ocr_widget, "📄 OCR")
        
        # Privacy tab
        self.privacy_widget = PrivacySettingsWidget(self.config)
        self.tab_widget.addTab(self.privacy_widget, "🔒 Privacy")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("Áp dụng")
        self.apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept_settings)
        self.ok_btn.setDefault(True)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
    def setup_styling(self):
        """Apply styling."""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            QPushButton:default {
                background-color: #0d6efd;
                border-color: #0d6efd;
                color: white;
            }
            QPushButton:default:hover {
                background-color: #0b5ed7;
                border-color: #0a58ca;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
    def apply_settings(self):
        """Apply settings without closing."""
        try:
            self.ocr_widget.save_settings()
            self.privacy_widget.save_settings()
            
            # Save config
            from core.utils import save_app_config
            save_app_config(self.config)
            
            QMessageBox.information(
                self, "Thành công",
                "Cài đặt đã được áp dụng!"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Lỗi",
                f"Không thể lưu cài đặt: {str(e)}"
            )
            
    def accept_settings(self):
        """Accept and close."""
        self.apply_settings()
        self.accept()
        
    def get_config(self) -> AppConfig:
        """Get updated config."""
        return self.config 