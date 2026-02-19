# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for handbrake-agent

from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        *copy_metadata('handbrake-agent'),
        *copy_metadata('tqdm'),
    ],
    hiddenimports=[
        # cli.flags submodules
        'cli.flags.auto_loop',
        'cli.flags.batch',
        'cli.flags.ffmpeg',
        'cli.flags.model',
        'cli.flags.params_file',
        'cli.flags.preview',
        'cli.flags.prompt',
        'cli.flags.verify',
        'cli.flags.version',
        'cli.flags.vmaf',
        'cli.flags.vmaf_feedback',
        'cli.flags.yes',
        # tools submodules
        'tools.ai_analyzer',
        'tools.quality',
        'tools.transcoder',
        'tools.video_info',
        # importlib.metadata for version reading
        'importlib.metadata',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='handbrake-agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
