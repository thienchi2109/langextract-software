"""
Demo script for Excel Export Integration - Complete Workflow.

This demo showcases the complete workflow with Excel export:
- File processing with real-time charts updates
- Excel export functionality integrated in MainWindow
- Professional Excel output with Data and Summary sheets
- Complete end-to-end processing pipeline

Run this script to test the full workflow from processing to Excel export.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def create_sample_files():
    """Create sample files with realistic financial data for testing Excel export."""
    sample_texts = [
        """
        TechViet Solutions Ltd. - Báo cáo tài chính Q4 2024
        
        Thông tin công ty:
        TechViet Solutions Ltd. là công ty công nghệ hàng đầu Việt Nam chuyên về phần mềm.
        
        Kết quả kinh doanh:
        - Doanh thu: 25.750.000.000 VNĐ
        - Nhân viên: 485 người
        - Lợi nhuận: 18.2%
        - Tăng trưởng: 15.8%
        - Vốn hóa: 850.000.000.000 VNĐ
        
        Thông tin liên hệ:
        Email: ir@techviet.vn
        Trụ sở: Hà Nội, Việt Nam
        Ngành: Công nghệ thông tin
        """,
        
        """
        Global Manufacturing Vietnam Co., Ltd - Q3 2024 Results
        
        Company: Global Manufacturing Vietnam Co., Ltd
        
        Financial Performance:
        - Revenue: 45.900.000.000 VND
        - Employees: 1,250 staff members
        - Profit Margin: 12.5%
        - Growth Rate: 8.7%
        - Market Cap: 1.200.000.000.000 VND
        
        Contact Information:
        Email: contact@globalmfg.vn
        Location: Ho Chi Minh City, Vietnam
        Industry: Manufacturing & Production
        """,
        
        """
        Vietnam Digital Bank - Báo cáo Q2 2024
        
        Tên tổ chức: Vietnam Digital Bank JSC
        
        Hiệu quả hoạt động:
        - Doanh thu hoạt động: 125.000.000.000 VNĐ
        - Cán bộ nhân viên: 2,100 người
        - Tỷ suất lợi nhuận: 28.4%
        - Tăng trưởng năm: 6.2%
        - Vốn hóa thị trường: 3.600.000.000.000 VNĐ
        
        Thông tin doanh nghiệp:
        Email: investor@vietdigitalbank.vn
        Trụ sở chính: TP. Hồ Chí Minh, Việt Nam
        Lĩnh vực: Dịch vụ tài chính ngân hàng
        """,
        
        """
        Viet Retail Corporation - Annual Report 2024
        
        Company Name: Viet Retail Corporation
        
        Business Results:
        - Total Revenue: 89.200.000.000 VND
        - Workforce: 3,500 employees
        - Net Margin: 14.7%
        - YoY Growth: 22.3%
        - Enterprise Value: 2.100.000.000.000 VND
        
        Company Details:
        Contact: ir@vietretail.com.vn
        Headquarters: Da Nang, Vietnam
        Sector: Retail & Consumer Goods
        """,
        
        """
        Green Energy Vietnam Ltd - Q1 2024 Financial Statement
        
        Organization: Green Energy Vietnam Ltd
        
        Key Metrics:
        - Operating Revenue: 67.800.000.000 VND
        - Personnel: 850 employees
        - Operating Margin: 19.6%
        - Growth: 28.5%
        - Market Valuation: 1.800.000.000.000 VND
        
        Corporate Info:
        Email: info@greenenergy.vn
        Office: Can Tho, Vietnam
        Industry: Renewable Energy
        """
    ]
    
    # Create temporary files
    temp_dir = Path(tempfile.gettempdir()) / "langextract_excel_demo"
    temp_dir.mkdir(exist_ok=True)
    
    file_paths = []
    for i, text in enumerate(sample_texts):
        file_path = temp_dir / f"financial_report_{i+1}.txt"
        file_path.write_text(text.strip(), encoding='utf-8')
        file_paths.append(str(file_path))
    
    return file_paths


class ExcelExportDemoWindow(MainWindow):
    """Demo window extending MainWindow for Excel export demonstration."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel Export Demo - Complete Processing Workflow")
        self.setup_demo_ui()
        self.load_sample_files()
    
    def setup_demo_ui(self):
        """Add demo-specific UI elements."""
        # Add demo info banner
        demo_banner = QWidget()
        demo_banner.setStyleSheet("""
            QWidget {
                background-color: #F0FDF4;
                border: 1px solid #16A34A;
                border-radius: 8px;
                padding: 12px;
                margin: 8px;
            }
        """)
        
        banner_layout = QVBoxLayout(demo_banner)
        
        # Title
        title_label = QLabel("📊 Excel Export Demo - Complete Processing Workflow")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #15803D; margin-bottom: 4px;")
        banner_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Complete workflow from file processing to professional Excel export. "
            "Process the sample Vietnamese financial reports and export to Excel with charts and statistics!"
        )
        desc_label.setStyleSheet("color: #15803D; font-size: 11px;")
        desc_label.setWordWrap(True)
        banner_layout.addWidget(desc_label)
        
        # Demo instructions
        instructions_layout = QHBoxLayout()
        
        step1_label = QLabel("1️⃣ Files loaded")
        step1_label.setStyleSheet("color: #15803D; font-size: 10px; font-weight: 600;")
        instructions_layout.addWidget(step1_label)
        
        step2_label = QLabel("2️⃣ Click 'Start Processing'")
        step2_label.setStyleSheet("color: #15803D; font-size: 10px; font-weight: 600;")
        instructions_layout.addWidget(step2_label)
        
        step3_label = QLabel("3️⃣ Watch real-time charts")
        step3_label.setStyleSheet("color: #15803D; font-size: 10px; font-weight: 600;")
        instructions_layout.addWidget(step3_label)
        
        step4_label = QLabel("4️⃣ Export to Excel!")
        step4_label.setStyleSheet("color: #15803D; font-size: 10px; font-weight: 600;")
        instructions_layout.addWidget(step4_label)
        
        instructions_layout.addStretch()
        
        reload_btn = QPushButton("🔄 Reload Files")
        reload_btn.setStyleSheet("""
            QPushButton {
                background-color: #16A34A;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #15803D;
            }
        """)
        reload_btn.clicked.connect(self.load_sample_files)
        instructions_layout.addWidget(reload_btn)
        
        banner_layout.addLayout(instructions_layout)
        
        # Insert banner at the top
        central_widget = self.centralWidget()
        layout = central_widget.layout()
        layout.insertWidget(0, demo_banner)
    
    def load_sample_files(self):
        """Load sample financial reports for demo."""
        try:
            sample_files = create_sample_files()
            
            # Clear existing files
            self.file_list.clear()
            
            # Add sample files
            for file_path in sample_files:
                self.file_list.add_file(file_path)
            
            self.show_toast_message(f"Loaded {len(sample_files)} Vietnamese financial reports", "success")
            
            # Update UI
            self.update_ui_state()
            
            # Show helpful message
            self.status_bar.showMessage(
                "Vietnamese financial reports loaded - Ready for processing and Excel export!"
            )
            
        except Exception as e:
            self.show_toast_message(f"Failed to load sample files: {str(e)}", "error")


def main():
    """Run the Excel Export demo application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Excel Export Demo")
    app.setApplicationVersion("1.0.0")
    
    # Apply global styling
    app.setStyleSheet("""
        QApplication {
            font-family: "Segoe UI", "Arial", sans-serif;
        }
    """)
    
    # Create and show demo window
    demo_window = ExcelExportDemoWindow()
    demo_window.show()
    
    print("📊 Excel Export Demo Started!")
    print("\nComplete Processing Workflow:")
    print("  1️⃣  Vietnamese financial reports pre-loaded")
    print("  2️⃣  Click 'Start Processing' to begin extraction")
    print("  3️⃣  Watch real-time charts update as files are processed")
    print("  4️⃣  Click 'Export to Excel' when processing completes")
    print("  📋 Professional Excel output with Data and Summary sheets")
    print("\nFeatures tested:")
    print("  📊 Real-time processing with charts")
    print("  📈 Analytics dashboard with 4 chart types")
    print("  📋 Excel export with aggregated data")
    print("  📊 Summary statistics and quality metrics")
    print("  🎨 Professional Excel formatting")
    print("  🔧 Error handling and validation")
    print("\nInstructions:")
    print("  • Process the sample files to see extraction in action")
    print("  • Switch to 'Analytics Dashboard' tab for live charts")
    print("  • Export results to Excel after processing completes")
    print("  • Check both Data and Summary sheets in Excel output")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 