---
title: Membra Company OS
emoji: 🏢
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# Membra Company OS

Monorepo for the Membra ecosystem: trading systems, AI agents, blockchain infrastructure, SDKs, and tooling.

## Repository Structure

```
├── 01_Trading_Systems/    # Trading bots, market makers, hedging tools (64 items)
├── 02_AI_Agents/          # AI agents, LLM systems, compute mesh (30 items)
├── 03_Documentation/      # Guides, summaries, appraisals (61 items)
├── 04_Software_Installers/# Reserved for installers
├── 05_Config_Files/       # Configuration files
├── 06_Projects/           # Full project codebases (88 items)
├── 07_Scripts/            # Standalone Python/Shell/JS scripts (11 items)
├── 08_Data_Files/         # JSON, JSONL, CSV, ledgers (20 items)
├── 09_Backup/             # History and backup files
├── membra-dmg-app/        # Electron desktop app
├── app.py                 # LLM 15m Signal Hunter (main app)
├── Dockerfile             # Container config for signal hunter
└── requirements.txt       # Python dependencies
```

See [README_ORGANIZED_DOWNLOADS.md](README_ORGANIZED_DOWNLOADS.md) for detailed folder contents.

## Key Projects

| Project | Location | Description |
|---------|----------|-------------|
| Signal Hunter | `app.py` | LLM-powered 15-minute crypto signal predictor |
| Membra Core | `06_Projects/membra-core/` | Core protocol and runtime |
| Membra SDK | `06_Projects/membra-sdk/` | Developer SDK |
| Membra L3 | `06_Projects/membra-l3/` | Layer 3 blockchain |
| Overmanifold | `06_Projects/overmanifold/` | Payment and tokenization platform |
| MemberMoney | `01_Trading_Systems/membramoney/` | Financial protocol |
| Compute Mesh | `02_AI_Agents/compute_mesh/` | Distributed compute network |
| DMG App | `membra-dmg-app/` | Electron desktop application |
| Agent Workforce | `02_AI_Agents/agent-workforce/` | AI agent orchestration platform |
| CompanyOS | `06_Projects/membra-companyos/` | Company operating system backend |

## Signal Hunter (Main App)

Multi-coin cryptocurrency signal prediction system using LLM analysis of Gate.io futures, Jupiter DEX, and Solana onchain data.

### Features
- **Multi-Coin Coverage**: SOL, BTC, ETH, JUP, WIF, BONK, RENDER, PYTH, HNT, RAY
- **Multiple Data Sources**: Gate.io futures, Jupiter DEX quotes, Solana RPC
- **LLM Predictions**: Groq, OpenRouter, or Gemini for 15-minute directional signals
- **Heuristic Fallback**: Rule-based predictions when LLM unavailable
- **Real-time Dashboard**: Web interface with live predictions and market data

### Configuration
Set environment variables:
- `GROQ_API_KEY`: Groq API key (optional)
- `OPENROUTER_API_KEY`: OpenRouter API key (optional)
- `GEMINI_API_KEY`: Google Gemini API key (optional)
- `SYMBOLS`: Comma-separated list of symbols to scan
- `PREDICTION_HORIZON_MINUTES`: Prediction horizon (default: 15)

### Deployment
Runs as an async web server on port 7860. Access the dashboard at the Space URL.

## License

MIT
