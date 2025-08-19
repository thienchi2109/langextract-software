"""
Chart theming system for Phase 3 charts.

Provides consistent visual styling that matches the existing UI theme,
with support for light/dark themes and professional color schemes.
"""

import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
from typing import Dict, Any
from gui.theme import get_theme_manager

# Color palettes that match the existing UI
LIGHT_THEME_COLORS = {
    'background': '#FFFFFF',
    'surface': '#F9FAFB', 
    'primary': '#3B82F6',
    'secondary': '#6366F1',
    'success': '#16A34A',
    'warning': '#F59E0B',
    'error': '#EF4444',
    'text_primary': '#111827',
    'text_secondary': '#6B7280',
    'border': '#E5E7EB',
    'grid': '#F3F4F6'
}

DARK_THEME_COLORS = {
    'background': '#1F2937',
    'surface': '#374151',
    'primary': '#60A5FA', 
    'secondary': '#818CF8',
    'success': '#22C55E',
    'warning': '#FBBF24',
    'error': '#F87171',
    'text_primary': '#F9FAFB',
    'text_secondary': '#D1D5DB',
    'border': '#4B5563',
    'grid': '#374151'
}

# Confidence level colors (consistent with existing UI)
CONFIDENCE_COLORS = {
    'high': '#16A34A',      # Green for >= 0.8
    'medium': '#F59E0B',    # Orange for 0.5-0.8
    'low': '#EF4444',       # Red for < 0.5
    'missing': '#9CA3AF'    # Gray for missing data
}

# Data quality color scheme
QUALITY_COLORS = [
    '#16A34A',  # Excellent
    '#22C55E',  # Good  
    '#F59E0B',  # Fair
    '#EF4444',  # Poor
    '#9CA3AF'   # Missing
]


def get_chart_theme(dark_mode: bool = False) -> Dict[str, Any]:
    """
    Get chart theme configuration based on current UI theme.
    
    Args:
        dark_mode: Whether to use dark theme colors
        
    Returns:
        Dictionary with theme configuration for matplotlib
    """
    colors = DARK_THEME_COLORS if dark_mode else LIGHT_THEME_COLORS
    
    return {
        'figure.facecolor': colors['background'],
        'axes.facecolor': colors['surface'],
        'axes.edgecolor': colors['border'],
        'axes.labelcolor': colors['text_primary'],
        'axes.axisbelow': True,
        'axes.grid': True,
        'axes.spines.left': True,
        'axes.spines.bottom': True,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'grid.color': colors['grid'],
        'grid.alpha': 0.6,
        'grid.linewidth': 0.5,
        'text.color': colors['text_primary'],
        'xtick.color': colors['text_secondary'],
        'ytick.color': colors['text_secondary'],
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'font.size': 11,
        'axes.titlesize': 13,
        'axes.labelsize': 11,
        'legend.frameon': True,
        'legend.facecolor': colors['surface'],
        'legend.edgecolor': colors['border'],
        'legend.fontsize': 10,
        'lines.linewidth': 2,
        'patch.linewidth': 0.5,
        'patch.facecolor': colors['primary'],
        'patch.edgecolor': colors['border']
    }


def apply_chart_theme(dark_mode: bool = False):
    """
    Apply the chart theme to matplotlib global settings.
    
    Args:
        dark_mode: Whether to use dark theme
    """
    theme = get_chart_theme(dark_mode)
    plt.rcParams.update(theme)


def get_confidence_color(confidence: float) -> str:
    """
    Get color for confidence score based on thresholds.
    
    Args:
        confidence: Confidence score (0.0 to 1.0)
        
    Returns:
        Hex color string
    """
    if confidence >= 0.8:
        return CONFIDENCE_COLORS['high']
    elif confidence >= 0.5:
        return CONFIDENCE_COLORS['medium']
    elif confidence > 0:
        return CONFIDENCE_COLORS['low']
    else:
        return CONFIDENCE_COLORS['missing']


def get_quality_colors(count: int) -> list:
    """
    Get list of quality colors for data visualization.
    
    Args:
        count: Number of colors needed
        
    Returns:
        List of hex color strings
    """
    if count <= len(QUALITY_COLORS):
        return QUALITY_COLORS[:count]
    else:
        # Extend with variations if more colors needed
        base_colors = QUALITY_COLORS.copy()
        while len(base_colors) < count:
            base_colors.extend(QUALITY_COLORS)
        return base_colors[:count]


def create_custom_colormap(colors: list, name: str = 'custom'):
    """
    Create a custom matplotlib colormap from color list.
    
    Args:
        colors: List of hex color strings
        name: Name for the colormap
        
    Returns:
        matplotlib colormap object
    """
    from matplotlib.colors import LinearSegmentedColormap
    
    cmap = LinearSegmentedColormap.from_list(name, colors)
    return cmap 