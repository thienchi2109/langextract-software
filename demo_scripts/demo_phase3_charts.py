"""
Demo script for Phase 3 Advanced Charts and Analytics Dashboard.

This demo showcases the new Phase 3 features:
- Interactive confidence trend charts
- Data quality pie charts
- Field distribution bar charts
- Real-time processing metrics
- Chart export capabilities
- Analytics dashboard with real-time updates

Run this script to see all Phase 3 chart features in action.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
import numpy as np
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.enhanced_preview_panel import EnhancedPreviewPanel
from core.models import (
    ExtractionResult, ProcessingSession, ExtractionTemplate, ExtractionField,
    ProcessingStatus, FieldType
)


def create_sample_template():
    """Create a sample extraction template for testing."""
    fields = [
        ExtractionField(name="company_name", type=FieldType.TEXT, description="Company name"),
        ExtractionField(name="revenue", type=FieldType.CURRENCY, description="Annual revenue"),
        ExtractionField(name="quarter", type=FieldType.TEXT, description="Reporting quarter"),
        ExtractionField(name="contact_email", type=FieldType.TEXT, description="Contact email"),
        ExtractionField(name="employee_count", type=FieldType.NUMBER, description="Number of employees"),
        ExtractionField(name="profit_margin", type=FieldType.NUMBER, description="Profit margin percentage"),
        ExtractionField(name="growth_rate", type=FieldType.NUMBER, description="Growth rate percentage"),
        ExtractionField(name="market_cap", type=FieldType.CURRENCY, description="Market capitalization"),
        ExtractionField(name="headquarters", type=FieldType.TEXT, description="Company headquarters"),
        ExtractionField(name="industry", type=FieldType.TEXT, description="Industry sector")
    ]
    
    return ExtractionTemplate(
        name="financial_analysis_demo",
        prompt_description="Extract financial metrics from quarterly reports",
        fields=fields,
        examples=[],
        provider={"name": "gemini"},
        run_options={}
    )


def create_comprehensive_sample_data():
    """Create comprehensive sample data demonstrating various scenarios."""
    
    # Sample extraction results with varied quality and confidence
    results = []
    
    # Dataset 1: Excellent quality extractions
    for i in range(5):
        result = ExtractionResult(
            source_file=f"excellent_report_{i+1}.pdf",
            extracted_data={
                "company_name": f"TechCorp Inc. {i+1}",
                "revenue": 15750000.50 + i * 2000000,
                "quarter": "Q4 2024",
                "contact_email": f"investor@techcorp{i+1}.com",
                "employee_count": 485 + i * 50,
                "profit_margin": 22.8 + i * 2.1,
                "growth_rate": 12.5 + i * 1.5,
                "market_cap": 2500000000 + i * 500000000,
                "headquarters": "San Francisco, CA",
                "industry": "Technology"
            },
            confidence_scores={
                "company_name": 0.98 - i * 0.02,
                "revenue": 0.94 - i * 0.03,
                "quarter": 0.96 - i * 0.01,
                "contact_email": 0.89 - i * 0.04,
                "employee_count": 0.87 - i * 0.02,
                "profit_margin": 0.92 - i * 0.05,
                "growth_rate": 0.88 - i * 0.03,
                "market_cap": 0.85 - i * 0.04,
                "headquarters": 0.93 - i * 0.02,
                "industry": 0.91 - i * 0.01
            },
            processing_time=2.8 + i * 0.3,
            errors=[],
            status=ProcessingStatus.COMPLETED
        )
        results.append(result)
    
    # Dataset 2: Good quality extractions with some missing data
    for i in range(4):
        result = ExtractionResult(
            source_file=f"good_report_{i+1}.docx",
            extracted_data={
                "company_name": f"Global Corp {i+1}",
                "revenue": 8900000.25 + i * 1500000,
                "quarter": "Q3 2024", 
                "contact_email": f"info@global{i+1}.com" if i < 2 else None,
                "employee_count": 320 + i * 40,
                "profit_margin": 15.2 + i * 1.8,
                "growth_rate": 8.3 + i * 1.2 if i < 3 else None,
                "market_cap": 1200000000 + i * 300000000 if i < 2 else None,
                "headquarters": "New York, NY",
                "industry": "Manufacturing" if i % 2 == 0 else "Finance"
            },
            confidence_scores={
                "company_name": 0.85 + i * 0.03,
                "revenue": 0.76 + i * 0.05,
                "quarter": 0.88 + i * 0.02,
                "contact_email": 0.82 - i * 0.1 if i < 2 else 0.0,
                "employee_count": 0.65 + i * 0.08,
                "profit_margin": 0.58 + i * 0.07,
                "growth_rate": 0.71 + i * 0.04 if i < 3 else 0.0,
                "market_cap": 0.69 + i * 0.06 if i < 2 else 0.0,
                "headquarters": 0.84 + i * 0.02,
                "industry": 0.79 + i * 0.05
            },
            processing_time=4.2 + i * 0.5,
            errors=[],
            status=ProcessingStatus.COMPLETED
        )
        results.append(result)
    
    # Dataset 3: Fair quality extractions with more issues
    for i in range(3):
        result = ExtractionResult(
            source_file=f"fair_report_{i+1}.pdf",
            extracted_data={
                "company_name": f"StartupCo {i+1}" if i < 2 else None,
                "revenue": 2500000.75 + i * 800000 if i < 2 else None,
                "quarter": "Q2 2024" if i == 0 else None,
                "contact_email": None,
                "employee_count": 125 + i * 25 if i < 2 else None,
                "profit_margin": 8.5 + i * 2.1 if i == 0 else None,
                "growth_rate": None,
                "market_cap": None,
                "headquarters": "Austin, TX" if i == 0 else None,
                "industry": "Retail" if i < 2 else None
            },
            confidence_scores={
                "company_name": 0.65 - i * 0.1 if i < 2 else 0.0,
                "revenue": 0.58 - i * 0.08 if i < 2 else 0.0,
                "quarter": 0.72 if i == 0 else 0.0,
                "contact_email": 0.0,
                "employee_count": 0.51 - i * 0.05 if i < 2 else 0.0,
                "profit_margin": 0.45 if i == 0 else 0.0,
                "growth_rate": 0.0,
                "market_cap": 0.0,
                "headquarters": 0.67 if i == 0 else 0.0,
                "industry": 0.55 - i * 0.1 if i < 2 else 0.0
            },
            processing_time=6.1 + i * 0.8,
            errors=[f"Low confidence extraction for field: {field}" for field in ["growth_rate", "market_cap"]],
            status=ProcessingStatus.COMPLETED
        )
        results.append(result)
    
    # Dataset 4: Failed extractions
    for i in range(2):
        result = ExtractionResult(
            source_file=f"failed_document_{i+1}.pdf",
            extracted_data={},
            confidence_scores={},
            processing_time=0.0,
            errors=[
                "Failed to extract text from document",
                "OCR processing failed",
                "Document format not supported"
            ],
            status=ProcessingStatus.FAILED
        )
        results.append(result)
    
    return results


class Phase3DemoWindow(QMainWindow):
    """Main demo window showcasing Phase 3 features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phase 3 Charts & Analytics Dashboard Demo")
        self.setGeometry(100, 100, 1400, 900)
        
        # Sample data
        self.template = create_sample_template()
        self.sample_results = create_comprehensive_sample_data()
        self.current_session = None
        
        # Demo state
        self.demo_step = 0
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.advance_demo)
        
        self.setup_ui()
        self.create_initial_session()
        
    def setup_ui(self):
        """Setup the demo UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header section
        self.create_header_section(layout)
        
        # Enhanced preview panel with charts
        self.preview_panel = EnhancedPreviewPanel()
        layout.addWidget(self.preview_panel)
        
        # Demo controls
        self.create_demo_controls(layout)
        
        # Apply styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F9FAFB;
            }
        """)
    
    def create_header_section(self, parent_layout):
        """Create demo header with information."""
        header_frame = QWidget()
        header_frame.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        header_frame.setMaximumHeight(80)
        
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("🚀 Phase 3: Advanced Charts & Analytics Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #111827; margin-bottom: 8px;")
        header_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Interactive charts with confidence trends, data quality metrics, field statistics, "
            "and real-time processing analytics. Includes chart export capabilities."
        )
        desc_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        desc_label.setWordWrap(True)
        header_layout.addWidget(desc_label)
        
        parent_layout.addWidget(header_frame)
    
    def create_demo_controls(self, parent_layout):
        """Create demo control buttons."""
        controls_frame = QWidget()
        controls_frame.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        controls_frame.setMaximumHeight(60)
        
        controls_layout = QHBoxLayout(controls_frame)
        
        # Demo scenario buttons
        scenarios = [
            ("📊 Load Full Dataset", self.load_full_dataset),
            ("⚡ Start Real-time Demo", self.start_realtime_demo),
            ("📈 Export Charts", self.export_charts),
            ("🔄 Reset Demo", self.reset_demo)
        ]
        
        for text, callback in scenarios:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3B82F6;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
                QPushButton:pressed {
                    background-color: #1D4ED8;
                }
            """)
            btn.clicked.connect(callback)
            controls_layout.addWidget(btn)
        
        controls_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready - Click buttons to see Phase 3 features")
        self.status_label.setStyleSheet("color: #6B7280; font-size: 11px; font-style: italic;")
        controls_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(controls_frame)
    
    def create_initial_session(self):
        """Create initial processing session with sample data."""
        # Start with a subset of data
        initial_results = self.sample_results[:3]
        
        self.current_session = ProcessingSession(
            template=self.template,
            files=[r.source_file for r in initial_results],
            results=initial_results,
            summary_stats={},
            export_path=""
        )
        
        # Update preview panel
        self.preview_panel.update_summary_preview(self.current_session)
        self.update_status("Initial dataset loaded - 3 excellent quality extractions")
    
    def load_full_dataset(self):
        """Load the complete sample dataset."""
        self.current_session = ProcessingSession(
            template=self.template,
            files=[r.source_file for r in self.sample_results],
            results=self.sample_results,
            summary_stats={},
            export_path=""
        )
        
        self.preview_panel.update_summary_preview(self.current_session)
        self.update_status(f"Full dataset loaded - {len(self.sample_results)} files with varied quality")
    
    def start_realtime_demo(self):
        """Start real-time demo simulation."""
        if self.demo_timer.isActive():
            self.demo_timer.stop()
            self.update_status("Real-time demo stopped")
            return
        
        # Start processing session
        self.preview_panel.start_processing_session()
        self.preview_panel.set_realtime_updates(True)
        
        # Reset demo state
        self.demo_step = 0
        self.demo_timer.start(2000)  # Update every 2 seconds
        self.update_status("Real-time demo started - Simulating processing...")
    
    def advance_demo(self):
        """Advance the real-time demo simulation."""
        max_steps = len(self.sample_results)
        
        if self.demo_step >= max_steps:
            self.demo_timer.stop()
            self.update_status("Real-time demo completed")
            return
        
        # Simulate progressive processing
        current_results = self.sample_results[:self.demo_step + 1]
        
        # Add some random processing time variation
        for result in current_results[-1:]:
            if result.status == ProcessingStatus.COMPLETED:
                result.processing_time += np.random.uniform(-0.5, 1.0)
        
        # Update session
        self.current_session = ProcessingSession(
            template=self.template,
            files=[r.source_file for r in current_results],
            results=current_results,
            summary_stats={},
            export_path=""
        )
        
        self.preview_panel.update_summary_preview(self.current_session)
        
        self.demo_step += 1
        self.update_status(f"Processing file {self.demo_step}/{max_steps} - Real-time charts updating...")
    
    def export_charts(self):
        """Export all charts."""
        self.preview_panel.export_charts()
        self.update_status("Chart export dialog opened")
    
    def reset_demo(self):
        """Reset the demo to initial state."""
        if self.demo_timer.isActive():
            self.demo_timer.stop()
        
        self.create_initial_session()
        self.update_status("Demo reset to initial state")
    
    def update_status(self, message: str):
        """Update status message."""
        self.status_label.setText(message)
        print(f"Demo Status: {message}")


def main():
    """Run the Phase 3 demo application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Phase 3 Charts Demo")
    app.setApplicationVersion("1.0.0")
    
    # Apply global styling
    app.setStyleSheet("""
        QApplication {
            font-family: "Segoe UI", "Arial", sans-serif;
        }
    """)
    
    # Create and show demo window
    demo_window = Phase3DemoWindow()
    demo_window.show()
    
    print("🚀 Phase 3 Demo Started!")
    print("Features demonstrated:")
    print("  📊 Interactive confidence trend charts")
    print("  🥧 Data quality pie charts")  
    print("  📊 Field distribution bar charts")
    print("  ⚡ Real-time processing metrics")
    print("  📈 Chart export capabilities")
    print("  🎛️ Analytics dashboard controls")
    print("\nClick the demo buttons to explore all features!")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 