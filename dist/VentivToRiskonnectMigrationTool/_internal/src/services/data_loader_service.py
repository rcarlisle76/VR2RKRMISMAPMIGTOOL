"""
Data loader service - loads data into Salesforce.

Transforms CSV data based on field mappings and inserts/updates records.
"""

import csv
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import re

from ..core.logging_config import get_logger
from ..connectors.salesforce.client import SalesforceClient
from ..models.mapping_models import FieldMapping, SourceFile
from ..models.salesforce_metadata import SalesforceObject

logger = get_logger(__name__)

# Threshold for switching from REST API to Bulk API
BULK_API_THRESHOLD = 200


@dataclass
class LoadResult:
    """Result of a data load operation."""
    total_rows: int
    successful_rows: int
    failed_rows: int
    errors: List[Dict[str, Any]]  # List of error details

    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_rows == 0:
            return 0.0
        return (self.successful_rows / self.total_rows) * 100


class DataLoaderService:
    """
    Service for loading data into Salesforce.
    """

    def __init__(self, sf_client: SalesforceClient):
        """
        Initialize the data loader service.

        Args:
            sf_client: Authenticated SalesforceClient instance
        """
        self.sf_client = sf_client

    def load_data(
        self,
        source_file: SourceFile,
        mappings: List[FieldMapping],
        salesforce_object: SalesforceObject,
        operation: str = 'insert',
        record_type_id: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> LoadResult:
        """
        Load data from source file to Salesforce.

        Args:
            source_file: Source CSV file
            mappings: Field mappings
            salesforce_object: Target Salesforce object with field metadata
            operation: 'insert' or 'update'
            record_type_id: Optional record type ID to assign to new records
            progress_callback: Optional callback for progress updates (message: str)

        Returns:
            LoadResult with statistics and errors
        """
        logger.info(f"Starting data load: {source_file.file_path} -> {salesforce_object.name} ({operation})")

        # Read CSV data
        csv_data = self._read_csv_data(source_file.file_path)
        total_rows = len(csv_data)

        logger.info(f"Read {total_rows} rows from CSV")

        # Transform data based on mappings
        transformed_data = self._transform_data(csv_data, mappings, salesforce_object, record_type_id)

        # Choose between REST API and Bulk API based on record count
        if total_rows >= BULK_API_THRESHOLD:
            logger.info(f"Using Bulk API for {total_rows} records (threshold: {BULK_API_THRESHOLD})")
            result = self._load_bulk(salesforce_object.name, transformed_data, operation, progress_callback)
        else:
            logger.info(f"Using REST API for {total_rows} records")
            # Load to Salesforce using REST API
            if operation == 'insert':
                result = self._insert_records(salesforce_object.name, transformed_data, progress_callback)
            elif operation == 'update':
                result = self._update_records(salesforce_object.name, transformed_data, progress_callback)
            else:
                raise ValueError(f"Invalid operation: {operation}")

        logger.info(
            f"Load complete: {result.successful_rows}/{result.total_rows} successful, "
            f"{result.failed_rows} failed"
        )

        return result

    def _read_csv_data(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read CSV file data.

        Args:
            file_path: Path to CSV file

        Returns:
            List of row dictionaries
        """
        rows = []

        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, newline='') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    break
            except UnicodeDecodeError:
                continue

        if not rows:
            raise ValueError("Unable to read CSV file with supported encodings")

        return rows

    def _transform_data(
        self,
        csv_data: List[Dict[str, Any]],
        mappings: List[FieldMapping],
        salesforce_object: SalesforceObject,
        record_type_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform CSV data based on field mappings with type conversion.

        Args:
            csv_data: Raw CSV data
            mappings: Field mappings
            salesforce_object: Target Salesforce object with field metadata
            record_type_id: Optional record type ID to assign to records

        Returns:
            Transformed data ready for Salesforce
        """
        logger.debug(f"Transforming {len(csv_data)} rows with {len(mappings)} mappings")

        # Build mapping lookup
        mapping_dict = {m.source_column: m.target_field for m in mappings}

        # Build field metadata lookup
        field_metadata = {f.name: f for f in salesforce_object.fields}

        transformed_rows = []

        for row_idx, csv_row in enumerate(csv_data):
            sf_row = {}

            # Add record type if specified (this takes precedence over any CSV mapping)
            if record_type_id:
                sf_row['RecordTypeId'] = record_type_id

            for source_col, target_field in mapping_dict.items():
                # Skip RecordTypeId - we set it from the dialog selection, not from CSV
                if target_field == 'RecordTypeId':
                    continue

                # Get value from CSV
                value = csv_row.get(source_col, '')

                # Get field metadata
                field = field_metadata.get(target_field)
                if not field:
                    continue

                # Skip non-createable fields (formula, roll-up summary, auto-number, etc.)
                if not field.createable:
                    if row_idx == 0:  # Log once per field
                        logger.warning(
                            f"Skipping read-only field '{field.name}' (createable={field.createable}, "
                            f"calculated={field.calculated}, auto_number={field.auto_number})"
                        )
                    continue

                # Also skip calculated fields even if createable flag is incorrectly set
                if field.calculated or field.auto_number:
                    if row_idx == 0:
                        logger.warning(
                            f"Skipping calculated/auto-number field '{field.name}' "
                            f"(calculated={field.calculated}, auto_number={field.auto_number})"
                        )
                    continue

                # Convert value based on field type
                converted_value = self._convert_value(value, field)

                # Only add non-None values
                if converted_value is not None:
                    sf_row[target_field] = converted_value

            transformed_rows.append(sf_row)

        return transformed_rows

    def _convert_value(self, value: Any, field: 'SalesforceField') -> Any:
        """
        Convert a value to the appropriate type for Salesforce.

        Args:
            value: Raw value from CSV
            field: SalesforceField with type and picklist information

        Returns:
            Converted value or None
        """
        # Handle empty values
        if value == '' or value is None:
            return None

        # Convert to string for processing
        str_value = str(value).strip()

        if not str_value:
            return None

        field_type = field.type

        try:
            # Picklist fields - validate against allowed values
            if field_type in ('picklist', 'multipicklist') and field.picklist_values:
                # Try exact match first
                if str_value in field.picklist_values:
                    return str_value

                # Try case-insensitive match
                picklist_lower = {v.lower(): v for v in field.picklist_values}
                if str_value.lower() in picklist_lower:
                    matched_value = picklist_lower[str_value.lower()]
                    logger.debug(f"Picklist value '{str_value}' matched to '{matched_value}'")
                    return matched_value

                # No match found - skip this value
                logger.warning(
                    f"Skipping invalid picklist value '{str_value}' for field {field.name}. "
                    f"Valid values: {', '.join(field.picklist_values[:5])}{'...' if len(field.picklist_values) > 5 else ''}"
                )
                return None

            # Lookup/Reference fields - only accept valid Salesforce IDs
            elif field_type in ('reference', 'masterDetail'):
                # Salesforce IDs are 15 or 18 characters, alphanumeric
                if len(str_value) in (15, 18) and str_value.isalnum():
                    return str_value
                else:
                    # Not a valid ID, skip this field
                    logger.warning(f"Skipping lookup field value '{str_value}' - not a valid Salesforce ID")
                    return None

            # Boolean fields
            elif field_type == 'boolean':
                lower_value = str_value.lower()
                if lower_value in ('true', 'yes', '1', 'y', 't'):
                    return True
                elif lower_value in ('false', 'no', '0', 'n', 'f'):
                    return False
                else:
                    return None

            # Numeric fields
            elif field_type in ('int', 'integer', 'long'):
                # Remove commas from numbers
                clean_value = str_value.replace(',', '')
                return int(float(clean_value))

            elif field_type in ('double', 'currency', 'percent'):
                # Remove commas and currency symbols
                clean_value = str_value.replace(',', '').replace('$', '').replace('%', '')
                return float(clean_value)

            # Date fields
            elif field_type == 'date':
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y']:
                    try:
                        dt = datetime.strptime(str_value, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                # If no format matched, return None
                logger.warning(f"Could not parse date value: {str_value}")
                return None

            # DateTime fields
            elif field_type == 'datetime':
                # Try common datetime formats
                for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                    try:
                        dt = datetime.strptime(str_value, fmt)
                        return dt.strftime('%Y-%m-%dT%H:%M:%S.000+0000')
                    except ValueError:
                        continue
                # Try date-only format
                try:
                    dt = datetime.strptime(str_value, '%Y-%m-%d')
                    return dt.strftime('%Y-%m-%dT00:00:00.000+0000')
                except ValueError:
                    pass
                logger.warning(f"Could not parse datetime value: {str_value}")
                return None

            # String fields (default)
            else:
                return str_value

        except Exception as e:
            logger.warning(f"Error converting value '{value}' to type '{field_type}': {e}")
            return None

    def _load_bulk(
        self,
        object_name: str,
        records: List[Dict[str, Any]],
        operation: str = 'insert',
        progress_callback: Optional[callable] = None
    ) -> LoadResult:
        """
        Load records using Bulk API 2.0.

        Args:
            object_name: Salesforce object API name
            records: Records to load
            operation: 'insert', 'update', 'upsert', or 'delete'
            progress_callback: Optional callback for progress updates

        Returns:
            LoadResult
        """
        logger.info(f"Starting Bulk API load: {len(records)} records to {object_name}")

        try:
            # Step 1: Create bulk job
            if progress_callback:
                progress_callback("Creating bulk job...")
            job_id = self.sf_client.create_bulk_job(object_name, operation)
            logger.info(f"Created bulk job: {job_id}")

            # Step 2: Upload data
            if progress_callback:
                progress_callback(f"Uploading {len(records)} records...")
            self.sf_client.upload_bulk_data(job_id, records)
            logger.info("Data uploaded successfully")

            # Step 3: Close job to start processing
            if progress_callback:
                progress_callback("Starting job processing...")
            self.sf_client.close_bulk_job(job_id)
            logger.info("Bulk job closed and processing started")

            # Step 4: Wait for job completion with progress updates
            if progress_callback:
                progress_callback("Processing records...")

            final_status = self.sf_client.wait_for_bulk_job(
                job_id,
                max_wait_seconds=3600,
                poll_interval=5
            )

            logger.info(f"Bulk job completed with state: {final_status['state']}")

            # Step 5: Get results
            if progress_callback:
                progress_callback("Retrieving results...")

            results = self.sf_client.get_bulk_job_results(job_id)

            successful_count = len(results['successful'])
            failed_count = len(results['failed'])

            # Parse error details
            errors = []
            for idx, failed_record in enumerate(results['failed']):
                errors.append({
                    'row': idx + 1,
                    'record': failed_record,
                    'error': failed_record.get('sf__Error', 'Unknown error')
                })

            logger.info(
                f"Bulk job {job_id} results: {successful_count} successful, {failed_count} failed"
            )

            return LoadResult(
                total_rows=len(records),
                successful_rows=successful_count,
                failed_rows=failed_count,
                errors=errors
            )

        except Exception as e:
            logger.error(f"Bulk load failed: {e}")
            # Return error result
            return LoadResult(
                total_rows=len(records),
                successful_rows=0,
                failed_rows=len(records),
                errors=[{
                    'row': 0,
                    'record': {},
                    'error': f"Bulk API error: {str(e)}"
                }]
            )

    def _insert_records(
        self,
        object_name: str,
        records: List[Dict[str, Any]],
        progress_callback: Optional[callable] = None
    ) -> LoadResult:
        """
        Insert records into Salesforce.

        Args:
            object_name: Salesforce object API name
            records: Records to insert
            progress_callback: Optional callback for progress updates

        Returns:
            LoadResult
        """
        logger.info(f"Inserting {len(records)} records into {object_name}")

        successful = 0
        failed = 0
        errors = []
        total_records = len(records)

        # Get sobject
        sobject = getattr(self.sf_client._sf_instance, object_name)

        # Insert records one by one (for now - can optimize with bulk later)
        for idx, record in enumerate(records):
            try:
                # Remove None values and Id field for insert
                cleaned_record = {k: v for k, v in record.items() if v is not None and k != 'Id'}

                # Log fields being inserted for first record
                if idx == 0:
                    logger.info(f"Fields being inserted: {', '.join(sorted(cleaned_record.keys()))}")

                # Insert
                result = sobject.create(cleaned_record)

                if result.get('success'):
                    successful += 1
                    logger.debug(f"Row {idx + 1}: Inserted successfully (ID: {result.get('id')})")
                else:
                    failed += 1
                    error_msg = '; '.join([e.get('message', 'Unknown error') for e in result.get('errors', [])])
                    errors.append({
                        'row': idx + 1,
                        'record': record,
                        'error': error_msg
                    })
                    logger.warning(f"Row {idx + 1}: Insert failed - {error_msg}")

            except Exception as e:
                failed += 1
                errors.append({
                    'row': idx + 1,
                    'record': record,
                    'error': str(e)
                })
                logger.error(f"Row {idx + 1}: Exception during insert - {e}")

            # Report progress
            if progress_callback:
                current = idx + 1
                progress_callback(current, successful, failed, total_records)

        return LoadResult(
            total_rows=len(records),
            successful_rows=successful,
            failed_rows=failed,
            errors=errors
        )

    def _update_records(
        self,
        object_name: str,
        records: List[Dict[str, Any]],
        progress_callback: Optional[callable] = None
    ) -> LoadResult:
        """
        Update records in Salesforce.

        Args:
            object_name: Salesforce object API name
            records: Records to update (must include Id field)
            progress_callback: Optional callback for progress updates

        Returns:
            LoadResult
        """
        logger.info(f"Updating {len(records)} records in {object_name}")

        successful = 0
        failed = 0
        errors = []
        total_records = len(records)

        # Get sobject
        sobject = getattr(self.sf_client._sf_instance, object_name)

        # Update records one by one
        for idx, record in enumerate(records):
            try:
                # Must have Id field for update
                if 'Id' not in record or not record['Id']:
                    failed += 1
                    errors.append({
                        'row': idx + 1,
                        'record': record,
                        'error': 'Missing Id field for update operation'
                    })
                    # Report progress even for validation failures
                    if progress_callback:
                        current = idx + 1
                        progress_callback(current, successful, failed, total_records)
                    continue

                record_id = record['Id']

                # Remove Id from update data
                update_data = {k: v for k, v in record.items() if k != 'Id' and v is not None}

                # Update
                result = sobject.update(record_id, update_data)

                # simple-salesforce returns 204 (no content) on successful update
                successful += 1
                logger.debug(f"Row {idx + 1}: Updated successfully (ID: {record_id})")

            except Exception as e:
                failed += 1
                errors.append({
                    'row': idx + 1,
                    'record': record,
                    'error': str(e)
                })
                logger.error(f"Row {idx + 1}: Exception during update - {e}")

            # Report progress
            if progress_callback:
                current = idx + 1
                progress_callback(current, successful, failed, total_records)

        return LoadResult(
            total_rows=len(records),
            successful_rows=successful,
            failed_rows=failed,
            errors=errors
        )
