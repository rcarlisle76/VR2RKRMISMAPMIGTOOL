# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Ventiv to Riskonnect Migration Tool.

Build command:
    pyinstaller build.spec
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect data files for sentence-transformers models
sentence_transformers_datas = collect_data_files('sentence_transformers')
torch_datas = collect_data_files('torch', include_py_files=True)
transformers_datas = collect_data_files('transformers')

# Collect data files for setuptools/jaraco to fix pkg_resources issue
setuptools_datas = collect_data_files('setuptools')
jaraco_datas = collect_data_files('jaraco')

# Collect all submodules that might be loaded dynamically
hidden_imports = [
    # Critical Python built-in modules (C extensions)
    '_socket',
    '_ssl',
    '_hashlib',
    '_bz2',
    '_lzma',
    'select',

    # Multiprocessing support
    'multiprocessing',
    'multiprocessing.pool',
    'multiprocessing.managers',

    # Keyring backends
    'keyring.backends',
    'keyring.backends.Windows',
    'keyring.backends.macOS',
    'keyring.backends.SecretService',

    # AI/ML libraries
    'sentence_transformers',
    'sentence_transformers.models',
    'sentence_transformers.util',
    'torch',
    'transformers',
    'sklearn',
    'sklearn.metrics.pairwise',

    # PyQt5 modules
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtNetwork',

    # Salesforce/networking
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
]

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=sentence_transformers_datas + torch_datas + transformers_datas + setuptools_datas + jaraco_datas + [('src', 'src')],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy.distutils',
        'tcl',
        'tk',
        '_tkinter',
        'tkinter',
        'Tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VentivToRiskonnectMigrationTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Production build - no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VentivToRiskonnectMigrationTool',
)
