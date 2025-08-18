"""
Unit tests for Schema Editor dialog.

Tests cover:
- Add/edit/delete field functionality
- Validation (unique names, format, required fields)
- Currency locale toggle behavior
- Optional flags and description limits
- Import/export template round-trip
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QPlainTextEdit, QCheckBox
from PySide6.QtTest import QTest

from gui.schema_editor import SchemaEditor
from core.models import ExtractionTemplate, ExtractionField, FieldType


@pytest.fixture
def app():
    """Create QApplication instance for tests."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def sample_template():
    """Create a sample template for testing."""
    return ExtractionTemplate(
        name="Test Template",
        prompt_description="Test template for unit tests",
        fields=[
            ExtractionField(
                name="company_name",
                type=FieldType.TEXT,
                description="Company name",
                optional=False
            ),
            ExtractionField(
                name="revenue",
                type=FieldType.CURRENCY,
                description="Annual revenue",
                optional=False,
                number_locale="vi-VN"
            )
        ]
    )


class TestSchemaEditor:
    """Test cases for SchemaEditor dialog."""
    
    def test_add_edit_delete(self, app, qtbot):
        """Test add/edit/delete field functionality."""
        # Create dialog
        dialog = SchemaEditor()
        qtbot.addWidget(dialog)
        
        # Initially should have one empty row
        assert dialog.table.rowCount() == 1
        assert dialog.ok_btn.isEnabled() == False  # Empty name should disable OK
        
        # Add a field
        qtbot.mouseClick(dialog.add_btn, Qt.LeftButton)
        assert dialog.table.rowCount() == 2
        
        # Edit first row - add valid name
        name_edit = dialog.table.cellWidget(0, dialog.COL_NAME)
        assert isinstance(name_edit, QLineEdit)
        
        name_edit.setText("test_field")
        dialog.validate_and_update_ui()  # Force validation

        # Should still be invalid due to second empty row
        assert dialog.ok_btn.isEnabled() == False

        # Edit second row
        name_edit2 = dialog.table.cellWidget(1, dialog.COL_NAME)
        name_edit2.setText("another_field")
        dialog.validate_and_update_ui()  # Force validation

        # Now should be valid
        assert dialog.ok_btn.isEnabled() == True
        
        # Select and delete second row
        dialog.table.selectRow(1)
        qtbot.mouseClick(dialog.delete_btn, Qt.LeftButton)
        
        # Mock the confirmation dialog to accept
        with patch('PySide6.QtWidgets.QMessageBox.question', return_value=16384):  # QMessageBox.Yes
            qtbot.mouseClick(dialog.delete_btn, Qt.LeftButton)
        
        assert dialog.table.rowCount() == 1
        assert dialog.ok_btn.isEnabled() == True
    
    def test_validation_unique_and_format(self, app, qtbot):
        """Test validation for unique names and format requirements."""
        dialog = SchemaEditor()
        qtbot.addWidget(dialog)
        
        # Add two rows
        qtbot.mouseClick(dialog.add_btn, Qt.LeftButton)
        assert dialog.table.rowCount() == 2
        
        # Set duplicate names
        name_edit1 = dialog.table.cellWidget(0, dialog.COL_NAME)
        name_edit2 = dialog.table.cellWidget(1, dialog.COL_NAME)
        
        name_edit1.setText("duplicate_name")
        name_edit2.setText("duplicate_name")
        dialog.validate_and_update_ui()  # Force validation

        # Should be invalid due to duplicate names
        assert dialog.ok_btn.isEnabled() == False
        # Check that error message is set (frame visibility might be affected by layout)
        assert "đã tồn tại" in dialog.error_label.text()

        # Test invalid format (uppercase)
        name_edit2.setText("InvalidName")
        dialog.validate_and_update_ui()  # Force validation
        assert dialog.ok_btn.isEnabled() == False
        assert "snake_case" in dialog.error_label.text()

        # Test reserved name
        name_edit2.setText("data")
        dialog.validate_and_update_ui()  # Force validation
        assert dialog.ok_btn.isEnabled() == False
        assert "từ khóa dành riêng" in dialog.error_label.text()

        # Fix to valid names
        name_edit1.setText("valid_field_one")
        name_edit2.setText("valid_field_two")
        dialog.validate_and_update_ui()  # Force validation

        # Should be valid now
        assert dialog.ok_btn.isEnabled() == True
    
    def test_currency_locale_toggle(self, app, qtbot):
        """Test currency locale toggle behavior."""
        dialog = SchemaEditor()
        qtbot.addWidget(dialog)
        
        # Get widgets for first row
        name_edit = dialog.table.cellWidget(0, dialog.COL_NAME)
        type_combo = dialog.table.cellWidget(0, dialog.COL_TYPE)
        locale_widget = dialog.table.cellWidget(0, dialog.COL_LOCALE)
        
        # Initially should be text type with disabled locale
        assert type_combo.currentText() == "text"
        assert not isinstance(locale_widget, QComboBox)
        
        # Set valid name first
        name_edit.setText("test_currency")
        
        # Change to currency type
        type_combo.setCurrentText("currency")
        
        # Locale widget should now be a combo box
        locale_widget = dialog.table.cellWidget(0, dialog.COL_LOCALE)
        assert isinstance(locale_widget, QComboBox)
        assert locale_widget.currentData() == "vi-VN"  # Default
        
        # Change back to number type
        type_combo.setCurrentText("number")
        
        # Locale widget should be disabled again
        locale_widget = dialog.table.cellWidget(0, dialog.COL_LOCALE)
        assert not isinstance(locale_widget, QComboBox)
    
    def test_optional_and_description(self, app, qtbot):
        """Test optional flag and description length validation."""
        dialog = SchemaEditor()
        qtbot.addWidget(dialog)
        
        # Get widgets
        name_edit = dialog.table.cellWidget(0, dialog.COL_NAME)
        desc_edit = dialog.table.cellWidget(0, dialog.COL_DESCRIPTION)
        optional_widget = dialog.table.cellWidget(0, dialog.COL_OPTIONAL)
        optional_checkbox = optional_widget.findChild(QCheckBox)
        
        # Set valid name
        name_edit.setText("test_field")
        
        # Test optional checkbox
        assert optional_checkbox.isChecked() == False
        optional_checkbox.setChecked(True)
        assert optional_checkbox.isChecked() == True
        
        # Test description within limit
        short_desc = "This is a short description"
        desc_edit.setPlainText(short_desc)
        dialog.validate_and_update_ui()  # Force validation
        assert dialog.ok_btn.isEnabled() == True

        # Test description over limit (>300 chars)
        long_desc = "x" * 301
        desc_edit.setPlainText(long_desc)
        dialog.validate_and_update_ui()  # Force validation
        assert dialog.ok_btn.isEnabled() == False
        assert "quá dài" in dialog.error_label.text()

        # Fix description
        desc_edit.setPlainText(short_desc)
        dialog.validate_and_update_ui()  # Force validation
        assert dialog.ok_btn.isEnabled() == True
    
    def test_import_export_roundtrip(self, app, qtbot):
        """Test import/export template round-trip."""
        dialog = SchemaEditor()
        qtbot.addWidget(dialog)
        
        # Create test template data
        template_data = {
            "name": "Test Template",
            "prompt_description": "Test description",
            "fields": [
                {
                    "name": "company_name",
                    "type": "text",
                    "description": "Company name field",
                    "optional": False
                },
                {
                    "name": "revenue",
                    "type": "currency",
                    "description": "Revenue field",
                    "optional": True,
                    "number_locale": "en-US"
                }
            ]
        }
        
        # Create temporary file for import
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(template_data, f)
            temp_file = f.name
        
        try:
            # Mock file dialog to return our temp file
            with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', 
                      return_value=(temp_file, "")):
                dialog.import_template()
            
            # Verify import
            assert dialog.table.rowCount() == 2
            
            # Check first field
            name_edit1 = dialog.table.cellWidget(0, dialog.COL_NAME)
            type_combo1 = dialog.table.cellWidget(0, dialog.COL_TYPE)
            desc_edit1 = dialog.table.cellWidget(0, dialog.COL_DESCRIPTION)
            optional_widget1 = dialog.table.cellWidget(0, dialog.COL_OPTIONAL)
            optional_checkbox1 = optional_widget1.findChild(QCheckBox)
            
            assert name_edit1.text() == "company_name"
            assert type_combo1.currentText() == "text"
            assert desc_edit1.toPlainText() == "Company name field"
            assert optional_checkbox1.isChecked() == False
            
            # Check second field (currency)
            name_edit2 = dialog.table.cellWidget(1, dialog.COL_NAME)
            type_combo2 = dialog.table.cellWidget(1, dialog.COL_TYPE)
            locale_combo2 = dialog.table.cellWidget(1, dialog.COL_LOCALE)
            desc_edit2 = dialog.table.cellWidget(1, dialog.COL_DESCRIPTION)
            optional_widget2 = dialog.table.cellWidget(1, dialog.COL_OPTIONAL)
            optional_checkbox2 = optional_widget2.findChild(QCheckBox)
            
            assert name_edit2.text() == "revenue"
            assert type_combo2.currentText() == "currency"
            assert isinstance(locale_combo2, QComboBox)
            assert locale_combo2.currentData() == "en-US"
            assert desc_edit2.toPlainText() == "Revenue field"
            assert optional_checkbox2.isChecked() == True
            
            # Edit a field
            name_edit1.setText("modified_company_name")
            
            # Export template
            export_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            export_file.close()
            
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',
                      return_value=(export_file.name, "")):
                dialog.export_template()
            
            # Verify export
            with open(export_file.name, 'r') as f:
                exported_data = json.load(f)
            
            assert len(exported_data['fields']) == 2
            assert exported_data['fields'][0]['name'] == "modified_company_name"
            assert exported_data['fields'][1]['name'] == "revenue"
            assert exported_data['fields'][1]['number_locale'] == "en-US"
            
            # Clean up
            Path(export_file.name).unlink()
            
        finally:
            # Clean up temp file
            Path(temp_file).unlink()
    
    def test_keyboard_shortcuts(self, app, qtbot):
        """Test keyboard shortcuts."""
        dialog = SchemaEditor()
        qtbot.addWidget(dialog)
        
        # Test Insert key (add field)
        initial_count = dialog.table.rowCount()
        qtbot.keyPress(dialog, Qt.Key_Insert)
        assert dialog.table.rowCount() == initial_count + 1
        
        # Test Escape key (cancel)
        with patch.object(dialog, 'reject') as mock_reject:
            qtbot.keyPress(dialog, Qt.Key_Escape)
            mock_reject.assert_called_once()
    
    def test_get_template_format(self, app, qtbot):
        """Test get_template returns correct format."""
        dialog = SchemaEditor()
        qtbot.addWidget(dialog)
        
        # Set up a currency field
        name_edit = dialog.table.cellWidget(0, dialog.COL_NAME)
        type_combo = dialog.table.cellWidget(0, dialog.COL_TYPE)
        desc_edit = dialog.table.cellWidget(0, dialog.COL_DESCRIPTION)
        
        name_edit.setText("test_currency")
        type_combo.setCurrentText("currency")
        desc_edit.setPlainText("Test currency field")
        
        # Get template data
        template_data = dialog.get_template()
        
        # Verify structure
        assert 'fields' in template_data
        assert len(template_data['fields']) == 1
        
        field = template_data['fields'][0]
        assert field['name'] == "test_currency"
        assert field['type'] == "currency"
        assert field['description'] == "Test currency field"
        assert field['optional'] == False
        assert 'number_locale' in field  # Should include for currency
        assert field['number_locale'] == "vi-VN"  # Default
        
        # Test non-currency field doesn't include number_locale
        type_combo.setCurrentText("text")
        template_data = dialog.get_template()
        field = template_data['fields'][0]
        assert 'number_locale' not in field
