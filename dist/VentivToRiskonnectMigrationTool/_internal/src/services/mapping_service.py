"""
Mapping service - manages field mappings and configurations.

Handles creation, validation, and persistence of field mappings.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from difflib import SequenceMatcher

from ..core.logging_config import get_logger
from ..models.mapping_models import (
    SourceFile, FieldMapping, MappingConfiguration
)
from ..models.salesforce_metadata import SalesforceObject, SalesforceField

logger = get_logger(__name__)


class MappingService:
    """
    Service for managing field mappings.
    """

    def __init__(self):
        """Initialize the mapping service."""
        pass

    def create_mapping(
        self,
        name: str,
        salesforce_object: SalesforceObject,
        source_file: SourceFile,
        description: str = ""
    ) -> MappingConfiguration:
        """
        Create a new mapping configuration.

        Args:
            name: Configuration name
            salesforce_object: Target Salesforce object
            source_file: Source file metadata
            description: Optional description

        Returns:
            New MappingConfiguration
        """
        logger.info(f"Creating mapping: {name} for {salesforce_object.name}")

        # Create source file signature
        signature = {
            "expected_columns": source_file.get_column_names(),
            "validation_mode": "warn_on_mismatch"
        }

        config = MappingConfiguration.create_new(
            name=name,
            salesforce_object=salesforce_object.name,
            description=description
        )
        config.source_file_signature = signature

        return config

    def auto_suggest_mappings(
        self,
        source_file: SourceFile,
        salesforce_object: SalesforceObject,
        threshold: float = 0.6
    ) -> List[FieldMapping]:
        """
        Automatically suggest field mappings based on name similarity.

        Args:
            source_file: Source file with columns
            salesforce_object: Target Salesforce object
            threshold: Minimum similarity score (0.0-1.0) to suggest mapping

        Returns:
            List of suggested FieldMapping objects
        """
        logger.info(f"Auto-suggesting mappings for {len(source_file.columns)} source columns")

        suggestions = []

        for source_col in source_file.columns:
            best_match = None
            best_score = threshold

            # Compare with each Salesforce field
            for sf_field in salesforce_object.fields:
                # Calculate similarity scores
                name_score = self._calculate_similarity(
                    source_col.name,
                    sf_field.name
                )
                label_score = self._calculate_similarity(
                    source_col.name,
                    sf_field.label
                )

                # Use the better score
                score = max(name_score, label_score)

                if score > best_score:
                    best_score = score
                    best_match = sf_field

            # If we found a good match, create mapping
            if best_match:
                mapping = FieldMapping(
                    source_column=source_col.name,
                    target_field=best_match.name,
                    mapping_type='direct',
                    is_required=best_match.required
                )
                suggestions.append(mapping)
                logger.debug(
                    f"Suggested mapping: {source_col.name} → {best_match.name} "
                    f"(score: {best_score:.2f})"
                )

        logger.info(f"Generated {len(suggestions)} mapping suggestions")
        return suggestions

    def save_mapping(self, config: MappingConfiguration, file_path: str):
        """
        Save mapping configuration to JSON file.

        Args:
            config: MappingConfiguration to save
            file_path: Path to save to
        """
        logger.info(f"Saving mapping to: {file_path}")

        # Convert to dictionary
        data = {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "salesforce_object": config.salesforce_object,
            "version": config.version,
            "created_date": config.created_date.isoformat(),
            "modified_date": config.modified_date.isoformat(),
            "source_file_signature": config.source_file_signature,
            "mappings": [
                {
                    "source_column": m.source_column,
                    "target_field": m.target_field,
                    "mapping_type": m.mapping_type,
                    "transform_expr": m.transform_expr,
                    "is_required": m.is_required
                }
                for m in config.mappings
            ]
        }

        # Write to file
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved mapping with {len(config.mappings)} field mappings")

    def load_mapping(self, file_path: str) -> MappingConfiguration:
        """
        Load mapping configuration from JSON file.

        Args:
            file_path: Path to load from

        Returns:
            MappingConfiguration
        """
        logger.info(f"Loading mapping from: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Create mappings
        mappings = [
            FieldMapping(
                source_column=m["source_column"],
                target_field=m["target_field"],
                mapping_type=m.get("mapping_type", "direct"),
                transform_expr=m.get("transform_expr"),
                is_required=m.get("is_required", False)
            )
            for m in data.get("mappings", [])
        ]

        # Create configuration
        config = MappingConfiguration(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            salesforce_object=data["salesforce_object"],
            source_file_signature=data.get("source_file_signature", {}),
            mappings=mappings,
            created_date=datetime.fromisoformat(data["created_date"]),
            modified_date=datetime.fromisoformat(data["modified_date"]),
            version=data.get("version", "1.0")
        )

        logger.info(f"Loaded mapping with {len(config.mappings)} field mappings")
        return config

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings.

        Uses fuzzy string matching to handle variations like:
        - first_name vs FirstName
        - account_id vs AccountId
        - email vs Email__c

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Normalize strings
        s1 = str1.lower().replace('_', '').replace(' ', '')
        s2 = str2.lower().replace('_', '').replace(' ', '')

        # Remove common suffixes
        for suffix in ['__c', 'id', 'name']:
            if s1.endswith(suffix):
                s1 = s1[:-len(suffix)]
            if s2.endswith(suffix):
                s2 = s2[:-len(suffix)]

        # Calculate similarity
        return SequenceMatcher(None, s1, s2).ratio()
