#!/usr/bin/env python3
"""
Demo script showing configuration and template management functionality.
"""

from core.models import AppConfig, ExtractionTemplate, ExtractionField, FieldType
from core.utils import load_config, save_config
from core.template_manager import TemplateManager


def demo_configuration():
    """Demonstrate configuration management."""
    print("=== Configuration Management Demo ===")
    
    # Load default configuration
    print("1. Loading default configuration...")
    config = load_config()
    print(f"   OCR enabled: {config.ocr_enabled}")
    print(f"   OCR languages: {config.ocr_languages}")
    print(f"   Max workers: {config.max_workers}")
    print(f"   Log level: {config.log_level}")
    
    # Modify configuration
    print("\n2. Modifying configuration...")
    config.ocr_enabled = False
    config.max_workers = 8
    config.log_level = 'DEBUG'
    config.offline_mode = True
    
    # Save configuration
    print("3. Saving configuration...")
    save_config(config)
    print("   Configuration saved successfully!")
    
    # Load configuration again to verify
    print("\n4. Loading configuration to verify changes...")
    loaded_config = load_config()
    print(f"   OCR enabled: {loaded_config.ocr_enabled}")
    print(f"   Max workers: {loaded_config.max_workers}")
    print(f"   Log level: {loaded_config.log_level}")
    print(f"   Offline mode: {loaded_config.offline_mode}")


def demo_template_management():
    """Demonstrate template management."""
    print("\n=== Template Management Demo ===")
    
    # Create template manager
    template_manager = TemplateManager()
    
    # Create sample template
    print("1. Creating sample template...")
    fields = [
        ExtractionField(
            name="company_name",
            type=FieldType.TEXT,
            description="Name of the company from the financial report"
        ),
        ExtractionField(
            name="total_revenue",
            type=FieldType.CURRENCY,
            description="Total annual revenue in VND",
            optional=False
        ),
        ExtractionField(
            name="profit_margin",
            type=FieldType.NUMBER,
            description="Profit margin as percentage",
            optional=True
        ),
        ExtractionField(
            name="report_date",
            type=FieldType.DATE,
            description="Date of the financial report"
        )
    ]
    
    template = ExtractionTemplate(
        name="Financial Report Template",
        prompt_description="Extract key financial information from Vietnamese company reports",
        fields=fields,
        examples=[
            {
                "company_name": "Công ty ABC",
                "total_revenue": "50000000000",
                "profit_margin": "15.5",
                "report_date": "2024-12-31"
            }
        ],
        provider={"name": "gemini", "model": "gemini-pro"},
        run_options={"temperature": 0.1, "max_tokens": 1000}
    )
    
    # Save template
    print("2. Saving template...")
    success = template_manager.save_template(template)
    print(f"   Template saved: {success}")
    
    # List templates
    print("\n3. Listing available templates...")
    templates = template_manager.list_templates()
    print(f"   Available templates: {templates}")
    
    # Load template
    print("\n4. Loading template...")
    loaded_template = template_manager.load_template("Financial Report Template")
    if loaded_template:
        print(f"   Template name: {loaded_template.name}")
        print(f"   Description: {loaded_template.prompt_description}")
        print(f"   Number of fields: {len(loaded_template.fields)}")
        print("   Fields:")
        for field in loaded_template.fields:
            print(f"     - {field.name} ({field.type.value}): {field.description}")
    
    # Get template info
    print("\n5. Getting template info...")
    info = template_manager.get_template_info("Financial Report Template")
    if info:
        print(f"   Name: {info['name']}")
        print(f"   Field count: {info['field_count']}")
        print(f"   File size: {info['file_size']} bytes")
    
    # Duplicate template
    print("\n6. Duplicating template...")
    success = template_manager.duplicate_template(
        "Financial Report Template", 
        "Financial Report Template - Copy"
    )
    print(f"   Template duplicated: {success}")
    
    # List templates again
    print("\n7. Listing templates after duplication...")
    templates = template_manager.list_templates()
    print(f"   Available templates: {templates}")
    
    # Clean up - delete templates
    print("\n8. Cleaning up templates...")
    for template_name in templates:
        success = template_manager.delete_template(template_name)
        print(f"   Deleted '{template_name}': {success}")


def demo_error_handling():
    """Demonstrate error handling."""
    print("\n=== Error Handling Demo ===")
    
    template_manager = TemplateManager()
    
    # Try to load non-existent template
    print("1. Loading non-existent template...")
    result = template_manager.load_template("NonExistent Template")
    print(f"   Result: {result}")
    
    # Try to save invalid template
    print("\n2. Saving invalid template (empty name)...")
    try:
        invalid_template = ExtractionTemplate(
            name="",  # Empty name
            prompt_description="Test",
            fields=[]  # No fields
        )
        template_manager.save_template(invalid_template)
    except Exception as e:
        print(f"   Error caught: {type(e).__name__}: {e}")
    
    # Try to delete non-existent template
    print("\n3. Deleting non-existent template...")
    result = template_manager.delete_template("NonExistent Template")
    print(f"   Result: {result}")


if __name__ == "__main__":
    try:
        demo_configuration()
        demo_template_management()
        demo_error_handling()
        print("\n=== Demo completed successfully! ===")
    except Exception as e:
        print(f"\nDemo failed with error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()