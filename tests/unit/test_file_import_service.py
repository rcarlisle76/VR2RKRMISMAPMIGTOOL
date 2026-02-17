"""
Unit tests for FileImportService.
"""

import pytest
from pathlib import Path

from src.services.file_import_service import FileImportService


@pytest.mark.unit
class TestFileTypeDetection:
    """Test suite for file type detection."""

    def test_detect_csv_lowercase(self):
        """Test detecting CSV with lowercase extension."""
        service = FileImportService()
        file_type = service._detect_file_type("test.csv")
        assert file_type == "csv"

    def test_detect_csv_uppercase(self):
        """Test detecting CSV with uppercase extension."""
        service = FileImportService()
        file_type = service._detect_file_type("test.CSV")
        assert file_type == "csv"

    def test_detect_xlsx(self):
        """Test detecting Excel xlsx files."""
        service = FileImportService()
        file_type = service._detect_file_type("test.xlsx")
        assert file_type == "excel"

    def test_detect_xls(self):
        """Test detecting Excel xls files."""
        service = FileImportService()
        file_type = service._detect_file_type("test.xls")
        assert file_type == "excel"

    def test_unsupported_extension(self):
        """Test that unsupported extensions raise ValueError."""
        service = FileImportService()
        with pytest.raises(ValueError, match="Unsupported file extension"):
            service._detect_file_type("test.txt")


@pytest.mark.unit
class TestTypeInference:
    """Test suite for data type inference."""

    def test_infer_string_type(self):
        """Test inferring string type."""
        service = FileImportService()
        values = ["John", "Jane", "Bob", "Alice"]
        inferred_type = service._infer_type(values)
        assert inferred_type == "string"

    def test_infer_number_type(self):
        """Test inferring number type."""
        service = FileImportService()
        values = ["100", "200.5", "300", "400.75"]
        inferred_type = service._infer_type(values)
        assert inferred_type == "number"

    def test_infer_number_with_currency(self):
        """Test inferring number with currency symbols."""
        service = FileImportService()
        values = ["$100", "$200.50", "$1,000.00", "$50"]
        inferred_type = service._infer_type(values)
        assert inferred_type == "number"

    def test_infer_number_with_commas(self):
        """Test inferring number with comma separators."""
        service = FileImportService()
        values = ["1,000", "2,500.50", "10,000", "500"]
        inferred_type = service._infer_type(values)
        assert inferred_type == "number"

    def test_infer_date_type_yyyy_mm_dd(self):
        """Test inferring date type (YYYY-MM-DD format)."""
        service = FileImportService()
        values = ["2024-01-15", "2024-02-20", "2024-03-30"]
        inferred_type = service._infer_type(values)
        assert inferred_type == "date"

    def test_infer_date_type_mm_dd_yyyy(self):
        """Test inferring date type (MM/DD/YYYY format)."""
        service = FileImportService()
        values = ["01/15/2024", "02/20/2024", "03/30/2024"]
        inferred_type = service._infer_type(values)
        assert inferred_type == "date"

    def test_infer_boolean_type_true_false(self):
        """Test inferring boolean type (true/false)."""
        service = FileImportService()
        values = ["true", "false", "TRUE", "FALSE", "True"]
        inferred_type = service._infer_type(values)
        assert inferred_type == "boolean"

    def test_infer_boolean_type_yes_no(self):
        """Test inferring boolean type (yes/no)."""
        service = FileImportService()
        values = ["yes", "no", "YES", "NO", "Yes"]
        inferred_type = service._infer_type(values)
        assert inferred_type == "boolean"

    def test_infer_boolean_type_1_0(self):
        """Test inferring boolean type (1/0)."""
        service = FileImportService()
        values = ["1", "0", "1", "0", "1"]
        # Note: This might be inferred as number, which is acceptable
        inferred_type = service._infer_type(values)
        assert inferred_type in ["boolean", "number"]

    def test_infer_with_empty_values(self):
        """Test type inference with some empty values."""
        service = FileImportService()
        values = ["100", "", "200", None, "300", ""]
        inferred_type = service._infer_type(values)
        assert inferred_type == "number"

    def test_infer_all_empty_values(self):
        """Test type inference with all empty values."""
        service = FileImportService()
        values = ["", None, "", "  ", None]
        inferred_type = service._infer_type(values)
        assert inferred_type == "string"  # Default to string

    def test_infer_mixed_types_defaults_to_string(self):
        """Test that mixed types default to string."""
        service = FileImportService()
        values = ["100", "text", "200", "more text", "300"]
        # Less than 80% numbers, should default to string
        inferred_type = service._infer_type(values)
        assert inferred_type == "string"

    def test_infer_threshold_80_percent(self):
        """Test that 80% threshold is applied correctly."""
        service = FileImportService()
        # 8 numbers out of 10 = 80%
        values = ["1", "2", "3", "4", "5", "6", "7", "8", "text", "text"]
        inferred_type = service._infer_type(values)
        assert inferred_type == "number"


@pytest.mark.unit
class TestValueValidation:
    """Test suite for value validation helpers."""

    def test_is_number_integer(self):
        """Test number detection for integers."""
        service = FileImportService()
        assert service._is_number("123") is True
        assert service._is_number("0") is True
        assert service._is_number("-50") is True

    def test_is_number_decimal(self):
        """Test number detection for decimals."""
        service = FileImportService()
        assert service._is_number("123.45") is True
        assert service._is_number("0.5") is True
        assert service._is_number("-50.75") is True

    def test_is_number_with_currency(self):
        """Test number detection with currency symbols."""
        service = FileImportService()
        assert service._is_number("$100") is True
        assert service._is_number("$1,234.56") is True

    def test_is_number_with_commas(self):
        """Test number detection with comma separators."""
        service = FileImportService()
        assert service._is_number("1,000") is True
        assert service._is_number("1,234,567.89") is True

    def test_is_number_invalid(self):
        """Test number detection returns False for non-numbers."""
        service = FileImportService()
        assert service._is_number("abc") is False
        assert service._is_number("12.34.56") is False
        assert service._is_number("") is False

    def test_is_date_yyyy_mm_dd(self):
        """Test date detection for YYYY-MM-DD format."""
        service = FileImportService()
        assert service._is_date("2024-01-15") is True
        assert service._is_date("2024-12-31") is True

    def test_is_date_mm_dd_yyyy(self):
        """Test date detection for MM/DD/YYYY format."""
        service = FileImportService()
        assert service._is_date("01/15/2024") is True
        assert service._is_date("12/31/2024") is True

    def test_is_date_mm_dd_yyyy_dash(self):
        """Test date detection for MM-DD-YYYY format."""
        service = FileImportService()
        assert service._is_date("01-15-2024") is True
        assert service._is_date("12-31-2024") is True

    def test_is_date_yyyy_mm_dd_slash(self):
        """Test date detection for YYYY/MM/DD format."""
        service = FileImportService()
        assert service._is_date("2024/01/15") is True
        assert service._is_date("2024/12/31") is True

    def test_is_date_with_time(self):
        """Test date detection with time component."""
        service = FileImportService()
        assert service._is_date("2024-01-15 10:30:00") is True
        assert service._is_date("01/15/2024 10:30") is True

    def test_is_date_invalid(self):
        """Test date detection returns False for non-dates."""
        service = FileImportService()
        assert service._is_date("not a date") is False
        assert service._is_date("123456") is False
        assert service._is_date("") is False

    def test_is_boolean_true_false(self):
        """Test boolean detection for true/false."""
        service = FileImportService()
        assert service._is_boolean("true") is True
        assert service._is_boolean("false") is True
        assert service._is_boolean("TRUE") is True
        assert service._is_boolean("FALSE") is True
        assert service._is_boolean("True") is True

    def test_is_boolean_yes_no(self):
        """Test boolean detection for yes/no."""
        service = FileImportService()
        assert service._is_boolean("yes") is True
        assert service._is_boolean("no") is True
        assert service._is_boolean("YES") is True
        assert service._is_boolean("NO") is True

    def test_is_boolean_1_0(self):
        """Test boolean detection for 1/0."""
        service = FileImportService()
        assert service._is_boolean("1") is True
        assert service._is_boolean("0") is True

    def test_is_boolean_t_f(self):
        """Test boolean detection for t/f."""
        service = FileImportService()
        assert service._is_boolean("t") is True
        assert service._is_boolean("f") is True
        assert service._is_boolean("T") is True
        assert service._is_boolean("F") is True

    def test_is_boolean_y_n(self):
        """Test boolean detection for y/n."""
        service = FileImportService()
        assert service._is_boolean("y") is True
        assert service._is_boolean("n") is True
        assert service._is_boolean("Y") is True
        assert service._is_boolean("N") is True

    def test_is_boolean_with_whitespace(self):
        """Test boolean detection with whitespace."""
        service = FileImportService()
        assert service._is_boolean("  true  ") is True
        assert service._is_boolean("  yes  ") is True

    def test_is_boolean_invalid(self):
        """Test boolean detection returns False for non-booleans."""
        service = FileImportService()
        assert service._is_boolean("maybe") is False
        assert service._is_boolean("2") is False
        assert service._is_boolean("") is False


@pytest.mark.unit
class TestCSVImport:
    """Test suite for CSV import functionality."""

    def test_import_csv_basic(self, sample_csv_file):
        """Test basic CSV import."""
        service = FileImportService()
        source_file = service.import_file(sample_csv_file)

        assert source_file.file_path == sample_csv_file
        assert source_file.file_type == "csv"
        assert source_file.total_rows == 3
        assert len(source_file.columns) == 5

    def test_import_csv_column_names(self, sample_csv_file):
        """Test that column names are correctly extracted."""
        service = FileImportService()
        source_file = service.import_file(sample_csv_file)

        column_names = [col.name for col in source_file.columns]
        assert "FirstName" in column_names
        assert "LastName" in column_names
        assert "Email" in column_names
        assert "Status" in column_names
        assert "Amount" in column_names

    def test_import_csv_type_inference(self, sample_csv_file):
        """Test that types are correctly inferred."""
        service = FileImportService()
        source_file = service.import_file(sample_csv_file)

        # Find Amount column - should be inferred as number
        amount_col = next(col for col in source_file.columns if col.name == "Amount")
        assert amount_col.inferred_type == "number"

        # Find Status column - should be string
        status_col = next(col for col in source_file.columns if col.name == "Status")
        assert status_col.inferred_type == "string"

    def test_import_csv_sample_values(self, sample_csv_file):
        """Test that sample values are collected."""
        service = FileImportService()
        source_file = service.import_file(sample_csv_file)

        firstname_col = next(
            col for col in source_file.columns if col.name == "FirstName"
        )
        assert len(firstname_col.sample_values) > 0
        assert "John" in firstname_col.sample_values

    def test_import_csv_with_custom_sample_size(self, sample_csv_file):
        """Test CSV import with custom sample size."""
        service = FileImportService()
        source_file = service.import_file(sample_csv_file, sample_size=2)

        # Should still read all rows for total count
        assert source_file.total_rows == 3

        # Sample values should be limited
        for col in source_file.columns:
            assert len(col.sample_values) <= 10  # Max 10 shown

    def test_import_csv_encoding_utf8(self, tmp_path):
        """Test CSV import with UTF-8 encoding."""
        csv_content = "Name,City\nJohn,New York\nJané,Paris"
        csv_file = tmp_path / "test_utf8.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        service = FileImportService()
        source_file = service.import_file(str(csv_file))

        assert source_file.encoding == "utf-8"
        assert source_file.total_rows == 2

    def test_import_csv_empty_file(self, tmp_path):
        """Test handling of empty CSV file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("", encoding="utf-8")

        service = FileImportService()
        with pytest.raises(ValueError, match="no headers"):
            service.import_file(str(csv_file))

    def test_import_csv_headers_only(self, tmp_path):
        """Test CSV with headers but no data rows."""
        csv_content = "FirstName,LastName,Email"
        csv_file = tmp_path / "headers_only.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        service = FileImportService()
        source_file = service.import_file(str(csv_file))

        assert len(source_file.columns) == 3
        assert source_file.total_rows == 0

    def test_get_preview_data(self, sample_csv_file):
        """Test getting preview data from CSV."""
        service = FileImportService()
        preview_data = service.get_preview_data(sample_csv_file, limit=2)

        assert len(preview_data) == 2
        assert "FirstName" in preview_data[0]
        assert preview_data[0]["FirstName"] == "John"

    def test_get_preview_data_limit_exceeds_rows(self, sample_csv_file):
        """Test preview when limit exceeds available rows."""
        service = FileImportService()
        preview_data = service.get_preview_data(sample_csv_file, limit=100)

        # Should return all available rows (3)
        assert len(preview_data) == 3


@pytest.mark.unit
class TestExcelImport:
    """Test suite for Excel import functionality."""

    def test_import_excel_not_implemented(self):
        """Test that Excel import raises NotImplementedError."""
        service = FileImportService()

        with pytest.raises(NotImplementedError, match="Excel import"):
            service._import_excel("test.xlsx", 100)

    def test_preview_excel_not_implemented(self):
        """Test that Excel preview raises NotImplementedError."""
        service = FileImportService()

        with pytest.raises(NotImplementedError, match="Excel preview"):
            service._preview_excel("test.xlsx", 10)
