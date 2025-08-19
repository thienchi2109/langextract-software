"""
Demo Complete Workflow với Settings Dialog - GUI hoàn chỉnh 100%.

Workflow hoàn chỉnh:
1. Mở Settings để nhập API key Gemini
2. Cấu hình OCR và Privacy settings  
3. Import files (PDF/Word)
4. Cấu hình Schema (tiếng Việt)
5. Xử lý với OCR + LangExtract AI
6. Xem preview kết quả
7. Xuất Excel

Giờ đây ứng dụng hoạt động 100% trên GUI!
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.simple_main_window import SimpleMainWindow


def main():
    """Chạy ứng dụng hoàn chỉnh với Settings."""
    app = QApplication(sys.argv)
    
    # Set app properties
    app.setApplicationName("LangExtractor Complete")
    app.setApplicationVersion("1.0.0")
    
    # Create main window
    window = SimpleMainWindow()
    window.show()
    
    print("🚀 LangExtractor Complete với Settings Started!")
    print("\n🎯 Workflow hoàn chỉnh:")
    print("  1️⃣ Mở Settings (Tools → Cài đặt hoặc Ctrl+,)")
    print("     • Tab 'API Key': Nhập API key Gemini")
    print("     • Tab 'OCR': Cài đặt ngôn ngữ và chất lượng")
    print("     • Tab 'Privacy': Cấu hình PII masking, offline mode")
    print("  2️⃣ Import files (drag-drop hoặc 'Thêm file')")
    print("  3️⃣ Cấu hình Schema ('Cấu hình Schema' - tên tiếng Việt OK)")
    print("  4️⃣ Xử lý files ('Bắt đầu xử lý' - tự động check API key)")
    print("  5️⃣ Xem preview trong 2 tab")
    print("  6️⃣ Xuất Excel ('Xuất Excel')")
    print("\n✨ Tính năng mới:")
    print("  🔑 API Key Management: Lưu an toàn vào Windows Credential Manager")
    print("  🧪 API Key Testing: Test API key trước khi lưu")
    print("  ⚙️ OCR Settings: Cấu hình ngôn ngữ và chất lượng OCR")
    print("  🔒 Privacy Controls: PII masking và offline mode")
    print("  ✅ Validation: Tự động check API key trước khi xử lý")
    print("\n🎉 GUI hoàn chỉnh 100% - không cần terminal commands!")
    print("\n📋 Hướng dẫn chi tiết:")
    print("  • Bắt đầu bằng mở Settings để setup API key")
    print("  • Lấy API key miễn phí tại: https://aistudio.google.com/app/apikey")
    print("  • Test API key trước khi lưu để đảm bảo hoạt động")
    print("  • Thử offline mode nếu không muốn dùng AI cloud")
    print("  • Schema Editor support tên tiếng Việt như 'tên công ty', 'doanh thu'")
    print("  • Ứng dụng sẽ tự động nhắc nhở nếu thiếu API key")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 