# Membra Mobile & Wallet — iPhone App

React Native iPhone app built with Expo for the **overandor/Membra_kpi** API. Lives inside the `membra-chat-to-chain` monorepo at `apps/ios`.

## What This Is

A 5-tab iPhone app connecting to the [overandor/Membra_kpi](https://github.com/overandor/Membra_kpi) assetification marketplace backend:
- **Dashboard** — Live counts: photos, inventory, drafts, public listings, KPIs, proofs, event outbox
- **Inventory** — Browse inventory items, listing drafts, public listings; request/confirm visibility
- **Wallet** — Wallet ledger events & payout eligibility tracking
- **Upload** — Photo analysis & KPI dataset upload forms
- **Proofbook** — SHA-256 audit ledger entries & event outbox stream

## Tech Stack

- React Native 0.76
- Expo 52
- React Navigation (Bottom Tabs)
- TypeScript
- Monorepo workspace (`@membra/shared` for shared types/constants)

## Project Structure

```
src/
  api/
    membra_kpi_client.ts   # overandor/Membra_kpi API client
  components/
    KPICard.tsx            # Reusable metric card
  screens/
    DashboardScreen.tsx    # KPI counts from /api/dashboard
    InventoryScreen.tsx   # Items, drafts, public listings
    WalletScreen.tsx      # Ledger events & payouts
    UploadScreen.tsx      # Photo analyze & KPI upload
    ProofbookScreen.tsx   # Proofbook & outbox events
  types/
    membra_kpi.ts         # TypeScript types for Membra_kpi API
```

## Getting Started

From the monorepo root:
```bash
npm install
```

Then from this app directory:
```bash
cd apps/ios
npm run ios
```

Or from root via Turbo:
```bash
npm run dev
```

> **Note**: The app connects to `http://localhost:8000`. For physical iPhone testing, update `BASE_URL` in `src/api/membra_kpi_client.ts` to your machine's local network IP.

## Backend Integration

Connects to overandor/Membra_kpi endpoints:
- `GET /api/health`, `/api/ready`, `/api/dashboard`
- `GET /api/photos`, `/api/inventory`, `/api/sku-map`, `/api/kpis`
- `GET /api/listings/public`, `/api/listings/drafts`
- `POST /api/listings/{id}/request-visibility`, `/api/listings/{id}/confirm-visibility`
- `GET /api/wallet-events`, `POST /api/wallet-events`
- `GET /api/payout-eligibility`, `POST /api/payout-eligibility`
- `GET /api/proofbook`
- `GET /api/events/outbox`, `/api/events/outbox/stats`
- `POST /api/photo/analyze`, `/api/kpi/upload`

## License

MIT
