# MEMBRA Bridge Ecosystem - Hierarchical Merkle Root Taxonomy

A comprehensive Solana bridging system with mathematical proof and tokenization of all files, IPFS backup, phone-based wallet addresses, SMS mining/rewards, and full oracle integration.

## Architecture Overview

### Core Components

1. **Hierarchical Merkle Root Taxonomy**
   - File system scanner with cryptographic hashing
   - Multi-level merkle tree construction (file → directory → filesystem → root)
   - Mathematical proof of file integrity and ownership
   - Tokenization of file assets on Solana

2. **IPFS Integration**
   - Automatic backup of all files to IPFS
   - Content-addressed storage with CID verification
   - Redundancy and distributed availability
   - Gateway integration for fast retrieval

3. **Phone-Based Wallet System**
   - Phone number as preregistered wallet address
   - Tokens premined for each phone number
   - Merkle tree derived from phone number
   - SMS acts as mining mechanism
   - Receiving SMS = rewarded
   - Sending SMS = sponsored and rewarded

4. **Oracle System**
   - 30+ endpoint integration for price discovery
   - KPI tracking for arbitrage signals
   - Collateralization and regulation mechanisms
   - Real-time price verification

5. **ZK Verification Network**
   - M5 Pro MacBooks as resource stakers
   - Zero-knowledge proof verification
   - LLM inference as validator service
   - LLM as main developer and oracle

6. **Bridge Liquidity Layer**
   - Novel liquidity bridging mechanism
   - Cross-chain compatibility
   - Automated market making
   - Real-time arbitrage opportunities

## System Flow

```
File System → Hash → Merkle Tree → IPFS Backup → Tokenization
                                                ↓
Phone Number → Wallet Address → Premined Tokens → SMS Mining
                                                ↓
Oracle System → KPI Tracking → Price Discovery → Arbitrage
                                                ↓
ZK Verification → LLM Inference → Validation → Rewards
                                                ↓
Bridge Liquidity → Cross-Chain → Market Making → Profit
```

## Quick Start

### Prerequisites

- Python 3.11+
- Solana CLI
- Docker
- IPFS node
- Phone number with SMS capability

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/membra-bridge-ecosystem
cd membra-bridge-ecosystem

# Install Python dependencies
pip install -r requirements.txt

# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Start IPFS node
ipfs init
ipfs daemon

# Deploy to Docker
docker-compose up -d
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

## Module Documentation

### 1. File Tokenization Module

Scans file systems, generates cryptographic hashes, and creates hierarchical merkle trees.

```python
from membra_bridge.file_tokenizer import FileTokenizer

tokenizer = FileTokenizer(root_path="/path/to/scan")
merkle_root = tokenizer.scan_and_tokenize()
```

### 2. IPFS Backup Module

Automatically backs up files to IPFS and manages content addressing.

```python
from membra_bridge.ipfs_manager import IPFSManager

ipfs = IPFSManager()
cid = ipfs.backup_file("/path/to/file")
```

### 3. Phone Wallet Module

Maps phone numbers to Solana wallet addresses with premined tokens.

```python
from membra_bridge.phone_wallet import PhoneWallet

phone_wallet = PhoneWallet(phone_number="+1234567890")
wallet_address = phone_wallet.get_wallet_address()
```

### 4. SMS Mining Module

Handles SMS mining rewards and sponsorship mechanisms.

```python
from membra_bridge.sms_miner import SMSMiner

miner = SMSMiner(phone_number="+1234567890")
reward = miner.process_sms(incoming=True, content="Hello")
```

### 5. Oracle Integration Module

Connects to 30+ endpoints for price discovery and KPI tracking.

```python
from membra_bridge.oracle_client import OracleClient

oracle = OracleClient()
prices = oracle.get_prices()
kpi_signals = oracle.get_kpi_signals()
```

### 6. ZK Verification Module

Manages zero-knowledge proof verification for M5 Pro MacBooks.

```python
from membra_bridge.zk_verifier import ZKVerifier

verifier = ZKVerifier()
proof = verifier.generate_proof(file_hash)
is_valid = verifier.verify_proof(proof)
```

## API Endpoints

### File Tokenization
- `POST /api/tokenize` - Tokenize a file or directory
- `GET /api/merkle/{root}` - Get merkle tree by root hash
- `GET /api/proof/{file_hash}` - Get proof for specific file

### IPFS Operations
- `POST /api/ipfs/backup` - Backup file to IPFS
- `GET /api/ipfs/{cid}` - Retrieve file from IPFS
- `GET /api/ipfs/status` - Check IPFS node status

### Phone Wallet
- `POST /api/wallet/register` - Register phone number
- `GET /api/wallet/{phone}` - Get wallet address
- `GET /api/balance/{phone}` - Get token balance

### SMS Mining
- `POST /api/sms/send` - Process sent SMS
- `POST /api/sms/receive` - Process received SMS
- `GET /api/sms/rewards/{phone}` - Get mining rewards

### Oracle Data
- `GET /api/oracle/prices` - Get current prices
- `GET /api/oracle/kpi` - Get KPI signals
- `GET /api/oracle/status` - Check oracle status

### ZK Verification
- `POST /api/zk/generate` - Generate ZK proof
- `POST /api/zk/verify` - Verify ZK proof
- `GET /api/zk/status` - Check verification status

## Deployment

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods
```

## Security Considerations

- No private keys or seeds in code
- Environment-based configuration
- Secure SMS verification
- ZK proof validation
- Rate limiting on all endpoints
- Audit logging for all transactions

## License

MIT License - See LICENSE file for details

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## Support

For support, email support@membra.network or join our Discord community.