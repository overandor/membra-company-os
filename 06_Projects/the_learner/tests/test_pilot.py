import json
import os
import sys
import tempfile

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from learner import models, referee, scientist  # noqa: E402
from learner.director import pick_scene  # noqa: E402
from learner.journal import Journal  # noqa: E402
from learner.trainer import BoundedTrainer  # noqa: E402


def test_journal_chain_and_tamper_detection(tmp_path):
    p = str(tmp_path / "j.jsonl")
    j = Journal(p)
    j.append("a", {"x": 1})
    j.append("b", {"y": 2})
    j.close()
    assert Journal.verify(p) == []
    # tamper: rewrite one payload
    lines = open(p).read().splitlines()
    rec = json.loads(lines[0])
    rec["payload"]["x"] = 999
    lines[0] = json.dumps(rec, sort_keys=True)
    open(p, "w").write("\n".join(lines) + "\n")
    errs = Journal.verify(p)
    assert errs and errs[0].reason.startswith("record hash") or \
        any("prev_hash" in e.reason or "hash" in e.reason for e in errs)


def test_referee_deterministic():
    out = referee.score(100.0, 100.5, "LONG", 0.7, "SHORT", 1, 0, 600)
    assert out.truth == "UP" and out.learner_points == 1 \
        and out.anchor_points == -1 and out.referee_review is False
    out2 = referee.score(100.0, 99.9, "SHORT", 0.8, "LONG", 1, 0, 600)
    assert out2.truth == "DOWN" and out2.learner_correct \
        and out2.referee_review is False
    flat = referee.score(100.0, 100.02, "WAIT", 0.9, "LONG", 1, 0, 600)
    assert flat.truth == "FLAT" and flat.learner_correct
    miss = referee.score(100.0, 99.0, "LONG", 0.9, "WAIT", 1, 0, 600)
    assert miss.referee_review is True


def test_identical_birth_and_anchor_frozen(tmp_path):
    b = models.Birth(scientist.feature_spec()["dim"], str(tmp_path))
    assert b.birth_hash == b.learner.hash() == b.anchor.hash()
    x = np.random.RandomState(0).randn(scientist.feature_spec()["dim"])
    lp = b.learner.predict(x)
    ap = b.anchor.predict(x)
    assert lp.action == ap.action and lp.confidence == ap.confidence


def test_trainer_bounds_and_accept(tmp_path):
    b = models.Birth(scientist.feature_spec()["dim"], str(tmp_path))
    tr = BoundedTrainer(min_batch=4, max_updates=2, cooldown_s=0,
                        lr=0.02, delta_norm_cap=0.05, max_drift=1.0)
    birth = (b.learner.w1.copy(), b.learner.b1.copy(),
             b.learner.w2.copy(), b.learner.b2.copy())
    matured = []
    rng = np.random.RandomState(1)
    for i in range(6):
        x = rng.randn(scientist.feature_spec()["dim"])
        pred = b.learner.predict(x)
        matured.append({"prediction_seq": i + 1, "features": list(x),
                        "learner_action": pred.action,
                        "learner": {"points": 1 if i % 2 else -1}})
    r = tr.maybe_update(b.learner, birth, matured, str(tmp_path))
    assert r["accepted"] and r["delta_norm_applied"] <= 0.050001
    assert r["weights_hash_before"] != r["weights_hash_after"]
    assert b.anchor.hash() == b.birth_hash
    more = []
    for i in range(6, 12):
        x = rng.randn(scientist.feature_spec()["dim"])
        pred = b.learner.predict(x)
        more.append({"prediction_seq": i + 1, "features": list(x),
                     "learner_action": pred.action,
                     "learner": {"points": 1}})
    matured += more
    r2 = tr.maybe_update(b.learner, birth, matured, str(tmp_path))
    assert r2["accepted"]
    r3 = tr.maybe_update(b.learner, birth, matured, str(tmp_path))
    assert not r3["accepted"] and r3["reason"] == "update_cap_reached"


def test_trainer_rejects_insufficient_evidence(tmp_path):
    b = models.Birth(scientist.feature_spec()["dim"], str(tmp_path))
    tr = BoundedTrainer(min_batch=8, cooldown_s=0)
    r = tr.maybe_update(b.learner,
                        (b.learner.w1, b.learner.b1, b.learner.w2,
                         b.learner.b2), [], str(tmp_path))
    assert r == {"accepted": False, "reason": "insufficient_evidence",
                 "evidence_n": 0}


def test_pick_scene_mapping():
    base = {"seq": 5, "hash": "x", "payload": {}}
    assert pick_scene({**base, "kind": "prediction",
                       "payload": {"learner": {"action": "LONG"},
                                   "anchor": {"action": "LONG"}}}
                      ) == "next_round"
    assert pick_scene({**base, "kind": "prediction",
                       "payload": {"learner": {"action": "LONG"},
                                   "anchor": {"action": "SHORT"}}}
                      ) == "rivalry"
    assert pick_scene({**base, "kind": "outcome",
                       "payload": {"referee_review": True}}) \
        == "referees_review"
    assert pick_scene({**base, "kind": "training_update",
                       "payload": {"accepted": False}}) is None
    assert pick_scene({**base, "kind": "feed_invalid"}) == "data_break"
    assert pick_scene({**base, "kind": "season_score"}) == "season_score"


def test_features_deterministic():
    from learner.feed import Candle
    candles = [Candle(t=i * 60, o=100 + i * 0.1, h=101, l=99,
                      c=100 + i * 0.15, v=1000 + i) for i in range(40)]
    a = scientist.compute_features(candles, 0.0001)
    bb = scientist.compute_features(candles, 0.0001)
    assert np.array_equal(a, bb)
    assert len(a) == scientist.feature_spec()["dim"]
    assert np.all(np.isfinite(a))
