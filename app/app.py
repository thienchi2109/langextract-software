"""
Main application entry point for LangExtractor GUI.

This module initializes the PySide6 application with modern theme support
and launches the main window.
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.main_window import MainWindow
from gui.theme import get_theme_manager
from core.logging_config import setup_logging, get_logger
from core.utils import load_config


def setup_application() -> QApplication:
    """
    Setup and configure the QApplication.
    
    Returns:
        Configured QApplication instance
    """
    # Create application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("LangExtractor")
    app.setApplicationDisplayName("LangExtractor - Automated Report Extraction")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("LangExtractor")
    app.setOrganizationDomain("langextractor.local")
    
    # Enable High-DPI support (for older Qt versions)
    try:
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # These attributes are deprecated in Qt 6.0+
        pass
    
    return app


def main():
    """Main application entry point."""
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging
        setup_logging({
            'log_level': config.log_level,
            'console_logging': True,
            'structured_logging': False
        })
        
        logger = get_logger(__name__)
        logger.info("Starting LangExtractor GUI Application")
        
        # Create application
        app = setup_application()
        
        # Setup theme manager
        theme_manager = get_theme_manager()
        theme_manager.setup_high_dpi(app)
        
        # Apply initial theme
        current_theme = theme_manager.get_current_theme()
        theme_manager.apply_theme(app, current_theme)
        logger.info(f"Applied {current_theme} theme")
        
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        logger.info("Application initialized successfully")
        
        # Run application
        exit_code = app.exec()
        logger.info(f"Application exited with code: {exit_code}")
        
        return exit_code
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Application startup failed: {e}", exc_info=True)
        
        # Try to show error dialog if possible
        try:
            from PySide6.QtWidgets import QMessageBox
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            QMessageBox.critical(
                None, "Application Error",
                f"Failed to start LangExtractor:\n\n{str(e)}"
            )
        except:
            print(f"Critical Error: {e}")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
