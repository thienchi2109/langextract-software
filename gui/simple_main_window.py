"""
Simple Main Window - workflow đơn giản cho automated report extraction.

Chỉ tập trung vào:
1. Import files (PDF/Word) với drag-drop
2. Configure schema (tiếng Việt)  
3. Process files (OCR + LangExtract)
4. Preview results (đơn giản)
5. Export Excel

Không có analytics dashboard phức tạp hay charts.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import Qt, Signal, QTimer, QMimeData, QUrl
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QProgressBar, QStatusBar, QMenuBar, QMenu, QToolBar, QLabel,
    QFrame, QSplitter, QMessageBox, QFileDialog, QApplication, QDialog
)
from PySide6.QtGui import QAction, QIcon, QDragEnterEvent, QDropEvent, QDragMoveEvent, QPainter, QPen
from gui.theme import get_theme_manager
from gui.simple_preview_panel import SimplePreviewPanel
from core.processing_orchestrator import ProcessingOrchestrator, ProcessingProgress
from core.excel_exporter import ExcelExporter
from core.aggregator import Aggregator
from datetime import datetime
from gui.schema_editor import SchemaEditor
from gui.settings_dialog import SettingsDialog
from core.utils import load_app_config, save_app_config
from core.models import AppConfig
from core.keychain import KeychainManager

logger = logging.getLogger(__name__)


class SimpleDropOverlay(QWidget):
    """Overlay đơn giản cho drag-and-drop."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.hide()
    
    def paintEvent(self, event):
        """Paint overlay với style đơn giản."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Semi-transparent background
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        # Dashed border
        pen = QPen(Qt.blue, 3, Qt.DashLine)
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect().adjusted(10, 10, -10, -10), 12, 12)
        
        # Text
        painter.setPen(Qt.blue)
        painter.setFont(self.font())
        text = "📁 Thả file PDF/Word vào đây"
        painter.drawText(self.rect(), Qt.AlignCenter, text)
    
    def show_overlay(self):
        """Show overlay."""
        if self.parent():
            self.resize(self.parent().size())
            self.move(0, 0)
        self.show()
        self.raise_()
    
    def hide_overlay(self):
        """Hide overlay."""
        self.hide()


class SimpleFileListWidget(QListWidget):
    """File list đơn giản."""
    
    files_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.supported_formats = {'.pdf', '.docx', '.doc'}
        self.setAlternatingRowColors(True)
        self.setDragDropMode(QListWidget.NoDragDrop)
    
    def add_file(self, file_path: str) -> bool:
        """Add file to list."""
        path = Path(file_path)
        
        # Check if file already exists
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == str(path):
                return False  # Duplicate
        
        # Check format
        if path.suffix.lower() not in self.supported_formats:
            return False  # Unsupported
        
        # Create item
        item = QListWidgetItem()
        item.setText(path.name)
        item.setData(Qt.UserRole, str(path))
        
        # Simple icon
        if path.suffix.lower() == '.pdf':
            item.setText(f"📄 {path.name}")
        else:
            item.setText(f"📝 {path.name}")
        
        item.setToolTip(str(path))
        
        self.addItem(item)
        self.files_changed.emit()
        
        logger.info(f"Added file: {path.name}")
        return True
    
    def remove_selected_files(self):
        """Remove selected files."""
        for item in self.selectedItems():
            row = self.row(item)
            self.takeItem(row)
        self.files_changed.emit()
    
    def clear_all_files(self):
        """Clear all files."""
        self.clear()
        self.files_changed.emit()
    
    def get_file_paths(self) -> List[str]:
        """Get all file paths."""
        paths = []
        for i in range(self.count()):
            item = self.item(i)
            paths.append(item.data(Qt.UserRole))
        return paths


class SimpleMainWindow(QMainWindow):
    """Main window đơn giản cho automated report extraction."""
    
    def __init__(self):
        super().__init__()
        self.theme_manager = get_theme_manager()
        self.drop_overlay = None
        
        # Current extraction template
        self.current_template = None
        
        # Load app configuration
        self.app_config = load_app_config()
        self.keychain_manager = KeychainManager()
        
        # Initialize processing orchestrator
        self.processing_orchestrator = ProcessingOrchestrator(self)
        
        self.setup_ui()
        self.setup_drag_drop()
        self.setup_theme()
        self.setup_connections()
        
        logger.info("Simple MainWindow initialized")
    
    def setup_ui(self):
        """Setup UI đơn giản."""
        self.setWindowTitle("LangExtractor - Trích xuất dữ liệu tự động")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Create header
        self.create_header(main_layout)
        
        # Create content area
        self.create_content_area(main_layout)
        
        # Create footer
        self.create_footer(main_layout)
        
        # Create menu
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
    
    def create_header(self, parent_layout):
        """Create simple header."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Box)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        # Title
        title_label = QLabel("🚀 Trích xuất dữ liệu tự động từ PDF/Word")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #333;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Theme toggle
        self.theme_toggle_btn = QPushButton("🎨")
        self.theme_toggle_btn.setToolTip("Đổi theme")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_toggle_btn)
        
        parent_layout.addWidget(header_frame)
    
    def create_content_area(self, parent_layout):
        """Create content area."""
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Files
        left_panel = self.create_file_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - Preview
        right_panel = self.create_preview_panel()
        content_splitter.addWidget(right_panel)
        
        # Set proportions
        content_splitter.setSizes([350, 650])
        
        parent_layout.addWidget(content_splitter)
    
    def create_file_panel(self) -> QWidget:
        """Create file panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        title_label = QLabel("📁 Files")
        title_label.setStyleSheet("font-size: 14pt; font-weight: 600; color: #333;")
        layout.addWidget(title_label)
        
        # File list
        self.file_list = SimpleFileListWidget()
        layout.addWidget(self.file_list)
        
        # Buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)
        
        self.add_files_btn = QPushButton("📁 Thêm file")
        self.add_files_btn.clicked.connect(self.add_files)
        button_layout.addWidget(self.add_files_btn)
        
        self.remove_files_btn = QPushButton("🗑️ Xóa file")
        self.remove_files_btn.clicked.connect(self.remove_files)
        self.remove_files_btn.setEnabled(False)
        button_layout.addWidget(self.remove_files_btn)
        
        self.clear_all_btn = QPushButton("🧹 Xóa tất cả")
        self.clear_all_btn.clicked.connect(self.clear_all_files)
        self.clear_all_btn.setEnabled(False)
        button_layout.addWidget(self.clear_all_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def create_preview_panel(self) -> QWidget:
        """Create preview panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        title_label = QLabel("👁️ Xem trước & Cấu hình")
        title_label.setStyleSheet("font-size: 14pt; font-weight: 600; color: #333;")
        layout.addWidget(title_label)
        
        # Preview panel
        self.preview_panel = SimplePreviewPanel()
        layout.addWidget(self.preview_panel, 1)
        
        # Action buttons
        action_layout = QVBoxLayout()
        action_layout.setSpacing(8)
        
        # Schema button
        self.schema_btn = QPushButton("⚙️ Cấu hình Schema")
        self.schema_btn.clicked.connect(self.open_schema_editor)
        self.schema_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5B21B6;
            }
        """)
        action_layout.addWidget(self.schema_btn)
        
        # Process button
        self.process_btn = QPushButton("🚀 Bắt đầu xử lý")
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:disabled {
                background-color: #9CA3AF;
                color: #6B7280;
            }
        """)
        action_layout.addWidget(self.process_btn)
        
        # Export button
        self.export_btn = QPushButton("📊 Xuất Excel")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #16A34A;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #15803D;
            }
            QPushButton:disabled {
                background-color: #9CA3AF;
                color: #6B7280;
            }
        """)
        action_layout.addWidget(self.export_btn)
        
        layout.addLayout(action_layout)
        
        return panel
    
    def create_footer(self, parent_layout):
        """Create simple footer."""
        footer_frame = QFrame()
        footer_frame.setFrameStyle(QFrame.Box)
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(8)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        footer_layout.addWidget(self.progress_bar)
        
        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        footer_layout.addWidget(self.progress_label)
        
        parent_layout.addWidget(footer_frame)
    
    def create_menu_bar(self):
        """Create simple menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        add_files_action = QAction("Thêm file...", self)
        add_files_action.setShortcut("Ctrl+O")
        add_files_action.triggered.connect(self.add_files)
        file_menu.addAction(add_files_action)
        
        file_menu.addSeparator()
        
        # Schema action
        schema_action = QAction("Cấu hình Schema...", self)
        schema_action.setShortcut("Ctrl+S")
        schema_action.triggered.connect(self.open_schema_editor)
        file_menu.addAction(schema_action)
        
        file_menu.addSeparator()
        
        # Export action
        export_excel_action = QAction("Xuất Excel...", self)
        export_excel_action.setShortcut("Ctrl+E")
        export_excel_action.triggered.connect(self.export_to_excel)
        export_excel_action.setEnabled(False)
        self.export_excel_action = export_excel_action
        file_menu.addAction(export_excel_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Thoát", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("Giới thiệu", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        settings_action = QAction("Cài đặt...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)
    
    def create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sẵn sàng - Thêm file và cấu hình schema để bắt đầu")
    
    def setup_drag_drop(self):
        """Setup drag drop."""
        self.setAcceptDrops(True)
        self.drop_overlay = SimpleDropOverlay(self)
    
    def setup_theme(self):
        """Setup theme."""
        app = QApplication.instance()
        current_theme = self.theme_manager.get_current_theme()
        self.theme_manager.apply_theme(app, current_theme)
    
    def setup_connections(self):
        """Setup connections."""
        self.file_list.files_changed.connect(self.update_ui_state)
        self.file_list.itemSelectionChanged.connect(self.update_ui_state)
        self.file_list.itemSelectionChanged.connect(self.on_file_selection_changed)
        
        # Processing signals
        self.processing_orchestrator.progress_updated.connect(self.on_processing_progress)
        self.processing_orchestrator.file_completed.connect(self.on_file_completed)
        self.processing_orchestrator.session_updated.connect(self.on_session_updated)
        self.processing_orchestrator.processing_completed.connect(self.on_processing_completed)
        self.processing_orchestrator.processing_error.connect(self.on_processing_error)
    
    def update_ui_state(self):
        """Update UI state."""
        has_files = self.file_list.count() > 0
        has_selection = len(self.file_list.selectedItems()) > 0
        has_template = self.current_template is not None
        
        self.remove_files_btn.setEnabled(has_selection)
        self.clear_all_btn.setEnabled(has_files)
        self.process_btn.setEnabled(has_files and has_template)
        
        # Update status
        file_count = self.file_list.count()
        if file_count == 0:
            self.status_bar.showMessage("Sẵn sàng - Thêm file và cấu hình schema để bắt đầu")
        elif not has_template:
            self.status_bar.showMessage(f"{file_count} file(s) đã tải - Cấu hình schema để tiếp tục")
        else:
            template_info = f"Schema: '{self.current_template.name}' ({len(self.current_template.fields)} trường)"
            self.status_bar.showMessage(f"{file_count} file(s) - {template_info} - Sẵn sàng xử lý!")
    
    def on_file_selection_changed(self):
        """Handle file selection changes."""
        selected_items = self.file_list.selectedItems()
        
        if not selected_items:
            self.preview_panel.clear_preview()
            return
        
        # Show mock preview for selected file
        selected_item = selected_items[0]
        file_path = selected_item.data(Qt.UserRole)
        self.show_simple_mock_preview(file_path)
    
    def show_simple_mock_preview(self, file_path: str):
        """Show simple mock preview."""
        from core.models import ExtractionResult, ProcessingStatus
        
        # Simple mock result
        mock_result = ExtractionResult(
            source_file=file_path,
            extracted_data={
                "ten_cong_ty": "Công ty Mẫu",
                "doanh_thu": "1,000,000,000 VND",
                "so_nhan_vien": "100 người"
            },
            confidence_scores={
                "ten_cong_ty": 0.95,
                "doanh_thu": 0.87,
                "so_nhan_vien": 0.72
            },
            processing_time=2.3,
            errors=[],
            status=ProcessingStatus.COMPLETED
        )
        
        # Simple template fields
        mock_template_fields = [
            {"name": "ten_cong_ty", "display_name": "Tên công ty", "type": "text"},
            {"name": "doanh_thu", "display_name": "Doanh thu", "type": "currency"},
            {"name": "so_nhan_vien", "display_name": "Số nhân viên", "type": "number"}
        ]
        
        self.preview_panel.update_file_preview(mock_result, mock_template_fields)
    
    # Rest of the methods remain similar but simplified...
    def open_schema_editor(self):
        """Open schema editor."""
        try:
            dialog = SchemaEditor(template=self.current_template, parent=self)
            
            if dialog.exec() == QDialog.Accepted:
                new_template = dialog.get_template()
                
                if new_template:
                    self.current_template = new_template
                    self.show_toast_message(f"Schema đã cấu hình: {len(new_template.fields)} trường", "success")
                    self.update_ui_state()
                    logger.info(f"Schema configured: {new_template.name}")
                else:
                    self.show_toast_message("Schema không hợp lệ", "warning")
        except Exception as e:
            self.show_toast_message(f"Lỗi mở schema editor: {str(e)}", "error")
            logger.error(f"Schema editor error: {e}", exc_info=True)
    
    def start_processing(self):
        """Start processing."""
        file_paths = self.file_list.get_file_paths()
        if not file_paths or not self.current_template:
            return
        
        # Kiểm tra API key nếu không ở offline mode
        if not self.app_config.offline_mode:
            if not self.check_api_key_available():
                reply = QMessageBox.question(
                    self, "Chưa có API key",
                    "Cần API key Gemini để sử dụng AI extraction.\n\n"
                    "Bạn có muốn mở cài đặt để nhập API key không?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.open_settings()
                    # Kiểm tra lại sau khi settings
                    if not self.check_api_key_available():
                        self.show_toast_message("Vẫn chưa có API key. Hủy xử lý.", "warning")
                        return
                else:
                    self.show_toast_message("Cần API key để xử lý. Hủy xử lý.", "warning")
                    return
        
        self.preview_panel.start_processing_session()
        self.start_new_processing()
        
        success = self.processing_orchestrator.start_processing(file_paths, self.current_template)
        
        if success:
            self.show_toast_message(f"Bắt đầu xử lý {len(file_paths)} file(s)...", "info")
            self.process_btn.setText("⏹️ Hủy xử lý")
            self.process_btn.clicked.disconnect()
            self.process_btn.clicked.connect(self.cancel_processing)
        else:
            self.show_toast_message("Lỗi bắt đầu xử lý", "error")
    
    def export_to_excel(self):
        """Export to Excel."""
        if not hasattr(self, 'completed_session') or not self.completed_session:
            self.show_toast_message("Chưa có dữ liệu để xuất", "warning")
            return
        
        try:
            export_path, _ = QFileDialog.getSaveFileName(
                self, "Xuất Excel",
                f"ket_qua_trich_xuat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if not export_path:
                return
            
            self.show_toast_message("Đang tạo file Excel...", "info")
            
            aggregator = Aggregator(self.completed_session.template)
            excel_exporter = ExcelExporter(self.completed_session.template)
            
            aggregation_result = aggregator.aggregate_results(self.completed_session.results)
            output_file = excel_exporter.export_results(aggregation_result, export_path)
            
            self.show_toast_message("Xuất Excel thành công!", "success")
            
            # Ask to open file
            reply = QMessageBox.question(
                self, "Xuất Excel thành công",
                f"File đã được xuất:\n{output_file}\n\nBạn có muốn mở file không?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                import os
                os.startfile(output_file)
            
        except Exception as e:
            self.show_toast_message(f"Lỗi xuất Excel: {str(e)}", "error")
            logger.error(f"Excel export error: {e}", exc_info=True)
    
    # Simplified event handlers
    def start_new_processing(self):
        """Reset for new processing."""
        self.export_btn.setEnabled(False)
        if hasattr(self, 'export_excel_action'):
            self.export_excel_action.setEnabled(False)
        if hasattr(self, 'completed_session'):
            delattr(self, 'completed_session')
    
    def on_processing_progress(self, progress: ProcessingProgress):
        """Handle progress."""
        self.show_progress(f"Đang xử lý {progress.current_file_name}...", 
                          progress.current_file, progress.total_files)
    
    def on_file_completed(self, result):
        """Handle file completion."""
        pass
    
    def on_session_updated(self, session):
        """Handle session updates."""
        self.preview_panel.update_summary_preview(session)
    
    def on_processing_completed(self, session):
        """Handle completion."""
        self.show_toast_message(f"Hoàn thành! Đã xử lý {len(session.results)} file(s)", "success")
        self.preview_panel.update_summary_preview(session)
        
        self.export_btn.setEnabled(True)
        if hasattr(self, 'export_excel_action'):
            self.export_excel_action.setEnabled(True)
        
        self.completed_session = session
        self._reset_processing_ui()
        self.status_bar.showMessage(f"Hoàn thành: {len(session.results)} file(s) - Sẵn sàng xuất Excel!")
    
    def on_processing_error(self, error_message: str):
        """Handle errors."""
        self.show_toast_message(f"Lỗi xử lý: {error_message}", "error")
        self._reset_processing_ui()
    
    def _reset_processing_ui(self):
        """Reset processing UI."""
        self.process_btn.setText("🚀 Bắt đầu xử lý")
        self.process_btn.clicked.disconnect()
        self.process_btn.clicked.connect(self.start_processing)
        self.hide_progress()
    
    def cancel_processing(self):
        """Cancel processing."""
        self.processing_orchestrator.cancel_processing()
        self.show_toast_message("Đã hủy xử lý", "warning")
        self._reset_processing_ui()
    
    # Simple utility methods
    def add_files(self):
        """Add files dialog."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Supported files (*.pdf *.docx *.doc)")
        
        if file_dialog.exec():
            added_count = 0
            for file_path in file_dialog.selectedFiles():
                if self.file_list.add_file(file_path):
                    added_count += 1
            
            if added_count > 0:
                self.show_toast_message(f"Đã thêm {added_count} file(s)", "success")
    
    def remove_files(self):
        """Remove selected files."""
        count = len(self.file_list.selectedItems())
        if count > 0:
            self.file_list.remove_selected_files()
            self.show_toast_message(f"Đã xóa {count} file(s)", "info")
    
    def clear_all_files(self):
        """Clear all files."""
        reply = QMessageBox.question(
            self, "Xóa tất cả file",
            "Bạn có chắc muốn xóa tất cả file?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            count = self.file_list.count()
            self.file_list.clear_all_files()
            self.show_toast_message(f"Đã xóa {count} file(s)", "info")
    
    def show_toast_message(self, message: str, message_type: str = "info"):
        """Show simple toast."""
        self.status_bar.showMessage(message, 3000)
        
        if message_type == "success":
            logger.info(f"Toast: {message}")
        elif message_type == "warning":
            logger.warning(f"Toast: {message}")
        elif message_type == "error":
            logger.error(f"Toast: {message}")
        else:
            logger.info(f"Toast: {message}")
    
    def show_progress(self, message: str, current: int, total: int):
        """Show progress."""
        self.progress_label.setText(message)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.progress_label.setVisible(True)
        self.progress_bar.setVisible(True)
    
    def hide_progress(self):
        """Hide progress."""
        self.progress_label.setVisible(False)
        self.progress_bar.setVisible(False)
    
    def toggle_theme(self):
        """Toggle theme."""
        app = QApplication.instance()
        self.theme_manager.toggle_theme(app)
    
    def show_about(self):
        """Show about."""
        QMessageBox.about(
            self, "Giới thiệu LangExtractor",
            "LangExtractor - Trích xuất dữ liệu tự động\n\n"
            "Công cụ đơn giản để trích xuất dữ liệu có cấu trúc từ PDF và Word\n"
            "sử dụng OCR và AI.\n\n"
            "Workflow đơn giản:\n"
            "1. Import file PDF/Word\n"
            "2. Cấu hình Schema (tiếng Việt)\n"
            "3. Xử lý với OCR + AI\n"
            "4. Xem trước kết quả\n"
            "5. Xuất Excel"
        )
    
    def open_settings(self):
        """Open settings dialog."""
        try:
            dialog = SettingsDialog(self.app_config, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.app_config = dialog.get_config()
                self.show_toast_message("Cài đặt đã được lưu", "success")
                logger.info("Settings saved")
        except Exception as e:
            self.show_toast_message(f"Lỗi mở cài đặt: {str(e)}", "error")
            logger.error(f"Settings dialog error: {e}", exc_info=True)
    
    def check_api_key_available(self) -> bool:
        """Kiểm tra xem API key có sẵn không."""
        try:
            api_key = self.keychain_manager.load_api_key()
            return bool(api_key and api_key.strip())
        except Exception as e:
            logger.error(f"Error checking API key: {e}")
            return False
    
    # Drag drop events
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            valid_files = self.get_valid_files_from_urls(event.mimeData().urls())
            if valid_files:
                event.acceptProposedAction()
                self.drop_overlay.show_overlay()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave."""
        self.drop_overlay.hide_overlay()
        super().dragLeaveEvent(event)
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop."""
        self.drop_overlay.hide_overlay()
        
        if event.mimeData().hasUrls():
            valid_files = self.get_valid_files_from_urls(event.mimeData().urls())
            added_count = 0
            
            for file_path in valid_files:
                if self.file_list.add_file(file_path):
                    added_count += 1
            
            if added_count > 0:
                self.show_toast_message(f"Đã thêm {added_count} file(s)", "success")
            
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def get_valid_files_from_urls(self, urls: List[QUrl]) -> List[str]:
        """Get valid files from URLs."""
        valid_files = []
        supported_formats = {'.pdf', '.docx', '.doc'}
        
        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()
                path = Path(file_path)
                
                if path.is_file() and path.suffix.lower() in supported_formats:
                    valid_files.append(file_path)
        
        return valid_files
    
    def closeEvent(self, event):
        """Handle close."""
        logger.info("SimpleMainWindow closing")
        event.accept() 