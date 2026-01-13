"""
Salesforce authentication module.

Handles authentication logic for Salesforce API connections.
"""

from typing import Optional, Tuple
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed
from simple_salesforce.exceptions import SalesforceGeneralError

from ...core.logging_config import get_logger
from ...core.credentials import SalesforceCredentials


logger = get_logger(__name__)


class SalesforceAuthError(Exception):
    """Raised when Salesforce authentication fails."""
    pass


class SalesforceAuthenticator:
    """Handles Salesforce authentication."""

    @staticmethod
    def authenticate(credentials: SalesforceCredentials) -> Tuple[Optional[Salesforce], Optional[str]]:
        """
        Authenticate with Salesforce using username, password, and security token.

        Args:
            credentials: SalesforceCredentials object

        Returns:
            Tuple of (Salesforce instance, error_message)
            If successful, returns (sf_instance, None)
            If failed, returns (None, error_message)
        """
        try:
            logger.info(f"Attempting to authenticate user: {credentials.username}")

            # Validate credentials
            if not credentials.username:
                return None, "Username is required"
            if not credentials.password:
                return None, "Password is required"
            if not credentials.security_token:
                return None, "Security token is required"

            logger.debug(f"Username: {credentials.username}")
            logger.debug(f"Password length: {len(credentials.password)}")
            logger.debug(f"Token length: {len(credentials.security_token)}")
            logger.debug(f"Instance URL: {credentials.instance_url}")

            # Extract domain for authentication
            domain = SalesforceAuthenticator._extract_domain(credentials.instance_url)
            logger.debug(f"Domain: {domain}")

            # Create Salesforce instance
            # Using username/password authentication
            sf = Salesforce(
                username=credentials.username,
                password=credentials.password,
                security_token=credentials.security_token,
                domain=domain
            )

            logger.info(f"Successfully authenticated user: {credentials.username}")
            return sf, None

        except SalesforceAuthenticationFailed as e:
            error_msg = "Invalid username, password, or security token"
            logger.error(f"Authentication failed for {credentials.username}: {e}")
            return None, error_msg

        except SalesforceGeneralError as e:
            error_msg = f"Salesforce error: {str(e)}"
            logger.error(f"Salesforce error during authentication: {e}")
            return None, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error during authentication: {e}")
            return None, error_msg

    @staticmethod
    def _extract_domain(instance_url: str) -> str:
        """
        Extract domain from instance URL.

        Args:
            instance_url: Full Salesforce instance URL

        Returns:
            Domain string ('login' for production, 'test' for sandbox)
        """
        if "test.salesforce.com" in instance_url.lower():
            return "test"
        else:
            return "login"

    @staticmethod
    def verify_connection(sf: Salesforce) -> bool:
        """
        Verify that a Salesforce connection is active and working.

        Args:
            sf: Salesforce instance

        Returns:
            True if connection is active, False otherwise
        """
        try:
            # Simple query to verify connection
            sf.query("SELECT Id FROM User LIMIT 1")
            return True
        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            return False
