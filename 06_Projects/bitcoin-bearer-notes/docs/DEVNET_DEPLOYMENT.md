# Devnet Deployment Guide

**Three-stage deploy: Anchor program → Backend API → Frontend UI**

> **WARNING: Devnet only. Do not use real BTC or mainnet funds.**

---

## Stage 1: Deploy Anchor Program to Solana Devnet

### 1.1 Install Toolchain

```bash
git clone https://github.com/overandor/membramoney.git
cd membramoney/bitcoin-bearer-notes
bash scripts/install_solana.sh
```

Or manually:

```bash
# Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"

# Anchor
cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
avm install 0.29.0
avm use 0.29.0

# Verify
solana --version   # 1.17.0
anchor --version   # anchor-cli 0.29.0
rustc --version    # 1.75.0+
```

### 1.2 Configure for Devnet

```bash
solana config set --url devnet
solana-keygen new --outfile ~/.config/solana/id.json --no-passphrase
solana airdrop 2
```

### 1.3 Build & Test

```bash
anchor build
anchor test
```

If tests fail:
- Check `npm install` ran in project root
- Check wallet has devnet SOL: `solana balance`
- Check `solana-test-validator` is not already running on port 8899

### 1.4 Deploy

```bash
anchor deploy --provider.cluster devnet
```

Anchor prints the deployed program ID. **Save it.**

### 1.5 Update Program ID Everywhere

Replace the old program ID in:

- `Anchor.toml` — under `[programs.localnet]` and `[programs.devnet]`
- `programs/bitcoin-bearer-notes/src/lib.rs` — `declare_id!("...")`

Then rebuild to verify:

```bash
anchor build
```

### 1.6 Verify On-Chain

```bash
solana program show <DEPLOYED_PROGRAM_ID>
```

---

## Stage 2: Deploy Backend API

### 2.1 Option A — Docker Compose on VPS (Fastest)

```bash
cd membramoney/bitcoin-bearer-notes

# Create production env
cp backend/.env.example .env

# Edit .env — set real secrets
# SECRET_KEY, PIN_PEPPER, CLAIM_LINK_SECRET must be ≥32 chars
# DATABASE_URL must point to the docker-compose db service
# FRONTEND_BASE_URL must point to your deployed frontend domain
```

Required `.env` values for Docker Compose:

```env
SECRET_KEY=generate-a-long-random-secret-here-minimum-32-characters
PIN_PEPPER=generate-a-long-random-pepper-here-32-characters
CLAIM_LINK_SECRET=generate-a-long-random-claim-secret-32-chars
DATABASE_URL=postgresql+asyncpg://coinpack:strong_password@db:5432/coinpack
REDIS_URL=redis://redis:6379/0
POSTGRES_USER=coinpack
POSTGRES_PASSWORD=change-this-to-a-strong-password
POSTGRES_DB=coinpack
REDIS_PASSWORD=change-this-to-a-strong-redis-password
FRONTEND_BASE_URL=https://your-frontend-domain.com
CORS_ORIGINS=https://your-frontend-domain.com
BTC_NETWORK=testnet
MEMPOOL_API_BASE=https://mempool.space/testnet/api
MIN_RESERVE_RATIO_BPS=10000
SOLANA_RPC_URL=https://api.devnet.solana.com
PROGRAM_ID=<YOUR_DEPLOYED_PROGRAM_ID>
ENV=production
LOG_LEVEL=INFO
```

Deploy:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Verify:

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
```

### 2.2 Option B — Render (GitHub-connected)

1. Push repo to GitHub: `github.com/overandor/membramoney-backend`
2. In Render dashboard → New Web Service → Connect repo
3. Render reads `render.yaml` automatically
4. Set environment variables in Render dashboard:
   - `SECRET_KEY` — generate long random string
   - `PIN_PEPPER` — ≥32 chars
   - `CLAIM_LINK_SECRET` — ≥32 chars
   - `FRONTEND_BASE_URL` — your Vercel domain
   - `PROGRAM_ID` — your deployed Anchor program ID
5. Deploy

---

## Stage 3: Deploy Frontend to Vercel

### 3.1 Prepare Frontend

Point the frontend API client to your backend domain. If the frontend reads a constant, update it:

```javascript
const API_BASE = 'https://your-api-domain.com/api/v1';
```

### 3.2 Deploy

```bash
cd app
vercel
```

Or connect GitHub repo `overandor/membramoney-frontend` to Vercel dashboard. `vercel.json` is already configured with security headers and SPA routing.

---

## Stage 4: Run Devnet Smoke Test

After all three stages are deployed:

```bash
cd membramoney/bitcoin-bearer-notes
npm install
npx ts-node scripts/devnet_smoke_test.ts
```

Expected flow:
1. Connects to devnet
2. Derives vault PDA
3. Mints test note
4. Creates claim bundle
5. Verifies claim flow
6. Tests burn/redeem path
7. Confirms reserve API responds

---

## Deployment Order Summary

Run in this exact order:

```bash
# 1. Validate local repo
bash scripts/validate.sh

# 2. Build Anchor
anchor build

# 3. Test Anchor
anchor test

# 4. Deploy Anchor to devnet
anchor deploy --provider.cluster devnet

# 5. Update program ID everywhere, then rebuild
anchor build

# 6. Deploy backend
docker compose -f docker-compose.prod.yml up -d --build

# 7. Deploy frontend to Vercel
vercel

# 8. Run smoke test
npx ts-node scripts/devnet_smoke_test.ts
```

---

## Important

- **Do not use mainnet** until all MAINNET_READINESS.md items are checked.
- **Do not use real BTC** in devnet. Use testnet BTC or mock values.
- **Keep EXPERIMENTAL banners** in all UI surfaces.
- **Rotate secrets** before any production deployment: `SECRET_KEY`, `PIN_PEPPER`, `CLAIM_LINK_SECRET`.
- **Mainnet requires:** security audit, reserve/custody legal review, production KYC/AML policy, monitored proof-of-reserves, rate limiting, real SMS provider hardening, incident response, and successful devnet end-to-end testing.
