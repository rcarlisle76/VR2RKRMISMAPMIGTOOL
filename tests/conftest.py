"""
Shared fixtures for all tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass
from typing import List

from src.models.salesforce_metadata import (
    SalesforceObject,
    SalesforceField,
    ObjectListItem,
    RecordType,
)
from src.models.mapping_models import SourceFile, FieldMapping, SourceColumn


# ==================== Mock Salesforce Objects ====================


@pytest.fixture
def sample_salesforce_field():
    """Create a sample Salesforce field for testing."""
    return SalesforceField(
        name="FirstName",
        label="First Name",
        type="string",
        length=80,
        createable=True,
        updateable=True,
        required=False,
        unique=False,
        external_id=False,
        picklist_values=[],
        reference_to=[],
        relationship_name=None,
        calculated=False,
        auto_number=False,
        default_value=None,
    )


@pytest.fixture
def sample_picklist_field():
    """Create a sample picklist field for testing."""
    return SalesforceField(
        name="Status",
        label="Status",
        type="picklist",
        length=None,
        createable=True,
        updateable=True,
        required=False,
        unique=False,
        external_id=False,
        picklist_values=["Open", "In Progress", "Closed"],
        reference_to=[],
        relationship_name=None,
        calculated=False,
        auto_number=False,
        default_value="Open",
    )


@pytest.fixture
def sample_lookup_field():
    """Create a sample lookup/reference field for testing."""
    return SalesforceField(
        name="AccountId",
        label="Account ID",
        type="reference",
        length=18,
        createable=True,
        updateable=True,
        required=False,
        unique=False,
        external_id=False,
        picklist_values=[],
        reference_to=["Account"],
        relationship_name="Account",
        calculated=False,
        auto_number=False,
        default_value=None,
    )


@pytest.fixture
def sample_readonly_field():
    """Create a read-only field (formula or rollup)."""
    return SalesforceField(
        name="TotalAmount",
        label="Total Amount",
        type="currency",
        length=None,
        createable=False,  # Read-only
        updateable=False,
        required=False,
        unique=False,
        external_id=False,
        picklist_values=[],
        reference_to=[],
        relationship_name=None,
        calculated=True,
        auto_number=False,
        default_value=None,
    )


@pytest.fixture
def sample_record_type():
    """Create a sample record type."""
    return RecordType(
        id="012000000000001AAA",
        name="Standard",
        developer_name="Standard",
        is_active=True,
        is_master=False,
    )


@pytest.fixture
def sample_salesforce_object(
    sample_salesforce_field,
    sample_picklist_field,
    sample_lookup_field,
    sample_readonly_field,
    sample_record_type,
):
    """Create a sample Salesforce object with various field types."""
    return SalesforceObject(
        name="Contact",
        label="Contact",
        label_plural="Contacts",
        custom=False,
        createable=True,
        updateable=True,
        deleteable=True,
        queryable=True,
        fields=[
            sample_salesforce_field,
            sample_picklist_field,
            sample_lookup_field,
            sample_readonly_field,
            SalesforceField(
                name="Id",
                label="Record ID",
                type="id",
                length=18,
                createable=False,
                updateable=False,
                required=False,
                unique=True,
                external_id=False,
                picklist_values=[],
                reference_to=[],
                relationship_name=None,
                calculated=False,
                auto_number=True,
                default_value=None,
            ),
            SalesforceField(
                name="Email",
                label="Email",
                type="email",
                length=80,
                createable=True,
                updateable=True,
                required=False,
                unique=False,
                external_id=False,
                picklist_values=[],
                reference_to=[],
                relationship_name=None,
                calculated=False,
                auto_number=False,
                default_value=None,
            ),
        ],
        record_types=[sample_record_type],
        key_prefix="003",
    )


@pytest.fixture
def object_list_items():
    """Create a list of Salesforce objects for testing."""
    return [
        ObjectListItem(name="Account", label="Account", custom=False),
        ObjectListItem(name="Contact", label="Contact", custom=False),
        ObjectListItem(name="Opportunity", label="Opportunity", custom=False),
        ObjectListItem(name="Claim__c", label="Claim", custom=True),
    ]


# ==================== Mock Source Files ====================


@pytest.fixture
def sample_source_columns():
    """Create sample source columns from a CSV."""
    return [
        SourceColumn(name="first_name", type="string", sample_values=["John", "Jane"]),
        SourceColumn(name="last_name", type="string", sample_values=["Doe", "Smith"]),
        SourceColumn(name="email", type="string", sample_values=["john@example.com", "jane@example.com"]),
        SourceColumn(name="status", type="string", sample_values=["Open", "Closed"]),
        SourceColumn(name="amount", type="number", sample_values=["1000.50", "2500.00"]),
    ]


@pytest.fixture
def sample_source_file(sample_source_columns):
    """Create a sample source file for testing."""
    return SourceFile(
        file_path="test_data.csv",
        columns=sample_source_columns,
        row_count=100,
        encoding="utf-8",
    )


# ==================== Mock Field Mappings ====================


@pytest.fixture
def sample_field_mappings():
    """Create sample field mappings for testing."""
    return [
        FieldMapping(
            source_column="first_name",
            target_field="FirstName",
            mapping_type="direct",
            is_required=False,
        ),
        FieldMapping(
            source_column="email",
            target_field="Email",
            mapping_type="direct",
            is_required=False,
        ),
        FieldMapping(
            source_column="status",
            target_field="Status",
            mapping_type="direct",
            is_required=False,
        ),
    ]


# ==================== Mock Salesforce Client ====================


@pytest.fixture
def mock_sf_client():
    """Create a mock Salesforce client for testing."""
    mock = Mock()

    # Mock describe_global response
    mock.describe_global.return_value = {
        "sobjects": [
            {"name": "Account", "label": "Account", "custom": False},
            {"name": "Contact", "label": "Contact", "custom": False},
            {"name": "Claim__c", "label": "Claim", "custom": True},
        ]
    }

    # Mock describe response for an object
    mock.describe_object.return_value = {
        "name": "Contact",
        "label": "Contact",
        "labelPlural": "Contacts",
        "custom": False,
        "createable": True,
        "updateable": True,
        "deleteable": True,
        "queryable": True,
        "keyPrefix": "003",
        "fields": [
            {
                "name": "Id",
                "label": "Record ID",
                "type": "id",
                "length": 18,
                "createable": False,
                "updateable": False,
                "nillable": False,
                "unique": True,
                "externalId": False,
                "picklistValues": [],
                "referenceTo": [],
                "relationshipName": None,
                "calculated": False,
                "autoNumber": True,
                "defaultValue": None,
            },
            {
                "name": "FirstName",
                "label": "First Name",
                "type": "string",
                "length": 80,
                "createable": True,
                "updateable": True,
                "nillable": True,
                "unique": False,
                "externalId": False,
                "picklistValues": [],
                "referenceTo": [],
                "relationshipName": None,
                "calculated": False,
                "autoNumber": False,
                "defaultValue": None,
            },
        ],
    }

    # Mock insert/update operations
    mock.insert.return_value = {"id": "001000000000001AAA", "success": True}
    mock.update.return_value = {"success": True}

    return mock


# ==================== Sample CSV Data ====================


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for file import testing."""
    return """FirstName,LastName,Email,Status,Amount
John,Doe,john@example.com,Open,1000.50
Jane,Smith,jane@example.com,Closed,2500.00
Bob,Johnson,bob@example.com,In Progress,750.00"""


@pytest.fixture
def sample_csv_file(tmp_path, sample_csv_content):
    """Create a temporary CSV file for testing."""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(sample_csv_content)
    return str(csv_file)


# ==================== Configuration Mocks ====================


@pytest.fixture
def mock_config():
    """Mock application configuration."""
    return {
        "use_semantic_matching": False,
        "use_llm_mapping": False,
        "claude_api_key": "",
        "last_instance_url": "https://login.salesforce.com",
    }


# ==================== PyQt Fixtures ====================


@pytest.fixture
def qapp(qtbot):
    """Provide QApplication instance for UI tests."""
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
