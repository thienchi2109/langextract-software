"""
Base chart widget for Phase 3 chart components.

Provides a foundation for all chart widgets with:
- PySide6 integration with matplotlib backend
- Consistent theming and styling
- Real-time update capabilities
- Interactive features and tooltips
- Export functionality
"""

import logging
from typing import Optional, Dict, Any, List
from abc import abstractmethod

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt backend for PySide6 compatibility
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .chart_themes import apply_chart_theme, get_chart_theme
from gui.theme import get_theme_manager

logger = logging.getLogger(__name__)


class ChartToolbar(NavigationToolbar):
    """
    Custom navigation toolbar with reduced buttons for better integration.
    """
    
    def __init__(self, canvas, parent=None):
        # Only include essential tools
        self.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            ('Pan', 'Left button pans, Right button zooms', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
            (None, None, None, None),  # Separator
            ('Save', 'Save chart as image', 'filesave', 'save_figure'),
        )
        super().__init__(canvas, parent)
        
        # Apply consistent styling
        self.setStyleSheet("""
            QToolBar {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
                spacing: 4px;
                padding: 2px;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 4px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #E5E7EB;
            }
            QToolButton:pressed {
                background-color: #D1D5DB;
            }
        """)


class BaseChartWidget(QWidget):
    """
    Base widget for all chart components.
    
    Provides:
    - Matplotlib integration with PySide6
    - Consistent theming and styling
    - Real-time update capabilities
    - Export functionality
    - Signal/slot integration
    
    Signals:
        chart_updated: Emitted when chart data is updated
        export_requested: Emitted when user requests chart export
    """
    
    chart_updated = Signal()
    export_requested = Signal(str)  # Export format
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        
        self.title = title
        self.theme_manager = get_theme_manager()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._delayed_update)
        self.update_timer.setSingleShot(True)
        
        # Chart data storage
        self._data: Dict[str, Any] = {}
        self._is_real_time = False
        
        self.setup_ui()
        self.setup_chart()
        
        logger.debug(f"BaseChartWidget '{title}' initialized")
    
    def setup_ui(self):
        """Setup the widget UI structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header section
        if self.title:
            header_layout = QHBoxLayout()
            
            # Title label
            title_label = QLabel(self.title)
            title_font = QFont()
            title_font.setPointSize(12)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #111827; margin-bottom: 4px;")
            header_layout.addWidget(title_label)
            
            header_layout.addStretch()
            
            # Export button
            export_btn = QPushButton("Export")
            export_btn.setMaximumWidth(80)
            export_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3B82F6;
                    color: white;
                    border: none;
                    padding: 4px 12px;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
                QPushButton:pressed {
                    background-color: #1D4ED8;
                }
            """)
            export_btn.clicked.connect(self._on_export_clicked)
            header_layout.addWidget(export_btn)
            
            layout.addLayout(header_layout)
        
        # Chart container
        chart_container = QFrame()
        chart_container.setFrameStyle(QFrame.StyledPanel)
        chart_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(4, 4, 4, 4)
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6), dpi=100, tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Add navigation toolbar
        self.toolbar = ChartToolbar(self.canvas, self)
        
        chart_layout.addWidget(self.toolbar)
        chart_layout.addWidget(self.canvas)
        
        layout.addWidget(chart_container)
        
        # Apply initial theme
        self.apply_theme()
    
    def setup_chart(self):
        """Setup the initial chart. Override in subclasses."""
        # Apply theme to matplotlib
        apply_chart_theme(dark_mode=False)  # TODO: Get from theme manager
        
        # Create initial empty axes
        self.axes = self.figure.add_subplot(111)
        self.axes.set_title("No data available", fontsize=12, color='#6B7280')
        self.axes.text(0.5, 0.5, 'Chart will display when data is loaded', 
                      ha='center', va='center', transform=self.axes.transAxes,
                      fontsize=11, color='#9CA3AF', style='italic')
        
        self.canvas.draw()
    
    def apply_theme(self):
        """Apply current theme to the chart."""
        # TODO: Get actual theme state from theme manager
        dark_mode = False
        apply_chart_theme(dark_mode)
        
        if hasattr(self, 'axes'):
            self.refresh_chart()
    
    def set_data(self, data: Dict[str, Any]):
        """
        Set chart data and trigger update.
        
        Args:
            data: Dictionary containing chart data
        """
        self._data = data
        self.schedule_update()
    
    def update_data(self, data: Dict[str, Any]):
        """
        Update chart data incrementally.
        
        Args:
            data: Dictionary containing new/updated chart data
        """
        self._data.update(data)
        self.schedule_update()
    
    def schedule_update(self, delay_ms: int = 100):
        """
        Schedule a delayed chart update to prevent excessive redraws.
        
        Args:
            delay_ms: Delay in milliseconds before update
        """
        self.update_timer.start(delay_ms)
    
    def _delayed_update(self):
        """Handle delayed chart update."""
        try:
            self.refresh_chart()
            self.chart_updated.emit()
        except Exception as e:
            logger.error(f"Chart update failed: {e}", exc_info=True)
    
    def _on_export_clicked(self):
        """Handle export button click."""
        self.export_requested.emit('png')  # Default to PNG format
    
    def export_chart(self, filepath: str, format: str = 'png', dpi: int = 300):
        """
        Export chart to file.
        
        Args:
            filepath: Output file path
            format: Export format ('png', 'svg', 'pdf')
            dpi: Resolution for raster formats
        """
        try:
            self.figure.savefig(filepath, format=format, dpi=dpi, 
                              bbox_inches='tight', facecolor='white')
            logger.info(f"Chart exported to {filepath}")
        except Exception as e:
            logger.error(f"Chart export failed: {e}")
            raise
    
    def clear_chart(self):
        """Clear all chart data and reset to empty state."""
        self._data.clear()
        self.axes.clear()
        self.setup_chart()
    
    def set_real_time_mode(self, enabled: bool):
        """
        Enable/disable real-time update mode.
        
        Args:
            enabled: Whether to enable real-time updates
        """
        self._is_real_time = enabled
        if enabled:
            logger.debug(f"Real-time mode enabled for {self.title}")
    
    @abstractmethod
    def refresh_chart(self):
        """
        Refresh the chart with current data. Must be implemented by subclasses.
        """
        pass
    
    def get_chart_data(self) -> Dict[str, Any]:
        """
        Get current chart data.
        
        Returns:
            Dictionary containing current chart data
        """
        return self._data.copy()
    
    def has_data(self) -> bool:
        """
        Check if chart has data to display.
        
        Returns:
            True if chart has data
        """
        return bool(self._data) 