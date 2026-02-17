# Test Suite

Comprehensive test suite for the Ventiv to Riskonnect Migration Tool.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, no external dependencies)
│   ├── test_mapping_service.py
│   ├── test_validation_service.py
│   ├── test_file_import_service.py
│   └── test_data_loader_service.py
├── integration/             # Integration tests (may require network/DB)
│   └── (to be added)
├── ui/                      # UI tests (require PyQt5)
│   └── (to be added)
└── fixtures/                # Test data files
    └── (sample CSV files, etc.)
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories

**Unit tests only (fast):**
```bash
pytest -m unit
```

**Integration tests:**
```bash
pytest -m integration
```

**UI tests:**
```bash
pytest -m ui
```

**Exclude slow tests:**
```bash
pytest -m "not slow"
```

### Run Specific Test Files
```bash
# Single file
pytest tests/unit/test_mapping_service.py

# Single test class
pytest tests/unit/test_mapping_service.py::TestMappingService

# Single test method
pytest tests/unit/test_mapping_service.py::TestMappingService::test_create_mapping
```

### Run with Coverage
```bash
# Install coverage
pip install pytest-cov

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Verbose Output
```bash
pytest -v  # Verbose
pytest -vv  # Very verbose
pytest -s  # Show print statements
```

## Test Markers

Tests are marked with the following markers (defined in `pytest.ini`):

- `@pytest.mark.unit` - Fast unit tests with no external dependencies
- `@pytest.mark.integration` - Integration tests that may require network/DB
- `@pytest.mark.ui` - UI tests requiring PyQt5
- `@pytest.mark.slow` - Tests that take >1 second to run
- `@pytest.mark.ai` - Tests requiring AI models (sentence-transformers)

Example:
```python
@pytest.mark.unit
def test_something():
    assert True
```

## Fixtures

Shared fixtures are defined in `conftest.py`:

### Salesforce Object Fixtures
- `sample_salesforce_field` - Standard field (FirstName)
- `sample_picklist_field` - Picklist field (Status)
- `sample_lookup_field` - Reference field (AccountId)
- `sample_readonly_field` - Read-only/formula field
- `sample_record_type` - Sample record type
- `sample_salesforce_object` - Complete Salesforce object with fields
- `object_list_items` - List of object metadata

### Source File Fixtures
- `sample_source_columns` - Sample CSV columns
- `sample_source_file` - Complete source file metadata
- `sample_csv_content` - CSV file content as string
- `sample_csv_file` - Temporary CSV file on disk

### Mapping Fixtures
- `sample_field_mappings` - Sample field mapping configurations

### Mock Fixtures
- `mock_sf_client` - Mock Salesforce client for testing
- `mock_config` - Mock application configuration

### PyQt Fixtures
- `qapp` - QApplication instance for UI tests

## Writing New Tests

### Unit Test Template

```python
"""
Unit tests for MyService.
"""

import pytest
from src.services.my_service import MyService


@pytest.mark.unit
class TestMyService:
    """Test suite for MyService."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        service = MyService()
        result = service.do_something()
        assert result == expected_value

    def test_edge_case(self):
        """Test edge case handling."""
        service = MyService()
        with pytest.raises(ValueError, match="error message"):
            service.do_invalid_thing()
```

### Using Fixtures

```python
@pytest.mark.unit
def test_with_fixture(sample_salesforce_object):
    """Test using a fixture."""
    # Fixture is automatically provided by pytest
    assert sample_salesforce_object.name == "Contact"
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

@pytest.mark.unit
def test_with_mock(mock_sf_client):
    """Test with mocked Salesforce client."""
    # mock_sf_client is provided by conftest.py
    service = MyService(mock_sf_client)

    # Mock returns predefined responses
    mock_sf_client.insert.return_value = {"id": "001xxx", "success": True}

    result = service.create_record({"Name": "Test"})
    assert result["success"] is True
```

### Temporary Files

```python
@pytest.mark.unit
def test_with_temp_file(tmp_path):
    """Test with temporary file."""
    # tmp_path is a pytest fixture for temporary directories
    test_file = tmp_path / "test.csv"
    test_file.write_text("Name,Email\nJohn,john@example.com")

    result = parse_csv(str(test_file))
    assert len(result) == 1
```

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Descriptive Names**: Use descriptive test method names that explain what is being tested
3. **AAA Pattern**: Arrange, Act, Assert
   ```python
   def test_something():
       # Arrange - Set up test data
       service = MyService()

       # Act - Execute the code under test
       result = service.do_something()

       # Assert - Verify the results
       assert result == expected_value
   ```
4. **One Assertion Per Test**: Ideally test one thing per test method
5. **Use Fixtures**: Leverage fixtures to avoid code duplication
6. **Mock External Dependencies**: Don't hit real APIs or databases in unit tests
7. **Test Edge Cases**: Test boundary conditions, empty inputs, invalid data, etc.

## Current Test Coverage

### Implemented Tests

✅ **MappingService** (test_mapping_service.py)
- Mapping creation and configuration
- Auto-suggestion algorithm
- Similarity calculation
- Save/load functionality
- Field validation

✅ **ValidationService** (test_validation_service.py)
- Required field validation
- Duplicate mapping detection
- Invalid field detection
- Non-updateable field warnings
- Validation result helpers

✅ **FileImportService** (test_file_import_service.py)
- File type detection
- Data type inference
- CSV reading with multiple encodings
- Value validation (dates, numbers, booleans)
- Preview functionality

✅ **DataLoaderService** (test_data_loader_service.py)
- Value conversion logic
- Type transformation
- Data validation
- Read-only field handling
- Record type assignment

### TODO: Additional Tests Needed

- [ ] AIEnhancedMappingService (semantic matching, LLM integration)
- [ ] MetadataService (requires mocked Salesforce API)
- [ ] AuthService (credential management)
- [ ] TemplateService (if implemented)
- [ ] UI Components (LoginWindow, MainWindow, etc.)
- [ ] Integration tests with real Salesforce sandbox
- [ ] End-to-end workflow tests

## CI/CD Integration

To integrate with CI/CD pipelines:

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Troubleshooting

### Import Errors
If you get import errors, make sure you're running pytest from the project root:
```bash
cd /path/to/VR2RKRMISMAPMIGTOOL
pytest
```

### PyQt5 Issues on Headless Systems
For CI/CD on headless systems, set:
```bash
export QT_QPA_PLATFORM=offscreen
pytest
```

### Slow Tests
Identify slow tests:
```bash
pytest --durations=10
```

## Contributing

When adding new features, please:
1. Write tests for new code
2. Ensure all tests pass: `pytest`
3. Maintain or improve coverage: `pytest --cov=src`
4. Follow existing test patterns and naming conventions
