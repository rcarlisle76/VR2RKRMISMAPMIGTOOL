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
    'keyring.backends',
    'keyring.backends.Windows',
    'keyring.backends.macOS',
    'keyring.backends.SecretService',
    'sentence_transformers',
    'sentence_transformers.models',
    'sentence_transformers.util',
    'torch',
    'transformers',
    'sklearn',
    'sklearn.metrics.pairwise',
]

# Additional hidden imports for PyQt5
hidden_imports.extend([
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
])

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
    console=False,  # Set to True if you want console window for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
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
