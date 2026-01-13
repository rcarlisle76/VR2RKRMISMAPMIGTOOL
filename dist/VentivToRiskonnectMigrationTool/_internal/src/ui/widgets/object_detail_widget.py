"""
Object detail widget - displays comprehensive metadata for a Salesforce object.

Shows object information, fields, relationships, and data preview in tabs.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QGroupBox, QHBoxLayout, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ...models.salesforce_metadata import SalesforceObject
from .field_table_widget import FieldTableWidget
from .field_detail_panel import FieldDetailPanel
from .data_preview_widget import DataPreviewWidget
from .mapping_widget import MappingWidget
from .relationship_table_widget import RelationshipTableWidget
from .log_viewer_widget import LogViewerWidget


class ObjectDetailWidget(QWidget):
    """
    Widget for displaying detailed information about a Salesforce object.

    Contains:
    - Object header with basic info
    - Tabbed interface for Fields, Relationships, and Preview
    """

    # Signals
    load_preview_data_requested = pyqtSignal()  # Request to load preview data
    export_preview_data_requested = pyqtSignal()  # Request to export preview data to CSV
    file_import_requested = pyqtSignal(str)  # file_path
    template_download_requested = pyqtSignal()  # Request CSV template download
    auto_map_requested = pyqtSignal()  # Request auto-mapping
    save_mapping_requested = pyqtSignal()  # Request save mapping
    load_mapping_requested = pyqtSignal()  # Request load mapping
    load_data_requested = pyqtSignal()  # Request data loading to Salesforce
    load_page_layouts_requested = pyqtSignal(str)  # Request page layout info for object

    def __init__(self):
        """Initialize the object detail widget."""
        super().__init__()
        self.current_object = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Object header section
        self.header_group = QGroupBox()
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)

        # Object name
        self.object_name_label = QLabel()
        name_font = QFont()
        name_font.setPointSize(16)
        name_font.setBold(True)
        self.object_name_label.setFont(name_font)
        header_layout.addWidget(self.object_name_label)

        # Object metadata (type, API name, field count)
        self.metadata_layout = QHBoxLayout()
        self.metadata_layout.setSpacing(20)

        self.type_label = QLabel()
        self.api_name_label = QLabel()
        self.field_count_label = QLabel()

        self.metadata_layout.addWidget(self.type_label)
        self.metadata_layout.addWidget(self.api_name_label)
        self.metadata_layout.addWidget(self.field_count_label)
        self.metadata_layout.addStretch()

        header_layout.addLayout(self.metadata_layout)

        self.header_group.setLayout(header_layout)
        self.header_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 15px;
            }
        """)
        layout.addWidget(self.header_group)

        # Tabbed interface
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #f3f3f3;
                border: 1px solid #d0d0d0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover {
                background-color: #e8e8e8;
            }
        """)

        # Fields tab with splitter (table on left, details on right)
        fields_tab = QWidget()
        fields_layout = QHBoxLayout()
        fields_layout.setContentsMargins(0, 0, 0, 0)

        fields_splitter = QSplitter(Qt.Horizontal)

        # Field table
        self.field_table_widget = FieldTableWidget()
        fields_splitter.addWidget(self.field_table_widget)

        # Field detail panel
        self.field_detail_panel = FieldDetailPanel()
        fields_splitter.addWidget(self.field_detail_panel)

        # Set splitter sizes (60% table, 40% details)
        fields_splitter.setSizes([600, 400])

        fields_layout.addWidget(fields_splitter)
        fields_tab.setLayout(fields_layout)

        self.tabs.addTab(fields_tab, "Fields")

        # Connect field selection to detail panel
        self.field_table_widget.field_selected.connect(self.field_detail_panel.set_field)

        # Relationships tab
        self.relationship_table_widget = RelationshipTableWidget()
        self.relationship_table_widget.load_page_layouts_requested.connect(
            self._on_load_page_layouts_requested
        )
        self.tabs.addTab(self.relationship_table_widget, "Relationships")

        # Preview tab
        self.data_preview_widget = DataPreviewWidget()
        self.data_preview_widget.load_data_requested.connect(self._on_load_preview_requested)
        self.data_preview_widget.export_data_requested.connect(self._on_export_preview_requested)
        self.tabs.addTab(self.data_preview_widget, "Preview")

        # Map Fields tab
        self.mapping_widget = MappingWidget()
        self.mapping_widget.file_import_requested.connect(self._on_file_import_requested)
        self.mapping_widget.template_download_requested.connect(self._on_template_download_requested)
        self.mapping_widget.auto_map_requested.connect(self._on_auto_map_requested)
        self.mapping_widget.save_mapping_requested.connect(self._on_save_mapping_requested)
        self.mapping_widget.load_mapping_requested.connect(self._on_load_mapping_requested)
        self.mapping_widget.load_data_requested.connect(self._on_load_data_requested)
        self.tabs.addTab(self.mapping_widget, "Map Fields")

        # Logs tab
        self.log_viewer_widget = LogViewerWidget()
        self.tabs.addTab(self.log_viewer_widget, "Logs")

        layout.addWidget(self.tabs)

        self.setLayout(layout)

        # Initially hide the widget (show when object is selected)
        self.hide()

    def set_object(self, salesforce_object: SalesforceObject):
        """
        Set the object to display.

        Args:
            salesforce_object: SalesforceObject instance with metadata
        """
        self.current_object = salesforce_object

        # Update header
        self.object_name_label.setText(salesforce_object.label)

        # Type label
        object_type = "Custom Object" if salesforce_object.custom else "Standard Object"
        type_color = "#0176d3" if salesforce_object.custom else "#2e844a"
        self.type_label.setText(f'<span style="color: {type_color}; font-weight: bold;">{object_type}</span>')

        # API name
        self.api_name_label.setText(f"API Name: <b>{salesforce_object.name}</b>")

        # Field count
        field_count = len(salesforce_object.fields)
        required_count = sum(1 for f in salesforce_object.fields if f.required)
        createable_required_count = sum(
            1 for f in salesforce_object.fields
            if f.required and f.createable and not getattr(f, 'calculated', False) and not getattr(f, 'auto_number', False)
        )
        self.field_count_label.setText(
            f"{field_count} fields ({createable_required_count} createable required, {required_count} total required)"
        )

        # Update fields table
        self.field_table_widget.set_fields(salesforce_object.fields)

        # Update relationships table (includes record types and page layouts)
        self.relationship_table_widget.set_object(salesforce_object)

        # Update preview widget
        self.data_preview_widget.set_object(salesforce_object)

        # Clear and update mapping widget (important: clear first to remove old data)
        self.mapping_widget.clear()
        self.mapping_widget.set_object(salesforce_object)

        # Switch to Fields tab
        self.tabs.setCurrentIndex(0)

        # Show the widget
        self.show()

    def clear(self):
        """Clear the current object and hide the widget."""
        self.current_object = None
        self.object_name_label.setText("")
        self.type_label.setText("")
        self.api_name_label.setText("")
        self.field_count_label.setText("")
        self.field_table_widget.clear()
        self.relationship_table_widget.clear()
        self.field_detail_panel.clear()
        self.data_preview_widget.clear()
        self.mapping_widget.clear()
        self.log_viewer_widget.clear()
        self.hide()

    def show_loading(self):
        """Show loading state."""
        self.object_name_label.setText("Loading object metadata...")
        self.type_label.setText("")
        self.api_name_label.setText("")
        self.field_count_label.setText("")
        self.field_table_widget.show_loading()
        self.relationship_table_widget.show_loading()
        self.show()

    def _on_load_preview_requested(self):
        """Handle request to load preview data."""
        self.load_preview_data_requested.emit()

    def _on_export_preview_requested(self):
        """Handle request to export preview data."""
        self.export_preview_data_requested.emit()

    def _on_file_import_requested(self, file_path: str):
        """Handle file import request."""
        self.file_import_requested.emit(file_path)

    def _on_template_download_requested(self):
        """Handle template download request."""
        self.template_download_requested.emit()

    def _on_auto_map_requested(self):
        """Handle auto-map request."""
        self.auto_map_requested.emit()

    def _on_save_mapping_requested(self):
        """Handle save mapping request."""
        self.save_mapping_requested.emit()

    def _on_load_mapping_requested(self):
        """Handle load mapping request."""
        self.load_mapping_requested.emit()

    def _on_load_data_requested(self):
        """Handle load data request."""
        self.load_data_requested.emit()

    def _on_load_page_layouts_requested(self, object_name: str):
        """Handle page layouts request."""
        self.load_page_layouts_requested.emit(object_name)
