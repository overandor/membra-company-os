# Jaqerbase / ArrowCAP

**ArrowCAP** (Arrow-Constrained Answer Protocol) is a working implementation of the thesis:

> We do not sell answers. We sell bonded answer-claims whose value can be priced through controlled blur and settled through an oracle.

It attacks Arrow's information paradox — a buyer cannot value information without
consuming it, and consuming it destroys the seller's ability to sell it — by splitting
every transaction into two machines:

1. **Disclosure** — an antonymified, non-consumable surrogate (a BlurHash64-style
   fidelity-ladder projection) lets a buyer price a claim without seeing the
   consumable content.
2. **Accountability** — a bonded, oracle-settled claim makes the disclosed surrogate's
   implicit promise economically enforceable: pass the hidden test, get paid; fail or
   cheat, get slashed.

The market unit is not "here is an answer." It is "here is a committed answer-claim:
inspect its blurred surrogate, verify its proof wrapper, see the bond, see the oracle,
and decide whether to escrow payment."

## The protocol's first law

> No full disclosure before payment. No payment without settlement. No settlement
> without an oracle. No oracle without a bond.

This is enforced in code, not just convention: `arrowcap.escrow.EscrowEngine` raises
`ProtocolViolation` for any out-of-order call (e.g. funding escrow before a bond is
posted, running the oracle before the answer is revealed, settling before the oracle
has run).

## Architecture

```
source object (file / answer)
   -> LLM antonymifier            arrowcap.antonymizer    non-consumable surrogate
   -> hash / Merkle commitment    arrowcap.commitment      identity + integrity
   -> BlurHash64 fidelity label   arrowcap.fidelity        disclosure level (0-9)
   -> lambda score                arrowcap.fidelity        transferability / friction
   -> oracle                      arrowcap.oracle          truth resolution (hidden tests)
   -> bond                        arrowcap.ledger           economic accountability
   -> escrow + settlement         arrowcap.escrow          first-law state machine
   -> settlement receipt          arrowcap.settlement      Ed25519-signed proof of outcome
   -> (optional) chain anchor     arrowcap.chain           Solana devnet commitment memo
   -> bond pricing                arrowcap.optimizer       GA + RL, trained on real history
```

### Module map

| Module | Responsibility |
|---|---|
| `commitment.py` | SHA-256 digests, domain-separated Merkle trees (RFC 6962-style leaf/node prefixes), inclusion proofs. |
| `fidelity.py` | The 10-level BlurHash64 fidelity ladder (Null -> Full-Transport), entropy/feature extraction, perceptual hashing (optional, degrades gracefully without Pillow), fuzzy (context-triggered piecewise) hashing, AES-256-GCM encrypted-body glyphs, lambda transferability scoring. |
| `antonymizer.py` | Builds the "verifiable non-seeing" surrogate: affirmed/negated structural predicates, risk score, length bucket, commitment hash — and `verify_binding` to catch bait-and-switch between preview and revealed answer. |
| `ledger.py` | SQLite ACID ledger (`BEGIN IMMEDIATE`, WAL mode, foreign keys). Accounts, deposits, transfers, and a hold lifecycle (active -> released or slashed) used for both bonds and escrow. |
| `claims.py` | `Claim` / `AnswerClaim` data model and the `ClaimStore` persistence layer backing the escrow state machine. |
| `oracle.py` | Subprocess-isolated execution of the buyer's hidden pytest suite against the seller's revealed answer, with timeout and a minimal environment. |
| `escrow.py` | `EscrowEngine` — the first-law state machine: post_claim -> submit_preview -> post_bond -> fund_escrow -> reveal_answer -> run_oracle -> settle. Raises `ProtocolViolation` on any reordering. |
| `settlement.py` | Ed25519-signed settlement receipts (`scheme` field for crypto-agility), tamper detection, persisted signing keys (`0o600`). |
| `chain.py` | Solana devnet adapter (`solders`/`solana-py`) that anchors a settlement commitment as an SPL Memo. Devnet-only by default; mainnet requires an explicit `allow_mainnet=True` opt-in and never auto-funds a mainnet keypair. |
| `optimizer.py` | Bond pricing: a genetic algorithm (tournament selection, elitism, blend crossover, Gaussian mutation) evolves a `BondGenome` against real settlement history, and a tabular Q-learner (epsilon-greedy contextual bandit) adapts bond-fraction recommendations per risk bucket. Documented bootstrap default for cold start (no fabricated history). |
| `cli.py` | The `arrowcap` command-line entry point wiring all of the above together. |

## The MVP: Hidden Test Claim Market

1. Buyer posts a task plus a hidden pytest suite (`post-claim`).
2. Seller submits an antonymified preview, not the full answer (`submit-preview`).
3. Seller posts a bond (`post-bond`).
4. Buyer funds escrow (`escrow-pay`) — only possible once the bond exists.
5. Seller reveals the full answer (`reveal-answer`) — checked against the preview's
   commitment for a binding violation.
6. Oracle and settlement run together (`settle`): the hidden tests execute against the
   revealed answer; on pass the bond is released and the buyer's escrow pays out minus
   a protocol fee; on fail (or on a binding violation) the bond is slashed to the buyer
   and the escrow is refunded.
7. A receipt is produced; with `--sign` it is Ed25519-signed and written to
   `<data-dir>/receipts/<answer_id>.json`; with `--anchor-devnet` its commitment is
   additionally memo-anchored on Solana devnet.

### CLI walkthrough

```bash
cd 06_Projects/jaqerbase
pip install -e ".[dev]"

export D="--data-dir ./.jaqerbase-demo"

cat > /tmp/test_hidden.py <<'EOF'
import submitted_answer

def test_add():
    assert submitted_answer.add(2, 3) == 5
EOF
printf 'def add(a, b):\n    return a + b\n' > answer.py

arrowcap $D post-claim --buyer alice --title "add()" --description "implement add" \
  --reward-cents 5000 --hidden-test-path /tmp/test_hidden.py \
  --fund-buyer-cents 100000

arrowcap $D submit-preview --claim-id <claim_id> --seller bob \
  --answer-file answer.py --bond-cents 1000 --fund-seller-cents 100000

arrowcap $D post-bond --answer-id <answer_id>
arrowcap $D escrow-pay --answer-id <answer_id>
arrowcap $D reveal-answer --answer-id <answer_id> --answer-file answer.py
arrowcap $D settle --answer-id <answer_id> --sign

arrowcap $D status --answer-id <answer_id>
arrowcap $D optimize-bonds
```

Every subcommand prints JSON to stdout; protocol violations and binding violations are
surfaced as a non-zero exit code with a message on stderr (see `tests/test_cli.py`).

## Settlement rail and the "no mock" constraint

Every layer is real, runnable code against real state — no simulated outcomes:

- The ledger is a real SQLite database with real ACID transactions and a real hold
  lifecycle, not an in-memory mock.
- The oracle really spawns a subprocess and really runs pytest against the revealed
  answer; pass/fail is the real exit status, not a stubbed bool.
- Settlement receipts are really Ed25519-signed with a real, persisted (`0o600`)
  keypair, not a fake signature string.
- The bond optimizer is really trained (GA + Q-learning) on settlement history
  produced by the actual escrow pipeline — `collect_history` reads genuine
  `ClaimStore` rows, not fabricated training data. With no history yet, it returns a
  documented, clearly-labeled bootstrap default rather than inventing data.
- The Solana adapter makes real RPC calls to real Solana devnet infrastructure
  (`api.devnet.solana.com`) using `solders`/`solana-py`; it does not stub the chain.
  Mainnet is gated behind an explicit `allow_mainnet=True` opt-in and is never
  auto-funded.

## Safety boundaries

- **Devnet by default.** `SolanaAnchor(network="mainnet")` raises
  `MainnetNotAuthorized` unless constructed with `allow_mainnet=True`. Airdrops are
  never available on mainnet, regardless of opt-in.
- **First law enforced in code.** `EscrowEngine` cannot be coerced into skipping a
  step; every transition checks the claim/answer's current status and raises
  `ProtocolViolation` otherwise.
- **Binding verification.** `verify_binding` compares the revealed answer's structural
  fingerprint against the antonymified preview's commitment; a mismatch is treated as
  a violation that slashes the bond without ever running the oracle.

## Testing

```bash
cd 06_Projects/jaqerbase
python3 -m pytest tests/ -v
```

105 tests pass; 2 live-devnet-RPC tests in `tests/test_chain.py` skip rather than fail
when the sandbox's network policy blocks outbound access to `api.devnet.solana.com`
(confirmed during development — this is an environment constraint, not a defect in the
adapter). All other tests exercise real cryptography, a real SQLite-backed ledger, real
subprocess oracle execution, and a real GA+RL optimizer trained on pipeline-derived
history — nothing in the suite mocks the system under test.

## On this living inside `membra-company-os`

Jaqerbase began as a sub-project of `overandor/membra-company-os`
(`06_Projects/jaqerbase/`) because a standalone repository could not be provisioned in
this environment (the GitHub App installation was scoped only to
`membra-company-os`). The package is self-contained (`src/arrowcap/`, its own
`pyproject.toml`, its own `tests/`) and can be lifted into a standalone repository
later with `git filter-repo` or a simple directory copy — no code in `src/arrowcap`
references anything outside this directory.
