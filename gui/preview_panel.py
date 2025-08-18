"""
Preview panel for displaying extraction results with modern, professional UI.

Features:
- Per-file preview with extracted data and confidence scores
- Summary preview with aggregated statistics  
- Highlighting for missing or low-confidence extractions
- Modern card-based layout with theme support
- Real-time updates during processing
- Interactive elements and enhanced data formatting
- Performance optimizations for large datasets
"""

import logging
from typing import Dict, List, Optional, Any
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea, QLabel,
    QFrame, QProgressBar, QGroupBox, QGridLayout, QSizePolicy, QSpacerItem,
    QPushButton, QToolTip, QTextEdit, QSplitter
)
from PySide6.QtGui import QPainter, QPen, QBrush, QFont, QFontMetrics, QCursor, QTextOption

from core.models import ExtractionResult, ProcessingSession, ProcessingStatus, FieldType
from gui.theme import get_theme_manager

logger = logging.getLogger(__name__)


class ConfidenceIndicator(QWidget):
    """
    Visual confidence score indicator with color coding and animation.
    
    Color scheme:
    - Green (●●●●●): >= 0.8 (High confidence)
    - Yellow (●●●○○): 0.5-0.8 (Medium confidence) 
    - Red (●○○○○): < 0.5 (Low confidence)
    - Gray (○○○○○): No data/Not processed
    """
    
    def __init__(self, confidence: float = 0.0, parent=None):
        super().__init__(parent)
        self.confidence = confidence
        self.theme_manager = get_theme_manager()
        self.setFixedSize(100, 20)
        self.setToolTip(f"Confidence: {confidence:.1%}")
    
    def set_confidence(self, confidence: float):
        """Update confidence score and refresh display."""
        self.confidence = confidence
        self.setToolTip(f"Confidence: {confidence:.1%}")
        self.update()
    
    def paintEvent(self, event):
        """Paint the confidence indicator dots."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate dot properties
        dot_size = 12
        dot_spacing = 18
        start_x = 5
        y_center = self.height() // 2
        
        # Determine color based on confidence
        if self.confidence >= 0.8:
            active_color = "#16A34A"  # Green
        elif self.confidence >= 0.5:
            active_color = "#F59E0B"  # Yellow/Orange
        else:
            active_color = "#EF4444"  # Red
        
        inactive_color = "#E5E7EB"  # Light gray
        
        # Calculate number of filled dots (out of 5)
        filled_dots = int(self.confidence * 5)
        
        # Draw 5 dots
        for i in range(5):
            x = start_x + i * dot_spacing
            
            if i < filled_dots:
                painter.setBrush(QBrush(active_color))
                painter.setPen(QPen(active_color))
            else:
                painter.setBrush(QBrush(inactive_color))
                painter.setPen(QPen(inactive_color))
            
            painter.drawEllipse(x, y_center - dot_size//2, dot_size, dot_size)


class DataFieldWidget(QFrame):
    """
    Enhanced widget for displaying a single extraction field with value and confidence.
    
    Features:
    - Rich data formatting based on field type
    - Interactive tooltips with detailed information
    - Copy-to-clipboard functionality
    - Validation status indicators
    - Animated confidence updates
    """
    
    field_clicked = Signal(str, Any)  # field_name, value
    
    def __init__(self, field_name: str, field_type: FieldType, value: Any = None, 
                 confidence: float = 0.0, is_missing: bool = False, 
                 is_optional: bool = False, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.field_type = field_type
        self.value = value
        self.confidence = confidence
        self.is_missing = is_missing
        self.is_optional = is_optional
        self.theme_manager = get_theme_manager()
        
        self.setup_ui()
        self.update_display()
        self.setup_interactions()
    
    def setup_ui(self):
        """Setup the enhanced field widget UI."""
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        # Header layout with field name and optional indicator
        header_layout = QHBoxLayout()
        
        # Field name with optional indicator
        name_text = self.field_name
        if self.is_optional:
            name_text += " (optional)"
        
        self.name_label = QLabel(name_text)
        self.name_label.setStyleSheet("font-weight: 600; color: @text; font-size: 11pt;")
        header_layout.addWidget(self.name_label)
        
        header_layout.addStretch()
        
        # Confidence indicator
        self.confidence_indicator = ConfidenceIndicator(self.confidence)
        header_layout.addWidget(self.confidence_indicator)
        
        layout.addLayout(header_layout)
        
        # Value display area
        value_layout = QHBoxLayout()
        
        # Value label with enhanced formatting
        self.value_label = QLabel()
        self.value_label.setWordWrap(True)
        self.value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.value_label.setMinimumHeight(24)
        value_layout.addWidget(self.value_label, 1)
        
        # Copy button (initially hidden)
        self.copy_btn = QPushButton("📋")
        self.copy_btn.setFixedSize(24, 24)
        self.copy_btn.setToolTip("Copy value to clipboard")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid @border;
                border-radius: 4px;
                background: @card;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: @primary;
                color: white;
            }
        """)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.hide()
        value_layout.addWidget(self.copy_btn)
        
        layout.addLayout(value_layout)
        
        # Status indicator (for validation issues)
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 9pt; color: @muted;")
        self.status_label.hide()
        layout.addWidget(self.status_label)
        
        # Apply theme styling
        self.apply_theme()
    
    def setup_interactions(self):
        """Setup interactive behaviors."""
        # Mouse hover events
        self.setMouseTracking(True)
        
        # Click handler
        self.mousePressEvent = self.on_click
    
    def enterEvent(self, event):
        """Handle mouse enter event."""
        if not self.is_missing and self.value is not None:
            self.copy_btn.show()
        
        # Show detailed tooltip
        self.show_detailed_tooltip()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event."""
        self.copy_btn.hide()
        super().leaveEvent(event)
    
    def on_click(self, event):
        """Handle click events."""
        if event.button() == Qt.LeftButton:
            self.field_clicked.emit(self.field_name, self.value)
    
    def copy_to_clipboard(self):
        """Copy field value to clipboard."""
        if self.value is not None:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(str(self.value))
            
            # Show temporary feedback
            self.copy_btn.setText("✓")
            QTimer.singleShot(1000, lambda: self.copy_btn.setText("📋"))
    
    def show_detailed_tooltip(self):
        """Show detailed tooltip with field information."""
        tooltip_text = f"""<b>{self.field_name}</b><br/>
Type: {self.field_type.value}<br/>
Confidence: {self.confidence:.1%}<br/>"""
        
        if self.is_optional:
            tooltip_text += "Optional field<br/>"
        
        if self.is_missing:
            tooltip_text += "<span style='color: #EF4444;'>Value not found</span>"
        elif self.value is not None:
            tooltip_text += f"Value: {self.get_formatted_value()}"
        
        self.setToolTip(tooltip_text)
    
    def get_formatted_value(self) -> str:
        """Get formatted value for display."""
        if self.value is None:
            return "N/A"
        
        if self.field_type == FieldType.CURRENCY:
            if isinstance(self.value, (int, float)):
                return f"${self.value:,.2f}"
            return str(self.value)
        elif self.field_type == FieldType.NUMBER:
            if isinstance(self.value, (int, float)):
                if isinstance(self.value, float) and self.value.is_integer():
                    return f"{int(self.value):,}"
                elif isinstance(self.value, float):
                    return f"{self.value:,.1f}"
                return f"{self.value:,}"
            return str(self.value)
        elif self.field_type == FieldType.DATE:
            # Enhanced date formatting
            return str(self.value)
        else:
            # Text field with length indication for long values
            text = str(self.value)
            if len(text) > 50:
                return f"{text[:47]}... ({len(text)} chars)"
            return text
    
    def apply_theme(self):
        """Apply enhanced theme-based styling."""
        base_style = """
            DataFieldWidget {
                border-radius: 8px;
                padding: 4px;
            }
        """
        
        if self.is_missing:
            self.setStyleSheet(base_style + """
                DataFieldWidget {
                    background-color: #FEF2F2;
                    border: 2px solid #FECACA;
                }
            """)
        elif self.confidence < 0.5:
            self.setStyleSheet(base_style + """
                DataFieldWidget {
                    background-color: #FFFBEB;
                    border: 2px solid #FED7AA;
                }
            """)
        elif self.confidence < 0.8:
            self.setStyleSheet(base_style + """
                DataFieldWidget {
                    background-color: #F0F9FF;
                    border: 2px solid #BAE6FD;
                }
            """)
        else:
            self.setStyleSheet(base_style + """
                DataFieldWidget {
                    background-color: @card;
                    border: 2px solid @border;
                }
                DataFieldWidget:hover {
                    border-color: @primary;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
            """)
    
    def update_display(self):
        """Update the display with current data."""
        if self.is_missing or self.value is None:
            self.value_label.setText("Not found")
            self.value_label.setStyleSheet("color: #9CA3AF; font-style: italic; font-size: 11pt;")
            
            if not self.is_optional:
                self.status_label.setText("⚠ Required field missing")
                self.status_label.setStyleSheet("color: #EF4444; font-size: 9pt;")
                self.status_label.show()
        else:
            formatted_value = self.get_formatted_value()
            self.value_label.setText(formatted_value)
            self.value_label.setStyleSheet("color: @text; font-size: 11pt; font-weight: 500;")
            
            # Show validation status for low confidence
            if self.confidence < 0.5:
                self.status_label.setText("⚠ Low confidence - please verify")
                self.status_label.setStyleSheet("color: #F59E0B; font-size: 9pt;")
                self.status_label.show()
            elif self.confidence < 0.7:
                self.status_label.setText("ℹ Medium confidence")
                self.status_label.setStyleSheet("color: #3B82F6; font-size: 9pt;")
                self.status_label.show()
        
        self.confidence_indicator.set_confidence(self.confidence)
        self.apply_theme()
    
    def animate_confidence_update(self, new_confidence: float):
        """Animate confidence indicator update."""
        # Create animation for confidence update
        self.confidence = new_confidence
        self.confidence_indicator.set_confidence(new_confidence)
        self.update_display()


class FilePreviewWidget(QScrollArea):
    """
    Widget for displaying extraction results from a single file.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_result: Optional[ExtractionResult] = None
        self.theme_manager = get_theme_manager()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the file preview UI."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create main content widget
        self.content_widget = QWidget()
        self.setWidget(self.content_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(16)
        
        # File info section
        self.create_file_info_section()
        
        # Extracted data section
        self.create_data_section()
        
        # Show empty state initially
        self.show_empty_state()
    
    def create_file_info_section(self):
        """Create file information display section."""
        self.file_info_group = QGroupBox("File Information")
        file_info_layout = QVBoxLayout(self.file_info_group)
        
        # File name and status
        self.file_name_label = QLabel("No file selected")
        self.file_name_label.setStyleSheet("font-size: 14pt; font-weight: 600; color: @text;")
        file_info_layout.addWidget(self.file_name_label)
        
        # Status and timing info
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Not processed")
        self.processing_time_label = QLabel("Processing time: --")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.processing_time_label)
        file_info_layout.addLayout(status_layout)
        
        self.main_layout.addWidget(self.file_info_group)
    
    def create_data_section(self):
        """Create extracted data display section."""
        self.data_group = QGroupBox("Extracted Data")
        self.data_layout = QVBoxLayout(self.data_group)
        self.data_layout.setSpacing(8)
        
        self.main_layout.addWidget(self.data_group)
        
        # Add stretch to push content to top
        self.main_layout.addStretch()
    
    def show_empty_state(self):
        """Show empty state when no file is selected."""
        self.file_name_label.setText("No file selected")
        self.status_label.setText("Status: Select a file to preview results")
        self.processing_time_label.setText("Processing time: --")
        
        # Clear data section
        self.clear_data_section()
        
        # Add empty state message
        empty_label = QLabel("Select a file from the list to preview extraction results")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("color: #6B7280; font-style: italic; padding: 40px;")
        self.data_layout.addWidget(empty_label)
    
    def clear_data_section(self):
        """Clear all widgets from the data section."""
        while self.data_layout.count():
            child = self.data_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def update_preview(self, result: ExtractionResult, template_fields: List[Dict]):
        """Update preview with extraction result and enhanced visual feedback."""
        self.current_result = result
        
        # Update file info with enhanced status display
        file_name = result.source_file.split('/')[-1].split('\\')[-1]  # Get filename only
        self.file_name_label.setText(file_name)
        
        # Enhanced status display with progress indication
        self.update_status_display(result)
        
        # Update processing time with performance metrics
        self.update_timing_display(result)
        
        # Update data section based on status
        self.clear_data_section()
        
        if result.status == ProcessingStatus.PROCESSING:
            self.show_processing_state(result, template_fields)
        elif result.status == ProcessingStatus.FAILED:
            self.show_error_state(result.errors)
        elif result.status == ProcessingStatus.PENDING:
            self.show_pending_state()
        else:
            # Completed or other final states
            self.show_extracted_data(result, template_fields)
    
    def update_status_display(self, result: ExtractionResult):
        """Update status display with enhanced visual feedback."""
        status_icons = {
            ProcessingStatus.COMPLETED: "✅",
            ProcessingStatus.PROCESSING: "⏳",
            ProcessingStatus.FAILED: "❌",
            ProcessingStatus.PENDING: "⏸️",
            ProcessingStatus.CANCELLED: "⏹️"
        }
        
        status_colors = {
            ProcessingStatus.COMPLETED: "#16A34A",
            ProcessingStatus.PROCESSING: "#F59E0B", 
            ProcessingStatus.FAILED: "#EF4444",
            ProcessingStatus.PENDING: "#6B7280",
            ProcessingStatus.CANCELLED: "#6B7280"
        }
        
        status_descriptions = {
            ProcessingStatus.COMPLETED: "Processing completed successfully",
            ProcessingStatus.PROCESSING: "Currently processing...",
            ProcessingStatus.FAILED: "Processing failed",
            ProcessingStatus.PENDING: "Waiting to be processed",
            ProcessingStatus.CANCELLED: "Processing was cancelled"
        }
        
        status_icon = status_icons.get(result.status, "❓")
        status_color = status_colors.get(result.status, "#6B7280")
        status_desc = status_descriptions.get(result.status, "Unknown status")
        
        self.status_label.setText(f"{status_icon} {status_desc}")
        self.status_label.setStyleSheet(f"color: {status_color}; font-weight: 600; font-size: 11pt;")
        
        # Add progress bar for processing status
        if result.status == ProcessingStatus.PROCESSING:
            if not hasattr(self, 'progress_bar'):
                self.progress_bar = QProgressBar()
                self.progress_bar.setRange(0, 0)  # Indeterminate progress
                self.progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 2px solid #E5E7EB;
                        border-radius: 4px;
                        text-align: center;
                        height: 16px;
                    }
                    QProgressBar::chunk {
                        background-color: #3B82F6;
                        border-radius: 2px;
                    }
                """)
                # Insert progress bar after status label
                layout = self.file_info_group.layout()
                layout.insertWidget(2, self.progress_bar)
            self.progress_bar.show()
        else:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.hide()
    
    def update_timing_display(self, result: ExtractionResult):
        """Update timing display with performance metrics."""
        if result.processing_time > 0:
            # Categorize performance
            if result.processing_time < 2.0:
                performance = "Fast"
                color = "#16A34A"
            elif result.processing_time < 5.0:
                performance = "Normal"
                color = "#F59E0B"
            else:
                performance = "Slow"
                color = "#EF4444"
            
            time_text = f"Processing time: {result.processing_time:.1f}s ({performance})"
            self.processing_time_label.setText(time_text)
            self.processing_time_label.setStyleSheet(f"color: {color}; font-size: 10pt;")
        else:
            self.processing_time_label.setText("Processing time: --")
            self.processing_time_label.setStyleSheet("color: #6B7280; font-size: 10pt;")
    
    def show_processing_state(self, result: ExtractionResult, template_fields: List[Dict]):
        """Show processing state with partial results."""
        processing_label = QLabel("🔄 Processing in progress...")
        processing_label.setStyleSheet("color: #F59E0B; font-weight: 600; font-size: 12pt; padding: 16px;")
        processing_label.setAlignment(Qt.AlignCenter)
        self.data_layout.addWidget(processing_label)
        
        # Show any partial results that are available
        if result.extracted_data:
            partial_label = QLabel("Partial results available:")
            partial_label.setStyleSheet("color: #6B7280; font-weight: 600; margin-top: 16px;")
            self.data_layout.addWidget(partial_label)
            
            for field_def in template_fields:
                field_name = field_def['name']
                value = result.extracted_data.get(field_name)
                confidence = result.confidence_scores.get(field_name, 0.0)
                
                if value is not None:
                    field_widget = DataFieldWidget(
                        field_name=field_name,
                        field_type=FieldType(field_def.get('type', 'text')),
                        value=value,
                        confidence=confidence,
                        is_missing=False,
                        is_optional=field_def.get('optional', False)
                    )
                    self.data_layout.addWidget(field_widget)
    
    def show_pending_state(self):
        """Show pending processing state."""
        pending_label = QLabel("⏸️ Waiting to be processed")
        pending_label.setStyleSheet("color: #6B7280; font-style: italic; font-size: 12pt; padding: 40px;")
        pending_label.setAlignment(Qt.AlignCenter)
        self.data_layout.addWidget(pending_label)
        
        info_label = QLabel("This file will be processed when extraction starts.")
        info_label.setStyleSheet("color: #9CA3AF; font-size: 10pt; padding: 0 40px;")
        info_label.setAlignment(Qt.AlignCenter)
        self.data_layout.addWidget(info_label)
    
    def show_error_state(self, errors: List[str]):
        """Show error state when processing failed."""
        error_label = QLabel("Processing failed with the following errors:")
        error_label.setStyleSheet("color: #EF4444; font-weight: 600; margin-bottom: 8px;")
        self.data_layout.addWidget(error_label)
        
        for error in errors:
            error_item = QLabel(f"• {error}")
            error_item.setWordWrap(True)
            error_item.setStyleSheet("color: #EF4444; margin-left: 16px; margin-bottom: 4px;")
            self.data_layout.addWidget(error_item)
    
    def show_extracted_data(self, result: ExtractionResult, template_fields: List[Dict]):
        """Show extracted data with enhanced confidence indicators and interactions."""
        if not template_fields:
            no_template_label = QLabel("No template fields defined")
            no_template_label.setStyleSheet("color: #6B7280; font-style: italic;")
            self.data_layout.addWidget(no_template_label)
            return
        
        # Create statistics header
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.Box)
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        # Calculate statistics
        total_fields = len(template_fields)
        extracted_fields = sum(1 for field in template_fields 
                             if result.extracted_data.get(field['name']) is not None)
        avg_confidence = 0.0
        if result.confidence_scores:
            avg_confidence = sum(result.confidence_scores.values()) / len(result.confidence_scores)
        
        # Add statistics
        stats_layout.addWidget(QLabel(f"Fields extracted: {extracted_fields}/{total_fields}"))
        stats_layout.addStretch()
        stats_layout.addWidget(QLabel(f"Avg. confidence: {avg_confidence:.1%}"))
        
        self.data_layout.addWidget(stats_frame)
        
        # Group fields by confidence level for better organization
        high_conf_fields = []
        med_conf_fields = []
        low_conf_fields = []
        missing_fields = []
        
        for field_def in template_fields:
            field_name = field_def['name']
            value = result.extracted_data.get(field_name)
            confidence = result.confidence_scores.get(field_name, 0.0)
            is_missing = value is None or value == ""
            
            if is_missing:
                missing_fields.append((field_def, value, confidence, is_missing))
            elif confidence >= 0.8:
                high_conf_fields.append((field_def, value, confidence, is_missing))
            elif confidence >= 0.5:
                med_conf_fields.append((field_def, value, confidence, is_missing))
            else:
                low_conf_fields.append((field_def, value, confidence, is_missing))
        
        # Create grouped sections
        sections = [
            ("High Confidence", high_conf_fields, "#DEF7EC"),
            ("Medium Confidence", med_conf_fields, "#FEF3C7"),  
            ("Low Confidence", low_conf_fields, "#FEE2E2"),
            ("Missing Data", missing_fields, "#F3F4F6")
        ]
        
        for section_name, fields, bg_color in sections:
            if not fields:
                continue
                
            # Section header
            section_label = QLabel(f"{section_name} ({len(fields)})")
            section_label.setStyleSheet(f"""
                font-weight: 600; 
                font-size: 12pt; 
                color: @text; 
                padding: 8px;
                background-color: {bg_color};
                border-radius: 4px;
                margin-top: 8px;
            """)
            self.data_layout.addWidget(section_label)
            
            # Add fields in this section
            for field_def, value, confidence, is_missing in fields:
                field_widget = DataFieldWidget(
                    field_name=field_def['name'],
                    field_type=FieldType(field_def.get('type', 'text')),
                    value=value,
                    confidence=confidence,
                    is_missing=is_missing,
                    is_optional=field_def.get('optional', False)
                )
                
                # Connect field click signal
                field_widget.field_clicked.connect(self.on_field_clicked)
                
                self.data_layout.addWidget(field_widget)
    
    def on_field_clicked(self, field_name: str, value: Any):
        """Handle field click events."""
        logger.debug(f"Field clicked: {field_name} = {value}")
        
        # Could trigger detail view, editing, or other interactions
        # For now, just log the interaction


class SummaryPreviewWidget(QWidget):
    """
    Widget for displaying aggregated statistics and data quality metrics.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_session: Optional[ProcessingSession] = None
        self.theme_manager = get_theme_manager()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the summary preview UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Processing statistics section
        self.create_processing_stats_section(layout)
        
        # Data quality section
        self.create_data_quality_section(layout)
        
        # Field statistics section
        self.create_field_stats_section(layout)
        
        layout.addStretch()
        
        # Show empty state initially
        self.show_empty_state()
    
    def create_processing_stats_section(self, parent_layout):
        """Create processing statistics section."""
        self.stats_group = QGroupBox("Processing Statistics")
        stats_layout = QGridLayout(self.stats_group)
        
        # Create stat labels
        self.total_files_label = QLabel("0")
        self.completed_files_label = QLabel("0")
        self.failed_files_label = QLabel("0")
        self.avg_processing_time_label = QLabel("--")
        
        # Add to grid
        stats_layout.addWidget(QLabel("Total Files:"), 0, 0)
        stats_layout.addWidget(self.total_files_label, 0, 1)
        stats_layout.addWidget(QLabel("Completed:"), 1, 0)
        stats_layout.addWidget(self.completed_files_label, 1, 1)
        stats_layout.addWidget(QLabel("Failed:"), 0, 2)
        stats_layout.addWidget(self.failed_files_label, 0, 3)
        stats_layout.addWidget(QLabel("Avg. Time:"), 1, 2)
        stats_layout.addWidget(self.avg_processing_time_label, 1, 3)
        
        parent_layout.addWidget(self.stats_group)
    
    def create_data_quality_section(self, parent_layout):
        """Create data quality metrics section."""
        self.quality_group = QGroupBox("Data Quality")
        quality_layout = QVBoxLayout(self.quality_group)
        
        # Quality indicators will be added dynamically
        self.quality_layout = quality_layout
        
        parent_layout.addWidget(self.quality_group)
    
    def create_field_stats_section(self, parent_layout):
        """Create field statistics section."""
        self.field_stats_group = QGroupBox("Field Statistics")
        self.field_stats_layout = QVBoxLayout(self.field_stats_group)
        
        parent_layout.addWidget(self.field_stats_group)
    
    def show_empty_state(self):
        """Show empty state when no session is available."""
        # Clear existing content
        self.clear_dynamic_content()
        
        # Add empty state message to quality section
        empty_label = QLabel("No processing session data available")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("color: #6B7280; font-style: italic; padding: 20px;")
        self.quality_layout.addWidget(empty_label)
    
    def clear_dynamic_content(self):
        """Clear dynamically generated content."""
        # Clear quality section
        while self.quality_layout.count():
            child = self.quality_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Clear field stats section
        while self.field_stats_layout.count():
            child = self.field_stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def update_summary(self, session: ProcessingSession):
        """Update summary with processing session data."""
        self.current_session = session
        
        # Update processing statistics
        total_files = len(session.files)
        completed_files = session.get_completed_count()
        failed_files = session.get_failed_count()
        
        self.total_files_label.setText(str(total_files))
        self.completed_files_label.setText(str(completed_files))
        self.completed_files_label.setStyleSheet("color: #16A34A; font-weight: 600;")
        self.failed_files_label.setText(str(failed_files))
        
        if failed_files > 0:
            self.failed_files_label.setStyleSheet("color: #EF4444; font-weight: 600;")
        else:
            self.failed_files_label.setStyleSheet("color: #16A34A; font-weight: 600;")
        
        # Calculate average processing time
        completed_results = [r for r in session.results if r.status == ProcessingStatus.COMPLETED]
        if completed_results:
            avg_time = sum(r.processing_time for r in completed_results) / len(completed_results)
            self.avg_processing_time_label.setText(f"{avg_time:.1f}s")
        else:
            self.avg_processing_time_label.setText("--")
        
        # Update data quality and field statistics
        self.update_data_quality(session)
        self.update_field_statistics(session)
    
    def update_data_quality(self, session: ProcessingSession):
        """Update data quality indicators with enhanced visualization."""
        self.clear_dynamic_content()
        
        if not session.results:
            self.show_empty_state()
            return
        
        # Calculate comprehensive quality metrics
        completed_results = [r for r in session.results if r.status == ProcessingStatus.COMPLETED]
        
        if not completed_results:
            no_data_label = QLabel("No completed extractions yet")
            no_data_label.setStyleSheet("color: #6B7280; font-style: italic;")
            self.quality_layout.addWidget(no_data_label)
            return
        
        # Create quality metrics container
        quality_container = QWidget()
        quality_container_layout = QVBoxLayout(quality_container)
        
        # Overall quality score
        self.create_overall_quality_display(completed_results, quality_container_layout)
        
        # Confidence distribution
        self.create_confidence_distribution(completed_results, quality_container_layout)
        
        # Data completeness metrics
        self.create_completeness_metrics(session, completed_results, quality_container_layout)
        
        self.quality_layout.addWidget(quality_container)
    
    def create_overall_quality_display(self, completed_results: List[ExtractionResult], layout):
        """Create overall quality score display."""
        # Calculate overall quality score
        all_confidences = []
        for result in completed_results:
            all_confidences.extend(result.confidence_scores.values())
        
        if not all_confidences:
            return
        
        overall_quality = sum(all_confidences) / len(all_confidences)
        
        # Quality score frame
        quality_frame = QFrame()
        quality_frame.setFrameShape(QFrame.Box)
        quality_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #F0F9FF, stop:1 #E0F2FE);
                border: 2px solid #0EA5E9;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        quality_layout = QHBoxLayout(quality_frame)
        
        # Quality score
        score_label = QLabel(f"{overall_quality:.1%}")
        score_label.setStyleSheet("font-size: 24pt; font-weight: bold; color: #0EA5E9;")
        quality_layout.addWidget(score_label)
        
        # Quality description
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Overall Data Quality"))
        
        if overall_quality >= 0.9:
            quality_desc = "Excellent"
            desc_color = "#16A34A"
        elif overall_quality >= 0.8:
            quality_desc = "Good"
            desc_color = "#65A30D"
        elif overall_quality >= 0.7:
            quality_desc = "Fair"
            desc_color = "#F59E0B"
        else:
            quality_desc = "Needs Improvement"
            desc_color = "#EF4444"
        
        quality_label = QLabel(quality_desc)
        quality_label.setStyleSheet(f"font-size: 14pt; font-weight: 600; color: {desc_color};")
        desc_layout.addWidget(quality_label)
        
        quality_layout.addLayout(desc_layout)
        quality_layout.addStretch()
        
        # Add confidence indicator
        conf_indicator = ConfidenceIndicator(overall_quality)
        quality_layout.addWidget(conf_indicator)
        
        layout.addWidget(quality_frame)
    
    def create_confidence_distribution(self, completed_results: List[ExtractionResult], layout):
        """Create confidence distribution visualization."""
        all_confidences = []
        for result in completed_results:
            all_confidences.extend(result.confidence_scores.values())
        
        if not all_confidences:
            return
        
        high_conf = sum(1 for c in all_confidences if c >= 0.8)
        med_conf = sum(1 for c in all_confidences if 0.5 <= c < 0.8)
        low_conf = sum(1 for c in all_confidences if c < 0.5)
        total = len(all_confidences)
        
        # Distribution frame
        dist_frame = QFrame()
        dist_frame.setFrameShape(QFrame.Box)
        dist_frame.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        dist_layout = QVBoxLayout(dist_frame)
        
        # Title
        title_label = QLabel("Confidence Distribution")
        title_label.setStyleSheet("font-weight: 600; font-size: 12pt; margin-bottom: 8px;")
        dist_layout.addWidget(title_label)
        
        # Create distribution bars
        distributions = [
            ("High (≥80%)", high_conf, total, "#16A34A"),
            ("Medium (50-79%)", med_conf, total, "#F59E0B"),
            ("Low (<50%)", low_conf, total, "#EF4444")
        ]
        
        for label, count, total_count, color in distributions:
            bar_layout = QHBoxLayout()
            
            # Label
            label_widget = QLabel(label)
            label_widget.setMinimumWidth(100)
            bar_layout.addWidget(label_widget)
            
            # Progress bar
            progress = QProgressBar()
            progress.setRange(0, total_count)
            progress.setValue(count)
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #D1D5DB;
                    border-radius: 4px;
                    text-align: center;
                    height: 20px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
            bar_layout.addWidget(progress, 1)
            
            # Count and percentage
            percentage = (count / total_count * 100) if total_count > 0 else 0
            count_label = QLabel(f"{count} ({percentage:.1f}%)")
            count_label.setStyleSheet(f"color: {color}; font-weight: 600;")
            count_label.setMinimumWidth(80)
            bar_layout.addWidget(count_label)
            
            dist_layout.addLayout(bar_layout)
        
        layout.addWidget(dist_frame)
    
    def create_completeness_metrics(self, session: ProcessingSession, completed_results: List[ExtractionResult], layout):
        """Create data completeness metrics display."""
        if not session.template or not session.template.fields:
            return
        
        # Completeness frame
        comp_frame = QFrame()
        comp_frame.setFrameShape(QFrame.Box)
        comp_frame.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        comp_layout = QVBoxLayout(comp_frame)
        
        # Title
        title_label = QLabel("Data Completeness by Field")
        title_label.setStyleSheet("font-weight: 600; font-size: 12pt; margin-bottom: 8px;")
        comp_layout.addWidget(title_label)
        
        # Calculate field completeness
        for field in session.template.fields:
            field_name = field.name
            
            # Count non-empty values
            values = [result.extracted_data.get(field_name) 
                     for result in completed_results
                     if result.extracted_data.get(field_name) is not None and 
                        result.extracted_data.get(field_name) != ""]
            
            completeness = len(values) / len(completed_results) if completed_results else 0
            
            # Create completeness bar
            field_layout = QHBoxLayout()
            
            # Field name
            name_label = QLabel(field_name)
            name_label.setMinimumWidth(120)
            if field.optional:
                name_label.setText(f"{field_name} (optional)")
                name_label.setStyleSheet("color: #6B7280;")
            field_layout.addWidget(name_label)
            
            # Completeness bar
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(int(completeness * 100))
            
            # Color based on completeness and whether field is required
            if completeness >= 0.9:
                color = "#16A34A"
            elif completeness >= 0.7:
                color = "#F59E0B"
            elif field.optional:
                color = "#6B7280"  # Gray for optional fields with low completeness
            else:
                color = "#EF4444"  # Red for required fields with low completeness
            
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #D1D5DB;
                    border-radius: 4px;
                    text-align: center;
                    height: 18px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
            field_layout.addWidget(progress, 1)
            
            # Percentage
            perc_label = QLabel(f"{completeness:.1%}")
            perc_label.setStyleSheet(f"color: {color}; font-weight: 600;")
            perc_label.setMinimumWidth(60)
            field_layout.addWidget(perc_label)
            
            comp_layout.addLayout(field_layout)
        
        layout.addWidget(comp_frame)
    
    def update_field_statistics(self, session: ProcessingSession):
        """Update field-specific statistics."""
        if not session.template or not session.template.fields:
            return
        
        completed_results = [r for r in session.results if r.status == ProcessingStatus.COMPLETED]
        
        if not completed_results:
            return
        
        # Calculate per-field statistics
        for field in session.template.fields:
            field_name = field.name
            
            # Calculate field completeness and average confidence
            values = []
            confidences = []
            
            for result in completed_results:
                value = result.extracted_data.get(field_name)
                confidence = result.confidence_scores.get(field_name, 0.0)
                
                if value is not None and value != "":
                    values.append(value)
                    confidences.append(confidence)
            
            # Create field stat widget
            field_frame = QFrame()
            field_frame.setFrameShape(QFrame.Box)
            field_frame.setStyleSheet("border: 1px solid @border; border-radius: 4px; padding: 8px;")
            field_layout = QHBoxLayout(field_frame)
            
            # Field name
            name_label = QLabel(field_name)
            name_label.setStyleSheet("font-weight: 600;")
            name_label.setMinimumWidth(120)
            field_layout.addWidget(name_label)
            
            # Completeness
            completeness = len(values) / len(completed_results) if completed_results else 0
            completeness_label = QLabel(f"Complete: {completeness:.1%}")
            field_layout.addWidget(completeness_label)
            
            # Average confidence
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                conf_indicator = ConfidenceIndicator(avg_confidence)
                field_layout.addWidget(conf_indicator)
            else:
                no_data_label = QLabel("No data")
                no_data_label.setStyleSheet("color: #6B7280; font-style: italic;")
                field_layout.addWidget(no_data_label)
            
            self.field_stats_layout.addWidget(field_frame)


class PreviewPanel(QWidget):
    """
    Main preview panel widget with tabbed interface for file and summary views.
    
    Signals:
        preview_updated: Emitted when preview data is updated
    """
    
    preview_updated = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.current_session: Optional[ProcessingSession] = None
        self.setup_ui()
        
        logger.info("PreviewPanel initialized")
    
    def setup_ui(self):
        """Setup the main preview panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        
        # File preview tab
        self.file_preview = FilePreviewWidget()
        self.tab_widget.addTab(self.file_preview, "File Preview")
        
        # Summary preview tab  
        self.summary_preview = SummaryPreviewWidget()
        self.tab_widget.addTab(self.summary_preview, "Summary")
        
        layout.addWidget(self.tab_widget)
        
        # Apply theme
        self.apply_theme()
    
    def apply_theme(self):
        """Apply theme styling to the preview panel."""
        # Tab widget styling will be handled by the global theme
        pass
    
    def update_file_preview(self, result: ExtractionResult, template_fields: List[Dict]):
        """
        Update the file preview with extraction result.
        
        Args:
            result: The extraction result to display
            template_fields: List of field definitions from the template
        """
        self.file_preview.update_preview(result, template_fields)
        self.preview_updated.emit()
        
        logger.debug(f"Updated file preview for {result.source_file}")
    
    def update_summary_preview(self, session: ProcessingSession):
        """
        Update the summary preview with session data.
        
        Args:
            session: The processing session data
        """
        self.current_session = session
        self.summary_preview.update_summary(session)
        self.preview_updated.emit()
        
        logger.debug(f"Updated summary preview with {len(session.results)} results")
    
    def clear_preview(self):
        """Clear all preview data and show empty state."""
        self.file_preview.show_empty_state()
        self.summary_preview.show_empty_state()
        self.current_session = None
        self.preview_updated.emit()
        
        logger.debug("Cleared preview panel")
    
    def get_current_tab(self) -> str:
        """Get the currently active tab name."""
        current_index = self.tab_widget.currentIndex()
        return self.tab_widget.tabText(current_index)
    
    def set_active_tab(self, tab_name: str):
        """Set the active tab by name."""
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_name:
                self.tab_widget.setCurrentIndex(i)
                break
