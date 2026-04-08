# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec per AllertAllocator.exe
#
# Uso:
#   pyinstaller desktop/desktop.spec --clean --noconfirm
#
# Output: dist/AllertAllocator.exe  (singolo file, ~100-150 MB)
#
# Nota: eseguire DOPO aver compilato il frontend React:
#   cd frontend && npm run build

from pathlib import Path

# SPECPATH è impostato da PyInstaller alla directory del file .spec
ROOT = Path(SPECPATH).parent   # root del repo allert-allocator

HIDDEN = [
    # ── uvicorn ──────────────────────────────────────────────────────────────
    "uvicorn",
    "uvicorn.main",
    "uvicorn.config",
    "uvicorn.server",
    "uvicorn.logging",
    "uvicorn.importer",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.http.flow_control",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.middleware",
    "uvicorn.middleware.proxy_headers",
    "uvicorn.middleware.asgi2",
    # ── h11 (parser HTTP/1.1, dipendenza diretta uvicorn) ────────────────────
    "h11",
    "h11._readers",
    "h11._writers",
    "h11._events",
    "h11._connection",
    "h11._state",
    "h11._util",
    # ── anyio (async backend per FastAPI/Starlette) ───────────────────────────
    "anyio",
    "anyio._backends._asyncio",
    "anyio._core._eventloop",
    "anyio._core._sockets",
    "anyio._core._tasks",
    "anyio._core._streams",
    "anyio._core._synchronization",
    "anyio._core._fileio",
    "anyio.from_thread",
    "anyio.abc",
    "anyio.streams.memory",
    # ── starlette ─────────────────────────────────────────────────────────────
    "starlette.routing",
    "starlette.requests",
    "starlette.responses",
    "starlette.staticfiles",
    "starlette.middleware.cors",
    "starlette.middleware.base",
    "starlette.middleware.exceptions",
    "starlette.datastructures",
    "starlette.background",
    "starlette.concurrency",
    "starlette.convertors",
    "starlette.formparsers",
    "starlette.types",
    # ── fastapi ───────────────────────────────────────────────────────────────
    "fastapi",
    "fastapi.routing",
    "fastapi.middleware.cors",
    "fastapi.staticfiles",
    "fastapi.responses",
    "fastapi.encoders",
    "fastapi.dependencies.utils",
    "fastapi.exception_handlers",
    # ── pydantic v2 ───────────────────────────────────────────────────────────
    "pydantic",
    "pydantic.main",
    "pydantic._internal._model_construction",
    "pydantic._internal._generate_schema",
    "pydantic._internal._config",
    "pydantic_core",
    "pydantic_core._pydantic_core",
    "pydantic_core.core_schema",
    # ── python-multipart (file upload) ────────────────────────────────────────
    "multipart",
    "multipart.multipart",
    # ── pandas ────────────────────────────────────────────────────────────────
    "pandas",
    "pandas.io.excel._openpyxl",
    "pandas.io.formats.excel",
    "pandas._libs.tslibs.np_datetime",
    "pandas._libs.tslibs.nattype",
    "pandas._libs.tslibs.timestamps",
    "pandas._libs.tslibs.timedeltas",
    "pandas._libs.missing",
    "pandas._libs.hashtable",
    "pandas._libs.lib",
    "pandas._libs.index",
    "pandas._libs.skiplist",
    # ── openpyxl ──────────────────────────────────────────────────────────────
    "openpyxl",
    "openpyxl.styles",
    "openpyxl.utils",
    "openpyxl.utils.dataframe",
    "openpyxl.writer.excel",
    "et_xmlfile",
    # ── sniffio (richiesto da anyio) ──────────────────────────────────────────
    "sniffio",
    # ── stdlib potenzialmente esclusi in onefile ──────────────────────────────
    "email.mime.multipart",
    "email.mime.text",
    "email.mime.base",
    "email.base64mime",
    "email.quoprimime",
]

a = Analysis(
    [str(ROOT / "desktop" / "desktop.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # (sorgente_sul_disco,  percorso_relativo_dentro_il_bundle)
        (str(ROOT / "frontend" / "dist"), "frontend/dist"),
        (str(ROOT / "backend"),           "backend"),
    ],
    hiddenimports=HIDDEN,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",           # tolto per ridurre dimensioni (usato solo come fallback errore)
        "matplotlib",
        "scipy",
        "PIL",
        "IPython",
        "notebook",
        "pytest",
        "setuptools",
        "distutils",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AllertAllocator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # UPX disabilitato: riduce falsi positivi antivirus
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # nessuna finestra nera cmd
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=str(ROOT / "desktop" / "icon.ico"),   # decommentare se si aggiunge un'icona
)
