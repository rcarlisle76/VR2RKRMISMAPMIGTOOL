"""
Main application window (View in MVP pattern).

Displays the object browser and detail panels after successful login.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QLabel, QVBoxLayout, QStatusBar, QMenuBar, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from .widgets.object_list_widget import ObjectListWidget
from .widgets.object_detail_widget import ObjectDetailWidget


class MainWindow(QMainWindow):
    """
    Main application window after login.

    Contains object list and detail panels.
    """

    # Signals
    object_selected = pyqtSignal(str)  # object_name
    logout_requested = pyqtSignal()

    def __init__(self, username: str = ""):
        """
        Initialize the main window.

        Args:
            username: Logged in username to display
        """
        super().__init__()
        self.username = username
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Ventiv to Riskonnect Migration Tool")
        self.setGeometry(100, 100, 1200, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create menu bar
        self._create_menu_bar()

        # Create splitter for left/right panels
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Object list
        self.object_list_widget = ObjectListWidget()
        self.object_list_widget.object_selected.connect(self._on_object_selected)
        splitter.addWidget(self.object_list_widget)

        # Right panel: Object detail widget
        self.object_detail_widget = ObjectDetailWidget()
        splitter.addWidget(self.object_detail_widget)

        # Set splitter sizes (30% left, 70% right)
        splitter.setSizes([360, 840])

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status(f"Connected as {self.username}")

        # Apply styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QSplitter::handle {
                background-color: #d0d0d0;
                width: 2px;
            }
        """)

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self._on_logout_clicked)
        file_menu.addAction(logout_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        refresh_action = QAction("Refresh Objects", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._on_refresh_clicked)
        tools_menu.addAction(refresh_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._on_about_clicked)
        help_menu.addAction(about_action)

    def _on_object_selected(self, object_name: str):
        """Handle object selection from list."""
        self.update_status(f"Selected: {object_name}")
        self.object_selected.emit(object_name)

    def _on_logout_clicked(self):
        """Handle logout menu click."""
        self.logout_requested.emit()

    def _on_refresh_clicked(self):
        """Handle refresh menu click."""
        self.update_status("Refreshing objects...")
        # Presenter will handle actual refresh

    def _on_about_clicked(self):
        """Handle about menu click."""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "About",
            "Salesforce Migration Tool\n\n"
            "Version: 1.0 (Phase 2)\n\n"
            "A professional data migration tool for Salesforce.\n\n"
            "© 2025"
        )

    def update_status(self, message: str):
        """
        Update status bar message.

        Args:
            message: Status message to display
        """
        self.status_bar.showMessage(message)

    def show_error(self, title: str, message: str):
        """
        Show error message dialog.

        Args:
            title: Error dialog title
            message: Error message
        """
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)

    def show_info(self, title: str, message: str, show_cancel: bool = False):
        """
        Show info message dialog.

        Args:
            title: Info dialog title
            message: Info message
            show_cancel: Whether to show cancel button

        Returns:
            True if OK clicked, False if Cancel clicked
        """
        from PyQt5.QtWidgets import QMessageBox
        if show_cancel:
            result = QMessageBox.question(
                self,
                title,
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            return result == QMessageBox.Yes
        else:
            QMessageBox.information(self, title, message)
            return True
