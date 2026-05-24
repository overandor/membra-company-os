# Mainnet Readiness Assessment

## Status: Devnet Candidate (Not Mainnet-Ready)

- **Production candidate hardening:** COMPLETE
- **Backend validation:** PASS (compileall + pytest service tests)
- **Anchor program compilation:** PASS (`cargo check` clean)
- **Anchor build/test:** BLOCKED — requires local Solana CLI + build-sbf toolchain
- **Devnet deployment:** NOT YET ATTEMPTED

This document tracks the gap between the current codebase and mainnet deployment.

## Completed Hardening

- [x] Anchor program: holder signature required for note transfer
- [x] Anchor program: vault pause checks on all mutating instructions
- [x] Anchor program: explicit serial_number argument in mint_note
- [x] Claim service: per-claim PIN salt + server-side pepper
- [x] Claim service: constant-time PIN verification (hmac.compare_digest)
- [x] Claim service: HMAC claim hash integrity check
- [x] Claim service: brute-force cooldown lockout
- [x] Backend: ReserveAccount, ReserveSnapshot, Liability models
- [x] Backend: proof-of-reserves endpoint with ratio enforcement
- [x] Backend: RiskDisclosureAcceptance tracking
- [x] Backend: Delivery provider abstraction (Console/Twilio/SendGrid)
- [x] Frontend: Risk banner, reserve view, audit log view
- [x] Frontend: Two-step claim with risk disclosure acceptance
- [x] Config: PIN_PEPPER, CLAIM_LINK_SECRET, MIN_RESERVE_RATIO_BPS
- [x] Security: .gitignore excludes .env*, no secrets in logs
- [x] Deployment: render.yaml, vercel.json, docker-compose.prod.yml, nginx.conf
- [x] Documentation: SECURITY.md, PRODUCTION_CHECKLIST.md, API_REFERENCE.md, ASSET_SUPPORT_MATRIX.md, CLAIM_LINK_SECURITY.md, RESERVE_MODEL.md, COMPLIANCE_BOUNDARIES.md

## Required Before Mainnet

### 1. Anchor Program Validation
- [ ] `anchor build` passes with zero errors
- [ ] `anchor test` passes all tests on devnet
- [ ] `cargo clippy` passes with no warnings
- [ ] Program deployed to devnet and manually tested
- [ ] Program ID updated from placeholder (`Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS`) to real deployment

### 2. Backend Test Coverage
- [ ] Integration tests for all API endpoints
- [ ] Database migration tests (Alembic)
- [ ] Reserve snapshot creation tested against live mempool.space API
- [ ] Claim link end-to-end flow tested (create → verify → claim)
- [ ] Rate limiting tested under load
- [ ] Audit log immutability verified

### 3. Reserve Accounting
- [ ] Reserve addresses configured and funded
- [ ] Liability table populated from on-chain note mints
- [ ] Reserve ratio calculation verified manually
- [ ] Snapshot cron job or scheduled task configured
- [ ] Alerting for reserve ratio < MIN_RESERVE_RATIO_BPS

### 4. Claim Link Audit
- [ ] No PINs in server logs (verify log masking)
- [ ] Claim URLs do not contain PINs or secrets
- [ ] QR codes verified to contain only claim ID
- [ ] Delivery provider logging masked
- [ ] Claim attempt table reviewed for sensitive data leakage

### 5. Devnet End-to-End
- [ ] Mint note flow: wallet → Anchor → backend → database
- [ ] Transfer note flow: QR scan → signature → on-chain update
- [ ] Create CoinPack flow: assets → PIN → claim URL → delivery
- [ ] Claim CoinPack flow: URL → PIN → risk disclosure → wallet receive
- [ ] Redeem note flow: burn → redemption queue → BTC payout
- [ ] Reserve proof display accurate and up-to-date

### 6. Operational Readiness
- [ ] Secret rotation procedure documented
- [ ] Backup and recovery tested for PostgreSQL
- [ ] Monitoring dashboards configured (Sentry, Prometheus)
- [ ] Incident response runbook
- [ ] Compliance review completed (legal assessment of bearer notes)

### 7. Mainnet-Specific
- [ ] Solana mainnet RPC configured and tested
- [ ] Real BTC reserve custody solution operational
- [ ] KYC/AML flow implemented (if required by jurisdiction)
- [ ] Insurance or bonding arrangement for reserve
- [ ] Bug bounty program or security audit

## Validation Commands

Run locally in Windsurf:

```bash
cd bitcoin-bearer-notes
anchor build
anchor test
cd backend
python -m compileall .
pytest
```

## Risk Acceptance

Until all items above are checked, this system should:
- Run on devnet only
- Use test BTC reserves (not customer funds)
- Require explicit opt-in for all test transactions
- Display "EXPERIMENTAL — DO NOT USE WITH REAL FUNDS" banners
