"""
Authentication service.

Orchestrates the authentication workflow, coordinating between
credential storage, validation, and Salesforce connection.
"""

from typing import Optional, Tuple
from datetime import datetime

from ..core.logging_config import get_logger
from ..core.credentials import CredentialManager, SalesforceCredentials
from ..connectors.salesforce.client import SalesforceClient
from ..models.connection import ConnectionStatus, ConnectionConfig
from ..utils.validators import validate_credentials


logger = get_logger(__name__)


class AuthService:
    """
    Handles authentication business logic.

    Coordinates validation, credential storage, and Salesforce connection.
    """

    def __init__(self):
        """Initialize the authentication service."""
        self.sf_client = SalesforceClient()
        self.current_connection: Optional[ConnectionConfig] = None

    def authenticate(self,
                    username: str,
                    password: str,
                    security_token: str,
                    instance_url: str = "https://login.salesforce.com",
                    remember_credentials: bool = False) -> ConnectionStatus:
        """
        Authenticate with Salesforce.

        Args:
            username: Salesforce username
            password: Salesforce password
            security_token: Salesforce security token
            instance_url: Salesforce instance URL
            remember_credentials: Whether to save credentials to keyring

        Returns:
            ConnectionStatus object with authentication result
        """
        logger.info(f"Authentication request for user: {username}")

        # Validate credentials
        valid, error_msg = validate_credentials(username, password, security_token)
        if not valid:
            logger.warning(f"Validation failed: {error_msg}")
            return ConnectionStatus(
                success=False,
                message="Validation failed",
                error=error_msg
            )

        # Create credentials object
        credentials = SalesforceCredentials(
            username=username,
            password=password,
            security_token=security_token,
            instance_url=instance_url
        )

        # Attempt connection
        try:
            self.sf_client.connect(credentials)

            # Get metadata
            metadata = self.sf_client.get_metadata()

            # Save credentials if requested
            if remember_credentials:
                success = CredentialManager.save_credentials(
                    username=username,
                    password=password,
                    security_token=security_token,
                    instance_url=instance_url
                )
                if success:
                    logger.info(f"Credentials saved for user: {username}")
                else:
                    logger.warning("Failed to save credentials to keyring")

            # Create connection config
            self.current_connection = ConnectionConfig(
                name="Default Connection",
                username=username,
                instance_url=instance_url,
                connected=True,
                last_connected=datetime.now()
            )

            logger.info(f"Authentication successful for user: {username}")

            return ConnectionStatus(
                success=True,
                message="Successfully connected to Salesforce",
                session_id=metadata.get("session_id")
            )

        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return ConnectionStatus(
                success=False,
                message="Connection failed",
                error=str(e)
            )

        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return ConnectionStatus(
                success=False,
                message="Unexpected error",
                error=str(e)
            )

        finally:
            # Clear sensitive data from memory
            CredentialManager.clear_sensitive_data(credentials)

    def load_saved_credentials(self, username: str) -> Optional[SalesforceCredentials]:
        """
        Load saved credentials from keyring.

        Args:
            username: Salesforce username

        Returns:
            SalesforceCredentials if found, None otherwise
        """
        logger.info(f"Attempting to load saved credentials for: {username}")
        credentials = CredentialManager.get_credentials(username)

        if credentials:
            logger.info(f"Credentials found for user: {username}")
        else:
            logger.info(f"No saved credentials found for user: {username}")

        return credentials

    def credentials_exist(self, username: str) -> bool:
        """
        Check if credentials exist for the given username.

        Args:
            username: Salesforce username

        Returns:
            True if credentials exist, False otherwise
        """
        return CredentialManager.credentials_exist(username)

    def disconnect(self) -> bool:
        """
        Disconnect from Salesforce.

        Returns:
            True if disconnection successful
        """
        logger.info("Disconnecting from Salesforce")

        if self.current_connection:
            self.current_connection.connected = False

        return self.sf_client.disconnect()

    def get_current_connection(self) -> Optional[ConnectionConfig]:
        """
        Get the current connection configuration.

        Returns:
            ConnectionConfig object or None if not connected
        """
        return self.current_connection

    def is_connected(self) -> bool:
        """
        Check if currently connected to Salesforce.

        Returns:
            True if connected, False otherwise
        """
        return self.sf_client.is_connected()

    def health_check(self) -> bool:
        """
        Perform a health check on the current connection.

        Returns:
            True if connection is healthy, False otherwise
        """
        return self.sf_client.health_check()

    def get_client(self) -> SalesforceClient:
        """
        Get the Salesforce client instance.

        Returns:
            SalesforceClient instance
        """
        return self.sf_client
