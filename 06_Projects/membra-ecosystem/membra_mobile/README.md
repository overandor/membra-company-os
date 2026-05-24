# Membra Mobile

**Membra Mobile is the owner-side proof app namespace for MEMBRA Labs and the MEMBRA Proof Network.**

It turns real-world owner actions into verified proof events that can activate campaigns, create audit records, and unlock reward eligibility.

## Company Context

- Company: **MEMBRA Labs**
- Flagship product: **MEMBRA Proof Network**
- Module: **Membra Mobile**
- Category: owner proof app, campaign offer app, QR/NFC scanner, proof-photo capture

## One-Line Thesis

Membra Mobile turns owner actions in the physical world into verified proof events.

## Product Role

Membra Mobile is the owner-facing app layer for:

- owner onboarding
- surface registration
- vehicle, window, wearable, bag, and sign capture
- campaign offer review
- media-kit receipt confirmation
- proof photo submission
- QR/NFC test scans
- reward status display
- claim/dispute submission
- profile and payout readiness

## Core Screens

1. home dashboard
2. register asset
3. campaign offers
4. media kit receipt
5. submit proof
6. QR/NFC scanner
7. reward status
8. claims and support
9. profile and payout readiness

## Proof Law

- no proof photo → no activation
- no receipt confirmation → no active media kit
- no approved proof → no reward eligibility
- no audit record → no trusted state change

## Integration Map

| Repo | Mobile Relationship |
|---|---|
| `overandor/Membra_api` | receives owner, asset, proof, and campaign actions |
| `overandor/Membra_ads` | defines campaign, media-kit, asset, and proof logic |
| `overandor/Membra_proofbook` | records proof hashes and audit records |
| `overandor/Membra_wallet` | tracks reward and payout readiness |
| `overandor/membra-qr-gateway` | displays dashboard analytics and public/private proof state |
| `overandor/Membra_admin-` | reviews owner-submitted proof and claims |
| `overandor/Membra_demo_data` | provides sample owner workflows for demo mode |

## Safety Rules

- no sensitive identity documents in public proof views
- no private location exposure without consent and access controls
- no reward display that implies guaranteed payout before review
- no upload flow without evidence retention policy
- no proof deletion without audit policy

## Productization Priority

This repo should become an Expo or React Native owner app after the backend and dashboard demo are stabilized.

Recommended build order:

1. static Expo shell
2. register asset screen
3. campaign offer screen
4. media-kit receipt screen
5. proof photo capture screen
6. QR/NFC scanner screen
7. reward status screen
8. API integration with `Membra_ads` or `Membra_api`

## Tech Stack

- **Framework**: Expo SDK 51 with React Native 0.74
- **Navigation**: Expo Router (file-based routing)
- **State Management**: Zustand with secure storage persistence
- **Language**: TypeScript
- **Styling**: React Native StyleSheet with dark/light theme support
- **Camera**: expo-camera / expo-image-picker
- **Scanner**: expo-barcode-scanner (QR/NFC placeholders)
- **Location**: expo-location
- **Auth**: JWT via expo-secure-store

## Project Structure

```
app/
  (tabs)/           # Main app tabs (home, assets, campaigns, proof, profile)
  (auth)/           # Auth screens (login)
  _layout.tsx       # Root layout with auth context
components/
  Button.tsx
  Card.tsx
  ScreenHeader.tsx
  TabIcon.tsx
constants/
  Colors.ts         # Theme colors
  Api.ts            # API endpoint definitions
hooks/
  useAuth.ts
  useTheme.ts
services/
  apiClient.ts      # HTTP client for Membra API
stores/
  authStore.ts      # Authentication state (Zustand + secure-store)
  appStore.ts       # App data state (assets, campaigns, proofs, etc.)
types/
  index.ts          # TypeScript interfaces
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Expo CLI (`npm install -g expo-cli`)
- iOS Simulator (macOS) or Android Studio Emulator

### Installation

```bash
git clone https://github.com/overandor/membra_mobile.git
cd membra_mobile
npm install
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your API URL:
# EXPO_PUBLIC_MEMBRA_API_URL=https://api.membra.labs/v1
```

### Running Locally

```bash
# Start the development server
npx expo start

# Press 'i' for iOS simulator
# Press 'a' for Android emulator
# Press 'w' for web
```

### Building for Production

```bash
# iOS build
npx expo run:ios --configuration Release

# Android build
npx expo run:android --variant release

# EAS Build (managed workflow)
npx eas build --platform all
```

## API Integration

The app is configured to connect to `Membra_api` and related services. Set `EXPO_PUBLIC_MEMBRA_API_URL` in your `.env` to point to your deployed backend.

| Endpoint | Purpose |
|---|---|
| `GET /v1/campaigns/available` | Fetch campaign offers |
| `POST /v1/campaigns/{id}/accept` | Accept a campaign |
| `POST /v1/ad-assets` | Register a new asset |
| `POST /v1/proof/photo` | Submit proof photo |
| `POST /v1/proof/qr-scan` | Record QR scan |
| `GET /v1/wallet/reward-status` | Check earnings |
| `POST /v1/claims` | Submit support claim |

## Current Stage

**Beta / Active Development**

- Expo shell with 5 tab screens implemented
- Asset registration with 6 asset types
- Campaign offers with accept/decline flow
- Proof submission (photo, QR, NFC placeholders)
- Profile with wallet readiness and claims
- Demo mode available without backend
- API client ready for `Membra_api` integration

## Remaining Work

- [ ] Integrate expo-camera for live photo capture
- [ ] Integrate expo-barcode-scanner for QR scanning
- [ ] Add react-native-maps for asset location pinning
- [ ] Connect to live `Membra_api` endpoints
- [ ] Add push notifications for proof approvals
- [ ] Media kit receipt confirmation flow
- [ ] Deep linking for campaign invites
- [ ] Biometric auth (Face ID / Touch ID)

## License

MIT — See [LICENSE](LICENSE) for details.