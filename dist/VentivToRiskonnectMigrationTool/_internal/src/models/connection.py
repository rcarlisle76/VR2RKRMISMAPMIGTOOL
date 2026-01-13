"""
Data models for connection configurations.

Defines the structure for connection settings and metadata.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ConnectionConfig:
    """
    Connection configuration for Salesforce.

    Attributes:
        name: Friendly name for the connection
        username: Salesforce username
        instance_url: Salesforce instance URL
        api_version: Salesforce API version
        connected: Whether currently connected
        last_connected: Timestamp of last successful connection
    """

    name: str
    username: str
    instance_url: str = "https://login.salesforce.com"
    api_version: str = "58.0"
    connected: bool = False
    last_connected: Optional[datetime] = None

    def __str__(self) -> str:
        """String representation of the connection."""
        return f"{self.name} ({self.username})"


@dataclass
class ConnectionStatus:
    """
    Status of a connection attempt.

    Attributes:
        success: Whether the connection was successful
        message: Status message
        error: Error message if connection failed
        session_id: Salesforce session ID if connected
    """

    success: bool
    message: str
    error: Optional[str] = None
    session_id: Optional[str] = None
