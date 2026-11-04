"""Append-only, hash-chained event journal — the single source of truth.

Every surface (vertical scene, landscape scene, narrator, verifier) reads only
from this journal. Records are canonical-JSON hashed into a chain:
record.hash = sha256(canonical(record without 'hash') including prev_hash).

Integrity rules enforced here:
  1. Records are appended only — never edited or removed (file opened 'a').
  2. Canonical serialization is deterministic (sort_keys, tight separators),
     so any verifier can re-derive every hash.
  3. `verify()` replays the whole chain and reports the first break.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Iterator, Optional


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_hash(record: dict) -> str:
    body = {k: v for k, v in record.items() if k != "hash"}
    return sha256_hex(canonical(body))


@dataclass
class ChainError:
    seq: int
    reason: str


class Journal:
    """Append-only JSONL journal with a SHA-256 hash chain."""

    GENESIS = "0" * 64

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self._seq = 0
        self._prev_hash = self.GENESIS
        if os.path.exists(path) and os.path.getsize(path) > 0:
            last = None
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        last = json.loads(line)
            if last is not None:
                self._seq = int(last["seq"])
                self._prev_hash = last["hash"]
        self._fh = open(path, "a", encoding="utf-8", buffering=1)

    def append(self, kind: str, payload: dict, minute_ts: Optional[int] = None) -> dict:
        rec = {
            "seq": self._seq + 1,
            "kind": kind,
            "ts_unix": int(time.time()),
            "minute_ts": minute_ts,
            "payload": payload,
            "prev_hash": self._prev_hash,
        }
        rec["hash"] = record_hash(rec)
        self._fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=True) + "\n")
        self._fh.flush()
        os.fsync(self._fh.fileno())
        self._seq = rec["seq"]
        self._prev_hash = rec["hash"]
        return rec

    def close(self) -> None:
        try:
            self._fh.close()
        except Exception:
            pass

    def __iter__(self) -> Iterator[dict]:
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)

    @staticmethod
    def verify(path: str) -> list[ChainError]:
        """Replay the chain. Returns [] when the journal is intact."""
        errors: list[ChainError] = []
        prev = Journal.GENESIS
        expected_seq = 1
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    errors.append(ChainError(lineno, "unparseable line"))
                    continue
                if rec.get("seq") != expected_seq:
                    errors.append(ChainError(rec.get("seq", lineno),
                                             f"seq gap: expected {expected_seq}"))
                if rec.get("prev_hash") != prev:
                    errors.append(ChainError(rec.get("seq", lineno),
                                             "prev_hash mismatch (insert/edit/delete)"))
                if rec.get("hash") != record_hash(rec):
                    errors.append(ChainError(rec.get("seq", lineno),
                                             "record hash mismatch (tampered payload)"))
                prev = rec.get("hash", prev)
                expected_seq = rec.get("seq", expected_seq) + 1
        return errors
