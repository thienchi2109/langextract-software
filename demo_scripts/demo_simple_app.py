"""
Demo Simple App - chỉ tập trung vào workflow cốt lõi.

Workflow đơn giản:
1. Import file PDF/Word
2. Cấu hình Schema (tiếng Việt)
3. Xử lý với OCR + AI
4. Xem trước kết quả
5. Xuất Excel

Không có analytics dashboard hay charts phức tạp.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.simple_main_window import SimpleMainWindow


def main():
    """Chạy ứng dụng đơn giản."""
    app = QApplication(sys.argv)
    
    # Set app properties
    app.setApplicationName("LangExtractor Simple")
    app.setApplicationVersion("1.0.0")
    
    # Create main window
    window = SimpleMainWindow()
    window.show()
    
    print("🚀 LangExtractor Simple Started!")
    print("\n📋 Workflow đơn giản:")
    print("  1️⃣ Import file PDF/Word (drag-drop hoặc nút 'Thêm file')")
    print("  2️⃣ Cấu hình Schema (nút 'Cấu hình Schema' - có thể dùng tên tiếng Việt)")
    print("  3️⃣ Xử lý với OCR + AI (nút 'Bắt đầu xử lý')")
    print("  4️⃣ Xem trước kết quả (tab 'Chi tiết file' và 'Tổng quan')")
    print("  5️⃣ Xuất Excel (nút 'Xuất Excel')")
    print("\n✨ Đơn giản và tập trung vào những gì bạn cần!")
    print("💡 Không có analytics dashboard phức tạp hay charts thừa thãi")
    print("\n🎯 Hướng dẫn:")
    print("  • Thử drag-drop file PDF hoặc Word vào cửa sổ")
    print("  • Click 'Cấu hình Schema' để định nghĩa các trường cần trích")
    print("  • Có thể dùng tên tiếng Việt như 'tên công ty', 'doanh thu', etc.")
    print("  • Click 'Bắt đầu xử lý' sau khi có file + schema")
    print("  • Xem kết quả trong 2 tab: Chi tiết file và Tổng quan")
    print("  • Click 'Xuất Excel' để có file Excel với dữ liệu đã trích")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 