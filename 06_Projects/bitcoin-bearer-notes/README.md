# Membra Money

A System for Off-Chain Transferable Bitcoin and Multi-Asset Bearer Notes

---

## Abstract

Membra Money is a proposed digital bearer-value system designed to enable instant, low-cost transfer of Bitcoin-backed and multi-asset monetary claims without requiring every transaction to be recorded directly on a blockchain. Instead of broadcasting each payment to a decentralized ledger, value is preloaded into transferable cryptographic bearer instruments referred to as **Membra Notes**. These notes may represent fixed denominations of Bitcoin, stablecoins, or other digital assets and can be transferred through SMS, QR codes, NFC, email, or direct device-to-device exchange.

The system aims to replicate the properties of physical cash in digital form: portability, instant settlement, divisibility, offline transfer capability, and bearer ownership. Blockchain interaction is reserved primarily for issuance, redemption, reserve balancing, and dispute resolution rather than every retail transaction.

Membra Money combines concepts from Bitcoin UTXOs, Chaumian ecash, statechains, tokenized claims, payment channels, and bearer voucher systems into a unified architecture intended for consumer payments and low-friction value transfer.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Conceptual Framework](#2-conceptual-framework)
3. [System Architecture](#3-system-architecture)
4. [Transaction Flow](#4-transaction-flow)
5. [Multi-Asset CoinPacks](#5-multi-asset-coinpacks)
6. [Security Challenges](#6-security-challenges)
7. [Comparison to Existing Systems](#7-comparison-to-existing-systems)
8. [Solana Prototype Architecture](#8-solana-prototype-architecture)
9. [Economic Implications](#9-economic-implications)
10. [Regulatory Considerations](#10-regulatory-considerations)
11. [Future Research](#11-future-research)
12. [Conclusion](#12-conclusion)
13. [Repository Structure](#repository-structure)
14. [Quick Start](#quick-start)
15. [API Reference](#api-reference)

---

## 1. Introduction

Blockchain systems such as Bitcoin provide decentralized monetary settlement but suffer from scalability limitations, transaction latency, and fees associated with on-chain consensus. Traditional Bitcoin transfers require every payment to be validated and permanently recorded across the network.

This architecture is highly secure but inefficient for high-frequency consumer transactions.

Membra Money proposes an alternative model:

> Use blockchain as the final settlement layer while enabling bearer-style transfer of pre-denominated value off-chain.

Under this model:

- A reserve of digital assets is deposited into a custody or federation layer.
- The reserve is split into transferable bearer claims.
- Claims circulate independently of the blockchain.
- Final redemption settles against the underlying reserve.

This creates a digital equivalent of banknotes backed by cryptographic reserves.

---

## 2. Conceptual Framework

### 2.1 Bearer Ownership

Bearer instruments derive value from possession rather than identity registration.

Examples include:

- Physical cash
- Cashier's checks
- Gift cards
- Stored-value vouchers

Membra extends this concept into digital cryptographic claims.

Ownership is determined by:

- possession of the claim token,
- cryptographic authorization,
- or control of the redemption path.

### 2.2 Denominated Bitcoin Claims

Bitcoin itself is indivisible at the key-control level:

- a private key controls an entire UTXO,
- not fractions independently transferable by multiple parties.

Membra instead creates:

- denomination-specific redemption claims,
- represented by transferable bearer notes.

**Example:**

1 BTC reserve may be represented as:

- 100 x 0.01 BTC notes
- 20 x 0.05 BTC notes
- 10 x 0.1 BTC notes

Each note acts similarly to a digital cash bill.

---

## 3. System Architecture

### 3.1 Core Components

#### A. Reserve Layer

Stores backing assets.

Possible reserve systems:

- Native BTC multisig vault
- Federated reserve
- Wrapped BTC custodian
- Stablecoin reserve accounts

Functions:

- issuance collateral,
- redemption settlement,
- proof-of-reserve auditing.

#### B. Membra Mint

The mint creates bearer notes against deposited reserves.

Responsibilities:

- issue denominations,
- maintain redemption mappings,
- monitor supply consistency,
- process note destruction on redemption.

#### C. Membra Notes

Digital bearer instruments representing fixed-value claims.

Properties:

- transferable,
- divisible by denomination,
- redeemable,
- cryptographically signed,
- optionally anonymous.

Supported transfer methods:

- SMS links
- QR codes
- NFC taps
- Email delivery
- Physical hardware transfer

#### D. Membra Wallet

Consumer application for:

- sending,
- receiving,
- storing,
- redeeming,
- and bundling notes.

Capabilities:

- multi-asset support,
- QR scanning,
- NFC transfer,
- claim-link management,
- merchant payments.

---

## 4. Transaction Flow

### 4.1 Issuance

1. User deposits BTC or supported assets.
2. Reserve layer confirms deposit.
3. Membra Mint generates denominations.
4. Notes are assigned to sender wallet.

### 4.2 Transfer

Sender:

- selects notes,
- bundles assets,
- generates claim package.

Transfer methods:

- SMS
- QR
- NFC
- email
- local wireless exchange

Recipient:

- claims notes into wallet,
- or forwards them without redemption.

### 4.3 Redemption

Recipient redeems notes:

1. Notes submitted to mint.
2. Mint validates authenticity.
3. Notes destroyed or invalidated.
4. Underlying asset released.

---

## 5. Multi-Asset CoinPacks

Membra supports bundled bearer transfers called **CoinPacks**.

A CoinPack may include:

- BTC notes
- stablecoins
- SOL
- ETH-backed claims
- merchant credit
- loyalty balances

**Example:**

```
CoinPack:
- $10 BTC
- $5 USDC
- 0.1 SOL
```

This allows unified cross-asset payment delivery through a single transfer channel.

### Claim Link Security

CoinPack claim links include:

- One-time claim ID
- PIN verification
- Expiration timer
- Device fingerprint binding
- Anti-double-claim logic
- Rate limiting
- Audit trail

---

## 6. Security Challenges

### 6.1 Double-Spending Problem

Digital bearer assets can be copied infinitely.

Therefore Membra requires anti-double-spend mechanisms.

Potential approaches:

- centralized validation,
- federated mints,
- hardware-sealed devices,
- statechain ownership transfer,
- blinded ecash protocols,
- one-time redemption signatures.

**Current implementation:** on-chain redemption status registry + serial number tracking.

### 6.2 Custody Risk

If reserves are centrally held:

- operators may become custodians,
- requiring transparency and auditing.

Mitigations:

- multisig reserves,
- proof-of-reserves,
- federation governance,
- periodic audits.

### 6.3 Link Theft

SMS and email are insecure transport layers.

Protections:

- claim expiration,
- PIN verification,
- device binding,
- rate limiting,
- multi-factor redemption.

---

## 7. Comparison to Existing Systems

| System      | Similarity              | Difference                       |
|-------------|------------------------|-----------------------------------|
| Opendime    | Bearer BTC transfer    | Hardware-only                     |
| Cashu       | Ecash minting          | Primarily Lightning-focused       |
| Fedimint    | Federated custody      | Community banking model           |
| Lightning   | Off-chain BTC          | Requires channels                 |
| Statechains | Off-chain ownership    | UTXO-focused                      |
| Paper Wallets| Bearer ownership      | Unsafe for repeated transfer      |

Membra combines:

- bearer transfer UX,
- denomination logic,
- multi-asset packaging,
- consumer messaging channels.

---

## 8. Solana Prototype Architecture

An initial implementation uses:

- **Solana blockchain**
- **SPL Tokens**
- **Token-2022**
- **Anchor framework**

Reasons:

- low fees,
- fast confirmation,
- mobile support,
- programmable tokenization.

BTC backing may be handled through:

- wrapped BTC,
- federated reserves,
- or external custody.

### Smart Contract Features

- Fixed denomination minting ($10, $50, $100, $500)
- Auto-incremented serial numbers
- Bearer transfer (no signature from sender)
- Burn-to-redeem with BTC address
- Anti-double-spend via on-chain redemption status
- Note expiration support
- Emergency pause/revoke
- Multi-asset CoinPack claim bundles
- PIN-protected claims
- Device fingerprint tracking

### Backend Services

- FastAPI redemption API
- PostgreSQL note registry
- Redis session/claim cache
- BTC reserve balance tracking
- Proof-of-reserves verification
- Claim link generation
- Anti-double-claim logic
- Audit logging
- Rate limiting
- Transaction indexing

### Frontend

- React + Tailwind CSS
- Phantom/Solflare wallet integration
- QR code generation/scanning
- CoinPack creation wizard
- Claim redemption flow
- Note portfolio view

---

## 9. Economic Implications

Membra transforms blockchain usage from:

- transaction-by-transaction settlement

into:

- reserve-backed periodic settlement.

Potential benefits:

- lower fees,
- instant payments,
- reduced blockchain congestion,
- improved retail usability,
- offline-capable transfers.

The system effectively introduces:

> digital bearer banking instruments for decentralized assets.

---

## 10. Regulatory Considerations

Potential classifications:

- stored-value instruments,
- money transmission,
- digital asset custody,
- prepaid access products.

Compliance requirements may include:

- KYC/AML,
- sanctions screening,
- reserve reporting,
- consumer disclosures.

Regulation varies by jurisdiction.

---

## 11. Future Research

Areas requiring further development:

- trust-minimized redemption,
- zero-knowledge anti-double-spend proofs,
- offline secure transfer,
- decentralized reserve governance,
- post-quantum bearer cryptography.

Potential future integrations:

- Lightning Network,
- Fedimint,
- Liquid,
- hardware wallets,
- mobile secure enclaves.

---

## 12. Conclusion

Membra Money proposes a framework for transforming blockchain assets into transferable digital bearer instruments capable of circulating independently from continuous blockchain settlement.

By separating:

- transaction circulation
- from
- final settlement,

the system seeks to provide:

- instant transferability,
- cash-like usability,
- reduced network load,
- and multi-asset interoperability.

The concept represents a hybrid between:

- cryptocurrency settlement networks,
- ecash systems,
- and traditional bearer-money mechanics.

If successfully implemented with robust anti-double-spend protections, Membra could serve as a scalable consumer payment layer for digital assets.

---

## Repository Structure

```
bitcoin-bearer-notes/
├── Anchor.toml                 # Anchor configuration
├── Cargo.toml                  # Rust workspace config
├── package.json                # Node dependencies
├── tsconfig.json               # TypeScript config
├── docker-compose.yml          # Local orchestration
├── README.md                   # This document
│
├── programs/
│   └── bitcoin-bearer-notes/
│       ├── Cargo.toml
│       └── src/
│           └── lib.rs          # Anchor smart contract
│
├── app/
│   ├── index.html              # Frontend entry
│   └── app.js                  # React application
│
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── core/
│   │   └── config.py           # Settings
│   ├── models/
│   │   └── database.py         # SQLAlchemy models
│   ├── services/
│   │   ├── btc_reserve.py      # BTC reserve tracking
│   │   └── claim_service.py    # Claim link management
│   └── api/
│       └── routes.py           # REST endpoints
│
└── tests/
    └── test_program.ts         # Anchor tests
```

---

## Quick Start

### Prerequisites

- Rust + Cargo
- Node.js 18+
- Solana CLI
- Anchor 0.29+
- Python 3.11+
- Docker & Docker Compose

### 1. Build the Solana Program

```bash
anchor build
```

### 2. Run Tests

```bash
anchor test
```

### 3. Start Backend

```bash
cd backend
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd app
# Serve with any static file server
python -m http.server 3000
```

### 5. Docker (Everything at Once)

```bash
docker-compose up --build
```

Access:
- API: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## API Reference

### Health

```
GET /api/v1/health
```

### Notes

```
GET    /api/v1/notes
GET    /api/v1/notes/{serial_number}
POST   /api/v1/notes/transfer
POST   /api/v1/notes/redeem
```

### CoinPack Claims

```
POST   /api/v1/claims
GET    /api/v1/claims/{claim_id}
POST   /api/v1/claims/{claim_id}/redeem
```

### BTC Reserves

```
GET    /api/v1/reserves
POST   /api/v1/reserves/verify
GET    /api/v1/reserves/balance/{address}
```

### Stats

```
GET    /api/v1/stats
```

---

## License

MIT License - See LICENSE file for details.

## Contributing

Pull requests welcome. Please open an issue first to discuss changes.

## Contact

- GitHub: [membra-money](https://github.com/membra-money)
- Twitter: [@membramoney](https://twitter.com/membramoney)
- Email: dev@membra.io
