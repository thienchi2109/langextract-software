"""
Unit tests for template management system.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.template_manager import TemplateManager
from core.models import ExtractionTemplate, ExtractionField, FieldType
from core.exceptions import ConfigurationError, ValidationError


class TestTemplateManager:
    """Test cases for TemplateManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def template_manager(self, temp_dir):
        """Create TemplateManager with temporary directory."""
        with patch('core.template_manager.get_templates_dir', return_value=temp_dir):
            return TemplateManager()
    
    @pytest.fixture
    def sample_template(self):
        """Create sample extraction template."""
        fields = [
            ExtractionField(
                name="company_name",
                type=FieldType.TEXT,
                description="Name of the company"
            ),
            ExtractionField(
                name="revenue",
                type=FieldType.CURRENCY,
                description="Annual revenue",
                optional=True
            )
        ]
        
        return ExtractionTemplate(
            name="Financial Report",
            prompt_description="Extract financial information from reports",
            fields=fields,
            examples=[{"company_name": "ABC Corp", "revenue": "1000000"}],
            provider={"name": "gemini", "model": "gemini-2.5-pro"},
            run_options={"temperature": 0.1}
        )
    
    def test_save_template_success(self, template_manager, sample_template):
        """Test successful template saving."""
        result = template_manager.save_template(sample_template)
        
        assert result is True
        assert template_manager.template_exists("Financial Report")
    
    def test_save_template_empty_name(self, template_manager, sample_template):
        """Test saving template with empty name."""
        sample_template.name = ""
        
        with pytest.raises(ValidationError) as exc_info:
            template_manager.save_template(sample_template)
        
        assert "Template name cannot be empty" in str(exc_info.value)
    
    def test_save_template_no_fields(self, template_manager, sample_template):
        """Test saving template with no fields."""
        sample_template.fields = []
        
        with pytest.raises(ValidationError) as exc_info:
            template_manager.save_template(sample_template)
        
        assert "Template must have at least one field" in str(exc_info.value)
    
    def test_save_template_duplicate_field_names(self, template_manager, sample_template):
        """Test saving template with duplicate field names."""
        sample_template.fields.append(
            ExtractionField(
                name="company_name",  # Duplicate name
                type=FieldType.TEXT,
                description="Another company name field"
            )
        )
        
        with pytest.raises(ValidationError) as exc_info:
            template_manager.save_template(sample_template)
        
        assert "field names must be unique" in str(exc_info.value)
    
    def test_load_template_success(self, template_manager, sample_template):
        """Test successful template loading."""
        # Save template first
        template_manager.save_template(sample_template)
        
        # Load template
        loaded_template = template_manager.load_template("Financial Report")
        
        assert loaded_template is not None
        assert loaded_template.name == sample_template.name
        assert loaded_template.prompt_description == sample_template.prompt_description
        assert len(loaded_template.fields) == len(sample_template.fields)
        assert loaded_template.fields[0].name == "company_name"
        assert loaded_template.fields[1].name == "revenue"
    
    def test_load_template_not_found(self, template_manager):
        """Test loading non-existent template."""
        result = template_manager.load_template("NonExistent")
        assert result is None
    
    def test_load_template_empty_name(self, template_manager):
        """Test loading template with empty name."""
        result = template_manager.load_template("")
        assert result is None
    
    def test_load_template_corrupted_json(self, template_manager, temp_dir):
        """Test loading template with corrupted JSON."""
        # Create corrupted JSON file
        corrupted_file = temp_dir / "corrupted.json"
        corrupted_file.write_text("{ invalid json }")
        
        with pytest.raises(ConfigurationError) as exc_info:
            template_manager.load_template("corrupted")
        
        assert "corrupted" in str(exc_info.value)
        assert "Template file may be corrupted" in str(exc_info.value)
    
    def test_load_template_invalid_structure(self, template_manager, temp_dir):
        """Test loading template with invalid structure."""
        # Create JSON with invalid structure
        invalid_data = {"name": "test", "fields": "not_a_list"}
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text(json.dumps(invalid_data))
        
        with pytest.raises(ConfigurationError):
            template_manager.load_template("invalid")
    
    def test_list_templates_empty(self, template_manager):
        """Test listing templates when none exist."""
        templates = template_manager.list_templates()
        assert templates == []
    
    def test_list_templates_with_templates(self, template_manager, sample_template):
        """Test listing templates when some exist."""
        # Save multiple templates
        template_manager.save_template(sample_template)
        
        sample_template.name = "Another Template"
        template_manager.save_template(sample_template)
        
        templates = template_manager.list_templates()
        assert len(templates) == 2
        assert "Another Template" in templates
        assert "Financial Report" in templates
        assert templates == sorted(templates)  # Should be sorted
    
    def test_delete_template_success(self, template_manager, sample_template):
        """Test successful template deletion."""
        # Save template first
        template_manager.save_template(sample_template)
        assert template_manager.template_exists("Financial Report")
        
        # Delete template
        result = template_manager.delete_template("Financial Report")
        
        assert result is True
        assert not template_manager.template_exists("Financial Report")
    
    def test_delete_template_not_found(self, template_manager):
        """Test deleting non-existent template."""
        result = template_manager.delete_template("NonExistent")
        assert result is False
    
    def test_delete_template_empty_name(self, template_manager):
        """Test deleting template with empty name."""
        result = template_manager.delete_template("")
        assert result is False
    
    def test_template_exists(self, template_manager, sample_template):
        """Test template existence check."""
        assert not template_manager.template_exists("Financial Report")
        
        template_manager.save_template(sample_template)
        assert template_manager.template_exists("Financial Report")
    
    def test_get_template_info_success(self, template_manager, sample_template):
        """Test getting template info."""
        template_manager.save_template(sample_template)
        
        info = template_manager.get_template_info("Financial Report")
        
        assert info is not None
        assert info['name'] == "Financial Report"
        assert info['description'] == "Extract financial information from reports"
        assert info['field_count'] == 2
        assert 'file_size' in info
        assert 'modified_time' in info
    
    def test_get_template_info_not_found(self, template_manager):
        """Test getting info for non-existent template."""
        info = template_manager.get_template_info("NonExistent")
        assert info is None
    
    def test_duplicate_template_success(self, template_manager, sample_template):
        """Test successful template duplication."""
        # Save original template
        template_manager.save_template(sample_template)
        
        # Duplicate template
        result = template_manager.duplicate_template("Financial Report", "Financial Report Copy")
        
        assert result is True
        assert template_manager.template_exists("Financial Report Copy")
        
        # Verify duplicated template
        duplicated = template_manager.load_template("Financial Report Copy")
        assert duplicated.name == "Financial Report Copy"
        assert duplicated.prompt_description == sample_template.prompt_description
        assert len(duplicated.fields) == len(sample_template.fields)
    
    def test_duplicate_template_source_not_found(self, template_manager):
        """Test duplicating non-existent template."""
        with pytest.raises(ValidationError) as exc_info:
            template_manager.duplicate_template("NonExistent", "New Template")
        
        assert "Source template 'NonExistent' not found" in str(exc_info.value)
    
    def test_duplicate_template_target_exists(self, template_manager, sample_template):
        """Test duplicating to existing template name."""
        # Save two templates
        template_manager.save_template(sample_template)
        
        sample_template.name = "Another Template"
        template_manager.save_template(sample_template)
        
        # Try to duplicate with existing name
        with pytest.raises(ValidationError) as exc_info:
            template_manager.duplicate_template("Financial Report", "Another Template")
        
        assert "Template 'Another Template' already exists" in str(exc_info.value)
    
    def test_duplicate_template_empty_names(self, template_manager):
        """Test duplicating with empty names."""
        with pytest.raises(ValidationError) as exc_info:
            template_manager.duplicate_template("", "New Template")
        
        assert "Source and new template names cannot be empty" in str(exc_info.value)
    
    def test_filename_sanitization(self, template_manager, sample_template):
        """Test that template names are properly sanitized for filenames."""
        # Use template name with invalid filename characters
        sample_template.name = "Report<>:\"/\\|?*Template"
        
        result = template_manager.save_template(sample_template)
        assert result is True
        
        # Should be able to load with original name
        loaded = template_manager.load_template("Report<>:\"/\\|?*Template")
        assert loaded is not None
        assert loaded.name == "Report<>:\"/\\|?*Template"
    
    def test_validation_field_empty_name(self, template_manager, sample_template):
        """Test validation of field with empty name."""
        sample_template.fields[0].name = ""
        
        with pytest.raises(ValidationError) as exc_info:
            template_manager.save_template(sample_template)
        
        assert "Field 1 name must be a non-empty string" in str(exc_info.value)
    
    def test_validation_field_invalid_description(self, template_manager, sample_template):
        """Test validation of field with invalid description."""
        sample_template.fields[0].description = None
        
        with pytest.raises(ValidationError) as exc_info:
            template_manager.save_template(sample_template)
        
        assert "Field 1 description must be a string" in str(exc_info.value)
    
    @patch('core.template_manager.safe_json_save')
    def test_save_template_io_error(self, mock_save, template_manager, sample_template):
        """Test handling of IO errors during save."""
        mock_save.side_effect = OSError("Permission denied")
        
        with pytest.raises(ConfigurationError) as exc_info:
            template_manager.save_template(sample_template)
        
        assert "Failed to save template" in str(exc_info.value)
        assert "Financial Report" in str(exc_info.value)
    
    @patch('core.template_manager.safe_json_load')
    def test_load_template_io_error(self, mock_load, template_manager, temp_dir):
        """Test handling of IO errors during load."""
        # Create template file
        template_file = temp_dir / "test.json"
        template_file.write_text("{}")
        
        mock_load.side_effect = OSError("Permission denied")
        
        with pytest.raises(ConfigurationError) as exc_info:
            template_manager.load_template("test")
        
        assert "Failed to load template" in str(exc_info.value)
        assert "test" in str(exc_info.value)