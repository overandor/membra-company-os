# Membra Money Production Checklist

## Pre-Launch

- [ ] Rotate all default secrets (`SECRET_KEY`, `PIN_PEPPER`, `CLAIM_LINK_SECRET`, `ENCRYPTION_KEY`)
- [ ] Configure production `.env` from `.env.example`
- [ ] Set `ENV=production`, `LOG_LEVEL=INFO`
- [ ] Set `SOLANA_RPC_URL` to mainnet-beta
- [ ] Configure `FRONTEND_BASE_URL` and `CORS_ORIGINS`
- [ ] Set `MIN_RESERVE_RATIO_BPS` (default 10000 = 100%)
- [ ] Configure reserve addresses in database
- [ ] Add delivery provider credentials (Twilio/SendGrid) or confirm Console provider in dev
- [ ] Run `pytest` and confirm all tests pass
- [ ] Run `anchor build` and confirm zero errors
- [ ] Run `anchor test` and confirm all tests pass
- [ ] Verify `.gitignore` ignores all `.env*` except `.env.example`
- [ ] Run secret scan: `grep -rE "(PRIVATE_KEY|SECRET|API_KEY|TOKEN)" --include="*.py" --include="*.rs" --include="*.ts"`

## Infrastructure

- [ ] Deploy PostgreSQL with backups enabled
- [ ] Deploy Redis with password auth
- [ ] Deploy backend API with health/readiness endpoints
- [ ] Configure NGINX with rate limiting and security headers
- [ ] Deploy frontend to Vercel/Netlify with CSP headers
- [ ] Configure Sentry DSN for error tracking
- [ ] Set up log aggregation (CloudWatch, Datadog, or similar)

## Security

- [ ] Verify `transfer_note` requires holder signature (not serial alone)
- [ ] Verify all mutating instructions check `vault.paused`
- [ ] Verify PIN verification uses `hmac.compare_digest`
- [ ] Verify claim links do not contain PIN or private keys
- [ ] Verify risk disclosure acceptance is tracked before claims/redemptions
- [ ] Verify audit logs capture all sensitive operations
- [ ] Verify reserve snapshots are created periodically
- [ ] Verify reserve ratio >= `MIN_RESERVE_RATIO_BPS` before allowing new mints

## Post-Launch

- [ ] Monitor `/api/v1/health` and `/api/v1/ready`
- [ ] Monitor reserve ratio alerts
- [ ] Review audit logs daily for anomalies
- [ ] Rotate secrets every 90 days
- [ ] Schedule quarterly security reviews
