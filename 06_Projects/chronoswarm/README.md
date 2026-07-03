# ChronoSwarm

ChronoSwarm is a real, working slice of a bigger pitch — "ChronoQuadrantOS," a
desktop reimagined as a scheduled runtime where you don't manage windows, you breed
layouts, and you don't open apps, you awaken workflows. That full pitch (GA-controlled
screen real estate, scheduled wake/sleep for every app, cursor-as-agent, screen-as-
database) assumes a GUI, a display server, and an accessibility API to drive window
geometry. This sandbox is headless: no X11/Wayland, no window manager, no accessibility
tree. So ChronoSwarm-lite builds the same three mechanisms against a substrate that
*is* real and scriptable here — **tmux**.

> Do not manage windows. Breed layouts. Do not open apps. Awaken workflows.

## What's actually real here

- **tmux is the window manager.** Every "window" is a real tmux pane in a real,
  live tmux session. `tmuxctl.py` shells out to the actual `tmux` binary — sessions,
  splits, resizes, and `capture-pane` reads are all real subprocess calls against
  real terminal state, not a simulated layout engine.
- **The GA breeds real geometry.** `genome.py`'s `evolve_layout` runs a tournament-
  selection + elitism + blend-crossover + Gaussian-mutation genetic algorithm
  (the same structure as Jaqerbase's bond-price optimizer) over candidate pane-width
  vectors, scored by `fitness.py`'s `layout_fitness` — a deterministic function of
  real captured pane text, real geometry, and real recency. The governor then applies
  the winning genome with real `tmux resize-pane` calls.
- **The scheduler runs on a real clock.** `scheduler.py`'s `ChronoScheduler` advances
  each pane through `sleeping -> warming -> awake -> working -> cooling -> archived`
  purely as a function of measured idle time (`now - last_activity_ts`) and whether
  the pane's real captured text contains an error marker (`Traceback`, `FAILED`,
  `panic:`, etc). No timer is faked; `tick(now=...)` defaults to `time.time()` and
  only accepts an explicit timestamp for deterministic tests.
- **The receipt ledger is a real SQLite database.** `store.py`'s `WorkflowStore` uses
  WAL mode, foreign keys, and `BEGIN IMMEDIATE` transactions — the same ACID pattern
  as Jaqerbase's `Ledger` — because the CLI runs as separate OS processes and must not
  lose state between invocations. Every layout breed and every state transition writes
  a row via `receipts.py`.

## What's explicitly out of scope (and why)

- **No GUI, no real windows, no cursor automation.** This sandbox has no display
  server. Driving real OS window geometry or moving an actual cursor isn't possible
  here, so it isn't claimed. tmux panes stand in for the "screen partitions" concept
  faithfully (real tiling, real geometry, real resize) without pretending to control
  an X11/Wayland compositor that doesn't exist in this environment.
- **No RL component.** Jaqerbase pairs GA bond-pricing with a Q-learning bandit
  because there's a meaningful "did this bond fraction get rewarded by real
  settlement history" signal to learn from. ChronoSwarm-lite's GA already directly
  optimizes against the real fitness function every time it's invoked; there's no
  analogous reward signal to bootstrap an RL layer here, so none is bolted on.

## Architecture

```
real tmux session         tmuxctl.py        sessions, panes, splits, resize, capture
   -> pane snapshot        fitness.py        deterministic score: visibility, errors,
                                              readability, recency, noise, churn
   -> layout genome         genome.py        GA: tournament + elitism + blend
                                              crossover + Gaussian mutation
   -> applied layout        governor.py      GeneticLayoutGovernor: breeds, then
                                              really resizes panes via tmuxctl
   -> lifecycle state       scheduler.py      ChronoScheduler: real-clock wake/sleep
                                              ladder, error-aware
   -> persisted state        store.py          WorkflowStore: SQLite, WAL, ACID
   -> audit trail            receipts.py       layout_breed / state_transition rows
   -> control surface         cli.py            the `chronoswarm` command
```

### Module map

| Module | Responsibility |
|---|---|
| `tmuxctl.py` | Real subprocess wrapper around the `tmux` binary: `new-session`, `list-panes`, `split-window`, `resize-pane`, `capture-pane`, `send-keys`, `kill-pane`/`kill-session`. |
| `fitness.py` | `PaneSnapshot` + `layout_fitness`: a pure, deterministic score over real geometry and real captured text — rewards a large readable active pane, visible error panes, content-dense panes, and recently-active panes; penalizes idle clutter and layout churn. |
| `genome.py` | `LayoutGenome` (one weight per pane) and named mutation operators (`expand_active`, `shrink_idle`, `swap`, `promote_failing`, `collapse_completed`, `restore_previous_layout`), plus `evolve_layout` — the GA loop. |
| `store.py` | `WorkflowStore` — SQLite (WAL, foreign keys, `BEGIN IMMEDIATE`) tables for `panes` and `receipts`. |
| `receipts.py` | `Receipt` dataclass and `record_layout_breed` / `record_state_transition` helpers on top of `WorkflowStore`. |
| `scheduler.py` | `ChronoScheduler` — the real-clock wake/sleep state machine (`next_state` is a pure function of idle seconds + error presence). |
| `governor.py` | `GeneticLayoutGovernor` — builds real `PaneSnapshot`s from live tmux state, runs `evolve_layout`, applies the winner via real `resize-pane` calls, writes receipts. |
| `cli.py` | The `chronoswarm` command-line entry point wiring all of the above together. |

## CLI walkthrough

```bash
cd 06_Projects/chronoswarm
pip install -e ".[dev]"

D="--data-dir ./.chronoswarm-demo --session demo"

chronoswarm $D start-session --width 160 --height 40
chronoswarm $D split --pane-id %0
chronoswarm $D list-panes

chronoswarm $D send-keys --pane-id %1 --keys "echo 'Traceback (most recent call last):'"
chronoswarm $D breed --generations 30 --population 20 --seed 7
chronoswarm $D tick
chronoswarm $D status
chronoswarm $D receipts

chronoswarm $D kill-session
```

`breed` runs the GA against the live session and really resizes panes — the pane
showing the error wins more width because `layout_fitness` rewards visible error
panes. `tick` advances pane lifecycle state on the real clock and real captured text.
`receipts` shows the full audit trail of what changed and what it did to fitness.

Every subcommand prints JSON to stdout; failures (an unknown pane, a real `tmux`
error) print to stderr with a non-zero exit code.

## Testing

```bash
cd 06_Projects/chronoswarm
python3 -m pytest tests/ -v
```

79 tests pass. They exercise a real, live tmux session per test (created and torn
down via the `tmux_session` fixture), a real SQLite-backed `WorkflowStore`, the real
GA breeding real pane widths, and the real CLI as a subprocess-free `main()` call
with captured stdout/stderr — nothing in the suite mocks tmux, the database, or the
fitness function.

## On this living inside `membra-company-os`

Like Jaqerbase, ChronoSwarm lives at `06_Projects/chronoswarm/` because a standalone
repository could not be provisioned in this environment. The package is
self-contained (`src/chronoswarm/`, its own `pyproject.toml`, its own `tests/`) and
references nothing outside this directory.
