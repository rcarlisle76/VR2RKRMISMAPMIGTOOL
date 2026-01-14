"""
Main application entry point for Ventiv to Riskonnect Migration Tool.

Bootstraps the application:
- Initializes logging
- Loads configuration
- Creates and displays login window
- Enters event loop
"""

# CRITICAL: Setup PyTorch DLL path and import torch BEFORE PyQt5
# This fixes DLL loading issues on Windows with Python 3.14
import sys
import os

if sys.platform == 'win32':
    torch_lib_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'torch', 'lib')
    if os.path.exists(torch_lib_path):
        # Add to PATH environment variable
        os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')
        # Add to DLL search path for Python 3.8+
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(torch_lib_path)

    # Pre-import torch to load its DLLs BEFORE PyQt5 loads
    try:
        import torch
        _torch_loaded = True
    except Exception as e:
        print(f"Warning: Could not pre-load PyTorch: {e}")
        _torch_loaded = False

from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from .core.logging_config import LoggingConfig
from .core.config import ConfigManager
from .ui.login_window import LoginWindow
from .ui.main_window import MainWindow
from .ui.presenters.login_presenter import LoginPresenter
from .ui.presenters.main_presenter import MainPresenter
from .services.metadata_service import MetadataService


def main():
    """Main application entry point."""

    # Setup logging
    LoggingConfig.setup_logging(
        log_level=LoggingConfig.DEBUG,
        console_output=True
    )

    logger = LoggingConfig.get_logger(__name__)
    logger.info("=" * 60)
    logger.info("Ventiv to Riskonnect Migration Tool Starting")
    logger.info("=" * 60)

    # Load configuration
    config_manager = ConfigManager()
    try:
        config = config_manager.load()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load configuration: {e}")
        logger.info("Using default configuration")

    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Ventiv to Riskonnect Migration Tool")
    app.setOrganizationName("SalesforceMigrationTool")

    # Enable high DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Create login window
    login_window = LoginWindow()

    # Create presenter
    login_presenter = LoginPresenter(login_window)

    # Keep references to main window and presenter
    main_window = None
    main_presenter = None

    # Handle successful authentication
    def on_authentication_success():
        nonlocal main_window, main_presenter

        logger.info("User authenticated successfully")

        # Get authenticated service to pass to main window
        auth_service = login_presenter.auth_service

        # Get username for display
        connection = auth_service.get_current_connection()
        username = connection.username if connection else "User"

        # Create metadata service
        metadata_service = MetadataService(auth_service.get_client())

        # Create main window
        main_window = MainWindow(username=username)

        # Create main presenter
        main_presenter = MainPresenter(main_window, metadata_service, auth_service)

        # Handle logout request
        def on_logout():
            nonlocal main_window, main_presenter
            logger.info("Logout requested from main window")

            # Close main window
            if main_window:
                main_window.close()
                main_window = None

            if main_presenter:
                main_presenter.cleanup()
                main_presenter = None

            # Show login window again
            login_window.clear_password_fields()
            login_window.show()

        main_presenter.logout_requested.connect(on_logout)

        # Hide login window and show main window
        login_window.hide()
        main_window.show()
        logger.info("Main window displayed")

    login_presenter.authentication_succeeded.connect(on_authentication_success)

    # Show login window
    login_window.show()
    logger.info("Login window displayed")

    # Start event loop
    logger.info("Entering application event loop")
    exit_code = app.exec_()

    # Cleanup
    logger.info("Application shutting down")
    login_presenter.cleanup()

    if main_presenter:
        main_presenter.cleanup()

    # Save configuration
    try:
        config_manager.save()
        logger.info("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")

    logger.info("=" * 60)
    logger.info("Ventiv to Riskonnect Migration Tool Closed")
    logger.info("=" * 60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
