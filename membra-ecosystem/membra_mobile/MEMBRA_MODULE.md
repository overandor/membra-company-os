# MEMBRA Module Contract — Mobile

## Role

Owner-side MEMBRA experience for onboarding, asset registration, proof capture, QR/NFC scans, relay requests, campaign participation, and wallet readiness.

## System inputs

- owner email / owner identity
- asset registration actions
- campaign acceptances
- proof photos or proof references
- QR/NFC test scans
- relay requests
- wallet readiness checks

## System outputs

- mobile event records
- proof-capture records
- owner action history
- sync-ready payloads for `Membra_api`, `Membra_proofbook`, `Membra_wallet`, and `membra-qr-gateway`

## Health

```text
GET /api/health
```

## Replit role

`service`

Runs as the owner-flow simulator until replaced by native/mobile frontend screens.

## Production boundary

Owner mobile actions are capture events. Public listing visibility still requires owner confirmation and review gates in the main MEMBRA flow.
