"""Claims: a buyer's task-with-hidden-tests, and a seller's bonded
answer-claim against it.

A Claim is the buyer's posted task: a description, a reward, and a path to a
hidden pytest suite that will serve as the oracle. An AnswerClaim is a
seller's bonded submission against a Claim: it starts as nothing but an
AntonymProfile (Section 4: resemblance without recoverability) and a
commitment hash, and only gains a revealed answer after bonding and escrow
are both in place (see escrow.py for the state machine that enforces this
ordering).
"""

from __future__ import annotations

import base64
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from .antonymizer import AntonymProfile

_SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    buyer_account TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    reward_cents INTEGER NOT NULL CHECK (reward_cents > 0),
    hidden_test_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'escrowed', 'resolved', 'cancelled')),
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS answer_claims (
    answer_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(claim_id),
    seller_account TEXT NOT NULL,
    antonym_profile_json TEXT NOT NULL,
    commitment_sha256 TEXT NOT NULL,
    bond_cents INTEGER NOT NULL,
    bond_hold_id INTEGER,
    escrow_hold_id INTEGER,
    revealed_answer_b64 TEXT,
    oracle_passed INTEGER,
    oracle_report_json TEXT,
    status TEXT NOT NULL DEFAULT 'preview'
        CHECK (status IN ('preview', 'bonded', 'funded', 'revealed', 'settled')),
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_answers_claim ON answer_claims(claim_id);
"""


def new_claim_id() -> str:
    return f"claim-{uuid.uuid4().hex[:12]}"


def new_answer_id() -> str:
    return f"answer-{uuid.uuid4().hex[:12]}"


@dataclass
class Claim:
    claim_id: str
    buyer_account: str
    title: str
    description: str
    reward_cents: int
    hidden_test_path: str
    status: str
    created_at: float


@dataclass
class AnswerClaim:
    answer_id: str
    claim_id: str
    seller_account: str
    antonym_profile: AntonymProfile
    commitment_sha256: str
    bond_cents: int
    bond_hold_id: Optional[int]
    escrow_hold_id: Optional[int]
    revealed_answer: Optional[bytes]
    oracle_passed: Optional[bool]
    oracle_report: Optional[dict]
    status: str
    created_at: float
    updated_at: float


class ClaimStore:
    """Shares a SQLite file with a Ledger (each keeps its own connection;
    SQLite's WAL mode serializes writers across connections to the same
    file). The escrow state machine sequences operations across the two
    stores so that no step assumes cross-connection atomicity."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        self._conn.close()

    def create_claim(
        self, buyer_account: str, title: str, description: str, reward_cents: int,
        hidden_test_path: str, claim_id: Optional[str] = None,
    ) -> Claim:
        claim_id = claim_id or new_claim_id()
        now = time.time()
        self._conn.execute(
            "INSERT INTO claims (claim_id, buyer_account, title, description, "
            "reward_cents, hidden_test_path, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'open', ?)",
            (claim_id, buyer_account, title, description, reward_cents, hidden_test_path, now),
        )
        return self.get_claim(claim_id)

    def get_claim(self, claim_id: str) -> Claim:
        row = self._conn.execute(
            "SELECT * FROM claims WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no such claim: {claim_id}")
        return Claim(**dict(row))

    def list_claims(self, status: Optional[str] = None) -> list[Claim]:
        if status:
            rows = self._conn.execute(
                "SELECT * FROM claims WHERE status = ? ORDER BY created_at", (status,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM claims ORDER BY created_at").fetchall()
        return [Claim(**dict(r)) for r in rows]

    def set_claim_status(self, claim_id: str, status: str) -> None:
        self._conn.execute(
            "UPDATE claims SET status = ? WHERE claim_id = ?", (status, claim_id)
        )

    def submit_preview(
        self, claim_id: str, seller_account: str, antonym_profile: AntonymProfile,
        bond_cents: int, answer_id: Optional[str] = None,
    ) -> AnswerClaim:
        answer_id = answer_id or new_answer_id()
        now = time.time()
        self._conn.execute(
            "INSERT INTO answer_claims (answer_id, claim_id, seller_account, "
            "antonym_profile_json, commitment_sha256, bond_cents, status, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 'preview', ?, ?)",
            (
                answer_id, claim_id, seller_account,
                json.dumps(antonym_profile.to_dict()), antonym_profile.commitment_sha256,
                bond_cents, now, now,
            ),
        )
        return self.get_answer(answer_id)

    def _row_to_answer(self, row: sqlite3.Row) -> AnswerClaim:
        revealed = row["revealed_answer_b64"]
        return AnswerClaim(
            answer_id=row["answer_id"],
            claim_id=row["claim_id"],
            seller_account=row["seller_account"],
            antonym_profile=AntonymProfile.from_dict(json.loads(row["antonym_profile_json"])),
            commitment_sha256=row["commitment_sha256"],
            bond_cents=row["bond_cents"],
            bond_hold_id=row["bond_hold_id"],
            escrow_hold_id=row["escrow_hold_id"],
            revealed_answer=base64.b64decode(revealed) if revealed else None,
            oracle_passed=bool(row["oracle_passed"]) if row["oracle_passed"] is not None else None,
            oracle_report=json.loads(row["oracle_report_json"]) if row["oracle_report_json"] else None,
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_answer(self, answer_id: str) -> AnswerClaim:
        row = self._conn.execute(
            "SELECT * FROM answer_claims WHERE answer_id = ?", (answer_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no such answer claim: {answer_id}")
        return self._row_to_answer(row)

    def list_answers_for_claim(self, claim_id: str) -> list[AnswerClaim]:
        rows = self._conn.execute(
            "SELECT * FROM answer_claims WHERE claim_id = ? ORDER BY created_at", (claim_id,)
        ).fetchall()
        return [self._row_to_answer(r) for r in rows]

    def set_bond_hold(self, answer_id: str, hold_id: int) -> None:
        self._conn.execute(
            "UPDATE answer_claims SET bond_hold_id = ?, status = 'bonded', "
            "updated_at = ? WHERE answer_id = ?",
            (hold_id, time.time(), answer_id),
        )

    def set_escrow_hold(self, answer_id: str, hold_id: int) -> None:
        self._conn.execute(
            "UPDATE answer_claims SET escrow_hold_id = ?, status = 'funded', "
            "updated_at = ? WHERE answer_id = ?",
            (hold_id, time.time(), answer_id),
        )

    def set_revealed_answer(self, answer_id: str, content: bytes) -> None:
        self._conn.execute(
            "UPDATE answer_claims SET revealed_answer_b64 = ?, status = 'revealed', "
            "updated_at = ? WHERE answer_id = ?",
            (base64.b64encode(content).decode("ascii"), time.time(), answer_id),
        )

    def set_oracle_result(self, answer_id: str, passed: bool, report: dict) -> None:
        self._conn.execute(
            "UPDATE answer_claims SET oracle_passed = ?, oracle_report_json = ?, "
            "updated_at = ? WHERE answer_id = ?",
            (1 if passed else 0, json.dumps(report), time.time(), answer_id),
        )

    def set_settled(self, answer_id: str) -> None:
        self._conn.execute(
            "UPDATE answer_claims SET status = 'settled', updated_at = ? WHERE answer_id = ?",
            (time.time(), answer_id),
        )
