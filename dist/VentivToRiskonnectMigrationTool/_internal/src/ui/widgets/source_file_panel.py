"""
Source file panel - displays imported file information and column list.

Shows file metadata and source columns with types and samples.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QPushButton, QFileDialog, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import Optional

from ...models.mapping_models import SourceFile


class SourceFilePanel(QWidget):
    """
    Panel for displaying source file information and columns.
    """

    # Signals
    file_imported = pyqtSignal(object)  # SourceFile
    template_download_requested = pyqtSignal()  # Request to download template

    def __init__(self):
        """Initialize the source file panel."""
        super().__init__()
        self.current_file: Optional[SourceFile] = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header with import button
        header_layout = QHBoxLayout()

        title_label = QLabel("Source File")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Download Template button
        self.template_button = QPushButton("Download Template")
        self.template_button.setStyleSheet("""
            QPushButton {
                background-color: #706e6b;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #514f4d;
            }
            QPushButton:disabled {
                background-color: #dddbda;
                color: #706e6b;
            }
        """)
        self.template_button.setToolTip("Download a CSV template with all required fields for the selected Salesforce object")
        self.template_button.clicked.connect(self._on_template_download_clicked)
        self.template_button.setEnabled(False)  # Disabled until object is selected
        header_layout.addWidget(self.template_button)

        self.import_button = QPushButton("Import CSV...")
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

        # File info group
        self.file_info_group = QGroupBox("File Information")
        file_info_layout = QVBoxLayout()

        self.file_path_label = QLabel("No file imported")
        self.file_path_label.setWordWrap(True)
        self.file_path_label.setStyleSheet("color: #666;")
        file_info_layout.addWidget(self.file_path_label)

        self.file_stats_label = QLabel("")
        self.file_stats_label.setStyleSheet("color: #333; font-weight: bold;")
        file_info_layout.addWidget(self.file_stats_label)

        self.file_info_group.setLayout(file_info_layout)
        self.file_info_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        layout.addWidget(self.file_info_group)

        # Columns label
        self.columns_label = QLabel("Columns (0)")
        self.columns_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.columns_label)

        # Columns table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Column Name",
            "Type",
            "Null %",
            "Sample Values"
        ])

        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Column Name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Null %
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Sample Values

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

    def set_file(self, source_file: SourceFile):
        """
        Display source file information.

        Args:
            source_file: SourceFile to display
        """
        self.current_file = source_file

        # Update file info
        self.file_path_label.setText(f"Path: {source_file.file_path}")
        self.file_stats_label.setText(
            f"{source_file.total_rows:,} rows • {len(source_file.columns)} columns"
        )

        # Update columns label
        self.columns_label.setText(f"Columns ({len(source_file.columns)})")

        # Clear and populate table
        self.table.setRowCount(0)

        for row_idx, column in enumerate(source_file.columns):
            self.table.insertRow(row_idx)

            # Column name
            name_item = QTableWidgetItem(column.name)
            name_item.setFont(self.font())
            self.table.setItem(row_idx, 0, name_item)

            # Type
            type_item = QTableWidgetItem(column.get_type_label())
            # Color code by type
            if column.inferred_type == 'number':
                type_item.setForeground(QColor('#0176d3'))
            elif column.inferred_type == 'date':
                type_item.setForeground(QColor('#2e844a'))
            elif column.inferred_type == 'boolean':
                type_item.setForeground(QColor('#c23934'))
            self.table.setItem(row_idx, 1, type_item)

            # Null percentage
            if column.sample_values:
                null_pct = (column.null_count / len(column.sample_values)) * 100
                null_item = QTableWidgetItem(f"{null_pct:.0f}%")
                if null_pct > 50:
                    null_item.setForeground(QColor('#c23934'))
                elif null_pct > 20:
                    null_item.setForeground(QColor('#fe9339'))
                self.table.setItem(row_idx, 2, null_item)

            # Sample values (first 3)
            sample_display = ', '.join(str(v) for v in column.sample_values[:3] if v)
            if len(sample_display) > 50:
                sample_display = sample_display[:47] + "..."
            sample_item = QTableWidgetItem(sample_display)
            sample_item.setToolTip(sample_display)  # Full text on hover
            self.table.setItem(row_idx, 3, sample_item)

    def clear(self):
        """Clear the panel."""
        self.current_file = None
        self.file_path_label.setText("No file imported")
        self.file_stats_label.setText("")
        self.columns_label.setText("Columns (0)")
        self.table.setRowCount(0)

    def enable_template_download(self, enabled: bool):
        """
        Enable or disable the template download button.

        Args:
            enabled: True to enable, False to disable
        """
        self.template_button.setEnabled(enabled)

    def _on_import_clicked(self):
        """Handle import button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Source File",
            "",
            "CSV Files (*.csv);;All Files (*.*)"
        )

        if file_path:
            # Emit signal with file path
            # The presenter will handle the actual import
            self.file_imported.emit(file_path)

    def _on_template_download_clicked(self):
        """Handle template download button click."""
        self.template_download_requested.emit()
