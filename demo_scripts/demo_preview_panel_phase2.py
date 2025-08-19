"""
Enhanced Demo for PreviewPanel Phase 2 Features.

This demo showcases the new Phase 2 enhancements:
- Enhanced file selection integration with varied mock data
- Interactive data field widgets with click events and copy functionality
- Advanced data visualization with confidence distribution
- Processing state indicators and progress bars
- Grouped field display by confidence levels
- Enhanced summary statistics with quality metrics
- Data completeness visualization
- Modern, professional UI improvements

Run this script to see all Phase 2 features in action.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import QTimer

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.preview_panel import PreviewPanel
from core.models import (
    ExtractionResult, ProcessingSession, ExtractionTemplate, ExtractionField,
    ProcessingStatus, FieldType
)


def create_enhanced_sample_data():
    """Create enhanced sample data for Phase 2 demonstration."""
    
    # Enhanced sample extraction results with varied scenarios
    results = [
        # High-quality extraction
        ExtractionResult(
            source_file="annual_report_2024.pdf",
            extracted_data={
                "company_name": "TechInnovate Solutions Inc.",
                "revenue": 15750000.50,
                "quarter": "Q4 2024",
                "contact_email": "ir@techinnovate.com",
                "employee_count": 485,
                "profit_margin": 22.8,
                "growth_rate": 12.5,
                "market_cap": 2500000000,
                "headquarters": "San Francisco, CA"
            },
            confidence_scores={
                "company_name": 0.98,
                "revenue": 0.94,
                "quarter": 0.96,
                "contact_email": 0.89,
                "employee_count": 0.87,
                "profit_margin": 0.82,
                "growth_rate": 0.78,
                "market_cap": 0.71,
                "headquarters": 0.93
            },
            processing_time=2.8,
            errors=[],
            status=ProcessingStatus.COMPLETED
        ),
        
        # Medium-quality extraction with some missing data
        ExtractionResult(
            source_file="quarterly_summary_q3.docx",
            extracted_data={
                "company_name": "Global Manufacturing Corp",
                "revenue": 8900000.25,
                "quarter": "Q3 2024", 
                "contact_email": None,  # Missing
                "employee_count": 320,
                "profit_margin": 15.2,
                "growth_rate": None,  # Missing
                "market_cap": None,  # Missing
                "headquarters": "Detroit, MI"
            },
            confidence_scores={
                "company_name": 0.91,
                "revenue": 0.76,
                "quarter": 0.88,
                "contact_email": 0.0,
                "employee_count": 0.65,
                "profit_margin": 0.58,
                "growth_rate": 0.0,
                "market_cap": 0.0,
                "headquarters": 0.84
            },
            processing_time=4.2,
            errors=[],
            status=ProcessingStatus.COMPLETED
        ),
        
        # Low-quality extraction with issues
        ExtractionResult(
            source_file="scanned_document_poor_quality.pdf",
            extracted_data={
                "company_name": "Unclear Text Inc",  # Low confidence
                "revenue": 1200000,  # No decimal precision
                "quarter": "Q2 2024",
                "contact_email": "unclear@email.com",  # Low confidence
                "employee_count": 150,
                "profit_margin": None,  # Missing
                "growth_rate": -2.1,  # Negative growth
                "market_cap": None,  # Missing
                "headquarters": None  # Missing
            },
            confidence_scores={
                "company_name": 0.42,
                "revenue": 0.38,
                "quarter": 0.67,
                "contact_email": 0.28,
                "employee_count": 0.45,
                "profit_margin": 0.0,
                "growth_rate": 0.51,
                "market_cap": 0.0,
                "headquarters": 0.0
            },
            processing_time=6.8,
            errors=["OCR quality warning: Text clarity below optimal threshold"],
            status=ProcessingStatus.COMPLETED
        ),
        
        # Failed processing
        ExtractionResult(
            source_file="corrupted_file.pdf",
            extracted_data={},
            confidence_scores={},
            processing_time=1.2,
            errors=[
                "PDF parsing failed: File appears to be corrupted",
                "OCR fallback failed: No readable text detected",
                "Manual review required"
            ],
            status=ProcessingStatus.FAILED
        ),
        
        # Currently processing
        ExtractionResult(
            source_file="large_document_processing.pdf",
            extracted_data={
                "company_name": "DataCorp Analytics Ltd.",
                "revenue": None,  # Still processing
                "quarter": "Q1 2024",
                "contact_email": None,  # Still processing
                "employee_count": 275,
                "profit_margin": None,  # Still processing
                "growth_rate": None,  # Still processing
                "market_cap": None,  # Still processing
                "headquarters": "Austin, TX"
            },
            confidence_scores={
                "company_name": 0.91,
                "revenue": 0.0,
                "quarter": 0.85,
                "contact_email": 0.0,
                "employee_count": 0.72,
                "profit_margin": 0.0,
                "growth_rate": 0.0,
                "market_cap": 0.0,
                "headquarters": 0.88
            },
            processing_time=0.0,
            errors=[],
            status=ProcessingStatus.PROCESSING
        ),
        
        # Pending processing
        ExtractionResult(
            source_file="pending_financial_report.xlsx",
            extracted_data={},
            confidence_scores={},
            processing_time=0.0,
            errors=[],
            status=ProcessingStatus.PENDING
        )
    ]
    
    # Enhanced template fields with more variety
    template_fields = [
        {
            "name": "company_name", 
            "type": "text", 
            "description": "Legal company name as registered",
            "optional": False
        },
        {
            "name": "revenue", 
            "type": "currency", 
            "description": "Total revenue for the reporting period",
            "optional": False
        },
        {
            "name": "quarter", 
            "type": "text", 
            "description": "Reporting quarter (Q1, Q2, Q3, Q4)",
            "optional": False
        },
        {
            "name": "contact_email", 
            "type": "text", 
            "description": "Investor relations or main contact email",
            "optional": True
        },
        {
            "name": "employee_count", 
            "type": "number", 
            "description": "Total number of employees",
            "optional": True
        },
        {
            "name": "profit_margin", 
            "type": "number", 
            "description": "Profit margin percentage",
            "optional": True
        },
        {
            "name": "growth_rate", 
            "type": "number", 
            "description": "Year-over-year growth rate percentage",
            "optional": True
        },
        {
            "name": "market_cap", 
            "type": "currency", 
            "description": "Market capitalization",
            "optional": True
        },
        {
            "name": "headquarters", 
            "type": "text", 
            "description": "Company headquarters location",
            "optional": True
        }
    ]
    
    # Create enhanced template
    template = ExtractionTemplate(
        name="enhanced_financial_template",
        prompt_description="Extract comprehensive financial data from corporate reports",
        fields=[
            ExtractionField("company_name", FieldType.TEXT, "Legal company name"),
            ExtractionField("revenue", FieldType.CURRENCY, "Total revenue"),
            ExtractionField("quarter", FieldType.TEXT, "Reporting quarter"),
            ExtractionField("contact_email", FieldType.TEXT, "Contact email", optional=True),
            ExtractionField("employee_count", FieldType.NUMBER, "Employee count", optional=True),
            ExtractionField("profit_margin", FieldType.NUMBER, "Profit margin %", optional=True),
            ExtractionField("growth_rate", FieldType.NUMBER, "Growth rate %", optional=True),
            ExtractionField("market_cap", FieldType.CURRENCY, "Market cap", optional=True),
            ExtractionField("headquarters", FieldType.TEXT, "HQ location", optional=True)
        ]
    )
    
    # Create enhanced session
    session = ProcessingSession(
        template=template,
        files=[result.source_file for result in results],
        results=results,
        summary_stats={
            "total_processing_time": sum(r.processing_time for r in results),
            "avg_confidence": 0.72,
            "data_quality_score": 0.78
        }
    )
    
    return results, template_fields, session


class EnhancedPreviewPanelDemo(QMainWindow):
    """Enhanced demo window showcasing Phase 2 PreviewPanel functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PreviewPanel Phase 2 Demo - Enhanced Features")
        self.setMinimumSize(1100, 800)
        self.resize(1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Control panel
        self.create_control_panel(main_layout)
        
        # Create preview panel
        self.preview_panel = PreviewPanel()
        main_layout.addWidget(self.preview_panel, 1)
        
        # Load enhanced sample data
        self.results, self.template_fields, self.session = create_enhanced_sample_data()
        self.current_file_index = 0
        
        # Setup demo timer
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.auto_cycle_demo)
        self.demo_step = 0
        
        # Connect preview panel signals
        self.connect_signals()
        
        # Start demo
        self.start_enhanced_demo()
    
    def create_control_panel(self, parent_layout):
        """Create control panel for demo interaction."""
        control_frame = QWidget()
        control_layout = QHBoxLayout(control_frame)
        
        # File navigation buttons
        self.prev_btn = QPushButton("◀ Previous File")
        self.prev_btn.clicked.connect(self.show_previous_file)
        control_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Next File ▶")
        self.next_btn.clicked.connect(self.show_next_file)
        control_layout.addWidget(self.next_btn)
        
        control_layout.addStretch()
        
        # View control buttons
        self.file_view_btn = QPushButton("File View")
        self.file_view_btn.clicked.connect(lambda: self.preview_panel.set_active_tab("File Preview"))
        control_layout.addWidget(self.file_view_btn)
        
        self.summary_view_btn = QPushButton("Summary View")
        self.summary_view_btn.clicked.connect(lambda: self.preview_panel.set_active_tab("Summary"))
        control_layout.addWidget(self.summary_view_btn)
        
        control_layout.addStretch()
        
        # Demo control
        self.auto_demo_btn = QPushButton("Start Auto Demo")
        self.auto_demo_btn.clicked.connect(self.toggle_auto_demo)
        control_layout.addWidget(self.auto_demo_btn)
        
        parent_layout.addWidget(control_frame)
    
    def connect_signals(self):
        """Connect preview panel signals for demonstration."""
        self.preview_panel.preview_updated.connect(self.on_preview_updated)
    
    def start_enhanced_demo(self):
        """Start the enhanced Phase 2 demo."""
        print("🎬 Starting Enhanced PreviewPanel Phase 2 Demo")
        print("=" * 50)
        print("🆕 New Phase 2 Features:")
        print("   • Enhanced file selection with varied mock scenarios")
        print("   • Interactive data field widgets with copy functionality")
        print("   • Grouped field display by confidence levels")
        print("   • Processing state indicators with progress bars")
        print("   • Advanced summary with quality metrics")
        print("   • Data completeness visualization")
        print("   • Enhanced error handling and validation")
        print("   • Professional UI improvements")
        print()
        
        # Show initial file
        self.show_current_file()
    
    def show_current_file(self):
        """Show the current file in the preview."""
        if 0 <= self.current_file_index < len(self.results):
            result = self.results[self.current_file_index]
            print(f"📄 Showing file {self.current_file_index + 1}/{len(self.results)}: {result.source_file}")
            print(f"   Status: {result.status.value} | Confidence: {self.get_avg_confidence(result):.1%}")
            
            self.preview_panel.update_file_preview(result, self.template_fields)
            self.preview_panel.update_summary_preview(self.session)
            
            # Update button states
            self.prev_btn.setEnabled(self.current_file_index > 0)
            self.next_btn.setEnabled(self.current_file_index < len(self.results) - 1)
    
    def show_previous_file(self):
        """Show previous file."""
        if self.current_file_index > 0:
            self.current_file_index -= 1
            self.show_current_file()
    
    def show_next_file(self):
        """Show next file."""
        if self.current_file_index < len(self.results) - 1:
            self.current_file_index += 1
            self.show_current_file()
    
    def get_avg_confidence(self, result: ExtractionResult) -> float:
        """Calculate average confidence for a result."""
        if not result.confidence_scores:
            return 0.0
        return sum(result.confidence_scores.values()) / len(result.confidence_scores)
    
    def toggle_auto_demo(self):
        """Toggle automatic demo mode."""
        if self.demo_timer.isActive():
            self.demo_timer.stop()
            self.auto_demo_btn.setText("Start Auto Demo")
            print("⏸️ Auto demo paused")
        else:
            self.demo_timer.start(4000)  # Change every 4 seconds
            self.auto_demo_btn.setText("Stop Auto Demo")
            print("▶️ Auto demo started")
    
    def auto_cycle_demo(self):
        """Auto cycle through demo views."""
        if self.demo_step % 2 == 0:
            # Show file view
            self.preview_panel.set_active_tab("File Preview")
            if self.demo_step > 0:  # Don't change file on first step
                self.show_next_file()
                if self.current_file_index >= len(self.results) - 1:
                    self.current_file_index = 0
                    self.show_current_file()
        else:
            # Show summary view
            self.preview_panel.set_active_tab("Summary")
        
        self.demo_step += 1
    
    def on_preview_updated(self):
        """Handle preview update signals."""
        current_tab = self.preview_panel.get_current_tab()
        print(f"🔄 Preview updated - Current tab: {current_tab}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        print()
        print("🏁 Enhanced Phase 2 Demo completed!")
        print("✅ All Phase 2 features demonstrated:")
        print("   ✓ Enhanced file selection integration")
        print("   ✓ Interactive data field widgets")
        print("   ✓ Advanced data visualization")
        print("   ✓ Processing state management")
        print("   ✓ Quality metrics and analytics")
        print("   ✓ Professional UI enhancements")
        print()
        print("🚀 Ready for Phase 3 implementation!")
        event.accept()


def main():
    """Run the enhanced PreviewPanel Phase 2 demo."""
    print("🚀 LangExtractor PreviewPanel Phase 2 Demo")
    print("Enhanced Features & Interactions")
    print("=" * 50)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show enhanced demo window
    demo = EnhancedPreviewPanelDemo()
    demo.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
