# MEMBRA LLM Developer — Desktop App (.dmg)

Desktop application for autonomous AI-driven software development, built with Electron and packaged as a macOS `.dmg`.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  MEMBRA LLM Developer (Electron)                │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐ │
│  │  LLM Bridge   │ │ Project Mgr   │ │ Agent Orchestrator    │ │
│  │               │ │               │ │                       │ │
│  │ • Groq        │ │ • File tree   │ │ • 10 AI agents        │ │
│  │ • OpenRouter  │ │ • Read/write  │ │ • Pipeline execution  │ │
│  │ • OpenAI      │ │ • Language    │ │ • Proof hashing       │ │
│  │ • Gemini      │ │   detection   │ │ • Auto-selection      │ │
│  │ • Ollama      │ │ • Project     │ │                       │ │
│  │               │ │   info        │ │ Agents:               │ │
│  │ Capabilities: │ │               │ │ Strategy, Product,    │ │
│  │ • Chat        │ └───────────────┘ │ Engineering, Reviewer, │ │
│  │ • Generate    │                   │ Testing, DevOps, Docs, │ │
│  │ • Review      │                   │ Security, Refactor,    │ │
│  │ • Explain     │                   │ Governance             │ │
│  │ • Refactor    │                   └───────────────────────┘ │
│  │ • Debug       │                                              │
│  └───────────────┘                                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Renderer (Dark Neomorphic UI)               │   │
│  │  Chat │ Code Editor │ Agent Pipeline │ Project │ Settings│   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **LLM Chat** — Conversational coding assistant (Groq, OpenRouter, OpenAI, Gemini, or local Ollama)
- **Code Generation** — Describe what you need, get production-ready code in 13+ languages
- **Code Review** — Automated review for bugs, security, performance, and best practices
- **Code Explanation** — Clear breakdowns of any code snippet
- **Refactoring** — AI-guided code improvements with specific instructions
- **Debugging** — Paste code + error → get root cause analysis and fix
- **Agent Pipeline** — Run 10 specialized AI agents in sequence on any task
- **Project Explorer** — Open directories, browse file trees, edit files in-app
- **Dark Neomorphic UI** — Consistent dark-gold design matching MEMBRA ecosystem

## Agent Registry

| Agent | Role |
|-------|------|
| Strategy | Decides what to build next |
| Product | Converts strategy to requirements |
| Engineering | Generates code and architectures |
| Code Review | Reviews for bugs, security, perf |
| Testing | Generates tests and validates |
| DevOps | Creates CI/CD, Docker, deployment |
| Documentation | Writes README, API docs, guides |
| Security | Vulnerability scanning and fixes |
| Refactoring | Code smell detection, optimization |
| Governance | Approval gates, compliance, proofs |

## Quick Start

```bash
cd membra-dmg-app
npm install
npm start
```

## Build DMG

```bash
# macOS
npm run build

# Windows
npm run build:win

# Linux
npm run build:linux
```

## Configuration

Set LLM provider via Settings view or environment variables:

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Google Gemini API key |

For local models, configure Ollama URL in Settings (default: `http://localhost:11434`).

## Tech Stack

- **Electron 31** — Cross-platform desktop framework
- **Vanilla JS** — No framework overhead, fast rendering
- **electron-builder** — DMG/NSIS/AppImage packaging
- **Dark Neomorphic CSS** — Consistent with MEMBRA CompanyOS design system

## Integration

This app connects to the broader MEMBRA ecosystem:
- **llm-os** — Kernel, System Builder, LLM Factory integration
- **membra-companyos** — 9 OS modules (IntentOS, TaskOS, AgentOS, etc.)
- **membra-core** — Proof-of-job pipeline, consensus, hashing

## License

MIT
