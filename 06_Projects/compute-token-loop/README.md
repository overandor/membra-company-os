# Compute Token Launch Loop

The full loop the session was building toward — **machine amortization → compute
collateralization → benchmarking → liquidification → token launch** — wiring the modules
already on `main` ("compute becomes liquidity," the Overmanifold/EIL thesis) into one cycle.

```
AMORTIZE      machine_value = hardware (depreciating) + recoverable utility (accruing)   [compute_capital]
 → COLLATERALIZE   underwrite that utility into a finance-readable Attributable Value Receipt [aau]
   → BENCHMARK      rank nodes; pool the eligible, settled collateral
     → LIQUIDIFY     over-collateralized backing → token supply + NAV
       → LOOP        new work → new receipts → re-amortize → re-back → updated NAV
```

## Honest by construction (the whole-session throughline)
- Backed by **modeled, underwritten, pre-revenue** compute value with **heavy haircuts**.
- Recoverable state is largely **non-transferable** → low exchangeability → big haircut. In the
  demo a fleet worth **$18,830 of machine value yields only ~$678 of finance-readable collateral**.
- **Over-collateralized**: each $1 of token face is backed by `OCR` ($2) of collateral.
- **NAV = modeled backing-per-token, not a market price.** "Launch" = a backing model + an
  auditable reserve ledger, **not** a securities offering or a redemption guarantee.
- A token is honest **iff its receipts are real/verified.** A gamed node is **rejected by the
  underwriter and contributes ZERO backing** (demo: `sketchy-04` → $0).

## Run it
```bash
python token_loop.py        # per-node amortize→collateralize, liquidify, 3-epoch launch loop
python test_token_loop.py   # 6 tests, or: pytest
```
Demo result: pool $678 → 339 COMP @ 200% backed; across 3 epochs of accrued work the pool
compounds to $1,372 / 686 COMP, reserve ledger hash-verifies, and the launch manifest carries
its disclaimers and a `NOT redemption-guaranteed` peg type.

## How it composes the stack
- `compute_capital.py` (underwriting-pipeline) — **amortization**: machine = hardware + recoverable utility.
- `aau.py` (attribution-underwriting) — **collateralization**: utility → finance-readable receipt, with the adversarial haircut stack.
- this module — **liquidification**: pool settled receipts → over-collateralized token supply + NAV, looped.
- reserve ledger — same hash-chain primitive as ProofBook; the token's backing history is auditable.

One line: *amortized + underwritten compute value, pooled and over-collateralized into a
coordination token — backed by verified receipts, not by story.*
