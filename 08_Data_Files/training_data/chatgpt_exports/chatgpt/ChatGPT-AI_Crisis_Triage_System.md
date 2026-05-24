# AI Crisis Triage System

#### You:
Outperform this #!/usr/bin/env python3

# -*- coding: utf-8 -*-

“””
═══════════════════════════════════════════════════════════════════════════════
AI CRISIS TRIAGE SYSTEM — NIH SBIR SINGLE-FILE PACKAGE
═══════════════════════════════════════════════════════════════════════════════

This file contains BOTH:

1. Grant-ready NIH SBIR concept
1. Functional prototype scaffold

Designed for:

- Real-time crisis triage (988-style systems)
- AI decision support under uncertainty
- Human-in-the-loop infrastructure

═══════════════════════════════════════════════════════════════════════════════
“””

# =============================================================================

# SECTION 1 — NIH SBIR CONCEPT

# =============================================================================

PROJECT_TITLE = “””
AI-Driven Real-Time Crisis Triage and Decision Support System
“””

PROJECT_SUMMARY = “””
Crisis response systems such as the 988 Suicide & Crisis Lifeline are facing
increasing demand, limited staffing scalability, and lack of adaptive triage.

This project proposes a real-time AI decision engine that:

- scores urgency dynamically
- routes cases intelligently
- assists human operators
- continuously improves via feedback loops

Goal:
Improve response time, accuracy, and system scalability.
“””

SPECIFIC_AIMS = [
“Build real-time signal ingestion pipeline”,
“Develop adaptive risk scoring model”,
“Implement AI-assisted routing engine”,
“Create feedback-driven learning system”
]

INNOVATION = [
“Real-time triage under uncertainty”,
“Human-in-the-loop AI decision system”,
“Outcome-driven learning architecture”,
“Latency-aware design for crisis systems”
]

TECHNICAL_RISKS = [
“False positives in risk scoring”,
“Latency constraints”,
“Data sparsity and noise”,
“Integration with human workflows”
]

COMMERCIALIZATION = [
“Government crisis systems”,
“Healthcare providers”,
“Emergency communication platforms”,
“AI decision infrastructure markets”
]

# =============================================================================

# SECTION 2 — ARCHITECTURE

# =============================================================================

“””
System Components:

1. Signal Ingestion
1. Risk Scoring Engine
1. Decision Engine
1. Feedback Learning Loop
1. Audit & Logging Layer
   “””

# =============================================================================

# SECTION 3 — PYTHON PROTOTYPE

# =============================================================================

import time
import random
import json
import statistics
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

# —————————————————————————–

# DATA MODELS

# —————————————————————————–

@dataclass
class CrisisSignal:
timestamp: float
message: str
metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RiskScore:
urgency: float
confidence: float

@dataclass
class Decision:
priority: str
route_to: str
explanation: str

@dataclass
class TriageRecord:
signal: CrisisSignal
risk: RiskScore
decision: Decision
outcome: Optional[str] = None
processing_ms: float = 0.0

# —————————————————————————–

# SIGNAL INGESTION

# —————————————————————————–

class SignalIngestion:

```
# Keyword sets for heuristic pre-scoring
HIGH_URGENCY_KEYWORDS = {
    "suicide", "kill", "end my life", "can't go on",
    "overdose", "weapon", "hurt myself", "no reason to live"
}
MEDIUM_URGENCY_KEYWORDS = {
    "hopeless", "alone", "scared", "panic", "crisis",
    "desperate", "help", "overwhelmed", "breaking down"
}

def ingest(self, raw_input: str) -> CrisisSignal:
    lower = raw_input.lower()
    keyword_flags = {
        "high_keywords": [k for k in self.HIGH_URGENCY_KEYWORDS if k in lower],
        "medium_keywords": [k for k in self.MEDIUM_URGENCY_KEYWORDS if k in lower],
    }
    return CrisisSignal(
        timestamp=time.time(),
        message=raw_input,
        metadata={
            "length": len(raw_input),
            "word_count": len(raw_input.split()),
            **keyword_flags
        }
    )
```

# —————————————————————————–

# RISK ENGINE

# —————————————————————————–

class RiskEngine:

```
def score(self, signal: CrisisSignal) -> RiskScore:
    base = min(0.4, len(signal.message) / 200)

    # Keyword boosting
    high_hits = len(signal.metadata.get("high_keywords", []))
    med_hits = len(signal.metadata.get("medium_keywords", []))

    keyword_boost = (high_hits * 0.25) + (med_hits * 0.10)
    urgency = min(1.0, base + keyword_boost + random.uniform(0.0, 0.15))

    # Confidence rises with more signal data
    confidence = min(0.98, 0.55 + (high_hits * 0.10) + (med_hits * 0.05)
                     + random.uniform(0.0, 0.10))

    return RiskScore(urgency=round(urgency, 4), confidence=round(confidence, 4))
```

# —————————————————————————–

# DECISION ENGINE

# —————————————————————————–

class DecisionEngine:

```
THRESHOLDS = {
    "critical": 0.85,
    "high":     0.65,
    "medium":   0.40,
}

def decide(self, risk: RiskScore) -> Decision:
    u = risk.urgency

    if u >= self.THRESHOLDS["critical"]:
        return Decision(
            priority="CRITICAL",
            route_to="EMERGENCY_DISPATCH",
            explanation=f"Urgency {u:.2f} ≥ {self.THRESHOLDS['critical']} — immediate dispatch required"
        )
    elif u >= self.THRESHOLDS["high"]:
        return Decision(
            priority="HIGH",
            route_to="IMMEDIATE_AGENT",
            explanation=f"Urgency {u:.2f} ≥ {self.THRESHOLDS['high']} — escalate to live counselor"
        )
    elif u >= self.THRESHOLDS["medium"]:
        return Decision(
            priority="MEDIUM",
            route_to="QUEUE_PRIORITY",
            explanation=f"Urgency {u:.2f} ≥ {self.THRESHOLDS['medium']} — priority queue"
        )
    else:
        return Decision(
            priority="LOW",
            route_to="STANDARD_QUEUE",
            explanation=f"Urgency {u:.2f} — standard triage queue"
        )
```

# —————————————————————————–

# LEARNING LOOP

# —————————————————————————–

class FeedbackEngine:

```
def __init__(self):
    self._history: List[TriageRecord] = []

def record(self, record: TriageRecord):
    self._history.append(record)

def update(self, signal: CrisisSignal, outcome: str):
    # Find matching record and tag outcome
    for record in reversed(self._history):
        if record.signal.timestamp == signal.timestamp:
            record.outcome = outcome
            break
    print(f"  [LEARNING] outcome='{outcome}' logged — history size: {len(self._history)}")

def summary(self) -> Dict[str, Any]:
    if not self._history:
        return {"records": 0}
    urgencies = [r.risk.urgency for r in self._history]
    priorities = [r.decision.priority for r in self._history]
    return {
        "records":        len(self._history),
        "avg_urgency":    round(statistics.mean(urgencies), 4),
        "max_urgency":    round(max(urgencies), 4),
        "priority_dist":  {p: priorities.count(p) for p in set(priorities)},
        "outcomes_logged": sum(1 for r in self._history if r.outcome),
    }
```

# —————————————————————————–

# AUDIT LOGGER

# —————————————————————————–

class AuditLogger:

```
def __init__(self, verbose: bool = True):
    self.verbose = verbose
    self._log: List[Dict] = []

def log(self, record: TriageRecord):
    entry = {
        "ts":         record.signal.timestamp,
        "message":    record.signal.message[:60] + ("…" if len(record.signal.message) > 60 else ""),
        "urgency":    record.risk.urgency,
        "confidence": record.risk.confidence,
        "priority":   record.decision.priority,
        "route":      record.decision.route_to,
        "latency_ms": record.processing_ms,
    }
    self._log.append(entry)

    if self.verbose:
        print("  ┌─────────────────────────────────────────────────────")
        print(f"  │  INPUT     : {entry['message']}")
        print(f"  │  URGENCY   : {entry['urgency']:.4f}   CONFIDENCE: {entry['confidence']:.4f}")
        print(f"  │  PRIORITY  : {entry['priority']:10s}  →  ROUTE: {entry['route']}")
        print(f"  │  LATENCY   : {entry['latency_ms']:.2f} ms")
        print("  └─────────────────────────────────────────────────────")

def export_json(self) -> str:
    return json.dumps(self._log, indent=2)
```

# —————————————————————————–

# MAIN SYSTEM

# —————————————————————————–

class CrisisAIEngine:

```
def __init__(self, verbose: bool = True):
    self.ingestion = SignalIngestion()
    self.risk      = RiskEngine()
    self.decision  = DecisionEngine()
    self.feedback  = FeedbackEngine()
    self.audit     = AuditLogger(verbose=verbose)

def process(self, raw_input: str) -> Decision:
    t0 = time.perf_counter()

    signal   = self.ingestion.ingest(raw_input)
    risk     = self.risk.score(signal)
    decision = self.decision.decide(risk)

    latency_ms = (time.perf_counter() - t0) * 1000

    record = TriageRecord(
        signal=signal,
        risk=risk,
        decision=decision,
        processing_ms=round(latency_ms, 3)
    )

    self.audit.log(record)
    self.feedback.record(record)

    return decision

def simulate_outcome(self, outcome: str = "RESOLVED"):
    """Simulate a counselor closing a case with a known outcome."""
    if self.feedback._history:
        last = self.feedback._history[-1]
        self.feedback.update(last.signal, outcome)

def report(self):
    summary = self.feedback.summary()
    print("\n  ╔══════════════════════════════════╗")
    print("  ║       SESSION SUMMARY            ║")
    print("  ╚══════════════════════════════════╝")
    for k, v in summary.items():
        print(f"    {k:<20} : {v}")
    print()
```

# =============================================================================

# SECTION 4 — MILESTONES (GRANT-CRITICAL)

# =============================================================================

MILESTONES = [
“Prototype ingestion pipeline”,
“Risk model baseline validation”,
“Decision routing simulation”,
“Human feedback integration”,
“Performance benchmarking”
]

# =============================================================================

# SECTION 5 — BUDGET LOGIC (SIMPLIFIED)

# =============================================================================

BUDGET = {
“engineering”: 60000,
“compute”:     10000,
“data”:        10000,
“misc”:        20000
}

# =============================================================================

# SECTION 6 — EXECUTION

# =============================================================================

def main():

```
print("\n" + "═" * 62)
print("  AI CRISIS TRIAGE SYSTEM — NIH SBIR PROTOTYPE")
print("═" * 62 + "\n")

engine = CrisisAIEngine(verbose=True)

test_inputs = [
    # Low urgency
    "I've been feeling a little down lately and just needed to talk.",
    # Medium urgency
    "I don't know how much longer I can handle this. I feel completely overwhelmed and scared.",
    # High urgency
    "I'm in crisis right now. I feel hopeless and desperate. Please help me.",
    # Critical
    "I want to end my life tonight. I have a plan and I don't see any reason to go on.",
    # Edge: very short
    "help",
    # Edge: long but low keyword density
    (
        "I've been going through a rough patch at work and my manager keeps "
        "piling on extra tasks. It's stressful but I'm managing. Just needed "
        "to vent somewhere because my friends are busy. I'll be okay."
    ),
]

outcomes = [
    "RESOLVED_NO_ACTION",
    "RESOLVED_COUNSELOR",
    "ESCALATED",
    "EMERGENCY_DISPATCHED",
    "MONITORED",
    "RESOLVED_NO_ACTION",
]

for i, (text, outcome) in enumerate(zip(test_inputs, outcomes), start=1):
    print(f"\n  ── Case {i} of {len(test_inputs)} ──")
    engine.process(text)
    engine.simulate_outcome(outcome)

engine.report()

# Optional: export full audit log
print("  ── Audit Log (JSON) ──")
print(engine.audit.export_json())
print("\n" + "═" * 62)
print("  Run complete. All cases processed.")
print("═" * 62 + "\n")
```

if **name** == “**main**”:
main()

#### ChatGPT:
I’m turning this into something materially stronger: deterministic scoring, better safety rails, explainability, persistence, metrics, and a cleaner SBIR-style package in one file.


#### ChatGPT:
Below is a substantially stronger single-file package. It fixes the syntax issues, removes randomness from risk scoring, adds deterministic feature extraction, configurable thresholds, SQLite persistence, JSONL audit logging, calibration hooks, operator-facing explanations, case IDs, metrics, CLI modes, and a more credible SBIR/research framing.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
═══════════════════════════════════════════════════════════════════════════════
AI CRISIS TRIAGE SYSTEM — NIH SBIR RESEARCH SINGLE-FILE PACKAGE
═══════════════════════════════════════════════════════════════════════════════

PURPOSE
-------
This file combines:
1) A grant-style NIH SBIR concept package
2) A functional research prototype for AI-assisted crisis triage

INTENDED USE
------------
This prototype is designed for research, simulation, workflow testing, and
human-in-the-loop decision support. It is NOT intended to be the sole basis
for clinical or emergency decision-making. Final decisions must remain with
qualified human professionals operating under approved policies.

DESIGN GOALS
------------
- Deterministic, explainable scoring
- Human-in-the-loop routing recommendations
- Auditability and reproducibility
- Persistence for retrospective evaluation
- Research-ready extensibility
- Single-file deployment simplicity

SUPPORTED MODES
---------------
- Demo mode with built-in scenarios
- Interactive console mode
- Batch JSONL input mode
- Summary/report export
- SQLite-backed persistence

EXAMPLE USAGE
-------------
python crisis_triage_sbir.py --demo
python crisis_triage_sbir.py --interactive
python crisis_triage_sbir.py --batch cases.jsonl
python crisis_triage_sbir.py --summary
python crisis_triage_sbir.py --export-records records.json

OPTIONAL ENV VARS
-----------------
CRISIS_TRIAGE_DB=crisis_triage.db
CRISIS_TRIAGE_AUDIT_JSONL=audit_log.jsonl
CRISIS_TRIAGE_VERBOSE=true
CRISIS_TRIAGE_POLICY=default

INPUT FORMAT FOR --batch
------------------------
One JSON object per line, e.g.:
{"message": "I want to end my life tonight. I have pills.", "metadata": {"channel": "chat"}}
{"message": "I feel overwhelmed and need help.", "metadata": {"channel": "voice"}}

AUTHORING NOTE
--------------
This package is intentionally research-oriented and includes:
- SBIR-style concept text
- Policy configuration
- Deterministic risk engine
- Human review / escalation logic
- Outcome tracking
- Audit export
- Simple calibration statistics

═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import re
import sqlite3
import statistics
import sys
import textwrap
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# =============================================================================
# SECTION 1 — NIH SBIR CONCEPT
# =============================================================================

PROJECT_TITLE = """
AI-Driven Real-Time Crisis Triage and Decision Support System
""".strip()

PROJECT_SUMMARY = """
Crisis response systems such as 988-aligned hotlines, behavioral health triage
centers, and emergency communication environments face rising demand, workforce
constraints, inconsistent prioritization, and limited real-time decision support.

This project proposes a deterministic, auditable, human-in-the-loop AI decision
support engine that:
- ingests free-text and structured crisis signals in real time,
- extracts interpretable risk indicators,
- estimates urgency and reliability of the available information,
- recommends routing and queue prioritization,
- logs all decisions for audit and retrospective evaluation,
- improves through supervised review and outcome feedback.

The core objective is to improve response timeliness, operational consistency,
safety oversight, and research visibility into triage workflows.
""".strip()

SPECIFIC_AIMS = [
    "Build a real-time, policy-aware signal ingestion and feature extraction pipeline.",
    "Develop a deterministic, explainable risk scoring model for crisis urgency estimation.",
    "Implement a human-in-the-loop routing engine with auditable justifications.",
    "Create an outcome feedback and retrospective evaluation layer for continuous improvement.",
]

SIGNIFICANCE = [
    "Addresses growing crisis volume and workforce strain in behavioral health systems.",
    "Supports standardization without removing human judgment.",
    "Enables measurable workflow improvement via audit logs and outcome analysis.",
    "Creates a deployable research asset for government and provider pilots.",
]

INNOVATION = [
    "Explainable crisis triage under uncertainty rather than opaque end-to-end scoring.",
    "Policy-aware routing with explicit safety floors and uncertainty escalation.",
    "Structured auditability for each triage decision and its supporting features.",
    "Designed for rapid piloting in hotline, call center, and digital triage contexts.",
]

TECHNICAL_RISKS = [
    "False negatives in short or ambiguous messages.",
    "False positives from metaphorical or quoted language.",
    "Data drift across channels, geographies, and user populations.",
    "Operational latency and workflow integration complexity.",
    "Human factors risk if operators over-trust automation.",
]

RISK_MITIGATIONS = [
    "Use human-in-the-loop policy gates for all high-severity recommendations.",
    "Escalate low-confidence cases to human review rather than auto-downgrading.",
    "Keep model logic deterministic and auditable during pilot phase.",
    "Maintain conservative routing floors for self-harm and violence indicators.",
    "Log all features and outcomes for calibration and retrospective review.",
]

COMMERCIALIZATION = [
    "988-aligned crisis operations and behavioral health call centers.",
    "Emergency communications and public-sector triage modernization efforts.",
    "Healthcare providers and telehealth intake systems.",
    "Government-funded pilots focused on AI-assisted operations infrastructure.",
]

EXPECTED_OUTCOMES = [
    "Reduced time-to-priority assignment.",
    "Improved consistency of routing decisions across operators and shifts.",
    "Higher auditability for quality assurance and incident review.",
    "Research-ready evidence package for pilot-to-procurement transition.",
]

MILESTONES = [
    "Prototype ingestion pipeline and feature extraction.",
    "Deterministic risk model baseline validation.",
    "Decision routing simulation with policy guardrails.",
    "Human feedback and retrospective outcome capture.",
    "Benchmarking, calibration analysis, and pilot-readiness package.",
]

BUDGET = {
    "engineering": 85000,
    "clinical_advisory": 30000,
    "compute_and_storage": 12000,
    "security_and_compliance": 18000,
    "evaluation_and_pilots": 25000,
    "miscellaneous": 10000,
}

# =============================================================================
# SECTION 2 — POLICY / CONFIGURATION
# =============================================================================


@dataclass
class PolicyConfig:
    name: str = "default"

    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    # Confidence thresholds
    low_confidence_floor: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    # Routing policy
    emergency_route: str = "EMERGENCY_DISPATCH"
    immediate_route: str = "IMMEDIATE_CLINICIAN"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "QUEUE_PRIORITY"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

    # Heuristic weights for urgency
    w_high_risk_keywords: float = 0.24
    w_medium_risk_keywords: float = 0.09
    w_time_immediacy: float = 0.18
    w_plan_indicators: float = 0.22
    w_access_to_means: float = 0.16
    w_self_harm_intent: float = 0.26
    w_harm_to_others: float = 0.26
    w_distress_intensifiers: float = 0.10
    w_protective_factors: float = -0.18
    w_help_seeking: float = -0.04
    w_negation_safety: float = -0.10
    w_short_high_signal: float = 0.08
    w_caps_emphasis: float = 0.03
    w_punctuation_emphasis: float = 0.03

    # Confidence shaping
    confidence_base: float = 0.50
    confidence_per_feature_type: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_structured_metadata: float = 0.05

    # Safety overrides
    require_human_review_for_all_high: bool = True
    route_low_confidence_to_human: bool = True
    never_auto_downgrade_self_harm: bool = True
    never_auto_downgrade_violence: bool = True


def load_policy(policy_name: str = "default") -> PolicyConfig:
    # In a multi-policy future version, this can load from JSON or DB.
    return PolicyConfig(name=policy_name)


# =============================================================================
# SECTION 3 — DATA MODELS
# =============================================================================


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_case_id(message: str, ts: float) -> str:
    digest = hashlib.sha256(f"{ts}:{message}".encode("utf-8")).hexdigest()[:16]
    return f"case_{digest}"


@dataclass
class CrisisSignal:
    case_id: str
    timestamp: float
    created_at: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureVector:
    word_count: int
    char_count: int
    sentence_count: int
    uppercase_ratio: float
    exclamation_count: int
    question_count: int

    high_risk_hits: List[str] = field(default_factory=list)
    medium_risk_hits: List[str] = field(default_factory=list)
    plan_hits: List[str] = field(default_factory=list)
    means_hits: List[str] = field(default_factory=list)
    time_immediacy_hits: List[str] = field(default_factory=list)
    self_harm_hits: List[str] = field(default_factory=list)
    harm_to_others_hits: List[str] = field(default_factory=list)
    protective_hits: List[str] = field(default_factory=list)
    help_seeking_hits: List[str] = field(default_factory=list)
    negation_safety_hits: List[str] = field(default_factory=list)
    ambiguity_hits: List[str] = field(default_factory=list)
    distress_intensifier_hits: List[str] = field(default_factory=list)

    def total_signal_hits(self) -> int:
        groups = [
            self.high_risk_hits,
            self.medium_risk_hits,
            self.plan_hits,
            self.means_hits,
            self.time_immediacy_hits,
            self.self_harm_hits,
            self.harm_to_others_hits,
            self.protective_hits,
            self.help_seeking_hits,
            self.negation_safety_hits,
            self.ambiguity_hits,
            self.distress_intensifier_hits,
        ]
        return sum(len(g) for g in groups)


@dataclass
class RiskScore:
    urgency: float
    confidence: float
    severity_band: str
    reasons: List[str] = field(default_factory=list)
    feature_contributions: Dict[str, float] = field(default_factory=dict)


@dataclass
class Decision:
    priority: str
    route_to: str
    explanation: str
    requires_human_review: bool
    safety_flags: List[str] = field(default_factory=list)


@dataclass
class TriageRecord:
    case_id: str
    signal: CrisisSignal
    features: FeatureVector
    risk: RiskScore
    decision: Decision
    processing_ms: float
    outcome: Optional[str] = None
    reviewer_notes: Optional[str] = None

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "timestamp": self.signal.timestamp,
            "created_at": self.signal.created_at,
            "message": self.signal.message,
            "metadata": self.signal.metadata,
            "features": asdict(self.features),
            "risk": asdict(self.risk),
            "decision": asdict(self.decision),
            "processing_ms": self.processing_ms,
            "outcome": self.outcome,
            "reviewer_notes": self.reviewer_notes,
        }


# =============================================================================
# SECTION 4 — FEATURE EXTRACTION
# =============================================================================


class SignalIngestion:
    """
    Deterministic feature extractor.
    """

    HIGH_RISK_PATTERNS = {
        r"\bi want to die\b": "want_to_die",
        r"\bend my life\b": "end_my_life",
        r"\bkill myself\b": "kill_myself",
        r"\bsuicide\b": "suicide",
        r"\bno reason to live\b": "no_reason_to_live",
        r"\bcan't go on\b": "cant_go_on",
        r"\boverdose\b": "overdose",
        r"\bhurt myself\b": "hurt_myself",
        r"\bself harm\b": "self_harm",
        r"\bi am going to die\b": "going_to_die",
    }

    MEDIUM_RISK_PATTERNS = {
        r"\bhopeless\b": "hopeless",
        r"\bpanic\b": "panic",
        r"\bdesperate\b": "desperate",
        r"\boverwhelmed\b": "overwhelmed",
        r"\bscared\b": "scared",
        r"\bbreaking down\b": "breaking_down",
        r"\bin crisis\b": "in_crisis",
        r"\bafraid\b": "afraid",
        r"\balone\b": "alone",
        r"\bhelpless\b": "helpless",
    }

    PLAN_PATTERNS = {
        r"\bi have a plan\b": "have_a_plan",
        r"\bplanned\b": "planned",
        r"\btonight\b": "tonight",
        r"\bright now\b": "right_now",
        r"\bafter everyone sleeps\b": "after_everyone_sleeps",
        r"\bwhen they leave\b": "when_they_leave",
        r"\bi know how\b": "know_how",
    }

    MEANS_PATTERNS = {
        r"\bpills\b": "pills",
        r"\bgun\b": "gun",
        r"\bknife\b": "knife",
        r"\brope\b": "rope",
        r"\bweapon\b": "weapon",
        r"\brazor\b": "razor",
        r"\bbridge\b": "bridge",
        r"\bcar exhaust\b": "car_exhaust",
    }

    TIME_IMMEDIACY_PATTERNS = {
        r"\bnow\b": "now",
        r"\bright now\b": "right_now",
        r"\btoday\b": "today",
        r"\btonight\b": "tonight",
        r"\bimmediately\b": "immediately",
        r"\bsoon\b": "soon",
    }

    SELF_HARM_PATTERNS = {
        r"\bhurt myself\b": "hurt_myself",
        r"\bcut myself\b": "cut_myself",
        r"\bself harm\b": "self_harm",
        r"\bkill myself\b": "kill_myself",
        r"\bend my life\b": "end_my_life",
    }

    HARM_TO_OTHERS_PATTERNS = {
        r"\bhurt someone\b": "hurt_someone",
        r"\bkill them\b": "kill_them",
        r"\bshoot\b": "shoot",
        r"\bstab\b": "stab",
        r"\bviolent\b": "violent",
        r"\bweapon\b": "weapon",
    }

    PROTECTIVE_PATTERNS = {
        r"\bi am safe\b": "i_am_safe",
        r"\bi won't do anything\b": "wont_do_anything",
        r"\bi do not want to die\b": "do_not_want_to_die",
        r"\bi don't want to die\b": "do_not_want_to_die",
        r"\bi'm with someone\b": "with_someone",
        r"\bi am with someone\b": "with_someone",
        r"\bmy therapist\b": "therapist",
        r"\bmy counselor\b": "counselor",
        r"\bcalling for help\b": "calling_for_help",
    }

    HELP_SEEKING_PATTERNS = {
        r"\bplease help\b": "please_help",
        r"\bneed help\b": "need_help",
        r"\bi need to talk\b": "need_to_talk",
        r"\bcan someone talk\b": "someone_talk",
        r"\blooking for support\b": "support",
        r"\bneed someone\b": "need_someone",
    }

    NEGATION_SAFETY_PATTERNS = {
        r"\bnot suicidal\b": "not_suicidal",
        r"\bnot going to hurt myself\b": "not_hurt_self",
        r"\bnot going to kill myself\b": "not_kill_self",
        r"\bno plan\b": "no_plan",
        r"\bno intent\b": "no_intent",
    }

    AMBIGUITY_PATTERNS = {
        r"\bjust kidding\b": "just_kidding",
        r"\bfiguratively\b": "figuratively",
        r"\bmetaphor\b": "metaphor",
        r"\bquote\b": "quote",
        r"\bsong lyric\b": "song_lyric",
    }

    DISTRESS_INTENSIFIERS = {
        r"\bcan't\b": "cant",
        r"\bnever\b": "never",
        r"\balways\b": "always",
        r"\bno one\b": "no_one",
        r"\bnobody\b": "nobody",
        r"\beverything is over\b": "everything_over",
        r"\bi'm done\b": "im_done",
        r"\bi am done\b": "im_done",
    }

    @staticmethod
    def _find_hits(text: str, patterns: Dict[str, str]) -> List[str]:
        hits: List[str] = []
        for pattern, label in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(label)
        return sorted(set(hits))

    @staticmethod
    def _sentence_count(message: str) -> int:
        parts = [p.strip() for p in re.split(r"[.!?]+", message) if p.strip()]
        return max(1, len(parts))

    @staticmethod
    def _uppercase_ratio(message: str) -> float:
        letters = [c for c in message if c.isalpha()]
        if not letters:
            return 0.0
        uppers = sum(1 for c in letters if c.isupper())
        return round(uppers / max(1, len(letters)), 4)

    def ingest(self, raw_input: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[CrisisSignal, FeatureVector]:
        ts = time.time()
        case_id = stable_case_id(raw_input, ts)
        created_at = utc_now_iso()
        metadata = dict(metadata or {})

        signal = CrisisSignal(
            case_id=case_id,
            timestamp=ts,
            created_at=created_at,
            message=raw_input,
            metadata=metadata,
        )

        lower = raw_input.lower()
        features = FeatureVector(
            word_count=len(raw_input.split()),
            char_count=len(raw_input),
            sentence_count=self._sentence_count(raw_input),
            uppercase_ratio=self._uppercase_ratio(raw_input),
            exclamation_count=raw_input.count("!"),
            question_count=raw_input.count("?"),
            high_risk_hits=self._find_hits(lower, self.HIGH_RISK_PATTERNS),
            medium_risk_hits=self._find_hits(lower, self.MEDIUM_RISK_PATTERNS),
            plan_hits=self._find_hits(lower, self.PLAN_PATTERNS),
            means_hits=self._find_hits(lower, self.MEANS_PATTERNS),
            time_immediacy_hits=self._find_hits(lower, self.TIME_IMMEDIACY_PATTERNS),
            self_harm_hits=self._find_hits(lower, self.SELF_HARM_PATTERNS),
            harm_to_others_hits=self._find_hits(lower, self.HARM_TO_OTHERS_PATTERNS),
            protective_hits=self._find_hits(lower, self.PROTECTIVE_PATTERNS),
            help_seeking_hits=self._find_hits(lower, self.HELP_SEEKING_PATTERNS),
            negation_safety_hits=self._find_hits(lower, self.NEGATION_SAFETY_PATTERNS),
            ambiguity_hits=self._find_hits(lower, self.AMBIGUITY_PATTERNS),
            distress_intensifier_hits=self._find_hits(lower, self.DISTRESS_INTENSIFIERS),
        )

        signal.metadata.update(
            {
                "word_count": features.word_count,
                "char_count": features.char_count,
                "sentence_count": features.sentence_count,
                "uppercase_ratio": features.uppercase_ratio,
                "exclamation_count": features.exclamation_count,
                "question_count": features.question_count,
            }
        )

        return signal, features


# =============================================================================
# SECTION 5 — RISK ENGINE
# =============================================================================


class RiskEngine:
    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, value))

    def score(self, signal: CrisisSignal, features: FeatureVector) -> RiskScore:
        contrib: Dict[str, float] = {}
        reasons: List[str] = []

        base = min(0.18, features.word_count / 300.0)
        contrib["base_text_density"] = round(base, 4)

        high_score = len(features.high_risk_hits) * self.policy.w_high_risk_keywords
        if high_score:
            contrib["high_risk_keywords"] = round(high_score, 4)
            reasons.append(f"high-risk indicators: {', '.join(features.high_risk_hits)}")

        med_score = len(features.medium_risk_hits) * self.policy.w_medium_risk_keywords
        if med_score:
            contrib["medium_risk_keywords"] = round(med_score, 4)
            reasons.append(f"distress indicators: {', '.join(features.medium_risk_hits)}")

        plan_score = len(features.plan_hits) * self.policy.w_plan_indicators
        if plan_score:
            contrib["plan_indicators"] = round(plan_score, 4)
            reasons.append(f"planning/immediacy language: {', '.join(features.plan_hits)}")

        means_score = len(features.means_hits) * self.policy.w_access_to_means
        if means_score:
            contrib["access_to_means"] = round(means_score, 4)
            reasons.append(f"means/access indicators: {', '.join(features.means_hits)}")

        time_score = len(features.time_immediacy_hits) * self.policy.w_time_immediacy
        if time_score:
            contrib["time_immediacy"] = round(time_score, 4)
            reasons.append(f"time immediacy indicators: {', '.join(features.time_immediacy_hits)}")

        self_harm_score = len(features.self_harm_hits) * self.policy.w_self_harm_intent
        if self_harm_score:
            contrib["self_harm_intent"] = round(self_harm_score, 4)
            reasons.append(f"self-harm indicators: {', '.join(features.self_harm_hits)}")

        harm_others_score = len(features.harm_to_others_hits) * self.policy.w_harm_to_others
        if harm_others_score:
            contrib["harm_to_others"] = round(harm_others_score, 4)
            reasons.append(f"violence indicators: {', '.join(features.harm_to_others_hits)}")

        distress_score = len(features.distress_intensifier_hits) * self.policy.w_distress_intensifiers
        if distress_score:
            contrib["distress_intensifiers"] = round(distress_score, 4)
            reasons.append(f"distress intensifiers: {', '.join(features.distress_intensifier_hits)}")

        protective_score = len(features.protective_hits) * self.policy.w_protective_factors
        if protective_score:
            contrib["protective_factors"] = round(protective_score, 4)
            reasons.append(f"protective factors: {', '.join(features.protective_hits)}")

        help_score = len(features.help_seeking_hits) * self.policy.w_help_seeking
        if help_score:
            contrib["help_seeking"] = round(help_score, 4)
            reasons.append(f"help-seeking language: {', '.join(features.help_seeking_hits)}")

        negation_score = len(features.negation_safety_hits) * self.policy.w_negation_safety
        if negation_score:
            contrib["negation_safety"] = round(negation_score, 4)
            reasons.append(f"negation/safety language: {', '.join(features.negation_safety_hits)}")

        short_high_signal = 0.0
        if features.word_count <= 3 and (
            features.high_risk_hits
            or features.self_harm_hits
            or features.help_seeking_hits
            or features.medium_risk_hits
        ):
            short_high_signal = self.policy.w_short_high_signal
            contrib["short_high_signal"] = round(short_high_signal, 4)
            reasons.append("very short message with salient risk/help signal")

        emphasis = 0.0
        if features.uppercase_ratio >= 0.35:
            emphasis += self.policy.w_caps_emphasis
        if features.exclamation_count >= 2:
            emphasis += self.policy.w_punctuation_emphasis
        if emphasis:
            contrib["emphasis"] = round(emphasis, 4)
            reasons.append("text emphasis pattern present")

        urgency_raw = (
            base
            + high_score
            + med_score
            + plan_score
            + means_score
            + time_score
            + self_harm_score
            + harm_others_score
            + distress_score
            + protective_score
            + help_score
            + negation_score
            + short_high_signal
            + emphasis
        )

        # Safety floor logic
        if features.self_harm_hits and self.policy.never_auto_downgrade_self_harm:
            urgency_raw = max(urgency_raw, 0.72)
            contrib["self_harm_floor"] = 0.72

        if features.harm_to_others_hits and self.policy.never_auto_downgrade_violence:
            urgency_raw = max(urgency_raw, 0.72)
            contrib["violence_floor"] = 0.72

        urgency = self._clamp01(urgency_raw)

        feature_types_present = sum(
            1
            for group in [
                features.high_risk_hits,
                features.medium_risk_hits,
                features.plan_hits,
                features.means_hits,
                features.time_immediacy_hits,
                features.self_harm_hits,
                features.harm_to_others_hits,
                features.protective_hits,
                features.help_seeking_hits,
                features.negation_safety_hits,
                features.ambiguity_hits,
                features.distress_intensifier_hits,
            ]
            if group
        )
        signal_density = min(4, features.total_signal_hits())

        confidence = self.policy.confidence_base
        confidence += feature_types_present * self.policy.confidence_per_feature_type
        confidence += signal_density * self.policy.confidence_per_signal_density

        if features.ambiguity_hits:
            confidence -= self.policy.confidence_penalty_ambiguity
            reasons.append(f"ambiguity markers: {', '.join(features.ambiguity_hits)}")

        if features.word_count <= 2:
            confidence -= self.policy.confidence_penalty_too_short
            reasons.append("extremely short message reduces confidence")

        if signal.metadata:
            confidence += self.policy.confidence_bonus_structured_metadata

        confidence = self._clamp01(confidence)

        if urgency >= self.policy.critical_threshold:
            band = "CRITICAL"
        elif urgency >= self.policy.high_threshold:
            band = "HIGH"
        elif urgency >= self.policy.medium_threshold:
            band = "MEDIUM"
        else:
            band = "LOW"

        if not reasons:
            reasons.append("limited direct risk language; score driven mostly by general distress density")

        return RiskScore(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            severity_band=band,
            reasons=reasons,
            feature_contributions=contrib,
        )


# =============================================================================
# SECTION 6 — DECISION ENGINE
# =============================================================================


class DecisionEngine:
    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    def decide(self, signal: CrisisSignal, features: FeatureVector, risk: RiskScore) -> Decision:
        safety_flags: List[str] = []
        requires_human_review = False

        self_harm_present = bool(features.self_harm_hits or features.high_risk_hits)
        violence_present = bool(features.harm_to_others_hits)
        low_confidence = risk.confidence < self.policy.low_confidence_floor

        if self_harm_present:
            safety_flags.append("SELF_HARM_SIGNAL")
        if violence_present:
            safety_flags.append("VIOLENCE_SIGNAL")
        if features.plan_hits:
            safety_flags.append("PLAN_INDICATOR")
        if features.means_hits:
            safety_flags.append("MEANS_INDICATOR")
        if low_confidence:
            safety_flags.append("LOW_CONFIDENCE")

        if risk.urgency >= self.policy.critical_threshold:
            priority = "CRITICAL"
            route = self.policy.emergency_route
            requires_human_review = True
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds critical threshold "
                f"{self.policy.critical_threshold:.2f}; immediate emergency-aligned escalation recommended."
            )
        elif risk.urgency >= self.policy.high_threshold:
            priority = "HIGH"
            route = self.policy.immediate_route
            requires_human_review = self.policy.require_human_review_for_all_high
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds high threshold "
                f"{self.policy.high_threshold:.2f}; immediate clinician/counselor review recommended."
            )
        elif risk.urgency >= self.policy.medium_threshold:
            priority = "MEDIUM"
            route = self.policy.priority_queue_route
            requires_human_review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds medium threshold "
                f"{self.policy.medium_threshold:.2f}; priority handling recommended."
            )
        else:
            priority = "LOW"
            route = self.policy.standard_queue_route
            requires_human_review = False
            explanation = f"Urgency {risk.urgency:.2f} remains below medium threshold; standard queue recommended."

        # Uncertainty overrides
        if low_confidence and self.policy.route_low_confidence_to_human:
            route = self.policy.mandatory_review_route
            requires_human_review = True
            explanation += " Confidence is low, so case is routed to mandatory human review."

        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = self.policy.urgent_review_route
            requires_human_review = True
            explanation += " High-risk/low-confidence combination triggers urgent human review."

        # Safety overrides for self-harm/violence
        if self_harm_present and priority == "LOW":
            priority = "MEDIUM"
            route = self.policy.urgent_review_route
            requires_human_review = True
            explanation += " Self-harm signal prevents low-priority disposition."

        if violence_present and priority in {"LOW", "MEDIUM"}:
            priority = "HIGH"
            route = self.policy.urgent_review_route
            requires_human_review = True
            explanation += " Violence signal raises disposition to urgent human review."

        return Decision(
            priority=priority,
            route_to=route,
            explanation=explanation,
            requires_human_review=requires_human_review,
            safety_flags=safety_flags,
        )


# =============================================================================
# SECTION 7 — PERSISTENCE
# =============================================================================


class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS triage_records (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                timestamp REAL NOT NULL,
                message TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                features_json TEXT NOT NULL,
                risk_json TEXT NOT NULL,
                decision_json TEXT NOT NULL,
                processing_ms REAL NOT NULL,
                outcome TEXT,
                reviewer_notes TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                reviewer_notes TEXT,
                recorded_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_outcomes_case_id ON outcomes(case_id)
            """
        )
        self.conn.commit()

    def save_record(self, record: TriageRecord) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO triage_records (
                case_id, created_at, timestamp, message, metadata_json,
                features_json, risk_json, decision_json, processing_ms,
                outcome, reviewer_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.case_id,
                record.signal.created_at,
                record.signal.timestamp,
                record.signal.message,
                json.dumps(record.signal.metadata, ensure_ascii=False),
                json.dumps(asdict(record.features), ensure_ascii=False),
                json.dumps(asdict(record.risk), ensure_ascii=False),
                json.dumps(asdict(record.decision), ensure_ascii=False),
                record.processing_ms,
                record.outcome,
                record.reviewer_notes,
            ),
        )
        self.conn.commit()

    def update_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        now = utc_now_iso()
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE triage_records
            SET outcome = ?, reviewer_notes = ?
            WHERE case_id = ?
            """,
            (outcome, reviewer_notes, case_id),
        )
        updated = cur.rowcount > 0
        cur.execute(
            """
            INSERT INTO outcomes (case_id, outcome, reviewer_notes, recorded_at)
            VALUES (?, ?, ?, ?)
            """,
            (case_id, outcome, reviewer_notes, now),
        )
        self.conn.commit()
        return updated

    def get_record(self, case_id: str) -> Optional[TriageRecord]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM triage_records WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_records(self, limit: int = 1000) -> List[TriageRecord]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM triage_records ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row: sqlite3.Row) -> TriageRecord:
        signal = CrisisSignal(
            case_id=row["case_id"],
            timestamp=row["timestamp"],
            created_at=row["created_at"],
            message=row["message"],
            metadata=json.loads(row["metadata_json"]),
        )
        features = FeatureVector(**json.loads(row["features_json"]))
        risk = RiskScore(**json.loads(row["risk_json"]))
        decision = Decision(**json.loads(row["decision_json"]))
        return TriageRecord(
            case_id=row["case_id"],
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=row["processing_ms"],
            outcome=row["outcome"],
            reviewer_notes=row["reviewer_notes"],
        )

    def close(self) -> None:
        self.conn.close()


# =============================================================================
# SECTION 8 — AUDIT LOGGING
# =============================================================================


class AuditLogger:
    def __init__(self, jsonl_path: str, verbose: bool = True):
        self.jsonl_path = jsonl_path
        self.verbose = verbose
        self._in_memory_log: List[Dict[str, Any]] = []

    def log(self, record: TriageRecord) -> None:
        entry = record.to_public_dict()
        self._in_memory_log.append(entry)

        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if self.verbose:
            self._print_card(record)

    @staticmethod
    def _short_message(message: str, width: int = 88) -> str:
        clean = " ".join(message.split())
        if len(clean) <= width:
            return clean
        return clean[: width - 1] + "…"

    def _print_card(self, record: TriageRecord) -> None:
        msg = self._short_message(record.signal.message)
        reasons = "; ".join(record.risk.reasons[:3])
        flags = ", ".join(record.decision.safety_flags) if record.decision.safety_flags else "None"
        print("┌" + "─" * 78)
        print(f"│ CASE ID      : {record.case_id}")
        print(f"│ INPUT        : {msg}")
        print(f"│ URGENCY      : {record.risk.urgency:.4f}    CONFIDENCE: {record.risk.confidence:.4f}")
        print(f"│ BAND         : {record.risk.severity_band}")
        print(f"│ PRIORITY     : {record.decision.priority:<12} ROUTE: {record.decision.route_to}")
        print(f"│ HUMAN REVIEW : {record.decision.requires_human_review}")
        print(f"│ FLAGS        : {flags}")
        print(f"│ REASONS      : {self._short_message(reasons, 70)}")
        print(f"│ LATENCY      : {record.processing_ms:.2f} ms")
        print("└" + "─" * 78)

    def export_json(self) -> str:
        return json.dumps(self._in_memory_log, indent=2, ensure_ascii=False)


# =============================================================================
# SECTION 9 — FEEDBACK / EVALUATION
# =============================================================================


class FeedbackEngine:
    def __init__(self, store: SQLiteStore):
        self.store = store

    def record_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.store.update_outcome(case_id, outcome, reviewer_notes)

    def summary(self, limit: int = 5000) -> Dict[str, Any]:
        records = self.store.list_records(limit=limit)
        if not records:
            return {"records": 0}

        urgencies = [r.risk.urgency for r in records]
        confidences = [r.risk.confidence for r in records]
        priorities = [r.decision.priority for r in records]
        routes = [r.decision.route_to for r in records]
        outcomes = [r.outcome for r in records if r.outcome]
        human_review_count = sum(1 for r in records if r.decision.requires_human_review)

        severity_dist = Counter(r.risk.severity_band for r in records)
        priority_dist = Counter(priorities)
        route_dist = Counter(routes)
        outcome_dist = Counter(outcomes)

        return {
            "records": len(records),
            "avg_urgency": round(statistics.mean(urgencies), 4),
            "max_urgency": round(max(urgencies), 4),
            "avg_confidence": round(statistics.mean(confidences), 4),
            "human_review_rate": round(human_review_count / len(records), 4),
            "severity_distribution": dict(severity_dist),
            "priority_distribution": dict(priority_dist),
            "route_distribution": dict(route_dist),
            "outcomes_logged": len(outcomes),
            "outcome_distribution": dict(outcome_dist),
        }

    def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
        """
        Very simple research-oriented snapshot:
        groups cases into urgency buckets and reports observed outcome counts.
        """
        records = [r for r in self.store.list_records(limit=limit) if r.outcome]
        if not records:
            return {"records_with_outcomes": 0, "buckets": {}}

        buckets = {
            "0.00-0.39": [],
            "0.40-0.64": [],
            "0.65-0.84": [],
            "0.85-1.00": [],
        }

        for r in records:
            u = r.risk.urgency
            if u < 0.40:
                buckets["0.00-0.39"].append(r.outcome or "UNKNOWN")
            elif u < 0.65:
                buckets["0.40-0.64"].append(r.outcome or "UNKNOWN")
            elif u < 0.85:
                buckets["0.65-0.84"].append(r.outcome or "UNKNOWN")
            else:
                buckets["0.85-1.00"].append(r.outcome or "UNKNOWN")

        return {
            "records_with_outcomes": len(records),
            "buckets": {k: dict(Counter(v)) for k, v in buckets.items()},
        }


# =============================================================================
# SECTION 10 — MAIN ENGINE
# =============================================================================


class CrisisAIEngine:
    def __init__(
        self,
        db_path: str,
        audit_jsonl_path: str,
        verbose: bool = True,
        policy_name: str = "default",
    ):
        self.policy = load_policy(policy_name)
        self.ingestion = SignalIngestion()
        self.risk_engine = RiskEngine(self.policy)
        self.decision_engine = DecisionEngine(self.policy)
        self.store = SQLiteStore(db_path)
        self.audit = AuditLogger(audit_jsonl_path, verbose=verbose)
        self.feedback = FeedbackEngine(self.store)

    def process(self, raw_input: str, metadata: Optional[Dict[str, Any]] = None) -> TriageRecord:
        t0 = time.perf_counter()

        signal, features = self.ingestion.ingest(raw_input, metadata=metadata)
        risk = self.risk_engine.score(signal, features)
        decision = self.decision_engine.decide(signal, features, risk)

        processing_ms = round((time.perf_counter() - t0) * 1000.0, 3)

        record = TriageRecord(
            case_id=signal.case_id,
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=processing_ms,
        )

        self.store.save_record(record)
        self.audit.log(record)
        return record

    def simulate_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.feedback.record_outcome(case_id, outcome, reviewer_notes)

    def report(self) -> Dict[str, Any]:
        return self.feedback.summary()

    def calibration_report(self) -> Dict[str, Any]:
        return self.feedback.calibration_snapshot()

    def export_records(self, path: str, limit: int = 5000) -> None:
        payload = [r.to_public_dict() for r in self.store.list_records(limit=limit)]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def close(self) -> None:
        self.store.close()


# =============================================================================
# SECTION 11 — DEMO DATA
# =============================================================================


DEMO_CASES: List[Tuple[str, Dict[str, Any], str]] = [
    (
        "I've been feeling a little down lately and just needed to talk.",
        {"channel": "chat", "source": "demo"},
        "RESOLVED_SUPPORTIVE_CONVERSATION",
    ),
    (
        "I don't know how much longer I can handle this. I feel completely overwhelmed and scared.",
        {"channel": "chat", "source": "demo"},
        "COUNSELOR_FOLLOW_UP",
    ),
    (
        "I'm in crisis right now. I feel hopeless and desperate. Please help me.",
        {"channel": "voice", "source": "demo"},
        "IMMEDIATE_CLINICIAN_CONTACT",
    ),
    (
        "I want to end my life tonight. I have a plan and I don't see any reason to go on.",
        {"channel": "chat", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
    (
        "help",
        {"channel": "sms", "source": "demo"},
        "MONITORED_AND_ENGAGED",
    ),
    (
        "I've been going through a rough patch at work and my manager keeps piling on extra tasks. "
        "It's stressful but I'm managing. Just needed to vent somewhere because my friends are busy. "
        "I'll be okay.",
        {"channel": "chat", "source": "demo"},
        "NO_ESCALATION_REQUIRED",
    ),
    (
        "Not suicidal. No plan. I am safe, but I really need to talk to someone tonight because I'm panicking.",
        {"channel": "chat", "source": "demo"},
        "URGENT_SUPPORT_CONTACT",
    ),
    (
        "I have pills and I think tonight is the night.",
        {"channel": "sms", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
]


# =============================================================================
# SECTION 12 — OUTPUT HELPERS
# =============================================================================


def print_header(title: str) -> None:
    print("\n" + "═" * 80)
    print(title)
    print("═" * 80 + "\n")


def print_sbir_concept() -> None:
    print_header("AI CRISIS TRIAGE SYSTEM — NIH SBIR CONCEPT OVERVIEW")
    sections = {
        "PROJECT TITLE": PROJECT_TITLE,
        "PROJECT SUMMARY": PROJECT_SUMMARY,
        "SPECIFIC AIMS": SPECIFIC_AIMS,
        "SIGNIFICANCE": SIGNIFICANCE,
        "INNOVATION": INNOVATION,
        "TECHNICAL RISKS": TECHNICAL_RISKS,
        "RISK MITIGATIONS": RISK_MITIGATIONS,
        "COMMERCIALIZATION": COMMERCIALIZATION,
        "EXPECTED OUTCOMES": EXPECTED_OUTCOMES,
        "MILESTONES": MILESTONES,
        "BUDGET": BUDGET,
    }

    for name, value in sections.items():
        print(f"{name}")
        print("-" * len(name))
        if isinstance(value, str):
            print(textwrap.fill(value, width=88))
        elif isinstance(value, dict):
            for k, v in value.items():
                print(f"  - {k}: ${v:,.0f}")
        else:
            for item in value:
                print(f"  - {item}")
        print()


def print_summary(summary: Dict[str, Any], calibration: Optional[Dict[str, Any]] = None) -> None:
    print_header("SESSION / DATABASE SUMMARY")
    for k, v in summary.items():
        print(f"{k:>24} : {v}")
    if calibration is not None:
        print("\nCALIBRATION SNAPSHOT")
        print("--------------------")
        for k, v in calibration.items():
            print(f"{k:>24} : {v}")
    print()


def print_record_detail(record: TriageRecord) -> None:
    print_header(f"CASE DETAIL — {record.case_id}")
    print(f"Created at      : {record.signal.created_at}")
    print(f"Message         : {record.signal.message}")
    print(f"Metadata        : {json.dumps(record.signal.metadata, ensure_ascii=False)}")
    print()
    print("Feature Summary")
    print("---------------")
    print(json.dumps(asdict(record.features), indent=2, ensure_ascii=False))
    print()
    print("Risk")
    print("----")
    print(json.dumps(asdict(record.risk), indent=2, ensure_ascii=False))
    print()
    print("Decision")
    print("--------")
    print(json.dumps(asdict(record.decision), indent=2, ensure_ascii=False))
    print()
    print(f"Processing ms   : {record.processing_ms}")
    print(f"Outcome         : {record.outcome}")
    print(f"Reviewer notes  : {record.reviewer_notes}")
    print()


# =============================================================================
# SECTION 13 — CLI
# =============================================================================


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Crisis Triage System — NIH SBIR Research Single-File Prototype"
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demonstration cases")
    parser.add_argument("--interactive", action="store_true", help="Run interactive console mode")
    parser.add_argument("--batch", type=str, help="Run batch mode from JSONL input file")
    parser.add_argument("--summary", action="store_true", help="Print summary from stored records")
    parser.add_argument("--show-case", type=str, help="Print detailed stored record by case_id")
    parser.add_argument("--export-records", type=str, help="Export stored records to JSON file")
    parser.add_argument("--print-concept", action="store_true", help="Print the SBIR concept package")
    parser.add_argument("--quiet", action="store_true", help="Reduce console output")
    parser.add_argument("--db", type=str, default=os.getenv("CRISIS_TRIAGE_DB", "crisis_triage.db"))
    parser.add_argument(
        "--audit-jsonl",
        type=str,
        default=os.getenv("CRISIS_TRIAGE_AUDIT_JSONL", "audit_log.jsonl"),
    )
    parser.add_argument(
        "--policy",
        type=str,
        default=os.getenv("CRISIS_TRIAGE_POLICY", "default"),
    )
    return parser.parse_args(argv)


# =============================================================================
# SECTION 14 — RUN MODES
# =============================================================================


def run_demo(engine: CrisisAIEngine) -> None:
    print_header("AI CRISIS TRIAGE SYSTEM — DEMO RUN")
    for idx, (message, metadata, outcome) in enumerate(DEMO_CASES, start=1):
        print(f"[Demo Case {idx}/{len(DEMO_CASES)}]")
        record = engine.process(message, metadata=metadata)
        engine.simulate_outcome(record.case_id, outcome, reviewer_notes="demo outcome")
        print(f"Outcome logged : {outcome}\n")

    summary = engine.report()
    calibration = engine.calibration_report()
    print_summary(summary, calibration=calibration)


def run_interactive(engine: CrisisAIEngine) -> None:
    print_header("INTERACTIVE MODE")
    print("Type a message and press Enter.")
    print("Commands:")
    print("  /quit                 exit")
    print("  /summary              print summary")
    print("  /show <case_id>       show case detail")
    print("  /outcome <case_id> <OUTCOME TEXT>")
    print()

    while True:
        try:
            raw = input("message> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if not raw:
            continue

        if raw == "/quit":
            break

        if raw == "/summary":
            print_summary(engine.report(), calibration=engine.calibration_report())
            continue

        if raw.startswith("/show "):
            _, _, case_id = raw.partition(" ")
            rec = engine.store.get_record(case_id.strip())
            if rec is None:
                print("No such case.")
            else:
                print_record_detail(rec)
            continue

        if raw.startswith("/outcome "):
            parts = raw.split(maxsplit=2)
            if len(parts) < 3:
                print("Usage: /outcome <case_id> <OUTCOME TEXT>")
                continue
            _, case_id, outcome = parts
            ok = engine.simulate_outcome(case_id, outcome, reviewer_notes="interactive outcome")
            print("Outcome recorded." if ok else "Case not found.")
            continue

        record = engine.process(raw, metadata={"channel": "interactive_console"})


def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"Line {line_no} is not a JSON object")
            yield obj


def run_batch(engine: CrisisAIEngine, path: str) -> None:
    print_header(f"BATCH MODE — {path}")
    count = 0
    for obj in iter_jsonl(path):
        message = str(obj.get("message", "")).strip()
        metadata = obj.get("metadata", {})
        if not message:
            continue
        engine.process(message, metadata=metadata if isinstance(metadata, dict) else {})
        count += 1

    print(f"Processed {count} records.\n")
    print_summary(engine.report(), calibration=engine.calibration_report())


# =============================================================================
# SECTION 15 — MAIN
# =============================================================================


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    verbose = not args.quiet
    engine = CrisisAIEngine(
        db_path=args.db,
        audit_jsonl_path=args.audit_jsonl,
        verbose=verbose,
        policy_name=args.policy,
    )

    try:
        if args.print_concept:
            print_sbir_concept()

        action_taken = False

        if args.demo:
            run_demo(engine)
            action_taken = True

        if args.interactive:
            run_interactive(engine)
            action_taken = True

        if args.batch:
            run_batch(engine, args.batch)
            action_taken = True

        if args.summary:
            print_summary(engine.report(), calibration=engine.calibration_report())
            action_taken = True

        if args.show_case:
            rec = engine.store.get_record(args.show_case)
            if rec is None:
                print(f"No record found for case_id={args.show_case}")
            else:
                print_record_detail(rec)
            action_taken = True

        if args.export_records:
            engine.export_records(args.export_records)
            print(f"Exported records to {args.export_records}")
            action_taken = True

        if not action_taken:
            print_header("AI CRISIS TRIAGE SYSTEM — READY")
            print("No action selected. Try one of:")
            print("  --demo")
            print("  --interactive")
            print("  --batch cases.jsonl")
            print("  --summary")
            print("  --print-concept")
            print()

    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

What makes this outperform the original:

- It is valid Python as written.
- It is deterministic instead of random.
- It separates feature extraction, scoring, routing, persistence, and evaluation cleanly.
- It has safety floors for self-harm and violence signals.
- It routes low-confidence cases to human review instead of pretending certainty.
- It stores everything in SQLite and JSONL for auditability.
- It includes CLI modes, case lookup, outcome logging, summaries, and calibration snapshots.
- It reads much more like a serious research prototype than a sketch.

I can also turn this into an even stronger “Phase I SBIR submission style” version with:

- synthetic evaluation harness,
- confusion-matrix reporting,
- YAML/JSON policy loading,
- FastAPI service endpoints,
- red-team test cases,
- Dockerfile and README,
  all still as one polished package.


#### You:
polish and refactor and rebrand this.

#### ChatGPT:
I’m tightening the architecture and giving it a cleaner product identity so it reads less like a draft and more like a real pilot-ready research platform.


#### ChatGPT:
Here’s a polished, refactored, and rebranded version.

I renamed it from a generic “AI Crisis Triage System” into a more credible, product-like research identity:

**Aegis Triage**
**Human-Guided Crisis Signal Intelligence Platform**

What changed:

- cleaner structure
- stronger naming
- more professional SBIR/research language
- clearer separation of concept, policy, engine, storage, and CLI
- more consistent explanations and operator-facing wording
- better docstrings and comments
- less rough prototype energy, more pilot-ready package energy

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
═══════════════════════════════════════════════════════════════════════════════
AEGIS TRIAGE
Human-Guided Crisis Signal Intelligence Platform
NIH SBIR Research Prototype — Single-File Edition
═══════════════════════════════════════════════════════════════════════════════

OVERVIEW
--------
Aegis Triage is a research-oriented, human-guided crisis signal intelligence
prototype designed for:
- real-time crisis signal intake,
- explainable urgency estimation,
- policy-aware routing recommendations,
- operator review support,
- retrospective audit and evaluation.

This file intentionally combines:
1) SBIR-style concept framing
2) a functional deterministic prototype
3) storage, audit, and reporting utilities
4) a command-line interface for demo, batch, and interactive use

IMPORTANT
---------
This software is a research prototype for workflow support, evaluation,
simulation, and pilot design. It is not a substitute for licensed clinical
judgment, emergency response procedure, or approved crisis center policy.

DESIGN PRINCIPLES
-----------------
- human-guided, not human-replacing
- deterministic and explainable
- auditable and retrospective-ready
- conservative in uncertainty
- single-file deployable
- pilot-program friendly

EXAMPLES
--------
python aegis_triage.py --demo
python aegis_triage.py --interactive
python aegis_triage.py --batch cases.jsonl
python aegis_triage.py --summary
python aegis_triage.py --print-concept

OPTIONAL ENVIRONMENT VARIABLES
------------------------------
AEGIS_DB=aegis_triage.db
AEGIS_AUDIT_JSONL=aegis_audit.jsonl
AEGIS_POLICY=default
AEGIS_VERBOSE=true
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import statistics
import textwrap
import time
import hashlib
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# BRAND + CONCEPT LAYER
# =============================================================================

BRAND_NAME = "Aegis Triage"
BRAND_TAGLINE = "Human-Guided Crisis Signal Intelligence Platform"
BRAND_SHORT_DESCRIPTION = (
    "A deterministic, explainable, human-guided triage intelligence prototype "
    "for crisis workflows, research pilots, and operator decision support."
)

PROJECT_TITLE = f"{BRAND_NAME}: {BRAND_TAGLINE}"

PROJECT_SUMMARY = """
Crisis response environments, including 988-aligned operations, behavioral
health triage teams, telehealth intake, and emergency communication workflows,
must make high-stakes prioritization decisions under time pressure, incomplete
information, and variable staffing.

Aegis Triage is a human-guided crisis signal intelligence platform designed to
support those workflows with deterministic feature extraction, explainable
urgency estimation, policy-aware routing recommendations, and retrospective
auditability.

The system does not replace human judgment. Instead, it helps teams:
- identify salient crisis indicators,
- structure urgency review consistently,
- prioritize uncertain and high-risk cases conservatively,
- log decision context for quality assurance and research,
- create an evaluation pathway for future supervised model refinement.

The goal is to improve response consistency, transparency, timeliness, and
operational learning in crisis support environments.
""".strip()

SPECIFIC_AIMS = [
    "Build a real-time crisis signal intake and feature extraction pipeline.",
    "Develop an explainable, deterministic urgency estimation engine.",
    "Implement policy-aware routing recommendations with conservative safety rules.",
    "Create a feedback and retrospective analysis layer for continuous evaluation.",
]

SIGNIFICANCE = [
    "Improves consistency in high-pressure triage workflows.",
    "Preserves human authority while enhancing operator support.",
    "Creates auditable evidence for quality assurance and pilot review.",
    "Supports public-sector and healthcare-oriented AI operations modernization.",
]

INNOVATION = [
    "Explainable crisis signal intelligence rather than opaque scoring alone.",
    "Conservative uncertainty handling that escalates review rather than suppressing it.",
    "Policy-aware routing recommendations with explicit safety floors.",
    "Single-file deployable research architecture for rapid pilots and demos.",
]

TECHNICAL_RISKS = [
    "Ambiguous language may create uncertainty in urgency estimation.",
    "Metaphorical or quoted language may trigger false positives.",
    "Workflow misuse may occur if operators over-trust automated suggestions.",
    "Different channels and populations may require policy recalibration.",
]

RISK_MITIGATIONS = [
    "Route uncertain cases toward human review.",
    "Maintain deterministic logic and transparent feature contributions.",
    "Enforce conservative safety floors for self-harm and violence signals.",
    "Preserve full audit logs for calibration and incident review.",
]

COMMERCIALIZATION = [
    "Crisis hotline modernization pilots",
    "Behavioral health intake support systems",
    "Emergency communications decision-support tooling",
    "Healthcare operations intelligence infrastructure",
]

MILESTONES = [
    "Signal intake and feature extraction baseline",
    "Urgency estimation and policy routing baseline",
    "Audit logging and persistence layer",
    "Outcome tracking and retrospective reporting",
    "Pilot-readiness package for grant and procurement discussions",
]

BUDGET = {
    "engineering": 90000,
    "clinical_advisory": 35000,
    "security_and_compliance": 20000,
    "cloud_and_storage": 12000,
    "evaluation_and_pilot_support": 28000,
    "miscellaneous": 15000,
}


# =============================================================================
# UTILITY LAYER
# =============================================================================

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_case_id(message: str, timestamp: float) -> str:
    raw = f"{timestamp}|{message}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:16]
    return f"aegis_{digest}"


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compact_text(text: str, width: int = 88) -> str:
    text = " ".join(text.split())
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


# =============================================================================
# POLICY LAYER
# =============================================================================

@dataclass
class Policy:
    name: str = "default"

    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    low_confidence_threshold: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    emergency_route: str = "EMERGENCY_DISPATCH_RECOMMENDED"
    immediate_route: str = "IMMEDIATE_CLINICIAN_REVIEW"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "PRIORITY_QUEUE"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

    w_high_risk: float = 0.24
    w_medium_risk: float = 0.09
    w_plan: float = 0.22
    w_means: float = 0.16
    w_immediacy: float = 0.18
    w_self_harm: float = 0.26
    w_violence: float = 0.26
    w_distress: float = 0.10
    w_protective: float = -0.18
    w_help_seeking: float = -0.04
    w_negation_safety: float = -0.10
    w_short_signal: float = 0.08
    w_caps: float = 0.03
    w_punctuation: float = 0.03

    confidence_base: float = 0.50
    confidence_per_feature_group: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_metadata: float = 0.05

    require_human_review_for_high: bool = True
    route_low_confidence_to_human: bool = True
    preserve_self_harm_floor: bool = True
    preserve_violence_floor: bool = True


def load_policy(name: str = "default") -> Policy:
    return Policy(name=name)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class CrisisSignal:
    case_id: str
    timestamp: float
    created_at: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureSet:
    word_count: int
    char_count: int
    sentence_count: int
    uppercase_ratio: float
    exclamation_count: int
    question_count: int

    high_risk_hits: List[str] = field(default_factory=list)
    medium_risk_hits: List[str] = field(default_factory=list)
    plan_hits: List[str] = field(default_factory=list)
    means_hits: List[str] = field(default_factory=list)
    immediacy_hits: List[str] = field(default_factory=list)
    self_harm_hits: List[str] = field(default_factory=list)
    violence_hits: List[str] = field(default_factory=list)
    protective_hits: List[str] = field(default_factory=list)
    help_hits: List[str] = field(default_factory=list)
    negation_hits: List[str] = field(default_factory=list)
    ambiguity_hits: List[str] = field(default_factory=list)
    distress_hits: List[str] = field(default_factory=list)

    def total_hits(self) -> int:
        groups = [
            self.high_risk_hits,
            self.medium_risk_hits,
            self.plan_hits,
            self.means_hits,
            self.immediacy_hits,
            self.self_harm_hits,
            self.violence_hits,
            self.protective_hits,
            self.help_hits,
            self.negation_hits,
            self.ambiguity_hits,
            self.distress_hits,
        ]
        return sum(len(group) for group in groups)


@dataclass
class RiskAssessment:
    urgency: float
    confidence: float
    band: str
    reasons: List[str] = field(default_factory=list)
    contributions: Dict[str, float] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    priority: str
    route_to: str
    explanation: str
    requires_human_review: bool
    safety_flags: List[str] = field(default_factory=list)


@dataclass
class CaseRecord:
    case_id: str
    signal: CrisisSignal
    features: FeatureSet
    risk: RiskAssessment
    decision: RoutingDecision
    processing_ms: float
    outcome: Optional[str] = None
    reviewer_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "signal": asdict(self.signal),
            "features": asdict(self.features),
            "risk": asdict(self.risk),
            "decision": asdict(self.decision),
            "processing_ms": self.processing_ms,
            "outcome": self.outcome,
            "reviewer_notes": self.reviewer_notes,
        }


# =============================================================================
# FEATURE EXTRACTION LAYER
# =============================================================================

class SignalAnalyzer:
    """
    Deterministic language-pattern extractor for research prototypes.
    """

    HIGH_RISK = {
        r"\bi want to die\b": "want_to_die",
        r"\bend my life\b": "end_my_life",
        r"\bkill myself\b": "kill_myself",
        r"\bsuicide\b": "suicide",
        r"\bno reason to live\b": "no_reason_to_live",
        r"\bcan't go on\b": "cant_go_on",
        r"\boverdose\b": "overdose",
        r"\bhurt myself\b": "hurt_myself",
        r"\bself harm\b": "self_harm",
    }

    MEDIUM_RISK = {
        r"\bhopeless\b": "hopeless",
        r"\bpanic\b": "panic",
        r"\bdesperate\b": "desperate",
        r"\boverwhelmed\b": "overwhelmed",
        r"\bscared\b": "scared",
        r"\bafraid\b": "afraid",
        r"\bbreaking down\b": "breaking_down",
        r"\bin crisis\b": "in_crisis",
        r"\balone\b": "alone",
    }

    PLAN = {
        r"\bi have a plan\b": "have_a_plan",
        r"\bplanned\b": "planned",
        r"\bi know how\b": "know_how",
        r"\btonight\b": "tonight",
        r"\bafter everyone sleeps\b": "after_everyone_sleeps",
    }

    MEANS = {
        r"\bpills\b": "pills",
        r"\bgun\b": "gun",
        r"\bknife\b": "knife",
        r"\brope\b": "rope",
        r"\bweapon\b": "weapon",
        r"\brazor\b": "razor",
    }

    IMMEDIACY = {
        r"\bnow\b": "now",
        r"\bright now\b": "right_now",
        r"\btoday\b": "today",
        r"\btonight\b": "tonight",
        r"\bimmediately\b": "immediately",
        r"\bsoon\b": "soon",
    }

    SELF_HARM = {
        r"\bhurt myself\b": "hurt_myself",
        r"\bcut myself\b": "cut_myself",
        r"\bself harm\b": "self_harm",
        r"\bkill myself\b": "kill_myself",
        r"\bend my life\b": "end_my_life",
    }

    VIOLENCE = {
        r"\bhurt someone\b": "hurt_someone",
        r"\bkill them\b": "kill_them",
        r"\bshoot\b": "shoot",
        r"\bstab\b": "stab",
        r"\bviolent\b": "violent",
        r"\bweapon\b": "weapon",
    }

    PROTECTIVE = {
        r"\bi am safe\b": "i_am_safe",
        r"\bi'm safe\b": "i_am_safe",
        r"\bi won't do anything\b": "wont_do_anything",
        r"\bi do not want to die\b": "do_not_want_to_die",
        r"\bi don't want to die\b": "do_not_want_to_die",
        r"\bi am with someone\b": "with_someone",
        r"\bi'm with someone\b": "with_someone",
        r"\bmy therapist\b": "therapist",
        r"\bmy counselor\b": "counselor",
    }

    HELP = {
        r"\bplease help\b": "please_help",
        r"\bneed help\b": "need_help",
        r"\bi need to talk\b": "need_to_talk",
        r"\bcan someone talk\b": "someone_talk",
        r"\blooking for support\b": "support",
    }

    NEGATION = {
        r"\bnot suicidal\b": "not_suicidal",
        r"\bnot going to hurt myself\b": "not_hurt_self",
        r"\bnot going to kill myself\b": "not_kill_self",
        r"\bno plan\b": "no_plan",
        r"\bno intent\b": "no_intent",
    }

    AMBIGUITY = {
        r"\bjust kidding\b": "just_kidding",
        r"\bfiguratively\b": "figuratively",
        r"\bquote\b": "quote",
        r"\bsong lyric\b": "song_lyric",
        r"\bmetaphor\b": "metaphor",
    }

    DISTRESS = {
        r"\bcan't\b": "cant",
        r"\bnever\b": "never",
        r"\balways\b": "always",
        r"\bno one\b": "no_one",
        r"\bnobody\b": "nobody",
        r"\bi'm done\b": "im_done",
        r"\bi am done\b": "im_done",
    }

    @staticmethod
    def _hits(text: str, patterns: Dict[str, str]) -> List[str]:
        found: List[str] = []
        for pattern, label in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.append(label)
        return sorted(set(found))

    @staticmethod
    def _sentence_count(text: str) -> int:
        parts = [p.strip() for p in re.split(r"[.!?]+", text) if p.strip()]
        return max(1, len(parts))

    @staticmethod
    def _uppercase_ratio(text: str) -> float:
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        uppercase = sum(1 for c in letters if c.isupper())
        return round(uppercase / len(letters), 4)

    def analyze(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[CrisisSignal, FeatureSet]:
        timestamp = time.time()
        case_id = make_case_id(message, timestamp)
        signal = CrisisSignal(
            case_id=case_id,
            timestamp=timestamp,
            created_at=now_utc_iso(),
            message=message,
            metadata=dict(metadata or {}),
        )

        lower = message.lower()
        features = FeatureSet(
            word_count=len(message.split()),
            char_count=len(message),
            sentence_count=self._sentence_count(message),
            uppercase_ratio=self._uppercase_ratio(message),
            exclamation_count=message.count("!"),
            question_count=message.count("?"),
            high_risk_hits=self._hits(lower, self.HIGH_RISK),
            medium_risk_hits=self._hits(lower, self.MEDIUM_RISK),
            plan_hits=self._hits(lower, self.PLAN),
            means_hits=self._hits(lower, self.MEANS),
            immediacy_hits=self._hits(lower, self.IMMEDIACY),
            self_harm_hits=self._hits(lower, self.SELF_HARM),
            violence_hits=self._hits(lower, self.VIOLENCE),
            protective_hits=self._hits(lower, self.PROTECTIVE),
            help_hits=self._hits(lower, self.HELP),
            negation_hits=self._hits(lower, self.NEGATION),
            ambiguity_hits=self._hits(lower, self.AMBIGUITY),
            distress_hits=self._hits(lower, self.DISTRESS),
        )

        signal.metadata.update(
            {
                "word_count": features.word_count,
                "char_count": features.char_count,
                "sentence_count": features.sentence_count,
                "uppercase_ratio": features.uppercase_ratio,
                "exclamation_count": features.exclamation_count,
                "question_count": features.question_count,
            }
        )
        return signal, features


# =============================================================================
# RISK LAYER
# =============================================================================

class UrgencyModel:
    def __init__(self, policy: Policy):
        self.policy = policy

    def assess(self, signal: CrisisSignal, features: FeatureSet) -> RiskAssessment:
        contributions: Dict[str, float] = {}
        reasons: List[str] = []

        base = min(0.18, features.word_count / 300.0)
        contributions["base_text_density"] = round(base, 4)

        def add_if_nonzero(name: str, value: float) -> None:
            if value:
                contributions[name] = round(value, 4)

        high = len(features.high_risk_hits) * self.policy.w_high_risk
        medium = len(features.medium_risk_hits) * self.policy.w_medium_risk
        plan = len(features.plan_hits) * self.policy.w_plan
        means = len(features.means_hits) * self.policy.w_means
        immediacy = len(features.immediacy_hits) * self.policy.w_immediacy
        self_harm = len(features.self_harm_hits) * self.policy.w_self_harm
        violence = len(features.violence_hits) * self.policy.w_violence
        distress = len(features.distress_hits) * self.policy.w_distress
        protective = len(features.protective_hits) * self.policy.w_protective
        help_signal = len(features.help_hits) * self.policy.w_help_seeking
        negation = len(features.negation_hits) * self.policy.w_negation_safety

        add_if_nonzero("high_risk", high)
        add_if_nonzero("medium_risk", medium)
        add_if_nonzero("plan", plan)
        add_if_nonzero("means", means)
        add_if_nonzero("immediacy", immediacy)
        add_if_nonzero("self_harm", self_harm)
        add_if_nonzero("violence", violence)
        add_if_nonzero("distress", distress)
        add_if_nonzero("protective", protective)
        add_if_nonzero("help_seeking", help_signal)
        add_if_nonzero("negation", negation)

        if features.high_risk_hits:
            reasons.append(f"high-risk indicators: {', '.join(features.high_risk_hits)}")
        if features.medium_risk_hits:
            reasons.append(f"distress indicators: {', '.join(features.medium_risk_hits)}")
        if features.plan_hits:
            reasons.append(f"plan indicators: {', '.join(features.plan_hits)}")
        if features.means_hits:
            reasons.append(f"means indicators: {', '.join(features.means_hits)}")
        if features.immediacy_hits:
            reasons.append(f"time/immediacy indicators: {', '.join(features.immediacy_hits)}")
        if features.self_harm_hits:
            reasons.append(f"self-harm indicators: {', '.join(features.self_harm_hits)}")
        if features.violence_hits:
            reasons.append(f"violence indicators: {', '.join(features.violence_hits)}")
        if features.protective_hits:
            reasons.append(f"protective factors: {', '.join(features.protective_hits)}")
        if features.help_hits:
            reasons.append(f"help-seeking language: {', '.join(features.help_hits)}")

        short_signal = 0.0
        if features.word_count <= 3 and (
            features.high_risk_hits
            or features.medium_risk_hits
            or features.help_hits
            or features.self_harm_hits
        ):
            short_signal = self.policy.w_short_signal
            contributions["short_signal"] = round(short_signal, 4)
            reasons.append("very short message with meaningful crisis/help signal")

        emphasis = 0.0
        if features.uppercase_ratio >= 0.35:
            emphasis += self.policy.w_caps
        if features.exclamation_count >= 2:
            emphasis += self.policy.w_punctuation
        add_if_nonzero("emphasis", emphasis)

        urgency_raw = (
            base
            + high
            + medium
            + plan
            + means
            + immediacy
            + self_harm
            + violence
            + distress
            + protective
            + help_signal
            + negation
            + short_signal
            + emphasis
        )

        if features.self_harm_hits and self.policy.preserve_self_harm_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["self_harm_floor"] = 0.72

        if features.violence_hits and self.policy.preserve_violence_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["violence_floor"] = 0.72

        urgency = clamp01(urgency_raw)

        feature_groups = sum(
            1 for group in [
                features.high_risk_hits,
                features.medium_risk_hits,
                features.plan_hits,
                features.means_hits,
                features.immediacy_hits,
                features.self_harm_hits,
                features.violence_hits,
                features.protective_hits,
                features.help_hits,
                features.negation_hits,
                features.ambiguity_hits,
                features.distress_hits,
            ] if group
        )

        confidence = self.policy.confidence_base
        confidence += feature_groups * self.policy.confidence_per_feature_group
        confidence += min(4, features.total_hits()) * self.policy.confidence_per_signal_density

        if features.ambiguity_hits:
            confidence -= self.policy.confidence_penalty_ambiguity
            reasons.append(f"ambiguity markers: {', '.join(features.ambiguity_hits)}")

        if features.word_count <= 2:
            confidence -= self.policy.confidence_penalty_too_short
            reasons.append("extremely short input lowers confidence")

        if signal.metadata:
            confidence += self.policy.confidence_bonus_metadata

        confidence = clamp01(confidence)

        if urgency >= self.policy.critical_threshold:
            band = "CRITICAL"
        elif urgency >= self.policy.high_threshold:
            band = "HIGH"
        elif urgency >= self.policy.medium_threshold:
            band = "MEDIUM"
        else:
            band = "LOW"

        if not reasons:
            reasons.append("limited direct risk language; estimate driven by general signal density")

        return RiskAssessment(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            band=band,
            reasons=reasons,
            contributions=contributions,
        )


# =============================================================================
# DECISION LAYER
# =============================================================================

class RoutingEngine:
    def __init__(self, policy: Policy):
        self.policy = policy

    def decide(self, features: FeatureSet, risk: RiskAssessment) -> RoutingDecision:
        flags: List[str] = []
        low_confidence = risk.confidence < self.policy.low_confidence_threshold
        self_harm_present = bool(features.self_harm_hits or features.high_risk_hits)
        violence_present = bool(features.violence_hits)

        if self_harm_present:
            flags.append("SELF_HARM_SIGNAL")
        if violence_present:
            flags.append("VIOLENCE_SIGNAL")
        if features.plan_hits:
            flags.append("PLAN_INDICATOR")
        if features.means_hits:
            flags.append("MEANS_INDICATOR")
        if low_confidence:
            flags.append("LOW_CONFIDENCE")

        if risk.urgency >= self.policy.critical_threshold:
            priority = "CRITICAL"
            route = self.policy.emergency_route
            review = True
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds critical threshold "
                f"{self.policy.critical_threshold:.2f}; emergency-aligned escalation is recommended."
            )
        elif risk.urgency >= self.policy.high_threshold:
            priority = "HIGH"
            route = self.policy.immediate_route
            review = self.policy.require_human_review_for_high
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds high threshold "
                f"{self.policy.high_threshold:.2f}; immediate clinician review is recommended."
            )
        elif risk.urgency >= self.policy.medium_threshold:
            priority = "MEDIUM"
            route = self.policy.priority_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds medium threshold "
                f"{self.policy.medium_threshold:.2f}; priority handling is recommended."
            )
        else:
            priority = "LOW"
            route = self.policy.standard_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} is below medium threshold; "
                f"standard queue placement is recommended."
            )

        if low_confidence and self.policy.route_low_confidence_to_human:
            route = self.policy.mandatory_review_route
            review = True
            explanation += " Confidence is limited, so human review is required."

        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = self.policy.urgent_review_route
            review = True
            explanation += " High-risk plus uncertainty triggers urgent human review."

        if self_harm_present and priority == "LOW":
            priority = "MEDIUM"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Self-harm language prevents a low-priority disposition."

        if violence_present and priority in {"LOW", "MEDIUM"}:
            priority = "HIGH"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Violence language elevates the case for urgent review."

        return RoutingDecision(
            priority=priority,
            route_to=route,
            explanation=explanation,
            requires_human_review=review,
            safety_flags=flags,
        )


# =============================================================================
# STORAGE LAYER
# =============================================================================

class CaseStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_records (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                timestamp REAL NOT NULL,
                message TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                features_json TEXT NOT NULL,
                risk_json TEXT NOT NULL,
                decision_json TEXT NOT NULL,
                processing_ms REAL NOT NULL,
                outcome TEXT,
                reviewer_notes TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                reviewer_notes TEXT,
                recorded_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_case_outcomes_case_id ON case_outcomes(case_id)"
        )
        self.conn.commit()

    def save(self, record: CaseRecord) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO case_records (
                case_id, created_at, timestamp, message, metadata_json,
                features_json, risk_json, decision_json, processing_ms,
                outcome, reviewer_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.case_id,
                record.signal.created_at,
                record.signal.timestamp,
                record.signal.message,
                json.dumps(record.signal.metadata, ensure_ascii=False),
                json.dumps(asdict(record.features), ensure_ascii=False),
                json.dumps(asdict(record.risk), ensure_ascii=False),
                json.dumps(asdict(record.decision), ensure_ascii=False),
                record.processing_ms,
                record.outcome,
                record.reviewer_notes,
            ),
        )
        self.conn.commit()

    def set_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE case_records
            SET outcome = ?, reviewer_notes = ?
            WHERE case_id = ?
            """,
            (outcome, reviewer_notes, case_id),
        )
        updated = cur.rowcount > 0
        cur.execute(
            """
            INSERT INTO case_outcomes (case_id, outcome, reviewer_notes, recorded_at)
            VALUES (?, ?, ?, ?)
            """,
            (case_id, outcome, reviewer_notes, now_utc_iso()),
        )
        self.conn.commit()
        return updated

    def get(self, case_id: str) -> Optional[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM case_records WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_recent(self, limit: int = 1000) -> List[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM case_records ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row: sqlite3.Row) -> CaseRecord:
        signal = CrisisSignal(
            case_id=row["case_id"],
            timestamp=row["timestamp"],
            created_at=row["created_at"],
            message=row["message"],
            metadata=json.loads(row["metadata_json"]),
        )
        features = FeatureSet(**json.loads(row["features_json"]))
        risk = RiskAssessment(**json.loads(row["risk_json"]))
        decision = RoutingDecision(**json.loads(row["decision_json"]))
        return CaseRecord(
            case_id=row["case_id"],
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=row["processing_ms"],
            outcome=row["outcome"],
            reviewer_notes=row["reviewer_notes"],
        )

    def close(self) -> None:
        self.conn.close()


# =============================================================================
# AUDIT LAYER
# =============================================================================

class AuditTrail:
    def __init__(self, jsonl_path: str, verbose: bool = True):
        self.jsonl_path = jsonl_path
        self.verbose = verbose
        self._entries: List[Dict[str, Any]] = []

    def log(self, record: CaseRecord) -> None:
        entry = record.to_dict()
        self._entries.append(entry)

        with open(self.jsonl_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if self.verbose:
            self._print(record)

    def _print(self, record: CaseRecord) -> None:
        print("┌" + "─" * 78)
        print(f"│ BRAND        : {BRAND_NAME}")
        print(f"│ CASE ID      : {record.case_id}")
        print(f"│ MESSAGE      : {compact_text(record.signal.message)}")
        print(f"│ URGENCY      : {record.risk.urgency:.4f}    CONFIDENCE: {record.risk.confidence:.4f}")
        print(f"│ BAND         : {record.risk.band}")
        print(f"│ PRIORITY     : {record.decision.priority:<12} ROUTE: {record.decision.route_to}")
        print(f"│ HUMAN REVIEW : {record.decision.requires_human_review}")
        print(f"│ FLAGS        : {', '.join(record.decision.safety_flags) if record.decision.safety_flags else 'None'}")
        print(f"│ REASONS      : {compact_text('; '.join(record.risk.reasons[:3]), 70)}")
        print(f"│ LATENCY      : {record.processing_ms:.2f} ms")
        print("└" + "─" * 78)

    def export_json(self) -> str:
        return json.dumps(self._entries, indent=2, ensure_ascii=False)


# =============================================================================
# FEEDBACK + REPORTING LAYER
# =============================================================================

class ReviewLoop:
    def __init__(self, store: CaseStore):
        self.store = store

    def record_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.store.set_outcome(case_id, outcome, reviewer_notes)

    def summary(self, limit: int = 5000) -> Dict[str, Any]:
        records = self.store.list_recent(limit=limit)
        if not records:
            return {"records": 0}

        urgencies = [r.risk.urgency for r in records]
        confidences = [r.risk.confidence for r in records]
        priorities = [r.decision.priority for r in records]
        routes = [r.decision.route_to for r in records]
        outcomes = [r.outcome for r in records if r.outcome]

        return {
            "brand": BRAND_NAME,
            "records": len(records),
            "avg_urgency": round(statistics.mean(urgencies), 4),
            "max_urgency": round(max(urgencies), 4),
            "avg_confidence": round(statistics.mean(confidences), 4),
            "human_review_rate": round(
                sum(1 for r in records if r.decision.requires_human_review) / len(records), 4
            ),
            "band_distribution": dict(Counter(r.risk.band for r in records)),
            "priority_distribution": dict(Counter(priorities)),
            "route_distribution": dict(Counter(routes)),
            "outcomes_logged": len(outcomes),
            "outcome_distribution": dict(Counter(outcomes)),
        }

    def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
        records = [r for r in self.store.list_recent(limit=limit) if r.outcome]
        if not records:
            return {"records_with_outcomes": 0, "buckets": {}}

        buckets = {
            "0.00-0.39": [],
            "0.40-0.64": [],
            "0.65-0.84": [],
            "0.85-1.00": [],
        }

        for record in records:
            u = record.risk.urgency
            if u < 0.40:
                buckets["0.00-0.39"].append(record.outcome or "UNKNOWN")
            elif u < 0.65:
                buckets["0.40-0.64"].append(record.outcome or "UNKNOWN")
            elif u < 0.85:
                buckets["0.65-0.84"].append(record.outcome or "UNKNOWN")
            else:
                buckets["0.85-1.00"].append(record.outcome or "UNKNOWN")

        return {
            "records_with_outcomes": len(records),
            "buckets": {k: dict(Counter(v)) for k, v in buckets.items()},
        }


# =============================================================================
# ORCHESTRATION LAYER
# =============================================================================

class AegisTriageEngine:
    def __init__(
        self,
        db_path: str,
        audit_jsonl_path: str,
        verbose: bool = True,
        policy_name: str = "default",
    ):
        self.policy = load_policy(policy_name)
        self.analyzer = SignalAnalyzer()
        self.urgency_model = UrgencyModel(self.policy)
        self.routing_engine = RoutingEngine(self.policy)
        self.store = CaseStore(db_path)
        self.audit = AuditTrail(audit_jsonl_path, verbose=verbose)
        self.review = ReviewLoop(self.store)

    def process(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> CaseRecord:
        start = time.perf_counter()

        signal, features = self.analyzer.analyze(message, metadata=metadata)
        risk = self.urgency_model.assess(signal, features)
        decision = self.routing_engine.decide(features, risk)

        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 3)

        record = CaseRecord(
            case_id=signal.case_id,
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=elapsed_ms,
        )

        self.store.save(record)
        self.audit.log(record)
        return record

    def log_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.review.record_outcome(case_id, outcome, reviewer_notes)

    def export_records(self, path: str, limit: int = 5000) -> None:
        payload = [r.to_dict() for r in self.store.list_recent(limit=limit)]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    def summary(self) -> Dict[str, Any]:
        return self.review.summary()

    def calibration(self) -> Dict[str, Any]:
        return self.review.calibration_snapshot()

    def close(self) -> None:
        self.store.close()


# =============================================================================
# PRESENTATION LAYER
# =============================================================================

def print_header(title: str) -> None:
    print("\n" + "═" * 80)
    print(title)
    print("═" * 80 + "\n")


def print_concept() -> None:
    print_header(f"{BRAND_NAME.upper()} — SBIR RESEARCH CONCEPT")
    sections = {
        "TITLE": PROJECT_TITLE,
        "BRAND DESCRIPTION": BRAND_SHORT_DESCRIPTION,
        "PROJECT SUMMARY": PROJECT_SUMMARY,
        "SPECIFIC AIMS": SPECIFIC_AIMS,
        "SIGNIFICANCE": SIGNIFICANCE,
        "INNOVATION": INNOVATION,
        "TECHNICAL RISKS": TECHNICAL_RISKS,
        "RISK MITIGATIONS": RISK_MITIGATIONS,
        "COMMERCIALIZATION": COMMERCIALIZATION,
        "MILESTONES": MILESTONES,
        "BUDGET": BUDGET,
    }

    for name, value in sections.items():
        print(name)
        print("-" * len(name))
        if isinstance(value, str):
            print(textwrap.fill(value, width=88))
        elif isinstance(value, dict):
            for k, v in value.items():
                print(f"  - {k}: ${v:,.0f}")
        else:
            for item in value:
                print(f"  - {item}")
        print()


def print_summary(summary: Dict[str, Any], calibration: Optional[Dict[str, Any]] = None) -> None:
    print_header(f"{BRAND_NAME.upper()} — SUMMARY")
    for key, value in summary.items():
        print(f"{key:>24} : {value}")
    if calibration is not None:
        print("\nCALIBRATION SNAPSHOT")
        print("--------------------")
        for key, value in calibration.items():
            print(f"{key:>24} : {value}")
    print()


def print_case(record: CaseRecord) -> None:
    print_header(f"{BRAND_NAME.upper()} — CASE DETAIL")
    print(f"Case ID         : {record.case_id}")
    print(f"Created at      : {record.signal.created_at}")
    print(f"Message         : {record.signal.message}")
    print(f"Metadata        : {json.dumps(record.signal.metadata, ensure_ascii=False)}")
    print()
    print("FEATURES")
    print("--------")
    print(json.dumps(asdict(record.features), indent=2, ensure_ascii=False))
    print()
    print("RISK")
    print("----")
    print(json.dumps(asdict(record.risk), indent=2, ensure_ascii=False))
    print()
    print("DECISION")
    print("--------")
    print(json.dumps(asdict(record.decision), indent=2, ensure_ascii=False))
    print()
    print(f"Processing ms   : {record.processing_ms}")
    print(f"Outcome         : {record.outcome}")
    print(f"Reviewer notes  : {record.reviewer_notes}")
    print()


# =============================================================================
# DEMO CASES
# =============================================================================

DEMO_CASES: List[Tuple[str, Dict[str, Any], str]] = [
    (
        "I've been feeling a little down lately and just needed to talk.",
        {"channel": "chat", "source": "demo"},
        "RESOLVED_SUPPORTIVE_CONTACT",
    ),
    (
        "I don't know how much longer I can handle this. I feel completely overwhelmed and scared.",
        {"channel": "chat", "source": "demo"},
        "COUNSELOR_FOLLOW_UP",
    ),
    (
        "I'm in crisis right now. I feel hopeless and desperate. Please help me.",
        {"channel": "voice", "source": "demo"},
        "IMMEDIATE_CLINICIAN_CONTACT",
    ),
    (
        "I want to end my life tonight. I have a plan and I don't see any reason to go on.",
        {"channel": "chat", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
    (
        "help",
        {"channel": "sms", "source": "demo"},
        "MONITORED_AND_ENGAGED",
    ),
    (
        "Not suicidal. No plan. I am safe, but I really need to talk to someone tonight because I'm panicking.",
        {"channel": "chat", "source": "demo"},
        "URGENT_SUPPORT_CONTACT",
    ),
    (
        "I have pills and I think tonight is the night.",
        {"channel": "sms", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
]


# =============================================================================
# CLI LAYER
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{BRAND_NAME} — single-file research prototype"
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demonstration cases")
    parser.add_argument("--interactive", action="store_true", help="Run interactive console mode")
    parser.add_argument("--batch", type=str, help="Process a JSONL batch file")
    parser.add_argument("--summary", action="store_true", help="Print stored summary")
    parser.add_argument("--show-case", type=str, help="Show stored case by case_id")
    parser.add_argument("--export-records", type=str, help="Export records to JSON")
    parser.add_argument("--print-concept", action="store_true", help="Print concept package")
    parser.add_argument("--quiet", action="store_true", help="Reduce console output")
    parser.add_argument("--db", type=str, default=os.getenv("AEGIS_DB", "aegis_triage.db"))
    parser.add_argument(
        "--audit-jsonl",
        type=str,
        default=os.getenv("AEGIS_AUDIT_JSONL", "aegis_audit.jsonl"),
    )
    parser.add_argument(
        "--policy",
        type=str,
        default=os.getenv("AEGIS_POLICY", "default"),
    )
    return parser.parse_args(argv)


def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Line {line_no} is not a JSON object")
            yield item


def run_demo(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — DEMO")
    for idx, (message, metadata, outcome) in enumerate(DEMO_CASES, start=1):
        print(f"[Demo Case {idx}/{len(DEMO_CASES)}]")
        record = engine.process(message, metadata=metadata)
        engine.log_outcome(record.case_id, outcome, reviewer_notes="demo outcome")
        print(f"Outcome logged : {outcome}\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_batch(engine: AegisTriageEngine, path: str) -> None:
    print_header(f"{BRAND_NAME.upper()} — BATCH MODE")
    processed = 0
    for item in iter_jsonl(path):
        message = str(item.get("message", "")).strip()
        metadata = item.get("metadata", {})
        if not message:
            continue
        engine.process(message, metadata if isinstance(metadata, dict) else {})
        processed += 1
    print(f"Processed {processed} records.\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_interactive(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — INTERACTIVE MODE")
    print("Enter a message, then press Enter.")
    print("Commands:")
    print("  /quit")
    print("  /summary")
    print("  /show <case_id>")
    print("  /outcome <case_id> <OUTCOME TEXT>")
    print()

    while True:
        try:
            raw = input("message> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if not raw:
            continue
        if raw == "/quit":
            break
        if raw == "/summary":
            print_summary(engine.summary(), calibration=engine.calibration())
            continue
        if raw.startswith("/show "):
            _, _, case_id = raw.partition(" ")
            record = engine.store.get(case_id.strip())
            if record is None:
                print("Case not found.")
            else:
                print_case(record)
            continue
        if raw.startswith("/outcome "):
            parts = raw.split(maxsplit=2)
            if len(parts) < 3:
                print("Usage: /outcome <case_id> <OUTCOME TEXT>")
                continue
            _, case_id, outcome = parts
            ok = engine.log_outcome(case_id, outcome, reviewer_notes="interactive outcome")
            print("Outcome recorded." if ok else "Case not found.")
            continue

        engine.process(raw, metadata={"channel": "interactive_console"})


# =============================================================================
# MAIN
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    engine = AegisTriageEngine(
        db_path=args.db,
        audit_jsonl_path=args.audit_jsonl,
        verbose=not args.quiet,
        policy_name=args.policy,
    )

    try:
        acted = False

        if args.print_concept:
            print_concept()
            acted = True

        if args.demo:
            run_demo(engine)
            acted = True

        if args.batch:
            run_batch(engine, args.batch)
            acted = True

        if args.interactive:
            run_interactive(engine)
            acted = True

        if args.summary:
            print_summary(engine.summary(), calibration=engine.calibration())
            acted = True

        if args.show_case:
            record = engine.store.get(args.show_case)
            if record is None:
                print(f"No case found for case_id={args.show_case}")
            else:
                print_case(record)
            acted = True

        if args.export_records:
            engine.export_records(args.export_records)
            print(f"Exported records to {args.export_records}")
            acted = True

        if not acted:
            print_header(f"{BRAND_NAME.upper()} — READY")
            print(BRAND_TAGLINE)
            print()
            print("No action selected. Try:")
            print("  --demo")
            print("  --interactive")
            print("  --batch cases.jsonl")
            print("  --summary")
            print("  --print-concept")
            print()

    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

A stronger brand set you can use around it:

**Primary name**

- Aegis Triage

**Tagline options**

- Human-Guided Crisis Signal Intelligence
- Explainable Triage Intelligence for High-Stakes Workflows
- Decision Support for Crisis Operations

**Alternative names**

- Sentinel Triage
- Harbor Signal
- Northline Response
- Continuum Triage
- Atlas Crisis Intelligence

Best one here is still **Aegis Triage** because it sounds protective, serious, and procurement-friendly without sounding gimmicky.

If you want, next I can turn this into a full sale-ready package with:

- README
- NIH-style abstract
- one-page architecture summary
- product positioning copy
- logo/title block
- FastAPI version in the same branding style


#### You:


#### ChatGPT:
Tell me what you want done next with it.


#### You:
Got it — you’re asking for a system prompt that chains chats, tracks assets, indexes files, and calculates valuation cumulatively (not just one-off appraisals).

This is the institutional-grade “master ledger + chaining + valuation engine” prompt you’re looking for:

⸻


You are an Institutional Asset Ledger, Appraisal Engine, and Chat Consolidator.

Your job is to:
1. Track all assets across this chat AND prior chained chats
2. Index them
3. Deduplicate overlap
4. Maintain a running valuation ledger
5. Calculate real, non-inflated dollar values

You are NOT a normal assistant.
You behave like:
- a technical due diligence analyst
- a VC associate
- a product/IP appraiser
- a systems auditor

--------------------------------------------------
CORE SYSTEM
--------------------------------------------------

You maintain a MASTER LEDGER.

Each new input (code, file, idea, system) must be:

1) IDENTIFIED
2) NAMED
3) CLASSIFIED
4) INDEXED
5) VALUED
6) MERGED with prior assets (if overlap exists)

--------------------------------------------------
ASSET TYPES
--------------------------------------------------

Classify each asset into one of:

- UI / Frontend Demo
- Backend System
- Script / Automation
- Research / Documentation
- Architecture / System Design
- Product Concept
- Dataset / File
- Infrastructure / DevOps
- AI / Agent System
- Financial / Trading System

--------------------------------------------------
LEDGER FORMAT
--------------------------------------------------

For each asset, store:

[ASSET ID]
- Sequential (A-001, A-002, ...)

[NAME]
- Clear unique name (e.g. "Ollama Agent Orchestrator UI Demo")

[TYPE]

[FILES / SOURCES]
- File names or descriptions from chat
- Example: ollama-agent-orchestrator-demo.zip
- Example: grant_copilot_single_file.py

[DESCRIPTION]
- What it actually is (no hype)

[STATUS]
- draft / demo / partial / production-ready

[VALUE BLOCK]

- Extractable Value: $X–$Y
- Realistic Buyer Value: $X–$Y
- Productized Value: $X–$Y

[OVERLAP]
- Which previous assets it overlaps with

[NET NEW VALUE]
- Value added AFTER removing duplication

[BLOCKERS]
- Why value is capped

--------------------------------------------------
MERGE RULE (CRITICAL)
--------------------------------------------------

When a new asset is added:

- DO NOT double count value
- If it overlaps existing assets:
    → reduce its standalone value
    → only count incremental improvement

Example:
If UI demo already exists and new UI is similar:
→ only count polish delta ($500–$2K), not full value again

--------------------------------------------------
VALUATION RULES
--------------------------------------------------

You MUST:

Penalize:
- no backend
- no execution engine
- no users
- no revenue
- security issues
- hardcoded secrets
- demo-only systems
- duplicated ideas

Reward:
- real architecture
- execution capability
- system cohesion
- production readiness
- monetization pathways
- unique research

--------------------------------------------------
CHAINING LOGIC
--------------------------------------------------

Treat this chat as part of a CONTINUOUS SYSTEM.

Maintain:

[CHAT INDEX]
- Chat 001, Chat 002, ...

[ASSET INDEX MAP]
- Which assets came from which chat

[VALUE EVOLUTION]
- Track how assets improved over time

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

Every time you respond, output:

==============================
[MASTER LEDGER SNAPSHOT]
==============================

List ALL assets:

A-001 ...
A-002 ...
...

Each with:
- Name
- Type
- Net Value

------------------------------

[PORTFOLIO TOTAL]

- Gross Value (before deduplication): $X–$Y
- Net Realistic Value: $X–$Y
- Productized Portfolio Value: $X–$Y

------------------------------

[VALUE CHANGES FROM LAST STATE]

- +$X added from new assets
- -$X removed due to overlap
- Net change: +$X / -$X

------------------------------

[TOP VALUE DRIVERS]

- Asset A-00X ...
- Asset A-00Y ...

------------------------------

[VALUE LEAKS]

- duplication
- incomplete systems
- missing execution layers
- security flaws

------------------------------

[HARD TRUTH]

Blunt, investor-level summary:
- what actually has value
- what is noise
- what must be fixed to unlock next level

--------------------------------------------------
STYLE RULES
--------------------------------------------------

- Be surgical, not emotional
- No fluff
- No hype
- No emojis
- No vague praise
- Think like money allocator, not assistant

--------------------------------------------------
GOAL
--------------------------------------------------

Your goal is to turn chaotic chats into:

→ a structured asset portfolio
→ a clean valuation model
→ a compounding system of value

You are building a ledger, not giving opinions.


⸻

🔥 What this gives you (important)

This prompt turns ChatGPT into:
	•	a persistent asset tracker
	•	a portfolio appraiser
	•	a de-duplication engine
	•	a value compounding system

Instead of:

random chats

You now get:

an evolving $-denominated system of your work

⸻

🧠 Pro move (use this next)

After pasting that prompt, follow with:

Initialize ledger from this chat.
Index all assets.
Assign IDs.
Calculate full portfolio value.


⸻

If you want next level, I can upgrade this into:
	•	automatic file ingestion system
	•	zip analyzer
	•	code quality scoring
	•	production readiness scoring
	•	investor-grade report generator

Just say:

“upgrade ledger to v2”respond to this 

#### ChatGPT:
This is already strong—but it’s still missing **true institutional rigor, enforceability, and scaling logic**.

I’m upgrading it into a **V2 SYSTEM PROMPT** that behaves like an actual internal tool a VC / PE / technical diligence team would use.

---

# 🔒 INSTITUTIONAL LEDGER SYSTEM PROMPT — V2 (UPGRADED)

```
You are an Institutional Asset Ledger, Valuation Engine, and System Consolidator.

You operate as:
- Technical Due Diligence Analyst
- VC Associate
- Product/IP Appraiser
- Systems Auditor

You do NOT behave like a conversational assistant.
You behave like a valuation system.

--------------------------------------------------
PRIMARY OBJECTIVE
--------------------------------------------------

Convert all inputs across chats into:

1) A structured asset portfolio
2) A deduplicated system map
3) A continuously updated valuation ledger

You track VALUE, not ideas.

--------------------------------------------------
GLOBAL MEMORY MODEL
--------------------------------------------------

You maintain:

[MASTER LEDGER] — all assets
[ASSET GRAPH] — relationships + overlaps
[CHAT INDEX] — chronological source tracking
[VALUE EVOLUTION LOG] — changes over time

Treat all chats as ONE continuous system.

--------------------------------------------------
ASSET INGESTION PIPELINE
--------------------------------------------------

Every new input MUST go through:

STEP 1 — IDENTIFICATION
- Detect distinct assets (code, systems, ideas, files)

STEP 2 — NORMALIZATION
- Merge duplicates
- Collapse variants into canonical asset

STEP 3 — CLASSIFICATION
Assign ONE primary type:

- UI / Frontend
- Backend System
- Script / Automation
- AI / Agent System
- Architecture / Design
- Research / Documentation
- Dataset / File
- DevOps / Infrastructure
- Financial / Trading System
- Product Concept

STEP 4 — DECOMPOSITION
Break asset into components:
- interface
- logic
- execution
- storage
- integration
- security

STEP 5 — SCORING
Evaluate across:

- Completeness (0–5)
- Execution Capability (0–5)
- Novelty (0–5)
- Monetization Potential (0–5)
- Production Readiness (0–5)

STEP 6 — VALUATION
Produce 3 layers:

- Extractable Value → theoretical max
- Realistic Value → what sells TODAY
- Productized Value → with packaging + polish

STEP 7 — MERGE
- Deduplicate against existing assets
- Only count incremental improvement

--------------------------------------------------
LEDGER STRUCTURE
--------------------------------------------------

Each asset MUST be stored as:

[ASSET ID]
A-001, A-002, ...

[NAME]
Canonical, stable name

[TYPE]

[ORIGIN]
- Chat ID(s)
- Source input

[FILES / SOURCES]

[DESCRIPTION]
Concrete, technical

[COMPONENTS]
- UI
- Backend
- Logic
- Data
- etc.

[STATUS]
- idea / draft / demo / partial / production-ready

[SCORING]
- Completeness: X/5
- Execution: X/5
- Novelty: X/5
- Monetization: X/5
- Readiness: X/5

[VALUE]
- Extractable: $X–$Y
- Realistic: $X–$Y
- Productized: $X–$Y

[OVERLAP]
- % overlap with existing assets
- Reference IDs

[NET NEW VALUE]
- Value AFTER deduplication

[DEPENDENCIES]
- Requires other assets to be useful

[BLOCKERS]
- What prevents higher valuation

--------------------------------------------------
MERGE + DEDUP ENGINE (STRICT)
--------------------------------------------------

You MUST:

- Detect similarity across assets
- Collapse duplicates
- Reduce value accordingly

Rules:

IF overlap > 70%:
→ Treat as same asset
→ Only log delta improvements

IF overlap 30–70%:
→ Partial merge
→ Discount value by overlap %

IF overlap < 30%:
→ New asset

NEVER double count.

--------------------------------------------------
VALUATION MODEL (STRICT)
--------------------------------------------------

Base values MUST be grounded in reality.

PENALIZE heavily:
- no execution
- demo-only
- no backend
- no persistence
- no users / traction
- security flaws
- copied / generic systems

REWARD:
- working systems
- integration depth
- real architecture
- monetization clarity
- unique capability
- production readiness

--------------------------------------------------
PORTFOLIO METRICS
--------------------------------------------------

You MUST compute:

[PORTFOLIO TOTAL]

- Gross Value (sum naive)
- Net Value (after deduplication)
- Productized Value (if packaged + sold)

[VALUE DENSITY]
- Value per asset

[FRAGMENTATION SCORE]
- How scattered vs cohesive system is

--------------------------------------------------
VALUE EVOLUTION LOG
--------------------------------------------------

Track deltas:

For each update:

+ Value added (new assets)
- Value removed (overlap/dedup)
= Net delta

--------------------------------------------------
OUTPUT FORMAT (MANDATORY)
--------------------------------------------------

==============================
MASTER LEDGER SNAPSHOT
==============================

A-001 — Name — Type — Net Value: $X–$Y
A-002 — Name — Type — Net Value: $X–$Y
...

------------------------------

PORTFOLIO TOTAL

- Gross Value: $X–$Y
- Net Realistic Value: $X–$Y
- Productized Value: $X–$Y

------------------------------

VALUE CHANGES

+ Added: $X
- Deducted: $X
= Net: $X

------------------------------

TOP VALUE DRIVERS

- A-00X → why
- A-00Y → why

------------------------------

VALUE LEAKS

- duplication
- missing execution
- weak integration
- security gaps

------------------------------

SYSTEM STRUCTURE

- Core assets
- Supporting assets
- Orphaned assets

------------------------------

HARD TRUTH

Blunt assessment:
- what actually has value
- what is noise
- what must be fixed to unlock next tier

NO SOFT LANGUAGE.

--------------------------------------------------
STYLE RULES
--------------------------------------------------

- No fluff
- No praise
- No emojis
- No speculation
- No hallucinated value

Be:
- precise
- critical
- grounded
- financially realistic

--------------------------------------------------
INITIALIZATION COMMAND
--------------------------------------------------

When user says:

"Initialize ledger"

You MUST:

1) Scan full chat
2) Extract all assets
3) Assign IDs
4) Deduplicate
5) Build full ledger
6) Output full snapshot

--------------------------------------------------
ADVANCED MODES (AUTO-DETECT)
--------------------------------------------------

If user provides:
- ZIP → treat as multi-asset bundle
- Code → extract systems + modules
- Prompt → treat as productizable IP
- Dataset → treat as leverage multiplier

--------------------------------------------------
GOAL
--------------------------------------------------

Transform chaotic work into:

→ a structured asset portfolio
→ a compounding valuation system
→ a decision-grade investment view

You are not assisting.

You are auditing and valuing.
```

---

# 🔥 What Changed (Why This Is Actually Better)

Your version = **good framework**

This version = **operational system**

Upgrades:

- Adds **scoring model (0–5 dimensions)** → objective valuation
- Adds **overlap % logic** → real deduplication math
- Adds **asset graph + dependencies** → system thinking
- Adds **fragmentation + density metrics** → portfolio quality insight
- Adds **component decomposition** → deeper technical audit
- Adds **strict merge rules** → prevents fake value inflation
- Adds **advanced ingestion modes (ZIP/code/prompt)**

---

# 🧠 If You Want Next Level (real power move)

Say:

**“upgrade ledger to v3”**

And I’ll give you:

- automatic code quality scoring
- security vulnerability detection
- revenue model inference
- SaaS packaging paths
- investor-grade PDF report generator
- “what to build next for +$100K value” engine

That’s where it becomes *dangerously useful*.


#### You:
Respond to prompt #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
═══════════════════════════════════════════════════════════════════════════════
AEGIS TRIAGE
Human-Guided Crisis Signal Intelligence Platform
NIH SBIR Research Prototype — Single-File Edition
═══════════════════════════════════════════════════════════════════════════════

OVERVIEW
--------
Aegis Triage is a research-oriented, human-guided crisis signal intelligence
prototype designed for:
- real-time crisis signal intake,
- explainable urgency estimation,
- policy-aware routing recommendations,
- operator review support,
- retrospective audit and evaluation.

This file intentionally combines:
1) SBIR-style concept framing
2) a functional deterministic prototype
3) storage, audit, and reporting utilities
4) a command-line interface for demo, batch, and interactive use

IMPORTANT
---------
This software is a research prototype for workflow support, evaluation,
simulation, and pilot design. It is not a substitute for licensed clinical
judgment, emergency response procedure, or approved crisis center policy.

DESIGN PRINCIPLES
-----------------
- human-guided, not human-replacing
- deterministic and explainable
- auditable and retrospective-ready
- conservative in uncertainty
- single-file deployable
- pilot-program friendly

EXAMPLES
--------
python aegis_triage.py --demo
python aegis_triage.py --interactive
python aegis_triage.py --batch cases.jsonl
python aegis_triage.py --summary
python aegis_triage.py --print-concept

OPTIONAL ENVIRONMENT VARIABLES
------------------------------
AEGIS_DB=aegis_triage.db
AEGIS_AUDIT_JSONL=aegis_audit.jsonl
AEGIS_POLICY=default
AEGIS_VERBOSE=true
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import statistics
import textwrap
import time
import hashlib
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# BRAND + CONCEPT LAYER
# =============================================================================

BRAND_NAME = "Aegis Triage"
BRAND_TAGLINE = "Human-Guided Crisis Signal Intelligence Platform"
BRAND_SHORT_DESCRIPTION = (
    "A deterministic, explainable, human-guided triage intelligence prototype "
    "for crisis workflows, research pilots, and operator decision support."
)

PROJECT_TITLE = f"{BRAND_NAME}: {BRAND_TAGLINE}"

PROJECT_SUMMARY = """
Crisis response environments, including 988-aligned operations, behavioral
health triage teams, telehealth intake, and emergency communication workflows,
must make high-stakes prioritization decisions under time pressure, incomplete
information, and variable staffing.

Aegis Triage is a human-guided crisis signal intelligence platform designed to
support those workflows with deterministic feature extraction, explainable
urgency estimation, policy-aware routing recommendations, and retrospective
auditability.

The system does not replace human judgment. Instead, it helps teams:
- identify salient crisis indicators,
- structure urgency review consistently,
- prioritize uncertain and high-risk cases conservatively,
- log decision context for quality assurance and research,
- create an evaluation pathway for future supervised model refinement.

The goal is to improve response consistency, transparency, timeliness, and
operational learning in crisis support environments.
""".strip()

SPECIFIC_AIMS = [
    "Build a real-time crisis signal intake and feature extraction pipeline.",
    "Develop an explainable, deterministic urgency estimation engine.",
    "Implement policy-aware routing recommendations with conservative safety rules.",
    "Create a feedback and retrospective analysis layer for continuous evaluation.",
]

SIGNIFICANCE = [
    "Improves consistency in high-pressure triage workflows.",
    "Preserves human authority while enhancing operator support.",
    "Creates auditable evidence for quality assurance and pilot review.",
    "Supports public-sector and healthcare-oriented AI operations modernization.",
]

INNOVATION = [
    "Explainable crisis signal intelligence rather than opaque scoring alone.",
    "Conservative uncertainty handling that escalates review rather than suppressing it.",
    "Policy-aware routing recommendations with explicit safety floors.",
    "Single-file deployable research architecture for rapid pilots and demos.",
]

TECHNICAL_RISKS = [
    "Ambiguous language may create uncertainty in urgency estimation.",
    "Metaphorical or quoted language may trigger false positives.",
    "Workflow misuse may occur if operators over-trust automated suggestions.",
    "Different channels and populations may require policy recalibration.",
]

RISK_MITIGATIONS = [
    "Route uncertain cases toward human review.",
    "Maintain deterministic logic and transparent feature contributions.",
    "Enforce conservative safety floors for self-harm and violence signals.",
    "Preserve full audit logs for calibration and incident review.",
]

COMMERCIALIZATION = [
    "Crisis hotline modernization pilots",
    "Behavioral health intake support systems",
    "Emergency communications decision-support tooling",
    "Healthcare operations intelligence infrastructure",
]

MILESTONES = [
    "Signal intake and feature extraction baseline",
    "Urgency estimation and policy routing baseline",
    "Audit logging and persistence layer",
    "Outcome tracking and retrospective reporting",
    "Pilot-readiness package for grant and procurement discussions",
]

BUDGET = {
    "engineering": 90000,
    "clinical_advisory": 35000,
    "security_and_compliance": 20000,
    "cloud_and_storage": 12000,
    "evaluation_and_pilot_support": 28000,
    "miscellaneous": 15000,
}


# =============================================================================
# UTILITY LAYER
# =============================================================================

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_case_id(message: str, timestamp: float) -> str:
    raw = f"{timestamp}|{message}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:16]
    return f"aegis_{digest}"


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compact_text(text: str, width: int = 88) -> str:
    text = " ".join(text.split())
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


# =============================================================================
# POLICY LAYER
# =============================================================================

@dataclass
class Policy:
    name: str = "default"

    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    low_confidence_threshold: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    emergency_route: str = "EMERGENCY_DISPATCH_RECOMMENDED"
    immediate_route: str = "IMMEDIATE_CLINICIAN_REVIEW"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "PRIORITY_QUEUE"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

    w_high_risk: float = 0.24
    w_medium_risk: float = 0.09
    w_plan: float = 0.22
    w_means: float = 0.16
    w_immediacy: float = 0.18
    w_self_harm: float = 0.26
    w_violence: float = 0.26
    w_distress: float = 0.10
    w_protective: float = -0.18
    w_help_seeking: float = -0.04
    w_negation_safety: float = -0.10
    w_short_signal: float = 0.08
    w_caps: float = 0.03
    w_punctuation: float = 0.03

    confidence_base: float = 0.50
    confidence_per_feature_group: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_metadata: float = 0.05

    require_human_review_for_high: bool = True
    route_low_confidence_to_human: bool = True
    preserve_self_harm_floor: bool = True
    preserve_violence_floor: bool = True


def load_policy(name: str = "default") -> Policy:
    return Policy(name=name)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class CrisisSignal:
    case_id: str
    timestamp: float
    created_at: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureSet:
    word_count: int
    char_count: int
    sentence_count: int
    uppercase_ratio: float
    exclamation_count: int
    question_count: int

    high_risk_hits: List[str] = field(default_factory=list)
    medium_risk_hits: List[str] = field(default_factory=list)
    plan_hits: List[str] = field(default_factory=list)
    means_hits: List[str] = field(default_factory=list)
    immediacy_hits: List[str] = field(default_factory=list)
    self_harm_hits: List[str] = field(default_factory=list)
    violence_hits: List[str] = field(default_factory=list)
    protective_hits: List[str] = field(default_factory=list)
    help_hits: List[str] = field(default_factory=list)
    negation_hits: List[str] = field(default_factory=list)
    ambiguity_hits: List[str] = field(default_factory=list)
    distress_hits: List[str] = field(default_factory=list)

    def total_hits(self) -> int:
        groups = [
            self.high_risk_hits,
            self.medium_risk_hits,
            self.plan_hits,
            self.means_hits,
            self.immediacy_hits,
            self.self_harm_hits,
            self.violence_hits,
            self.protective_hits,
            self.help_hits,
            self.negation_hits,
            self.ambiguity_hits,
            self.distress_hits,
        ]
        return sum(len(group) for group in groups)


@dataclass
class RiskAssessment:
    urgency: float
    confidence: float
    band: str
    reasons: List[str] = field(default_factory=list)
    contributions: Dict[str, float] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    priority: str
    route_to: str
    explanation: str
    requires_human_review: bool
    safety_flags: List[str] = field(default_factory=list)


@dataclass
class CaseRecord:
    case_id: str
    signal: CrisisSignal
    features: FeatureSet
    risk: RiskAssessment
    decision: RoutingDecision
    processing_ms: float
    outcome: Optional[str] = None
    reviewer_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "signal": asdict(self.signal),
            "features": asdict(self.features),
            "risk": asdict(self.risk),
            "decision": asdict(self.decision),
            "processing_ms": self.processing_ms,
            "outcome": self.outcome,
            "reviewer_notes": self.reviewer_notes,
        }


# =============================================================================
# FEATURE EXTRACTION LAYER
# =============================================================================

class SignalAnalyzer:
    """
    Deterministic language-pattern extractor for research prototypes.
    """

    HIGH_RISK = {
        r"\bi want to die\b": "want_to_die",
        r"\bend my life\b": "end_my_life",
        r"\bkill myself\b": "kill_myself",
        r"\bsuicide\b": "suicide",
        r"\bno reason to live\b": "no_reason_to_live",
        r"\bcan't go on\b": "cant_go_on",
        r"\boverdose\b": "overdose",
        r"\bhurt myself\b": "hurt_myself",
        r"\bself harm\b": "self_harm",
    }

    MEDIUM_RISK = {
        r"\bhopeless\b": "hopeless",
        r"\bpanic\b": "panic",
        r"\bdesperate\b": "desperate",
        r"\boverwhelmed\b": "overwhelmed",
        r"\bscared\b": "scared",
        r"\bafraid\b": "afraid",
        r"\bbreaking down\b": "breaking_down",
        r"\bin crisis\b": "in_crisis",
        r"\balone\b": "alone",
    }

    PLAN = {
        r"\bi have a plan\b": "have_a_plan",
        r"\bplanned\b": "planned",
        r"\bi know how\b": "know_how",
        r"\btonight\b": "tonight",
        r"\bafter everyone sleeps\b": "after_everyone_sleeps",
    }

    MEANS = {
        r"\bpills\b": "pills",
        r"\bgun\b": "gun",
        r"\bknife\b": "knife",
        r"\brope\b": "rope",
        r"\bweapon\b": "weapon",
        r"\brazor\b": "razor",
    }

    IMMEDIACY = {
        r"\bnow\b": "now",
        r"\bright now\b": "right_now",
        r"\btoday\b": "today",
        r"\btonight\b": "tonight",
        r"\bimmediately\b": "immediately",
        r"\bsoon\b": "soon",
    }

    SELF_HARM = {
        r"\bhurt myself\b": "hurt_myself",
        r"\bcut myself\b": "cut_myself",
        r"\bself harm\b": "self_harm",
        r"\bkill myself\b": "kill_myself",
        r"\bend my life\b": "end_my_life",
    }

    VIOLENCE = {
        r"\bhurt someone\b": "hurt_someone",
        r"\bkill them\b": "kill_them",
        r"\bshoot\b": "shoot",
        r"\bstab\b": "stab",
        r"\bviolent\b": "violent",
        r"\bweapon\b": "weapon",
    }

    PROTECTIVE = {
        r"\bi am safe\b": "i_am_safe",
        r"\bi'm safe\b": "i_am_safe",
        r"\bi won't do anything\b": "wont_do_anything",
        r"\bi do not want to die\b": "do_not_want_to_die",
        r"\bi don't want to die\b": "do_not_want_to_die",
        r"\bi am with someone\b": "with_someone",
        r"\bi'm with someone\b": "with_someone",
        r"\bmy therapist\b": "therapist",
        r"\bmy counselor\b": "counselor",
    }

    HELP = {
        r"\bplease help\b": "please_help",
        r"\bneed help\b": "need_help",
        r"\bi need to talk\b": "need_to_talk",
        r"\bcan someone talk\b": "someone_talk",
        r"\blooking for support\b": "support",
    }

    NEGATION = {
        r"\bnot suicidal\b": "not_suicidal",
        r"\bnot going to hurt myself\b": "not_hurt_self",
        r"\bnot going to kill myself\b": "not_kill_self",
        r"\bno plan\b": "no_plan",
        r"\bno intent\b": "no_intent",
    }

    AMBIGUITY = {
        r"\bjust kidding\b": "just_kidding",
        r"\bfiguratively\b": "figuratively",
        r"\bquote\b": "quote",
        r"\bsong lyric\b": "song_lyric",
        r"\bmetaphor\b": "metaphor",
    }

    DISTRESS = {
        r"\bcan't\b": "cant",
        r"\bnever\b": "never",
        r"\balways\b": "always",
        r"\bno one\b": "no_one",
        r"\bnobody\b": "nobody",
        r"\bi'm done\b": "im_done",
        r"\bi am done\b": "im_done",
    }

    @staticmethod
    def _hits(text: str, patterns: Dict[str, str]) -> List[str]:
        found: List[str] = []
        for pattern, label in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.append(label)
        return sorted(set(found))

    @staticmethod
    def _sentence_count(text: str) -> int:
        parts = [p.strip() for p in re.split(r"[.!?]+", text) if p.strip()]
        return max(1, len(parts))

    @staticmethod
    def _uppercase_ratio(text: str) -> float:
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        uppercase = sum(1 for c in letters if c.isupper())
        return round(uppercase / len(letters), 4)

    def analyze(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[CrisisSignal, FeatureSet]:
        timestamp = time.time()
        case_id = make_case_id(message, timestamp)
        signal = CrisisSignal(
            case_id=case_id,
            timestamp=timestamp,
            created_at=now_utc_iso(),
            message=message,
            metadata=dict(metadata or {}),
        )

        lower = message.lower()
        features = FeatureSet(
            word_count=len(message.split()),
            char_count=len(message),
            sentence_count=self._sentence_count(message),
            uppercase_ratio=self._uppercase_ratio(message),
            exclamation_count=message.count("!"),
            question_count=message.count("?"),
            high_risk_hits=self._hits(lower, self.HIGH_RISK),
            medium_risk_hits=self._hits(lower, self.MEDIUM_RISK),
            plan_hits=self._hits(lower, self.PLAN),
            means_hits=self._hits(lower, self.MEANS),
            immediacy_hits=self._hits(lower, self.IMMEDIACY),
            self_harm_hits=self._hits(lower, self.SELF_HARM),
            violence_hits=self._hits(lower, self.VIOLENCE),
            protective_hits=self._hits(lower, self.PROTECTIVE),
            help_hits=self._hits(lower, self.HELP),
            negation_hits=self._hits(lower, self.NEGATION),
            ambiguity_hits=self._hits(lower, self.AMBIGUITY),
            distress_hits=self._hits(lower, self.DISTRESS),
        )

        signal.metadata.update(
            {
                "word_count": features.word_count,
                "char_count": features.char_count,
                "sentence_count": features.sentence_count,
                "uppercase_ratio": features.uppercase_ratio,
                "exclamation_count": features.exclamation_count,
                "question_count": features.question_count,
            }
        )
        return signal, features


# =============================================================================
# RISK LAYER
# =============================================================================

class UrgencyModel:
    def __init__(self, policy: Policy):
        self.policy = policy

    def assess(self, signal: CrisisSignal, features: FeatureSet) -> RiskAssessment:
        contributions: Dict[str, float] = {}
        reasons: List[str] = []

        base = min(0.18, features.word_count / 300.0)
        contributions["base_text_density"] = round(base, 4)

        def add_if_nonzero(name: str, value: float) -> None:
            if value:
                contributions[name] = round(value, 4)

        high = len(features.high_risk_hits) * self.policy.w_high_risk
        medium = len(features.medium_risk_hits) * self.policy.w_medium_risk
        plan = len(features.plan_hits) * self.policy.w_plan
        means = len(features.means_hits) * self.policy.w_means
        immediacy = len(features.immediacy_hits) * self.policy.w_immediacy
        self_harm = len(features.self_harm_hits) * self.policy.w_self_harm
        violence = len(features.violence_hits) * self.policy.w_violence
        distress = len(features.distress_hits) * self.policy.w_distress
        protective = len(features.protective_hits) * self.policy.w_protective
        help_signal = len(features.help_hits) * self.policy.w_help_seeking
        negation = len(features.negation_hits) * self.policy.w_negation_safety

        add_if_nonzero("high_risk", high)
        add_if_nonzero("medium_risk", medium)
        add_if_nonzero("plan", plan)
        add_if_nonzero("means", means)
        add_if_nonzero("immediacy", immediacy)
        add_if_nonzero("self_harm", self_harm)
        add_if_nonzero("violence", violence)
        add_if_nonzero("distress", distress)
        add_if_nonzero("protective", protective)
        add_if_nonzero("help_seeking", help_signal)
        add_if_nonzero("negation", negation)

        if features.high_risk_hits:
            reasons.append(f"high-risk indicators: {', '.join(features.high_risk_hits)}")
        if features.medium_risk_hits:
            reasons.append(f"distress indicators: {', '.join(features.medium_risk_hits)}")
        if features.plan_hits:
            reasons.append(f"plan indicators: {', '.join(features.plan_hits)}")
        if features.means_hits:
            reasons.append(f"means indicators: {', '.join(features.means_hits)}")
        if features.immediacy_hits:
            reasons.append(f"time/immediacy indicators: {', '.join(features.immediacy_hits)}")
        if features.self_harm_hits:
            reasons.append(f"self-harm indicators: {', '.join(features.self_harm_hits)}")
        if features.violence_hits:
            reasons.append(f"violence indicators: {', '.join(features.violence_hits)}")
        if features.protective_hits:
            reasons.append(f"protective factors: {', '.join(features.protective_hits)}")
        if features.help_hits:
            reasons.append(f"help-seeking language: {', '.join(features.help_hits)}")

        short_signal = 0.0
        if features.word_count <= 3 and (
            features.high_risk_hits
            or features.medium_risk_hits
            or features.help_hits
            or features.self_harm_hits
        ):
            short_signal = self.policy.w_short_signal
            contributions["short_signal"] = round(short_signal, 4)
            reasons.append("very short message with meaningful crisis/help signal")

        emphasis = 0.0
        if features.uppercase_ratio >= 0.35:
            emphasis += self.policy.w_caps
        if features.exclamation_count >= 2:
            emphasis += self.policy.w_punctuation
        add_if_nonzero("emphasis", emphasis)

        urgency_raw = (
            base
            + high
            + medium
            + plan
            + means
            + immediacy
            + self_harm
            + violence
            + distress
            + protective
            + help_signal
            + negation
            + short_signal
            + emphasis
        )

        if features.self_harm_hits and self.policy.preserve_self_harm_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["self_harm_floor"] = 0.72

        if features.violence_hits and self.policy.preserve_violence_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["violence_floor"] = 0.72

        urgency = clamp01(urgency_raw)

        feature_groups = sum(
            1 for group in [
                features.high_risk_hits,
                features.medium_risk_hits,
                features.plan_hits,
                features.means_hits,
                features.immediacy_hits,
                features.self_harm_hits,
                features.violence_hits,
                features.protective_hits,
                features.help_hits,
                features.negation_hits,
                features.ambiguity_hits,
                features.distress_hits,
            ] if group
        )

        confidence = self.policy.confidence_base
        confidence += feature_groups * self.policy.confidence_per_feature_group
        confidence += min(4, features.total_hits()) * self.policy.confidence_per_signal_density

        if features.ambiguity_hits:
            confidence -= self.policy.confidence_penalty_ambiguity
            reasons.append(f"ambiguity markers: {', '.join(features.ambiguity_hits)}")

        if features.word_count <= 2:
            confidence -= self.policy.confidence_penalty_too_short
            reasons.append("extremely short input lowers confidence")

        if signal.metadata:
            confidence += self.policy.confidence_bonus_metadata

        confidence = clamp01(confidence)

        if urgency >= self.policy.critical_threshold:
            band = "CRITICAL"
        elif urgency >= self.policy.high_threshold:
            band = "HIGH"
        elif urgency >= self.policy.medium_threshold:
            band = "MEDIUM"
        else:
            band = "LOW"

        if not reasons:
            reasons.append("limited direct risk language; estimate driven by general signal density")

        return RiskAssessment(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            band=band,
            reasons=reasons,
            contributions=contributions,
        )


# =============================================================================
# DECISION LAYER
# =============================================================================

class RoutingEngine:
    def __init__(self, policy: Policy):
        self.policy = policy

    def decide(self, features: FeatureSet, risk: RiskAssessment) -> RoutingDecision:
        flags: List[str] = []
        low_confidence = risk.confidence < self.policy.low_confidence_threshold
        self_harm_present = bool(features.self_harm_hits or features.high_risk_hits)
        violence_present = bool(features.violence_hits)

        if self_harm_present:
            flags.append("SELF_HARM_SIGNAL")
        if violence_present:
            flags.append("VIOLENCE_SIGNAL")
        if features.plan_hits:
            flags.append("PLAN_INDICATOR")
        if features.means_hits:
            flags.append("MEANS_INDICATOR")
        if low_confidence:
            flags.append("LOW_CONFIDENCE")

        if risk.urgency >= self.policy.critical_threshold:
            priority = "CRITICAL"
            route = self.policy.emergency_route
            review = True
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds critical threshold "
                f"{self.policy.critical_threshold:.2f}; emergency-aligned escalation is recommended."
            )
        elif risk.urgency >= self.policy.high_threshold:
            priority = "HIGH"
            route = self.policy.immediate_route
            review = self.policy.require_human_review_for_high
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds high threshold "
                f"{self.policy.high_threshold:.2f}; immediate clinician review is recommended."
            )
        elif risk.urgency >= self.policy.medium_threshold:
            priority = "MEDIUM"
            route = self.policy.priority_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds medium threshold "
                f"{self.policy.medium_threshold:.2f}; priority handling is recommended."
            )
        else:
            priority = "LOW"
            route = self.policy.standard_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} is below medium threshold; "
                f"standard queue placement is recommended."
            )

        if low_confidence and self.policy.route_low_confidence_to_human:
            route = self.policy.mandatory_review_route
            review = True
            explanation += " Confidence is limited, so human review is required."

        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = self.policy.urgent_review_route
            review = True
            explanation += " High-risk plus uncertainty triggers urgent human review."

        if self_harm_present and priority == "LOW":
            priority = "MEDIUM"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Self-harm language prevents a low-priority disposition."

        if violence_present and priority in {"LOW", "MEDIUM"}:
            priority = "HIGH"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Violence language elevates the case for urgent review."

        return RoutingDecision(
            priority=priority,
            route_to=route,
            explanation=explanation,
            requires_human_review=review,
            safety_flags=flags,
        )


# =============================================================================
# STORAGE LAYER
# =============================================================================

class CaseStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_records (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                timestamp REAL NOT NULL,
                message TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                features_json TEXT NOT NULL,
                risk_json TEXT NOT NULL,
                decision_json TEXT NOT NULL,
                processing_ms REAL NOT NULL,
                outcome TEXT,
                reviewer_notes TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                reviewer_notes TEXT,
                recorded_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_case_outcomes_case_id ON case_outcomes(case_id)"
        )
        self.conn.commit()

    def save(self, record: CaseRecord) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO case_records (
                case_id, created_at, timestamp, message, metadata_json,
                features_json, risk_json, decision_json, processing_ms,
                outcome, reviewer_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.case_id,
                record.signal.created_at,
                record.signal.timestamp,
                record.signal.message,
                json.dumps(record.signal.metadata, ensure_ascii=False),
                json.dumps(asdict(record.features), ensure_ascii=False),
                json.dumps(asdict(record.risk), ensure_ascii=False),
                json.dumps(asdict(record.decision), ensure_ascii=False),
                record.processing_ms,
                record.outcome,
                record.reviewer_notes,
            ),
        )
        self.conn.commit()

    def set_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE case_records
            SET outcome = ?, reviewer_notes = ?
            WHERE case_id = ?
            """,
            (outcome, reviewer_notes, case_id),
        )
        updated = cur.rowcount > 0
        cur.execute(
            """
            INSERT INTO case_outcomes (case_id, outcome, reviewer_notes, recorded_at)
            VALUES (?, ?, ?, ?)
            """,
            (case_id, outcome, reviewer_notes, now_utc_iso()),
        )
        self.conn.commit()
        return updated

    def get(self, case_id: str) -> Optional[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM case_records WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_recent(self, limit: int = 1000) -> List[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM case_records ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row: sqlite3.Row) -> CaseRecord:
        signal = CrisisSignal(
            case_id=row["case_id"],
            timestamp=row["timestamp"],
            created_at=row["created_at"],
            message=row["message"],
            metadata=json.loads(row["metadata_json"]),
        )
        features = FeatureSet(**json.loads(row["features_json"]))
        risk = RiskAssessment(**json.loads(row["risk_json"]))
        decision = RoutingDecision(**json.loads(row["decision_json"]))
        return CaseRecord(
            case_id=row["case_id"],
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=row["processing_ms"],
            outcome=row["outcome"],
            reviewer_notes=row["reviewer_notes"],
        )

    def close(self) -> None:
        self.conn.close()


# =============================================================================
# AUDIT LAYER
# =============================================================================

class AuditTrail:
    def __init__(self, jsonl_path: str, verbose: bool = True):
        self.jsonl_path = jsonl_path
        self.verbose = verbose
        self._entries: List[Dict[str, Any]] = []

    def log(self, record: CaseRecord) -> None:
        entry = record.to_dict()
        self._entries.append(entry)

        with open(self.jsonl_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if self.verbose:
            self._print(record)

    def _print(self, record: CaseRecord) -> None:
        print("┌" + "─" * 78)
        print(f"│ BRAND        : {BRAND_NAME}")
        print(f"│ CASE ID      : {record.case_id}")
        print(f"│ MESSAGE      : {compact_text(record.signal.message)}")
        print(f"│ URGENCY      : {record.risk.urgency:.4f}    CONFIDENCE: {record.risk.confidence:.4f}")
        print(f"│ BAND         : {record.risk.band}")
        print(f"│ PRIORITY     : {record.decision.priority:<12} ROUTE: {record.decision.route_to}")
        print(f"│ HUMAN REVIEW : {record.decision.requires_human_review}")
        print(f"│ FLAGS        : {', '.join(record.decision.safety_flags) if record.decision.safety_flags else 'None'}")
        print(f"│ REASONS      : {compact_text('; '.join(record.risk.reasons[:3]), 70)}")
        print(f"│ LATENCY      : {record.processing_ms:.2f} ms")
        print("└" + "─" * 78)

    def export_json(self) -> str:
        return json.dumps(self._entries, indent=2, ensure_ascii=False)


# =============================================================================
# FEEDBACK + REPORTING LAYER
# =============================================================================

class ReviewLoop:
    def __init__(self, store: CaseStore):
        self.store = store

    def record_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.store.set_outcome(case_id, outcome, reviewer_notes)

    def summary(self, limit: int = 5000) -> Dict[str, Any]:
        records = self.store.list_recent(limit=limit)
        if not records:
            return {"records": 0}

        urgencies = [r.risk.urgency for r in records]
        confidences = [r.risk.confidence for r in records]
        priorities = [r.decision.priority for r in records]
        routes = [r.decision.route_to for r in records]
        outcomes = [r.outcome for r in records if r.outcome]

        return {
            "brand": BRAND_NAME,
            "records": len(records),
            "avg_urgency": round(statistics.mean(urgencies), 4),
            "max_urgency": round(max(urgencies), 4),
            "avg_confidence": round(statistics.mean(confidences), 4),
            "human_review_rate": round(
                sum(1 for r in records if r.decision.requires_human_review) / len(records), 4
            ),
            "band_distribution": dict(Counter(r.risk.band for r in records)),
            "priority_distribution": dict(Counter(priorities)),
            "route_distribution": dict(Counter(routes)),
            "outcomes_logged": len(outcomes),
            "outcome_distribution": dict(Counter(outcomes)),
        }

    def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
        records = [r for r in self.store.list_recent(limit=limit) if r.outcome]
        if not records:
            return {"records_with_outcomes": 0, "buckets": {}}

        buckets = {
            "0.00-0.39": [],
            "0.40-0.64": [],
            "0.65-0.84": [],
            "0.85-1.00": [],
        }

        for record in records:
            u = record.risk.urgency
            if u < 0.40:
                buckets["0.00-0.39"].append(record.outcome or "UNKNOWN")
            elif u < 0.65:
                buckets["0.40-0.64"].append(record.outcome or "UNKNOWN")
            elif u < 0.85:
                buckets["0.65-0.84"].append(record.outcome or "UNKNOWN")
            else:
                buckets["0.85-1.00"].append(record.outcome or "UNKNOWN")

        return {
            "records_with_outcomes": len(records),
            "buckets": {k: dict(Counter(v)) for k, v in buckets.items()},
        }


# =============================================================================
# ORCHESTRATION LAYER
# =============================================================================

class AegisTriageEngine:
    def __init__(
        self,
        db_path: str,
        audit_jsonl_path: str,
        verbose: bool = True,
        policy_name: str = "default",
    ):
        self.policy = load_policy(policy_name)
        self.analyzer = SignalAnalyzer()
        self.urgency_model = UrgencyModel(self.policy)
        self.routing_engine = RoutingEngine(self.policy)
        self.store = CaseStore(db_path)
        self.audit = AuditTrail(audit_jsonl_path, verbose=verbose)
        self.review = ReviewLoop(self.store)

    def process(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> CaseRecord:
        start = time.perf_counter()

        signal, features = self.analyzer.analyze(message, metadata=metadata)
        risk = self.urgency_model.assess(signal, features)
        decision = self.routing_engine.decide(features, risk)

        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 3)

        record = CaseRecord(
            case_id=signal.case_id,
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=elapsed_ms,
        )

        self.store.save(record)
        self.audit.log(record)
        return record

    def log_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.review.record_outcome(case_id, outcome, reviewer_notes)

    def export_records(self, path: str, limit: int = 5000) -> None:
        payload = [r.to_dict() for r in self.store.list_recent(limit=limit)]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    def summary(self) -> Dict[str, Any]:
        return self.review.summary()

    def calibration(self) -> Dict[str, Any]:
        return self.review.calibration_snapshot()

    def close(self) -> None:
        self.store.close()


# =============================================================================
# PRESENTATION LAYER
# =============================================================================

def print_header(title: str) -> None:
    print("\n" + "═" * 80)
    print(title)
    print("═" * 80 + "\n")


def print_concept() -> None:
    print_header(f"{BRAND_NAME.upper()} — SBIR RESEARCH CONCEPT")
    sections = {
        "TITLE": PROJECT_TITLE,
        "BRAND DESCRIPTION": BRAND_SHORT_DESCRIPTION,
        "PROJECT SUMMARY": PROJECT_SUMMARY,
        "SPECIFIC AIMS": SPECIFIC_AIMS,
        "SIGNIFICANCE": SIGNIFICANCE,
        "INNOVATION": INNOVATION,
        "TECHNICAL RISKS": TECHNICAL_RISKS,
        "RISK MITIGATIONS": RISK_MITIGATIONS,
        "COMMERCIALIZATION": COMMERCIALIZATION,
        "MILESTONES": MILESTONES,
        "BUDGET": BUDGET,
    }

    for name, value in sections.items():
        print(name)
        print("-" * len(name))
        if isinstance(value, str):
            print(textwrap.fill(value, width=88))
        elif isinstance(value, dict):
            for k, v in value.items():
                print(f"  - {k}: ${v:,.0f}")
        else:
            for item in value:
                print(f"  - {item}")
        print()


def print_summary(summary: Dict[str, Any], calibration: Optional[Dict[str, Any]] = None) -> None:
    print_header(f"{BRAND_NAME.upper()} — SUMMARY")
    for key, value in summary.items():
        print(f"{key:>24} : {value}")
    if calibration is not None:
        print("\nCALIBRATION SNAPSHOT")
        print("--------------------")
        for key, value in calibration.items():
            print(f"{key:>24} : {value}")
    print()


def print_case(record: CaseRecord) -> None:
    print_header(f"{BRAND_NAME.upper()} — CASE DETAIL")
    print(f"Case ID         : {record.case_id}")
    print(f"Created at      : {record.signal.created_at}")
    print(f"Message         : {record.signal.message}")
    print(f"Metadata        : {json.dumps(record.signal.metadata, ensure_ascii=False)}")
    print()
    print("FEATURES")
    print("--------")
    print(json.dumps(asdict(record.features), indent=2, ensure_ascii=False))
    print()
    print("RISK")
    print("----")
    print(json.dumps(asdict(record.risk), indent=2, ensure_ascii=False))
    print()
    print("DECISION")
    print("--------")
    print(json.dumps(asdict(record.decision), indent=2, ensure_ascii=False))
    print()
    print(f"Processing ms   : {record.processing_ms}")
    print(f"Outcome         : {record.outcome}")
    print(f"Reviewer notes  : {record.reviewer_notes}")
    print()


# =============================================================================
# DEMO CASES
# =============================================================================

DEMO_CASES: List[Tuple[str, Dict[str, Any], str]] = [
    (
        "I've been feeling a little down lately and just needed to talk.",
        {"channel": "chat", "source": "demo"},
        "RESOLVED_SUPPORTIVE_CONTACT",
    ),
    (
        "I don't know how much longer I can handle this. I feel completely overwhelmed and scared.",
        {"channel": "chat", "source": "demo"},
        "COUNSELOR_FOLLOW_UP",
    ),
    (
        "I'm in crisis right now. I feel hopeless and desperate. Please help me.",
        {"channel": "voice", "source": "demo"},
        "IMMEDIATE_CLINICIAN_CONTACT",
    ),
    (
        "I want to end my life tonight. I have a plan and I don't see any reason to go on.",
        {"channel": "chat", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
    (
        "help",
        {"channel": "sms", "source": "demo"},
        "MONITORED_AND_ENGAGED",
    ),
    (
        "Not suicidal. No plan. I am safe, but I really need to talk to someone tonight because I'm panicking.",
        {"channel": "chat", "source": "demo"},
        "URGENT_SUPPORT_CONTACT",
    ),
    (
        "I have pills and I think tonight is the night.",
        {"channel": "sms", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
]


# =============================================================================
# CLI LAYER
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{BRAND_NAME} — single-file research prototype"
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demonstration cases")
    parser.add_argument("--interactive", action="store_true", help="Run interactive console mode")
    parser.add_argument("--batch", type=str, help="Process a JSONL batch file")
    parser.add_argument("--summary", action="store_true", help="Print stored summary")
    parser.add_argument("--show-case", type=str, help="Show stored case by case_id")
    parser.add_argument("--export-records", type=str, help="Export records to JSON")
    parser.add_argument("--print-concept", action="store_true", help="Print concept package")
    parser.add_argument("--quiet", action="store_true", help="Reduce console output")
    parser.add_argument("--db", type=str, default=os.getenv("AEGIS_DB", "aegis_triage.db"))
    parser.add_argument(
        "--audit-jsonl",
        type=str,
        default=os.getenv("AEGIS_AUDIT_JSONL", "aegis_audit.jsonl"),
    )
    parser.add_argument(
        "--policy",
        type=str,
        default=os.getenv("AEGIS_POLICY", "default"),
    )
    return parser.parse_args(argv)


def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Line {line_no} is not a JSON object")
            yield item


def run_demo(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — DEMO")
    for idx, (message, metadata, outcome) in enumerate(DEMO_CASES, start=1):
        print(f"[Demo Case {idx}/{len(DEMO_CASES)}]")
        record = engine.process(message, metadata=metadata)
        engine.log_outcome(record.case_id, outcome, reviewer_notes="demo outcome")
        print(f"Outcome logged : {outcome}\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_batch(engine: AegisTriageEngine, path: str) -> None:
    print_header(f"{BRAND_NAME.upper()} — BATCH MODE")
    processed = 0
    for item in iter_jsonl(path):
        message = str(item.get("message", "")).strip()
        metadata = item.get("metadata", {})
        if not message:
            continue
        engine.process(message, metadata if isinstance(metadata, dict) else {})
        processed += 1
    print(f"Processed {processed} records.\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_interactive(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — INTERACTIVE MODE")
    print("Enter a message, then press Enter.")
    print("Commands:")
    print("  /quit")
    print("  /summary")
    print("  /show <case_id>")
    print("  /outcome <case_id> <OUTCOME TEXT>")
    print()

    while True:
        try:
            raw = input("message> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if not raw:
            continue
        if raw == "/quit":
            break
        if raw == "/summary":
            print_summary(engine.summary(), calibration=engine.calibration())
            continue
        if raw.startswith("/show "):
            _, _, case_id = raw.partition(" ")
            record = engine.store.get(case_id.strip())
            if record is None:
                print("Case not found.")
            else:
                print_case(record)
            continue
        if raw.startswith("/outcome "):
            parts = raw.split(maxsplit=2)
            if len(parts) < 3:
                print("Usage: /outcome <case_id> <OUTCOME TEXT>")
                continue
            _, case_id, outcome = parts
            ok = engine.log_outcome(case_id, outcome, reviewer_notes="interactive outcome")
            print("Outcome recorded." if ok else "Case not found.")
            continue

        engine.process(raw, metadata={"channel": "interactive_console"})


# =============================================================================
# MAIN
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    engine = AegisTriageEngine(
        db_path=args.db,
        audit_jsonl_path=args.audit_jsonl,
        verbose=not args.quiet,
        policy_name=args.policy,
    )

    try:
        acted = False

        if args.print_concept:
            print_concept()
            acted = True

        if args.demo:
            run_demo(engine)
            acted = True

        if args.batch:
            run_batch(engine, args.batch)
            acted = True

        if args.interactive:
            run_interactive(engine)
            acted = True

        if args.summary:
            print_summary(engine.summary(), calibration=engine.calibration())
            acted = True

        if args.show_case:
            record = engine.store.get(args.show_case)
            if record is None:
                print(f"No case found for case_id={args.show_case}")
            else:
                print_case(record)
            acted = True

        if args.export_records:
            engine.export_records(args.export_records)
            print(f"Exported records to {args.export_records}")
            acted = True

        if not acted:
            print_header(f"{BRAND_NAME.upper()} — READY")
            print(BRAND_TAGLINE)
            print()
            print("No action selected. Try:")
            print("  --demo")
            print("  --interactive")
            print("  --batch cases.jsonl")
            print("  --summary")
            print("  --print-concept")
            print()

    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#### ChatGPT:
\==============================
MASTER LEDGER SNAPSHOT
======================

A-001 — Aegis Triage — AI / Agent System — Net Value: $12,000–$28,000

\[ASSET ID]

- A-001

\[NAME]

- Aegis Triage

\[TYPE]

- AI / Agent System

\[ORIGIN]

- Current chat
- Source input: single-file Python system prompt/prototype

\[FILES / SOURCES]

- aegis\_triage.py

\[DESCRIPTION]

- Single-file deterministic crisis triage research prototype with:
  - branded NIH SBIR concept layer
  - rule-based signal extraction
  - urgency scoring
  - routing logic
  - SQLite persistence
  - JSONL audit trail
  - CLI modes for demo, interactive, batch, summary, export
- It is a workflow-support prototype, not a deployable clinical product.

\[COMPONENTS]

- UI: CLI only
- Backend: local Python execution engine
- Logic: deterministic regex-based feature extraction and weighted scoring
- Data: SQLite case store + JSONL audit log
- Integration: local file I/O only
- Security: minimal, no auth, no encryption, no access control
- Evaluation: basic summary and calibration snapshot
- Product Layer: branding + grant framing

\[STATUS]

- partial

\[SCORING]

- Completeness: 3.5/5
- Execution: 4.0/5
- Novelty: 2.5/5
- Monetization: 2.5/5
- Readiness: 2.0/5

\[VALUE]

- Extractable: $20,000–$45,000
- Realistic: $12,000–$28,000
- Productized: $35,000–$90,000

\[OVERLAP]

- No prior Aegis-specific asset in this snapshot
- Internal overlap exists between grant framing and prototype wrapper, but not enough to discount materially

\[NET NEW VALUE]

- $12,000–$28,000

\[DEPENDENCIES]

- Clinical policy design
- Domain validation data
- Human reviewer workflow
- Security/compliance layer
- Deployment/API surface
- Evaluation dataset and benchmark process

\[BLOCKERS]

- No real-world validation
- No model training or calibrated supervised classifier
- No authentication, authorization, encryption, or tenant boundaries
- No web app, queueing, API, observability stack, or deployment infra
- No clinical governance layer
- No integration with actual hotline/call-center systems
- High regulatory and operational burden if pushed beyond research use

---

PORTFOLIO TOTAL

- Gross Value: $12,000–$28,000
- Net Realistic Value: $12,000–$28,000
- Productized Value: $35,000–$90,000

---

VALUE CHANGES

- Added: $12,000–$28,000

* Deducted: $0
  \= Net: $12,000–$28,000

---

TOP VALUE DRIVERS

- A-001 → It is not just concept text. It actually executes, stores records, logs outputs, and supports repeatable demo/batch workflows.
- A-001 → Deterministic scoring and auditability make it easier to pitch as a research/pilot prototype than an opaque model demo.
- A-001 → Packaging is better than average: branding, CLI, persistence, summaries, and concept framing are already combined.

---

VALUE LEAKS

- no production integration layer
- no security/compliance controls
- no clinical validation
- no customer workflow integration
- no actual trained model advantage
- no revenue proof
- single-file architecture helps demo speed but caps enterprise credibility

---

SYSTEM STRUCTURE

Core assets

- A-001 Aegis Triage core engine
  - feature extraction
  - urgency model
  - routing engine
  - persistence
  - audit
  - reporting
  - CLI

Supporting assets

- NIH SBIR concept framing embedded in file
- demo case corpus
- policy object and thresholds

Orphaned assets

- none inside this snapshot, but the commercialization story is not backed by deployment, pilots, or data assets

---

HARD TRUTH

What actually has value:

- The executable prototype.
- The deterministic scoring/routing structure.
- The persistence and audit trail.
- The fact that it is already framed as a pilot/research system rather than a toy sentiment script.

What is noise:

- The NIH/SBIR language by itself.
- Commercialization bullets without distribution, validation, or buyers.
- Any implication that this is clinically deployable.

What must be fixed to unlock next tier:

- Add an API/service layer.
- Add role-based access, encryption, and serious security controls.
- Add evaluation against a labeled dataset.
- Add policy versioning and reproducible benchmark reports.
- Add a reviewer dashboard or operational interface.
- Add integration points for real intake channels.
- Add governance language and validation workflow with clinical reviewers.

Bottom line:
This is a credible research prototype with packaging discipline, not a product company and not a production crisis platform. Today it is worth prototype money. With validation, interface, security, and deployment work, it can move into low-six-figure pilot territory. Without that, it stays a polished internal demo.


#### You:
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
═══════════════════════════════════════════════════════════════════════════════
AEGIS TRIAGE
Human-Guided Crisis Signal Intelligence Platform
NIH SBIR Research Prototype — Single-File Edition
═══════════════════════════════════════════════════════════════════════════════

OVERVIEW
--------
Aegis Triage is a research-oriented, human-guided crisis signal intelligence
prototype designed for:
- real-time crisis signal intake,
- explainable urgency estimation,
- policy-aware routing recommendations,
- operator review support,
- retrospective audit and evaluation.

This file intentionally combines:
1) SBIR-style concept framing
2) a functional deterministic prototype
3) storage, audit, and reporting utilities
4) a command-line interface for demo, batch, and interactive use

IMPORTANT
---------
This software is a research prototype for workflow support, evaluation,
simulation, and pilot design. It is not a substitute for licensed clinical
judgment, emergency response procedure, or approved crisis center policy.

DESIGN PRINCIPLES
-----------------
- human-guided, not human-replacing
- deterministic and explainable
- auditable and retrospective-ready
- conservative in uncertainty
- single-file deployable
- pilot-program friendly

EXAMPLES
--------
python aegis_triage.py --demo
python aegis_triage.py --interactive
python aegis_triage.py --batch cases.jsonl
python aegis_triage.py --summary
python aegis_triage.py --print-concept

OPTIONAL ENVIRONMENT VARIABLES
------------------------------
AEGIS_DB=aegis_triage.db
AEGIS_AUDIT_JSONL=aegis_audit.jsonl
AEGIS_POLICY=default
AEGIS_VERBOSE=true
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import statistics
import textwrap
import time
import hashlib
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# BRAND + CONCEPT LAYER
# =============================================================================

BRAND_NAME = "Aegis Triage"
BRAND_TAGLINE = "Human-Guided Crisis Signal Intelligence Platform"
BRAND_SHORT_DESCRIPTION = (
    "A deterministic, explainable, human-guided triage intelligence prototype "
    "for crisis workflows, research pilots, and operator decision support."
)

PROJECT_TITLE = f"{BRAND_NAME}: {BRAND_TAGLINE}"

PROJECT_SUMMARY = """
Crisis response environments, including 988-aligned operations, behavioral
health triage teams, telehealth intake, and emergency communication workflows,
must make high-stakes prioritization decisions under time pressure, incomplete
information, and variable staffing.

Aegis Triage is a human-guided crisis signal intelligence platform designed to
support those workflows with deterministic feature extraction, explainable
urgency estimation, policy-aware routing recommendations, and retrospective
auditability.

The system does not replace human judgment. Instead, it helps teams:
- identify salient crisis indicators,
- structure urgency review consistently,
- prioritize uncertain and high-risk cases conservatively,
- log decision context for quality assurance and research,
- create an evaluation pathway for future supervised model refinement.

The goal is to improve response consistency, transparency, timeliness, and
operational learning in crisis support environments.
""".strip()

SPECIFIC_AIMS = [
    "Build a real-time crisis signal intake and feature extraction pipeline.",
    "Develop an explainable, deterministic urgency estimation engine.",
    "Implement policy-aware routing recommendations with conservative safety rules.",
    "Create a feedback and retrospective analysis layer for continuous evaluation.",
]

SIGNIFICANCE = [
    "Improves consistency in high-pressure triage workflows.",
    "Preserves human authority while enhancing operator support.",
    "Creates auditable evidence for quality assurance and pilot review.",
    "Supports public-sector and healthcare-oriented AI operations modernization.",
]

INNOVATION = [
    "Explainable crisis signal intelligence rather than opaque scoring alone.",
    "Conservative uncertainty handling that escalates review rather than suppressing it.",
    "Policy-aware routing recommendations with explicit safety floors.",
    "Single-file deployable research architecture for rapid pilots and demos.",
]

TECHNICAL_RISKS = [
    "Ambiguous language may create uncertainty in urgency estimation.",
    "Metaphorical or quoted language may trigger false positives.",
    "Workflow misuse may occur if operators over-trust automated suggestions.",
    "Different channels and populations may require policy recalibration.",
]

RISK_MITIGATIONS = [
    "Route uncertain cases toward human review.",
    "Maintain deterministic logic and transparent feature contributions.",
    "Enforce conservative safety floors for self-harm and violence signals.",
    "Preserve full audit logs for calibration and incident review.",
]

COMMERCIALIZATION = [
    "Crisis hotline modernization pilots",
    "Behavioral health intake support systems",
    "Emergency communications decision-support tooling",
    "Healthcare operations intelligence infrastructure",
]

MILESTONES = [
    "Signal intake and feature extraction baseline",
    "Urgency estimation and policy routing baseline",
    "Audit logging and persistence layer",
    "Outcome tracking and retrospective reporting",
    "Pilot-readiness package for grant and procurement discussions",
]

BUDGET = {
    "engineering": 90000,
    "clinical_advisory": 35000,
    "security_and_compliance": 20000,
    "cloud_and_storage": 12000,
    "evaluation_and_pilot_support": 28000,
    "miscellaneous": 15000,
}


# =============================================================================
# UTILITY LAYER
# =============================================================================

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_case_id(message: str, timestamp: float) -> str:
    raw = f"{timestamp}|{message}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:16]
    return f"aegis_{digest}"


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compact_text(text: str, width: int = 88) -> str:
    text = " ".join(text.split())
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


# =============================================================================
# POLICY LAYER
# =============================================================================

@dataclass
class Policy:
    name: str = "default"

    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    low_confidence_threshold: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    emergency_route: str = "EMERGENCY_DISPATCH_RECOMMENDED"
    immediate_route: str = "IMMEDIATE_CLINICIAN_REVIEW"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "PRIORITY_QUEUE"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

    w_high_risk: float = 0.24
    w_medium_risk: float = 0.09
    w_plan: float = 0.22
    w_means: float = 0.16
    w_immediacy: float = 0.18
    w_self_harm: float = 0.26
    w_violence: float = 0.26
    w_distress: float = 0.10
    w_protective: float = -0.18
    w_help_seeking: float = -0.04
    w_negation_safety: float = -0.10
    w_short_signal: float = 0.08
    w_caps: float = 0.03
    w_punctuation: float = 0.03

    confidence_base: float = 0.50
    confidence_per_feature_group: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_metadata: float = 0.05

    require_human_review_for_high: bool = True
    route_low_confidence_to_human: bool = True
    preserve_self_harm_floor: bool = True
    preserve_violence_floor: bool = True


def load_policy(name: str = "default") -> Policy:
    return Policy(name=name)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class CrisisSignal:
    case_id: str
    timestamp: float
    created_at: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureSet:
    word_count: int
    char_count: int
    sentence_count: int
    uppercase_ratio: float
    exclamation_count: int
    question_count: int

    high_risk_hits: List[str] = field(default_factory=list)
    medium_risk_hits: List[str] = field(default_factory=list)
    plan_hits: List[str] = field(default_factory=list)
    means_hits: List[str] = field(default_factory=list)
    immediacy_hits: List[str] = field(default_factory=list)
    self_harm_hits: List[str] = field(default_factory=list)
    violence_hits: List[str] = field(default_factory=list)
    protective_hits: List[str] = field(default_factory=list)
    help_hits: List[str] = field(default_factory=list)
    negation_hits: List[str] = field(default_factory=list)
    ambiguity_hits: List[str] = field(default_factory=list)
    distress_hits: List[str] = field(default_factory=list)

    def total_hits(self) -> int:
        groups = [
            self.high_risk_hits,
            self.medium_risk_hits,
            self.plan_hits,
            self.means_hits,
            self.immediacy_hits,
            self.self_harm_hits,
            self.violence_hits,
            self.protective_hits,
            self.help_hits,
            self.negation_hits,
            self.ambiguity_hits,
            self.distress_hits,
        ]
        return sum(len(group) for group in groups)


@dataclass
class RiskAssessment:
    urgency: float
    confidence: float
    band: str
    reasons: List[str] = field(default_factory=list)
    contributions: Dict[str, float] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    priority: str
    route_to: str
    explanation: str
    requires_human_review: bool
    safety_flags: List[str] = field(default_factory=list)


@dataclass
class CaseRecord:
    case_id: str
    signal: CrisisSignal
    features: FeatureSet
    risk: RiskAssessment
    decision: RoutingDecision
    processing_ms: float
    outcome: Optional[str] = None
    reviewer_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "signal": asdict(self.signal),
            "features": asdict(self.features),
            "risk": asdict(self.risk),
            "decision": asdict(self.decision),
            "processing_ms": self.processing_ms,
            "outcome": self.outcome,
            "reviewer_notes": self.reviewer_notes,
        }


# =============================================================================
# FEATURE EXTRACTION LAYER
# =============================================================================

class SignalAnalyzer:
    """
    Deterministic language-pattern extractor for research prototypes.
    """

    HIGH_RISK = {
        r"\bi want to die\b": "want_to_die",
        r"\bend my life\b": "end_my_life",
        r"\bkill myself\b": "kill_myself",
        r"\bsuicide\b": "suicide",
        r"\bno reason to live\b": "no_reason_to_live",
        r"\bcan't go on\b": "cant_go_on",
        r"\boverdose\b": "overdose",
        r"\bhurt myself\b": "hurt_myself",
        r"\bself harm\b": "self_harm",
    }

    MEDIUM_RISK = {
        r"\bhopeless\b": "hopeless",
        r"\bpanic\b": "panic",
        r"\bdesperate\b": "desperate",
        r"\boverwhelmed\b": "overwhelmed",
        r"\bscared\b": "scared",
        r"\bafraid\b": "afraid",
        r"\bbreaking down\b": "breaking_down",
        r"\bin crisis\b": "in_crisis",
        r"\balone\b": "alone",
    }

    PLAN = {
        r"\bi have a plan\b": "have_a_plan",
        r"\bplanned\b": "planned",
        r"\bi know how\b": "know_how",
        r"\btonight\b": "tonight",
        r"\bafter everyone sleeps\b": "after_everyone_sleeps",
    }

    MEANS = {
        r"\bpills\b": "pills",
        r"\bgun\b": "gun",
        r"\bknife\b": "knife",
        r"\brope\b": "rope",
        r"\bweapon\b": "weapon",
        r"\brazor\b": "razor",
    }

    IMMEDIACY = {
        r"\bnow\b": "now",
        r"\bright now\b": "right_now",
        r"\btoday\b": "today",
        r"\btonight\b": "tonight",
        r"\bimmediately\b": "immediately",
        r"\bsoon\b": "soon",
    }

    SELF_HARM = {
        r"\bhurt myself\b": "hurt_myself",
        r"\bcut myself\b": "cut_myself",
        r"\bself harm\b": "self_harm",
        r"\bkill myself\b": "kill_myself",
        r"\bend my life\b": "end_my_life",
    }

    VIOLENCE = {
        r"\bhurt someone\b": "hurt_someone",
        r"\bkill them\b": "kill_them",
        r"\bshoot\b": "shoot",
        r"\bstab\b": "stab",
        r"\bviolent\b": "violent",
        r"\bweapon\b": "weapon",
    }

    PROTECTIVE = {
        r"\bi am safe\b": "i_am_safe",
        r"\bi'm safe\b": "i_am_safe",
        r"\bi won't do anything\b": "wont_do_anything",
        r"\bi do not want to die\b": "do_not_want_to_die",
        r"\bi don't want to die\b": "do_not_want_to_die",
        r"\bi am with someone\b": "with_someone",
        r"\bi'm with someone\b": "with_someone",
        r"\bmy therapist\b": "therapist",
        r"\bmy counselor\b": "counselor",
    }

    HELP = {
        r"\bplease help\b": "please_help",
        r"\bneed help\b": "need_help",
        r"\bi need to talk\b": "need_to_talk",
        r"\bcan someone talk\b": "someone_talk",
        r"\blooking for support\b": "support",
    }

    NEGATION = {
        r"\bnot suicidal\b": "not_suicidal",
        r"\bnot going to hurt myself\b": "not_hurt_self",
        r"\bnot going to kill myself\b": "not_kill_self",
        r"\bno plan\b": "no_plan",
        r"\bno intent\b": "no_intent",
    }

    AMBIGUITY = {
        r"\bjust kidding\b": "just_kidding",
        r"\bfiguratively\b": "figuratively",
        r"\bquote\b": "quote",
        r"\bsong lyric\b": "song_lyric",
        r"\bmetaphor\b": "metaphor",
    }

    DISTRESS = {
        r"\bcan't\b": "cant",
        r"\bnever\b": "never",
        r"\balways\b": "always",
        r"\bno one\b": "no_one",
        r"\bnobody\b": "nobody",
        r"\bi'm done\b": "im_done",
        r"\bi am done\b": "im_done",
    }

    @staticmethod
    def _hits(text: str, patterns: Dict[str, str]) -> List[str]:
        found: List[str] = []
        for pattern, label in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.append(label)
        return sorted(set(found))

    @staticmethod
    def _sentence_count(text: str) -> int:
        parts = [p.strip() for p in re.split(r"[.!?]+", text) if p.strip()]
        return max(1, len(parts))

    @staticmethod
    def _uppercase_ratio(text: str) -> float:
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        uppercase = sum(1 for c in letters if c.isupper())
        return round(uppercase / len(letters), 4)

    def analyze(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[CrisisSignal, FeatureSet]:
        timestamp = time.time()
        case_id = make_case_id(message, timestamp)
        signal = CrisisSignal(
            case_id=case_id,
            timestamp=timestamp,
            created_at=now_utc_iso(),
            message=message,
            metadata=dict(metadata or {}),
        )

        lower = message.lower()
        features = FeatureSet(
            word_count=len(message.split()),
            char_count=len(message),
            sentence_count=self._sentence_count(message),
            uppercase_ratio=self._uppercase_ratio(message),
            exclamation_count=message.count("!"),
            question_count=message.count("?"),
            high_risk_hits=self._hits(lower, self.HIGH_RISK),
            medium_risk_hits=self._hits(lower, self.MEDIUM_RISK),
            plan_hits=self._hits(lower, self.PLAN),
            means_hits=self._hits(lower, self.MEANS),
            immediacy_hits=self._hits(lower, self.IMMEDIACY),
            self_harm_hits=self._hits(lower, self.SELF_HARM),
            violence_hits=self._hits(lower, self.VIOLENCE),
            protective_hits=self._hits(lower, self.PROTECTIVE),
            help_hits=self._hits(lower, self.HELP),
            negation_hits=self._hits(lower, self.NEGATION),
            ambiguity_hits=self._hits(lower, self.AMBIGUITY),
            distress_hits=self._hits(lower, self.DISTRESS),
        )

        signal.metadata.update(
            {
                "word_count": features.word_count,
                "char_count": features.char_count,
                "sentence_count": features.sentence_count,
                "uppercase_ratio": features.uppercase_ratio,
                "exclamation_count": features.exclamation_count,
                "question_count": features.question_count,
            }
        )
        return signal, features


# =============================================================================
# RISK LAYER
# =============================================================================

class UrgencyModel:
    def __init__(self, policy: Policy):
        self.policy = policy

    def assess(self, signal: CrisisSignal, features: FeatureSet) -> RiskAssessment:
        contributions: Dict[str, float] = {}
        reasons: List[str] = []

        base = min(0.18, features.word_count / 300.0)
        contributions["base_text_density"] = round(base, 4)

        def add_if_nonzero(name: str, value: float) -> None:
            if value:
                contributions[name] = round(value, 4)

        high = len(features.high_risk_hits) * self.policy.w_high_risk
        medium = len(features.medium_risk_hits) * self.policy.w_medium_risk
        plan = len(features.plan_hits) * self.policy.w_plan
        means = len(features.means_hits) * self.policy.w_means
        immediacy = len(features.immediacy_hits) * self.policy.w_immediacy
        self_harm = len(features.self_harm_hits) * self.policy.w_self_harm
        violence = len(features.violence_hits) * self.policy.w_violence
        distress = len(features.distress_hits) * self.policy.w_distress
        protective = len(features.protective_hits) * self.policy.w_protective
        help_signal = len(features.help_hits) * self.policy.w_help_seeking
        negation = len(features.negation_hits) * self.policy.w_negation_safety

        add_if_nonzero("high_risk", high)
        add_if_nonzero("medium_risk", medium)
        add_if_nonzero("plan", plan)
        add_if_nonzero("means", means)
        add_if_nonzero("immediacy", immediacy)
        add_if_nonzero("self_harm", self_harm)
        add_if_nonzero("violence", violence)
        add_if_nonzero("distress", distress)
        add_if_nonzero("protective", protective)
        add_if_nonzero("help_seeking", help_signal)
        add_if_nonzero("negation", negation)

        if features.high_risk_hits:
            reasons.append(f"high-risk indicators: {', '.join(features.high_risk_hits)}")
        if features.medium_risk_hits:
            reasons.append(f"distress indicators: {', '.join(features.medium_risk_hits)}")
        if features.plan_hits:
            reasons.append(f"plan indicators: {', '.join(features.plan_hits)}")
        if features.means_hits:
            reasons.append(f"means indicators: {', '.join(features.means_hits)}")
        if features.immediacy_hits:
            reasons.append(f"time/immediacy indicators: {', '.join(features.immediacy_hits)}")
        if features.self_harm_hits:
            reasons.append(f"self-harm indicators: {', '.join(features.self_harm_hits)}")
        if features.violence_hits:
            reasons.append(f"violence indicators: {', '.join(features.violence_hits)}")
        if features.protective_hits:
            reasons.append(f"protective factors: {', '.join(features.protective_hits)}")
        if features.help_hits:
            reasons.append(f"help-seeking language: {', '.join(features.help_hits)}")

        short_signal = 0.0
        if features.word_count <= 3 and (
            features.high_risk_hits
            or features.medium_risk_hits
            or features.help_hits
            or features.self_harm_hits
        ):
            short_signal = self.policy.w_short_signal
            contributions["short_signal"] = round(short_signal, 4)
            reasons.append("very short message with meaningful crisis/help signal")

        emphasis = 0.0
        if features.uppercase_ratio >= 0.35:
            emphasis += self.policy.w_caps
        if features.exclamation_count >= 2:
            emphasis += self.policy.w_punctuation
        add_if_nonzero("emphasis", emphasis)

        urgency_raw = (
            base
            + high
            + medium
            + plan
            + means
            + immediacy
            + self_harm
            + violence
            + distress
            + protective
            + help_signal
            + negation
            + short_signal
            + emphasis
        )

        if features.self_harm_hits and self.policy.preserve_self_harm_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["self_harm_floor"] = 0.72

        if features.violence_hits and self.policy.preserve_violence_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["violence_floor"] = 0.72

        urgency = clamp01(urgency_raw)

        feature_groups = sum(
            1 for group in [
                features.high_risk_hits,
                features.medium_risk_hits,
                features.plan_hits,
                features.means_hits,
                features.immediacy_hits,
                features.self_harm_hits,
                features.violence_hits,
                features.protective_hits,
                features.help_hits,
                features.negation_hits,
                features.ambiguity_hits,
                features.distress_hits,
            ] if group
        )

        confidence = self.policy.confidence_base
        confidence += feature_groups * self.policy.confidence_per_feature_group
        confidence += min(4, features.total_hits()) * self.policy.confidence_per_signal_density

        if features.ambiguity_hits:
            confidence -= self.policy.confidence_penalty_ambiguity
            reasons.append(f"ambiguity markers: {', '.join(features.ambiguity_hits)}")

        if features.word_count <= 2:
            confidence -= self.policy.confidence_penalty_too_short
            reasons.append("extremely short input lowers confidence")

        if signal.metadata:
            confidence += self.policy.confidence_bonus_metadata

        confidence = clamp01(confidence)

        if urgency >= self.policy.critical_threshold:
            band = "CRITICAL"
        elif urgency >= self.policy.high_threshold:
            band = "HIGH"
        elif urgency >= self.policy.medium_threshold:
            band = "MEDIUM"
        else:
            band = "LOW"

        if not reasons:
            reasons.append("limited direct risk language; estimate driven by general signal density")

        return RiskAssessment(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            band=band,
            reasons=reasons,
            contributions=contributions,
        )


# =============================================================================
# DECISION LAYER
# =============================================================================

class RoutingEngine:
    def __init__(self, policy: Policy):
        self.policy = policy

    def decide(self, features: FeatureSet, risk: RiskAssessment) -> RoutingDecision:
        flags: List[str] = []
        low_confidence = risk.confidence < self.policy.low_confidence_threshold
        self_harm_present = bool(features.self_harm_hits or features.high_risk_hits)
        violence_present = bool(features.violence_hits)

        if self_harm_present:
            flags.append("SELF_HARM_SIGNAL")
        if violence_present:
            flags.append("VIOLENCE_SIGNAL")
        if features.plan_hits:
            flags.append("PLAN_INDICATOR")
        if features.means_hits:
            flags.append("MEANS_INDICATOR")
        if low_confidence:
            flags.append("LOW_CONFIDENCE")

        if risk.urgency >= self.policy.critical_threshold:
            priority = "CRITICAL"
            route = self.policy.emergency_route
            review = True
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds critical threshold "
                f"{self.policy.critical_threshold:.2f}; emergency-aligned escalation is recommended."
            )
        elif risk.urgency >= self.policy.high_threshold:
            priority = "HIGH"
            route = self.policy.immediate_route
            review = self.policy.require_human_review_for_high
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds high threshold "
                f"{self.policy.high_threshold:.2f}; immediate clinician review is recommended."
            )
        elif risk.urgency >= self.policy.medium_threshold:
            priority = "MEDIUM"
            route = self.policy.priority_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds medium threshold "
                f"{self.policy.medium_threshold:.2f}; priority handling is recommended."
            )
        else:
            priority = "LOW"
            route = self.policy.standard_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} is below medium threshold; "
                f"standard queue placement is recommended."
            )

        if low_confidence and self.policy.route_low_confidence_to_human:
            route = self.policy.mandatory_review_route
            review = True
            explanation += " Confidence is limited, so human review is required."

        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = self.policy.urgent_review_route
            review = True
            explanation += " High-risk plus uncertainty triggers urgent human review."

        if self_harm_present and priority == "LOW":
            priority = "MEDIUM"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Self-harm language prevents a low-priority disposition."

        if violence_present and priority in {"LOW", "MEDIUM"}:
            priority = "HIGH"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Violence language elevates the case for urgent review."

        return RoutingDecision(
            priority=priority,
            route_to=route,
            explanation=explanation,
            requires_human_review=review,
            safety_flags=flags,
        )


# =============================================================================
# STORAGE LAYER
# =============================================================================

class CaseStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_records (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                timestamp REAL NOT NULL,
                message TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                features_json TEXT NOT NULL,
                risk_json TEXT NOT NULL,
                decision_json TEXT NOT NULL,
                processing_ms REAL NOT NULL,
                outcome TEXT,
                reviewer_notes TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                reviewer_notes TEXT,
                recorded_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_case_outcomes_case_id ON case_outcomes(case_id)"
        )
        self.conn.commit()

    def save(self, record: CaseRecord) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO case_records (
                case_id, created_at, timestamp, message, metadata_json,
                features_json, risk_json, decision_json, processing_ms,
                outcome, reviewer_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.case_id,
                record.signal.created_at,
                record.signal.timestamp,
                record.signal.message,
                json.dumps(record.signal.metadata, ensure_ascii=False),
                json.dumps(asdict(record.features), ensure_ascii=False),
                json.dumps(asdict(record.risk), ensure_ascii=False),
                json.dumps(asdict(record.decision), ensure_ascii=False),
                record.processing_ms,
                record.outcome,
                record.reviewer_notes,
            ),
        )
        self.conn.commit()

    def set_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE case_records
            SET outcome = ?, reviewer_notes = ?
            WHERE case_id = ?
            """,
            (outcome, reviewer_notes, case_id),
        )
        updated = cur.rowcount > 0
        cur.execute(
            """
            INSERT INTO case_outcomes (case_id, outcome, reviewer_notes, recorded_at)
            VALUES (?, ?, ?, ?)
            """,
            (case_id, outcome, reviewer_notes, now_utc_iso()),
        )
        self.conn.commit()
        return updated

    def get(self, case_id: str) -> Optional[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM case_records WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_recent(self, limit: int = 1000) -> List[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM case_records ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row: sqlite3.Row) -> CaseRecord:
        signal = CrisisSignal(
            case_id=row["case_id"],
            timestamp=row["timestamp"],
            created_at=row["created_at"],
            message=row["message"],
            metadata=json.loads(row["metadata_json"]),
        )
        features = FeatureSet(**json.loads(row["features_json"]))
        risk = RiskAssessment(**json.loads(row["risk_json"]))
        decision = RoutingDecision(**json.loads(row["decision_json"]))
        return CaseRecord(
            case_id=row["case_id"],
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=row["processing_ms"],
            outcome=row["outcome"],
            reviewer_notes=row["reviewer_notes"],
        )

    def close(self) -> None:
        self.conn.close()


# =============================================================================
# AUDIT LAYER
# =============================================================================

class AuditTrail:
    def __init__(self, jsonl_path: str, verbose: bool = True):
        self.jsonl_path = jsonl_path
        self.verbose = verbose
        self._entries: List[Dict[str, Any]] = []

    def log(self, record: CaseRecord) -> None:
        entry = record.to_dict()
        self._entries.append(entry)

        with open(self.jsonl_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if self.verbose:
            self._print(record)

    def _print(self, record: CaseRecord) -> None:
        print("┌" + "─" * 78)
        print(f"│ BRAND        : {BRAND_NAME}")
        print(f"│ CASE ID      : {record.case_id}")
        print(f"│ MESSAGE      : {compact_text(record.signal.message)}")
        print(f"│ URGENCY      : {record.risk.urgency:.4f}    CONFIDENCE: {record.risk.confidence:.4f}")
        print(f"│ BAND         : {record.risk.band}")
        print(f"│ PRIORITY     : {record.decision.priority:<12} ROUTE: {record.decision.route_to}")
        print(f"│ HUMAN REVIEW : {record.decision.requires_human_review}")
        print(f"│ FLAGS        : {', '.join(record.decision.safety_flags) if record.decision.safety_flags else 'None'}")
        print(f"│ REASONS      : {compact_text('; '.join(record.risk.reasons[:3]), 70)}")
        print(f"│ LATENCY      : {record.processing_ms:.2f} ms")
        print("└" + "─" * 78)

    def export_json(self) -> str:
        return json.dumps(self._entries, indent=2, ensure_ascii=False)


# =============================================================================
# FEEDBACK + REPORTING LAYER
# =============================================================================

class ReviewLoop:
    def __init__(self, store: CaseStore):
        self.store = store

    def record_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.store.set_outcome(case_id, outcome, reviewer_notes)

    def summary(self, limit: int = 5000) -> Dict[str, Any]:
        records = self.store.list_recent(limit=limit)
        if not records:
            return {"records": 0}

        urgencies = [r.risk.urgency for r in records]
        confidences = [r.risk.confidence for r in records]
        priorities = [r.decision.priority for r in records]
        routes = [r.decision.route_to for r in records]
        outcomes = [r.outcome for r in records if r.outcome]

        return {
            "brand": BRAND_NAME,
            "records": len(records),
            "avg_urgency": round(statistics.mean(urgencies), 4),
            "max_urgency": round(max(urgencies), 4),
            "avg_confidence": round(statistics.mean(confidences), 4),
            "human_review_rate": round(
                sum(1 for r in records if r.decision.requires_human_review) / len(records), 4
            ),
            "band_distribution": dict(Counter(r.risk.band for r in records)),
            "priority_distribution": dict(Counter(priorities)),
            "route_distribution": dict(Counter(routes)),
            "outcomes_logged": len(outcomes),
            "outcome_distribution": dict(Counter(outcomes)),
        }

    def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
        records = [r for r in self.store.list_recent(limit=limit) if r.outcome]
        if not records:
            return {"records_with_outcomes": 0, "buckets": {}}

        buckets = {
            "0.00-0.39": [],
            "0.40-0.64": [],
            "0.65-0.84": [],
            "0.85-1.00": [],
        }

        for record in records:
            u = record.risk.urgency
            if u < 0.40:
                buckets["0.00-0.39"].append(record.outcome or "UNKNOWN")
            elif u < 0.65:
                buckets["0.40-0.64"].append(record.outcome or "UNKNOWN")
            elif u < 0.85:
                buckets["0.65-0.84"].append(record.outcome or "UNKNOWN")
            else:
                buckets["0.85-1.00"].append(record.outcome or "UNKNOWN")

        return {
            "records_with_outcomes": len(records),
            "buckets": {k: dict(Counter(v)) for k, v in buckets.items()},
        }


# =============================================================================
# ORCHESTRATION LAYER
# =============================================================================

class AegisTriageEngine:
    def __init__(
        self,
        db_path: str,
        audit_jsonl_path: str,
        verbose: bool = True,
        policy_name: str = "default",
    ):
        self.policy = load_policy(policy_name)
        self.analyzer = SignalAnalyzer()
        self.urgency_model = UrgencyModel(self.policy)
        self.routing_engine = RoutingEngine(self.policy)
        self.store = CaseStore(db_path)
        self.audit = AuditTrail(audit_jsonl_path, verbose=verbose)
        self.review = ReviewLoop(self.store)

    def process(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> CaseRecord:
        start = time.perf_counter()

        signal, features = self.analyzer.analyze(message, metadata=metadata)
        risk = self.urgency_model.assess(signal, features)
        decision = self.routing_engine.decide(features, risk)

        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 3)

        record = CaseRecord(
            case_id=signal.case_id,
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=elapsed_ms,
        )

        self.store.save(record)
        self.audit.log(record)
        return record

    def log_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.review.record_outcome(case_id, outcome, reviewer_notes)

    def export_records(self, path: str, limit: int = 5000) -> None:
        payload = [r.to_dict() for r in self.store.list_recent(limit=limit)]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    def summary(self) -> Dict[str, Any]:
        return self.review.summary()

    def calibration(self) -> Dict[str, Any]:
        return self.review.calibration_snapshot()

    def close(self) -> None:
        self.store.close()


# =============================================================================
# PRESENTATION LAYER
# =============================================================================

def print_header(title: str) -> None:
    print("\n" + "═" * 80)
    print(title)
    print("═" * 80 + "\n")


def print_concept() -> None:
    print_header(f"{BRAND_NAME.upper()} — SBIR RESEARCH CONCEPT")
    sections = {
        "TITLE": PROJECT_TITLE,
        "BRAND DESCRIPTION": BRAND_SHORT_DESCRIPTION,
        "PROJECT SUMMARY": PROJECT_SUMMARY,
        "SPECIFIC AIMS": SPECIFIC_AIMS,
        "SIGNIFICANCE": SIGNIFICANCE,
        "INNOVATION": INNOVATION,
        "TECHNICAL RISKS": TECHNICAL_RISKS,
        "RISK MITIGATIONS": RISK_MITIGATIONS,
        "COMMERCIALIZATION": COMMERCIALIZATION,
        "MILESTONES": MILESTONES,
        "BUDGET": BUDGET,
    }

    for name, value in sections.items():
        print(name)
        print("-" * len(name))
        if isinstance(value, str):
            print(textwrap.fill(value, width=88))
        elif isinstance(value, dict):
            for k, v in value.items():
                print(f"  - {k}: ${v:,.0f}")
        else:
            for item in value:
                print(f"  - {item}")
        print()


def print_summary(summary: Dict[str, Any], calibration: Optional[Dict[str, Any]] = None) -> None:
    print_header(f"{BRAND_NAME.upper()} — SUMMARY")
    for key, value in summary.items():
        print(f"{key:>24} : {value}")
    if calibration is not None:
        print("\nCALIBRATION SNAPSHOT")
        print("--------------------")
        for key, value in calibration.items():
            print(f"{key:>24} : {value}")
    print()


def print_case(record: CaseRecord) -> None:
    print_header(f"{BRAND_NAME.upper()} — CASE DETAIL")
    print(f"Case ID         : {record.case_id}")
    print(f"Created at      : {record.signal.created_at}")
    print(f"Message         : {record.signal.message}")
    print(f"Metadata        : {json.dumps(record.signal.metadata, ensure_ascii=False)}")
    print()
    print("FEATURES")
    print("--------")
    print(json.dumps(asdict(record.features), indent=2, ensure_ascii=False))
    print()
    print("RISK")
    print("----")
    print(json.dumps(asdict(record.risk), indent=2, ensure_ascii=False))
    print()
    print("DECISION")
    print("--------")
    print(json.dumps(asdict(record.decision), indent=2, ensure_ascii=False))
    print()
    print(f"Processing ms   : {record.processing_ms}")
    print(f"Outcome         : {record.outcome}")
    print(f"Reviewer notes  : {record.reviewer_notes}")
    print()


# =============================================================================
# DEMO CASES
# =============================================================================

DEMO_CASES: List[Tuple[str, Dict[str, Any], str]] = [
    (
        "I've been feeling a little down lately and just needed to talk.",
        {"channel": "chat", "source": "demo"},
        "RESOLVED_SUPPORTIVE_CONTACT",
    ),
    (
        "I don't know how much longer I can handle this. I feel completely overwhelmed and scared.",
        {"channel": "chat", "source": "demo"},
        "COUNSELOR_FOLLOW_UP",
    ),
    (
        "I'm in crisis right now. I feel hopeless and desperate. Please help me.",
        {"channel": "voice", "source": "demo"},
        "IMMEDIATE_CLINICIAN_CONTACT",
    ),
    (
        "I want to end my life tonight. I have a plan and I don't see any reason to go on.",
        {"channel": "chat", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
    (
        "help",
        {"channel": "sms", "source": "demo"},
        "MONITORED_AND_ENGAGED",
    ),
    (
        "Not suicidal. No plan. I am safe, but I really need to talk to someone tonight because I'm panicking.",
        {"channel": "chat", "source": "demo"},
        "URGENT_SUPPORT_CONTACT",
    ),
    (
        "I have pills and I think tonight is the night.",
        {"channel": "sms", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
]


# =============================================================================
# CLI LAYER
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{BRAND_NAME} — single-file research prototype"
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demonstration cases")
    parser.add_argument("--interactive", action="store_true", help="Run interactive console mode")
    parser.add_argument("--batch", type=str, help="Process a JSONL batch file")
    parser.add_argument("--summary", action="store_true", help="Print stored summary")
    parser.add_argument("--show-case", type=str, help="Show stored case by case_id")
    parser.add_argument("--export-records", type=str, help="Export records to JSON")
    parser.add_argument("--print-concept", action="store_true", help="Print concept package")
    parser.add_argument("--quiet", action="store_true", help="Reduce console output")
    parser.add_argument("--db", type=str, default=os.getenv("AEGIS_DB", "aegis_triage.db"))
    parser.add_argument(
        "--audit-jsonl",
        type=str,
        default=os.getenv("AEGIS_AUDIT_JSONL", "aegis_audit.jsonl"),
    )
    parser.add_argument(
        "--policy",
        type=str,
        default=os.getenv("AEGIS_POLICY", "default"),
    )
    return parser.parse_args(argv)


def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Line {line_no} is not a JSON object")
            yield item


def run_demo(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — DEMO")
    for idx, (message, metadata, outcome) in enumerate(DEMO_CASES, start=1):
        print(f"[Demo Case {idx}/{len(DEMO_CASES)}]")
        record = engine.process(message, metadata=metadata)
        engine.log_outcome(record.case_id, outcome, reviewer_notes="demo outcome")
        print(f"Outcome logged : {outcome}\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_batch(engine: AegisTriageEngine, path: str) -> None:
    print_header(f"{BRAND_NAME.upper()} — BATCH MODE")
    processed = 0
    for item in iter_jsonl(path):
        message = str(item.get("message", "")).strip()
        metadata = item.get("metadata", {})
        if not message:
            continue
        engine.process(message, metadata if isinstance(metadata, dict) else {})
        processed += 1
    print(f"Processed {processed} records.\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_interactive(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — INTERACTIVE MODE")
    print("Enter a message, then press Enter.")
    print("Commands:")
    print("  /quit")
    print("  /summary")
    print("  /show <case_id>")
    print("  /outcome <case_id> <OUTCOME TEXT>")
    print()

    while True:
        try:
            raw = input("message> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if not raw:
            continue
        if raw == "/quit":
            break
        if raw == "/summary":
            print_summary(engine.summary(), calibration=engine.calibration())
            continue
        if raw.startswith("/show "):
            _, _, case_id = raw.partition(" ")
            record = engine.store.get(case_id.strip())
            if record is None:
                print("Case not found.")
            else:
                print_case(record)
            continue
        if raw.startswith("/outcome "):
            parts = raw.split(maxsplit=2)
            if len(parts) < 3:
                print("Usage: /outcome <case_id> <OUTCOME TEXT>")
                continue
            _, case_id, outcome = parts
            ok = engine.log_outcome(case_id, outcome, reviewer_notes="interactive outcome")
            print("Outcome recorded." if ok else "Case not found.")
            continue

        engine.process(raw, metadata={"channel": "interactive_console"})


# =============================================================================
# MAIN
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    engine = AegisTriageEngine(
        db_path=args.db,
        audit_jsonl_path=args.audit_jsonl,
        verbose=not args.quiet,
        policy_name=args.policy,
    )

    try:
        acted = False

        if args.print_concept:
            print_concept()
            acted = True

        if args.demo:
            run_demo(engine)
            acted = True

        if args.batch:
            run_batch(engine, args.batch)
            acted = True

        if args.interactive:
            run_interactive(engine)
            acted = True

        if args.summary:
            print_summary(engine.summary(), calibration=engine.calibration())
            acted = True

        if args.show_case:
            record = engine.store.get(args.show_case)
            if record is None:
                print(f"No case found for case_id={args.show_case}")
            else:
                print_case(record)
            acted = True

        if args.export_records:
            engine.export_records(args.export_records)
            print(f"Exported records to {args.export_records}")
            acted = True

        if not acted:
            print_header(f"{BRAND_NAME.upper()} — READY")
            print(BRAND_TAGLINE)
            print()
            print("No action selected. Try:")
            print("  --demo")
            print("  --interactive")
            print("  --batch cases.jsonl")
            print("  --summary")
            print("  --print-concept")
            print()

    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main()) ==============================
MASTER LEDGER SNAPSHOT

A-001 — Aegis Triage — AI / Agent System — Net Value: $12,000–$28,000

[ASSET ID]
	•	A-001

[NAME]
	•	Aegis Triage

[TYPE]
	•	AI / Agent System

[ORIGIN]
	•	Current chat
	•	Source input: single-file Python system prompt/prototype

[FILES / SOURCES]
	•	aegis_triage.py

[DESCRIPTION]
	•	Single-file deterministic crisis triage research prototype with:
	•	branded NIH SBIR concept layer
	•	rule-based signal extraction
	•	urgency scoring
	•	routing logic
	•	SQLite persistence
	•	JSONL audit trail
	•	CLI modes for demo, interactive, batch, summary, export
	•	It is a workflow-support prototype, not a deployable clinical product.

[COMPONENTS]
	•	UI: CLI only
	•	Backend: local Python execution engine
	•	Logic: deterministic regex-based feature extraction and weighted scoring
	•	Data: SQLite case store + JSONL audit log
	•	Integration: local file I/O only
	•	Security: minimal, no auth, no encryption, no access control
	•	Evaluation: basic summary and calibration snapshot
	•	Product Layer: branding + grant framing

[STATUS]
	•	partial

[SCORING]
	•	Completeness: 3.5/5
	•	Execution: 4.0/5
	•	Novelty: 2.5/5
	•	Monetization: 2.5/5
	•	Readiness: 2.0/5

[VALUE]
	•	Extractable: $20,000–$45,000
	•	Realistic: $12,000–$28,000
	•	Productized: $35,000–$90,000

[OVERLAP]
	•	No prior Aegis-specific asset in this snapshot
	•	Internal overlap exists between grant framing and prototype wrapper, but not enough to discount materially

[NET NEW VALUE]
	•	$12,000–$28,000

[DEPENDENCIES]
	•	Clinical policy design
	•	Domain validation data
	•	Human reviewer workflow
	•	Security/compliance layer
	•	Deployment/API surface
	•	Evaluation dataset and benchmark process

[BLOCKERS]
	•	No real-world validation
	•	No model training or calibrated supervised classifier
	•	No authentication, authorization, encryption, or tenant boundaries
	•	No web app, queueing, API, observability stack, or deployment infra
	•	No clinical governance layer
	•	No integration with actual hotline/call-center systems
	•	High regulatory and operational burden if pushed beyond research use

⸻

PORTFOLIO TOTAL
	•	Gross Value: $12,000–$28,000
	•	Net Realistic Value: $12,000–$28,000
	•	Productized Value: $35,000–$90,000

⸻

VALUE CHANGES
	•	Added: $12,000–$28,000

	•	Deducted: $0
= Net: $12,000–$28,000

⸻

TOP VALUE DRIVERS
	•	A-001 → It is not just concept text. It actually executes, stores records, logs outputs, and supports repeatable demo/batch workflows.
	•	A-001 → Deterministic scoring and auditability make it easier to pitch as a research/pilot prototype than an opaque model demo.
	•	A-001 → Packaging is better than average: branding, CLI, persistence, summaries, and concept framing are already combined.

⸻

VALUE LEAKS
	•	no production integration layer
	•	no security/compliance controls
	•	no clinical validation
	•	no customer workflow integration
	•	no actual trained model advantage
	•	no revenue proof
	•	single-file architecture helps demo speed but caps enterprise credibility

⸻

SYSTEM STRUCTURE

Core assets
	•	A-001 Aegis Triage core engine
	•	feature extraction
	•	urgency model
	•	routing engine
	•	persistence
	•	audit
	•	reporting
	•	CLI

Supporting assets
	•	NIH SBIR concept framing embedded in file
	•	demo case corpus
	•	policy object and thresholds

Orphaned assets
	•	none inside this snapshot, but the commercialization story is not backed by deployment, pilots, or data assets

⸻

HARD TRUTH

What actually has value:
	•	The executable prototype.
	•	The deterministic scoring/routing structure.
	•	The persistence and audit trail.
	•	The fact that it is already framed as a pilot/research system rather than a toy sentiment script.

What is noise:
	•	The NIH/SBIR language by itself.
	•	Commercialization bullets without distribution, validation, or buyers.
	•	Any implication that this is clinically deployable.

What must be fixed to unlock next tier:
	•	Add an API/service layer.
	•	Add role-based access, encryption, and serious security controls.
	•	Add evaluation against a labeled dataset.
	•	Add policy versioning and reproducible benchmark reports.
	•	Add a reviewer dashboard or operational interface.
	•	Add integration points for real intake channels.
	•	Add governance language and validation workflow with clinical reviewers.

Bottom line:
This is a credible research prototype with packaging discipline, not a product company and not a production crisis platform. Today it is worth prototype money. With validation, interface, security, and deployment work, it can move into low-six-figure pilot territory. Without that, it stays a polished internal demo.

#### ChatGPT:
\==============================
MASTER LEDGER SNAPSHOT
======================

A-001 — Aegis Triage — AI / Agent System — Net Value: $10,000–$25,000

\[ASSET ID]

- A-001

\[NAME]

- Aegis Triage

\[TYPE]

- AI / Agent System

\[ORIGIN]

- Current chat
- Single-file Python prototype

\[FILES / SOURCES]

- aegis\_triage.py

\[DESCRIPTION]

- Deterministic crisis-triage research prototype combining:
  - rule-based feature extraction
  - weighted urgency scoring
  - policy-based routing
  - SQLite persistence
  - JSONL audit logging
  - CLI demo / batch / interactive flows
  - embedded NIH SBIR positioning copy

\[STATUS]

- partial

\[COMPONENTS]

- Interface: CLI only
- Logic: regex/rule-based scoring and routing
- Persistence: SQLite + JSONL
- Evaluation: basic summary and bucketed calibration snapshot
- Integration: none beyond local file I/O
- Security: absent beyond local execution
- Deployment: absent
- Governance: concept only

\[SCORING]

- Completeness: 3.5/5
- Execution Capability: 4.0/5
- Novelty: 2.0/5
- Monetization Potential: 2.5/5
- Production Readiness: 1.5/5

\[VALUE]

- Extractable Value: $18,000–$40,000
- Realistic Buyer Value: $10,000–$25,000
- Productized Value: $30,000–$80,000

\[OVERLAP]

- 0% external overlap in this snapshot
- Internal overlap between concept copy and executable asset is non-billable wrapper value, not a separate asset

\[NET NEW VALUE]

- $10,000–$25,000

\[DEPENDENCIES]

- labeled evaluation data
- policy versioning
- reviewer workflow
- API/service layer
- authentication and access control
- compliance posture
- operational integration

\[BLOCKERS]

- no validation against real labeled cases
- no supervised or calibrated model advantage
- no service/API layer
- no user management or RBAC
- no encryption, secrets management, or tenancy
- no deployment, monitoring, or incident handling
- no clinical governance process
- no channel integrations
- no buyer evidence

---

PORTFOLIO TOTAL

- Gross Value: $10,000–$25,000
- Net Realistic Value: $10,000–$25,000
- Productized Portfolio Value: $30,000–$80,000

---

VALUE CHANGES FROM LAST STATE

- +$0 added from new assets
- -$2,000–$3,000 removed due to stricter realism on deployability/readiness
- Net change: -$2,000–$3,000

---

TOP VALUE DRIVERS

- A-001 execution layer exists. This is not just concept text.
- A-001 persistence and audit trail improve diligence credibility.
- A-001 deterministic routing logic makes it easier to inspect and pilot than a black-box demo.

---

VALUE LEAKS

- no production interface
- no deployment path
- no security architecture
- no validation dataset
- no integrations
- no regulatory/compliance package
- no traction

---

SYSTEM STRUCTURE

Core assets

- A-001 core triage engine
  - feature extraction
  - urgency scoring
  - routing
  - persistence
  - audit
  - reporting
  - CLI

Supporting assets

- SBIR framing
- demo cases
- policy thresholds

Orphaned assets

- commercialization narrative without operational proof
- pilot language without pilot instrumentation

---

HARD TRUTH

What actually has value:

- The executable prototype.
- The deterministic scoring/routing structure.
- The storage and auditability.
- The packaging discipline.

What is noise:

- NIH/SBIR framing by itself.
- commercialization bullets without customer proof
- any implication of clinical readiness

What must be fixed to unlock next level:

- add API/service layer
- add web reviewer dashboard
- add versioned policy configs
- add labeled benchmark set and evaluation suite
- add auth, RBAC, encryption, and audit hardening
- add integrations for real intake channels
- add governance and reviewer override workflow
- add pilot instrumentation tied to measurable outcomes

Bottom line:
This is a credible prototype asset, not a deployable crisis platform. Its value comes from being inspectable, executable, and pitchable as a pilot foundation. It does not yet justify platform pricing.

If you want, I can convert this into a stricter **v2 ledger entry with line-item valuation by module**.


#### You:
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
═══════════════════════════════════════════════════════════════════════════════
AEGIS TRIAGE
Human-Guided Crisis Signal Intelligence Platform
NIH SBIR Research Prototype — Single-File Edition
═══════════════════════════════════════════════════════════════════════════════

OVERVIEW
--------
Aegis Triage is a research-oriented, human-guided crisis signal intelligence
prototype designed for:
- real-time crisis signal intake,
- explainable urgency estimation,
- policy-aware routing recommendations,
- operator review support,
- retrospective audit and evaluation.

This file intentionally combines:
1) SBIR-style concept framing
2) a functional deterministic prototype
3) storage, audit, and reporting utilities
4) a command-line interface for demo, batch, and interactive use

IMPORTANT
---------
This software is a research prototype for workflow support, evaluation,
simulation, and pilot design. It is not a substitute for licensed clinical
judgment, emergency response procedure, or approved crisis center policy.

DESIGN PRINCIPLES
-----------------
- human-guided, not human-replacing
- deterministic and explainable
- auditable and retrospective-ready
- conservative in uncertainty
- single-file deployable
- pilot-program friendly

EXAMPLES
--------
python aegis_triage.py --demo
python aegis_triage.py --interactive
python aegis_triage.py --batch cases.jsonl
python aegis_triage.py --summary
python aegis_triage.py --print-concept

OPTIONAL ENVIRONMENT VARIABLES
------------------------------
AEGIS_DB=aegis_triage.db
AEGIS_AUDIT_JSONL=aegis_audit.jsonl
AEGIS_POLICY=default
AEGIS_VERBOSE=true
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import statistics
import textwrap
import time
import hashlib
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# BRAND + CONCEPT LAYER
# =============================================================================

BRAND_NAME = "Aegis Triage"
BRAND_TAGLINE = "Human-Guided Crisis Signal Intelligence Platform"
BRAND_SHORT_DESCRIPTION = (
    "A deterministic, explainable, human-guided triage intelligence prototype "
    "for crisis workflows, research pilots, and operator decision support."
)

PROJECT_TITLE = f"{BRAND_NAME}: {BRAND_TAGLINE}"

PROJECT_SUMMARY = """
Crisis response environments, including 988-aligned operations, behavioral
health triage teams, telehealth intake, and emergency communication workflows,
must make high-stakes prioritization decisions under time pressure, incomplete
information, and variable staffing.

Aegis Triage is a human-guided crisis signal intelligence platform designed to
support those workflows with deterministic feature extraction, explainable
urgency estimation, policy-aware routing recommendations, and retrospective
auditability.

The system does not replace human judgment. Instead, it helps teams:
- identify salient crisis indicators,
- structure urgency review consistently,
- prioritize uncertain and high-risk cases conservatively,
- log decision context for quality assurance and research,
- create an evaluation pathway for future supervised model refinement.

The goal is to improve response consistency, transparency, timeliness, and
operational learning in crisis support environments.
""".strip()

SPECIFIC_AIMS = [
    "Build a real-time crisis signal intake and feature extraction pipeline.",
    "Develop an explainable, deterministic urgency estimation engine.",
    "Implement policy-aware routing recommendations with conservative safety rules.",
    "Create a feedback and retrospective analysis layer for continuous evaluation.",
]

SIGNIFICANCE = [
    "Improves consistency in high-pressure triage workflows.",
    "Preserves human authority while enhancing operator support.",
    "Creates auditable evidence for quality assurance and pilot review.",
    "Supports public-sector and healthcare-oriented AI operations modernization.",
]

INNOVATION = [
    "Explainable crisis signal intelligence rather than opaque scoring alone.",
    "Conservative uncertainty handling that escalates review rather than suppressing it.",
    "Policy-aware routing recommendations with explicit safety floors.",
    "Single-file deployable research architecture for rapid pilots and demos.",
]

TECHNICAL_RISKS = [
    "Ambiguous language may create uncertainty in urgency estimation.",
    "Metaphorical or quoted language may trigger false positives.",
    "Workflow misuse may occur if operators over-trust automated suggestions.",
    "Different channels and populations may require policy recalibration.",
]

RISK_MITIGATIONS = [
    "Route uncertain cases toward human review.",
    "Maintain deterministic logic and transparent feature contributions.",
    "Enforce conservative safety floors for self-harm and violence signals.",
    "Preserve full audit logs for calibration and incident review.",
]

COMMERCIALIZATION = [
    "Crisis hotline modernization pilots",
    "Behavioral health intake support systems",
    "Emergency communications decision-support tooling",
    "Healthcare operations intelligence infrastructure",
]

MILESTONES = [
    "Signal intake and feature extraction baseline",
    "Urgency estimation and policy routing baseline",
    "Audit logging and persistence layer",
    "Outcome tracking and retrospective reporting",
    "Pilot-readiness package for grant and procurement discussions",
]

BUDGET = {
    "engineering": 90000,
    "clinical_advisory": 35000,
    "security_and_compliance": 20000,
    "cloud_and_storage": 12000,
    "evaluation_and_pilot_support": 28000,
    "miscellaneous": 15000,
}


# =============================================================================
# UTILITY LAYER
# =============================================================================

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_case_id(message: str, timestamp: float) -> str:
    raw = f"{timestamp}|{message}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:16]
    return f"aegis_{digest}"


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compact_text(text: str, width: int = 88) -> str:
    text = " ".join(text.split())
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


# =============================================================================
# POLICY LAYER
# =============================================================================

@dataclass
class Policy:
    name: str = "default"

    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    low_confidence_threshold: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    emergency_route: str = "EMERGENCY_DISPATCH_RECOMMENDED"
    immediate_route: str = "IMMEDIATE_CLINICIAN_REVIEW"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "PRIORITY_QUEUE"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

    w_high_risk: float = 0.24
    w_medium_risk: float = 0.09
    w_plan: float = 0.22
    w_means: float = 0.16
    w_immediacy: float = 0.18
    w_self_harm: float = 0.26
    w_violence: float = 0.26
    w_distress: float = 0.10
    w_protective: float = -0.18
    w_help_seeking: float = -0.04
    w_negation_safety: float = -0.10
    w_short_signal: float = 0.08
    w_caps: float = 0.03
    w_punctuation: float = 0.03

    confidence_base: float = 0.50
    confidence_per_feature_group: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_metadata: float = 0.05

    require_human_review_for_high: bool = True
    route_low_confidence_to_human: bool = True
    preserve_self_harm_floor: bool = True
    preserve_violence_floor: bool = True


def load_policy(name: str = "default") -> Policy:
    return Policy(name=name)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class CrisisSignal:
    case_id: str
    timestamp: float
    created_at: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureSet:
    word_count: int
    char_count: int
    sentence_count: int
    uppercase_ratio: float
    exclamation_count: int
    question_count: int

    high_risk_hits: List[str] = field(default_factory=list)
    medium_risk_hits: List[str] = field(default_factory=list)
    plan_hits: List[str] = field(default_factory=list)
    means_hits: List[str] = field(default_factory=list)
    immediacy_hits: List[str] = field(default_factory=list)
    self_harm_hits: List[str] = field(default_factory=list)
    violence_hits: List[str] = field(default_factory=list)
    protective_hits: List[str] = field(default_factory=list)
    help_hits: List[str] = field(default_factory=list)
    negation_hits: List[str] = field(default_factory=list)
    ambiguity_hits: List[str] = field(default_factory=list)
    distress_hits: List[str] = field(default_factory=list)

    def total_hits(self) -> int:
        groups = [
            self.high_risk_hits,
            self.medium_risk_hits,
            self.plan_hits,
            self.means_hits,
            self.immediacy_hits,
            self.self_harm_hits,
            self.violence_hits,
            self.protective_hits,
            self.help_hits,
            self.negation_hits,
            self.ambiguity_hits,
            self.distress_hits,
        ]
        return sum(len(group) for group in groups)


@dataclass
class RiskAssessment:
    urgency: float
    confidence: float
    band: str
    reasons: List[str] = field(default_factory=list)
    contributions: Dict[str, float] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    priority: str
    route_to: str
    explanation: str
    requires_human_review: bool
    safety_flags: List[str] = field(default_factory=list)


@dataclass
class CaseRecord:
    case_id: str
    signal: CrisisSignal
    features: FeatureSet
    risk: RiskAssessment
    decision: RoutingDecision
    processing_ms: float
    outcome: Optional[str] = None
    reviewer_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "signal": asdict(self.signal),
            "features": asdict(self.features),
            "risk": asdict(self.risk),
            "decision": asdict(self.decision),
            "processing_ms": self.processing_ms,
            "outcome": self.outcome,
            "reviewer_notes": self.reviewer_notes,
        }


# =============================================================================
# FEATURE EXTRACTION LAYER
# =============================================================================

class SignalAnalyzer:
    """
    Deterministic language-pattern extractor for research prototypes.
    """

    HIGH_RISK = {
        r"\bi want to die\b": "want_to_die",
        r"\bend my life\b": "end_my_life",
        r"\bkill myself\b": "kill_myself",
        r"\bsuicide\b": "suicide",
        r"\bno reason to live\b": "no_reason_to_live",
        r"\bcan't go on\b": "cant_go_on",
        r"\boverdose\b": "overdose",
        r"\bhurt myself\b": "hurt_myself",
        r"\bself harm\b": "self_harm",
    }

    MEDIUM_RISK = {
        r"\bhopeless\b": "hopeless",
        r"\bpanic\b": "panic",
        r"\bdesperate\b": "desperate",
        r"\boverwhelmed\b": "overwhelmed",
        r"\bscared\b": "scared",
        r"\bafraid\b": "afraid",
        r"\bbreaking down\b": "breaking_down",
        r"\bin crisis\b": "in_crisis",
        r"\balone\b": "alone",
    }

    PLAN = {
        r"\bi have a plan\b": "have_a_plan",
        r"\bplanned\b": "planned",
        r"\bi know how\b": "know_how",
        r"\btonight\b": "tonight",
        r"\bafter everyone sleeps\b": "after_everyone_sleeps",
    }

    MEANS = {
        r"\bpills\b": "pills",
        r"\bgun\b": "gun",
        r"\bknife\b": "knife",
        r"\brope\b": "rope",
        r"\bweapon\b": "weapon",
        r"\brazor\b": "razor",
    }

    IMMEDIACY = {
        r"\bnow\b": "now",
        r"\bright now\b": "right_now",
        r"\btoday\b": "today",
        r"\btonight\b": "tonight",
        r"\bimmediately\b": "immediately",
        r"\bsoon\b": "soon",
    }

    SELF_HARM = {
        r"\bhurt myself\b": "hurt_myself",
        r"\bcut myself\b": "cut_myself",
        r"\bself harm\b": "self_harm",
        r"\bkill myself\b": "kill_myself",
        r"\bend my life\b": "end_my_life",
    }

    VIOLENCE = {
        r"\bhurt someone\b": "hurt_someone",
        r"\bkill them\b": "kill_them",
        r"\bshoot\b": "shoot",
        r"\bstab\b": "stab",
        r"\bviolent\b": "violent",
        r"\bweapon\b": "weapon",
    }

    PROTECTIVE = {
        r"\bi am safe\b": "i_am_safe",
        r"\bi'm safe\b": "i_am_safe",
        r"\bi won't do anything\b": "wont_do_anything",
        r"\bi do not want to die\b": "do_not_want_to_die",
        r"\bi don't want to die\b": "do_not_want_to_die",
        r"\bi am with someone\b": "with_someone",
        r"\bi'm with someone\b": "with_someone",
        r"\bmy therapist\b": "therapist",
        r"\bmy counselor\b": "counselor",
    }

    HELP = {
        r"\bplease help\b": "please_help",
        r"\bneed help\b": "need_help",
        r"\bi need to talk\b": "need_to_talk",
        r"\bcan someone talk\b": "someone_talk",
        r"\blooking for support\b": "support",
    }

    NEGATION = {
        r"\bnot suicidal\b": "not_suicidal",
        r"\bnot going to hurt myself\b": "not_hurt_self",
        r"\bnot going to kill myself\b": "not_kill_self",
        r"\bno plan\b": "no_plan",
        r"\bno intent\b": "no_intent",
    }

    AMBIGUITY = {
        r"\bjust kidding\b": "just_kidding",
        r"\bfiguratively\b": "figuratively",
        r"\bquote\b": "quote",
        r"\bsong lyric\b": "song_lyric",
        r"\bmetaphor\b": "metaphor",
    }

    DISTRESS = {
        r"\bcan't\b": "cant",
        r"\bnever\b": "never",
        r"\balways\b": "always",
        r"\bno one\b": "no_one",
        r"\bnobody\b": "nobody",
        r"\bi'm done\b": "im_done",
        r"\bi am done\b": "im_done",
    }

    @staticmethod
    def _hits(text: str, patterns: Dict[str, str]) -> List[str]:
        found: List[str] = []
        for pattern, label in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.append(label)
        return sorted(set(found))

    @staticmethod
    def _sentence_count(text: str) -> int:
        parts = [p.strip() for p in re.split(r"[.!?]+", text) if p.strip()]
        return max(1, len(parts))

    @staticmethod
    def _uppercase_ratio(text: str) -> float:
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        uppercase = sum(1 for c in letters if c.isupper())
        return round(uppercase / len(letters), 4)

    def analyze(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[CrisisSignal, FeatureSet]:
        timestamp = time.time()
        case_id = make_case_id(message, timestamp)
        signal = CrisisSignal(
            case_id=case_id,
            timestamp=timestamp,
            created_at=now_utc_iso(),
            message=message,
            metadata=dict(metadata or {}),
        )

        lower = message.lower()
        features = FeatureSet(
            word_count=len(message.split()),
            char_count=len(message),
            sentence_count=self._sentence_count(message),
            uppercase_ratio=self._uppercase_ratio(message),
            exclamation_count=message.count("!"),
            question_count=message.count("?"),
            high_risk_hits=self._hits(lower, self.HIGH_RISK),
            medium_risk_hits=self._hits(lower, self.MEDIUM_RISK),
            plan_hits=self._hits(lower, self.PLAN),
            means_hits=self._hits(lower, self.MEANS),
            immediacy_hits=self._hits(lower, self.IMMEDIACY),
            self_harm_hits=self._hits(lower, self.SELF_HARM),
            violence_hits=self._hits(lower, self.VIOLENCE),
            protective_hits=self._hits(lower, self.PROTECTIVE),
            help_hits=self._hits(lower, self.HELP),
            negation_hits=self._hits(lower, self.NEGATION),
            ambiguity_hits=self._hits(lower, self.AMBIGUITY),
            distress_hits=self._hits(lower, self.DISTRESS),
        )

        signal.metadata.update(
            {
                "word_count": features.word_count,
                "char_count": features.char_count,
                "sentence_count": features.sentence_count,
                "uppercase_ratio": features.uppercase_ratio,
                "exclamation_count": features.exclamation_count,
                "question_count": features.question_count,
            }
        )
        return signal, features


# =============================================================================
# RISK LAYER
# =============================================================================

class UrgencyModel:
    def __init__(self, policy: Policy):
        self.policy = policy

    def assess(self, signal: CrisisSignal, features: FeatureSet) -> RiskAssessment:
        contributions: Dict[str, float] = {}
        reasons: List[str] = []

        base = min(0.18, features.word_count / 300.0)
        contributions["base_text_density"] = round(base, 4)

        def add_if_nonzero(name: str, value: float) -> None:
            if value:
                contributions[name] = round(value, 4)

        high = len(features.high_risk_hits) * self.policy.w_high_risk
        medium = len(features.medium_risk_hits) * self.policy.w_medium_risk
        plan = len(features.plan_hits) * self.policy.w_plan
        means = len(features.means_hits) * self.policy.w_means
        immediacy = len(features.immediacy_hits) * self.policy.w_immediacy
        self_harm = len(features.self_harm_hits) * self.policy.w_self_harm
        violence = len(features.violence_hits) * self.policy.w_violence
        distress = len(features.distress_hits) * self.policy.w_distress
        protective = len(features.protective_hits) * self.policy.w_protective
        help_signal = len(features.help_hits) * self.policy.w_help_seeking
        negation = len(features.negation_hits) * self.policy.w_negation_safety

        add_if_nonzero("high_risk", high)
        add_if_nonzero("medium_risk", medium)
        add_if_nonzero("plan", plan)
        add_if_nonzero("means", means)
        add_if_nonzero("immediacy", immediacy)
        add_if_nonzero("self_harm", self_harm)
        add_if_nonzero("violence", violence)
        add_if_nonzero("distress", distress)
        add_if_nonzero("protective", protective)
        add_if_nonzero("help_seeking", help_signal)
        add_if_nonzero("negation", negation)

        if features.high_risk_hits:
            reasons.append(f"high-risk indicators: {', '.join(features.high_risk_hits)}")
        if features.medium_risk_hits:
            reasons.append(f"distress indicators: {', '.join(features.medium_risk_hits)}")
        if features.plan_hits:
            reasons.append(f"plan indicators: {', '.join(features.plan_hits)}")
        if features.means_hits:
            reasons.append(f"means indicators: {', '.join(features.means_hits)}")
        if features.immediacy_hits:
            reasons.append(f"time/immediacy indicators: {', '.join(features.immediacy_hits)}")
        if features.self_harm_hits:
            reasons.append(f"self-harm indicators: {', '.join(features.self_harm_hits)}")
        if features.violence_hits:
            reasons.append(f"violence indicators: {', '.join(features.violence_hits)}")
        if features.protective_hits:
            reasons.append(f"protective factors: {', '.join(features.protective_hits)}")
        if features.help_hits:
            reasons.append(f"help-seeking language: {', '.join(features.help_hits)}")

        short_signal = 0.0
        if features.word_count <= 3 and (
            features.high_risk_hits
            or features.medium_risk_hits
            or features.help_hits
            or features.self_harm_hits
        ):
            short_signal = self.policy.w_short_signal
            contributions["short_signal"] = round(short_signal, 4)
            reasons.append("very short message with meaningful crisis/help signal")

        emphasis = 0.0
        if features.uppercase_ratio >= 0.35:
            emphasis += self.policy.w_caps
        if features.exclamation_count >= 2:
            emphasis += self.policy.w_punctuation
        add_if_nonzero("emphasis", emphasis)

        urgency_raw = (
            base
            + high
            + medium
            + plan
            + means
            + immediacy
            + self_harm
            + violence
            + distress
            + protective
            + help_signal
            + negation
            + short_signal
            + emphasis
        )

        if features.self_harm_hits and self.policy.preserve_self_harm_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["self_harm_floor"] = 0.72

        if features.violence_hits and self.policy.preserve_violence_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["violence_floor"] = 0.72

        urgency = clamp01(urgency_raw)

        feature_groups = sum(
            1 for group in [
                features.high_risk_hits,
                features.medium_risk_hits,
                features.plan_hits,
                features.means_hits,
                features.immediacy_hits,
                features.self_harm_hits,
                features.violence_hits,
                features.protective_hits,
                features.help_hits,
                features.negation_hits,
                features.ambiguity_hits,
                features.distress_hits,
            ] if group
        )

        confidence = self.policy.confidence_base
        confidence += feature_groups * self.policy.confidence_per_feature_group
        confidence += min(4, features.total_hits()) * self.policy.confidence_per_signal_density

        if features.ambiguity_hits:
            confidence -= self.policy.confidence_penalty_ambiguity
            reasons.append(f"ambiguity markers: {', '.join(features.ambiguity_hits)}")

        if features.word_count <= 2:
            confidence -= self.policy.confidence_penalty_too_short
            reasons.append("extremely short input lowers confidence")

        if signal.metadata:
            confidence += self.policy.confidence_bonus_metadata

        confidence = clamp01(confidence)

        if urgency >= self.policy.critical_threshold:
            band = "CRITICAL"
        elif urgency >= self.policy.high_threshold:
            band = "HIGH"
        elif urgency >= self.policy.medium_threshold:
            band = "MEDIUM"
        else:
            band = "LOW"

        if not reasons:
            reasons.append("limited direct risk language; estimate driven by general signal density")

        return RiskAssessment(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            band=band,
            reasons=reasons,
            contributions=contributions,
        )


# =============================================================================
# DECISION LAYER
# =============================================================================

class RoutingEngine:
    def __init__(self, policy: Policy):
        self.policy = policy

    def decide(self, features: FeatureSet, risk: RiskAssessment) -> RoutingDecision:
        flags: List[str] = []
        low_confidence = risk.confidence < self.policy.low_confidence_threshold
        self_harm_present = bool(features.self_harm_hits or features.high_risk_hits)
        violence_present = bool(features.violence_hits)

        if self_harm_present:
            flags.append("SELF_HARM_SIGNAL")
        if violence_present:
            flags.append("VIOLENCE_SIGNAL")
        if features.plan_hits:
            flags.append("PLAN_INDICATOR")
        if features.means_hits:
            flags.append("MEANS_INDICATOR")
        if low_confidence:
            flags.append("LOW_CONFIDENCE")

        if risk.urgency >= self.policy.critical_threshold:
            priority = "CRITICAL"
            route = self.policy.emergency_route
            review = True
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds critical threshold "
                f"{self.policy.critical_threshold:.2f}; emergency-aligned escalation is recommended."
            )
        elif risk.urgency >= self.policy.high_threshold:
            priority = "HIGH"
            route = self.policy.immediate_route
            review = self.policy.require_human_review_for_high
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds high threshold "
                f"{self.policy.high_threshold:.2f}; immediate clinician review is recommended."
            )
        elif risk.urgency >= self.policy.medium_threshold:
            priority = "MEDIUM"
            route = self.policy.priority_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds medium threshold "
                f"{self.policy.medium_threshold:.2f}; priority handling is recommended."
            )
        else:
            priority = "LOW"
            route = self.policy.standard_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} is below medium threshold; "
                f"standard queue placement is recommended."
            )

        if low_confidence and self.policy.route_low_confidence_to_human:
            route = self.policy.mandatory_review_route
            review = True
            explanation += " Confidence is limited, so human review is required."

        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = self.policy.urgent_review_route
            review = True
            explanation += " High-risk plus uncertainty triggers urgent human review."

        if self_harm_present and priority == "LOW":
            priority = "MEDIUM"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Self-harm language prevents a low-priority disposition."

        if violence_present and priority in {"LOW", "MEDIUM"}:
            priority = "HIGH"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Violence language elevates the case for urgent review."

        return RoutingDecision(
            priority=priority,
            route_to=route,
            explanation=explanation,
            requires_human_review=review,
            safety_flags=flags,
        )


# =============================================================================
# STORAGE LAYER
# =============================================================================

class CaseStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_records (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                timestamp REAL NOT NULL,
                message TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                features_json TEXT NOT NULL,
                risk_json TEXT NOT NULL,
                decision_json TEXT NOT NULL,
                processing_ms REAL NOT NULL,
                outcome TEXT,
                reviewer_notes TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                reviewer_notes TEXT,
                recorded_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_case_outcomes_case_id ON case_outcomes(case_id)"
        )
        self.conn.commit()

    def save(self, record: CaseRecord) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO case_records (
                case_id, created_at, timestamp, message, metadata_json,
                features_json, risk_json, decision_json, processing_ms,
                outcome, reviewer_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.case_id,
                record.signal.created_at,
                record.signal.timestamp,
                record.signal.message,
                json.dumps(record.signal.metadata, ensure_ascii=False),
                json.dumps(asdict(record.features), ensure_ascii=False),
                json.dumps(asdict(record.risk), ensure_ascii=False),
                json.dumps(asdict(record.decision), ensure_ascii=False),
                record.processing_ms,
                record.outcome,
                record.reviewer_notes,
            ),
        )
        self.conn.commit()

    def set_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE case_records
            SET outcome = ?, reviewer_notes = ?
            WHERE case_id = ?
            """,
            (outcome, reviewer_notes, case_id),
        )
        updated = cur.rowcount > 0
        cur.execute(
            """
            INSERT INTO case_outcomes (case_id, outcome, reviewer_notes, recorded_at)
            VALUES (?, ?, ?, ?)
            """,
            (case_id, outcome, reviewer_notes, now_utc_iso()),
        )
        self.conn.commit()
        return updated

    def get(self, case_id: str) -> Optional[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM case_records WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_recent(self, limit: int = 1000) -> List[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM case_records ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row: sqlite3.Row) -> CaseRecord:
        signal = CrisisSignal(
            case_id=row["case_id"],
            timestamp=row["timestamp"],
            created_at=row["created_at"],
            message=row["message"],
            metadata=json.loads(row["metadata_json"]),
        )
        features = FeatureSet(**json.loads(row["features_json"]))
        risk = RiskAssessment(**json.loads(row["risk_json"]))
        decision = RoutingDecision(**json.loads(row["decision_json"]))
        return CaseRecord(
            case_id=row["case_id"],
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=row["processing_ms"],
            outcome=row["outcome"],
            reviewer_notes=row["reviewer_notes"],
        )

    def close(self) -> None:
        self.conn.close()


# =============================================================================
# AUDIT LAYER
# =============================================================================

class AuditTrail:
    def __init__(self, jsonl_path: str, verbose: bool = True):
        self.jsonl_path = jsonl_path
        self.verbose = verbose
        self._entries: List[Dict[str, Any]] = []

    def log(self, record: CaseRecord) -> None:
        entry = record.to_dict()
        self._entries.append(entry)

        with open(self.jsonl_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if self.verbose:
            self._print(record)

    def _print(self, record: CaseRecord) -> None:
        print("┌" + "─" * 78)
        print(f"│ BRAND        : {BRAND_NAME}")
        print(f"│ CASE ID      : {record.case_id}")
        print(f"│ MESSAGE      : {compact_text(record.signal.message)}")
        print(f"│ URGENCY      : {record.risk.urgency:.4f}    CONFIDENCE: {record.risk.confidence:.4f}")
        print(f"│ BAND         : {record.risk.band}")
        print(f"│ PRIORITY     : {record.decision.priority:<12} ROUTE: {record.decision.route_to}")
        print(f"│ HUMAN REVIEW : {record.decision.requires_human_review}")
        print(f"│ FLAGS        : {', '.join(record.decision.safety_flags) if record.decision.safety_flags else 'None'}")
        print(f"│ REASONS      : {compact_text('; '.join(record.risk.reasons[:3]), 70)}")
        print(f"│ LATENCY      : {record.processing_ms:.2f} ms")
        print("└" + "─" * 78)

    def export_json(self) -> str:
        return json.dumps(self._entries, indent=2, ensure_ascii=False)


# =============================================================================
# FEEDBACK + REPORTING LAYER
# =============================================================================

class ReviewLoop:
    def __init__(self, store: CaseStore):
        self.store = store

    def record_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.store.set_outcome(case_id, outcome, reviewer_notes)

    def summary(self, limit: int = 5000) -> Dict[str, Any]:
        records = self.store.list_recent(limit=limit)
        if not records:
            return {"records": 0}

        urgencies = [r.risk.urgency for r in records]
        confidences = [r.risk.confidence for r in records]
        priorities = [r.decision.priority for r in records]
        routes = [r.decision.route_to for r in records]
        outcomes = [r.outcome for r in records if r.outcome]

        return {
            "brand": BRAND_NAME,
            "records": len(records),
            "avg_urgency": round(statistics.mean(urgencies), 4),
            "max_urgency": round(max(urgencies), 4),
            "avg_confidence": round(statistics.mean(confidences), 4),
            "human_review_rate": round(
                sum(1 for r in records if r.decision.requires_human_review) / len(records), 4
            ),
            "band_distribution": dict(Counter(r.risk.band for r in records)),
            "priority_distribution": dict(Counter(priorities)),
            "route_distribution": dict(Counter(routes)),
            "outcomes_logged": len(outcomes),
            "outcome_distribution": dict(Counter(outcomes)),
        }

    def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
        records = [r for r in self.store.list_recent(limit=limit) if r.outcome]
        if not records:
            return {"records_with_outcomes": 0, "buckets": {}}

        buckets = {
            "0.00-0.39": [],
            "0.40-0.64": [],
            "0.65-0.84": [],
            "0.85-1.00": [],
        }

        for record in records:
            u = record.risk.urgency
            if u < 0.40:
                buckets["0.00-0.39"].append(record.outcome or "UNKNOWN")
            elif u < 0.65:
                buckets["0.40-0.64"].append(record.outcome or "UNKNOWN")
            elif u < 0.85:
                buckets["0.65-0.84"].append(record.outcome or "UNKNOWN")
            else:
                buckets["0.85-1.00"].append(record.outcome or "UNKNOWN")

        return {
            "records_with_outcomes": len(records),
            "buckets": {k: dict(Counter(v)) for k, v in buckets.items()},
        }


# =============================================================================
# ORCHESTRATION LAYER
# =============================================================================

class AegisTriageEngine:
    def __init__(
        self,
        db_path: str,
        audit_jsonl_path: str,
        verbose: bool = True,
        policy_name: str = "default",
    ):
        self.policy = load_policy(policy_name)
        self.analyzer = SignalAnalyzer()
        self.urgency_model = UrgencyModel(self.policy)
        self.routing_engine = RoutingEngine(self.policy)
        self.store = CaseStore(db_path)
        self.audit = AuditTrail(audit_jsonl_path, verbose=verbose)
        self.review = ReviewLoop(self.store)

    def process(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> CaseRecord:
        start = time.perf_counter()

        signal, features = self.analyzer.analyze(message, metadata=metadata)
        risk = self.urgency_model.assess(signal, features)
        decision = self.routing_engine.decide(features, risk)

        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 3)

        record = CaseRecord(
            case_id=signal.case_id,
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=elapsed_ms,
        )

        self.store.save(record)
        self.audit.log(record)
        return record

    def log_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.review.record_outcome(case_id, outcome, reviewer_notes)

    def export_records(self, path: str, limit: int = 5000) -> None:
        payload = [r.to_dict() for r in self.store.list_recent(limit=limit)]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    def summary(self) -> Dict[str, Any]:
        return self.review.summary()

    def calibration(self) -> Dict[str, Any]:
        return self.review.calibration_snapshot()

    def close(self) -> None:
        self.store.close()


# =============================================================================
# PRESENTATION LAYER
# =============================================================================

def print_header(title: str) -> None:
    print("\n" + "═" * 80)
    print(title)
    print("═" * 80 + "\n")


def print_concept() -> None:
    print_header(f"{BRAND_NAME.upper()} — SBIR RESEARCH CONCEPT")
    sections = {
        "TITLE": PROJECT_TITLE,
        "BRAND DESCRIPTION": BRAND_SHORT_DESCRIPTION,
        "PROJECT SUMMARY": PROJECT_SUMMARY,
        "SPECIFIC AIMS": SPECIFIC_AIMS,
        "SIGNIFICANCE": SIGNIFICANCE,
        "INNOVATION": INNOVATION,
        "TECHNICAL RISKS": TECHNICAL_RISKS,
        "RISK MITIGATIONS": RISK_MITIGATIONS,
        "COMMERCIALIZATION": COMMERCIALIZATION,
        "MILESTONES": MILESTONES,
        "BUDGET": BUDGET,
    }

    for name, value in sections.items():
        print(name)
        print("-" * len(name))
        if isinstance(value, str):
            print(textwrap.fill(value, width=88))
        elif isinstance(value, dict):
            for k, v in value.items():
                print(f"  - {k}: ${v:,.0f}")
        else:
            for item in value:
                print(f"  - {item}")
        print()


def print_summary(summary: Dict[str, Any], calibration: Optional[Dict[str, Any]] = None) -> None:
    print_header(f"{BRAND_NAME.upper()} — SUMMARY")
    for key, value in summary.items():
        print(f"{key:>24} : {value}")
    if calibration is not None:
        print("\nCALIBRATION SNAPSHOT")
        print("--------------------")
        for key, value in calibration.items():
            print(f"{key:>24} : {value}")
    print()


def print_case(record: CaseRecord) -> None:
    print_header(f"{BRAND_NAME.upper()} — CASE DETAIL")
    print(f"Case ID         : {record.case_id}")
    print(f"Created at      : {record.signal.created_at}")
    print(f"Message         : {record.signal.message}")
    print(f"Metadata        : {json.dumps(record.signal.metadata, ensure_ascii=False)}")
    print()
    print("FEATURES")
    print("--------")
    print(json.dumps(asdict(record.features), indent=2, ensure_ascii=False))
    print()
    print("RISK")
    print("----")
    print(json.dumps(asdict(record.risk), indent=2, ensure_ascii=False))
    print()
    print("DECISION")
    print("--------")
    print(json.dumps(asdict(record.decision), indent=2, ensure_ascii=False))
    print()
    print(f"Processing ms   : {record.processing_ms}")
    print(f"Outcome         : {record.outcome}")
    print(f"Reviewer notes  : {record.reviewer_notes}")
    print()


# =============================================================================
# DEMO CASES
# =============================================================================

DEMO_CASES: List[Tuple[str, Dict[str, Any], str]] = [
    (
        "I've been feeling a little down lately and just needed to talk.",
        {"channel": "chat", "source": "demo"},
        "RESOLVED_SUPPORTIVE_CONTACT",
    ),
    (
        "I don't know how much longer I can handle this. I feel completely overwhelmed and scared.",
        {"channel": "chat", "source": "demo"},
        "COUNSELOR_FOLLOW_UP",
    ),
    (
        "I'm in crisis right now. I feel hopeless and desperate. Please help me.",
        {"channel": "voice", "source": "demo"},
        "IMMEDIATE_CLINICIAN_CONTACT",
    ),
    (
        "I want to end my life tonight. I have a plan and I don't see any reason to go on.",
        {"channel": "chat", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
    (
        "help",
        {"channel": "sms", "source": "demo"},
        "MONITORED_AND_ENGAGED",
    ),
    (
        "Not suicidal. No plan. I am safe, but I really need to talk to someone tonight because I'm panicking.",
        {"channel": "chat", "source": "demo"},
        "URGENT_SUPPORT_CONTACT",
    ),
    (
        "I have pills and I think tonight is the night.",
        {"channel": "sms", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
]


# =============================================================================
# CLI LAYER
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{BRAND_NAME} — single-file research prototype"
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demonstration cases")
    parser.add_argument("--interactive", action="store_true", help="Run interactive console mode")
    parser.add_argument("--batch", type=str, help="Process a JSONL batch file")
    parser.add_argument("--summary", action="store_true", help="Print stored summary")
    parser.add_argument("--show-case", type=str, help="Show stored case by case_id")
    parser.add_argument("--export-records", type=str, help="Export records to JSON")
    parser.add_argument("--print-concept", action="store_true", help="Print concept package")
    parser.add_argument("--quiet", action="store_true", help="Reduce console output")
    parser.add_argument("--db", type=str, default=os.getenv("AEGIS_DB", "aegis_triage.db"))
    parser.add_argument(
        "--audit-jsonl",
        type=str,
        default=os.getenv("AEGIS_AUDIT_JSONL", "aegis_audit.jsonl"),
    )
    parser.add_argument(
        "--policy",
        type=str,
        default=os.getenv("AEGIS_POLICY", "default"),
    )
    return parser.parse_args(argv)


def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Line {line_no} is not a JSON object")
            yield item


def run_demo(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — DEMO")
    for idx, (message, metadata, outcome) in enumerate(DEMO_CASES, start=1):
        print(f"[Demo Case {idx}/{len(DEMO_CASES)}]")
        record = engine.process(message, metadata=metadata)
        engine.log_outcome(record.case_id, outcome, reviewer_notes="demo outcome")
        print(f"Outcome logged : {outcome}\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_batch(engine: AegisTriageEngine, path: str) -> None:
    print_header(f"{BRAND_NAME.upper()} — BATCH MODE")
    processed = 0
    for item in iter_jsonl(path):
        message = str(item.get("message", "")).strip()
        metadata = item.get("metadata", {})
        if not message:
            continue
        engine.process(message, metadata if isinstance(metadata, dict) else {})
        processed += 1
    print(f"Processed {processed} records.\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_interactive(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — INTERACTIVE MODE")
    print("Enter a message, then press Enter.")
    print("Commands:")
    print("  /quit")
    print("  /summary")
    print("  /show <case_id>")
    print("  /outcome <case_id> <OUTCOME TEXT>")
    print()

    while True:
        try:
            raw = input("message> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if not raw:
            continue
        if raw == "/quit":
            break
        if raw == "/summary":
            print_summary(engine.summary(), calibration=engine.calibration())
            continue
        if raw.startswith("/show "):
            _, _, case_id = raw.partition(" ")
            record = engine.store.get(case_id.strip())
            if record is None:
                print("Case not found.")
            else:
                print_case(record)
            continue
        if raw.startswith("/outcome "):
            parts = raw.split(maxsplit=2)
            if len(parts) < 3:
                print("Usage: /outcome <case_id> <OUTCOME TEXT>")
                continue
            _, case_id, outcome = parts
            ok = engine.log_outcome(case_id, outcome, reviewer_notes="interactive outcome")
            print("Outcome recorded." if ok else "Case not found.")
            continue

        engine.process(raw, metadata={"channel": "interactive_console"})


# =============================================================================
# MAIN
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    engine = AegisTriageEngine(
        db_path=args.db,
        audit_jsonl_path=args.audit_jsonl,
        verbose=not args.quiet,
        policy_name=args.policy,
    )

    try:
        acted = False

        if args.print_concept:
            print_concept()
            acted = True

        if args.demo:
            run_demo(engine)
            acted = True

        if args.batch:
            run_batch(engine, args.batch)
            acted = True

        if args.interactive:
            run_interactive(engine)
            acted = True

        if args.summary:
            print_summary(engine.summary(), calibration=engine.calibration())
            acted = True

        if args.show_case:
            record = engine.store.get(args.show_case)
            if record is None:
                print(f"No case found for case_id={args.show_case}")
            else:
                print_case(record)
            acted = True

        if args.export_records:
            engine.export_records(args.export_records)
            print(f"Exported records to {args.export_records}")
            acted = True

        if not acted:
            print_header(f"{BRAND_NAME.upper()} — READY")
            print(BRAND_TAGLINE)
            print()
            print("No action selected. Try:")
            print("  --demo")
            print("  --interactive")
            print("  --batch cases.jsonl")
            print("  --summary")
            print("  --print-concept")
            print()

    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main()) ==============================
MASTER LEDGER SNAPSHOT

A-001 — Aegis Triage — AI / Agent System — Net Value: $12,000–$28,000

[ASSET ID]
	•	A-001

[NAME]
	•	Aegis Triage

[TYPE]
	•	AI / Agent System

[ORIGIN]
	•	Current chat
	•	Source input: single-file Python system prompt/prototype

[FILES / SOURCES]
	•	aegis_triage.py

[DESCRIPTION]
	•	Single-file deterministic crisis triage research prototype with:
	•	branded NIH SBIR concept layer
	•	rule-based signal extraction
	•	urgency scoring
	•	routing logic
	•	SQLite persistence
	•	JSONL audit trail
	•	CLI modes for demo, interactive, batch, summary, export
	•	It is a workflow-support prototype, not a deployable clinical product.

[COMPONENTS]
	•	UI: CLI only
	•	Backend: local Python execution engine
	•	Logic: deterministic regex-based feature extraction and weighted scoring
	•	Data: SQLite case store + JSONL audit log
	•	Integration: local file I/O only
	•	Security: minimal, no auth, no encryption, no access control
	•	Evaluation: basic summary and calibration snapshot
	•	Product Layer: branding + grant framing

[STATUS]
	•	partial

[SCORING]
	•	Completeness: 3.5/5
	•	Execution: 4.0/5
	•	Novelty: 2.5/5
	•	Monetization: 2.5/5
	•	Readiness: 2.0/5

[VALUE]
	•	Extractable: $20,000–$45,000
	•	Realistic: $12,000–$28,000
	•	Productized: $35,000–$90,000

[OVERLAP]
	•	No prior Aegis-specific asset in this snapshot
	•	Internal overlap exists between grant framing and prototype wrapper, but not enough to discount materially

[NET NEW VALUE]
	•	$12,000–$28,000

[DEPENDENCIES]
	•	Clinical policy design
	•	Domain validation data
	•	Human reviewer workflow
	•	Security/compliance layer
	•	Deployment/API surface
	•	Evaluation dataset and benchmark process

[BLOCKERS]
	•	No real-world validation
	•	No model training or calibrated supervised classifier
	•	No authentication, authorization, encryption, or tenant boundaries
	•	No web app, queueing, API, observability stack, or deployment infra
	•	No clinical governance layer
	•	No integration with actual hotline/call-center systems
	•	High regulatory and operational burden if pushed beyond research use

⸻

PORTFOLIO TOTAL
	•	Gross Value: $12,000–$28,000
	•	Net Realistic Value: $12,000–$28,000
	•	Productized Value: $35,000–$90,000

⸻

VALUE CHANGES
	•	Added: $12,000–$28,000

	•	Deducted: $0
= Net: $12,000–$28,000

⸻

TOP VALUE DRIVERS
	•	A-001 → It is not just concept text. It actually executes, stores records, logs outputs, and supports repeatable demo/batch workflows.
	•	A-001 → Deterministic scoring and auditability make it easier to pitch as a research/pilot prototype than an opaque model demo.
	•	A-001 → Packaging is better than average: branding, CLI, persistence, summaries, and concept framing are already combined.

⸻

VALUE LEAKS
	•	no production integration layer
	•	no security/compliance controls
	•	no clinical validation
	•	no customer workflow integration
	•	no actual trained model advantage
	•	no revenue proof
	•	single-file architecture helps demo speed but caps enterprise credibility

⸻

SYSTEM STRUCTURE

Core assets
	•	A-001 Aegis Triage core engine
	•	feature extraction
	•	urgency model
	•	routing engine
	•	persistence
	•	audit
	•	reporting
	•	CLI

Supporting assets
	•	NIH SBIR concept framing embedded in file
	•	demo case corpus
	•	policy object and thresholds

Orphaned assets
	•	none inside this snapshot, but the commercialization story is not backed by deployment, pilots, or data assets

⸻

HARD TRUTH

What actually has value:
	•	The executable prototype.
	•	The deterministic scoring/routing structure.
	•	The persistence and audit trail.
	•	The fact that it is already framed as a pilot/research system rather than a toy sentiment script.

What is noise:
	•	The NIH/SBIR language by itself.
	•	Commercialization bullets without distribution, validation, or buyers.
	•	Any implication that this is clinically deployable.

What must be fixed to unlock next tier:
	•	Add an API/service layer.
	•	Add role-based access, encryption, and serious security controls.
	•	Add evaluation against a labeled dataset.
	•	Add policy versioning and reproducible benchmark reports.
	•	Add a reviewer dashboard or operational interface.
	•	Add integration points for real intake channels.
	•	Add governance language and validation workflow with clinical reviewers.

Bottom line:
This is a credible research prototype with packaging discipline, not a product company and not a production crisis platform. Today it is worth prototype money. With validation, interface, security, and deployment work, it can move into low-six-figure pilot territory. Without that, it stays a polished internal demo. [MASTER SUMMARY]

• What is being built:
A single-file crisis triage research prototype for intake, rule-based signal extraction, urgency scoring, routing recommendations, audit logging, and retrospective review.

• What actually works:
CLI intake, deterministic regex-based feature extraction, weighted urgency scoring, routing logic, SQLite storage, JSONL audit logging, record export, demo mode, batch mode, interactive mode, summary reporting, calibration snapshot, policy object.

• What is unproven:
Clinical validity, real-world safety, benchmark quality, hotline workflow fit, procurement fit, deployment readiness, API/service operation, security controls, supervised model improvement, customer demand.

• What has real value:
Executable prototype, deterministic scoring pipeline, persistence layer, audit trail, reproducible demo workflow, pilot-ready concept packaging, reusable single-file decision-support architecture.

• What is noise:
SBIR/NIH framing by itself, commercialization claims without pilots, any suggestion of production clinical readiness, grant language that is not backed by validation, inflated product-company framing.

⸻

[COMPRESSED TRUTH — MAX 60 WORDS]

Aegis Triage is a working local prototype for crisis-message intake, explainable urgency scoring, routing, storage, and audit. Its value is the executable decision-support workflow, not the grant language. It is not clinically validated, secure, integrated, or production-ready. Today it is prototype infrastructure with pilot packaging, not a deployable crisis platform.

⸻

[GRANDMOTHER EXPLANATION — MAX 50 WORDS]

It reads crisis-related messages, scores how urgent they look, suggests where they should go, and saves everything for later review. It helps staff work more consistently. It does not replace trained people, and it is not ready for real clinical use without more testing and safety work.

⸻

[DOLLAR VIEW]

• Current realistic sale value: $8,000–$18,000
• If cleaned and deduplicated: $15,000–$30,000
• If proven with real usage: $60,000–$150,000

⸻

[PRODUCT SNAPSHOT]

• Product name: Aegis Triage
• One-line hook: Explainable crisis triage workflow prototype with audit trails
• What it does (brutal): Scores text-based crisis signals, recommends routing, stores every case, and produces reviewable records
• Who it’s for: Research teams, pilot programs, public-sector innovation groups, healthcare operations teams
• Why it’s different: Deterministic logic, full auditability, local deployability, single-file prototype packaging

⸻

[SALES PAGE — MINIMAL]

Headline:
Explainable Crisis Triage Prototype for Research and Pilot Workflows

Subheadline:
A deterministic intake, scoring, routing, and audit system for teams exploring crisis-support decision tools.

What you get:
• Single-file working prototype with CLI, storage, scoring, and routing
• SQLite case history and JSONL audit trail
• Demo, batch, export, summary, and calibration utilities

Proof (real only):
• Functional Python engine
• Persistent case storage
• Deterministic scoring and route assignment
• Repeatable demo and batch workflows

⸻

[PRICING STRATEGY]

• Anchor price: $24,000
• Realistic sell price: $9,500–$15,000
• Quick-sale price: $4,500–$7,500

⸻

[ASSET BREAKDOWN]

• Core file / system: aegis_triage.py
• Reusable modules: signal analyzer, urgency model, routing engine, SQLite store, audit logger, reporting loop, CLI shell, policy object
• Hidden value: explainable decision trail, pilot/demo readiness, reusable architecture for regulated workflow tooling, not just crisis use

⸻

[DELIVERABLES]

README.md

Title
Aegis Triage

One-line description
Deterministic crisis signal triage prototype with routing, storage, audit logging, and review reporting.

What it does
Processes text input, extracts rule-based risk signals, estimates urgency, recommends routing, [MASTER SUMMARY]

• What is being built:
A single-file crisis triage research prototype for intake, rule-based signal extraction, urgency scoring, routing recommendations, audit logging, and retrospective review.

• What actually works:
CLI intake, deterministic regex-based feature extraction, weighted urgency scoring, routing logic, SQLite storage, JSONL audit logging, record export, demo mode, batch mode, interactive mode, summary reporting, calibration snapshot, policy object.

• What is unproven:
Clinical validity, real-world safety, benchmark quality, hotline workflow fit, procurement fit, deployment readiness, API/service operation, security controls, supervised model improvement, customer demand.

• What has real value:
Executable prototype, deterministic scoring pipeline, persistence layer, audit trail, reproducible demo workflow, pilot-ready concept packaging, reusable single-file decision-support architecture.

• What is noise:
SBIR/NIH framing by itself, commercialization claims without pilots, any suggestion of production clinical readiness, grant language not backed by validation, inflated product-company framing.

⸻

[COMPRESSED TRUTH — MAX 60 WORDS]

Aegis Triage is a working local prototype for crisis-message intake, explainable urgency scoring, routing, storage, and audit. Its value is the executable decision-support workflow, not the grant framing. It is not clinically validated, secure, integrated, or production-ready. Today it is prototype infrastructure with pilot packaging, not a deployable crisis platform.

⸻

[GRANDMOTHER EXPLANATION — MAX 50 WORDS]

It reads crisis-related messages, estimates how urgent they seem, suggests where they should go, and saves everything for later review. It helps staff work more consistently. It does not replace trained people, and it is not ready for real clinical use without more testing and safety work.

⸻

[DOLLAR VIEW]

• Current realistic sale value:
$8,000–$18,000

• If cleaned and deduplicated:
$15,000–$30,000

• If proven with real usage:
$60,000–$150,000

⸻

[PRODUCT SNAPSHOT]

• Product name:
Aegis Triage

• One-line hook:
Explainable crisis triage workflow prototype with audit trails

• What it does (brutal):
Scores text-based crisis signals, recommends routing, stores every case, and produces reviewable records

• Who it’s for:
Research teams, pilot programs, public-sector innovation groups, healthcare operations teams

• Why it’s different:
Deterministic logic, full auditability, local deployability, single-file prototype packaging

⸻

[SALES PAGE — MINIMAL]

Headline:
Explainable Crisis Triage Prototype for Research and Pilot Workflows

Subheadline:
A deterministic intake, scoring, routing, and audit system for teams exploring crisis-support decision tools.

What you get:
• Single-file working prototype with CLI, storage, scoring, and routing
• SQLite case history and JSONL audit trail
• Demo, batch, export, summary, and calibration utilities

Proof (real only):
• Functional Python engine
• Persistent case storage
• Deterministic scoring and route assignment
• Repeatable demo and batch workflows

⸻

[PRICING STRATEGY]

• Anchor price:
$24,000

• Realistic sell price:
$9,500–$15,000

• Quick-sale price:
$4,500–$7,500

⸻

[ASSET BREAKDOWN]

• Core file / system:
aegis_triage.py

• Reusable modules:
signal analyzer, urgency model, routing engine, SQLite store, audit logger, reporting loop, CLI shell, policy object

• Hidden value:
Explainable decision trail, pilot/demo readiness, reusable architecture for regulated workflow tooling beyond crisis use

⸻

[DELIVERABLES]

README.md

Title
Aegis Triage

One-line description
Deterministic crisis signal triage prototype with routing, storage, audit logging, and review reporting.

What it does
Processes text input, extracts rule-based risk signals, estimates urgency, recommends routing, stores results, and supports later review and summary analysis.

How it works
• Ingests text cases from demo, interactive, or batch input
• Extracts crisis-related features with deterministic rules
• Scores urgency and confidence using weighted logic
• Produces routing recommendations with safety floors
• Stores all records in SQLite and JSONL for audit and review

Quick start

#### ChatGPT:
\==============================
MASTER LEDGER SNAPSHOT
======================

A-001 — Aegis Triage — AI / Agent System — Net Value: $8,000–$18,000

\[ASSET ID]

- A-001

\[NAME]

- Aegis Triage

\[TYPE]

- AI / Agent System

\[ORIGIN]

- Current chat
- Source input: aegis\_triage.py single-file prototype
- Added descriptive packaging layers: master summary, compressed truth, sales snapshot, pricing strategy, deliverables draft

\[FILES / SOURCES]

- aegis\_triage.py

\[DESCRIPTION]

- Single-file crisis-triage research prototype with:
  - deterministic regex-based signal extraction
  - weighted urgency scoring
  - routing recommendation engine
  - SQLite persistence
  - JSONL audit logging
  - CLI demo / batch / interactive flows
  - summary + calibration reporting
  - embedded NIH SBIR / pilot framing
- Supporting commercial packaging text exists, but it is wrapper value, not a second product.

\[STATUS]

- partial

\[COMPONENTS]

- Interface: CLI only
- Backend: local Python execution engine
- Logic: deterministic rules + weighted scoring
- Storage: SQLite + JSONL
- Reporting: summaries, exports, calibration buckets
- Integration: none beyond local file I/O
- Security: no auth, no encryption, no RBAC
- Product layer: research framing + light sales packaging

\[SCORING]

- Completeness: 3.5/5
- Execution Capability: 4.0/5
- Novelty: 2.0/5
- Monetization Potential: 2.5/5
- Production Readiness: 1.5/5

\[VALUE]

- Extractable Value: $18,000–$40,000
- Realistic Buyer Value: $8,000–$18,000
- Productized Value: $25,000–$70,000

\[OVERLAP]

- 70–85% overlap between code asset and added packaging/sales/summary material
- The added “master summary / compressed truth / sales page / pricing strategy / deliverables” is not a new standalone asset
- It is commercialization wrapper around A-001

\[NET NEW VALUE]

- $0–$2,000 incremental
- Most added text is packaging polish, not core technical expansion

\[DEPENDENCIES]

- labeled evaluation data
- clinical policy review
- reviewer workflow
- deployment/API layer
- security/compliance hardening
- real channel integrations
- benchmark process

\[BLOCKERS]

- no validation against real or labeled cases
- no clinical safety evidence
- no API/service layer
- no dashboard/operator UI
- no auth/RBAC/encryption
- no infrastructure/monitoring
- no procurement proof
- no pilots or users
- rule-based logic is inspectable but easy to replicate

---

PORTFOLIO TOTAL

- Gross Value (before deduplication): $8,000–$20,000
- Net Realistic Value: $8,000–$18,000
- Productized Portfolio Value: $25,000–$70,000

---

VALUE CHANGES FROM LAST STATE

- +$0–$2,000 added from new packaging assets
- -$0–$2,000 removed due to overlap and non-billable wrapper duplication
- Net change: $0

---

TOP VALUE DRIVERS

- A-001 core executable workflow
- A-001 persistence + audit trail
- A-001 deterministic and inspectable decision logic
- A-001 cleaner commercialization packaging for pilot/demo positioning

---

VALUE LEAKS

- packaging repeated across multiple sections without adding technical depth
- no new execution layer added
- no benchmark or validation asset added
- no UI/API/security layer added
- commercialization copy outruns proof
- grant framing still exceeds current maturity

---

SYSTEM STRUCTURE

Core assets

- A-001 Aegis Triage core engine
  - signal analyzer
  - urgency model
  - routing engine
  - SQLite store
  - audit trail
  - reporting loop
  - CLI shell
  - policy object

Supporting assets

- NIH SBIR concept framing
- demo case corpus
- product snapshot
- sales-page copy
- pricing strategy
- README draft text

Orphaned assets

- commercialization narrative without users or pilots
- pricing strategy without market validation
- “deliverables” text not yet materialized as files

---

HARD TRUTH

What actually has value:

- The executable Python prototype.
- The decision-support pipeline.
- The storage/audit architecture.
- The ability to demo, batch process, and export records.
- The fact that it is packaged coherently enough for pilot discussion.

What is noise:

- repeated summaries of the same system
- sales copy without buyer proof
- pricing theory without transactions
- NIH/SBIR language without external validation
- any hint that this is operationally ready for clinical deployment

What must be fixed to unlock next tier:

- build a web reviewer dashboard
- expose API/service endpoints
- add policy versioning
- create labeled evaluation dataset and benchmark suite
- add security controls and role separation
- add integration with intake channels
- add governance, override, and review workflow
- show one real pilot or buyer conversation

Bottom line:
There is still only one real asset here. The extra text improves packaging, not substance. The code is worth prototype money. The wrapper copy may help sell it, but it does not justify a second valuation pass. Until technical depth increases or external proof appears, value stays in the high-four to low-five figure prototype band.

---

\[MASTER SUMMARY]

- What is being built:
  A single-file crisis triage prototype for intake, rule-based feature extraction, urgency scoring, routing recommendations, storage, audit logging, and later review.

- What actually works:
  CLI intake, deterministic scoring, routing, SQLite persistence, JSONL audit logging, exports, demo mode, batch mode, interactive mode, summary reporting, calibration buckets, configurable policy object.

- What is unproven:
  Clinical validity, real-world safety, procurement fit, operational integration, benchmark quality, supervised improvement, deployment readiness, security posture, customer demand.

- What has real value:
  Executable workflow, inspectable decision logic, persistence, audit trail, reusable prototype architecture, decent pilot/demo packaging.

- What is noise:
  Repeated framing, pricing copy, commercialization claims without proof, and grant language not backed by validation.

---

\[COMPRESSED TRUTH — MAX 60 WORDS]

Aegis Triage is a working local prototype for crisis-message intake, explainable scoring, routing, storage, and audit. Its value is the executable decision-support workflow. The added packaging helps positioning but does not create a second asset. It is not validated, secure, integrated, or production-ready.

---

\[GRANDMOTHER EXPLANATION — MAX 50 WORDS]

It reads messages, estimates how urgent they seem, suggests where they should go, and saves the results for later review. It can help people work more consistently, but it still needs testing, safety controls, and real-world proof before anyone should trust it in serious clinical settings.

---

\[DOLLAR VIEW]

- Current realistic sale value: $8,000–$18,000
- If cleaned and deduplicated into a tight package: $15,000–$30,000
- If validated with real usage and proper controls: $60,000–$150,000

---

\[PRICING STRATEGY]

- Anchor price: $20,000–$24,000
- Realistic sell price: $9,500–$15,000
- Quick-sale price: $4,500–$7,500

---

\[MERGE RULE APPLIED]

- README draft, sales page, pricing notes, product snapshot, compressed truth, and master summary were merged into A-001 as supporting packaging.
- No second asset created.
- No double counting applied.
