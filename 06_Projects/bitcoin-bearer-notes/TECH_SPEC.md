# Membra Money — Technical Specification

**Version:** 0.1.0-alpha
**Date:** May 15, 2026
**Status:** Draft / Pre-MVP
**Classification:** Founder / Engineering Document

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [User Flow](#2-user-flow)
3. [Money Flow](#3-money-flow)
4. [Smart Contract Design](#4-smart-contract-design)
5. [Backend Design](#5-backend-design)
6. [Wallet UI](#6-wallet-ui)
7. [Security Model](#7-security-model)
8. [Compliance Model](#8-compliance-model)
9. [MVP Roadmap](#9-mvp-roadmap)
10. [Appendices](#10-appendices)

---

## 1. System Overview

### 1.1 Mission

Membra Money enables **instant, low-cost transfer of Bitcoin-backed and multi-asset monetary claims** through cryptographic bearer instruments that circulate off-chain while settling on-chain only at issuance and redemption.

### 1.2 Core Thesis

Blockchain is a settlement court, not a payment rail.

Most consumer payments do not require global consensus. They require:
- Finality guarantees
- Bearer portability
- Instant settlement
- Low cost

Membra separates **circulation** from **settlement**, using the blockchain as a vault and arbiter rather than a transaction processor.

### 1.3 Product Definition

| Layer | Component | Technology |
|-------|-----------|------------|
| Settlement | Reserve vault | BTC multisig + SPL token mint |
| Issuance | Membra Mint | Anchor program on Solana |
| Circulation | Membra Notes | Off-chain bearer claims |
| Transfer | Membra Wallet | React + Phantom/Solflare |
| Packaging | CoinPacks | Multi-asset claim bundles |
| Redemption | Redemption API | FastAPI + PostgreSQL + Redis |

### 1.4 Key Terminology

| Term | Definition |
|------|------------|
| **Membra Note** | A fixed-denomination bearer claim on a reserve asset |
| **CoinPack** | A multi-asset bundle of Membra Notes delivered via a single claim link |
| **Membra Mint** | The smart contract + service that issues notes against reserves |
| **Reserve Vault** | The BTC/SOL/USDC pool backing all circulating notes |
| **Claim Link** | A one-time URL containing a CoinPack, protected by PIN |
| **Redemption** | The process of burning a note and receiving the underlying asset on-chain |

### 1.5 Non-Goals (MVP)

- No native BTC L1 smart contracts (use wrapped/federated reserves)
- No offline P2P without internet (QR/NFC still need claim server)
- No privacy-preserving blind signatures (MVP uses transparent registry)
- No fiat on/off ramps (MVP is crypto-native)
- No merchant POS hardware integration (MVP is wallet-to-wallet)

---

## 2. User Flow

### 2.1 Actor Definitions

| Actor | Role |
|-------|------|
| **Sender** | User who creates and transfers notes/CoinPacks |
| **Recipient** | User who receives and claims notes/CoinPacks |
| **Redeemer** | User who burns notes to receive underlying assets |
| **Reserve Operator** | Entity managing the BTC/SOL reserve vault |
| **Mint Operator** | Entity with admin rights to the Membra Mint program |

### 2.2 Flow 1: Mint a Note

```
1. Sender opens Membra Wallet
2. Connects Phantom/Solflare wallet
3. Selects "Mint Note"
4. Chooses denomination ($10 / $50 / $100 / $500)
5. Approves SPL token transfer to Reserve Vault
6. Backend confirms reserve deposit
7. Anchor program mints Note with serial number
8. Note appears in Sender's wallet
```

**Time:** ~5 seconds (Solana confirmation)

### 2.3 Flow 2: Transfer a Note (QR + Signature)

```
1. Sender opens note in wallet
2. Clicks "Transfer"
3. Wallet generates QR code: coinpack://note/{serial}
4. Recipient scans QR with Membra Wallet
5. Recipient initiates transfer; Sender signs with wallet
6. Wallet calls transfer_note instruction (holder is Signer)
7. Ownership updates on-chain
8. Both parties see updated balances
```

**Security:** `transfer_note` requires the `holder` to be a `Signer`. Serial number alone is never authority.

**Time:** ~2 seconds

### 2.4 Flow 3: Send a CoinPack (SMS)

```
1. Sender opens "Create CoinPack"
2. Selects assets: $10 BTC, $5 USDC, 0.1 SOL
3. Sets PIN (4-8 digits)
4. Chooses expiration (1h / 24h / 3d / 7d)
5. Enters recipient phone number
6. Backend generates claim_id + claim_url
7. SMS sent: "You received a CoinPack... Claim: link"
8. Sender sees "Pending" status in wallet
```

**Time:** ~3 seconds

### 2.5 Flow 4: Claim a CoinPack

```
1. Recipient opens SMS link
2. Browser opens Membra claim page
3. Enters PIN
4. (Optional) Creates wallet if no existing wallet
5. System validates PIN + checks not expired + anti-double-claim
6. On success: assets transferred to recipient wallet
7. Sender receives "Claimed" notification
```

**Time:** ~5 seconds

### 2.6 Flow 5: Redeem a Note

```
1. Holder opens note in wallet
2. Clicks "Redeem"
3. Enters BTC receiving address
4. Confirms burn
5. Anchor program marks note as redeemed
6. Backend queues BTC withdrawal
7. BTC sent to address (30-60 min)
8. Note marked "Redeemed" in wallet
```

**Time:** Instant burn; BTC settlement 30-60 min

### 2.7 Flow 6: Forward Unopened CoinPack

```
1. Recipient receives CoinPack but doesn't claim
2. Clicks "Forward" instead of "Claim"
3. Enters new phone number
4. Backend creates new claim link
5. Original link invalidated
6. New recipient gets SMS
```

**Security:** Original PIN may or may not be reset.

---

## 3. Money Flow

### 3.1 Reserve Accounting

All Membra Notes are **100% backed** by assets held in the Reserve Vault.

```
Reserve Vault (Solana SPL + BTC multisig)
├── BTC Reserve Address: bc1q...
│   └── Balance: 16.50000000 BTC
├── USDC Token Account
│   └── Balance: $45,000.00
└── SOL Token Account
    └── Balance: 1,200.00 SOL

Liability Tracking (PostgreSQL)
├── Total Notes Minted: 1,247 notes
├── Total BTC Backing Required: 9.35000000 BTC
├── Total USDC Backing Required: $28,450.00
├── Total SOL Backing Required: 890.00 SOL
└── Reserve Ratio: 1.765x (overcollateralized)
```

### 3.2 Issuance Flow

```
User Deposits
     │
     ▼
┌──────────────┐
│ Reserve Vault │
│ (SPL + BTC)   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Membra Mint   │
│ Anchor Program│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Membra Note   │
│ (PDA on Solana)│
└───────────────┘
```

**Invariants:**
- `sum(all note denominations) <= reserve_balance`
- `reserve_ratio >= 1.0` at all times
- Each note has globally unique serial number

### 3.3 Circulation Flow

```
┌────────┐      bearer transfer      ┌────────┐
│ Alice  │ ────────────────────────► │  Bob   │
│ Note#1 │  (no blockchain touched)  │ Note#1 │
└────────┘                           └────────┘
```

Notes can change hands:
- Via QR code scan
- Via NFC tap
- Via SMS/email CoinPack
- Via wallet address input

**No blockchain interaction occurs during circulation.**

### 3.4 Redemption Flow

```
User Requests Redemption
         │
         ▼
┌─────────────────┐
│  Burn Note      │  ← Anchor program marks redeemed=true
│  (Solana TX)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Queue Withdrawal│  ← Backend creates RedemptionRequest
│ (PostgreSQL)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ BTC/USDC/SOL    │  ← Multisig signs withdrawal
│ Withdrawal       │
└────────┬────────┘
         │
         ▼
   User Receives Asset
```

**Settlement time:**
- SOL/USDC: ~5 seconds
- BTC: 30-60 minutes (1-2 confirmations)

### 3.5 Fee Model (MVP)

| Action | Fee |
|--------|-----|
| Mint Note | 0% (reserve deposit only) |
| Transfer Note | Free |
| Send CoinPack | Free |
| Claim CoinPack | Free |
| Redeem Note | Network fee only (BTC tx fee) |
| Reserve Operator | Revenue from yield on reserves (future) |

---

## 4. Smart Contract Design

### 4.1 Program: `bitcoin_bearer_notes`

**Language:** Rust + Anchor 0.29.0
**Platform:** Solana (devnet → mainnet)
**Program ID:** `Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS`

### 4.2 Data Structures

#### Vault (Singleton PDA)

```rust
pub struct Vault {
    pub authority: Pubkey,           // Admin pubkey
    pub total_btc_reserved: u64,   // Total BTC in satoshis
    pub total_notes_minted: u64,
    pub total_notes_redeemed: u64,
    pub paused: bool,
    pub bump: u8,
}
```

**Size:** 82 bytes
**PDA Seeds:** `["vault"]`

#### Note (PDA per serial)

```rust
pub struct Note {
    pub serial_number: u64,
    pub denomination: u64,           // In satoshis
    pub mint_authority: Pubkey,
    pub current_holder: Pubkey,      // Bearer: possession = ownership
    pub original_holder: Pubkey,
    pub metadata_uri: String,        // Max 200 chars
    pub created_at: i64,
    pub expires_at: Option<i64>,
    pub redeemed: bool,              // Anti-double-spend flag
    pub redeemed_at: Option<i64>,
    pub btc_receiving_address: Option<String>,
    pub revoked: bool,
    pub revoked_at: Option<i64>,
    pub claim_id: Option<[u8; 32]>,
    pub bump: u8,
}
```

**Size:** ~580 bytes
**PDA Seeds:** `["note", serial_number.to_le_bytes()]`

#### ClaimBundle (PDA per claim_id)

```rust
pub struct ClaimBundle {
    pub claim_id: [u8; 32],
    pub creator: Pubkey,
    pub asset_types: Vec<String>,    // ["BTC", "USDC", "SOL"]
    pub amounts: Vec<u64>,           // [100000, 5000000, 100000000]
    pub expires_at: i64,
    pub pin_hash: [u8; 32],          // SHA256 of PIN
    pub claimed: bool,
    pub claimer: Option<Pubkey>,
    pub claimed_at: Option<i64>,
    pub device_fingerprint: Option<String>,
    pub bump: u8,
}
```

**Max Size:** ~590 bytes (10 assets max)
**PDA Seeds:** `["claim", claim_id]`

### 4.3 Instruction Set

| Instruction | Accounts | Description |
|-------------|----------|-------------|
| `initialize` | vault, authority, system_program | Create protocol vault |
| `mint_note` | note, vault, mint_authority, holder, authority | Mint new note against reserves |
| `transfer_note` | note, vault, new_holder, holder | Transfer requires holder signature |
| `burn_and_redeem` | note, vault, holder | Burn note + queue redemption |
| `revoke_note` | note, vault, authority | Emergency revoke (admin only) |
| `set_expiration` | note, holder | Set expiration time |
| `set_paused` | vault, authority | Emergency pause/unpause |
| `create_claim_bundle` | claim_bundle, creator | Create multi-asset CoinPack |
| `claim_bundle` | claim_bundle, claimer | Claim with PIN + device fingerprint |

### 4.4 Denomination Table

| USD Value | BTC Equivalent (@$65k) | Satoshis |
|-----------|------------------------|----------|
| $10 | 0.00015384 BTC | 153,846 sats |
| $50 | 0.00076923 BTC | 769,231 sats |
| $100 | 0.00153846 BTC | 1,538,462 sats |
| $500 | 0.00769230 BTC | 7,692,308 sats |

**Note:** Actual implementation uses USD-pegged satoshi amounts updated by oracle or fixed at mint time. MVP uses fixed denominations.

### 4.5 Event Log

All state changes emit Anchor events for indexing:

```
VaultInitialized { authority, vault }
NoteMinted { serial_number, denomination, holder, mint_authority }
NoteTransferred { serial_number, from, to }
NoteRedeemed { serial_number, holder, btc_address, denomination }
NoteRevoked { serial_number, authority }
ClaimBundleCreated { claim_id, creator, asset_count, expires_at }
ClaimBundleClaimed { claim_id, claimer, assets, amounts }
```

### 4.6 Error Codes

| Code | Meaning |
|------|---------|
| `VaultPaused` | Protocol is in emergency pause |
| `InvalidDenomination` | Amount not in allowed set |
| `NoteAlreadyRedeemed` | Double-spend attempt detected |
| `NoteRevoked` | Note was revoked by admin |
| `NotNoteHolder` | Caller doesn't possess the note |
| `AlreadyClaimed` | CoinPack already claimed |
| `ClaimExpired` | Claim link past expiration |
| `InvalidPin` | PIN hash mismatch |
| `TooManyAssets` | CoinPack exceeds 10 assets |

---

## 5. Backend Design

### 5.1 Architecture

```
┌─────────────────────────────────────────────┐
│              API Gateway (Nginx)              │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────┐
│     FastAPI (Python 3.11)   │
│  • Request validation         │
│  • Rate limiting              │
│  • JWT auth (future)          │
└──────┬──────────────┬───────┘
       │              │
┌──────▼──────┐  ┌────▼──────┐
│ PostgreSQL  │  │  Redis    │
│ (Asyncpg)   │  │  Claims   │
│ • Notes     │  │ • Sessions│
│ • Claims    │  │ • Rate    │
│ • Redemptions│ │   limits  │
│ • Audit     │  └───────────┘
└─────────────┘
       │
┌──────▼──────────────────────────────┐
│ External APIs                       │
│ • Solana RPC (Helius/QuickNode)    │
│ • BTC Mempool.space (balance check) │
│ • Jupiter (SOL swaps, future)      │
└─────────────────────────────────────┘
```

### 5.2 Database Schema

#### Notes Table

```sql
CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    serial_number BIGINT UNIQUE NOT NULL,
    denomination BIGINT NOT NULL,
    mint_authority VARCHAR(44) NOT NULL,
    current_holder VARCHAR(44) NOT NULL,
    original_holder VARCHAR(44) NOT NULL,
    metadata_uri VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    redeemed BOOLEAN DEFAULT FALSE,
    redeemed_at TIMESTAMPTZ,
    btc_receiving_address VARCHAR(100),
    revoked BOOLEAN DEFAULT FALSE,
    claim_id VARCHAR(64),
    tx_signature VARCHAR(100),
    INDEX idx_holder_redeemed (current_holder, redeemed),
    INDEX idx_serial (serial_number)
);
```

#### Claim Bundles Table

```sql
CREATE TABLE claim_bundles (
    id SERIAL PRIMARY KEY,
    claim_id VARCHAR(64) UNIQUE NOT NULL,
    creator VARCHAR(44) NOT NULL,
    asset_types JSONB NOT NULL,
    amounts JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    pin_hash VARCHAR(64) NOT NULL,
    claimed BOOLEAN DEFAULT FALSE,
    claimer VARCHAR(44),
    claimed_at TIMESTAMPTZ,
    device_fingerprint VARCHAR(128),
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    delivery_method VARCHAR(20) DEFAULT 'link',
    delivery_address VARCHAR(255),
    INDEX idx_claim_id (claim_id),
    INDEX idx_expires (expires_at, claimed)
);
```

#### Claim Attempts Table

```sql
CREATE TABLE claim_attempts (
    id SERIAL PRIMARY KEY,
    claim_id VARCHAR(64) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent VARCHAR(255),
    device_fingerprint VARCHAR(128),
    attempted_at TIMESTAMPTZ DEFAULT NOW(),
    success BOOLEAN DEFAULT FALSE,
    failure_reason VARCHAR(50),
    pin_attempt VARCHAR(10),
    INDEX idx_claim_attempt (claim_id, attempted_at)
);
```

#### Redemption Requests Table

```sql
CREATE TABLE redemption_requests (
    id SERIAL PRIMARY KEY,
    serial_number BIGINT NOT NULL,
    holder VARCHAR(44) NOT NULL,
    btc_address VARCHAR(100) NOT NULL,
    denomination BIGINT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    txid VARCHAR(100),
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    estimated_fee BIGINT,
    actual_fee BIGINT,
    error_message TEXT,
    INDEX idx_serial (serial_number),
    INDEX idx_holder (holder)
);
```

#### Audit Logs Table

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    wallet_address VARCHAR(44),
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_event (event_type, created_at),
    INDEX idx_wallet (wallet_address, created_at)
);
```

### 5.3 API Endpoints

#### Health

```
GET /api/v1/health
Response: { "status": "healthy", "service": "coinpack-api", "version": "0.1.0" }
```

#### Notes

```
GET    /api/v1/notes?holder={pubkey}&redeemed={bool}
GET    /api/v1/notes/{serial_number}
POST   /api/v1/notes/{serial_number}/transfer
  Body: { "holder": string, "new_holder": string }
POST   /api/v1/notes/{serial_number}/burn-to-redeem
  Body: { "holder": string, "btc_address": string, "accepted_risk_disclosure": bool }
```

#### Claims

```
POST   /api/v1/claims
  Body: {
    "creator": string,
    "assets": [{ "type": "BTC", "amount": 0.0001 }],
    "pin": string,
    "expires_hours": int,
    "delivery_method": "sms",
    "delivery_address": "+1234567890"
  }

GET    /api/v1/claims/{claim_id}
  Returns: claim info without PIN

POST   /api/v1/claims/{claim_id}/redeem
  Body: {
    "claim_id": string,
    "pin": string,
    "device_fingerprint": string
  }
```

#### Reserves

```
GET    /api/v1/reserves
  Returns: total_reserved, total_minted, reserve_ratio, fully_backed

POST   /api/v1/reserves/verify
  Body: { "reserve_addresses": ["bc1q..."], "required_sats": int }

GET    /api/v1/reserves/balance/{btc_address}
```

#### Stats

```
GET    /api/v1/stats
  Returns: total_notes, redeemed_notes, total_claims, claimed_claims
```

### 5.4 Services

#### BTCReserveService

- `get_address_balance(address)` → Query mempool.space API
- `verify_reserves(addresses, required_sats)` → Compare reserve to liabilities
- `generate_proof_of_reserves(message, addresses)` → SHA256 commitment

#### RedemptionProcessor

- `validate_btc_address(address)` → Regex + length validation
- `estimate_fee(sats_per_vbyte)` → ~141 vbytes * rate
- `queue_redemption(serial, btc_address, denomination)` → Create DB record

#### ClaimService

- `create_claim(...)` → Generate claim_id, hash PIN, store in DB
- `validate_claim(...)` → Check PIN, expiration, anti-double-claim, brute-force protection
- `get_claim_stats(claim_id)` → Attempt history

### 5.5 Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Auth endpoints | 5 | 1 minute |
| General API | 100 | 1 minute |
| Claim redemption | 10 | 1 minute |
| PIN attempts per claim | 5 | 30 minutes |

Implemented via Redis + slowapi.

---

## 6. Wallet UI

### 6.1 Technology Stack

- **Framework:** React 18 (UMD via CDN for MVP)
- **Styling:** Tailwind CSS (CDN)
- **Wallet Adapter:** Phantom + Solflare via `@solana/web3.js`
- **QR Codes:** qrcode.js
- **Icons:** Inline SVG

### 6.2 Screens

#### Home / Dashboard

```
┌─────────────────────────────┐
│  Membra Money               │
│  [Connect Wallet]           │
├─────────────────────────────┤
│  Vault Stats                │
│  • 16.50 BTC reserved       │
│  • 1,247 notes minted       │
│  • 312 notes redeemed       │
├─────────────────────────────┤
│  [My Notes] [Mint]         │
│  [Create CoinPack] [Claim] │
└─────────────────────────────┘
```

#### My Notes

```
┌─────────────────────────────┐
│  Note #0042        [ACTIVE] │
│  0.00153846 BTC    ($100)   │
│  [QR] [Transfer] [Redeem]   │
├─────────────────────────────┤
│  Note #0089       [REDEEMED]│
│  0.00015384 BTC     ($10)   │
│  → bc1q...xyz               │
└─────────────────────────────┘
```

#### Mint Note

```
┌─────────────────────────────┐
│  Select Denomination        │
│  [ $10 ] [ $50 ]           │
│  [$100 ] [$500 ]           │
│                             │
│  [ Mint Note ]              │
└─────────────────────────────┘
```

#### Create CoinPack

```
┌─────────────────────────────┐
│  Create CoinPack            │
│                             │
│  BTC    [ 0.0001 ]         │
│  USDC   [ 5.00    ] +      │
│  SOL    [ 0.1     ] +      │
│                             │
│  PIN: [****]                │
│  Expires: [24 hours ▼]     │
│                             │
│  [ Generate CoinPack ]     │
└─────────────────────────────┘
```

#### Claim CoinPack

```
┌─────────────────────────────┐
│  Claim Your CoinPack        │
│                             │
│  Enter PIN: [____]         │
│                             │
│  [ Claim Assets ]           │
│                             │
│  Expires in: 18h 32m       │
└─────────────────────────────┘
```

#### Redeem Modal

```
┌─────────────────────────────┐
│  Redeem Note #0042          │
│                             │
│  Amount: 0.00153846 BTC      │
│  Value: $100.00              │
│                             │
│  BTC Address:               │
│  [ bc1q...                  ]│
│                             │
│  [ Cancel ] [ Burn & Redeem]│
└─────────────────────────────┘
```

### 6.3 Design System

- **Background:** `#0a0e1a` (deep navy)
- **Primary:** `#f59e0b` (amber/gold)
- **Secondary:** `#f97316` (orange)
- **Text:** White + gray scale
- **Font:** Inter (body), JetBrains Mono (numbers, addresses)
- **Cards:** `rgba(255,255,255,0.03)` with `rgba(255,255,255,0.08)` border
- **Success:** `#22c55e` (green)
- **Danger:** `#ef4444` (red)
- **Warning:** `#f59e0b` (amber)

---

## 7. Security Model

### 7.1 Threat Matrix

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| Double-spend | Critical | Medium | On-chain redemption registry |
| Reserve theft | Critical | Low | Multisig (2-of-3), cold storage |
| Claim link theft | High | High | PIN + expiration + device binding |
| Brute-force PIN | High | Medium | Rate limiting (5 attempts / 30 min) |
| Smart contract bug | Critical | Medium | Audit, formal verification (future) |
| Backend compromise | High | Low | Minimal keys, read-only reserves |
| Social engineering | Medium | High | User education, clear UX warnings |
| Replay attack | High | Medium | Nonce-based claims, one-time redemption |
| Sybil attack | Low | Medium | Cost to mint, claim rate limits |

### 7.2 Anti-Double-Spend Architecture

**Problem:** Digital data copies perfectly. A malicious user could:
1. Copy note data
2. Redeem original
3. Attempt to redeem copy

**Solution Layers:**

1. **On-chain redemption status:** Every note PDA has `redeemed: bool`. Once true, burn instruction fails with `NoteAlreadyRedeemed`.

2. **Serial number uniqueness:** Notes use auto-incremented serials. No two notes share a serial.

3. **Backend reconciliation:** PostgreSQL mirrors on-chain state. Backend rejects redemption if `redeemed=true` in DB.

4. **Claim bundle atomicity:** CoinPack claims are single-use. `claimed=true` permanently locks the bundle.

### 7.3 Claim Link Security

**Attack:** Intercept SMS/email and claim before legitimate recipient.

**Defenses:**

| Layer | Mechanism |
|-------|-----------|
| Transport | HTTPS only, HSTS |
| Authentication | 4-8 digit PIN, SHA256 hashed |
| Expiration | 1h - 7d configurable |
| Brute-force | 5 attempts → 30 min lockout |
| Device binding | Fingerprint hash logged (future: required match) |
| One-time | Claim ID is single-use |
| Audit | Every attempt logged with IP + UA |
| Forwarding | Original invalidated on forward |

### 7.4 Reserve Security

| Control | Implementation |
|---------|----------------|
| Multisig | 2-of-3 threshold |
| Key distribution | 3 separate HSMs / geographic locations |
| Cold storage | 95% of reserves offline |
| Proof-of-reserves | Monthly public attestation |
| Insurance | Third-party custody insurance (future) |
| Emergency pause | Smart contract `set_paused` + backend circuit breaker |

### 7.5 Smart Contract Security

- **Upgrade path:** Program is not upgradeable (immutable for trust)
- **Admin keys:** Authority can pause/revoke, cannot mint without reserves
- **Overflow checks:** Rust `checked_add` / `checked_sub`
- **Input validation:** Denomination whitelist, address length checks
- **Reentrancy:** Not applicable (Solana sequential execution)

---

## 8. Compliance Model

### 8.1 Regulatory Classification

Membra Money may be classified as:

| Jurisdiction | Likely Classification |
|--------------|------------------------|
| USA | Stored-value / prepaid access (FinCEN) |
| EU | E-money / payment instrument (EMD2) |
| UK | Electronic money (FCA) |
| Singapore | Digital payment token (MAS) |

### 8.2 Compliance Architecture (Future)

#### Tier 1: Light (MVP)

- No KYC for sending/receiving notes under $1,000/day
- Optional KYC for redemption above $10,000
- Basic rate limiting
- Audit logs retained 1 year

#### Tier 2: Standard (Post-MVP)

- KYC for all redemption
- Travel Rule compliance for transfers >$1,000
- OFAC/sanctions screening
- Suspicious Activity Report (SAR) filing
- AML monitoring
- Customer due diligence

#### Tier 3: Full (Enterprise)

- Full KYC/AML for all users
- Real-time transaction monitoring
- Regulatory reporting
- Licensed as money transmitter
- Insurance-backed reserves
- Annual audits

### 8.3 Data Retention

| Data Type | Retention | Encryption |
|-----------|-----------|------------|
| Note registry | Indefinite | Public (on-chain) |
| Claim attempts | 2 years | AES-256 at rest |
| Audit logs | 7 years | AES-256 at rest |
| User PII | Per jurisdiction | AES-256 + TLS |
| Wallet addresses | Indefinite | Public |

### 8.4 Privacy Considerations

**Current:**
- Notes are pseudonymous (wallet addresses, not names)
- Claim links require no account
- No IP logging for basic transfers

**Future (Cashu integration):**
- Blinded signatures for mint issuance
- No link between mint and user
- Amount privacy via range proofs

---

## 9. MVP Roadmap

### Phase 1: Foundation (Weeks 1-4)

| Week | Deliverable |
|------|-------------|
| 1 | Finalize smart contract, deploy to devnet |
| 2 | Build backend API + database |
| 3 | Build wallet UI (React) |
| 4 | Integration testing, bug fixes |

**Scope:**
- [x] Fixed denomination notes ($10/$50/$100/$500)
- [x] Mint + transfer + redeem
- [x] QR code transfer
- [x] CoinPack creation (SMS delivery)
- [x] Claim with PIN
- [x] Reserve tracking
- [x] Basic audit logs

### Phase 2: Security Hardening (Weeks 5-8)

| Week | Deliverable |
|------|-------------|
| 5 | Smart contract audit (external) |
| 6 | Implement rate limiting + brute-force protection |
| 7 | HSM integration for reserve keys |
| 8 | Penetration testing |

**Scope:**
- [ ] Professional audit by OtterSec or Neodyme
- [ ] Formal verification of critical paths
- [ ] Multisig reserve deployment
- [ ] Bug bounty program

### Phase 3: Multi-Asset Expansion (Weeks 9-12)

| Week | Deliverable |
|------|-------------|
| 9 | Add USDC support |
| 10 | Add SOL support |
| 11 | Add ETH-wrapped support |
| 12 | Merchant payment SDK |

**Scope:**
- [ ] SPL token mints for each asset
- [ ] Cross-asset CoinPacks
- [ ] Merchant QR generation
- [ ] Point-of-sale demo

### Phase 4: Mainnet Launch (Weeks 13-16)

| Week | Deliverable |
|------|-------------|
| 13 | Mainnet program deployment |
| 14 | Production backend (AWS/GCP) |
| 15 | Mobile app (React Native) |
| 16 | Public launch + marketing |

**Scope:**
- [ ] Mainnet deployment
- [ ] Production monitoring (Datadog/Sentry)
- [ ] iOS/Android apps
- [ ] PR + community building

### Phase 5: Advanced Features (Months 5-12)

- [ ] Cashu blinded ecash integration
- [ ] Lightning Network redemption
- [ ] Fedimint federation support
- [ ] Hardware wallet integration (Ledger, Trezor)
- [ ] NFC tap-to-pay
- [ ] Offline mesh network (Bluetooth/BLE)
- [ ] Cross-chain bridges (ETH, BSC, Arbitrum)
- [ ] DAO governance for reserve parameters

---

## 10. Appendices

### A. Glossary

| Term | Definition |
|------|------------|
| **Bearer Instrument** | Asset where possession conveys ownership |
| **CoinPack** | Multi-asset claim bundle |
| **Denomination** | Fixed face value of a note |
| **Double-Spend** | Attempting to redeem the same value twice |
| **Mint** | Entity that issues notes against reserves |
| **PDA** | Program Derived Address (Solana) |
| **Redemption** | Exchanging a note for underlying asset |
| **Reserve** | Pool of assets backing circulating notes |
| **SPL Token** | Solana token standard |
| **UTXO** | Unspent Transaction Output (Bitcoin) |

### B. Technology Stack Summary

| Layer | Technology |
|-------|------------|
| Blockchain | Solana |
| Smart Contracts | Rust + Anchor 0.29 |
| Tokens | SPL + Token-2022 |
| Backend | Python 3.11 + FastAPI |
| Database | PostgreSQL 15 + asyncpg |
| Cache | Redis 7 |
| Frontend | React 18 + Tailwind CSS |
| Wallets | Phantom, Solflare, Backpack |
| BTC API | mempool.space |
| Deployment | Docker + Docker Compose |
| Monitoring | Sentry + Prometheus (future) |

### C. API Examples

#### Mint a Note

```bash
curl -X POST http://localhost:8000/api/v1/notes/mint \
  -H "Content-Type: application/json" \
  -d '{
    "denomination": 153846,
    "holder": "7xKX...",
    "metadata_uri": "ipfs://Qm..."
  }'
```

#### Create CoinPack

```bash
curl -X POST http://localhost:8000/api/v1/claims \
  -H "Content-Type: application/json" \
  -d '{
    "creator": "7xKX...",
    "assets": [
      {"type": "BTC", "amount": 0.0001},
      {"type": "USDC", "amount": 5.0}
    ],
    "pin": "123456",
    "expires_hours": 24,
    "delivery_method": "sms",
    "delivery_address": "+1234567890"
  }'
```

#### Claim CoinPack

```bash
curl -X POST http://localhost:8000/api/v1/claims/abc123.../redeem \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "abc123...",
    "pin": "123456",
    "device_fingerprint": "fp-abc-123"
  }'
```

### D. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0-alpha | 2026-05-15 | Initial specification |

### E. Document Ownership

| Role | Owner |
|------|-------|
| Author | Cascade AI Assistant |
| Reviewer | [Pending founder review] |
| Approver | [Pending founder approval] |

---

**End of Technical Specification**
