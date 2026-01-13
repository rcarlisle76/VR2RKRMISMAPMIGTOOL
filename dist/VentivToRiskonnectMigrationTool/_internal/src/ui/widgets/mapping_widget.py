"""
Mapping widget - main interface for field mapping.

Allows users to map source CSV columns to Salesforce fields.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from typing import Optional, List

from ...models.salesforce_metadata import SalesforceObject
from ...models.mapping_models import SourceFile, FieldMapping
from .source_file_panel import SourceFilePanel
from .mapping_table_widget import MappingTableWidget


class MappingWidget(QWidget):
    """
    Widget for mapping source file columns to Salesforce fields.
    """

    # Signals
    file_import_requested = pyqtSignal(str)  # file_path
    template_download_requested = pyqtSignal()  # Download CSV template
    auto_map_requested = pyqtSignal()
    save_mapping_requested = pyqtSignal()
    load_mapping_requested = pyqtSignal()
    load_data_requested = pyqtSignal()  # Load data to Salesforce

    def __init__(self):
        """Initialize the mapping widget."""
        super().__init__()
        self.current_object: Optional[SalesforceObject] = None
        self.source_file: Optional[SourceFile] = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Splitter for source and mapping panels
        self.splitter = QSplitter(Qt.Horizontal)

        # Left: Source file panel
        self.source_file_panel = SourceFilePanel()
        self.source_file_panel.file_imported.connect(self._on_file_imported)
        self.source_file_panel.template_download_requested.connect(self._on_template_download_requested)
        self.splitter.addWidget(self.source_file_panel)

        # Right: Mapping table
        self.mapping_table = MappingTableWidget()
        self.mapping_table.auto_map_requested.connect(self._on_auto_map_requested)
        self.mapping_table.save_requested.connect(self._on_save_requested)
        self.mapping_table.load_requested.connect(self._on_load_requested)
        self.mapping_table.load_data_requested.connect(self._on_load_data_requested)
        self.splitter.addWidget(self.mapping_table)

        # Set splitter sizes (40% left, 60% right)
        self.splitter.setSizes([400, 600])

        layout.addWidget(self.splitter)

        self.setLayout(layout)

    def set_object(self, salesforce_object: SalesforceObject):
        """
        Set the target Salesforce object for mapping.

        Args:
            salesforce_object: SalesforceObject to map to
        """
        self.current_object = salesforce_object

        # Enable template download button when object is selected
        self.source_file_panel.enable_template_download(salesforce_object is not None)

    def set_source_file(self, source_file: SourceFile):
        """
        Set the source file.

        Args:
            source_file: SourceFile with column information
        """
        self.source_file = source_file
        self.source_file_panel.set_file(source_file)

        # If we have both source file and object, populate mapping table
        if self.current_object:
            self.mapping_table.set_data(source_file, self.current_object)

    def set_mappings(self, mappings: List[FieldMapping]):
        """
        Apply suggested mappings.

        Args:
            mappings: List of FieldMapping objects
        """
        self.mapping_table.set_mappings(mappings)

    def get_mappings(self) -> List[FieldMapping]:
        """
        Get current mappings.

        Returns:
            List of FieldMapping objects
        """
        return self.mapping_table.get_mappings()

    def clear(self):
        """Clear the mapping widget."""
        self.current_object = None
        self.source_file = None
        self.source_file_panel.clear()
        self.source_file_panel.enable_template_download(False)
        self.mapping_table.clear()

    def show_loading(self):
        """Show loading state."""
        # Could add visual loading indicator here
        pass

    def show_error(self, error_message: str):
        """
        Show error message.

        Args:
            error_message: Error message to display
        """
        # Could show error dialog or inline message
        pass

    def _on_file_imported(self, file_path: str):
        """
        Handle file import from source file panel.

        Args:
            file_path: Path to imported file
        """
        # Emit signal for presenter to handle
        self.file_import_requested.emit(file_path)

    def _on_auto_map_requested(self):
        """Handle auto-map button click."""
        self.auto_map_requested.emit()

    def _on_save_requested(self):
        """Handle save mapping button click."""
        self.save_mapping_requested.emit()

    def _on_load_requested(self):
        """Handle load mapping button click."""
        self.load_mapping_requested.emit()

    def _on_load_data_requested(self):
        """Handle load data button click."""
        self.load_data_requested.emit()

    def _on_template_download_requested(self):
        """Handle template download button click."""
        self.template_download_requested.emit()
