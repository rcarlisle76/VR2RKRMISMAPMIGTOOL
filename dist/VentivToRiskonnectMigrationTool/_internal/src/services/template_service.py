"""
Template generation service.

Creates CSV templates with field headers based on Salesforce object metadata.
"""

import csv
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..core.logging_config import get_logger
from ..models.salesforce_metadata import SalesforceObject, SalesforceField


logger = get_logger(__name__)


class TemplateService:
    """
    Service for generating CSV templates from Salesforce object metadata.
    """

    def generate_template(
        self,
        salesforce_object: SalesforceObject,
        output_path: str,
        include_optional: bool = True,
        include_sample_row: bool = True
    ) -> bool:
        """
        Generate a CSV template for a Salesforce object.

        Args:
            salesforce_object: SalesforceObject with field metadata
            output_path: Path where CSV template will be saved
            include_optional: Include commonly-used optional fields
            include_sample_row: Include a sample data row with field descriptions

        Returns:
            True if template created successfully

        Raises:
            Exception: If template generation fails
        """
        logger.info(f"Generating CSV template for {salesforce_object.name}")

        try:
            # Get fields for template
            fields = self._select_template_fields(salesforce_object, include_optional)

            if not fields:
                raise ValueError(f"No createable fields found for {salesforce_object.name}")

            # Extract field names for headers
            headers = [field.name for field in fields]

            # Create CSV file
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Write header row
                writer.writerow(headers)

                # Optionally write sample/documentation row
                if include_sample_row:
                    sample_row = self._generate_sample_row(fields)
                    writer.writerow(sample_row)

            logger.info(f"Template created successfully: {output_path}")
            logger.info(f"Template contains {len(headers)} fields: {', '.join(headers[:10])}{'...' if len(headers) > 10 else ''}")

            return True

        except Exception as e:
            logger.error(f"Failed to generate template: {e}")
            raise

    def _select_template_fields(
        self,
        salesforce_object: SalesforceObject,
        include_optional: bool
    ) -> List[SalesforceField]:
        """
        Select which fields to include in the template.

        Args:
            salesforce_object: SalesforceObject with field metadata
            include_optional: Include optional fields

        Returns:
            List of SalesforceField objects to include
        """
        selected_fields = []

        # Define commonly-used optional fields
        common_optional_fields = {
            'Description', 'Comments', 'Notes', 'Status', 'Type',
            'Priority', 'Category', 'Owner', 'OwnerId',
            'Phone', 'Email', 'Website', 'Industry',
            'BillingStreet', 'BillingCity', 'BillingState', 'BillingPostalCode', 'BillingCountry',
            'ShippingStreet', 'ShippingCity', 'ShippingState', 'ShippingPostalCode', 'ShippingCountry'
        }

        for field in salesforce_object.fields:
            # Skip system fields that users shouldn't populate
            if field.name in ('Id', 'CreatedDate', 'CreatedById', 'LastModifiedDate', 'LastModifiedById', 'SystemModstamp'):
                continue

            # Skip non-createable fields (formulas, rollups, auto-number)
            if not field.createable:
                continue

            # Skip calculated/auto-number fields
            if field.calculated or field.auto_number:
                continue

            # Include if required
            if field.required:
                selected_fields.append(field)
                continue

            # Include if optional and in common list (and user wants optional fields)
            if include_optional and field.name in common_optional_fields:
                selected_fields.append(field)
                continue

            # Include RecordTypeId if object has record types
            if field.name == 'RecordTypeId' and salesforce_object.record_types:
                selected_fields.append(field)
                continue

        # Sort: required first, then alphabetically
        selected_fields.sort(key=lambda f: (not f.required, f.name))

        return selected_fields

    def _generate_sample_row(self, fields: List[SalesforceField]) -> List[str]:
        """
        Generate a sample/documentation row showing field types and requirements.

        Args:
            fields: List of fields in template

        Returns:
            List of sample values/descriptions
        """
        sample_row = []

        for field in fields:
            # Build description based on field type
            parts = []

            # Add type
            type_label = field.type

            # Add requirement indicator
            if field.required:
                parts.append("REQUIRED")

            # Add type-specific hints
            if field.type in ('picklist', 'multipicklist'):
                if field.picklist_values:
                    # Show first 3 picklist values
                    values = field.picklist_values[:3]
                    values_str = '/'.join(values)
                    if len(field.picklist_values) > 3:
                        values_str += '/...'
                    parts.append(f"Picklist: {values_str}")
                else:
                    parts.append("Picklist")

            elif field.type in ('reference', 'masterDetail'):
                ref_names = ', '.join(field.reference_to) if field.reference_to else 'ID'
                parts.append(f"Lookup ({ref_names} ID)")

            elif field.type == 'boolean':
                parts.append("TRUE/FALSE")

            elif field.type in ('date', 'datetime'):
                if field.type == 'date':
                    parts.append("Date (YYYY-MM-DD)")
                else:
                    parts.append("DateTime (YYYY-MM-DD HH:MM:SS)")

            elif field.type in ('currency', 'double', 'percent'):
                parts.append("Number")

            elif field.type == 'email':
                parts.append("Email address")

            elif field.type == 'phone':
                parts.append("Phone number")

            elif field.type == 'url':
                parts.append("URL")

            elif field.type == 'string' or field.type == 'textarea':
                if field.length:
                    parts.append(f"Text (max {field.length} chars)")
                else:
                    parts.append("Text")

            else:
                parts.append(field.type)

            sample_row.append(' | '.join(parts))

        return sample_row
