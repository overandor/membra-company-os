"""The Narrator — a local LLM that reads only journal records.

Rules enforced in code:
  * The model prompt contains ONLY the journal record(s) being narrated —
    no market context the journal does not hold.
  * Every narration is written back to the journal as a `narration` event
    naming its source record seqs, so both scenes read it from the journal.
  * The narrator may not invent causation, neuron intent, or motives —
    the prompt forbids it and the fallback labels itself as a template.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Optional

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:0.5b"
TIMEOUT_S = 30

_SYSTEM = (
    "You narrate a live experiment called THE LEARNER: AI vs Bitcoin. "
    "You receive ONE journal record as JSON. Write exactly one short "
    "sentence (<=18 words) for a stranger watching. Only describe what the "
    "record shows. entry_price is the observed price, not a price target. "
    "Never claim causes, feelings, or intentions. Never say a "
    "model 'believes' or 'wants'. Say 'the Learner predicted' not 'thinks'. "
    "Mention numbers from the record. No emojis."
)


def _template_line(rec: dict) -> str:
    p = rec.get("payload", {})
    k = rec.get("kind")
    if k == "prediction":
        l, a = p["learner"], p["anchor"]
        return (f"Minute {p['minute_ts']}: Learner {l['action']} "
                f"{l['confidence']:.0%}, Anchor {a['action']} "
                f"{a['confidence']:.0%}, BTC {p['entry_price']:.1f}.")
    if k == "outcome":
        return (f"Move {p['move_bps']:+.1f} bps ({p['truth']}): "
                f"Learner {'+' if p['learner']['correct'] else ''}"
                f"{'right' if p['learner']['correct'] else 'wrong'}, "
                f"Anchor {'right' if p['anchor']['correct'] else 'wrong'}.")
    if k == "training_update":
        return (f"Update {'accepted' if p['accepted'] else 'rejected'}: "
                f"{p['reason']} on {p.get('evidence_n', 0)} matured records.")
    if k == "feed_invalid":
        return f"Feed invalid ({p['reason']}); predictions paused this cycle."
    if k == "science_eval":
        return (f"Science check: scientist features "
                f"{p.get('scientist_acc')}, simple baseline "
                f"{p.get('baseline_acc')}.")
    if k == "season_score":
        return (f"Season score — Learner {p['learner']['points']} pts "
                f"vs Anchor {p['anchor']['points']} pts.")
    return f"Journal record {rec.get('seq')} ({k})."


class Narrator:
    def __init__(self, model: str = MODEL):
        self.model = model
        self.engine = "template-v1"
        try:
            req = urllib.request.Request(
                "http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=3) as r:
                tags = json.loads(r.read())
            names = [m["name"] for m in tags.get("models", [])]
            if any(n.startswith(model.split(":")[0]) for n in names):
                self.engine = f"ollama:{model}"
            elif names:
                self.model = names[0]
                self.engine = f"ollama:{self.model}"
        except Exception:
            pass

    def narrate(self, rec: dict) -> dict:
        """Returns {'text', 'engine', 'source_seq'} — payload for the journal."""
        if self.engine.startswith("ollama:"):
            try:
                body = json.dumps({
                    "model": self.model, "stream": False,
                    "system": _SYSTEM,
                    "prompt": "Narrate this journal record:\n"
                              + json.dumps(rec, sort_keys=True)[:3000],
                    "options": {"temperature": 0.2, "num_predict": 60},
                }).encode()
                req = urllib.request.Request(
                    OLLAMA_URL, data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST")
                with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                    text = json.loads(r.read())["response"].strip()
                text = " ".join(text.split())
                if text:
                    return {"text": text, "engine": self.engine,
                            "source_seq": rec["seq"]}
            except Exception:
                pass
            self.engine = "template-v1"
        return {"text": _template_line(rec), "engine": self.engine,
                "source_seq": rec["seq"]}
