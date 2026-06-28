"""Persistent pane/workflow state. A real SQLite database (WAL mode, foreign
keys on) — not an in-memory dict — because the CLI is invoked as separate OS
processes that must not lose state between calls."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional

VALID_STATES = ("sleeping", "warming", "awake", "working", "cooling", "archived")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS panes (
    pane_id TEXT PRIMARY KEY,
    session_name TEXT NOT NULL,
    role TEXT NOT NULL,
    state TEXT NOT NULL,
    last_activity_ts REAL NOT NULL,
    created_ts REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    pane_id TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT NOT NULL,
    fitness_before REAL,
    fitness_after REAL,
    FOREIGN KEY (pane_id) REFERENCES panes(pane_id)
);
"""


@dataclass(frozen=True)
class PaneRecord:
    pane_id: str
    session_name: str
    role: str
    state: str
    last_activity_ts: float
    created_ts: float


class WorkflowStore:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        self._conn.close()

    def register_pane(self, pane_id: str, session_name: str, role: str, now: float) -> PaneRecord:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT INTO panes (pane_id, session_name, role, state, last_activity_ts, created_ts) "
                "VALUES (?, ?, ?, 'awake', ?, ?)",
                (pane_id, session_name, role, now, now),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return self.get_pane(pane_id)

    def get_pane(self, pane_id: str) -> Optional[PaneRecord]:
        row = self._conn.execute(
            "SELECT pane_id, session_name, role, state, last_activity_ts, created_ts "
            "FROM panes WHERE pane_id = ?",
            (pane_id,),
        ).fetchone()
        return PaneRecord(*row) if row else None

    def list_panes(self, session_name: Optional[str] = None) -> List[PaneRecord]:
        if session_name is None:
            rows = self._conn.execute(
                "SELECT pane_id, session_name, role, state, last_activity_ts, created_ts FROM panes"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT pane_id, session_name, role, state, last_activity_ts, created_ts "
                "FROM panes WHERE session_name = ?",
                (session_name,),
            ).fetchall()
        return [PaneRecord(*row) for row in rows]

    def update_state(self, pane_id: str, state: str, now: float) -> None:
        if state not in VALID_STATES:
            raise ValueError(f"invalid state {state!r}; must be one of {VALID_STATES}")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE panes SET state = ? WHERE pane_id = ?", (state, pane_id)
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def touch_activity(self, pane_id: str, now: float) -> None:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE panes SET last_activity_ts = ? WHERE pane_id = ?", (now, pane_id)
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def remove_pane(self, pane_id: str) -> None:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute("DELETE FROM receipts WHERE pane_id = ?", (pane_id,))
            self._conn.execute("DELETE FROM panes WHERE pane_id = ?", (pane_id,))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def add_receipt(
        self,
        pane_id: str,
        action: str,
        detail: str,
        now: float,
        fitness_before: Optional[float] = None,
        fitness_after: Optional[float] = None,
    ) -> int:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "INSERT INTO receipts (ts, pane_id, action, detail, fitness_before, fitness_after) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (now, pane_id, action, detail, fitness_before, fitness_after),
            )
            self._conn.execute("COMMIT")
            return cur.lastrowid
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def list_receipts(self, pane_id: Optional[str] = None) -> List[sqlite3.Row]:
        if pane_id is None:
            return self._conn.execute(
                "SELECT id, ts, pane_id, action, detail, fitness_before, fitness_after "
                "FROM receipts ORDER BY id"
            ).fetchall()
        return self._conn.execute(
            "SELECT id, ts, pane_id, action, detail, fitness_before, fitness_after "
            "FROM receipts WHERE pane_id = ? ORDER BY id",
            (pane_id,),
        ).fetchall()
