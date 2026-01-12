"""
Salesforce client wrapper with session management.

Provides thread-safe connection management and automatic reconnection.
"""

import threading
import requests
import time
import csv
import io
from typing import Any, Dict, Optional, List
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceExpiredSession

from ..base import BaseConnector
from ...core.logging_config import get_logger
from ...core.credentials import SalesforceCredentials
from .auth import SalesforceAuthenticator


logger = get_logger(__name__)


class SalesforceClient(BaseConnector):
    """
    Thread-safe Salesforce API client wrapper.

    Manages Salesforce connection lifecycle including:
    - Authentication
    - Session management
    - Automatic token refresh
    - Thread safety
    """

    def __init__(self):
        """Initialize the Salesforce client."""
        super().__init__()
        self._sf_instance: Optional[Salesforce] = None
        self._credentials: Optional[SalesforceCredentials] = None
        self._lock = threading.Lock()

    def connect(self, credentials: SalesforceCredentials) -> bool:
        """
        Establish connection to Salesforce.

        Args:
            credentials: SalesforceCredentials object

        Returns:
            True if connection successful, False otherwise

        Raises:
            ConnectionError: If connection fails
        """
        with self._lock:
            try:
                logger.info(f"Connecting to Salesforce for user: {credentials.username}")

                # Store credentials for potential reconnection
                self._credentials = credentials

                # Authenticate
                sf_instance, error = SalesforceAuthenticator.authenticate(credentials)

                if sf_instance:
                    self._sf_instance = sf_instance
                    self._connected = True
                    logger.info("Successfully connected to Salesforce")
                    return True
                else:
                    logger.error(f"Failed to connect: {error}")
                    raise ConnectionError(error)

            except Exception as e:
                logger.error(f"Connection error: {e}")
                raise ConnectionError(f"Failed to connect to Salesforce: {str(e)}")

    def disconnect(self) -> bool:
        """
        Close connection to Salesforce.

        Returns:
            True if disconnection successful
        """
        with self._lock:
            try:
                if self._sf_instance:
                    # Clear the instance
                    self._sf_instance = None
                    self._connected = False
                    logger.info("Disconnected from Salesforce")

                return True

            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
                return False

    def is_connected(self) -> bool:
        """
        Check if currently connected to Salesforce.

        Returns:
            True if connected, False otherwise
        """
        return self._connected and self._sf_instance is not None

    def health_check(self) -> bool:
        """
        Perform a health check on the Salesforce connection.

        Returns:
            True if connection is healthy, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            return SalesforceAuthenticator.verify_connection(self._sf_instance)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the Salesforce instance.

        Returns:
            Dictionary containing metadata

        Raises:
            Exception: If not connected
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        try:
            metadata = {
                "instance_url": self._sf_instance.sf_instance,
                "session_id": self._sf_instance.session_id,
                "api_version": self._sf_instance.sf_version,
                "username": self._credentials.username if self._credentials else None
            }
            return metadata

        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            raise

    def get_instance(self) -> Optional[Salesforce]:
        """
        Get the underlying Salesforce instance.

        Returns:
            Salesforce instance or None if not connected
        """
        return self._sf_instance

    def query(self, soql: str) -> Dict[str, Any]:
        """
        Execute a SOQL query.

        Args:
            soql: SOQL query string

        Returns:
            Query results

        Raises:
            Exception: If not connected or query fails
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        with self._lock:
            try:
                logger.debug(f"Executing query: {soql}")
                result = self._sf_instance.query(soql)
                return result

            except SalesforceExpiredSession:
                logger.warning("Session expired, attempting to reconnect")
                if self._reconnect():
                    # Retry query after reconnection
                    result = self._sf_instance.query(soql)
                    return result
                else:
                    raise Exception("Failed to reconnect after session expiration")

            except Exception as e:
                logger.error(f"Query failed: {e}")
                raise

    def _reconnect(self) -> bool:
        """
        Attempt to reconnect to Salesforce.

        Returns:
            True if reconnection successful, False otherwise
        """
        if not self._credentials:
            logger.error("Cannot reconnect: credentials not available")
            return False

        try:
            logger.info("Attempting to reconnect to Salesforce")
            sf_instance, error = SalesforceAuthenticator.authenticate(self._credentials)

            if sf_instance:
                self._sf_instance = sf_instance
                self._connected = True
                logger.info("Successfully reconnected to Salesforce")
                return True
            else:
                logger.error(f"Reconnection failed: {error}")
                return False

        except Exception as e:
            logger.error(f"Reconnection error: {e}")
            return False

    def describe_global(self) -> Dict[str, Any]:
        """
        Get global describe information (list of all objects).

        Returns:
            Dictionary with 'sobjects' list containing all object metadata

        Raises:
            Exception: If not connected or describe fails
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        with self._lock:
            try:
                logger.debug("Fetching global describe")
                # Use simple-salesforce's describe method
                result = self._sf_instance.describe()
                logger.info(f"Retrieved {len(result['sobjects'])} objects")
                return result

            except SalesforceExpiredSession:
                logger.warning("Session expired during describe_global")
                if self._reconnect():
                    result = self._sf_instance.describe()
                    return result
                else:
                    raise Exception("Failed to reconnect after session expiration")

            except Exception as e:
                logger.error(f"Global describe failed: {e}")
                raise

    def describe_object(self, object_name: str) -> Dict[str, Any]:
        """
        Get detailed describe information for a specific object.

        Args:
            object_name: API name of the Salesforce object (e.g., 'Account', 'Custom__c')

        Returns:
            Dictionary containing full object metadata including fields

        Raises:
            Exception: If not connected or describe fails
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        with self._lock:
            try:
                logger.debug(f"Fetching describe for object: {object_name}")
                # Access the SObject and call describe
                sobject = getattr(self._sf_instance, object_name)
                result = sobject.describe()
                logger.info(f"Retrieved metadata for {object_name}: {len(result.get('fields', []))} fields")
                return result

            except SalesforceExpiredSession:
                logger.warning(f"Session expired during describe of {object_name}")
                if self._reconnect():
                    sobject = getattr(self._sf_instance, object_name)
                    result = sobject.describe()
                    return result
                else:
                    raise Exception("Failed to reconnect after session expiration")

            except AttributeError:
                logger.error(f"Object not found: {object_name}")
                raise Exception(f"Object '{object_name}' not found in Salesforce")

            except Exception as e:
                logger.error(f"Describe failed for {object_name}: {e}")
                raise

    # ==================== Bulk API 2.0 Methods ====================

    def create_bulk_job(self, object_name: str, operation: str = 'insert') -> str:
        """
        Create a Bulk API 2.0 job.

        Args:
            object_name: Salesforce object API name
            operation: 'insert', 'update', 'upsert', or 'delete'

        Returns:
            Job ID

        Raises:
            Exception: If job creation fails
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        url = f"{self._sf_instance.base_url}jobs/ingest"
        headers = {
            "Authorization": f"Bearer {self._sf_instance.session_id}",
            "Content-Type": "application/json"
        }
        payload = {
            "object": object_name,
            "operation": operation,
            "contentType": "CSV"
        }

        try:
            logger.info(f"Creating bulk job for {object_name} ({operation})")
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            job_data = response.json()
            job_id = job_data['id']
            logger.info(f"Bulk job created: {job_id}")
            return job_id

        except Exception as e:
            logger.error(f"Failed to create bulk job: {e}")
            raise

    def upload_bulk_data(self, job_id: str, csv_data: List[Dict[str, Any]]) -> bool:
        """
        Upload CSV data to a bulk job.

        Args:
            job_id: Bulk job ID
            csv_data: List of dictionaries to upload

        Returns:
            True if upload successful

        Raises:
            Exception: If upload fails
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        url = f"{self._sf_instance.base_url}jobs/ingest/{job_id}/batches"
        headers = {
            "Authorization": f"Bearer {self._sf_instance.session_id}",
            "Content-Type": "text/csv"
        }

        try:
            # Convert data to CSV string
            if not csv_data:
                raise ValueError("No data to upload")

            csv_buffer = io.StringIO()
            fieldnames = csv_data[0].keys()
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
            csv_content = csv_buffer.getvalue()

            logger.info(f"Uploading {len(csv_data)} records to bulk job {job_id}")
            response = requests.put(url, headers=headers, data=csv_content.encode('utf-8'))
            response.raise_for_status()

            logger.info(f"Data uploaded successfully to job {job_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload data to bulk job: {e}")
            raise

    def close_bulk_job(self, job_id: str) -> bool:
        """
        Close a bulk job to start processing.

        Args:
            job_id: Bulk job ID

        Returns:
            True if job closed successfully

        Raises:
            Exception: If closing fails
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        url = f"{self._sf_instance.base_url}jobs/ingest/{job_id}"
        headers = {
            "Authorization": f"Bearer {self._sf_instance.session_id}",
            "Content-Type": "application/json"
        }
        payload = {"state": "UploadComplete"}

        try:
            logger.info(f"Closing bulk job {job_id}")
            response = requests.patch(url, headers=headers, json=payload)
            response.raise_for_status()

            logger.info(f"Bulk job {job_id} closed and processing started")
            return True

        except Exception as e:
            logger.error(f"Failed to close bulk job: {e}")
            raise

    def get_bulk_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a bulk job.

        Args:
            job_id: Bulk job ID

        Returns:
            Dictionary with job status information

        Raises:
            Exception: If status check fails
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        url = f"{self._sf_instance.base_url}jobs/ingest/{job_id}"
        headers = {
            "Authorization": f"Bearer {self._sf_instance.session_id}"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get bulk job status: {e}")
            raise

    def wait_for_bulk_job(self, job_id: str, max_wait_seconds: int = 3600,
                          poll_interval: int = 5) -> Dict[str, Any]:
        """
        Wait for a bulk job to complete.

        Args:
            job_id: Bulk job ID
            max_wait_seconds: Maximum time to wait (default: 1 hour)
            poll_interval: Seconds between status checks (default: 5)

        Returns:
            Final job status

        Raises:
            Exception: If job fails or timeout occurs
        """
        start_time = time.time()
        while True:
            status = self.get_bulk_job_status(job_id)
            state = status['state']

            logger.debug(f"Bulk job {job_id} state: {state}")

            if state in ('JobComplete', 'Failed', 'Aborted'):
                return status

            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                raise Exception(f"Bulk job {job_id} timeout after {max_wait_seconds} seconds")

            time.sleep(poll_interval)

    def get_bulk_job_results(self, job_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get successful and failed results from a completed bulk job.

        Args:
            job_id: Bulk job ID

        Returns:
            Dictionary with 'successful' and 'failed' lists

        Raises:
            Exception: If getting results fails
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        results = {
            'successful': [],
            'failed': []
        }

        headers = {
            "Authorization": f"Bearer {self._sf_instance.session_id}"
        }

        try:
            # Get successful results
            success_url = f"{self._sf_instance.base_url}jobs/ingest/{job_id}/successfulResults/"
            response = requests.get(success_url, headers=headers)
            if response.status_code == 200:
                csv_reader = csv.DictReader(io.StringIO(response.text))
                results['successful'] = list(csv_reader)

            # Get failed results
            failed_url = f"{self._sf_instance.base_url}jobs/ingest/{job_id}/failedResults/"
            response = requests.get(failed_url, headers=headers)
            if response.status_code == 200:
                csv_reader = csv.DictReader(io.StringIO(response.text))
                results['failed'] = list(csv_reader)

            logger.info(
                f"Bulk job {job_id} results: {len(results['successful'])} successful, "
                f"{len(results['failed'])} failed"
            )

            return results

        except Exception as e:
            logger.error(f"Failed to get bulk job results: {e}")
            raise

    def abort_bulk_job(self, job_id: str) -> bool:
        """
        Abort a running bulk job.

        Args:
            job_id: Bulk job ID

        Returns:
            True if job aborted successfully

        Raises:
            Exception: If abort fails
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        url = f"{self._sf_instance.base_url}jobs/ingest/{job_id}"
        headers = {
            "Authorization": f"Bearer {self._sf_instance.session_id}",
            "Content-Type": "application/json"
        }
        payload = {"state": "Aborted"}

        try:
            logger.info(f"Aborting bulk job {job_id}")
            response = requests.patch(url, headers=headers, json=payload)
            response.raise_for_status()

            logger.info(f"Bulk job {job_id} aborted")
            return True

        except Exception as e:
            logger.error(f"Failed to abort bulk job: {e}")
            raise

    def get_page_layout_fields(self, object_name: str, record_type_id: Optional[str] = None) -> List[str]:
        """
        Get fields from the page layout for an object and record type using UI API.

        Args:
            object_name: API name of the Salesforce object
            record_type_id: Record type ID (optional, uses default if not provided)

        Returns:
            List of field API names from the page layout

        Raises:
            Exception: If UI API call fails
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        try:
            # Use the correct UI API endpoint for record-specific layout
            # /ui-api/record-ui/{recordIds} with layoutTypes parameter
            # OR /ui-api/layout/{objectApiName}
            #
            # Since we need layout by record type, we'll use object-ui endpoint with mode parameter
            # The correct endpoint is: /ui-api/object-info/{objectApiName} to get default record type,
            # then /ui-api/record-ui/{recordIds} with that record type
            #
            # Actually, the simplest approach is to use describe() from Metadata API
            # and get the page layout assignment, then use Tooling API to query the layout
            #
            # For now, let's use a simpler approach: query the Layout object via Tooling API
            base_url = self._sf_instance.base_url.replace('/data/', '/tooling/')

            # Query for page layout assignments for this record type
            if record_type_id:
                # Get layout ID for this record type
                query = f"SELECT Id, Layout.Name, RecordTypeId FROM RecordTypeLayout WHERE RecordTypeId = '{record_type_id}'"
            else:
                # Get default layout for the object
                query = f"SELECT Id FROM Layout WHERE EntityDefinitionId = '{object_name}' AND Name LIKE '%Layout%' LIMIT 1"

            logger.info(f"Querying Tooling API for layout: {query}")
            tooling_url = f"{base_url}query?q={requests.utils.quote(query)}"
            headers = {
                "Authorization": f"Bearer {self._sf_instance.session_id}",
                "Content-Type": "application/json"
            }

            response = requests.get(tooling_url, headers=headers)
            logger.info(f"Tooling API response status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Tooling API error: {response.text[:500]}")
                return []

            layout_result = response.json()
            records = layout_result.get('records', [])

            if not records:
                logger.warning(f"No layout found for {object_name}, record type {record_type_id}")
                return []

            # Get layout metadata
            layout_id = records[0].get('Id') if 'Id' in records[0] else records[0].get('Layout', {}).get('Id')

            if not layout_id:
                logger.warning(f"Could not extract layout ID from response")
                return []

            # Query the actual layout to get field names
            layout_query = f"SELECT Metadata FROM Layout WHERE Id = '{layout_id}'"
            layout_url = f"{base_url}query?q={requests.utils.quote(layout_query)}"

            layout_response = requests.get(layout_url, headers=headers)

            if layout_response.status_code != 200:
                logger.error(f"Failed to fetch layout metadata: {layout_response.text[:500]}")
                return []

            layout_data = layout_response.json()
            layout_records = layout_data.get('records', [])

            if not layout_records:
                return []

            # Parse layout metadata to extract field names
            metadata = layout_records[0].get('Metadata', {})
            layout_fields = set()

            # Extract fields from layout sections
            sections = metadata.get('layoutSections', [])
            for section in sections:
                layout_columns = section.get('layoutColumns', [])
                for column in layout_columns:
                    layout_items = column.get('layoutItems', [])
                    for item in layout_items:
                        field_name = item.get('field')
                        if field_name:
                            layout_fields.add(field_name)

            field_list = sorted(list(layout_fields))
            logger.info(f"Retrieved {len(field_list)} fields from page layout for {object_name}")
            return field_list

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching page layout: {e}")
            logger.error(f"Response status: {e.response.status_code if e.response else 'N/A'}")
            logger.error(f"Response body: {e.response.text[:1000] if e.response else 'N/A'}")
            # Return empty list to fall back to default behavior
            return []
        except Exception as e:
            logger.error(f"Failed to get page layout fields: {e}", exc_info=True)
            # Return empty list to fall back to default behavior
            return []

    def get_page_layout_assignments(self, object_name: str, record_types: list = None) -> Dict[str, str]:
        """
        Get page layout assignments for record types using simple-salesforce Metadata API.

        Args:
            object_name: API name of the Salesforce object
            record_types: List of RecordType objects with name and record_type_id

        Returns:
            Dict mapping record_type_id -> layout_name

        Raises:
            Exception: If API call fails
        """
        if not self.is_connected():
            raise Exception("Not connected to Salesforce")

        try:
            # Use simple-salesforce to list available layouts via REST API
            # Query the Layout sobject directly
            logger.info(f"Fetching page layouts for {object_name} using Metadata API")

            # First, try to get layout names by querying Metadata API via REST
            # Use the Metadata API listMetadata endpoint
            metadata_url = f"{self._sf_instance.base_url.replace('/data/', '/metadata/')}listMetadata/"
            headers = {
                "Authorization": f"Bearer {self._sf_instance.session_id}",
                "Content-Type": "application/json"
            }

            # Query for Layout metadata
            payload = {
                "type": "Layout",
                "folder": object_name
            }

            logger.info(f"Calling Metadata API listMetadata for Layout type, folder: {object_name}")
            response = requests.post(metadata_url, headers=headers, json=payload)

            # If listMetadata doesn't work, try describe API
            if response.status_code != 200:
                logger.warning(f"listMetadata failed ({response.status_code}), trying describe approach")

                # Alternative: use the metadata describe endpoint
                describe_url = f"{self._sf_instance.base_url}sobjects/{object_name}/describe"
                describe_response = requests.get(describe_url, headers=headers)
                describe_response.raise_for_status()
                describe_data = describe_response.json()

                # Get record type infos which include layout information
                record_type_infos = describe_data.get('recordTypeInfos', [])

                if not record_type_infos:
                    logger.warning(f"No record type info found for {object_name}")
                    if record_types:
                        return {rt.record_type_id: f"{object_name} Layout" for rt in record_types}
                    return {}

                logger.info(f"Found {len(record_type_infos)} record type infos from describe")

                # Build mapping by fetching layout details from the layout URL
                # Store both layout names and full layout data (with fields)
                layout_assignments = {}
                layout_data_cache = {}  # Cache full layout structures by layout_id

                for rt_info in record_type_infos:
                    rt_id = rt_info.get('recordTypeId')
                    urls = rt_info.get('urls', {})
                    layout_url = urls.get('layout')

                    if not rt_id or not layout_url:
                        logger.warning(f"Skipping record type with missing data: recordTypeId={rt_id}, layout_url={layout_url}")
                        continue

                    try:
                        # Fetch layout details from the layout URL
                        # Construct full URL using the base URL from Salesforce instance
                        base_instance_url = f"https://{self._sf_instance.sf_instance}"
                        full_url = f"{base_instance_url}{layout_url}"
                        logger.info(f"Fetching layout for record type {rt_id} from: {full_url}")

                        layout_response = requests.get(full_url, headers=headers)

                        if layout_response.status_code == 200:
                            layout_data = layout_response.json()

                            # Extract the layout ID from the response
                            layout_id = layout_data.get('id')

                            if layout_id:
                                # Use Tooling API to query the Layout object for the name
                                try:
                                    import urllib.parse
                                    query = f"SELECT Name FROM Layout WHERE Id = '{layout_id}'"
                                    encoded_query = urllib.parse.quote(query)
                                    tooling_url = f"{base_instance_url}/services/data/v57.0/tooling/query/?q={encoded_query}"

                                    tooling_response = requests.get(tooling_url, headers=headers)

                                    if tooling_response.status_code == 200:
                                        tooling_data = tooling_response.json()
                                        records = tooling_data.get('records', [])

                                        if records and len(records) > 0:
                                            layout_name = records[0].get('Name', 'Unknown Layout')

                                            # Store layout assignment with name and ID
                                            layout_assignments[rt_id] = {
                                                'name': layout_name,
                                                'id': layout_id
                                            }

                                            # Cache the full layout structure (with fields)
                                            if layout_id not in layout_data_cache:
                                                layout_data_cache[layout_id] = layout_data

                                            logger.info(f"Record type {rt_id} -> Layout: {layout_name}")
                                        else:
                                            logger.warning(f"No layout records found for layout ID {layout_id}")
                                            layout_assignments[rt_id] = {'name': "Unknown Layout", 'id': None}
                                    else:
                                        logger.warning(f"Tooling API query failed for layout {layout_id}: {tooling_response.status_code}")
                                        layout_assignments[rt_id] = {'name': "Unknown Layout", 'id': None}

                                except Exception as e:
                                    logger.error(f"Error querying layout name for {layout_id}: {e}")
                                    layout_assignments[rt_id] = {'name': "Unknown Layout", 'id': None}
                            else:
                                logger.warning(f"No layout ID found in response for record type {rt_id}")
                                layout_assignments[rt_id] = {'name': "Unknown Layout", 'id': None}
                        else:
                            logger.warning(f"Failed to fetch layout for {rt_id}: {layout_response.status_code}")
                            layout_assignments[rt_id] = {'name': "Layout Not Found", 'id': None}

                    except Exception as e:
                        logger.error(f"Error fetching layout for record type {rt_id}: {e}")
                        layout_assignments[rt_id] = {'name': "Error Loading Layout", 'id': None}

                # Store layout data cache in the client for later retrieval
                self._layout_data_cache = layout_data_cache

                logger.info(f"Retrieved {len(layout_assignments)} layout assignments via layout URLs")
                return layout_assignments

            # Process listMetadata response
            response.raise_for_status()
            layout_list = response.json()

            if not layout_list:
                logger.warning(f"No layouts returned from listMetadata for {object_name}")
                if record_types:
                    return {rt.record_type_id: f"{object_name} Layout" for rt in record_types}
                return {}

            # listMetadata returns list of metadata components
            logger.info(f"Found {len(layout_list) if isinstance(layout_list, list) else 1} layouts")

            # For now, assign first layout to all record types
            # Getting specific assignments requires reading each layout's full metadata
            if record_types:
                first_layout_name = layout_list[0].get('fullName', f"{object_name} Layout") if isinstance(layout_list, list) else layout_list.get('fullName', f"{object_name} Layout")
                layout_assignments = {rt.record_type_id: first_layout_name for rt in record_types}
                logger.info(f"Assigned layout '{first_layout_name}' to all {len(record_types)} record types")
                return layout_assignments

            return {}

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching page layouts: {e}")
            logger.error(f"Response status: {e.response.status_code if e.response else 'N/A'}")
            if e.response:
                logger.error(f"Response body: {e.response.text[:1000]}")
            # Fallback on error
            if record_types:
                return {rt.record_type_id: f"{object_name} Layout" for rt in record_types}
            return {}
        except Exception as e:
            logger.error(f"Failed to get page layout assignments: {e}", exc_info=True)
            # Fallback on error
            if record_types:
                return {rt.record_type_id: f"{object_name} Layout" for rt in record_types}
            return {}

    def get_layout_fields(self, layout_id: str) -> List[str]:
        """
        Get list of field API names on a specific page layout.

        Args:
            layout_id: Salesforce layout ID

        Returns:
            List of field API names on the layout
        """
        try:
            if not hasattr(self, '_layout_data_cache') or not self._layout_data_cache:
                logger.warning("No layout data cache available")
                return []

            layout_data = self._layout_data_cache.get(layout_id)
            if not layout_data:
                logger.warning(f"No cached layout data for layout ID {layout_id}")
                logger.info(f"Available layout IDs in cache: {list(self._layout_data_cache.keys())}")
                return []

            logger.info(f"Processing layout data for {layout_id}")
            logger.info(f"Layout data keys: {list(layout_data.keys())}")

            field_names = set()

            # Extract fields from editLayoutSections
            edit_sections = layout_data.get('editLayoutSections', [])
            logger.info(f"Found {len(edit_sections)} edit layout sections")
            for section in edit_sections:
                layout_rows = section.get('layoutRows', [])
                for row in layout_rows:
                    layout_items = row.get('layoutItems', [])
                    for item in layout_items:
                        layout_components = item.get('layoutComponents', [])
                        for component in layout_components:
                            field_name = component.get('value')
                            if field_name:
                                field_names.add(field_name)

            # Extract fields from detailLayoutSections
            detail_sections = layout_data.get('detailLayoutSections', [])
            logger.info(f"Found {len(detail_sections)} detail layout sections")
            for section in detail_sections:
                layout_rows = section.get('layoutRows', [])
                for row in layout_rows:
                    layout_items = row.get('layoutItems', [])
                    for item in layout_items:
                        layout_components = item.get('layoutComponents', [])
                        for component in layout_components:
                            field_name = component.get('value')
                            if field_name:
                                field_names.add(field_name)

            logger.info(f"Extracted {len(field_names)} fields from layout {layout_id}")
            return sorted(list(field_names))

        except Exception as e:
            logger.error(f"Error extracting fields from layout {layout_id}: {e}", exc_info=True)
            return []
