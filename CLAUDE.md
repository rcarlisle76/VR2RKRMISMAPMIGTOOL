# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Launch the application
python -m src.main
```

The application MUST be run as a module (`python -m src.main`) due to relative imports. Running `python src/main.py` will fail with ImportError.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Code formatting
black src/

# Type checking
mypy src/
```

## Architecture Overview

### MVP Pattern (Model-View-Presenter)

The application strictly follows MVP to separate UI from business logic:

- **View (PyQt5 widgets)**: Pure UI, emits PyQt signals, NO business logic
- **Presenter**: Orchestrates between View and Services, handles signals
- **Model/Services**: Business logic, data access, Salesforce API calls

**Critical Rule**: Views NEVER call Services directly. All interactions go through Presenters.

### Application Flow

1. **main.py**: Bootstraps app → Creates LoginWindow + LoginPresenter
2. **LoginPresenter**: Handles auth → On success, creates MainWindow + MainPresenter
3. **MainPresenter**: Orchestrates all main window operations (metadata, mapping, data loading)

### Threading Model

**All long-running operations MUST run in QThread workers to prevent UI blocking:**

- `MetadataLoadWorker`: Loads Salesforce object list (~200-500ms)
- `ObjectDescribeWorker`: Fetches object metadata (200-500ms per object)
- `DataPreviewWorker`: Queries sample data from Salesforce
- `FileImportWorker`: Parses CSV/Excel files with type inference
- `DataLoadWorker`: Inserts/updates records to Salesforce

**Pattern**:
```python
class SomeWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def run(self):
        try:
            result = self.service.do_work()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

### Data Loading Pipeline

**Critical Validation Chain** (src/services/data_loader_service.py):

The `_convert_value()` method validates and transforms CSV values based on Salesforce field metadata:

1. **System Fields**: Automatically exclude `Id` (auto-generated) and `RecordTypeId` (from dialog selection)
2. **Read-only Fields**: Skip fields where `field.createable == False` (formula, rollup, auto-number)
3. **Picklist Fields**: Validate against `field.picklist_values`, case-insensitive matching
4. **Lookup/Reference Fields**: Only accept valid 15 or 18-character Salesforce IDs
5. **Type Conversion**:
   - Boolean: "Yes"/"No"/"True"/"False" → `True`/`False`
   - Numeric: Remove commas, currency symbols ("1,000" → 1000, "$50" → 50.0)
   - Date: Support multiple formats (YYYY-MM-DD, MM/DD/YYYY, etc.)

**Invalid values are skipped (set to None) rather than causing load failures.**

### Record Type Handling

Objects with multiple record types show a `RecordTypeDialog` before data load:
- `MetadataService._fetch_record_types()`: Queries RecordType object during object describe
- `RecordTypeDialog`: User selects which record type to assign
- Selected `record_type_id` is added to all records during transformation
- CSV columns mapped to RecordTypeId are ignored

### Signal Flow Example (Data Loading)

```
User clicks "Load Data" button
→ MappingTableWidget.load_data_requested signal
→ MappingWidget.load_data_requested signal
→ ObjectDetailWidget.load_data_requested signal
→ MainPresenter._handle_load_data()
  → Validates mappings
  → Shows RecordTypeDialog (if object has record types)
  → Shows confirmation dialog
  → Creates DataLoadWorker
  → Shows LoadProgressDialog
→ DataLoadWorker.finished signal
→ MainPresenter._on_data_loaded()
  → Updates progress dialog with results
```

### Key Services

**MetadataService** (`src/services/metadata_service.py`):
- Fetches Salesforce object lists and field metadata
- Queries RecordType objects for each SalesforceObject
- Uses `SalesforceClient.describe_global()` and `.describe_object()`

**MappingService** (`src/services/mapping_service.py`):
- Auto-suggests field mappings using fuzzy string matching (SequenceMatcher)
- Normalizes field names: lowercase, remove underscores/spaces, strip suffixes (__c, id, name)
- Saves/loads mapping configurations as JSON

**AIEnhancedMappingService** (`src/services/ai_mapping_service.py`):
- Extends MappingService with AI capabilities (hybrid approach)
- **Phase 1**: Semantic embeddings using sentence-transformers (local, offline, free)
  - Understands synonyms: phone ↔ telephone, email ↔ e-mail
  - Handles abbreviations: amt ↔ amount, num ↔ number
  - Uses all-MiniLM-L6-v2 model (~500MB, cached locally)
- **Phase 2**: Claude API integration (optional, requires API key)
  - LLM-based intelligent mapping for complex scenarios
  - Context-aware suggestions (analyzes all fields together)
  - Type validation and reasoning explanation
  - Cost: ~$0.003 per mapping operation
- Three-step hybrid algorithm:
  1. Fuzzy matching (threshold 0.7) - fast, deterministic
  2. Semantic matching (threshold 0.6) - for low-confidence fuzzy matches
  3. LLM mapping (threshold 0.75) - for remaining unmapped columns
- Configuration via AppConfig: use_semantic_matching, use_llm_mapping, claude_api_key
- Lazy-loads models to avoid startup delay
- Falls back to basic MappingService if AI features disabled or dependencies missing

**DataLoaderService** (`src/services/data_loader_service.py`):
- Transforms CSV data based on field mappings and Salesforce metadata
- Handles type conversion and validation (see Data Loading Pipeline above)
- Inserts/updates records via simple-salesforce client
- Returns `LoadResult` with success/failure counts and error details

**FileImportService** (`src/services/file_import_service.py`):
- Parses CSV with multiple encoding support (utf-8, latin-1, cp1252)
- Infers column types (date > number > boolean > string) from sample values
- Returns `SourceFile` with column metadata

### Data Models

**SalesforceObject** (`src/models/salesforce_metadata.py`):
```python
@dataclass
class SalesforceObject:
    name: str           # API name
    label: str          # Display label
    fields: List[SalesforceField]
    record_types: List[RecordType]  # Available record types
    createable: bool
    # ... other metadata
```

**SalesforceField**:
```python
@dataclass
class SalesforceField:
    name: str
    type: str           # string, reference, picklist, boolean, etc.
    createable: bool    # Can be set during insert
    required: bool      # Nillable=False in SF
    picklist_values: List[str]  # For validation
    # ... other metadata
```

**FieldMapping** (`src/models/mapping_models.py`):
```python
@dataclass
class FieldMapping:
    source_column: str      # CSV column name
    target_field: str       # Salesforce field API name
    mapping_type: str       # 'direct', future: 'transform', 'concat'
    is_required: bool
```

## Credential Storage

Uses OS-level secure storage via `keyring` library:
- **Windows**: Credential Manager
- **macOS**: Keychain
- **Linux**: Secret Service (GNOME Keyring)

Credentials stored at service name: `salesforce_migration_tool`

## Configuration & Logs

All stored in `~/.salesforce_migration_tool/`:
- `config.json`: App configuration
- `logs/migration_tool.log`: Application logs (INFO level)
- `logs/migration_tool_error.log`: Error logs (ERROR level)

**Sensitive data (passwords, tokens) are NEVER logged.**

## Widget Hierarchy

```
MainWindow
├── ObjectListWidget (left panel)
│   └── Shows all Salesforce objects
└── ObjectDetailWidget (right panel)
    ├── HeaderGroup (object info)
    └── QTabWidget
        ├── Fields Tab
        │   ├── FieldTableWidget
        │   └── FieldDetailPanel
        ├── Preview Tab
        │   └── DataPreviewWidget
        └── Map Fields Tab
            └── MappingWidget
                ├── SourceFilePanel (left)
                └── MappingTableWidget (right)
                    └── Dropdowns for field mappings
```

## Common Pitfalls

1. **Running without `-m` flag**: Always use `python -m src.main`, not `python src/main.py`
2. **Blocking UI thread**: All API calls and file operations must use QThread workers
3. **Skipping field validation**: Always check `field.createable` before including in insert
4. **Not clearing state**: When switching objects, call `widget.clear()` before `set_object()`
5. **Missing signal connections**: Presenters must connect to ALL widget signals they need

## File Naming Conventions

- Services: `{name}_service.py` (e.g., `metadata_service.py`)
- Widgets: `{name}_widget.py` (e.g., `mapping_table_widget.py`)
- Dialogs: `{name}_dialog.py` (e.g., `record_type_dialog.py`)
- Presenters: `{name}_presenter.py` (e.g., `main_presenter.py`)
- Workers: Defined inline in presenters as `{Operation}Worker` classes

## Adding New Features

When adding data transformation features:

1. Update `DataLoaderService._convert_value()` with new field type handling
2. Update `FileImportService._infer_type()` if new CSV type detection needed
3. Add validation in `ValidationService` for new mapping rules
4. Update `MappingService.auto_suggest_mappings()` if field name patterns change

When adding new Salesforce metadata:

1. Add fields to `SalesforceObject` or `SalesforceField` dataclass
2. Update `MetadataService._parse_object_describe()` to parse new fields
3. Consider if field needs validation in `DataLoaderService`
