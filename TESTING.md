# Testing Guide

Quick start guide for running tests in the Ventiv to Riskonnect Migration Tool.

## Setup

### 1. Install Test Dependencies

First, make sure you have all development dependencies installed:

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (includes pytest)
pip install -r requirements-dev.txt
```

### 2. Verify Installation

Check that pytest is installed:

```bash
pytest --version
```

You should see something like:
```
pytest 7.4.3
```

## Running Tests

### Quick Start

Run all unit tests:
```bash
pytest tests/unit/ -v
```

### Common Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_mapping_service.py

# Run specific test class
pytest tests/unit/test_mapping_service.py::TestMappingService

# Run specific test
pytest tests/unit/test_mapping_service.py::TestMappingService::test_create_mapping

# Run only unit tests (fast)
pytest -m unit

# Run with coverage report
pytest --cov=src --cov-report=term --cov-report=html

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l
```

## Test Results

### Expected Output

When all tests pass, you should see:
```
================================ test session starts ================================
collected 85 items

tests/unit/test_mapping_service.py ...................... [ 24%]
tests/unit/test_validation_service.py ................... [ 47%]
tests/unit/test_file_import_service.py .................. [ 71%]
tests/unit/test_data_loader_service.py .................. [100%]

================================ 85 passed in 2.5s ==================================
```

### Test Coverage

Generate a coverage report:
```bash
pytest --cov=src --cov-report=html
```

Then open `htmlcov/index.html` in your browser to see detailed coverage.

## Test Structure

```
tests/
├── conftest.py                  # Shared fixtures
├── unit/                        # Unit tests (✅ implemented)
│   ├── test_mapping_service.py
│   ├── test_validation_service.py
│   ├── test_file_import_service.py
│   └── test_data_loader_service.py
├── integration/                 # Integration tests (📝 TODO)
└── ui/                          # UI tests (📝 TODO)
```

## Current Test Coverage

### ✅ Implemented (85 tests)

**MappingService** (34 tests)
- ✅ Mapping creation and configuration
- ✅ Auto-suggestion with fuzzy matching
- ✅ String similarity algorithm
- ✅ Save/load JSON mappings
- ✅ Required field detection

**ValidationService** (16 tests)
- ✅ Required field validation
- ✅ Invalid field detection
- ✅ Duplicate mapping warnings
- ✅ Non-updateable field checks
- ✅ Validation result helpers

**FileImportService** (24 tests)
- ✅ File type detection (CSV, Excel)
- ✅ Type inference (string, number, date, boolean)
- ✅ Multi-encoding support (UTF-8, Latin-1, etc.)
- ✅ Value validation helpers
- ✅ Preview functionality

**DataLoaderService** (11 tests)
- ✅ Value conversion by type
- ✅ Picklist validation
- ✅ Reference field validation
- ✅ Data transformation
- ✅ Read-only field handling

### 📝 TODO: Additional Tests

- [ ] AIEnhancedMappingService (semantic + LLM)
- [ ] MetadataService (Salesforce API mocking)
- [ ] AuthService (credential management)
- [ ] UI Components (PyQt5 widgets)
- [ ] Integration tests (real Salesforce sandbox)

## Troubleshooting

### "No module named pytest"

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

### "Import error: No module named src"

Make sure you're running pytest from the project root directory:
```bash
cd C:\Users\robert.carlisle\Desktop\MigrationTool\VR2RKRMISMAPMIGTOOL
pytest
```

### "Fixture 'qtbot' not found" (for UI tests)

Install pytest-qt:
```bash
pip install pytest-qt
```

### Tests are slow

Run only fast unit tests:
```bash
pytest -m unit -m "not slow"
```

### See print() statements

Use the `-s` flag:
```bash
pytest -s
```

## Continuous Integration

### GitHub Actions Example

Add to `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
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

## Writing New Tests

See `tests/README.md` for detailed guidance on writing tests.

### Quick Template

```python
"""
Unit tests for MyNewService.
"""

import pytest
from src.services.my_new_service import MyNewService


@pytest.mark.unit
class TestMyNewService:
    """Test suite for MyNewService."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        service = MyNewService()
        result = service.do_something()
        assert result == expected_value
```

## Next Steps

1. **Install dependencies**: `pip install -r requirements-dev.txt`
2. **Run tests**: `pytest -v`
3. **Check coverage**: `pytest --cov=src --cov-report=html`
4. **Review coverage**: Open `htmlcov/index.html`
5. **Add more tests**: See TODO section above

---

For more detailed documentation, see:
- `tests/README.md` - Comprehensive test documentation
- `pytest.ini` - Pytest configuration
- `tests/conftest.py` - Shared fixtures
