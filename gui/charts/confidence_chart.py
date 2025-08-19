"""
Confidence trend chart for displaying confidence scores over time/files.

Provides interactive visualization of confidence trends with:
- Line charts showing confidence trends across files
- Color-coded confidence levels
- Interactive tooltips and hover effects
- Real-time updates as processing progresses
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

from .base_chart import BaseChartWidget
from .chart_themes import get_confidence_color, CONFIDENCE_COLORS
from core.models import ExtractionResult, ProcessingSession

logger = logging.getLogger(__name__)


class ConfidenceTrendChart(BaseChartWidget):
    """
    Chart widget for displaying confidence trends across files and fields.
    
    Features:
    - Line chart showing average confidence per file
    - Color-coded confidence levels (high/medium/low)
    - Field-specific confidence trends
    - Interactive tooltips with file names and scores
    """
    
    def __init__(self, parent=None):
        super().__init__("Confidence Trends", parent)
        
        # Chart configuration
        self.show_field_trends = True
        self.confidence_threshold_high = 0.8
        self.confidence_threshold_medium = 0.5
        
        logger.debug("ConfidenceTrendChart initialized")
    
    def set_session_data(self, session: ProcessingSession):
        """
        Update chart with processing session data.
        
        Args:
            session: ProcessingSession containing extraction results
        """
        if not session or not session.results:
            self.clear_chart()
            return
        
        # Extract confidence data from results
        confidence_data = self._extract_confidence_data(session.results)
        self.set_data(confidence_data)
    
    def _extract_confidence_data(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """
        Extract confidence data from extraction results.
        
        Args:
            results: List of extraction results
            
        Returns:
            Dictionary containing processed confidence data
        """
        # Filter completed results only
        completed_results = [r for r in results if r.confidence_scores]
        
        if not completed_results:
            return {}
        
        # Extract file-level data
        file_names = []
        file_confidences = []
        processing_times = []
        
        # Extract field-level data
        field_trends = {}
        
        for i, result in enumerate(completed_results):
            file_names.append(result.source_file)
            processing_times.append(result.processing_time)
            
            # Calculate average confidence for this file
            confidences = [score for score in result.confidence_scores.values() if score > 0]
            avg_confidence = np.mean(confidences) if confidences else 0.0
            file_confidences.append(avg_confidence)
            
            # Track individual field trends
            for field_name, confidence in result.confidence_scores.items():
                if field_name not in field_trends:
                    field_trends[field_name] = []
                field_trends[field_name].append(confidence)
        
        return {
            'file_names': file_names,
            'file_confidences': file_confidences,
            'processing_times': processing_times,
            'field_trends': field_trends,
            'total_files': len(completed_results)
        }
    
    def refresh_chart(self):
        """Refresh the confidence trend chart with current data."""
        if not self.has_data():
            self.setup_chart()
            return
        
        data = self.get_chart_data()
        file_names = data.get('file_names', [])
        file_confidences = data.get('file_confidences', [])
        field_trends = data.get('field_trends', {})
        
        if not file_names or not file_confidences:
            self.setup_chart()
            return
        
        # Clear previous chart
        self.axes.clear()
        
        # Create x-axis (file indices)
        x_indices = range(len(file_names))
        
        # Plot main confidence trend line
        colors = [get_confidence_color(conf) for conf in file_confidences]
        
        # Main trend line
        self.axes.plot(x_indices, file_confidences, 
                      color='#3B82F6', linewidth=2.5, 
                      marker='o', markersize=6, alpha=0.8,
                      label='Average Confidence')
        
        # Color-coded scatter points
        scatter = self.axes.scatter(x_indices, file_confidences, 
                                  c=colors, s=60, alpha=0.7, 
                                  edgecolors='white', linewidth=1,
                                  zorder=5)
        
        # Add confidence threshold lines
        self.axes.axhline(y=self.confidence_threshold_high, 
                         color=CONFIDENCE_COLORS['high'], 
                         linestyle='--', alpha=0.6, linewidth=1,
                         label='High Confidence (≥80%)')
        
        self.axes.axhline(y=self.confidence_threshold_medium, 
                         color=CONFIDENCE_COLORS['medium'], 
                         linestyle='--', alpha=0.6, linewidth=1,
                         label='Medium Confidence (≥50%)')
        
        # Add field trends if enabled and data available
        if self.show_field_trends and field_trends:
            self._add_field_trends(x_indices, field_trends)
        
        # Customize chart appearance
        self.axes.set_xlabel('File Index', fontweight='bold')
        self.axes.set_ylabel('Confidence Score', fontweight='bold')
        self.axes.set_title('Confidence Trends Across Files', fontweight='bold', pad=20)
        
        # Set y-axis limits and formatting
        self.axes.set_ylim(-0.05, 1.05)
        self.axes.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
        
        # Customize x-axis
        if len(file_names) <= 10:
            # Show all file names for small datasets
            self.axes.set_xticks(x_indices)
            self.axes.set_xticklabels([name.split('/')[-1][:15] + '...' if len(name) > 15 
                                     else name.split('/')[-1] for name in file_names], 
                                    rotation=45, ha='right')
        else:
            # Show subset for large datasets
            step = max(1, len(file_names) // 8)
            tick_indices = list(range(0, len(file_names), step))
            self.axes.set_xticks(tick_indices)
            self.axes.set_xticklabels([f"File {i+1}" for i in tick_indices])
        
        # Add legend
        self.axes.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
        
        # Add grid for better readability
        self.axes.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Add summary statistics as text
        self._add_summary_stats(file_confidences)
        
        # Refresh canvas
        self.canvas.draw()
        
        logger.debug(f"Confidence trend chart updated with {len(file_names)} files")
    
    def _add_field_trends(self, x_indices: range, field_trends: Dict[str, List[float]]):
        """
        Add field-specific trend lines to the chart.
        
        Args:
            x_indices: X-axis indices for files
            field_trends: Dictionary mapping field names to confidence lists
        """
        # Limit to top 3 fields by average confidence to avoid clutter
        field_averages = {
            field: np.mean([conf for conf in confidences if conf > 0])
            for field, confidences in field_trends.items()
        }
        
        top_fields = sorted(field_averages.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Color palette for field lines
        field_colors = ['#10B981', '#F59E0B', '#EF4444']
        
        for i, (field_name, _) in enumerate(top_fields):
            confidences = field_trends[field_name]
            if len(confidences) == len(x_indices):
                self.axes.plot(x_indices, confidences,
                             color=field_colors[i % len(field_colors)],
                             linewidth=1.5, alpha=0.6, linestyle=':',
                             label=f'{field_name[:15]}{"..." if len(field_name) > 15 else ""}')
    
    def _add_summary_stats(self, confidences: List[float]):
        """
        Add summary statistics as text annotation.
        
        Args:
            confidences: List of confidence scores
        """
        if not confidences:
            return
        
        avg_conf = np.mean(confidences)
        min_conf = np.min(confidences)
        max_conf = np.max(confidences)
        
        # Count confidence levels
        high_count = sum(1 for c in confidences if c >= self.confidence_threshold_high)
        medium_count = sum(1 for c in confidences if self.confidence_threshold_medium <= c < self.confidence_threshold_high)
        low_count = sum(1 for c in confidences if c < self.confidence_threshold_medium)
        
        stats_text = (
            f"Average: {avg_conf:.1%} | Range: {min_conf:.1%} - {max_conf:.1%}\n"
            f"High: {high_count} | Medium: {medium_count} | Low: {low_count}"
        )
        
        # Add text box with statistics
        self.axes.text(0.02, 0.98, stats_text,
                      transform=self.axes.transAxes,
                      bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9),
                      verticalalignment='top', fontsize=9,
                      family='monospace')
    
    def toggle_field_trends(self, show: bool):
        """
        Toggle display of individual field trends.
        
        Args:
            show: Whether to show field trends
        """
        self.show_field_trends = show
        if self.has_data():
            self.refresh_chart()
    
    def set_confidence_thresholds(self, high: float, medium: float):
        """
        Set confidence level thresholds.
        
        Args:
            high: Threshold for high confidence (default 0.8)
            medium: Threshold for medium confidence (default 0.5)
        """
        self.confidence_threshold_high = high
        self.confidence_threshold_medium = medium
        
        if self.has_data():
            self.refresh_chart() 