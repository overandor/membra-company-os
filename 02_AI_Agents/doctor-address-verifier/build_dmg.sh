#!/bin/bash
#
# build_dmg.sh — Build a macOS .dmg for the Doctor Address Verifier
#
# This script builds a self-contained macOS application that bundles:
#   - A native Swift wrapper (AppKit + WKWebView)
#   - The Flask verification server (via PyInstaller)
#   - Ollama binary for local LLM inference
#
# Run on macOS:
#   chmod +x build_dmg.sh
#   ./build_dmg.sh
#
# Prerequisites:
#   - macOS 13.0+ (Ventura or later)
#   - Xcode Command Line Tools (xcode-select --install)
#   - Python 3.10+ (python3 on PATH)
#   - Internet connection (to download Ollama + pip packages)
#
# Output: dist/DoctorAddressVerifier.dmg
#

set -euo pipefail

APP_NAME="DoctorAddressVerifier"
BUNDLE_ID="com.membra.doctor-address-verifier"
VERSION="2.0.0"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
VOLUME_NAME="Doctor Address Verifier"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SWIFT_PROJECT="DoctorAddressVerifierApp"

echo "=========================================="
echo " Doctor Address Verifier — DMG Builder v2 "
echo " (Swift + Flask + Ollama)                 "
echo "=========================================="
echo ""

# ── Pre-flight checks ───────────────────────────────────────────────

if [[ "$(uname)" != "Darwin" ]]; then
    echo "ERROR: This script must be run on macOS."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+ from https://python.org"
    exit 1
fi

if ! command -v swift &> /dev/null; then
    echo "ERROR: Swift not found. Install Xcode Command Line Tools:"
    echo "       xcode-select --install"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
SWIFT_VERSION=$(swift --version 2>&1 | head -1)
echo "Python: ${PYTHON_VERSION}"
echo "Swift:  ${SWIFT_VERSION}"
echo ""

cd "$SCRIPT_DIR"

# Detect architecture
ARCH=$(uname -m)
echo "Architecture: ${ARCH}"
echo ""

# ── Step 1: Build Flask server binary with PyInstaller ──────────────

echo "[1/5] Building Flask server with PyInstaller..."

if [ -d "build_venv" ]; then
    rm -rf build_venv
fi
python3 -m venv build_venv
source build_venv/bin/activate

echo "  Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt pyinstaller > /dev/null 2>&1

echo "  Running PyInstaller..."
rm -rf build dist

# Build a --onefile console binary for the Flask server
pyinstaller \
    --name flask_server \
    --onefile \
    --console \
    --add-data "templates:templates" \
    --add-data "verifier.py:." \
    --add-data "web_crawler.py:." \
    --add-data "app_bundle.py:." \
    --hidden-import flask \
    --hidden-import jinja2 \
    --hidden-import markupsafe \
    --hidden-import werkzeug \
    --hidden-import pandas \
    --hidden-import openpyxl \
    --hidden-import requests \
    --hidden-import urllib3 \
    --hidden-import certifi \
    --hidden-import charset_normalizer \
    --hidden-import idna \
    --hidden-import bs4 \
    --hidden-import lxml \
    --hidden-import numpy \
    --hidden-import pytz \
    --hidden-import dateutil \
    --hidden-import six \
    --hidden-import app_bundle \
    --hidden-import verifier \
    --hidden-import web_crawler \
    --exclude-module tkinter \
    --exclude-module matplotlib \
    --exclude-module scipy \
    --exclude-module PIL \
    --exclude-module IPython \
    --exclude-module notebook \
    --exclude-module pytest \
    --noconfirm \
    launcher.py 2>&1 | tail -5

if [ ! -f "dist/flask_server" ]; then
    echo "ERROR: PyInstaller failed to produce flask_server binary."
    deactivate
    exit 1
fi

FLASK_SIZE=$(du -sh "dist/flask_server" | cut -f1)
echo "  Flask server binary: ${FLASK_SIZE}"

deactivate

# ── Step 2: Download Ollama binary ──────────────────────────────────

echo ""
echo "[2/5] Downloading Ollama binary..."

OLLAMA_BIN="dist/ollama"
if [ -f "$OLLAMA_BIN" ]; then
    echo "  Using cached Ollama binary."
else
    # Determine download URL based on architecture
    if [[ "$ARCH" == "arm64" ]]; then
        OLLAMA_URL="https://github.com/ollama/ollama/releases/latest/download/ollama-darwin"
    else
        OLLAMA_URL="https://github.com/ollama/ollama/releases/latest/download/ollama-darwin"
    fi

    echo "  Downloading from ${OLLAMA_URL}..."
    curl -L -o "$OLLAMA_BIN" "$OLLAMA_URL" 2>&1 | tail -3

    if [ ! -f "$OLLAMA_BIN" ]; then
        echo "WARNING: Failed to download Ollama. The app will run in rule-based mode only."
        echo "         You can manually download ollama and place it at: dist/ollama"
    else
        chmod +x "$OLLAMA_BIN"
        OLLAMA_SIZE=$(du -sh "$OLLAMA_BIN" | cut -f1)
        echo "  Ollama binary: ${OLLAMA_SIZE}"
    fi
fi

# ── Step 3: Build Swift wrapper app ─────────────────────────────────

echo ""
echo "[3/5] Building Swift wrapper app..."

cd "$SWIFT_PROJECT"
swift build -c release 2>&1 | tail -3

SWIFT_BIN=".build/release/${APP_NAME}"
if [ ! -f "$SWIFT_BIN" ]; then
    echo "ERROR: Swift build failed. Check errors above."
    exit 1
fi
echo "  Swift binary built successfully."
cd "$SCRIPT_DIR"

# ── Step 4: Assemble .app bundle ────────────────────────────────────

echo ""
echo "[4/5] Assembling ${APP_NAME}.app..."

APP_DIR="dist/${APP_NAME}.app"
CONTENTS="${APP_DIR}/Contents"
MACOS="${CONTENTS}/MacOS"
RESOURCES="${CONTENTS}/Resources"

rm -rf "$APP_DIR"
mkdir -p "$MACOS" "$RESOURCES/bin" "$RESOURCES/templates"

# Copy Swift binary
cp "${SWIFT_PROJECT}/.build/release/${APP_NAME}" "$MACOS/${APP_NAME}"
chmod +x "$MACOS/${APP_NAME}"

# Copy Flask server binary
cp "dist/flask_server" "$RESOURCES/bin/flask_server"
chmod +x "$RESOURCES/bin/flask_server"

# Copy Ollama binary (if downloaded)
if [ -f "dist/ollama" ]; then
    cp "dist/ollama" "$RESOURCES/bin/ollama"
    chmod +x "$RESOURCES/bin/ollama"
fi

# Copy Python source files (for dev fallback)
cp app_bundle.py "$RESOURCES/"
cp verifier.py "$RESOURCES/"
cp web_crawler.py "$RESOURCES/"

# Copy templates
cp templates/index.html "$RESOURCES/templates/"

# Create Info.plist
cat > "$CONTENTS/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>${BUNDLE_ID}</string>
    <key>CFBundleName</key>
    <string>Doctor Address Verifier</string>
    <key>CFBundleDisplayName</key>
    <string>Doctor Address Verifier</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>LSUIElement</key>
    <false/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsLocalNetworking</key>
        <true/>
    </dict>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
EOF

APP_SIZE=$(du -sh "$APP_DIR" | cut -f1)
echo "  ${APP_NAME}.app assembled (${APP_SIZE})"

# ── Step 5: Create the DMG ──────────────────────────────────────────

echo ""
echo "[5/5] Creating ${DMG_NAME}..."

rm -f "dist/${DMG_NAME}"

# Create staging directory
DMG_STAGING="dist/dmg_staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"

# Copy the .app bundle
cp -R "$APP_DIR" "$DMG_STAGING/"

# Add Applications symlink for drag-to-install
ln -s /Applications "$DMG_STAGING/Applications"

# Add README
cat > "$DMG_STAGING/README.txt" <<'READMEEOF'
Doctor Address Verifier v2.0
============================

A healthcare provider address verification tool with:
  - NPPES Registry lookups
  - Live web crawling (Doximity, Healthgrades, WebMD, hospital pages)
  - Ollama LLM for intelligent analysis of ambiguous evidence
  - Native macOS interface

INSTALLATION:
  Drag "DoctorAddressVerifier.app" into the Applications folder.

FIRST LAUNCH:
  1. Double-click DoctorAddressVerifier in Applications
  2. macOS may warn about an unidentified developer
     → Right-click the app → Open → Open to bypass
  3. The app will start Ollama and the verification server
  4. A web UI will appear in the app window

OLLAMA MODEL SETUP:
  On first use, you may need to pull a model. Open Terminal and run:
    /Applications/DoctorAddressVerifier.app/Contents/Resources/bin/ollama pull llama3.1
  Or pull a smaller model for faster inference:
    /Applications/DoctorAddressVerifier.app/Contents/Resources/bin/ollama pull llama3.2:1b

DATA STORAGE:
  Uploads and results are saved to:
    ~/Documents/DoctorAddressVerifier/

  Ollama models are stored in:
    ~/Documents/DoctorAddressVerifier/models/

TO UNINSTALL:
  1. Delete DoctorAddressVerifier.app from Applications
  2. Optionally delete ~/Documents/DoctorAddressVerifier/
READMEEOF

# Create temporary DMG
TMP_DMG="dist/tmp.dmg"
rm -f "$TMP_DMG"
hdiutil detach "/Volumes/${APP_NAME}" 2>/dev/null || true

hdiutil create \
    -srcfolder "$DMG_STAGING" \
    -volname "$VOLUME_NAME" \
    -fs HFS+ \
    -size 500m \
    "$TMP_DMG" \
    -ov 2>&1 | grep -v "^$"

# Mount, add Applications symlink (it's already in staging, but ensure it works)
hdiutil attach "$TMP_DMG" -nobrowse 2>/dev/null || true
hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true

# Compress final DMG
hdiutil convert "$TMP_DMG" -format UDZO -o "dist/${DMG_NAME}" 2>&1 | grep -v "^$"
rm -f "$TMP_DMG"

# Clean up staging
rm -rf "$DMG_STAGING"

if [ ! -f "dist/${DMG_NAME}" ]; then
    echo "ERROR: Failed to create DMG."
    exit 1
fi

DMG_SIZE=$(du -sh "dist/${DMG_NAME}" | cut -f1)

# ── Cleanup ─────────────────────────────────────────────────────────

echo ""
echo "Cleaning up build artifacts..."
rm -rf build_venv build dist/flask_server
# Keep dist/ollama cached for future builds

echo ""
echo "=========================================="
echo " BUILD COMPLETE"
echo "=========================================="
echo ""
echo "  Output:  dist/${DMG_NAME} (${DMG_SIZE})"
echo "  Version: ${VERSION}"
echo ""
echo "  Contents:"
echo "    - ${APP_NAME}.app (Swift + WKWebView)"
echo "    - Flask verification server (PyInstaller)"
if [ -f "dist/ollama" ]; then
echo "    - Ollama binary (bundled for LLM inference)"
else
echo "    - Ollama: NOT bundled (download failed)"
fi
echo "    - Web crawlers: Doximity, Healthgrades, WebMD"
echo ""
echo "  To install:"
echo "    1. Open dist/${DMG_NAME}"
echo "    2. Drag DoctorAddressVerifier to Applications"
echo "    3. Right-click → Open (first time only)"
echo ""
echo "  To pull an Ollama model after install:"
echo "    /Applications/${APP_NAME}.app/Contents/Resources/bin/ollama pull llama3.1"
echo ""
