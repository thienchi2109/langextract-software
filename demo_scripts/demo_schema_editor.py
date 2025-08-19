"""
Demo script for Schema Editor dialog.

This script demonstrates the SchemaEditor with proper focus ring styling
and tests the button highlight behavior.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtCore import Qt

from gui.schema_editor import SchemaEditor
from core.models import ExtractionTemplate, ExtractionField, FieldType


class DemoWindow(QMainWindow):
    """Demo window for testing Schema Editor."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schema Editor Demo")
        self.setGeometry(100, 100, 400, 300)
        
        # Apply global style to fix button focus rings
        self.setStyleSheet("""
            QMessageBox QPushButton {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                min-height: 20px;
                min-width: 60px;
            }
            
            QMessageBox QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            
            QMessageBox QPushButton:pressed {
                background-color: #dee2e6;
            }
            
            QMessageBox QPushButton:focus {
                border: 2px solid #0d6efd;
                padding: 7px 15px;
            }
            
            QMessageBox QPushButton:default {
                background-color: #0d6efd;
                border-color: #0d6efd;
                color: white;
            }
            
            QMessageBox QPushButton:default:hover {
                background-color: #0b5ed7;
                border-color: #0a58ca;
            }
            
            QMessageBox QPushButton:default:focus {
                border: 2px solid #ffffff;
                padding: 7px 15px;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Buttons
        self.new_schema_btn = QPushButton("Tạo Schema Mới")
        self.new_schema_btn.clicked.connect(self.create_new_schema)
        layout.addWidget(self.new_schema_btn)
        
        self.edit_schema_btn = QPushButton("Chỉnh sửa Schema Mẫu (Test UI Fixes)")
        self.edit_schema_btn.clicked.connect(self.edit_sample_schema)
        layout.addWidget(self.edit_schema_btn)
        
        self.test_confirmation_btn = QPushButton("Test Confirmation Dialog")
        self.test_confirmation_btn.clicked.connect(self.test_confirmation)
        layout.addWidget(self.test_confirmation_btn)
        
        layout.addStretch()
    
    def create_new_schema(self):
        """Create a new schema."""
        dialog = SchemaEditor()
        if dialog.exec() == SchemaEditor.Accepted:
            template_data = dialog.get_template()
            QMessageBox.information(
                self,
                "Thành công",
                f"Đã tạo schema với {len(template_data['fields'])} trường"
            )
    
    def edit_sample_schema(self):
        """Edit a sample schema."""
        # Create sample template
        sample_template = ExtractionTemplate(
            name="Company Information",
            prompt_description="Extract company information from documents",
            fields=[
                ExtractionField(
                    name="company_name",
                    type=FieldType.TEXT,
                    description="Tên công ty",
                    optional=False
                ),
                ExtractionField(
                    name="revenue",
                    type=FieldType.CURRENCY,
                    description="Doanh thu hàng năm",
                    optional=False,
                    number_locale="vi-VN"
                ),
                ExtractionField(
                    name="employee_count",
                    type=FieldType.NUMBER,
                    description="Số lượng nhân viên làm việc tại công ty (bao gồm cả nhân viên toàn thời gian và bán thời gian)",
                    optional=True
                ),
                ExtractionField(
                    name="founded_date",
                    type=FieldType.DATE,
                    description="Ngày thành lập công ty theo định dạng dd/mm/yyyy",
                    optional=True
                ),
                ExtractionField(
                    name="headquarters_address",
                    type=FieldType.TEXT,
                    description="Địa chỉ trụ sở chính của công ty bao gồm số nhà, tên đường, quận/huyện, thành phố/tỉnh",
                    optional=False
                )
            ]
        )
        
        dialog = SchemaEditor(sample_template)
        if dialog.exec() == SchemaEditor.Accepted:
            template_data = dialog.get_template()
            QMessageBox.information(
                self,
                "Thành công",
                f"Đã cập nhật schema với {len(template_data['fields'])} trường"
            )
    
    def test_confirmation(self):
        """Test confirmation dialog with proper button styling."""
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc muốn thực hiện hành động này không?\n\nĐây là test để kiểm tra button focus ring.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Kết quả", "Bạn đã chọn Yes")
        else:
            QMessageBox.information(self, "Kết quả", "Bạn đã chọn No")


def main():
    """Main demo function."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')  # Use Fusion style for better cross-platform appearance
    
    # Create and show demo window
    window = DemoWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
