# LaunchR — Reality Status

**Last updated:** 2026-05-29
**Phase:** 2.5 — Multi-source Software Asset Intelligence
**Status:** Infrastructure operational. Token/Launch features gated.

---

## What LaunchR Actually Is

LaunchR is **Software Asset Intelligence infrastructure**.

It discovers, appraises, and generates evidence for software assets across multiple sources (GitHub, Hugging Face, package registries, public deployments). It does **not** mint tradable tokens or create liquidity pools for unreviewed assets.

---

## Compliance Gates

| Gate | Status | Required For |
|------|--------|-------------|
| **G1: Ownership Verification** | `PARTIAL` | Any launch action |
| **G2: Legal Review** | `BLOCKED` | Public token launch |
| **G3: Security Audit** | `BLOCKED` | Public token launch |
| **G4: KYC/AML** | `BLOCKED` | Public token launch |
| **G5: Regulatory Clearance** | `BLOCKED` | Public token launch |

**Rule:** No tradable token can be launched until G1–G5 are all `PASS`.

---

## Feature Matrix

| Feature | Status | Notes |
|---------|--------|-------|
| GitHub repo scanning | `OPERATIONAL` | Rate-limited without token; demo fallback active |
| Hugging Face scanning | `OPERATIONAL` | Models, spaces, datasets |
| npm/PyPI/Cargo scanning | `OPERATIONAL` | New in Phase 2.5 |
| Public deployment detection | `OPERATIONAL` | Vercel, Netlify, Fly.io |
| README/license/security scoring | `OPERATIONAL` | Quality metrics per repo |
| Asset portfolio dashboard | `OPERATIONAL` | Multi-source aggregation |
| Evidence packet generation | `OPERATIONAL` | Canonical hashing + Merkle root |
| Evidence packet export | `OPERATIONAL` | JSON + PDF |
| BitNet-compatible receipt hash | `OPERATIONAL` | 64-char SHA-256 Merkle root |
| Ownership verification | `SCAFFOLD` | GitHub token flow; not enforced |
| Token mint (devnet) | `GATED` | UI present but marked experimental |
| Liquidity pool creation | `GATED` | UI scaffold; no real AMM integration |
| Public token launch | `BLOCKED` | Pending G1–G5 |

---

## Architecture Stack

```
Layer 1 — Discovery
  ├─ GitHub Scanner (repos, stars, forks, languages, CI, activity)
  ├─ Hugging Face Scanner (models, spaces, datasets)
  ├─ Package Registry Scanner (npm, PyPI, Cargo, crates.io)
  └─ Deployment Scanner (Vercel, Netlify, Fly.io, Heroku)

Layer 2 — Appraisal
  ├─ Repo Quality Score (README, tests, docs, license, CI, security)
  ├─ Novelty Score (language diversity, topic diversity)
  ├─ Buildability Score (CI, docs, tests, activity)
  ├─ Market Demand Score (stars, forks, dependents, downloads)
  └─ Risk Engine (flags: no license, stale, no tests, single contributor)

Layer 3 — Evidence
  ├─ Canonical Evidence Packet (snapshot + hash)
  ├─ Merkle Root (SHA-256 over packet fields)
  ├─ BitNet-Compatible Receipt Hash (64-char hex)
  ├─ Ownership Status (GitHub token / gist verification)
  └─ Epoch History (time-series evidence snapshots)

Layer 4 — Portfolio
  ├─ Multi-source Asset Map
  ├─ Portfolio Capitalization (sum of asset values)
  └─ Ecosystem Clustering (by language, prefix, topic)

Layer 5 — Launch (GATED)
  ├─ Non-transferable Proof Receipt (G1 only)
  ├─ Restricted Reviewed Launch Token (G1–G3)
  └─ Public Liquidity Pool (G1–G5)
```

---

## Token Launch Policy

1. **Proof Receipt** (non-transferable): Can be generated after ownership verification (G1). This is a receipt, not a tradable token.
2. **Restricted Token**: Can only be launched after legal review (G2) and security audit (G3). Distribution is restricted to accredited/verified participants.
3. **Public Token**: Only after full regulatory clearance (G5). This is the only stage where public liquidity pools are permitted.

**Current Phase:** We are at Layer 1–4. Layer 5 is scaffolded but gated.

---

## BitNet / Provenance-Engine Integration

LaunchR evidence packets include a **BitNet-compatible receipt hash** computed as:

```
receipt = SHA256( asset_id || epoch || canonical_hash || timestamp )
```

This hash is deterministic and can be verified by:
- **BitNet** (folder-level proof system)
- **provenance-engine** (repo evolution tracking)
- **LaunchR** (packet verification endpoint)

Together they form the **Software Asset Intelligence stack**:
- LaunchR discovers and appraises software assets.
- BitNet proves folder contents.
- provenance-engine proves repo evolution over time.

---

## How to Enable Full Token Launch

1. Set `GITHUB_TOKEN` on the backend for real GitHub data.
2. Complete ownership verification flow for the target repo.
3. Pass legal review (engage counsel).
4. Pass security audit (3rd-party review).
5. Pass KYC/AML checks.
6. Obtain regulatory clearance (jurisdiction-dependent).
7. Update this file: mark G1–G5 as `PASS`.
8. Only then enable public token launch in the UI.

---

## Contact

For compliance or legal questions, open an issue on the repository.
