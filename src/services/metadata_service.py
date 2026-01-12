"""
Metadata service for Salesforce schema discovery.

Handles retrieving, caching, and filtering Salesforce object metadata.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from ..core.logging_config import get_logger
from ..connectors.salesforce.client import SalesforceClient
from ..models.salesforce_metadata import SalesforceObject, SalesforceField, ObjectListItem, RecordType


logger = get_logger(__name__)


class MetadataService:
    """
    Service for managing Salesforce metadata operations.

    Coordinates between Salesforce API and cached metadata.
    """

    def __init__(self, sf_client: SalesforceClient, cache_dir: Optional[Path] = None):
        """
        Initialize metadata service.

        Args:
            sf_client: Authenticated Salesforce client
            cache_dir: Directory for caching metadata (default: ~/.salesforce_migration_tool/cache)
        """
        self.sf_client = sf_client

        # Set up cache directory
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            home_dir = Path.home()
            self.cache_dir = home_dir / ".salesforce_migration_tool" / "cache"

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"MetadataService initialized with cache dir: {self.cache_dir}")

    def get_all_objects(self,
                       force_refresh: bool = False,
                       include_custom: bool = True,
                       include_standard: bool = True) -> List[ObjectListItem]:
        """
        Get list of all Salesforce objects.

        Args:
            force_refresh: If True, bypass cache and fetch from Salesforce
            include_custom: Include custom objects
            include_standard: Include standard objects

        Returns:
            List of ObjectListItem objects

        Raises:
            Exception: If Salesforce API call fails
        """
        try:
            logger.info("Fetching all Salesforce objects")

            # Get global describe from Salesforce
            result = self.sf_client.describe_global()

            # Parse sobjects list
            objects = []
            for sobject_data in result.get('sobjects', []):
                # Filter based on custom/standard
                is_custom = sobject_data.get('custom', False)

                if (is_custom and not include_custom) or (not is_custom and not include_standard):
                    continue

                # Only include queryable objects
                if not sobject_data.get('queryable', False):
                    continue

                obj = ObjectListItem(
                    name=sobject_data['name'],
                    label=sobject_data['label'],
                    label_plural=sobject_data.get('labelPlural', sobject_data['label']),
                    custom=is_custom,
                    queryable=sobject_data.get('queryable', False)
                )
                objects.append(obj)

            logger.info(f"Retrieved {len(objects)} objects (custom: {sum(1 for o in objects if o.custom)}, "
                       f"standard: {sum(1 for o in objects if not o.custom)})")

            return sorted(objects, key=lambda x: x.label)

        except Exception as e:
            logger.error(f"Failed to get all objects: {e}")
            raise

    def get_object_metadata(self,
                           object_name: str,
                           force_refresh: bool = False) -> SalesforceObject:
        """
        Get detailed metadata for a specific object.

        Args:
            object_name: API name of the Salesforce object
            force_refresh: If True, bypass cache and fetch from Salesforce

        Returns:
            SalesforceObject with full field metadata

        Raises:
            Exception: If Salesforce API call fails or object not found
        """
        try:
            logger.info(f"Fetching metadata for object: {object_name}")

            # Get describe from Salesforce
            describe_result = self.sf_client.describe_object(object_name)

            # Parse object metadata
            obj = self._parse_object_describe(describe_result)

            logger.info(f"Retrieved metadata for {object_name}: {len(obj.fields)} fields")

            return obj

        except Exception as e:
            logger.error(f"Failed to get metadata for {object_name}: {e}")
            raise

    def _parse_object_describe(self, describe_data: Dict[str, Any]) -> SalesforceObject:
        """
        Parse Salesforce describe response into SalesforceObject model.

        Args:
            describe_data: Raw describe response from Salesforce API

        Returns:
            SalesforceObject instance
        """
        # Parse fields
        fields = []
        for field_data in describe_data.get('fields', []):
            field = SalesforceField(
                name=field_data['name'],
                label=field_data.get('label', field_data['name']),
                type=field_data['type'],
                length=field_data.get('length'),
                required=not field_data.get('nillable', True),
                updateable=field_data.get('updateable', False),
                createable=field_data.get('createable', False),
                relationship_name=field_data.get('relationshipName'),
                reference_to=field_data.get('referenceTo', []),
                picklist_values=[pv['value'] for pv in field_data.get('picklistValues', [])],
                default_value=field_data.get('defaultValue'),
                calculated=field_data.get('calculated', False),
                auto_number=field_data.get('autoNumber', False)
            )
            fields.append(field)

        # Fetch record types
        record_types = self._fetch_record_types(describe_data['name'])

        # Create object
        obj = SalesforceObject(
            name=describe_data['name'],
            label=describe_data['label'],
            label_plural=describe_data.get('labelPlural', describe_data['label']),
            custom=describe_data.get('custom', False),
            fields=fields,
            record_types=record_types,
            createable=describe_data.get('createable', False),
            updateable=describe_data.get('updateable', False),
            deletable=describe_data.get('deletable', False),
            queryable=describe_data.get('queryable', False),
            fetched_at=datetime.now()
        )

        return obj

    def _fetch_record_types(self, object_name: str) -> List[RecordType]:
        """
        Fetch available record types for an object.

        Args:
            object_name: Salesforce object API name

        Returns:
            List of RecordType objects
        """
        try:
            # Query for active record types
            query = f"""
                SELECT Id, Name, DeveloperName, IsActive
                FROM RecordType
                WHERE SObjectType = '{object_name}' AND IsActive = TRUE
            """

            result = self.sf_client.query(query)
            record_types = []

            for rt_data in result.get('records', []):
                record_type = RecordType(
                    record_type_id=rt_data['Id'],
                    name=rt_data['DeveloperName'],
                    label=rt_data['Name'],
                    is_active=rt_data['IsActive'],
                    is_default=False  # We'll set this separately if needed
                )
                record_types.append(record_type)

            logger.debug(f"Found {len(record_types)} record types for {object_name}")
            return record_types

        except Exception as e:
            logger.warning(f"Could not fetch record types for {object_name}: {e}")
            return []

    def search_objects(self, query: str, objects: List[ObjectListItem]) -> List[ObjectListItem]:
        """
        Search/filter objects by name or label.

        Args:
            query: Search query string
            objects: List of objects to search

        Returns:
            Filtered list of objects
        """
        if not query:
            return objects

        query_lower = query.lower()
        return [
            obj for obj in objects
            if query_lower in obj.name.lower() or query_lower in obj.label.lower()
        ]
