# Continuous File Appraiser

Ollama-powered agent that continuously appraises every file in a directory, assigns dollar values based on agent work complexity, and generates billable invoices.

## Requirements

```bash
pip install aiohttp
ollama serve  # must be running
ollama pull llama3  # or any model
```

## Usage

```bash
# One-shot appraisal of current directory
python appraiser.py --dir /path/to/project --interval 0 --invoice

# Continuous monitoring (every 5 minutes)
python appraiser.py --dir /path/to/project --model llama3 --interval 300

# Generate invoice from existing ledger
python appraiser.py --dir /path/to/project --interval 0 --invoice

# Summary only
python appraiser.py --dir /path/to/project --summary
```

## How It Works

1. **Discovery** — walks the directory tree, skipping binaries/media/caches
2. **Hash check** — only re-appraises files that changed since last run
3. **Ollama appraisal** — sends file content to local LLM which estimates category, complexity (0-1), and hours of skilled work
4. **Dollar value** — `hourly_rate × estimated_hours × complexity_score`
5. **Ledger** — persists all appraisals to `appraisal_ledger.json`
6. **Invoice** — generates billable JSON invoices in `invoices/`

## Rate Table ($/hr by category)

| Category | Rate |
|---|---|
| Smart Contract | $250 |
| Trading System | $225 |
| ML Pipeline | $200 |
| Infrastructure | $185 |
| API Service | $175 |
| Frontend | $150 |
| Test | $130 |
| Script | $120 |
| Configuration | $110 |
| Documentation | $95 |
| Data | $80 |

## Output

- `appraisal_ledger.json` — per-file valuations with hashes, deltas, reasoning
- `invoices/INV-*.json` — billable invoices with line items and totals
