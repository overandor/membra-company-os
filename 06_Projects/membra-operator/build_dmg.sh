#!/usr/bin/env zsh
# Build MEMBRA Operator macOS DMG via PyInstaller
set -e

cd "$(dirname "$0")"
APP_NAME="MEMBRA Operator"
BUNDLE="dist/${APP_NAME}.app"
DMG_NAME="MEMBRA-Operator-0.1.0.dmg"
VOL_NAME="MEMBRA Operator Install"

echo "[1/4] Installing deps..."
pip install -r requirements.txt --quiet

echo "[2/4] Building app with PyInstaller..."
pyinstaller main.py \
  --name "${APP_NAME}" \
  --windowed \
  --onedir \
  --osx-bundle-identifier "ai.membra.operator" \
  --add-data "voice_interface.py:." \
  --add-data "windsurf_monitor.py:." \
  --add-data "llm_bridge.py:." \
  --add-data "memory_store.py:." \
  --add-data "tools.py:." \
  --add-data "coordinator.py:." \
  --hidden-import tkinter \
  --hidden-import sqlite3 \
  --hidden-import uuid \
  --hidden-import json \
  --hidden-import subprocess \
  --hidden-import pathlib \
  --hidden-import threading \
  --hidden-import datetime \
  --hidden-import requests \
  --hidden-import certifi \
  --exclude-module torch \
  --exclude-module torchvision \
  --exclude-module torchaudio \
  --exclude-module scipy \
  --exclude-module pandas \
  --exclude-module numpy \
  --exclude-module matplotlib \
  --exclude-module sklearn \
  --exclude-module numba \
  --exclude-module llvmlite \
  --exclude-module pyarrow \
  --exclude-module PIL \
  --exclude-module pytest \
  --exclude-module mypy \
  --exclude-module IPython \
  --exclude-module jupyter \
  --exclude-module notebook \
  --exclude-module sqlalchemy \
  --exclude-module OpenSSL \
  --clean \
  --noconfirm

echo "[3/4] Verifying bundle..."
if [ ! -d "$BUNDLE" ]; then
    echo "ERROR: Bundle not found at $BUNDLE"
    exit 1
fi

echo "[3.5/4] Signing bundle with network entitlements..."
codesign --force --deep --sign - \
  --entitlements MEMBRA_Operator.entitlements \
  "$BUNDLE" || echo "Warning: codesign failed (non-fatal for local use)"

echo "[4/4] Creating DMG..."
rm -f "dist/$DMG_NAME"
TMP_DMG="dist/temp_membra_operator.dmg"
SIZE="1g"

hdiutil create -size "$SIZE" -volname "$VOL_NAME" -srcfolder "$BUNDLE" -ov -format UDZO "$TMP_DMG"
mv "$TMP_DMG" "dist/$DMG_NAME"

echo ""
echo "✅ Build complete: dist/$DMG_NAME"
echo "Install by dragging ${APP_NAME}.app to /Applications"
ls -lh "dist/$DMG_NAME"
