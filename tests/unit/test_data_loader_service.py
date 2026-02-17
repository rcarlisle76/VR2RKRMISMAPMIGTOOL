"""
Unit tests for DataLoaderService.
"""

import pytest
from unittest.mock import Mock, patch, call

from src.services.data_loader_service import DataLoaderService, LoadResult
from src.models.mapping_models import FieldMapping
from src.models.salesforce_metadata import SalesforceField


@pytest.mark.unit
class TestLoadResult:
    """Test suite for LoadResult helper methods."""

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = LoadResult(
            total_rows=100,
            successful_rows=95,
            failed_rows=5,
            errors=[],
        )

        assert result.get_success_rate() == 95.0

    def test_success_rate_all_successful(self):
        """Test success rate when all rows succeed."""
        result = LoadResult(
            total_rows=50,
            successful_rows=50,
            failed_rows=0,
            errors=[],
        )

        assert result.get_success_rate() == 100.0

    def test_success_rate_all_failed(self):
        """Test success rate when all rows fail."""
        result = LoadResult(
            total_rows=50,
            successful_rows=0,
            failed_rows=50,
            errors=[],
        )

        assert result.get_success_rate() == 0.0

    def test_success_rate_zero_rows(self):
        """Test success rate with zero rows."""
        result = LoadResult(
            total_rows=0,
            successful_rows=0,
            failed_rows=0,
            errors=[],
        )

        assert result.get_success_rate() == 0.0


@pytest.mark.unit
class TestValueConversion:
    """Test suite for value conversion logic."""

    def test_convert_empty_string(self, mock_sf_client):
        """Test conversion of empty string returns None."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
            name="Email",
            label="Email",
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

        result = service._convert_value("", field)
        assert result is None

    def test_convert_none_value(self, mock_sf_client):
        """Test conversion of None returns None."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
            name="Email",
            label="Email",
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

        result = service._convert_value(None, field)
        assert result is None

    def test_convert_string_field(self, mock_sf_client):
        """Test conversion of string field."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
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

        result = service._convert_value("  John  ", field)
        assert result == "John"

    def test_convert_boolean_true_variants(self, mock_sf_client):
        """Test conversion of boolean true variants."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
            name="IsActive",
            label="Is Active",
            type="boolean",
            length=None,
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

        assert service._convert_value("true", field) is True
        assert service._convert_value("True", field) is True
        assert service._convert_value("TRUE", field) is True
        assert service._convert_value("yes", field) is True
        assert service._convert_value("1", field) is True
        assert service._convert_value("y", field) is True
        assert service._convert_value("t", field) is True

    def test_convert_boolean_false_variants(self, mock_sf_client):
        """Test conversion of boolean false variants."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
            name="IsActive",
            label="Is Active",
            type="boolean",
            length=None,
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

        assert service._convert_value("false", field) is False
        assert service._convert_value("False", field) is False
        assert service._convert_value("FALSE", field) is False
        assert service._convert_value("no", field) is False
        assert service._convert_value("0", field) is False
        assert service._convert_value("n", field) is False
        assert service._convert_value("f", field) is False

    def test_convert_integer(self, mock_sf_client):
        """Test conversion of integer values."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
            name="NumberOfEmployees",
            label="Number of Employees",
            type="int",
            length=None,
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

        assert service._convert_value("100", field) == 100
        assert service._convert_value("1,000", field) == 1000
        assert service._convert_value("1,234,567", field) == 1234567

    def test_convert_double(self, mock_sf_client):
        """Test conversion of double/currency values."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
            name="Amount",
            label="Amount",
            type="currency",
            length=None,
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

        assert service._convert_value("100.50", field) == 100.50
        assert service._convert_value("$1,000.75", field) == 1000.75
        assert service._convert_value("50%", field) == 50.0

    def test_convert_date_yyyy_mm_dd(self, mock_sf_client):
        """Test conversion of date in YYYY-MM-DD format."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
            name="StartDate",
            label="Start Date",
            type="date",
            length=None,
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

        result = service._convert_value("2024-01-15", field)
        assert result == "2024-01-15"

    def test_convert_date_mm_dd_yyyy(self, mock_sf_client):
        """Test conversion of date in MM/DD/YYYY format."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
            name="StartDate",
            label="Start Date",
            type="date",
            length=None,
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

        result = service._convert_value("01/15/2024", field)
        assert result == "2024-01-15"

    def test_convert_picklist_exact_match(self, mock_sf_client):
        """Test conversion of picklist with exact match."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
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
            default_value=None,
        )

        result = service._convert_value("Open", field)
        assert result == "Open"

    def test_convert_picklist_case_insensitive(self, mock_sf_client):
        """Test conversion of picklist with case-insensitive match."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
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
            default_value=None,
        )

        result = service._convert_value("open", field)
        assert result == "Open"

        result = service._convert_value("IN PROGRESS", field)
        assert result == "In Progress"

    def test_convert_picklist_invalid_value(self, mock_sf_client):
        """Test conversion of picklist with invalid value returns None."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
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
            default_value=None,
        )

        result = service._convert_value("InvalidStatus", field)
        assert result is None

    def test_convert_reference_valid_id(self, mock_sf_client):
        """Test conversion of reference field with valid Salesforce ID."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
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

        # 15-character ID
        result = service._convert_value("001000000000001", field)
        assert result == "001000000000001"

        # 18-character ID
        result = service._convert_value("001000000000001AAA", field)
        assert result == "001000000000001AAA"

    def test_convert_reference_invalid_id(self, mock_sf_client):
        """Test conversion of reference field with invalid ID returns None."""
        service = DataLoaderService(mock_sf_client)

        field = SalesforceField(
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

        # Too short
        result = service._convert_value("001", field)
        assert result is None

        # Invalid characters
        result = service._convert_value("001000000000001@@@", field)
        assert result is None


@pytest.mark.unit
class TestDataTransformation:
    """Test suite for data transformation logic."""

    def test_transform_basic_mapping(self, mock_sf_client, sample_salesforce_object):
        """Test basic data transformation with direct mappings."""
        service = DataLoaderService(mock_sf_client)

        csv_data = [
            {"first_name": "John", "email": "john@example.com"},
            {"first_name": "Jane", "email": "jane@example.com"},
        ]

        mappings = [
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
        ]

        transformed = service._transform_data(
            csv_data, mappings, sample_salesforce_object, record_type_id=None
        )

        assert len(transformed) == 2
        assert transformed[0]["FirstName"] == "John"
        assert transformed[0]["Email"] == "john@example.com"
        assert transformed[1]["FirstName"] == "Jane"
        assert transformed[1]["Email"] == "jane@example.com"

    def test_transform_with_record_type(self, mock_sf_client, sample_salesforce_object):
        """Test data transformation with record type ID."""
        service = DataLoaderService(mock_sf_client)

        csv_data = [{"first_name": "John"}]

        mappings = [
            FieldMapping(
                source_column="first_name",
                target_field="FirstName",
                mapping_type="direct",
                is_required=False,
            ),
        ]

        transformed = service._transform_data(
            csv_data, mappings, sample_salesforce_object, record_type_id="012000000000001AAA"
        )

        assert transformed[0]["RecordTypeId"] == "012000000000001AAA"
        assert transformed[0]["FirstName"] == "John"

    def test_transform_skips_readonly_fields(self, mock_sf_client, sample_salesforce_object, sample_readonly_field):
        """Test that read-only fields are skipped during transformation."""
        service = DataLoaderService(mock_sf_client)

        # Add readonly field to object
        sample_salesforce_object.fields.append(sample_readonly_field)

        csv_data = [{"amount": "1000.50"}]

        mappings = [
            FieldMapping(
                source_column="amount",
                target_field="TotalAmount",
                mapping_type="direct",
                is_required=False,
            ),
        ]

        transformed = service._transform_data(
            csv_data, mappings, sample_salesforce_object, record_type_id=None
        )

        # TotalAmount should not be in transformed data (it's read-only)
        assert "TotalAmount" not in transformed[0]

    def test_transform_skips_empty_values(self, mock_sf_client, sample_salesforce_object):
        """Test that empty values are skipped."""
        service = DataLoaderService(mock_sf_client)

        csv_data = [{"first_name": "", "email": "john@example.com"}]

        mappings = [
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
        ]

        transformed = service._transform_data(
            csv_data, mappings, sample_salesforce_object, record_type_id=None
        )

        # FirstName should not be in result (empty value)
        assert "FirstName" not in transformed[0]
        assert transformed[0]["Email"] == "john@example.com"

    def test_transform_ignores_csv_record_type_id(self, mock_sf_client, sample_salesforce_object):
        """Test that CSV RecordTypeId column is ignored when record_type_id parameter is provided."""
        service = DataLoaderService(mock_sf_client)

        csv_data = [{"record_type": "012WRONGIDXXXXXX", "first_name": "John"}]

        mappings = [
            FieldMapping(
                source_column="record_type",
                target_field="RecordTypeId",
                mapping_type="direct",
                is_required=False,
            ),
            FieldMapping(
                source_column="first_name",
                target_field="FirstName",
                mapping_type="direct",
                is_required=False,
            ),
        ]

        transformed = service._transform_data(
            csv_data, mappings, sample_salesforce_object, record_type_id="012CORRECTIDXXXX"
        )

        # Should use the parameter record_type_id, not the CSV value
        assert transformed[0]["RecordTypeId"] == "012CORRECTIDXXXX"
        assert transformed[0]["FirstName"] == "John"


@pytest.mark.unit
class TestCSVReading:
    """Test suite for CSV reading functionality."""

    def test_read_csv_data(self, mock_sf_client, sample_csv_file):
        """Test reading CSV data."""
        service = DataLoaderService(mock_sf_client)

        data = service._read_csv_data(sample_csv_file)

        assert len(data) == 3
        assert data[0]["FirstName"] == "John"
        assert data[1]["FirstName"] == "Jane"
        assert data[2]["FirstName"] == "Bob"

    def test_read_csv_utf8_encoding(self, mock_sf_client, tmp_path):
        """Test reading CSV with UTF-8 encoding."""
        csv_content = "Name,City\nJohn,New York\nJané,Paris"
        csv_file = tmp_path / "test_utf8.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        service = DataLoaderService(mock_sf_client)
        data = service._read_csv_data(str(csv_file))

        assert len(data) == 2
        assert data[1]["Name"] == "Jané"
