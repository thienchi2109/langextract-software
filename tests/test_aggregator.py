"""
Unit tests for the data aggregation and validation system.

Tests cover:
- Data aggregation and validation logic
- Type conversion and validation based on schema field types
- Summary statistics calculation for aggregated data
- Error collection and reporting per file
"""

import pytest
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from core.aggregator import Aggregator
from core.models import (
    ExtractionResult, ExtractionTemplate, ExtractionField, FieldType, 
    ProcessingSession, ProcessingStatus
)
from core.exceptions import ValidationError


class TestAggregator(unittest.TestCase):
    """Test cases for the Aggregator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample template
        self.template = ExtractionTemplate(
            name="Test Template",
            prompt_description="Test extraction template",
            fields=[
                ExtractionField(name="company_name", type=FieldType.TEXT, description="Company name"),
                ExtractionField(name="revenue", type=FieldType.CURRENCY, description="Annual revenue"),
                ExtractionField(name="employee_count", type=FieldType.NUMBER, description="Number of employees"),
                ExtractionField(name="founded_date", type=FieldType.DATE, description="Date founded"),
                ExtractionField(name="description", type=FieldType.TEXT, description="Company description", optional=True)
            ]
        )
        
        self.aggregator = Aggregator(self.template)
        
        # Sample extraction results
        self.sample_results = [
            ExtractionResult(
                source_file="company1.pdf",
                extracted_data={
                    "company_name": "ABC Corp",
                    "revenue": "1.000.000.000 ₫",
                    "employee_count": "150",
                    "founded_date": "15/03/2010",
                    "description": "Leading technology company"
                },
                confidence_scores={"company_name": 0.95, "revenue": 0.85},
                processing_time=2.5,
                status=ProcessingStatus.COMPLETED
            ),
            ExtractionResult(
                source_file="company2.pdf",
                extracted_data={
                    "company_name": "XYZ Ltd",
                    "revenue": "500,000,000 VND",
                    "employee_count": "75",
                    "founded_date": "2015-12-01"
                },
                confidence_scores={"company_name": 0.92, "revenue": 0.78},
                processing_time=3.1,
                status=ProcessingStatus.COMPLETED
            )
        ]
    
    def test_aggregator_initialization(self):
        """Test aggregator initialization with template."""
        self.assertEqual(self.aggregator.template, self.template)
        self.assertEqual(len(self.aggregator._field_lookup), 5)
        self.assertIn("company_name", self.aggregator._field_lookup)
    
    def test_convert_field_value_text(self):
        """Test text field conversion."""
        field = ExtractionField(name="test", type=FieldType.TEXT, description="Test field")
        result = self.aggregator._convert_field_value("  Test Company  ", field)
        self.assertEqual(result, "Test Company")
    
    def test_convert_field_value_number_vietnamese(self):
        """Test number conversion with Vietnamese locale."""
        field = ExtractionField(name="test", type=FieldType.NUMBER, description="Test field", number_locale="vi-VN")
        
        # Test integer
        result = self.aggregator._convert_field_value("1.000", field)
        self.assertEqual(result, 1000)
        
        # Test float
        result = self.aggregator._convert_field_value("1.234.567,89", field)
        self.assertEqual(result, 1234567.89)
    
    def test_convert_field_value_number_english(self):
        """Test number conversion with English locale."""
        field = ExtractionField(name="test", type=FieldType.NUMBER, description="Test field", number_locale="en-US")
        
        # Test integer
        result = self.aggregator._convert_field_value("1,000", field)
        self.assertEqual(result, 1000)
        
        # Test float
        result = self.aggregator._convert_field_value("1,234,567.89", field)
        self.assertEqual(result, 1234567.89)
    
    def test_convert_field_value_date(self):
        """Test date field conversion."""
        field = ExtractionField(name="test", type=FieldType.DATE, description="Test field")
        
        # Test various date formats
        test_cases = [
            ("15/03/2024", datetime(2024, 3, 15)),
            ("15-03-2024", datetime(2024, 3, 15)),
            ("2024-03-15", datetime(2024, 3, 15)),
            ("15.03.2024", datetime(2024, 3, 15))
        ]
        
        for date_str, expected in test_cases:
            result = self.aggregator._convert_field_value(date_str, field)
            self.assertEqual(result, expected)
    
    def test_convert_field_value_currency(self):
        """Test currency field conversion."""
        field = ExtractionField(name="test", type=FieldType.CURRENCY, description="Test field")
        
        # Test various currency formats
        test_cases = [
            ("1.000.000 ₫", Decimal("1000000")),
            ("1,000,000 USD", Decimal("1000000")),
            ("500.000 VND", Decimal("500000"))
        ]
        
        for currency_str, expected in test_cases:
            result = self.aggregator._convert_field_value(currency_str, field)
            self.assertEqual(result, expected)
    
    def test_convert_field_value_invalid_date(self):
        """Test invalid date conversion raises ValueError."""
        field = ExtractionField(name="test", type=FieldType.DATE, description="Test field")
        
        with self.assertRaises(ValueError):
            self.aggregator._convert_field_value("invalid-date", field)
    
    def test_validate_and_convert_result_success(self):
        """Test successful result validation and conversion."""
        result = self.sample_results[0]
        validated_data = self.aggregator._validate_and_convert_result(result)
        
        self.assertEqual(validated_data["company_name"], "ABC Corp")
        self.assertEqual(validated_data["employee_count"], 150)
        self.assertIsInstance(validated_data["revenue"], Decimal)
        self.assertIsInstance(validated_data["founded_date"], datetime)
    
    def test_validate_and_convert_result_missing_required_field(self):
        """Test validation failure with missing required field."""
        result = ExtractionResult(
            source_file="test.pdf",
            extracted_data={"company_name": "Test Corp"},  # Missing required fields
            status=ProcessingStatus.COMPLETED
        )
        
        with self.assertRaises(ValidationError) as context:
            self.aggregator._validate_and_convert_result(result)
        
        error_message = str(context.exception)
        self.assertIn("Required field 'revenue' is missing", error_message)
        self.assertIn("Required field 'employee_count' is missing", error_message)
    
    def test_validate_and_convert_result_unexpected_field(self):
        """Test validation with unexpected field."""
        result = ExtractionResult(
            source_file="test.pdf",
            extracted_data={
                "company_name": "Test Corp",
                "revenue": "1000000",
                "employee_count": "100",
                "founded_date": "2020-01-01",
                "unexpected_field": "value"  # Not in template
            },
            status=ProcessingStatus.COMPLETED
        )
        
        with self.assertRaises(ValidationError) as context:
            self.aggregator._validate_and_convert_result(result)
        
        self.assertIn("Unexpected field 'unexpected_field'", str(context.exception))
    
    def test_aggregate_results_success(self):
        """Test successful aggregation of multiple results."""
        aggregation_result = self.aggregator.aggregate_results(self.sample_results)
        
        self.assertEqual(aggregation_result['total_files'], 2)
        self.assertEqual(aggregation_result['successful_files'], 2)
        self.assertEqual(aggregation_result['failed_files'], 0)
        
        # Check aggregated data structure
        aggregated_data = aggregation_result['aggregated_data']
        self.assertEqual(len(aggregated_data), 2)
        
        # Check first record
        first_record = aggregated_data[0]
        self.assertEqual(first_record['source_file'], "company1.pdf")
        self.assertEqual(first_record['company_name'], "ABC Corp")
        self.assertEqual(first_record['employee_count'], 150)
        
        # Check summary statistics
        summary_stats = aggregation_result['summary_statistics']
        self.assertIn('processing_summary', summary_stats)
        self.assertIn('data_quality_summary', summary_stats)
        self.assertIn('field_summaries', summary_stats)
    
    def test_aggregate_results_with_failures(self):
        """Test aggregation with some failed results."""
        # Add a result with missing required fields
        failed_result = ExtractionResult(
            source_file="failed.pdf",
            extracted_data={"company_name": "Failed Corp"},  # Missing required fields
            status=ProcessingStatus.COMPLETED
        )
        
        results_with_failure = self.sample_results + [failed_result]
        aggregation_result = self.aggregator.aggregate_results(results_with_failure)
        
        self.assertEqual(aggregation_result['total_files'], 3)
        self.assertEqual(aggregation_result['successful_files'], 2)
        self.assertEqual(aggregation_result['failed_files'], 1)
        
        # Check validation errors
        validation_errors = aggregation_result['validation_errors']
        self.assertIn("failed.pdf", validation_errors)
    
    def test_calculate_summary_statistics(self):
        """Test summary statistics calculation."""
        aggregation_result = self.aggregator.aggregate_results(self.sample_results)
        summary_stats = aggregation_result['summary_statistics']
        
        # Check processing summary
        processing_summary = summary_stats['processing_summary']
        self.assertEqual(processing_summary['total_files'], 2)
        self.assertEqual(processing_summary['successful_files'], 2)
        self.assertEqual(processing_summary['failed_files'], 0)
        self.assertEqual(processing_summary['success_rate'], 100.0)
        self.assertGreater(processing_summary['total_processing_time'], 0)
        
        # Check field summaries
        field_summaries = summary_stats['field_summaries']
        self.assertIn('company_name', field_summaries)
        self.assertIn('revenue', field_summaries)
        
        # Check company_name field summary
        company_name_summary = field_summaries['company_name']
        self.assertEqual(company_name_summary['field_type'], 'text')
        self.assertEqual(company_name_summary['total_count'], 2)
        self.assertEqual(company_name_summary['null_count'], 0)
        self.assertEqual(company_name_summary['completeness_rate'], 100.0)
        self.assertEqual(company_name_summary['unique_count'], 2)
    
    def test_field_statistics_numeric_fields(self):
        """Test statistics calculation for numeric fields."""
        aggregation_result = self.aggregator.aggregate_results(self.sample_results)
        field_summaries = aggregation_result['summary_statistics']['field_summaries']
        
        # Check employee_count field statistics
        employee_summary = field_summaries['employee_count']
        self.assertEqual(employee_summary['field_type'], 'number')
        self.assertIn('min_value', employee_summary)
        self.assertIn('max_value', employee_summary)
        self.assertIn('mean_value', employee_summary)
        self.assertIn('median_value', employee_summary)
        
        # Verify actual values
        self.assertEqual(employee_summary['min_value'], 75)
        self.assertEqual(employee_summary['max_value'], 150)
        self.assertEqual(employee_summary['mean_value'], 112.5)
    
    def test_field_statistics_text_fields(self):
        """Test statistics calculation for text fields."""
        aggregation_result = self.aggregator.aggregate_results(self.sample_results)
        field_summaries = aggregation_result['summary_statistics']['field_summaries']
        
        # Check company_name field statistics
        company_summary = field_summaries['company_name']
        self.assertEqual(company_summary['field_type'], 'text')
        self.assertIn('min_length', company_summary)
        self.assertIn('max_length', company_summary)
        self.assertIn('avg_length', company_summary)
    
    def test_field_statistics_date_fields(self):
        """Test statistics calculation for date fields."""
        aggregation_result = self.aggregator.aggregate_results(self.sample_results)
        field_summaries = aggregation_result['summary_statistics']['field_summaries']
        
        # Check founded_date field statistics
        date_summary = field_summaries['founded_date']
        self.assertEqual(date_summary['field_type'], 'date')
        self.assertIn('earliest_date', date_summary)
        self.assertIn('latest_date', date_summary)
        self.assertIn('date_range_days', date_summary)
    
    def test_validate_session_data(self):
        """Test session data validation."""
        session = ProcessingSession(
            template=self.template,
            files=["company1.pdf", "company2.pdf"],
            results=self.sample_results
        )
        
        aggregation_result = self.aggregator.validate_session_data(session)
        
        self.assertEqual(aggregation_result['total_files'], 2)
        self.assertEqual(aggregation_result['successful_files'], 2)
        
        # Check that session summary stats were updated
        self.assertIsNotNone(session.summary_stats)
        self.assertIn('processing_summary', session.summary_stats)
    
    def test_get_data_quality_report(self):
        """Test data quality report generation."""
        aggregation_result = self.aggregator.aggregate_results(self.sample_results)
        quality_report = self.aggregator.get_data_quality_report(aggregation_result)
        
        self.assertIn('overall_quality_grade', quality_report)
        self.assertIn('completeness_rate', quality_report)
        self.assertIn('error_summary', quality_report)
        self.assertIn('problematic_fields', quality_report)
        self.assertIn('recommendations', quality_report)
        
        # Check error summary structure
        error_summary = quality_report['error_summary']
        self.assertIn('total_errors', error_summary)
        self.assertIn('files_with_errors', error_summary)
        self.assertIn('common_error_patterns', error_summary)
    
    def test_get_quality_grade(self):
        """Test quality grade calculation."""
        self.assertEqual(self.aggregator._get_quality_grade(95), "A")
        self.assertEqual(self.aggregator._get_quality_grade(85), "B")
        self.assertEqual(self.aggregator._get_quality_grade(75), "C")
        self.assertEqual(self.aggregator._get_quality_grade(65), "D")
        self.assertEqual(self.aggregator._get_quality_grade(55), "F")
    
    def test_generate_quality_recommendations(self):
        """Test quality recommendations generation."""
        # Mock summary stats with quality issues
        summary_stats = {
            'data_quality_summary': {
                'overall_quality_score': 75,
                'completeness_rate': 80
            },
            'processing_summary': {
                'success_rate': 85
            }
        }
        
        error_patterns = {'missing_required_fields': 3, 'type_conversion_errors': 2}
        
        recommendations = self.aggregator._generate_quality_recommendations(summary_stats, error_patterns)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check that recommendations contain expected suggestions
        recommendations_text = ' '.join(recommendations)
        self.assertIn('document quality', recommendations_text)
        self.assertIn('extraction prompts', recommendations_text)
    
    def test_empty_results_handling(self):
        """Test handling of empty results list."""
        aggregation_result = self.aggregator.aggregate_results([])
        
        self.assertEqual(aggregation_result['total_files'], 0)
        self.assertEqual(aggregation_result['successful_files'], 0)
        self.assertEqual(aggregation_result['failed_files'], 0)
        
        summary_stats = aggregation_result['summary_statistics']
        self.assertEqual(summary_stats['processing_summary']['success_rate'], 0)
    
    def test_optional_field_handling(self):
        """Test handling of optional fields."""
        result = ExtractionResult(
            source_file="test.pdf",
            extracted_data={
                "company_name": "Test Corp",
                "revenue": "1000000",
                "employee_count": "100",
                "founded_date": "2020-01-01"
                # description is optional and missing
            },
            status=ProcessingStatus.COMPLETED
        )
        
        # Should not raise validation error for missing optional field
        validated_data = self.aggregator._validate_and_convert_result(result)
        self.assertIsNone(validated_data["description"])


if __name__ == '__main__':
    unittest.main()