"""
Demo script for Phase 4 - Real-time Processing Integration.

This demo showcases the integration of real-time processing with charts:
- Live data streaming to charts during processing
- Real-time updates from ProcessingOrchestrator
- Integration with actual MainWindow and EnhancedPreviewPanel
- Progress tracking and cancellation support
- Live analytics dashboard updates

Run this script to see Phase 4 real-time integration in action.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel, QFileDialog
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def create_sample_files():
    """Create sample files for testing real-time processing."""
    sample_texts = [
        """
        Tech Corp Inc. Financial Report Q4 2024
        
        Company Overview:
        Tech Corp Inc. is a leading technology company specializing in software solutions.
        
        Financial Highlights:
        - Total Revenue: $15,750,000
        - Employee Count: 485 employees
        - Profit Margin: 22.8%
        - Growth Rate: 12.5%
        - Market Cap: $2,500,000,000
        
        Contact Information:
        Email: investor@techcorp.com
        Headquarters: San Francisco, CA
        Industry: Technology
        """,
        
        """
        Global Manufacturing Ltd. Q3 2024 Results
        
        Company: Global Manufacturing Ltd.
        
        Performance Metrics:
        - Annual Revenue: $8,900,000
        - Workforce: 320 employees  
        - Profit Margin: 15.2%
        - Growth Rate: 8.3%
        - Market Capitalization: $1,200,000,000
        
        Business Details:
        Contact: info@globalmanuf.com
        Location: New York, NY
        Sector: Manufacturing
        """,
        
        """
        StartupCo Quarterly Report Q2 2024
        
        Company Name: StartupCo Innovation Labs
        
        Financial Summary:
        - Revenue: $2,500,000
        - Team Size: 125 employees
        - Profit Margin: 8.5%
        - Growth: High potential
        - Valuation: Under review
        
        Company Info:
        Headquarters: Austin, TX  
        Industry: Retail Technology
        """,
        
        """
        RetailCorpXYZ Annual Report 2024
        
        RetailCorpXYZ Financial Overview
        
        Key Figures:
        - Total Revenue: $45,200,000
        - Staff: 1,250 employees
        - Margin: 18.7%
        - Growth Rate: 15.8% 
        - Market Value: $8,900,000,000
        
        Contact Details:
        Email: ir@retailcorp.com
        HQ: Chicago, IL
        Sector: Retail & E-commerce
        """,
        
        """
        FinanceFirst Bank Q1 2024 Statement
        
        Organization: FinanceFirst Banking Corp
        
        Financial Performance:
        - Operating Revenue: $125,000,000
        - Personnel: 2,100 employees
        - Net Margin: 28.4%
        - YoY Growth: 6.2%
        - Market Cap: $15,600,000,000
        
        Corporate Information:
        Contact: corporate@financefirst.com
        Headquarters: Boston, MA
        Industry: Financial Services
        """
    ]
    
    # Create temporary files
    temp_dir = Path(tempfile.gettempdir()) / "langextract_phase4_demo"
    temp_dir.mkdir(exist_ok=True)
    
    file_paths = []
    for i, text in enumerate(sample_texts):
        file_path = temp_dir / f"sample_report_{i+1}.txt"
        file_path.write_text(text.strip(), encoding='utf-8')
        file_paths.append(str(file_path))
    
    return file_paths


class Phase4DemoWindow(MainWindow):
    """Demo window extending MainWindow for Phase 4 demonstration."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phase 4 Demo - Real-time Processing Integration")
        self.setup_demo_ui()
        self.load_sample_files()
    
    def setup_demo_ui(self):
        """Add demo-specific UI elements."""
        # Add demo info banner
        demo_banner = QWidget()
        demo_banner.setStyleSheet("""
            QWidget {
                background-color: #EBF8FF;
                border: 1px solid #3B82F6;
                border-radius: 8px;
                padding: 12px;
                margin: 8px;
            }
        """)
        
        banner_layout = QVBoxLayout(demo_banner)
        
        # Title
        title_label = QLabel("🚀 Phase 4: Real-time Processing Integration Demo")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1E40AF; margin-bottom: 4px;")
        banner_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Watch live data streaming to charts during processing. Charts update in real-time "
            "as files are processed by the ProcessingOrchestrator. Try processing the sample files!"
        )
        desc_label.setStyleSheet("color: #1E40AF; font-size: 11px;")
        desc_label.setWordWrap(True)
        banner_layout.addWidget(desc_label)
        
        # Demo controls
        controls_layout = QHBoxLayout()
        
        load_sample_btn = QPushButton("🔄 Load Sample Files")
        load_sample_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        load_sample_btn.clicked.connect(self.load_sample_files)
        controls_layout.addWidget(load_sample_btn)
        
        controls_layout.addStretch()
        
        status_label = QLabel("💡 Tip: Switch to 'Analytics Dashboard' tab to see live charts")
        status_label.setStyleSheet("color: #1E40AF; font-size: 10px; font-style: italic;")
        controls_layout.addWidget(status_label)
        
        banner_layout.addLayout(controls_layout)
        
        # Insert banner at the top
        central_widget = self.centralWidget()
        layout = central_widget.layout()
        layout.insertWidget(0, demo_banner)
    
    def load_sample_files(self):
        """Load sample files for demo."""
        try:
            sample_files = create_sample_files()
            
            # Clear existing files
            self.file_list.clear()
            
            # Add sample files
            for file_path in sample_files:
                self.file_list.add_file(file_path)
            
            self.show_toast_message(f"Loaded {len(sample_files)} sample files for demo", "success")
            
            # Update UI
            self.update_ui_state()
            
            # Show a helpful message
            self.status_bar.showMessage(
                "Sample files loaded - Click 'Start Processing' to see real-time charts in action!"
            )
            
        except Exception as e:
            self.show_toast_message(f"Failed to load sample files: {str(e)}", "error")


def main():
    """Run the Phase 4 demo application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Phase 4 Integration Demo")
    app.setApplicationVersion("1.0.0")
    
    # Apply global styling
    app.setStyleSheet("""
        QApplication {
            font-family: "Segoe UI", "Arial", sans-serif;
        }
    """)
    
    # Create and show demo window
    demo_window = Phase4DemoWindow()
    demo_window.show()
    
    print("🚀 Phase 4 Real-time Integration Demo Started!")
    print("\nPhase 4 Features:")
    print("  📊 Real-time chart updates during processing")
    print("  ⚡ Live data streaming from ProcessingOrchestrator")
    print("  🎛️ Integrated analytics dashboard in MainWindow")
    print("  📈 Progress tracking with detailed metrics")
    print("  🔄 Cancellation support for long operations")
    print("  📱 Complete UI integration with existing workflow")
    print("\nInstructions:")
    print("  1. Sample files are pre-loaded for demonstration")
    print("  2. Click 'Start Processing' to begin real-time processing")
    print("  3. Switch to 'Analytics Dashboard' tab to see live charts")
    print("  4. Watch charts update in real-time as files are processed")
    print("  5. Try cancelling processing to test cancellation support")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 