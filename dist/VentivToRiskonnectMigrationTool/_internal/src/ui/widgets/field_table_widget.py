"""
Field table widget - displays field metadata in a table.

Shows fields with their types, required status, and other properties.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import List, Optional

from ...models.salesforce_metadata import SalesforceField


class FieldTableWidget(QWidget):
    """
    Widget for displaying Salesforce object fields in a table.
    """

    # Signals
    field_selected = pyqtSignal(object)  # SalesforceField
    download_template_requested = pyqtSignal()  # Request to download template with current fields

    def __init__(self):
        """Initialize the field table widget."""
        super().__init__()
        self.fields: List[SalesforceField] = []
        self.all_fields: List[SalesforceField] = []  # Store all fields for filtering
        self.active_filter_layout_name: Optional[str] = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Info label
        self.info_label = QLabel("Fields")
        self.info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.info_label)

        # Filter banner (initially hidden)
        self.filter_banner = QWidget()
        filter_banner_layout = QHBoxLayout()
        filter_banner_layout.setContentsMargins(10, 5, 10, 5)

        self.filter_label = QLabel()
        self.filter_label.setStyleSheet("color: #0176d3; font-weight: bold;")

        self.clear_filter_button = QPushButton("Clear Filter")
        self.clear_filter_button.setStyleSheet("""
            QPushButton {
                background-color: #f3f3f3;
                border: 1px solid #d0d0d0;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.clear_filter_button.clicked.connect(self.clear_filter)

        self.download_template_button = QPushButton("Download Template")
        self.download_template_button.setStyleSheet("""
            QPushButton {
                background-color: #0176d3;
                color: white;
                border: 1px solid #0176d3;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #014f8e;
            }
        """)
        self.download_template_button.clicked.connect(self.download_template_requested.emit)

        filter_banner_layout.addWidget(self.filter_label)
        filter_banner_layout.addStretch()
        filter_banner_layout.addWidget(self.download_template_button)
        filter_banner_layout.addWidget(self.clear_filter_button)
        self.filter_banner.setLayout(filter_banner_layout)
        self.filter_banner.setStyleSheet("background-color: #e8f4fd; border: 1px solid #0176d3; border-radius: 3px;")
        self.filter_banner.setVisible(False)  # Initially hidden
        layout.addWidget(self.filter_banner)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Field Name",
            "API Name",
            "Type",
            "Length",
            "Required",
            "Updateable",
            "Createable"
        ])

        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Field Name
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Label
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Length
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Required
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Updateable
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Createable

        layout.addWidget(self.table)

        self.setLayout(layout)

        # Connect selection signal
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

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

    def set_fields(self, fields: List[SalesforceField]):
        """
        Set the list of fields to display.

        Args:
            fields: List of SalesforceField objects
        """
        self.table.setRowCount(0)  # Clear existing rows

        if not fields:
            self.info_label.setText("No fields")
            self.fields = []
            return

        # Update info label
        required_count = sum(1 for f in fields if f.required)
        self.info_label.setText(f"{len(fields)} fields ({required_count} required)")

        # Sort fields alphabetically by label and store
        sorted_fields = sorted(fields, key=lambda f: f.label)
        self.fields = sorted_fields

        # Add rows
        for row, field in enumerate(sorted_fields):
            self.table.insertRow(row)

            # Field Name (show label)
            name_item = QTableWidgetItem(field.label)
            name_item.setFont(self._get_bold_font() if field.required else self.font())
            self.table.setItem(row, 0, name_item)

            # API Name
            label_item = QTableWidgetItem(field.name)
            self.table.setItem(row, 1, label_item)

            # Type
            type_text = field.type
            if field.reference_to:
                type_text += f" → {', '.join(field.reference_to)}"
            type_item = QTableWidgetItem(type_text)

            # Color code by type
            if field.type == 'reference':
                type_item.setForeground(QColor('#0176d3'))  # Blue for references
            elif field.type in ['datetime', 'date']:
                type_item.setForeground(QColor('#2e844a'))  # Green for dates

            self.table.setItem(row, 2, type_item)

            # Length
            length_item = QTableWidgetItem(str(field.length) if field.length else "")
            length_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, length_item)

            # Required
            required_item = QTableWidgetItem("✓" if field.required else "")
            required_item.setTextAlignment(Qt.AlignCenter)
            if field.required:
                required_item.setForeground(QColor('#c23934'))  # Red for required
            self.table.setItem(row, 4, required_item)

            # Updateable
            updateable_item = QTableWidgetItem("✓" if field.updateable else "")
            updateable_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, updateable_item)

            # Createable
            createable_item = QTableWidgetItem("✓" if field.createable else "")
            createable_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, createable_item)

    def clear(self):
        """Clear the table."""
        self.table.setRowCount(0)
        self.fields = []
        self.info_label.setText("Fields")

    def show_loading(self):
        """Show loading state."""
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        loading_item = QTableWidgetItem("Loading field metadata...")
        loading_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(0, 0, loading_item)

    def _on_selection_changed(self):
        """Handle field selection change."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows and self.fields:
            row = selected_rows[0].row()
            if 0 <= row < len(self.fields):
                selected_field = self.fields[row]
                self.field_selected.emit(selected_field)

    def _get_bold_font(self):
        """Get bold font for required fields."""
        font = self.font()
        font.setBold(True)
        return font

    def filter_by_layout_fields(self, layout_field_names: List[str], layout_name: str):
        """
        Filter fields to show only those on a specific page layout.

        Args:
            layout_field_names: List of field API names on the layout
            layout_name: Name of the layout for display
        """
        if not self.all_fields:
            # Store all fields for filtering
            self.all_fields = self.fields.copy()

        # Filter fields to only those on the layout
        filtered_fields = [f for f in self.all_fields if f.name in layout_field_names]

        # Update the display
        self.set_fields(filtered_fields)

        # Show filter banner
        self.active_filter_layout_name = layout_name
        self.filter_label.setText(f"Showing fields on layout: {layout_name} ({len(filtered_fields)} fields)")
        self.filter_banner.setVisible(True)

    def clear_filter(self):
        """Clear the active filter and show all fields."""
        if self.all_fields:
            self.set_fields(self.all_fields)
            self.all_fields = []

        self.active_filter_layout_name = None
        self.filter_banner.setVisible(False)
