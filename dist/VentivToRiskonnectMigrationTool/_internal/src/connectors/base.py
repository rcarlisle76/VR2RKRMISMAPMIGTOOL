"""
Abstract base connector interface for data sources.

Defines the contract that all connector implementations must follow,
enabling support for multiple data sources (Salesforce, databases, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseConnector(ABC):
    """Abstract base class for all data source connectors."""

    def __init__(self):
        """Initialize the connector."""
        self._connected = False

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """
        Establish connection to the data source.

        Args:
            **kwargs: Connection parameters specific to the connector

        Returns:
            True if connection successful, False otherwise

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to the data source.

        Returns:
            True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if currently connected to the data source.

        Returns:
            True if connected, False otherwise
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Perform a health check on the connection.

        Returns:
            True if connection is healthy, False otherwise
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the data source.

        Returns:
            Dictionary containing metadata

        Raises:
            Exception: If not connected or metadata retrieval fails
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
