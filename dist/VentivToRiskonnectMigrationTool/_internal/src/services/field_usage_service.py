"""
Field usage service - parses HTML and CSV field usage reports.

Handles parsing of reports containing field statistics for source data tables.
"""

import csv
import logging
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional, List, Dict

from bs4 import BeautifulSoup

from ..models.field_usage_models import (
    FieldUsageReport,
    FieldUsageStats,
    TableUsageReport,
)
from ..models.mapping_models import SourceFile

logger = logging.getLogger(__name__)


class FieldUsageService:
    """Service for parsing and managing field usage reports."""

    def __init__(self):
        """Initialize the field usage service."""
        self.current_report: Optional[FieldUsageReport] = None

    def import_report(self, file_path: str) -> FieldUsageReport:
        """
        Parse field usage report file (HTML or CSV).

        Args:
            file_path: Path to the report file (HTML or CSV)

        Returns:
            FieldUsageReport containing all parsed tables

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file cannot be parsed
        """
        logger.info(f"Importing field usage report from: {file_path}")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Report file not found: {file_path}")

        # Detect file type and parse accordingly
        suffix = path.suffix.lower()
        if suffix == '.csv':
            report = self._import_csv_report(file_path)
        elif suffix in ('.html', '.htm'):
            report = self._import_html_report(file_path)
        else:
            # Try to detect by content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                if first_line.strip().startswith('<') or 'DOCTYPE' in first_line.upper():
                    report = self._import_html_report(file_path)
                else:
                    report = self._import_csv_report(file_path)
            except Exception:
                raise ValueError(f"Could not determine file type for: {file_path}")

        # Store as current report
        self.current_report = report

        logger.info(f"Successfully imported report with {report.table_count} tables")
        return report

    def _import_html_report(self, file_path: str) -> FieldUsageReport:
        """
        Parse HTML field usage report file.

        Args:
            file_path: Path to the HTML report file

        Returns:
            FieldUsageReport containing all parsed tables
        """
        # Read and parse HTML
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with latin-1 encoding as fallback
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()

        soup = BeautifulSoup(content, 'html.parser')

        # Find all table sections
        tables = []
        for div in soup.find_all('div', class_='field-table'):
            table_report = self._parse_table_section(div)
            if table_report:
                tables.append(table_report)
                logger.debug(f"Parsed table: {table_report.display_name} ({table_report.field_count} fields)")

        if not tables:
            raise ValueError("No field-table sections found in the HTML report")

        return FieldUsageReport(
            file_path=file_path,
            tables=tables,
            parsed_at=datetime.now()
        )

    def _import_csv_report(self, file_path: str) -> FieldUsageReport:
        """
        Parse CSV field usage report file.

        Expected CSV format (columns can be in any order):
        - Table Name (or Table, Source Table) - required
        - Column Name (or Field Name, Column, Field) - required
        - Data Type (or Type) - optional
        - Max Size (or Size, Length) - optional
        - Count (or Record Count, Non-Null Count) - optional
        - Distinct (or Unique, Distinct Count) - optional
        - Nulls (or Null Count, Nulls Count) - optional
        - Min (or Min Value, Minimum) - optional
        - Max (or Max Value, Maximum) - optional
        - Sum - optional
        - Avg (or Average) - optional

        Args:
            file_path: Path to the CSV report file

        Returns:
            FieldUsageReport containing all parsed tables
        """
        # Try different encodings
        content = None
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise ValueError(f"Could not read CSV file with any supported encoding")

        # Parse CSV
        reader = csv.DictReader(content.splitlines())

        # Normalize column names for flexible matching
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("CSV file has no headers")

        col_map = self._map_csv_columns(fieldnames)

        if 'column_name' not in col_map:
            raise ValueError("CSV must have a 'Column Name' or 'Field Name' column")

        # Group rows by table name
        tables_dict: Dict[str, List[FieldUsageStats]] = {}

        for row in reader:
            # Get table name (use filename if not present)
            table_name = None
            if 'table_name' in col_map:
                table_name = row.get(col_map['table_name'], '').strip()

            if not table_name:
                table_name = Path(file_path).stem  # Use filename as table name

            # Parse field stats
            field_stats = self._parse_csv_row(row, col_map)
            if field_stats:
                if table_name not in tables_dict:
                    tables_dict[table_name] = []
                tables_dict[table_name].append(field_stats)

        if not tables_dict:
            raise ValueError("No valid field data found in CSV")

        # Convert to TableUsageReport objects
        tables = []
        for table_name, fields in tables_dict.items():
            # Create display name from table name
            display_name = table_name.replace('_', ' ').replace('-', ' ')
            tables.append(TableUsageReport(
                table_name=table_name,
                display_name=display_name,
                fields=fields
            ))

        logger.info(f"Parsed {len(tables)} tables from CSV")
        return FieldUsageReport(
            file_path=file_path,
            tables=tables,
            parsed_at=datetime.now()
        )

    def _map_csv_columns(self, fieldnames: List[str]) -> Dict[str, str]:
        """
        Map CSV column names to standardized field names.

        Args:
            fieldnames: List of CSV column headers

        Returns:
            Dictionary mapping standard names to actual CSV column names
        """
        col_map = {}

        # Define mappings (standard_name -> possible CSV names)
        mappings = {
            'table_name': ['table name', 'table', 'source table', 'source', 'object', 'entity'],
            'column_name': ['column name', 'field name', 'column', 'field', 'attribute', 'name'],
            'data_type': ['data type', 'type', 'datatype', 'field type'],
            'max_size': ['max size', 'size', 'length', 'max length', 'maxsize'],
            'count': ['count', 'record count', 'non-null count', 'non null count', 'filled', 'populated'],
            'distinct': ['distinct', 'unique', 'distinct count', 'unique count', 'cardinality'],
            'nulls': ['nulls', 'null count', 'nulls count', 'null', 'empty', 'blank'],
            'min_value': ['min', 'min value', 'minimum', 'min_value'],
            'max_value': ['max', 'max value', 'maximum', 'max_value'],
            'sum_value': ['sum', 'total', 'sum_value'],
            'avg_value': ['avg', 'average', 'mean', 'avg_value'],
        }

        # Normalize fieldnames for matching
        fieldnames_lower = {fn.lower().strip(): fn for fn in fieldnames}

        for standard_name, possible_names in mappings.items():
            for possible in possible_names:
                if possible in fieldnames_lower:
                    col_map[standard_name] = fieldnames_lower[possible]
                    break

        return col_map

    def _parse_csv_row(self, row: Dict[str, str], col_map: Dict[str, str]) -> Optional[FieldUsageStats]:
        """
        Parse a single CSV row into FieldUsageStats.

        Args:
            row: CSV row dictionary
            col_map: Column name mapping

        Returns:
            FieldUsageStats or None if parsing fails
        """
        try:
            column_name = row.get(col_map.get('column_name', ''), '').strip()
            if not column_name:
                return None

            return FieldUsageStats(
                column_name=column_name,
                data_type=row.get(col_map.get('data_type', ''), '').strip() or 'unknown',
                max_size=self._parse_int(row.get(col_map.get('max_size', ''), '')),
                count=self._parse_int(row.get(col_map.get('count', ''), '')) or 0,
                distinct=self._parse_int(row.get(col_map.get('distinct', ''), '')) or 0,
                nulls=self._parse_int(row.get(col_map.get('nulls', ''), '')) or 0,
                min_value=row.get(col_map.get('min_value', ''), '').strip() or None,
                max_value=row.get(col_map.get('max_value', ''), '').strip() or None,
                sum_value=self._parse_float(row.get(col_map.get('sum_value', ''), '')),
                avg_value=self._parse_float(row.get(col_map.get('avg_value', ''), '')),
            )
        except Exception as e:
            logger.warning(f"Failed to parse CSV row: {e}")
            return None

    def _parse_table_section(self, div_element) -> Optional[TableUsageReport]:
        """
        Parse a single table section from the HTML.

        Args:
            div_element: BeautifulSoup div element with class='field-table'

        Returns:
            TableUsageReport or None if parsing fails
        """
        # Get table ID from div
        table_id = div_element.get('id', 'Unknown')

        # Get display name from h2
        h2 = div_element.find('h2')
        display_name = h2.get_text(strip=True) if h2 else table_id

        # Find the table element
        table_element = div_element.find('table')
        if not table_element:
            logger.warning(f"No table found in section: {table_id}")
            return None

        # Parse table rows
        fields = []
        tbody = table_element.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            # Fall back to finding all tr elements (skip header row)
            rows = table_element.find_all('tr')[1:]

        for row in rows:
            field_stats = self._parse_table_row(row)
            if field_stats:
                fields.append(field_stats)

        return TableUsageReport(
            table_name=table_id,
            display_name=display_name,
            fields=fields
        )

    def _parse_table_row(self, row_element) -> Optional[FieldUsageStats]:
        """
        Parse a single table row into FieldUsageStats.

        Expected columns: Column Name, Data Type, Max Size, Count, Distinct, Nulls, Min, Max, Sum, Avg

        Args:
            row_element: BeautifulSoup tr element

        Returns:
            FieldUsageStats or None if parsing fails
        """
        cells = row_element.find_all('td')
        if len(cells) < 6:
            return None

        try:
            column_name = cells[0].get_text(strip=True)
            data_type = cells[1].get_text(strip=True)
            max_size = self._parse_int(cells[2].get_text(strip=True))
            count = self._parse_int(cells[3].get_text(strip=True)) or 0
            distinct = self._parse_int(cells[4].get_text(strip=True)) or 0
            nulls = self._parse_int(cells[5].get_text(strip=True)) or 0

            # Optional columns (may not exist)
            min_value = cells[6].get_text(strip=True) if len(cells) > 6 else None
            max_value = cells[7].get_text(strip=True) if len(cells) > 7 else None
            sum_value = self._parse_float(cells[8].get_text(strip=True)) if len(cells) > 8 else None
            avg_value = self._parse_float(cells[9].get_text(strip=True)) if len(cells) > 9 else None

            # Clean up empty strings
            min_value = min_value if min_value else None
            max_value = max_value if max_value else None

            return FieldUsageStats(
                column_name=column_name,
                data_type=data_type,
                max_size=max_size,
                count=count,
                distinct=distinct,
                nulls=nulls,
                min_value=min_value,
                max_value=max_value,
                sum_value=sum_value,
                avg_value=avg_value
            )
        except Exception as e:
            logger.warning(f"Failed to parse row: {e}")
            return None

    def _parse_int(self, text: str) -> Optional[int]:
        """Parse integer from text, handling commas and empty strings."""
        if not text or text.strip() == '':
            return None
        try:
            # Remove commas and parse
            cleaned = text.replace(',', '').strip()
            return int(cleaned)
        except ValueError:
            return None

    def _parse_float(self, text: str) -> Optional[float]:
        """Parse float from text, handling commas and currency symbols."""
        if not text or text.strip() == '':
            return None
        try:
            # Remove commas, currency symbols, and parse
            cleaned = re.sub(r'[$,]', '', text.strip())
            return float(cleaned)
        except ValueError:
            return None

    def get_usage_for_source_file(self, source_file: SourceFile) -> Optional[TableUsageReport]:
        """
        Match a source file to a table in the usage report.

        Matching strategies (in order):
        1. Exact match on filename (without extension)
        2. Fuzzy match on table name/display name
        3. Match based on column name overlap

        Args:
            source_file: SourceFile to match

        Returns:
            TableUsageReport if match found, None otherwise
        """
        if not self.current_report:
            return None

        # Get filename without extension
        filename = Path(source_file.file_path).stem
        filename_lower = filename.lower()

        # Strategy 1: Exact match on filename
        for table in self.current_report.tables:
            if table.table_name.lower() == filename_lower:
                logger.info(f"Matched '{filename}' to table '{table.display_name}' by table_name")
                return table
            if table.display_name.lower() == filename_lower:
                logger.info(f"Matched '{filename}' to table '{table.display_name}' by display_name")
                return table

        # Strategy 2: Fuzzy match on table name
        best_match = None
        best_ratio = 0.0

        for table in self.current_report.tables:
            # Compare with table_name (underscores to spaces)
            table_name_normalized = table.table_name.replace('_', ' ').lower()
            ratio1 = SequenceMatcher(None, filename_lower, table_name_normalized).ratio()

            # Compare with display_name
            ratio2 = SequenceMatcher(None, filename_lower, table.display_name.lower()).ratio()

            ratio = max(ratio1, ratio2)
            if ratio > best_ratio and ratio >= 0.7:
                best_ratio = ratio
                best_match = table

        if best_match:
            logger.info(f"Fuzzy matched '{filename}' to table '{best_match.display_name}' (ratio: {best_ratio:.2f})")
            return best_match

        # Strategy 3: Match by column overlap
        source_columns = set(col.name.lower() for col in source_file.columns)

        best_match = None
        best_overlap = 0

        for table in self.current_report.tables:
            table_columns = set(f.column_name.lower() for f in table.fields)
            overlap = len(source_columns & table_columns)

            # Require at least 70% column overlap
            if overlap > best_overlap and overlap >= len(source_columns) * 0.7:
                best_overlap = overlap
                best_match = table

        if best_match:
            logger.info(f"Matched '{filename}' to table '{best_match.display_name}' by column overlap ({best_overlap} columns)")
            return best_match

        logger.info(f"No matching table found for '{filename}'")
        return None

    def get_usage_for_column(self, table_name: str, column_name: str) -> Optional[FieldUsageStats]:
        """
        Get usage stats for a specific column.

        Args:
            table_name: Table name or display name
            column_name: Column name to find

        Returns:
            FieldUsageStats if found, None otherwise
        """
        if not self.current_report:
            return None

        table = self.current_report.get_table_by_name(table_name)
        if not table:
            return None

        return table.get_field_by_name(column_name)

    def clear(self):
        """Clear the current report."""
        self.current_report = None
