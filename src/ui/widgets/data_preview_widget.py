"""
Data preview widget - displays sample records in a table.

Shows a preview of actual data from Salesforce objects.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QHBoxLayout, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import List, Dict, Any, Optional

from ...models.salesforce_metadata import SalesforceObject, RecordType


class DataPreviewWidget(QWidget):
    """
    Widget for displaying sample data from a Salesforce object.
    """

    # Signals
    load_data_requested = pyqtSignal()  # User clicked load data button
    export_data_requested = pyqtSignal()  # User clicked export to CSV button

    def __init__(self):
        """Initialize the data preview widget."""
        super().__init__()
        self.current_object: Optional[SalesforceObject] = None
        self.current_data: Optional[Dict[str, Any]] = None  # Store loaded data for export
        self.selected_record_type_id: Optional[str] = None  # Currently selected record type ID
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Record type selection row
        record_type_layout = QHBoxLayout()

        record_type_label = QLabel("Record Type:")
        record_type_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        record_type_layout.addWidget(record_type_label)

        self.record_type_combo = QComboBox()
        self.record_type_combo.setMinimumWidth(200)
        self.record_type_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #0176d3;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.record_type_combo.currentIndexChanged.connect(self._on_record_type_changed)
        record_type_layout.addWidget(self.record_type_combo)

        record_type_layout.addStretch()
        layout.addLayout(record_type_layout)

        # Info section
        info_layout = QHBoxLayout()

        self.info_label = QLabel("No data loaded")
        self.info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        info_layout.addWidget(self.info_label)

        info_layout.addStretch()

        # Load button
        self.load_button = QPushButton("Load Sample Data")
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #0176d3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #014f8e;
            }
            QPushButton:disabled {
                background-color: #d0d0d0;
                color: #666;
            }
        """)
        self.load_button.clicked.connect(self._on_load_clicked)
        self.load_button.setEnabled(False)
        info_layout.addWidget(self.load_button)

        # Export button (initially hidden, shown after data is loaded)
        self.export_button = QPushButton("Export to CSV")
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #2e844a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1f5a32;
            }
            QPushButton:disabled {
                background-color: #d0d0d0;
                color: #666;
            }
        """)
        self.export_button.clicked.connect(self._on_export_clicked)
        self.export_button.setEnabled(False)
        self.export_button.setVisible(False)  # Hidden until data is loaded
        info_layout.addWidget(self.export_button)

        layout.addLayout(info_layout)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Apply styling
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #0176d3;
                color: white;
            }
            QHeaderView::section {
                background-color: #f3f3f3;
                padding: 6px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.table)

        self.setLayout(layout)

    def set_object(self, salesforce_object: SalesforceObject):
        """
        Set the object for data preview.

        Args:
            salesforce_object: SalesforceObject instance
        """
        self.current_object = salesforce_object
        self.clear()

        # Populate record type dropdown
        self.record_type_combo.blockSignals(True)  # Prevent triggering change event
        self.record_type_combo.clear()

        if salesforce_object.record_types:
            # Add "All Record Types" option
            self.record_type_combo.addItem("All Record Types", None)

            # Add each record type
            for record_type in salesforce_object.record_types:
                self.record_type_combo.addItem(record_type.name, record_type.record_type_id)

            # Select first record type by default
            if len(salesforce_object.record_types) == 1:
                # If only one record type, select it
                self.record_type_combo.setCurrentIndex(1)
                self.selected_record_type_id = salesforce_object.record_types[0].record_type_id
            else:
                # Multiple record types, start with "All"
                self.record_type_combo.setCurrentIndex(0)
                self.selected_record_type_id = None

            self.record_type_combo.setEnabled(True)
        else:
            # No record types
            self.record_type_combo.addItem("No record types", None)
            self.record_type_combo.setEnabled(False)
            self.selected_record_type_id = None

        self.record_type_combo.blockSignals(False)

        self.load_button.setEnabled(True)
        self.info_label.setText(f"Select a record type and click 'Load Sample Data' to preview records from {salesforce_object.label}")

    def set_data(self, data: Dict[str, Any]):
        """
        Display data in the table.

        Args:
            data: Dictionary with 'records', 'fields', and 'total_size'
        """
        # Store data for export
        self.current_data = data

        records = data.get('records', [])
        fields = data.get('fields', [])
        total_size = data.get('total_size', 0)

        if not records:
            self.info_label.setText("No records found")
            self.table.setRowCount(0)
            self.export_button.setEnabled(False)
            self.export_button.setVisible(False)
            return

        # Update info label
        self.info_label.setText(
            f"Showing {len(records)} of {total_size} records"
        )

        # Enable and show export button
        self.export_button.setEnabled(True)
        self.export_button.setVisible(True)

        # Set up table
        self.table.setRowCount(len(records))
        self.table.setColumnCount(len(fields))
        self.table.setHorizontalHeaderLabels(fields)

        # Populate table
        for row_idx, record in enumerate(records):
            for col_idx, field_name in enumerate(fields):
                value = record.get(field_name, '')

                # Format value for display
                display_value = self._format_value(value)

                # Create table item
                item = QTableWidgetItem(display_value)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                # Color code null values
                if value is None:
                    item.setForeground(QColor('#999'))

                self.table.setItem(row_idx, col_idx, item)

        # Resize columns to content
        self.table.resizeColumnsToContents()

        # Set minimum column widths
        header = self.table.horizontalHeader()
        for col in range(len(fields)):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
            if self.table.columnWidth(col) < 100:
                self.table.setColumnWidth(col, 100)

    def clear(self):
        """Clear the table."""
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.info_label.setText("No data loaded")
        self.current_data = None
        self.selected_record_type_id = None
        self.record_type_combo.clear()
        self.export_button.setEnabled(False)
        self.export_button.setVisible(False)

    def show_loading(self):
        """Show loading state."""
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels([""])
        loading_item = QTableWidgetItem("Loading sample data...")
        loading_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(0, 0, loading_item)
        self.info_label.setText("Loading...")
        self.load_button.setEnabled(False)

    def show_error(self, error_message: str):
        """
        Show error state.

        Args:
            error_message: Error message to display
        """
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Error"])
        error_item = QTableWidgetItem(f"Error loading data: {error_message}")
        error_item.setTextAlignment(Qt.AlignCenter)
        error_item.setForeground(QColor('#c23934'))
        self.table.setItem(0, 0, error_item)
        self.info_label.setText("Error")
        self.load_button.setEnabled(True)

    def _on_load_clicked(self):
        """Handle load button click."""
        self.load_data_requested.emit()

    def _on_export_clicked(self):
        """Handle export button click."""
        self.export_data_requested.emit()

    def _on_record_type_changed(self, index: int):
        """Handle record type selection change."""
        # Get the selected record type ID from combo box data
        self.selected_record_type_id = self.record_type_combo.itemData(index)

        # Clear existing preview data when record type changes
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.current_data = None
        self.export_button.setEnabled(False)
        self.export_button.setVisible(False)

        # Update info label
        if self.current_object:
            record_type_name = self.record_type_combo.currentText()
            self.info_label.setText(f"Click 'Load Sample Data' to preview {record_type_name} records")

    def get_selected_record_type_id(self) -> Optional[str]:
        """
        Get the currently selected record type ID.

        Returns:
            Record type ID or None if "All Record Types" is selected
        """
        return self.selected_record_type_id

    def _format_value(self, value: Any) -> str:
        """
        Format a field value for display.

        Args:
            value: Field value

        Returns:
            Formatted string
        """
        if value is None:
            return "(null)"

        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, (int, float)):
            return str(value)

        if isinstance(value, dict):
            # Lookup/reference field - show Name if available
            if 'Name' in value:
                return value['Name']
            # Otherwise show the ID or first available field
            for key in ['Id', 'name', 'id']:
                if key in value:
                    return str(value[key])
            return str(value)

        # Convert to string
        return str(value)
