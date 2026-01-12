"""
File import service - handles CSV and Excel file parsing and analysis.

Parses source files, infers data types, and provides preview functionality.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from ..core.logging_config import get_logger
from ..models.mapping_models import SourceFile, SourceColumn

logger = get_logger(__name__)


class FileImportService:
    """
    Service for importing and analyzing CSV and Excel files.
    """

    def __init__(self):
        """Initialize the file import service."""
        pass

    def import_file(self, file_path: str, sample_size: int = 100) -> SourceFile:
        """
        Import and analyze a CSV or Excel file.

        Args:
            file_path: Path to the file
            sample_size: Number of rows to sample for type inference

        Returns:
            SourceFile with metadata and column information
        """
        logger.info(f"Importing file: {file_path}")

        file_type = self._detect_file_type(file_path)

        if file_type == 'csv':
            return self._import_csv(file_path, sample_size)
        elif file_type == 'excel':
            return self._import_excel(file_path, sample_size)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def get_preview_data(self, file_path: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get preview data from file without full analysis.

        Args:
            file_path: Path to the file
            limit: Maximum number of rows to return

        Returns:
            List of dictionaries representing rows
        """
        logger.debug(f"Getting preview data from: {file_path}")

        file_type = self._detect_file_type(file_path)

        if file_type == 'csv':
            return self._preview_csv(file_path, limit)
        elif file_type == 'excel':
            return self._preview_excel(file_path, limit)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _detect_file_type(self, file_path: str) -> str:
        """
        Detect file type from extension.

        Args:
            file_path: Path to the file

        Returns:
            'csv' or 'excel'
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == '.csv':
            return 'csv'
        elif extension in ['.xlsx', '.xls']:
            return 'excel'
        else:
            raise ValueError(f"Unsupported file extension: {extension}")

    def _import_csv(self, file_path: str, sample_size: int) -> SourceFile:
        """
        Import CSV file.

        Args:
            file_path: Path to CSV file
            sample_size: Number of rows to sample

        Returns:
            SourceFile with metadata
        """
        logger.debug(f"Importing CSV: {file_path}")

        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        content = None
        used_encoding = 'utf-8'

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, newline='') as f:
                    content = f.read()
                    used_encoding = encoding
                    break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise ValueError("Unable to decode file with supported encodings")

        # Parse CSV
        lines = content.splitlines()
        reader = csv.DictReader(lines)

        # Get column names
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("CSV file has no headers")

        # Read sample rows
        sample_rows = []
        total_rows = 0

        for row in reader:
            total_rows += 1
            if len(sample_rows) < sample_size:
                sample_rows.append(row)

        logger.info(f"CSV has {len(fieldnames)} columns and {total_rows} data rows")

        # Create SourceColumn objects
        columns = []
        for idx, col_name in enumerate(fieldnames):
            # Get sample values for this column
            sample_values = [row.get(col_name, '') for row in sample_rows]

            # Infer type
            inferred_type = self._infer_type(sample_values)

            # Count nulls
            null_count = sum(1 for v in sample_values if v == '' or v is None)

            column = SourceColumn(
                name=col_name,
                index=idx,
                sample_values=sample_values[:10],  # Keep only first 10 for display
                inferred_type=inferred_type,
                null_count=null_count
            )
            columns.append(column)

        return SourceFile(
            file_path=file_path,
            file_type='csv',
            total_rows=total_rows,
            columns=columns,
            encoding=used_encoding
        )

    def _import_excel(self, file_path: str, sample_size: int) -> SourceFile:
        """
        Import Excel file.

        Args:
            file_path: Path to Excel file
            sample_size: Number of rows to sample

        Returns:
            SourceFile with metadata
        """
        # For Phase 3B - Excel support
        # For now, raise not implemented
        raise NotImplementedError("Excel import will be added in Phase 3B")

    def _preview_csv(self, file_path: str, limit: int) -> List[Dict[str, Any]]:
        """
        Get preview rows from CSV.

        Args:
            file_path: Path to CSV file
            limit: Maximum number of rows

        Returns:
            List of row dictionaries
        """
        rows = []

        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    rows.append(row)
        except Exception as e:
            logger.error(f"Error previewing CSV: {e}")
            raise

        return rows

    def _preview_excel(self, file_path: str, limit: int) -> List[Dict[str, Any]]:
        """
        Get preview rows from Excel.

        Args:
            file_path: Path to Excel file
            limit: Maximum number of rows

        Returns:
            List of row dictionaries
        """
        # For Phase 3B
        raise NotImplementedError("Excel preview will be added in Phase 3B")

    def _infer_type(self, values: List[Any]) -> str:
        """
        Infer data type from sample values.

        Priority: date > number > boolean > string

        Args:
            values: List of sample values

        Returns:
            Inferred type: 'date', 'number', 'boolean', or 'string'
        """
        # Filter out empty values
        non_empty = [v for v in values if v and str(v).strip()]

        if not non_empty:
            return 'string'

        # Check for date (YYYY-MM-DD, MM/DD/YYYY, etc.)
        date_count = sum(1 for v in non_empty if self._is_date(str(v)))
        if date_count / len(non_empty) > 0.8:  # 80% threshold
            return 'date'

        # Check for number
        number_count = sum(1 for v in non_empty if self._is_number(str(v)))
        if number_count / len(non_empty) > 0.8:
            return 'number'

        # Check for boolean
        boolean_count = sum(1 for v in non_empty if self._is_boolean(str(v)))
        if boolean_count / len(non_empty) > 0.8:
            return 'boolean'

        # Default to string
        return 'string'

    def _is_date(self, value: str) -> bool:
        """
        Check if value looks like a date.

        Args:
            value: String value

        Returns:
            True if appears to be a date
        """
        # Common date patterns
        patterns = [
            r'^\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'^\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
        ]

        for pattern in patterns:
            if re.match(pattern, value.strip()):
                return True

        return False

    def _is_number(self, value: str) -> bool:
        """
        Check if value is a number.

        Args:
            value: String value

        Returns:
            True if can be parsed as number
        """
        try:
            # Remove common number formatting
            cleaned = value.replace(',', '').replace('$', '').strip()
            float(cleaned)
            return True
        except ValueError:
            return False

    def _is_boolean(self, value: str) -> bool:
        """
        Check if value is a boolean.

        Args:
            value: String value

        Returns:
            True if appears to be boolean
        """
        lower_val = value.lower().strip()
        return lower_val in ['true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n']
