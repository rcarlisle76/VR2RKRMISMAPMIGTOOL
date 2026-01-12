"""
Data models for field mapping and source file handling.

Represents source data files, columns, and field mappings for migration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid


@dataclass
class SourceColumn:
    """
    Represents a column from a CSV or Excel file.
    """
    name: str
    index: int
    sample_values: List[Any] = field(default_factory=list)
    inferred_type: str = 'string'  # 'string', 'number', 'date', 'boolean'
    null_count: int = 0

    def get_type_label(self) -> str:
        """Get human-readable type label."""
        type_labels = {
            'string': 'Text',
            'number': 'Number',
            'date': 'Date',
            'boolean': 'Boolean'
        }
        return type_labels.get(self.inferred_type, 'Unknown')


@dataclass
class SourceFile:
    """
    Metadata about an imported CSV or Excel file.
    """
    file_path: str
    file_type: str  # 'csv' or 'excel'
    total_rows: int
    columns: List[SourceColumn] = field(default_factory=list)
    encoding: str = 'utf-8'
    sheet_name: Optional[str] = None  # For Excel files

    def get_column_by_name(self, name: str) -> Optional[SourceColumn]:
        """
        Get a column by name.

        Args:
            name: Column name

        Returns:
            SourceColumn if found, None otherwise
        """
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def get_column_names(self) -> List[str]:
        """Get list of all column names."""
        return [col.name for col in self.columns]


@dataclass
class FieldMapping:
    """
    Represents a mapping from source column to Salesforce field.
    """
    source_column: str
    target_field: str  # Salesforce API name
    mapping_type: str = 'direct'  # 'direct', 'transform', 'lookup', 'constant'
    transform_expr: Optional[str] = None
    is_required: bool = False
    confidence: Optional[float] = None  # Confidence score (0.0-1.0) from AI mapping
    method: Optional[str] = None  # Mapping method: 'fuzzy', 'semantic', 'llm', 'manual'

    def __str__(self) -> str:
        """String representation of mapping."""
        return f"{self.source_column} → {self.target_field}"


@dataclass
class MappingConfiguration:
    """
    Complete reusable field mapping configuration.
    """
    id: str
    name: str
    description: str
    salesforce_object: str
    source_file_signature: Dict[str, Any]
    mappings: List[FieldMapping] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)
    version: str = "1.0"

    @staticmethod
    def create_new(name: str, salesforce_object: str, description: str = "") -> 'MappingConfiguration':
        """
        Create a new mapping configuration.

        Args:
            name: Configuration name
            salesforce_object: Target Salesforce object API name
            description: Optional description

        Returns:
            New MappingConfiguration instance
        """
        return MappingConfiguration(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            salesforce_object=salesforce_object,
            source_file_signature={},
            mappings=[],
            created_date=datetime.now(),
            modified_date=datetime.now()
        )

    def add_mapping(self, mapping: FieldMapping):
        """
        Add a field mapping.

        Args:
            mapping: FieldMapping to add
        """
        # Remove existing mapping for same target field
        self.mappings = [m for m in self.mappings if m.target_field != mapping.target_field]
        self.mappings.append(mapping)
        self.modified_date = datetime.now()

    def remove_mapping(self, target_field: str):
        """
        Remove a field mapping.

        Args:
            target_field: Salesforce field API name
        """
        self.mappings = [m for m in self.mappings if m.target_field != target_field]
        self.modified_date = datetime.now()

    def get_mapping_for_field(self, target_field: str) -> Optional[FieldMapping]:
        """
        Get mapping for a specific Salesforce field.

        Args:
            target_field: Salesforce field API name

        Returns:
            FieldMapping if exists, None otherwise
        """
        for mapping in self.mappings:
            if mapping.target_field == target_field:
                return mapping
        return None

    def get_mapped_source_columns(self) -> List[str]:
        """Get list of source columns that are mapped."""
        return [m.source_column for m in self.mappings]

    def get_mapped_target_fields(self) -> List[str]:
        """Get list of target fields that have mappings."""
        return [m.target_field for m in self.mappings]
