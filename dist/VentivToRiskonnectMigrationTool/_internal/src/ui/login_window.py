"""
Login window UI (View in MVP pattern).

Provides the user interface for Salesforce authentication.
Pure presentation layer with no business logic.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class LoginWindow(QMainWindow):
    """
    Login window for Salesforce authentication.

    Emits signals for user actions, handled by LoginPresenter.
    """

    # Signals
    login_requested = pyqtSignal(str, str, str, str, bool)  # username, password, token, instance_url, remember
    load_credentials_requested = pyqtSignal(str)  # username

    def __init__(self):
        """Initialize the login window."""
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Ventiv to Riskonnect Migration Tool - Login")
        self.setFixedSize(550, 620)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 50, 40, 40)

        # Title
        title_label = QLabel("Ventiv to Riskonnect Migration Tool")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setMinimumHeight(50)
        layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Connect to your Salesforce org")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #666;")
        layout.addWidget(subtitle_label)

        # Spacing
        layout.addSpacing(20)

        # Username field
        username_label = QLabel("Username (Email):")
        layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("your.email@example.com")
        self.username_input.setMinimumHeight(35)
        self.username_input.textChanged.connect(self._on_username_changed)
        layout.addWidget(self.username_input)

        # Spacing between fields
        layout.addSpacing(10)

        # Password field
        password_label = QLabel("Password:")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(35)
        layout.addWidget(self.password_input)

        # Spacing between fields
        layout.addSpacing(10)

        # Security token field
        token_label = QLabel("Security Token:")
        layout.addWidget(token_label)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Enter your security token")
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setMinimumHeight(35)
        layout.addWidget(self.token_input)

        # Spacing between fields
        layout.addSpacing(10)

        # Instance URL field
        instance_label = QLabel("Instance URL:")
        layout.addWidget(instance_label)

        self.instance_input = QLineEdit()
        self.instance_input.setText("https://login.salesforce.com")
        self.instance_input.setMinimumHeight(35)
        layout.addWidget(self.instance_input)

        # Spacing before checkbox
        layout.addSpacing(5)

        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember my credentials")
        layout.addWidget(self.remember_checkbox)

        # Spacing
        layout.addSpacing(10)

        # Login button
        self.login_button = QPushButton("Connect to Salesforce")
        self.login_button.setMinimumHeight(40)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #0176d3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0159a5;
            }
            QPushButton:pressed {
                background-color: #014a8c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.login_button.clicked.connect(self._on_login_clicked)
        layout.addWidget(self.login_button)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(40)
        layout.addWidget(self.status_label)

        # Help text
        help_label = QLabel('<a href="https://help.salesforce.com/s/articleView?id=sf.user_security_token.htm">How to get your security token?</a>')
        help_label.setOpenExternalLinks(True)
        help_label.setAlignment(Qt.AlignCenter)
        help_label.setStyleSheet("color: #0176d3; font-size: 13px;")
        layout.addWidget(help_label)

        # Set layout
        central_widget.setLayout(layout)

        # Apply global stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f3f3f3;
            }
            QLabel {
                color: #333;
                font-size: 11pt;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border: 1px solid #0176d3;
            }
            QCheckBox {
                color: #333;
                font-size: 11pt;
            }
        """)

    def _on_username_changed(self, username: str):
        """Handle username field changes to auto-load credentials."""
        if username and "@" in username:
            # Check if credentials exist when user finishes typing (basic check)
            self.load_credentials_requested.emit(username.strip())

    def _on_login_clicked(self):
        """Handle login button click."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        token = self.token_input.text()
        instance_url = self.instance_input.text().strip()
        remember = self.remember_checkbox.isChecked()

        # Emit login request signal
        self.login_requested.emit(username, password, token, instance_url, remember)

    def set_loading(self, loading: bool):
        """
        Set loading state (disable inputs during authentication).

        Args:
            loading: True to disable inputs, False to enable
        """
        self.username_input.setEnabled(not loading)
        self.password_input.setEnabled(not loading)
        self.token_input.setEnabled(not loading)
        self.instance_input.setEnabled(not loading)
        self.remember_checkbox.setEnabled(not loading)
        self.login_button.setEnabled(not loading)

        if loading:
            self.login_button.setText("Connecting...")
            self.show_status("Connecting to Salesforce...", "info")
        else:
            self.login_button.setText("Connect to Salesforce")

    def show_status(self, message: str, status_type: str = "info"):
        """
        Display status message to user.

        Args:
            message: Status message to display
            status_type: Type of status ('success', 'error', 'info')
        """
        self.status_label.setText(message)

        if status_type == "success":
            self.status_label.setStyleSheet("color: #2e844a; font-weight: bold;")
        elif status_type == "error":
            self.status_label.setStyleSheet("color: #c23934; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #666;")

    def show_error(self, title: str, message: str):
        """
        Show error message dialog.

        Args:
            title: Error dialog title
            message: Error message
        """
        QMessageBox.critical(self, title, message)

    def show_success(self, title: str, message: str):
        """
        Show success message dialog.

        Args:
            title: Success dialog title
            message: Success message
        """
        QMessageBox.information(self, title, message)

    def auto_fill_credentials(self, password: str, token: str):
        """
        Auto-fill password and token fields.

        Args:
            password: Password to fill
            token: Security token to fill
        """
        self.password_input.setText(password)
        self.token_input.setText(token)
        self.show_status("Credentials loaded from secure storage", "info")

    def clear_password_fields(self):
        """Clear password and token fields."""
        self.password_input.clear()
        self.token_input.clear()
