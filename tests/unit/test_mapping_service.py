"""
Unit tests for MappingService.
"""

import pytest
import json
from pathlib import Path

from src.services.mapping_service import MappingService
from src.models.mapping_models import FieldMapping, MappingConfiguration


@pytest.mark.unit
class TestMappingService:
    """Test suite for MappingService."""

    def test_create_mapping(self, sample_salesforce_object, sample_source_file):
        """Test creating a new mapping configuration."""
        service = MappingService()

        config = service.create_mapping(
            name="Test Mapping",
            salesforce_object=sample_salesforce_object,
            source_file=sample_source_file,
            description="Test description",
        )

        assert config.name == "Test Mapping"
        assert config.salesforce_object == "Contact"
        assert config.description == "Test description"
        assert config.version == "1.0"
        assert "expected_columns" in config.source_file_signature
        assert len(config.source_file_signature["expected_columns"]) == 5

    def test_create_mapping_without_description(
        self, sample_salesforce_object, sample_source_file
    ):
        """Test creating mapping without description."""
        service = MappingService()

        config = service.create_mapping(
            name="Test Mapping",
            salesforce_object=sample_salesforce_object,
            source_file=sample_source_file,
        )

        assert config.description == ""

    def test_auto_suggest_mappings_exact_match(
        self, sample_salesforce_object, sample_source_file
    ):
        """Test auto-suggest with exact field name matches."""
        service = MappingService()

        suggestions = service.auto_suggest_mappings(
            source_file=sample_source_file,
            salesforce_object=sample_salesforce_object,
            threshold=0.6,
        )

        # Should map: first_name -> FirstName, email -> Email
        assert len(suggestions) >= 2

        # Check that email mapped correctly
        email_mapping = next(
            (m for m in suggestions if m.source_column == "email"), None
        )
        assert email_mapping is not None
        assert email_mapping.target_field == "Email"
        assert email_mapping.mapping_type == "direct"

    def test_auto_suggest_mappings_no_matches_below_threshold(
        self, sample_salesforce_object
    ):
        """Test auto-suggest when no fields meet threshold."""
        service = MappingService()

        # Create source file with completely different column names
        from src.models.mapping_models import SourceFile, SourceColumn

        source_file = SourceFile(
            file_path="test.csv",
            columns=[
                SourceColumn(name="xyz123", type="string", sample_values=["test"]),
                SourceColumn(name="abc456", type="string", sample_values=["test"]),
            ],
            row_count=10,
            encoding="utf-8",
        )

        suggestions = service.auto_suggest_mappings(
            source_file=source_file,
            salesforce_object=sample_salesforce_object,
            threshold=0.8,  # High threshold
        )

        # Should have no suggestions
        assert len(suggestions) == 0

    def test_auto_suggest_mappings_custom_threshold(
        self, sample_salesforce_object, sample_source_file
    ):
        """Test auto-suggest with custom threshold."""
        service = MappingService()

        # Low threshold should give more suggestions
        low_threshold_suggestions = service.auto_suggest_mappings(
            source_file=sample_source_file,
            salesforce_object=sample_salesforce_object,
            threshold=0.3,
        )

        # High threshold should give fewer suggestions
        high_threshold_suggestions = service.auto_suggest_mappings(
            source_file=sample_source_file,
            salesforce_object=sample_salesforce_object,
            threshold=0.9,
        )

        assert len(low_threshold_suggestions) >= len(high_threshold_suggestions)

    def test_save_and_load_mapping(self, tmp_path, sample_salesforce_object, sample_source_file):
        """Test saving and loading mapping configuration."""
        service = MappingService()

        # Create a mapping
        config = service.create_mapping(
            name="Test Mapping",
            salesforce_object=sample_salesforce_object,
            source_file=sample_source_file,
            description="Test description",
        )

        # Add some field mappings
        config.mappings = [
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

        # Save to file
        file_path = tmp_path / "test_mapping.json"
        service.save_mapping(config, str(file_path))

        # Verify file exists
        assert file_path.exists()

        # Load it back
        loaded_config = service.load_mapping(str(file_path))

        # Verify all data is intact
        assert loaded_config.id == config.id
        assert loaded_config.name == config.name
        assert loaded_config.description == config.description
        assert loaded_config.salesforce_object == config.salesforce_object
        assert len(loaded_config.mappings) == 2
        assert loaded_config.mappings[0].source_column == "first_name"
        assert loaded_config.mappings[0].target_field == "FirstName"

    def test_save_mapping_creates_directories(self, tmp_path, sample_salesforce_object, sample_source_file):
        """Test that save_mapping creates parent directories if needed."""
        service = MappingService()

        config = service.create_mapping(
            name="Test Mapping",
            salesforce_object=sample_salesforce_object,
            source_file=sample_source_file,
        )

        # Save to nested path that doesn't exist
        file_path = tmp_path / "subdir" / "nested" / "test_mapping.json"
        service.save_mapping(config, str(file_path))

        # Verify file exists and directories were created
        assert file_path.exists()
        assert file_path.parent.exists()

    def test_load_mapping_with_missing_optional_fields(self, tmp_path):
        """Test loading mapping with some optional fields missing."""
        service = MappingService()

        # Create minimal JSON (backward compatibility test)
        minimal_data = {
            "id": "test-id-123",
            "name": "Minimal Mapping",
            "salesforce_object": "Contact",
            "created_date": "2024-01-01T00:00:00",
            "modified_date": "2024-01-01T00:00:00",
            "mappings": [
                {
                    "source_column": "email",
                    "target_field": "Email",
                }
            ],
        }

        file_path = tmp_path / "minimal_mapping.json"
        with open(file_path, "w") as f:
            json.dump(minimal_data, f)

        # Should load without errors
        config = service.load_mapping(str(file_path))

        assert config.id == "test-id-123"
        assert config.name == "Minimal Mapping"
        assert config.description == ""  # Default value
        assert config.version == "1.0"  # Default value
        assert len(config.mappings) == 1
        assert config.mappings[0].mapping_type == "direct"  # Default value
        assert config.mappings[0].is_required is False  # Default value


@pytest.mark.unit
class TestMappingSimilarity:
    """Test suite for similarity calculation algorithm."""

    def test_exact_match(self):
        """Test exact string match."""
        service = MappingService()
        score = service._calculate_similarity("FirstName", "FirstName")
        assert score == 1.0

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        service = MappingService()
        score = service._calculate_similarity("firstname", "FIRSTNAME")
        assert score == 1.0

    def test_underscore_normalization(self):
        """Test that underscores are normalized."""
        service = MappingService()
        score = service._calculate_similarity("first_name", "firstname")
        assert score == 1.0

    def test_space_normalization(self):
        """Test that spaces are normalized."""
        service = MappingService()
        score = service._calculate_similarity("first name", "firstname")
        assert score == 1.0

    def test_custom_suffix_removal(self):
        """Test removal of __c suffix."""
        service = MappingService()
        score = service._calculate_similarity("Email", "Email__c")
        assert score == 1.0

    def test_id_suffix_removal(self):
        """Test removal of 'id' suffix."""
        service = MappingService()
        score = service._calculate_similarity("account", "accountid")
        assert score == 1.0

    def test_name_suffix_removal(self):
        """Test removal of 'name' suffix."""
        service = MappingService()
        score = service._calculate_similarity("account", "accountname")
        assert score == 1.0

    def test_combined_normalization(self):
        """Test combined normalization rules."""
        service = MappingService()
        # first_name vs FirstName__c should match
        score = service._calculate_similarity("first_name", "FirstName__c")
        assert score == 1.0

    def test_partial_match(self):
        """Test partial string matching."""
        service = MappingService()
        score = service._calculate_similarity("email", "EmailAddress")
        # Should have some similarity but not perfect
        assert 0.5 < score < 1.0

    def test_no_match(self):
        """Test completely different strings."""
        service = MappingService()
        score = service._calculate_similarity("email", "xyz123")
        # Should have very low similarity
        assert score < 0.3

    def test_abbreviation_similarity(self):
        """Test handling of abbreviations."""
        service = MappingService()
        # These should have some similarity
        score = service._calculate_similarity("amt", "amount")
        assert score > 0.5

    def test_empty_string(self):
        """Test handling of empty strings."""
        service = MappingService()
        score = service._calculate_similarity("", "test")
        assert score == 0.0

    def test_both_empty_strings(self):
        """Test both strings empty."""
        service = MappingService()
        score = service._calculate_similarity("", "")
        assert score == 1.0


@pytest.mark.unit
class TestMappingValidation:
    """Test suite for mapping validation."""

    def test_required_field_mapping(self, sample_salesforce_object, sample_source_file):
        """Test that required fields are properly flagged in suggestions."""
        service = MappingService()

        # Add a required field to the Salesforce object
        from src.models.salesforce_metadata import SalesforceField

        required_field = SalesforceField(
            name="LastName",
            label="Last Name",
            type="string",
            length=80,
            createable=True,
            updateable=True,
            required=True,  # This is required
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

        suggestions = service.auto_suggest_mappings(
            source_file=sample_source_file,
            salesforce_object=sample_salesforce_object,
            threshold=0.6,
        )

        # Find the LastName mapping
        lastname_mapping = next(
            (m for m in suggestions if m.target_field == "LastName"), None
        )

        # Should exist and be marked as required
        assert lastname_mapping is not None
        assert lastname_mapping.is_required is True
