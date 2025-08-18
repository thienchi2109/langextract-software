"""
Schema Editor Dialog for dynamic field configuration.

This module provides a modern, professional dialog for editing extraction templates
with table-based field configuration, validation, and import/export functionality.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QLineEdit, QPlainTextEdit, QCheckBox, QLabel,
    QHeaderView, QMessageBox, QFileDialog, QInputDialog, QFrame, QWidget,
    QSizePolicy, QAbstractItemView
)
from PySide6.QtGui import QFont, QColor, QPalette

from core.models import ExtractionTemplate, ExtractionField, FieldType


class SchemaEditor(QDialog):
    """
    Modern schema editor dialog for dynamic field configuration.
    
    Features:
    - Table-based editor with inline validation
    - Add/edit/delete field functionality
    - Data type selection with locale options
    - Import/export template functionality
    - Professional UX with modern styling
    """
    
    # Column indices
    COL_NAME = 0
    COL_TYPE = 1
    COL_LOCALE = 2
    COL_DESCRIPTION = 3
    COL_OPTIONAL = 4
    
    # Reserved field names
    RESERVED_NAMES = {"data", "summary", "source_file", "parsed_at"}
    
    # Locale options
    LOCALE_OPTIONS = {
        "vi-VN": "Vietnamese (Vietnam)",
        "en-US": "English (United States)", 
        "fr-FR": "French (France)",
        "de-DE": "German (Germany)",
        "Custom...": "Custom locale..."
    }
    
    def __init__(self, template: Optional[ExtractionTemplate] = None, parent=None):
        """
        Initialize schema editor dialog.
        
        Args:
            template: Optional template to edit (None for new template)
            parent: Parent widget
        """
        super().__init__(parent)
        self.template = template
        self.settings = QSettings("LangExtractor", "LangExtractor")
        self.has_unsaved_changes = False

        # Validation timer for delayed validation
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.validate_and_update_ui)
        self.validation_timer.setInterval(300)  # 300ms delay
        
        self.setup_ui()
        self.setup_styling()
        self.load_template_data()
        self.restore_geometry()
        
        # Connect signals for change tracking
        self.setup_change_tracking()
    
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Schema Editor")
        self.setModal(True)
        self.resize(800, 600)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)
        
        self.add_btn = QPushButton("+ Thêm trường")
        self.add_btn.clicked.connect(self.add_field)
        toolbar_layout.addWidget(self.add_btn)
        
        self.delete_btn = QPushButton("– Xoá chọn")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_btn)
        
        toolbar_layout.addStretch()
        
        self.import_btn = QPushButton("Nhập template...")
        self.import_btn.clicked.connect(self.import_template)
        toolbar_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("Xuất template...")
        self.export_btn.clicked.connect(self.export_template)
        toolbar_layout.addWidget(self.export_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Table widget
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)
        
        # Error banner (initially hidden)
        self.error_frame = QFrame()
        self.error_frame.setFrameStyle(QFrame.Box)
        self.error_frame.setStyleSheet("""
            QFrame {
                background-color: #fee;
                border: 1px solid #fcc;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        self.error_frame.setVisible(False)
        
        error_layout = QHBoxLayout(self.error_frame)
        error_layout.setContentsMargins(8, 8, 8, 8)
        
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #c33; font-weight: bold;")
        error_layout.addWidget(self.error_label)
        
        layout.addWidget(self.error_frame)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Huỷ")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setDefault(True)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
    
    def setup_table(self):
        """Setup the table widget."""
        # Set columns
        headers = ["Tên trường", "Kiểu dữ liệu", "Locale", "Mô tả", "Tùy chọn"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # Configure table
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        # Setup header
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        
        # Set column widths (increased for better text visibility)
        self.table.setColumnWidth(self.COL_NAME, 180)
        self.table.setColumnWidth(self.COL_TYPE, 140)
        self.table.setColumnWidth(self.COL_LOCALE, 140)
        self.table.setColumnWidth(self.COL_DESCRIPTION, 300)
        self.table.setColumnWidth(self.COL_OPTIONAL, 100)
        
        # Connect selection change
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Restore column widths
        self.restore_column_widths()
    
    def setup_styling(self):
        """Apply modern styling to the dialog."""
        # Apply inline QSS for modern look
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }

            QPushButton {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                min-height: 20px;
                min-width: 60px;
            }

            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }

            QPushButton:pressed {
                background-color: #dee2e6;
            }

            QPushButton:focus {
                border: 2px solid #0d6efd;
                padding: 7px 15px;
                margin: 0px;
            }

            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
                border-color: #dee2e6;
            }

            QPushButton[class="primary"] {
                background-color: #0d6efd;
                border-color: #0d6efd;
                color: white;
            }

            QPushButton[class="primary"]:hover {
                background-color: #0b5ed7;
                border-color: #0a58ca;
            }

            QPushButton[class="primary"]:focus {
                border: 2px solid #ffffff;
                padding: 7px 15px;
                margin: 0px;
            }
            
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                gridline-color: #e9ecef;
                selection-background-color: #e7f3ff;
            }
            
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            
            QTableWidget::item:selected {
                background-color: #e7f3ff;
            }
            
            QHeaderView::section {
                background-color: #f8f9fa;
                border: none;
                border-bottom: 1px solid #dee2e6;
                padding: 8px;
                font-weight: bold;
            }
            
            QComboBox, QLineEdit, QPlainTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px 10px;
                background-color: white;
                min-height: 20px;
            }
            
            QComboBox:focus, QLineEdit:focus, QPlainTextEdit:focus {
                border-color: #86b7fe;
                outline: none;
            }
            


            /* Fix QMessageBox button focus rings */
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
                margin: 0px;
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
                margin: 0px;
            }
        """)
        
        # Set primary button style
        self.ok_btn.setProperty("class", "primary")
    
    def setup_change_tracking(self):
        """Setup change tracking for unsaved changes detection."""
        # Initial validation
        self.validate_and_update_ui()

    def load_template_data(self):
        """Load template data into the table."""
        if self.template and self.template.fields:
            self.table.setRowCount(len(self.template.fields))

            for row, field in enumerate(self.template.fields):
                self.populate_row(row, field)
        else:
            # Start with one empty row
            self.add_field()

    def populate_row(self, row: int, field: ExtractionField):
        """Populate a table row with field data."""
        # Name column
        name_edit = QLineEdit(field.name)
        name_edit.textChanged.connect(self.on_field_changed)
        self.table.setCellWidget(row, self.COL_NAME, name_edit)

        # Type column
        type_combo = QComboBox()
        type_combo.addItems([t.value for t in FieldType])
        type_combo.setCurrentText(field.type.value)
        type_combo.currentTextChanged.connect(self.on_type_changed)
        self.table.setCellWidget(row, self.COL_TYPE, type_combo)

        # Locale column
        locale_widget = self.create_locale_widget(field)
        self.table.setCellWidget(row, self.COL_LOCALE, locale_widget)

        # Description column
        desc_edit = QPlainTextEdit(field.description)
        desc_edit.setMaximumHeight(100)
        desc_edit.setMinimumHeight(40)
        desc_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        desc_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        desc_edit.textChanged.connect(self.on_field_changed)
        self.table.setCellWidget(row, self.COL_DESCRIPTION, desc_edit)

        # Optional column - create a simple checkbox with minimal styling
        optional_check = QCheckBox()
        optional_check.setChecked(field.optional)
        optional_check.toggled.connect(self.on_field_changed)

        # Remove all custom styling to use system default
        optional_check.setStyleSheet("")

        # Create container widget with center alignment
        optional_widget = QWidget()
        optional_widget.setStyleSheet("background: transparent; border: none;")

        # Use simple layout
        layout = QHBoxLayout(optional_widget)
        layout.addStretch()
        layout.addWidget(optional_check)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table.setCellWidget(row, self.COL_OPTIONAL, optional_widget)

        # Set row height (increased for better text visibility)
        self.table.setRowHeight(row, 50)

    def create_locale_widget(self, field: ExtractionField) -> QWidget:
        """Create locale widget based on field type."""
        if field.type == FieldType.CURRENCY:
            combo = QComboBox()
            for code, name in self.LOCALE_OPTIONS.items():
                combo.addItem(f"{code} - {name}", code)

            # Set current locale
            locale = getattr(field, 'number_locale', 'vi-VN')
            index = combo.findData(locale)
            if index >= 0:
                combo.setCurrentIndex(index)
            else:
                # Custom locale
                combo.addItem(f"{locale} - Custom", locale)
                combo.setCurrentIndex(combo.count() - 1)

            combo.currentTextChanged.connect(self.on_locale_changed)
            return combo
        else:
            # Disabled placeholder for non-currency types
            label = QLabel("—")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #6c757d;")
            return label

    def add_field(self):
        """Add a new field row."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Create default field
        default_field = ExtractionField(
            name="",
            type=FieldType.TEXT,
            description="",
            optional=False
        )

        self.populate_row(row, default_field)
        self.has_unsaved_changes = True
        self.validate_and_update_ui()

        # Focus on name field
        name_edit = self.table.cellWidget(row, self.COL_NAME)
        if name_edit:
            name_edit.setFocus()

    def delete_selected(self):
        """Delete selected rows."""
        # Get selected rows from selection model
        selected_rows = set()
        selection_model = self.table.selectionModel()
        if selection_model:
            for index in selection_model.selectedRows():
                selected_rows.add(index.row())

        if not selected_rows:
            return

        # Confirm deletion
        count = len(selected_rows)
        reply = QMessageBox.question(
            self,
            "Xác nhận xóa",
            f"Bạn có chắc muốn xóa {count} trường đã chọn?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Remove rows in reverse order
            for row in sorted(selected_rows, reverse=True):
                self.table.removeRow(row)

            self.has_unsaved_changes = True
            self.validate_and_update_ui()

    def on_selection_changed(self):
        """Handle table selection changes."""
        selection_model = self.table.selectionModel()
        has_selection = selection_model and len(selection_model.selectedRows()) > 0
        self.delete_btn.setEnabled(has_selection)

    def on_field_changed(self):
        """Handle field value changes."""
        self.has_unsaved_changes = True
        # Use timer to avoid excessive validation calls
        self.validation_timer.start()

    def on_type_changed(self, new_type: str):
        """Handle field type changes."""
        sender = self.sender()
        if not sender:
            return

        # Find the row of the changed combo box
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, self.COL_TYPE) == sender:
                # Update locale widget based on new type
                field_type = FieldType(new_type)
                if field_type == FieldType.CURRENCY:
                    # Create currency locale combo
                    combo = QComboBox()
                    for code, name in self.LOCALE_OPTIONS.items():
                        combo.addItem(f"{code} - {name}", code)
                    combo.setCurrentIndex(0)  # Default to vi-VN
                    combo.currentTextChanged.connect(self.on_locale_changed)
                    self.table.setCellWidget(row, self.COL_LOCALE, combo)
                else:
                    # Create disabled placeholder
                    label = QLabel("—")
                    label.setAlignment(Qt.AlignCenter)
                    label.setStyleSheet("color: #6c757d;")
                    self.table.setCellWidget(row, self.COL_LOCALE, label)
                break

        self.has_unsaved_changes = True
        self.validation_timer.start()

    def on_locale_changed(self, text: str):
        """Handle locale changes."""
        sender = self.sender()
        if not sender or not text:
            return

        # Check if "Custom..." was selected
        if "Custom..." in text:
            custom_locale, ok = QInputDialog.getText(
                self,
                "Custom Locale",
                "Enter BCP-47 locale tag (e.g., ja-JP, zh-CN):",
                text="vi-VN"
            )

            if ok and custom_locale.strip():
                # Add custom locale to combo
                combo = sender
                combo.addItem(f"{custom_locale} - Custom", custom_locale)
                combo.setCurrentIndex(combo.count() - 1)

        self.has_unsaved_changes = True
        self.validation_timer.start()

    def validate_and_update_ui(self):
        """Validate all fields and update UI state."""
        errors = self._collect_errors()

        # Update error banner
        if errors:
            # Show first 3 errors
            error_messages = [f"Row {err['row'] + 1}: {err['message']}" for err in errors[:3]]
            if len(errors) > 3:
                error_messages.append(f"and {len(errors) - 3} more...")

            self.error_label.setText(" • ".join(error_messages))
            self.error_frame.setVisible(True)
            self.error_frame.show()  # Force show
            self.ok_btn.setEnabled(False)
        else:
            self.error_frame.setVisible(False)
            self.error_frame.hide()  # Force hide
            self.ok_btn.setEnabled(self.table.rowCount() > 0)

        # Update cell styling for errors
        self._update_cell_styling(errors)

    def _collect_errors(self) -> List[Dict[str, Any]]:
        """Collect all validation errors."""
        errors = []
        names_seen = set()

        for row in range(self.table.rowCount()):
            # Get field data
            name_edit = self.table.cellWidget(row, self.COL_NAME)
            type_combo = self.table.cellWidget(row, self.COL_TYPE)
            desc_edit = self.table.cellWidget(row, self.COL_DESCRIPTION)

            if not all([name_edit, type_combo, desc_edit]):
                continue

            name = name_edit.text().strip()
            field_type = type_combo.currentText()
            description = desc_edit.toPlainText()

            # Validate name
            if not name:
                errors.append({
                    'row': row,
                    'column': self.COL_NAME,
                    'message': 'Tên trường không được để trống'
                })
            elif not re.match(r'^[a-z][a-z0-9_]{1,63}$', name):
                errors.append({
                    'row': row,
                    'column': self.COL_NAME,
                    'message': 'Tên trường phải theo định dạng snake_case (a-z, 0-9, _)'
                })
            elif name.lower() in self.RESERVED_NAMES:
                errors.append({
                    'row': row,
                    'column': self.COL_NAME,
                    'message': f'Tên trường "{name}" là từ khóa dành riêng'
                })
            elif name.lower() in names_seen:
                errors.append({
                    'row': row,
                    'column': self.COL_NAME,
                    'message': f'Tên trường "{name}" đã tồn tại'
                })
            else:
                names_seen.add(name.lower())

            # Validate description length
            if len(description) > 300:
                errors.append({
                    'row': row,
                    'column': self.COL_DESCRIPTION,
                    'message': f'Mô tả quá dài ({len(description)}/300 ký tự)'
                })

            # Validate locale for currency fields
            if field_type == "currency":
                locale_widget = self.table.cellWidget(row, self.COL_LOCALE)
                if isinstance(locale_widget, QComboBox):
                    locale_data = locale_widget.currentData()
                    if not locale_data or not locale_data.strip():
                        errors.append({
                            'row': row,
                            'column': self.COL_LOCALE,
                            'message': 'Locale không được để trống cho trường currency'
                        })

        return errors

    def _update_cell_styling(self, errors: List[Dict[str, Any]]):
        """Update cell styling to highlight errors."""
        # Reset all cell styles first
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                widget = self.table.cellWidget(row, col)
                if widget:
                    widget.setStyleSheet("")

        # Apply error styling
        error_style = "border: 2px solid #dc3545; border-radius: 4px;"
        for error in errors:
            widget = self.table.cellWidget(error['row'], error['column'])
            if widget:
                widget.setStyleSheet(error_style)
                widget.setToolTip(error['message'])

    def import_template(self):
        """Import template from JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Nhập Template",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate template structure
            if 'fields' not in data:
                QMessageBox.warning(self, "Lỗi", "File không chứa trường 'fields'")
                return

            # Clear current table
            self.table.setRowCount(0)

            # Load fields
            for field_data in data['fields']:
                row = self.table.rowCount()
                self.table.insertRow(row)

                # Create field object
                field = ExtractionField(
                    name=field_data.get('name', ''),
                    type=FieldType(field_data.get('type', 'text')),
                    description=field_data.get('description', ''),
                    optional=field_data.get('optional', False)
                )

                # Add number_locale if present
                if 'number_locale' in field_data:
                    field.number_locale = field_data['number_locale']

                self.populate_row(row, field)

            self.has_unsaved_changes = True
            self.validate_and_update_ui()

            QMessageBox.information(self, "Thành công", f"Đã nhập {len(data['fields'])} trường từ template")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể nhập template: {str(e)}")

    def export_template(self):
        """Export current template to JSON file."""
        if not self.table.rowCount():
            QMessageBox.warning(self, "Cảnh báo", "Không có trường nào để xuất")
            return

        # Validate before export
        errors = self._collect_errors()
        if errors:
            QMessageBox.warning(self, "Lỗi", "Vui lòng sửa các lỗi trước khi xuất template")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Xuất Template",
            "template.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            template_data = self.get_template()

            # Convert to JSON-serializable format
            export_data = {
                'name': template_data.get('name', 'Exported Template'),
                'prompt_description': template_data.get('prompt_description', ''),
                'fields': template_data['fields']
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Thành công", f"Đã xuất template ra {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất template: {str(e)}")

    def get_template(self) -> Dict[str, Any]:
        """
        Get the current template data.

        Returns:
            Dict containing template data with fields in table order
        """
        fields = []

        for row in range(self.table.rowCount()):
            # Get widgets
            name_edit = self.table.cellWidget(row, self.COL_NAME)
            type_combo = self.table.cellWidget(row, self.COL_TYPE)
            locale_widget = self.table.cellWidget(row, self.COL_LOCALE)
            desc_edit = self.table.cellWidget(row, self.COL_DESCRIPTION)
            optional_widget = self.table.cellWidget(row, self.COL_OPTIONAL)

            if not all([name_edit, type_combo, desc_edit, optional_widget]):
                continue

            # Extract values
            name = name_edit.text().strip()
            field_type = type_combo.currentText()
            description = desc_edit.toPlainText()

            # Get optional value from checkbox
            optional_checkbox = optional_widget.findChild(QCheckBox)
            optional = optional_checkbox.isChecked() if optional_checkbox else False

            # Build field data
            field_data = {
                'name': name,
                'type': field_type,
                'description': description,
                'optional': optional
            }

            # Add number_locale only for currency fields
            if field_type == 'currency' and isinstance(locale_widget, QComboBox):
                locale_data = locale_widget.currentData()
                if locale_data:
                    field_data['number_locale'] = locale_data

            fields.append(field_data)

        return {
            'name': getattr(self.template, 'name', 'New Template') if self.template else 'New Template',
            'prompt_description': getattr(self.template, 'prompt_description', '') if self.template else '',
            'fields': fields
        }

    def restore_geometry(self):
        """Restore dialog geometry from settings."""
        geometry = self.settings.value("schema_editor/geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def save_geometry(self):
        """Save dialog geometry to settings."""
        self.settings.setValue("schema_editor/geometry", self.saveGeometry())

    def restore_column_widths(self):
        """Restore table column widths from settings."""
        for col in range(self.table.columnCount()):
            width = self.settings.value(f"schema_editor/column_{col}_width")
            if width:
                self.table.setColumnWidth(col, int(width))

    def save_column_widths(self):
        """Save table column widths to settings."""
        for col in range(self.table.columnCount()):
            width = self.table.columnWidth(col)
            self.settings.setValue(f"schema_editor/column_{col}_width", width)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key_Insert:
            self.add_field()
        elif event.key() == Qt.Key_Delete:
            if self.table.hasFocus():
                self.delete_selected()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
            if self.ok_btn.isEnabled():
                self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Thay đổi chưa lưu",
                "Bạn có thay đổi chưa được lưu. Bạn có muốn thoát mà không lưu?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                event.ignore()
                return

        # Save geometry and column widths
        self.save_geometry()
        self.save_column_widths()

        event.accept()

    def accept(self):
        """Handle OK button click."""
        # Final validation
        errors = self._collect_errors()
        if errors:
            QMessageBox.warning(self, "Lỗi", "Vui lòng sửa các lỗi trước khi lưu")
            return

        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Lỗi", "Phải có ít nhất một trường")
            return

        # Save geometry and column widths
        self.save_geometry()
        self.save_column_widths()

        super().accept()

    def reject(self):
        """Handle Cancel button click."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Thay đổi chưa lưu",
                "Bạn có thay đổi chưa được lưu. Bạn có muốn thoát mà không lưu?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                return

        # Save geometry and column widths
        self.save_geometry()
        self.save_column_widths()

        super().reject()
