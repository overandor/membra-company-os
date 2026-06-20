"""
proofbook.py — append-only, hash-linked provenance ledger.

Every underwriting decision (and, later, every memory-mesh handoff receipt)
is hashed into a tamper-evident chain: hash_i = sha256(hash_{i-1} || body_i).
This is the "provenance becomes collateral" primitive — a verifiable record
that a given decision/receipt existed with given contents at a given time.

Stored as JSONL so it's greppable and externally auditable.
"""
from __future__ import annotations
import hashlib, json, os, time

GENESIS = "GENESIS"


def _canon(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class ProofBook:
    def __init__(self, path: str):
        self.path = path
        self.entries: list[dict] = []
        if os.path.exists(path):
            with open(path) as fh:
                self.entries = [json.loads(line) for line in fh if line.strip()]

    @property
    def head(self) -> str:
        return self.entries[-1]["hash"] if self.entries else GENESIS

    def append(self, kind: str, payload: dict) -> dict:
        prev = self.head
        body = _canon(payload)
        h = hashlib.sha256((prev + "|" + body).encode()).hexdigest()
        entry = {"index": len(self.entries), "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "kind": kind, "prev": prev, "hash": h, "payload": payload}
        self.entries.append(entry)
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a") as fh:
            fh.write(json.dumps(entry) + "\n")
        return entry

    def verify_chain(self) -> bool:
        prev = GENESIS
        for e in self.entries:
            h = hashlib.sha256((prev + "|" + _canon(e["payload"])).encode()).hexdigest()
            if e["prev"] != prev or e["hash"] != h:
                return False
            prev = e["hash"]
        return True
