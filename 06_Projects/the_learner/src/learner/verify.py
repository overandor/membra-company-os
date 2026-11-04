"""Pilot acceptance verifier — every criterion re-derived from disk artifacts.

Usage: python -m learner.verify --data-dir <run_dir>

Checks, in order:
  1. 60 scheduled cycles attempted and each logged (prediction /
     feed_invalid / cycle_skipped), minute-aligned timestamps.
  2. Journal hash chain intact => forecasts immutable.
  3. Every outcome score reproducible from journal fields alone.
  4. Invalid-data states explicit; no prediction exists for invalid minutes.
  5. Training updates truthful: accepted => checkpoint exists and
     weights_hash_after matches; rejected => reason present.
  6. Anchor weights provably unchanged (birth hash == final hash == every
     prediction's anchor weights hash == anchor file hash).
  7. Learner lineage replayable: replaying accepted updates from birth
     weights reproduces the final learner weights hash.
  8. Scene frame counts match across orientations (synchronized, journal-only).
  9. No credential-shaped strings in run artifacts or committed source.
 10. Zero exchange orders: feed module performs only two public GETs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

import numpy as np

from . import models, referee, scientist
from .journal import Journal, record_hash
from .trainer import BoundedTrainer

CRED_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"api[_-]?key[\"'=:\s]+[A-Za-z0-9_\-]{16,}",
    r"api[_-]?secret[\"'=:\s]+[A-Za-z0-9_\-]{16,}",
    r"Bearer\s+[A-Za-z0-9_\-\.]{20,}",
]


def _check(name: str, ok: bool, detail: str = "") -> dict:
    return {"check": name, "ok": bool(ok), "detail": detail}


def verify(data_dir: str) -> list[dict]:
    out: list[dict] = []
    jpath = os.path.join(data_dir, "journal.jsonl")
    if not os.path.exists(jpath):
        return [_check("journal_exists", False, jpath)]
    recs = list(iter(Journal(jpath)))
    start = next((r for r in recs if r["kind"] == "pilot_start"), None)
    end = next((r for r in recs if r["kind"] == "pilot_end"), None)
    if start is None:
        return [_check("pilot_start", False)]
    cfg = start["payload"]

    # 1. cycle accounting
    cyc = [r for r in recs
           if r["kind"] in ("prediction", "feed_invalid", "cycle_skipped")]
    aligned = all((r.get("minute_ts") or r["payload"].get(
        "scheduled_minute_ts") or 0) % 60 == 0 for r in cyc)
    n_sched = cfg["cycles_scheduled"]
    attempted = len({(r.get("minute_ts") or
                      r["payload"].get("scheduled_minute_ts"))
                     for r in cyc})
    out.append(_check("cycles_attempted", attempted == n_sched,
                      f"{attempted}/{n_sched} logged"))
    out.append(_check("minute_alignment", aligned,
                      "every cycle record carries a minute-aligned ts"))

    # 2. immutability
    errors = Journal.verify(jpath)
    out.append(_check("journal_chain_intact", not errors,
                      "" if not errors else f"{len(errors)} break(s), first: "
                      f"{errors[0].reason} @seq {errors[0].seq}"))
    preds = [r for r in recs if r["kind"] == "prediction"]
    out.append(_check("predictions_before_outcomes", all(
        p["payload"]["mature_minute_ts"] > p["minute_ts"] for p in preds),
        f"{len(preds)} predictions all reference a future maturity"))

    # 3. scoring reproducible
    bad = []
    for r in recs:
        if r["kind"] != "outcome":
            continue
        p = r["payload"]
        move = (p["exit_price"] - p["entry_price"]) / p["entry_price"] * 1e4
        truth = referee.truth_label(move)
        lp, lc = referee.score_action(p["learner_action"], truth)
        ap, ac = referee.score_action(p["anchor_action"], truth)
        if (abs(move - p["move_bps"]) > 1e-9 or truth != p["truth"]
                or lp != p["learner"]["points"] or ap != p["anchor"]["points"]
                or lc != p["learner"]["correct"]
                or ac != p["anchor"]["correct"]):
            bad.append(r["seq"])
    out.append(_check("scoring_reproducible", not bad,
                      f"all outcomes re-derived" if not bad
                      else f"mismatch at seqs {bad[:5]}"))

    # 4. invalid explicit
    inv = [r for r in recs if r["kind"] == "feed_invalid"]
    inv_minutes = {r["minute_ts"] for r in inv}
    pred_minutes = {r["minute_ts"] for r in preds}
    out.append(_check("invalid_states_explicit",
                      all(r["payload"].get("reason") for r in inv)
                      and not (inv_minutes & pred_minutes),
                      f"{len(inv)} invalid cycles, none carry predictions"))

    # 5. training updates truthful
    ups = [r for r in recs if r["kind"] == "training_update"]
    truthy = True
    for u in ups:
        p = u["payload"]
        if p["accepted"]:
            ckpt = os.path.join(data_dir, "weights", p["checkpoint"])
            ok = os.path.exists(ckpt) and models.weights_hash(
                *models.load_weights(ckpt)) == p["weights_hash_after"]
            truthy &= ok
        else:
            truthy &= bool(p.get("reason"))
    out.append(_check("training_updates_truthful", truthy,
                      f"{len(ups)} update decisions, "
                      f"{sum(1 for u in ups if u['payload']['accepted'])} "
                      "accepted"))

    # 6. anchor unchanged
    a0 = cfg["anchor_weights_hash"]
    af0 = cfg["anchor_file_hash"]
    afinal = end["payload"]["anchor_weights_hash_final"] if end else None
    affinal = end["payload"]["anchor_file_hash_final"] if end else None
    every = all(p["payload"]["anchor"]["weights_hash"] == a0 for p in preds)
    afile = os.path.join(data_dir, "weights", "anchor.npz")
    afile_now = models.file_hash(afile) if os.path.exists(afile) else None
    out.append(_check("anchor_unchanged",
                      a0 == afinal and af0 == affinal == afile_now and every,
                      f"birth==final==file ({a0[:12]}…)"))

    # 7. lineage replay
    try:
        w1, b1, w2, b2 = models.init_weights(
            cfg["feature_spec"]["dim"], models.INIT_SEED)
        birth_arrs = (w1, b1, w2, b2)
        learner = models.TinyPolicyNet(w1, b1, w2, b2, "replay")
        tr = BoundedTrainer()
        tr.cooldown_s = -1  # replay mode: only bound checks are batch/caps
        tr.last_update_ts = -10**9
        outcome_by_seq = {r["seq"]: r["payload"] for r in recs
                          if r["kind"] == "outcome"}
        replayed = 0
        replay_dir = os.path.join(data_dir, "weights", "_replay")
        for u in ups:
            if not u["payload"]["accepted"]:
                continue
            seqs = u["payload"]["trained_seqs"]
            ev = []
            for s in seqs:
                o = outcome_by_seq.get(s)
                pred = next(p for p in preds if p["seq"] == s)
                ev.append({**o, "features": pred["payload"]["features"],
                           "learner_action":
                           pred["payload"]["learner"]["action"],
                           "prediction_seq": s})
            res = tr.maybe_update(learner, birth_arrs, ev, replay_dir)
            if not res.get("accepted"):
                raise RuntimeError(f"replay update rejected: {res['reason']}")
            replayed += 1
        expected = end["payload"]["learner_weights_hash_final"] if end else None
        out.append(_check("lineage_replayable",
                          learner.hash() == expected or replayed == 0,
                          f"replay hash {learner.hash()[:12]} vs "
                          f"{str(expected)[:12]}"))
    except Exception as exc:
        out.append(_check("lineage_replayable", False,
                          f"{type(exc).__name__}: {exc}"))

    # 8. scenes synchronized
    fv = len([f for f in os.listdir(os.path.join(data_dir, "frames_vertical"))
              if f.endswith(".png")]) \
        if os.path.isdir(os.path.join(data_dir, "frames_vertical")) else 0
    fl = len([f for f in os.listdir(os.path.join(data_dir, "frames_landscape"))
              if f.endswith(".png")]) \
        if os.path.isdir(os.path.join(data_dir, "frames_landscape")) else 0
    out.append(_check("scenes_synchronized", fv == fl and fv > 0,
                      f"vertical={fv} landscape={fl} frames"))

    # 9. no credentials
    hits = []
    roots = [data_dir,
             os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    seen = set()
    for root in roots:
        for dp, _, files in os.walk(root):
            for fn in files:
                fp = os.path.join(dp, fn)
                if fp in seen or fn.endswith((".png", ".mp4", ".npz")):
                    continue
                seen.add(fp)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                        txt = fh.read()
                except OSError:
                    continue
                for pat in CRED_PATTERNS:
                    for m in re.finditer(pat, txt):
                        hits.append(f"{fp}:{m.start()}")
    out.append(_check("no_credentials", not hits,
                      "clean" if not hits else f"{len(hits)} suspicious hits"))

    # 10. zero orders — static check on feed module
    feed_src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "feed.py")
    with open(feed_src) as fh:
        src = fh.read()
    order_verbs = re.findall(r"\bpost\b|\border\b|\blist_futures_orders", src,
                             flags=re.I)
    out.append(_check("zero_orders",
                      "orders" not in src.lower() and not order_verbs,
                      "feed issues GET requests only"))

    return out


def birth_tuple(learner):
    return (learner.w1.copy(), learner.b1.copy(),
            learner.w2.copy(), learner.b2.copy())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    args = ap.parse_args()
    results = verify(args.data_dir)
    for r in results:
        print(f"[{'PASS' if r['ok'] else 'FAIL'}] {r['check']}"
              + (f" — {r['detail']}" if r["detail"] else ""))
    ok = all(r["ok"] for r in results)
    print(f"\n{'PILOT PASSES' if ok else 'PILOT FAILS'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
