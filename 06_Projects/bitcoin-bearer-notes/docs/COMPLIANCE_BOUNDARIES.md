# Compliance Boundaries

## Forbidden Claims

The following must never appear in documentation, marketing, UI, or smart contract comments:

- Investment returns, yield, or profit guarantees
- "Passive income" or "rewards" without clear fee/service basis
- Claims that notes are equivalent to native Bitcoin
- Claims of FDIC insurance or government backing
- Promises of instant or guaranteed redemption
- Misrepresentation of reserve backing as 100% auditable by users

## Required Disclaimers

All user-facing surfaces must display:

1. **Custodial Risk**: BTC-backed notes are claims, not native BTC
2. **Reserve Trust**: Reserve/custody/federation risk exists
3. **Claim Expiration**: Claim links can expire; loss of access = loss of claimability
4. **Transport Risk**: SMS/email are insecure; links may be intercepted
5. **Experimental Software**: Use only funds you can afford to lose
6. **No Profit Guarantee**: Membra Money does not guarantee profit, yield, or liquidity

## Risk Disclosure Flow

- User must accept risk disclosure before claiming a CoinPack
- User must accept risk disclosure before redeeming a note
- Acceptance recorded with wallet, timestamp, IP hash, user agent hash
- Acceptance hash computed for audit integrity

## KYC/AML

Not implemented in MVP. Future phases may require:
- Identity verification for redemption above thresholds
- Travel rule compliance for large transfers
- Suspicious activity reporting

## Jurisdiction

MVP is jurisdiction-agnostic. Future phases must address:
- Securities law classification of bearer notes
- Money transmitter licensing
- Custodian licensing requirements
- Tax reporting obligations
