"""
Demo Settings Dialog - test API key management và cài đặt.

Test các tính năng:
- API key input, test, save, load
- OCR settings (languages, quality, threads)
- Privacy settings (PII masking, offline mode)
- Security warnings và validations
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.settings_dialog import SettingsDialog
from core.models import AppConfig


def main():
    """Test settings dialog."""
    app = QApplication(sys.argv)
    
    # Set app properties
    app.setApplicationName("LangExtractor Settings Test")
    app.setApplicationVersion("1.0.0")
    
    # Create test config
    config = AppConfig()
    
    # Create settings dialog
    dialog = SettingsDialog(config)
    
    print("🔧 Settings Dialog Test Started!")
    print("\n📋 Hướng dẫn test:")
    print("  1️⃣ Tab 'API Key': Test nhập/lưu/test API key")
    print("  2️⃣ Tab 'OCR': Cài đặt ngôn ngữ và chất lượng OCR")
    print("  3️⃣ Tab 'Privacy': Cài đặt PII masking và offline mode")
    print("\n🔑 API Key Test:")
    print("  • Nhập API key giả: AIzaSyTestKey123")
    print("  • Click 'Test API Key' (sẽ fail nhưng test được UI)")
    print("  • Click 'Lưu' để test lưu vào Windows Credential Manager")
    print("  • Click 'Xóa' để test xóa API key")
    print("\n🔒 Security Features:")
    print("  • API key được ẩn bằng password field")
    print("  • Click nút mắt để hiện/ẩn")
    print("  • Progress bar khi test API")
    print("  • Status messages với màu sắc")
    
    # Show dialog
    result = dialog.exec()
    
    if result:
        updated_config = dialog.get_config()
        print(f"\n✅ Settings saved!")
        print(f"  • OCR enabled: {updated_config.ocr_enabled}")
        print(f"  • OCR languages: {updated_config.ocr_languages}")
        print(f"  • PII masking: {updated_config.pii_masking_enabled}")
        print(f"  • Offline mode: {updated_config.offline_mode}")
        print(f"  • Max workers: {updated_config.max_workers}")
    else:
        print("\n❌ Settings cancelled")
    
    print("\n🎯 Test completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 