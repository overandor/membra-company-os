# DeCloud — Decentralized Hosting

A lightweight, decentralized alternative to Render, Netlify, and Vercel.

## Architecture

- **Gateway** — Accepts deploy requests, writes to an append-only deployment chain, distributes bundles to edge nodes, and reverse-proxies traffic.
- **Edge Node** — Serves app bundles, gossips with peers, and syncs the deployment chain from the gateway.
- **CLI** — Developer tool to deploy static sites and inspect status.
- **Chain** — Tamper-evident, append-only log of all deployment records (deploy, update, delete, rollback).
- **Store** — Content-addressed storage (IPFS-lite) deduplicates identical bundles automatically.

## Quick Start

### 1. Install dependencies

```bash
cd decloud
pip install -r requirements.txt
```

### 2. Start a Gateway

```bash
python run_gateway.py
# Or with env vars:
PORT=8080 python run_gateway.py
```

### 3. Start one or more Edge Nodes

```bash
# Terminal 2
DECLOUD_GATEWAY=http://127.0.0.1:8080 DECLOUD_PORT=9001 python run_node.py

# Terminal 3
DECLOUD_GATEWAY=http://127.0.0.1:8080 DECLOUD_PORT=9002 DECLOUD_REGION=us-east python run_node.py
```

### 4. Deploy an app

```bash
python cli.py deploy my-app ./my-static-site --owner alice
```

Visit the app at: `http://127.0.0.1:8080/proxy/my-app/`

### 5. Inspect status

```bash
python cli.py list
python cli.py status my-app
python cli.py nodes
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` / `DECLOUD_PORT` | HTTP listen port | `8080` (gateway), `9000` (node) |
| `HOST` | HTTP bind address | `0.0.0.0` |
| `DECLOUD_GATEWAY` | URL of gateway for nodes/CLI | `http://127.0.0.1:8080` |
| `DECLOUD_REGION` | Region label for edge node | `unknown` |
| `DECLOUD_ENDPOINT` | Public endpoint for edge node | auto |

## Design Principles

- **No single point of failure** — Gateways can be federated; edge nodes gossip directly.
- **Content addressing** — Bundles are stored by SHA-256 CID, so deduplication is free.
- **Immutable history** — Every deployment is recorded on-chain; rollbacks are trivial.
- **Minimal dependencies** — Only FastAPI, httpx, and uvicorn.

## Roadmap

- [ ] WebSocket real-time logs
- [ ] Multi-gateway federation with chain replication
- [ ] DNS / ENS integration for custom domains
- [ ] TLS termination via reverse proxy
- [ ] Docker / WASM runtime for non-static apps
- [ ] Incentive layer (tokens for node operators)
