"""
Enhanced Preview Panel for Phase 3 with advanced charting capabilities.

Extends the existing PreviewPanel with:
- Interactive charts and visualizations
- Real-time analytics dashboard
- Advanced export capabilities
- Smart recommendations
"""

import logging
from typing import Dict, List, Optional, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea, QLabel,
    QFrame, QProgressBar, QGroupBox, QGridLayout, QSizePolicy, QSpacerItem,
    QPushButton, QSplitter, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from gui.preview_panel import PreviewPanel, FilePreviewWidget
from gui.charts import (
    ConfidenceTrendChart, DataQualityChart, FieldDistributionChart, 
    ProcessingMetricsChart
)
from core.models import ExtractionResult, ProcessingSession
from gui.theme import get_theme_manager
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedSummaryWidget(QWidget):
    """
    Enhanced summary widget with integrated charts and analytics.
    
    Features:
    - Interactive charts for confidence trends and data quality
    - Real-time processing metrics
    - Advanced data visualization
    - Export capabilities
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_session: Optional[ProcessingSession] = None
        self.theme_manager = get_theme_manager()
        
        # Chart widgets
        self.confidence_chart = None
        self.quality_chart = None
        self.field_chart = None
        self.metrics_chart = None
        
        # Update timer for real-time updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_charts)
        self.update_timer.setSingleShot(False)
        
        self.setup_ui()
        
        logger.debug("EnhancedSummaryWidget initialized")
    
    def setup_ui(self):
        """Setup the enhanced summary UI with charts."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Chart controls section
        self.create_chart_controls(layout)
        
        # Main charts container using splitter for resizable layout
        main_splitter = QSplitter(Qt.Vertical)
        
        # Top section: Confidence and Quality charts
        top_splitter = QSplitter(Qt.Horizontal)
        
        # Confidence trend chart
        self.confidence_chart = ConfidenceTrendChart()
        self.confidence_chart.setMinimumHeight(300)
        top_splitter.addWidget(self.confidence_chart)
        
        # Data quality chart
        self.quality_chart = DataQualityChart()
        self.quality_chart.setMinimumHeight(300)
        top_splitter.addWidget(self.quality_chart)
        
        # Set equal sizes for top charts
        top_splitter.setSizes([400, 400])
        main_splitter.addWidget(top_splitter)
        
        # Bottom section: Field statistics and metrics
        bottom_splitter = QSplitter(Qt.Horizontal)
        
        # Field distribution chart
        self.field_chart = FieldDistributionChart()
        self.field_chart.setMinimumHeight(300)
        bottom_splitter.addWidget(self.field_chart)
        
        # Processing metrics chart
        self.metrics_chart = ProcessingMetricsChart()
        self.metrics_chart.setMinimumHeight(300)
        bottom_splitter.addWidget(self.metrics_chart)
        
        # Set equal sizes for bottom charts
        bottom_splitter.setSizes([400, 400])
        main_splitter.addWidget(bottom_splitter)
        
        # Set splitter proportions (60% top, 40% bottom)
        main_splitter.setSizes([360, 240])
        
        layout.addWidget(main_splitter)
        
        # Connect chart signals
        self._connect_chart_signals()
        
        # Show empty state initially
        self.show_empty_state()
    
    def create_chart_controls(self, parent_layout):
        """Create chart control panel."""
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        controls_frame.setMaximumHeight(60)
        
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title_label = QLabel("📊 Advanced Analytics Dashboard")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #111827;")
        controls_layout.addWidget(title_label)
        
        controls_layout.addStretch()
        
        # Real-time updates toggle
        self.realtime_checkbox = QCheckBox("Real-time Updates")
        self.realtime_checkbox.setChecked(True)
        self.realtime_checkbox.toggled.connect(self.toggle_realtime_updates)
        self.realtime_checkbox.setStyleSheet("""
            QCheckBox {
                color: #374151;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:checked {
                background-color: #3B82F6;
                border: 1px solid #3B82F6;
            }
        """)
        controls_layout.addWidget(self.realtime_checkbox)
        
        # Export button
        export_btn = QPushButton("📈 Export Charts")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        export_btn.clicked.connect(self.export_all_charts)
        controls_layout.addWidget(export_btn)
        
        parent_layout.addWidget(controls_frame)
    
    def _connect_chart_signals(self):
        """Connect chart signals for coordinated updates."""
        if self.confidence_chart:
            self.confidence_chart.chart_updated.connect(self._on_chart_updated)
        
        if self.quality_chart:
            self.quality_chart.chart_updated.connect(self._on_chart_updated)
        
        if self.field_chart:
            self.field_chart.chart_updated.connect(self._on_chart_updated)
        
        if self.metrics_chart:
            self.metrics_chart.chart_updated.connect(self._on_chart_updated)
    
    def _on_chart_updated(self):
        """Handle chart update events."""
        logger.debug("Chart updated")
    
    def update_summary(self, session: ProcessingSession):
        """
        Update all charts with new session data.
        
        Args:
            session: ProcessingSession containing extraction results
        """
        self.current_session = session
        
        if not session:
            self.show_empty_state()
            return
        
        # Update all charts
        self._update_all_charts(session)
        
        # Start real-time updates if enabled
        if self.realtime_checkbox.isChecked():
            self.start_realtime_updates()
        
        logger.debug(f"Enhanced summary updated with {len(session.results) if session.results else 0} results")
    
    def _update_all_charts(self, session: ProcessingSession):
        """Update all chart widgets with session data."""
        try:
            # Update confidence trend chart
            if self.confidence_chart:
                self.confidence_chart.set_session_data(session)
            
            # Update data quality chart
            if self.quality_chart:
                self.quality_chart.set_session_data(session)
            
            # Update field distribution chart
            if self.field_chart:
                self.field_chart.set_session_data(session)
            
            # Update processing metrics chart
            if self.metrics_chart:
                self.metrics_chart.set_session_data(session)
                
        except Exception as e:
            logger.error(f"Error updating charts: {e}", exc_info=True)
    
    def _update_charts(self):
        """Timer-based chart updates for real-time mode."""
        if self.current_session:
            self._update_all_charts(self.current_session)
    
    def start_realtime_updates(self, interval_ms: int = 2000):
        """
        Start real-time chart updates.
        
        Args:
            interval_ms: Update interval in milliseconds
        """
        if not self.update_timer.isActive():
            self.update_timer.start(interval_ms)
            logger.debug("Real-time updates started")
    
    def stop_realtime_updates(self):
        """Stop real-time chart updates."""
        if self.update_timer.isActive():
            self.update_timer.stop()
            logger.debug("Real-time updates stopped")
    
    def toggle_realtime_updates(self, enabled: bool):
        """
        Toggle real-time updates on/off.
        
        Args:
            enabled: Whether to enable real-time updates
        """
        if enabled:
            self.start_realtime_updates()
        else:
            self.stop_realtime_updates()
    
    def export_all_charts(self):
        """Export all charts to files (simplified)."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from pathlib import Path
        
        try:
            # Get export directory
            export_dir = QFileDialog.getExistingDirectory(
                self, "Select Export Directory", ""
            )
            
            if not export_dir:
                return
            
            export_path = Path(export_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export each chart (PNG only, simplified)
            charts_to_export = [
                (self.confidence_chart, f"confidence_trends_{timestamp}.png"),
                (self.quality_chart, f"data_quality_{timestamp}.png"),
                (self.field_chart, f"field_statistics_{timestamp}.png"),
                (self.metrics_chart, f"processing_metrics_{timestamp}.png")
            ]
            
            exported_files = []
            for chart, filename in charts_to_export:
                if chart and chart.has_data():
                    filepath = export_path / filename
                    chart.export_chart(str(filepath), format='png', dpi=150)  # Lower DPI for simplicity
                    exported_files.append(filename)
            
            # Show success message
            if exported_files:
                QMessageBox.information(
                    self, "Export Complete",
                    f"Exported {len(exported_files)} charts to:\n{export_dir}"
                )
            else:
                QMessageBox.warning(
                    self, "Export Warning",
                    "No charts with data available for export."
                )
                
        except Exception as e:
            logger.error(f"Chart export failed: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Export Error",
                f"Failed to export charts: {str(e)}"
            )
    
    def show_empty_state(self):
        """Show empty state when no data is available."""
        # Clear all charts
        if self.confidence_chart:
            self.confidence_chart.clear_chart()
        if self.quality_chart:
            self.quality_chart.clear_chart()
        if self.field_chart:
            self.field_chart.clear_chart()
        if self.metrics_chart:
            self.metrics_chart.clear_chart()
        
        # Stop real-time updates
        self.stop_realtime_updates()
    
    def start_processing_session(self):
        """Mark the start of a new processing session."""
        if self.metrics_chart:
            self.metrics_chart.start_processing_session()
    
    def set_confidence_thresholds(self, high: float, medium: float):
        """
        Set confidence thresholds for all charts.
        
        Args:
            high: High confidence threshold
            medium: Medium confidence threshold
        """
        if self.confidence_chart:
            self.confidence_chart.set_confidence_thresholds(high, medium)


class EnhancedPreviewPanel(PreviewPanel):
    """
    Enhanced preview panel with Phase 3 chart integration.
    
    Extends the existing PreviewPanel with advanced charting capabilities
    while maintaining backward compatibility.
    """
    
    def __init__(self, parent=None):
        # Initialize parent without calling setup_ui yet
        QWidget.__init__(self, parent)
        
        self.theme_manager = get_theme_manager()
        self.current_session: Optional[ProcessingSession] = None
        
        # Setup enhanced UI
        self.setup_enhanced_ui()
        
        logger.info("EnhancedPreviewPanel initialized with Phase 3 features")
    
    def setup_enhanced_ui(self):
        """Setup the enhanced preview panel UI with charts."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        
        # File preview tab (existing functionality)
        self.file_preview = FilePreviewWidget()
        self.tab_widget.addTab(self.file_preview, "📄 File Preview")
        
        # Enhanced summary tab with charts
        self.enhanced_summary = EnhancedSummaryWidget()
        self.tab_widget.addTab(self.enhanced_summary, "📊 Analytics Dashboard")
        
        layout.addWidget(self.tab_widget)
        
        # Apply theme
        self.apply_theme()
    
    def apply_theme(self):
        """Apply theme styling to the enhanced preview panel."""
        # Enhanced tab styling
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5E7EB;
                background-color: white;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                padding: 8px 16px;
                margin-right: 2px;
                border-bottom: none;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #3B82F6;
                color: #3B82F6;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E5E7EB;
            }
        """)
    
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
        Update the enhanced summary preview with session data.
        
        Args:
            session: ProcessingSession containing extraction results
        """
        self.current_session = session
        self.enhanced_summary.update_summary(session)
        self.preview_updated.emit()
        
        logger.debug("Updated enhanced summary preview")
    
    def start_processing_session(self):
        """Mark the start of a new processing session."""
        self.enhanced_summary.start_processing_session()
    
    def get_current_session(self) -> Optional[ProcessingSession]:
        """
        Get the current processing session.
        
        Returns:
            Current ProcessingSession or None
        """
        return self.current_session
    
    def export_charts(self):
        """Export all charts from the analytics dashboard."""
        self.enhanced_summary.export_all_charts()
    
    def set_realtime_updates(self, enabled: bool):
        """
        Enable/disable real-time chart updates.
        
        Args:
            enabled: Whether to enable real-time updates
        """
        self.enhanced_summary.toggle_realtime_updates(enabled) 