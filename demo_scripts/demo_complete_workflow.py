"""
Demo script for Complete OCR + LangExtract + Schema Editor + Excel Export Workflow.

This demo showcases the complete end-to-end functionality:
- User-configurable schema editor for extraction fields
- Real OCR processing for scanned documents
- LangExtract AI-powered data extraction
- Real-time analytics dashboard
- Professional Excel export

Run this script to test the complete automated report extraction system.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.main_window import MainWindow


def create_vietnamese_sample_files():
    """Create Vietnamese sample files to test OCR and extraction."""
    sample_texts = [
        """
        CÔNG TY CỔ PHẦN CÔNG NGHỆ VIETTECH
        BÁO CÁO TÀI CHÍNH QUÝ 4 NĂM 2024
        
        THÔNG TIN DOANH NGHIỆP:
        Tên công ty: Công ty Cổ phần Công nghệ VietTech
        Địa chỉ: Số 123 Nguyễn Huệ, Quận 1, TP.HCM
        Email liên hệ: ir@viettech.com.vn
        
        CÁC CHỈ SỐ TÀI CHÍNH:
        • Doanh thu thuần: 125.750.000.000 VNĐ
        • Lợi nhuận sau thuế: 22.500.000.000 VNĐ  
        • Tổng tài sản: 450.000.000.000 VNĐ
        • Số lượng nhân viên: 850 người
        • Tỷ suất lợi nhuận: 18.2%
        • Tăng trưởng doanh thu: 24.5%
        
        LĨNH VỰC HOẠT ĐỘNG:
        Phát triển phần mềm và dịch vụ công nghệ thông tin
        """,
        
        """
        NGÂN HÀNG THƯƠNG MẠI CỔ PHẦN DIGITAL VIETNAM
        BẢNG CÂN ĐỐI KẾ TOÁN QUÝ 3/2024
        
        THÔNG TIN TỔ CHỨC:
        Tên: Ngân hàng TMCP Digital Vietnam
        Trụ sở chính: 456 Lê Lợi, Q.1, TP.HCM  
        Điện thoại: (028) 3829-xxxx
        Website: www.digitalvietnam.bank
        Email: info@digitalvietnam.bank
        
        HIỆU QUẢ KINH DOANH:
        - Thu nhập lãi thuần: 2.850.000.000.000 VNĐ
        - Lãi từ hoạt động dịch vụ: 456.000.000.000 VNĐ
        - Lợi nhuận trước thuế: 1.200.000.000.000 VNĐ
        - ROE: 16.8%
        - ROA: 1.4%
        - Tổng nhân sự: 4.250 người
        
        NGÀNH NGHỀ: Dịch vụ tài chính ngân hàng
        """,
        
        """
        TẬP ĐOÀN BÁN LẺ SAIGON MART
        BÁO CÁO THƯỜNG NIÊN 2024
        
        GIỚI THIỆU CÔNG TY:
        Tên doanh nghiệp: Tập đoàn Bán lẻ Saigon Mart
        Văn phòng: Tầng 15, Tòa nhà Bitexco, Q.1, TPHCM
        Hotline: 1900-xxxx
        Email: contact@saigonmart.vn
        
        TỔNG QUAN TÀI CHÍNH:
        ★ Doanh thu bán hàng: 89.500.000.000.000 VNĐ
        ★ Chi phí hàng bán: 67.200.000.000.000 VNĐ  
        ★ Lợi nhuận gộp: 22.300.000.000.000 VNĐ
        ★ Biên lợi nhuận gộp: 24.9%
        ★ Tăng trường YoY: 18.7%
        ★ Tổng số cửa hàng: 1.250 điểm
        ★ Nhân viên toàn hệ thống: 25.000 người
        
        NGÀNH: Bán lẻ và tiêu dùng
        """,
        
        """
        CÔNG TY TNHH NĂNG LƯỢNG XANH VIỆT NAM
        THÔNG TIN TÀI CHÍNH QUÝ I/2024
        
        HỒ SƠ DOANH NGHIỆP:
        Công ty: Năng lượng Xanh Việt Nam Limited
        Địa chỉ: KCN Hiệp Phước, TP. Thủ Đức, TPHCM
        Fax: (028) 3715-xxxx  
        Email: info@greenenergy.vn
        
        BẢNG SỐ LIỆU:
        → Doanh thu hoạt động: 45.800.000.000 VNĐ
        → Chi phí sản xuất: 32.100.000.000 VNĐ
        → EBITDA: 18.500.000.000 VNĐ
        → Margin EBITDA: 40.4%  
        → Tăng trưởng: 32.1%
        → Công suất lắp đặt: 150 MW
        → Lao động: 680 nhân viên
        
        LĨNH VỰC: Năng lượng tái tạo
        """,
        
        """
        CÔNG TY CỔ PHẦN VẬN TẢI LOGISTICS MIỀN NAM
        FINANCIAL REPORT Q2 2024
        
        COMPANY INFORMATION:
        Name: Southern Logistics Corporation  
        Address: 789 Nguyen Van Linh, District 7, HCMC
        Phone: +84-28-3xxx-xxxx
        Contact Email: ir@southernlogistics.vn
        
        FINANCIAL HIGHLIGHTS:
        ◆ Revenue: 156.700.000.000 VND
        ◆ Operating Profit: 18.900.000.000 VND
        ◆ Net Income: 14.200.000.000 VND
        ◆ Operating Margin: 12.1%
        ◆ Growth Rate: 15.3%
        ◆ Fleet Size: 450 vehicles
        ◆ Employees: 1.850 people
        ◆ Warehouses: 25 locations
        
        INDUSTRY: Transportation & Logistics
        """
    ]
    
    # Create temporary files
    temp_dir = Path(tempfile.gettempdir()) / "langextract_complete_demo"
    temp_dir.mkdir(exist_ok=True)
    
    file_paths = []
    for i, text in enumerate(sample_texts):
        file_path = temp_dir / f"vietnamese_report_{i+1}.txt"
        file_path.write_text(text.strip(), encoding='utf-8')
        file_paths.append(str(file_path))
    
    return file_paths


class CompleteWorkflowDemoWindow(MainWindow):
    """Demo window for complete OCR + LangExtract + Schema Editor workflow."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Complete Workflow Demo - OCR + LangExtract + Schema + Excel Export")
        self.setup_demo_ui()
        self.load_sample_files()
    
    def setup_demo_ui(self):
        """Add demo-specific UI elements."""
        # Add demo info banner
        demo_banner = QWidget()
        demo_banner.setStyleSheet("""
            QWidget {
                background-color: #FEF3C7;
                border: 1px solid #F59E0B;
                border-radius: 8px;
                padding: 16px;
                margin: 8px;
            }
        """)
        
        banner_layout = QVBoxLayout(demo_banner)
        
        # Title
        title_label = QLabel("🔥 Complete Automated Report Extraction Demo")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #92400E; margin-bottom: 8px;")
        banner_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "🎯 Complete end-to-end workflow: User-configurable schema → OCR processing → "
            "AI-powered extraction → Real-time charts → Professional Excel export. "
            "Test with Vietnamese financial reports!"
        )
        desc_label.setStyleSheet("color: #92400E; font-size: 12px; font-weight: 500;")
        desc_label.setWordWrap(True)
        banner_layout.addWidget(desc_label)
        
        # Workflow steps
        steps_layout = QHBoxLayout()
        
        steps = [
            "1️⃣ Configure Schema",
            "2️⃣ Load Files", 
            "3️⃣ Start Processing",
            "4️⃣ View Live Charts",
            "5️⃣ Export Excel"
        ]
        
        for step in steps:
            step_label = QLabel(step)
            step_label.setStyleSheet("color: #92400E; font-size: 11px; font-weight: 600; padding: 4px 8px; background-color: #FBBF24; border-radius: 4px; margin: 2px;")
            steps_layout.addWidget(step_label)
        
        steps_layout.addStretch()
        
        # Demo controls
        reload_btn = QPushButton("🔄 Reload Sample Files")
        reload_btn.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #D97706;
            }
        """)
        reload_btn.clicked.connect(self.load_sample_files)
        steps_layout.addWidget(reload_btn)
        
        banner_layout.addLayout(steps_layout)
        
        # Insert banner at the top
        central_widget = self.centralWidget()
        layout = central_widget.layout()
        layout.insertWidget(0, demo_banner)
    
    def load_sample_files(self):
        """Load Vietnamese sample financial reports."""
        try:
            sample_files = create_vietnamese_sample_files()
            
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
                f"{len(sample_files)} Vietnamese reports loaded - Configure schema to enable processing!"
            )
            
        except Exception as e:
            self.show_toast_message(f"Failed to load sample files: {str(e)}", "error")


def main():
    """Run the complete workflow demo."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Complete Workflow Demo")
    app.setApplicationVersion("1.0.0")
    
    # Apply global styling
    app.setStyleSheet("""
        QApplication {
            font-family: "Segoe UI", "Arial", sans-serif;
        }
    """)
    
    # Create and show demo window
    demo_window = CompleteWorkflowDemoWindow()
    demo_window.show()
    
    print("🔥 Complete Automated Report Extraction Demo Started!")
    print("\n🎯 End-to-End Workflow Features:")
    print("  1️⃣  User-configurable Schema Editor (define your own extraction fields)")
    print("  2️⃣  Real OCR processing with EasyOCR (Vietnamese + English support)")
    print("  3️⃣  AI-powered extraction with LangExtract + Gemini")
    print("  4️⃣  Real-time analytics dashboard with 4 chart types")
    print("  5️⃣  Professional Excel export with Data + Summary sheets")
    print("\n📋 Vietnamese Test Data:")
    print("  • VietTech - Technology company financial report")
    print("  • Digital Vietnam Bank - Banking sector report")
    print("  • Saigon Mart - Retail conglomerate annual report")
    print("  • Green Energy Vietnam - Renewable energy quarterly")
    print("  • Southern Logistics - Transportation & logistics")
    print("\n🛠️ Complete Workflow Instructions:")
    print("  Step 1: Click 'Configure Schema' to define extraction fields")
    print("  Step 2: Sample Vietnamese files are pre-loaded")
    print("  Step 3: Click 'Start Processing' (OCR + AI extraction)")
    print("  Step 4: Switch to 'Analytics Dashboard' for live charts")
    print("  Step 5: Click 'Export to Excel' for professional reports")
    print("\n🔧 Technology Stack:")
    print("  • OCR: EasyOCR with Vietnamese language support")
    print("  • AI Extraction: LangExtract + Google Gemini")
    print("  • Charts: Matplotlib with real-time updates")
    print("  • Export: Professional Excel with xlsxwriter")
    print("  • UI: Modern PySide6 with responsive design")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 