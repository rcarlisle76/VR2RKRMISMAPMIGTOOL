"""
Object list widget - displays list of Salesforce objects with search/filter.

Part of the left panel in the main window.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QCheckBox, QHBoxLayout, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import List

from ...models.salesforce_metadata import ObjectListItem


class ObjectListWidget(QWidget):
    """
    Widget for displaying and filtering Salesforce objects.

    Emits signals when objects are selected.
    """

    # Signals
    object_selected = pyqtSignal(str)  # object_name

    def __init__(self):
        """Initialize the object list widget."""
        super().__init__()
        self.all_objects: List[ObjectListItem] = []
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title = QLabel("Objects")
        title_font = title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search objects...")
        self.search_box.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_box)

        # Filter checkboxes
        filter_layout = QHBoxLayout()

        self.standard_checkbox = QCheckBox("Standard")
        self.standard_checkbox.setChecked(True)
        self.standard_checkbox.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.standard_checkbox)

        self.custom_checkbox = QCheckBox("Custom")
        self.custom_checkbox.setChecked(True)
        self.custom_checkbox.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.custom_checkbox)

        layout.addLayout(filter_layout)

        # Object list
        self.object_list = QListWidget()
        self.object_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.object_list)

        # Object count label
        self.count_label = QLabel("0 objects")
        self.count_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.count_label)

        self.setLayout(layout)

    def set_objects(self, objects: List[ObjectListItem]):
        """
        Set the list of objects to display.

        Args:
            objects: List of ObjectListItem objects
        """
        self.all_objects = objects
        self._update_display()

    def _update_display(self):
        """Update the displayed object list based on filters and search."""
        self.object_list.clear()

        # Apply filters
        filtered = []
        for obj in self.all_objects:
            # Check standard/custom filter
            if obj.custom and not self.custom_checkbox.isChecked():
                continue
            if not obj.custom and not self.standard_checkbox.isChecked():
                continue

            # Check search filter
            search_text = self.search_box.text().lower()
            if search_text:
                if search_text not in obj.name.lower() and search_text not in obj.label.lower():
                    continue

            filtered.append(obj)

        # Sort by label
        filtered.sort(key=lambda x: x.label)

        # Add to list
        for obj in filtered:
            item = QListWidgetItem()

            # Display format: "Account (Standard)" or "Custom_Object__c (Custom)"
            object_type = "Custom" if obj.custom else "Standard"
            display_text = f"{obj.label}"

            item.setText(display_text)
            item.setData(Qt.UserRole, obj.name)  # Store API name

            # Color code custom objects
            if obj.custom:
                item.setForeground(Qt.blue)

            self.object_list.addItem(item)

        # Update count
        custom_count = sum(1 for o in filtered if o.custom)
        standard_count = len(filtered) - custom_count
        self.count_label.setText(
            f"{len(filtered)} objects ({standard_count} standard, {custom_count} custom)"
        )

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self._update_display()

    def _on_filter_changed(self, state: int):
        """Handle filter checkbox change."""
        self._update_display()

    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle object selection."""
        object_name = item.data(Qt.UserRole)
        if object_name:
            self.object_selected.emit(object_name)

    def clear_selection(self):
        """Clear the current selection."""
        self.object_list.clearSelection()

    def show_loading(self, loading: bool):
        """
        Show/hide loading state.

        Args:
            loading: True to show loading, False to hide
        """
        if loading:
            self.object_list.clear()
            item = QListWidgetItem("Loading objects...")
            item.setFlags(Qt.NoItemFlags)
            self.object_list.addItem(item)
            self.search_box.setEnabled(False)
            self.standard_checkbox.setEnabled(False)
            self.custom_checkbox.setEnabled(False)
        else:
            self.search_box.setEnabled(True)
            self.standard_checkbox.setEnabled(True)
            self.custom_checkbox.setEnabled(True)
