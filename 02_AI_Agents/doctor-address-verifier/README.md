# Doctor Address Verifier

Healthcare provider address verification tool with NPPES registry lookups, **live web crawling**, and **Ollama LLM** analysis.

## Features

- **NPPES API** — Query the CMS National Provider registry for NPI data and practice addresses
- **Live Web Crawling** — Scrape Doximity, Healthgrades, WebMD, hospital directories, and web search results for real-time address confirmation
- **Ollama LLM Agent** — Feed all evidence (NPPES + crawled data) to a local LLM for intelligent analysis of ambiguous cases
- **Hospital System Detection** — Automatic recognition of Montefiore, Jacobi, BronxCare, CHAM, Open Door, and other NYC-area systems
- **Proof Links** — Clickable evidence links for every doctor (Google Maps, Doximity, WebMD, Healthgrades, hospital pages)
- **Batch + Single** — Upload an Excel worklist for batch verification, or use the API for single doctor lookups
- **macOS .dmg** — Build a standalone native macOS app with bundled Ollama
- **Hugging Face Space** — Public Gradio web app for browser-based verification
- **CI/CD DMG Build** — GitHub Actions workflow builds DMG automatically on macOS

## Hugging Face Space

A public Gradio web app is available for browser-based verification — no install needed.

### Run Locally

```bash
cd 02_AI_Agents/doctor-address-verifier
pip install -r hf_requirements.txt
python hf_app.py
```

Open http://localhost:7860 in your browser.

### Deploy to Hugging Face Spaces

1. Create a new Space at https://huggingface.co/new-space (SDK: Gradio)
2. Copy these files to the Space repo:
   - `hf_app.py` → `app.py`
   - `hf_requirements.txt` → `requirements.txt`
   - `verifier.py`
   - `web_crawler.py`
3. Push and the Space will auto-deploy

### CI-Built DMG

The `.dmg` is built automatically by GitHub Actions on every push to `main` that touches `02_AI_Agents/doctor-address-verifier/`. You can also trigger it manually via workflow dispatch.

Download the DMG from the **Actions → Build macOS DMG → Artifacts** tab.

## Quick Start (Development)

```bash
cd 02_AI_Agents/doctor-address-verifier
pip install -r requirements.txt

# With full features (Ollama + crawling):
python app.py

# Rule-based only (no Ollama):
NO_OLLAMA=1 python app.py

# Disable web crawling (NPPES + links only):
NO_CRAWLING=1 python app.py
```

Open http://localhost:5001 in your browser.

## macOS App (.dmg)

Build a standalone macOS application that bundles:
- Native Swift wrapper (AppKit + WKWebView)
- Flask verification server (PyInstaller binary)
- Ollama binary for local LLM inference

### Prerequisites (build machine only)

- macOS 13.0+ (Ventura or later)
- Xcode Command Line Tools (`xcode-select --install`)
- Python 3.10+ (`python3` on PATH)
- Internet connection (for pip packages and Ollama download)

### Build

```bash
cd 02_AI_Agents/doctor-address-verifier
chmod +x build_dmg.sh
./build_dmg.sh
```

Output: `dist/DoctorAddressVerifier-2.0.0.dmg`

### Install

1. Open `DoctorAddressVerifier-2.0.0.dmg`
2. Drag `DoctorAddressVerifier.app` to Applications
3. First launch: right-click → Open → Open (bypasses Gatekeeper)
4. Pull an Ollama model (first time only):
   ```bash
   /Applications/DoctorAddressVerifier.app/Contents/Resources/bin/ollama pull llama3.1
   ```

### How It Works

The DMG bundles three components:

1. **Swift wrapper** — Native macOS app with WKWebView that displays the web UI. Manages lifecycle of Flask and Ollama processes.
2. **Flask server** — PyInstaller-compiled Python binary with all dependencies baked in. Runs at `http://127.0.0.1:5001`. No Python installation needed.
3. **Ollama** — Local LLM inference server. Bundled binary starts automatically. Models stored in `~/Documents/DoctorAddressVerifier/models/`.

Data is stored in `~/Documents/DoctorAddressVerifier/` (uploads, results, Ollama models).

## Architecture

```
DoctorAddressVerifier.app/
├── Contents/
│   ├── MacOS/
│   │   └── DoctorAddressVerifier    # Swift binary (WKWebView wrapper)
│   ├── Resources/
│   │   ├── bin/
│   │   │   ├── flask_server         # PyInstaller binary (Flask + verifier)
│   │   │   └── ollama               # Ollama binary
│   │   ├── templates/
│   │   │   └── index.html           # Web UI
│   │   ├── app_bundle.py            # Flask app factory (dev fallback)
│   │   ├── verifier.py              # Verification engine
│   │   └── web_crawler.py           # Web crawling module
│   └── Info.plist
```

## Verification Pipeline

For each doctor, the engine:

1. **NPPES API** — Query CMS registry by name, match NPI record, compare addresses
2. **Hospital System Detection** — Check if address belongs to a known hospital system
3. **Live Web Crawling** (6+ sources):
   - NPI Profile (npiprofile.com)
   - Doximity provider profiles
   - Healthgrades physician pages
   - WebMD doctor listings
   - Hospital directories (Montefiore Einstein, NYC Health + Hospitals)
   - DuckDuckGo web search verification
4. **Rule-Based Scoring** — Combine NPPES match + hospital system + crawl evidence
5. **Ollama LLM Analysis** — For ambiguous cases, send ALL evidence to the LLM for a final verdict

Output columns: Visit Readiness, Confidence (High/Medium/Low), Verification Method, Evidence Note, Corrected Address, Routing Action, proof links, crawl evidence summary, LLM analysis.

## API

```bash
# Verify a single doctor
curl -X POST http://localhost:5001/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SMITH, JOHN",
    "address": "111 E 210TH ST",
    "city": "BRONX",
    "state": "NY",
    "zip": "10467"
  }'

# Check Ollama status
curl http://localhost:5001/api/ollama-status
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_PORT` | `5001` | Port for the Flask server |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.1` | Ollama model name |
| `NO_OLLAMA` | `0` | Set to `1` to disable Ollama LLM analysis |
| `NO_CRAWLING` | `0` | Set to `1` to disable live web crawling |
| `NO_BROWSER` | `0` | Set to `1` to prevent auto-opening browser |

## Files

| File | Description |
|------|-------------|
| `app.py` | Flask development server (direct run) |
| `app_bundle.py` | Flask app factory (for PyInstaller bundle) |
| `verifier.py` | Core verification engine (NPPES + rules + Ollama) |
| `web_crawler.py` | Real web crawling module (Doximity, Healthgrades, etc.) |
| `launcher.py` | PyInstaller entry point with bundle-aware paths |
| `templates/index.html` | Web UI with dark theme |
| `DoctorAddressVerifier.spec` | PyInstaller build configuration |
| `build_dmg.sh` | macOS DMG build script (Swift + PyInstaller + Ollama) |
| `hf_app.py` | Hugging Face Spaces Gradio app |
| `hf_requirements.txt` | Python dependencies for the HF Space |
| `DoctorAddressVerifierApp/` | Swift macOS wrapper (Package.swift + sources) |
