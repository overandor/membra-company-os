# MEMBRA Architecture

## Overview
MEMBRA is a Chat-to-Chain Human Value Infrastructure.

## Components
- **Frontend**: Next.js app with Solana wallet adapters
- **Backend**: FastAPI with artifact lifecycle API
- **On-chain**: Anchor program for QR artifact support receipts
- **Shared**: Types, constants, schemas

## Data Flow
Chat -> Artifact -> Hash -> Appraisal -> Proof -> Funding -> Solana Payout
