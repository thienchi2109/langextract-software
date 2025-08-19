#!/usr/bin/env python3
"""
Quick test script to verify UI fixes for preview panel text cutoff issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from gui.preview_panel import SummaryPreviewWidget
from core.models import ProcessingSession, ExtractionTemplate, ExtractionField, ExtractionResult, ProcessingStatus, FieldType
from datetime import datetime

def create_test_session():
    """Create a test session with sample data."""
    # Create template
    fields = [
        ExtractionField(name="company_name", type=FieldType.TEXT, description="Company name"),
        ExtractionField(name="revenue", type=FieldType.CURRENCY, description="Annual revenue"),
        ExtractionField(name="employees_count", type=FieldType.NUMBER, description="Number of employees"),
        ExtractionField(name="contact_email", type=FieldType.TEXT, description="Contact email"),
        ExtractionField(name="establishment_date", type=FieldType.DATE, description="Date established"),
        ExtractionField(name="profit_margin", type=FieldType.NUMBER, description="Profit margin"),
        ExtractionField(name="growth_rate", type=FieldType.NUMBER, description="Annual growth rate"),
        ExtractionField(name="market_cap", type=FieldType.CURRENCY, description="Market capitalization"),
        ExtractionField(name="headquarters", type=FieldType.TEXT, description="Headquarters location"),
    ]
    
    template = ExtractionTemplate(
        name="Company Report Template",
        prompt_description="Template for extracting company information",
        fields=fields
    )
    
    # Create results
    results = []
    
    # Result 1 - High confidence
    result1 = ExtractionResult(
        source_file="annual_report_2024.pdf",
        status=ProcessingStatus.COMPLETED,
        extracted_data={
            "company_name": "TechCorp Inc.",
            "revenue": "$50,000,000",
            "employees_count": "250",
            "contact_email": "info@techcorp.com",
            "establishment_date": "2010-03-15",
            "profit_margin": "15.5%",
            "growth_rate": "12.3%",
            "market_cap": "$500,000,000",
            "headquarters": "San Francisco, CA"
        },
        confidence_scores={
            "company_name": 0.95,
            "revenue": 0.88,
            "employees_count": 0.92,
            "contact_email": 0.85,
            "establishment_date": 0.90,
            "profit_margin": 0.87,
            "growth_rate": 0.83,
            "market_cap": 0.89,
            "headquarters": 0.91
        },
        processing_time=2.5
    )
    
    # Result 2 - Medium confidence
    result2 = ExtractionResult(
        source_file="quarterly_report_q3.pdf",
        status=ProcessingStatus.COMPLETED,
        extracted_data={
            "company_name": "DataSoft LLC",
            "revenue": "$25,000,000",
            "employees_count": "120",
            "contact_email": "contact@datasoft.com",
            "establishment_date": "2015-08-20",
            "profit_margin": "8.2%",
            "growth_rate": "7.8%",
            "market_cap": "$180,000,000",
            "headquarters": "Austin, TX"
        },
        confidence_scores={
            "company_name": 0.78,
            "revenue": 0.72,
            "employees_count": 0.75,
            "contact_email": 0.68,
            "establishment_date": 0.70,
            "profit_margin": 0.65,
            "growth_rate": 0.62,
            "market_cap": 0.71,
            "headquarters": 0.74
        },
        processing_time=3.1
    )
    
    # Result 3 - Low confidence
    result3 = ExtractionResult(
        source_file="financial_summary.pdf",
        status=ProcessingStatus.COMPLETED,
        extracted_data={
            "company_name": "InnovateTech",
            "revenue": "$8,500,000",
            "employees_count": "45",
            "contact_email": "",  # Missing data
            "establishment_date": "2020-01-10",
            "profit_margin": "3.1%",
            "growth_rate": "",  # Missing data
            "market_cap": "$45,000,000",
            "headquarters": "Seattle, WA"
        },
        confidence_scores={
            "company_name": 0.45,
            "revenue": 0.42,
            "employees_count": 0.48,
            "contact_email": 0.0,  # No data
            "establishment_date": 0.40,
            "profit_margin": 0.38,
            "growth_rate": 0.0,  # No data
            "market_cap": 0.44,
            "headquarters": 0.46
        },
        processing_time=4.2
    )
    
    results = [result1, result2, result3]
    
    # Create session
    session = ProcessingSession(
        template=template,
        files=["annual_report_2024.pdf", "quarterly_report_q3.pdf", "financial_summary.pdf"],
        results=results
    )
    
    return session

def main():
    """Main test function."""
    app = QApplication(sys.argv)
    
    # Create test widget
    widget = SummaryPreviewWidget()
    widget.setWindowTitle("Preview Panel UI Fix Test")
    widget.resize(800, 600)
    
    # Create and set test session
    session = create_test_session()
    widget.update_summary(session)
    
    # Show widget
    widget.show()
    
    print("🧪 UI Fix Test Started")
    print("📋 Test Instructions:")
    print("   1. Check that all text in 'Data Quality' section is visible")
    print("   2. Check that all text in 'Field Statistics' section is visible")
    print("   3. Verify field names, completeness percentages, and confidence indicators are not cut off")
    print("   4. Test scrolling if content exceeds window size")
    print("   5. Close window when testing is complete")
    
    # Auto-close after 30 seconds for automated testing
    timer = QTimer()
    timer.timeout.connect(app.quit)
    timer.start(30000)  # 30 seconds
    
    # Run app
    result = app.exec()
    
    print("✅ UI Fix Test Completed")
    return result

if __name__ == "__main__":
    sys.exit(main())
