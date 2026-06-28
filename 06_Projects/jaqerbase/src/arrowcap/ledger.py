"""An ACID, append-only ledger backed by SQLite.

Every balance change is driven by an explicit, immediately-locked
transaction and recorded as an immutable ledger_entries row, so the full
history of any account is reconstructable and auditable. Holds (escrow and
bond) reduce the holder's spendable balance the instant they are created and
can only be resolved by release (back to the holder or forward to a
counterparty) or slash (forward to a counterparty only) -- there is no path
that lets a held amount silently disappear or be spent twice.
"""

from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional


class LedgerError(Exception):
    pass


class AccountNotFound(LedgerError):
    pass


class InsufficientFunds(LedgerError):
    pass


class InvalidHoldState(LedgerError):
    pass


_SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    balance_cents INTEGER NOT NULL DEFAULT 0 CHECK (balance_cents >= 0),
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    delta_cents INTEGER NOT NULL,
    balance_after_cents INTEGER NOT NULL,
    kind TEXT NOT NULL,
    ref_id TEXT,
    memo TEXT,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS holds (
    hold_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    kind TEXT NOT NULL CHECK (kind IN ('escrow', 'bond')),
    ref_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'released', 'slashed')),
    created_at REAL NOT NULL,
    resolved_at REAL,
    resolution_account_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_entries_account ON ledger_entries(account_id);
CREATE INDEX IF NOT EXISTS idx_holds_ref ON holds(ref_id);
"""


@dataclass
class Hold:
    hold_id: int
    account_id: str
    amount_cents: int
    kind: str
    ref_id: str
    status: str
    created_at: float
    resolved_at: Optional[float]
    resolution_account_id: Optional[str]


class Ledger:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def _txn(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def open_account(self, account_id: str) -> None:
        with self._txn() as cur:
            cur.execute(
                "INSERT OR IGNORE INTO accounts (account_id, balance_cents, created_at) "
                "VALUES (?, 0, ?)",
                (account_id, time.time()),
            )

    def balance(self, account_id: str) -> int:
        row = self._conn.execute(
            "SELECT balance_cents FROM accounts WHERE account_id = ?", (account_id,)
        ).fetchone()
        if row is None:
            raise AccountNotFound(account_id)
        return row["balance_cents"]

    def _adjust(
        self, cur: sqlite3.Cursor, account_id: str, delta_cents: int, kind: str,
        ref_id: Optional[str], memo: Optional[str],
    ) -> int:
        row = cur.execute(
            "SELECT balance_cents FROM accounts WHERE account_id = ?", (account_id,)
        ).fetchone()
        if row is None:
            raise AccountNotFound(account_id)
        new_balance = row["balance_cents"] + delta_cents
        if new_balance < 0:
            raise InsufficientFunds(
                f"account {account_id} has {row['balance_cents']} cents, "
                f"cannot apply delta {delta_cents}"
            )
        cur.execute(
            "UPDATE accounts SET balance_cents = ? WHERE account_id = ?",
            (new_balance, account_id),
        )
        cur.execute(
            "INSERT INTO ledger_entries "
            "(account_id, delta_cents, balance_after_cents, kind, ref_id, memo, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (account_id, delta_cents, new_balance, kind, ref_id, memo, time.time()),
        )
        return new_balance

    def deposit(
        self, account_id: str, amount_cents: int, *, ref_id: Optional[str] = None,
        memo: Optional[str] = None,
    ) -> int:
        if amount_cents <= 0:
            raise ValueError("deposit amount must be positive")
        with self._txn() as cur:
            return self._adjust(cur, account_id, amount_cents, "deposit", ref_id, memo)

    def transfer(
        self, from_account: str, to_account: str, amount_cents: int, *,
        ref_id: Optional[str] = None, memo: Optional[str] = None,
    ) -> None:
        if amount_cents <= 0:
            raise ValueError("transfer amount must be positive")
        with self._txn() as cur:
            self._adjust(cur, from_account, -amount_cents, "transfer_out", ref_id, memo)
            self._adjust(cur, to_account, amount_cents, "transfer_in", ref_id, memo)

    def create_hold(
        self, account_id: str, amount_cents: int, kind: str, ref_id: str,
    ) -> int:
        if kind not in ("escrow", "bond"):
            raise ValueError("kind must be 'escrow' or 'bond'")
        if amount_cents <= 0:
            raise ValueError("hold amount must be positive")
        with self._txn() as cur:
            self._adjust(cur, account_id, -amount_cents, f"{kind}_hold", ref_id, None)
            cur.execute(
                "INSERT INTO holds (account_id, amount_cents, kind, ref_id, status, created_at) "
                "VALUES (?, ?, ?, ?, 'active', ?)",
                (account_id, amount_cents, kind, ref_id, time.time()),
            )
            return cur.lastrowid

    def _get_hold(self, cur: sqlite3.Cursor, hold_id: int) -> sqlite3.Row:
        row = cur.execute("SELECT * FROM holds WHERE hold_id = ?", (hold_id,)).fetchone()
        if row is None:
            raise InvalidHoldState(f"no such hold: {hold_id}")
        if row["status"] != "active":
            raise InvalidHoldState(f"hold {hold_id} is already {row['status']}")
        return row

    def release_hold(self, hold_id: int, destination_account_id: Optional[str] = None) -> None:
        with self._txn() as cur:
            hold = self._get_hold(cur, hold_id)
            destination = destination_account_id or hold["account_id"]
            self._adjust(
                cur, destination, hold["amount_cents"], f"{hold['kind']}_release",
                hold["ref_id"], None,
            )
            cur.execute(
                "UPDATE holds SET status = 'released', resolved_at = ?, "
                "resolution_account_id = ? WHERE hold_id = ?",
                (time.time(), destination, hold_id),
            )

    def slash_hold(self, hold_id: int, destination_account_id: str) -> None:
        with self._txn() as cur:
            hold = self._get_hold(cur, hold_id)
            self._adjust(
                cur, destination_account_id, hold["amount_cents"], f"{hold['kind']}_slash",
                hold["ref_id"], None,
            )
            cur.execute(
                "UPDATE holds SET status = 'slashed', resolved_at = ?, "
                "resolution_account_id = ? WHERE hold_id = ?",
                (time.time(), destination_account_id, hold_id),
            )

    def get_hold(self, hold_id: int) -> Hold:
        row = self._conn.execute("SELECT * FROM holds WHERE hold_id = ?", (hold_id,)).fetchone()
        if row is None:
            raise InvalidHoldState(f"no such hold: {hold_id}")
        return Hold(**dict(row))

    def holds_for_ref(self, ref_id: str) -> list[Hold]:
        rows = self._conn.execute(
            "SELECT * FROM holds WHERE ref_id = ? ORDER BY hold_id", (ref_id,)
        ).fetchall()
        return [Hold(**dict(r)) for r in rows]

    def history(self, account_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM ledger_entries WHERE account_id = ? ORDER BY entry_id",
            (account_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def all_resolved_holds(self, kind: Optional[str] = None) -> list[Hold]:
        if kind:
            rows = self._conn.execute(
                "SELECT * FROM holds WHERE status != 'active' AND kind = ? ORDER BY hold_id",
                (kind,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM holds WHERE status != 'active' ORDER BY hold_id"
            ).fetchall()
        return [Hold(**dict(r)) for r in rows]
