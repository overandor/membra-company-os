# Membra Money — Asset Support Matrix

## MVP Asset Types

| Asset | Native Chain | Wrapped/Claim Asset | Custody Requirement | Redemption Route | MVP Supported | Mainnet Ready |
|-------|-------------|---------------------|---------------------|------------------|---------------|---------------|
| SOL | Solana | Native SOL | Self-custody or hot wallet | Direct SPL transfer | Yes | Yes |
| USDC | Solana | SPL Token (USDC) | None (on-chain) | SPL transfer | Yes | Yes |
| BTC-backed Note | Bitcoin | SPL Token representation on Solana | Multisig / Federation / Wrapped provider | Off-chain BTC withdrawal via redemption processor | Yes | No (requires custody integration) |
| Token-2022 Note | Solana | Token-2022 with metadata | None (on-chain) | SPL transfer | Optional | Partial |

## Non-MVP Assets (Future)

| Asset | Status | Notes |
|-------|--------|-------|
| ETH | Not in MVP | Requires Wormhole/Portal bridge or wrapped provider |
| USDT | Not in MVP | SPL version available, similar to USDC |
| Merchant Credit | Not in MVP | Off-chain ledger, requires merchant integration |
| Loyalty Balances | Not in MVP | Off-chain ledger, requires partner APIs |

## Custody Models

| Model | Description | Risk Level | MVP Use |
|-------|-------------|------------|---------|
| Self-custody | User controls keys directly | Low | SOL, USDC |
| Multisig | 2-of-3 threshold signature | Medium | BTC reserve (recommended) |
| Federation | Community-operated mint federation | Medium-High | Future (Fedimint integration) |
| Wrapped Provider | Commercial custodian (e.g., BitGo, Fireblocks) | High | BTC backing if no multisig available |

## Redemption Routes

| Asset Type | Settlement Time | On-chain? | Fee |
|------------|------------------|-----------|-----|
| SOL | ~5 seconds | Yes | Network fee only |
| USDC | ~5 seconds | Yes | Network fee only |
| BTC-backed Note | 30-60 minutes | No (off-chain BTC tx) | BTC network fee + processor fee |

## Risk Disclosures Per Asset

- **SOL/USDC**: Standard SPL token risks (smart contract bugs, network congestion).
- **BTC-backed Notes**: Custody risk, reserve availability, redemption delays, compliance checks required.
- **Token-2022**: Newer standard, may have limited wallet support.
