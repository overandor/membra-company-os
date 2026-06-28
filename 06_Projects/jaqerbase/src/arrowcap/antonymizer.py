"""Antonymified surrogates: "verifiable non-seeing" of an answer-claim.

Arrow's information paradox says a buyer cannot value information without
consuming it, and once they have consumed it they no longer need to buy it.
The antonymifier resolves this by describing an answer primarily through its
*negative space* -- which structural predicates are confirmed FALSE -- rather
than through its positive content. A buyer can learn that a submitted answer
"does not call eval", "does not perform network I/O", "is in the 'small'
length bucket", and "is bound to commitment <sha256>" without ever seeing
code, prose, or data that could itself satisfy the task.

The profile is cryptographically bound (by SHA-256 of the exact bytes) to
whatever is eventually revealed, so a seller cannot bait-and-switch: the
oracle/settlement layer re-derives the same profile from the revealed answer
and rejects it if the commitment or the predicate set has changed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from .commitment import sha256_hex

CODE_PREDICATES: dict[str, Callable[[str], bool]] = {
    "uses_eval_or_exec": lambda s: bool(re.search(r"\b(eval|exec)\s*\(", s)),
    "uses_network_io": lambda s: bool(
        re.search(r"\b(socket|requests|urllib|http\.client|aiohttp)\b", s)
    ),
    "uses_subprocess_or_shell": lambda s: bool(
        re.search(r"\b(subprocess|os\.system|os\.popen|shutil\.rmtree)\b", s)
    ),
    "uses_file_write": lambda s: bool(re.search(r"open\([^)]*['\"][wa]", s)),
    "defines_class": lambda s: bool(re.search(r"^\s*class\s+\w+", s, re.MULTILINE)),
    "uses_async": lambda s: "async def" in s or "await " in s,
    "uses_global_state": lambda s: bool(re.search(r"^\s*global\s+\w+", s, re.MULTILINE)),
    "contains_todo_or_stub": lambda s: bool(
        re.search(r"\bTODO\b|NotImplementedError", s)
    ),
    "raises_exceptions": lambda s: bool(re.search(r"^\s*raise\s+\w+", s, re.MULTILINE)),
    "uses_recursion_hint": lambda s: bool(
        re.search(r"def\s+(\w+)\([^)]*\):[^\n]*\n(?:.*\n)*?\s+\1\(", s)
    ),
}

GENERIC_PREDICATES: dict[str, Callable[[str], bool]] = {
    "contains_url": lambda s: bool(re.search(r"https?://", s)),
    "contains_email_like": lambda s: bool(
        re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", s)
    ),
    "contains_ssn_like": lambda s: bool(re.search(r"\b\d{3}-\d{2}-\d{4}\b", s)),
    "contains_credit_card_like": lambda s: bool(
        re.search(r"\b(?:\d[ -]*?){13,16}\b", s)
    ),
    "all_numeric": lambda s: bool(s.strip()) and s.strip().replace(".", "").replace(
        "-", ""
    ).replace(",", "").isdigit(),
    "multiline": lambda s: "\n" in s.strip(),
}

_RISK_WEIGHTS = {
    "uses_eval_or_exec": 0.35,
    "uses_subprocess_or_shell": 0.3,
    "uses_network_io": 0.2,
    "uses_file_write": 0.15,
    "contains_credit_card_like": 0.4,
    "contains_ssn_like": 0.4,
}


def length_bucket(n: int) -> str:
    if n == 0:
        return "empty"
    if n < 256:
        return "tiny"
    if n < 4096:
        return "small"
    if n < 65536:
        return "medium"
    if n < 1 << 20:
        return "large"
    return "huge"


@dataclass
class AntonymProfile:
    broad_class: str
    length_bucket: str
    risk_score: float
    affirmed: list[str] = field(default_factory=list)
    negated: list[str] = field(default_factory=list)
    commitment_sha256: str = ""

    def to_dict(self) -> dict:
        return {
            "broad_class": self.broad_class,
            "length_bucket": self.length_bucket,
            "risk_score": self.risk_score,
            "affirmed": sorted(self.affirmed),
            "negated": sorted(self.negated),
            "exclusion_count": len(self.negated),
            "commitment_sha256": self.commitment_sha256,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AntonymProfile":
        return cls(
            broad_class=data["broad_class"],
            length_bucket=data["length_bucket"],
            risk_score=data["risk_score"],
            affirmed=list(data.get("affirmed", [])),
            negated=list(data.get("negated", [])),
            commitment_sha256=data.get("commitment_sha256", ""),
        )


def _predicate_set(broad_class: str) -> dict[str, Callable[[str], bool]]:
    if broad_class in ("source", "code"):
        return {**CODE_PREDICATES, **GENERIC_PREDICATES}
    return GENERIC_PREDICATES


def antonymify(content: bytes, broad_class: str = "text") -> AntonymProfile:
    """Derive a verifiable non-seeing profile from raw answer bytes.

    The profile never includes the content itself. It includes a length
    bucket (not exact length), a bounded risk score, and a predicate set
    split into affirmed (true-but-structural, e.g. "defines_class") and
    negated (false, e.g. "does_not_use_network_io") -- the latter is the
    antonymified core: it bounds the answer by what it provably is not.
    """
    text = content.decode("utf-8", errors="replace")
    predicates = _predicate_set(broad_class)
    affirmed: list[str] = []
    negated: list[str] = []
    for name, fn in predicates.items():
        try:
            is_true = bool(fn(text))
        except Exception:
            is_true = False
        if is_true:
            affirmed.append(name)
        else:
            negated.append(f"does_not_{name}")

    risk = sum(_RISK_WEIGHTS.get(name, 0.0) for name in affirmed)
    risk = max(0.0, min(1.0, risk))

    return AntonymProfile(
        broad_class=broad_class,
        length_bucket=length_bucket(len(content)),
        risk_score=round(risk, 4),
        affirmed=affirmed,
        negated=negated,
        commitment_sha256=sha256_hex(content),
    )


def verify_binding(profile: AntonymProfile, revealed_content: bytes) -> tuple[bool, list[str]]:
    """Re-derive the profile from the revealed answer and check it matches
    what was promised at preview time. Returns (ok, mismatches)."""
    recomputed = antonymify(revealed_content, profile.broad_class)
    mismatches: list[str] = []
    if recomputed.commitment_sha256 != profile.commitment_sha256:
        mismatches.append("sha256_mismatch")
    if recomputed.length_bucket != profile.length_bucket:
        mismatches.append("length_bucket_mismatch")
    if set(recomputed.affirmed) != set(profile.affirmed):
        mismatches.append("affirmed_predicate_mismatch")
    if set(recomputed.negated) != set(profile.negated):
        mismatches.append("negated_predicate_mismatch")
    return (len(mismatches) == 0, mismatches)
