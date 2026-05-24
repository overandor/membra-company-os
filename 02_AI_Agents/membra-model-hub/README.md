# Membra Decentralized Model Hub

A decentralized Hugging Face alternative that runs on your own network.

- **No cloud required** — LAN multicast + HTTP gossip discovers peers automatically
- **Honest distributed inference** — job parallelism across nodes, not model-parallel magic
- **Model registry replicas** — every node caches the catalog; no single point of failure
- **Ollama-native** — workers host models via Ollama; any GGUF works out of the box

## Architecture

```
User CLI / API
      |
      v
[Inference Router]  --HTTP+WebSocket gossip-->  [Registry Replica]
      |                                               |
      | POST /inference                             | models, nodes
      |                                             |
      v                                             v
[Worker Node A: llama3.1:8b]               [Worker Node B: phi3]
      | Ollama local inference                     | Ollama local inference
      |                                            |
   Result + proof hash                          Result + proof hash
```

- **Registry/Router**: FastAPI node that accepts inference requests, finds a healthy worker hosting the requested model, and returns a task ID for polling.
- **Worker Node**: FastAPI node that runs Ollama locally and exposes `/v1/inference`. It announces its hosted models to the mesh via gossip.
- **Discovery**: UDP multicast beacons for LAN peers + periodic HTTP gossip to merge model/node state across the mesh.
- **CLI**: `list-models`, `list-nodes`, `infer`, `publish`, `worker`, `registry` commands.

## Quick Start

### 1. Install

```bash
cd membra-model-hub
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Make sure Ollama is running

```bash
ollama serve
```

Pull a model if needed:
```bash
ollama pull llama3.1:8b
```

### 3. Start a Registry + Router (Terminal 1)

```bash
export MEMBRA_API_KEY="change-me-to-a-long-secret"
python cli.py registry --port 8765
```

### 4. Start a Worker (Terminal 2)

```bash
export MEMBRA_API_KEY="change-me-to-a-long-secret"
python cli.py worker --models llama3.1:8b --port 8766 --bootstrap http://localhost:8765
```

### 5. Use the CLI (Terminal 3)

List models on the network:
```bash
export MEMBRA_API_KEY="change-me-to-a-long-secret"
export MEMBRA_REGISTRY="http://localhost:8765"
python cli.py list-models
```

Run inference:
```bash
python cli.py infer llama3.1:8b "Explain quantum computing in one sentence"
```

Publish a model card:
```bash
python cli.py publish my-custom-llm --description "Fine-tuned for finance" --tags finance,llm --parameters 7B
```

### 6. Add more Workers

On another machine on the same LAN:
```bash
export MEMBRA_API_KEY="change-me-to-a-long-secret"
python cli.py worker --models llama3.1:8b --port 8766 --bootstrap http://<router-ip>:8765
```

UDP multicast will auto-discover peers on the same LAN. For WAN or VLANs, use `--bootstrap` with known peer URLs.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMBRA_API_KEY` | `dev-key-change-me` | Bearer token for auth |
| `MEMBRA_NODE_ID` | auto | Unique node identifier |
| `MEMBRA_API_PORT` | `8765` (router) / `8766` (worker) | HTTP API port |
| `MEMBRA_WORKER_PORT` | `8766` | Worker HTTP port |
| `MEMBRA_REGISTRY` | `http://localhost:8765` | Default registry URL for CLI |
| `MEMBRA_BOOTSTRAP_PEERS` | `""` | Comma-separated peer URLs |
| `MEMBRA_DISCOVERY_ADDR` | `239.255.42.99` | UDP multicast group |
| `MEMBRA_DISCOVERY_PORT` | `42424` | UDP multicast port |
| `MEMBRA_GOSSIP_INTERVAL` | `5` | Seconds between gossip rounds |
| `MEMBRA_INFERENCE_TIMEOUT` | `120` | Seconds to wait for inference |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |

## API Endpoints

### Registry / Router

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Node + mesh status |
| `/models` | GET | No | List known models |
| `/models/{id}` | GET | No | Get model card |
| `/models` | POST | Bearer | Publish model card |
| `/nodes` | GET | No | List peers |
| `/inference` | POST | No | Submit inference task |
| `/inference/{id}` | GET | No | Poll task result |
| `/gossip` | POST | No | Exchange mesh state |

### Worker

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Worker status |
| `/v1/models` | GET | No | Models hosted locally |
| `/v1/inference` | POST | Bearer | Run inference |
| `/gossip` | POST | No | Exchange mesh state |

## Honest Limitations

- **Job parallelism only**: two workers = 2x batch throughput, not 2x speed on a single prompt.
- **Each worker loads its own model copy**: memory does not pool across nodes.
- **No streaming yet**: polling-based results; WebSocket streaming can be added.
- **In-memory state**: production should use Redis/Postgres for task queues and persistent registry.

## Production Hardening

- Replace in-memory `DiscoveryProtocol.peers` and `RouterState.tasks` with Redis.
- Add TLS (`https://`, `wss://`) and mTLS for worker auth.
- Use a persistent gossip backend (libp2p, Redis pub/sub, or NATS).
- Run workers in containers with cgroup limits.
- Add payment/verification hooks using the existing MEMBRA proof-of-job hashes.

## License

MIT
