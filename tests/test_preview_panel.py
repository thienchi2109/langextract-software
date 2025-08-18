"""
GUI tests for the PreviewPanel functionality.

Tests:
- PreviewPanel widget creation and initialization
- File preview with extraction results
- Summary preview with session data
- Confidence indicators and data quality display
- Theme integration and styling
"""

import sys
import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

# Add project root to path for imports
sys.path.insert(0, '..')

from gui.preview_panel import (
    PreviewPanel, FilePreviewWidget, SummaryPreviewWidget, 
    ConfidenceIndicator, DataFieldWidget
)
from core.models import (
    ExtractionResult, ProcessingSession, ExtractionTemplate, ExtractionField,
    ProcessingStatus, FieldType
)


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    if not QApplication.instance():
        return QApplication(sys.argv)
    return QApplication.instance()


@pytest.fixture
def mock_theme_manager():
    """Mock theme manager for testing."""
    with patch('gui.preview_panel.get_theme_manager') as mock:
        theme_manager = Mock()
        theme_manager.create_icon.return_value = Mock()
        mock.return_value = theme_manager
        yield theme_manager


@pytest.fixture
def sample_extraction_result():
    """Create sample extraction result for testing."""
    return ExtractionResult(
        source_file="test_document.pdf",
        extracted_data={
            "company_name": "Test Company Ltd.",
            "revenue": 1000000.50,
            "quarter": "Q2 2024",
            "contact_email": "test@company.com"
        },
        confidence_scores={
            "company_name": 0.95,
            "revenue": 0.82,
            "quarter": 0.90,
            "contact_email": 0.45
        },
        processing_time=1.5,
        errors=[],
        status=ProcessingStatus.COMPLETED
    )


@pytest.fixture
def sample_template_fields():
    """Create sample template fields for testing."""
    return [
        {"name": "company_name", "type": "text", "description": "Company name"},
        {"name": "revenue", "type": "currency", "description": "Total revenue"},
        {"name": "quarter", "type": "text", "description": "Reporting quarter"},
        {"name": "contact_email", "type": "text", "description": "Contact email"}
    ]


@pytest.fixture
def sample_session(sample_extraction_result):
    """Create sample processing session for testing."""
    template = ExtractionTemplate(
        name="test_template",
        prompt_description="Test extraction template",
        fields=[
            ExtractionField("company_name", FieldType.TEXT, "Company name"),
            ExtractionField("revenue", FieldType.CURRENCY, "Total revenue"),
            ExtractionField("quarter", FieldType.TEXT, "Reporting quarter"),
            ExtractionField("contact_email", FieldType.TEXT, "Contact email")
        ]
    )
    
    session = ProcessingSession(
        template=template,
        files=["test_document.pdf", "another_doc.docx"],
        results=[sample_extraction_result]
    )
    
    return session


class TestConfidenceIndicator:
    """Test ConfidenceIndicator widget."""
    
    def test_confidence_indicator_creation(self, app, mock_theme_manager):
        """Test confidence indicator widget creation."""
        indicator = ConfidenceIndicator(confidence=0.8)
        
        assert indicator.confidence == 0.8
        assert indicator.toolTip() == "Confidence: 80.0%"
        assert indicator.width() == 100
        assert indicator.height() == 20
    
    def test_confidence_indicator_update(self, app, mock_theme_manager):
        """Test confidence indicator update."""
        indicator = ConfidenceIndicator(confidence=0.5)
        
        # Update confidence
        indicator.set_confidence(0.9)
        
        assert indicator.confidence == 0.9
        assert indicator.toolTip() == "Confidence: 90.0%"
    
    def test_confidence_indicator_painting(self, app, mock_theme_manager):
        """Test confidence indicator painting (basic test)."""
        indicator = ConfidenceIndicator(confidence=0.6)
        indicator.show()
        
        # Trigger paint event
        indicator.repaint()
        
        # If no exception is raised, painting works
        assert True


class TestDataFieldWidget:
    """Test DataFieldWidget."""
    
    def test_data_field_widget_creation(self, app, mock_theme_manager):
        """Test data field widget creation."""
        widget = DataFieldWidget(
            field_name="company_name",
            field_type=FieldType.TEXT,
            value="Test Company",
            confidence=0.85
        )
        
        assert widget.field_name == "company_name"
        assert widget.field_type == FieldType.TEXT
        assert widget.value == "Test Company"
        assert widget.confidence == 0.85
        assert not widget.is_missing
    
    def test_data_field_widget_missing_value(self, app, mock_theme_manager):
        """Test data field widget with missing value."""
        widget = DataFieldWidget(
            field_name="missing_field",
            field_type=FieldType.TEXT,
            value=None,
            confidence=0.0,
            is_missing=True
        )
        
        assert widget.is_missing
        assert "Not found" in widget.value_label.text()
    
    def test_data_field_widget_currency_formatting(self, app, mock_theme_manager):
        """Test currency field formatting."""
        widget = DataFieldWidget(
            field_name="revenue",
            field_type=FieldType.CURRENCY,
            value=1234567.89,
            confidence=0.9
        )
        
        widget.update_display()
        assert "$1,234,567.89" in widget.value_label.text()
    
    def test_data_field_widget_number_formatting(self, app, mock_theme_manager):
        """Test number field formatting."""
        widget = DataFieldWidget(
            field_name="count",
            field_type=FieldType.NUMBER,
            value=1234,
            confidence=0.8
        )
        
        widget.update_display()
        assert "1,234" in widget.value_label.text()


class TestFilePreviewWidget:
    """Test FilePreviewWidget."""
    
    def test_file_preview_widget_creation(self, app, mock_theme_manager):
        """Test file preview widget creation."""
        widget = FilePreviewWidget()
        
        assert widget.current_result is None
        assert widget.content_widget is not None
        assert widget.file_info_group is not None
        assert widget.data_group is not None
    
    def test_file_preview_update(self, app, mock_theme_manager, sample_extraction_result, sample_template_fields):
        """Test file preview update with extraction result."""
        widget = FilePreviewWidget()
        
        widget.update_preview(sample_extraction_result, sample_template_fields)
        
        assert widget.current_result == sample_extraction_result
        assert "test_document.pdf" in widget.file_name_label.text()
        assert "✓" in widget.status_label.text()  # Completed status icon
        assert "1.5s" in widget.processing_time_label.text()
    
    def test_file_preview_empty_state(self, app, mock_theme_manager):
        """Test file preview empty state."""
        widget = FilePreviewWidget()
        
        widget.show_empty_state()
        
        assert "No file selected" in widget.file_name_label.text()
        assert "Select a file" in widget.status_label.text()
    
    def test_file_preview_error_state(self, app, mock_theme_manager, sample_template_fields):
        """Test file preview with failed processing."""
        failed_result = ExtractionResult(
            source_file="failed_doc.pdf",
            extracted_data={},
            confidence_scores={},
            processing_time=0.0,
            errors=["OCR failed", "File corrupted"],
            status=ProcessingStatus.FAILED
        )
        
        widget = FilePreviewWidget()
        widget.update_preview(failed_result, sample_template_fields)
        
        assert "✗" in widget.status_label.text()  # Failed status icon


class TestSummaryPreviewWidget:
    """Test SummaryPreviewWidget."""
    
    def test_summary_preview_widget_creation(self, app, mock_theme_manager):
        """Test summary preview widget creation."""
        widget = SummaryPreviewWidget()
        
        assert widget.current_session is None
        assert widget.stats_group is not None
        assert widget.quality_group is not None
        assert widget.field_stats_group is not None
    
    def test_summary_preview_update(self, app, mock_theme_manager, sample_session):
        """Test summary preview update with session data."""
        widget = SummaryPreviewWidget()
        
        widget.update_summary(sample_session)
        
        assert widget.current_session == sample_session
        assert "2" in widget.total_files_label.text()  # 2 files in session
        assert "1" in widget.completed_files_label.text()  # 1 completed
        assert "0" in widget.failed_files_label.text()  # 0 failed
    
    def test_summary_preview_empty_state(self, app, mock_theme_manager):
        """Test summary preview empty state."""
        widget = SummaryPreviewWidget()
        
        widget.show_empty_state()
        
        # Should show empty state message
        assert widget.current_session is None


class TestPreviewPanel:
    """Test main PreviewPanel widget."""
    
    def test_preview_panel_creation(self, app, mock_theme_manager):
        """Test preview panel creation."""
        panel = PreviewPanel()
        
        assert panel.tab_widget is not None
        assert panel.file_preview is not None
        assert panel.summary_preview is not None
        assert panel.current_session is None
        
        # Should have 2 tabs
        assert panel.tab_widget.count() == 2
        assert panel.tab_widget.tabText(0) == "File Preview"
        assert panel.tab_widget.tabText(1) == "Summary"
    
    def test_preview_panel_file_update(self, app, mock_theme_manager, sample_extraction_result, sample_template_fields):
        """Test preview panel file update."""
        panel = PreviewPanel()
        
        # Connect signal to track updates
        update_count = [0]
        def on_update():
            update_count[0] += 1
        panel.preview_updated.connect(on_update)
        
        panel.update_file_preview(sample_extraction_result, sample_template_fields)
        
        assert update_count[0] == 1  # Signal should be emitted
    
    def test_preview_panel_summary_update(self, app, mock_theme_manager, sample_session):
        """Test preview panel summary update."""
        panel = PreviewPanel()
        
        # Connect signal to track updates
        update_count = [0]
        def on_update():
            update_count[0] += 1
        panel.preview_updated.connect(on_update)
        
        panel.update_summary_preview(sample_session)
        
        assert panel.current_session == sample_session
        assert update_count[0] == 1  # Signal should be emitted
    
    def test_preview_panel_clear(self, app, mock_theme_manager):
        """Test preview panel clear functionality."""
        panel = PreviewPanel()
        
        # Connect signal to track updates
        update_count = [0]
        def on_update():
            update_count[0] += 1
        panel.preview_updated.connect(on_update)
        
        panel.clear_preview()
        
        assert panel.current_session is None
        assert update_count[0] == 1  # Signal should be emitted
    
    def test_preview_panel_tab_management(self, app, mock_theme_manager):
        """Test preview panel tab management."""
        panel = PreviewPanel()
        
        # Test getting current tab
        current_tab = panel.get_current_tab()
        assert current_tab in ["File Preview", "Summary"]
        
        # Test setting active tab
        panel.set_active_tab("Summary")
        assert panel.get_current_tab() == "Summary"
        
        panel.set_active_tab("File Preview")
        assert panel.get_current_tab() == "File Preview"


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])
