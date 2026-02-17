# Build Fix for _socket Module Error

## Problem

When running the executable, you encountered:
```
ModuleNotFoundError: No module named '_socket'
```

## Root Cause

PyInstaller wasn't including critical Python C extension modules that are needed for:
- **Network operations** (`_socket`, `_ssl`)
- **Multiprocessing** (required by PyQt5 and data processing)
- **Compression** (`_bz2`, `_lzma`)
- **Security** (`_hashlib`)

These modules are built-in Python C extensions, not pure Python modules, so PyInstaller sometimes misses them during automatic dependency detection.

## Solution Applied

Updated `build.spec` to explicitly include missing modules:

```python
hidden_imports = [
    # Critical Python built-in modules (C extensions)
    '_socket',      # ← FIX: Socket operations (networking)
    '_ssl',         # ← FIX: SSL/TLS support
    '_hashlib',     # ← FIX: Cryptographic hashing
    '_bz2',         # ← FIX: Bzip2 compression
    '_lzma',        # ← FIX: LZMA compression
    'select',       # ← FIX: I/O multiplexing

    # Multiprocessing support
    'multiprocessing',
    'multiprocessing.pool',
    'multiprocessing.managers',

    # ... (rest of imports)
]
```

Also temporarily enabled console mode for easier debugging:
```python
console=True,  # Shows console window with error messages
```

## Rebuild Steps

```bash
# Clean previous build
cd C:\Users\robert.carlisle\Desktop\MigrationTool\VR2RKRMISMAPMIGTOOL

# Rebuild with fixed configuration
py -m PyInstaller build.spec --clean --noconfirm
```

## Testing After Rebuild

1. Navigate to `dist\VentivToRiskonnectMigrationTool\`
2. Double-click `VentivToRiskonnectMigrationTool.exe`
3. **Console window will appear** - this is normal (debugging mode)
4. Check for any error messages in the console
5. Login window should appear shortly

## Expected Result

✅ Application launches without `ModuleNotFoundError`
✅ Console window shows startup logs
✅ Login window appears
✅ No missing module errors

## If Still Having Issues

If you see other `ModuleNotFoundError` messages, add those modules to the `hidden_imports` list in `build.spec`.

Common missing modules:
- `_ctypes` - For ctypes library
- `_decimal` - For decimal arithmetic
- `_asyncio` - For async operations
- `_queue` - For queue operations

## Production Build

Once everything works, disable console mode for production:

```python
console=False,  # No console window in production
```

Then rebuild:
```bash
py -m PyInstaller build.spec --clean --noconfirm
```

## Technical Background

### Why This Happens

PyInstaller uses "hooks" to detect dependencies. For pure Python modules, it can easily trace imports. However:

1. **C Extensions** are compiled binaries (.pyd on Windows)
2. They're imported via the Python C API, not regular Python imports
3. PyInstaller's hooks sometimes miss these indirect dependencies
4. Especially problematic when imported conditionally or dynamically

### How _socket is Used

The error trace shows:
```
multiprocessing → context.py → reduction.py → socket.py → _socket
```

- **PyQt5** uses multiprocessing for threading
- **Multiprocessing** needs sockets for inter-process communication
- **Socket** module wraps the `_socket` C extension
- **PyInstaller** didn't detect this deep dependency chain

### Prevention for Future

When adding new dependencies that might use C extensions:
1. Test the .exe after building
2. Check console output for `ModuleNotFoundError`
3. Add missing modules to `hidden_imports`
4. Rebuild and test again

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Common PyInstaller Issues](https://github.com/pyinstaller/pyinstaller/wiki/Common-Issues)
- [Hook Configuration Guide](https://pyinstaller.org/en/stable/hooks.html)
