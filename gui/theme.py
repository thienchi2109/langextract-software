"""
Theme management system for LangExtractor GUI.

Provides modern light/dark theme support with design tokens,
QSS loading, and High-DPI awareness.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtCore import QSettings, QObject, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    """
    Manages application themes with design token support.
    
    Features:
    - Light/dark theme switching
    - Design token substitution in QSS
    - Theme persistence with QSettings
    - High-DPI support
    - Icon theme management
    """
    
    # Signal emitted when theme changes
    theme_changed = Signal(str)  # theme_name
    
    # Design tokens for light theme
    LIGHT_TOKENS = {
        '@bg': '#F7F7FB',
        '@card': '#FFFFFF',
        '@text': '#1A1A1E',
        '@muted': '#6B7280',
        '@primary': '#3B82F6',
        '@primary600': '#2563EB',
        '@success': '#16A34A',
        '@warning': '#F59E0B',
        '@danger': '#EF4444',
        '@border': '#E5E7EB',
        '@focus': '#60A5FA'
    }
    
    # Design tokens for dark theme
    DARK_TOKENS = {
        '@bg': '#0F1115',
        '@card': '#151922',
        '@text': '#E5E7EB',
        '@muted': '#9CA3AF',
        '@primary': '#60A5FA',
        '@primary600': '#3B82F6',
        '@success': '#22C55E',
        '@warning': '#FBBF24',
        '@danger': '#F87171',
        '@border': '#273042',
        '@focus': '#93C5FD'
    }
    
    def __init__(self):
        """Initialize theme manager."""
        super().__init__()
        self.settings = QSettings("LangExtractor", "LangExtractor")
        self.current_theme = self.settings.value("theme", "light")
        self.assets_path = Path(__file__).parent.parent / "assets"
        
        # Ensure High-DPI support (for older Qt versions)
        try:
            QApplication.setAttribute(QApplication.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(QApplication.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            # These attributes are deprecated in Qt 6.0+
            pass
        
        logger.info(f"ThemeManager initialized with theme: {self.current_theme}")
    
    def get_current_theme(self) -> str:
        """Get current theme name."""
        return self.current_theme
    
    def get_available_themes(self) -> list:
        """Get list of available themes."""
        return ["light", "dark"]
    
    def load_qss(self, theme_name: str) -> str:
        """
        Load QSS file for specified theme.
        
        Args:
            theme_name: Theme name ('light' or 'dark')
            
        Returns:
            QSS content as string
            
        Raises:
            FileNotFoundError: If QSS file not found
        """
        qss_path = self.assets_path / "theme" / f"{theme_name}.qss"
        
        if not qss_path.exists():
            raise FileNotFoundError(f"QSS file not found: {qss_path}")
        
        try:
            with open(qss_path, 'r', encoding='utf-8') as f:
                qss_content = f.read()
            
            logger.debug(f"Loaded QSS file: {qss_path}")
            return qss_content
            
        except Exception as e:
            logger.error(f"Failed to load QSS file {qss_path}: {e}")
            raise
    
    def substitute_tokens(self, qss_content: str, theme_name: str) -> str:
        """
        Substitute design tokens in QSS content.
        
        Args:
            qss_content: Raw QSS content with token placeholders
            theme_name: Theme name to get tokens for
            
        Returns:
            QSS content with tokens substituted
        """
        tokens = self.LIGHT_TOKENS if theme_name == "light" else self.DARK_TOKENS
        
        # Replace all token placeholders
        for token, value in tokens.items():
            qss_content = qss_content.replace(token, value)
        
        logger.debug(f"Substituted {len(tokens)} design tokens for {theme_name} theme")
        return qss_content
    
    def apply_theme(self, app: QApplication, theme_name: str) -> bool:
        """
        Apply theme to application.
        
        Args:
            app: QApplication instance
            theme_name: Theme name to apply
            
        Returns:
            True if theme applied successfully, False otherwise
        """
        try:
            # Validate theme name
            if theme_name not in self.get_available_themes():
                logger.error(f"Invalid theme name: {theme_name}")
                return False
            
            # Load and process QSS
            qss_content = self.load_qss(theme_name)
            processed_qss = self.substitute_tokens(qss_content, theme_name)
            
            # Apply to application
            app.setStyleSheet(processed_qss)
            
            # Update current theme
            old_theme = self.current_theme
            self.current_theme = theme_name
            
            # Persist theme choice
            self.settings.setValue("theme", theme_name)
            self.settings.sync()
            
            # Emit signal if theme changed
            if old_theme != theme_name:
                self.theme_changed.emit(theme_name)
            
            logger.info(f"Applied {theme_name} theme successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply theme {theme_name}: {e}")
            return False
    
    def toggle_theme(self, app: QApplication) -> str:
        """
        Toggle between light and dark themes.
        
        Args:
            app: QApplication instance
            
        Returns:
            New theme name
        """
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(app, new_theme)
        return new_theme
    
    def get_icon_path(self, icon_name: str) -> Path:
        """
        Get path to icon file.
        
        Args:
            icon_name: Icon name (without extension)
            
        Returns:
            Path to icon file
        """
        return self.assets_path / "icons" / f"{icon_name}.svg"
    
    def create_icon(self, icon_name: str) -> QIcon:
        """
        Create QIcon from SVG file.
        
        Args:
            icon_name: Icon name (without extension)
            
        Returns:
            QIcon instance
        """
        icon_path = self.get_icon_path(icon_name)
        
        if icon_path.exists():
            return QIcon(str(icon_path))
        else:
            logger.warning(f"Icon not found: {icon_path}")
            return QIcon()  # Empty icon
    
    def setup_high_dpi(self, app: QApplication):
        """
        Setup High-DPI support for the application.

        Args:
            app: QApplication instance
        """
        # Enable High-DPI scaling (for older Qt versions)
        try:
            app.setAttribute(QApplication.AA_EnableHighDpiScaling, True)
            app.setAttribute(QApplication.AA_UseHighDpiPixmaps, True)

            # Set device pixel ratio policy
            app.setHighDpiScaleFactorRoundingPolicy(
                QApplication.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        except AttributeError:
            # These attributes are deprecated in Qt 6.0+
            pass

        logger.info("High-DPI support configured")


# Global theme manager instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """Get global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def apply_theme(app: QApplication, theme_name: str) -> bool:
    """
    Convenience function to apply theme.
    
    Args:
        app: QApplication instance
        theme_name: Theme name to apply
        
    Returns:
        True if successful, False otherwise
    """
    return get_theme_manager().apply_theme(app, theme_name)
