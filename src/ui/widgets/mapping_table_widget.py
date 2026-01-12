"""
Mapping table widget - displays source-to-target field mappings.

Shows source columns with dropdowns to select target Salesforce fields.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLabel, QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon
from typing import List, Dict, Optional

from ...models.salesforce_metadata import SalesforceObject, SalesforceField
from ...models.mapping_models import SourceFile, FieldMapping, MappingConfiguration


class MappingTableWidget(QWidget):
    """
    Widget for displaying and editing field mappings.
    """

    # Signals
    mapping_changed = pyqtSignal(str, str)  # source_column, target_field
    auto_map_requested = pyqtSignal()
    validate_requested = pyqtSignal()
    save_requested = pyqtSignal()
    load_requested = pyqtSignal()
    load_data_requested = pyqtSignal()  # Load data to Salesforce

    def __init__(self):
        """Initialize the mapping table widget."""
        super().__init__()
        self.source_file: Optional[SourceFile] = None
        self.salesforce_object: Optional[SalesforceObject] = None
        self.mappings: Dict[str, str] = {}  # source_column -> target_field
        self.confidence_scores: Dict[str, float] = {}  # source_column -> confidence
        self.mapping_methods: Dict[str, str] = {}  # source_column -> method
        self.combo_boxes: Dict[str, QComboBox] = {}  # source_column -> combo
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header with buttons
        header_layout = QHBoxLayout()

        title_label = QLabel("Field Mappings")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Load button
        self.load_button = QPushButton("Load Mapping...")
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #706e6b;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a5856;
            }
            QPushButton:disabled {
                background-color: #d0d0d0;
                color: #666;
            }
        """)
        self.load_button.clicked.connect(self._on_load_clicked)
        self.load_button.setEnabled(False)
        header_layout.addWidget(self.load_button)

        # Save button
        self.save_button = QPushButton("Save Mapping...")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #706e6b;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a5856;
            }
            QPushButton:disabled {
                background-color: #d0d0d0;
                color: #666;
            }
        """)
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.setEnabled(False)
        header_layout.addWidget(self.save_button)

        # Auto-map button
        self.auto_map_button = QPushButton("Auto-Map")
        self.auto_map_button.setStyleSheet("""
            QPushButton {
                background-color: #2e844a;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1f5a30;
            }
            QPushButton:disabled {
                background-color: #d0d0d0;
                color: #666;
            }
        """)
        self.auto_map_button.clicked.connect(self._on_auto_map_clicked)
        self.auto_map_button.setEnabled(False)
        header_layout.addWidget(self.auto_map_button)

        # Load Data button
        self.load_data_button = QPushButton("Load Data to Salesforce")
        self.load_data_button.setStyleSheet("""
            QPushButton {
                background-color: #0176d3;
                color: white;
                border: none;
                padding: 6px 12px;
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
        self.load_data_button.clicked.connect(self._on_load_data_clicked)
        self.load_data_button.setEnabled(False)
        header_layout.addWidget(self.load_data_button)

        layout.addLayout(header_layout)

        # Mapping stats
        self.stats_label = QLabel("0 of 0 required fields mapped")
        self.stats_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.stats_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Source Column",
            "→",
            "Salesforce Field",
            "Confidence",
            "Method",
            "Status"
        ])

        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Source Column
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Arrow
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Salesforce Field
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Confidence
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Method
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Status

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

    def set_data(self, source_file: SourceFile, salesforce_object: SalesforceObject):
        """
        Set source file and target object.

        Args:
            source_file: SourceFile with columns
            salesforce_object: Target Salesforce object
        """
        self.source_file = source_file
        self.salesforce_object = salesforce_object
        self.mappings = {}
        self.confidence_scores = {}
        self.mapping_methods = {}
        self.combo_boxes = {}

        # Enable buttons
        self.auto_map_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.load_button.setEnabled(True)
        self.load_data_button.setEnabled(True)

        # Build field options
        self._build_table()
        self._update_stats()

    def set_mappings(self, mappings: List[FieldMapping]):
        """
        Apply mappings to the table.

        Args:
            mappings: List of FieldMapping objects
        """
        for mapping in mappings:
            # Store confidence score if available
            if mapping.confidence is not None:
                self.confidence_scores[mapping.source_column] = mapping.confidence
            # Store method if available
            if mapping.method is not None:
                self.mapping_methods[mapping.source_column] = mapping.method
            self._apply_mapping(mapping.source_column, mapping.target_field)

    def get_mappings(self) -> List[FieldMapping]:
        """
        Get current mappings.

        Returns:
            List of FieldMapping objects
        """
        mappings = []

        for source_col, target_field in self.mappings.items():
            if target_field:  # Skip unmapped fields
                # Check if target field is required
                sf_field = next(
                    (f for f in self.salesforce_object.fields if f.name == target_field),
                    None
                )
                is_required = sf_field.required if sf_field else False

                mapping = FieldMapping(
                    source_column=source_col,
                    target_field=target_field,
                    mapping_type='direct',
                    is_required=is_required
                )
                mappings.append(mapping)

        return mappings

    def clear(self):
        """Clear the table."""
        self.table.setRowCount(0)
        self.source_file = None
        self.salesforce_object = None
        self.mappings = {}
        self.confidence_scores = {}
        self.mapping_methods = {}
        self.combo_boxes = {}
        self.auto_map_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.load_button.setEnabled(False)
        self.load_data_button.setEnabled(False)
        self.stats_label.setText("0 of 0 required fields mapped")

    def _build_table(self):
        """Build the mapping table."""
        if not self.source_file or not self.salesforce_object:
            return

        self.table.setRowCount(len(self.source_file.columns))

        for row_idx, source_col in enumerate(self.source_file.columns):
            # Source column name
            source_item = QTableWidgetItem(source_col.name)
            source_item.setFlags(source_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 0, source_item)

            # Arrow
            arrow_item = QTableWidgetItem("→")
            arrow_item.setTextAlignment(Qt.AlignCenter)
            arrow_item.setFlags(arrow_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 1, arrow_item)

            # Salesforce field dropdown
            combo = QComboBox()
            combo.addItem("(unmapped)", None)

            # Add Salesforce fields
            for sf_field in sorted(self.salesforce_object.fields, key=lambda f: f.label):
                display_text = f"{sf_field.label} ({sf_field.name})"
                if sf_field.required:
                    display_text += " *"
                combo.addItem(display_text, sf_field.name)

            # Disable mouse wheel scrolling to prevent accidental changes
            combo.wheelEvent = lambda event: None

            combo.currentIndexChanged.connect(
                lambda idx, col=source_col.name: self._on_mapping_changed(col, idx)
            )

            self.table.setCellWidget(row_idx, 2, combo)
            self.combo_boxes[source_col.name] = combo

            # Confidence percentage
            confidence_item = QTableWidgetItem("")
            confidence_item.setTextAlignment(Qt.AlignCenter)
            confidence_item.setFlags(confidence_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 3, confidence_item)

            # Method
            method_item = QTableWidgetItem("")
            method_item.setTextAlignment(Qt.AlignCenter)
            method_item.setFlags(method_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 4, method_item)

            # Status icon
            status_item = QTableWidgetItem("")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 5, status_item)

    def _apply_mapping(self, source_column: str, target_field: str):
        """
        Apply a mapping to the table.

        Args:
            source_column: Source column name
            target_field: Salesforce field API name
        """
        if source_column not in self.combo_boxes:
            return

        combo = self.combo_boxes[source_column]

        # Find and select the target field
        for i in range(combo.count()):
            if combo.itemData(i) == target_field:
                combo.setCurrentIndex(i)
                break

        # Update confidence display if available
        row = list(self.combo_boxes.keys()).index(source_column)
        confidence_item = self.table.item(row, 3)
        method_item = self.table.item(row, 4)

        if source_column in self.confidence_scores:
            confidence = self.confidence_scores[source_column]
            percentage = int(confidence * 100)
            confidence_item.setText(f"{percentage}%")

            # Color code based on confidence
            if confidence >= 0.9:
                confidence_item.setForeground(QColor('#2e844a'))  # Green
            elif confidence >= 0.75:
                confidence_item.setForeground(QColor('#fe9339'))  # Orange
            else:
                confidence_item.setForeground(QColor('#666'))  # Gray
        else:
            confidence_item.setText("")

        # Update method display if available
        if source_column in self.mapping_methods:
            method = self.mapping_methods[source_column]
            # Format method name for display
            method_display = method.upper() if method else ""
            method_item.setText(method_display)

            # Color code based on method
            if method == 'llm':
                method_item.setForeground(QColor('#0176d3'))  # Blue
            elif method == 'semantic':
                method_item.setForeground(QColor('#9050e9'))  # Purple
            elif method == 'fuzzy':
                method_item.setForeground(QColor('#706e6b'))  # Gray
            else:
                method_item.setForeground(QColor('#666'))  # Default gray
        else:
            method_item.setText("")

    def _on_mapping_changed(self, source_column: str, combo_index: int):
        """
        Handle mapping change from dropdown.

        Args:
            source_column: Source column name
            combo_index: Selected combo box index
        """
        combo = self.combo_boxes.get(source_column)
        if not combo:
            return

        target_field = combo.itemData(combo_index)

        # Update mappings
        if target_field:
            self.mappings[source_column] = target_field
        else:
            self.mappings.pop(source_column, None)

        # Update status icon
        row = list(self.combo_boxes.keys()).index(source_column)
        status_item = self.table.item(row, 5)

        if target_field:
            status_item.setText("✓")
            status_item.setForeground(QColor('#2e844a'))
        else:
            status_item.setText("")
            # Also clear confidence and method when unmapped
            confidence_item = self.table.item(row, 3)
            confidence_item.setText("")
            self.confidence_scores.pop(source_column, None)

            method_item = self.table.item(row, 4)
            method_item.setText("")
            self.mapping_methods.pop(source_column, None)

        # Update stats
        self._update_stats()

        # Emit signal
        self.mapping_changed.emit(source_column, target_field or "")

    def _update_stats(self):
        """Update mapping statistics."""
        if not self.salesforce_object:
            return

        # Count required fields
        required_fields = [f for f in self.salesforce_object.fields if f.required]
        mapped_required = [
            f for f in required_fields
            if f.name in self.mappings.values()
        ]

        # Update label
        total_mapped = len(self.mappings)
        self.stats_label.setText(
            f"{total_mapped} fields mapped • "
            f"{len(mapped_required)} of {len(required_fields)} required fields mapped"
        )

        # Color code based on required fields
        if len(mapped_required) == len(required_fields):
            self.stats_label.setStyleSheet("color: #2e844a; font-size: 11px; font-weight: bold;")
        elif len(mapped_required) > 0:
            self.stats_label.setStyleSheet("color: #fe9339; font-size: 11px; font-weight: bold;")
        else:
            self.stats_label.setStyleSheet("color: #c23934; font-size: 11px; font-weight: bold;")

    def _on_auto_map_clicked(self):
        """Handle auto-map button click."""
        self.auto_map_requested.emit()

    def _on_save_clicked(self):
        """Handle save button click."""
        self.save_requested.emit()

    def _on_load_clicked(self):
        """Handle load button click."""
        self.load_requested.emit()

    def _on_load_data_clicked(self):
        """Handle load data button click."""
        self.load_data_requested.emit()
