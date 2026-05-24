#!/bin/bash
set -e

APP_NAME="Continuous File Appraiser"
BUNDLE_ID="com.membra.file-appraiser"
VERSION="1.0.0"
BUILD_DIR="$(pwd)/build"
APP_DIR="$BUILD_DIR/${APP_NAME}.app"
DMG_NAME="Continuous_File_Appraiser_v${VERSION}.dmg"
DMG_PATH="$(pwd)/$DMG_NAME"

echo "=== Building ${APP_NAME} v${VERSION} ==="

# Clean
rm -rf "$BUILD_DIR" "$DMG_PATH"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# --- Info.plist ---
cat > "$APP_DIR/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Continuous File Appraiser</string>
    <key>CFBundleDisplayName</key>
    <string>Continuous File Appraiser</string>
    <key>CFBundleIdentifier</key>
    <string>com.membra.file-appraiser</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleIconFile</key>
    <string>appicon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# --- Copy Python source ---
cp appraiser.py "$APP_DIR/Contents/Resources/appraiser.py"

# --- Create the GUI wrapper (uses tkinter, ships with macOS Python) ---
cat > "$APP_DIR/Contents/Resources/gui.py" << 'GUIPY'
#!/usr/bin/env python3
"""
Continuous File Appraiser — macOS GUI
Wraps the CLI appraiser with a tkinter interface for selecting directories,
running appraisals, viewing results, and generating invoices.
"""

import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from appraiser import ContinuousAppraiser

MODELS = [
    "llama3.1:8b",
    "llama3.2:1b",
    "deepseek-r1:latest",
    "deepseek-coder:1.3b",
    "phi3:mini",
    "qwen2.5:0.5b",
    "llama2:latest",
]


class AppraiserGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Continuous File Appraiser")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        self.appraiser = None
        self.running = False

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Directory:").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        ttk.Entry(top, textvariable=self.dir_var, width=45).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="Browse", command=self._browse).pack(side=tk.LEFT)

        ttk.Label(top, text="  Model:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value=MODELS[0])
        ttk.Combobox(top, textvariable=self.model_var, values=MODELS, width=20).pack(side=tk.LEFT, padx=5)

        btn_frame = ttk.Frame(self.root, padding=5)
        btn_frame.pack(fill=tk.X)

        self.run_btn = ttk.Button(btn_frame, text="Run Appraisal", command=self._run)
        self.run_btn.pack(side=tk.LEFT, padx=5)
        self.invoice_btn = ttk.Button(btn_frame, text="Generate Invoice", command=self._invoice)
        self.invoice_btn.pack(side=tk.LEFT, padx=5)
        self.summary_btn = ttk.Button(btn_frame, text="Summary", command=self._summary)
        self.summary_btn.pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(btn_frame, textvariable=self.status_var).pack(side=tk.RIGHT, padx=10)

        # Results table
        cols = ("file", "category", "hours", "rate", "value")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", height=12)
        self.tree.heading("file", text="File")
        self.tree.heading("category", text="Category")
        self.tree.heading("hours", text="Hours")
        self.tree.heading("rate", text="Rate ($/hr)")
        self.tree.heading("value", text="Value ($)")
        self.tree.column("file", width=350)
        self.tree.column("category", width=140)
        self.tree.column("hours", width=70, anchor=tk.E)
        self.tree.column("rate", width=90, anchor=tk.E)
        self.tree.column("value", width=100, anchor=tk.E)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Total bar
        total_frame = ttk.Frame(self.root, padding=5)
        total_frame.pack(fill=tk.X)
        self.total_var = tk.StringVar(value="Total: $0.00")
        ttk.Label(total_frame, textvariable=self.total_var, font=("Helvetica", 16, "bold")).pack(side=tk.RIGHT, padx=15)

        # Log
        self.log = scrolledtext.ScrolledText(self.root, height=8, state=tk.DISABLED, font=("Menlo", 11))
        self.log.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    def _log(self, msg):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def _init_appraiser(self):
        self.appraiser = ContinuousAppraiser(
            target_dir=self.dir_var.get(),
            model=self.model_var.get(),
        )

    def _run(self):
        if self.running:
            return
        self.running = True
        self.run_btn.config(state=tk.DISABLED)
        self.status_var.set("Appraising...")
        self._init_appraiser()
        threading.Thread(target=self._run_async, daemon=True).start()

    def _run_async(self):
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(self.appraiser.run_full_appraisal())
            self.root.after(0, lambda: self._show_results(results))
        except Exception as e:
            self.root.after(0, lambda: self._log(f"Error: {e}"))
        finally:
            loop.close()
            self.running = False
            self.root.after(0, lambda: self.run_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set("Done"))

    def _show_results(self, results):
        for row in self.tree.get_children():
            self.tree.delete(row)

        total = 0.0
        for rel, entry in sorted(self.appraiser.ledger.items()):
            v = entry.get("dollar_value", 0)
            total += v
            self.tree.insert("", tk.END, values=(
                rel,
                entry.get("category", ""),
                f"{entry.get('estimated_hours', 0):.1f}",
                f"${entry.get('hourly_rate', 0):.0f}",
                f"${v:,.2f}",
            ))

        self.total_var.set(f"Total: ${total:,.2f}")
        self._log(f"Appraised {len(results)} files. Portfolio: ${total:,.2f}")

    def _invoice(self):
        if not self.appraiser:
            self._init_appraiser()
        if not self.appraiser.ledger:
            messagebox.showinfo("No data", "Run an appraisal first.")
            return
        path = self.appraiser.generate_invoice()
        self._log(f"Invoice saved: {path}")
        messagebox.showinfo("Invoice", f"Saved to:\n{path}")

    def _summary(self):
        if not self.appraiser:
            self._init_appraiser()
        if not self.appraiser.ledger:
            self._log("No appraisals in ledger yet.")
            return
        total = sum(e.get("dollar_value", 0) for e in self.appraiser.ledger.values())
        cats = {}
        for e in self.appraiser.ledger.values():
            c = e.get("category", "unknown")
            cats[c] = cats.get(c, 0) + e.get("dollar_value", 0)
        lines = [f"Portfolio: {len(self.appraiser.ledger)} files = ${total:,.2f}"]
        for c, v in sorted(cats.items(), key=lambda x: -x[1]):
            lines.append(f"  {c}: ${v:,.2f}")
        self._log("\n".join(lines))


def main():
    root = tk.Tk()
    AppraiserGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
GUIPY

# --- Launcher script ---
cat > "$APP_DIR/Contents/MacOS/launch" << 'LAUNCHER'
#!/bin/bash
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
exec /usr/bin/python3 "$DIR/gui.py"
LAUNCHER
chmod +x "$APP_DIR/Contents/MacOS/launch"

# --- Create app icon (simple programmatic icns) ---
python3 - "$APP_DIR/Contents/Resources" << 'ICONPY'
import struct, sys, os

# 32x32 ARGB icon — green $ on dark background
size = 32
pixels = []
for y in range(size):
    for x in range(size):
        # dark background
        r, g, b, a = 30, 30, 40, 255
        # green border
        if x < 2 or x >= 30 or y < 2 or y >= 30:
            r, g, b = 0, 180, 80
        # $ sign area (center)
        cx, cy = x - 16, y - 16
        if 12 <= y <= 20 and 11 <= x <= 20:
            r, g, b = 0, 220, 100
        pixels.append(struct.pack('BBBB', a, r, g, b))

icon_data = b''.join(pixels)
# Wrap in icns with is32 type (32x32)
entry = b'is32' + struct.pack('>I', 8 + len(icon_data)) + icon_data
icns = b'icns' + struct.pack('>I', 8 + len(entry)) + entry

out = os.path.join(sys.argv[1], 'appicon.icns')
with open(out, 'wb') as f:
    f.write(icns)
ICONPY

echo "=== App bundle created ==="

# --- Build DMG ---
echo "=== Creating DMG ==="
mkdir -p "$BUILD_DIR/dmg_staging"
cp -R "$APP_DIR" "$BUILD_DIR/dmg_staging/"

# Add a symlink to Applications for drag-install
ln -s /Applications "$BUILD_DIR/dmg_staging/Applications"

# Add README
cp README.md "$BUILD_DIR/dmg_staging/" 2>/dev/null || true

hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$BUILD_DIR/dmg_staging" \
    -ov -format UDZO \
    "$DMG_PATH" \
    2>&1

echo ""
echo "=== Done ==="
echo "DMG: $DMG_PATH"
echo "Size: $(du -h "$DMG_PATH" | cut -f1)"
