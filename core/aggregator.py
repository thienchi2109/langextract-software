"""
Data aggregation and validation system for extraction results.

This module provides the Aggregator class that handles:
- Collection and validation of extraction results
- Data type conversion and validation based on schema field types
- Summary statistics calculation for aggregated data
- Error collection and reporting per file
"""

import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
from collections import defaultdict, Counter

from .models import (
    ExtractionResult, ExtractionTemplate, ExtractionField, FieldType, 
    ProcessingSession, ProcessingStatus
)
from .exceptions import ValidationError, LangExtractorError, ErrorCategory

logger = logging.getLogger(__name__)


class Aggregator:
    """
    Data aggregation and validation system for extraction results.
    
    Provides comprehensive validation, type conversion, statistics calculation,
    and error reporting for extracted data across multiple files.
    """
    
    def __init__(self, template: ExtractionTemplate):
        """
        Initialize aggregator with extraction template.
        
        Args:
            template: ExtractionTemplate defining the schema for validation
        """
        self.template = template
        self.logger = logger
        self._field_lookup = {field.name: field for field in template.fields}
    
    def aggregate_results(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """
        Aggregate and validate extraction results from multiple files.
        
        Args:
            results: List of extraction results to aggregate
            
        Returns:
            Dict containing aggregated data, statistics, and validation summary
            
        Raises:
            ValidationError: If critical validation errors occur
        """
        self.logger.info(f"Aggregating {len(results)} extraction results")
        
        # Initialize aggregation containers
        aggregated_data = []
        validation_errors = defaultdict(list)
        field_statistics = defaultdict(dict)
        
        # Process each result
        for result in results:
            try:
                validated_data = self._validate_and_convert_result(result)
                aggregated_data.append({
                    'source_file': result.source_file,
                    'status': result.status.value,
                    'processing_time': result.processing_time,
                    'confidence_scores': result.confidence_scores,
                    **validated_data
                })
                
                # Collect field statistics
                self._update_field_statistics(validated_data, field_statistics, result.source_file)
                
            except ValidationError as e:
                validation_errors[result.source_file].extend(e.args)
                self.logger.warning(f"Validation failed for {result.source_file}: {e}")
                
                # Add failed record with available data
                aggregated_data.append({
                    'source_file': result.source_file,
                    'status': ProcessingStatus.FAILED.value,
                    'processing_time': result.processing_time,
                    'validation_errors': list(e.args),
                    **{field.name: None for field in self.template.fields}
                })
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_statistics(
            aggregated_data, field_statistics, validation_errors
        )
        
        return {
            'aggregated_data': aggregated_data,
            'summary_statistics': summary_stats,
            'validation_errors': dict(validation_errors),
            'field_statistics': dict(field_statistics),
            'total_files': len(results),
            'successful_files': len([d for d in aggregated_data if d['status'] == ProcessingStatus.COMPLETED.value]),
            'failed_files': len(validation_errors)
        }
    
    def _validate_and_convert_result(self, result: ExtractionResult) -> Dict[str, Any]:
        """
        Validate and convert extraction result based on template schema.
        
        Args:
            result: ExtractionResult to validate
            
        Returns:
            Dict with validated and converted field values
            
        Raises:
            ValidationError: If validation fails
        """
        validated_data = {}
        errors = []
        
        # Check for required fields
        for field in self.template.fields:
            field_name = field.name
            raw_value = result.extracted_data.get(field_name)
            
            # Handle missing values
            if raw_value is None or raw_value == "":
                if not field.optional:
                    errors.append(f"Required field '{field_name}' is missing or empty")
                validated_data[field_name] = None
                continue
            
            # Convert and validate based on field type
            try:
                converted_value = self._convert_field_value(raw_value, field)
                validated_data[field_name] = converted_value
            except (ValueError, InvalidOperation) as e:
                errors.append(f"Field '{field_name}' conversion failed: {str(e)}")
                validated_data[field_name] = raw_value  # Keep original value
        
        # Check for unexpected fields
        for extracted_field in result.extracted_data:
            if extracted_field not in self._field_lookup:
                errors.append(f"Unexpected field '{extracted_field}' not in template schema")
        
        if errors:
            raise ValidationError(f"Validation errors for {result.source_file}: {'; '.join(errors)}")
        
        return validated_data
    
    def _convert_field_value(self, value: Any, field: ExtractionField) -> Any:
        """
        Convert field value to appropriate type based on field configuration.
        
        Args:
            value: Raw extracted value
            field: ExtractionField defining the target type
            
        Returns:
            Converted value
            
        Raises:
            ValueError: If conversion fails
        """
        if value is None or value == "":
            return None
        
        # Convert to string first for consistent processing
        str_value = str(value).strip()
        
        if field.type == FieldType.TEXT:
            return str_value
        
        elif field.type == FieldType.NUMBER:
            return self._convert_to_number(str_value, field.number_locale)
        
        elif field.type == FieldType.DATE:
            return self._convert_to_date(str_value)
        
        elif field.type == FieldType.CURRENCY:
            return self._convert_to_currency(str_value, field.number_locale)
        
        else:
            raise ValueError(f"Unsupported field type: {field.type}")
    
    def _convert_to_number(self, value: str, locale: str = 'vi-VN') -> Union[int, float]:
        """Convert string to number based on locale."""
        # Remove common thousand separators and handle Vietnamese format
        if locale == 'vi-VN':
            # Vietnamese: 1.234.567,89 (dots for thousands, comma for decimal)
            # Count dots and commas to determine format
            dot_count = value.count('.')
            comma_count = value.count(',')
            
            if comma_count == 1 and dot_count >= 1:
                # Format: 1.234.567,89 - dots are thousands, comma is decimal
                value = value.replace('.', '').replace(',', '.')
            elif dot_count >= 1 and comma_count == 0:
                # Format: 1.234.567 - dots are thousands separators, no decimal
                value = value.replace('.', '')
            # If no special separators, keep as is
        else:
            # English: 1,234,567.89 (commas for thousands, dot for decimal)
            value = value.replace(',', '')
        
        # Remove any remaining non-numeric characters except decimal point and minus
        value = re.sub(r'[^\d.-]', '', value)
        
        # Handle empty or invalid values
        if not value or value == '.':
            raise ValueError(f"Invalid number format: {value}")
        
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError as e:
            raise ValueError(f"Could not convert '{value}' to number: {str(e)}")
    
    def _convert_to_date(self, value: str) -> datetime:
        """Convert string to datetime object."""
        # Common Vietnamese date formats
        date_formats = [
            '%d/%m/%Y',     # 15/03/2024
            '%d-%m-%Y',     # 15-03-2024
            '%Y-%m-%d',     # 2024-03-15
            '%d/%m/%y',     # 15/03/24
            '%d.%m.%Y',     # 15.03.2024
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {value}")
    
    def _convert_to_currency(self, value: str, locale: str = 'vi-VN') -> Decimal:
        """Convert string to currency (Decimal) based on locale."""
        # Remove currency symbols
        currency_symbols = ['₫', 'VND', 'đ', '$', '€', '£', 'USD', 'EUR', 'GBP']
        for symbol in currency_symbols:
            value = value.replace(symbol, '')
        
        # Convert to number first
        numeric_value = self._convert_to_number(value, locale)
        return Decimal(str(numeric_value))
    
    def _update_field_statistics(self, validated_data: Dict[str, Any], 
                                field_stats: Dict[str, Dict], source_file: str):
        """Update field-level statistics with new data."""
        for field_name, value in validated_data.items():
            if field_name not in field_stats:
                field_stats[field_name] = {
                    'values': [],
                    'null_count': 0,
                    'total_count': 0,
                    'unique_values': set(),
                    'data_quality_score': 0.0
                }
            
            stats = field_stats[field_name]
            stats['total_count'] += 1
            
            if value is None:
                stats['null_count'] += 1
            else:
                stats['values'].append(value)
                stats['unique_values'].add(str(value))
    
    def _calculate_summary_statistics(self, aggregated_data: List[Dict], 
                                    field_stats: Dict[str, Dict],
                                    validation_errors: Dict[str, List]) -> Dict[str, Any]:
        """Calculate comprehensive summary statistics."""
        total_files = len(aggregated_data)
        successful_files = len([d for d in aggregated_data if d['status'] == ProcessingStatus.COMPLETED.value])
        
        # Overall processing statistics
        processing_times = [d['processing_time'] for d in aggregated_data if d['processing_time'] > 0]
        
        summary = {
            'processing_summary': {
                'total_files': total_files,
                'successful_files': successful_files,
                'failed_files': len(validation_errors),
                'success_rate': (successful_files / total_files * 100) if total_files > 0 else 0,
                'total_processing_time': sum(processing_times),
                'average_processing_time': statistics.mean(processing_times) if processing_times else 0,
                'median_processing_time': statistics.median(processing_times) if processing_times else 0
            },
            'data_quality_summary': {},
            'field_summaries': {}
        }
        
        # Calculate field-level statistics
        for field_name, stats in field_stats.items():
            field_summary = self._calculate_field_summary(field_name, stats)
            summary['field_summaries'][field_name] = field_summary
        
        # Overall data quality score
        field_quality_scores = [fs.get('data_quality_score', 0) for fs in summary['field_summaries'].values()]
        summary['data_quality_summary'] = {
            'overall_quality_score': statistics.mean(field_quality_scores) if field_quality_scores else 0,
            'fields_with_issues': len([fs for fs in summary['field_summaries'].values() 
                                     if fs.get('data_quality_score', 100) < 80]),
            'completeness_rate': (sum(stats['total_count'] - stats['null_count'] 
                                    for stats in field_stats.values()) / 
                                sum(stats['total_count'] for stats in field_stats.values()) * 100) 
                               if field_stats else 0
        }
        
        return summary
    
    def _calculate_field_summary(self, field_name: str, stats: Dict) -> Dict[str, Any]:
        """Calculate summary statistics for a specific field."""
        field_config = self._field_lookup.get(field_name)
        values = stats['values']
        total_count = stats['total_count']
        null_count = stats['null_count']
        
        summary = {
            'field_type': field_config.type.value if field_config else 'unknown',
            'total_count': total_count,
            'null_count': null_count,
            'completeness_rate': ((total_count - null_count) / total_count * 100) if total_count > 0 else 0,
            'unique_count': len(stats['unique_values']),
            'data_quality_score': 0.0
        }
        
        # Calculate data quality score
        completeness_score = summary['completeness_rate']
        uniqueness_score = min(summary['unique_count'] / max(len(values), 1) * 100, 100)
        summary['data_quality_score'] = (completeness_score + uniqueness_score) / 2
        
        # Type-specific statistics
        if values and field_config:
            if field_config.type in [FieldType.NUMBER, FieldType.CURRENCY]:
                numeric_values = [v for v in values if isinstance(v, (int, float, Decimal))]
                if numeric_values:
                    summary.update({
                        'min_value': min(numeric_values),
                        'max_value': max(numeric_values),
                        'mean_value': statistics.mean(numeric_values),
                        'median_value': statistics.median(numeric_values),
                        'std_deviation': statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
                    })
            
            elif field_config.type == FieldType.TEXT:
                text_lengths = [len(str(v)) for v in values]
                if text_lengths:
                    summary.update({
                        'min_length': min(text_lengths),
                        'max_length': max(text_lengths),
                        'avg_length': statistics.mean(text_lengths)
                    })
            
            elif field_config.type == FieldType.DATE:
                date_values = [v for v in values if isinstance(v, datetime)]
                if date_values:
                    summary.update({
                        'earliest_date': min(date_values).isoformat(),
                        'latest_date': max(date_values).isoformat(),
                        'date_range_days': (max(date_values) - min(date_values)).days
                    })
        
        return summary
    
    def validate_session_data(self, session: ProcessingSession) -> Dict[str, Any]:
        """
        Validate and aggregate data for a complete processing session.
        
        Args:
            session: ProcessingSession to validate
            
        Returns:
            Dict containing validation results and aggregated data
        """
        self.logger.info(f"Validating session data for template: {session.template.name}")
        
        # Ensure template matches
        if session.template.name != self.template.name:
            self.logger.warning(f"Template mismatch: expected {self.template.name}, got {session.template.name}")
        
        # Aggregate results
        aggregation_result = self.aggregate_results(session.results)
        
        # Update session summary stats
        session.summary_stats = aggregation_result['summary_statistics']
        
        return aggregation_result
    
    def get_data_quality_report(self, aggregation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive data quality report.
        
        Args:
            aggregation_result: Result from aggregate_results method
            
        Returns:
            Dict containing detailed data quality analysis
        """
        summary_stats = aggregation_result['summary_statistics']
        validation_errors = aggregation_result['validation_errors']
        
        # Identify common error patterns
        error_patterns = Counter()
        for file_errors in validation_errors.values():
            for error in file_errors:
                # Extract error type patterns
                if "missing" in error.lower():
                    error_patterns["missing_required_fields"] += 1
                elif "conversion failed" in error.lower():
                    error_patterns["type_conversion_errors"] += 1
                elif "unexpected field" in error.lower():
                    error_patterns["schema_mismatches"] += 1
        
        # Identify fields with quality issues
        problematic_fields = []
        for field_name, field_summary in summary_stats['field_summaries'].items():
            if field_summary['data_quality_score'] < 80:
                problematic_fields.append({
                    'field_name': field_name,
                    'quality_score': field_summary['data_quality_score'],
                    'completeness_rate': field_summary['completeness_rate'],
                    'issues': []
                })
                
                # Identify specific issues
                if field_summary['completeness_rate'] < 90:
                    problematic_fields[-1]['issues'].append("Low completeness rate")
                if field_summary['unique_count'] < 2:
                    problematic_fields[-1]['issues'].append("Low data diversity")
        
        return {
            'overall_quality_grade': self._get_quality_grade(summary_stats['data_quality_summary']['overall_quality_score']),
            'completeness_rate': summary_stats['data_quality_summary']['completeness_rate'],
            'error_summary': {
                'total_errors': sum(len(errors) for errors in validation_errors.values()),
                'files_with_errors': len(validation_errors),
                'common_error_patterns': dict(error_patterns.most_common(5))
            },
            'problematic_fields': problematic_fields,
            'recommendations': self._generate_quality_recommendations(summary_stats, error_patterns)
        }
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _generate_quality_recommendations(self, summary_stats: Dict, error_patterns: Counter) -> List[str]:
        """Generate actionable recommendations for improving data quality."""
        recommendations = []
        
        overall_score = summary_stats['data_quality_summary']['overall_quality_score']
        
        if overall_score < 80:
            recommendations.append("Consider reviewing document quality and OCR settings")
        
        if error_patterns.get("missing_required_fields", 0) > 2:
            recommendations.append("Review extraction prompts for better field detection")
        
        if error_patterns.get("type_conversion_errors", 0) > 2:
            recommendations.append("Verify field type configurations match document formats")
        
        if summary_stats['data_quality_summary']['completeness_rate'] < 85:
            recommendations.append("Consider improving document preprocessing or extraction templates")
        
        if summary_stats['processing_summary']['success_rate'] < 90:
            recommendations.append("Review failed files for common patterns and adjust processing parameters")
        
        return recommendations