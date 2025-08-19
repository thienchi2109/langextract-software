"""
Demo script for Task 11: Modern GUI with drag-drop support.

This script demonstrates the new MainWindow with:
- Modern light/dark theme switching
- Drag-and-drop file interface
- File list with icons and status indicators
- Progress tracking and cancellation support
- Menu structure and toolbar
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui.main_window import MainWindow
from gui.theme import get_theme_manager
from core.logging_config import setup_logging, get_logger


def setup_demo_logging():
    """Setup logging for demo."""
    setup_logging({
        'log_level': 'INFO',
        'console_logging': True,
        'structured_logging': False
    })


def demo_theme_switching(main_window):
    """Demonstrate automatic theme switching."""
    logger = get_logger(__name__)
    
    def switch_theme():
        current_theme = main_window.theme_manager.get_current_theme()
        new_theme = "dark" if current_theme == "light" else "light"
        
        app = QApplication.instance()
        main_window.theme_manager.apply_theme(app, new_theme)
        
        logger.info(f"Demo: Switched to {new_theme} theme")
        
        # Schedule next switch in 5 seconds
        QTimer.singleShot(5000, switch_theme)
    
    # Start theme switching after 3 seconds
    QTimer.singleShot(3000, switch_theme)
    logger.info("Demo: Automatic theme switching will start in 3 seconds")


def add_sample_files(main_window):
    """Add some sample files to demonstrate the file list."""
    logger = get_logger(__name__)
    
    # Create some sample file paths (these don't need to exist for demo)
    sample_files = [
        "sample_report.pdf",
        "financial_data.xlsx", 
        "company_info.docx",
        "quarterly_report.pdf",
        "employee_data.xlsx"
    ]
    
    def add_file():
        if sample_files:
            file_name = sample_files.pop(0)
            # For demo, we'll just add the filename (normally would be full path)
            # This won't work with real file validation, but shows the UI
            logger.info(f"Demo: Would add file {file_name}")
            
            # Schedule next file addition
            if sample_files:
                QTimer.singleShot(1000, add_file)
    
    # Start adding files after 2 seconds
    QTimer.singleShot(2000, add_file)
    logger.info("Demo: Sample files will be added automatically")


def demo_progress_simulation(main_window):
    """Demonstrate progress bar functionality."""
    logger = get_logger(__name__)
    
    progress_value = 0
    
    def update_progress():
        nonlocal progress_value
        progress_value += 10
        
        if progress_value <= 100:
            main_window.show_progress(f"Processing... {progress_value}%", progress_value, 100)
            
            if progress_value < 100:
                QTimer.singleShot(500, update_progress)
            else:
                # Hide progress after completion
                QTimer.singleShot(1000, main_window.hide_progress)
                logger.info("Demo: Progress simulation completed")
    
    # Start progress simulation after 8 seconds
    QTimer.singleShot(8000, update_progress)
    logger.info("Demo: Progress simulation will start in 8 seconds")


def print_demo_instructions():
    """Print demo instructions to console."""
    print("\n" + "="*60)
    print("LangExtractor GUI Demo - Task 11")
    print("="*60)
    print("\nFeatures to test:")
    print("1. 🎨 Theme Switching:")
    print("   - Click the palette button in header")
    print("   - Use View > Toggle Theme menu")
    print("   - Use Ctrl+T shortcut")
    print("   - Automatic switching will start in 3 seconds")
    
    print("\n2. 📁 Drag & Drop:")
    print("   - Drag PDF, DOCX, or XLSX files into the window")
    print("   - See the drop overlay with dashed border")
    print("   - Files will appear in the list with icons")
    print("   - Duplicates are automatically ignored")
    
    print("\n3. 📋 File Management:")
    print("   - Use 'Add Files' button to browse for files")
    print("   - Select files and click 'Remove' to delete them")
    print("   - Use 'Clear All' to remove all files")
    print("   - File icons change based on extension")
    
    print("\n4. 🔧 Interface Elements:")
    print("   - Menu bar with File, View, Help menus")
    print("   - Toolbar with quick action buttons")
    print("   - Status bar showing file count")
    print("   - Progress bar (simulation starts in 8 seconds)")
    
    print("\n5. ⌨️ Keyboard Shortcuts:")
    print("   - Ctrl+O: Add files")
    print("   - Ctrl+T: Toggle theme")
    print("   - Ctrl+Q: Exit application")
    
    print("\n6. 🎯 Accessibility:")
    print("   - All controls have keyboard focus indicators")
    print("   - High contrast colors for readability")
    print("   - Tooltips on all interactive elements")
    
    print("\n" + "="*60)
    print("The demo includes automatic features:")
    print("- Theme switching every 5 seconds")
    print("- Progress bar simulation after 8 seconds")
    print("- Status messages and toast notifications")
    print("="*60 + "\n")


def main():
    """Main demo function."""
    # Setup logging
    setup_demo_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting LangExtractor GUI Demo")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("LangExtractor Demo")
    
    # Enable High-DPI support
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        # Setup theme manager
        theme_manager = get_theme_manager()
        theme_manager.setup_high_dpi(app)
        
        # Apply initial theme
        current_theme = theme_manager.get_current_theme()
        theme_manager.apply_theme(app, current_theme)
        logger.info(f"Applied {current_theme} theme")
        
        # Create main window
        main_window = MainWindow()
        main_window.show()
        
        # Print demo instructions
        print_demo_instructions()
        
        # Setup demo features
        demo_theme_switching(main_window)
        add_sample_files(main_window)
        demo_progress_simulation(main_window)
        
        logger.info("GUI Demo initialized successfully")
        
        # Run application
        exit_code = app.exec()
        logger.info(f"Demo exited with code: {exit_code}")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"Demo Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
