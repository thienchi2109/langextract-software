"""
Template management system for saving/loading extraction templates.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from core.models import ExtractionTemplate, TemplateManagerInterface
from core.exceptions import ConfigurationError, ValidationError
from core.utils import get_templates_dir, sanitize_filename, safe_json_load, safe_json_save


class TemplateManager(TemplateManagerInterface):
    """
    Manages extraction templates with JSON persistence.
    
    Handles saving, loading, listing, and deleting extraction templates
    with validation and error handling for corrupted templates.
    """
    
    def __init__(self):
        """Initialize template manager."""
        self._templates_dir = get_templates_dir()
    
    def save_template(self, template: ExtractionTemplate) -> bool:
        """
        Save extraction template to JSON file.
        
        Args:
            template: ExtractionTemplate to save
            
        Returns:
            True if saved successfully
            
        Raises:
            ValidationError: If template is invalid
            ConfigurationError: If save operation fails
        """
        if not template or not template.name:
            raise ValidationError(
                message="Template name cannot be empty",
                field_name="template.name",
                field_value=template.name if template else None
            )
        
        if not template.fields:
            raise ValidationError(
                message="Template must have at least one field",
                field_name="template.fields",
                field_value=template.fields
            )
        
        # Validate template structure
        self._validate_template(template)
        
        # Sanitize filename
        safe_name = sanitize_filename(template.name)
        template_file = self._templates_dir / f"{safe_name}.json"
        
        try:
            template_data = template.to_dict()
            safe_json_save(template_data, template_file)
            return True
        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to save template '{template.name}': {str(e)}",
                config_key=template.name,
                original_error=e
            )
    
    def load_template(self, name: str) -> Optional[ExtractionTemplate]:
        """
        Load extraction template by name.
        
        Args:
            name: Template name
            
        Returns:
            ExtractionTemplate if found, None otherwise
            
        Raises:
            ConfigurationError: If template file is corrupted
        """
        if not name:
            return None
        
        safe_name = sanitize_filename(name)
        template_file = self._templates_dir / f"{safe_name}.json"
        
        if not template_file.exists():
            return None
        
        try:
            template_data = safe_json_load(template_file)
            template = ExtractionTemplate.from_dict(template_data)
            
            # Validate loaded template
            self._validate_template(template)
            
            return template
        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to load template '{name}': Template file may be corrupted",
                config_key=name,
                original_error=e
            )
    
    def list_templates(self) -> List[str]:
        """
        List available template names.
        
        Returns:
            List of template names
        """
        template_names = []
        
        try:
            for template_file in self._templates_dir.glob("*.json"):
                # Extract name from filename (remove .json extension)
                name = template_file.stem
                template_names.append(name)
        except OSError:
            # Return empty list if directory cannot be read
            pass
        
        return sorted(template_names)
    
    def delete_template(self, name: str) -> bool:
        """
        Delete template by name.
        
        Args:
            name: Template name to delete
            
        Returns:
            True if deleted successfully, False if not found
            
        Raises:
            ConfigurationError: If delete operation fails
        """
        if not name:
            return False
        
        safe_name = sanitize_filename(name)
        template_file = self._templates_dir / f"{safe_name}.json"
        
        if not template_file.exists():
            return False
        
        try:
            template_file.unlink()
            return True
        except OSError as e:
            raise ConfigurationError(
                message=f"Failed to delete template '{name}': {str(e)}",
                config_key=name,
                original_error=e
            )
    
    def template_exists(self, name: str) -> bool:
        """
        Check if template exists.
        
        Args:
            name: Template name
            
        Returns:
            True if template exists
        """
        if not name:
            return False
        
        safe_name = sanitize_filename(name)
        template_file = self._templates_dir / f"{safe_name}.json"
        return template_file.exists()
    
    def get_template_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get template metadata without loading full template.
        
        Args:
            name: Template name
            
        Returns:
            Dictionary with template info or None if not found
        """
        if not name:
            return None
        
        safe_name = sanitize_filename(name)
        template_file = self._templates_dir / f"{safe_name}.json"
        
        if not template_file.exists():
            return None
        
        try:
            template_data = safe_json_load(template_file)
            return {
                'name': template_data.get('name', name),
                'description': template_data.get('prompt_description', ''),
                'field_count': len(template_data.get('fields', [])),
                'file_size': template_file.stat().st_size,
                'modified_time': template_file.stat().st_mtime
            }
        except Exception:
            return None
    
    def duplicate_template(self, source_name: str, new_name: str) -> bool:
        """
        Duplicate an existing template with a new name.
        
        Args:
            source_name: Name of template to duplicate
            new_name: Name for the new template
            
        Returns:
            True if duplicated successfully
            
        Raises:
            ValidationError: If source template doesn't exist or new name is invalid
            ConfigurationError: If duplication fails
        """
        if not source_name or not new_name:
            raise ValidationError(
                message="Source and new template names cannot be empty",
                field_name="template_names",
                field_value={"source": source_name, "new": new_name}
            )
        
        # Load source template
        source_template = self.load_template(source_name)
        if not source_template:
            raise ValidationError(
                message=f"Source template '{source_name}' not found",
                field_name="source_name",
                field_value=source_name
            )
        
        # Check if new name already exists
        if self.template_exists(new_name):
            raise ValidationError(
                message=f"Template '{new_name}' already exists",
                field_name="new_name",
                field_value=new_name
            )
        
        # Create new template with updated name
        new_template = ExtractionTemplate(
            name=new_name,
            prompt_description=source_template.prompt_description,
            fields=source_template.fields.copy(),
            examples=source_template.examples.copy(),
            provider=source_template.provider.copy(),
            run_options=source_template.run_options.copy()
        )
        
        return self.save_template(new_template)
    
    def _validate_template(self, template: ExtractionTemplate) -> None:
        """
        Validate template structure and content.
        
        Args:
            template: Template to validate
            
        Raises:
            ValidationError: If template is invalid
        """
        if not isinstance(template.name, str) or not template.name.strip():
            raise ValidationError(
                message="Template name must be a non-empty string",
                field_name="template.name",
                field_value=template.name
            )
        
        if not isinstance(template.prompt_description, str):
            raise ValidationError(
                message="Template prompt description must be a string",
                field_name="template.prompt_description",
                field_value=template.prompt_description
            )
        
        if not isinstance(template.fields, list) or not template.fields:
            raise ValidationError(
                message="Template must have at least one field",
                field_name="template.fields",
                field_value=template.fields
            )
        
        # Validate field names are unique
        field_names = [field.name for field in template.fields]
        if len(field_names) != len(set(field_names)):
            raise ValidationError(
                message="Template field names must be unique",
                field_name="template.fields",
                field_value=field_names
            )
        
        # Validate each field
        for i, field in enumerate(template.fields):
            if not isinstance(field.name, str) or not field.name.strip():
                raise ValidationError(
                    message=f"Field {i+1} name must be a non-empty string",
                    field_name=f"template.fields[{i}].name",
                    field_value=field.name
                )
            
            if not isinstance(field.description, str):
                raise ValidationError(
                    message=f"Field {i+1} description must be a string",
                    field_name=f"template.fields[{i}].description",
                    field_value=field.description
                )