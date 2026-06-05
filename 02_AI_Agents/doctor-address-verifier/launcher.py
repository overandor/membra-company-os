#!/usr/bin/env python3
"""
Launcher for the Doctor Address Verifier macOS app bundle.

When running as a PyInstaller-frozen app, resource paths and working directories
differ from a normal Python script. This launcher:
  1. Detects whether we're in a PyInstaller bundle or running from source.
  2. Sets up paths so Flask can find templates, and uploads/results go to
     ~/Documents/DoctorAddressVerifier/.
  3. Automatically opens the user's browser to the app URL.
  4. Starts the Flask server with Ollama + web crawling enabled.
"""

import os
import sys
import webbrowser
import threading
import time


def get_base_path():
    """Return the base path for bundled resources."""
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller bundle
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_data_dir():
    """Return the user-writable data directory for uploads and results."""
    data_dir = os.path.expanduser("~/Documents/DoctorAddressVerifier")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def open_browser(port):
    """Open the default browser after a short delay."""
    time.sleep(1.5)
    webbrowser.open(f"http://127.0.0.1:{port}")


def main():
    base_path = get_base_path()
    data_dir = get_data_dir()

    # Set environment so app_bundle.py can find everything
    os.environ["FLASK_TEMPLATE_DIR"] = os.path.join(base_path, "templates")
    os.environ["UPLOAD_DIR"] = os.path.join(data_dir, "uploads")
    os.environ["RESULTS_DIR"] = os.path.join(data_dir, "results")

    # Ollama defaults — enable by default in bundle, falls back gracefully
    if "OLLAMA_HOST" not in os.environ:
        os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"
    if "OLLAMA_MODEL" not in os.environ:
        os.environ["OLLAMA_MODEL"] = "llama3.1"
    # Don't set NO_OLLAMA — let the app try Ollama and fall back if unavailable

    # Web crawling is enabled by default
    # Set NO_CRAWLING=1 to disable

    # Make sure the package dir is on path
    sys.path.insert(0, base_path)

    port = int(os.environ.get("FLASK_PORT", 5001))

    # Open browser automatically (only when run standalone, not via Swift wrapper)
    if os.environ.get("NO_BROWSER") != "1":
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Import and run the Flask app
    from app_bundle import create_app
    app = create_app()
    print(f"Doctor Address Verifier starting on http://127.0.0.1:{port}")
    print(f"Data directory: {data_dir}")
    print(f"Ollama: {os.environ.get('OLLAMA_HOST', 'default')}")
    print(f"Web crawling: {'disabled' if os.environ.get('NO_CRAWLING') == '1' else 'enabled'}")
    print("Press Ctrl+C to quit.")
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
