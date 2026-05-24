# Membra Money API Reference

## Base URL

- Development: `http://localhost:8000/api/v1`
- Production: `https://api.membra.io/api/v1`

## Health

### GET /health
Returns service health status.

### GET /ready
Returns readiness including database connectivity.

## Notes

### GET /notes
Query params: `holder`, `redeemed`
List bearer notes with optional filtering.

### GET /notes/{serial_number}
Get a specific note by serial number.

### POST /notes/{serial_number}/transfer
Body: `holder`, `new_holder`
Transfer a note (requires holder signature).

### POST /notes/{serial_number}/burn-to-redeem
Body: `holder`, `btc_address`, `accepted_risk_disclosure`
Burn a note and queue BTC redemption.

### GET /notes/{serial_number}/status
Get note status and redemption state.

## CoinPack Claims

### POST /claims
Body: `creator`, `assets`, `pin`, `expires_hours`, `delivery_method`, `delivery_address`
Create a new CoinPack claim bundle.

### GET /claims/{claim_id}
Get claim info (no PIN returned).

### POST /coinpacks/{claim_id}/verify
Body: `pin`, `device_fingerprint`
Verify a claim without consuming it.

### POST /coinpacks/{claim_id}/claim
Body: `pin`, `device_fingerprint`, `wallet_address`, `accepted_risk_disclosure`
Claim a CoinPack with risk disclosure acceptance.

### POST /coinpacks/{claim_id}/expire
Expire a claim (admin/creator).

## Redemptions

### POST /redemptions
Query params: `holder`, `status`
List redemption requests.

### GET /redemptions/{redemption_id}
Get redemption details.

### POST /redemptions/{redemption_id}/process
Body: `status`, `txid`, `actual_fee`
Update redemption status.

### POST /redemptions/{redemption_id}/mark-paid
Mark redemption as completed.

### POST /redemptions/{redemption_id}/reject
Reject a redemption.

## Reserves

### GET /reserves
Get current reserve status with disclaimer.

### GET /reserves/proof
Get latest proof-of-reserves with snapshots.

### POST /reserves/snapshot
Query param: `reserve_account_id`
Create a new reserve snapshot.

### POST /reserves/verify
Body: `reserve_addresses`, `required_sats`
Verify reserves against required backing.

### GET /reserves/balance/{address}
Get BTC balance for an address.

## Audit

### GET /audit/events
Query params: `event_type`, `wallet_address`, `limit`
List audit events.

### GET /audit/subject/{subject_type}/{subject_id}
Get audit trail for a note or claim.

## Risk Disclosure

### GET /risk-disclosures/current
Get current risk disclosure text and hash.

### POST /risk-disclosures/accept
Body: `wallet_address`, `claim_id`, `accepted`
Record risk disclosure acceptance.

## Stats

### GET /stats
Get overall protocol statistics.
