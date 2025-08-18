"""
Demo script for Task 8: LangExtract integration for data extraction.

This script demonstrates the new Extractor class functionality with different
extraction templates and integration with the document processing pipeline.
"""

import os
import tempfile
from pathlib import Path

# Import core components
from core.extractor import Extractor
from core.models import ExtractionTemplate, ExtractionField, FieldType
from core.keychain import KeychainManager
from core.pii_masker import PIIMasker
from core.exceptions import CredentialError, APIValidationError


def create_sample_templates():
    """Create sample extraction templates for demonstration."""
    
    # Template 1: Company Information
    company_template = ExtractionTemplate(
        name="Company Information",
        prompt_description="""Extract company information from business documents.
        Focus on company name, financial data, and employee information.
        Use exact text for extractions and provide meaningful attributes.""",
        fields=[
            ExtractionField(
                name="company_name",
                type=FieldType.TEXT,
                description="Official name of the company",
                optional=False
            ),
            ExtractionField(
                name="annual_revenue",
                type=FieldType.CURRENCY,
                description="Annual revenue or sales figures",
                optional=True
            ),
            ExtractionField(
                name="employee_count",
                type=FieldType.NUMBER,
                description="Total number of employees",
                optional=True
            ),
            ExtractionField(
                name="industry",
                type=FieldType.TEXT,
                description="Industry or business sector",
                optional=True
            ),
            ExtractionField(
                name="founded_year",
                type=FieldType.NUMBER,
                description="Year the company was founded",
                optional=True
            )
        ],
        examples=[
            {
                "text": "TechCorp Inc., a leading software company founded in 2010, reported annual revenue of $50 million with a workforce of 200 employees in the technology sector.",
                "extractions": [
                    {"field_name": "company_name", "value": "TechCorp Inc.", "attributes": {"type": "corporation"}},
                    {"field_name": "annual_revenue", "value": "$50 million", "attributes": {"currency": "USD"}},
                    {"field_name": "employee_count", "value": "200", "attributes": {"type": "total_workforce"}},
                    {"field_name": "industry", "value": "technology sector", "attributes": {"category": "software"}},
                    {"field_name": "founded_year", "value": "2010", "attributes": {"precision": "exact"}}
                ]
            }
        ]
    )
    
    # Template 2: Financial Report
    financial_template = ExtractionTemplate(
        name="Financial Report",
        prompt_description="""Extract key financial metrics from financial reports.
        Focus on revenue, profit, expenses, and financial ratios.
        Convert all monetary values to numeric format when possible.""",
        fields=[
            ExtractionField(
                name="total_revenue",
                type=FieldType.CURRENCY,
                description="Total revenue for the period",
                optional=False
            ),
            ExtractionField(
                name="net_profit",
                type=FieldType.CURRENCY,
                description="Net profit or loss",
                optional=True
            ),
            ExtractionField(
                name="operating_expenses",
                type=FieldType.CURRENCY,
                description="Total operating expenses",
                optional=True
            ),
            ExtractionField(
                name="reporting_period",
                type=FieldType.TEXT,
                description="Time period for the report",
                optional=True
            )
        ],
        examples=[
            {
                "text": "For Q3 2024, the company achieved total revenue of $2.5 million, with net profit of $450,000 after operating expenses of $1.8 million.",
                "extractions": [
                    {"field_name": "total_revenue", "value": "$2.5 million", "attributes": {"period": "Q3 2024"}},
                    {"field_name": "net_profit", "value": "$450,000", "attributes": {"type": "after_tax"}},
                    {"field_name": "operating_expenses", "value": "$1.8 million", "attributes": {"type": "total"}},
                    {"field_name": "reporting_period", "value": "Q3 2024", "attributes": {"format": "quarterly"}}
                ]
            }
        ]
    )
    
    # Template 3: Contact Information
    contact_template = ExtractionTemplate(
        name="Contact Information",
        prompt_description="""Extract contact information from documents.
        Focus on names, addresses, phone numbers, and email addresses.
        Note: PII will be automatically masked before cloud processing.""",
        fields=[
            ExtractionField(
                name="person_name",
                type=FieldType.TEXT,
                description="Full name of the person",
                optional=False
            ),
            ExtractionField(
                name="job_title",
                type=FieldType.TEXT,
                description="Job title or position",
                optional=True
            ),
            ExtractionField(
                name="company",
                type=FieldType.TEXT,
                description="Company or organization name",
                optional=True
            ),
            ExtractionField(
                name="location",
                type=FieldType.TEXT,
                description="City, state, or country",
                optional=True
            )
        ],
        examples=[
            {
                "text": "John Smith, Senior Manager at ABC Corporation, is based in Ho Chi Minh City and can be reached at john.smith@abc.com or +84-123-456-789.",
                "extractions": [
                    {"field_name": "person_name", "value": "John Smith", "attributes": {"type": "full_name"}},
                    {"field_name": "job_title", "value": "Senior Manager", "attributes": {"level": "senior"}},
                    {"field_name": "company", "value": "ABC Corporation", "attributes": {"type": "employer"}},
                    {"field_name": "location", "value": "Ho Chi Minh City", "attributes": {"country": "Vietnam"}}
                ]
            }
        ]
    )
    
    return {
        "company": company_template,
        "financial": financial_template,
        "contact": contact_template
    }


def demo_basic_extraction():
    """Demonstrate basic extraction functionality."""
    print("=" * 60)
    print("DEMO: Basic Data Extraction")
    print("=" * 60)
    
    # Create extractor instance
    extractor = Extractor(
        model_id='gemini-2.5-flash',
        offline_mode=False,  # Set to True for offline testing
        max_workers=2,
        extraction_passes=1
    )
    
    # Get sample templates
    templates = create_sample_templates()
    
    # Sample texts for extraction
    sample_texts = {
        "company": """
        GlobalTech Solutions is a multinational technology company established in 2015.
        The company specializes in cloud computing and artificial intelligence solutions.
        Last year, GlobalTech reported annual revenue of $125 million and employs
        approximately 850 people worldwide across the technology industry.
        """,
        
        "financial": """
        Financial Summary for Q4 2024:
        - Total Revenue: $3.2 million (up 15% from previous quarter)
        - Operating Expenses: $2.1 million
        - Net Profit: $950,000
        - EBITDA: $1.1 million
        This represents our strongest quarterly performance to date.
        """,
        
        "contact": """
        Dr. Nguyen Thi Mai, Chief Technology Officer at VietTech Innovations,
        leads the AI research division from the company's headquarters in Hanoi.
        She previously worked at Google and Microsoft before joining VietTech in 2020.
        Contact: mai.nguyen@viettech.vn or +84-24-1234-5678.
        """
    }
    
    # Perform extractions
    for template_name, template in templates.items():
        print(f"\n--- Extracting {template_name.title()} Information ---")
        
        text = sample_texts[template_name]
        print(f"Input text: {text.strip()[:100]}...")
        
        try:
            result = extractor.extract(text, template)
            
            print(f"Status: {result.status.value}")
            print(f"Processing time: {result.processing_time:.2f}s")
            
            if result.extracted_data:
                print("Extracted data:")
                for field, value in result.extracted_data.items():
                    confidence = result.confidence_scores.get(field, 0.0)
                    print(f"  - {field}: {value} (confidence: {confidence:.2f})")
            
            if result.errors:
                print("Errors:")
                for error in result.errors:
                    print(f"  - {error}")
                    
        except Exception as e:
            print(f"Error during extraction: {e}")


def demo_large_document_processing():
    """Demonstrate processing of large documents with chunking."""
    print("\n" + "=" * 60)
    print("DEMO: Large Document Processing")
    print("=" * 60)
    
    # Create extractor with small buffer for demonstration
    extractor = Extractor(
        model_id='gemini-2.5-flash',
        offline_mode=True,  # Use offline mode for demo
        max_char_buffer=500,  # Small buffer to trigger chunking
        max_workers=2
    )
    
    # Create a large document
    large_text = """
    TechGiant Corporation Annual Report 2024
    
    Executive Summary:
    TechGiant Corporation, founded in 2005, has established itself as a leader in the
    enterprise software industry. The company develops and markets cloud-based solutions
    for businesses worldwide.
    
    Financial Performance:
    For the fiscal year 2024, TechGiant achieved record-breaking results:
    - Total Revenue: $450 million (25% increase from 2023)
    - Net Income: $85 million
    - Operating Expenses: $320 million
    - Research & Development: $45 million
    
    Workforce and Operations:
    The company currently employs 2,500 professionals across 15 countries.
    Our headquarters remain in San Francisco, with major offices in London,
    Tokyo, and Singapore.
    
    Market Position:
    TechGiant holds a 12% market share in the enterprise cloud software sector.
    We serve over 10,000 customers globally, including 85% of Fortune 500 companies.
    
    Future Outlook:
    Looking ahead to 2025, we project continued growth with expected revenue
    of $550 million and plan to hire an additional 400 employees.
    """ * 3  # Repeat to make it larger
    
    template = create_sample_templates()["company"]
    
    print(f"Document size: {len(large_text)} characters")
    
    # Test chunking
    chunks = extractor._chunk_text_if_needed(large_text)
    print(f"Document split into {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
        print(f"Chunk {i+1} size: {len(chunk)} characters")
        print(f"Chunk {i+1} preview: {chunk[:100]}...")


def demo_pii_masking():
    """Demonstrate PII masking functionality."""
    print("\n" + "=" * 60)
    print("DEMO: PII Masking Integration")
    print("=" * 60)
    
    # Create extractor with PII masking enabled
    pii_masker = PIIMasker()
    extractor = Extractor(
        offline_mode=True,  # Use offline mode for demo
        pii_masker=pii_masker
    )
    
    # Text with PII information
    text_with_pii = """
    Contact Information:
    Name: Nguyen Van A
    Email: nguyenvana@example.com
    Phone: 0123456789
    ID Number: 123456789012
    Bank Account: 1234567890123456
    
    Company: ABC Tech Solutions
    Position: Software Engineer
    """
    
    print("Original text:")
    print(text_with_pii)
    
    print("\nMasked text (for cloud processing):")
    masked_text = pii_masker.mask_for_cloud(text_with_pii)
    print(masked_text)
    
    # Show that extractor uses masking
    template = create_sample_templates()["contact"]
    
    print("\nExtracting from masked text...")
    try:
        result = extractor.extract(text_with_pii, template)
        print(f"Extraction status: {result.status.value}")
        if result.errors:
            print("Expected errors (offline mode):")
            for error in result.errors:
                print(f"  - {error}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main demo function."""
    print("LangExtract Integration Demo - Task 8")
    print("====================================")
    
    # Check API key availability
    try:
        keychain = KeychainManager()
        api_key = keychain.load_api_key()
        if api_key:
            print("✓ Gemini API key found - online extraction available")
        else:
            print("⚠ No API key found - running in offline mode")
            print("  To enable online extraction, configure your API key first:")
            print("  python -c \"from core.keychain import KeychainManager; KeychainManager().save_api_key('your-api-key')\"")
    except Exception as e:
        print(f"⚠ Keychain error: {e}")
    
    print("\nExtractor Configuration:")
    print("  - Model: gemini-2.5-flash")
    print("  - PII Masking: Enabled")
    print("  - Chunking: Enabled for large documents")
    print("  - Error Handling: Comprehensive")
    
    # Run demos
    try:
        demo_basic_extraction()
        demo_large_document_processing()
        demo_pii_masking()
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)
        
        print("\nNext Steps:")
        print("1. Configure your Gemini API key for online extraction")
        print("2. Test with your own documents and templates")
        print("3. Integrate with the GUI components (upcoming tasks)")
        print("4. Run the test suite: pytest tests/test_extractor.py")
        
    except Exception as e:
        print(f"\nDemo error: {e}")
        print("This is expected if running without proper API configuration.")


if __name__ == "__main__":
    main()
