"""
Field usage report models - data structures for parsed HTML usage reports.

These models hold statistics about source data fields including counts,
distinct values, nulls, and min/max values.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class FieldUsageStats:
    """Statistics for a single field/column from the usage report."""

    column_name: str
    data_type: str
    max_size: Optional[int] = None
    count: int = 0              # Non-null record count
    distinct: int = 0           # Unique value count
    nulls: int = 0              # Null count
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    sum_value: Optional[float] = None
    avg_value: Optional[float] = None

    @property
    def total_records(self) -> int:
        """Total records (count + nulls)."""
        return self.count + self.nulls

    @property
    def null_percentage(self) -> float:
        """Calculate null percentage."""
        total = self.total_records
        return (self.nulls / total * 100) if total > 0 else 0.0

    @property
    def fill_rate(self) -> float:
        """Calculate fill rate (percentage of non-null values)."""
        return 100.0 - self.null_percentage


@dataclass
class TableUsageReport:
    """Usage report for a single source table."""

    table_name: str             # ID from HTML (e.g., "Business_Income_R")
    display_name: str           # Human-readable name (e.g., "Business Income")
    fields: List[FieldUsageStats] = field(default_factory=list)

    def get_field_by_name(self, name: str) -> Optional[FieldUsageStats]:
        """
        Get field stats by column name (case-insensitive).

        Args:
            name: Column name to find

        Returns:
            FieldUsageStats if found, None otherwise
        """
        name_lower = name.lower()
        for f in self.fields:
            if f.column_name.lower() == name_lower:
                return f
        return None

    def get_field_names(self) -> List[str]:
        """Get list of all field names in this table."""
        return [f.column_name for f in self.fields]

    @property
    def field_count(self) -> int:
        """Number of fields in this table."""
        return len(self.fields)


@dataclass
class FieldUsageReport:
    """Complete field usage report containing multiple tables."""

    file_path: str
    tables: List[TableUsageReport] = field(default_factory=list)
    parsed_at: datetime = field(default_factory=datetime.now)

    def get_table_by_name(self, name: str) -> Optional[TableUsageReport]:
        """
        Get table by name (case-insensitive, matches table_name or display_name).

        Args:
            name: Table name or display name to find

        Returns:
            TableUsageReport if found, None otherwise
        """
        name_lower = name.lower()
        for table in self.tables:
            if table.table_name.lower() == name_lower:
                return table
            if table.display_name.lower() == name_lower:
                return table
        return None

    def get_table_names(self) -> List[str]:
        """Get list of all table display names in the report."""
        return [t.display_name for t in self.tables]

    def get_table_ids(self) -> List[str]:
        """Get list of all table IDs in the report."""
        return [t.table_name for t in self.tables]

    @property
    def table_count(self) -> int:
        """Number of tables in this report."""
        return len(self.tables)
