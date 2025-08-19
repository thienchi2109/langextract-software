"""
Test script để verify Schema Editor cho phép tên trường tiếng Việt.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QDialog

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.schema_editor import SchemaEditor
from core.models import ExtractionTemplate, ExtractionField, FieldType


def test_vietnamese_field_names():
    """Test schema editor với tên trường tiếng Việt."""
    app = QApplication(sys.argv)
    
    # Tạo schema editor dialog
    dialog = SchemaEditor()
    
    print("🧪 Testing Schema Editor với tên trường tiếng Việt")
    print("📝 Instructions:")
    print("  1. Dialog sẽ mở")
    print("  2. Thêm các trường với tên tiếng Việt:")
    print("     • 'tên công ty' (text)")
    print("     • 'doanh thu' (currency)")  
    print("     • 'số nhân viên' (number)")
    print("     • 'thời gian báo cáo' (text)")
    print("  3. Click OK để test conversion")
    print("  4. Sẽ hiển thị kết quả conversion")
    
    # Hiển thị dialog
    result = dialog.exec()
    
    if result == QDialog.Accepted:
        template = dialog.get_template()
        
        if template:
            print("\n✅ Schema Editor test thành công!")
            print(f"📋 Template name: {template.name}")
            print(f"🔢 Number of fields: {len(template.fields)}")
            print("\n📊 Field conversions:")
            
            for field in template.fields:
                display_name = getattr(field, 'display_name', 'N/A')
                print(f"  • '{display_name}' → '{field.name}' ({field.type.value})")
                
            print("\n🎯 Test completed successfully!")
        else:
            print("\n❌ Schema validation failed")
    else:
        print("\n⏹️ Dialog cancelled")
    
    return 0


if __name__ == "__main__":
    sys.exit(test_vietnamese_field_names()) 