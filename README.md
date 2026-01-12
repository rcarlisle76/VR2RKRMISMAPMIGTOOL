# Ventiv to Riskonnect Migration Tool

A cross-platform desktop application for Salesforce data migration. This tool provides a secure, user-friendly interface for connecting to Salesforce and managing data migration tasks from Ventiv to Riskonnect.

## Features

### Phase 1 (Current)
- **Secure Authentication**: Connect to Salesforce using username, password, and security token
- **Credential Management**: Securely store credentials using OS-level keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Professional UI**: Clean, intuitive interface built with PyQt5

### Coming Soon
- Schema discovery and object introspection
- Data extraction and export
- Field mapping engine
- Data loading with bulk API
- Monitoring and reporting

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

## Installation

### 1. Clone or Download the Repository

```bash
cd "migration mapping tool and data loader"
```

### 2. Create a Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

### Development Mode

Run the application directly with Python:

```bash
python -m src.main
```

Or:

```bash
cd src
python main.py
```

## Getting Your Salesforce Security Token

To connect to Salesforce, you'll need:
1. **Username**: Your Salesforce login email
2. **Password**: Your Salesforce password
3. **Security Token**: A unique token from Salesforce

### How to Get Your Security Token:

1. Log in to Salesforce
2. Click on your profile picture (top right)
3. Select **Settings**
4. In the left sidebar, go to **Personal** → **Reset My Security Token**
5. Click **Reset Security Token**
6. Check your email for the new security token
7. Copy the token from the email

**Note**: If you don't see the "Reset My Security Token" option, your organization may have IP restrictions enabled. In that case, you may not need a security token when connecting from your office network.

## Using the Application

### First Time Login

1. Launch the application
2. Enter your Salesforce username (email)
3. Enter your password
4. Enter your security token
5. Select the correct instance URL:
   - `https://login.salesforce.com` for production/developer orgs
   - `https://test.salesforce.com` for sandbox orgs
6. Check "Remember my credentials" to save credentials securely
7. Click "Connect to Salesforce"

### Subsequent Logins

If you checked "Remember my credentials":
1. Enter your username
2. Password and token will auto-fill from secure storage
3. Click "Connect to Salesforce"

## Project Structure

```
migration-tool/
├── src/
│   ├── main.py                      # Application entry point
│   ├── core/                        # Core infrastructure
│   │   ├── config.py                # Configuration management
│   │   ├── credentials.py           # Secure credential storage
│   │   └── logging_config.py        # Logging setup
│   ├── connectors/                  # Data source connectors
│   │   ├── base.py                  # Base connector interface
│   │   └── salesforce/              # Salesforce connector
│   ├── models/                      # Data models
│   ├── services/                    # Business logic
│   │   └── auth_service.py          # Authentication service
│   ├── ui/                          # User interface
│   │   ├── login_window.py          # Login window
│   │   └── presenters/              # UI presenters (MVP pattern)
│   └── utils/                       # Utilities
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
└── README.md                        # This file
```

## Architecture

This application follows the **Model-View-Presenter (MVP)** pattern:

- **Model**: Business logic and data access (`services/`, `connectors/`, `models/`)
- **View**: PyQt5 UI components (`ui/*.py`)
- **Presenter**: Orchestration layer (`ui/presenters/`)

### Key Benefits:
- **Testable**: Business logic separated from UI
- **Maintainable**: Clear separation of concerns
- **Extensible**: Easy to add new features and data sources

## Configuration

Application configuration is stored at:
- **Windows**: `C:\Users\{username}\.salesforce_migration_tool\config.json`
- **macOS**: `/Users/{username}/.salesforce_migration_tool/config.json`
- **Linux**: `/home/{username}/.salesforce_migration_tool/config.json`

Logs are stored in the same directory under the `logs/` folder.

## Security

### Credential Storage
- Credentials are stored using OS-level secure storage:
  - **Windows**: Credential Manager
  - **macOS**: Keychain
  - **Linux**: Secret Service (e.g., GNOME Keyring)
- Passwords and tokens are never stored in plain text
- Session data is kept in memory only

### Logging
- Sensitive data (passwords, tokens) are never logged
- Logs contain only usernames and connection status
- Error logs are stored separately

## Troubleshooting

### "Invalid username, password, or security token"
- Double-check your credentials
- Ensure your security token is current (reset if needed)
- Verify you're using the correct instance URL (login vs test)

### "Connection failed"
- Check your internet connection
- Verify the instance URL is correct
- Check if Salesforce is accessible from your network

### Credentials not auto-filling
- Make sure you checked "Remember my credentials" during first login
- Try entering your username again
- On Linux, ensure you have a keyring daemon running (e.g., gnome-keyring)

### Application won't start
- Verify Python 3.9+ is installed: `python --version`
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check the logs at `~/.salesforce_migration_tool/logs/migration_tool.log`

## Development

### Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

### Code Formatting

```bash
black src/
```

### Type Checking

```bash
mypy src/
```

## Building a Standalone Executable

You can package the application into a standalone executable that users can run without installing Python.

### Prerequisites for Building

```bash
# Install development dependencies (includes PyInstaller)
pip install -r requirements-dev.txt
```

### Build the Executable

**Option 1: Using the build script (recommended)**

```bash
python build.py
```

This script will:
- Check for PyInstaller and install if needed
- Clean previous builds
- Build the executable using PyInstaller
- Display the output location

**Option 2: Using PyInstaller directly**

```bash
pyinstaller build.spec --clean --noconfirm
```

### Output

The executable and all necessary files will be in:
```
dist/VentivToRiskonnectMigrationTool/
├── VentivToRiskonnectMigrationTool.exe  (Windows)
├── VentivToRiskonnectMigrationTool      (macOS/Linux)
└── [supporting files and libraries]
```

### Distribution

**Important**: Users need the entire `VentivToRiskonnectMigrationTool` folder, not just the .exe file.

To distribute:
1. Zip the entire `dist/VentivToRiskonnectMigrationTool/` folder
2. Send the zip file to users
3. Users extract and run the executable

### Build Notes

- **First build takes longer** (~5-10 minutes) due to sentence-transformers model collection
- **Executable size**: ~500-800 MB (includes PyQt5, PyTorch, and AI models)
- **No Python installation required** by end users
- **All dependencies bundled** in the output folder

## License

TBD

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs at `~/.salesforce_migration_tool/logs/`
3. [Create an issue](link-to-your-repo/issues) with log details

## Roadmap

- [x] Phase 1: Secure authentication and connection management
- [ ] Phase 2: Schema discovery and object introspection
- [ ] Phase 3: Data extraction and export
- [ ] Phase 4: Visual field mapping
- [ ] Phase 5: Data loading with bulk API
- [ ] Phase 6: Monitoring and reporting dashboard

---

**Version**: 1.0.0 (Phase 1)
**Last Updated**: 2025-12-30
