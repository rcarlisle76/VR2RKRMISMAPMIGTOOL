"""
Field usage widget - displays field usage statistics from HTML reports.

Shows a list of tables and detailed field statistics for each.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QSplitter,
    QGroupBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from typing import Optional

from ...models.field_usage_models import FieldUsageReport, TableUsageReport


class FieldUsageWidget(QWidget):
    """Widget for displaying field usage statistics from HTML report."""

    # Signals
    import_report_requested = pyqtSignal()

    def __init__(self):
        """Initialize the field usage widget."""
        super().__init__()
        self.current_report: Optional[FieldUsageReport] = None
        self.current_table: Optional[TableUsageReport] = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header with title and import button
        header_layout = QHBoxLayout()

        title_label = QLabel("Field Usage Report")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.import_button = QPushButton("Import Usage Report...")
        self.import_button.setStyleSheet("""
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
        """)
        self.import_button.clicked.connect(self._on_import_clicked)
        header_layout.addWidget(self.import_button)

        layout.addLayout(header_layout)

        # Report info label
        self.report_info_label = QLabel("No report loaded")
        self.report_info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.report_info_label)

        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Table list
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        self.table_list_label = QLabel("Tables (0)")
        self.table_list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(self.table_list_label)

        self.table_list = QListWidget()
        self.table_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #0176d3;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #f3f3f3;
            }
        """)
        self.table_list.currentItemChanged.connect(self._on_table_selected)
        left_layout.addWidget(self.table_list)

        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)

        # Right panel - Field statistics table
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        self.fields_label = QLabel("Fields")
        self.fields_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(self.fields_label)

        self.fields_table = QTableWidget()
        self.fields_table.setColumnCount(8)
        self.fields_table.setHorizontalHeaderLabels([
            "Column Name", "Data Type", "Max Size", "Count",
            "Distinct", "Null %", "Min", "Max"
        ])

        # Configure table
        self.fields_table.setAlternatingRowColors(True)
        self.fields_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.fields_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.fields_table.verticalHeader().setVisible(False)
        self.fields_table.setSortingEnabled(True)

        # Set column widths
        header = self.fields_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Column Name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Data Type
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Max Size
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Count
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Distinct
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Null %
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Min
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Max

        # Apply styling
        self.fields_table.setStyleSheet("""
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

        right_layout.addWidget(self.fields_table)

        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)

        # Set splitter sizes (30% left, 70% right)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

        self.setLayout(layout)

    def set_report(self, report: FieldUsageReport):
        """
        Display the usage report.

        Args:
            report: FieldUsageReport to display
        """
        self.current_report = report
        self.current_table = None

        # Update report info
        self.report_info_label.setText(
            f"Loaded: {report.file_path}"
        )
        self.report_info_label.setStyleSheet("color: #2e844a; font-style: normal;")

        # Update table list
        self.table_list_label.setText(f"Tables ({report.table_count})")
        self.table_list.clear()

        for table in report.tables:
            item = QListWidgetItem(f"{table.display_name} ({table.field_count})")
            item.setData(Qt.UserRole, table.table_name)  # Store table ID
            self.table_list.addItem(item)

        # Clear fields table
        self.fields_table.setRowCount(0)
        self.fields_label.setText("Fields")

        # Select first table if available
        if report.tables:
            self.table_list.setCurrentRow(0)

    def _on_table_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle table selection change."""
        if not current or not self.current_report:
            return

        table_id = current.data(Qt.UserRole)
        table = self.current_report.get_table_by_name(table_id)

        if table:
            self._display_table_fields(table)

    def _display_table_fields(self, table: TableUsageReport):
        """
        Display fields for the selected table.

        Args:
            table: TableUsageReport to display
        """
        self.current_table = table
        self.fields_label.setText(f"Fields for: {table.display_name} ({table.field_count})")

        # Disable sorting while populating
        self.fields_table.setSortingEnabled(False)
        self.fields_table.setRowCount(0)

        for row_idx, field in enumerate(table.fields):
            self.fields_table.insertRow(row_idx)

            # Column Name
            name_item = QTableWidgetItem(field.column_name)
            name_item.setFont(QFont("", -1, QFont.Bold))
            self.fields_table.setItem(row_idx, 0, name_item)

            # Data Type
            type_item = QTableWidgetItem(field.data_type)
            # Color code by type
            if 'NUMBER' in field.data_type.upper() or 'INT' in field.data_type.upper():
                type_item.setForeground(QColor('#0176d3'))
            elif 'DATE' in field.data_type.upper() or 'TIME' in field.data_type.upper():
                type_item.setForeground(QColor('#2e844a'))
            elif 'VARCHAR' in field.data_type.upper() or 'CHAR' in field.data_type.upper():
                type_item.setForeground(QColor('#706e6b'))
            self.fields_table.setItem(row_idx, 1, type_item)

            # Max Size
            max_size_item = QTableWidgetItem(str(field.max_size) if field.max_size else "")
            max_size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.fields_table.setItem(row_idx, 2, max_size_item)

            # Count
            count_item = QTableWidgetItem(f"{field.count:,}")
            count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            count_item.setData(Qt.UserRole, field.count)  # For sorting
            self.fields_table.setItem(row_idx, 3, count_item)

            # Distinct
            distinct_item = QTableWidgetItem(f"{field.distinct:,}")
            distinct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            distinct_item.setData(Qt.UserRole, field.distinct)  # For sorting
            self.fields_table.setItem(row_idx, 4, distinct_item)

            # Null %
            null_pct = field.null_percentage
            null_item = QTableWidgetItem(f"{null_pct:.1f}%")
            null_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            null_item.setData(Qt.UserRole, null_pct)  # For sorting

            # Color code by null percentage
            if null_pct > 50:
                null_item.setForeground(QColor('#c23934'))  # Red
                null_item.setBackground(QColor('#ffd0d0'))  # Light red background
            elif null_pct > 20:
                null_item.setForeground(QColor('#fe9339'))  # Orange
            self.fields_table.setItem(row_idx, 5, null_item)

            # Min
            min_item = QTableWidgetItem(field.min_value or "")
            if field.min_value and len(field.min_value) > 20:
                min_item.setText(field.min_value[:17] + "...")
                min_item.setToolTip(field.min_value)
            self.fields_table.setItem(row_idx, 6, min_item)

            # Max
            max_item = QTableWidgetItem(field.max_value or "")
            if field.max_value and len(field.max_value) > 20:
                max_item.setText(field.max_value[:17] + "...")
                max_item.setToolTip(field.max_value)
            self.fields_table.setItem(row_idx, 7, max_item)

        # Re-enable sorting
        self.fields_table.setSortingEnabled(True)

    def highlight_table(self, table_name: str):
        """
        Highlight and scroll to a specific table.

        Args:
            table_name: Table name or display name to highlight
        """
        if not self.current_report:
            return

        # Find the table in the list
        for i in range(self.table_list.count()):
            item = self.table_list.item(i)
            table_id = item.data(Qt.UserRole)

            if table_id.lower() == table_name.lower():
                self.table_list.setCurrentItem(item)
                self.table_list.scrollToItem(item)
                return

            # Also check display name
            table = self.current_report.get_table_by_name(table_id)
            if table and table.display_name.lower() == table_name.lower():
                self.table_list.setCurrentItem(item)
                self.table_list.scrollToItem(item)
                return

    def _on_import_clicked(self):
        """Handle import button click."""
        self.import_report_requested.emit()

    def clear(self):
        """Clear the widget."""
        self.current_report = None
        self.current_table = None
        self.report_info_label.setText("No report loaded")
        self.report_info_label.setStyleSheet("color: #666; font-style: italic;")
        self.table_list_label.setText("Tables (0)")
        self.table_list.clear()
        self.fields_label.setText("Fields")
        self.fields_table.setRowCount(0)
