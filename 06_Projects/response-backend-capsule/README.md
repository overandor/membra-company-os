# Response Backend Capsule (RBC) — answer-to-endpoint runtime

A terminal-first runtime that turns an **operational** model answer into a runnable
backend capsule: files + endpoint + tests + receipts. The user sees an explanation;
the terminal receives a tested micro-service. The capstone of this repo's
"value-becomes-financeable-when-verifiable" thesis.

```
prompt → classify → emit capsule → materialize → safety-check → test → serve → receipt
```

## The honest accounting (enforced in code, not asserted)
- **GUARANTEED:** a runnable, tested artifact — or an explicit block/failure.
- **MEASURED:** optimization (time saved / error reduced) — logged, never assumed.
- **NEVER GUARANTEED:** revenue. Money appears only when a usage event logs `money_moved`.

> `economic_proof = executable_artifact + usage_event + (time_saved or error_reduced) + receipt`

The runtime **does not trust the model**: it static-safety-checks and tests every capsule
before it can serve, and it cannot claim "uploaded/deployed/responded" unless it actually
did and holds a receipt. This kills action-overpromise, fake-endpoint, and fake-economic claims.

## Two ledgers, strictly separate
| Ledger | Answers | Class |
|---|---|---|
| **Technical receipt** (`TechnicalLedger`) | what was generated, did it run, file hashes, tests, endpoint | hash-chained (same primitive as ProofBook) |
| **Economic activity** (`EconomicLedger`) | was it used, how long, what baseline it replaced, error rate, money moved | append-only events |

That separation is the whole game: *"the model generated a runnable backend, test passed,
endpoint responded, hash exists"* is a different (and provable) claim from *"it made money."*

## The capsule
Two faces: the **visible** explanation, and the **operational** scaffold — `Manifest`
(name, purpose, kind, input/output schema, files, commands, deploy) + a `handler` (the
endpoint) + a `test` (the truth filter). One artifact-worthy answer = one mini-service.

## The boundary
**Each *operational* response must have a backend — not every answer.** A deterministic
classifier routes prompts to `explanation / artifact / endpoint / workflow`:
- "what is a tesseract" → explanation-only, **no backend forced**.
- "convert Beige Book adjectives into policy pressure" → **endpoint** (compiles, serves, responds).
- "build a shadow receivable ledger" → **workflow** (stateful service).
- malicious capsule (`rm -rf`, `os.system`) → **BLOCKED**, never served, `activity_proven=False`.

*(The classifier here is a deterministic stand-in; in production the model itself routes.)*

## Run it
```bash
python demo.py          # full end-to-end walkthrough (all four cases)
python test_capsule.py  # 6 tests, or: pytest
```

## Build path (terminal is the factory; web is the storefront)
One local folder per answer · one manifest per response · one endpoint per artifact-worthy
answer · one receipt per execution. Deployment (GitHub / Docker / HF Space / tunnel / zip)
is an **output of a verified local runtime**, never an unverified promise in chat. The web UI
comes later — it's just the storefront over the terminal factory.

## How it closes the loop
- **ProofBook** — the technical ledger is the same hash-chain; capsule receipts are underwritable evidence.
- **Underwriting / computational-capital** — a capsule with usage logs is exactly the *audited productive capacity* the underwriter counts; thousands of capsules + usage logs = an underwritable product.
- **SGE / EIL** — a capsule's test is a deterministic grader (sell the assay); its execution is an atomically-verifiable settlement. Same kernel: financeable iff verifiable.
