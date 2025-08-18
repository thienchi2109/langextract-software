"""
Main window for LangExtractor GUI with modern design and drag-drop support.

Features:
- Modern light/dark theme support
- Drag-and-drop file interface
- File list with status indicators
- Progress tracking and cancellation
- Menu structure and toolbar
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import Qt, Signal, QTimer, QMimeData, QUrl
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QProgressBar, QStatusBar, QMenuBar, QMenu, QToolBar, QLabel,
    QFrame, QSplitter, QMessageBox, QFileDialog, QApplication
)
from PySide6.QtGui import QAction, QIcon, QDragEnterEvent, QDropEvent, QDragMoveEvent, QPainter, QPen
from gui.theme import get_theme_manager
from gui.preview_panel import PreviewPanel

logger = logging.getLogger(__name__)


class DropOverlay(QWidget):
    """
    Semi-transparent overlay widget for drag-and-drop visual feedback.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.hide()
    
    def paintEvent(self, event):
        """Paint the drop overlay with dashed border and hint text."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Semi-transparent background
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        
        # Dashed border
        pen = QPen(Qt.blue, 3, Qt.DashLine)
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect().adjusted(10, 10, -10, -10), 12, 12)
        
        # Hint text
        painter.setPen(Qt.blue)
        painter.setFont(self.font())
        text = "Thả file vào đây..."
        painter.drawText(self.rect(), Qt.AlignCenter, text)
    
    def show_overlay(self):
        """Show the overlay."""
        if self.parent():
            self.resize(self.parent().size())
            self.move(0, 0)
        self.show()
        self.raise_()
    
    def hide_overlay(self):
        """Hide the overlay."""
        self.hide()


class FileListWidget(QListWidget):
    """
    Enhanced list widget with file icons and status indicators.
    """
    
    files_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.supported_formats = {'.pdf', '.docx', '.xlsx', '.xls'}
        self.setAlternatingRowColors(True)
        self.setDragDropMode(QListWidget.NoDragDrop)  # Handle drag-drop in main window
    
    def add_file(self, file_path: str) -> bool:
        """
        Add file to the list with appropriate icon.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file was added, False if duplicate or unsupported
        """
        path = Path(file_path)
        
        # Check if file already exists
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == str(path):
                return False  # Duplicate
        
        # Check if format is supported
        if path.suffix.lower() not in self.supported_formats:
            return False  # Unsupported format
        
        # Create list item
        item = QListWidgetItem()
        item.setText(path.name)
        item.setData(Qt.UserRole, str(path))
        
        # Set icon based on file extension
        icon_name = self.get_icon_name(path.suffix.lower())
        icon = self.theme_manager.create_icon(icon_name)
        item.setIcon(icon)
        
        # Set tooltip with full path
        item.setToolTip(str(path))
        
        self.addItem(item)
        self.files_changed.emit()
        
        logger.info(f"Added file to list: {path.name}")
        return True
    
    def get_icon_name(self, extension: str) -> str:
        """Get icon name for file extension."""
        icon_map = {
            '.pdf': 'file-pdf',
            '.docx': 'file-docx',
            '.xlsx': 'file-xlsx',
            '.xls': 'file-xlsx'
        }
        return icon_map.get(extension, 'file-pdf')
    
    def remove_selected_files(self):
        """Remove selected files from the list."""
        for item in self.selectedItems():
            row = self.row(item)
            self.takeItem(row)
        self.files_changed.emit()
    
    def clear_all_files(self):
        """Clear all files from the list."""
        self.clear()
        self.files_changed.emit()
    
    def get_file_paths(self) -> List[str]:
        """Get list of all file paths."""
        paths = []
        for i in range(self.count()):
            item = self.item(i)
            paths.append(item.data(Qt.UserRole))
        return paths


class MainWindow(QMainWindow):
    """
    Main application window with modern design and drag-drop support.
    """
    
    def __init__(self):
        super().__init__()
        self.theme_manager = get_theme_manager()
        self.drop_overlay = None
        self.setup_ui()
        self.setup_drag_drop()
        self.setup_theme()
        self.setup_connections()
        
        logger.info("MainWindow initialized")
    
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("LangExtractor - Automated Report Extraction")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Create header
        self.create_header(main_layout)
        
        # Create main content area
        self.create_content_area(main_layout)
        
        # Create footer
        self.create_footer(main_layout)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.create_status_bar()
    
    def create_header(self, parent_layout):
        """Create header section."""
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Box)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        # Title
        title_label = QLabel("Automated Report Extraction")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Theme toggle button
        self.theme_toggle_btn = QPushButton()
        self.theme_toggle_btn.setIcon(self.theme_manager.create_icon("palette"))
        self.theme_toggle_btn.setToolTip("Toggle theme")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_toggle_btn)
        
        parent_layout.addWidget(header_frame)
    
    def create_content_area(self, parent_layout):
        """Create main content area."""
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - File list
        left_panel = self.create_file_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - Preview/Settings (placeholder)
        right_panel = self.create_preview_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        content_splitter.setSizes([400, 800])
        
        parent_layout.addWidget(content_splitter)
    
    def create_file_panel(self) -> QWidget:
        """Create file management panel."""
        panel = QFrame()
        panel.setFrameShape(QFrame.Box)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Panel title
        title_label = QLabel("Files")
        title_label.setStyleSheet("font-size: 14pt; font-weight: 600;")
        layout.addWidget(title_label)
        
        # File list
        self.file_list = FileListWidget()
        layout.addWidget(self.file_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.setIcon(self.theme_manager.create_icon("add"))
        self.add_files_btn.clicked.connect(self.add_files)
        button_layout.addWidget(self.add_files_btn)
        
        self.remove_files_btn = QPushButton("Remove")
        self.remove_files_btn.setIcon(self.theme_manager.create_icon("trash"))
        self.remove_files_btn.clicked.connect(self.remove_files)
        self.remove_files_btn.setEnabled(False)
        button_layout.addWidget(self.remove_files_btn)
        
        button_layout.addStretch()
        
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all_files)
        self.clear_all_btn.setEnabled(False)
        button_layout.addWidget(self.clear_all_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def create_preview_panel(self) -> QWidget:
        """Create preview panel with extraction results display."""
        panel = QFrame()
        panel.setFrameShape(QFrame.Box)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Panel title
        title_label = QLabel("Preview & Settings")
        title_label.setStyleSheet("font-size: 14pt; font-weight: 600;")
        layout.addWidget(title_label)
        
        # Create preview panel
        self.preview_panel = PreviewPanel()
        layout.addWidget(self.preview_panel, 1)  # Give it stretch factor of 1
        
        # Process button
        self.process_btn = QPushButton("Start Processing")
        self.process_btn.setProperty("class", "primary")
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self.start_processing)
        layout.addWidget(self.process_btn)
        
        return panel
    
    def create_footer(self, parent_layout):
        """Create footer with progress bar."""
        footer_frame = QFrame()
        footer_frame.setFrameShape(QFrame.Box)
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(8)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        footer_layout.addWidget(self.progress_bar)
        
        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        footer_layout.addWidget(self.progress_label)
        
        parent_layout.addWidget(footer_frame)
    
    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        add_files_action = QAction("Add Files...", self)
        add_files_action.setShortcut("Ctrl+O")
        add_files_action.triggered.connect(self.add_files)
        file_menu.addAction(add_files_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        toggle_theme_action = QAction("Toggle Theme", self)
        toggle_theme_action.setShortcut("Ctrl+T")
        toggle_theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(toggle_theme_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        
        # Add files action
        add_files_action = QAction(self.theme_manager.create_icon("add"), "Add Files", self)
        add_files_action.triggered.connect(self.add_files)
        toolbar.addAction(add_files_action)
        
        # Remove files action
        remove_files_action = QAction(self.theme_manager.create_icon("trash"), "Remove Files", self)
        remove_files_action.triggered.connect(self.remove_files)
        toolbar.addAction(remove_files_action)
        
        toolbar.addSeparator()
        
        # Theme toggle action
        theme_action = QAction(self.theme_manager.create_icon("palette"), "Toggle Theme", self)
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)
    
    def create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality."""
        self.setAcceptDrops(True)
        
        # Create drop overlay
        self.drop_overlay = DropOverlay(self)
    
    def setup_theme(self):
        """Setup initial theme."""
        app = QApplication.instance()
        current_theme = self.theme_manager.get_current_theme()
        self.theme_manager.apply_theme(app, current_theme)
        
        # Update theme toggle button text
        self.update_theme_button()
    
    def setup_connections(self):
        """Setup signal connections."""
        self.file_list.files_changed.connect(self.update_ui_state)
        self.file_list.itemSelectionChanged.connect(self.update_ui_state)
        self.file_list.itemSelectionChanged.connect(self.on_file_selection_changed)
        
        # Theme change signal
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
    
    def update_ui_state(self):
        """Update UI state based on current conditions."""
        has_files = self.file_list.count() > 0
        has_selection = len(self.file_list.selectedItems()) > 0
        
        self.remove_files_btn.setEnabled(has_selection)
        self.clear_all_btn.setEnabled(has_files)
        self.process_btn.setEnabled(has_files)
        
        # Update status bar
        file_count = self.file_list.count()
        if file_count == 0:
            self.status_bar.showMessage("Ready")
        else:
            self.status_bar.showMessage(f"{file_count} file(s) loaded")
    
    def on_file_selection_changed(self):
        """Handle file selection changes to update preview."""
        selected_items = self.file_list.selectedItems()
        
        if not selected_items:
            # No file selected, show empty state
            self.preview_panel.clear_preview()
            return
        
        # Get selected file path
        selected_item = selected_items[0]  # Single selection for now
        file_path = selected_item.data(Qt.UserRole)
        
        # For now, show a mock extraction result since we don't have processing yet
        # TODO: Replace with actual extraction results when processing is implemented
        self.show_mock_preview(file_path)
    
    def show_mock_preview(self, file_path: str):
        """Show mock preview data for demonstration purposes with varied scenarios."""
        from core.models import ExtractionResult, ProcessingStatus
        import random
        import time
        from pathlib import Path
        
        # Create varied mock data based on file type and name
        file_name = Path(file_path).name.lower()
        
        # Determine mock scenario based on filename
        if "error" in file_name or "corrupt" in file_name:
            # Failed processing scenario
            mock_result = ExtractionResult(
                source_file=file_path,
                extracted_data={},
                confidence_scores={},
                processing_time=0.8,
                errors=["OCR failed - document appears to be corrupted", "Unable to extract readable text"],
                status=ProcessingStatus.FAILED
            )
        elif "pending" in file_name or "queue" in file_name:
            # Pending processing scenario
            mock_result = ExtractionResult(
                source_file=file_path,
                extracted_data={},
                confidence_scores={},
                processing_time=0.0,
                errors=[],
                status=ProcessingStatus.PENDING
            )
        elif "processing" in file_name:
            # Currently processing scenario
            mock_result = ExtractionResult(
                source_file=file_path,
                extracted_data={
                    "company_name": "DataTech Solutions Inc.",
                    "revenue": None,  # Still being processed
                    "quarter": "Q4 2024"
                },
                confidence_scores={
                    "company_name": 0.89,
                    "quarter": 0.82
                },
                processing_time=0.0,
                errors=[],
                status=ProcessingStatus.PROCESSING
            )
        else:
            # Successful processing with realistic variance
            company_names = [
                "TechCorp Solutions Ltd.", "Global Industries Inc.", "Innovation Partners LLC",
                "Data Analytics Co.", "Future Systems Group", "Digital Transform Ltd."
            ]
            quarters = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
            
            # Generate realistic but varied data
            base_revenue = random.randint(500000, 5000000)
            employee_count = random.randint(50, 1000)
            
            mock_result = ExtractionResult(
                source_file=file_path,
                extracted_data={
                    "company_name": random.choice(company_names),
                    "revenue": base_revenue + random.randint(-100000, 100000),
                    "quarter": random.choice(quarters),
                    "contact_email": f"ir@{file_name.split('.')[0].replace('_', '').replace('-', '')}.com",
                    "employee_count": employee_count,
                    "profit_margin": round(random.uniform(5.0, 25.0), 1),
                    "growth_rate": round(random.uniform(-5.0, 15.0), 1)
                },
                confidence_scores={
                    "company_name": random.uniform(0.85, 0.98),
                    "revenue": random.uniform(0.70, 0.95),
                    "quarter": random.uniform(0.88, 0.97),
                    "contact_email": random.uniform(0.60, 0.85),
                    "employee_count": random.uniform(0.40, 0.80),
                    "profit_margin": random.uniform(0.45, 0.75),
                    "growth_rate": random.uniform(0.35, 0.70)
                },
                processing_time=random.uniform(1.2, 4.8),
                errors=[],
                status=ProcessingStatus.COMPLETED
            )
        
        # Enhanced template fields with more variety
        mock_template_fields = [
            {
                "name": "company_name", 
                "type": "text", 
                "description": "Legal company name as registered",
                "optional": False
            },
            {
                "name": "revenue", 
                "type": "currency", 
                "description": "Total revenue for the reporting period",
                "optional": False
            },
            {
                "name": "quarter", 
                "type": "text", 
                "description": "Reporting quarter (Q1, Q2, Q3, Q4)",
                "optional": False
            },
            {
                "name": "contact_email", 
                "type": "text", 
                "description": "Investor relations or main contact email",
                "optional": True
            },
            {
                "name": "employee_count", 
                "type": "number", 
                "description": "Total number of employees",
                "optional": True
            },
            {
                "name": "profit_margin", 
                "type": "number", 
                "description": "Profit margin percentage",
                "optional": True
            },
            {
                "name": "growth_rate", 
                "type": "number", 
                "description": "Year-over-year growth rate percentage",
                "optional": True
            }
        ]
        
        # Update preview with enhanced data
        self.preview_panel.update_file_preview(mock_result, mock_template_fields)
        
        # Also update summary if we have multiple files
        self.update_mock_summary()
    
    def update_mock_summary(self):
        """Update summary preview with mock session data for all files."""
        from core.models import (
            ProcessingSession, ExtractionTemplate, ExtractionField, FieldType,
            ExtractionResult, ProcessingStatus
        )
        from pathlib import Path
        import random
        
        # Get all file paths
        file_paths = self.file_list.get_file_paths()
        
        if not file_paths:
            self.preview_panel.clear_preview()
            return
        
        # Create mock template
        template = ExtractionTemplate(
            name="financial_reports_template",
            prompt_description="Extract financial data from quarterly and annual reports",
            fields=[
                ExtractionField("company_name", FieldType.TEXT, "Legal company name"),
                ExtractionField("revenue", FieldType.CURRENCY, "Total revenue"),
                ExtractionField("quarter", FieldType.TEXT, "Reporting quarter"),
                ExtractionField("contact_email", FieldType.TEXT, "Contact email"),
                ExtractionField("employee_count", FieldType.NUMBER, "Employee count"),
                ExtractionField("profit_margin", FieldType.NUMBER, "Profit margin %"),
                ExtractionField("growth_rate", FieldType.NUMBER, "Growth rate %")
            ]
        )
        
        # Generate mock results for all files
        mock_results = []
        for file_path in file_paths:
            file_name = Path(file_path).name.lower()
            
            if "error" in file_name or "corrupt" in file_name:
                result = ExtractionResult(
                    source_file=file_path,
                    extracted_data={},
                    confidence_scores={},
                    processing_time=0.5,
                    errors=["Processing failed"],
                    status=ProcessingStatus.FAILED
                )
            elif "pending" in file_name:
                result = ExtractionResult(
                    source_file=file_path,
                    extracted_data={},
                    confidence_scores={},
                    processing_time=0.0,
                    errors=[],
                    status=ProcessingStatus.PENDING
                )
            else:
                # Generate successful result
                result = ExtractionResult(
                    source_file=file_path,
                    extracted_data={
                        "company_name": f"Company {len(mock_results) + 1} Ltd.",
                        "revenue": random.randint(500000, 3000000),
                        "quarter": random.choice(["Q1 2024", "Q2 2024", "Q3 2024"]),
                        "contact_email": f"contact{len(mock_results) + 1}@company.com",
                        "employee_count": random.randint(50, 500),
                        "profit_margin": round(random.uniform(8.0, 20.0), 1),
                        "growth_rate": round(random.uniform(-2.0, 12.0), 1)
                    },
                    confidence_scores={
                        "company_name": random.uniform(0.85, 0.98),
                        "revenue": random.uniform(0.70, 0.92),
                        "quarter": random.uniform(0.88, 0.96),
                        "contact_email": random.uniform(0.60, 0.80),
                        "employee_count": random.uniform(0.45, 0.75),
                        "profit_margin": random.uniform(0.50, 0.70),
                        "growth_rate": random.uniform(0.40, 0.65)
                    },
                    processing_time=random.uniform(1.5, 4.0),
                    errors=[],
                    status=ProcessingStatus.COMPLETED
                )
            
            mock_results.append(result)
        
        # Create mock session
        session = ProcessingSession(
            template=template,
            files=file_paths,
            results=mock_results
        )
        
        # Update summary preview
        self.preview_panel.update_summary_preview(session)
    
    def update_theme_button(self):
        """Update theme toggle button appearance."""
        current_theme = self.theme_manager.get_current_theme()
        tooltip = f"Switch to {'light' if current_theme == 'dark' else 'dark'} theme"
        self.theme_toggle_btn.setToolTip(tooltip)

    # Drag and Drop Events
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            # Check if any URLs are valid files
            valid_files = self.get_valid_files_from_urls(event.mimeData().urls())
            if valid_files:
                event.acceptProposedAction()
                self.drop_overlay.show_overlay()
                logger.debug("Drag enter accepted")
            else:
                event.ignore()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self.drop_overlay.hide_overlay()
        logger.debug("Drag leave")
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        self.drop_overlay.hide_overlay()

        if event.mimeData().hasUrls():
            valid_files = self.get_valid_files_from_urls(event.mimeData().urls())
            added_count = 0
            duplicate_count = 0

            for file_path in valid_files:
                if self.file_list.add_file(file_path):
                    added_count += 1
                else:
                    duplicate_count += 1

            # Show feedback message
            if added_count > 0:
                message = f"Added {added_count} file(s)"
                if duplicate_count > 0:
                    message += f" ({duplicate_count} duplicate(s) ignored)"
                self.show_toast_message(message, "success")
                logger.info(f"Drop completed: {added_count} added, {duplicate_count} duplicates")
            elif duplicate_count > 0:
                self.show_toast_message(f"All {duplicate_count} file(s) already in list", "warning")

            event.acceptProposedAction()
        else:
            event.ignore()

    def get_valid_files_from_urls(self, urls: List[QUrl]) -> List[str]:
        """Extract valid file paths from URL list."""
        valid_files = []
        supported_formats = {'.pdf', '.docx', '.xlsx', '.xls'}

        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()
                path = Path(file_path)

                if path.is_file() and path.suffix.lower() in supported_formats:
                    valid_files.append(file_path)

        return valid_files

    def show_toast_message(self, message: str, message_type: str = "info"):
        """Show toast/snackbar message."""
        # For now, use status bar message
        # TODO: Implement proper toast notification
        self.status_bar.showMessage(message, 3000)  # Show for 3 seconds

        if message_type == "success":
            logger.info(f"Toast: {message}")
        elif message_type == "warning":
            logger.warning(f"Toast: {message}")
        else:
            logger.info(f"Toast: {message}")

    # Action Handlers
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        app = QApplication.instance()
        new_theme = self.theme_manager.toggle_theme(app)
        logger.info(f"Theme switched to: {new_theme}")

    def on_theme_changed(self, theme_name: str):
        """Handle theme change signal."""
        self.update_theme_button()
        logger.info(f"Theme changed to: {theme_name}")

    def add_files(self):
        """Open file dialog to add files."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Supported files (*.pdf *.docx *.xlsx *.xls)")

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            added_count = 0
            duplicate_count = 0

            for file_path in selected_files:
                if self.file_list.add_file(file_path):
                    added_count += 1
                else:
                    duplicate_count += 1

            # Show feedback
            if added_count > 0:
                message = f"Added {added_count} file(s)"
                if duplicate_count > 0:
                    message += f" ({duplicate_count} duplicate(s) ignored)"
                self.show_toast_message(message, "success")

    def remove_files(self):
        """Remove selected files."""
        selected_count = len(self.file_list.selectedItems())
        if selected_count > 0:
            self.file_list.remove_selected_files()
            self.show_toast_message(f"Removed {selected_count} file(s)", "info")

    def clear_all_files(self):
        """Clear all files after confirmation."""
        reply = QMessageBox.question(
            self, "Clear All Files",
            "Are you sure you want to remove all files from the list?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            file_count = self.file_list.count()
            self.file_list.clear_all_files()
            self.show_toast_message(f"Cleared {file_count} file(s)", "info")

    def start_processing(self):
        """Start processing files."""
        file_paths = self.file_list.get_file_paths()
        if not file_paths:
            return

        # TODO: Implement actual processing
        self.show_toast_message(f"Processing {len(file_paths)} file(s)...", "info")
        logger.info(f"Started processing {len(file_paths)} files")

        # Simulate progress
        self.show_progress("Processing files...", 0, len(file_paths))

        # TODO: Connect to actual processing pipeline

    def show_progress(self, message: str, current: int, total: int):
        """Show progress bar with message."""
        self.progress_label.setText(message)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)

        self.progress_label.setVisible(True)
        self.progress_bar.setVisible(True)

    def hide_progress(self):
        """Hide progress bar."""
        self.progress_label.setVisible(False)
        self.progress_bar.setVisible(False)

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About LangExtractor",
            "LangExtractor - Automated Report Extraction System\n\n"
            "A modern tool for extracting structured data from documents\n"
            "using OCR and AI-powered extraction.\n\n"
            "Built with PySide6 and modern design principles."
        )

    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("MainWindow closing")
        event.accept()
