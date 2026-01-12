"""
Field detail panel - displays detailed information about a selected field.

Shows all field properties in a readable format.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import Optional

from ...models.salesforce_metadata import SalesforceField


class FieldDetailPanel(QWidget):
    """
    Panel for displaying detailed information about a single field.
    """

    def __init__(self):
        """Initialize the field detail panel."""
        super().__init__()
        self.current_field: Optional[SalesforceField] = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for field details
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout.setSpacing(15)
        self.content_layout.setAlignment(Qt.AlignTop)

        # Title label
        self.title_label = QLabel("Select a field to view details")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(True)
        self.content_layout.addWidget(self.title_label)

        # Details container
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        self.details_layout.setContentsMargins(0, 10, 0, 0)
        self.details_layout.setSpacing(12)
        self.details_widget.setLayout(self.details_layout)
        self.content_layout.addWidget(self.details_widget)

        self.content_layout.addStretch()
        self.content_widget.setLayout(self.content_layout)

        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)

        self.setLayout(layout)

        # Apply styling
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            QScrollArea {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
        """)

    def set_field(self, field: SalesforceField):
        """
        Display field details.

        Args:
            field: SalesforceField to display
        """
        self.current_field = field

        # Update title
        self.title_label.setText(f"{field.label}")

        # Clear existing details
        self._clear_details()

        # Add field details
        self._add_detail("API Name", field.name, bold_value=True)
        self._add_detail("Type", field.type.title())

        if field.length:
            self._add_detail("Length", str(field.length))

        # Required status
        required_text = "Yes" if field.required else "No"
        required_color = "#c23934" if field.required else "#2e844a"
        self._add_detail("Required", required_text, value_color=required_color)

        # Createable
        self._add_detail("Createable", "Yes" if field.createable else "No")

        # Updateable
        self._add_detail("Updateable", "Yes" if field.updateable else "No")

        # Relationship info
        if field.relationship_name:
            self._add_detail("Relationship Name", field.relationship_name)

        if field.reference_to:
            ref_text = ", ".join(field.reference_to)
            self._add_detail("References", ref_text, value_color="#0176d3")

        # Picklist values
        if field.picklist_values:
            values_text = "\n".join(f"• {value}" for value in field.picklist_values)
            self._add_detail("Picklist Values", values_text, multiline=True)

    def clear(self):
        """Clear the panel."""
        self.current_field = None
        self.title_label.setText("Select a field to view details")
        self._clear_details()

    def _clear_details(self):
        """Clear all detail widgets."""
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_detail(self, label: str, value: str, bold_value: bool = False,
                    value_color: Optional[str] = None, multiline: bool = False):
        """
        Add a detail row to the panel.

        Args:
            label: Detail label
            value: Detail value
            bold_value: Whether to bold the value
            value_color: Optional color for the value
            multiline: Whether this is a multiline value
        """
        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #666; font-size: 11px;")
        self.details_layout.addWidget(label_widget)

        # Value
        value_widget = QLabel(value)
        value_widget.setWordWrap(True)

        # Styling
        style_parts = ["font-size: 13px;"]
        if bold_value:
            style_parts.append("font-weight: bold;")
        if value_color:
            style_parts.append(f"color: {value_color};")
        else:
            style_parts.append("color: #333;")

        value_widget.setStyleSheet(" ".join(style_parts))

        if multiline:
            value_widget.setTextFormat(Qt.PlainText)

        self.details_layout.addWidget(value_widget)

        # Add spacing
        if not multiline:
            self.details_layout.addSpacing(5)
