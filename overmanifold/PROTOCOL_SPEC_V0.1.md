# Overmanifold Protocol Specification v0.1 (Testnet)

**Status**: Frozen for Testnet Deployment  
**Version**: 0.1.0  
**Date**: 2026-05-18  
**Network**: Testnet (Read-Only Chain Integration)

## Executive Summary

Overmanifold Testnet v0.1 demonstrates that messages, commits, files, and blockchain transactions can become Merkle-verifiable economic endpoints routed through LLM-governed workers.

**Security Boundary**: No autonomous fund movement. All value transfer requires explicit human approval.

## Core Thesis

```text
human intent → economic state → Merkle proof → routing value
```

The protocol treats:
- Blockchains as worker networks
- Transactions as programmable endpoints  
- Repositories as tokenized micro-companies
- Messages as economic intent packets
- LLMs as semantic governors
- Liquidity as traversable manifold geometry

## Testnet Scope (v0.1)

### ✅ Included Features

#### 1. Merkle Provenance System
- Hierarchical Merkle tree construction for all state transitions
- SHA-256 hash-based provenance tracking
- Merkle proof generation and verification
- Recursive provenance linking across subsystems

#### 2. Transaction Endpoint Workers
- Real-time blockchain transaction observation (Ethereum, Solana)
- Lifecycle state management: mempool_seen → finalized
- Worker modes: one_shot, confirmation_triggered, cron, reorg_watch
- Push targets: Overmanifold, IPFS, GitHub, oracles, SMS, email
- KPI tracking: latency, finality confidence, liquidity impact

#### 3. LLM Mempool Review
- Observation of pending transactions across multiple chains
- Intent classification and semantic interpretation
- Liquidity impact estimation
- Arbitrage/MEV opportunity detection
- Recommendation generation (non-executing)

#### 4. GitHub Repository Tokenization
- Repository analysis and valuation
- Token generation for micro-company governance
- Contributor reward distribution based on contribution scores
- Governance proposal system
- Merkle-verifiable repository state

#### 5. SMS/Email Intent Syntax
- Overmanifold Message Language (OML) parsing
- Intent extraction from natural language
- Semantic packet construction
- Cryptographic authentication of messages
- Cross-channel intent routing

#### 6. Appraisal-Priced Token Minting
- Multi-oracle valuation system
- Collateral-backed token generation
- Dynamic pricing based on network participation
- Treasury-controlled supply mechanics
- Inverse mining (supply burn from useful work)

#### 7. Read-Only Chain Integration
- Ethereum mainnet read-only access via RPC
- Solana mainnet read-only access via RPC
- Transaction observation and decoding
- Balance and state queries (no signing)
- Event log streaming

### ❌ Explicitly Excluded (Security Boundaries)

#### 1. Autonomous Fund Movement
- **NO** automatic token transfers
- **NO** automatic liquidity provision
- **NO** automatic trading or arbitrage execution
- **NO** automatic treasury operations
- All value transfer requires explicit human approval

#### 2. Private Key Management
- **NO** private key storage or generation
- **NO** transaction signing capabilities
- **NO** wallet seed phrase handling
- Users maintain custody of their own keys

#### 3. Real Financial Value
- **NO** connection to real financial markets
- **NO** real money handling
- Testnet tokens only for demonstration
- No bridge to mainnet assets

#### 4. External API Execution
- **NO** automatic external API calls that move value
- **NO** integration with payment processors
- **NO** connection to banking systems

## Technical Architecture

### Core Mathematical Model

```python
M = (E, H, C, V, L)

Where:
E = endpoints (identity + liquidity + routing)
H = hashes (Merkle roots + state commitments)
C = channels (SMS, email, blockchain, API)
V = verifications (proofs + attestations)
L = liquidity states (manifold geometry)

State Transition:
S[t+1] = F(S[t], assetDeltas, proofConstraints, settlementOperator)
```

### System Components

#### 1. State Transition Engine
- Merkle-verifiable state transitions
- Semantic intent processing
- Capability-based access control
- Liquidity surface updates

#### 2. Geodesic Routing System
- Modified A* algorithm for optimal manifold traversal
- Trust-density weighted pathfinding
- Multi-hop liquidity routing
- Slippage and cost estimation

#### 3. Proof-of-Profit Consensus
- 15 work types for useful activity
- Reputation-based validator selection
- Inverse mining supply burn
- Treasury-controlled deflation

#### 4. LLM Governance Engine
- Intent interpretation and classification
- Risk assessment and policy recommendation
- Semantic fragment convergence
- Human-in-the-loop execution

## Security Model

### Threat Mitigation

#### 1. Input Validation
- All external inputs validated and sanitized
- SQL injection, XSS, command injection prevention
- Type checking and range validation
- Schema validation for all data structures

#### 2. Access Control
- Human approval gates for all value transfers
- Role-based access control (RBAC)
- Rate limiting per API endpoint
- IP-based access restrictions

#### 3. Data Protection
- Encryption at rest and in transit
- Privacy-preserving DID credentials
- No sensitive data in logs
- Secure secret management

#### 4. Operational Security
- Read-only blockchain access
- No private key storage
- Comprehensive audit logging
- Security scanning in CI/CD pipeline

### Approval Gates

All operations affecting value transfer require:

```python
def human_approval_gate(operation):
    if operation.affects_value():
        if not operation.has_human_approval():
            return False
    return True
```

## Network Configuration

### Testnet Parameters

```yaml
environment: testnet
network_id: overmanifold-testnet-v0.1
chain_config:
  ethereum:
    rpc: https://eth-mainnet.alchemyapi.io/v2/DEMO_KEY
    chain_id: 1
    confirmations_required: 12
    read_only: true
  solana:
    rpc: https://api.mainnet-beta.solana.com
    confirmations_required: 32
    read_only: true

security:
  approval_required: true
  max_transaction_value: 0  # No real value
  rate_limit_per_minute: 60
  allowed_origins:
    - http://localhost:3000
    - https://testnet.overmanifold.io

features:
  transaction_workers: true
  repo_tokenization: true
  llm_governance: true
  sms_transport: true
  browser_validators: true
  autonomous_trading: false  # EXPLICITLY DISABLED
```

## API Endpoints

### Health & Monitoring
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe
- `GET /health/detailed` - Component status

### Transaction Workers
- `POST /transactions/observe` - Observe blockchain transaction
- `GET /transactions/{chain}/{txHash}` - Get transaction endpoint state
- `POST /transactions/{chain}/{txHash}/merkle` - Create Merkle proof
- `POST /transactions/{chain}/{txHash}/approve` - Human approval gate

### Repository Tokenization
- `POST /repos/tokenize` - Tokenize GitHub repository
- `GET /repos/{repoId}` - Get repository micro-company
- `POST /repos/{repoId}/governance/propose` - Create governance proposal
- `POST /repos/{repoId}/approve` - Human approval for repo operations

### Intent Transport
- `POST /intent/submit` - Submit semantic intent
- `GET /intent/{intentId}` - Get intent status
- `POST /intent/{intentId}/approve` - Human approval for intent execution

## Data Models

### Transaction Endpoint Worker
```python
T = (χ, h, τ, φ, μ, κ, α)

χ = chain
h = tx hash
τ = lifecycle state
φ = finality policy
μ = Merkle commitment
κ = KPI vector
α = permitted action set
```

### Repository Micro-Company
```python
R = (repo_id, token, metrics, contributors, governance, merkle_root)

token = (token_id, total_supply, price_per_token, governance_rights)
metrics = (community_score, activity_score, quality_score, health_score)
governance = (voting_period, proposal_threshold, quorum_threshold)
```

## Success Criteria

Testnet v0.1 is considered successful when:

1. ✅ Transaction endpoint workers successfully observe real blockchain transactions
2. ✅ LLM governance provides accurate intent classification
3. ✅ GitHub repositories can be tokenized with governance
4. ✅ SMS/email intents are parsed and routed correctly
5. ✅ Merkle proofs are generated and verified
6. ✅ Human approval gates prevent autonomous value transfer
7. ✅ System operates stably for 30+ days
8. ✅ Security audit finds no critical vulnerabilities

## Known Limitations

1. **Read-Only Access**: Cannot execute transactions on mainnet chains
2. **Simulated Value**: Token prices and valuations are for demonstration
3. **Single Region**: Initial deployment in single geographic region
4. **Limited LLM**: Uses basic intent interpretation (can be upgraded)
5. **Manual Approval**: All value transfer requires human intervention

## Future Roadmap (Post-v0.1)

### v0.2 (Security Audit)
- Professional security audit
- Penetration testing
- Smart contract formal verification
- Bug bounty program launch

### v0.3 (Mainnet Preparation)
- Private key management integration
- Transaction signing capabilities
- Real liquidity pool deployment
- Bridge to mainnet assets

### v1.0 (Mainnet Launch)
- Full autonomous operation (with safety rails)
- Real financial value integration
- Multi-region deployment
- Production-grade SLAs

## Compliance & Legal

### Testnet Compliance
- No real financial instruments
- No user funds handling
- Educational and research purposes only
- Clear demarcation from production systems

### Data Privacy
- GDPR-compliant data handling
- Privacy-preserving DID credentials
- No personal data in logs
- User data deletion capabilities

## Appendix A: Security Audit Scope

Pre-audit security checklist:

- [ ] Input validation coverage analysis
- [ ] Authentication/authorization review
- [ ] Cryptographic implementation verification
- [ ] API security assessment
- [ ] Infrastructure security review
- [ ] Dependency vulnerability scan
- [ ] Code quality analysis
- [ ] Operational security procedures

## Appendix B: Monitoring Metrics

Key metrics for testnet:

- Transaction observation success rate
- LLM intent classification accuracy
- Merkle proof verification time
- API response times (P50, P95, P99)
- Error rates by component
- Human approval gate performance
- System uptime and availability

## Appendix C: Emergency Procedures

### Incident Response
1. Immediate shutdown capability
2. Data rollback procedures
3. Communication protocols
4. Post-incident analysis process

### System Recovery
- Database backup restoration
- Redis cache rebuilding
- Service restart procedures
- Configuration rollback

---

**This specification is frozen for Testnet v0.1 deployment. Any changes require a new version and full review.**