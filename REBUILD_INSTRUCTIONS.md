# How to Rebuild the Executable (Fixed Version)

## Problem Fixed

The `_socket` module error has been **FIXED** in the `build.spec` file. Now you just need to rebuild the executable.

## Quick Rebuild Steps

### Option 1: Using the Build Script (Recommended)

1. **Open Command Prompt or PowerShell**
   ```cmd
   cd C:\Users\robert.carlisle\Desktop\MigrationTool\VR2RKRMISMAPMIGTOOL
   ```

2. **Run the build script**
   ```cmd
   python build.py
   ```

   Or if that doesn't work:
   ```cmd
   py build.py
   ```

3. **Wait for completion** (5-10 minutes)
   - Script will automatically install PyInstaller if needed
   - Will clean old builds
   - Will create new executable with fixed configuration

4. **Test the new executable**
   ```cmd
   cd dist\VentivToRiskonnectMigrationTool
   VentivToRiskonnectMigrationTool.exe
   ```

### Option 2: Manual Rebuild

If the build script doesn't work:

1. **Ensure you're in a Python environment with dependencies**
   ```cmd
   cd C:\Users\robert.carlisle\Desktop\MigrationTool\VR2RKRMISMAPMIGTOOL

   # If you have a virtual environment, activate it first:
   venv\Scripts\activate
   ```

2. **Install PyInstaller** (if not already installed)
   ```cmd
   pip install pyinstaller
   ```

3. **Clean old build**
   ```cmd
   rmdir /s /q build
   rmdir /s /q dist
   ```

4. **Build new executable**
   ```cmd
   pyinstaller build.spec --clean --noconfirm
   ```

5. **Test**
   ```cmd
   cd dist\VentivToRiskonnectMigrationTool
   VentivToRiskonnectMigrationTool.exe
   ```

## What Was Fixed

The `build.spec` file now includes:

```python
hidden_imports = [
    '_socket',      # ← FIXED: Was missing, causing the error
    '_ssl',         # ← ADDED: SSL/TLS support
    '_hashlib',     # ← ADDED: Cryptographic functions
    '_bz2',         # ← ADDED: Compression
    '_lzma',        # ← ADDED: Compression
    'select',       # ← ADDED: I/O operations
    'multiprocessing',  # ← ADDED: Better multiprocessing support
    # ... and more
]
```

Also, **console mode is now enabled** for easier debugging:
- You'll see a console window when the app starts
- Error messages will appear in the console
- Makes troubleshooting much easier

## Expected Result After Rebuild

✅ **No _socket error**
✅ **Console window appears** (showing startup logs)
✅ **Login window appears** shortly after
✅ **Application works normally**

## Testing Checklist

After rebuilding, verify:

- [ ] Executable launches without errors
- [ ] Console window shows log messages (no errors in red)
- [ ] Login window appears
- [ ] Can enter credentials
- [ ] Can connect to Salesforce

## If You Still Get Errors

### Check Console Output

The console window will show exactly what's wrong. Look for:

```
ModuleNotFoundError: No module named 'XXX'
```

If you see this:
1. Note the missing module name
2. Add it to `build.spec` in the `hidden_imports` list
3. Rebuild again

### Common Missing Modules

If you see errors for these, add them to `hidden_imports`:

```python
'_ctypes',      # For ctypes library
'_decimal',     # For decimal numbers
'_asyncio',     # For async operations
'_queue',       # For queue operations
'_json',        # For JSON parsing
'_uuid',        # For UUID generation
```

## Production Build (No Console Window)

Once everything works perfectly:

1. **Edit build.spec**
   ```python
   console=False,  # Change True to False
   ```

2. **Rebuild**
   ```cmd
   pyinstaller build.spec --clean --noconfirm
   ```

3. **Test**
   - Should work exactly the same
   - No console window this time
   - Cleaner user experience

## Troubleshooting Build Errors

### "Python not found"

Make sure Python is installed and in your PATH:
```cmd
python --version
```

Should show Python 3.9 or higher.

### "PyInstaller not found"

Install it:
```cmd
pip install pyinstaller
```

### "Permission denied" during clean

Close any running instances of the executable, then retry.

### Build takes forever

First build can take 5-10 minutes because:
- PyInstaller analyzes all dependencies
- Sentence-transformers models are large (~500MB)
- Compiling with UPX compression

Be patient! Subsequent builds are faster.

## Need Help?

If you continue to have issues:

1. **Check the console output** carefully
2. **Look for ModuleNotFoundError** messages
3. **Add missing modules** to build.spec hidden_imports
4. **Try rebuilding** with those additions

The build.spec file is now properly configured for all the known dependencies. The rebuild should work!
