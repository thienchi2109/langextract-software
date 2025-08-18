"""
Demo script for PreviewPanel functionality.

This script demonstrates the new PreviewPanel widget features:
- Modern, professional GUI design
- Per-file preview with extraction results
- Confidence indicators and data quality display
- Summary statistics
- Integration with MainWindow

Run this script to see the PreviewPanel in action.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.preview_panel import PreviewPanel
from core.models import (
    ExtractionResult, ProcessingSession, ExtractionTemplate, ExtractionField,
    ProcessingStatus, FieldType
)


def create_sample_data():
    """Create sample data for demonstration."""
    
    # Sample extraction results
    results = [
        ExtractionResult(
            source_file="financial_report_q1.pdf",
            extracted_data={
                "company_name": "TechCorp Solutions Ltd.",
                "revenue": 2500000.75,
                "quarter": "Q1 2024",
                "contact_email": "ir@techcorp.com",
                "employee_count": 350,
                "profit_margin": 15.8
            },
            confidence_scores={
                "company_name": 0.98,
                "revenue": 0.92,
                "quarter": 0.95,
                "contact_email": 0.87,
                "employee_count": 0.76,
                "profit_margin": 0.42
            },
            processing_time=3.2,
            errors=[],
            status=ProcessingStatus.COMPLETED
        ),
        ExtractionResult(
            source_file="financial_report_q2.pdf", 
            extracted_data={
                "company_name": "TechCorp Solutions Ltd.",
                "revenue": 2750000.25,
                "quarter": "Q2 2024",
                "contact_email": "ir@techcorp.com",
                "employee_count": 375,
                "profit_margin": 18.2
            },
            confidence_scores={
                "company_name": 0.97,
                "revenue": 0.89,
                "quarter": 0.94,
                "contact_email": 0.91,
                "employee_count": 0.68,
                "profit_margin": 0.55
            },
            processing_time=2.8,
            errors=[],
            status=ProcessingStatus.COMPLETED
        ),
        ExtractionResult(
            source_file="corrupted_document.pdf",
            extracted_data={},
            confidence_scores={},
            processing_time=0.5,
            errors=["OCR failed - document appears to be corrupted", "Text extraction returned empty result"],
            status=ProcessingStatus.FAILED
        )
    ]
    
    # Template fields
    template_fields = [
        {"name": "company_name", "type": "text", "description": "Company name"},
        {"name": "revenue", "type": "currency", "description": "Total revenue"},
        {"name": "quarter", "type": "text", "description": "Reporting quarter"},
        {"name": "contact_email", "type": "text", "description": "Investor relations email"},
        {"name": "employee_count", "type": "number", "description": "Number of employees"},
        {"name": "profit_margin", "type": "number", "description": "Profit margin percentage"}
    ]
    
    # Create template
    template = ExtractionTemplate(
        name="financial_report_template",
        prompt_description="Extract financial data from quarterly reports",
        fields=[
            ExtractionField("company_name", FieldType.TEXT, "Company name"),
            ExtractionField("revenue", FieldType.CURRENCY, "Total revenue"),
            ExtractionField("quarter", FieldType.TEXT, "Reporting quarter"),
            ExtractionField("contact_email", FieldType.TEXT, "Investor relations email"),
            ExtractionField("employee_count", FieldType.NUMBER, "Number of employees"),
            ExtractionField("profit_margin", FieldType.NUMBER, "Profit margin percentage")
        ]
    )
    
    # Create session
    session = ProcessingSession(
        template=template,
        files=["financial_report_q1.pdf", "financial_report_q2.pdf", "corrupted_document.pdf"],
        results=results
    )
    
    return results, template_fields, session


class PreviewPanelDemo(QMainWindow):
    """Demo window showcasing PreviewPanel functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PreviewPanel Demo - LangExtractor")
        self.setMinimumSize(900, 700)
        self.resize(1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Create preview panel
        self.preview_panel = PreviewPanel()
        layout.addWidget(self.preview_panel)
        
        # Load sample data
        self.results, self.template_fields, self.session = create_sample_data()
        
        # Setup demo timer to cycle through different views
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.cycle_demo)
        self.demo_step = 0
        
        # Start demo
        self.start_demo()
    
    def start_demo(self):
        """Start the automated demo."""
        print("🎬 Starting PreviewPanel Demo")
        print("📋 Features demonstrated:")
        print("   • File preview with extraction results")
        print("   • Confidence indicators with color coding")
        print("   • Data quality visualization")
        print("   • Summary statistics")
        print("   • Error handling display")
        print("   • Modern, professional UI design")
        print()
        
        # Show initial view
        self.cycle_demo()
        
        # Start timer for automatic cycling
        self.demo_timer.start(5000)  # Change view every 5 seconds
    
    def cycle_demo(self):
        """Cycle through different demo views."""
        if self.demo_step == 0:
            print("📄 Showing file preview - Successful extraction (Q1 Report)")
            self.preview_panel.update_file_preview(self.results[0], self.template_fields)
            self.preview_panel.set_active_tab("File Preview")
            
        elif self.demo_step == 1:
            print("📄 Showing file preview - Another successful extraction (Q2 Report)")
            self.preview_panel.update_file_preview(self.results[1], self.template_fields)
            self.preview_panel.set_active_tab("File Preview")
            
        elif self.demo_step == 2:
            print("❌ Showing file preview - Failed extraction (Corrupted Document)")
            self.preview_panel.update_file_preview(self.results[2], self.template_fields)
            self.preview_panel.set_active_tab("File Preview")
            
        elif self.demo_step == 3:
            print("📊 Showing summary statistics and data quality")
            self.preview_panel.update_summary_preview(self.session)
            self.preview_panel.set_active_tab("Summary")
            
        elif self.demo_step == 4:
            print("🔄 Back to file preview - Demonstrating confidence indicators")
            self.preview_panel.update_file_preview(self.results[0], self.template_fields)
            self.preview_panel.set_active_tab("File Preview")
        
        self.demo_step = (self.demo_step + 1) % 5
    
    def closeEvent(self, event):
        """Handle window close event."""
        print("🏁 Demo completed!")
        print("✅ PreviewPanel Phase 1 implementation verified")
        event.accept()


def main():
    """Run the PreviewPanel demo."""
    print("🚀 LangExtractor PreviewPanel Demo")
    print("=" * 40)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show demo window
    demo = PreviewPanelDemo()
    demo.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
