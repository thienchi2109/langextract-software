"""
Simple Preview Panel - chỉ hiển thị kết quả extraction đơn giản.

Không có charts, analytics hay metrics phức tạp - chỉ tập trung vào:
- Hiển thị dữ liệu đã trích từ từng file
- Summary đơn giản 
- Confidence scores cơ bản
"""

import logging
from typing import Dict, List, Optional, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea, QLabel,
    QFrame, QGroupBox, QGridLayout, QProgressBar, QTableWidget, 
    QTableWidgetItem, QHeaderView, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.models import ExtractionResult, ProcessingSession, FieldType, ProcessingStatus

logger = logging.getLogger(__name__)


class SimpleDataFieldWidget(QFrame):
    """Widget đơn giản để hiển thị một trường dữ liệu đã trích."""
    
    def __init__(self, field_name: str, field_type: FieldType, value: Any = None, 
                 confidence: float = 0.0, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.field_type = field_type
        self.value = value
        self.confidence = confidence
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI đơn giản."""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Field name với confidence
        header_layout = QHBoxLayout()
        
        name_label = QLabel(self.field_name)
        name_label.setStyleSheet("font-weight: bold; color: #333;")
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        # Confidence indicator đơn giản
        confidence_label = QLabel(f"{self.confidence:.1%}")
        if self.confidence >= 0.8:
            confidence_label.setStyleSheet("color: #28a745; font-weight: bold;")
        elif self.confidence >= 0.6:
            confidence_label.setStyleSheet("color: #ffc107; font-weight: bold;")
        else:
            confidence_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        header_layout.addWidget(confidence_label)
        
        layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(str(self.value) if self.value is not None else "—")
        value_label.setStyleSheet("color: #666; padding: 4px 0;")
        value_label.setWordWrap(True)
        layout.addWidget(value_label)


class SimpleFilePreviewWidget(QScrollArea):
    """Widget đơn giản để hiển thị kết quả extraction từ một file."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Main widget
        main_widget = QWidget()
        self.setWidget(main_widget)
        
        self.main_layout = QVBoxLayout(main_widget)
        self.main_layout.setSpacing(12)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Initial state
        self.show_empty_state()
        
    def show_empty_state(self):
        """Hiển thị trạng thái trống."""
        self.clear_layout()
        
        empty_label = QLabel("📄 Chọn file để xem kết quả extraction")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14pt;
                padding: 40px;
                border: 2px dashed #ccc;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
        """)
        self.main_layout.addWidget(empty_label)
        
    def clear_layout(self):
        """Xóa tất cả widgets trong layout."""
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def update_file_preview(self, result: ExtractionResult, template_fields: List[Dict]):
        """Cập nhật preview cho một file."""
        self.clear_layout()
        
        # File header
        file_label = QLabel(f"📄 {result.source_file}")
        file_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333; margin-bottom: 8px;")
        self.main_layout.addWidget(file_label)
        
        # Status
        if result.status == ProcessingStatus.COMPLETED:
            status_label = QLabel("✅ Extraction hoàn thành")
            status_label.setStyleSheet("color: #28a745; font-weight: bold;")
        elif result.status == ProcessingStatus.FAILED:
            status_label = QLabel("❌ Extraction thất bại")
            status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        else:
            status_label = QLabel("⏳ Đang xử lý...")
            status_label.setStyleSheet("color: #ffc107; font-weight: bold;")
            
        self.main_layout.addWidget(status_label)
        
        # Errors (if any)
        if result.errors:
            error_frame = QFrame()
            error_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 4px;
                    padding: 8px;
                    margin: 4px 0;
                }
            """)
            error_layout = QVBoxLayout(error_frame)
            
            error_title = QLabel("❌ Lỗi:")
            error_title.setStyleSheet("font-weight: bold; color: #721c24;")
            error_layout.addWidget(error_title)
            
            for error in result.errors:
                error_label = QLabel(f"• {error}")
                error_label.setStyleSheet("color: #721c24; margin-left: 16px;")
                error_label.setWordWrap(True)
                error_layout.addWidget(error_label)
                
            self.main_layout.addWidget(error_frame)
            
        # Extracted data
        if result.extracted_data:
            data_group = QGroupBox("📊 Dữ liệu đã trích")
            data_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
            
            data_layout = QVBoxLayout(data_group)
            data_layout.setSpacing(8)
            
            # Show extracted fields
            for field_def in template_fields:
                field_name = field_def['name']
                display_name = field_def.get('display_name', field_name)
                field_type = FieldType(field_def.get('type', 'text'))
                
                value = result.extracted_data.get(field_name)
                confidence = result.confidence_scores.get(field_name, 0.0)
                
                field_widget = SimpleDataFieldWidget(
                    field_name=display_name,
                    field_type=field_type,
                    value=value,
                    confidence=confidence
                )
                data_layout.addWidget(field_widget)
                
            self.main_layout.addWidget(data_group)
        
        # Processing info
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                margin: 4px 0;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        
        time_label = QLabel(f"⏱️ Thời gian xử lý: {result.processing_time:.2f}s")
        time_label.setStyleSheet("color: #6c757d; font-size: 10pt;")
        info_layout.addWidget(time_label)
        
        info_layout.addStretch()
        
        self.main_layout.addWidget(info_frame)
        self.main_layout.addStretch()


class SimpleSummaryWidget(QWidget):
    """Widget đơn giản để hiển thị tổng quan kết quả."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title_label = QLabel("📊 Tổng quan kết quả")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #333;")
        layout.addWidget(title_label)
        
        # Stats area
        self.stats_frame = QFrame()
        self.stats_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        layout.addWidget(self.stats_frame)
        
        # Table area for data
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                gridline-color: #eee;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                padding: 8px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)
        
        self.show_empty_state()
        
    def show_empty_state(self):
        """Hiển thị trạng thái trống."""
        stats_layout = QVBoxLayout(self.stats_frame)
        
        empty_label = QLabel("Chưa có dữ liệu để hiển thị")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("color: #666; font-size: 12pt; padding: 20px;")
        stats_layout.addWidget(empty_label)
        
        # Hide table
        self.table.setVisible(False)
        
    def update_summary(self, session: ProcessingSession):
        """Cập nhật tổng quan với session data."""
        # Clear existing layout
        while self.stats_frame.layout():
            old_layout = self.stats_frame.layout()
            for i in reversed(range(old_layout.count())):
                old_layout.itemAt(i).widget().deleteLater()
            self.stats_frame.setLayout(None)
            
        stats_layout = QGridLayout(self.stats_frame)
        
        # Basic stats
        total_files = len(session.files)
        completed_files = len([r for r in session.results if r.status == ProcessingStatus.COMPLETED])
        failed_files = len([r for r in session.results if r.status == ProcessingStatus.FAILED])
        
        # Stats widgets
        self.add_stat_widget(stats_layout, 0, 0, "📁 Tổng số file", str(total_files), "#007bff")
        self.add_stat_widget(stats_layout, 0, 1, "✅ Thành công", str(completed_files), "#28a745")
        self.add_stat_widget(stats_layout, 0, 2, "❌ Thất bại", str(failed_files), "#dc3545")
        
        # Average confidence
        if session.results:
            all_confidences = []
            for result in session.results:
                if result.confidence_scores:
                    all_confidences.extend(result.confidence_scores.values())
            
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
            self.add_stat_widget(stats_layout, 1, 0, "🎯 Độ tin cậy TB", f"{avg_confidence:.1%}", "#ffc107")
            
            # Processing time
            total_time = sum(r.processing_time for r in session.results)
            self.add_stat_widget(stats_layout, 1, 1, "⏱️ Tổng thời gian", f"{total_time:.1f}s", "#6c757d")
        
        # Show extracted data in table
        self.populate_data_table(session)
        self.table.setVisible(True)
        
    def add_stat_widget(self, layout, row, col, title, value, color):
        """Thêm stat widget vào layout."""
        stat_frame = QFrame()
        stat_frame.setStyleSheet(f"""
            QFrame {{
                border-left: 4px solid {color};
                background-color: #f8f9fa;
                padding: 12px;
                border-radius: 4px;
            }}
        """)
        
        stat_layout = QVBoxLayout(stat_frame)
        stat_layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 10pt; color: #666; font-weight: bold;")
        stat_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 16pt; color: {color}; font-weight: bold;")
        stat_layout.addWidget(value_label)
        
        layout.addWidget(stat_frame, row, col)
        
    def populate_data_table(self, session: ProcessingSession):
        """Populate table với extracted data."""
        if not session.results:
            return
            
        # Get all unique field names
        all_fields = set()
        field_display_names = {}
        
        for result in session.results:
            all_fields.update(result.extracted_data.keys())
            
        # Use template fields if available
        if session.template and session.template.fields:
            for field in session.template.fields:
                display_name = getattr(field, 'display_name', field.name)
                field_display_names[field.name] = display_name
                all_fields.add(field.name)
        
        all_fields = sorted(list(all_fields))
        
        # Setup table
        self.table.setRowCount(len(session.results))
        self.table.setColumnCount(len(all_fields) + 1)  # +1 for file name
        
        # Headers
        headers = ["File"] + [field_display_names.get(f, f) for f in all_fields]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Populate data
        for row, result in enumerate(session.results):
            # File name
            item = QTableWidgetItem(result.source_file.split('/')[-1])  # Just filename
            self.table.setItem(row, 0, item)
            
            # Field values
            for col, field_name in enumerate(all_fields, 1):
                value = result.extracted_data.get(field_name, "—")
                confidence = result.confidence_scores.get(field_name, 0.0)
                
                item = QTableWidgetItem(str(value))
                
                # Color based on confidence
                if confidence >= 0.8:
                    item.setBackground(Qt.GlobalColor.lightGreen)
                elif confidence >= 0.6:
                    item.setBackground(Qt.GlobalColor.yellow)
                elif confidence > 0:
                    item.setBackground(Qt.GlobalColor.red)
                    
                item.setToolTip(f"Confidence: {confidence:.1%}")
                self.table.setItem(row, col, item)
        
        # Auto-resize columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)


class SimplePreviewPanel(QWidget):
    """Panel preview đơn giản - chỉ tập trung vào hiển thị kết quả extraction."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_session = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI đơn giản."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # File preview tab
        self.file_preview = SimpleFilePreviewWidget()
        self.tab_widget.addTab(self.file_preview, "📄 Chi tiết file")
        
        # Summary tab  
        self.summary_preview = SimpleSummaryWidget()
        self.tab_widget.addTab(self.summary_preview, "📊 Tổng quan")
        
    def clear_preview(self):
        """Xóa tất cả preview data."""
        self.file_preview.show_empty_state()
        self.summary_preview.show_empty_state()
        self.current_session = None
        
    def update_file_preview(self, result: ExtractionResult, template_fields: List[Dict]):
        """Cập nhật preview cho file được chọn."""
        self.file_preview.update_file_preview(result, template_fields)
        
    def update_summary_preview(self, session: ProcessingSession):
        """Cập nhật tổng quan."""
        self.current_session = session
        self.summary_preview.update_summary(session)
        
    def start_processing_session(self):
        """Bắt đầu session processing mới."""
        self.clear_preview()
        
        # Switch to summary tab để xem progress
        self.tab_widget.setCurrentIndex(1) 