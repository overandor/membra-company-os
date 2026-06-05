# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for Doctor Address Verifier (Flask + web crawling + Ollama).
# This builds a single-file executable that can be used as the backend server.
#
# Usage: pyinstaller DoctorAddressVerifier.spec --noconfirm
#

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    datas=[
        ("templates", "templates"),
        ("app_bundle.py", "."),
        ("verifier.py", "."),
        ("web_crawler.py", "."),
    ],
    hiddenimports=[
        "flask",
        "jinja2",
        "markupsafe",
        "werkzeug",
        "pandas",
        "openpyxl",
        "requests",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "idna",
        "bs4",
        "lxml",
        "numpy",
        "pytz",
        "dateutil",
        "six",
        "app_bundle",
        "verifier",
        "web_crawler",
    ],
    excludes=[
        "tkinter",
        "matplotlib",
        "scipy",
        "PIL",
        "IPython",
        "notebook",
        "pytest",
    ],
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="flask_server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    target_arch=None,
)

# Also build as a macOS .app bundle (optional, for standalone use without Swift)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="DoctorAddressVerifier",
)

app = BUNDLE(
    coll,
    name="DoctorAddressVerifier.app",
    bundle_identifier="com.membra.doctor-address-verifier",
    info_plist={
        "NSPrincipalClass": "NSApplication",
        "CFBundleShortVersionString": "2.0.0",
        "LSMinimumSystemVersion": "13.0",
        "NSAppTransportSecurity": {
            "NSAllowsLocalNetworking": True,
        },
    },
)
