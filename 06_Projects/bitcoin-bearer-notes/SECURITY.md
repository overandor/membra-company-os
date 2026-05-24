# Membra Money Security Policy

## Security Model

### Note Transfer Authority

**A note transfer must require one of:**
1. **Holder wallet signature** (current implementation)
2. **Valid bearer claim secret + unused status + expiration check** (future enhancement)
3. **Governed admin recovery path** (future enhancement)

**Serial number alone is NEVER authority.** The `transfer_note` instruction requires the `holder` to be a `Signer` and validates `note.current_holder == holder.key()`.

## Threat Model

| Threat | Mitigation | Status |
|--------|-----------|--------|
| Secret leakage in codebase | `.gitignore` excludes `.env*`, secret scan in CI | Done |
| Hardcoded DB passwords | `docker-compose.yml` uses `${VAR:-default}` pattern | Done |
| Timing attacks on PIN verification | `hmac.compare_digest` constant-time comparison | Done |
| Brute-force PIN guessing | Per-claim attempt count + cooldown lockout | Done |
| Claim link tampering | HMAC `claim_hash` per claim bundle | Done |
| Double-claim | Atomic `claimed` flag check + set | Done |
| Double-spend (note redemption) | `redeemed` flag + `NoteAlreadyRedeemed` error | Done |
| Unauthorized note transfer | Holder signature required | Done |
| Emergency pause | `set_paused` instruction (vault authority only) | Done |
| Math overflow | `checked_add` / `checked_sub` everywhere | Done |
| Fake balances in UI | No mock balances in production; data from API | Done |
| Private keys in logs/DB | Never logged; claim links never contain keys | Done |

## Claim Link Security

- PINs are hashed with **per-claim salt + global pepper**
- Claim URLs **never contain the PIN**
- QR codes **never encode the PIN**
- Delivery providers abstracted; **no claim link logging in production**
- Failed attempts tracked per-claim with exponential cooldown

## Reserve / Custody Trust Disclosure

BTC-backed notes are **custodial claims**, not native Bitcoin. Users do not hold private keys to the on-chain BTC reserve. The reserve operator is a trust boundary. See `docs/RESERVE_MODEL.md` for proof-of-reserves architecture.

## Compliance Boundaries

- No investment or profit claims
- No infinite passive rewards
- No private keys in claim links or logs
- Risk disclosure required before claims and redemptions
- Audit logs immutable with IP/user agent hashing

## Reporting Vulnerabilities

Email security@membra.io with details. Do not disclose publicly until fixed.
