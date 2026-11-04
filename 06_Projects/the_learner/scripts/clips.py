#!/usr/bin/env python3
"""Clip candidate extractor — genuinely noteworthy real moments only.

Each candidate carries its original journal seq, minute timestamp and its
simulated label. Nothing is rewritten for a better clip.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from learner.journal import Journal  # noqa: E402

TITLES = {
    "referees_review": "The AI Was Confident. Bitcoin Disagreed.",
    "anchor_ahead": "The Frozen Model Beat the Learner Again.",
    "learning_moment": "One Prediction, One Mistake, One Neural Update.",
    "data_break": "Why the AI Refused to Pick a Direction.",
    "science_room": "Did Our Physics Model Just Fail Its Test?",
    "rivalry": "The Learner and the Anchor Disagree.",
}


def hhmm(minute_ts):
    return time.strftime("%H:%M UTC %Y-%m-%d", time.gmtime(minute_ts))


def candidates(data_dir: str) -> list[dict]:
    recs = list(iter(Journal(os.path.join(data_dir, "journal.jsonl"))))
    out = []
    l_pts = a_pts = 0
    for r in recs:
        p = r.get("payload", {})
        k = r["kind"]
        if k == "outcome":
            l_pts += p["learner"]["points"]
            a_pts += p["anchor"]["points"]
            if p.get("referee_review"):
                out.append({"title": TITLES["referees_review"], "seq": r["seq"],
                            "minute_utc": hhmm(p["minute_ts"]),
                            "simulated": True,
                            "why": f"Learner {p['learner_action']} at "
                                   f"{p['learner_conf']:.0%} conf, market "
                                   f"went {p['truth']} ({p['move_bps']:+.1f} bps)"})
            if a_pts > l_pts and l_pts < 0:
                out.append({"title": TITLES["anchor_ahead"], "seq": r["seq"],
                            "minute_utc": hhmm(p["minute_ts"]),
                            "simulated": True,
                            "why": f"score A{a_pts:+d} vs L{l_pts:+d}"})
        elif k == "prediction" and \
                p["learner"]["action"] != p["anchor"]["action"] and \
                abs(p["learner"]["confidence"] - p["anchor"]["confidence"]) > 0.15:
            out.append({"title": TITLES["rivalry"], "seq": r["seq"],
                        "minute_utc": hhmm(p["minute_ts"]),
                        "simulated": True,
                        "why": f"L:{p['learner']['action']} vs "
                               f"A:{p['anchor']['action']}"})
        elif k == "training_update" and p.get("accepted"):
            out.append({"title": TITLES["learning_moment"], "seq": r["seq"],
                        "minute_utc": hhmm(r["minute_ts"]) if r.get("minute_ts") else "n/a",
                        "simulated": True,
                        "why": f"update #{p.get('updates_done')} on "
                               f"{p['evidence_n']} matured records"})
        elif k == "feed_invalid":
            out.append({"title": TITLES["data_break"], "seq": r["seq"],
                        "minute_utc": hhmm(r["minute_ts"]) if r.get("minute_ts") else "n/a",
                        "simulated": True,
                        "why": p["reason"]})
        elif k == "science_eval":
            out.append({"title": TITLES["science_room"], "seq": r["seq"],
                        "minute_utc": hhmm(r["minute_ts"]) if r.get("minute_ts") else "n/a",
                        "simulated": True,
                        "why": p.get("verdict", "")})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    args = ap.parse_args()
    print(json.dumps(candidates(args.data_dir), indent=2))


if __name__ == "__main__":
    main()
