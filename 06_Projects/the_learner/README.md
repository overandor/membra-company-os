# THE LEARNER: AI vs. Bitcoin — Season One

**Day Zero: The AI Enters the Arena.** A locally recorded 60-minute pilot:
two identical models watch Gate's public `BTC_USDT` perpetual feed; one learns,
one stays frozen. The frozen one makes "improvement" falsifiable.

## Cast (presentation roles for real components)

| On screen | Is actually |
|---|---|
| The Learner | `models.TinyPolicyNet` — adaptive MLP (19→16 tanh→3 softmax), updated by REINFORCE |
| The Anchor | same net, same birth weights, frozen forever (hash-checked every cycle) |
| The Scientist | `scientist.py` — Navier–Stokes-inspired fluid features + spinor (delay-embedded complex field) features |
| The Referee | `referee.py` — deterministic `referee-v1` scoring |
| The Narrator | local Ollama (`qwen2.5:0.5b`) reading only journal records; falls back to `template-v1`, always labeled |
| The Director | `director.py` — scene picker over verified journal events only |

## The experiment

Every minute, on the minute (60 scheduled boundaries):

1. Both models observe identical closed-candle data + ticker.
2. Each emits LONG / SHORT / WAIT + confidence → appended to the journal
   **before the outcome exists**.
3. At `T + 10 min` (fixed horizon, recorded in `pilot_start`) the Referee
   scores both from the exit candle close.
4. Matured records become training evidence; the bounded trainer may update
   the Learner (batch≥8, ≤10 updates, 5-min cooldown, ‖Δ‖≤0.05, drift≤1.0).
   The Anchor is never touched.
5. The director renders both surfaces from journal events only — vertical
   (1080×1920) and landscape (1920×1080), same records, same order.

## Files

- `src/learner/journal.py` — append-only JSONL, SHA-256 hash chain
- `src/learner/feed.py` — public Gate feed, explicit `INVALID` states
- `src/learner/scientist.py` — fluid + spinor features, honest probe vs simple baseline
- `src/learner/models.py` — TinyPolicyNet, birth/learner/anchor weight files + hashes
- `src/learner/referee.py` — `referee-v1`: ±3 bps flat band, +1/−1, high-conf miss ⇒ review
- `src/learner/trainer.py` — `trainer-v1`: bounded REINFORCE, logged accept/reject
- `src/learner/narrator.py` — journal-only narration, engine always labeled
- `src/learner/director.py` — scene mapping + PIL renderer for both orientations
- `src/learner/pilot.py` — minute-aligned orchestrator
- `src/learner/verify.py` — acceptance-criteria verifier
- `scripts/encode_episode.sh` — ffmpeg frame→mp4 encoder

## Run

```bash
cd 06_Projects/the_learner
PYTHONPATH=src python3 -m learner.pilot --data-dir runs/day_zero --cycles 60
PYTHONPATH=src python3 -m learner.verify --data-dir runs/day_zero
bash scripts/encode_episode.sh runs/day_zero
```

## Integrity rules → code

| Rule | Enforcement |
|---|---|
| Predictions immutable | hash-chained journal; `Journal.verify` replays every hash |
| Surfaces read same records | both renderers consume journal events only |
| Invalid feed → explicit state | `feed_invalid` events with reason; no interpolated predictions |
| Narrator can't invent | prompt limited to the record; engine labeled per line |
| "updated" ≠ "improved" | on-screen note on every learning-moment scene |
| No fabricated progress | no XP/IQ/progress bars anywhere in renderer |
| Simulated labeled | every frame footer: "SIMULATED — no real orders" |
| Zero orders | feed module GETs two public endpoints only (verified) |
| Negative result valid | `season_score` verdict prints "Anchor beat the Learner" when true |

## Acceptance criteria

`python -m learner.verify` re-derives every criterion from disk: 60 attempted
cycles logged, chain intact, scoring reproducible, invalid states explicit,
updates truthful, anchor hash unchanged (birth==final==file), lineage
replayable from birth weights, frames synchronized, no credentials, no orders.

## Clips

`scripts/clips.py` selects genuinely noteworthy journal moments (each with its
original timestamp and simulated label) — working titles from the directive.
No history rewriting for a better clip.
