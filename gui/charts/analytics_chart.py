"""
Analytics charts for processing metrics and performance monitoring.

Provides real-time visualization of processing performance:
- Processing speed and throughput charts
- Memory usage monitoring
- Error rate tracking
- Performance trends over time
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime, timedelta
import time

from .base_chart import BaseChartWidget
from .chart_themes import LIGHT_THEME_COLORS
from core.models import ExtractionResult, ProcessingSession

logger = logging.getLogger(__name__)


class ProcessingMetricsChart(BaseChartWidget):
    """
    Chart widget for displaying real-time processing metrics.
    
    Features:
    - Processing speed (files per minute)
    - Average processing time per file
    - Error rate monitoring
    - Real-time updates during processing
    """
    
    def __init__(self, parent=None):
        super().__init__("Processing Metrics", parent)
        
        # Performance tracking
        self.processing_start_time = None
        self.performance_history = []
        self.max_history_points = 50
        
        logger.debug("ProcessingMetricsChart initialized")
    
    def start_processing_session(self):
        """Mark the start of a processing session."""
        self.processing_start_time = time.time()
        self.performance_history.clear()
        logger.debug("Processing session started")
    
    def set_session_data(self, session: ProcessingSession):
        """
        Update chart with processing session data.
        
        Args:
            session: ProcessingSession containing extraction results
        """
        if not session:
            self.clear_chart()
            return
        
        # Calculate processing metrics
        metrics_data = self._calculate_processing_metrics(session)
        self.set_data(metrics_data)
        
        # Add to performance history for trend tracking
        self._update_performance_history(metrics_data)
    
    def _calculate_processing_metrics(self, session: ProcessingSession) -> Dict[str, Any]:
        """
        Calculate processing performance metrics.
        
        Args:
            session: ProcessingSession to analyze
            
        Returns:
            Dictionary containing metrics data
        """
        if not session.results:
            return {}
        
        completed_results = [r for r in session.results if hasattr(r, 'processing_time') and r.processing_time > 0]
        total_results = len(session.results)
        completed_count = len(completed_results)
        failed_count = total_results - completed_count
        
        if completed_count == 0:
            return {
                'total_files': total_results,
                'completed_files': 0,
                'failed_files': failed_count,
                'success_rate': 0.0,
                'avg_processing_time': 0.0,
                'throughput': 0.0
            }
        
        # Calculate timing metrics
        processing_times = [r.processing_time for r in completed_results]
        total_processing_time = sum(processing_times)
        avg_processing_time = np.mean(processing_times)
        min_processing_time = min(processing_times)
        max_processing_time = max(processing_times)
        
        # Calculate throughput (files per minute)
        if self.processing_start_time:
            elapsed_time = time.time() - self.processing_start_time
            throughput = (completed_count / elapsed_time) * 60 if elapsed_time > 0 else 0
        else:
            throughput = 0
        
        # Calculate success rate
        success_rate = completed_count / total_results if total_results > 0 else 0
        
        # Calculate error rate
        error_rate = failed_count / total_results if total_results > 0 else 0
        
        return {
            'total_files': total_results,
            'completed_files': completed_count,
            'failed_files': failed_count,
            'success_rate': success_rate,
            'error_rate': error_rate,
            'avg_processing_time': avg_processing_time,
            'min_processing_time': min_processing_time,
            'max_processing_time': max_processing_time,
            'total_processing_time': total_processing_time,
            'throughput': throughput,
            'processing_times': processing_times
        }
    
    def _update_performance_history(self, metrics: Dict[str, Any]):
        """
        Update performance history for trend tracking.
        
        Args:
            metrics: Current metrics data
        """
        timestamp = datetime.now()
        
        history_point = {
            'timestamp': timestamp,
            'throughput': metrics.get('throughput', 0),
            'avg_processing_time': metrics.get('avg_processing_time', 0),
            'success_rate': metrics.get('success_rate', 0),
            'completed_files': metrics.get('completed_files', 0)
        }
        
        self.performance_history.append(history_point)
        
        # Keep only recent history
        if len(self.performance_history) > self.max_history_points:
            self.performance_history = self.performance_history[-self.max_history_points:]
    
    def refresh_chart(self):
        """Refresh the processing metrics chart with current data."""
        if not self.has_data():
            self.setup_chart()
            return
        
        data = self.get_chart_data()
        
        if data.get('total_files', 0) == 0:
            self.setup_chart()
            return
        
        # Clear previous chart
        self.axes.clear()
        
        # Create subplots for different metrics
        fig = self.figure
        fig.clear()
        
        # Create a 2x2 grid of subplots
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Subplot 1: Processing Time Distribution
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_processing_time_distribution(ax1, data)
        
        # Subplot 2: Success/Error Rate
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_success_rate(ax2, data)
        
        # Subplot 3: Throughput Trend
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_throughput_trend(ax3)
        
        # Subplot 4: Key Metrics Summary
        ax4 = fig.add_subplot(gs[1, 1])
        self._plot_metrics_summary(ax4, data)
        
        # Refresh canvas
        self.canvas.draw()
        
        logger.debug("Processing metrics chart updated")
    
    def _plot_processing_time_distribution(self, ax, data: Dict[str, Any]):
        """Plot processing time distribution histogram."""
        processing_times = data.get('processing_times', [])
        
        if not processing_times:
            ax.text(0.5, 0.5, 'No timing data available', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Processing Time Distribution', fontsize=10, fontweight='bold')
            return
        
        # Create histogram
        ax.hist(processing_times, bins=min(10, len(processing_times)), 
               color=LIGHT_THEME_COLORS['primary'], alpha=0.7, edgecolor='white')
        
        ax.set_xlabel('Processing Time (s)', fontsize=9)
        ax.set_ylabel('Count', fontsize=9)
        ax.set_title('Processing Time Distribution', fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add statistics
        avg_time = np.mean(processing_times)
        ax.axvline(avg_time, color='red', linestyle='--', alpha=0.8, 
                  label=f'Avg: {avg_time:.1f}s')
        ax.legend(fontsize=8)
    
    def _plot_success_rate(self, ax, data: Dict[str, Any]):
        """Plot success/error rate pie chart."""
        completed = data.get('completed_files', 0)
        failed = data.get('failed_files', 0)
        
        if completed == 0 and failed == 0:
            ax.text(0.5, 0.5, 'No processing data', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Success Rate', fontsize=10, fontweight='bold')
            return
        
        # Create pie chart
        sizes = [completed, failed] if failed > 0 else [completed]
        labels = ['Success', 'Failed'] if failed > 0 else ['Success']
        colors = [LIGHT_THEME_COLORS['success'], LIGHT_THEME_COLORS['error']][:len(sizes)]
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                         autopct='%1.1f%%', startangle=90)
        
        ax.set_title('Success Rate', fontsize=10, fontweight='bold')
        
        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)
    
    def _plot_throughput_trend(self, ax):
        """Plot throughput trend over time."""
        if len(self.performance_history) < 2:
            ax.text(0.5, 0.5, 'Collecting throughput data...', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Throughput Trend', fontsize=10, fontweight='bold')
            return
        
        # Extract time series data
        timestamps = [point['timestamp'] for point in self.performance_history]
        throughputs = [point['throughput'] for point in self.performance_history]
        
        # Plot line chart
        ax.plot(timestamps, throughputs, color=LIGHT_THEME_COLORS['primary'], 
               linewidth=2, marker='o', markersize=3)
        
        ax.set_xlabel('Time', fontsize=9)
        ax.set_ylabel('Files/min', fontsize=9)
        ax.set_title('Throughput Trend', fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        if len(timestamps) > 5:
            ax.tick_params(axis='x', rotation=45)
        
        # Show current throughput
        if throughputs:
            current = throughputs[-1]
            ax.text(0.98, 0.95, f'Current: {current:.1f} files/min',
                   transform=ax.transAxes, ha='right', va='top',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8),
                   fontsize=8)
    
    def _plot_metrics_summary(self, ax, data: Dict[str, Any]):
        """Plot key metrics summary as text display."""
        # Hide axes for text display
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Prepare metrics text
        total_files = data.get('total_files', 0)
        completed = data.get('completed_files', 0)
        avg_time = data.get('avg_processing_time', 0)
        throughput = data.get('throughput', 0)
        success_rate = data.get('success_rate', 0)
        
        metrics_text = f"""Key Metrics:

Files Processed: {completed}/{total_files}
Success Rate: {success_rate:.1%}
Avg. Time: {avg_time:.2f}s
Throughput: {throughput:.1f} files/min

Performance: {'Good' if success_rate > 0.9 else 'Fair' if success_rate > 0.7 else 'Poor'}"""
        
        ax.text(0.1, 0.9, metrics_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle="round,pad=0.4", facecolor=LIGHT_THEME_COLORS['surface'], alpha=0.9))
        
        ax.set_title('Summary', fontsize=10, fontweight='bold')
    
    def get_current_throughput(self) -> float:
        """
        Get current processing throughput.
        
        Returns:
            Current throughput in files per minute
        """
        if self.performance_history:
            return self.performance_history[-1]['throughput']
        return 0.0
    
    def reset_metrics(self):
        """Reset all performance metrics and history."""
        self.processing_start_time = None
        self.performance_history.clear()
        self.clear_chart()
        logger.debug("Processing metrics reset") 