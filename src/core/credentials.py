"""
Secure credential storage using OS-level keyring.

Uses platform-specific secure storage:
- Windows: Credential Manager
- macOS: Keychain
- Linux: Secret Service
"""

import keyring
from typing import Optional
from dataclasses import dataclass

from .logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class SalesforceCredentials:
    """Salesforce authentication credentials."""

    username: str
    password: str
    security_token: str
    instance_url: str = "https://login.salesforce.com"


class CredentialManager:
    """Manages secure storage and retrieval of credentials using OS keyring."""

    SERVICE_NAME = "SalesforceMigrationTool"

    @classmethod
    def save_credentials(cls,
                        username: str,
                        password: str,
                        security_token: str,
                        instance_url: str = "https://login.salesforce.com") -> bool:
        """
        Store credentials securely in OS keyring.

        Args:
            username: Salesforce username
            password: Salesforce password
            security_token: Salesforce security token
            instance_url: Salesforce instance URL

        Returns:
            True if credentials saved successfully, False otherwise
        """
        try:
            # Store password
            keyring.set_password(
                cls.SERVICE_NAME,
                f"{username}:password",
                password
            )

            # Store security token
            keyring.set_password(
                cls.SERVICE_NAME,
                f"{username}:token",
                security_token
            )

            # Store instance URL
            keyring.set_password(
                cls.SERVICE_NAME,
                f"{username}:instance_url",
                instance_url
            )

            logger.info(f"Credentials saved for user: {username}")
            return True

        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False

    @classmethod
    def get_credentials(cls, username: str) -> Optional[SalesforceCredentials]:
        """
        Retrieve credentials from OS keyring.

        Args:
            username: Salesforce username

        Returns:
            SalesforceCredentials object if found, None otherwise
        """
        try:
            # Retrieve password
            password = keyring.get_password(
                cls.SERVICE_NAME,
                f"{username}:password"
            )

            # Retrieve security token
            security_token = keyring.get_password(
                cls.SERVICE_NAME,
                f"{username}:token"
            )

            # Retrieve instance URL (with default fallback)
            instance_url = keyring.get_password(
                cls.SERVICE_NAME,
                f"{username}:instance_url"
            )

            if password and security_token:
                credentials = SalesforceCredentials(
                    username=username,
                    password=password,
                    security_token=security_token,
                    instance_url=instance_url or "https://login.salesforce.com"
                )
                logger.info(f"Credentials retrieved for user: {username}")
                return credentials
            else:
                logger.info(f"No stored credentials found for user: {username}")
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {e}")
            return None

    @classmethod
    def delete_credentials(cls, username: str) -> bool:
        """
        Remove credentials from OS keyring.

        Args:
            username: Salesforce username

        Returns:
            True if credentials deleted successfully, False otherwise
        """
        try:
            # Delete password
            try:
                keyring.delete_password(
                    cls.SERVICE_NAME,
                    f"{username}:password"
                )
            except keyring.errors.PasswordDeleteError:
                pass  # Already deleted or doesn't exist

            # Delete security token
            try:
                keyring.delete_password(
                    cls.SERVICE_NAME,
                    f"{username}:token"
                )
            except keyring.errors.PasswordDeleteError:
                pass

            # Delete instance URL
            try:
                keyring.delete_password(
                    cls.SERVICE_NAME,
                    f"{username}:instance_url"
                )
            except keyring.errors.PasswordDeleteError:
                pass

            logger.info(f"Credentials deleted for user: {username}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete credentials: {e}")
            return False

    @classmethod
    def credentials_exist(cls, username: str) -> bool:
        """
        Check if credentials exist for the given username.

        Args:
            username: Salesforce username

        Returns:
            True if credentials exist, False otherwise
        """
        try:
            password = keyring.get_password(
                cls.SERVICE_NAME,
                f"{username}:password"
            )
            return password is not None
        except Exception:
            return False

    @classmethod
    def clear_sensitive_data(cls, credentials: Optional[SalesforceCredentials]) -> None:
        """
        Clear sensitive data from memory.

        Args:
            credentials: Credentials object to clear
        """
        if credentials:
            # Overwrite sensitive fields
            credentials.password = ""
            credentials.security_token = ""
