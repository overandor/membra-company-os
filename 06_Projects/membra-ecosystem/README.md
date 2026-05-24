# MEMBRA Agent OS

**60 Autonomous LLM Employees as Network Nodes**

Each employee is a dot-notation identity: `{name}.{department}.membra`

- `alex.strategy.membra` — Chief Strategy Officer
- `kai.engineering.membra` — Chief Technology Officer
- `zack.marketing.membra` — Chief Marketing Officer
- `eve.hr.membra` — Chief Human Resources Officer
- ... and 56 more

## Architecture

```
agents/
  base.py              # BaseAgent — LLM integration + network protocol
  registry.py          # AgentRegistry — discovery & orchestration
  __init__.py
  alex_strategy_membra.py      # 60 individual agent files
  kai_engineering_membra.py
  ...

api/
  agent_network.py     # FastAPI endpoints
  __init__.py

tests/
  test_agent_network.py

main.py                # FastAPI entry point
```

## Quick Start

```bash
# 1. Install Ollama and pull models
ollama pull llama3.2
ollama serve

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the Agent OS
python main.py

# 4. Query any agent
open http://localhost:8000/v1/agent-network/agents
```

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /v1/agent-network/agents` | List all 60 agents |
| `GET /v1/agent-network/agents/{id}` | Get agent details |
| `GET /v1/agent-network/agents/{id}/job` | Full job description |
| `POST /v1/agent-network/agents/{id}/think` | Run LLM task |
| `POST /v1/agent-network/agents/{id}/generate` | Raw LLM generation |
| `GET /v1/agent-network/departments` | Department stats |
| `GET /v1/agent-network/stats` | Aggregate stats |
| `POST /v1/agent-network/start` | Start TCP network |

## Agent Network Protocol

Agents communicate over TCP with message types:
- **heartbeat** — peer discovery
- **gossip** — peer table synchronization
- **rpc** — remote procedure calls
- **task** — LLM task delegation
- **result** — task completion

## License

MIT
