# Reserve Model

## Overview

Membra Money BTC-backed notes are **custodial claims** against a BTC reserve. The reserve is tracked via:
- `ReserveAccount`: On-chain addresses under custody
- `ReserveSnapshot`: Periodic balance + liability snapshots
- `Liability`: Outstanding note obligations

## Reserve Ratio

```
reserve_ratio = reserve_balance / outstanding_liabilities
```

- Expressed in basis points (10000 = 100%)
- `MIN_RESERVE_RATIO_BPS` default: 10000 (100%)
- New mints blocked if ratio < minimum

## Wallet Types

| Type | Description | Risk |
|------|-------------|------|
| custodian | Single commercial custodian | High (counterparty) |
| multisig | M-of-N threshold signature | Medium |
| federation | Community-operated federation | Medium-High |
| wrapped_provider | Tokenized BTC wrapper (e.g., WBTC) | High |

## Proof-of-Reserves

1. Query mempool.space for each `ReserveAccount` balance
2. Sum `Liability` where `status = outstanding`
3. Compute ratio
4. Store `ReserveSnapshot` with proof hash
5. Expose via `/api/v1/reserves/proof`

## Degraded Status

If a reserve source is unreachable:
- `degraded_source = true`
- `can_mint_new_notes = false`
- Disclaimers shown in UI and API responses

## Trust Disclosure

Users do **not** hold private keys to on-chain BTC. The reserve operator is a trust boundary. Reserve data is informational and depends on configured source availability.
