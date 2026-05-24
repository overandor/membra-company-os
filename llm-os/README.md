# LLM OS — Autonomous Operating System for LLM-Driven Economics

The LLM OS is an autonomous operating system built on top of [membra-core](../membra-core/) that enables LLMs to:

1. **Create other LLMs** — Spawn, train, and manage model instances using LLMGPT
2. **Build software systems** — Autonomously develop deployable applications, APIs, trading bots
3. **Generate real income** — Marketplace builds, compute rental, model licensing, policy-gated trading
4. **Track economics** — Cost accounting, profit calculation, budget allocation, runway analysis
5. **Stay safe** — Governance gates, emergency halt, audit trails, human approval flows

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM OS KERNEL                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────┐ │
│  │  SENSE  │ │ DECIDE  │ │  PLAN   │ │ EXECUTE │ │VERIFY│ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └──┬───┘ │
│       └───────────┴───────────┴───────────┴──────────┘      │
│                         ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                     LEARN & ACCOUNT                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  ECONOMIC     │    │   SYSTEM      │    │   LLM         │
│  ENGINE       │    │   BUILDER     │    │   FACTORY     │
│               │    │               │    │               │
│ • Marketplace │    │ • Web apps    │    │ • Create specs│
│ • Trading     │    │ • APIs        │    │ • Train models│
│ • Compute rent│    │ • Trading bots│    │ • Evaluate    │
│ • Model license│    │ • Dashboards  │    │ • Export C++  │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │    TREASURY     │
                    │  (accounting)   │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │   GOVERNANCE    │
                    │  (safety gates) │
                    └─────────────────┘
```

## Quick Start

```bash
# Show OS status
python -m llm_os status

# Run one autonomous cycle
python -m llm_os start --once

# Start continuous autonomous loop
python -m llm_os start

# Scan for economic opportunities
python -m llm_os scan

# Build a system
python -m llm_os build api_service

# Train an LLM
python -m llm_os train my_model

# Check treasury
python -m llm_os treasury
```

## Python API

```python
from llm_os import Kernel

# Initialize with conservative policy
kernel = Kernel(starting_balance_usd=100.0)

# Run one cycle
kernel.start(autonomous=False)

# Or run continuous loop
kernel.start(autonomous=True, max_loops=10)

# Check status
print(kernel.get_status())
```

## Subsystems

### Economic Engine
Scans for and executes revenue-generating opportunities:
- **Marketplace builds** — Claim jobs from membra marketplace, build artifacts, earn bounties
- **Trading** — Policy-gated Gate.io futures market making (wraps existing systems)
- **Compute rental** — Rent idle worker capacity for inference/validation
- **Model licensing** — License trained model checkpoints

All opportunities are evaluated for expected ROI before execution.

### System Builder
Autonomous software development:
- Analyze job requirements
- Generate code (web apps, APIs, trading bots, dashboards, pipelines, LLM training)
- Run syntax checks and tests
- Finalize proof bundles with hashes

### LLM Factory
Creates and trains LLM instances:
- Spawn model specs (configurable layers, dimensions, heads)
- Train on custom corpora using LLMGPT Python/PyTorch
- Evaluate model quality
- Export trained weights to C++ for inference
- Maintain model registry with hashes and metrics

### Treasury
Central accounting:
- Track all costs and revenue per subsystem
- Calculate P&L and ROI
- Budget allocation based on historical performance
- Runway calculation (days until funds exhausted)

### Governance
Safety and policy enforcement:
- Action classification (SAFE, STANDARD, RISKY, CRITICAL, SELF_MODIFYING)
- Cost limits (daily and per-action)
- Human approval for critical actions
- Emergency halt with audit trail
- Simulation mode by default (no real money moves)

## Safety

**By default, the OS runs in SIMULATION mode.**
- No real payments are made
- No real trading positions are opened
- No production deployments occur
- All costs are estimated/simulated

To enable production features:
```bash
export MEMBRA_MODE=production
export STRIPE_SECRET_KEY=sk_...
export GATE_API_KEY=...
export GATE_API_SECRET=...
```

**Critical actions require human approval** even in production:
- Money movement
- Production deployment
- Model training over $50
- Self-modification of OS code

## Building macOS DMG

To create a distributable macOS disk image (.dmg):

```bash
# Build the .app bundle
./build_app.sh

# Create the DMG disk image
./build_dmg.sh
```

The DMG will be created at `dist/LLM-OS-0.1.0.dmg` and can be distributed to macOS users.

**Requirements:**
- macOS
- Python 3.11+
- Xcode Command Line Tools (for hdiutil)

**Note:** The bundled app includes only core dependencies. For trading or training features, users should install the package via pip with the appropriate extras.

## Model Compression

Reduce LLM model size and improve inference speed:

```python
from llm_os import ModelCompressor

# Compress a model
compressor = ModelCompressor("path/to/model.bin")

# Quantize to 8-bit (50% size reduction)
compressed = compressor.quantize(bits=8)

# Or 4-bit (75% size reduction)
compressed = compressor.quantize(bits=4)

# Prune weights
compressed = compressor.prune(sparsity=0.3)

# Export for transmission (GGUF, SafeTensors, ONNX)
compressed = compressor.export_for_transmission(format="gguf")

# Get compression statistics
stats = compressor.get_compression_stats()
print(f"Size reduction: {stats['size_reduction']}")
```

**Convenience function for DMG distribution:**
```python
from llm_os import compress_model_for_dmg

result = compress_model_for_dmg("model.bin", bits=8)
print(f"Compressed to: {result['compressed_path']}")
print(f"Stats: {result['stats']}")
```

## Electrical Signal Transmission

Distribute compressed models over electrical signals using powerline communication:

```python
from llm_os import ElectricalTransmitter, get_transmission_estimate

# Estimate transmission time
estimate = get_transmission_estimate(
    model_size_bytes=500_000_000,  # 500MB
    modulation="QAM"
)
print(f"Estimated time: {estimate['estimated_time_minutes']:.1f} minutes")

# Prepare and transmit
transmitter = ElectricalTransmitter(interface="/dev/ttyUSB0")
metadata = transmitter.prepare_model_for_transmission(
    "compressed_model_q4.bin",
    modulation="QAM"
)
print(f"Chunks: {metadata['total_chunks']}")
print(f"Est. time: {metadata['estimated_transmission_time_minutes']:.1f} min")

# Transmit (requires PLC hardware)
result = transmitter.transmit("compressed_model_q4.bin", receiver_address="node-001")
```

**Receive models:**
```python
from llm_os import ElectricalReceiver

receiver = ElectricalReceiver(interface="/dev/ttyUSB0")
result = receiver.receive(
    output_path="received_model.bin",
    expected_hash="abc123..."
)
```

**Supported modulation schemes:**
- ASK (Amplitude Shift Keying) - 1 bit/symbol
- FSK (Frequency Shift Keying) - 1 bit/symbol
- PSK (Phase Shift Keying) - 2 bits/symbol
- QAM (Quadrature Amplitude Modulation) - 4 bits/symbol (fastest)

## Local Inference

Run compressed models locally with optimized inference:

```python
from llm_os import LocalInferenceRunner, quick_inference, estimate_inference_speed

# Quick one-shot inference
result = quick_inference(
    model_path="model_q4.gguf",
    prompt="Explain quantum computing",
    max_tokens=256
)
print(result)

# Full inference runner
runner = LocalInferenceRunner("model_q4.gguf", backend="llama.cpp")
runner.load_model()

response = runner.generate(
    prompt="Write a Python function",
    max_tokens=512,
    temperature=0.7,
    top_p=0.9
)
print(response["generated_text"])

# Benchmark speed
bench = runner.benchmark(num_runs=5)
print(f"Tokens/sec: {bench['tokens_per_second']:.1f}")

runner.unload()
```

**Estimate inference speed:**
```python
from llm_os import estimate_inference_speed

speed = estimate_inference_speed(
    model_size_mb=500,
    quantization="4-bit",
    hardware="cpu"
)
print(f"Est. tokens/sec: {speed['estimated_tokens_per_second']:.1f}")
```

**Inference server:**
```python
from llm_os import InferenceServer

server = InferenceServer("model_q4.gguf", host="127.0.0.1", port=8080)
server.start()
# Server now available at http://127.0.0.1:8080/generate
server.stop()
```

## Enterprise LLM Suite ($200K Value)

Complete enterprise-grade LLM platform with native macOS GUI:

**Features:**
- Multi-model inference (local + API: OpenAI, Anthropic, Cohere, HuggingFace)
- RAG with vector database for document intelligence
- Fine-tuning and model management
- Enterprise authentication and RBAC
- Analytics and monitoring dashboard
- Document processing and ingestion
- API key management
- SQLite database for persistence
- Native Cocoa GUI with tabbed interface

**Build Enterprise DMG:**
```bash
# Install enterprise dependencies
pip install -e ".[macos,enterprise]"

# Build .app bundle
./build_enterprise_app.sh

# Create DMG disk image
./build_enterprise_dmg.sh
```

The DMG will be created at `dist/Enterprise-LLM-Suite-1.0.0.dmg` containing the complete $200K enterprise suite.

**Programmatic Usage:**
```python
from enterprise_suite import create_enterprise_suite

# Initialize suite
suite = create_enterprise_suite()

# Create users
admin = suite.create_user("admin", "admin@company.com", UserRole.ADMIN)

# Register models
suite.register_model(
    "Llama-2-7B",
    ModelProvider.LOCAL,
    "~/models/llama-2-7b.gguf",
    4096,
    "4-bit"
)

# Ingest documents for RAG
doc = suite.ingest_document("company_handbook.pdf")

# Create conversation and chat
conv = suite.create_conversation(admin.id, model_id, "Project Planning")
response = suite.send_message(conv.id, "Summarize the handbook", use_rag=True)

# Fine-tune models
job_id = suite.create_fine_tuning_job(
    base_model_id,
    "training_data.jsonl",
    "my-fine-tuned-model"
)

# Analytics
report = suite.get_analytics_report(days=30)

# Export for backup/distribution
export_path = suite.export_suite("~/backup")
```

**GUI Application:**
```bash
# Launch GUI
python enterprise_gui.py
```

The GUI provides:
- **Chat Tab**: Conversation management with RAG-enabled chat
- **Models Tab**: Register, load, and manage LLM models
- **Documents Tab**: Upload and search documents for RAG
- **Analytics Tab**: View usage statistics and metrics
- **Settings Tab**: Export suite and configure settings

## Web Server & Shareable Links

Host inference locally and expose access via shareable links:

**Start the web server:**
```bash
./start_server.sh
# Or directly:
python enterprise_server.py
```

The server starts on `http://localhost:8000` with:
- **Web UI**: Browser-based chat interface at `http://localhost:8000`
- **API**: RESTful API at `http://localhost:8000/api`
- **Shareable Links**: Generate links for conversation access

**API Endpoints:**

```bash
# Create user
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com"}'

# List models (requires API key)
curl http://localhost:8000/api/models \
  -H "X-API-Key: your-api-key"

# Send message
curl -X POST http://localhost:8000/api/conversations/message \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"conversation_id": "conv-id", "message": "Hello", "use_rag": true}'

# Create shareable link
curl -X POST http://localhost:8000/api/share \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"conversation_id": "conv-id", "expires_in_hours": 24}'
```

**Shareable Links:**
- Generate time-limited links for conversations
- Share via URL: `http://localhost:8000/share/{token}`
- Recipients can view and send messages without accounts
- Links expire after specified duration

**Python API Client:**
```python
import requests

BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {"X-API-Key": API_KEY}

# Create conversation
conv = requests.post(
    f"{BASE_URL}/api/conversations",
    json={"user_id": "user-id", "model_id": "model-id", "title": "My Chat"},
    headers=headers
).json()

# Send message
response = requests.post(
    f"{BASE_URL}/api/conversations/message",
    json={"conversation_id": conv["id"], "message": "Hello", "use_rag": True},
    headers=headers
).json()

print(response["response"])

# Create share link
share = requests.post(
    f"{BASE_URL}/api/share",
    json={"conversation_id": conv["id"], "expires_in_hours": 24},
    headers=headers
).json()

print(f"Share link: {BASE_URL}{share['share_url']}")
```

## Solana Token Gating & Liquid Staking

Wrap the inference service in Solana devnet tokens with liquid staking:

**Smart Contracts:**
- `programs/inference-token/` - SPL token for inference payments
- `programs/liquid-staking/` - Liquid staking pool for token holders

**Deploy to Solana Devnet:**
```bash
# Install dependencies
cargo install anchor-cli
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Deploy programs
./deploy_solana.sh
```

**Solana Integration:**
```python
from solana_integration import create_solana_manager, TokenGating

# Initialize Solana manager
manager = create_solana_manager(
    rpc_url="https://api.devnet.solana.com",
    private_key_path="~/.config/solana/id.json"
)

# Token gating for inference
gating = TokenGating(manager)

# Check wallet access
access = await gating.check_access("wallet_address")
print(f"Has access: {access['has_access']}")
print(f"Balance: {access['balance']}")
print(f"Required: {access['required']}")

# Process payment for inference
payment = await gating.process_payment("wallet_address", "conv_id")
print(f"Payment signature: {payment['signature']}")
```

**API Endpoints:**
```bash
# Check token balance
curl http://localhost:8000/api/solana/balance/{wallet_address}

# Check access
curl http://localhost:8000/api/solana/access/{wallet_address}

# Process payment
curl -X POST http://localhost:8000/api/solana/pay \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "...", "conversation_id": "..."}'

# Stake tokens
curl -X POST http://localhost:8000/api/solana/stake \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "...", "amount": 100, "pool_address": "..."}'

# Get stake info
curl http://localhost:8000/api/solana/stake/{wallet_address}

# Claim rewards
curl -X POST "http://localhost:8000/api/solana/claim?wallet_address=...&pool_address=..."
```

**Staking UI:**
Access the staking interface at `http://localhost:8000/staking`

Features:
- Stake inference tokens to earn rewards
- 50% discount on inference for stakers
- Claim accumulated rewards
- View staking statistics

**Token Economics:**
- **Inference Token (INF)**: Used to pay for inference requests
- **Cost**: 1 token per inference request
- **Staker Discount**: 50% off for token stakers
- **Staking Rewards**: Earn additional tokens by staking
- **Liquid Staking**: Unstake anytime without lockup

## Liquid Staked Endpoints

**Liquid Staked Endpoints turn a local inference server into a stake-backed, revenue-sharing marketplace.**

This system enables you to:
- Create inference endpoints backed by local model capacity
- Stake tokens to receive liquid ownership claims on endpoint revenue
- Run inference with cryptographically signed receipts
- Share revenue between operators and stakers
- Monitor uptime, performance, and rewards via operator dashboard

### Important Limitations

**Local Ledger Mode (Default):**
- Balances and transactions are stored in SQLite
- No real blockchain integration
- Suitable for testing, development, and closed environments
- Tokens cannot be transferred outside this system

**Solana Devnet Mode:**
- Requires deployed Anchor programs (`inference-token`, `liquid-staking`)
- Requires Solana CLI and wallet configuration
- Real SPL token transfers on devnet
- **Do not use on mainnet without full security audit**

**Inference:**
- Inference runs on this machine using local backends (Ollama, llama.cpp)
- Public access requires a tunnel (ngrok, Cloudflare Tunnel) or domain
- Stakers own liquid claims on endpoint revenue, not the machine itself
- No guarantee of uptime or performance

### Quick Start

```bash
# Set ledger mode (default: local)
export LEDGER_MODE=local

# Start the enterprise server
python enterprise_server.py

# Access the UI
open http://localhost:8000/liquid-endpoints
```

### API Endpoints

**Create an Endpoint:**
```bash
curl -X POST http://localhost:8000/api/liquid-endpoints/create \
  -H "Content-Type: application/json" \
  -d '{
    "owner_wallet": "wallet_address",
    "name": "My LLM Endpoint",
    "runtime_type": "ollama",
    "model_name": "llama2",
    "endpoint_url": "http://localhost:11434",
    "price_per_request": 1.0,
    "price_per_1k_tokens": 0.1,
    "revenue_share_bps": 7000
  }'
```

**List Endpoints:**
```bash
curl http://localhost:8000/api/liquid-endpoints
```

**Stake in an Endpoint:**
```bash
curl -X POST http://localhost:8000/api/liquid-endpoints/{endpoint_id}/stake \
  -H "Content-Type: application/json" \
  -d '{
    "wallet": "wallet_address",
    "amount": 1000.0,
    "lock_days": 0
  }'
```

**Run Inference:**
```bash
curl -X POST http://localhost:8000/api/liquid-endpoints/{endpoint_id}/infer \
  -H "Content-Type: application/json" \
  -d '{
    "wallet": "wallet_address",
    "prompt": "Explain quantum computing",
    "tier": "staker",
    "max_tokens": 512,
    "temperature": 0.7
  }'
```

**View Receipts:**
```bash
curl http://localhost:8000/api/liquid-endpoints/{endpoint_id}/receipts
```

**Claim Rewards:**
```bash
curl -X POST http://localhost:8000/api/liquid-endpoints/{endpoint_id}/claim \
  -H "Content-Type: application/json" \
  -d '{"wallet": "wallet_address"}'
```

**View Endpoint Stats:**
```bash
curl http://localhost:8000/api/liquid-endpoints/{endpoint_id}/stats
```

**Send Heartbeat (Operator):**
```bash
curl -X GET "http://localhost:8000/api/liquid-endpoints/{endpoint_id}/heartbeat?status=healthy&latency_ms=50&model_loaded=true&available_memory=8192&queue_depth=0"
```

**Pause/Resume Endpoint:**
```bash
curl -X POST http://localhost:8000/api/liquid-endpoints/{endpoint_id}/pause
curl -X POST http://localhost:8000/api/liquid-endpoints/{endpoint_id}/resume
```

### Features

**Liquid Staking:**
- Stake tokens to receive liquid tokens (lsEND-{id})
- Dynamic exchange rate based on total staked vs liquid supply
- Unstake anytime (no lockup required)
- Revenue share proportional to liquid token ownership

**Inference:**
- Support for Ollama, llama.cpp, OpenAI Proxy, and custom backends
- Cryptographically signed receipts for every inference
- Token-based pricing (per request or per 1K tokens)
- Usage tiers with discounts (free, staker, premium, validator)

**Operator Dashboard:**
- Real-time endpoint statistics
- Uptime monitoring via heartbeats
- Pause/resume endpoints
- View stakers, revenue, and APR estimates

**Data Persistence:**
- SQLite storage for endpoints, stakes, receipts, heartbeats
- Local ledger mode for testing without blockchain
- Optional Solana devnet integration

### Testing

**Run Smoke Test:**
```bash
python smoke_liquid_endpoints.py
```

This tests the complete workflow:
1. Initialize local ledger
2. Create endpoint
3. Fund wallet
4. Stake tokens
5. Run inference
6. Create signed receipt
7. Claim rewards
8. Verify data persistence

**Run Unit Tests:**
```bash
pytest test_liquid_endpoints.py -v
```

### Configuration

**Environment Variables:**
- `LEDGER_MODE` - `local` (default) or `solana_devnet`
- `RECEIPT_SIGNING_KEY` - Secret key for receipt signing (default: dev key)

**Inference Backends:**
- Ollama: `http://localhost:11434`
- llama.cpp: `http://localhost:8080`
- Custom: Configure endpoint URL accordingly

### Security Notes

- **Never commit private keys or secrets**
- **Use strong signing keys in production**
- **Solana programs are prototype quality - audit before mainnet**
- **Local ledger mode is for testing only**
- **Receipts provide proof of inference but do not guarantee correctness**

### Endpoint Statuses

- `active` - Accepting inference requests
- `paused` - Temporarily paused by operator
- `slashed` - Penalized (emergency - funds may be lost)
- `retired` - Decommissioned

## Decentralized Local Inference Node

**This machine becomes a decentralized inference worker: it registers capacity, runs local LLM jobs, signs receipts, and distributes endpoint revenue to liquid stakers.**

### Quick Start

```bash
# One-command launch
./start_decentralized_node.sh

# Or run full stack smoke test
python3 smoke_full_decentralized_stack.py

# Or run accounting audit
python3 accounting_audit.py
```

### Important Limitations

**Local Registry Mode (Default):**
- Node registry is simulated in SQLite
- No real peer discovery or network coordination
- Suitable for single-machine testing and development
- Nodes cannot discover each other across machines

**Solana Devnet Mode:**
- Requires deployed Anchor programs for on-chain node registry
- Requires Solana CLI and wallet configuration
- Real on-chain node registration and job posting
- **Do not use on mainnet without full security audit**

**Public Access:**
- Local mode requires ngrok, cloudflared, or custom domain for public access
- Tunnels require additional setup (auth tokens, installation)
- Public access exposes your machine to the internet
- No built-in DDoS protection or rate limiting

**Inference:**
- Inference runs on this machine using local backends
- Node identity provides cryptographic proof of job execution
- Signed receipts prove metadata (job ID, timestamps, hashes), not semantic correctness
- Stakers receive revenue share from endpoint, not machine ownership
- No guarantee of uptime, performance, or correctness

### Quick Start

```bash
# Set registry mode (default: local)
export REGISTRY_MODE=local

# Start the worker daemon
python3 decentralized_worker.py \
  --endpoint smoke_end_001 \
  --model llama2 \
  --runtime mock \
  --url http://localhost:11434 \
  --wallet your_wallet_address

# Or start the enterprise server and use the UI
python enterprise_server.py
# Access: http://localhost:8000/decentralized-node
```

### Worker CLI

```bash
python3 decentralized_worker.py \
  --endpoint ENDPOINT_ID \
  --model MODEL_NAME \
  --runtime RUNTIME_TYPE \
  --url ENDPOINT_URL \
  --wallet WALLET_ADDRESS \
  --heartbeat 30
```

**Runtime Types:**
- `mock` - Mock adapter for testing
- `ollama` - Ollama local inference
- `llama_cpp` - llama.cpp server

### API Endpoints

**Node Management:**
```bash
# Register node
curl -X POST http://localhost:8000/api/decentralized/node/register \
  -H "Content-Type: application/json" \
  -d '{
    "machine_name": "my-node",
    "models_available": ["llama2"],
    "endpoint_url": "http://localhost:11434",
    "wallet_address": "wallet_address"
  }'

# Get node identity
curl http://localhost:8000/api/decentralized/node/me

# Send heartbeat
curl -X POST http://localhost:8000/api/decentralized/node/heartbeat \
  -H "Content-Type: application/json" \
  -d '{
    "latency_ms": 50,
    "model_loaded": true,
    "available_memory": 8192,
    "queue_depth": 0
  }'

# List all nodes
curl http://localhost:8000/api/decentralized/nodes

# Find nodes by model
curl http://localhost:8000/api/decentralized/nodes/model/llama2
```

**Job Queue:**
```bash
# Submit job
curl -X POST http://localhost:8000/api/decentralized/jobs \
  -H "Content-Type: "application/json" \
  -d '{
    "requester_wallet": "wallet_address",
    "endpoint_id": "smoke_end_001",
    "model_name": "llama2",
    "prompt": "Explain quantum computing",
    "max_fee": 0.01
  }'

# Get job status
curl http://localhost:8000/api/decentralized/jobs/{job_id}

# List jobs
curl http://localhost:8000/api/decentralized/jobs?status=queued

# Get job receipt
curl http://localhost:8000/api/decentralized/jobs/{job_id}/receipt
```

**Public Access:**
```bash
# Start public link
curl -X POST http://localhost:8000/api/decentralized/public-link/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "local"}'

# Check status
curl http://localhost:8000/api/decentralized/public-link/status

# Stop public link
curl -X POST http://localhost:8000/api/decentralized/public-link/stop
```

### Features

**Node Identity:**
- Ed25519 key pair for cryptographic signing
- Node ID derived from public key hash
- Private key stored locally (never exposed)
- Public metadata includes models, endpoint URL, wallet

**Decentralized Registry:**
- Local SQLite registry for testing
- Solana devnet integration (placeholder)
- Node registration and heartbeat tracking
- Model-based node discovery

**Job Queue:**
- Submit inference jobs to queue
- Workers claim jobs by model
- Job status tracking (queued, running, completed, failed)
- Automatic job expiration

**Signed Receipts:**
- Every job produces cryptographically signed receipt
- Receipt signed by node identity
- Receipt signed by receipt signer
- Proves job execution metadata

**Revenue Distribution:**
- Fees split between operator and stakers
- Staker share based on liquid token ownership
- Rewards claimable via liquid endpoints
- Node earns operator revenue

**Public Access:**
- Local-only mode (localhost)
- Ngrok tunnel support
- Cloudflare tunnel support
- Custom domain configuration

### Testing

**Run Smoke Test:**
```bash
python3 smoke_decentralized_worker.py
```

This tests the complete workflow:
1. Generate node identity
2. Create local registry
3. Register node
4. Create liquid endpoint
5. Stake 1000 local tokens
6. Submit inference job
7. Worker claims job
8. Worker completes job using MockAdapter
9. Receipt verifies
10. Rewards are claimable
11. Print final accounting

### Configuration

**Environment Variables:**
- `REGISTRY_MODE` - `local` (default) or `solana_devnet`
- `NGROK_AUTH_TOKEN` - Ngrok auth token for tunneling
- `RECEIPT_SIGNING_KEY` - Secret key for receipt signing

**Node Identity:**
- Stored in `~/.llm_os/node_identity.json` (private)
- Public metadata in `~/.llm_os/node_public.json`
- Generate with `node_identity.py`

**Databases:**
- Node registry: `~/llm_decentralized_nodes.db`
- Job queue: `~/llm_inference_jobs.db`
- Liquid endpoints: `~/llm_liquid_endpoints.db`

### Security Notes

- **Never commit private keys or secrets**
- **Node identity private key must be protected**
- **Public access exposes your machine to the internet**
- **Signed receipts prove metadata, not semantic correctness**
- **Solana programs are prototype quality - audit before mainnet**
- **Local registry is a simulation, not real decentralization**

### Product Boundary

**This is NOT:**
- A true peer-to-peer network
- Blockchain-based coordination
- Automatic load balancing
- Global node discovery
- Production-grade DDoS protection

**This IS:**
- A local inference worker with cryptographic identity
- A job queue for inference requests
- Signed receipts proving job execution
- Revenue distribution to liquid stakers
- Public access via tunnels
- Testing framework for decentralized concepts

## License

MIT — Autonomous research prototype. No guaranteed income. See membra-core SECURITY.md before handling keys.
