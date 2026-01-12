"""
Salesforce metadata data models.

Represents Salesforce objects, fields, and relationships for schema discovery.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class RecordType:
    """Represents a Salesforce Record Type."""

    record_type_id: str                 # Record Type ID
    name: str                           # Developer name
    label: str                          # Display label
    is_active: bool = True
    is_default: bool = False

    def __str__(self) -> str:
        """String representation of the record type."""
        default_marker = " (Default)" if self.is_default else ""
        return f"{self.label}{default_marker}"


@dataclass
class SalesforceField:
    """Represents a single field in a Salesforce object."""

    name: str                           # API name (e.g., 'AccountNumber')
    label: str                          # Display label
    type: str                           # Field type: string, reference, datetime, etc.
    length: Optional[int] = None        # Max length for string fields
    required: bool = False              # Nillable=False in SF
    updateable: bool = True
    createable: bool = True
    relationship_name: Optional[str] = None  # For reference fields
    reference_to: List[str] = field(default_factory=list)  # Target object names for lookups
    picklist_values: List[str] = field(default_factory=list)  # For picklist/multipicklist
    default_value: Optional[str] = None
    calculated: bool = False            # Formula field
    auto_number: bool = False          # Auto-number field

    def __str__(self) -> str:
        """String representation of the field."""
        return f"{self.label} ({self.name}) - {self.type}"


@dataclass
class SalesforceObject:
    """Represents a Salesforce standard or custom object."""

    name: str                           # API name (Account, Custom__c)
    label: str                          # Display label
    label_plural: str                   # Plural label
    custom: bool = False                # True for custom objects
    fields: List[SalesforceField] = field(default_factory=list)
    record_types: List[RecordType] = field(default_factory=list)  # Available record types
    createable: bool = True
    updateable: bool = True
    deletable: bool = True
    queryable: bool = True
    record_count: Optional[int] = None  # Cached from COUNT() query
    fetched_at: Optional[datetime] = None  # Metadata cache timestamp

    def __str__(self) -> str:
        """String representation of the object."""
        object_type = "Custom" if self.custom else "Standard"
        return f"{self.label} ({self.name}) - {object_type}"

    def get_required_fields(self) -> List[SalesforceField]:
        """Get list of required fields."""
        return [f for f in self.fields if f.required]

    def get_updateable_fields(self) -> List[SalesforceField]:
        """Get list of updateable fields."""
        return [f for f in self.fields if f.updateable]

    def get_createable_fields(self) -> List[SalesforceField]:
        """Get list of createable fields."""
        return [f for f in self.fields if f.createable]

    def get_reference_fields(self) -> List[SalesforceField]:
        """Get list of reference/lookup fields."""
        return [f for f in self.fields if f.type in ['reference', 'masterDetail']]


@dataclass
class ObjectListItem:
    """Lightweight object representation for listing."""

    name: str
    label: str
    label_plural: str
    custom: bool
    queryable: bool

    def __str__(self) -> str:
        """String representation."""
        return f"{self.label} ({self.name})"
