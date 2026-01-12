"""
Data preview service - executes SOQL queries to fetch sample data.

Retrieves a limited number of records for preview purposes.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.logging_config import get_logger
from ..connectors.salesforce.client import SalesforceClient
from ..models.salesforce_metadata import SalesforceObject

logger = get_logger(__name__)


class DataPreviewService:
    """
    Service for fetching sample data from Salesforce objects.
    """

    def __init__(self, sf_client: SalesforceClient):
        """
        Initialize the data preview service.

        Args:
            sf_client: Authenticated SalesforceClient instance
        """
        self.sf_client = sf_client

    def get_sample_data(
        self,
        object_name: str,
        fields: List[str],
        limit: int = 20,
        record_type_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch sample records from an object.

        Args:
            object_name: API name of the object
            fields: List of field API names to retrieve
            limit: Maximum number of records to fetch (default 20)
            record_type_id: Optional record type ID to filter by

        Returns:
            Dictionary with 'records' list and 'total_size' count
        """
        logger.info(f"Fetching sample data for {object_name} (limit: {limit}, record_type: {record_type_id or 'all'})")

        try:
            # Build SOQL query
            field_list = ", ".join(fields)
            soql = f"SELECT {field_list} FROM {object_name}"

            # Add WHERE clause for record type if specified
            if record_type_id:
                soql += f" WHERE RecordTypeId = '{record_type_id}'"

            soql += f" LIMIT {limit}"

            logger.debug(f"Executing SOQL: {soql}")

            # Execute query
            result = self.sf_client.query(soql)

            records = result.get('records', [])
            total_size = result.get('totalSize', 0)

            # Remove 'attributes' from each record (internal Salesforce metadata)
            cleaned_records = []
            for record in records:
                cleaned = {k: v for k, v in record.items() if k != 'attributes'}
                cleaned_records.append(cleaned)

            logger.info(f"Retrieved {len(cleaned_records)} records for {object_name}")

            return {
                'records': cleaned_records,
                'total_size': total_size
            }

        except Exception as e:
            logger.error(f"Error fetching sample data for {object_name}: {e}")
            raise

    def get_sample_data_for_object(
        self,
        salesforce_object: SalesforceObject,
        limit: int = 20,
        include_all_required: bool = True,
        record_type_id: Optional[str] = None,
        layout_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch sample records for a SalesforceObject.

        Automatically selects important fields to display.

        Args:
            salesforce_object: SalesforceObject instance with metadata
            limit: Maximum number of records to fetch
            include_all_required: Whether to include all required fields (default True)
            record_type_id: Optional record type ID to filter by
            layout_fields: Optional list of fields from page layout (if provided, overrides automatic selection)

        Returns:
            Dictionary with 'records', 'total_size', and 'fields' (field names used)
        """
        logger.info(f"Fetching sample data for object: {salesforce_object.name}")

        # Use layout fields if provided, otherwise select fields automatically
        if layout_fields:
            # Filter to only include fields that exist in the object
            available_field_names = {f.name for f in salesforce_object.fields}
            selected_fields = [f for f in layout_fields if f in available_field_names]
            logger.info(f"Using {len(selected_fields)} fields from page layout")
        else:
            # Select fields to query
            selected_fields = self._select_preview_fields(
                salesforce_object.fields,
                include_all_required
            )

        if not selected_fields:
            logger.warning(f"No queryable fields found for {salesforce_object.name}")
            return {
                'records': [],
                'total_size': 0,
                'fields': []
            }

        # Fetch data
        result = self.get_sample_data(
            salesforce_object.name,
            selected_fields,
            limit,
            record_type_id
        )

        result['fields'] = selected_fields
        return result

    def _select_preview_fields(
        self,
        fields: List,
        include_all_required: bool = True
    ) -> List[str]:
        """
        Select the most relevant fields for preview.

        Prioritizes: Id, Name, all required fields, then common fields.

        Args:
            fields: List of SalesforceField objects
            include_all_required: If True, includes ALL required fields regardless of count

        Returns:
            List of field API names to query
        """
        selected = []

        # Priority 1: Always include Id if it exists
        id_field = next((f for f in fields if f.name == 'Id'), None)
        if id_field:
            selected.append('Id')

        # Priority 2: Name field (common identifier)
        name_field = next((f for f in fields if f.name == 'Name'), None)
        if name_field:
            selected.append('Name')

        # Priority 3: ALL Required fields (if include_all_required is True)
        if include_all_required:
            for field in fields:
                if field.required and field.name not in selected:
                    # Skip system fields that can't be set by users
                    if field.name not in ['Id', 'CreatedDate', 'CreatedById',
                                         'LastModifiedDate', 'LastModifiedById',
                                         'SystemModstamp', 'IsDeleted']:
                        selected.append(field.name)
                        logger.debug(f"Added required field: {field.name}")

        # Priority 4: Common important fields (for context)
        common_fields = [
            'CreatedDate', 'LastModifiedDate', 'OwnerId', 'RecordTypeId'
        ]

        for field_name in common_fields:
            field = next((f for f in fields if f.name == field_name), None)
            if field and field.name not in selected:
                selected.append(field.name)

        # Priority 5: Other createable fields (limit to 10 additional to keep UI manageable)
        additional_count = 0
        max_additional = 10
        for field in fields:
            if additional_count >= max_additional:
                break
            if field.createable and field.name not in selected:
                selected.append(field.name)
                additional_count += 1

        logger.info(f"Selected {len(selected)} fields for preview (required fields included: {include_all_required})")
        return selected
