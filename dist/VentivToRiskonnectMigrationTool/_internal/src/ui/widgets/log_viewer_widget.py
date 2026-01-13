"""
Log viewer widget for displaying application logs.
"""
import os
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QComboBox, QLabel, QCheckBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QTextCursor


class LogViewerWidget(QWidget):
    """Widget for viewing application logs in real-time."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_dir = os.path.expanduser("~/.salesforce_migration_tool/logs")
        self.current_log_file: Optional[str] = None
        self.auto_refresh_enabled = False

        self._setup_ui()
        self._setup_auto_refresh()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Controls row
        controls_layout = QHBoxLayout()

        # Log file selector
        controls_layout.addWidget(QLabel("Log File:"))
        self.log_combo = QComboBox()
        self.log_combo.addItem("migration_tool.log (INFO)", "migration_tool.log")
        self.log_combo.addItem("migration_tool_error.log (ERROR)", "migration_tool_error.log")
        self.log_combo.currentIndexChanged.connect(self._on_log_file_changed)
        controls_layout.addWidget(self.log_combo)

        controls_layout.addStretch()

        # Auto-refresh checkbox
        self.auto_refresh_checkbox = QCheckBox("Auto-refresh")
        self.auto_refresh_checkbox.setChecked(True)
        self.auto_refresh_checkbox.stateChanged.connect(self._on_auto_refresh_changed)
        controls_layout.addWidget(self.auto_refresh_checkbox)

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_log)
        controls_layout.addWidget(self.refresh_button)

        # Clear button
        clear_button = QPushButton("Clear Display")
        clear_button.clicked.connect(self._clear_display)
        controls_layout.addWidget(clear_button)

        layout.addLayout(controls_layout)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
        """)
        layout.addWidget(self.log_text)

        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: gray; font-size: 8pt;")
        layout.addWidget(self.status_label)

        # Set initial log file
        self.current_log_file = "migration_tool.log"
        self.auto_refresh_enabled = True

    def _setup_auto_refresh(self):
        """Set up auto-refresh timer."""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_log)
        self.refresh_timer.start(2000)  # Refresh every 2 seconds

    def _on_log_file_changed(self, index: int):
        """Handle log file selection change."""
        self.current_log_file = self.log_combo.itemData(index)
        self.load_log()

    def _on_auto_refresh_changed(self, state: int):
        """Handle auto-refresh checkbox state change."""
        self.auto_refresh_enabled = (state == Qt.Checked)
        if self.auto_refresh_enabled:
            self.refresh_timer.start(2000)
        else:
            self.refresh_timer.stop()

    def load_log(self):
        """Load and display the current log file."""
        if not self.current_log_file:
            return

        log_path = os.path.join(self.log_dir, self.current_log_file)

        if not os.path.exists(log_path):
            self.log_text.setPlainText(f"Log file not found: {log_path}")
            self.status_label.setText("Log file not found")
            return

        try:
            # Read the last 1000 lines of the log file
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Keep last 1000 lines to prevent memory issues
            if len(lines) > 1000:
                lines = lines[-1000:]
                display_text = "... (showing last 1000 lines)\n\n" + "".join(lines)
            else:
                display_text = "".join(lines)

            # Store current scroll position
            scrollbar = self.log_text.verticalScrollBar()
            was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 10

            # Update text
            self.log_text.setPlainText(display_text)

            # Auto-scroll to bottom if we were already at bottom
            if was_at_bottom:
                self.log_text.moveCursor(QTextCursor.End)

            # Update status
            file_size = os.path.getsize(log_path)
            size_kb = file_size / 1024
            self.status_label.setText(f"Loaded {len(lines)} lines ({size_kb:.1f} KB)")

        except Exception as e:
            self.log_text.setPlainText(f"Error reading log file: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")

    def _clear_display(self):
        """Clear the log display."""
        self.log_text.clear()
        self.status_label.setText("Display cleared")

    def clear(self):
        """Clear the widget (called when switching objects)."""
        # Don't clear logs when switching objects - keep them visible
        pass

    def showEvent(self, event):
        """Load logs when the tab is shown."""
        super().showEvent(event)
        self.load_log()
