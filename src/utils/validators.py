"""
Input validation utilities.

Provides validation functions for user input fields.
"""

import re
from typing import Tuple


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not email.strip():
        return False, "Email cannot be empty"

    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if re.match(pattern, email.strip()):
        return True, ""
    else:
        return False, "Invalid email format"


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate Salesforce username (typically an email).

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username or not username.strip():
        return False, "Username cannot be empty"

    # Salesforce usernames are typically emails
    return validate_email(username)


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password is not empty.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"

    if len(password) < 1:
        return False, "Password cannot be empty"

    return True, ""


def validate_security_token(token: str) -> Tuple[bool, str]:
    """
    Validate Salesforce security token.

    Args:
        token: Security token to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not token:
        return False, "Security token cannot be empty"

    # Salesforce security tokens are typically 25 characters (alphanumeric)
    # But we'll just check it's not empty
    if len(token.strip()) < 1:
        return False, "Security token cannot be empty"

    return True, ""


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    # Basic URL pattern
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'

    if re.match(pattern, url.strip()):
        return True, ""
    else:
        return False, "Invalid URL format (must start with http:// or https://)"


def validate_credentials(username: str, password: str, security_token: str) -> Tuple[bool, str]:
    """
    Validate all credentials at once.

    Args:
        username: Salesforce username
        password: Salesforce password
        security_token: Salesforce security token

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate username
    valid, error = validate_username(username)
    if not valid:
        return False, error

    # Validate password
    valid, error = validate_password(password)
    if not valid:
        return False, error

    # Validate security token
    valid, error = validate_security_token(security_token)
    if not valid:
        return False, error

    return True, ""
