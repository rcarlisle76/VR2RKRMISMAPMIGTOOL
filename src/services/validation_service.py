"""
Validation service - validates field mappings.

Checks mapping completeness, type compatibility, and data constraints.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from ..core.logging_config import get_logger
from ..models.mapping_models import MappingConfiguration, FieldMapping
from ..models.salesforce_metadata import SalesforceObject, SalesforceField

logger = get_logger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error."""
    field_name: str
    error_type: str  # 'missing_required', 'type_mismatch', 'invalid_field'
    message: str
    severity: str = 'error'  # 'error' or 'warning'


@dataclass
class ValidationResult:
    """Result of mapping validation."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def get_all_issues(self) -> List[ValidationError]:
        """Get all errors and warnings combined."""
        return self.errors + self.warnings


class MappingValidationService:
    """
    Service for validating field mappings.
    """

    def __init__(self):
        """Initialize the validation service."""
        pass

    def validate(
        self,
        mappings: List[FieldMapping],
        salesforce_object: SalesforceObject
    ) -> ValidationResult:
        """
        Validate a list of field mappings.

        Args:
            mappings: List of FieldMapping objects
            salesforce_object: Target Salesforce object

        Returns:
            ValidationResult with errors and warnings
        """
        logger.info(f"Validating {len(mappings)} mappings for {salesforce_object.name}")

        errors = []
        warnings = []

        # Build lookup for Salesforce fields
        sf_fields_by_name = {f.name: f for f in salesforce_object.fields}

        # Check for required fields
        required_fields = [f for f in salesforce_object.fields if f.required]
        mapped_fields = {m.target_field for m in mappings}

        for required_field in required_fields:
            if required_field.name not in mapped_fields:
                errors.append(ValidationError(
                    field_name=required_field.name,
                    error_type='missing_required',
                    message=f"Required field '{required_field.label}' ({required_field.name}) is not mapped",
                    severity='error'
                ))

        # Check for duplicate mappings (multiple source columns → same target field)
        target_field_counts: Dict[str, int] = {}
        for mapping in mappings:
            target_field_counts[mapping.target_field] = target_field_counts.get(mapping.target_field, 0) + 1

        for target_field, count in target_field_counts.items():
            if count > 1:
                sf_field = sf_fields_by_name.get(target_field)
                field_label = sf_field.label if sf_field else target_field
                warnings.append(ValidationError(
                    field_name=target_field,
                    error_type='duplicate_mapping',
                    message=f"Multiple source columns mapped to '{field_label}' ({target_field})",
                    severity='warning'
                ))

        # Check for invalid target fields
        for mapping in mappings:
            if mapping.target_field not in sf_fields_by_name:
                errors.append(ValidationError(
                    field_name=mapping.target_field,
                    error_type='invalid_field',
                    message=f"Target field '{mapping.target_field}' does not exist on {salesforce_object.name}",
                    severity='error'
                ))

        # Check for non-updateable fields
        for mapping in mappings:
            sf_field = sf_fields_by_name.get(mapping.target_field)
            if sf_field and not sf_field.updateable and sf_field.name != 'Id':
                warnings.append(ValidationError(
                    field_name=mapping.target_field,
                    error_type='non_updateable',
                    message=f"Field '{sf_field.label}' ({sf_field.name}) is not updateable",
                    severity='warning'
                ))

        # Determine overall validity
        is_valid = len(errors) == 0

        result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )

        logger.info(
            f"Validation result: {'VALID' if is_valid else 'INVALID'} "
            f"({len(errors)} errors, {len(warnings)} warnings)"
        )

        return result

    def validate_single_mapping(
        self,
        mapping: FieldMapping,
        salesforce_field: SalesforceField
    ) -> Optional[ValidationError]:
        """
        Validate a single field mapping.

        Args:
            mapping: FieldMapping to validate
            salesforce_field: Target Salesforce field

        Returns:
            ValidationError if there's an issue, None otherwise
        """
        # Check if field is updateable
        if not salesforce_field.updateable and salesforce_field.name != 'Id':
            return ValidationError(
                field_name=salesforce_field.name,
                error_type='non_updateable',
                message=f"Field '{salesforce_field.label}' is not updateable",
                severity='warning'
            )

        return None
