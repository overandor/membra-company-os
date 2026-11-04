"""The Referee — deterministic scoring, fixed before the pilot starts.

Rules (referee-v1), frozen at pilot_start and recorded in the journal:
  horizon_min   : minutes between prediction boundary and outcome close
  flat_band_bps : |move| below this -> truth is FLAT
  points        : correct +1, wrong -1, no partial credit
  high_conf_miss: confidence >= 0.6 AND wrong -> THE REFEREE'S REVIEW

Every score is re-derivable from the journal alone: entry price, exit price,
the model's action, and this rule version.
"""

from __future__ import annotations

from dataclasses import dataclass

RULES_VERSION = "referee-v1"
FLAT_BAND_BPS = 3.0
HIGH_CONF_THRESHOLD = 0.6
HORIZON_MIN = 10  # fixed before the pilot; never tuned afterwards


def truth_label(move_bps: float, band: float = FLAT_BAND_BPS) -> str:
    if move_bps > band:
        return "UP"
    if move_bps < -band:
        return "DOWN"
    return "FLAT"


def score_action(action: str, truth: str) -> tuple[int, bool]:
    """Returns (points, correct)."""
    win = {"UP": "LONG", "DOWN": "SHORT", "FLAT": "WAIT"}
    correct = action == win[truth]
    return (1 if correct else -1), correct


@dataclass
class Outcome:
    prediction_seq: int
    minute_ts: int
    mature_minute_ts: int
    entry_price: float
    exit_price: float
    move_bps: float
    truth: str
    learner_points: int
    learner_correct: bool
    anchor_points: int
    anchor_correct: bool
    referee_review: bool   # high-confidence miss by the Learner
    rules_version: str = RULES_VERSION

    def to_payload(self) -> dict:
        return {
            "prediction_seq": self.prediction_seq,
            "minute_ts": self.minute_ts,
            "mature_minute_ts": self.mature_minute_ts,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "move_bps": self.move_bps,
            "truth": self.truth,
            "learner": {"points": self.learner_points,
                        "correct": self.learner_correct},
            "anchor": {"points": self.anchor_points,
                       "correct": self.anchor_correct},
            "referee_review": self.referee_review,
            "rules_version": self.rules_version,
        }


def score(entry_price: float, exit_price: float,
          learner_action: str, learner_conf: float,
          anchor_action: str, prediction_seq: int,
          minute_ts: int, mature_minute_ts: int) -> Outcome:
    move_bps = (exit_price - entry_price) / entry_price * 1e4
    truth = truth_label(move_bps)
    lp, lc = score_action(learner_action, truth)
    ap, ac = score_action(anchor_action, truth)
    review = lc is False and learner_conf >= HIGH_CONF_THRESHOLD
    return Outcome(prediction_seq=prediction_seq, minute_ts=minute_ts,
                   mature_minute_ts=mature_minute_ts,
                   entry_price=entry_price, exit_price=exit_price,
                   move_bps=move_bps, truth=truth,
                   learner_points=lp, learner_correct=lc,
                   anchor_points=ap, anchor_correct=ac,
                   referee_review=review)
