"""
Relationship table widget - displays object relationships.

Shows lookup and master-detail relationships to other Salesforce objects,
plus record type to page layout assignments.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import List, Dict, Optional

from ...models.salesforce_metadata import SalesforceField, SalesforceObject


class RelationshipTableWidget(QWidget):
    """
    Widget for displaying Salesforce object relationships.

    Shows lookup and master-detail fields that reference other objects,
    plus record type to page layout assignments.
    """

    # Signal to request page layout info
    load_page_layouts_requested = pyqtSignal(str)  # object_name

    # Signal when layout is clicked - emits (record_type_id, layout_id)
    layout_clicked = pyqtSignal(str, str)

    def __init__(self):
        """Initialize the relationship table widget."""
        super().__init__()
        self.relationships: List[SalesforceField] = []
        self.current_object_name: Optional[str] = None
        self.record_type_data: Dict[int, tuple] = {}  # Maps row -> (record_type_id, layout_id)
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Create splitter for two sections
        splitter = QSplitter(Qt.Vertical)

        # === RECORD TYPES & PAGE LAYOUTS SECTION ===
        record_types_widget = QWidget()
        rt_layout = QVBoxLayout()
        rt_layout.setContentsMargins(0, 0, 0, 0)
        rt_layout.setSpacing(10)

        # Record types info label
        self.record_types_label = QLabel("Record Types & Page Layouts")
        self.record_types_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        rt_layout.addWidget(self.record_types_label)

        # Record types table
        self.record_types_table = QTableWidget()
        self.record_types_table.setColumnCount(2)
        self.record_types_table.setHorizontalHeaderLabels([
            "Record Type",
            "Assigned Page Layout"
        ])

        # Configure record types table
        self.record_types_table.setAlternatingRowColors(True)
        self.record_types_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.record_types_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.record_types_table.verticalHeader().setVisible(False)

        # Connect click handler
        self.record_types_table.itemClicked.connect(self._on_layout_row_clicked)

        # Set column widths
        rt_header = self.record_types_table.horizontalHeader()
        rt_header.setSectionResizeMode(0, QHeaderView.Stretch)  # Record Type
        rt_header.setSectionResizeMode(1, QHeaderView.Stretch)  # Assigned Page Layout

        rt_layout.addWidget(self.record_types_table)
        record_types_widget.setLayout(rt_layout)

        # === FIELD RELATIONSHIPS SECTION ===
        relationships_widget = QWidget()
        rel_layout = QVBoxLayout()
        rel_layout.setContentsMargins(0, 0, 0, 0)
        rel_layout.setSpacing(10)

        # Relationships info label
        self.info_label = QLabel("Field Relationships")
        self.info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        rel_layout.addWidget(self.info_label)

        # Relationships table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Field Name",
            "Label",
            "Relationship Name",
            "References To",
            "Type",
            "Required"
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
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Relationship Name
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # References To
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Required

        rel_layout.addWidget(self.table)
        relationships_widget.setLayout(rel_layout)

        # Add both sections to splitter
        splitter.addWidget(record_types_widget)
        splitter.addWidget(relationships_widget)

        # Set initial sizes (30% record types, 70% relationships)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)
        self.setLayout(layout)

        # Apply styling to both tables
        table_style = """
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
        """
        self.table.setStyleSheet(table_style)
        self.record_types_table.setStyleSheet(table_style)

    def set_object(self, salesforce_object: SalesforceObject):
        """
        Set the Salesforce object and populate both tables.

        Args:
            salesforce_object: SalesforceObject with metadata and record types
        """
        self.current_object_name = salesforce_object.name

        # Set field relationships
        self.set_fields(salesforce_object.fields)

        # Set record types (page layouts will be loaded separately via signal)
        self.set_record_types(salesforce_object)

    def set_record_types(self, salesforce_object: SalesforceObject):
        """
        Populate record types table.

        Args:
            salesforce_object: SalesforceObject with record types
        """
        self.record_types_table.setRowCount(0)  # Clear existing rows

        # Ensure proper column setup
        self.record_types_table.setColumnCount(2)
        self.record_types_table.setHorizontalHeaderLabels([
            "Record Type",
            "Assigned Page Layout"
        ])

        # Re-apply column sizing
        rt_header = self.record_types_table.horizontalHeader()
        rt_header.setSectionResizeMode(0, QHeaderView.Stretch)  # Record Type
        rt_header.setSectionResizeMode(1, QHeaderView.Stretch)  # Assigned Page Layout

        if not salesforce_object.record_types:
            self.record_types_label.setText("No record types")
            return

        # Update label
        self.record_types_label.setText(
            f"{len(salesforce_object.record_types)} Record Types & Page Layouts"
        )

        # Sort by default first, then by name
        sorted_record_types = sorted(
            salesforce_object.record_types,
            key=lambda rt: (not rt.is_default, rt.name)
        )

        # Add rows
        self.record_type_data.clear()  # Clear previous data
        for row, record_type in enumerate(sorted_record_types):
            self.record_types_table.insertRow(row)

            # Store record type ID for this row (layout ID will be stored later)
            self.record_type_data[row] = (record_type.record_type_id, None)

            # Record Type Name
            rt_item = QTableWidgetItem(record_type.label)
            if record_type.is_default:
                rt_item.setFont(self._get_bold_font())
            self.record_types_table.setItem(row, 0, rt_item)

            # Page Layout (placeholder - will be loaded)
            layout_item = QTableWidgetItem("Loading...")
            layout_item.setForeground(QColor('#888888'))
            self.record_types_table.setItem(row, 1, layout_item)

        # Request page layout info
        if self.current_object_name:
            self.load_page_layouts_requested.emit(self.current_object_name)

    def set_page_layout_assignments(self, layout_assignments: Dict[str, str]):
        """
        Update record types table with page layout names.

        Args:
            layout_assignments: Dict mapping record_type_id -> layout_name
        """
        # Update existing rows with page layout names
        for row in range(self.record_types_table.rowCount()):
            rt_name_item = self.record_types_table.item(row, 0)
            if rt_name_item:
                # Find matching record type ID
                # We'll need to store record type IDs or match by name
                # For now, just update with the layout info we have
                # This will be populated by the presenter
                pass

    def update_page_layout_for_row(self, row: int, layout_name: str, layout_id: Optional[str] = None):
        """
        Update a specific row's page layout name and ID.

        Args:
            row: Row index
            layout_name: Page layout name to display
            layout_id: Salesforce layout ID (optional)
        """
        if row < self.record_types_table.rowCount():
            layout_item = QTableWidgetItem(layout_name)
            layout_item.setForeground(QColor('#9050e9'))  # Purple for layouts
            self.record_types_table.setItem(row, 1, layout_item)

            # Update the stored layout ID for this row
            if row in self.record_type_data:
                record_type_id, _ = self.record_type_data[row]
                self.record_type_data[row] = (record_type_id, layout_id)

    def set_fields(self, fields: List[SalesforceField]):
        """
        Set the list of all fields and extract relationships.

        Args:
            fields: List of all SalesforceField objects
        """
        self.table.setRowCount(0)  # Clear existing rows

        # Filter for reference fields only
        relationships = [f for f in fields if f.type == 'reference']

        if not relationships:
            self.info_label.setText("No field relationships")
            self.relationships = []
            return

        # Update info label
        required_count = sum(1 for f in relationships if f.required)
        self.info_label.setText(
            f"{len(relationships)} field relationships ({required_count} required)"
        )

        # Sort relationships alphabetically by label and store
        sorted_relationships = sorted(relationships, key=lambda f: f.label)
        self.relationships = sorted_relationships

        # Add rows
        for row, field in enumerate(sorted_relationships):
            self.table.insertRow(row)

            # Field Name (API name)
            name_item = QTableWidgetItem(field.name)
            name_item.setFont(self._get_bold_font() if field.required else self.font())
            self.table.setItem(row, 0, name_item)

            # Label
            label_item = QTableWidgetItem(field.label)
            self.table.setItem(row, 1, label_item)

            # Relationship Name
            relationship_name = field.relationship_name or ""
            rel_item = QTableWidgetItem(relationship_name)
            rel_item.setForeground(QColor('#9050e9'))  # Purple for relationship names
            self.table.setItem(row, 2, rel_item)

            # References To
            references = ", ".join(field.reference_to) if field.reference_to else ""
            ref_item = QTableWidgetItem(references)
            ref_item.setForeground(QColor('#0176d3'))  # Blue for target objects
            self.table.setItem(row, 3, ref_item)

            # Type (determine if lookup or master-detail)
            # Master-detail fields are always required and not deletable
            if field.required and not field.updateable:
                rel_type = "Master-Detail"
                type_color = QColor('#c23934')  # Red for master-detail
            else:
                rel_type = "Lookup"
                type_color = QColor('#2e844a')  # Green for lookup

            type_item = QTableWidgetItem(rel_type)
            type_item.setForeground(type_color)
            type_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, type_item)

            # Required
            required_item = QTableWidgetItem("✓" if field.required else "")
            required_item.setTextAlignment(Qt.AlignCenter)
            if field.required:
                required_item.setForeground(QColor('#c23934'))  # Red for required
            self.table.setItem(row, 5, required_item)

    def clear(self):
        """Clear both tables."""
        self.table.setRowCount(0)
        self.record_types_table.setRowCount(0)
        self.relationships = []
        self.current_object_name = None
        self.info_label.setText("Field Relationships")
        self.record_types_label.setText("Record Types & Page Layouts")

    def show_loading(self):
        """Show loading state."""
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        loading_item = QTableWidgetItem("Loading relationships...")
        loading_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(0, 0, loading_item)

        self.record_types_table.setRowCount(1)
        self.record_types_table.setColumnCount(2)
        self.record_types_table.setHorizontalHeaderLabels([
            "Record Type",
            "Assigned Page Layout"
        ])
        rt_loading_item = QTableWidgetItem("Loading record types...")
        rt_loading_item.setTextAlignment(Qt.AlignCenter)
        self.record_types_table.setItem(0, 0, rt_loading_item)
        self.record_types_table.setSpan(0, 0, 1, 2)  # Span across both columns

    def _get_bold_font(self):
        """Get bold font for required fields."""
        font = self.font()
        font.setBold(True)
        return font

    def _on_layout_row_clicked(self, item: QTableWidgetItem):
        """
        Handle click on record type/layout row.

        Args:
            item: The clicked table item
        """
        row = item.row()

        # Get record type ID and layout ID for this row
        if row in self.record_type_data:
            record_type_id, layout_id = self.record_type_data[row]

            if layout_id:
                # Emit signal with record type ID and layout ID
                self.layout_clicked.emit(record_type_id, layout_id)
            else:
                # Layout not loaded yet
                pass
