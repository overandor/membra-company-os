# Doctor Address Verifier

An Ollama-powered agent that automates healthcare provider address verification using NPPES, web directories, and LLM analysis.

## Features

- **NPPES API Integration**: Queries the CMS National Provider Identifier registry for each doctor
- **Multi-Source Web Verification**: Cross-references addresses against Doximity, WebMD, Healthgrades, hospital systems
- **Ollama LLM Agent**: Uses a local Ollama model to analyze conflicting evidence and produce a verdict
- **Proof Links**: Generates clickable verification links (Google Maps, provider directories, hospital pages) for every doctor
- **Excel I/O**: Upload a worklist spreadsheet, get back a fully verified spreadsheet with evidence
- **Web Dashboard**: Flask-based UI to upload, monitor progress, and download results

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐
│  Flask Web   │───▶│  Verifier    │───▶│  NPPES API     │
│  Dashboard   │    │  Agent       │    │  (CMS Registry)│
└─────────────┘    │              │    └────────────────┘
                   │  ┌──────────┐│    ┌────────────────┐
                   │  │ Ollama   ││───▶│  Web Search    │
                   │  │ LLM      ││    │  (Doximity,    │
                   │  └──────────┘│    │   WebMD, etc)  │
                   └──────────────┘    └────────────────┘
```

## Setup

### Prerequisites

1. **Python 3.10+**
2. **Ollama** installed and running locally:
   ```bash
   # Install Ollama (Linux/macOS)
   curl -fsSL https://ollama.com/install.sh | sh

   # Pull a model (recommended: llama3.1 or mistral)
   ollama pull llama3.1
   ```

### Installation

```bash
cd 02_AI_Agents/doctor-address-verifier
pip install -r requirements.txt
```

### Running

```bash
# Start with defaults (Ollama at localhost:11434, model llama3.1)
python app.py

# Custom Ollama endpoint/model
OLLAMA_HOST=http://myserver:11434 OLLAMA_MODEL=mistral python app.py

# Run without Ollama (rule-based verification only)
NO_OLLAMA=1 python app.py
```

Open `http://localhost:5001` in your browser.

## Usage

1. **Upload** an Excel file with columns: `Doctor Name`, `Address`, `City`, `State`, `Zip`
2. **Click Verify** — the agent will process each doctor through NPPES + web sources
3. **Monitor** progress in real-time on the dashboard
4. **Download** the verified spreadsheet with all evidence columns populated

## Output Columns

| Column | Description |
|--------|-------------|
| Visit Readiness | EXTERNALLY SUPPORTED, REVIEW, or UNVERIFIED |
| Confidence | High, Medium, or Low |
| Verification_Method | Which sources confirmed (NPPES-MATCH, MONTEFIORE-CAMPUS, etc.) |
| External Evidence Note | Human-readable summary of findings |
| NPPES_Address | Address found in NPPES registry |
| Corrected Address | Suggested alternative address (if mismatch) |
| NPPES_Link | Direct link to NPI record |
| Doximity_Link | Search link for Doximity profile |
| WebMD_Link | Search link for WebMD profile |
| Healthgrades_Link | Search link for Healthgrades profile |
| Google_Maps_Link | Google Maps search for the address |
| Hospital_Page_Link | Link to hospital/system provider page |
| LLM_Analysis | Ollama model's analysis of conflicting evidence |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| OLLAMA_HOST | http://localhost:11434 | Ollama API endpoint |
| OLLAMA_MODEL | llama3.1 | Model to use for analysis |
| NO_OLLAMA | (unset) | Set to 1 to skip LLM analysis |
| FLASK_PORT | 5001 | Web server port |

## License

MIT — Part of the Membra Company OS monorepo.
