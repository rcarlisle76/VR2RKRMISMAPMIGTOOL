"""
Load progress dialog - shows progress during data loading.

Displays real-time progress, success/failure counts, and allows cancellation.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class LoadProgressDialog(QDialog):
    """
    Dialog for showing data load progress.
    """

    def __init__(self, parent=None):
        """Initialize the progress dialog."""
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Loading Data to Salesforce")
        self.setModal(True)
        self.setFixedSize(500, 300)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title
        title_label = QLabel("Loading Data...")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v of %m records processed (%p%)")
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Preparing data...")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.status_label)

        # Stats label
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.stats_label)

        # Error log (hidden by default)
        self.error_log = QTextEdit()
        self.error_log.setReadOnly(True)
        self.error_log.setMaximumHeight(100)
        self.error_log.setStyleSheet("background-color: #fff3cd; color: #856404; font-size: 10px;")
        self.error_log.hide()
        layout.addWidget(self.error_log)

        layout.addStretch()

        # Close button (initially hidden)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.hide()
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def set_total(self, total: int):
        """
        Set total number of records.

        Args:
            total: Total record count
        """
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)

    def update_status(self, message: str):
        """
        Update the status message.

        Args:
            message: Status message to display
        """
        self.status_label.setText(message)

    def update_progress(self, current: int, successful: int, failed: int):
        """
        Update progress.

        Args:
            current: Current record number
            successful: Number of successful records
            failed: Number of failed records
        """
        self.progress_bar.setValue(current)

        # Update status
        self.status_label.setText(f"Processing record {current} of {self.progress_bar.maximum()}...")

        # Update stats
        self.stats_label.setText(
            f'<span style="color: #2e844a;">✓ {successful} successful</span> • '
            f'<span style="color: #c23934;">✗ {failed} failed</span>'
        )

    def add_error(self, row: int, error: str):
        """
        Add an error to the log.

        Args:
            row: Row number
            error: Error message
        """
        self.error_log.show()
        self.error_log.append(f"Row {row}: {error}")

    def set_complete(self, successful: int, failed: int):
        """
        Mark operation as complete.

        Args:
            successful: Number of successful records
            failed: Number of failed records
        """
        self.status_label.setText("Load complete!")

        if failed == 0:
            self.status_label.setStyleSheet("color: #2e844a; font-size: 12px; font-weight: bold;")
            self.status_label.setText(f"✓ Successfully loaded {successful} records!")
        else:
            self.status_label.setStyleSheet("color: #fe9339; font-size: 12px; font-weight: bold;")
            self.status_label.setText(
                f"Load complete with {failed} errors. {successful} records loaded successfully."
            )

        # Show close button
        self.close_button.show()

    def set_error(self, error_message: str):
        """
        Show error state.

        Args:
            error_message: Error message
        """
        self.status_label.setText("Error during load")
        self.status_label.setStyleSheet("color: #c23934; font-size: 12px; font-weight: bold;")

        self.error_log.show()
        self.error_log.setText(error_message)

        self.close_button.show()
