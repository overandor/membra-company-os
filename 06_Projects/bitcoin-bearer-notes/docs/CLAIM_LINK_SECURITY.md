# Claim Link Security Architecture

## Threat Model

| Threat | Mitigation |
|--------|-----------|
| Brute-force PIN | Per-claim attempt limit + cooldown |
| Timing attack on PIN | `hmac.compare_digest` constant-time compare |
| Claim link tampering | HMAC `claim_hash` integrity check |
| PIN storage exposure | Per-claim salt + global pepper |
| QR code leaks PIN | QR never encodes PIN |
| URL leaks PIN | URL never contains PIN |
| Delivery interception | Encrypted payload + delivery abstraction |
| Replay attack | Claim ID + proof_hash tied to wallet + timestamp |
| Double-claim | Atomic `claimed` flag |

## PIN Hashing

```
pin_hash = SHA256(pin + ":" + salt + ":" + pepper)
```

- `salt`: 16-byte random per claim
- `pepper`: 32+ char global secret (`PIN_PEPPER`)
- Compared with `hmac.compare_digest`

## Claim Link Format

Production:
```
https://membra.io/claim/{claim_id}
```

**Never:**
- `?pin=123456`
- `?key=private_key`
- `?seed=mnemonic`

## Anti-Brute Force

1. Each failed attempt increments `attempt_count`
2. After `PIN_MAX_ATTEMPTS` (default 5), cooldown begins
3. Cooldown duration: `PIN_LOCKOUT_MINUTES` (default 30 min)
4. Attempts reset after cooldown expires
5. All attempts logged in `claim_attempts` table

## Delivery Providers

- `ConsoleProvider`: Development only, masked output
- `TwilioProvider`: SMS delivery
- `SendGridProvider`: Email delivery
- Factory selects first configured provider; falls back to Console

## Audit

Every claim creation, verification attempt, and success is logged with:
- IP address
- User agent
- Device fingerprint (hashed)
- Wallet address (if available)
- Proof hash for integrity
