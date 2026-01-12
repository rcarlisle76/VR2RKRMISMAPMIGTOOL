"""
Login presenter (Presenter in MVP pattern).

Orchestrates login flow between UI and business logic.
Contains no PyQt5 dependencies - pure Python business logic.
"""

from typing import Optional
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from ...core.logging_config import get_logger
from ...services.auth_service import AuthService
from ...models.connection import ConnectionStatus


logger = get_logger(__name__)


class AuthWorker(QThread):
    """
    Worker thread for authentication to prevent UI blocking.

    Runs authentication in background thread.
    """

    finished = pyqtSignal(object)  # ConnectionStatus
    error = pyqtSignal(str)

    def __init__(self, auth_service: AuthService, username: str, password: str,
                 token: str, instance_url: str, remember: bool):
        """
        Initialize authentication worker.

        Args:
            auth_service: AuthService instance
            username: Salesforce username
            password: Salesforce password
            token: Security token
            instance_url: Instance URL
            remember: Whether to remember credentials
        """
        super().__init__()
        self.auth_service = auth_service
        self.username = username
        self.password = password
        self.token = token
        self.instance_url = instance_url
        self.remember = remember

    def run(self):
        """Execute authentication in background thread."""
        try:
            status = self.auth_service.authenticate(
                username=self.username,
                password=self.password,
                security_token=self.token,
                instance_url=self.instance_url,
                remember_credentials=self.remember
            )
            self.finished.emit(status)

        except Exception as e:
            logger.error(f"Authentication worker error: {e}")
            self.error.emit(str(e))


class LoginPresenter(QObject):
    """
    Presenter for login window.

    Handles business logic for login workflow:
    - Receives signals from LoginWindow (View)
    - Calls AuthService (Model/Service)
    - Updates LoginWindow based on results
    """

    # Signal to notify when authentication succeeds
    authentication_succeeded = pyqtSignal()

    def __init__(self, view, auth_service: Optional[AuthService] = None):
        """
        Initialize login presenter.

        Args:
            view: LoginWindow instance
            auth_service: AuthService instance (created if not provided)
        """
        super().__init__()
        self.view = view
        self.auth_service = auth_service or AuthService()
        self.auth_worker: Optional[AuthWorker] = None

        # Connect view signals to presenter methods
        self.view.login_requested.connect(self._handle_login_request)
        self.view.load_credentials_requested.connect(self._handle_load_credentials)

    def _handle_login_request(self, username: str, password: str, token: str,
                              instance_url: str, remember: bool):
        """
        Handle login request from view.

        Args:
            username: Salesforce username
            password: Salesforce password
            token: Security token
            instance_url: Instance URL
            remember: Whether to remember credentials
        """
        logger.info(f"Login request received for user: {username}")

        # Set UI to loading state
        self.view.set_loading(True)

        # Create and start authentication worker thread
        self.auth_worker = AuthWorker(
            self.auth_service,
            username,
            password,
            token,
            instance_url,
            remember
        )

        # Connect worker signals
        self.auth_worker.finished.connect(self._handle_auth_result)
        self.auth_worker.error.connect(self._handle_auth_error)

        # Start authentication
        self.auth_worker.start()

    def _handle_auth_result(self, status: ConnectionStatus):
        """
        Handle authentication result from worker thread.

        Args:
            status: ConnectionStatus object
        """
        # Reset UI loading state
        self.view.set_loading(False)

        if status.success:
            logger.info("Authentication successful")
            self.view.show_status(status.message, "success")
            self.view.show_success("Success", "Successfully connected to Salesforce!")

            # Emit success signal
            self.authentication_succeeded.emit()

        else:
            logger.warning(f"Authentication failed: {status.error}")
            self.view.show_status("Authentication failed", "error")

            error_message = status.error or "Unknown error occurred"
            self.view.show_error("Authentication Failed", error_message)

        # Clean up worker
        if self.auth_worker:
            self.auth_worker.deleteLater()
            self.auth_worker = None

    def _handle_auth_error(self, error_message: str):
        """
        Handle authentication error from worker thread.

        Args:
            error_message: Error message
        """
        logger.error(f"Authentication error: {error_message}")

        # Reset UI loading state
        self.view.set_loading(False)
        self.view.show_status("Authentication error", "error")
        self.view.show_error("Error", f"An error occurred: {error_message}")

        # Clean up worker
        if self.auth_worker:
            self.auth_worker.deleteLater()
            self.auth_worker = None

    def _handle_load_credentials(self, username: str):
        """
        Handle request to load saved credentials.

        Args:
            username: Username to load credentials for
        """
        logger.info(f"Checking for saved credentials: {username}")

        # Check if credentials exist
        if self.auth_service.credentials_exist(username):
            # Load credentials
            credentials = self.auth_service.load_saved_credentials(username)

            if credentials:
                # Auto-fill password and token fields
                self.view.auto_fill_credentials(
                    password=credentials.password,
                    token=credentials.security_token
                )
                logger.info(f"Credentials auto-filled for user: {username}")
            else:
                logger.warning(f"Failed to load credentials for user: {username}")

    def cleanup(self):
        """Cleanup resources when presenter is no longer needed."""
        if self.auth_worker and self.auth_worker.isRunning():
            self.auth_worker.terminate()
            self.auth_worker.wait()

        if self.auth_service.is_connected():
            self.auth_service.disconnect()
