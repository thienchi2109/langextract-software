"""
Unit tests for Excel export functionality.

Tests cover:
- Excel file generation with Data and Summary sheets
- Professional formatting with frozen headers and auto-fit columns
- Vietnamese locale support for numbers and dates
- Error handling and validation
"""

import pytest
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd

from core.excel_exporter import ExcelExporter
from core.models import (
    ExtractionTemplate, ExtractionField, ExtractionResult, FieldType, 
    ProcessingStatus
)
from core.exceptions import LangExtractorError


class TestExcelExporter(unittest.TestCase):
    """Test cases for the ExcelExporter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample template
        self.template = ExtractionTemplate(
            name="Company Information",
            prompt_description="Extract company information",
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
                    optional=False
                ),
                ExtractionField(
                    name="employee_count",
                    type=FieldType.NUMBER,
                    description="Number of employees",
                    optional=True
                ),
                ExtractionField(
                    name="founded_date",
                    type=FieldType.DATE,
                    description="Founded date",
                    optional=True
                )
            ]
        )
        
        self.exporter = ExcelExporter(self.template)
        
        # Sample aggregation result
        self.sample_aggregation_result = {
            'aggregated_data': [
                {
                    'source_file': 'company1.pdf',
                    'status': 'completed',
                    'processing_time': 2.5,
                    'confidence_scores': {'company_name': 0.95, 'revenue': 0.85},
                    'company_name': 'ABC Corp',
                    'revenue': 1000000000,
                    'employee_count': 150,
                    'founded_date': '2010-03-15'
                },
                {
                    'source_file': 'company2.pdf',
                    'status': 'completed',
                    'processing_time': 3.1,
                    'confidence_scores': {'company_name': 0.92, 'revenue': 0.78},
                    'company_name': 'XYZ Ltd',
                    'revenue': 500000000,
                    'employee_count': 75,
                    'founded_date': '2015-12-01'
                }
            ],
            'summary_statistics': {
                'processing_summary': {
                    'success_rate': 100.0,
                    'total_processing_time': 5.6,
                    'average_processing_time': 2.8,
                    'median_processing_time': 2.8
                },
                'data_quality_summary': {
                    'overall_quality_score': 85.5,
                    'completeness_rate': 90.0,
                    'consistency_score': 88.0,
                    'error_rate': 5.0
                },
                'field_summaries': {
                    'company_name': {
                        'completeness_rate': 100.0,
                        'unique_count': 2,
                        'min_value': 'ABC Corp',
                        'max_value': 'XYZ Ltd'
                    },
                    'revenue': {
                        'completeness_rate': 100.0,
                        'unique_count': 2,
                        'min_value': 500000000,
                        'max_value': 1000000000,
                        'mean_value': 750000000
                    },
                    'employee_count': {
                        'completeness_rate': 100.0,
                        'unique_count': 2,
                        'min_value': 75,
                        'max_value': 150,
                        'mean_value': 112.5
                    }
                }
            },
            'validation_errors': {
                'company3.pdf': ['Required field "revenue" is missing']
            },
            'total_files': 3,
            'successful_files': 2,
            'failed_files': 1
        }
    
    def test_initialization(self):
        """Test ExcelExporter initialization."""
        self.assertEqual(self.exporter.template, self.template)
        self.assertEqual(self.exporter.date_format, 'dd/mm/yyyy')
        self.assertEqual(self.exporter.currency_format, '#,##0" ₫"')
    
    def test_get_data_columns(self):
        """Test data columns ordering."""
        columns = self.exporter._get_data_columns()
        
        expected_columns = [
            'source_file', 'status', 'processing_time',
            'company_name', 'revenue', 'employee_count', 'founded_date',
            'confidence_scores'
        ]
        
        self.assertEqual(columns, expected_columns)
    
    def test_reorder_data_columns(self):
        """Test DataFrame column reordering."""
        # Create DataFrame with mixed column order
        df = pd.DataFrame({
            'revenue': [1000000],
            'source_file': ['test.pdf'],
            'company_name': ['Test Corp'],
            'status': ['completed'],
            'extra_column': ['extra_value']
        })
        
        reordered_df = self.exporter._reorder_data_columns(df)
        
        # Check that columns are in correct order
        expected_start = ['source_file', 'status', 'company_name', 'revenue']
        actual_start = list(reordered_df.columns)[:4]
        self.assertEqual(actual_start, expected_start)
        
        # Check that extra column is preserved
        self.assertIn('extra_column', reordered_df.columns)
    
    def test_apply_data_types(self):
        """Test data type conversion."""
        df = pd.DataFrame({
            'company_name': ['Test Corp'],
            'revenue': ['1000000'],
            'employee_count': ['100'],
            'founded_date': ['2020-01-01']
        })
        
        converted_df = self.exporter._apply_data_types(df)
        
        # Check data types
        self.assertEqual(converted_df['company_name'].dtype, 'object')  # TEXT remains object
        self.assertTrue(pd.api.types.is_numeric_dtype(converted_df['revenue']))  # CURRENCY to numeric
        self.assertTrue(pd.api.types.is_numeric_dtype(converted_df['employee_count']))  # NUMBER to numeric
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(converted_df['founded_date']))  # DATE to datetime
    
    def test_format_stat_value(self):
        """Test statistical value formatting."""
        # Test number formatting
        self.assertEqual(
            self.exporter._format_stat_value(1234567.89, FieldType.NUMBER),
            "1,234,567.89"
        )
        
        # Test currency formatting
        self.assertEqual(
            self.exporter._format_stat_value(1000000, FieldType.CURRENCY),
            "1,000,000 ₫"
        )
        
        # Test text formatting
        long_text = "This is a very long text that should be truncated for display"
        formatted_text = self.exporter._format_stat_value(long_text, FieldType.TEXT)
        self.assertLessEqual(len(formatted_text), 50)
        
        # Test None value
        self.assertEqual(
            self.exporter._format_stat_value(None, FieldType.TEXT),
            "N/A"
        )
    
    def test_get_export_filename(self):
        """Test export filename generation."""
        # Test with default base name
        filename = self.exporter.get_export_filename()
        self.assertTrue(filename.startswith('company_information_export_'))
        self.assertTrue(filename.endswith('.xlsx'))
        
        # Test with custom base name
        filename = self.exporter.get_export_filename('custom_report')
        self.assertTrue(filename.startswith('custom_report_export_'))
        self.assertTrue(filename.endswith('.xlsx'))
    
    def test_validate_aggregation_result_valid(self):
        """Test validation of valid aggregation result."""
        self.assertTrue(self.exporter.validate_aggregation_result(self.sample_aggregation_result))
    
    def test_validate_aggregation_result_invalid(self):
        """Test validation of invalid aggregation result."""
        invalid_result = {'aggregated_data': []}  # Missing required keys
        self.assertFalse(self.exporter.validate_aggregation_result(invalid_result))
    
    def test_export_results_success(self):
        """Test successful Excel export."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'test_export.xlsx'
            
            result_path = self.exporter.export_results(
                self.sample_aggregation_result,
                output_path
            )
            
            # Check that file was created
            self.assertTrue(Path(result_path).exists())
            self.assertEqual(result_path, str(output_path))
            
            # Check file size (should be > 0)
            self.assertGreater(Path(result_path).stat().st_size, 0)
    
    def test_export_results_with_empty_data(self):
        """Test Excel export with empty data."""
        empty_result = {
            'aggregated_data': [],
            'summary_statistics': {
                'processing_summary': {},
                'data_quality_summary': {},
                'field_summaries': {}
            },
            'validation_errors': {},
            'total_files': 0,
            'successful_files': 0,
            'failed_files': 0
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'empty_export.xlsx'
            
            result_path = self.exporter.export_results(empty_result, output_path)
            
            # Check that file was created even with empty data
            self.assertTrue(Path(result_path).exists())
    
    def test_export_results_invalid_path(self):
        """Test Excel export with invalid output path."""
        # Use a path that definitely cannot be created (invalid characters on Windows)
        invalid_path = 'C:\\invalid<>path\\test.xlsx'

        with self.assertRaises(LangExtractorError):
            self.exporter.export_results(self.sample_aggregation_result, invalid_path)
    
    def test_export_results_with_charts(self):
        """Test Excel export with charts enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'test_with_charts.xlsx'
            
            result_path = self.exporter.export_results(
                self.sample_aggregation_result,
                output_path,
                include_charts=True
            )
            
            self.assertTrue(Path(result_path).exists())
    
    def test_export_results_without_charts(self):
        """Test Excel export with charts disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'test_without_charts.xlsx'
            
            result_path = self.exporter.export_results(
                self.sample_aggregation_result,
                output_path,
                include_charts=False
            )
            
            self.assertTrue(Path(result_path).exists())
    
    def test_create_formats(self):
        """Test Excel format creation."""
        # Mock workbook
        mock_workbook = Mock()
        mock_workbook.add_format.return_value = Mock()
        
        formats = self.exporter._create_formats(mock_workbook)
        
        # Check that all required formats are created
        required_formats = [
            'header', 'date', 'number', 'currency', 'percentage', 'text',
            'summary_header', 'summary_label', 'summary_value'
        ]
        
        for format_name in required_formats:
            self.assertIn(format_name, formats)
        
        # Check that workbook.add_format was called for each format
        self.assertEqual(mock_workbook.add_format.call_count, len(required_formats))
    
    def test_integration_with_real_data(self):
        """Test integration with realistic aggregation data."""
        # This test uses more realistic data structure
        realistic_result = {
            'aggregated_data': [
                {
                    'source_file': 'annual_report_2023.pdf',
                    'status': 'completed',
                    'processing_time': 4.2,
                    'confidence_scores': {
                        'company_name': 0.98,
                        'revenue': 0.92,
                        'employee_count': 0.87
                    },
                    'company_name': 'Công ty TNHH ABC',
                    'revenue': 15000000000,  # 15 billion VND
                    'employee_count': 250,
                    'founded_date': '1995-06-15'
                }
            ],
            'summary_statistics': {
                'processing_summary': {
                    'success_rate': 95.0,
                    'total_processing_time': 12.5,
                    'average_processing_time': 4.17,
                    'median_processing_time': 4.2
                },
                'data_quality_summary': {
                    'overall_quality_score': 92.3,
                    'completeness_rate': 95.0,
                    'consistency_score': 89.5,
                    'error_rate': 2.1
                },
                'field_summaries': {
                    'company_name': {
                        'completeness_rate': 100.0,
                        'unique_count': 1
                    },
                    'revenue': {
                        'completeness_rate': 95.0,
                        'unique_count': 1,
                        'min_value': 15000000000,
                        'max_value': 15000000000,
                        'mean_value': 15000000000
                    }
                }
            },
            'validation_errors': {},
            'total_files': 1,
            'successful_files': 1,
            'failed_files': 0
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'realistic_export.xlsx'
            
            result_path = self.exporter.export_results(realistic_result, output_path)
            
            self.assertTrue(Path(result_path).exists())
            
            # Verify file can be read back
            try:
                df = pd.read_excel(result_path, sheet_name='Data')
                self.assertGreater(len(df), 0)
                self.assertIn('company_name', df.columns)
                self.assertIn('revenue', df.columns)
            except Exception as e:
                self.fail(f"Failed to read generated Excel file: {e}")


if __name__ == '__main__':
    unittest.main()
