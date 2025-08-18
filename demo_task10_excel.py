"""
Demo script for Task 10: Excel export functionality.

This script demonstrates the ExcelExporter class with:
- Professional Excel report generation
- Data and Summary sheets with formatting
- Vietnamese locale support
- Charts and visualizations
- Error handling and validation
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.excel_exporter import ExcelExporter
from core.models import ExtractionTemplate, ExtractionField, FieldType
from core.logging_config import setup_logging, get_logger


def create_sample_template():
    """Create sample extraction template for demo."""
    return ExtractionTemplate(
        name="Vietnamese Company Report",
        prompt_description="Extract company information from Vietnamese business reports",
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
                optional=False
            ),
            ExtractionField(
                name="employee_count",
                type=FieldType.NUMBER,
                description="Số lượng nhân viên",
                optional=True
            ),
            ExtractionField(
                name="founded_date",
                type=FieldType.DATE,
                description="Ngày thành lập",
                optional=True
            ),
            ExtractionField(
                name="industry",
                type=FieldType.TEXT,
                description="Lĩnh vực kinh doanh",
                optional=True
            ),
            ExtractionField(
                name="headquarters",
                type=FieldType.TEXT,
                description="Trụ sở chính",
                optional=True
            )
        ]
    )


def create_sample_aggregation_result():
    """Create comprehensive sample aggregation result."""
    return {
        'aggregated_data': [
            {
                'source_file': 'bao_cao_tai_chinh_vietcombank_2023.pdf',
                'status': 'completed',
                'processing_time': 5.2,
                'confidence_scores': {
                    'company_name': 0.98,
                    'revenue': 0.95,
                    'employee_count': 0.89,
                    'founded_date': 0.92
                },
                'company_name': 'Ngân hàng TMCP Ngoại thương Việt Nam',
                'revenue': 45678900000000,  # 45.6 trillion VND
                'employee_count': 23456,
                'founded_date': '1963-04-01',
                'industry': 'Ngân hàng và Dịch vụ tài chính',
                'headquarters': 'Hà Nội'
            },
            {
                'source_file': 'bao_cao_thuong_nien_vingroup_2023.pdf',
                'status': 'completed',
                'processing_time': 6.8,
                'confidence_scores': {
                    'company_name': 0.97,
                    'revenue': 0.93,
                    'employee_count': 0.85,
                    'founded_date': 0.88
                },
                'company_name': 'Tập đoàn Vingroup',
                'revenue': 156789000000000,  # 156.7 trillion VND
                'employee_count': 45678,
                'founded_date': '1993-08-15',
                'industry': 'Bất động sản và Dịch vụ',
                'headquarters': 'Hà Nội'
            },
            {
                'source_file': 'bao_cao_tai_chinh_fpt_2023.pdf',
                'status': 'completed',
                'processing_time': 4.1,
                'confidence_scores': {
                    'company_name': 0.96,
                    'revenue': 0.91,
                    'employee_count': 0.87,
                    'founded_date': 0.94
                },
                'company_name': 'Công ty Cổ phần FPT',
                'revenue': 34567800000000,  # 34.5 trillion VND
                'employee_count': 28934,
                'founded_date': '1988-09-13',
                'industry': 'Công nghệ thông tin',
                'headquarters': 'Hà Nội'
            },
            {
                'source_file': 'bao_cao_petrolimex_2023.pdf',
                'status': 'completed',
                'processing_time': 3.9,
                'confidence_scores': {
                    'company_name': 0.99,
                    'revenue': 0.94,
                    'employee_count': 0.82
                },
                'company_name': 'Tập đoàn Xăng dầu Việt Nam',
                'revenue': 287654000000000,  # 287.6 trillion VND
                'employee_count': 15678,
                'founded_date': '1956-01-01',
                'industry': 'Năng lượng và Dầu khí',
                'headquarters': 'Hà Nội'
            },
            {
                'source_file': 'bao_cao_mobifone_2023.pdf',
                'status': 'completed',
                'processing_time': 4.7,
                'confidence_scores': {
                    'company_name': 0.95,
                    'revenue': 0.89,
                    'employee_count': 0.78
                },
                'company_name': 'Tổng công ty Viễn thông MobiFone',
                'revenue': 23456700000000,  # 23.4 trillion VND
                'employee_count': 8934,
                'founded_date': '1993-02-16',
                'industry': 'Viễn thông',
                'headquarters': 'Hà Nội'
            }
        ],
        'summary_statistics': {
            'processing_summary': {
                'success_rate': 83.3,  # 5 out of 6 files successful
                'total_processing_time': 24.7,
                'average_processing_time': 4.94,
                'median_processing_time': 4.7
            },
            'data_quality_summary': {
                'overall_quality_score': 89.2,
                'completeness_rate': 92.5,
                'consistency_score': 87.8,
                'error_rate': 7.5
            },
            'field_summaries': {
                'company_name': {
                    'completeness_rate': 100.0,
                    'unique_count': 5,
                    'min_value': 'Công ty Cổ phần FPT',
                    'max_value': 'Tổng công ty Viễn thông MobiFone'
                },
                'revenue': {
                    'completeness_rate': 100.0,
                    'unique_count': 5,
                    'min_value': 23456700000000,
                    'max_value': 287654000000000,
                    'mean_value': 109629280000000
                },
                'employee_count': {
                    'completeness_rate': 100.0,
                    'unique_count': 5,
                    'min_value': 8934,
                    'max_value': 45678,
                    'mean_value': 24536
                },
                'founded_date': {
                    'completeness_rate': 80.0,
                    'unique_count': 4,
                    'min_value': '1956-01-01',
                    'max_value': '1993-08-15'
                },
                'industry': {
                    'completeness_rate': 100.0,
                    'unique_count': 5,
                    'min_value': 'Bất động sản và Dịch vụ',
                    'max_value': 'Viễn thông'
                },
                'headquarters': {
                    'completeness_rate': 100.0,
                    'unique_count': 1,
                    'min_value': 'Hà Nội',
                    'max_value': 'Hà Nội'
                }
            }
        },
        'validation_errors': {
            'bao_cao_sacombank_2023.pdf': [
                'Required field "revenue" is missing or empty',
                'Field "employee_count" conversion failed: invalid literal for int()'
            ]
        },
        'total_files': 6,
        'successful_files': 5,
        'failed_files': 1
    }


def demo_basic_export():
    """Demonstrate basic Excel export functionality."""
    print("\n" + "="*60)
    print("DEMO: Basic Excel Export")
    print("="*60)
    
    # Create template and exporter
    template = create_sample_template()
    exporter = ExcelExporter(template)
    
    # Create sample data
    aggregation_result = create_sample_aggregation_result()
    
    # Export to temporary file
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / exporter.get_export_filename("vietnamese_companies")
        
        print(f"Exporting to: {output_path}")
        
        try:
            result_path = exporter.export_results(
                aggregation_result,
                output_path,
                include_charts=True,
                include_validation=True
            )
            
            print(f"✅ Export successful: {result_path}")
            print(f"📊 File size: {Path(result_path).stat().st_size:,} bytes")
            
            # Show export details
            print(f"\n📋 Export Details:")
            print(f"  - Template: {template.name}")
            print(f"  - Fields: {len(template.fields)}")
            print(f"  - Records: {len(aggregation_result['aggregated_data'])}")
            print(f"  - Success rate: {aggregation_result['summary_statistics']['processing_summary']['success_rate']:.1f}%")
            
            return result_path
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return None


def demo_formatting_features():
    """Demonstrate Excel formatting features."""
    print("\n" + "="*60)
    print("DEMO: Excel Formatting Features")
    print("="*60)
    
    template = create_sample_template()
    exporter = ExcelExporter(template)
    
    print("🎨 Formatting Features:")
    print("  ✅ Frozen headers for easy navigation")
    print("  ✅ Auto-fit columns for optimal width")
    print("  ✅ Vietnamese currency formatting (₫)")
    print("  ✅ Date formatting (dd/mm/yyyy)")
    print("  ✅ Number formatting with thousands separators")
    print("  ✅ Professional color scheme")
    print("  ✅ Conditional formatting for quality scores")
    print("  ✅ Charts and visualizations")
    
    print(f"\n📐 Format Specifications:")
    print(f"  - Date format: {exporter.date_format}")
    print(f"  - Number format: {exporter.number_format}")
    print(f"  - Currency format: {exporter.currency_format}")
    print(f"  - Percentage format: {exporter.percentage_format}")


def demo_data_validation():
    """Demonstrate data validation features."""
    print("\n" + "="*60)
    print("DEMO: Data Validation")
    print("="*60)
    
    template = create_sample_template()
    exporter = ExcelExporter(template)
    aggregation_result = create_sample_aggregation_result()
    
    print("🔍 Validation Features:")
    
    # Test validation
    is_valid = exporter.validate_aggregation_result(aggregation_result)
    print(f"  ✅ Aggregation result validation: {'PASSED' if is_valid else 'FAILED'}")
    
    # Show data quality metrics
    quality_summary = aggregation_result['summary_statistics']['data_quality_summary']
    print(f"  📊 Overall quality score: {quality_summary['overall_quality_score']:.1f}")
    print(f"  📈 Completeness rate: {quality_summary['completeness_rate']:.1f}%")
    print(f"  🎯 Consistency score: {quality_summary['consistency_score']:.1f}")
    print(f"  ⚠️  Error rate: {quality_summary['error_rate']:.1f}%")
    
    # Show error analysis
    validation_errors = aggregation_result['validation_errors']
    if validation_errors:
        print(f"\n❌ Validation Errors Found:")
        for file_name, errors in validation_errors.items():
            print(f"  📄 {file_name}:")
            for error in errors:
                print(f"    - {error}")
    else:
        print(f"\n✅ No validation errors found")


def demo_vietnamese_locale():
    """Demonstrate Vietnamese locale support."""
    print("\n" + "="*60)
    print("DEMO: Vietnamese Locale Support")
    print("="*60)
    
    template = create_sample_template()
    exporter = ExcelExporter(template)
    
    print("🇻🇳 Vietnamese Locale Features:")
    
    # Test currency formatting
    test_values = [1000000, 1234567890, 45678900000000]
    print(f"\n💰 Currency Formatting:")
    for value in test_values:
        formatted = exporter._format_stat_value(value, FieldType.CURRENCY)
        print(f"  {value:,} → {formatted}")
    
    # Test number formatting
    print(f"\n🔢 Number Formatting:")
    for value in test_values:
        formatted = exporter._format_stat_value(value, FieldType.NUMBER)
        print(f"  {value:,} → {formatted}")
    
    # Test date formatting
    print(f"\n📅 Date Formatting:")
    test_dates = ['1963-04-01', '1993-08-15', '1988-09-13']
    for date_str in test_dates:
        formatted = exporter._format_stat_value(date_str, FieldType.DATE)
        print(f"  {date_str} → {formatted}")


def main():
    """Main demo function."""
    # Setup logging
    setup_logging({
        'log_level': 'INFO',
        'console_logging': True,
        'structured_logging': False
    })
    
    logger = get_logger(__name__)
    logger.info("Starting Excel Export Demo")
    
    print("Excel Export Functionality Demo - Task 10")
    print("=========================================")
    
    try:
        # Run demos
        export_path = demo_basic_export()
        demo_formatting_features()
        demo_data_validation()
        demo_vietnamese_locale()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        if export_path:
            print(f"\n📁 Sample Excel file generated at:")
            print(f"   {export_path}")
            print(f"\n💡 Features demonstrated:")
            print(f"   ✅ Professional Excel report generation")
            print(f"   ✅ Data and Summary sheets with formatting")
            print(f"   ✅ Vietnamese locale support")
            print(f"   ✅ Charts and visualizations")
            print(f"   ✅ Data validation and error reporting")
            print(f"   ✅ Comprehensive statistics and analysis")
        
        print(f"\n🚀 Ready for integration with:")
        print(f"   - Task 8 Extractor (data extraction)")
        print(f"   - Task 9 Aggregator (data validation)")
        print(f"   - Task 11 GUI (user interface)")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"❌ Demo Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
