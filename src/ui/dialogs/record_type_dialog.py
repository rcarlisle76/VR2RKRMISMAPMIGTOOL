"""
Record type selection dialog.

Allows user to select a record type before loading data.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import List, Optional

from ...models.salesforce_metadata import RecordType


class RecordTypeDialog(QDialog):
    """
    Dialog for selecting a record type.
    """

    def __init__(self, record_types: List[RecordType], object_label: str, parent=None):
        """
        Initialize the record type dialog.

        Args:
            record_types: List of available record types
            object_label: Display label of the Salesforce object
            parent: Parent widget
        """
        super().__init__(parent)
        self.record_types = record_types
        self.selected_record_type: Optional[RecordType] = None
        self.init_ui(object_label)

    def init_ui(self, object_label: str):
        """Initialize the user interface."""
        self.setWindowTitle("Select Record Type")
        self.setModal(True)
        self.setFixedWidth(450)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title
        title_label = QLabel(f"Select Record Type for {object_label}")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "This object has multiple record types. "
            "Please select which record type to use for the new records."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(desc_label)

        # Record type dropdown
        combo_label = QLabel("Record Type:")
        layout.addWidget(combo_label)

        self.record_type_combo = QComboBox()
        for rt in self.record_types:
            display_text = str(rt)  # Uses RecordType.__str__ which includes (Default) marker
            self.record_type_combo.addItem(display_text, rt)

        # Select first item by default
        if self.record_types:
            self.record_type_combo.setCurrentIndex(0)

        self.record_type_combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #0176d3;
            }
        """)
        layout.addWidget(self.record_type_combo)

        layout.addStretch()

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def accept(self):
        """Handle OK button click."""
        # Get selected record type
        index = self.record_type_combo.currentIndex()
        if index >= 0:
            self.selected_record_type = self.record_type_combo.itemData(index)
        super().accept()

    def get_selected_record_type(self) -> Optional[RecordType]:
        """
        Get the selected record type.

        Returns:
            Selected RecordType or None if cancelled
        """
        return self.selected_record_type
