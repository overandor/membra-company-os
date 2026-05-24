# Membra Mobile API Flow

## Owner onboarding

POST /v1/owners
POST /v1/owners/profile

## Asset registration

POST /v1/ad-assets
POST /v1/windows
POST /v1/vehicles
POST /v1/wearables

## Campaign interaction

GET /v1/campaigns/available
POST /v1/campaigns/{campaign_id}/accept
POST /v1/campaigns/{campaign_id}/decline

## Media-kit flow

POST /v1/media-kits/{kit_id}/confirm-receipt
POST /v1/proof/photo
POST /v1/proof/location

## QR and NFC flow

POST /v1/proof/qr-scan
POST /v1/proof/nfc-tap

## Reward flow

GET /v1/wallet/reward-status
GET /v1/wallet/payout-history

## Claim flow

POST /v1/claims
GET /v1/claims/{claim_id}
