"""
Unit tests for MappingValidationService.
"""

import pytest

from src.services.validation_service import MappingValidationService, ValidationError
from src.models.mapping_models import FieldMapping
from src.models.salesforce_metadata import SalesforceField


@pytest.mark.unit
class TestMappingValidationService:
    """Test suite for MappingValidationService."""

    def test_validate_valid_mappings(self, sample_salesforce_object):
        """Test validation with all valid mappings."""
        service = MappingValidationService()

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

        result = service.validate(mappings, sample_salesforce_object)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert not result.has_errors()

    def test_validate_missing_required_field(self, sample_salesforce_object):
        """Test validation when a required field is missing."""
        service = MappingValidationService()

        # Add a required field
        required_field = SalesforceField(
            name="LastName",
            label="Last Name",
            type="string",
            length=80,
            createable=True,
            updateable=True,
            required=True,  # Required field
            unique=False,
            external_id=False,
            picklist_values=[],
            reference_to=[],
            relationship_name=None,
            calculated=False,
            auto_number=False,
            default_value=None,
        )
        sample_salesforce_object.fields.append(required_field)

        # Mappings don't include LastName
        mappings = [
            FieldMapping(
                source_column="first_name",
                target_field="FirstName",
                mapping_type="direct",
                is_required=False,
            ),
        ]

        result = service.validate(mappings, sample_salesforce_object)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].error_type == "missing_required"
        assert "LastName" in result.errors[0].message
        assert result.has_errors()

    def test_validate_invalid_target_field(self, sample_salesforce_object):
        """Test validation when mapping to non-existent field."""
        service = MappingValidationService()

        mappings = [
            FieldMapping(
                source_column="some_column",
                target_field="NonExistentField__c",
                mapping_type="direct",
                is_required=False,
            ),
        ]

        result = service.validate(mappings, sample_salesforce_object)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].error_type == "invalid_field"
        assert "NonExistentField__c" in result.errors[0].message

    def test_validate_duplicate_mapping(self, sample_salesforce_object):
        """Test validation when multiple source columns map to same target."""
        service = MappingValidationService()

        mappings = [
            FieldMapping(
                source_column="email1",
                target_field="Email",
                mapping_type="direct",
                is_required=False,
            ),
            FieldMapping(
                source_column="email2",
                target_field="Email",
                mapping_type="direct",
                is_required=False,
            ),
        ]

        result = service.validate(mappings, sample_salesforce_object)

        # Duplicate mappings are warnings, not errors
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.warnings[0].error_type == "duplicate_mapping"
        assert result.has_warnings()

    def test_validate_non_updateable_field(self, sample_salesforce_object, sample_readonly_field):
        """Test validation when mapping to a non-updateable field."""
        service = MappingValidationService()

        # Add the read-only field to the object
        sample_salesforce_object.fields.append(sample_readonly_field)

        mappings = [
            FieldMapping(
                source_column="amount",
                target_field="TotalAmount",
                mapping_type="direct",
                is_required=False,
            ),
        ]

        result = service.validate(mappings, sample_salesforce_object)

        # Non-updateable fields are warnings
        assert result.is_valid is True
        assert len(result.warnings) == 1
        assert result.warnings[0].error_type == "non_updateable"
        assert "not updateable" in result.warnings[0].message.lower()

    def test_validate_id_field_allowed(self, sample_salesforce_object):
        """Test that Id field doesn't trigger non-updateable warning."""
        service = MappingValidationService()

        mappings = [
            FieldMapping(
                source_column="record_id",
                target_field="Id",
                mapping_type="direct",
                is_required=False,
            ),
        ]

        result = service.validate(mappings, sample_salesforce_object)

        # Id field should be allowed even though it's not updateable
        assert result.is_valid is True
        assert len(result.warnings) == 0

    def test_validate_multiple_errors_and_warnings(self, sample_salesforce_object):
        """Test validation with both errors and warnings."""
        service = MappingValidationService()

        # Add required field
        required_field = SalesforceField(
            name="LastName",
            label="Last Name",
            type="string",
            length=80,
            createable=True,
            updateable=True,
            required=True,
            unique=False,
            external_id=False,
            picklist_values=[],
            reference_to=[],
            relationship_name=None,
            calculated=False,
            auto_number=False,
            default_value=None,
        )
        sample_salesforce_object.fields.append(required_field)

        mappings = [
            # Invalid field - error
            FieldMapping(
                source_column="col1",
                target_field="InvalidField",
                mapping_type="direct",
                is_required=False,
            ),
            # Duplicate mapping - warning
            FieldMapping(
                source_column="email1",
                target_field="Email",
                mapping_type="direct",
                is_required=False,
            ),
            FieldMapping(
                source_column="email2",
                target_field="Email",
                mapping_type="direct",
                is_required=False,
            ),
        ]
        # Missing required field LastName - error

        result = service.validate(mappings, sample_salesforce_object)

        assert result.is_valid is False
        assert len(result.errors) == 2  # invalid field + missing required
        assert len(result.warnings) == 1  # duplicate mapping
        assert len(result.get_all_issues()) == 3

    def test_validate_empty_mappings(self, sample_salesforce_object):
        """Test validation with no mappings."""
        service = MappingValidationService()

        # Add required field
        required_field = SalesforceField(
            name="LastName",
            label="Last Name",
            type="string",
            length=80,
            createable=True,
            updateable=True,
            required=True,
            unique=False,
            external_id=False,
            picklist_values=[],
            reference_to=[],
            relationship_name=None,
            calculated=False,
            auto_number=False,
            default_value=None,
        )
        sample_salesforce_object.fields.append(required_field)

        result = service.validate([], sample_salesforce_object)

        # Should fail because required fields are missing
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_single_mapping_valid(self):
        """Test validating a single mapping - valid case."""
        service = MappingValidationService()

        field = SalesforceField(
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
        )

        mapping = FieldMapping(
            source_column="email",
            target_field="Email",
            mapping_type="direct",
            is_required=False,
        )

        error = service.validate_single_mapping(mapping, field)

        assert error is None

    def test_validate_single_mapping_non_updateable(self):
        """Test validating a single mapping - non-updateable field."""
        service = MappingValidationService()

        field = SalesforceField(
            name="Formula__c",
            label="Formula Field",
            type="string",
            length=255,
            createable=False,
            updateable=False,  # Not updateable
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

        mapping = FieldMapping(
            source_column="formula",
            target_field="Formula__c",
            mapping_type="direct",
            is_required=False,
        )

        error = service.validate_single_mapping(mapping, field)

        assert error is not None
        assert error.error_type == "non_updateable"
        assert error.severity == "warning"

    def test_validate_single_mapping_id_field(self):
        """Test that Id field passes single mapping validation."""
        service = MappingValidationService()

        field = SalesforceField(
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
        )

        mapping = FieldMapping(
            source_column="record_id",
            target_field="Id",
            mapping_type="direct",
            is_required=False,
        )

        error = service.validate_single_mapping(mapping, field)

        # Id field should pass even though it's not updateable
        assert error is None


@pytest.mark.unit
class TestValidationResult:
    """Test suite for ValidationResult helper methods."""

    def test_has_errors_true(self):
        """Test has_errors when errors exist."""
        from src.services.validation_service import ValidationResult

        result = ValidationResult(
            is_valid=False,
            errors=[
                ValidationError(
                    field_name="Test",
                    error_type="test_error",
                    message="Test error",
                )
            ],
            warnings=[],
        )

        assert result.has_errors() is True

    def test_has_errors_false(self):
        """Test has_errors when no errors."""
        from src.services.validation_service import ValidationResult

        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        assert result.has_errors() is False

    def test_has_warnings_true(self):
        """Test has_warnings when warnings exist."""
        from src.services.validation_service import ValidationResult

        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[
                ValidationError(
                    field_name="Test",
                    error_type="test_warning",
                    message="Test warning",
                    severity="warning",
                )
            ],
        )

        assert result.has_warnings() is True

    def test_has_warnings_false(self):
        """Test has_warnings when no warnings."""
        from src.services.validation_service import ValidationResult

        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        assert result.has_warnings() is False

    def test_get_all_issues(self):
        """Test getting all issues combined."""
        from src.services.validation_service import ValidationResult

        result = ValidationResult(
            is_valid=False,
            errors=[
                ValidationError(
                    field_name="Error1",
                    error_type="error",
                    message="Error message",
                )
            ],
            warnings=[
                ValidationError(
                    field_name="Warning1",
                    error_type="warning",
                    message="Warning message",
                    severity="warning",
                ),
                ValidationError(
                    field_name="Warning2",
                    error_type="warning",
                    message="Warning message 2",
                    severity="warning",
                ),
            ],
        )

        all_issues = result.get_all_issues()

        assert len(all_issues) == 3
        assert all_issues[0].field_name == "Error1"
        assert all_issues[1].field_name == "Warning1"
        assert all_issues[2].field_name == "Warning2"
