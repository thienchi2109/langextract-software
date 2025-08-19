"""
Data quality charts for visualizing completeness metrics and field statistics.

Provides interactive visualization of data quality with:
- Pie charts for data completeness by field
- Bar charts for field extraction statistics
- Distribution charts for confidence levels
- Real-time quality monitoring
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

from .base_chart import BaseChartWidget
from .chart_themes import get_quality_colors, get_confidence_color, CONFIDENCE_COLORS
from core.models import ExtractionResult, ProcessingSession, FieldType

logger = logging.getLogger(__name__)


class DataQualityChart(BaseChartWidget):
    """
    Pie chart widget for displaying data completeness metrics.
    
    Features:
    - Interactive pie chart showing data completeness
    - Color-coded quality levels
    - Detailed breakdowns and statistics
    - Export capabilities
    """
    
    def __init__(self, parent=None):
        super().__init__("Data Quality Overview", parent)
        
        # Chart configuration
        self.quality_thresholds = {
            'excellent': 0.95,
            'good': 0.80,
            'fair': 0.60,
            'poor': 0.0
        }
        
        logger.debug("DataQualityChart initialized")
    
    def set_session_data(self, session: ProcessingSession):
        """
        Update chart with processing session data.
        
        Args:
            session: ProcessingSession containing extraction results
        """
        if not session or not session.results:
            self.clear_chart()
            return
        
        # Calculate quality metrics
        quality_data = self._calculate_quality_metrics(session.results, session.template)
        self.set_data(quality_data)
    
    def _calculate_quality_metrics(self, results: List[ExtractionResult], template) -> Dict[str, Any]:
        """
        Calculate comprehensive quality metrics.
        
        Args:
            results: List of extraction results
            template: Extraction template with field definitions
            
        Returns:
            Dictionary containing quality metrics
        """
        if not results:
            return {}
        
        completed_results = [r for r in results if r.extracted_data]
        total_files = len(completed_results)
        
        if total_files == 0:
            return {'total_files': 0}
        
        # Field completeness analysis
        field_stats = {}
        overall_completeness = 0
        
        for field in template.fields:
            field_name = field.name
            
            # Count successful extractions for this field
            extracted_count = 0
            confidence_scores = []
            
            for result in completed_results:
                if field_name in result.extracted_data:
                    value = result.extracted_data[field_name]
                    if value is not None and str(value).strip():
                        extracted_count += 1
                
                # Get confidence score
                if field_name in result.confidence_scores:
                    confidence_scores.append(result.confidence_scores[field_name])
            
            completeness = extracted_count / total_files if total_files > 0 else 0
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
            
            field_stats[field_name] = {
                'completeness': completeness,
                'extracted_count': extracted_count,
                'total_count': total_files,
                'avg_confidence': avg_confidence,
                'quality_level': self._get_quality_level(completeness)
            }
            
            overall_completeness += completeness
        
        # Calculate overall metrics
        avg_completeness = overall_completeness / len(template.fields) if template.fields else 0
        
        # Quality distribution
        quality_distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        for stats in field_stats.values():
            quality_distribution[stats['quality_level']] += 1
        
        return {
            'total_files': total_files,
            'field_stats': field_stats,
            'avg_completeness': avg_completeness,
            'quality_distribution': quality_distribution,
            'overall_quality': self._get_quality_level(avg_completeness)
        }
    
    def _get_quality_level(self, completeness: float) -> str:
        """
        Determine quality level based on completeness score.
        
        Args:
            completeness: Completeness ratio (0.0 to 1.0)
            
        Returns:
            Quality level string
        """
        if completeness >= self.quality_thresholds['excellent']:
            return 'excellent'
        elif completeness >= self.quality_thresholds['good']:
            return 'good'
        elif completeness >= self.quality_thresholds['fair']:
            return 'fair'
        else:
            return 'poor'
    
    def refresh_chart(self):
        """Refresh the data quality chart with current data."""
        if not self.has_data():
            self.setup_chart()
            return
        
        data = self.get_chart_data()
        
        if data.get('total_files', 0) == 0:
            self.setup_chart()
            return
        
        quality_distribution = data.get('quality_distribution', {})
        avg_completeness = data.get('avg_completeness', 0)
        
        # Clear previous chart
        self.axes.clear()
        
        # Prepare pie chart data
        labels = []
        sizes = []
        colors = []
        
        quality_colors = {
            'excellent': '#16A34A',  # Green
            'good': '#22C55E',       # Light Green
            'fair': '#F59E0B',       # Orange
            'poor': '#EF4444'        # Red
        }
        
        for quality, count in quality_distribution.items():
            if count > 0:
                labels.append(f'{quality.title()}\n({count} fields)')
                sizes.append(count)
                colors.append(quality_colors[quality])
        
        if not sizes:
            self.setup_chart()
            return
        
        # Create pie chart
        wedges, texts, autotexts = self.axes.pie(
            sizes, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90,
            explode=[0.05] * len(sizes),  # Slight separation
            shadow=True, textprops={'fontsize': 10}
        )
        
        # Enhance text appearance
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # Set title with overall quality
        title = f'Data Quality Distribution\nOverall Completeness: {avg_completeness:.1%}'
        self.axes.set_title(title, fontweight='bold', pad=20)
        
        # Add summary statistics
        self._add_quality_summary(data)
        
        # Refresh canvas
        self.canvas.draw()
        
        logger.debug("Data quality chart updated")
    
    def _add_quality_summary(self, data: Dict[str, Any]):
        """
        Add quality summary as text annotation.
        
        Args:
            data: Quality metrics data
        """
        total_files = data.get('total_files', 0)
        field_stats = data.get('field_stats', {})
        
        if not field_stats:
            return
        
        # Calculate summary metrics
        completeness_values = [stats['completeness'] for stats in field_stats.values()]
        min_completeness = min(completeness_values)
        max_completeness = max(completeness_values)
        
        # Find best and worst performing fields
        best_field = max(field_stats.items(), key=lambda x: x[1]['completeness'])
        worst_field = min(field_stats.items(), key=lambda x: x[1]['completeness'])
        
        summary_text = (
            f"Total Files: {total_files}\n"
            f"Range: {min_completeness:.1%} - {max_completeness:.1%}\n"
            f"Best: {best_field[0][:12]} ({best_field[1]['completeness']:.1%})\n"
            f"Worst: {worst_field[0][:12]} ({worst_field[1]['completeness']:.1%})"
        )
        
        # Add text box
        self.axes.text(1.3, 0.5, summary_text,
                      transform=self.axes.transAxes,
                      bbox=dict(boxstyle="round,pad=0.4", facecolor='white', alpha=0.9),
                      verticalalignment='center', fontsize=9,
                      family='monospace')


class FieldDistributionChart(BaseChartWidget):
    """
    Bar chart widget for displaying field-specific statistics.
    
    Features:
    - Horizontal bar chart showing field completeness
    - Color-coded bars based on quality levels
    - Confidence score overlays
    - Interactive tooltips
    """
    
    def __init__(self, parent=None):
        super().__init__("Field Statistics", parent)
        
        logger.debug("FieldDistributionChart initialized")
    
    def set_session_data(self, session: ProcessingSession):
        """
        Update chart with processing session data.
        
        Args:
            session: ProcessingSession containing extraction results
        """
        if not session or not session.results:
            self.clear_chart()
            return
        
        # Calculate field statistics
        field_data = self._calculate_field_statistics(session.results, session.template)
        self.set_data(field_data)
    
    def _calculate_field_statistics(self, results: List[ExtractionResult], template) -> Dict[str, Any]:
        """
        Calculate detailed field-level statistics.
        
        Args:
            results: List of extraction results
            template: Extraction template with field definitions
            
        Returns:
            Dictionary containing field statistics
        """
        if not results or not template:
            return {}
        
        completed_results = [r for r in results if r.extracted_data]
        total_files = len(completed_results)
        
        if total_files == 0:
            return {}
        
        field_stats = []
        
        for field in template.fields:
            field_name = field.name
            
            # Count extractions and calculate metrics
            extracted_count = 0
            confidence_scores = []
            data_types_found = set()
            
            for result in completed_results:
                # Check if field was extracted
                if field_name in result.extracted_data:
                    value = result.extracted_data[field_name]
                    if value is not None and str(value).strip():
                        extracted_count += 1
                        data_types_found.add(type(value).__name__)
                
                # Collect confidence scores
                if field_name in result.confidence_scores:
                    confidence_scores.append(result.confidence_scores[field_name])
            
            # Calculate metrics
            completeness = extracted_count / total_files
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
            min_confidence = min(confidence_scores) if confidence_scores else 0
            max_confidence = max(confidence_scores) if confidence_scores else 0
            
            field_stats.append({
                'name': field_name,
                'type': field.type.value if hasattr(field.type, 'value') else str(field.type),
                'completeness': completeness,
                'extracted_count': extracted_count,
                'total_count': total_files,
                'avg_confidence': avg_confidence,
                'min_confidence': min_confidence,
                'max_confidence': max_confidence,
                'data_types_found': list(data_types_found),
                'optional': getattr(field, 'optional', False)
            })
        
        # Sort by completeness (descending)
        field_stats.sort(key=lambda x: x['completeness'], reverse=True)
        
        return {
            'field_stats': field_stats,
            'total_files': total_files
        }
    
    def refresh_chart(self):
        """Refresh the field distribution chart with current data."""
        if not self.has_data():
            self.setup_chart()
            return
        
        data = self.get_chart_data()
        field_stats = data.get('field_stats', [])
        
        if not field_stats:
            self.setup_chart()
            return
        
        # Clear previous chart
        self.axes.clear()
        
        # Prepare data for horizontal bar chart
        field_names = [stat['name'][:20] + '...' if len(stat['name']) > 20 
                      else stat['name'] for stat in field_stats]
        completeness_values = [stat['completeness'] for stat in field_stats]
        confidence_values = [stat['avg_confidence'] for stat in field_stats]
        
        # Create colors based on completeness levels
        colors = []
        for completeness in completeness_values:
            if completeness >= 0.95:
                colors.append('#16A34A')  # Excellent - Green
            elif completeness >= 0.80:
                colors.append('#22C55E')  # Good - Light Green
            elif completeness >= 0.60:
                colors.append('#F59E0B')  # Fair - Orange
            else:
                colors.append('#EF4444')  # Poor - Red
        
        # Create horizontal bar chart
        y_positions = range(len(field_names))
        bars = self.axes.barh(y_positions, completeness_values, color=colors, alpha=0.8)
        
        # Add confidence score overlays as dots
        for i, (completeness, confidence) in enumerate(zip(completeness_values, confidence_values)):
            if confidence > 0:
                self.axes.scatter(completeness, i, 
                                c=get_confidence_color(confidence), 
                                s=60, alpha=0.9, edgecolors='white', linewidth=1,
                                zorder=5)
        
        # Customize chart appearance
        self.axes.set_yticks(y_positions)
        self.axes.set_yticklabels(field_names)
        self.axes.set_xlabel('Completeness Rate', fontweight='bold')
        self.axes.set_title('Field Extraction Statistics', fontweight='bold', pad=20)
        
        # Set x-axis limits and formatting
        self.axes.set_xlim(0, 1.05)
        self.axes.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
        
        # Add grid for better readability
        self.axes.grid(True, alpha=0.3, axis='x')
        
        # Add value labels on bars
        for i, (bar, completeness, confidence) in enumerate(zip(bars, completeness_values, confidence_values)):
            width = bar.get_width()
            
            # Completeness percentage
            self.axes.text(width + 0.01, bar.get_y() + bar.get_height()/2,
                          f'{completeness:.1%}',
                          ha='left', va='center', fontweight='bold', fontsize=9)
            
            # Confidence score (if available)
            if confidence > 0:
                self.axes.text(width - 0.02, bar.get_y() + bar.get_height()/2,
                              f'conf: {confidence:.1%}',
                              ha='right', va='center', fontsize=8, 
                              color='white', fontweight='bold')
        
        # Add legend
        legend_elements = [
            plt.Rectangle((0,0),1,1, facecolor='#16A34A', alpha=0.8, label='Excellent (≥95%)'),
            plt.Rectangle((0,0),1,1, facecolor='#22C55E', alpha=0.8, label='Good (≥80%)'),
            plt.Rectangle((0,0),1,1, facecolor='#F59E0B', alpha=0.8, label='Fair (≥60%)'),
            plt.Rectangle((0,0),1,1, facecolor='#EF4444', alpha=0.8, label='Poor (<60%)')
        ]
        
        self.axes.legend(handles=legend_elements, loc='lower right', 
                        frameon=True, fancybox=True, shadow=True)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Refresh canvas
        self.canvas.draw()
        
        logger.debug(f"Field distribution chart updated with {len(field_stats)} fields") 