"""
Excel export functionality for extraction results.

This module provides the ExcelExporter class that generates professional Excel reports
with Data and Summary sheets from aggregated extraction results.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import pandas as pd
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell

from .models import ExtractionTemplate, ExtractionField, FieldType
from .exceptions import LangExtractorError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class ExcelExporter:
    """
    Excel export functionality for extraction results.
    
    Generates professional Excel reports with:
    - Data sheet with schema-ordered columns and metadata
    - Summary sheet with processing statistics and quality analysis
    - Professional formatting with frozen headers and auto-fit columns
    - Vietnamese locale support for numbers and dates
    """
    
    def __init__(self, template: ExtractionTemplate):
        """
        Initialize Excel exporter with extraction template.
        
        Args:
            template: ExtractionTemplate defining the schema for export
        """
        self.template = template
        self.logger = logger
        
        # Excel formatting options
        self.date_format = 'dd/mm/yyyy'
        self.number_format = '#,##0.00'
        self.currency_format = '#,##0" ₫"'
        self.percentage_format = '0.00%'
        
        self.logger.info(f"ExcelExporter initialized for template: {template.name}")
    
    def export_results(
        self, 
        aggregation_result: Dict[str, Any], 
        output_path: Union[str, Path],
        include_charts: bool = True,
        include_validation: bool = True
    ) -> str:
        """
        Export aggregation results to Excel file.
        
        Args:
            aggregation_result: Result from Aggregator.aggregate_results()
            output_path: Path for output Excel file
            include_charts: Whether to include charts in Summary sheet
            include_validation: Whether to include data validation
            
        Returns:
            str: Path to generated Excel file
            
        Raises:
            LangExtractorError: If export fails
        """
        try:
            output_path = Path(output_path)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Exporting results to: {output_path}")
            
            # Create Excel workbook
            with pd.ExcelWriter(
                output_path,
                engine='xlsxwriter'
            ) as writer:
                
                # Create Data sheet
                self._create_data_sheet(aggregation_result, writer)
                
                # Create Summary sheet
                self._create_summary_sheet(aggregation_result, writer, include_charts)
                
                # Apply formatting
                self._apply_formatting(writer, include_validation)
            
            self.logger.info(f"Excel export completed: {output_path}")
            return str(output_path)
            
        except Exception as e:
            error_msg = f"Excel export failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise LangExtractorError(
                error_msg,
                category=ErrorCategory.EXPORT_ERROR,
                severity=ErrorSeverity.HIGH
            )
    
    def _create_data_sheet(self, aggregation_result: Dict[str, Any], writer: pd.ExcelWriter):
        """
        Create Data sheet with extraction results.
        
        Args:
            aggregation_result: Aggregation results from Aggregator
            writer: Excel writer instance
        """
        self.logger.debug("Creating Data sheet")
        
        # Get aggregated data
        aggregated_data = aggregation_result.get('aggregated_data', [])
        
        if not aggregated_data:
            # Create empty sheet with headers
            df = pd.DataFrame(columns=self._get_data_columns())
        else:
            # Convert to DataFrame
            df = pd.DataFrame(aggregated_data)
            
            # Reorder columns according to template schema
            df = self._reorder_data_columns(df)
            
            # Apply data type conversions
            df = self._apply_data_types(df)
        
        # Write to Excel
        df.to_excel(writer, sheet_name='Data', index=False, freeze_panes=(1, 0))
        
        self.logger.debug(f"Data sheet created with {len(df)} rows")
    
    def _create_summary_sheet(
        self, 
        aggregation_result: Dict[str, Any], 
        writer: pd.ExcelWriter,
        include_charts: bool = True
    ):
        """
        Create Summary sheet with statistics and analysis.
        
        Args:
            aggregation_result: Aggregation results from Aggregator
            writer: Excel writer instance
            include_charts: Whether to include charts
        """
        self.logger.debug("Creating Summary sheet")
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = workbook.add_worksheet('Summary')
        
        # Current row tracker
        current_row = 0
        
        # 1. Processing Summary
        current_row = self._add_processing_summary(
            worksheet, aggregation_result, current_row
        )
        current_row += 2  # Add spacing
        
        # 2. Data Quality Summary
        current_row = self._add_quality_summary(
            worksheet, aggregation_result, current_row
        )
        current_row += 2  # Add spacing
        
        # 3. Field Statistics
        current_row = self._add_field_statistics(
            worksheet, aggregation_result, current_row
        )
        current_row += 2  # Add spacing
        
        # 4. Error Analysis
        current_row = self._add_error_analysis(
            worksheet, aggregation_result, current_row
        )
        
        # 5. Add charts if requested
        if include_charts:
            self._add_summary_charts(worksheet, workbook, aggregation_result)
        
        self.logger.debug("Summary sheet created")
    
    def _get_data_columns(self) -> List[str]:
        """Get ordered list of columns for Data sheet."""
        # Metadata columns first
        columns = ['source_file', 'status', 'processing_time']
        
        # Template fields in order
        for field in self.template.fields:
            columns.append(field.name)
        
        # Confidence scores last
        columns.append('confidence_scores')
        
        return columns
    
    def _reorder_data_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Reorder DataFrame columns according to template schema."""
        desired_columns = self._get_data_columns()
        
        # Keep only columns that exist in the DataFrame
        existing_columns = [col for col in desired_columns if col in df.columns]
        
        # Add any extra columns at the end
        extra_columns = [col for col in df.columns if col not in existing_columns]
        final_columns = existing_columns + extra_columns
        
        return df[final_columns]
    
    def _apply_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply appropriate data types to DataFrame columns."""
        for field in self.template.fields:
            if field.name not in df.columns:
                continue
            
            try:
                if field.type == FieldType.NUMBER:
                    df[field.name] = pd.to_numeric(df[field.name], errors='coerce')
                elif field.type == FieldType.CURRENCY:
                    # Convert currency to numeric
                    df[field.name] = pd.to_numeric(df[field.name], errors='coerce')
                elif field.type == FieldType.DATE:
                    df[field.name] = pd.to_datetime(df[field.name], errors='coerce')
                # TEXT fields remain as-is
                
            except Exception as e:
                self.logger.warning(f"Failed to convert column {field.name}: {e}")
        
        return df
    
    def _apply_formatting(self, writer: pd.ExcelWriter, include_validation: bool = True):
        """
        Apply Excel formatting to sheets.
        
        Args:
            writer: Excel writer instance
            include_validation: Whether to include data validation
        """
        workbook = writer.book
        
        # Define formats
        formats = self._create_formats(workbook)
        
        # Format Data sheet
        if 'Data' in writer.sheets:
            self._format_data_sheet(writer.sheets['Data'], formats, include_validation)
        
        # Format Summary sheet
        if 'Summary' in writer.sheets:
            self._format_summary_sheet(writer.sheets['Summary'], formats)
    
    def _create_formats(self, workbook) -> Dict[str, Any]:
        """Create Excel formats for styling."""
        return {
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            }),
            'date': workbook.add_format({
                'num_format': self.date_format,
                'border': 1
            }),
            'number': workbook.add_format({
                'num_format': self.number_format,
                'border': 1
            }),
            'currency': workbook.add_format({
                'num_format': self.currency_format,
                'border': 1
            }),
            'percentage': workbook.add_format({
                'num_format': self.percentage_format,
                'border': 1
            }),
            'text': workbook.add_format({
                'border': 1,
                'text_wrap': True
            }),
            'summary_header': workbook.add_format({
                'bold': True,
                'font_size': 14,
                'bg_color': '#D9E1F2',
                'border': 1
            }),
            'summary_label': workbook.add_format({
                'bold': True,
                'border': 1
            }),
            'summary_value': workbook.add_format({
                'border': 1
            })
        }
    
    def _format_data_sheet(self, worksheet, formats: Dict[str, Any], include_validation: bool):
        """Format the Data sheet."""
        # Set column widths and formats
        for col_num, field in enumerate(self.template.fields):
            col_letter = chr(ord('A') + col_num + 3)  # Offset for metadata columns
            
            if field.type == FieldType.DATE:
                worksheet.set_column(f'{col_letter}:{col_letter}', 12, formats['date'])
            elif field.type == FieldType.NUMBER:
                worksheet.set_column(f'{col_letter}:{col_letter}', 15, formats['number'])
            elif field.type == FieldType.CURRENCY:
                worksheet.set_column(f'{col_letter}:{col_letter}', 18, formats['currency'])
            else:  # TEXT
                worksheet.set_column(f'{col_letter}:{col_letter}', 20, formats['text'])
        
        # Format metadata columns
        worksheet.set_column('A:A', 25, formats['text'])  # source_file
        worksheet.set_column('B:B', 12, formats['text'])  # status
        worksheet.set_column('C:C', 15, formats['number'])  # processing_time
        
        # Apply header format to first row
        last_col = chr(ord('A') + len(self._get_data_columns()) - 1)
        worksheet.conditional_format(f'A1:{last_col}1', {
            'type': 'no_errors',
            'format': formats['header']
        })
    
    def _format_summary_sheet(self, worksheet, formats: Dict[str, Any]):
        """Format the Summary sheet."""
        # Set default column widths
        worksheet.set_column('A:A', 25)  # Labels
        worksheet.set_column('B:B', 20)  # Values
        worksheet.set_column('C:Z', 15)  # Additional columns

    def _add_processing_summary(
        self,
        worksheet,
        aggregation_result: Dict[str, Any],
        start_row: int
    ) -> int:
        """
        Add processing summary section to Summary sheet.

        Args:
            worksheet: Excel worksheet
            aggregation_result: Aggregation results
            start_row: Starting row number

        Returns:
            int: Next available row number
        """
        summary_stats = aggregation_result.get('summary_statistics', {})
        processing_summary = summary_stats.get('processing_summary', {})

        # Section header
        worksheet.write(start_row, 0, 'Processing Summary')
        worksheet.write(start_row, 1, '')
        current_row = start_row + 1

        # Processing metrics
        metrics = [
            ('Total Files', aggregation_result.get('total_files', 0)),
            ('Successful Files', aggregation_result.get('successful_files', 0)),
            ('Failed Files', aggregation_result.get('failed_files', 0)),
            ('Success Rate', f"{processing_summary.get('success_rate', 0):.1f}%"),
            ('Total Processing Time', f"{processing_summary.get('total_processing_time', 0):.2f}s"),
            ('Average Processing Time', f"{processing_summary.get('average_processing_time', 0):.2f}s"),
            ('Median Processing Time', f"{processing_summary.get('median_processing_time', 0):.2f}s")
        ]

        for label, value in metrics:
            worksheet.write(current_row, 0, label)
            worksheet.write(current_row, 1, value)
            current_row += 1

        return current_row

    def _add_quality_summary(
        self,
        worksheet,
        aggregation_result: Dict[str, Any],
        start_row: int
    ) -> int:
        """
        Add data quality summary section to Summary sheet.

        Args:
            worksheet: Excel worksheet
            aggregation_result: Aggregation results
            start_row: Starting row number

        Returns:
            int: Next available row number
        """
        summary_stats = aggregation_result.get('summary_statistics', {})
        quality_summary = summary_stats.get('data_quality_summary', {})

        # Section header
        worksheet.write(start_row, 0, 'Data Quality Summary')
        worksheet.write(start_row, 1, '')
        current_row = start_row + 1

        # Quality metrics
        metrics = [
            ('Overall Quality Score', f"{quality_summary.get('overall_quality_score', 0):.1f}"),
            ('Completeness Rate', f"{quality_summary.get('completeness_rate', 0):.1f}%"),
            ('Data Consistency', f"{quality_summary.get('consistency_score', 0):.1f}"),
            ('Error Rate', f"{quality_summary.get('error_rate', 0):.1f}%")
        ]

        for label, value in metrics:
            worksheet.write(current_row, 0, label)
            worksheet.write(current_row, 1, value)
            current_row += 1

        return current_row

    def _add_field_statistics(
        self,
        worksheet,
        aggregation_result: Dict[str, Any],
        start_row: int
    ) -> int:
        """
        Add field statistics section to Summary sheet.

        Args:
            worksheet: Excel worksheet
            aggregation_result: Aggregation results
            start_row: Starting row number

        Returns:
            int: Next available row number
        """
        summary_stats = aggregation_result.get('summary_statistics', {})
        field_summaries = summary_stats.get('field_summaries', {})

        # Section header
        worksheet.write(start_row, 0, 'Field Statistics')
        current_row = start_row + 1

        # Table headers
        headers = ['Field Name', 'Type', 'Completeness', 'Unique Values', 'Min', 'Max', 'Mean']
        for col, header in enumerate(headers):
            worksheet.write(current_row, col, header)
        current_row += 1

        # Field statistics
        for field in self.template.fields:
            field_name = field.name
            field_summary = field_summaries.get(field_name, {})

            row_data = [
                field_name,
                field.type.value,
                f"{field_summary.get('completeness_rate', 0):.1f}%",
                field_summary.get('unique_count', 0),
                self._format_stat_value(field_summary.get('min_value'), field.type),
                self._format_stat_value(field_summary.get('max_value'), field.type),
                self._format_stat_value(field_summary.get('mean_value'), field.type)
            ]

            for col, value in enumerate(row_data):
                worksheet.write(current_row, col, value)
            current_row += 1

        return current_row

    def _add_error_analysis(
        self,
        worksheet,
        aggregation_result: Dict[str, Any],
        start_row: int
    ) -> int:
        """
        Add error analysis section to Summary sheet.

        Args:
            worksheet: Excel worksheet
            aggregation_result: Aggregation results
            start_row: Starting row number

        Returns:
            int: Next available row number
        """
        validation_errors = aggregation_result.get('validation_errors', {})

        # Section header
        worksheet.write(start_row, 0, 'Error Analysis')
        current_row = start_row + 1

        if not validation_errors:
            worksheet.write(current_row, 0, 'No validation errors found')
            return current_row + 1

        # Error summary
        total_errors = sum(len(errors) for errors in validation_errors.values())
        worksheet.write(current_row, 0, f'Total Errors: {total_errors}')
        current_row += 1

        worksheet.write(current_row, 0, f'Files with Errors: {len(validation_errors)}')
        current_row += 2

        # Error details by file
        worksheet.write(current_row, 0, 'File')
        worksheet.write(current_row, 1, 'Error Count')
        worksheet.write(current_row, 2, 'Error Details')
        current_row += 1

        for file_name, errors in validation_errors.items():
            worksheet.write(current_row, 0, file_name)
            worksheet.write(current_row, 1, len(errors))
            worksheet.write(current_row, 2, '; '.join(errors[:3]))  # Show first 3 errors
            current_row += 1

        return current_row

    def _add_summary_charts(self, worksheet, workbook, aggregation_result: Dict[str, Any]):
        """
        Add charts to Summary sheet.

        Args:
            worksheet: Excel worksheet
            workbook: Excel workbook
            aggregation_result: Aggregation results
        """

        # Success Rate Pie Chart
        successful_files = aggregation_result.get('successful_files', 0)
        failed_files = aggregation_result.get('failed_files', 0)

        if successful_files > 0 or failed_files > 0:
            # Write chart data to worksheet first
            chart_data_row = 25  # Start after summary tables
            worksheet.write(chart_data_row, 0, 'Category')
            worksheet.write(chart_data_row, 1, 'Count')
            worksheet.write(chart_data_row + 1, 0, 'Successful')
            worksheet.write(chart_data_row + 1, 1, successful_files)
            worksheet.write(chart_data_row + 2, 0, 'Failed')
            worksheet.write(chart_data_row + 2, 1, failed_files)

            # Create pie chart
            chart = workbook.add_chart({'type': 'pie'})
            chart.add_series({
                'categories': f'Summary!$A${chart_data_row + 2}:$A${chart_data_row + 3}',
                'values': f'Summary!$B${chart_data_row + 2}:$B${chart_data_row + 3}',
                'data_labels': {'percentage': True}
            })

            chart.set_title({'name': 'Processing Success Rate'})
            chart.set_size({'width': 400, 'height': 300})

            # Insert chart
            worksheet.insert_chart('E2', chart)

    def _format_stat_value(self, value: Any, field_type: FieldType) -> str:
        """
        Format statistical value for display.

        Args:
            value: Statistical value
            field_type: Field type for formatting

        Returns:
            str: Formatted value
        """
        if value is None:
            return 'N/A'

        try:
            if field_type == FieldType.NUMBER:
                return f"{float(value):,.2f}"
            elif field_type == FieldType.CURRENCY:
                return f"{float(value):,.0f} ₫"
            elif field_type == FieldType.DATE:
                if isinstance(value, str):
                    return value
                return value.strftime('%d/%m/%Y') if hasattr(value, 'strftime') else str(value)
            else:  # TEXT
                return str(value)[:50]  # Truncate long text
        except (ValueError, TypeError):
            return str(value)

    def get_export_filename(self, base_name: str = None) -> str:
        """
        Generate export filename with timestamp.

        Args:
            base_name: Base name for the file

        Returns:
            str: Generated filename
        """
        if base_name is None:
            base_name = self.template.name.replace(' ', '_').lower()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_name}_export_{timestamp}.xlsx"

    def validate_aggregation_result(self, aggregation_result: Dict[str, Any]) -> bool:
        """
        Validate aggregation result structure.

        Args:
            aggregation_result: Result to validate

        Returns:
            bool: True if valid, False otherwise
        """
        required_keys = ['aggregated_data', 'summary_statistics', 'total_files']

        for key in required_keys:
            if key not in aggregation_result:
                self.logger.error(f"Missing required key in aggregation result: {key}")
                return False

        return True
