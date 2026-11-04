"""Day Zero orchestrator — 60 scheduled minute boundaries, locally recorded.

Flow per boundary T (minute-aligned unix):
  1. snapshot Gate BTC_USDT public feed (closed 1m candles + ticker)
  2. Learner + Anchor predict on identical features, before any outcome exists
  3. predictions appended to the hash-chained journal
  4. predictions at T-H mature: referee scores them deterministically
  5. bounded trainer may update the Learner (Anchor never touched)
  6. director renders both surfaces from journal events only

No orders are placed anywhere. Simulated == labeled simulated.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

from . import models, referee, scientist
from .director import pick_scene, render_frame
from .feed import GateFeed
from .journal import Journal, record_hash, sha256_hex, canonical
from .narrator import Narrator
from .trainer import BoundedTrainer

FRAMES_PER_EVENT = 18   # 3 seconds at 6 fps in the final encode
FPS = 6


def next_boundary(now: float) -> int:
    return (int(now) // 60 + 1) * 60


def wait_until(ts: int) -> None:
    while True:
        rem = ts - time.time()
        if rem <= 0:
            return
        time.sleep(min(rem, 0.5))


class Pilot:
    def __init__(self, data_dir: str, cycles: int = 60,
                 horizon_min: int = referee.HORIZON_MIN):
        self.data_dir = data_dir
        self.cycles = cycles
        self.horizon_min = horizon_min
        os.makedirs(data_dir, exist_ok=True)
        self.journal = Journal(os.path.join(data_dir, "journal.jsonl"))
        self.weights_dir = os.path.join(data_dir, "weights")
        self.frames_v = os.path.join(data_dir, "frames_vertical")
        self.frames_l = os.path.join(data_dir, "frames_landscape")
        self.feed = GateFeed()
        self.narrator = Narrator()
        self.trainer = BoundedTrainer()
        self.frame_idx = 0
        self.pending: list[dict] = []          # prediction payloads
        self.matured: list[dict] = []          # outcome payloads + joined fields
        self.l_points = self.a_points = 0
        self.l_correct = self.a_correct = 0
        self.scored = 0
        self.latest_narration = ""

    # ---- journal helpers ----

    def emit(self, kind: str, payload: dict, minute_ts=None,
             narrate: bool = True, render: bool = True) -> dict:
        rec = self.journal.append(kind, payload, minute_ts=minute_ts)
        if narrate:
            n = self.narrator.narrate(rec)
            nrec = self.journal.append("narration", n)
            self.latest_narration = n["text"]
        if render:
            self.render(rec)
        return rec

    def render(self, rec: dict) -> None:
        scene = pick_scene(rec)
        if scene is None:
            return
        for _ in range(FRAMES_PER_EVENT):
            self.frame_idx += 1
            render_frame(rec, scene, self.latest_narration,
                         "vertical", rec["seq"], self.frame_idx, self.frames_v)
            render_frame(rec, scene, self.latest_narration,
                         "landscape", rec["seq"], self.frame_idx, self.frames_l)

    def scoreboard(self) -> list[str]:
        return [f"LEARNER  {self.l_points:+d} pts",
                f"ANCHOR   {self.a_points:+d} pts",
                f"scored   {self.scored}",
                f"pending  {len(self.pending)}"]

    # ---- the pilot ----

    def start(self) -> None:
        spec = scientist.feature_spec()
        birth = models.Birth(spec["dim"], self.weights_dir)
        self.birth = birth
        self.birth_w = (birth.learner.w1.copy(), birth.learner.b1.copy(),
                        birth.learner.w2.copy(), birth.learner.b2.copy())
        payload = {
            "schema": "pilot-v1",
            "title": "Day Zero: The AI Enters the Arena",
            "contract": "BTC_USDT", "settle": "usdt", "venue": "gate",
            "feed": "public futures candlesticks+tickers (read-only)",
            "cycles_scheduled": self.cycles,
            "horizon_min": self.horizon_min,
            "rules_version": referee.RULES_VERSION,
            "flat_band_bps": referee.FLAT_BAND_BPS,
            "high_conf_threshold": referee.HIGH_CONF_THRESHOLD,
            "feature_spec": spec,
            "feature_spec_hash": sha256_hex(canonical(spec)),
            "birth_weights_hash": birth.birth_hash,
            "learner_weights_hash": birth.learner.hash(),
            "anchor_weights_hash": birth.anchor.hash(),
            "anchor_file_hash": models.file_hash(birth.anchor_path),
            "trainer": self.trainer.config(),
            "narrator_engine": self.narrator.engine,
            "cast": {"learner": "adaptive RL network (TinyPolicyNet)",
                     "anchor": "frozen reference model (identical init)",
                     "scientist": "NS-inspired + spinor feature models",
                     "referee": referee.RULES_VERSION},
            "integrity": {"predictions_immutable": True,
                          "surfaces_read_journal_only": True,
                          "orders": "none — simulated labels only"},
        }
        self.journal.append("pilot_start", payload)
        # cold open frames
        rec = {"seq": 0, "kind": "pilot_start", "payload": payload,
               "hash": self.journal._prev_hash}
        scene = "cold_open"
        for _ in range(FRAMES_PER_EVENT * 2):
            self.frame_idx += 1
            render_frame(rec, scene, "Day Zero begins.",
                         "vertical", 0, self.frame_idx, self.frames_v)
            render_frame(rec, scene, "Day Zero begins.",
                         "landscape", 0, self.frame_idx, self.frames_l)

    def run_cycle(self, cycle_no: int, minute_ts: int) -> None:
        anchor_ok = (models.file_hash(self.birth.anchor_path) ==
                     self.journal_payload_anchor_hash())
        if not anchor_ok:
            self.emit("integrity_breach",
                      {"what": "anchor_weights_changed"}, minute_ts=minute_ts)
            raise RuntimeError("Anchor weights changed — aborting pilot")

        snap = self.feed.snapshot(minute_ts)
        if not snap.valid and snap.invalid_reason and snap.invalid_reason \
                .startswith(("stale_candle", "no_closed_candle")):
            # the just-closed minute candle may lag the API a few seconds
            time.sleep(8)
            snap = self.feed.snapshot(minute_ts)
        if not snap.valid:
            self.emit("feed_invalid",
                      {"cycle": cycle_no, "reason": snap.invalid_reason},
                      minute_ts=minute_ts)
            self.mature_pending(minute_ts)
            return

        features = scientist.compute_features(
            snap.candles,
            funding_rate=getattr(snap, "funding_rate", 0.0))
        fx = np.array([round(float(v), 6) for v in features])
        l_pred = self.birth.learner.predict(fx)
        a_pred = self.birth.anchor.predict(fx)
        payload = {
            "cycle": cycle_no,
            "minute_ts": minute_ts,
            "mature_minute_ts": minute_ts + self.horizon_min * 60,
            "entry_price": snap.entry_price,
            "mark_price": snap.mark_price,
            "features": [float(v) for v in fx],
            "features_hash": sha256_hex(canonical(fx.tolist())),
            "horizon_min": self.horizon_min,
            "learner": {"action": l_pred.action,
                        "confidence": round(l_pred.confidence, 4),
                        "probs": {k: round(v, 4)
                                  for k, v in l_pred.probs.items()},
                        "weights_hash": self.birth.learner.hash()},
            "anchor": {"action": a_pred.action,
                       "confidence": round(a_pred.confidence, 4),
                       "probs": {k: round(v, 4)
                                 for k, v in a_pred.probs.items()},
                       "weights_hash": self.birth.anchor.hash()},
            "scoreboard": self.scoreboard(),
            "simulated": True,
        }
        rec = self.emit("prediction", payload, minute_ts=minute_ts)
        self.pending.append({**payload, "seq": rec["seq"]})
        self.mature_pending(minute_ts)
        self.try_train()
        if cycle_no % 15 == 0:
            self.science_eval(minute_ts)

    def mature_pending(self, now_ts: int) -> None:
        still = []
        for p in self.pending:
            if p["mature_minute_ts"] > now_ts:
                still.append(p)
                continue
            exit_price, err = self.feed.exit_price(p["mature_minute_ts"])
            if exit_price is None:
                still.append(p)
                continue
            out = referee.score(
                entry_price=p["entry_price"], exit_price=exit_price,
                learner_action=p["learner"]["action"],
                learner_conf=p["learner"]["confidence"],
                anchor_action=p["anchor"]["action"],
                prediction_seq=p["seq"], minute_ts=p["minute_ts"],
                mature_minute_ts=p["mature_minute_ts"])
            op = out.to_payload()
            op.update({
                "learner_action": p["learner"]["action"],
                "anchor_action": p["anchor"]["action"],
                "learner_conf": p["learner"]["confidence"],
                "features": p["features"],
                "truth_bps": out.move_bps,
                "scoreboard": None,
            })
            self.l_points += out.learner_points
            self.a_points += out.anchor_points
            self.l_correct += 1 if out.learner_correct else 0
            self.a_correct += 1 if out.anchor_correct else 0
            self.scored += 1
            op["learner_score_total"] = self.l_points
            op["anchor_score_total"] = self.a_points
            op["scoreboard"] = self.scoreboard()
            self.emit("outcome", op, minute_ts=now_ts)
            self.matured.append({**op, "prediction_seq": p["seq"],
                                 "features": p["features"],
                                 "learner_action": p["learner"]["action"]})
        self.pending = still

    def try_train(self) -> None:
        res = self.trainer.maybe_update(
            self.birth.learner, self.birth_w, self.matured, self.weights_dir)
        if res.get("accepted"):
            res["delta_norm_cap"] = self.trainer.delta_norm_cap
            res["scoreboard"] = self.scoreboard()
        self.emit("training_update", res,
                  narrate=bool(res.get("accepted")),
                  render=bool(res.get("accepted")))

    def science_eval(self, minute_ts: int) -> None:
        n_sci = [scientist.FEATURE_NAMES.index(n)
                 for n in scientist.SCIENTIST_NAMES]
        n_sim = [scientist.FEATURE_NAMES.index(n)
                 for n in scientist.SIMPLE_NAMES]
        sa = scientist.probe_accuracy(self.matured, n_sci)
        ba = scientist.probe_accuracy(self.matured, n_sim)
        if sa is None or ba is None:
            verdict = "insufficient evidence — no claim made"
        elif sa > ba:
            verdict = "scientist features beat simple indicators"
        elif sa < ba:
            verdict = "simple indicators beat scientist features"
        else:
            verdict = "dead heat — scientist earned nothing extra"
        self.emit("science_eval",
                  {"matured_n": len(self.matured),
                   "scientist_acc": sa, "baseline_acc": ba,
                   "verdict": verdict}, minute_ts=minute_ts)

    def journal_payload_anchor_hash(self) -> str:
        recs = [r for r in self.journal if r["kind"] == "pilot_start"]
        return recs[-1]["payload"]["anchor_file_hash"]

    def finale(self) -> None:
        self.science_eval(int(time.time()))
        verdict = ("the Learner beat the Anchor"
                   if self.l_points > self.a_points
                   else "the Anchor beat the Learner — a rigorous negative result"
                   if self.a_points > self.l_points
                   else "dead heat — no improvement demonstrated")
        self.emit("season_score", {
            "learner": {"points": self.l_points, "correct": self.l_correct,
                        "scored": self.scored},
            "anchor": {"points": self.a_points, "correct": self.a_correct,
                       "scored": self.scored},
            "updates_accepted": self.trainer.updates_done,
            "verdict": verdict,
            "note": "update ≠ improvement; a negative result is a valid finale",
        })

    def end(self, cycles_attempted: int, cycles_predicted: int,
            cycles_invalid: int) -> None:
        self.journal.append("pilot_end", {
            "cycles_attempted": cycles_attempted,
            "cycles_predicted": cycles_predicted,
            "cycles_invalid_data": cycles_invalid,
            "anchor_weights_hash_final": self.birth.anchor.hash(),
            "anchor_file_hash_final":
                models.file_hash(self.birth.anchor_path),
            "learner_weights_hash_final": self.birth.learner.hash(),
            "matured_total": self.scored,
            "unmatured_total": len(self.pending),
        })
        self.journal.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="Day Zero pilot")
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--cycles", type=int, default=60)
    ap.add_argument("--horizon-min", type=int, default=referee.HORIZON_MIN)
    ap.add_argument("--no-align", action="store_true",
                    help="testing only: do not wait for minute boundaries")
    args = ap.parse_args()

    p = Pilot(args.data_dir, cycles=args.cycles, horizon_min=args.horizon_min)
    p.start()
    attempted = predicted = invalid = 0

    boundaries: list[int] = []
    if args.no_align:
        base = int(time.time()) // 60 * 60
        boundaries = [base + i * 60 for i in range(args.cycles)]
    else:
        t0 = next_boundary(time.time())
        boundaries = [t0 + i * 60 for i in range(args.cycles)]

    for i, ts in enumerate(boundaries, start=1):
        if not args.no_align:
            wait_until(ts)
            now = time.time()
            if now - ts > 55:
                p.journal.append("cycle_skipped", {
                    "cycle": i, "scheduled_minute_ts": ts,
                    "reason": "missed_boundary",
                    "drift_s": round(now - ts, 1)})
                attempted += 1
                continue
        attempted += 1
        try:
            p.run_cycle(i, ts)
            kinds = [r for r in p.journal if r.get("minute_ts") == ts
                     and r["kind"] in ("prediction", "feed_invalid")]
            if any(r["kind"] == "prediction" for r in kinds):
                predicted += 1
            else:
                invalid += 1
        except Exception as exc:
            p.journal.append("cycle_skipped", {
                "cycle": i, "scheduled_minute_ts": ts,
                "reason": f"error:{type(exc).__name__}:{exc}"})
            invalid += 1

    # drain maturities
    if args.no_align:
        deadline = time.time() + 20
    else:
        deadline = boundaries[-1] + p.horizon_min * 60 + 120
    while p.pending and time.time() < deadline:
        p.mature_pending(int(time.time()))
        if p.pending:
            time.sleep(10)
    for un in p.pending:
        p.journal.append("outcome_missing", {
            "prediction_seq": un["seq"],
            "reason": "exit candle unavailable at deadline"})

    p.finale()
    p.end(attempted, predicted, invalid)
    print(json.dumps({"data_dir": args.data_dir, "attempted": attempted,
                      "predicted": predicted, "invalid": invalid,
                      "matured": p.scored}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
