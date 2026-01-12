"""
Main window presenter (Presenter in MVP pattern).

Orchestrates main window business logic.
"""

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from typing import Optional

from ...core.logging_config import get_logger
from ...core.config import ConfigManager
from ...services.metadata_service import MetadataService
from ...services.data_preview_service import DataPreviewService
from ...services.file_import_service import FileImportService
from ...services.mapping_service import MappingService
from ...services.ai_mapping_service import AIEnhancedMappingService
from ...services.data_loader_service import DataLoaderService, LoadResult
from ...services.template_service import TemplateService
from ...services.auth_service import AuthService
from ...models.salesforce_metadata import ObjectListItem, SalesforceObject
from ...models.mapping_models import SourceFile, FieldMapping


logger = get_logger(__name__)


class MetadataLoadWorker(QThread):
    """Worker thread for loading metadata in background."""

    finished = pyqtSignal(list)  # List[ObjectListItem]
    error = pyqtSignal(str)

    def __init__(self, metadata_service: MetadataService):
        """
        Initialize worker.

        Args:
            metadata_service: MetadataService instance
        """
        super().__init__()
        self.metadata_service = metadata_service

    def run(self):
        """Load objects in background thread."""
        try:
            logger.debug("Loading objects in background thread")
            objects = self.metadata_service.get_all_objects()
            self.finished.emit(objects)

        except Exception as e:
            logger.error(f"Error loading objects: {e}")
            self.error.emit(str(e))


class ObjectDescribeWorker(QThread):
    """Worker thread for loading object describe metadata in background."""

    finished = pyqtSignal(object)  # SalesforceObject
    error = pyqtSignal(str)

    def __init__(self, metadata_service: MetadataService, object_name: str):
        """
        Initialize worker.

        Args:
            metadata_service: MetadataService instance
            object_name: API name of object to describe
        """
        super().__init__()
        self.metadata_service = metadata_service
        self.object_name = object_name

    def run(self):
        """Load object describe in background thread."""
        try:
            logger.debug(f"Loading describe for object: {self.object_name}")
            obj = self.metadata_service.get_object_metadata(self.object_name)
            self.finished.emit(obj)

        except Exception as e:
            logger.error(f"Error loading object describe: {e}")
            self.error.emit(str(e))


class PageLayoutWorker(QThread):
    """Worker thread for fetching page layout fields in background."""

    finished = pyqtSignal(list)  # List of field API names
    error = pyqtSignal(str)

    def __init__(self, sf_client, object_name: str, record_type_id: str = None):
        """
        Initialize worker.

        Args:
            sf_client: SalesforceClient instance
            object_name: Object API name
            record_type_id: Optional record type ID
        """
        super().__init__()
        self.sf_client = sf_client
        self.object_name = object_name
        self.record_type_id = record_type_id

    def run(self):
        """Fetch page layout fields in background thread."""
        try:
            logger.debug(f"Fetching page layout fields for: {self.object_name} (record type: {self.record_type_id})")
            layout_fields = self.sf_client.get_page_layout_fields(
                self.object_name,
                self.record_type_id
            )
            self.finished.emit(layout_fields)

        except Exception as e:
            logger.error(f"Error fetching page layout: {e}")
            self.error.emit(str(e))


class PageLayoutAssignmentsWorker(QThread):
    """Worker thread for fetching page layout assignments in background."""

    finished = pyqtSignal(dict)  # Dict[str, str] mapping record_type_id -> layout_name
    error = pyqtSignal(str)

    def __init__(self, sf_client, object_name: str, salesforce_object: SalesforceObject):
        """
        Initialize worker.

        Args:
            sf_client: SalesforceClient instance
            object_name: Object API name
            salesforce_object: SalesforceObject with record types
        """
        super().__init__()
        self.sf_client = sf_client
        self.object_name = object_name
        self.salesforce_object = salesforce_object

    def run(self):
        """Fetch page layout assignments in background thread."""
        try:
            logger.debug(f"Fetching page layout assignments for: {self.object_name}")

            # Pass full record types list to enable name-to-ID matching
            layout_assignments = self.sf_client.get_page_layout_assignments(
                self.object_name,
                self.salesforce_object.record_types
            )
            self.finished.emit(layout_assignments)

        except Exception as e:
            logger.error(f"Error fetching page layout assignments: {e}")
            self.error.emit(str(e))


class DataPreviewWorker(QThread):
    """Worker thread for loading sample data in background."""

    finished = pyqtSignal(dict)  # Dictionary with records, fields, total_size
    error = pyqtSignal(str)

    def __init__(
        self,
        data_preview_service: DataPreviewService,
        salesforce_object: SalesforceObject,
        record_type_id: str = None,
        layout_fields: list = None
    ):
        """
        Initialize worker.

        Args:
            data_preview_service: DataPreviewService instance
            salesforce_object: SalesforceObject to preview
            record_type_id: Optional record type ID to filter by
            layout_fields: Optional list of fields from page layout
        """
        super().__init__()
        self.data_preview_service = data_preview_service
        self.salesforce_object = salesforce_object
        self.record_type_id = record_type_id
        self.layout_fields = layout_fields

    def run(self):
        """Load sample data in background thread."""
        try:
            logger.debug(f"Loading sample data for: {self.salesforce_object.name}")
            data = self.data_preview_service.get_sample_data_for_object(
                self.salesforce_object,
                limit=20,
                include_all_required=(not self.layout_fields),  # Use all required if no layout
                record_type_id=self.record_type_id,
                layout_fields=self.layout_fields
            )
            self.finished.emit(data)

        except Exception as e:
            logger.error(f"Error loading sample data: {e}")
            self.error.emit(str(e))


class FileImportWorker(QThread):
    """Worker thread for importing CSV/Excel files in background."""

    finished = pyqtSignal(object)  # SourceFile
    error = pyqtSignal(str)

    def __init__(self, file_import_service: FileImportService, file_path: str):
        """
        Initialize worker.

        Args:
            file_import_service: FileImportService instance
            file_path: Path to file to import
        """
        super().__init__()
        self.file_import_service = file_import_service
        self.file_path = file_path

    def run(self):
        """Import file in background thread."""
        try:
            logger.debug(f"Importing file: {self.file_path}")
            source_file = self.file_import_service.import_file(self.file_path, sample_size=100)
            self.finished.emit(source_file)

        except Exception as e:
            logger.error(f"Error importing file: {e}")
            self.error.emit(str(e))


class DataLoadWorker(QThread):
    """Worker thread for loading data to Salesforce in background."""

    progress = pyqtSignal(int, int, int)  # current, successful, failed
    status = pyqtSignal(str)  # Status message for bulk API progress
    finished = pyqtSignal(object)  # LoadResult
    error = pyqtSignal(str)

    def __init__(self, data_loader_service: DataLoaderService, source_file: SourceFile,
                 mappings: list, salesforce_object: SalesforceObject, operation: str = 'insert',
                 record_type_id: str = None):
        """
        Initialize worker.

        Args:
            data_loader_service: DataLoaderService instance
            source_file: SourceFile to load
            mappings: List of FieldMapping objects
            salesforce_object: Target Salesforce object with field metadata
            operation: 'insert' or 'update'
            record_type_id: Optional record type ID for records
        """
        super().__init__()
        self.data_loader_service = data_loader_service
        self.source_file = source_file
        self.mappings = mappings
        self.salesforce_object = salesforce_object
        self.operation = operation
        self.record_type_id = record_type_id

    def _status_callback(self, message: str):
        """Callback for status messages from data loader (Bulk API)."""
        self.status.emit(message)

    def _progress_callback(self, current: int, successful: int, failed: int, total: int):
        """Callback for numeric progress updates from data loader (REST API)."""
        self.progress.emit(current, successful, failed)

    def _unified_progress_callback(self, *args):
        """
        Unified callback that handles both string messages and numeric progress.

        Args can be:
        - (message: str) for Bulk API status updates
        - (current, successful, failed, total) for REST API progress
        """
        if len(args) == 1 and isinstance(args[0], str):
            # String message - Bulk API status
            self._status_callback(args[0])
        elif len(args) == 4:
            # Numeric progress - REST API
            self._progress_callback(args[0], args[1], args[2], args[3])

    def run(self):
        """Load data in background thread."""
        try:
            logger.debug(f"Loading data to {self.salesforce_object.name} ({self.operation})")
            result = self.data_loader_service.load_data(
                self.source_file,
                self.mappings,
                self.salesforce_object,
                self.operation,
                self.record_type_id,
                progress_callback=self._unified_progress_callback
            )
            self.finished.emit(result)

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.error.emit(str(e))


class MainPresenter(QObject):
    """
    Presenter for main window.

    Handles business logic for object browsing and metadata operations.
    """

    # Signals
    logout_requested = pyqtSignal()

    def __init__(self, view, metadata_service: MetadataService, auth_service: AuthService):
        """
        Initialize main presenter.

        Args:
            view: MainWindow instance
            metadata_service: MetadataService instance
            auth_service: AuthService instance
        """
        super().__init__()
        self.view = view
        self.metadata_service = metadata_service
        self.auth_service = auth_service
        self.sf_client = auth_service.get_client()  # Store client reference
        self.data_preview_service = DataPreviewService(self.sf_client)
        self.file_import_service = FileImportService()

        # Initialize AI-enhanced mapping service with config
        self.config_manager = ConfigManager()
        config = self.config_manager.load()

        # Use AI-enhanced mapping service if enabled, otherwise fallback to basic
        if config.use_semantic_matching or config.use_llm_mapping:
            logger.info(
                f"Initializing AI-enhanced mapping service "
                f"(semantic: {config.use_semantic_matching}, llm: {config.use_llm_mapping})"
            )
            self.mapping_service = AIEnhancedMappingService(
                use_semantic=config.use_semantic_matching,
                use_llm=config.use_llm_mapping,
                llm_provider=config.llm_provider,
                llm_model=config.llm_model,
                api_key=config.claude_api_key
            )
        else:
            logger.info("Using standard fuzzy matching service")
            self.mapping_service = MappingService()

        self.data_loader_service = DataLoaderService(auth_service.get_client())
        self.template_service = TemplateService()
        self.worker: Optional[MetadataLoadWorker] = None
        self.describe_worker: Optional[ObjectDescribeWorker] = None
        self.preview_worker: Optional[DataPreviewWorker] = None
        self.import_worker: Optional[FileImportWorker] = None
        self.load_worker: Optional[DataLoadWorker] = None

        # Connect view signals
        self.view.object_selected.connect(self._handle_object_selected)
        self.view.logout_requested.connect(self._handle_logout)
        self.view.object_detail_widget.load_preview_data_requested.connect(self._handle_load_preview_data)
        self.view.object_detail_widget.export_preview_data_requested.connect(self._handle_export_preview_data)
        self.view.object_detail_widget.file_import_requested.connect(self._handle_file_import)
        self.view.object_detail_widget.auto_map_requested.connect(self._handle_auto_map)
        self.view.object_detail_widget.save_mapping_requested.connect(self._handle_save_mapping)
        self.view.object_detail_widget.load_mapping_requested.connect(self._handle_load_mapping)
        self.view.object_detail_widget.load_data_requested.connect(self._handle_load_data)
        self.view.object_detail_widget.template_download_requested.connect(self._handle_template_download)
        self.view.object_detail_widget.load_page_layouts_requested.connect(self._handle_load_page_layouts)
        self.view.object_detail_widget.relationship_table_widget.layout_clicked.connect(self._handle_layout_clicked)
        self.view.object_detail_widget.field_table_widget.download_template_requested.connect(self._handle_filtered_template_download)

        # Load objects on initialization
        self.load_objects()

    def load_objects(self):
        """Load Salesforce objects in background thread."""
        logger.info("Starting to load Salesforce objects")

        # Show loading state
        self.view.object_list_widget.show_loading(True)
        self.view.update_status("Loading Salesforce objects...")

        # Create and start worker thread
        self.worker = MetadataLoadWorker(self.metadata_service)
        self.worker.finished.connect(self._on_objects_loaded)
        self.worker.error.connect(self._on_load_error)
        self.worker.start()

    def _on_objects_loaded(self, objects: list):
        """
        Handle objects loaded successfully.

        Args:
            objects: List of ObjectListItem objects
        """
        logger.info(f"Loaded {len(objects)} objects")

        # Update view
        self.view.object_list_widget.show_loading(False)
        self.view.object_list_widget.set_objects(objects)
        self.view.update_status(f"Loaded {len(objects)} objects")

        # Cleanup worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def _on_load_error(self, error_message: str):
        """
        Handle error loading objects.

        Args:
            error_message: Error message
        """
        logger.error(f"Failed to load objects: {error_message}")

        # Update view
        self.view.object_list_widget.show_loading(False)
        self.view.show_error(
            "Error Loading Objects",
            f"Failed to load Salesforce objects:\n\n{error_message}"
        )
        self.view.update_status("Error loading objects")

        # Cleanup worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def _handle_object_selected(self, object_name: str):
        """
        Handle object selection from list.

        Args:
            object_name: API name of selected object
        """
        logger.info(f"Object selected: {object_name}")

        # Show loading state
        self.view.object_detail_widget.show_loading()
        self.view.update_status(f"Loading metadata for {object_name}...")

        # Create and start worker thread
        self.describe_worker = ObjectDescribeWorker(self.metadata_service, object_name)
        self.describe_worker.finished.connect(self._on_object_describe_loaded)
        self.describe_worker.error.connect(self._on_describe_error)
        self.describe_worker.start()

    def _on_object_describe_loaded(self, salesforce_object: SalesforceObject):
        """
        Handle object describe loaded successfully.

        Args:
            salesforce_object: SalesforceObject with full metadata
        """
        logger.info(f"Loaded metadata for: {salesforce_object.name}")

        # Update view
        self.view.object_detail_widget.set_object(salesforce_object)
        self.view.update_status(
            f"Loaded {salesforce_object.label} ({len(salesforce_object.fields)} fields)"
        )

        # Cleanup worker
        if self.describe_worker:
            self.describe_worker.deleteLater()
            self.describe_worker = None

    def _on_describe_error(self, error_message: str):
        """
        Handle error loading object describe.

        Args:
            error_message: Error message
        """
        logger.error(f"Failed to load object describe: {error_message}")

        # Update view
        self.view.object_detail_widget.clear()
        self.view.show_error(
            "Error Loading Object Metadata",
            f"Failed to load object metadata:\n\n{error_message}"
        )
        self.view.update_status("Error loading object metadata")

        # Cleanup worker
        if self.describe_worker:
            self.describe_worker.deleteLater()
            self.describe_worker = None

    def _handle_load_preview_data(self):
        """Handle request to load preview data for current object."""
        current_object = self.view.object_detail_widget.current_object
        if not current_object:
            logger.warning("No current object to preview")
            return

        # Get selected record type from widget
        record_type_id = self.view.object_detail_widget.data_preview_widget.get_selected_record_type_id()

        logger.info(f"Loading preview data for: {current_object.name} (record type: {record_type_id or 'all'})")

        # Show loading state
        self.view.object_detail_widget.data_preview_widget.show_loading()
        self.view.update_status(f"Loading sample data for {current_object.label}...")

        # If a record type is selected, fetch page layout fields first
        if record_type_id:
            logger.info(f"Fetching page layout fields for record type: {record_type_id}")
            self.view.update_status(f"Fetching page layout...")

            # Create and start page layout worker
            self.layout_worker = PageLayoutWorker(
                self.sf_client,
                current_object.name,
                record_type_id
            )
            self.layout_worker.finished.connect(
                lambda layout_fields: self._on_layout_fields_loaded(
                    layout_fields, current_object, record_type_id
                )
            )
            self.layout_worker.error.connect(
                lambda error: self._on_layout_error(error, current_object, record_type_id)
            )
            self.layout_worker.start()
        else:
            # No record type selected, load with default field selection
            self._load_preview_data(current_object, record_type_id, layout_fields=None)

    def _on_layout_fields_loaded(self, layout_fields: list, salesforce_object, record_type_id):
        """
        Handle page layout fields loaded successfully.

        Args:
            layout_fields: List of field API names from page layout
            salesforce_object: SalesforceObject to preview
            record_type_id: Record type ID
        """
        logger.info(f"Loaded {len(layout_fields)} fields from page layout")

        # Cleanup worker
        if hasattr(self, 'layout_worker') and self.layout_worker:
            self.layout_worker.deleteLater()
            self.layout_worker = None

        # Now load preview data with these fields
        self._load_preview_data(salesforce_object, record_type_id, layout_fields)

    def _on_layout_error(self, error_message: str, salesforce_object, record_type_id):
        """
        Handle error loading page layout fields.

        Args:
            error_message: Error message
            salesforce_object: SalesforceObject to preview
            record_type_id: Record type ID
        """
        logger.warning(f"Failed to load page layout, using default fields: {error_message}")

        # Cleanup worker
        if hasattr(self, 'layout_worker') and self.layout_worker:
            self.layout_worker.deleteLater()
            self.layout_worker = None

        # Fall back to loading with default field selection
        self._load_preview_data(salesforce_object, record_type_id, layout_fields=None)

    def _load_preview_data(self, salesforce_object, record_type_id, layout_fields):
        """
        Load preview data with specified parameters.

        Args:
            salesforce_object: SalesforceObject to preview
            record_type_id: Optional record type ID
            layout_fields: Optional list of fields from page layout
        """
        self.view.update_status(f"Loading sample data...")

        # Create and start data preview worker
        self.preview_worker = DataPreviewWorker(
            self.data_preview_service,
            salesforce_object,
            record_type_id,
            layout_fields
        )
        self.preview_worker.finished.connect(self._on_preview_data_loaded)
        self.preview_worker.error.connect(self._on_preview_error)
        self.preview_worker.start()

    def _on_preview_data_loaded(self, data: dict):
        """
        Handle preview data loaded successfully.

        Args:
            data: Dictionary with records, fields, and total_size
        """
        record_count = len(data.get('records', []))
        logger.info(f"Loaded {record_count} sample records")

        # Update view
        self.view.object_detail_widget.data_preview_widget.set_data(data)
        self.view.update_status(f"Loaded {record_count} sample records")

        # Cleanup worker
        if self.preview_worker:
            self.preview_worker.deleteLater()
            self.preview_worker = None

    def _on_preview_error(self, error_message: str):
        """
        Handle error loading preview data.

        Args:
            error_message: Error message
        """
        logger.error(f"Failed to load preview data: {error_message}")

        # Update view
        self.view.object_detail_widget.data_preview_widget.show_error(error_message)
        self.view.update_status("Error loading preview data")

        # Cleanup worker
        if self.preview_worker:
            self.preview_worker.deleteLater()
            self.preview_worker = None

    def _handle_export_preview_data(self):
        """Handle request to export preview data to CSV."""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import csv

        # Get current object and data
        current_object = self.view.object_detail_widget.current_object
        preview_widget = self.view.object_detail_widget.data_preview_widget

        if not current_object:
            logger.warning("No current object for export")
            return

        if not preview_widget.current_data:
            self.view.show_error(
                "Export Preview Data",
                "No preview data loaded. Click 'Load Sample Data' first."
            )
            return

        logger.info(f"Exporting preview data for: {current_object.name}")

        # Prompt for save location
        default_filename = f"{current_object.name}_SampleData.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Export Preview Data",
            default_filename,
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            # Get data from preview widget
            data = preview_widget.current_data
            records = data.get('records', [])
            fields = data.get('fields', [])

            # Write to CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields)
                writer.writeheader()

                # Write records
                for record in records:
                    # Extract only the fields we want (ignore nested objects)
                    row = {}
                    for field in fields:
                        value = record.get(field, '')
                        # Handle None values
                        if value is None:
                            row[field] = ''
                        # Handle boolean values
                        elif isinstance(value, bool):
                            row[field] = 'TRUE' if value else 'FALSE'
                        # Handle nested objects (lookup fields) - extract Name or Id
                        elif isinstance(value, dict):
                            row[field] = value.get('Name', value.get('Id', str(value)))
                        else:
                            row[field] = value
                    writer.writerow(row)

            logger.info(f"Exported {len(records)} records to: {file_path}")

            # Show success message
            QMessageBox.information(
                self.view,
                "Export Successful",
                f"Successfully exported {len(records)} records to CSV!\n\n"
                f"File: {file_path}\n"
                f"Fields: {len(fields)}\n"
                f"Records: {len(records)}"
            )

            self.view.update_status(f"Exported {len(records)} records to CSV")

        except Exception as e:
            logger.error(f"Error exporting preview data: {e}")
            self.view.show_error(
                "Export Failed",
                f"Failed to export preview data:\n{str(e)}"
            )

    def _handle_load_page_layouts(self, object_name: str):
        """
        Handle request to load page layout assignments for an object.

        Args:
            object_name: API name of the Salesforce object
        """
        current_object = self.view.object_detail_widget.current_object
        if not current_object or current_object.name != object_name:
            logger.warning(f"Current object mismatch: {current_object.name if current_object else 'None'} != {object_name}")
            return

        if not current_object.record_types:
            logger.info(f"No record types for {object_name}, skipping page layout fetch")
            return

        logger.info(f"Loading page layout assignments for: {object_name}")

        # Create and start page layout assignments worker
        self.page_layout_assignments_worker = PageLayoutAssignmentsWorker(
            self.sf_client,
            object_name,
            current_object
        )
        self.page_layout_assignments_worker.finished.connect(
            lambda assignments: self._on_page_layout_assignments_loaded(assignments, current_object)
        )
        self.page_layout_assignments_worker.error.connect(self._on_page_layout_assignments_error)
        self.page_layout_assignments_worker.start()

    def _on_page_layout_assignments_loaded(self, layout_assignments: dict, salesforce_object: SalesforceObject):
        """
        Handle page layout assignments loaded successfully.

        Args:
            layout_assignments: Dict mapping record_type_id -> layout_name
            salesforce_object: SalesforceObject with record types
        """
        logger.info(f"Page layout assignments loaded for {salesforce_object.name}: {len(layout_assignments)} assignments")

        # Update relationship widget with page layout information
        relationship_widget = self.view.object_detail_widget.relationship_table_widget

        # Update each row with its page layout name and ID
        for row, record_type in enumerate(sorted(salesforce_object.record_types, key=lambda rt: (not rt.is_default, rt.name))):
            layout_info = layout_assignments.get(record_type.record_type_id, {'name': "No layout assigned", 'id': None})
            layout_name = layout_info.get('name', 'No layout assigned') if isinstance(layout_info, dict) else layout_info
            layout_id = layout_info.get('id') if isinstance(layout_info, dict) else None
            relationship_widget.update_page_layout_for_row(row, layout_name, layout_id)

        logger.info(f"Updated {len(salesforce_object.record_types)} record type rows with page layout names")

        # Cleanup worker
        if hasattr(self, 'page_layout_assignments_worker'):
            self.page_layout_assignments_worker.deleteLater()
            self.page_layout_assignments_worker = None

    def _on_page_layout_assignments_error(self, error_message: str):
        """
        Handle error loading page layout assignments.

        Args:
            error_message: Error message
        """
        logger.error(f"Failed to load page layout assignments: {error_message}")

        # Update rows with error message
        relationship_widget = self.view.object_detail_widget.relationship_table_widget
        for row in range(relationship_widget.record_types_table.rowCount()):
            relationship_widget.update_page_layout_for_row(row, "Error loading layout")

        # Cleanup worker
        if hasattr(self, 'page_layout_assignments_worker'):
            self.page_layout_assignments_worker.deleteLater()
            self.page_layout_assignments_worker = None

    def _handle_layout_clicked(self, record_type_id: str, layout_id: str):
        """
        Handle layout click - filter fields to show only fields on the clicked layout.

        Args:
            record_type_id: ID of the record type
            layout_id: ID of the page layout
        """
        try:
            logger.info(f"Layout clicked: record_type_id={record_type_id}, layout_id={layout_id}")

            # Get current object from view
            current_object = self.view.object_detail_widget.current_object
            if not current_object:
                logger.warning("No object selected")
                return

            if not layout_id:
                logger.warning("No layout ID provided")
                return

            # Get layout fields from the Salesforce client
            layout_field_names = self.sf_client.get_layout_fields(layout_id)

            if not layout_field_names:
                logger.warning(f"No fields found for layout {layout_id}")
                self.view.update_status(f"No fields found on this layout")
                return

            # Get the layout name from the layout assignments
            relationship_widget = self.view.object_detail_widget.relationship_table_widget

            # Find the layout name by searching through the stored data
            layout_name = "Selected Layout"
            for row in range(relationship_widget.record_types_table.rowCount()):
                if row in relationship_widget.record_type_data:
                    rt_id, stored_layout_id = relationship_widget.record_type_data[row]
                    if stored_layout_id == layout_id:
                        layout_item = relationship_widget.record_types_table.item(row, 1)
                        if layout_item:
                            layout_name = layout_item.text()
                        break

            # Filter the fields tab to show only fields on this layout
            field_table_widget = self.view.object_detail_widget.field_table_widget
            field_table_widget.filter_by_layout_fields(layout_field_names, layout_name)

            # Switch to the Fields tab to show the filtered results
            self.view.object_detail_widget.tabs.setCurrentIndex(0)  # Fields tab is index 0

            logger.info(f"Filtered to {len(layout_field_names)} fields on layout {layout_name}")
            self.view.update_status(f"Showing {len(layout_field_names)} fields from layout: {layout_name}")

        except Exception as e:
            logger.error(f"Error handling layout click: {e}", exc_info=True)
            self.view.update_status(f"Error filtering layout fields: {e}")

    def _handle_file_import(self, file_path: str):
        """
        Handle file import request.

        Args:
            file_path: Path to file to import
        """
        logger.info(f"File import requested: {file_path}")

        # Show loading state
        self.view.object_detail_widget.mapping_widget.show_loading()
        self.view.update_status(f"Importing file...")

        # Create and start worker thread
        self.import_worker = FileImportWorker(self.file_import_service, file_path)
        self.import_worker.finished.connect(self._on_file_imported)
        self.import_worker.error.connect(self._on_import_error)
        self.import_worker.start()

    def _on_file_imported(self, source_file: SourceFile):
        """
        Handle file imported successfully.

        Args:
            source_file: SourceFile with metadata
        """
        logger.info(f"File imported: {source_file.total_rows} rows, {len(source_file.columns)} columns")

        # Update view
        self.view.object_detail_widget.mapping_widget.set_source_file(source_file)
        self.view.update_status(
            f"Imported {source_file.total_rows:,} rows from {source_file.file_type.upper()} file"
        )

        # Cleanup worker
        if self.import_worker:
            self.import_worker.deleteLater()
            self.import_worker = None

    def _on_import_error(self, error_message: str):
        """
        Handle error importing file.

        Args:
            error_message: Error message
        """
        logger.error(f"Failed to import file: {error_message}")

        # Update view
        self.view.object_detail_widget.mapping_widget.show_error(error_message)
        self.view.update_status("Error importing file")

        # Cleanup worker
        if self.import_worker:
            self.import_worker.deleteLater()
            self.import_worker = None

    def _handle_auto_map(self):
        """Handle auto-map request."""
        current_object = self.view.object_detail_widget.current_object
        mapping_widget = self.view.object_detail_widget.mapping_widget
        source_file = mapping_widget.source_file

        if not current_object or not source_file:
            logger.warning("Cannot auto-map: missing object or source file")
            return

        logger.info(f"Auto-mapping fields for {current_object.name}")

        # Generate mapping suggestions
        suggestions = self.mapping_service.auto_suggest_mappings(
            source_file,
            current_object,
            threshold=0.6
        )

        # Apply suggestions to the UI
        mapping_widget.set_mappings(suggestions)

        # Update status
        self.view.update_status(
            f"Auto-mapped {len(suggestions)} fields based on name similarity"
        )

    def _handle_save_mapping(self):
        """Handle save mapping request."""
        from PyQt5.QtWidgets import QFileDialog

        current_object = self.view.object_detail_widget.current_object
        mapping_widget = self.view.object_detail_widget.mapping_widget
        source_file = mapping_widget.source_file

        if not current_object or not source_file:
            logger.warning("Cannot save mapping: missing object or source file")
            return

        # Get current mappings
        mappings = mapping_widget.get_mappings()

        if not mappings:
            self.view.show_info("No Mappings", "There are no field mappings to save.")
            return

        # Prompt for file location
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Save Field Mapping",
            f"{current_object.name}_mapping.json",
            "JSON Files (*.json);;All Files (*.*)"
        )

        if not file_path:
            return

        try:
            # Create mapping configuration
            config = self.mapping_service.create_mapping(
                name=f"{current_object.label} Mapping",
                salesforce_object=current_object,
                source_file=source_file,
                description=f"Field mapping for {source_file.file_path}"
            )

            # Add mappings
            for mapping in mappings:
                config.add_mapping(mapping)

            # Save to file
            self.mapping_service.save_mapping(config, file_path)

            logger.info(f"Saved mapping configuration to: {file_path}")
            self.view.update_status(f"Mapping saved with {len(mappings)} fields")
            self.view.show_info("Mapping Saved", f"Field mapping saved to:\n{file_path}")

        except Exception as e:
            logger.error(f"Error saving mapping: {e}")
            self.view.show_error("Save Error", f"Failed to save mapping:\n\n{str(e)}")

    def _handle_load_mapping(self):
        """Handle load mapping request."""
        from PyQt5.QtWidgets import QFileDialog

        current_object = self.view.object_detail_widget.current_object
        mapping_widget = self.view.object_detail_widget.mapping_widget

        if not current_object:
            logger.warning("Cannot load mapping: no object selected")
            return

        # Prompt for file location
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Load Field Mapping",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )

        if not file_path:
            return

        try:
            # Load mapping configuration
            config = self.mapping_service.load_mapping(file_path)

            # Verify it matches the current object
            if config.salesforce_object != current_object.name:
                response = self.view.show_info(
                    "Object Mismatch",
                    f"This mapping is for '{config.salesforce_object}' but you selected '{current_object.name}'.\n\n"
                    "Do you want to load it anyway?",
                    show_cancel=True
                )
                if not response:
                    return

            # Apply mappings
            mapping_widget.set_mappings(config.mappings)

            logger.info(f"Loaded mapping configuration from: {file_path}")
            self.view.update_status(f"Loaded mapping with {len(config.mappings)} fields")

        except Exception as e:
            logger.error(f"Error loading mapping: {e}")
            self.view.show_error("Load Error", f"Failed to load mapping:\n\n{str(e)}")

    def _handle_template_download(self):
        """Handle template download request."""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox

        current_object = self.view.object_detail_widget.current_object

        if not current_object:
            logger.warning("Cannot download template: no object selected")
            self.view.show_error("Template Download", "Please select a Salesforce object first.")
            return

        # Prompt user for save location
        default_filename = f"{current_object.name}_Template.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Save CSV Template",
            default_filename,
            "CSV Files (*.csv);;All Files (*.*)"
        )

        if not file_path:
            return  # User cancelled

        try:
            # Generate template
            logger.info(f"Generating template for {current_object.name}")
            self.template_service.generate_template(
                current_object,
                file_path,
                include_optional=True,
                include_sample_row=True
            )

            # Count fields included in template
            createable_required = sum(
                1 for f in current_object.fields
                if f.required and f.createable and not getattr(f, 'calculated', False) and not getattr(f, 'auto_number', False)
            )
            total_required = sum(1 for f in current_object.fields if f.required)

            # Show success message
            QMessageBox.information(
                self.view,
                "Template Created",
                f"CSV template created successfully!\n\n"
                f"File: {file_path}\n\n"
                f"The template includes:\n"
                f"• {createable_required} required fields that you can populate\n"
                f"• Commonly-used optional fields\n"
                f"• A sample row showing field types and requirements\n\n"
                f"Note: {total_required - createable_required} required fields are excluded because they are\n"
                f"auto-calculated (formulas, rollups, auto-numbers) and cannot be set during import.\n\n"
                f"You can delete the sample row before importing your data."
            )

            logger.info(f"Template created successfully: {file_path}")

        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            self.view.show_error("Template Error", f"Failed to create template:\n{str(e)}")

    def _handle_filtered_template_download(self):
        """Handle template download for filtered fields (from layout click)."""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import csv

        current_object = self.view.object_detail_widget.current_object
        field_table_widget = self.view.object_detail_widget.field_table_widget

        if not current_object:
            logger.warning("Cannot download template: no object selected")
            self.view.show_error("Template Download", "Please select a Salesforce object first.")
            return

        # Get currently displayed fields
        displayed_fields = field_table_widget.fields

        if not displayed_fields:
            logger.warning("No fields to include in template")
            self.view.show_error("Template Download", "No fields to include in template.")
            return

        # Generate filename based on active filter
        if field_table_widget.active_filter_layout_name:
            layout_name_clean = field_table_widget.active_filter_layout_name.replace(" ", "_").replace("-", "_")
            default_filename = f"{current_object.name}_{layout_name_clean}_Template.csv"
        else:
            default_filename = f"{current_object.name}_Filtered_Template.csv"

        # Prompt user for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Save Filtered CSV Template",
            default_filename,
            "CSV Files (*.csv);;All Files (*.*)"
        )

        if not file_path:
            return  # User cancelled

        try:
            # Generate CSV with field API names as headers
            logger.info(f"Generating filtered template with {len(displayed_fields)} fields")

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Write header row with field API names
                field_names = [field.name for field in displayed_fields]
                writer.writerow(field_names)

            # Show success message
            layout_info = f" from layout '{field_table_widget.active_filter_layout_name}'" if field_table_widget.active_filter_layout_name else ""
            QMessageBox.information(
                self.view,
                "Template Created",
                f"CSV template created successfully!\n\n"
                f"File: {file_path}\n\n"
                f"The template includes {len(displayed_fields)} fields{layout_info}.\n\n"
                f"Column headers are the Salesforce field API names.\n"
                f"Add your data rows below the header row."
            )

            logger.info(f"Filtered template created successfully: {file_path}")

        except Exception as e:
            logger.error(f"Failed to create filtered template: {e}", exc_info=True)
            self.view.show_error("Template Error", f"Failed to create template:\n{str(e)}")

    def _handle_load_data(self):
        """Handle load data to Salesforce request."""
        from PyQt5.QtWidgets import QMessageBox
        from ..dialogs.load_progress_dialog import LoadProgressDialog
        from ..dialogs.record_type_dialog import RecordTypeDialog

        current_object = self.view.object_detail_widget.current_object
        mapping_widget = self.view.object_detail_widget.mapping_widget
        source_file = mapping_widget.source_file

        if not current_object or not source_file:
            logger.warning("Cannot load data: missing object or source file")
            self.view.show_error("Load Error", "Please select a Salesforce object and import a source file first.")
            return

        # Get current mappings
        mappings = mapping_widget.get_mappings()

        if not mappings:
            self.view.show_error("Load Error", "Please create field mappings before loading data.")
            return

        # Check if required fields are mapped
        required_fields = [f for f in current_object.fields if f.required]
        mapped_required = [
            f for f in required_fields
            if f.name in [m.target_field for m in mappings]
        ]

        if len(mapped_required) < len(required_fields):
            missing = [f for f in required_fields if f.name not in [m.target_field for m in mappings]]
            response = QMessageBox.question(
                self.view,
                "Missing Required Fields",
                f"The following required fields are not mapped:\n\n" +
                "\n".join([f"• {f.label} ({f.name})" for f in missing]) +
                f"\n\nDo you want to continue anyway? Records may fail to load.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if response == QMessageBox.No:
                return

        # Check if object has record types - prompt for selection
        record_type_id = None
        selected_rt = None
        if current_object.record_types:
            logger.info(f"Object {current_object.name} has {len(current_object.record_types)} record types")
            rt_dialog = RecordTypeDialog(current_object.record_types, current_object.label, self.view)
            if rt_dialog.exec_() == RecordTypeDialog.Accepted:
                selected_rt = rt_dialog.get_selected_record_type()
                if selected_rt:
                    record_type_id = selected_rt.record_type_id
                    logger.info(f"Selected record type: {selected_rt.label} ({record_type_id})")
            else:
                # User cancelled record type selection
                return

        # Confirm data load
        rt_info = f"\nRecord Type: {selected_rt.label}" if selected_rt else ""
        response = QMessageBox.question(
            self.view,
            "Confirm Data Load",
            f"Load {source_file.total_rows:,} records to {current_object.label}?\n\n"
            f"Operation: Insert\n"
            f"Mapped fields: {len(mappings)}{rt_info}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if response == QMessageBox.No:
            return

        logger.info(f"Starting data load: {source_file.total_rows} rows to {current_object.name}")

        # Create progress dialog
        progress_dialog = LoadProgressDialog(self.view)
        progress_dialog.set_total(source_file.total_rows)
        progress_dialog.show()

        # Create and start worker thread
        self.load_worker = DataLoadWorker(
            self.data_loader_service,
            source_file,
            mappings,
            current_object,
            operation='insert',
            record_type_id=record_type_id
        )
        self.load_worker.finished.connect(lambda result: self._on_data_loaded(result, progress_dialog))
        self.load_worker.error.connect(lambda error: self._on_load_data_error(error, progress_dialog))
        self.load_worker.status.connect(progress_dialog.update_status)  # Connect status updates for Bulk API
        self.load_worker.progress.connect(progress_dialog.update_progress)  # Connect progress updates
        self.load_worker.start()

        self.view.update_status(f"Loading {source_file.total_rows:,} records to Salesforce...")

    def _on_data_loaded(self, result: LoadResult, progress_dialog: 'LoadProgressDialog'):
        """
        Handle data loaded successfully.

        Args:
            result: LoadResult with statistics
            progress_dialog: Progress dialog to update
        """
        logger.info(
            f"Data load complete: {result.successful_rows}/{result.total_rows} successful, "
            f"{result.failed_rows} failed"
        )

        # Update progress bar to show final state
        progress_dialog.update_progress(result.total_rows, result.successful_rows, result.failed_rows)

        # Update progress dialog with completion message
        progress_dialog.set_complete(result.successful_rows, result.failed_rows)

        # Add errors to dialog
        for error in result.errors:
            progress_dialog.add_error(error['row'], error['error'])

        # Update status
        if result.failed_rows == 0:
            self.view.update_status(f"Successfully loaded {result.successful_rows:,} records!")
        else:
            self.view.update_status(
                f"Load complete: {result.successful_rows:,} successful, {result.failed_rows} failed"
            )

        # Cleanup worker
        if self.load_worker:
            self.load_worker.deleteLater()
            self.load_worker = None

    def _on_load_data_error(self, error_message: str, progress_dialog: 'LoadProgressDialog'):
        """
        Handle error loading data.

        Args:
            error_message: Error message
            progress_dialog: Progress dialog to update
        """
        logger.error(f"Failed to load data: {error_message}")

        # Update progress dialog
        progress_dialog.set_error(error_message)

        # Update status
        self.view.update_status("Error loading data")

        # Cleanup worker
        if self.load_worker:
            self.load_worker.deleteLater()
            self.load_worker = None

    def _handle_logout(self):
        """Handle logout request."""
        logger.info("Logout requested")

        # Disconnect from Salesforce
        if self.auth_service.is_connected():
            self.auth_service.disconnect()

        # Emit signal to app to show login again
        self.logout_requested.emit()

    def cleanup(self):
        """Cleanup resources when presenter is no longer needed."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        if self.describe_worker and self.describe_worker.isRunning():
            self.describe_worker.terminate()
            self.describe_worker.wait()

        if self.preview_worker and self.preview_worker.isRunning():
            self.preview_worker.terminate()
            self.preview_worker.wait()

        if self.import_worker and self.import_worker.isRunning():
            self.import_worker.terminate()
            self.import_worker.wait()

        if self.load_worker and self.load_worker.isRunning():
            self.load_worker.terminate()
            self.load_worker.wait()

        if self.auth_service.is_connected():
            self.auth_service.disconnect()
