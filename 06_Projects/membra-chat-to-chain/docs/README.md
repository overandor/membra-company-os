# MEMBRA Chat-to-Chain

Human stream to chat labor to artifact to appraisal to proof to funding to Solana payout.

## Quick Start
1. Copy `.env.example` to `.env` and fill values
2. Run `npm install` at root
3. Start backend: `python apps/api/src/server.py`
4. Start frontend: `npm run dev` in `apps/web`
5. Start iOS app: `npm run ios` in `apps/ios`
6. Deploy Anchor program: `anchor deploy` in `programs/membra_qr_gateway`

## Apps

- `apps/api` — FastAPI backend for chat-to-chain pipeline
- `apps/web` — Next.js frontend for artifact support & QR campaigns
- `apps/ios` — React Native / Expo iPhone app for Membra KPI marketplace (Dashboard, Inventory, Wallet, Upload, Proofbook)
- `packages/shared` — Shared types, schemas, and constants across all apps
