# Ollama Hub — Self-Hosted LLM on Apple Silicon

Runs entirely on your Mac. Zero API keys. Zero cloud dependency. Uses your own compute.

## What This Is

- **Ollama Hub** — Centralized inference server/client for local LLMs
- **Language Adapters** — Drop-in LLM clients for Python, JS/TS, Rust, Go, Shell
- **Auto-Installer** — Automatically adds LLM integration to every project in your workspace

## Quick Start

### 1. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull Recommended Models

```bash
cd /Users/alep/Downloads/ollama_hub
python3 hub.py
```

This pulls the full model registry ( ~14GB total):
- `llama3.2:1b` — General Q&A (1.3GB)
- `deepseek-coder:1.3b` — Code review (0.8GB)
- `deepseek-r1:latest` — Deep reasoning (5.2GB)
- `qwen2.5:0.5b` — Fast chat (0.4GB)
- `nomic-embed-text` — Embeddings (0.3GB)
- `llava:latest` — Vision (4.5GB)

### 3. Install LLM Adapters Into All Projects

```bash
python3 install_llm.py
```

This scanned **388 projects** and installed **564 adapters** across your workspace.

## Usage in Any Project

### Python

```python
from llm import llm

# Generate
response = llm.generate("Explain blockchain consensus")

# Code review
review = llm.code_review(your_code, language="python")

# Generate tests
tests = llm.generate_tests(your_code, language="python")
```

### JavaScript/TypeScript

```javascript
import { llm } from './llm.js';

const response = await llm.generate("Explain async/await");
const review = await llm.codeReview(yourCode, 'javascript');
```

### Rust

```rust
use llm::LLMClient;

let client = LLMClient::new();
let review = client.code_review(code).await?;
```

### Go

```go
import "./llm"

client := llm.NewClient()
review, _ := client.CodeReview(code)
```

### Shell

```bash
source ./llm.sh

llm_generate "Summarize this code" "" "" 0.3 200
llm_code_review ./main.py python
llm_explain ./script.sh
```

## Architecture

```
ollama_hub/
  hub.py              → Ollama server management, model registry
  install_llm.py      → Auto-installs adapters into every project
  adapters/
    python_adapter.py → llm.py for Python projects
    javascript_adapter.js → llm.js for JS/TS projects
    rust_adapter.rs   → llm.rs for Rust projects
    go_adapter.go     → llm.go for Go projects
    shell_adapter.sh  → llm.sh for Shell projects
```

## Model Registry

| Task | Model | Size | Purpose |
|------|-------|------|---------|
| General | llama3.2:1b | 1.3GB | Q&A, lightweight |
| Coding | deepseek-coder:1.3b | 0.8GB | Code completion |
| Reasoning | deepseek-r1:latest | 5.2GB | Deep analysis |
| Chat | qwen2.5:0.5b | 0.4GB | Fast chat |
| Embeddings | nomic-embed-text | 0.3GB | RAG, search |
| Vision | llava:latest | 4.5GB | Image understanding |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_DEFAULT_MODEL` | `llama3.2:1b` | Default model for adapters |

## License

MIT
