# Salesforce Migration Mapping Tool - User Manual

**Version 1.0**

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation & Setup](#2-installation--setup)
3. [Getting Started](#3-getting-started)
4. [Main Interface Overview](#4-main-interface-overview)
5. [Object Browser](#5-object-browser)
6. [Field Details](#6-field-details)
7. [Relationships Tab](#7-relationships-tab)
8. [Data Preview](#8-data-preview)
9. [Field Usage Reports](#9-field-usage-reports)
10. [Mapping Fields](#10-mapping-fields)
11. [Auto-Mapping Features](#11-auto-mapping-features)
12. [Loading Data to Salesforce](#12-loading-data-to-salesforce)
13. [Saving & Loading Mappings](#13-saving--loading-mappings)
14. [Logs](#14-logs)
15. [Keyboard Shortcuts](#15-keyboard-shortcuts)
16. [Troubleshooting](#16-troubleshooting)
17. [Appendix: Configuration Files](#17-appendix-configuration-files)

---

## 1. Introduction

The Salesforce Migration Mapping Tool is a desktop application designed to simplify the process of migrating data from CSV files into Salesforce. It provides:

- **Visual field mapping** between source CSV columns and Salesforce fields
- **Intelligent auto-mapping** using fuzzy matching, semantic analysis, and optional AI
- **Data validation** to ensure values match Salesforce field requirements
- **Field usage analysis** to understand your source data quality
- **Batch data loading** with progress tracking and error reporting

### Key Benefits

- **Reduce manual effort**: Auto-mapping can match 80-95% of fields automatically
- **Prevent errors**: Validates data types, picklist values, and required fields before loading
- **Understand your data**: Field usage reports show null rates, distinct values, and data quality
- **Track progress**: Real-time progress indicators during data loads
- **Save your work**: Export and import mapping configurations for reuse

---

## 2. Installation & Setup

### System Requirements

- Windows 10/11, macOS 10.14+, or Linux
- Python 3.8 or higher
- Internet connection for Salesforce API access

### Installation Steps

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the application**:
   ```bash
   python -m src.main
   ```

   > **Important**: Always run with `python -m src.main`, not `python src/main.py`

### Optional: AI-Enhanced Mapping

For semantic matching (free, runs locally):
```bash
pip install sentence-transformers
```

For LLM-based mapping (requires API key):
- See `AI_MAPPING_GUIDE.md` for Claude API setup
- Configure your API key in the application settings

---

## 3. Getting Started

### Logging In

1. Launch the application
2. Enter your Salesforce credentials:
   - **Email**: Your Salesforce username
   - **Password**: Your Salesforce password
   - **Security Token**: Your Salesforce security token (see below)
   - **Instance URL**: Usually `https://login.salesforce.com` (or sandbox URL)

3. Optionally check **Remember credentials** to save for future sessions
4. Click **Login**

### Getting Your Security Token

1. Log into Salesforce
2. Click your profile icon → **Settings**
3. Go to **Personal** → **Reset My Security Token**
4. Click **Reset Security Token**
5. Check your email for the new token

> **Note**: The security token is required unless your IP is whitelisted in Salesforce.

### Credential Security

Your credentials are stored securely using your operating system's credential manager:
- **Windows**: Windows Credential Manager
- **macOS**: Keychain
- **Linux**: GNOME Keyring / Secret Service

Passwords are never stored in plain text or log files.

---

## 4. Main Interface Overview

After logging in, you'll see the main window with two panels:

```
+------------------+----------------------------------------+
|                  |                                        |
|  Object List     |           Object Detail Panel          |
|  (Left Panel)    |                                        |
|                  |  +----------------------------------+  |
|  - Search box    |  | Fields | Relations | Preview |   |  |
|  - Filter options|  | Map Fields | Field Usage | Logs |  |
|  - Object list   |  +----------------------------------+  |
|                  |                                        |
+------------------+----------------------------------------+
|                    Status Bar                             |
+-----------------------------------------------------------+
```

### Left Panel: Object Browser
Lists all Salesforce objects you can migrate data to.

### Right Panel: Object Details
Shows details for the selected object across multiple tabs:
- **Fields**: View all fields and their properties
- **Relationships**: Record types, page layouts, and related objects
- **Preview**: View sample data from Salesforce
- **Map Fields**: Import CSV and map columns to fields
- **Field Usage**: Import and view data quality reports
- **Logs**: View application logs for debugging

### Status Bar
Shows your current connection status (e.g., "Connected as user@example.com")

---

## 5. Object Browser

The left panel displays all Salesforce objects available for data import.

### Searching Objects

Type in the search box to filter objects by name. The search matches both:
- Display labels (e.g., "Account")
- API names (e.g., "Account", "Custom_Object__c")

### Filtering Objects

Use the checkboxes to filter the list:
- **Show Standard Objects**: Built-in Salesforce objects (Account, Contact, etc.)
- **Show Custom Objects**: Objects ending in `__c`

### Object Display

- **Standard objects**: Displayed in black text
- **Custom objects**: Displayed in blue text
- **Object count**: Shows total with breakdown (e.g., "52 objects (48 standard, 4 custom)")

### Selecting an Object

Click any object to view its details in the right panel. The selected object will be highlighted.

### Refreshing the Object List

- Press **F5** or use **Tools → Refresh Objects** to reload the list from Salesforce

---

## 6. Field Details

The **Fields** tab shows all fields for the selected Salesforce object.

### Field Table

| Column | Description |
|--------|-------------|
| Field Name | Display label (bold if required) |
| API Name | Technical name used in API calls |
| Type | Field data type (string, reference, picklist, etc.) |
| Length | Maximum length for text/number fields |
| Required | Checkmark if field must have a value |
| Updateable | Checkmark if field can be updated after creation |
| Createable | Checkmark if field can be set during record creation |

### Type Color Coding

- **Blue**: Reference/lookup fields (link to other objects)
- **Green**: Date and datetime fields
- **Black**: All other field types

### Field Detail Panel

Click any field to see detailed information on the right:

- **API Name**: The technical field name
- **Type**: Full data type description
- **Length**: Maximum characters/digits allowed
- **Required**: Yes (red) or No
- **Createable**: Whether you can set this during insert
- **Updateable**: Whether you can modify this after creation
- **Relationship Name**: For lookups, the relationship query name
- **References**: For lookups, which objects this field can reference
- **Picklist Values**: For picklist fields, all valid values (bulleted list)

---

## 7. Relationships Tab

The **Relationships** tab provides information about record types and object relationships.

### Record Type to Page Layout Mapping

Shows which page layout is assigned to each record type:

| Record Type | Page Layout |
|-------------|-------------|
| Business Account | Business Account Layout |
| Person Account | Person Account Layout |

Click a row to filter the Fields tab to show only fields on that layout.

### Field Relationships

Lists all lookup and master-detail relationship fields:

| Relationship | Type | Referenced Object | Relationship Name |
|--------------|------|-------------------|-------------------|
| AccountId | Lookup | Account | Account |
| ParentId | Master-Detail | Account | Parent |

### Clearing Filters

After selecting a page layout, click **Clear Filter** to show all fields again.

---

## 8. Data Preview

The **Preview** tab lets you view sample records from Salesforce.

### Loading Sample Data

1. Select a **Record Type** from the dropdown (or "All Record Types")
2. Click **Load Sample Data**
3. The table displays up to 50 sample records

### Data Display

- **Column headers**: Field API names from Salesforce
- **Null values**: Shown as "(null)" in gray italic text
- **Boolean values**: Displayed as "true" or "false"
- **Lookup fields**: Show the related record's Name field

### Exporting Data

After loading data, click **Export to CSV** to save the preview to a CSV file.

---

## 9. Field Usage Reports

The **Field Usage** tab helps you understand your source data quality before migration.

### Importing a Usage Report

1. Go to the **Field Usage** tab
2. Click **Import Usage Report...**
3. Select an HTML or CSV file containing field statistics

### Supported Report Formats

**HTML Reports**: The tool parses HTML tables with field statistics. Expected columns:
- Column Name, Data Type, Max Size, Count, Distinct, Nulls, Min, Max, Sum, Avg

**CSV Reports**: Standard CSV with flexible column headers:
- Supports variations like "column_name", "Column Name", "field_name"
- Auto-maps columns based on content

### Viewing Usage Data

After import, the tab displays:

**Left Panel - Table List**:
- All tables/objects found in the report
- Click a table to view its field statistics

**Right Panel - Field Statistics**:

| Column | Description |
|--------|-------------|
| Field Name | Source column name |
| Type | Detected data type |
| Max Size | Maximum value length |
| Count | Number of non-null values |
| Distinct | Number of unique values |
| Null % | Percentage of null/empty values |
| Min | Minimum value |
| Max | Maximum value |

### Null Percentage Highlighting

- **Red background**: >50% null (high concern)
- **Orange background**: >20% null (moderate concern)

### Auto-Matching with Source Files

When you import a CSV file in the Map Fields tab, the tool automatically tries to match it with a table in your usage report by:
1. Matching the filename to a table name
2. Comparing column names between the CSV and report tables
3. Finding the best match based on column overlap

When matched, the Source File Panel shows enhanced data including Count and Distinct columns.

---

## 10. Mapping Fields

The **Map Fields** tab is where you connect your source CSV columns to Salesforce fields.

### Step 1: Import Your Source File

1. Go to the **Map Fields** tab
2. Click **Import CSV** in the left panel
3. Select your CSV file
4. The file is parsed and columns are displayed

### Source File Panel (Left)

Shows information about your imported CSV:

| Column | Description |
|--------|-------------|
| Column Name | Header name from CSV |
| Type | Auto-detected type (string, number, date, boolean) |
| Null % | Percentage of empty values |
| Count | Non-null count (if usage report matched) |
| Distinct | Unique values (if usage report matched) |
| Sample | First few values from the column |

**Type Color Coding**:
- Blue: Numeric columns
- Green: Date columns
- Red: Boolean columns

### Step 2: Map Columns to Fields

The right panel shows the mapping interface:

| Column | Description |
|--------|-------------|
| Source Column | Your CSV column name |
| Null % | Percentage of null values (sortable) |
| → | Arrow indicator |
| Salesforce Field | Dropdown to select target field |
| Confidence | Match confidence percentage |
| Method | How the match was determined |
| Status | Mapping status indicator |

**To manually map a field**:
1. Find the source column row
2. Click the **Salesforce Field** dropdown
3. Type to search or scroll to find the field
4. Select the target field

**To skip a column**:
- Select **Skip** from the dropdown (the column won't be imported)

### Sorting by Null Percentage

Click the **Null %** column header to sort:
- Click once: Sort ascending (lowest null % first)
- Click again: Sort descending (highest null % first)

This helps you focus on columns with the most data.

### Download Template

Click **Download Template** to generate a CSV template with:
- All createable field names as headers
- Proper column structure for the selected object

---

## 11. Auto-Mapping Features

The tool offers multiple levels of intelligent auto-mapping.

### Basic Auto-Mapping (Fuzzy Matching)

Click **Auto-Map** to automatically match columns using fuzzy string matching:

- Compares normalized names (lowercase, no underscores/spaces)
- Strips common suffixes (__c, id, name)
- Threshold: 70% similarity required
- Method shown as "Fuzzy match"

### Semantic Matching (AI-Enhanced, Free)

If `sentence-transformers` is installed, semantic matching runs automatically:

- Uses AI embeddings to understand meaning
- Matches synonyms: phone ↔ telephone, email ↔ e-mail
- Handles abbreviations: amt ↔ amount, num ↔ number
- Threshold: 60% similarity required
- Method shown as "Semantic match"
- **Runs locally** - no internet or API key required
- **Free** - no usage costs

### LLM Mapping (Optional, API Key Required)

For the most intelligent matching, configure Claude API:

1. Get an API key from Anthropic
2. Configure in settings (see `SETUP_CLAUDE_API.md`)
3. Enable LLM mapping in configuration

LLM mapping provides:
- Context-aware analysis of all fields together
- Type validation and compatibility checking
- Explanation of why matches were made
- Method shown as "LLM match"
- Cost: ~$0.003 per mapping operation

### Mapping Algorithm Order

The tool applies mapping methods in order:

1. **Fuzzy matching** (threshold 0.7) - fast, deterministic
2. **Semantic matching** (threshold 0.6) - for low-confidence fuzzy matches
3. **LLM mapping** (threshold 0.75) - for remaining unmapped columns

Each method only runs on columns that haven't been confidently matched yet.

### Confidence Scores

Each mapping shows a confidence percentage:
- **90-100%**: Very high confidence match
- **70-89%**: Good confidence match
- **60-69%**: Moderate confidence, review recommended
- **Below 60%**: Low confidence, manual review needed

---

## 12. Loading Data to Salesforce

Once your mappings are configured, you can load data into Salesforce.

### Pre-Load Validation

Before loading, the tool checks:
- A source file is imported
- At least one mapping exists
- Required Salesforce fields are mapped (warns if missing)

### Record Type Selection

If the target object has multiple record types:

1. A dialog appears asking you to select a record type
2. Choose the record type to assign to all imported records
3. The default record type is marked with "(Default)"
4. Click **OK** to proceed or **Cancel** to abort

### Starting the Load

1. Review your mappings
2. Click **Load Data to Salesforce**
3. Confirm the operation in the dialog
4. The progress dialog appears

### Progress Dialog

During the load, you'll see:

- **Progress bar**: Visual percentage complete
- **Record count**: "X of Y records processed (P%)"
- **Success count**: Green checkmark with count
- **Failed count**: Red X with count (if any failures)
- **Status message**: Current operation
- **Error log**: Details of any failures (appears if errors occur)

### Data Transformation

The tool automatically handles:

**Type Conversions**:
- Boolean: "Yes", "No", "True", "False" → true/false
- Numbers: Removes commas and currency symbols ("1,000" → 1000, "$50" → 50.0)
- Dates: Supports multiple formats (YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY, etc.)

**Field Validation**:
- **Picklist fields**: Values must match allowed picklist values (case-insensitive)
- **Lookup fields**: Must be valid 15 or 18-character Salesforce IDs
- **Required fields**: Warns before load if not mapped
- **Read-only fields**: Automatically skipped (formulas, auto-numbers, etc.)

**Automatic Exclusions**:
- **Id field**: Auto-generated by Salesforce
- **RecordTypeId**: Uses your selection from the dialog

**Invalid Values**:
- Invalid values are set to null rather than failing the entire record
- This prevents one bad value from blocking the entire import

### Load Results

After completion:
- **All successful**: Green success message with count
- **Some failures**: Warning message with success/failure counts
- **Error details**: Expandable log showing which rows failed and why

---

## 13. Saving & Loading Mappings

Save your mapping configurations for reuse across sessions.

### Saving Mappings

1. Configure your field mappings
2. Click **Save Mapping...**
3. Choose a location and filename (.json)
4. Click **Save**

The saved file includes:
- All source column to target field mappings
- Confidence scores
- Mapping methods
- Skipped columns

### Loading Mappings

1. Import your source CSV file
2. Click **Load Mapping...**
3. Select a previously saved .json mapping file
4. Click **Open**

The mappings are applied to matching column names. Columns not in the saved mapping remain unmapped.

### Best Practices

- Save mappings after configuring a complex migration
- Use descriptive filenames (e.g., "account_migration_v2.json")
- Keep mappings organized by object and project
- Reload and verify after loading a saved mapping

---

## 14. Logs

The **Logs** tab helps you debug issues and track operations.

### Viewing Logs

1. Go to the **Logs** tab
2. Select a log file from the dropdown:
   - **migration_tool.log**: All INFO level and above messages
   - **migration_tool_error.log**: Only ERROR level messages

### Log Controls

- **Auto-refresh**: Toggle automatic log updates (every 2 seconds)
- **Refresh**: Manually reload the log display
- **Clear Display**: Clear the on-screen log (doesn't delete the file)

### Log Information

The display shows:
- Last 1000 lines of the selected log
- Line count and file size
- Timestamp, level, and message for each entry

### Log File Location

Logs are stored in:
```
~/.salesforce_migration_tool/logs/
├── migration_tool.log
└── migration_tool_error.log
```

---

## 15. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| F5 | Refresh object list |
| Ctrl+Q | Quit application |

---

## 16. Troubleshooting

### Login Issues

**"Invalid username or password"**
- Verify your Salesforce credentials
- Check that your security token is correct and not expired
- Ensure you're using the correct instance URL (production vs. sandbox)

**"IP not whitelisted"**
- Add your IP to Salesforce's trusted IP ranges, OR
- Append your security token to your password

**"Session expired"**
- Your session timed out - log in again

### Import Issues

**"Failed to parse CSV"**
- Check the file encoding (UTF-8 is recommended)
- Ensure the file has a header row
- Look for malformed rows (mismatched quotes, extra commas)

**"No columns detected"**
- Verify the file is not empty
- Check that the delimiter is comma (not semicolon or tab)

### Mapping Issues

**"No mappings suggested"**
- Column names may be very different from Salesforce fields
- Try enabling semantic matching for better results
- Map fields manually using the dropdowns

**"Field not in dropdown"**
- The field may not be createable
- Check the Fields tab to verify the field's createable status

### Data Load Issues

**"Required field missing"**
- Map all required fields before loading
- Check the Fields tab for required fields (bold names)

**"Invalid picklist value"**
- The value doesn't match any allowed picklist option
- Check valid values in the Field Detail Panel
- Values are matched case-insensitively

**"Invalid ID format"**
- Lookup fields require valid 15 or 18-character Salesforce IDs
- Verify the IDs in your source data

**"Rate limit exceeded"**
- Too many API calls in a short period
- Wait a few minutes and try again
- Consider loading in smaller batches

### Performance Issues

**"Application is slow"**
- Large CSV files (>100K rows) may take time to parse
- Consider splitting very large files
- Semantic matching downloads a ~500MB model on first use

---

## 17. Appendix: Configuration Files

### Application Configuration

Location: `~/.salesforce_migration_tool/config.json`

Contains:
- Window size and position
- Last used username (if "Remember credentials" checked)
- Last used Salesforce instance URL
- AI mapping preferences
- LLM API keys (encrypted)
- Mapping thresholds

### Credentials Storage

Credentials are stored securely in your OS credential manager:
- **Service name**: `salesforce_migration_tool`
- **Username**: Your Salesforce email
- **Password**: Your Salesforce password + security token

To clear saved credentials:
- **Windows**: Control Panel → Credential Manager → Windows Credentials
- **macOS**: Keychain Access → search for "salesforce_migration_tool"
- **Linux**: Seahorse (Passwords and Keys) application

### Log Files

Location: `~/.salesforce_migration_tool/logs/`

Files:
- `migration_tool.log` - General application log (INFO level)
- `migration_tool_error.log` - Error-only log (ERROR level)

Logs are automatically rotated to prevent excessive disk usage.

---

## Getting Help

If you encounter issues not covered in this manual:

1. Check the **Logs** tab for error details
2. Review the `migration_tool_error.log` file
3. Consult the `AI_MAPPING_GUIDE.md` for AI feature issues
4. Report issues at the project repository

---

*End of User Manual*
