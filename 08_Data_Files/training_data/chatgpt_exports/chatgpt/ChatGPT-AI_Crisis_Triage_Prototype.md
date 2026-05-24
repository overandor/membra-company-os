# AI Crisis Triage Prototype

#### You:
Conrinue this #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
═══════════════════════════════════════════════════════════════════════════════
AI CRISIS TRIAGE SYSTEM — NIH SBIR SINGLE-FILE PACKAGE
═══════════════════════════════════════════════════════════════════════════════

This file contains BOTH:
1) Grant-ready NIH SBIR concept
2) Functional prototype scaffold

Designed for:
- Real-time crisis triage (988-style systems)
- AI decision support under uncertainty
- Human-in-the-loop infrastructure

═══════════════════════════════════════════════════════════════════════════════
"""

# =============================================================================
# SECTION 1 — NIH SBIR CONCEPT
# =============================================================================

PROJECT_TITLE = """
AI-Driven Real-Time Crisis Triage and Decision Support System
"""

PROJECT_SUMMARY = """
Crisis response systems such as the 988 Suicide & Crisis Lifeline are facing
increasing demand, limited staffing scalability, and lack of adaptive triage.

This project proposes a real-time AI decision engine that:
- scores urgency dynamically
- routes cases intelligently
- assists human operators
- continuously improves via feedback loops

Goal:
Improve response time, accuracy, and system scalability.
"""

SPECIFIC_AIMS = [
    "Build real-time signal ingestion pipeline",
    "Develop adaptive risk scoring model",
    "Implement AI-assisted routing engine",
    "Create feedback-driven learning system"
]

INNOVATION = [
    "Real-time triage under uncertainty",
    "Human-in-the-loop AI decision system",
    "Outcome-driven learning architecture",
    "Latency-aware design for crisis systems"
]

TECHNICAL_RISKS = [
    "False positives in risk scoring",
    "Latency constraints",
    "Data sparsity and noise",
    "Integration with human workflows"
]

COMMERCIALIZATION = [
    "Government crisis systems",
    "Healthcare providers",
    "Emergency communication platforms",
    "AI decision infrastructure markets"
]

# =============================================================================
# SECTION 2 — ARCHITECTURE
# =============================================================================

"""
System Components:

1. Signal Ingestion
2. Risk Scoring Engine
3. Decision Engine
4. Feedback Learning Loop
5. Audit & Logging Layer
"""

# =============================================================================
# SECTION 3 — PYTHON PROTOTYPE
# =============================================================================

import time
import random
from dataclasses import dataclass, field
from typing import Dict, Any


# -----------------------------------------------------------------------------
# DATA MODELS
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# SIGNAL INGESTION
# -----------------------------------------------------------------------------

class SignalIngestion:

    def ingest(self, raw_input: str) -> CrisisSignal:
        return CrisisSignal(
            timestamp=time.time(),
            message=raw_input,
            metadata={"length": len(raw_input)}
        )


# -----------------------------------------------------------------------------
# RISK ENGINE
# -----------------------------------------------------------------------------

class RiskEngine:

    def score(self, signal: CrisisSignal) -> RiskScore:
        base = len(signal.message) / 100

        # Simulated heuristic
        urgency = min(1.0, base + random.uniform(0, 0.5))
        confidence = random.uniform(0.6, 0.95)

        return RiskScore(urgency=urgency, confidence=confidence)


# -----------------------------------------------------------------------------
# DECISION ENGINE
# -----------------------------------------------------------------------------

class DecisionEngine:

    def decide(self, risk: RiskScore) -> Decision:

        if risk.urgency > 0.8:
            return Decision("HIGH", "IMMEDIATE_AGENT", "High urgency detected")

        elif risk.urgency > 0.5:
            return Decision("MEDIUM", "QUEUE_PRIORITY", "Moderate urgency")

        return Decision("LOW", "STANDARD_QUEUE", "Low urgency")


# -----------------------------------------------------------------------------
# LEARNING LOOP
# -----------------------------------------------------------------------------

class FeedbackEngine:

    def update(self, signal: CrisisSignal, outcome: str):
        print(f"[LEARNING] Updating model with outcome={outcome}")


# -----------------------------------------------------------------------------
# MAIN SYSTEM
# -----------------------------------------------------------------------------

class CrisisAIEngine:

    def __init__(self):
        self.ingestion = SignalIngestion()
        self.risk = RiskEngine()
        self.decision = DecisionEngine()
        self.feedback = FeedbackEngine()

    def process(self, raw_input: str):

        signal = self.ingestion.ingest(raw_input)
        risk = self.risk.score(signal)
        decision = self.decision.decide(risk)

        self.log(signal, risk, decision)

        return decision

    def log(self, signal, risk, decision):
        print("──────────────")
        print(f"INPUT: {signal.message}")
        print(f"URGENCY: {risk.urgency:.2f}")
        print(f"DECISION: {decision.priority}")
        print(f"ROUTE: {decision.route_to}")
        print("──────────────")


# =============================================================================
# SECTION 4 — MILESTONES (GRANT-CRITICAL)
# =============================================================================

MILESTONES = [
    "Prototype ingestion pipeline",
    "Risk model baseline validation",
    "Decision routing simulation",
    "Human feedback integration",
    "Performance benchmarking"
]

# =============================================================================
# SECTION 5 — BUDGET LOGIC (SIMPLIFIED)
# =============================================================================

BUDGET = {
    "engineering": 60000,
    "compute": 10000,
    "data": 10000,
    "misc": 20000
}

# =============================================================================
# SECTION 6 — EXECUTION
# =============================================================================

def main():

    engine = CrisisAIEngine()

    test_inputs = [
       K

#### ChatGPT:
I’m turning your scaffold into a fuller single-file prototype: finishing the runner, adding safer deterministic scoring, audit logging, feedback storage, simple benchmarking, and a grant-style output section.


#### ChatGPT:
Here’s a continued and polished version of your file, keeping it single-file and executable while making it much more complete as a prototype.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
═══════════════════════════════════════════════════════════════════════════════
AI CRISIS TRIAGE SYSTEM — NIH SBIR SINGLE-FILE PACKAGE
═══════════════════════════════════════════════════════════════════════════════

This file contains BOTH:
1) Grant-ready NIH SBIR concept
2) Functional prototype scaffold

Designed for:
- Real-time crisis triage (988-style systems)
- AI decision support under uncertainty
- Human-in-the-loop infrastructure

IMPORTANT:
- This is a prototype decision-support scaffold, not a clinical device.
- It is not a substitute for licensed clinical judgment or emergency response.
- Any real deployment in crisis settings requires expert validation, security,
  privacy review, human oversight, and formal testing.

═══════════════════════════════════════════════════════════════════════════════
"""

# =============================================================================
# SECTION 1 — NIH SBIR CONCEPT
# =============================================================================

PROJECT_TITLE = """
AI-Driven Real-Time Crisis Triage and Decision Support System
"""

PROJECT_SUMMARY = """
Crisis response systems such as the 988 Suicide & Crisis Lifeline are facing
increasing demand, limited staffing scalability, and lack of adaptive triage.

This project proposes a real-time AI decision engine that:
- scores urgency dynamically
- routes cases intelligently
- assists human operators
- continuously improves via feedback loops

Goal:
Improve response time, accuracy, and system scalability.
"""

SPECIFIC_AIMS = [
    "Build real-time signal ingestion pipeline",
    "Develop adaptive risk scoring model",
    "Implement AI-assisted routing engine",
    "Create feedback-driven learning system",
]

INNOVATION = [
    "Real-time triage under uncertainty",
    "Human-in-the-loop AI decision system",
    "Outcome-driven learning architecture",
    "Latency-aware design for crisis systems",
]

TECHNICAL_RISKS = [
    "False positives in risk scoring",
    "False negatives in risk scoring",
    "Latency constraints",
    "Data sparsity and noise",
    "Integration with human workflows",
    "Operator trust and explainability requirements",
]

COMMERCIALIZATION = [
    "Government crisis systems",
    "Healthcare providers",
    "Emergency communication platforms",
    "AI decision infrastructure markets",
]

EXPECTED_IMPACT = [
    "Reduce queue misprioritization",
    "Improve operator support under high load",
    "Create auditable triage recommendations",
    "Provide measurable feedback loops for system improvement",
]

# =============================================================================
# SECTION 2 — ARCHITECTURE
# =============================================================================

"""
System Components:

1. Signal Ingestion
2. Feature Extraction
3. Risk Scoring Engine
4. Decision Engine
5. Human Override / Feedback Loop
6. Audit & Logging Layer
7. Benchmark / Simulation Harness
"""

# =============================================================================
# SECTION 3 — IMPORTS
# =============================================================================

import csv
import json
import math
import os
import re
import statistics
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# SECTION 4 — CONFIGURATION
# =============================================================================

APP_NAME = "ai_crisis_triage_system"
DATA_DIR = Path(os.getenv("CRISIS_AI_DATA_DIR", "./crisis_ai_data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

EVENT_LOG_PATH = DATA_DIR / "events.jsonl"
FEEDBACK_LOG_PATH = DATA_DIR / "feedback.jsonl"
BENCHMARK_CSV_PATH = DATA_DIR / "benchmark_results.csv"

CONFIG = {
    "high_threshold": 0.85,
    "medium_threshold": 0.55,
    "human_review_threshold": 0.40,
    "min_confidence_for_direct_high": 0.65,
    "enable_human_review": True,
    "enable_learning_log": True,
    "max_message_chars": 5000,
}

# Lexicons are prototype-only heuristics. In production, these would be
# replaced or complemented by validated models and governance controls.
HIGH_RISK_PHRASES = [
    "kill myself",
    "want to die",
    "end my life",
    "suicide",
    "can't go on",
    "overdose",
    "hurt myself",
    "self harm",
    "self-harm",
    "have a gun",
    "have pills",
    "going to die tonight",
    "i will die",
    "i'm going to do it",
]

MEDIUM_RISK_PHRASES = [
    "hopeless",
    "worthless",
    "panic attack",
    "can't breathe",
    "hearing voices",
    "nobody cares",
    "i'm scared",
    "i'm alone",
    "breakdown",
    "abuse",
    "unsafe",
    "threatened",
]

PROTECTIVE_PHRASES = [
    "want help",
    "need help",
    "please help",
    "calling for support",
    "reaching out",
    "talk to someone",
    "stay safe",
    "friend is with me",
    "family is here",
]

URGENCY_MARKERS = [
    "right now",
    "tonight",
    "immediately",
    "urgent",
    "now",
    "asap",
]

# =============================================================================
# SECTION 5 — DATA MODELS
# =============================================================================

@dataclass
class CrisisSignal:
    timestamp: float
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedFeatures:
    message_length: int
    high_risk_hits: List[str]
    medium_risk_hits: List[str]
    protective_hits: List[str]
    urgency_hits: List[str]
    exclamation_count: int
    uppercase_ratio: float
    contains_plan_like_language: bool
    contains_time_reference: bool
    distress_score_proxy: float
    feature_version: str = "v1"


@dataclass
class RiskScore:
    urgency: float
    confidence: float
    severity_band: str
    factors: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    priority: str
    route_to: str
    explanation: str
    requires_human_review: bool
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class FeedbackRecord:
    timestamp: float
    message: str
    decision_priority: str
    routed_to: str
    operator_outcome: str
    operator_notes: str = ""


@dataclass
class SystemMetrics:
    processed_count: int = 0
    avg_urgency: float = 0.0
    high_priority_count: int = 0
    medium_priority_count: int = 0
    low_priority_count: int = 0
    review_count: int = 0


# =============================================================================
# SECTION 6 — UTILITY FUNCTIONS
# =============================================================================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def safe_text(text: str, max_len: int) -> str:
    text = (text or "").strip()
    return text[:max_len]


def tokenize_lower(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def write_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def append_csv_row(path: Path, row: Dict[str, Any], header: Optional[List[str]] = None) -> None:
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header or list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


# =============================================================================
# SECTION 7 — FEATURE EXTRACTION
# =============================================================================

class FeatureExtractor:
    def __init__(self) -> None:
        self.high_risk_phrases = HIGH_RISK_PHRASES
        self.medium_risk_phrases = MEDIUM_RISK_PHRASES
        self.protective_phrases = PROTECTIVE_PHRASES
        self.urgency_markers = URGENCY_MARKERS

    def _find_hits(self, text: str, phrases: List[str]) -> List[str]:
        hits = []
        for phrase in phrases:
            if phrase in text:
                hits.append(phrase)
        return hits

    def _uppercase_ratio(self, original_text: str) -> float:
        letters = [c for c in original_text if c.isalpha()]
        if not letters:
            return 0.0
        upper = sum(1 for c in letters if c.isupper())
        return upper / len(letters)

    def _contains_plan_like_language(self, text: str) -> bool:
        patterns = [
            r"\bgun\b",
            r"\bpills?\b",
            r"\bknife\b",
            r"\brope\b",
            r"\boverdose\b",
            r"\bbridge\b",
            r"\btonight\b",
            r"\bright now\b",
            r"\bwhen everyone sleeps\b",
        ]
        return any(re.search(p, text) for p in patterns)

    def _contains_time_reference(self, text: str) -> bool:
        patterns = [
            r"\bnow\b",
            r"\bright now\b",
            r"\btonight\b",
            r"\btoday\b",
            r"\bimmediately\b",
            r"\bwithin an hour\b",
        ]
        return any(re.search(p, text) for p in patterns)

    def extract(self, signal: CrisisSignal) -> ExtractedFeatures:
        normalized = tokenize_lower(signal.message)
        exclamations = signal.message.count("!")
        upper_ratio = self._uppercase_ratio(signal.message)

        high_hits = self._find_hits(normalized, self.high_risk_phrases)
        medium_hits = self._find_hits(normalized, self.medium_risk_phrases)
        protective_hits = self._find_hits(normalized, self.protective_phrases)
        urgency_hits = self._find_hits(normalized, self.urgency_markers)

        contains_plan_like_language = self._contains_plan_like_language(normalized)
        contains_time_reference = self._contains_time_reference(normalized)

        distress_score_proxy = clamp(
            (
                len(high_hits) * 0.35
                + len(medium_hits) * 0.12
                + len(urgency_hits) * 0.15
                + (0.10 if contains_plan_like_language else 0.0)
                + (0.05 if contains_time_reference else 0.0)
                + min(exclamations, 5) * 0.01
                + min(upper_ratio, 0.5) * 0.10
                - len(protective_hits) * 0.07
            ),
            0.0,
            1.0,
        )

        return ExtractedFeatures(
            message_length=len(signal.message),
            high_risk_hits=high_hits,
            medium_risk_hits=medium_hits,
            protective_hits=protective_hits,
            urgency_hits=urgency_hits,
            exclamation_count=exclamations,
            uppercase_ratio=upper_ratio,
            contains_plan_like_language=contains_plan_like_language,
            contains_time_reference=contains_time_reference,
            distress_score_proxy=distress_score_proxy,
        )


# =============================================================================
# SECTION 8 — SIGNAL INGESTION
# =============================================================================

class SignalIngestion:
    def ingest(self, raw_input: str, source: str = "text_console") -> CrisisSignal:
        clean = safe_text(raw_input, CONFIG["max_message_chars"])
        return CrisisSignal(
            timestamp=time.time(),
            message=clean,
            metadata={
                "length": len(clean),
                "source": source,
                "received_at": utc_now_iso(),
            },
        )


# =============================================================================
# SECTION 9 — RISK ENGINE
# =============================================================================

class RiskEngine:
    def score(self, signal: CrisisSignal, features: ExtractedFeatures) -> RiskScore:
        # Deterministic weighted heuristic prototype.
        urgency = 0.0

        urgency += min(features.message_length / 800.0, 0.10)
        urgency += len(features.high_risk_hits) * 0.28
        urgency += len(features.medium_risk_hits) * 0.10
        urgency += len(features.urgency_hits) * 0.10

        if features.contains_plan_like_language:
            urgency += 0.18

        if features.contains_time_reference:
            urgency += 0.08

        urgency += min(features.exclamation_count, 5) * 0.01
        urgency += min(features.uppercase_ratio, 0.6) * 0.08
        urgency -= len(features.protective_hits) * 0.05

        urgency = clamp(urgency)

        signal_density = (
            len(features.high_risk_hits)
            + len(features.medium_risk_hits)
            + len(features.urgency_hits)
            + (1 if features.contains_plan_like_language else 0)
        )
        confidence = clamp(0.50 + min(signal_density * 0.08, 0.35) + min(features.message_length / 3000.0, 0.08))

        if urgency >= CONFIG["high_threshold"]:
            severity_band = "SEVERE"
        elif urgency >= CONFIG["medium_threshold"]:
            severity_band = "ELEVATED"
        else:
            severity_band = "LOWER"

        factors = {
            "high_risk_hits": features.high_risk_hits,
            "medium_risk_hits": features.medium_risk_hits,
            "protective_hits": features.protective_hits,
            "urgency_hits": features.urgency_hits,
            "contains_plan_like_language": features.contains_plan_like_language,
            "contains_time_reference": features.contains_time_reference,
            "distress_score_proxy": features.distress_score_proxy,
            "uppercase_ratio": round(features.uppercase_ratio, 4),
            "message_length": features.message_length,
        }

        return RiskScore(
            urgency=urgency,
            confidence=confidence,
            severity_band=severity_band,
            factors=factors,
        )


# =============================================================================
# SECTION 10 — DECISION ENGINE
# =============================================================================

class DecisionEngine:
    def decide(self, risk: RiskScore) -> Decision:
        urgency = risk.urgency
        confidence = risk.confidence

        if urgency >= CONFIG["high_threshold"] and confidence >= CONFIG["min_confidence_for_direct_high"]:
            return Decision(
                priority="HIGH",
                route_to="IMMEDIATE_AGENT",
                explanation="Severe urgency with sufficient confidence. Immediate human escalation recommended.",
                requires_human_review=True,
                recommended_actions=[
                    "Escalate to live crisis specialist immediately",
                    "Preserve audit trail",
                    "Surface high-risk factors to operator",
                    "Minimize routing delay",
                ],
            )

        if urgency >= CONFIG["medium_threshold"]:
            return Decision(
                priority="MEDIUM",
                route_to="QUEUE_PRIORITY",
                explanation="Elevated urgency detected. Prioritize for rapid human review.",
                requires_human_review=True,
                recommended_actions=[
                    "Move to priority queue",
                    "Display supportive operator guidance",
                    "Request operator validation",
                ],
            )

        if urgency >= CONFIG["human_review_threshold"] and CONFIG["enable_human_review"]:
            return Decision(
                priority="LOW-MODERATE",
                route_to="REVIEW_QUEUE",
                explanation="Moderate uncertainty or mild distress signals detected. Human review recommended.",
                requires_human_review=True,
                recommended_actions=[
                    "Place in supervised review queue",
                    "Collect additional clarifying context",
                ],
            )

        return Decision(
            priority="LOW",
            route_to="STANDARD_QUEUE",
            explanation="No strong acute risk markers detected in prototype scoring.",
            requires_human_review=False,
            recommended_actions=[
                "Standard queue placement",
                "Continue passive monitoring if available",
            ],
        )


# =============================================================================
# SECTION 11 — FEEDBACK / LEARNING LOOP
# =============================================================================

class FeedbackEngine:
    def __init__(self) -> None:
        self.records: List[FeedbackRecord] = []

    def update(
        self,
        signal: CrisisSignal,
        decision: Decision,
        outcome: str,
        operator_notes: str = "",
    ) -> FeedbackRecord:
        record = FeedbackRecord(
            timestamp=time.time(),
            message=signal.message,
            decision_priority=decision.priority,
            routed_to=decision.route_to,
            operator_outcome=outcome,
            operator_notes=operator_notes,
        )
        self.records.append(record)

        if CONFIG["enable_learning_log"]:
            write_jsonl(FEEDBACK_LOG_PATH, asdict(record))

        return record


# =============================================================================
# SECTION 12 — AUDIT LOGGER
# =============================================================================

class AuditLogger:
    def log_event(
        self,
        signal: CrisisSignal,
        features: ExtractedFeatures,
        risk: RiskScore,
        decision: Decision,
    ) -> None:
        payload = {
            "event_type": "triage_decision",
            "created_at": utc_now_iso(),
            "signal": asdict(signal),
            "features": asdict(features),
            "risk": asdict(risk),
            "decision": asdict(decision),
        }
        write_jsonl(EVENT_LOG_PATH, payload)

    def print_human_readable(
        self,
        signal: CrisisSignal,
        features: ExtractedFeatures,
        risk: RiskScore,
        decision: Decision,
    ) -> None:
        print("════════════════════════════════════════════════════════════")
        print(f"TIME:       {utc_now_iso()}")
        print(f"INPUT:      {signal.message}")
        print(f"LENGTH:     {features.message_length}")
        print(f"URGENCY:    {risk.urgency:.2f}")
        print(f"CONFIDENCE: {risk.confidence:.2f}")
        print(f"BAND:       {risk.severity_band}")
        print(f"PRIORITY:   {decision.priority}")
        print(f"ROUTE:      {decision.route_to}")
        print(f"EXPLAIN:    {decision.explanation}")
        print(f"HIGH HITS:  {features.high_risk_hits}")
        print(f"MEDIUM:     {features.medium_risk_hits}")
        print(f"PROTECTIVE: {features.protective_hits}")
        print(f"URGENT:     {features.urgency_hits}")
        print(f"REVIEW:     {decision.requires_human_review}")
        if decision.recommended_actions:
            print("ACTIONS:")
            for item in decision.recommended_actions:
                print(f"  - {item}")
        print("════════════════════════════════════════════════════════════")


# =============================================================================
# SECTION 13 — METRICS
# =============================================================================

class MetricsTracker:
    def __init__(self) -> None:
        self.urgency_values: List[float] = []
        self.metrics = SystemMetrics()

    def update(self, risk: RiskScore, decision: Decision) -> None:
        self.metrics.processed_count += 1
        self.urgency_values.append(risk.urgency)

        if decision.priority == "HIGH":
            self.metrics.high_priority_count += 1
        elif decision.priority == "MEDIUM":
            self.metrics.medium_priority_count += 1
        else:
            self.metrics.low_priority_count += 1

        if decision.requires_human_review:
            self.metrics.review_count += 1

        self.metrics.avg_urgency = statistics.mean(self.urgency_values) if self.urgency_values else 0.0

    def snapshot(self) -> Dict[str, Any]:
        return {
            "processed_count": self.metrics.processed_count,
            "avg_urgency": round(self.metrics.avg_urgency, 4),
            "high_priority_count": self.metrics.high_priority_count,
            "medium_priority_count": self.metrics.medium_priority_count,
            "low_priority_count": self.metrics.low_priority_count,
            "review_count": self.metrics.review_count,
        }


# =============================================================================
# SECTION 14 — MAIN SYSTEM
# =============================================================================

class CrisisAIEngine:
    def __init__(self) -> None:
        self.ingestion = SignalIngestion()
        self.extractor = FeatureExtractor()
        self.risk = RiskEngine()
        self.decision = DecisionEngine()
        self.feedback = FeedbackEngine()
        self.logger = AuditLogger()
        self.metrics = MetricsTracker()

    def process(self, raw_input: str, source: str = "text_console") -> Dict[str, Any]:
        signal = self.ingestion.ingest(raw_input, source=source)
        features = self.extractor.extract(signal)
        risk = self.risk.score(signal, features)
        decision = self.decision.decide(risk)

        self.logger.log_event(signal, features, risk, decision)
        self.logger.print_human_readable(signal, features, risk, decision)
        self.metrics.update(risk, decision)

        return {
            "signal": signal,
            "features": features,
            "risk": risk,
            "decision": decision,
        }

    def submit_feedback(
        self,
        signal: CrisisSignal,
        decision: Decision,
        outcome: str,
        operator_notes: str = "",
    ) -> FeedbackRecord:
        record = self.feedback.update(signal, decision, outcome, operator_notes)
        print(f"[LEARNING] Recorded feedback outcome={outcome}")
        return record

    def health(self) -> Dict[str, Any]:
        return {
            "app": APP_NAME,
            "status": "ok",
            "timestamp": utc_now_iso(),
            "metrics": self.metrics.snapshot(),
            "paths": {
                "event_log": str(EVENT_LOG_PATH),
                "feedback_log": str(FEEDBACK_LOG_PATH),
                "benchmark_csv": str(BENCHMARK_CSV_PATH),
            },
        }


# =============================================================================
# SECTION 15 — BENCHMARK / SIMULATION HARNESS
# =============================================================================

class BenchmarkHarness:
    def __init__(self, engine: CrisisAIEngine) -> None:
        self.engine = engine

    def run(self, cases: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        cases: list of (message, expected_priority_group)
        expected_priority_group ∈ {"HIGH", "MEDIUM", "LOW"}
        """
        total = 0
        correct = 0
        results = []

        for idx, (message, expected) in enumerate(cases, start=1):
            bundle = self.engine.process(message, source="benchmark")
            actual = bundle["decision"].priority
            normalized_actual = "LOW" if actual in {"LOW", "LOW-MODERATE"} else actual
            hit = int(normalized_actual == expected)

            row = {
                "case_id": idx,
                "timestamp": utc_now_iso(),
                "message": message,
                "expected": expected,
                "actual": actual,
                "urgency": round(bundle["risk"].urgency, 4),
                "confidence": round(bundle["risk"].confidence, 4),
                "correct": hit,
            }
            append_csv_row(BENCHMARK_CSV_PATH, row)
            results.append(row)

            total += 1
            correct += hit

        accuracy = (correct / total) if total else 0.0
        summary = {
            "total_cases": total,
            "correct": correct,
            "accuracy": round(accuracy, 4),
            "output_csv": str(BENCHMARK_CSV_PATH),
        }
        return {
            "summary": summary,
            "results": results,
        }


# =============================================================================
# SECTION 16 — MILESTONES (GRANT-CRITICAL)
# =============================================================================

MILESTONES = [
    "Prototype ingestion pipeline",
    "Risk model baseline validation",
    "Decision routing simulation",
    "Human feedback integration",
    "Performance benchmarking",
    "Explainability and audit logging",
    "Human-override workflow testing",
]

PHASE_I_OBJECTIVES = [
    "Demonstrate functioning prototype for text-based triage",
    "Establish initial risk-scoring baseline",
    "Generate audit-ready routing outputs",
    "Create benchmark harness with labeled scenarios",
    "Document human review integration points",
]

PHASE_II_DIRECTION = [
    "Integrate multimodal signals where permitted",
    "Conduct validation with domain experts",
    "Add secure deployment architecture",
    "Measure latency and operator workflow outcomes",
]

# =============================================================================
# SECTION 17 — BUDGET LOGIC (SIMPLIFIED)
# =============================================================================

BUDGET = {
    "engineering": 60000,
    "compute": 10000,
    "data": 10000,
    "security_privacy": 15000,
    "clinical_advisory": 20000,
    "misc": 20000,
}

def total_budget(budget: Dict[str, int]) -> int:
    return sum(budget.values())


# =============================================================================
# SECTION 18 — REPORTING HELPERS
# =============================================================================

def print_project_brief() -> None:
    print("\n" + "═" * 75)
    print(PROJECT_TITLE.strip())
    print("═" * 75)
    print(PROJECT_SUMMARY.strip())
    print("\nSPECIFIC AIMS:")
    for item in SPECIFIC_AIMS:
        print(f"  - {item}")

    print("\nINNOVATION:")
    for item in INNOVATION:
        print(f"  - {item}")

    print("\nTECHNICAL RISKS:")
    for item in TECHNICAL_RISKS:
        print(f"  - {item}")

    print("\nCOMMERCIALIZATION:")
    for item in COMMERCIALIZATION:
        print(f"  - {item}")

    print("\nEXPECTED IMPACT:")
    for item in EXPECTED_IMPACT:
        print(f"  - {item}")

    print("\nPHASE I OBJECTIVES:")
    for item in PHASE_I_OBJECTIVES:
        print(f"  - {item}")

    print("\nPHASE II DIRECTION:")
    for item in PHASE_II_DIRECTION:
        print(f"  - {item}")

    print("\nBUDGET:")
    for k, v in BUDGET.items():
        print(f"  - {k}: ${v:,.0f}")
    print(f"TOTAL: ${total_budget(BUDGET):,.0f}")
    print("═" * 75 + "\n")


def print_health(engine: CrisisAIEngine) -> None:
    print(json.dumps(engine.health(), indent=2))


# =============================================================================
# SECTION 19 — EXECUTION
# =============================================================================

def main() -> None:
    print_project_brief()

    engine = CrisisAIEngine()

    test_inputs = [
        "I feel overwhelmed and alone. I don't know what to do.",
        "I want to die tonight and I have pills with me.",
        "Please help me. I am panicking right now.",
        "My friend is here with me and I want support before things get worse.",
        "Everything is bad but I am just looking for someone to talk to.",
        "I can't go on anymore. I have a gun and I might do it now.",
    ]

    processed_bundles = []

    print("RUNNING SAMPLE TRIAGE CASES...\n")
    for message in test_inputs:
        bundle = engine.process(message)
        processed_bundles.append(bundle)
        time.sleep(0.05)

    print("\nRECORDING SAMPLE FEEDBACK...\n")
    if processed_bundles:
        engine.submit_feedback(
            processed_bundles[0]["signal"],
            processed_bundles[0]["decision"],
            outcome="operator_reviewed_low_to_moderate_distress",
            operator_notes="Caller expressed distress but no immediate plan or means disclosed.",
        )
        engine.submit_feedback(
            processed_bundles[1]["signal"],
            processed_bundles[1]["decision"],
            outcome="operator_confirmed_high_risk_escalation",
            operator_notes="Immediate live escalation was appropriate.",
        )

    print("\nRUNNING BENCHMARK HARNESS...\n")
    benchmark_cases = [
        ("I want to die and I have pills right now.", "HIGH"),
        ("I'm scared, unsafe, and I need help immediately.", "MEDIUM"),
        ("I feel down and need someone to talk to.", "LOW"),
        ("I have a gun and I'm going to do it tonight.", "HIGH"),
        ("I feel hopeless and alone.", "MEDIUM"),
        ("My family is here and I want support.", "LOW"),
    ]
    benchmark = BenchmarkHarness(engine).run(benchmark_cases)
    print(json.dumps(benchmark["summary"], indent=2))

    print("\nSYSTEM HEALTH...\n")
    print_health(engine)

    print("\nFILES WRITTEN:")
    print(f"  - Event log:     {EVENT_LOG_PATH}")
    print(f"  - Feedback log:  {FEEDBACK_LOG_PATH}")
    print(f"  - Benchmark CSV: {BENCHMARK_CSV_PATH}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
```

What I added:

- completed `test_inputs` and `main()`
- replaced random scoring with deterministic heuristic scoring
- added feature extraction
- added explainable factors
- added audit logging to JSONL
- added feedback logging
- added simple metrics and health output
- added benchmark harness and CSV export
- kept it single-file and runnable

One important note: for a real 988 or emergency-adjacent workflow, this would still need:

- formal clinical review
- privacy/security layer
- real API/server infrastructure
- authentication and access controls
- validated datasets
- human override guarantees
- legal and compliance review

I can also turn this into a much more production-style single-file next, with:

- FastAPI HTTP service
- SQLite persistence
- REST endpoints for `/triage`, `/feedback`, `/health`
- config class
- structured logging
- unit-testable components


#### You:
Outrerform and reprint this #!/usr/bin/env python3
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

#### ChatGPT:
Below is a stronger, cleaner reprint of your file with tighter structure, safer research framing, better persistence hygiene, deterministic scoring cleanup, improved CLI, policy/report helpers, and more polished output.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
════════════════════════════════════════════════════════════════════════════════
AI CRISIS TRIAGE SYSTEM — NIH SBIR RESEARCH SINGLE-FILE PACKAGE
════════════════════════════════════════════════════════════════════════════════

PURPOSE
-------
This file combines:
1) A grant-style NIH SBIR concept package
2) A functional research prototype for AI-assisted crisis triage

INTENDED USE
------------
This prototype is designed for research, simulation, workflow testing, and
human-in-the-loop decision support. It is NOT intended to be the sole basis
for clinical, hotline, dispatch, or emergency decision-making. Final decisions
must remain with qualified human professionals operating under approved policy,
governance, training, supervision, and legal/compliance review.

DESIGN GOALS
------------
- Deterministic, explainable scoring
- Human-in-the-loop routing recommendations
- Auditability and reproducibility
- SQLite-backed persistence
- Research-ready extensibility
- Single-file deployment simplicity
- Clean CLI for demo, interactive, and batch workflows

SUPPORTED MODES
---------------
- Demo mode with built-in scenarios
- Interactive console mode
- Batch JSONL input mode
- Summary/report export
- SQLite-backed persistence
- JSON export and CSV summary export

EXAMPLE USAGE
-------------
python crisis_triage_sbir.py --demo
python crisis_triage_sbir.py --interactive
python crisis_triage_sbir.py --batch cases.jsonl
python crisis_triage_sbir.py --summary
python crisis_triage_sbir.py --export-records records.json
python crisis_triage_sbir.py --export-summary summary.csv
python crisis_triage_sbir.py --print-concept

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
- Calibration statistics
- CLI and persistence infrastructure

IMPORTANT SAFETY NOTE
---------------------
This is a prototype research tool. Real deployment in crisis environments would
require domain expert validation, secure architecture, rigorous evaluation,
formal human oversight, privacy review, compliance controls, and approved
operational protocols.
════════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import statistics
import sys
import textwrap
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# SECTION 1 — NIH SBIR CONCEPT
# =============================================================================

PROJECT_TITLE = "AI-Driven Real-Time Crisis Triage and Decision Support System"

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
    "False positives from metaphorical, quoted, or indirect language.",
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

@dataclass(frozen=True)
class PolicyConfig:
    name: str = "default"

    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    low_confidence_floor: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    emergency_route: str = "EMERGENCY_DISPATCH"
    immediate_route: str = "IMMEDIATE_CLINICIAN"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "QUEUE_PRIORITY"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

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

    confidence_base: float = 0.50
    confidence_per_feature_type: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_structured_metadata: float = 0.05

    require_human_review_for_all_high: bool = True
    route_low_confidence_to_human: bool = True
    never_auto_downgrade_self_harm: bool = True
    never_auto_downgrade_violence: bool = True


def load_policy(policy_name: str = "default") -> PolicyConfig:
    # Placeholder for future multi-policy loading from JSON or DB.
    # Kept deterministic and local for prototype reliability.
    return PolicyConfig(name=policy_name)


# =============================================================================
# SECTION 3 — UTILITIES
# =============================================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def normalize_whitespace(text: str) -> str:
    return " ".join((text or "").split())


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def stable_case_id(message: str, ts: float) -> str:
    digest = hashlib.sha256(f"{ts}:{message}".encode("utf-8")).hexdigest()[:16]
    return f"case_{digest}"


def ensure_parent_dir(path: str) -> None:
    parent = Path(path).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


def bool_from_env(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=False)


# =============================================================================
# SECTION 4 — DATA MODELS
# =============================================================================

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
        groups = (
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
        )
        return sum(len(g) for g in groups)

    def active_feature_groups(self) -> int:
        groups = (
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
        )
        return sum(1 for g in groups if g)


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
# SECTION 5 — FEATURE EXTRACTION
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
        r"\bself[- ]harm\b": "self_harm",
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
        r"\bpills?\b": "pills",
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
        r"\bself[- ]harm\b": "self_harm",
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
        r"^\s*help\s*$": "help_only_message",
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
        cleaned = normalize_whitespace(raw_input)
        ts = time.time()
        case_id = stable_case_id(cleaned, ts)
        created_at = utc_now_iso()
        metadata = dict(metadata or {})

        signal = CrisisSignal(
            case_id=case_id,
            timestamp=ts,
            created_at=created_at,
            message=cleaned,
            metadata=metadata,
        )

        lower = cleaned.lower()
        features = FeatureVector(
            word_count=len(cleaned.split()),
            char_count=len(cleaned),
            sentence_count=self._sentence_count(cleaned),
            uppercase_ratio=self._uppercase_ratio(cleaned),
            exclamation_count=cleaned.count("!"),
            question_count=cleaned.count("?"),
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
# SECTION 6 — RISK ENGINE
# =============================================================================

class RiskEngine:
    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    def score(self, signal: CrisisSignal, features: FeatureVector) -> RiskScore:
        contrib: Dict[str, float] = {}
        reasons: List[str] = []

        base = min(0.18, features.word_count / 300.0)
        contrib["base_text_density"] = round(base, 4)

        high_score = len(features.high_risk_hits) * self.policy.w_high_risk_keywords
        med_score = len(features.medium_risk_hits) * self.policy.w_medium_risk_keywords
        plan_score = len(features.plan_hits) * self.policy.w_plan_indicators
        means_score = len(features.means_hits) * self.policy.w_access_to_means
        time_score = len(features.time_immediacy_hits) * self.policy.w_time_immediacy
        self_harm_score = len(features.self_harm_hits) * self.policy.w_self_harm_intent
        harm_others_score = len(features.harm_to_others_hits) * self.policy.w_harm_to_others
        distress_score = len(features.distress_intensifier_hits) * self.policy.w_distress_intensifiers
        protective_score = len(features.protective_hits) * self.policy.w_protective_factors
        help_score = len(features.help_seeking_hits) * self.policy.w_help_seeking
        negation_score = len(features.negation_safety_hits) * self.policy.w_negation_safety

        if high_score:
            contrib["high_risk_keywords"] = round(high_score, 4)
            reasons.append(f"high-risk indicators: {', '.join(features.high_risk_hits)}")
        if med_score:
            contrib["medium_risk_keywords"] = round(med_score, 4)
            reasons.append(f"distress indicators: {', '.join(features.medium_risk_hits)}")
        if plan_score:
            contrib["plan_indicators"] = round(plan_score, 4)
            reasons.append(f"planning/immediacy language: {', '.join(features.plan_hits)}")
        if means_score:
            contrib["access_to_means"] = round(means_score, 4)
            reasons.append(f"means/access indicators: {', '.join(features.means_hits)}")
        if time_score:
            contrib["time_immediacy"] = round(time_score, 4)
            reasons.append(f"time immediacy indicators: {', '.join(features.time_immediacy_hits)}")
        if self_harm_score:
            contrib["self_harm_intent"] = round(self_harm_score, 4)
            reasons.append(f"self-harm indicators: {', '.join(features.self_harm_hits)}")
        if harm_others_score:
            contrib["harm_to_others"] = round(harm_others_score, 4)
            reasons.append(f"violence indicators: {', '.join(features.harm_to_others_hits)}")
        if distress_score:
            contrib["distress_intensifiers"] = round(distress_score, 4)
            reasons.append(f"distress intensifiers: {', '.join(features.distress_intensifier_hits)}")
        if protective_score:
            contrib["protective_factors"] = round(protective_score, 4)
            reasons.append(f"protective factors: {', '.join(features.protective_hits)}")
        if help_score:
            contrib["help_seeking"] = round(help_score, 4)
            reasons.append(f"help-seeking language: {', '.join(features.help_seeking_hits)}")
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

        if features.self_harm_hits and self.policy.never_auto_downgrade_self_harm:
            urgency_raw = max(urgency_raw, 0.72)
            contrib["self_harm_floor"] = 0.72

        if features.harm_to_others_hits and self.policy.never_auto_downgrade_violence:
            urgency_raw = max(urgency_raw, 0.72)
            contrib["violence_floor"] = 0.72

        urgency = clamp01(urgency_raw)

        feature_types_present = features.active_feature_groups()
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
            reasons.append("limited direct risk language; score driven mostly by general distress density")

        return RiskScore(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            severity_band=band,
            reasons=reasons,
            feature_contributions=contrib,
        )


# =============================================================================
# SECTION 7 — DECISION ENGINE
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
            explanation = (
                f"Urgency {risk.urgency:.2f} remains below medium threshold; "
                f"standard queue recommended."
            )

        if low_confidence and self.policy.route_low_confidence_to_human:
            route = self.policy.mandatory_review_route
            requires_human_review = True
            explanation += " Confidence is low, so the case is routed to mandatory human review."

        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = self.policy.urgent_review_route
            requires_human_review = True
            explanation += " High-risk/low-confidence combination triggers urgent human review."

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
# SECTION 8 — PERSISTENCE
# =============================================================================

class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).expanduser())
        ensure_parent_dir(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
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
                recorded_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES triage_records(case_id)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_records_timestamp ON triage_records(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_records_priority_json ON triage_records(created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_case_id ON outcomes(case_id)")
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
                json_dumps(record.signal.metadata),
                json_dumps(asdict(record.features)),
                json_dumps(asdict(record.risk)),
                json_dumps(asdict(record.decision)),
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

        if updated:
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
            (max(1, int(limit)),),
        )
        rows = cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    def count_records(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM triage_records")
        row = cur.fetchone()
        return int(row["c"]) if row else 0

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
# SECTION 9 — AUDIT LOGGING
# =============================================================================

class AuditLogger:
    def __init__(self, jsonl_path: str, verbose: bool = True):
        self.jsonl_path = str(Path(jsonl_path).expanduser())
        self.verbose = verbose
        self._in_memory_log: List[Dict[str, Any]] = []
        ensure_parent_dir(self.jsonl_path)

    def log(self, record: TriageRecord) -> None:
        entry = record.to_public_dict()
        self._in_memory_log.append(entry)

        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json_dumps(entry) + "\n")

        if self.verbose:
            self._print_card(record)

    @staticmethod
    def _short_message(message: str, width: int = 88) -> str:
        clean = normalize_whitespace(message)
        return clean if len(clean) <= width else clean[: width - 1] + "…"

    def _print_card(self, record: TriageRecord) -> None:
        msg = self._short_message(record.signal.message)
        reasons = "; ".join(record.risk.reasons[:3]) or "n/a"
        flags = ", ".join(record.decision.safety_flags) if record.decision.safety_flags else "None"

        print("┌" + "─" * 92)
        print(f"│ CASE ID      : {record.case_id}")
        print(f"│ INPUT        : {msg}")
        print(f"│ URGENCY      : {record.risk.urgency:.4f}    CONFIDENCE: {record.risk.confidence:.4f}")
        print(f"│ BAND         : {record.risk.severity_band}")
        print(f"│ PRIORITY     : {record.decision.priority:<12} ROUTE: {record.decision.route_to}")
        print(f"│ HUMAN REVIEW : {record.decision.requires_human_review}")
        print(f"│ FLAGS        : {flags}")
        print(f"│ REASONS      : {self._short_message(reasons, 80)}")
        print(f"│ LATENCY      : {record.processing_ms:.2f} ms")
        print("└" + "─" * 92)

    def export_json(self) -> str:
        return json.dumps(self._in_memory_log, indent=2, ensure_ascii=False)


# =============================================================================
# SECTION 10 — FEEDBACK / EVALUATION
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

        processing_ms = [r.processing_ms for r in records]

        return {
            "records": len(records),
            "avg_urgency": round(statistics.mean(urgencies), 4),
            "max_urgency": round(max(urgencies), 4),
            "avg_confidence": round(statistics.mean(confidences), 4),
            "avg_processing_ms": round(statistics.mean(processing_ms), 3),
            "max_processing_ms": round(max(processing_ms), 3),
            "human_review_rate": round(human_review_count / len(records), 4),
            "severity_distribution": dict(severity_dist),
            "priority_distribution": dict(priority_dist),
            "route_distribution": dict(route_dist),
            "outcomes_logged": len(outcomes),
            "outcome_distribution": dict(outcome_dist),
        }

    def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
        records = [r for r in self.store.list_records(limit=limit) if r.outcome]
        if not records:
            return {"records_with_outcomes": 0, "buckets": {}}

        buckets: Dict[str, List[str]] = {
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

    def export_summary_csv(self, path: str, limit: int = 5000) -> None:
        ensure_parent_dir(path)
        records = self.store.list_records(limit=limit)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "case_id",
                    "created_at",
                    "message",
                    "urgency",
                    "confidence",
                    "severity_band",
                    "priority",
                    "route_to",
                    "requires_human_review",
                    "processing_ms",
                    "outcome",
                ],
            )
            writer.writeheader()
            for r in records:
                writer.writerow(
                    {
                        "case_id": r.case_id,
                        "created_at": r.signal.created_at,
                        "message": r.signal.message,
                        "urgency": r.risk.urgency,
                        "confidence": r.risk.confidence,
                        "severity_band": r.risk.severity_band,
                        "priority": r.decision.priority,
                        "route_to": r.decision.route_to,
                        "requires_human_review": r.decision.requires_human_review,
                        "processing_ms": r.processing_ms,
                        "outcome": r.outcome or "",
                    }
                )


# =============================================================================
# SECTION 11 — MAIN ENGINE
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
        ensure_parent_dir(path)
        payload = [r.to_public_dict() for r in self.store.list_records(limit=limit)]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def export_summary_csv(self, path: str, limit: int = 5000) -> None:
        self.feedback.export_summary_csv(path, limit=limit)

    def close(self) -> None:
        self.store.close()


# =============================================================================
# SECTION 12 — DEMO DATA
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
# SECTION 13 — OUTPUT HELPERS
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
        print(name)
        print("-" * len(name))
        if isinstance(value, str):
            print(textwrap.fill(value, width=88))
        elif isinstance(value, dict):
            total = 0
            for k, v in value.items():
                total += int(v)
                print(f"  - {k}: ${v:,.0f}")
            print(f"  - total: ${total:,.0f}")
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


def print_readiness_banner(db_path: str, audit_jsonl_path: str, policy_name: str) -> None:
    print_header("AI CRISIS TRIAGE SYSTEM — READY")
    print(f"Database        : {db_path}")
    print(f"Audit JSONL     : {audit_jsonl_path}")
    print(f"Policy          : {policy_name}")
    print()
    print("Try one of:")
    print("  --demo")
    print("  --interactive")
    print("  --batch cases.jsonl")
    print("  --summary")
    print("  --print-concept")
    print("  --export-records records.json")
    print("  --export-summary summary.csv")
    print()


# =============================================================================
# SECTION 14 — CLI
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
    parser.add_argument("--export-summary", type=str, help="Export summary rows to CSV file")
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
# SECTION 15 — RUN MODES
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
            print_summary(engine.report(), calibration=engine.calibration_report())
            continue

        if raw.startswith("/show "):
            _, _, case_id = raw.partition(" ")
            rec = engine.store.get_record(case_id.strip())
            print("No such case." if rec is None else "")
            if rec is not None:
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

        engine.process(raw, metadata={"channel": "interactive_console"})


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
# SECTION 16 — MAIN
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    verbose = False if args.quiet else bool_from_env("CRISIS_TRIAGE_VERBOSE", True)

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

        if args.export_summary:
            engine.export_summary_csv(args.export_summary)
            print(f"Exported summary CSV to {args.export_summary}")
            action_taken = True

        if not action_taken:
            print_readiness_banner(args.db, args.audit_jsonl, args.policy)

    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

What’s better in this version:

- tighter structure and cleaner imports
- safer path handling and parent-dir creation
- SQLite WAL mode enabled
- cleaner normalization and utility layer
- CSV summary export added
- slightly stronger regex handling like `self[- ]harm` and `pills?`
- improved reporting and readiness banner
- fewer loose edges in outcome persistence
- cleaner prototype framing for research use

What still is not enough for real-world deployment:

- no authenticated users, roles, or access control
- no encryption, secrets handling, or PHI-safe architecture
- no actual hotline integration or queue transport
- no expert validation or clinical governance
- no calibration against real labeled datasets
- no formal false-negative / false-positive evaluation
- no secure web API, observability stack, or deployment profile

The strongest next step would be turning this into a still-single-file but much more serious research service with:

- FastAPI endpoints
- SQLite plus migration-ready schema
- policy profiles
- reviewer actions
- queue simulation
- benchmark suite
- richer export package for NIH-style appendix material


#### You:
Make a longer stronger polished ready for submition #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
════════════════════════════════════════════════════════════════════════════════
AI CRISIS TRIAGE SYSTEM — NIH SBIR RESEARCH SINGLE-FILE PACKAGE
════════════════════════════════════════════════════════════════════════════════

PURPOSE
-------
This file combines:
1) A grant-style NIH SBIR concept package
2) A functional research prototype for AI-assisted crisis triage

INTENDED USE
------------
This prototype is designed for research, simulation, workflow testing, and
human-in-the-loop decision support. It is NOT intended to be the sole basis
for clinical, hotline, dispatch, or emergency decision-making. Final decisions
must remain with qualified human professionals operating under approved policy,
governance, training, supervision, and legal/compliance review.

DESIGN GOALS
------------
- Deterministic, explainable scoring
- Human-in-the-loop routing recommendations
- Auditability and reproducibility
- SQLite-backed persistence
- Research-ready extensibility
- Single-file deployment simplicity
- Clean CLI for demo, interactive, and batch workflows

SUPPORTED MODES
---------------
- Demo mode with built-in scenarios
- Interactive console mode
- Batch JSONL input mode
- Summary/report export
- SQLite-backed persistence
- JSON export and CSV summary export

EXAMPLE USAGE
-------------
python crisis_triage_sbir.py --demo
python crisis_triage_sbir.py --interactive
python crisis_triage_sbir.py --batch cases.jsonl
python crisis_triage_sbir.py --summary
python crisis_triage_sbir.py --export-records records.json
python crisis_triage_sbir.py --export-summary summary.csv
python crisis_triage_sbir.py --print-concept

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
- Calibration statistics
- CLI and persistence infrastructure

IMPORTANT SAFETY NOTE
---------------------
This is a prototype research tool. Real deployment in crisis environments would
require domain expert validation, secure architecture, rigorous evaluation,
formal human oversight, privacy review, compliance controls, and approved
operational protocols.
════════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import statistics
import sys
import textwrap
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# SECTION 1 — NIH SBIR CONCEPT
# =============================================================================

PROJECT_TITLE = "AI-Driven Real-Time Crisis Triage and Decision Support System"

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
    "False positives from metaphorical, quoted, or indirect language.",
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

@dataclass(frozen=True)
class PolicyConfig:
    name: str = "default"

    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    low_confidence_floor: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    emergency_route: str = "EMERGENCY_DISPATCH"
    immediate_route: str = "IMMEDIATE_CLINICIAN"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "QUEUE_PRIORITY"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

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

    confidence_base: float = 0.50
    confidence_per_feature_type: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_structured_metadata: float = 0.05

    require_human_review_for_all_high: bool = True
    route_low_confidence_to_human: bool = True
    never_auto_downgrade_self_harm: bool = True
    never_auto_downgrade_violence: bool = True


def load_policy(policy_name: str = "default") -> PolicyConfig:
    # Placeholder for future multi-policy loading from JSON or DB.
    # Kept deterministic and local for prototype reliability.
    return PolicyConfig(name=policy_name)


# =============================================================================
# SECTION 3 — UTILITIES
# =============================================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def normalize_whitespace(text: str) -> str:
    return " ".join((text or "").split())


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def stable_case_id(message: str, ts: float) -> str:
    digest = hashlib.sha256(f"{ts}:{message}".encode("utf-8")).hexdigest()[:16]
    return f"case_{digest}"


def ensure_parent_dir(path: str) -> None:
    parent = Path(path).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


def bool_from_env(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=False)


# =============================================================================
# SECTION 4 — DATA MODELS
# =============================================================================

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
        groups = (
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
        )
        return sum(len(g) for g in groups)

    def active_feature_groups(self) -> int:
        groups = (
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
        )
        return sum(1 for g in groups if g)


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
# SECTION 5 — FEATURE EXTRACTION
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
        r"\bself[- ]harm\b": "self_harm",
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
        r"\bpills?\b": "pills",
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
        r"\bself[- ]harm\b": "self_harm",
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
        r"^\s*help\s*$": "help_only_message",
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
        cleaned = normalize_whitespace(raw_input)
        ts = time.time()
        case_id = stable_case_id(cleaned, ts)
        created_at = utc_now_iso()
        metadata = dict(metadata or {})

        signal = CrisisSignal(
            case_id=case_id,
            timestamp=ts,
            created_at=created_at,
            message=cleaned,
            metadata=metadata,
        )

        lower = cleaned.lower()
        features = FeatureVector(
            word_count=len(cleaned.split()),
            char_count=len(cleaned),
            sentence_count=self._sentence_count(cleaned),
            uppercase_ratio=self._uppercase_ratio(cleaned),
            exclamation_count=cleaned.count("!"),
            question_count=cleaned.count("?"),
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
# SECTION 6 — RISK ENGINE
# =============================================================================

class RiskEngine:
    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    def score(self, signal: CrisisSignal, features: FeatureVector) -> RiskScore:
        contrib: Dict[str, float] = {}
        reasons: List[str] = []

        base = min(0.18, features.word_count / 300.0)
        contrib["base_text_density"] = round(base, 4)

        high_score = len(features.high_risk_hits) * self.policy.w_high_risk_keywords
        med_score = len(features.medium_risk_hits) * self.policy.w_medium_risk_keywords
        plan_score = len(features.plan_hits) * self.policy.w_plan_indicators
        means_score = len(features.means_hits) * self.policy.w_access_to_means
        time_score = len(features.time_immediacy_hits) * self.policy.w_time_immediacy
        self_harm_score = len(features.self_harm_hits) * self.policy.w_self_harm_intent
        harm_others_score = len(features.harm_to_others_hits) * self.policy.w_harm_to_others
        distress_score = len(features.distress_intensifier_hits) * self.policy.w_distress_intensifiers
        protective_score = len(features.protective_hits) * self.policy.w_protective_factors
        help_score = len(features.help_seeking_hits) * self.policy.w_help_seeking
        negation_score = len(features.negation_safety_hits) * self.policy.w_negation_safety

        if high_score:
            contrib["high_risk_keywords"] = round(high_score, 4)
            reasons.append(f"high-risk indicators: {', '.join(features.high_risk_hits)}")
        if med_score:
            contrib["medium_risk_keywords"] = round(med_score, 4)
            reasons.append(f"distress indicators: {', '.join(features.medium_risk_hits)}")
        if plan_score:
            contrib["plan_indicators"] = round(plan_score, 4)
            reasons.append(f"planning/immediacy language: {', '.join(features.plan_hits)}")
        if means_score:
            contrib["access_to_means"] = round(means_score, 4)
            reasons.append(f"means/access indicators: {', '.join(features.means_hits)}")
        if time_score:
            contrib["time_immediacy"] = round(time_score, 4)
            reasons.append(f"time immediacy indicators: {', '.join(features.time_immediacy_hits)}")
        if self_harm_score:
            contrib["self_harm_intent"] = round(self_harm_score, 4)
            reasons.append(f"self-harm indicators: {', '.join(features.self_harm_hits)}")
        if harm_others_score:
            contrib["harm_to_others"] = round(harm_others_score, 4)
            reasons.append(f"violence indicators: {', '.join(features.harm_to_others_hits)}")
        if distress_score:
            contrib["distress_intensifiers"] = round(distress_score, 4)
            reasons.append(f"distress intensifiers: {', '.join(features.distress_intensifier_hits)}")
        if protective_score:
            contrib["protective_factors"] = round(protective_score, 4)
            reasons.append(f"protective factors: {', '.join(features.protective_hits)}")
        if help_score:
            contrib["help_seeking"] = round(help_score, 4)
            reasons.append(f"help-seeking language: {', '.join(features.help_seeking_hits)}")
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

        if features.self_harm_hits and self.policy.never_auto_downgrade_self_harm:
            urgency_raw = max(urgency_raw, 0.72)
            contrib["self_harm_floor"] = 0.72

        if features.harm_to_others_hits and self.policy.never_auto_downgrade_violence:
            urgency_raw = max(urgency_raw, 0.72)
            contrib["violence_floor"] = 0.72

        urgency = clamp01(urgency_raw)

        feature_types_present = features.active_feature_groups()
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
            reasons.append("limited direct risk language; score driven mostly by general distress density")

        return RiskScore(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            severity_band=band,
            reasons=reasons,
            feature_contributions=contrib,
        )


# =============================================================================
# SECTION 7 — DECISION ENGINE
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
            explanation = (
                f"Urgency {risk.urgency:.2f} remains below medium threshold; "
                f"standard queue recommended."
            )

        if low_confidence and self.policy.route_low_confidence_to_human:
            route = self.policy.mandatory_review_route
            requires_human_review = True
            explanation += " Confidence is low, so the case is routed to mandatory human review."

        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = self.policy.urgent_review_route
            requires_human_review = True
            explanation += " High-risk/low-confidence combination triggers urgent human review."

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
# SECTION 8 — PERSISTENCE
# =============================================================================

class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).expanduser())
        ensure_parent_dir(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
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
                recorded_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES triage_records(case_id)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_records_timestamp ON triage_records(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_records_priority_json ON triage_records(created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_case_id ON outcomes(case_id)")
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
                json_dumps(record.signal.metadata),
                json_dumps(asdict(record.features)),
                json_dumps(asdict(record.risk)),
                json_dumps(asdict(record.decision)),
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

        if updated:
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
            (max(1, int(limit)),),
        )
        rows = cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    def count_records(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM triage_records")
        row = cur.fetchone()
        return int(row["c"]) if row else 0

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
# SECTION 9 — AUDIT LOGGING
# =============================================================================

class AuditLogger:
    def __init__(self, jsonl_path: str, verbose: bool = True):
        self.jsonl_path = str(Path(jsonl_path).expanduser())
        self.verbose = verbose
        self._in_memory_log: List[Dict[str, Any]] = []
        ensure_parent_dir(self.jsonl_path)

    def log(self, record: TriageRecord) -> None:
        entry = record.to_public_dict()
        self._in_memory_log.append(entry)

        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json_dumps(entry) + "\n")

        if self.verbose:
            self._print_card(record)

    @staticmethod
    def _short_message(message: str, width: int = 88) -> str:
        clean = normalize_whitespace(message)
        return clean if len(clean) <= width else clean[: width - 1] + "…"

    def _print_card(self, record: TriageRecord) -> None:
        msg = self._short_message(record.signal.message)
        reasons = "; ".join(record.risk.reasons[:3]) or "n/a"
        flags = ", ".join(record.decision.safety_flags) if record.decision.safety_flags else "None"

        print("┌" + "─" * 92)
        print(f"│ CASE ID      : {record.case_id}")
        print(f"│ INPUT        : {msg}")
        print(f"│ URGENCY      : {record.risk.urgency:.4f}    CONFIDENCE: {record.risk.confidence:.4f}")
        print(f"│ BAND         : {record.risk.severity_band}")
        print(f"│ PRIORITY     : {record.decision.priority:<12} ROUTE: {record.decision.route_to}")
        print(f"│ HUMAN REVIEW : {record.decision.requires_human_review}")
        print(f"│ FLAGS        : {flags}")
        print(f"│ REASONS      : {self._short_message(reasons, 80)}")
        print(f"│ LATENCY      : {record.processing_ms:.2f} ms")
        print("└" + "─" * 92)

    def export_json(self) -> str:
        return json.dumps(self._in_memory_log, indent=2, ensure_ascii=False)


# =============================================================================
# SECTION 10 — FEEDBACK / EVALUATION
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

        processing_ms = [r.processing_ms for r in records]

        return {
            "records": len(records),
            "avg_urgency": round(statistics.mean(urgencies), 4),
            "max_urgency": round(max(urgencies), 4),
            "avg_confidence": round(statistics.mean(confidences), 4),
            "avg_processing_ms": round(statistics.mean(processing_ms), 3),
            "max_processing_ms": round(max(processing_ms), 3),
            "human_review_rate": round(human_review_count / len(records), 4),
            "severity_distribution": dict(severity_dist),
            "priority_distribution": dict(priority_dist),
            "route_distribution": dict(route_dist),
            "outcomes_logged": len(outcomes),
            "outcome_distribution": dict(outcome_dist),
        }

    def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
        records = [r for r in self.store.list_records(limit=limit) if r.outcome]
        if not records:
            return {"records_with_outcomes": 0, "buckets": {}}

        buckets: Dict[str, List[str]] = {
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

    def export_summary_csv(self, path: str, limit: int = 5000) -> None:
        ensure_parent_dir(path)
        records = self.store.list_records(limit=limit)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "case_id",
                    "created_at",
                    "message",
                    "urgency",
                    "confidence",
                    "severity_band",
                    "priority",
                    "route_to",
                    "requires_human_review",
                    "processing_ms",
                    "outcome",
                ],
            )
            writer.writeheader()
            for r in records:
                writer.writerow(
                    {
                        "case_id": r.case_id,
                        "created_at": r.signal.created_at,
                        "message": r.signal.message,
                        "urgency": r.risk.urgency,
                        "confidence": r.risk.confidence,
                        "severity_band": r.risk.severity_band,
                        "priority": r.decision.priority,
                        "route_to": r.decision.route_to,
                        "requires_human_review": r.decision.requires_human_review,
                        "processing_ms": r.processing_ms,
                        "outcome": r.outcome or "",
                    }
                )


# =============================================================================
# SECTION 11 — MAIN ENGINE
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
        ensure_parent_dir(path)
        payload = [r.to_public_dict() for r in self.store.list_records(limit=limit)]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def export_summary_csv(self, path: str, limit: int = 5000) -> None:
        self.feedback.export_summary_csv(path, limit=limit)

    def close(self) -> None:
        self.store.close()


# =============================================================================
# SECTION 12 — DEMO DATA
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
# SECTION 13 — OUTPUT HELPERS
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
        print(name)
        print("-" * len(name))
        if isinstance(value, str):
            print(textwrap.fill(value, width=88))
        elif isinstance(value, dict):
            total = 0
            for k, v in value.items():
                total += int(v)
                print(f"  - {k}: ${v:,.0f}")
            print(f"  - total: ${total:,.0f}")
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


def print_readiness_banner(db_path: str, audit_jsonl_path: str, policy_name: str) -> None:
    print_header("AI CRISIS TRIAGE SYSTEM — READY")
    print(f"Database        : {db_path}")
    print(f"Audit JSONL     : {audit_jsonl_path}")
    print(f"Policy          : {policy_name}")
    print()
    print("Try one of:")
    print("  --demo")
    print("  --interactive")
    print("  --batch cases.jsonl")
    print("  --summary")
    print("  --print-concept")
    print("  --export-records records.json")
    print("  --export-summary summary.csv")
    print()


# =============================================================================
# SECTION 14 — CLI
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
    parser.add_argument("--export-summary", type=str, help="Export summary rows to CSV file")
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
# SECTION 15 — RUN MODES
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
            print_summary(engine.report(), calibration=engine.calibration_report())
            continue

        if raw.startswith("/show "):
            _, _, case_id = raw.partition(" ")
            rec = engine.store.get_record(case_id.strip())
            print("No such case." if rec is None else "")
            if rec is not None:
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

        engine.process(raw, metadata={"channel": "interactive_console"})


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
# SECTION 16 — MAIN
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    verbose = False if args.quiet else bool_from_env("CRISIS_TRIAGE_VERBOSE", True)

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

        if args.export_summary:
            engine.export_summary_csv(args.export_summary)
            print(f"Exported summary CSV to {args.export_summary}")
            action_taken = True

        if not action_taken:
            print_readiness_banner(args.db, args.audit_jsonl, args.policy)

    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#### ChatGPT:
I’m turning this into a more submission-grade package rather than just a code cleanup: stronger SBIR sections, sharper policy/governance framing, richer evaluation/reporting, and a more complete research prototype in one file.


#### ChatGPT:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
════════════════════════════════════════════════════════════════════════════════
AI CRISIS TRIAGE SYSTEM — NIH SBIR RESEARCH / SUBMISSION-READY SINGLE-FILE KIT
════════════════════════════════════════════════════════════════════════════════

PURPOSE
-------
This file combines:
1) A grant-style NIH SBIR concept and submission support package
2) A functional research prototype for deterministic, auditable,
   human-in-the-loop AI-assisted crisis triage

INTENDED USE
------------
This package is designed for:
- research
- simulation
- workflow testing
- pilot planning
- retrospective quality review
- human-in-the-loop decision support

This system is NOT intended to be the sole basis for clinical, hotline,
dispatch, or emergency action. Final operational decisions must remain with
qualified human professionals operating under approved policies, training,
oversight, governance, legal/compliance review, and domain-specific protocols.

DESIGN GOALS
------------
- Deterministic, explainable scoring
- Human-in-the-loop routing recommendations
- Conservative safety escalation
- Auditability and reproducibility
- SQLite-backed persistence
- Submission-grade project narrative support
- Research-ready extensibility
- Single-file deployment simplicity
- Clean CLI for demo, interactive, and batch workflows
- Evidence-friendly exports for pilot review

SUPPORTED MODES
---------------
- Demo mode with built-in scenarios
- Interactive console mode
- Batch JSONL input mode
- Summary / calibration reporting
- JSON export and CSV summary export
- Markdown appendix export
- Readiness / governance narrative printouts
- SQLite-backed persistence

EXAMPLE USAGE
-------------
python crisis_triage_sbir.py --demo
python crisis_triage_sbir.py --interactive
python crisis_triage_sbir.py --batch cases.jsonl
python crisis_triage_sbir.py --summary
python crisis_triage_sbir.py --export-records records.json
python crisis_triage_sbir.py --export-summary summary.csv
python crisis_triage_sbir.py --export-appendix appendix.md
python crisis_triage_sbir.py --print-concept
python crisis_triage_sbir.py --print-submission-brief

OPTIONAL ENV VARS
-----------------
CRISIS_TRIAGE_DB=crisis_triage.db
CRISIS_TRIAGE_AUDIT_JSONL=audit_log.jsonl
CRISIS_TRIAGE_VERBOSE=true
CRISIS_TRIAGE_POLICY=default
CRISIS_TRIAGE_APPENDIX=appendix.md

INPUT FORMAT FOR --batch
------------------------
One JSON object per line, for example:
{"message": "I want to end my life tonight. I have pills.", "metadata": {"channel": "chat"}}
{"message": "I feel overwhelmed and need help.", "metadata": {"channel": "voice"}}

AUTHORING NOTE
--------------
This package is intentionally research-oriented and includes:
- SBIR-style concept text
- policy configuration
- deterministic feature extraction
- explainable risk engine
- human review / escalation logic
- outcome tracking
- audit export
- calibration statistics
- summary reporting
- readiness and appendix helpers
- CLI and persistence infrastructure

IMPORTANT SAFETY NOTE
---------------------
This is a prototype research tool. Real deployment in crisis environments would
require domain expert validation, secure architecture, privacy controls,
rigorous evaluation, formal human oversight, compliance review, approved
protocols, and operational governance with continuous monitoring.
════════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import statistics
import textwrap
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# SECTION 1 — NIH SBIR CONCEPT / SUBMISSION NARRATIVE
# =============================================================================

PROJECT_TITLE = "AI-Driven Real-Time Crisis Triage and Decision Support System"

PROJECT_TAGLINE = (
    "A deterministic, auditable, human-in-the-loop crisis triage research "
    "platform for 988-aligned and related behavioral health workflows."
)

PROJECT_SUMMARY = """
Crisis response systems such as 988-aligned hotlines, behavioral health triage
centers, digital crisis intake channels, and emergency communication
environments face rising demand, workforce constraints, inconsistent
prioritization, limited real-time decision support, and growing requirements
for auditability and quality oversight.

This project proposes a deterministic, auditable, policy-aware, human-in-the-
loop AI decision support engine that:
- ingests free-text and structured crisis signals in real time,
- extracts interpretable risk indicators,
- estimates urgency and confidence under uncertainty,
- recommends routing and queue prioritization,
- logs all inputs, features, and recommendations for review,
- supports retrospective calibration and workflow improvement.

The core objective is to improve timeliness, consistency, safety oversight, and
research visibility into triage workflows while explicitly preserving human
authority over operational decisions.
""".strip()

PUBLIC_HEALTH_NEED = """
Behavioral health crisis systems continue to encounter increasing operational
pressure, including staffing shortages, uneven queue prioritization, and
variation in triage decisions across channels and shifts. Many organizations
lack structured tooling that can support early risk flagging while also
documenting why a recommendation was made. This creates operational friction in
both frontline response and later quality review. A system that offers
explainable, policy-aware, human-supervised triage support could strengthen
timeliness, consistency, accountability, and pilot readiness for future
evaluation efforts.
""".strip()

OVERALL_OBJECTIVE = """
Develop and validate a deterministic, explainable, research-grade crisis triage
decision support system that can assist qualified human operators by producing
auditable urgency estimates, routing recommendations, and retrospective review
artifacts suitable for pilot planning and operational evaluation.
""".strip()

CENTRAL_HYPOTHESIS = """
A conservative, deterministic, policy-aware triage support system with explicit
human-review gates and full audit logging can improve consistency and evidence
capture in crisis workflow simulations without removing human oversight.
""".strip()

SPECIFIC_AIMS = [
    "Build a real-time, policy-aware signal ingestion and feature extraction pipeline.",
    "Develop a deterministic, explainable risk scoring model for crisis urgency estimation.",
    "Implement a human-in-the-loop routing engine with auditable justifications and safety floors.",
    "Create an outcome feedback and retrospective evaluation layer for calibration, reporting, and pilot readiness.",
]

SIGNIFICANCE = [
    "Addresses growing crisis volume and workforce strain in behavioral health systems.",
    "Supports standardization without displacing trained human judgment.",
    "Improves auditability for quality assurance, incident review, and supervisory workflows.",
    "Creates a research asset for pilot studies, procurement preparation, and workflow modernization.",
]

INNOVATION = [
    "Explainable crisis triage under uncertainty rather than opaque end-to-end scoring.",
    "Policy-aware routing with explicit safety floors and uncertainty escalation.",
    "Structured auditability for each triage recommendation and its supporting features.",
    "Single-file research deployment model that supports rapid simulation, demonstration, and pilot preparation.",
]

APPROACH_OVERVIEW = [
    "Use deterministic lexicon and signal-pattern extraction as an interpretable baseline.",
    "Apply policy-configurable weighted scoring to derive urgency and confidence estimates.",
    "Use conservative routing logic with mandatory human review under specified conditions.",
    "Persist records, outcomes, and calibration snapshots for retrospective analysis.",
    "Generate submission-friendly summaries, appendices, and evidence exports.",
]

TECHNICAL_RISKS = [
    "False negatives in short or ambiguous messages.",
    "False positives from metaphorical, quoted, joking, or indirect language.",
    "Data drift across channels, geographies, organizations, and user populations.",
    "Operational latency and workflow integration complexity in real-world environments.",
    "Human factors risk if operators over-trust automation or misread model explanations.",
]

RISK_MITIGATIONS = [
    "Use human-in-the-loop policy gates for all high-severity recommendations.",
    "Escalate low-confidence cases to human review rather than auto-downgrading them.",
    "Keep model logic deterministic and auditable during the pilot-oriented baseline phase.",
    "Maintain conservative routing floors for self-harm and violence indicators.",
    "Persist all features, recommendations, and outcomes for calibration and retrospective review.",
]

EXPECTED_OUTCOMES = [
    "Reduced time-to-priority assignment in simulated or supervised workflows.",
    "Improved consistency of routing recommendations across repeated scenarios.",
    "Higher auditability for quality assurance and incident review.",
    "A clearer pilot-to-procurement evidence package for public-sector and provider settings.",
]

COMMERCIALIZATION = [
    "988-aligned crisis operations and behavioral health call centers.",
    "Emergency communications and public-sector triage modernization efforts.",
    "Healthcare providers and telehealth intake systems.",
    "Government-funded pilots focused on AI-assisted operations infrastructure.",
]

PHASE_I_WORKPLAN = [
    "Complete deterministic baseline engine and submission-grade research package.",
    "Define pilot evaluation scenarios and safety review pathways.",
    "Generate benchmark cases with outcome capture for supervised review.",
    "Produce policy, reporting, and appendix materials for evaluator inspection.",
]

PHASE_II_DIRECTION = [
    "Integrate secure service APIs and role-based reviewer interfaces.",
    "Expand evaluation design with expert review and organization-specific policy profiles.",
    "Add comparative calibration analysis across channels and scenario classes.",
    "Prepare secure pilot deployment architecture and formal validation studies.",
]

SUCCESS_METRICS = [
    "Coverage of predefined high-risk benchmark scenarios.",
    "Routing consistency across repeated evaluation runs.",
    "Reviewability of all recommendations and their feature-level explanations.",
    "Completeness of audit logs and retrospective exports.",
    "Operational feasibility for pilot demonstration and oversight workflows.",
]

EVALUATION_PLAN = [
    "Scenario-based benchmark review using labeled simulated cases.",
    "Retrospective comparison of urgency buckets against recorded outcomes.",
    "Review of human-review trigger rates and high-risk floor behavior.",
    "Latency measurement and persistence integrity checks.",
]

ETHICS_AND_GOVERNANCE = [
    "Human authority retained for all operational decisions.",
    "No autonomous dispatch or treatment decisions by the prototype.",
    "Explicit logging of model reasons, safety flags, and review triggers.",
    "Conservative handling of uncertainty and high-risk indicators.",
    "Clear boundary between research support and operational deployment.",
]

MILESTONES = [
    "Prototype ingestion pipeline and feature extraction.",
    "Deterministic risk model baseline validation.",
    "Decision routing simulation with policy guardrails.",
    "Human feedback and retrospective outcome capture.",
    "Benchmarking, calibration analysis, and pilot-readiness package.",
    "Submission appendix and reporting export generation.",
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

@dataclass(frozen=True)
class PolicyConfig:
    name: str = "default"

    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    low_confidence_floor: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    emergency_route: str = "EMERGENCY_DISPATCH"
    immediate_route: str = "IMMEDIATE_CLINICIAN"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "QUEUE_PRIORITY"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

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

    confidence_base: float = 0.50
    confidence_per_feature_type: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_structured_metadata: float = 0.05

    require_human_review_for_all_high: bool = True
    route_low_confidence_to_human: bool = True
    never_auto_downgrade_self_harm: bool = True
    never_auto_downgrade_violence: bool = True

    description: str = (
        "Default deterministic research policy with conservative escalation "
        "floors and mandatory human review for uncertainty-sensitive cases."
    )


def load_policy(policy_name: str = "default") -> PolicyConfig:
    policy_name = (policy_name or "default").strip().lower()

    if policy_name == "conservative":
        return PolicyConfig(
            name="conservative",
            critical_threshold=0.82,
            high_threshold=0.60,
            medium_threshold=0.35,
            low_confidence_floor=0.50,
            uncertain_high_risk_floor=0.55,
            description="Lower thresholds, stronger escalation bias, suitable for conservative pilot review.",
        )

    if policy_name == "balanced":
        return PolicyConfig(
            name="balanced",
            critical_threshold=0.86,
            high_threshold=0.66,
            medium_threshold=0.42,
            low_confidence_floor=0.44,
            uncertain_high_risk_floor=0.60,
            description="Balanced baseline policy for simulated workflow comparisons.",
        )

    return PolicyConfig(name="default")


# =============================================================================
# SECTION 3 — UTILITIES
# =============================================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def normalize_whitespace(text: str) -> str:
    return " ".join((text or "").split())


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def stable_case_id(message: str, ts: float) -> str:
    digest = hashlib.sha256(f"{ts}:{message}".encode("utf-8")).hexdigest()[:16]
    return f"case_{digest}"


def ensure_parent_dir(path: str) -> None:
    parent = Path(path).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


def bool_from_env(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=False)


def fmt_usd(amount: int) -> str:
    return f"${amount:,.0f}"


def wrapped(text: str, width: int = 92) -> str:
    return textwrap.fill(text, width=width)


def total_budget(budget: Dict[str, int]) -> int:
    return int(sum(int(v) for v in budget.values()))


# =============================================================================
# SECTION 4 — DATA MODELS
# =============================================================================

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
        groups = (
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
        )
        return sum(len(g) for g in groups)

    def active_feature_groups(self) -> int:
        groups = (
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
        )
        return sum(1 for g in groups if g)

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "word_count": self.word_count,
            "char_count": self.char_count,
            "sentence_count": self.sentence_count,
            "uppercase_ratio": self.uppercase_ratio,
            "exclamation_count": self.exclamation_count,
            "question_count": self.question_count,
            "total_signal_hits": self.total_signal_hits(),
            "active_feature_groups": self.active_feature_groups(),
        }


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


@dataclass
class BenchmarkCase:
    name: str
    message: str
    metadata: Dict[str, Any]
    expected_min_priority_rank: int
    expected_flags: List[str] = field(default_factory=list)


# =============================================================================
# SECTION 5 — FEATURE EXTRACTION
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
        r"\bself[- ]harm\b": "self_harm",
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
        r"\bpills?\b": "pills",
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
        r"\bself[- ]harm\b": "self_harm",
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
        r"^\s*help\s*$": "help_only_message",
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
        cleaned = normalize_whitespace(raw_input)
        ts = time.time()
        case_id = stable_case_id(cleaned, ts)
        created_at = utc_now_iso()
        metadata = dict(metadata or {})

        signal = CrisisSignal(
            case_id=case_id,
            timestamp=ts,
            created_at=created_at,
            message=cleaned,
            metadata=metadata,
        )

        lower = cleaned.lower()
        features = FeatureVector(
            word_count=len(cleaned.split()),
            char_count=len(cleaned),
            sentence_count=self._sentence_count(cleaned),
            uppercase_ratio=self._uppercase_ratio(cleaned),
            exclamation_count=cleaned.count("!"),
            question_count=cleaned.count("?"),
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
# SECTION 6 — RISK ENGINE
# =============================================================================

class RiskEngine:
    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    def score(self, signal: CrisisSignal, features: FeatureVector) -> RiskScore:
        contrib: Dict[str, float] = {}
        reasons: List[str] = []

        base = min(0.18, features.word_count / 300.0)
        contrib["base_text_density"] = round(base, 4)

        high_score = len(features.high_risk_hits) * self.policy.w_high_risk_keywords
        med_score = len(features.medium_risk_hits) * self.policy.w_medium_risk_keywords
        plan_score = len(features.plan_hits) * self.policy.w_plan_indicators
        means_score = len(features.means_hits) * self.policy.w_access_to_means
        time_score = len(features.time_immediacy_hits) * self.policy.w_time_immediacy
        self_harm_score = len(features.self_harm_hits) * self.policy.w_self_harm_intent
        harm_others_score = len(features.harm_to_others_hits) * self.policy.w_harm_to_others
        distress_score = len(features.distress_intensifier_hits) * self.policy.w_distress_intensifiers
        protective_score = len(features.protective_hits) * self.policy.w_protective_factors
        help_score = len(features.help_seeking_hits) * self.policy.w_help_seeking
        negation_score = len(features.negation_safety_hits) * self.policy.w_negation_safety

        if high_score:
            contrib["high_risk_keywords"] = round(high_score, 4)
            reasons.append(f"high-risk indicators: {', '.join(features.high_risk_hits)}")
        if med_score:
            contrib["medium_risk_keywords"] = round(med_score, 4)
            reasons.append(f"distress indicators: {', '.join(features.medium_risk_hits)}")
        if plan_score:
            contrib["plan_indicators"] = round(plan_score, 4)
            reasons.append(f"planning/immediacy language: {', '.join(features.plan_hits)}")
        if means_score:
            contrib["access_to_means"] = round(means_score, 4)
            reasons.append(f"means/access indicators: {', '.join(features.means_hits)}")
        if time_score:
            contrib["time_immediacy"] = round(time_score, 4)
            reasons.append(f"time immediacy indicators: {', '.join(features.time_immediacy_hits)}")
        if self_harm_score:
            contrib["self_harm_intent"] = round(self_harm_score, 4)
            reasons.append(f"self-harm indicators: {', '.join(features.self_harm_hits)}")
        if harm_others_score:
            contrib["harm_to_others"] = round(harm_others_score, 4)
            reasons.append(f"violence indicators: {', '.join(features.harm_to_others_hits)}")
        if distress_score:
            contrib["distress_intensifiers"] = round(distress_score, 4)
            reasons.append(f"distress intensifiers: {', '.join(features.distress_intensifier_hits)}")
        if protective_score:
            contrib["protective_factors"] = round(protective_score, 4)
            reasons.append(f"protective factors: {', '.join(features.protective_hits)}")
        if help_score:
            contrib["help_seeking"] = round(help_score, 4)
            reasons.append(f"help-seeking language: {', '.join(features.help_seeking_hits)}")
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

        if features.self_harm_hits and self.policy.never_auto_downgrade_self_harm:
            urgency_raw = max(urgency_raw, 0.72)
            contrib["self_harm_floor"] = 0.72

        if features.harm_to_others_hits and self.policy.never_auto_downgrade_violence:
            urgency_raw = max(urgency_raw, 0.72)
            contrib["violence_floor"] = 0.72

        urgency = clamp01(urgency_raw)

        feature_types_present = features.active_feature_groups()
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
            reasons.append(
                "limited direct risk language; score driven mostly by general distress density"
            )

        return RiskScore(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            severity_band=band,
            reasons=reasons,
            feature_contributions=contrib,
        )


# =============================================================================
# SECTION 7 — DECISION ENGINE
# =============================================================================

class DecisionEngine:
    PRIORITY_RANK = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }

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
            explanation = (
                f"Urgency {risk.urgency:.2f} remains below medium threshold; "
                f"standard queue recommended."
            )

        if low_confidence and self.policy.route_low_confidence_to_human:
            route = self.policy.mandatory_review_route
            requires_human_review = True
            explanation += " Confidence is low, so the case is routed to mandatory human review."

        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = self.policy.urgent_review_route
            requires_human_review = True
            explanation += " High-risk/low-confidence combination triggers urgent human review."

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

    @classmethod
    def priority_rank(cls, priority: str) -> int:
        return cls.PRIORITY_RANK.get(priority.upper(), 0)


# =============================================================================
# SECTION 8 — PERSISTENCE
# =============================================================================

class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).expanduser())
        ensure_parent_dir(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
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
                recorded_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES triage_records(case_id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS run_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )

        cur.execute("CREATE INDEX IF NOT EXISTS idx_records_timestamp ON triage_records(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_records_created_at ON triage_records(created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_case_id ON outcomes(case_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_run_events_created_at ON run_events(created_at)")
        self.conn.commit()

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO run_events (event_type, created_at, payload_json)
            VALUES (?, ?, ?)
            """,
            (event_type, utc_now_iso(), json_dumps(payload)),
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
                json_dumps(record.signal.metadata),
                json_dumps(asdict(record.features)),
                json_dumps(asdict(record.risk)),
                json_dumps(asdict(record.decision)),
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

        if updated:
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
            (max(1, int(limit)),),
        )
        rows = cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    def count_records(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM triage_records")
        row = cur.fetchone()
        return int(row["c"]) if row else 0

    def list_run_events(self, limit: int = 200) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM run_events ORDER BY id DESC LIMIT ?",
            (max(1, int(limit)),),
        )
        rows = cur.fetchall()
        results: List[Dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "id": row["id"],
                    "event_type": row["event_type"],
                    "created_at": row["created_at"],
                    "payload": json.loads(row["payload_json"]),
                }
            )
        return results

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
# SECTION 9 — AUDIT LOGGING
# =============================================================================

class AuditLogger:
    def __init__(self, jsonl_path: str, verbose: bool = True):
        self.jsonl_path = str(Path(jsonl_path).expanduser())
        self.verbose = verbose
        self._in_memory_log: List[Dict[str, Any]] = []
        ensure_parent_dir(self.jsonl_path)

    def log(self, record: TriageRecord) -> None:
        entry = record.to_public_dict()
        self._in_memory_log.append(entry)

        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json_dumps(entry) + "\n")

        if self.verbose:
            self._print_card(record)

    @staticmethod
    def _short_message(message: str, width: int = 88) -> str:
        clean = normalize_whitespace(message)
        return clean if len(clean) <= width else clean[: width - 1] + "…"

    def _print_card(self, record: TriageRecord) -> None:
        msg = self._short_message(record.signal.message)
        reasons = "; ".join(record.risk.reasons[:3]) or "n/a"
        flags = ", ".join(record.decision.safety_flags) if record.decision.safety_flags else "None"

        print("┌" + "─" * 96)
        print(f"│ CASE ID      : {record.case_id}")
        print(f"│ INPUT        : {msg}")
        print(f"│ URGENCY      : {record.risk.urgency:.4f}    CONFIDENCE: {record.risk.confidence:.4f}")
        print(f"│ BAND         : {record.risk.severity_band}")
        print(f"│ PRIORITY     : {record.decision.priority:<12} ROUTE: {record.decision.route_to}")
        print(f"│ HUMAN REVIEW : {record.decision.requires_human_review}")
        print(f"│ FLAGS        : {flags}")
        print(f"│ REASONS      : {self._short_message(reasons, 84)}")
        print(f"│ LATENCY      : {record.processing_ms:.2f} ms")
        print("└" + "─" * 96)

    def export_json(self) -> str:
        return json.dumps(self._in_memory_log, indent=2, ensure_ascii=False)


# =============================================================================
# SECTION 10 — FEEDBACK / EVALUATION
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
        routes = [r.decision.route_to for r in records]
        priorities = [r.decision.priority for r in records]
        outcomes = [r.outcome for r in records if r.outcome]
        human_review_count = sum(1 for r in records if r.decision.requires_human_review)
        flags = [flag for r in records for flag in r.decision.safety_flags]
        processing_ms = [r.processing_ms for r in records]

        severity_dist = Counter(r.risk.severity_band for r in records)
        priority_dist = Counter(priorities)
        route_dist = Counter(routes)
        outcome_dist = Counter(outcomes)
        flag_dist = Counter(flags)

        return {
            "records": len(records),
            "avg_urgency": round(statistics.mean(urgencies), 4),
            "median_urgency": round(statistics.median(urgencies), 4),
            "max_urgency": round(max(urgencies), 4),
            "avg_confidence": round(statistics.mean(confidences), 4),
            "median_confidence": round(statistics.median(confidences), 4),
            "avg_processing_ms": round(statistics.mean(processing_ms), 3),
            "max_processing_ms": round(max(processing_ms), 3),
            "human_review_rate": round(human_review_count / len(records), 4),
            "severity_distribution": dict(severity_dist),
            "priority_distribution": dict(priority_dist),
            "route_distribution": dict(route_dist),
            "flag_distribution": dict(flag_dist),
            "outcomes_logged": len(outcomes),
            "outcome_distribution": dict(outcome_dist),
        }

    def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
        records = [r for r in self.store.list_records(limit=limit) if r.outcome]
        if not records:
            return {"records_with_outcomes": 0, "buckets": {}}

        buckets: Dict[str, List[str]] = {
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

    def benchmark_report(self, benchmark_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not benchmark_rows:
            return {"benchmarks": 0}

        passes = sum(1 for row in benchmark_rows if row["passed"])
        flag_hits = sum(1 for row in benchmark_rows if row["flags_ok"])
        return {
            "benchmarks": len(benchmark_rows),
            "pass_rate": round(passes / len(benchmark_rows), 4),
            "flag_expectation_rate": round(flag_hits / len(benchmark_rows), 4),
            "details": benchmark_rows,
        }

    def export_summary_csv(self, path: str, limit: int = 5000) -> None:
        ensure_parent_dir(path)
        records = self.store.list_records(limit=limit)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "case_id",
                    "created_at",
                    "message",
                    "urgency",
                    "confidence",
                    "severity_band",
                    "priority",
                    "route_to",
                    "requires_human_review",
                    "processing_ms",
                    "outcome",
                ],
            )
            writer.writeheader()
            for r in records:
                writer.writerow(
                    {
                        "case_id": r.case_id,
                        "created_at": r.signal.created_at,
                        "message": r.signal.message,
                        "urgency": r.risk.urgency,
                        "confidence": r.risk.confidence,
                        "severity_band": r.risk.severity_band,
                        "priority": r.decision.priority,
                        "route_to": r.decision.route_to,
                        "requires_human_review": r.decision.requires_human_review,
                        "processing_ms": r.processing_ms,
                        "outcome": r.outcome or "",
                    }
                )


# =============================================================================
# SECTION 11 — BENCHMARKS
# =============================================================================

BENCHMARK_CASES: List[BenchmarkCase] = [
    BenchmarkCase(
        name="acute_self_harm_with_means",
        message="I have pills and I want to end my life tonight.",
        metadata={"channel": "sms", "suite": "benchmark"},
        expected_min_priority_rank=4,
        expected_flags=["SELF_HARM_SIGNAL", "PLAN_INDICATOR", "MEANS_INDICATOR"],
    ),
    BenchmarkCase(
        name="high_distress_help_seeking",
        message="Please help me right now. I feel hopeless and in crisis.",
        metadata={"channel": "chat", "suite": "benchmark"},
        expected_min_priority_rank=2,
        expected_flags=[],
    ),
    BenchmarkCase(
        name="negated_suicidality_but_panicking",
        message="Not suicidal. No plan. I am safe, but I need help tonight because I am panicking.",
        metadata={"channel": "chat", "suite": "benchmark"},
        expected_min_priority_rank=2,
        expected_flags=[],
    ),
    BenchmarkCase(
        name="violence_signal",
        message="I am so angry I think I might hurt someone with a knife.",
        metadata={"channel": "chat", "suite": "benchmark"},
        expected_min_priority_rank=3,
        expected_flags=["VIOLENCE_SIGNAL", "MEANS_INDICATOR"],
    ),
    BenchmarkCase(
        name="low_supportive_case",
        message="I feel stressed and needed someone to talk to, but I think I'll be okay.",
        metadata={"channel": "chat", "suite": "benchmark"},
        expected_min_priority_rank=1,
        expected_flags=[],
    ),
]


# =============================================================================
# SECTION 12 — MAIN ENGINE
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

        self.store.log_event(
            "engine_initialized",
            {
                "policy_name": self.policy.name,
                "policy_description": self.policy.description,
                "db_path": db_path,
                "audit_jsonl_path": audit_jsonl_path,
                "verbose": verbose,
            },
        )

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

    def run_benchmarks(self) -> Dict[str, Any]:
        rows: List[Dict[str, Any]] = []

        for case in BENCHMARK_CASES:
            record = self.process(case.message, metadata=case.metadata)
            actual_rank = self.decision_engine.priority_rank(record.decision.priority)
            expected_rank = case.expected_min_priority_rank
            passed = actual_rank >= expected_rank
            flags_ok = all(flag in record.decision.safety_flags for flag in case.expected_flags)

            rows.append(
                {
                    "name": case.name,
                    "expected_min_priority_rank": expected_rank,
                    "actual_priority": record.decision.priority,
                    "actual_rank": actual_rank,
                    "passed": passed,
                    "expected_flags": case.expected_flags,
                    "actual_flags": record.decision.safety_flags,
                    "flags_ok": flags_ok,
                    "urgency": record.risk.urgency,
                    "confidence": record.risk.confidence,
                }
            )

        self.store.log_event("benchmark_run", {"rows": rows})
        return self.feedback.benchmark_report(rows)

    def export_records(self, path: str, limit: int = 5000) -> None:
        ensure_parent_dir(path)
        payload = [r.to_public_dict() for r in self.store.list_records(limit=limit)]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def export_summary_csv(self, path: str, limit: int = 5000) -> None:
        self.feedback.export_summary_csv(path, limit=limit)

    def export_appendix_markdown(self, path: str, limit: int = 200) -> None:
        ensure_parent_dir(path)

        summary = self.report()
        calibration = self.calibration_report()
        records = self.store.list_records(limit=limit)
        benchmarks = self.run_benchmarks()

        lines: List[str] = []
        lines.append(f"# {PROJECT_TITLE}")
        lines.append("")
        lines.append(f"**Tagline:** {PROJECT_TAGLINE}")
        lines.append("")
        lines.append("## Project Summary")
        lines.append("")
        lines.append(PROJECT_SUMMARY)
        lines.append("")
        lines.append("## Overall Objective")
        lines.append("")
        lines.append(OVERALL_OBJECTIVE)
        lines.append("")
        lines.append("## Central Hypothesis")
        lines.append("")
        lines.append(CENTRAL_HYPOTHESIS)
        lines.append("")
        lines.append("## Policy Profile")
        lines.append("")
        lines.append(f"- Name: `{self.policy.name}`")
        lines.append(f"- Description: {self.policy.description}")
        lines.append(f"- Critical threshold: {self.policy.critical_threshold}")
        lines.append(f"- High threshold: {self.policy.high_threshold}")
        lines.append(f"- Medium threshold: {self.policy.medium_threshold}")
        lines.append("")
        lines.append("## Summary Metrics")
        lines.append("")
        for k, v in summary.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
        lines.append("## Calibration Snapshot")
        lines.append("")
        for k, v in calibration.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
        lines.append("## Benchmark Snapshot")
        lines.append("")
        for k, v in benchmarks.items():
            if k == "details":
                continue
            lines.append(f"- **{k}**: {v}")
        lines.append("")
        lines.append("## Recent Case Excerpts")
        lines.append("")
        for record in records[:10]:
            lines.append(f"### {record.case_id}")
            lines.append(f"- Message: {record.signal.message}")
            lines.append(f"- Urgency: {record.risk.urgency}")
            lines.append(f"- Confidence: {record.risk.confidence}")
            lines.append(f"- Priority: {record.decision.priority}")
            lines.append(f"- Route: {record.decision.route_to}")
            lines.append(f"- Flags: {record.decision.safety_flags}")
            lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def close(self) -> None:
        self.store.log_event("engine_closed", {"records": self.store.count_records()})
        self.store.close()


# =============================================================================
# SECTION 13 — DEMO DATA
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
# SECTION 14 — OUTPUT HELPERS
# =============================================================================

def print_header(title: str) -> None:
    print("\n" + "═" * 92)
    print(title)
    print("═" * 92 + "\n")


def print_sbir_concept() -> None:
    print_header("AI CRISIS TRIAGE SYSTEM — NIH SBIR CONCEPT OVERVIEW")

    sections = {
        "PROJECT TITLE": PROJECT_TITLE,
        "PROJECT TAGLINE": PROJECT_TAGLINE,
        "PROJECT SUMMARY": PROJECT_SUMMARY,
        "PUBLIC HEALTH NEED": PUBLIC_HEALTH_NEED,
        "OVERALL OBJECTIVE": OVERALL_OBJECTIVE,
        "CENTRAL HYPOTHESIS": CENTRAL_HYPOTHESIS,
        "SPECIFIC AIMS": SPECIFIC_AIMS,
        "SIGNIFICANCE": SIGNIFICANCE,
        "INNOVATION": INNOVATION,
        "APPROACH OVERVIEW": APPROACH_OVERVIEW,
        "TECHNICAL RISKS": TECHNICAL_RISKS,
        "RISK MITIGATIONS": RISK_MITIGATIONS,
        "EXPECTED OUTCOMES": EXPECTED_OUTCOMES,
        "EVALUATION PLAN": EVALUATION_PLAN,
        "ETHICS AND GOVERNANCE": ETHICS_AND_GOVERNANCE,
        "COMMERCIALIZATION": COMMERCIALIZATION,
        "PHASE I WORKPLAN": PHASE_I_WORKPLAN,
        "PHASE II DIRECTION": PHASE_II_DIRECTION,
        "SUCCESS METRICS": SUCCESS_METRICS,
        "MILESTONES": MILESTONES,
        "BUDGET": BUDGET,
    }

    for name, value in sections.items():
        print(name)
        print("-" * len(name))
        if isinstance(value, str):
            print(wrapped(value))
        elif isinstance(value, dict):
            total = 0
            for k, v in value.items():
                total += int(v)
                print(f"  - {k}: {fmt_usd(int(v))}")
            print(f"  - total: {fmt_usd(total)}")
        else:
            for item in value:
                print(f"  - {item}")
        print()


def print_submission_brief(policy: PolicyConfig) -> None:
    print_header("SUBMISSION BRIEF — EXECUTIVE READINESS VIEW")
    print(f"Title              : {PROJECT_TITLE}")
    print(f"Tagline            : {PROJECT_TAGLINE}")
    print(f"Policy             : {policy.name}")
    print(f"Policy Description : {policy.description}")
    print()
    print("Why this package is stronger for submission:")
    print("  - Deterministic and explainable scoring baseline")
    print("  - Human-review gates and conservative escalation logic")
    print("  - SQLite-backed persistence and JSONL audit logging")
    print("  - Benchmark cases, calibration snapshot, and export tooling")
    print("  - Explicit research framing, safety boundaries, and governance text")
    print("  - Single-file packaging that is easy to inspect and demonstrate")
    print()
    print("What reviewers can immediately evaluate:")
    print("  - project rationale")
    print("  - feature extraction logic")
    print("  - urgency / confidence calculation")
    print("  - routing policy and safety overrides")
    print("  - outcome tracking and retrospective analysis")
    print("  - exportable appendix artifacts")
    print()


def print_summary(summary: Dict[str, Any], calibration: Optional[Dict[str, Any]] = None) -> None:
    print_header("SESSION / DATABASE SUMMARY")
    for k, v in summary.items():
        print(f"{k:>28} : {v}")
    if calibration is not None:
        print("\nCALIBRATION SNAPSHOT")
        print("--------------------")
        for k, v in calibration.items():
            print(f"{k:>28} : {v}")
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


def print_benchmark_report(report: Dict[str, Any]) -> None:
    print_header("BENCHMARK REPORT")
    for k, v in report.items():
        if k == "details":
            continue
        print(f"{k:>28} : {v}")

    details = report.get("details", [])
    if details:
        print("\nDETAILS")
        print("-------")
        for row in details:
            print(
                f"- {row['name']}: priority={row['actual_priority']} "
                f"rank={row['actual_rank']} passed={row['passed']} "
                f"flags_ok={row['flags_ok']} urgency={row['urgency']:.4f} "
                f"confidence={row['confidence']:.4f}"
            )
    print()


def print_readiness_banner(db_path: str, audit_jsonl_path: str, policy_name: str) -> None:
    print_header("AI CRISIS TRIAGE SYSTEM — READY")
    print(f"Database        : {db_path}")
    print(f"Audit JSONL     : {audit_jsonl_path}")
    print(f"Policy          : {policy_name}")
    print()
    print("Try one of:")
    print("  --demo")
    print("  --interactive")
    print("  --batch cases.jsonl")
    print("  --summary")
    print("  --benchmarks")
    print("  --print-concept")
    print("  --print-submission-brief")
    print("  --export-records records.json")
    print("  --export-summary summary.csv")
    print("  --export-appendix appendix.md")
    print()


# =============================================================================
# SECTION 15 — CLI
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Crisis Triage System — NIH SBIR Research Submission-Ready Single-File Prototype"
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demonstration cases")
    parser.add_argument("--interactive", action="store_true", help="Run interactive console mode")
    parser.add_argument("--batch", type=str, help="Run batch mode from JSONL input file")
    parser.add_argument("--summary", action="store_true", help="Print summary from stored records")
    parser.add_argument("--show-case", type=str, help="Print detailed stored record by case_id")
    parser.add_argument("--benchmarks", action="store_true", help="Run built-in benchmark suite")
    parser.add_argument("--export-records", type=str, help="Export stored records to JSON file")
    parser.add_argument("--export-summary", type=str, help="Export summary rows to CSV file")
    parser.add_argument("--export-appendix", type=str, help="Export markdown appendix file")
    parser.add_argument("--print-concept", action="store_true", help="Print the SBIR concept package")
    parser.add_argument("--print-submission-brief", action="store_true", help="Print a concise submission-readiness brief")
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
# SECTION 16 — RUN MODES
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
    print("  /quit")
    print("  /summary")
    print("  /show <case_id>")
    print("  /bench")
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

        if raw == "/bench":
            print_benchmark_report(engine.run_benchmarks())
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

        engine.process(raw, metadata={"channel": "interactive_console"})


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
# SECTION 17 — MAIN
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    verbose = False if args.quiet else bool_from_env("CRISIS_TRIAGE_VERBOSE", True)

    engine = CrisisAIEngine(
        db_path=args.db,
        audit_jsonl_path=args.audit_jsonl,
        verbose=verbose,
        policy_name=args.policy,
    )

    try:
        if args.print_concept:
            print_sbir_concept()

        if args.print_submission_brief:
            print_submission_brief(engine.policy)

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

        if args.benchmarks:
            print_benchmark_report(engine.run_benchmarks())
            action_taken = True

        if args.export_records:
            engine.export_records(args.export_records)
            print(f"Exported records to {args.export_records}")
            action_taken = True

        if args.export_summary:
            engine.export_summary_csv(args.export_summary)
            print(f"Exported summary CSV to {args.export_summary}")
            action_taken = True

        if args.export_appendix:
            engine.export_appendix_markdown(args.export_appendix)
            print(f"Exported appendix markdown to {args.export_appendix}")
            action_taken = True

        if not action_taken:
            print_readiness_banner(args.db, args.audit_jsonl, args.policy)

    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

This version is stronger for submission because it adds:

- a fuller SBIR-style narrative
- clearer public-health need, hypothesis, workplan, evaluation, and governance sections
- policy profiles
- benchmark suite
- appendix export
- run-event logging
- more polished readiness and submission outputs

The next strongest upgrade would be a final “banker-polished” submission pack with:

- abstract page
- specific aims page
- commercialization section rewritten in formal NIH tone
- appendix templates
- README
- one-page executive summary
- matching slide deck text


#### You:
Appraise in dollars #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
════════════════════════════════════════════════════════════════════════════════
AI CRISIS TRIAGE SYSTEM — NIH SBIR RESEARCH / SUBMISSION-READY SINGLE-FILE KIT
════════════════════════════════════════════════════════════════════════════════

PURPOSE
-------
This file combines:
1) A grant-style NIH SBIR concept and submission support package
2) A functional research prototype for deterministic, auditable,
   human-in-the-loop AI-assisted crisis triage

... (documentation truncated for brevity, same as provided)
════════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import statistics
import sys
import textwrap
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# =============================================================================
# SECTION 1 — NIH SBIR CONCEPT / SUBMISSION NARRATIVE
# =============================================================================

PROJECT_TITLE = "AI-Driven Real-Time Crisis Triage and Decision Support System"

PROJECT_TAGLINE = (
    "A deterministic, auditable, human-in-the-loop crisis triage research "
    "platform for 988-aligned and related behavioral health workflows."
)

PROJECT_SUMMARY = """
Crisis response systems such as 988-aligned hotlines, behavioral health triage
centers, digital crisis intake channels, and emergency communication
environments face rising demand, workforce constraints, inconsistent
prioritization, limited real-time decision support, and growing requirements
for auditability and quality oversight.

This project proposes a deterministic, auditable, policy-aware, human-in-the-
loop AI decision support engine that:
- ingests free-text and structured crisis signals in real time,
- extracts interpretable risk indicators,
- estimates urgency and confidence under uncertainty,
- recommends routing and queue prioritization,
- logs all inputs, features, and recommendations for review,
- supports retrospective calibration and workflow improvement.

The core objective is to improve timeliness, consistency, safety oversight, and
research visibility into triage workflows while explicitly preserving human
authority over operational decisions.
""".strip()

PUBLIC_HEALTH_NEED = """
Behavioral health crisis systems continue to encounter increasing operational
pressure, including staffing shortages, uneven queue prioritization, and
variation in triage decisions across channels and shifts. Many organizations
lack structured tooling that can support early risk flagging while also
documenting why a recommendation was made. This creates operational friction in
both frontline response and later quality review. A system that offers
explainable, policy-aware, human-supervised triage support could strengthen
timeliness, consistency, accountability, and pilot readiness for future
evaluation efforts.
""".strip()

OVERALL_OBJECTIVE = """
Develop and validate a deterministic, explainable, research-grade crisis triage
decision support system that can assist qualified human operators by producing
auditable urgency estimates, routing recommendations, and retrospective review
artifacts suitable for pilot planning and operational evaluation.
""".strip()

CENTRAL_HYPOTHESIS = """
A conservative, deterministic, policy-aware triage support system with explicit
human-review gates and full audit logging can improve consistency and evidence
capture in crisis workflow simulations without removing human oversight.
""".strip()

SPECIFIC_AIMS = [
    "Build a real-time, policy-aware signal ingestion and feature extraction pipeline.",
    "Develop a deterministic, explainable risk scoring model for crisis urgency estimation.",
    "Implement a human-in-the-loop routing engine with auditable justifications and safety floors.",
    "Create an outcome feedback and retrospective evaluation layer for calibration, reporting, and pilot readiness.",
]

SIGNIFICANCE = [
    "Addresses growing crisis volume and workforce strain in behavioral health systems.",
    "Supports standardization without displacing trained human judgment.",
    "Improves auditability for quality assurance, incident review, and supervisory workflows.",
    "Creates a research asset for pilot studies, procurement preparation, and workflow modernization.",
]

INNOVATION = [
    "Explainable crisis triage under uncertainty rather than opaque end-to-end scoring.",
    "Policy-aware routing with explicit safety floors and uncertainty escalation.",
    "Structured auditability for each triage recommendation and its supporting features.",
    "Single-file research deployment model that supports rapid simulation, demonstration, and pilot preparation.",
]

APPROACH_OVERVIEW = [
    "Use deterministic lexicon and signal-pattern extraction as an interpretable baseline.",
    "Apply policy-configurable weighted scoring to derive urgency and confidence estimates.",
    "Use conservative routing logic with mandatory human review under specified conditions.",
    "Persist records, outcomes, and calibration snapshots for retrospective analysis.",
    "Generate submission-friendly summaries, appendices, and evidence exports.",
]

TECHNICAL_RISKS = [
    "False negatives in short or ambiguous messages.",
    "False positives from metaphorical, quoted, joking, or indirect language.",
    "Data drift across channels, geographies, organizations, and user populations.",
    "Operational latency and workflow integration complexity in real-world environments.",
    "Human factors risk if operators over-trust automation or misread model explanations.",
]

RISK_MITIGATIONS = [
    "Use human-in-the-loop policy gates for all high-severity recommendations.",
    "Escalate low-confidence cases to human review rather than auto-downgrading them.",
    "Keep model logic deterministic and auditable during the pilot-oriented baseline phase.",
    "Maintain conservative routing floors for self-harm and violence indicators.",
    "Persist all features, recommendations, and outcomes for calibration and retrospective review.",
]

EXPECTED_OUTCOMES = [
    "Reduced time-to-priority assignment in simulated or supervised workflows.",
    "Improved consistency of routing recommendations across repeated scenarios.",
    "Higher auditability for quality assurance and incident review.",
    "A clearer pilot-to-procurement evidence package for public-sector and provider settings.",
]

COMMERCIALIZATION = [
    "988-aligned crisis operations and behavioral health call centers.",
    "Emergency communications and public-sector triage modernization efforts.",
    "Healthcare providers and telehealth intake systems.",
    "Government-funded pilots focused on AI-assisted operations infrastructure.",
]

PHASE_I_WORKPLAN = [
    "Complete deterministic baseline engine and submission-grade research package.",
    "Define pilot evaluation scenarios and safety review pathways.",
    "Generate benchmark cases with outcome capture for supervised review.",
    "Produce policy, reporting, and appendix materials for evaluator inspection.",
]

PHASE_II_DIRECTION = [
    "Integrate secure service APIs and role-based reviewer interfaces.",
    "Expand evaluation design with expert review and organization-specific policy profiles.",
    "Add comparative calibration analysis across channels and scenario classes.",
    "Prepare secure pilot deployment architecture and formal validation studies.",
]

SUCCESS_METRICS = [
    "Coverage of predefined high-risk benchmark scenarios.",
    "Routing consistency across repeated evaluation runs.",
    "Reviewability of all recommendations and their feature-level explanations.",
    "Completeness of audit logs and retrospective exports.",
    "Operational feasibility for pilot demonstration and oversight workflows.",
]

EVALUATION_PLAN = [
    "Scenario-based benchmark review using labeled simulated cases.",
    "Retrospective comparison of urgency buckets against recorded outcomes.",
    "Review of human-review trigger rates and high-risk floor behavior.",
    "Latency measurement and persistence integrity checks.",
]

ETHICS_AND_GOVERNANCE = [
    "Human authority retained for all operational decisions.",
    "No autonomous dispatch or treatment decisions by the prototype.",
    "Explicit logging of model reasons, safety flags, and review triggers.",
    "Conservative handling of uncertainty and high-risk indicators.",
    "Clear boundary between research support and operational deployment.",
]

MILESTONES = [
    "Prototype ingestion pipeline and feature extraction.",
    "Deterministic risk model baseline validation.",
    "Decision routing simulation with policy guardrails.",
    "Human feedback and retrospective outcome capture.",
    "Benchmarking, calibration analysis, and pilot-readiness package.",
    "Submission appendix and reporting export generation.",
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

@dataclass(frozen=True)
class PolicyConfig:
    name: str = "default"

    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    low_confidence_floor: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    emergency_route: str = "EMERGENCY_DISPATCH"
    immediate_route: str = "IMMEDIATE_CLINICIAN"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "QUEUE_PRIORITY"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

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

    confidence_base: float = 0.50
    confidence_per_feature_type: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_structured_metadata: float = 0.05

    require_human_review_for_all_high: bool = True
    route_low_confidence_to_human: bool = True
    never_auto_downgrade_self_harm: bool = True
    never_auto_downgrade_violence: bool = True

    description: str = (
        "Default deterministic research policy with conservative escalation "
        "floors and mandatory human review for uncertainty-sensitive cases."
    )


def load_policy(policy_name: str = "default") -> PolicyConfig:
    policy_name = (policy_name or "default").strip().lower()

    if policy_name == "conservative":
        return PolicyConfig(
            name="conservative",
            critical_threshold=0.82,
            high_threshold=0.60,
            medium_threshold=0.35,
            low_confidence_floor=0.50,
            uncertain_high_risk_floor=0.55,
            description="Lower thresholds, stronger escalation bias, suitable for conservative pilot review.",
        )

    if policy_name == "balanced":
        return PolicyConfig(
            name="balanced",
            critical_threshold=0.86,
            high_threshold=0.66,
            medium_threshold=0.42,
            low_confidence_floor=0.44,
            uncertain_high_risk_floor=0.60,
            description="Balanced baseline policy for simulated workflow comparisons.",
        )

    return PolicyConfig(name="default")


# =============================================================================
# SECTION 3 — UTILITIES
# =============================================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def normalize_whitespace(text: str) -> str:
    return " ".join((text or "").split())


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def stable_case_id(message: str, ts: float) -> str:
    digest = hashlib.sha256(f"{ts}:{message}".encode("utf-8")).hexdigest()[:16]
    return f"case_{digest}"


def ensure_parent_dir(path: str) -> None:
    parent = Path(path).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


def bool_from_env(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=False)


def fmt_usd(amount: int) -> str:
    return f"${amount:,.0f}"


def wrapped(text: str, width: int = 92) -> str:
    return textwrap.fill(text, width=width)


def total_budget(budget: Dict[str, int]) -> int:
    return int(sum(int(v) for v in budget.values()))


# =============================================================================
# SECTION 4 — DATA MODELS
# =============================================================================

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
        groups = (
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
        )
        return sum(len(g) for g in groups)

    def active_feature_groups(self) -> int:
        groups = (
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
        )
        return sum(1 for g in groups if g)

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "word_count": self.word_count,
            "char_count": self.char_count,
            "sentence_count": self.sentence_count,
            "uppercase_ratio": self.uppercase_ratio,
            "exclamation_count": self.exclamation_count,
            "question_count": self.question_count,
            "total_signal_hits": self.total_signal_hits(),
            "active_feature_groups": self.active_feature_groups(),
        }


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


@dataclass
class BenchmarkCase:
    name: str
    message: str
    metadata: Dict[str, Any]
    expected_min_priority_rank: int
    expected_flags: List[str] = field(default_factory=list)


# =============================================================================
# SECTION 5 — FEATURE EXTRACTION
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
        r"\bself[- ]harm\b": "self_harm",
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
        r"\bpills?\b": "pills",
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
        r"\bself[- ]harm\b": "self_harm",
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
        r"^\s*help\s*$": "help_only_message",
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
        cleaned = normalize_whitespace(raw_input)
        ts = time.time()
        case_id = stable_case_id(cleaned, ts)
        created_at = utc_now_iso()
        metadata = dict(metadata or {})

        signal = CrisisSignal(
            case_id=case_id,
            timestamp=ts,
            created_at=created_at,
            message=cleaned,
            metadata=metadata,
        )

        lower = cleaned.lower()
        features = FeatureVector(
            word_count=len(cleaned.split()),
            char_count=len(cleaned),
            sentence_count=self._sentence_count(cleaned),
            uppercase_ratio=self._uppercase_ratio(cleaned),
            exclamation_count=cleaned.count("!"),
            question_count=cleaned.count("?"),
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
# SECTION 6 — RISK ENGINE
# =============================================================================

class RiskEngine:
    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    def score(self, features: FeatureVector) -> RiskScore:
        contributions: Dict[str, float] = {}

        # Base score from weighted features
        score = 0.0
        # High risk keywords
        if features.high_risk_hits:
            contrib = self.policy.w_high_risk_keywords * len(features.high_risk_hits)
            contributions["high_risk_keywords"] = contrib
            score += contrib
        # Medium risk
        if features.medium_risk_hits:
            contrib = self.policy.w_medium_risk_keywords * len(features.medium_risk_hits)
            contributions["medium_risk_keywords"] = contrib
            score += contrib
        # Plan indicators
        if features.plan_hits:
            contrib = self.policy.w_plan_indicators * len(features.plan_hits)
            contributions["plan_indicators"] = contrib
            score += contrib
        # Means
        if features.means_hits:
            contrib = self.policy.w_access_to_means * len(features.means_hits)
            contributions["access_to_means"] = contrib
            score += contrib
        # Time immediacy
        if features.time_immediacy_hits:
            contrib = self.policy.w_time_immediacy * len(features.time_immediacy_hits)
            contributions["time_immediacy"] = contrib
            score += contrib
        # Self-harm
        if features.self_harm_hits:
            contrib = self.policy.w_self_harm_intent * len(features.self_harm_hits)
            contributions["self_harm_intent"] = contrib
            score += contrib
        # Harm to others
        if features.harm_to_others_hits:
            contrib = self.policy.w_harm_to_others * len(features.harm_to_others_hits)
            contributions["harm_to_others"] = contrib
            score += contrib
        # Distress intensifiers
        if features.distress_intensifier_hits:
            contrib = self.policy.w_distress_intensifiers * len(features.distress_intensifier_hits)
            contributions["distress_intensifiers"] = contrib
            score += contrib
        # Protective factors (negative)
        if features.protective_hits:
            contrib = self.policy.w_protective_factors * len(features.protective_hits)
            contributions["protective_factors"] = contrib
            score += contrib
        # Help seeking
        if features.help_seeking_hits:
            contrib = self.policy.w_help_seeking * len(features.help_seeking_hits)
            contributions["help_seeking"] = contrib
            score += contrib
        # Negation safety
        if features.negation_safety_hits:
            contrib = self.policy.w_negation_safety * len(features.negation_safety_hits)
            contributions["negation_safety"] = contrib
            score += contrib
        # Short high signal: if message is short but contains high-risk words
        if features.word_count <= 12 and features.high_risk_hits:
            contrib = self.policy.w_short_high_signal
            contributions["short_high_signal"] = contrib
            score += contrib
        # Caps emphasis
        if features.uppercase_ratio > 0.3:
            contrib = self.policy.w_caps_emphasis
            contributions["caps_emphasis"] = contrib
            score += contrib
        # Punctuation emphasis
        if features.exclamation_count > 1 or features.question_count > 1:
            contrib = self.policy.w_punctuation_emphasis
            contributions["punctuation_emphasis"] = contrib
            score += contrib

        urgency = clamp01(score)

        # Confidence calculation
        confidence = self.policy.confidence_base
        # Add per active feature group
        confidence += self.policy.confidence_per_feature_type * features.active_feature_groups()
        # Signal density (hits per word)
        if features.word_count > 0:
            density = features.total_signal_hits() / features.word_count
            confidence += self.policy.confidence_per_signal_density * min(density, 2.0)
        # Penalty for ambiguity indicators
        if features.ambiguity_hits:
            confidence -= self.policy.confidence_penalty_ambiguity * len(features.ambiguity_hits)
        # Penalty for very short message without clear signals
        if features.word_count < 5 and features.total_signal_hits() == 0:
            confidence -= self.policy.confidence_penalty_too_short
        # Bonus for structured metadata (if present from ingestion)
        # This is already accounted for via the ingestion process, but we can add a small bump
        # if there is meaningful metadata beyond defaults.
        confidence = clamp01(confidence)

        # Determine severity band
        if urgency >= self.policy.critical_threshold:
            severity_band = "CRITICAL"
        elif urgency >= self.policy.high_threshold:
            severity_band = "HIGH"
        elif urgency >= self.policy.medium_threshold:
            severity_band = "MEDIUM"
        else:
            severity_band = "LOW"

        reasons = []
        if features.high_risk_hits:
            reasons.append(f"High-risk indicators: {', '.join(features.high_risk_hits[:3])}")
        if features.self_harm_hits:
            reasons.append(f"Self-harm intent expressed: {', '.join(features.self_harm_hits[:2])}")
        if features.harm_to_others_hits:
            reasons.append(f"Harm to others expressed: {', '.join(features.harm_to_others_hits[:2])}")
        if features.plan_hits:
            reasons.append("Specific plan elements detected.")
        if features.means_hits:
            reasons.append(f"Access to means indicated: {', '.join(features.means_hits[:2])}")
        if features.time_immediacy_hits:
            reasons.append("Imminent timeframe indicated.")
        if features.protective_hits:
            reasons.append("Protective statements present, may lower risk.")
        if features.negation_safety_hits:
            reasons.append("Explicit denial of intent, may lower risk.")
        if features.ambiguity_hits:
            reasons.append("Ambiguity/sarcasm markers detected; confidence reduced.")
        if not reasons:
            reasons.append("No strong crisis signals detected; base urgency low.")

        return RiskScore(
            urgency=urgency,
            confidence=confidence,
            severity_band=severity_band,
            reasons=reasons,
            feature_contributions=contributions,
        )


# =============================================================================
# SECTION 7 — DECISION ENGINE
# =============================================================================

class DecisionEngine:
    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    def decide(self, features: FeatureVector, risk: RiskScore) -> Decision:
        safety_flags = []
        requires_human_review = False

        # Determine priority and route based on urgency and confidence
        urgency = risk.urgency
        confidence = risk.confidence
        severity = risk.severity_band

        # Safety overrides
        has_self_harm = bool(features.self_harm_hits)
        has_violence = bool(features.harm_to_others_hits)
        has_plan = bool(features.plan_hits)
        has_means = bool(features.means_hits)

        # Determine base priority and route
        if severity == "CRITICAL":
            priority = "CRITICAL"
            route = self.policy.emergency_route
            requires_human_review = True
            safety_flags.append("CRITICAL_URGENCY")
        elif severity == "HIGH":
            priority = "HIGH"
            route = self.policy.immediate_route
            requires_human_review = True
        elif severity == "MEDIUM":
            priority = "MEDIUM"
            route = self.policy.priority_queue_route
        else:
            priority = "LOW"
            route = self.policy.standard_queue_route

        # Confidence-based adjustments
        if confidence < self.policy.low_confidence_floor:
            if severity in ("CRITICAL", "HIGH") and confidence < self.policy.uncertain_high_risk_floor:
                # Very low confidence on high-risk case → mandatory review
                requires_human_review = True
                route = self.policy.mandatory_review_route
                safety_flags.append("LOW_CONFIDENCE_HIGH_RISK")
            elif self.policy.route_low_confidence_to_human:
                requires_human_review = True
                route = self.policy.mandatory_review_route
                safety_flags.append("LOW_CONFIDENCE")
        else:
            if severity in ("HIGH", "CRITICAL") and self.policy.require_human_review_for_all_high:
                requires_human_review = True

        # Never auto-downgrade self-harm or violence cases
        if has_self_harm and self.policy.never_auto_downgrade_self_harm:
            if severity not in ("CRITICAL", "HIGH"):
                # Upgrade to at least HIGH
                priority = "HIGH"
                route = self.policy.immediate_route
                requires_human_review = True
                safety_flags.append("SELF_HARM_UPGRADE")
        if has_violence and self.policy.never_auto_downgrade_violence:
            if severity not in ("CRITICAL", "HIGH"):
                priority = "HIGH"
                route = self.policy.immediate_route
                requires_human_review = True
                safety_flags.append("VIOLENCE_UPGRADE")

        # Additional safety flags
        if has_plan and has_means:
            safety_flags.append("PLAN_AND_MEANS")
        elif has_plan:
            safety_flags.append("PLAN_DETECTED")
        elif has_means:
            safety_flags.append("MEANS_DETECTED")

        explanation_parts = [
            f"Urgency {urgency:.2f} (confidence {confidence:.2f}) → {priority} priority.",
        ]
        if risk.reasons:
            explanation_parts.append(f"Key factors: {risk.reasons[0]}")
        if safety_flags:
            explanation_parts.append(f"Safety flags: {', '.join(safety_flags)}")

        return Decision(
            priority=priority,
            route_to=route,
            explanation=" ".join(explanation_parts),
            requires_human_review=requires_human_review,
            safety_flags=safety_flags,
        )


# =============================================================================
# SECTION 8 — SQLITE STORAGE
# =============================================================================

class SQLiteStorage:
    def __init__(self, db_path: str = "crisis_triage.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS triage_records (
                case_id TEXT PRIMARY KEY,
                timestamp REAL,
                created_at TEXT,
                message TEXT,
                metadata_json TEXT,
                features_json TEXT,
                risk_json TEXT,
                decision_json TEXT,
                processing_ms REAL,
                outcome TEXT,
                reviewer_notes TEXT,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_timestamp ON triage_records(timestamp);
            CREATE INDEX IF NOT EXISTS idx_severity ON triage_records(json_extract(risk_json, '$.severity_band'));
            CREATE INDEX IF NOT EXISTS idx_priority ON triage_records(json_extract(decision_json, '$.priority'));
        """)
        conn.commit()
        conn.close()

    def save_record(self, record: TriageRecord) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO triage_records (
                case_id, timestamp, created_at, message, metadata_json,
                features_json, risk_json, decision_json, processing_ms,
                outcome, reviewer_notes, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.case_id,
            record.signal.timestamp,
            record.signal.created_at,
            record.signal.message,
            json_dumps(record.signal.metadata),
            json_dumps(asdict(record.features)),
            json_dumps(asdict(record.risk)),
            json_dumps(asdict(record.decision)),
            record.processing_ms,
            record.outcome,
            record.reviewer_notes,
            utc_now_iso(),
        ))
        conn.commit()
        conn.close()

    def load_records(self, limit: Optional[int] = None) -> List[TriageRecord]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM triage_records ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        rows = conn.execute(query).fetchall()
        conn.close()

        records = []
        for row in rows:
            signal = CrisisSignal(
                case_id=row["case_id"],
                timestamp=row["timestamp"],
                created_at=row["created_at"],
                message=row["message"],
                metadata=json.loads(row["metadata_json"]),
            )
            features_dict = json.loads(row["features_json"])
            features = FeatureVector(**features_dict)
            risk_dict = json.loads(row["risk_json"])
            risk = RiskScore(**risk_dict)
            decision_dict = json.loads(row["decision_json"])
            decision = Decision(**decision_dict)
            record = TriageRecord(
                case_id=row["case_id"],
                signal=signal,
                features=features,
                risk=risk,
                decision=decision,
                processing_ms=row["processing_ms"],
                outcome=row["outcome"],
                reviewer_notes=row["reviewer_notes"],
            )
            records.append(record)
        return records

    def update_outcome(self, case_id: str, outcome: str, notes: Optional[str] = None) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            UPDATE triage_records
            SET outcome = ?, reviewer_notes = ?, updated_at = ?
            WHERE case_id = ?
        """, (outcome, notes, utc_now_iso(), case_id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0


# =============================================================================
# SECTION 9 — AUDIT LOGGER
# =============================================================================

class AuditLogger:
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path or os.getenv("CRISIS_TRIAGE_AUDIT_JSONL", "audit_log.jsonl")
        if self.log_path:
            ensure_parent_dir(self.log_path)

    def log(self, record: TriageRecord) -> None:
        if not self.log_path:
            return
        with open(self.log_path, "a", encoding="utf-8") as f:
            entry = {
                "timestamp": utc_now_iso(),
                "case_id": record.case_id,
                "urgency": record.risk.urgency,
                "confidence": record.risk.confidence,
                "severity": record.risk.severity_band,
                "priority": record.decision.priority,
                "route": record.decision.route_to,
                "requires_human_review": record.decision.requires_human_review,
                "safety_flags": record.decision.safety_flags,
                "message": record.signal.message,
                "processing_ms": record.processing_ms,
            }
            f.write(json.dumps(entry) + "\n")


# =============================================================================
# SECTION 10 — TRIAGE SYSTEM (COORDINATOR)
# =============================================================================

class TriageSystem:
    def __init__(
        self,
        policy_name: str = "default",
        db_path: str = "crisis_triage.db",
        audit_log_path: Optional[str] = None,
        verbose: bool = False,
    ):
        self.policy = load_policy(policy_name)
        self.ingestion = SignalIngestion()
        self.risk_engine = RiskEngine(self.policy)
        self.decision_engine = DecisionEngine(self.policy)
        self.storage = SQLiteStorage(db_path)
        self.audit_logger = AuditLogger(audit_log_path)
        self.verbose = verbose or bool_from_env("CRISIS_TRIAGE_VERBOSE", False)

    def triage(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> TriageRecord:
        start = time.perf_counter()
        signal, features = self.ingestion.ingest(message, metadata)
        risk = self.risk_engine.score(features)
        decision = self.decision_engine.decide(features, risk)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        record = TriageRecord(
            case_id=signal.case_id,
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=elapsed_ms,
        )

        self.storage.save_record(record)
        self.audit_logger.log(record)

        if self.verbose:
            self._print_summary(record)

        return record

    def _print_summary(self, record: TriageRecord) -> None:
        print(f"\n--- Triage Result: {record.case_id} ---")
        print(f"Message: {record.signal.message}")
        print(f"Urgency: {record.risk.urgency:.2f} (Confidence: {record.risk.confidence:.2f})")
        print(f"Severity: {record.risk.severity_band}, Priority: {record.decision.priority}")
        print(f"Route: {record.decision.route_to}")
        print(f"Human Review Required: {record.decision.requires_human_review}")
        if record.decision.safety_flags:
            print(f"Safety Flags: {', '.join(record.decision.safety_flags)}")
        print(f"Processing Time: {record.processing_ms:.2f} ms")

    def record_outcome(self, case_id: str, outcome: str, notes: Optional[str] = None) -> bool:
        return self.storage.update_outcome(case_id, outcome, notes)


# =============================================================================
# SECTION 11 — DEMO SCENARIOS
# =============================================================================

DEMO_SCENARIOS = [
    {
        "name": "High Risk - Imminent Self Harm",
        "message": "I want to die tonight. I have pills ready. Nobody can help me.",
        "metadata": {"channel": "chat", "demo": True},
        "expected_priority": "CRITICAL or HIGH",
    },
    {
        "name": "Medium Risk - Distressed but No Plan",
        "message": "I feel completely overwhelmed and hopeless. I don't know what to do.",
        "metadata": {"channel": "voice", "demo": True},
        "expected_priority": "MEDIUM",
    },
    {
        "name": "Low Risk - Seeking Help Only",
        "message": "I need someone to talk to. I'm feeling anxious but I'm safe.",
        "metadata": {"channel": "app", "demo": True},
        "expected_priority": "LOW",
    },
    {
        "name": "Violence Toward Others",
        "message": "I'm going to hurt someone. I have a weapon and I'm so angry.",
        "metadata": {"channel": "hotline", "demo": True},
        "expected_priority": "CRITICAL or HIGH",
    },
    {
        "name": "Ambiguous / Sarcasm",
        "message": "Haha I'm so done with life lol just kidding not really",
        "metadata": {"channel": "sms", "demo": True},
        "expected_priority": "Requires human review",
    },
]


# =============================================================================
# SECTION 12 — SUMMARY AND REPORTING
# =============================================================================

def compute_summary_stats(records: List[TriageRecord]) -> Dict[str, Any]:
    if not records:
        return {"count": 0}
    urgencies = [r.risk.urgency for r in records]
    confidences = [r.risk.confidence for r in records]
    severity_counts = Counter(r.risk.severity_band for r in records)
    priority_counts = Counter(r.decision.priority for r in records)
    human_review_count = sum(1 for r in records if r.decision.requires_human_review)

    return {
        "count": len(records),
        "urgency_mean": statistics.mean(urgencies),
        "urgency_median": statistics.median(urgencies),
        "confidence_mean": statistics.mean(confidences),
        "severity_distribution": dict(severity_counts),
        "priority_distribution": dict(priority_counts),
        "human_review_rate": human_review_count / len(records) if records else 0,
        "avg_processing_ms": statistics.mean(r.processing_ms for r in records),
    }


def export_records_json(records: List[TriageRecord], output_path: str) -> None:
    ensure_parent_dir(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([r.to_public_dict() for r in records], f, indent=2, ensure_ascii=False)


def export_summary_csv(records: List[TriageRecord], output_path: str) -> None:
    ensure_parent_dir(output_path)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "case_id", "timestamp", "message", "urgency", "confidence",
            "severity", "priority", "route", "requires_human_review",
            "safety_flags", "outcome", "reviewer_notes"
        ])
        for r in records:
            writer.writerow([
                r.case_id,
                r.signal.created_at,
                r.signal.message,
                f"{r.risk.urgency:.3f}",
                f"{r.risk.confidence:.3f}",
                r.risk.severity_band,
                r.decision.priority,
                r.decision.route_to,
                str(r.decision.requires_human_review),
                "|".join(r.decision.safety_flags),
                r.outcome or "",
                r.reviewer_notes or "",
            ])


# =============================================================================
# SECTION 13 — CLI AND MAIN
# =============================================================================

def print_concept():
    print("=" * 100)
    print(f"PROJECT: {PROJECT_TITLE}")
    print(f"TAGLINE: {PROJECT_TAGLINE}")
    print("=" * 100)
    print(wrapped(PROJECT_SUMMARY))
    print("\nPUBLIC HEALTH NEED:")
    print(wrapped(PUBLIC_HEALTH_NEED))
    print("\nOBJECTIVE:")
    print(wrapped(OVERALL_OBJECTIVE))
    print("\nSPECIFIC AIMS:")
    for aim in SPECIFIC_AIMS:
        print(f"  - {aim}")
    print("\nSIGNIFICANCE:")
    for s in SIGNIFICANCE:
        print(f"  - {s}")
    print("\nINNOVATION:")
    for i in INNOVATION:
        print(f"  - {i}")


def print_submission_brief():
    print_concept()
    print("\n" + "=" * 100)
    print("BUDGET OVERVIEW")
    print("=" * 100)
    for k, v in BUDGET.items():
        print(f"  {k.replace('_', ' ').title()}: {fmt_usd(v)}")
    print(f"  TOTAL: {fmt_usd(total_budget(BUDGET))}")
    print("\nMILESTONES:")
    for m in MILESTONES:
        print(f"  - {m}")
    print("\nEVALUATION PLAN:")
    for e in EVALUATION_PLAN:
        print(f"  - {e}")
    print("\nETHICS & GOVERNANCE:")
    for g in ETHICS_AND_GOVERNANCE:
        print(f"  - {g}")


def export_appendix_markdown(output_path: str) -> None:
    ensure_parent_dir(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {PROJECT_TITLE} — Research Appendix\n\n")
        f.write("## Concept Summary\n\n")
        f.write(PROJECT_SUMMARY + "\n\n")
        f.write("## Specific Aims\n\n")
        for aim in SPECIFIC_AIMS:
            f.write(f"- {aim}\n")
        f.write("\n## Significance\n\n")
        for s in SIGNIFICANCE:
            f.write(f"- {s}\n")
        f.write("\n## Innovation\n\n")
        for i in INNOVATION:
            f.write(f"- {i}\n")
        f.write("\n## Approach Overview\n\n")
        for a in APPROACH_OVERVIEW:
            f.write(f"- {a}\n")
        f.write("\n## Technical Risks & Mitigations\n\n")
        for r, m in zip(TECHNICAL_RISKS, RISK_MITIGATIONS):
            f.write(f"- **Risk**: {r}  \n  **Mitigation**: {m}\n")
        f.write("\n## Expected Outcomes\n\n")
        for o in EXPECTED_OUTCOMES:
            f.write(f"- {o}\n")
        f.write("\n## Commercialization Pathways\n\n")
        for c in COMMERCIALIZATION:
            f.write(f"- {c}\n")
        f.write("\n## Phase I Workplan\n\n")
        for p in PHASE_I_WORKPLAN:
            f.write(f"- {p}\n")
        f.write("\n## Phase II Direction\n\n")
        for p in PHASE_II_DIRECTION:
            f.write(f"- {p}\n")
        f.write("\n## Success Metrics\n\n")
        for s in SUCCESS_METRICS:
            f.write(f"- {s}\n")
        f.write(f"\n## Budget Summary\n\n")
        f.write("| Category | Amount |\n|----------|--------|\n")
        for k, v in BUDGET.items():
            f.write(f"| {k.replace('_', ' ').title()} | {fmt_usd(v)} |\n")
        f.write(f"| **Total** | **{fmt_usd(total_budget(BUDGET))}** |\n")
    print(f"Appendix written to {output_path}")


def run_demo(system: TriageSystem) -> List[TriageRecord]:
    print("\nRunning Demo Scenarios...\n")
    records = []
    for scenario in DEMO_SCENARIOS:
        print(f"--- Scenario: {scenario['name']} ---")
        print(f"Message: {scenario['message']}")
        record = system.triage(scenario["message"], scenario["metadata"])
        records.append(record)
        print(f"Expected: {scenario['expected_priority']}\n")
    return records


def run_interactive(system: TriageSystem):
    print("\nInteractive Crisis Triage (type 'quit' to exit)\n")
    while True:
        try:
            msg = input("Enter crisis message: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if msg.lower() in ("quit", "exit", "q"):
            break
        if not msg:
            continue
        system.triage(msg, {"channel": "interactive"})
        print()


def run_batch(system: TriageSystem, input_path: str):
    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line: {line[:80]}...")
                continue
            msg = data.get("message", "")
            meta = data.get("metadata", {})
            if not msg:
                continue
            record = system.triage(msg, meta)
            records.append(record)
    print(f"Processed {len(records)} records from {input_path}")
    return records


def main():
    parser = argparse.ArgumentParser(description="AI Crisis Triage System (SBIR Research Prototype)")
    parser.add_argument("--demo", action="store_true", help="Run demonstration scenarios")
    parser.add_argument("--interactive", action="store_true", help="Interactive console mode")
    parser.add_argument("--batch", metavar="FILE.jsonl", help="Process JSONL batch file")
    parser.add_argument("--summary", action="store_true", help="Print summary statistics from database")
    parser.add_argument("--export-records", metavar="FILE.json", help="Export all records to JSON")
    parser.add_argument("--export-summary", metavar="FILE.csv", help="Export summary CSV")
    parser.add_argument("--export-appendix", metavar="FILE.md", help="Export SBIR appendix as markdown")
    parser.add_argument("--print-concept", action="store_true", help="Print SBIR concept summary")
    parser.add_argument("--print-submission-brief", action="store_true", help="Print full submission brief")
    parser.add_argument("--policy", default="default", help="Policy name (default, conservative, balanced)")
    parser.add_argument("--db", default="crisis_triage.db", help="SQLite database path")
    parser.add_argument("--audit-log", help="Audit log JSONL path")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Handle SBIR document exports without requiring DB setup
    if args.print_concept:
        print_concept()
        return
    if args.print_submission_brief:
        print_submission_brief()
        return
    if args.export_appendix:
        export_appendix_markdown(args.export_appendix)
        return

    # Initialize system
    system = TriageSystem(
        policy_name=args.policy,
        db_path=args.db,
        audit_log_path=args.audit_log,
        verbose=args.verbose,
    )

    # Mode dispatch
    if args.demo:
        run_demo(system)
    elif args.interactive:
        run_interactive(system)
    elif args.batch:
        run_batch(system, args.batch)
    elif args.summary:
        records = system.storage.load_records()
        stats = compute_summary_stats(records)
        print("\n--- Database Summary ---")
        for k, v in stats.items():
            print(f"{k}: {v}")
    elif args.export_records:
        records = system.storage.load_records()
        export_records_json(records, args.export_records)
        print(f"Exported {len(records)} records to {args.export_records}")
    elif args.export_summary:
        records = system.storage.load_records()
        export_summary_csv(records, args.export_summary)
        print(f"Exported summary CSV to {args.export_summary}")
    else:
        # Default to demo if no mode specified
        print("No mode specified. Running demo mode...\n")
        run_demo(system)


if __name__ == "__main__":
    main()

#### ChatGPT:
As-is, I’d appraise it at **$4,000–$12,000**.

My honest breakdown:

- **$4k–$6k** as a strong research prototype and grant-support asset.
- **$7k–$12k** if packaged well for a buyer who specifically wants:
  - a submission-ready SBIR-style concept
  - a deterministic triage prototype
  - audit logging, SQLite persistence, batch/demo modes
  - something easy to demo and extend

Why it has real value:

- It is not just code. It is **code + concept packaging + reporting + demoability**.
- The structure is unusually good for a single file.
- It has credible research framing, policy config, feature extraction, scoring, routing, storage, export, and CLI.
- It is legible enough that a technical reviewer, grant consultant, or small pilot team could actually use it as a starting point.

Why it is **not** worth much more yet:

- It is still a **heuristic prototype**, not a validated production crisis system.
- No real security architecture, auth, encryption, API service, role permissions, or deployment profile.
- No clinical validation, no real benchmark dataset, no calibration against real outcomes, no compliance layer.
- Some duplication and architectural inconsistency are still present, especially around storage/logger/system layers.
- The “submission-ready” narrative is stronger than the actual operational maturity.

Commercially:

- As a **GitHub/research asset**: about **$2,500–$6,000**.
- As a **custom consulting deliverable** to the right small org or founder: **$8,000–$15,000**.
- As a serious **government/health pilot base**, it needs another big step before it justifies higher numbers.

My blunt verdict: **good money-grade prototype, not yet enterprise-grade product**.

If you want, I can do a harsher institutional appraisal with a “what gets it to $25k+” breakdown.


#### You:
So do you think this can be integrated into the current ecosystem, like as is, or it has to be rewritten? And who is going to be responsible for rewriting it?

#### ChatGPT:
It can be **integrated as a research/demo layer as-is**, but **not as-is for real live crisis operations**.

The clean way to think about it:

**What it can do now**

- act as a prototype in demos
- support grant submissions
- simulate workflow logic
- generate audit-style records
- help a team discuss policy, routing, review queues, and evaluation design

**What it cannot safely do as-is**

- sit directly inside a real 988 or emergency workflow as an operational decision engine
- handle production security, privacy, permissions, incident controls, monitoring, or governance
- survive compliance review without major additions
- replace a properly designed service/API/application stack

So the answer is: **it does not need a total rewrite for concept validation**, but it **does need a structured rewrite/refactor for production integration**.

Who would be responsible depends on the stage:

**If this is for submission / pilot positioning**

- you or the product/research owner can keep this file as the “reference prototype”
- maybe lightly polish it, but no full rewrite is required yet

**If this is for a real pilot inside an organization**

- a **software engineer or engineering team** rewrites the architecture into services, APIs, auth, storage, logging, and deployment
- a **clinical/safety lead** defines policy constraints and escalation rules
- a **security/compliance owner** handles privacy, access control, audit, and review requirements
- a **product/research lead** owns evaluation design and pilot scope

So the rewrite responsibility is **not one person only**. Usually it breaks out like this:

- **you / founder / R\&D lead** own the concept and logic
- **engineering** owns system rewrite and integration
- **clinical/governance stakeholders** own safety policy
- **compliance/security** own deployability

If you personally stay in control, then practically **you are responsible for the rewrite plan**, even if someone else writes the code.

My blunt opinion:

- **for a grant:** keep it, polish it
- **for a real ecosystem integration:** refactor, not throw away
- **for production:** rewrite the shell around the core logic, and probably preserve the deterministic scoring logic as the baseline engine inside a more serious system

The smartest path is usually **not “rewrite everything”**. It is:

- preserve the scoring logic
- preserve the policy model
- preserve the benchmark cases
- preserve the narrative/docs
- rewrite the infrastructure around them

That is much cheaper and much more defensible.

If you want, I can map exactly which parts should be kept, which parts should be refactored, and which parts should be completely replaced.


#### You:
But how do you know that what you printed and what I deposited for you is actually what the system looks like from the inside?

#### ChatGPT:
That’s a sharp question—and honestly, it’s the right one to ask if you’re thinking like a real builder.

Short answer: **I don’t know for sure.**\
I only know what you showed me.

Here’s the precise breakdown so you can trust (or challenge) the evaluation properly:

---

### 1. What I *actually see*

I’m evaluating:

- the **code you pasted**
- the **structure and patterns inside that file**
- the **consistency between sections (policy → features → risk → decision → storage)**
- the **claims vs what’s implemented**

So my appraisal is based on:

> “If this file is the system, what is it worth?”

---

### 2. What I *cannot see*

I do NOT see:

- hidden modules
- external services
- deployment infrastructure
- real data pipelines
- integrations (APIs, Twilio, 988 systems, etc.)
- how it behaves under load
- whether it was tested in real conditions

So I **cannot verify the true “inside” of the system beyond this file**.

---

### 3. What I *infer from experience*

Even without seeing everything, there are strong signals:

From your file I can tell:

- it’s **deterministic, rule-based**
- no ML model training loop
- no real-time external ingestion
- no auth/security layer
- no distributed system behavior

That tells me:

> this is a **prototype engine + submission artifact**, not a deployed system

That inference is very reliable because production systems *always* leave fingerprints:

- retries
- backpressure
- queues
- auth
- observability
- failure handling
- concurrency control

Your file doesn’t show those → so it’s not that layer yet.

---

### 4. The key distinction (this is important)

There are 3 different “truths” of a system:

1. **Presentation layer** (what you showed)
2. **Core logic layer** (what actually makes decisions)
3. **Operational system** (what runs in reality)

What you gave me is:

> **1 + 2 combined in a single file**

What you *don’t yet have* (based on evidence) is:

> **3 (production system)**

---

### 5. Why my appraisal is still valid

Even without seeing everything, I can price:

- architecture quality
- clarity of logic
- extensibility
- realism of claims
- readiness for next stage

That’s enough to say:

> “This is a strong research prototype, not a deployable system yet”

And that’s exactly how buyers, grant reviewers, and engineers will also judge it.

---

### 6. The real test (if you want certainty)

If you want to prove it’s more than what I think, ask yourself:

- Can it handle **10,000 concurrent messages?**
- Can it integrate with **Twilio / SIP / chat APIs?**
- Does it enforce **HIPAA-like constraints?**
- Does it have **role-based access control?**
- Does it survive **process crash + restart cleanly?**
- Does it have **monitoring / alerting?**

If the answer is “no” or “not yet” → then my classification is correct.

---

### 7. The good news (and this matters)

This is actually a strong position.

Because:

- your **core logic is already clean**
- your **policy system is explicit**
- your **auditability is better than most prototypes**

That means:

> you’re not missing the brain—you’re missing the body around it

And that’s much easier to build than the reverse.

---

### Final truth

I’m not guessing randomly.\
I’m doing a **structural read of the system from the code you provided**.

But if you have:

- hidden modules
- real integrations
- production wrappers

then show them—and the valuation can jump **fast**.

---

If you want, I can do a **“prove it’s real” checklist** that would push this from $10k → $50k+ territory.


#### You:
Do it

#### ChatGPT:
Here’s the **prove-it’s-real checklist** that moves this from “good prototype” to “serious asset.”

## What gets it from \~$10k to $50k+

Right now, the file shows:

- strong concept framing
- coherent deterministic triage logic
- persistence and audit basics
- submission/demo readiness

What it does **not** yet prove is that the system can live inside a real operating environment.

To change that, you need evidence in five layers.

### 1. Real system boundary

This is where buyers stop thinking “research toy” and start thinking “usable platform.”

You want to show:

- real input interfaces, not just local CLI
- a real service boundary like HTTP API or queue consumer
- stable request/response schema
- health endpoint
- versioned policy/config
- reproducible startup and shutdown behavior

Proof items:

- `/health`, `/triage`, `/feedback`, `/summary` endpoints
- JSON schemas for input and output
- one-command local run
- sample API requests and responses
- service logs that show normal and failure cases

Without this, it still looks like a notebook-grade prototype in a nice coat.

### 2. Security and governance shell

For crisis-adjacent systems, this is not optional.

You want:

- authentication
- role separation
- audit of user actions, not just model actions
- redaction strategy
- environment-based secrets
- access control around records and outcomes

Proof items:

- admin vs reviewer roles
- immutable audit events
- record access logging
- redacted export mode
- documented data retention settings
- simple threat model

This alone changes how serious people perceive the asset.

### 3. Evaluation evidence

This is the single biggest gap between “clever script” and “fundable system.”

You need:

- labeled benchmark cases
- expected outcomes
- false positive / false negative analysis
- priority consistency checks
- calibration snapshots
- regression tests so behavior doesn’t drift silently

Proof items:

- benchmark suite with 50 to 200 curated scenarios
- pass/fail report
- confusion-style summary by severity bucket
- explicit tests for self-harm, violence, ambiguity, negation, plan, means
- test run artifact checked into repo

If the system can show “here are 120 benchmark cases and this version scores 93% as expected on our ruleset,” value jumps fast.

### 4. Operational readiness

This is where the market starts seeing “pilot candidate.”

You need to prove:

- restart safety
- error handling
- data integrity
- latency stability
- reproducible deployment
- observability

Proof items:

- process crash/restart with preserved state
- structured logs
- metrics like request count, latency, error count, human-review rate
- Dockerfile or equivalent run packaging
- example deployment config
- backup/export/restore path

Even a lightweight version of this makes the system feel real.

### 5. Human workflow fit

A crisis system is not just scoring. It has to fit people.

You need:

- reviewer-facing output
- explicit escalation reasons
- review queues
- outcome capture loop
- override support
- supervisory summaries

Proof items:

- “why this case was escalated” display
- override mechanism with reviewer notes
- queue states like standard, priority, urgent review
- supervisor summary screen or export
- outcome taxonomy with consistent labels

This turns it from “risk scorer” into “workflow support system.”

## The fastest path to higher value

If you want the shortest route to a real jump, build these in order:

**Tier 1: gets it to \~$15k–$25k**

- FastAPI service wrapper
- benchmark suite
- test cases
- structured logs
- markdown appendix and README
- Docker run path

**Tier 2: gets it to \~$25k–$50k**

- auth and role model
- reviewer override flow
- better audit events
- metrics endpoint
- redacted exports
- pilot-style dashboard or reviewer UI

**Tier 3: gets it beyond that**

- real channel integration
- formal evaluation with domain experts
- secure deployment package
- organization-specific policy profiles
- procurement-grade documentation

## What to keep vs replace

### Keep

These are the strongest parts of what you already have:

- deterministic feature extraction
- policy config idea
- urgency/confidence scoring structure
- routing logic
- benchmark concept
- audit/export mentality
- submission narrative sections

### Refactor

These should be improved, not discarded:

- storage layer consistency
- evaluation/reporting layout
- CLI modes
- policy profile handling
- benchmark/report exports
- decision explanation formatting

### Replace

These are the areas that need a more serious shell:

- local-only interface
- weak security posture
- limited operational observability
- flat persistence assumptions
- no real service/API boundary
- no user/role-aware workflow layer

## Who would believe it’s real

The first people who’ll take it seriously are:

- grant reviewers who like operational clarity
- consultants helping behavioral health orgs modernize workflows
- small pilot teams
- public-sector innovation groups
- founders building AI-assisted intake or triage infrastructure

The people who will **not** accept it as-is:

- enterprise security teams
- compliance teams
- serious health-system IT
- actual production 988 operations

That does not mean it is weak. It means it is at the **prototype-to-pilot bridge** stage.

## The proof package that changes perception

If I were packaging this to make people stop doubting it, I’d want exactly these artifacts:

- `crisis_triage_service.py`
- `README.md`
- `BENCHMARKS.md`
- `POLICY.md`
- `THREAT_MODEL.md`
- `demo_cases.jsonl`
- `tests/test_triage_rules.py`
- `docker-compose.yml` or simple Dockerfile
- `sample_exports/summary.csv`
- `sample_exports/appendix.md`

That package would feel dramatically more real than one large single file.

## Hard appraisal shift

Here’s how value changes in practice:

- **Current file as shown:** $4k–$12k
- **With API, tests, benchmark suite, README, Docker:** $15k–$25k
- **With auth, reviewer workflow, metrics, redaction, pilot-grade packaging:** $25k–$50k
- **With actual pilot evidence or domain validation:** potentially much higher

## The real bottleneck

Your bottleneck is **not logic quality**.

It is **evidence of operational maturity**.

That’s good news, because operational maturity can be added in layers.

## Blunt final verdict

To prove it’s real, you do **not** need to reinvent the scoring core.

You need to wrap it in:

- service boundaries
- tests
- benchmark evidence
- workflow surfaces
- security/governance scaffolding

That is what makes people pay.

If you want, next I can turn this into a **concrete “Phase 1 to $25k” build plan** with exact files, functions, and implementation order.


#### You:
Appraise this in dollars and readiness in %

#### ChatGPT:


#### You:
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
════════════════════════════════════════════════════════════════════════════════
AI CRISIS TRIAGE SYSTEM — NIH SBIR RESEARCH / SUBMISSION-READY SINGLE-FILE KIT
════════════════════════════════════════════════════════════════════════════════

PURPOSE
-------
This file provides a complete research package that combines:
1) A grant-style NIH SBIR concept and submission support documentation
2) A functional research prototype for deterministic, auditable,
   human-in-the-loop AI-assisted crisis triage

The system is designed to be a self-contained, single-file deployment that can
be used for research, simulation, workflow testing, pilot planning,
retrospective quality review, and human-in-the-loop decision support.

INTENDED USE
------------
This package is designed exclusively for:
- Research and development
- Simulation and modeling
- Workflow testing and validation
- Pilot planning and preparation
- Retrospective quality review
- Human-in-the-loop decision support

This system is NOT intended to be the sole basis for clinical, hotline,
dispatch, or emergency action. Final operational decisions must remain with
qualified human professionals operating under approved policies, training,
oversight, governance, legal/compliance review, and domain-specific protocols.

DESIGN GOALS
------------
- Deterministic, explainable scoring
- Human-in-the-loop routing recommendations
- Conservative safety escalation
- Auditability and reproducibility
- SQLite-backed persistence for all triage events
- Submission-grade project narrative support
- Research-ready extensibility
- Single-file deployment simplicity
- Clean CLI for demo, interactive, and batch workflows
- Evidence-friendly exports for pilot review

SUPPORTED MODES
---------------
- Demo mode with built-in scenarios
- Interactive console mode
- Batch JSONL input mode
- Summary / calibration reporting
- JSON export and CSV summary export
- Markdown appendix export
- Readiness / governance narrative printouts
- SQLite-backed persistence

EXAMPLE USAGE
-------------
python crisis_triage_sbir.py --demo
python crisis_triage_sbir.py --interactive
python crisis_triage_sbir.py --batch cases.jsonl
python crisis_triage_sbir.py --summary
python crisis_triage_sbir.py --export-records records.json
python crisis_triage_sbir.py --export-summary summary.csv
python crisis_triage_sbir.py --export-appendix appendix.md
python crisis_triage_sbir.py --print-concept
python crisis_triage_sbir.py --print-submission-brief

OPTIONAL ENV VARS
-----------------
CRISIS_TRIAGE_DB=crisis_triage.db
CRISIS_TRIAGE_AUDIT_JSONL=audit_log.jsonl
CRISIS_TRIAGE_VERBOSE=true
CRISIS_TRIAGE_POLICY=default
CRISIS_TRIAGE_APPENDIX=appendix.md

INPUT FORMAT FOR --batch
------------------------
One JSON object per line, for example:
{"message": "I want to end my life tonight. I have pills.", "metadata": {"channel": "chat"}}
{"message": "I feel overwhelmed and need help.", "metadata": {"channel": "voice"}}

AUTHORING NOTE
--------------
This package is intentionally research-oriented and includes:
- SBIR-style concept text
- Policy configuration
- Deterministic feature extraction
- Explainable risk engine
- Human review / escalation logic
- Outcome tracking
- Audit export
- Calibration statistics
- Summary reporting
- Readiness and appendix helpers
- CLI and persistence infrastructure

IMPORTANT SAFETY NOTE
---------------------
This is a prototype research tool. Real deployment in crisis environments would
require domain expert validation, secure architecture, privacy controls,
rigorous evaluation, formal human oversight, compliance review, approved
protocols, and operational governance with continuous monitoring.
════════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import statistics
import textwrap
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# SECTION 1 — NIH SBIR CONCEPT / SUBMISSION NARRATIVE
# =============================================================================
# This section contains the full grant-style narrative text that can be
# printed or exported as part of submission documentation. All content is
# aligned with NIH SBIR requirements and public health crisis response context.
# =============================================================================

PROJECT_TITLE = "AI-Driven Real-Time Crisis Triage and Decision Support System"

PROJECT_TAGLINE = (
    "A deterministic, auditable, human-in-the-loop crisis triage research "
    "platform for 988-aligned and related behavioral health workflows."
)

PROJECT_SUMMARY = """
Crisis response systems such as 988-aligned hotlines, behavioral health triage
centers, digital crisis intake channels, and emergency communication
environments face rising demand, workforce constraints, inconsistent
prioritization, limited real-time decision support, and growing requirements
for auditability and quality oversight.

This project proposes a deterministic, auditable, policy-aware, human-in-the-
loop AI decision support engine that:
- ingests free-text and structured crisis signals in real time,
- extracts interpretable risk indicators,
- estimates urgency and confidence under uncertainty,
- recommends routing and queue prioritization,
- logs all inputs, features, and recommendations for review,
- supports retrospective calibration and workflow improvement.

The core objective is to improve timeliness, consistency, safety oversight, and
research visibility into triage workflows while explicitly preserving human
authority over operational decisions.
""".strip()

PUBLIC_HEALTH_NEED = """
Behavioral health crisis systems continue to encounter increasing operational
pressure, including staffing shortages, uneven queue prioritization, and
variation in triage decisions across channels and shifts. Many organizations
lack structured tooling that can support early risk flagging while also
documenting why a recommendation was made. This creates operational friction in
both frontline response and later quality review. A system that offers
explainable, policy-aware, human-supervised triage support could strengthen
timeliness, consistency, accountability, and pilot readiness for future
evaluation efforts.
""".strip()

OVERALL_OBJECTIVE = """
Develop and validate a deterministic, explainable, research-grade crisis triage
decision support system that can assist qualified human operators by producing
auditable urgency estimates, routing recommendations, and retrospective review
artifacts suitable for pilot planning and operational evaluation.
""".strip()

CENTRAL_HYPOTHESIS = """
A conservative, deterministic, policy-aware triage support system with explicit
human-review gates and full audit logging can improve consistency and evidence
capture in crisis workflow simulations without removing human oversight.
""".strip()

SPECIFIC_AIMS = [
    "Build a real-time, policy-aware signal ingestion and feature extraction pipeline.",
    "Develop a deterministic, explainable risk scoring model for crisis urgency estimation.",
    "Implement a human-in-the-loop routing engine with auditable justifications and safety floors.",
    "Create an outcome feedback and retrospective evaluation layer for calibration, reporting, and pilot readiness.",
]

SIGNIFICANCE = [
    "Addresses growing crisis volume and workforce strain in behavioral health systems.",
    "Supports standardization without displacing trained human judgment.",
    "Improves auditability for quality assurance, incident review, and supervisory workflows.",
    "Creates a research asset for pilot studies, procurement preparation, and workflow modernization.",
]

INNOVATION = [
    "Explainable crisis triage under uncertainty rather than opaque end-to-end scoring.",
    "Policy-aware routing with explicit safety floors and uncertainty escalation.",
    "Structured auditability for each triage recommendation and its supporting features.",
    "Single-file research deployment model that supports rapid simulation, demonstration, and pilot preparation.",
]

APPROACH_OVERVIEW = [
    "Use deterministic lexicon and signal-pattern extraction as an interpretable baseline.",
    "Apply policy-configurable weighted scoring to derive urgency and confidence estimates.",
    "Use conservative routing logic with mandatory human review under specified conditions.",
    "Persist records, outcomes, and calibration snapshots for retrospective analysis.",
    "Generate submission-friendly summaries, appendices, and evidence exports.",
]

TECHNICAL_RISKS = [
    "False negatives in short or ambiguous messages.",
    "False positives from metaphorical, quoted, joking, or indirect language.",
    "Data drift across channels, geographies, organizations, and user populations.",
    "Operational latency and workflow integration complexity in real-world environments.",
    "Human factors risk if operators over-trust automation or misread model explanations.",
]

RISK_MITIGATIONS = [
    "Use human-in-the-loop policy gates for all high-severity recommendations.",
    "Escalate low-confidence cases to human review rather than auto-downgrading them.",
    "Keep model logic deterministic and auditable during the pilot-oriented baseline phase.",
    "Maintain conservative routing floors for self-harm and violence indicators.",
    "Persist all features, recommendations, and outcomes for calibration and retrospective review.",
]

EXPECTED_OUTCOMES = [
    "Reduced time-to-priority assignment in simulated or supervised workflows.",
    "Improved consistency of routing recommendations across repeated scenarios.",
    "Higher auditability for quality assurance and incident review.",
    "A clearer pilot-to-procurement evidence package for public-sector and provider settings.",
]

COMMERCIALIZATION = [
    "988-aligned crisis operations and behavioral health call centers.",
    "Emergency communications and public-sector triage modernization efforts.",
    "Healthcare providers and telehealth intake systems.",
    "Government-funded pilots focused on AI-assisted operations infrastructure.",
]

PHASE_I_WORKPLAN = [
    "Complete deterministic baseline engine and submission-grade research package.",
    "Define pilot evaluation scenarios and safety review pathways.",
    "Generate benchmark cases with outcome capture for supervised review.",
    "Produce policy, reporting, and appendix materials for evaluator inspection.",
]

PHASE_II_DIRECTION = [
    "Integrate secure service APIs and role-based reviewer interfaces.",
    "Expand evaluation design with expert review and organization-specific policy profiles.",
    "Add comparative calibration analysis across channels and scenario classes.",
    "Prepare secure pilot deployment architecture and formal validation studies.",
]

SUCCESS_METRICS = [
    "Coverage of predefined high-risk benchmark scenarios.",
    "Routing consistency across repeated evaluation runs.",
    "Reviewability of all recommendations and their feature-level explanations.",
    "Completeness of audit logs and retrospective exports.",
    "Operational feasibility for pilot demonstration and oversight workflows.",
]

EVALUATION_PLAN = [
    "Scenario-based benchmark review using labeled simulated cases.",
    "Retrospective comparison of urgency buckets against recorded outcomes.",
    "Review of human-review trigger rates and high-risk floor behavior.",
    "Latency measurement and persistence integrity checks.",
]

ETHICS_AND_GOVERNANCE = [
    "Human authority retained for all operational decisions.",
    "No autonomous dispatch or treatment decisions by the prototype.",
    "Explicit logging of model reasons, safety flags, and review triggers.",
    "Conservative handling of uncertainty and high-risk indicators.",
    "Clear boundary between research support and operational deployment.",
]

MILESTONES = [
    "Prototype ingestion pipeline and feature extraction.",
    "Deterministic risk model baseline validation.",
    "Decision routing simulation with policy guardrails.",
    "Human feedback and retrospective outcome capture.",
    "Benchmarking, calibration analysis, and pilot-readiness package.",
    "Submission appendix and reporting export generation.",
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
# The PolicyConfig dataclass centralizes all tunable thresholds, weights,
# and routing labels. Different policy presets (default, conservative,
# balanced) can be loaded via the load_policy() factory function.
# =============================================================================

@dataclass(frozen=True)
class PolicyConfig:
    """
    Configuration container for all policy-related parameters.
    Instances are immutable and can be shared safely across components.
    """
    name: str = "default"

    # Urgency band thresholds (0.0 to 1.0)
    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    # Confidence handling thresholds
    low_confidence_floor: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    # Route label mappings (human-readable, can be adapted to local SOPs)
    emergency_route: str = "EMERGENCY_DISPATCH"
    immediate_route: str = "IMMEDIATE_CLINICIAN"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "QUEUE_PRIORITY"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

    # Feature weights for urgency calculation
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

    # Confidence calculation parameters
    confidence_base: float = 0.50
    confidence_per_feature_type: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_structured_metadata: float = 0.05

    # Decision engine safety overrides
    require_human_review_for_all_high: bool = True
    route_low_confidence_to_human: bool = True
    never_auto_downgrade_self_harm: bool = True
    never_auto_downgrade_violence: bool = True

    # Human-readable description for reporting
    description: str = (
        "Default deterministic research policy with conservative escalation "
        "floors and mandatory human review for uncertainty-sensitive cases."
    )


def load_policy(policy_name: str = "default") -> PolicyConfig:
    """
    Factory function to return a PolicyConfig instance based on a named preset.
    Additional presets can be added here as needed.
    """
    policy_name = (policy_name or "default").strip().lower()

    if policy_name == "conservative":
        return PolicyConfig(
            name="conservative",
            critical_threshold=0.82,
            high_threshold=0.60,
            medium_threshold=0.35,
            low_confidence_floor=0.50,
            uncertain_high_risk_floor=0.55,
            description="Lower thresholds, stronger escalation bias, suitable for conservative pilot review.",
        )

    if policy_name == "balanced":
        return PolicyConfig(
            name="balanced",
            critical_threshold=0.86,
            high_threshold=0.66,
            medium_threshold=0.42,
            low_confidence_floor=0.44,
            uncertain_high_risk_floor=0.60,
            description="Balanced baseline policy for simulated workflow comparisons.",
        )

    # Default policy (also returned for any unrecognized name)
    return PolicyConfig(name="default")


# =============================================================================
# SECTION 3 — UTILITIES
# =============================================================================
# General-purpose helper functions used throughout the codebase.
# =============================================================================

def utc_now() -> datetime:
    """Return current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return current UTC datetime as ISO 8601 string."""
    return utc_now().isoformat()


def normalize_whitespace(text: str) -> str:
    """
    Collapse all whitespace sequences (spaces, tabs, newlines) into single
    spaces and trim leading/trailing whitespace.
    """
    return " ".join((text or "").split())


def clamp01(value: float) -> float:
    """Constrain a floating point value to the interval [0.0, 1.0]."""
    return max(0.0, min(1.0, value))


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert any value to float, returning a default if conversion fails.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def stable_case_id(message: str, ts: float) -> str:
    """
    Generate a deterministic, collision-resistant case identifier based on the
    message content and a timestamp. Uses SHA-256 truncated to 16 hex digits.
    """
    digest = hashlib.sha256(f"{ts}:{message}".encode("utf-8")).hexdigest()[:16]
    return f"case_{digest}"


def ensure_parent_dir(path: str) -> None:
    """
    Ensure that the parent directory of the given file path exists,
    creating it if necessary.
    """
    parent = Path(path).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


def bool_from_env(name: str, default: bool = True) -> bool:
    """
    Read a boolean value from an environment variable. Accepts '1', 'true',
    'yes', 'y', 'on' (case-insensitive) as True.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def json_dumps(value: Any) -> str:
    """
    Serialize a Python object to a compact JSON string with non-ASCII
    characters preserved.
    """
    return json.dumps(value, ensure_ascii=False, sort_keys=False)


def fmt_usd(amount: int) -> str:
    """Format an integer amount as US dollars with thousands separators."""
    return f"${amount:,.0f}"


def wrapped(text: str, width: int = 92) -> str:
    """Wrap a paragraph of text to a specified width for console display."""
    return textwrap.fill(text, width=width)


def total_budget(budget: Dict[str, int]) -> int:
    """Sum all values in the budget dictionary."""
    return int(sum(int(v) for v in budget.values()))


# =============================================================================
# SECTION 4 — DATA MODELS
# =============================================================================
# Core dataclasses that represent the state flowing through the pipeline.
# =============================================================================

@dataclass
class CrisisSignal:
    """
    Represents a single incoming crisis communication, including metadata
    about the context of the message.
    """
    case_id: str
    timestamp: float
    created_at: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureVector:
    """
    Container for all extracted features from a CrisisSignal.
    Includes both numeric descriptors and lists of matched pattern labels.
    """
    # Basic text statistics
    word_count: int
    char_count: int
    sentence_count: int
    uppercase_ratio: float
    exclamation_count: int
    question_count: int

    # Pattern match results (each list holds the matched label strings)
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
        """Return the total number of pattern matches across all categories."""
        groups = (
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
        )
        return sum(len(g) for g in groups)

    def active_feature_groups(self) -> int:
        """
        Count how many distinct feature categories have at least one match.
        Used as a proxy for signal diversity.
        """
        groups = (
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
        )
        return sum(1 for g in groups if g)

    def summary_dict(self) -> Dict[str, Any]:
        """Return a compact summary dictionary of numeric features."""
        return {
            "word_count": self.word_count,
            "char_count": self.char_count,
            "sentence_count": self.sentence_count,
            "uppercase_ratio": self.uppercase_ratio,
            "exclamation_count": self.exclamation_count,
            "question_count": self.question_count,
            "total_signal_hits": self.total_signal_hits(),
            "active_feature_groups": self.active_feature_groups(),
        }


@dataclass
class RiskScore:
    """
    Output of the risk engine: urgency estimate, confidence, severity band,
    and supporting explanatory information.
    """
    urgency: float
    confidence: float
    severity_band: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    reasons: List[str] = field(default_factory=list)
    feature_contributions: Dict[str, float] = field(default_factory=dict)


@dataclass
class Decision:
    """
    Output of the decision engine: final priority, routing recommendation,
    human-review flag, and any safety flags triggered.
    """
    priority: str
    route_to: str
    explanation: str
    requires_human_review: bool
    safety_flags: List[str] = field(default_factory=list)


@dataclass
class TriageRecord:
    """
    Complete record of a single triage case, aggregating all pipeline outputs.
    Includes optional outcome and reviewer notes fields.
    """
    case_id: str
    signal: CrisisSignal
    features: FeatureVector
    risk: RiskScore
    decision: Decision
    processing_ms: float
    outcome: Optional[str] = None
    reviewer_notes: Optional[str] = None

    def to_public_dict(self) -> Dict[str, Any]:
        """
        Convert the triage record to a JSON-serializable dictionary suitable
        for exports and audit logs.
        """
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


@dataclass
class BenchmarkCase:
    """
    Definition of a benchmark test case, including expected minimum priority
    rank and a list of expected safety flags.
    """
    name: str
    message: str
    metadata: Dict[str, Any]
    expected_min_priority_rank: int
    expected_flags: List[str] = field(default_factory=list)


# =============================================================================
# SECTION 5 — FEATURE EXTRACTION
# =============================================================================
# The SignalIngestion class transforms raw text into a structured
# FeatureVector using a set of regex-based pattern matchers.
# =============================================================================

class SignalIngestion:
    """
    Deterministic feature extractor that uses curated regex patterns to detect
    clinically and operationally relevant signals in crisis text.
    """

    # Patterns are defined as class-level dictionaries for clarity.
    # Each dictionary maps a regex pattern to a human-readable label.

    HIGH_RISK_PATTERNS = {
        r"\bi want to die\b": "want_to_die",
        r"\bend my life\b": "end_my_life",
        r"\bkill myself\b": "kill_myself",
        r"\bsuicide\b": "suicide",
        r"\bno reason to live\b": "no_reason_to_live",
        r"\bcan't go on\b": "cant_go_on",
        r"\boverdose\b": "overdose",
        r"\bhurt myself\b": "hurt_myself",
        r"\bself[- ]harm\b": "self_harm",
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
        r"\bpills?\b": "pills",
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
        r"\bself[- ]harm\b": "self_harm",
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
        r"^\s*help\s*$": "help_only_message",
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
        """
        Scan the lowercased text against a dictionary of patterns and return
        a sorted list of unique matching labels.
        """
        hits: List[str] = []
        for pattern, label in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(label)
        return sorted(set(hits))

    @staticmethod
    def _sentence_count(message: str) -> int:
        """
        Estimate the number of sentences based on punctuation delimiters
        (. ! ?). Returns at least 1.
        """
        parts = [p.strip() for p in re.split(r"[.!?]+", message) if p.strip()]
        return max(1, len(parts))

    @staticmethod
    def _uppercase_ratio(message: str) -> float:
        """
        Compute the ratio of uppercase alphabetic characters to total
        alphabetic characters.
        """
        letters = [c for c in message if c.isalpha()]
        if not letters:
            return 0.0
        uppers = sum(1 for c in letters if c.isupper())
        return round(uppers / max(1, len(letters)), 4)

    def ingest(self, raw_input: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[CrisisSignal, FeatureVector]:
        """
        Main ingestion method: normalizes the input, generates a case ID,
        extracts all features, and returns a CrisisSignal and FeatureVector.
        """
        cleaned = normalize_whitespace(raw_input)
        ts = time.time()
        case_id = stable_case_id(cleaned, ts)
        created_at = utc_now_iso()
        metadata = dict(metadata or {})

        signal = CrisisSignal(
            case_id=case_id,
            timestamp=ts,
            created_at=created_at,
            message=cleaned,
            metadata=metadata,
        )

        lower = cleaned.lower()
        features = FeatureVector(
            word_count=len(cleaned.split()),
            char_count=len(cleaned),
            sentence_count=self._sentence_count(cleaned),
            uppercase_ratio=self._uppercase_ratio(cleaned),
            exclamation_count=cleaned.count("!"),
            question_count=cleaned.count("?"),
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

        # Augment metadata with basic text statistics for convenience
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
# SECTION 6 — RISK ENGINE
# =============================================================================
# The RiskEngine computes an urgency score and confidence estimate from a
# FeatureVector using the weights and thresholds defined in the active policy.
# =============================================================================

class RiskEngine:
    """
    Deterministic risk scoring engine. All calculations are policy-driven
    and produce fully explainable outputs.
    """
    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    def score(self, signal: CrisisSignal, features: FeatureVector) -> RiskScore:
        """
        Compute urgency and confidence for the given signal and feature vector.
        Returns a RiskScore object with severity band and explanatory reasons.
        """
        contrib: Dict[str, float] = {}
        reasons: List[str] = []

        # Base score from text density (small contribution)
        base = min(0.18, features.word_count / 300.0)
        contrib["base_text_density"] = round(base, 4)

        # Compute weighted contributions from each feature category
        high_score = len(features.high_risk_hits) * self.policy.w_high_risk_keywords
        med_score = len(features.medium_risk_hits) * self.policy.w_medium_risk_keywords
        plan_score = len(features.plan_hits) * self.policy.w_plan_indicators
        means_score = len(features.means_hits) * self.policy.w_access_to_means
        time_score = len(features.time_immediacy_hits) * self.policy.w_time_immediacy
        self_harm_score = len(features.self_harm_hits) * self.policy.w_self_harm_intent
        harm_others_score = len(features.harm_to_others_hits) * self.policy.w_harm_to_others
        distress_score = len(features.distress_intensifier_hits) * self.policy.w_distress_intensifiers
        protective_score = len(features.protective_hits) * self.policy.w_protective_factors
        help_score = len(features.help_seeking_hits) * self.policy.w_help_seeking
        negation_score = len(features.negation_safety_hits) * self.policy.w_negation_safety

        # Record contributions and build human-readable reasons
        if high_score:
            contrib["high_risk_keywords"] = round(high_score, 4)
            reasons.append(f"high-risk indicators: {', '.join(features.high_risk_hits)}")
        if med_score:
            contrib["medium_risk_keywords"] = round(med_score, 4)
            reasons.append(f"distress indicators: {', '.join(features.medium_risk_hits)}")
        if plan_score:
            contrib["plan_indicators"] = round(plan_score, 4)
            reasons.append(f"planning/immediacy language: {', '.join(features.plan_hits)}")
        if means_score:
            contrib["access_to_means"] = round(means_score, 4)
            reasons.append(f"means/access indicators: {', '.join(features.means_hits)}")
        if time_score:
            contrib["time_immediacy"] = round(time_score, 4)
            reasons.append(f"time immediacy indicators: {', '.join(features.time_immediacy_hits)}")
        if self_harm_score:
            contrib["self_harm_intent"] = round(self_harm_score, 4)
            reasons.append(f"self-harm indicators: {', '.join(features.self_harm_hits)}")
        if harm_others_score:
            contrib["harm_to_others"] = round(harm_others_score, 4)
            reasons.append(f"violence indicators: {', '.join(features.harm_to_others_hits)}")
        if distress_score:
            contrib["distress_intensifiers"] = round(distress_score, 4)
            reasons.append(f"distress intensifiers: {', '.join(features.distress_intensifier_hits)}")
        if protective_score:
            contrib["protective_factors"] = round(protective_score, 4)
            reasons.append(f"protective factors: {', '.join(features.protective_hits)}")
        if help_score:
            contrib["help_seeking"] = round(help_score, 4)
            reasons.append(f"help-seeking language: {', '.join(features.help_seeking_hits)}")
        if negation_score:
            contrib["negation_safety"] = round(negation_score, 4)
            reasons.append(f"negation/safety language: {', '.join(features.negation_safety_hits)}")

        # Short message with high signal content gets a small boost
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

        # Emphasis from CAPS and excessive punctuation
        emphasis = 0.0
        if features.uppercase_ratio >= 0.35:
            emphasis += self.policy.w_caps_emphasis
        if features.exclamation_count >= 2:
            emphasis += self.policy.w_punctuation_emphasis
        if emphasis:
            contrib["emphasis"] = round(emphasis, 4)
            reasons.append("text emphasis pattern present")

        # Sum raw urgency
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

        # Apply policy-mandated safety floors
        if features.self_harm_hits and self.policy.never_auto_downgrade_self_harm:
            urgency_raw = max(urgency_raw, 0.72)
            contrib["self_harm_floor"] = 0.72

        if features.harm_to_others_hits and self.policy.never_auto_downgrade_violence:
            urgency_raw = max(urgency_raw, 0.72)
            contrib["violence_floor"] = 0.72

        urgency = clamp01(urgency_raw)

        # Confidence estimation
        feature_types_present = features.active_feature_groups()
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

        confidence = clamp01(confidence)

        # Determine severity band
        if urgency >= self.policy.critical_threshold:
            band = "CRITICAL"
        elif urgency >= self.policy.high_threshold:
            band = "HIGH"
        elif urgency >= self.policy.medium_threshold:
            band = "MEDIUM"
        else:
            band = "LOW"

        # Fallback reason if none were generated
        if not reasons:
            reasons.append(
                "limited direct risk language; score driven mostly by general distress density"
            )

        return RiskScore(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            severity_band=band,
            reasons=reasons,
            feature_contributions=contrib,
        )


# =============================================================================
# SECTION 7 — DECISION ENGINE
# =============================================================================
# The DecisionEngine translates a RiskScore and FeatureVector into a concrete
# routing recommendation, incorporating policy overrides and safety gates.
# =============================================================================

class DecisionEngine:
    """
    Policy-aware decision engine that maps urgency and confidence into a
    priority level, route label, and human-review requirement.
    """

    # Mapping from priority string to numeric rank for comparisons
    PRIORITY_RANK = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }

    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    def decide(self, signal: CrisisSignal, features: FeatureVector, risk: RiskScore) -> Decision:
        """
        Apply decision logic to produce a routing recommendation.
        Safety flags and human-review requirements are computed based on
        policy thresholds and feature flags.
        """
        safety_flags: List[str] = []
        requires_human_review = False

        # Determine presence of critical signals
        self_harm_present = bool(features.self_harm_hits or features.high_risk_hits)
        violence_present = bool(features.harm_to_others_hits)
        low_confidence = risk.confidence < self.policy.low_confidence_floor

        # Build safety flag list
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

        # Primary routing based on urgency band
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
            explanation = (
                f"Urgency {risk.urgency:.2f} remains below medium threshold; "
                f"standard queue recommended."
            )

        # Apply confidence-based overrides
        if low_confidence and self.policy.route_low_confidence_to_human:
            route = self.policy.mandatory_review_route
            requires_human_review = True
            explanation += " Confidence is low, so the case is routed to mandatory human review."

        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = self.policy.urgent_review_route
            requires_human_review = True
            explanation += " High-risk/low-confidence combination triggers urgent human review."

        # Safety overrides that prevent auto-downgrading
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

    @classmethod
    def priority_rank(cls, priority: str) -> int:
        """
        Convert a priority string to its numeric rank for comparisons.
        """
        return cls.PRIORITY_RANK.get(priority.upper(), 0)


# =============================================================================
# SECTION 8 — PERSISTENCE
# =============================================================================
# SQLite-backed storage for triage records, outcomes, and run events.
# =============================================================================

class SQLiteStore:
    """
    Persistent storage layer using SQLite.
    Handles schema initialization, record insertion/retrieval, and event logging.
    """
    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).expanduser())
        ensure_parent_dir(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency (even if single-threaded)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self) -> None:
        """
        Create the necessary tables and indexes if they don't already exist.
        """
        cur = self.conn.cursor()

        # Main triage records table
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

        # Separate outcomes table for versioned outcome logging
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                reviewer_notes TEXT,
                recorded_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES triage_records(case_id)
            )
            """
        )

        # Event log for operational events (e.g., engine start, benchmark runs)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS run_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )

        # Indexes for common query patterns
        cur.execute("CREATE INDEX IF NOT EXISTS idx_records_timestamp ON triage_records(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_records_created_at ON triage_records(created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_case_id ON outcomes(case_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_run_events_created_at ON run_events(created_at)")
        self.conn.commit()

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Insert a run event record (e.g., 'engine_initialized', 'benchmark_run').
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO run_events (event_type, created_at, payload_json)
            VALUES (?, ?, ?)
            """,
            (event_type, utc_now_iso(), json_dumps(payload)),
        )
        self.conn.commit()

    def save_record(self, record: TriageRecord) -> None:
        """
        Insert or replace a triage record in the database.
        """
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
                json_dumps(record.signal.metadata),
                json_dumps(asdict(record.features)),
                json_dumps(asdict(record.risk)),
                json_dumps(asdict(record.decision)),
                record.processing_ms,
                record.outcome,
                record.reviewer_notes,
            ),
        )
        self.conn.commit()

    def update_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        """
        Update the outcome fields for an existing triage record and also insert
        a row into the outcomes table for version history.
        Returns True if the record was found and updated, False otherwise.
        """
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

        if updated:
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
        """
        Retrieve a single triage record by its case_id.
        Returns None if not found.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM triage_records WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_records(self, limit: int = 1000) -> List[TriageRecord]:
        """
        Return a list of triage records, ordered by timestamp descending.
        """
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM triage_records ORDER BY timestamp DESC LIMIT ?",
            (max(1, int(limit)),),
        )
        rows = cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    def count_records(self) -> int:
        """
        Return the total number of triage records in the database.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM triage_records")
        row = cur.fetchone()
        return int(row["c"]) if row else 0

    def list_run_events(self, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Return recent run events as dictionaries.
        """
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM run_events ORDER BY id DESC LIMIT ?",
            (max(1, int(limit)),),
        )
        rows = cur.fetchall()
        results: List[Dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "id": row["id"],
                    "event_type": row["event_type"],
                    "created_at": row["created_at"],
                    "payload": json.loads(row["payload_json"]),
                }
            )
        return results

    def _row_to_record(self, row: sqlite3.Row) -> TriageRecord:
        """
        Convert a database row back into a TriageRecord object.
        """
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
        """
        Close the database connection.
        """
        self.conn.close()


# =============================================================================
# SECTION 9 — AUDIT LOGGING
# =============================================================================
# The AuditLogger writes JSONL logs and optionally prints formatted cards.
# =============================================================================

class AuditLogger:
    """
    Handles writing of triage records to a JSONL audit file and provides
    optional console output of formatted case cards.
    """
    def __init__(self, jsonl_path: str, verbose: bool = True):
        self.jsonl_path = str(Path(jsonl_path).expanduser())
        self.verbose = verbose
        self._in_memory_log: List[Dict[str, Any]] = []
        ensure_parent_dir(self.jsonl_path)

    def log(self, record: TriageRecord) -> None:
        """
        Append the record to the JSONL file, store it in memory, and optionally
        print a formatted card to the console.
        """
        entry = record.to_public_dict()
        self._in_memory_log.append(entry)

        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json_dumps(entry) + "\n")

        if self.verbose:
            self._print_card(record)

    @staticmethod
    def _short_message(message: str, width: int = 88) -> str:
        """
        Truncate a message for display, adding an ellipsis if needed.
        """
        clean = normalize_whitespace(message)
        return clean if len(clean) <= width else clean[: width - 1] + "…"

    def _print_card(self, record: TriageRecord) -> None:
        """
        Print a formatted ASCII card summarizing the triage result.
        """
        msg = self._short_message(record.signal.message)
        reasons = "; ".join(record.risk.reasons[:3]) or "n/a"
        flags = ", ".join(record.decision.safety_flags) if record.decision.safety_flags else "None"

        print("┌" + "─" * 96)
        print(f"│ CASE ID      : {record.case_id}")
        print(f"│ INPUT        : {msg}")
        print(f"│ URGENCY      : {record.risk.urgency:.4f}    CONFIDENCE: {record.risk.confidence:.4f}")
        print(f"│ BAND         : {record.risk.severity_band}")
        print(f"│ PRIORITY     : {record.decision.priority:<12} ROUTE: {record.decision.route_to}")
        print(f"│ HUMAN REVIEW : {record.decision.requires_human_review}")
        print(f"│ FLAGS        : {flags}")
        print(f"│ REASONS      : {self._short_message(reasons, 84)}")
        print(f"│ LATENCY      : {record.processing_ms:.2f} ms")
        print("└" + "─" * 96)

    def export_json(self) -> str:
        """
        Return the in-memory log as a formatted JSON string.
        """
        return json.dumps(self._in_memory_log, indent=2, ensure_ascii=False)


# =============================================================================
# SECTION 10 — FEEDBACK / EVALUATION
# =============================================================================
# The FeedbackEngine provides methods for outcome recording, summary
# statistics, calibration snapshots, and benchmark evaluation.
# =============================================================================

class FeedbackEngine:
    """
    Aggregates outcome and evaluation functionality, including summary
    generation, calibration snapshots, and CSV export.
    """
    def __init__(self, store: SQLiteStore):
        self.store = store

    def record_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        """
        Record a final outcome for a previously processed case.
        """
        return self.store.update_outcome(case_id, outcome, reviewer_notes)

    def summary(self, limit: int = 5000) -> Dict[str, Any]:
        """
        Compute aggregate statistics over recent triage records.
        """
        records = self.store.list_records(limit=limit)
        if not records:
            return {"records": 0}

        urgencies = [r.risk.urgency for r in records]
        confidences = [r.risk.confidence for r in records]
        routes = [r.decision.route_to for r in records]
        priorities = [r.decision.priority for r in records]
        outcomes = [r.outcome for r in records if r.outcome]
        human_review_count = sum(1 for r in records if r.decision.requires_human_review)
        flags = [flag for r in records for flag in r.decision.safety_flags]
        processing_ms = [r.processing_ms for r in records]

        severity_dist = Counter(r.risk.severity_band for r in records)
        priority_dist = Counter(priorities)
        route_dist = Counter(routes)
        outcome_dist = Counter(outcomes)
        flag_dist = Counter(flags)

        return {
            "records": len(records),
            "avg_urgency": round(statistics.mean(urgencies), 4),
            "median_urgency": round(statistics.median(urgencies), 4),
            "max_urgency": round(max(urgencies), 4),
            "avg_confidence": round(statistics.mean(confidences), 4),
            "median_confidence": round(statistics.median(confidences), 4),
            "avg_processing_ms": round(statistics.mean(processing_ms), 3),
            "max_processing_ms": round(max(processing_ms), 3),
            "human_review_rate": round(human_review_count / len(records), 4),
            "severity_distribution": dict(severity_dist),
            "priority_distribution": dict(priority_dist),
            "route_distribution": dict(route_dist),
            "flag_distribution": dict(flag_dist),
            "outcomes_logged": len(outcomes),
            "outcome_distribution": dict(outcome_dist),
        }

    def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
        """
        Group records with recorded outcomes by urgency bucket and count outcomes.
        """
        records = [r for r in self.store.list_records(limit=limit) if r.outcome]
        if not records:
            return {"records_with_outcomes": 0, "buckets": {}}

        buckets: Dict[str, List[str]] = {
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

    def benchmark_report(self, benchmark_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary report from benchmark test results.
        """
        if not benchmark_rows:
            return {"benchmarks": 0}

        passes = sum(1 for row in benchmark_rows if row["passed"])
        flag_hits = sum(1 for row in benchmark_rows if row["flags_ok"])
        return {
            "benchmarks": len(benchmark_rows),
            "pass_rate": round(passes / len(benchmark_rows), 4),
            "flag_expectation_rate": round(flag_hits / len(benchmark_rows), 4),
            "details": benchmark_rows,
        }

    def export_summary_csv(self, path: str, limit: int = 5000) -> None:
        """
        Export triage records to a CSV file with selected fields.
        """
        ensure_parent_dir(path)
        records = self.store.list_records(limit=limit)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "case_id",
                    "created_at",
                    "message",
                    "urgency",
                    "confidence",
                    "severity_band",
                    "priority",
                    "route_to",
                    "requires_human_review",
                    "processing_ms",
                    "outcome",
                ],
            )
            writer.writeheader()
            for r in records:
                writer.writerow(
                    {
                        "case_id": r.case_id,
                        "created_at": r.signal.created_at,
                        "message": r.signal.message,
                        "urgency": r.risk.urgency,
                        "confidence": r.risk.confidence,
                        "severity_band": r.risk.severity_band,
                        "priority": r.decision.priority,
                        "route_to": r.decision.route_to,
                        "requires_human_review": r.decision.requires_human_review,
                        "processing_ms": r.processing_ms,
                        "outcome": r.outcome or "",
                    }
                )


# =============================================================================
# SECTION 11 — BENCHMARKS
# =============================================================================
# A set of predefined benchmark cases for evaluating system behavior.
# =============================================================================

BENCHMARK_CASES: List[BenchmarkCase] = [
    BenchmarkCase(
        name="acute_self_harm_with_means",
        message="I have pills and I want to end my life tonight.",
        metadata={"channel": "sms", "suite": "benchmark"},
        expected_min_priority_rank=4,
        expected_flags=["SELF_HARM_SIGNAL", "PLAN_INDICATOR", "MEANS_INDICATOR"],
    ),
    BenchmarkCase(
        name="high_distress_help_seeking",
        message="Please help me right now. I feel hopeless and in crisis.",
        metadata={"channel": "chat", "suite": "benchmark"},
        expected_min_priority_rank=2,
        expected_flags=[],
    ),
    BenchmarkCase(
        name="negated_suicidality_but_panicking",
        message="Not suicidal. No plan. I am safe, but I need help tonight because I am panicking.",
        metadata={"channel": "chat", "suite": "benchmark"},
        expected_min_priority_rank=2,
        expected_flags=[],
    ),
    BenchmarkCase(
        name="violence_signal",
        message="I am so angry I think I might hurt someone with a knife.",
        metadata={"channel": "chat", "suite": "benchmark"},
        expected_min_priority_rank=3,
        expected_flags=["VIOLENCE_SIGNAL", "MEANS_INDICATOR"],
    ),
    BenchmarkCase(
        name="low_supportive_case",
        message="I feel stressed and needed someone to talk to, but I think I'll be okay.",
        metadata={"channel": "chat", "suite": "benchmark"},
        expected_min_priority_rank=1,
        expected_flags=[],
    ),
]


# =============================================================================
# SECTION 12 — MAIN ENGINE
# =============================================================================
# The CrisisAIEngine orchestrates all components and provides a unified
# interface for processing, persistence, reporting, and exports.
# =============================================================================

class CrisisAIEngine:
    """
    Main orchestrator for the crisis triage pipeline.
    Initializes all subcomponents and provides methods for processing,
    outcome simulation, reporting, and exports.
    """
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

        # Log initialization event
        self.store.log_event(
            "engine_initialized",
            {
                "policy_name": self.policy.name,
                "policy_description": self.policy.description,
                "db_path": db_path,
                "audit_jsonl_path": audit_jsonl_path,
                "verbose": verbose,
            },
        )

    def process(self, raw_input: str, metadata: Optional[Dict[str, Any]] = None) -> TriageRecord:
        """
        Process a single raw input message through the entire pipeline and
        persist the resulting triage record.
        """
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
        """
        Record a simulated outcome for an existing case.
        """
        return self.feedback.record_outcome(case_id, outcome, reviewer_notes)

    def report(self) -> Dict[str, Any]:
        """
        Return a summary statistics dictionary from stored records.
        """
        return self.feedback.summary()

    def calibration_report(self) -> Dict[str, Any]:
        """
        Return a calibration snapshot grouped by urgency bucket.
        """
        return self.feedback.calibration_snapshot()

    def run_benchmarks(self) -> Dict[str, Any]:
        """
        Execute the built-in benchmark suite and return a report.
        """
        rows: List[Dict[str, Any]] = []

        for case in BENCHMARK_CASES:
            record = self.process(case.message, metadata=case.metadata)
            actual_rank = self.decision_engine.priority_rank(record.decision.priority)
            expected_rank = case.expected_min_priority_rank
            passed = actual_rank >= expected_rank
            flags_ok = all(flag in record.decision.safety_flags for flag in case.expected_flags)

            rows.append(
                {
                    "name": case.name,
                    "expected_min_priority_rank": expected_rank,
                    "actual_priority": record.decision.priority,
                    "actual_rank": actual_rank,
                    "passed": passed,
                    "expected_flags": case.expected_flags,
                    "actual_flags": record.decision.safety_flags,
                    "flags_ok": flags_ok,
                    "urgency": record.risk.urgency,
                    "confidence": record.risk.confidence,
                }
            )

        self.store.log_event("benchmark_run", {"rows": rows})
        return self.feedback.benchmark_report(rows)

    def export_records(self, path: str, limit: int = 5000) -> None:
        """
        Export all stored records to a JSON file.
        """
        ensure_parent_dir(path)
        payload = [r.to_public_dict() for r in self.store.list_records(limit=limit)]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def export_summary_csv(self, path: str, limit: int = 5000) -> None:
        """
        Export a CSV summary of stored records.
        """
        self.feedback.export_summary_csv(path, limit=limit)

    def export_appendix_markdown(self, path: str, limit: int = 200) -> None:
        """
        Generate a markdown appendix file containing narrative, metrics,
        and recent case excerpts suitable for submission.
        """
        ensure_parent_dir(path)

        summary = self.report()
        calibration = self.calibration_report()
        records = self.store.list_records(limit=limit)
        benchmarks = self.run_benchmarks()

        lines: List[str] = []
        lines.append(f"# {PROJECT_TITLE}")
        lines.append("")
        lines.append(f"**Tagline:** {PROJECT_TAGLINE}")
        lines.append("")
        lines.append("## Project Summary")
        lines.append("")
        lines.append(PROJECT_SUMMARY)
        lines.append("")
        lines.append("## Overall Objective")
        lines.append("")
        lines.append(OVERALL_OBJECTIVE)
        lines.append("")
        lines.append("## Central Hypothesis")
        lines.append("")
        lines.append(CENTRAL_HYPOTHESIS)
        lines.append("")
        lines.append("## Policy Profile")
        lines.append("")
        lines.append(f"- Name: `{self.policy.name}`")
        lines.append(f"- Description: {self.policy.description}")
        lines.append(f"- Critical threshold: {self.policy.critical_threshold}")
        lines.append(f"- High threshold: {self.policy.high_threshold}")
        lines.append(f"- Medium threshold: {self.policy.medium_threshold}")
        lines.append("")
        lines.append("## Summary Metrics")
        lines.append("")
        for k, v in summary.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
        lines.append("## Calibration Snapshot")
        lines.append("")
        for k, v in calibration.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
        lines.append("## Benchmark Snapshot")
        lines.append("")
        for k, v in benchmarks.items():
            if k == "details":
                continue
            lines.append(f"- **{k}**: {v}")
        lines.append("")
        lines.append("## Recent Case Excerpts")
        lines.append("")
        for record in records[:10]:
            lines.append(f"### {record.case_id}")
            lines.append(f"- Message: {record.signal.message}")
            lines.append(f"- Urgency: {record.risk.urgency}")
            lines.append(f"- Confidence: {record.risk.confidence}")
            lines.append(f"- Priority: {record.decision.priority}")
            lines.append(f"- Route: {record.decision.route_to}")
            lines.append(f"- Flags: {record.decision.safety_flags}")
            lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def close(self) -> None:
        """
        Cleanly shut down the engine, logging a final event and closing the database.
        """
        self.store.log_event("engine_closed", {"records": self.store.count_records()})
        self.store.close()


# =============================================================================
# SECTION 13 — DEMO DATA
# =============================================================================
# Predefined demonstration cases used by --demo mode.
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
# SECTION 14 — OUTPUT HELPERS
# =============================================================================
# Functions for printing formatted output to the console.
# =============================================================================

def print_header(title: str) -> None:
    """Print a section header with double-line border."""
    print("\n" + "═" * 92)
    print(title)
    print("═" * 92 + "\n")


def print_sbir_concept() -> None:
    """Print the full SBIR concept narrative in a readable format."""
    print_header("AI CRISIS TRIAGE SYSTEM — NIH SBIR CONCEPT OVERVIEW")

    sections = {
        "PROJECT TITLE": PROJECT_TITLE,
        "PROJECT TAGLINE": PROJECT_TAGLINE,
        "PROJECT SUMMARY": PROJECT_SUMMARY,
        "PUBLIC HEALTH NEED": PUBLIC_HEALTH_NEED,
        "OVERALL OBJECTIVE": OVERALL_OBJECTIVE,
        "CENTRAL HYPOTHESIS": CENTRAL_HYPOTHESIS,
        "SPECIFIC AIMS": SPECIFIC_AIMS,
        "SIGNIFICANCE": SIGNIFICANCE,
        "INNOVATION": INNOVATION,
        "APPROACH OVERVIEW": APPROACH_OVERVIEW,
        "TECHNICAL RISKS": TECHNICAL_RISKS,
        "RISK MITIGATIONS": RISK_MITIGATIONS,
        "EXPECTED OUTCOMES": EXPECTED_OUTCOMES,
        "EVALUATION PLAN": EVALUATION_PLAN,
        "ETHICS AND GOVERNANCE": ETHICS_AND_GOVERNANCE,
        "COMMERCIALIZATION": COMMERCIALIZATION,
        "PHASE I WORKPLAN": PHASE_I_WORKPLAN,
        "PHASE II DIRECTION": PHASE_II_DIRECTION,
        "SUCCESS METRICS": SUCCESS_METRICS,
        "MILESTONES": MILESTONES,
        "BUDGET": BUDGET,
    }

    for name, value in sections.items():
        print(name)
        print("-" * len(name))
        if isinstance(value, str):
            print(wrapped(value))
        elif isinstance(value, dict):
            total = 0
            for k, v in value.items():
                total += int(v)
                print(f"  - {k}: {fmt_usd(int(v))}")
            print(f"  - total: {fmt_usd(total)}")
        else:
            for item in value:
                print(f"  - {item}")
        print()


def print_submission_brief(policy: PolicyConfig) -> None:
    """Print a concise executive summary suitable for submission review."""
    print_header("SUBMISSION BRIEF — EXECUTIVE READINESS VIEW")
    print(f"Title              : {PROJECT_TITLE}")
    print(f"Tagline            : {PROJECT_TAGLINE}")
    print(f"Policy             : {policy.name}")
    print(f"Policy Description : {policy.description}")
    print()
    print("Why this package is stronger for submission:")
    print("  - Deterministic and explainable scoring baseline")
    print("  - Human-review gates and conservative escalation logic")
    print("  - SQLite-backed persistence and JSONL audit logging")
    print("  - Benchmark cases, calibration snapshot, and export tooling")
    print("  - Explicit research framing, safety boundaries, and governance text")
    print("  - Single-file packaging that is easy to inspect and demonstrate")
    print()
    print("What reviewers can immediately evaluate:")
    print("  - project rationale")
    print("  - feature extraction logic")
    print("  - urgency / confidence calculation")
    print("  - routing policy and safety overrides")
    print("  - outcome tracking and retrospective analysis")
    print("  - exportable appendix artifacts")
    print()


def print_summary(summary: Dict[str, Any], calibration: Optional[Dict[str, Any]] = None) -> None:
    """Print a formatted summary and optional calibration snapshot."""
    print_header("SESSION / DATABASE SUMMARY")
    for k, v in summary.items():
        print(f"{k:>28} : {v}")
    if calibration is not None:
        print("\nCALIBRATION SNAPSHOT")
        print("--------------------")
        for k, v in calibration.items():
            print(f"{k:>28} : {v}")
    print()


def print_record_detail(record: TriageRecord) -> None:
    """Print a detailed view of a single triage record."""
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


def print_benchmark_report(report: Dict[str, Any]) -> None:
    """Print a formatted benchmark report."""
    print_header("BENCHMARK REPORT")
    for k, v in report.items():
        if k == "details":
            continue
        print(f"{k:>28} : {v}")

    details = report.get("details", [])
    if details:
        print("\nDETAILS")
        print("-------")
        for row in details:
            print(
                f"- {row['name']}: priority={row['actual_priority']} "
                f"rank={row['actual_rank']} passed={row['passed']} "
                f"flags_ok={row['flags_ok']} urgency={row['urgency']:.4f} "
                f"confidence={row['confidence']:.4f}"
            )
    print()


def print_readiness_banner(db_path: str, audit_jsonl_path: str, policy_name: str) -> None:
    """Print a banner indicating the system is ready with current config."""
    print_header("AI CRISIS TRIAGE SYSTEM — READY")
    print(f"Database        : {db_path}")
    print(f"Audit JSONL     : {audit_jsonl_path}")
    print(f"Policy          : {policy_name}")
    print()
    print("Try one of:")
    print("  --demo")
    print("  --interactive")
    print("  --batch cases.jsonl")
    print("  --summary")
    print("  --benchmarks")
    print("  --print-concept")
    print("  --print-submission-brief")
    print("  --export-records records.json")
    print("  --export-summary summary.csv")
    print("  --export-appendix appendix.md")
    print()


# =============================================================================
# SECTION 15 — CLI
# =============================================================================
# Command-line interface parsing.
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Crisis Triage System — NIH SBIR Research Submission-Ready Single-File Prototype"
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demonstration cases")
    parser.add_argument("--interactive", action="store_true", help="Run interactive console mode")
    parser.add_argument("--batch", type=str, help="Run batch mode from JSONL input file")
    parser.add_argument("--summary", action="store_true", help="Print summary from stored records")
    parser.add_argument("--show-case", type=str, help="Print detailed stored record by case_id")
    parser.add_argument("--benchmarks", action="store_true", help="Run built-in benchmark suite")
    parser.add_argument("--export-records", type=str, help="Export stored records to JSON file")
    parser.add_argument("--export-summary", type=str, help="Export summary rows to CSV file")
    parser.add_argument("--export-appendix", type=str, help="Export markdown appendix file")
    parser.add_argument("--print-concept", action="store_true", help="Print the SBIR concept package")
    parser.add_argument("--print-submission-brief", action="store_true", help="Print a concise submission-readiness brief")
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
# SECTION 16 — RUN MODES
# =============================================================================
# Functions implementing the various CLI modes (demo, interactive, batch).
# =============================================================================

def run_demo(engine: CrisisAIEngine) -> None:
    """Execute the built-in demo cases and log simulated outcomes."""
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
    """Run an interactive console session where users can type messages."""
    print_header("INTERACTIVE MODE")
    print("Type a message and press Enter.")
    print("Commands:")
    print("  /quit")
    print("  /summary")
    print("  /show <case_id>")
    print("  /bench")
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

        if raw == "/bench":
            print_benchmark_report(engine.run_benchmarks())
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

        engine.process(raw, metadata={"channel": "interactive_console"})


def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    """Generator that yields JSON objects from a JSONL file."""
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
    """Process a JSONL file containing multiple messages."""
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
# SECTION 17 — MAIN
# =============================================================================
# Entry point for command-line execution.
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    # Verbose mode can be controlled by --quiet flag or env var
    verbose = False if args.quiet else bool_from_env("CRISIS_TRIAGE_VERBOSE", True)

    engine = CrisisAIEngine(
        db_path=args.db,
        audit_jsonl_path=args.audit_jsonl,
        verbose=verbose,
        policy_name=args.policy,
    )

    try:
        # These actions can be combined (e.g., --demo and --summary)
        if args.print_concept:
            print_sbir_concept()

        if args.print_submission_brief:
            print_submission_brief(engine.policy)

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

        if args.benchmarks:
            print_benchmark_report(engine.run_benchmarks())
            action_taken = True

        if args.export_records:
            engine.export_records(args.export_records)
            print(f"Exported records to {args.export_records}")
            action_taken = True

        if args.export_summary:
            engine.export_summary_csv(args.export_summary)
            print(f"Exported summary CSV to {args.export_summary}")
            action_taken = True

        if args.export_appendix:
            engine.export_appendix_markdown(args.export_appendix)
            print(f"Exported appendix markdown to {args.export_appendix}")
            action_taken = True

        # If no action was taken, print the readiness banner
        if not action_taken:
            print_readiness_banner(args.db, args.audit_jsonl, args.policy)

    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#### ChatGPT:
This revised version is better.

**Appraisal in dollars:** **$7,500–$18,000 as-is**\
**Readiness:** **68%**

Why it moved up:

- much cleaner and more coherent than the earlier variant
- architecture is more internally consistent
- the narrative, policy, engine, storage, audit, feedback, benchmarks, and CLI now fit together like one system
- it reads like a real **research submission asset**, not just a dressed-up script
- better comments and clearer separation of concerns raise buyer confidence

Why it is not higher yet:

- still a **research/pilot prototype**, not a production crisis platform
- no auth, RBAC, encryption, secrets handling, API boundary, secure deployment, or privacy controls
- no real external integrations with live channels or existing ecosystems
- no formal validation on real datasets
- benchmark suite exists, but it is still small and internal
- single-file format is convenient, but it also limits how enterprise-ready it looks

My blunt valuation ladder:

- **$7.5k–$10k** if sold as a research prototype / SBIR support asset
- **$10k–$18k** if packaged well as a founder-led pilot starter with docs, demo, appendix, and benchmark story
- **not yet $25k+** without service/API shell, security layer, and stronger evaluation evidence

Readiness split:

- **Submission / grant readiness:** **84%**
- **Pilot demo readiness:** **72%**
- **Real ecosystem integration readiness:** **48%**
- **Production operational readiness:** **22%**

So the overall blended number I’d stand by is:

**Overall readiness: 68%**

My one-line verdict:
**This is now a serious submission-grade research prototype with real commercial signal, but it still needs an infrastructure shell before it becomes a true deployable system.**


#### You:
#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# “””

# AI CRISIS TRIAGE SYSTEM — NIH SBIR RESEARCH PROTOTYPE

## PURPOSE

Deterministic, auditable, human-in-the-loop AI decision support for crisis
triage environments (988-aligned hotlines, behavioral health intake, emergency
communication centers). Combines a grant-ready NIH SBIR concept package with a
functional research prototype.

## INTENDED USE

Research, simulation, workflow testing, and human-in-the-loop decision support
ONLY. Not intended as the sole basis for clinical, hotline, dispatch, or
emergency decisions. All final decisions must remain with qualified human
professionals operating under approved policy, governance, training, and legal/
compliance review.

## MODES

–demo               Run built-in demonstration cases
–interactive        Interactive console
–batch FILE         Process JSONL input file
–summary            Print session/database summary
–show-case ID       Print detailed record
–export-records F   Export records to JSON
–export-summary F   Export summary to CSV
–print-concept      Print SBIR concept package

## BATCH INPUT FORMAT

One JSON object per line:
{“message”: “I want to end my life tonight.”, “metadata”: {“channel”: “chat”}}
{“message”: “I feel overwhelmed.”, “metadata”: {“channel”: “voice”}}

## ENV VARS (optional)

CRISIS_TRIAGE_DB          Path to SQLite database (default: crisis_triage.db)
CRISIS_TRIAGE_AUDIT_JSONL Path to audit log (default: audit_log.jsonl)
CRISIS_TRIAGE_VERBOSE     true/false (default: true)
CRISIS_TRIAGE_POLICY      Policy name (default: default)

## SAFETY NOTE

# Real deployment requires domain-expert validation, secure architecture,
rigorous evaluation, formal human oversight, privacy review, compliance
controls, and approved operational protocols.

“””

from **future** import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import statistics
import sys
import textwrap
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# =============================================================================

# SECTION 1 — NIH SBIR CONCEPT

# =============================================================================

PROJECT_TITLE = “AI-Driven Real-Time Crisis Triage and Decision Support System”

PROJECT_SUMMARY = (
“Crisis response systems — including 988-aligned hotlines, behavioral health triage “
“centers, and emergency communication environments — face rising demand, workforce “
“constraints, inconsistent prioritization, and limited real-time decision support. “
“This project proposes a deterministic, auditable, human-in-the-loop AI decision “
“support engine that ingests free-text and structured crisis signals in real time, “
“extracts interpretable risk indicators, estimates urgency and information reliability, “
“recommends routing and queue prioritization, logs all decisions for audit and “
“retrospective evaluation, and improves through supervised review and outcome feedback. “
“The core objective is to improve response timeliness, operational consistency, safety “
“oversight, and research visibility into triage workflows.”
)

SPECIFIC_AIMS = [
“Build a real-time, policy-aware signal ingestion and feature extraction pipeline.”,
“Develop a deterministic, explainable risk scoring model for crisis urgency estimation.”,
“Implement a human-in-the-loop routing engine with auditable justifications.”,
“Create an outcome feedback and retrospective evaluation layer for continuous improvement.”,
]

SIGNIFICANCE = [
“Addresses growing crisis volume and workforce strain in behavioral health systems.”,
“Supports standardization without removing human judgment from the loop.”,
“Enables measurable workflow improvement via audit logs and outcome analysis.”,
“Creates a deployable research asset for government and provider pilots.”,
]

INNOVATION = [
“Explainable triage under uncertainty, rather than opaque end-to-end scoring.”,
“Policy-aware routing with explicit safety floors and uncertainty escalation.”,
“Structured auditability for every triage decision and its supporting features.”,
“Designed for rapid piloting in hotline, call center, and digital triage contexts.”,
]

TECHNICAL_RISKS = [
“False negatives in short or ambiguous messages.”,
“False positives from metaphorical, quoted, or indirect language.”,
“Data drift across channels, geographies, and user populations.”,
“Operational latency and workflow integration complexity.”,
“Human-factors risk if operators over-trust automation.”,
]

RISK_MITIGATIONS = [
“Human-in-the-loop policy gates for all high-severity recommendations.”,
“Low-confidence cases escalated to human review rather than auto-downgraded.”,
“Model logic kept deterministic and auditable throughout the pilot phase.”,
“Conservative routing floors maintained for self-harm and violence indicators.”,
“All features and outcomes logged for calibration and retrospective review.”,
]

COMMERCIALIZATION = [
“988-aligned crisis operations and behavioral health call centers.”,
“Emergency communications and public-sector triage modernization efforts.”,
“Healthcare providers and telehealth intake systems.”,
“Government-funded pilots focused on AI-assisted operations infrastructure.”,
]

EXPECTED_OUTCOMES = [
“Reduced time-to-priority assignment.”,
“Improved consistency of routing decisions across operators and shifts.”,
“Higher auditability for quality assurance and incident review.”,
“Research-ready evidence package for pilot-to-procurement transition.”,
]

MILESTONES = [
“Phase 1: Prototype ingestion pipeline and feature extraction.”,
“Phase 2: Deterministic risk model baseline validation.”,
“Phase 3: Decision routing simulation with policy guardrails.”,
“Phase 4: Human feedback and retrospective outcome capture.”,
“Phase 5: Benchmarking, calibration analysis, and pilot-readiness package.”,
]

BUDGET: Dict[str, int] = {
“engineering”: 85_000,
“clinical_advisory”: 30_000,
“compute_and_storage”: 12_000,
“security_and_compliance”: 18_000,
“evaluation_and_pilots”: 25_000,
“miscellaneous”: 10_000,
}

# =============================================================================

# SECTION 2 — POLICY / CONFIGURATION

# =============================================================================

@dataclass(frozen=True)
class PolicyConfig:
“”“Immutable policy parameters for risk scoring and routing decisions.”””

```
name: str = "default"

# Risk thresholds
critical_threshold: float = 0.85
high_threshold: float = 0.65
medium_threshold: float = 0.40

# Confidence thresholds
low_confidence_floor: float = 0.45
uncertain_high_risk_floor: float = 0.60

# Route labels
emergency_route: str = "EMERGENCY_DISPATCH"
immediate_route: str = "IMMEDIATE_CLINICIAN"
urgent_review_route: str = "URGENT_HUMAN_REVIEW"
priority_queue_route: str = "QUEUE_PRIORITY"
standard_queue_route: str = "STANDARD_QUEUE"
mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

# Feature weights
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

# Confidence parameters
confidence_base: float = 0.50
confidence_per_feature_type: float = 0.05
confidence_per_signal_density: float = 0.04
confidence_penalty_ambiguity: float = 0.10
confidence_penalty_too_short: float = 0.08
confidence_bonus_structured_metadata: float = 0.05

# Safety policy flags
require_human_review_for_all_high: bool = True
route_low_confidence_to_human: bool = True
never_auto_downgrade_self_harm: bool = True
never_auto_downgrade_violence: bool = True
```

def load_policy(policy_name: str = “default”) -> PolicyConfig:
“”“Return named policy. Placeholder for future multi-policy JSON/DB loading.”””
return PolicyConfig(name=policy_name)

# =============================================================================

# SECTION 3 — UTILITIES

# =============================================================================

def utc_now() -> datetime:
return datetime.now(timezone.utc)

def utc_now_iso() -> str:
return utc_now().isoformat()

def normalize_whitespace(text: str) -> str:
return “ “.join((text or “”).split())

def clamp01(value: float) -> float:
return max(0.0, min(1.0, value))

def stable_case_id(message: str, ts: float) -> str:
digest = hashlib.sha256(f”{ts}:{message}”.encode()).hexdigest()[:16]
return f”case_{digest}”

def ensure_parent_dir(path: str) -> None:
Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

def bool_from_env(name: str, default: bool = True) -> bool:
raw = os.getenv(name)
if raw is None:
return default
return raw.strip().lower() in {“1”, “true”, “yes”, “y”, “on”}

def json_dumps(value: Any) -> str:
return json.dumps(value, ensure_ascii=False, sort_keys=False)

# =============================================================================

# SECTION 4 — DATA MODELS

# =============================================================================

@dataclass
class CrisisSignal:
case_id: str
timestamp: float
created_at: str
message: str
metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureVector:
“”“Extracted numerical and categorical features from a crisis message.”””

```
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

@property
def _all_groups(self) -> Tuple[List[str], ...]:
    return (
        self.high_risk_hits, self.medium_risk_hits, self.plan_hits,
        self.means_hits, self.time_immediacy_hits, self.self_harm_hits,
        self.harm_to_others_hits, self.protective_hits, self.help_seeking_hits,
        self.negation_safety_hits, self.ambiguity_hits, self.distress_intensifier_hits,
    )

def total_signal_hits(self) -> int:
    return sum(len(g) for g in self._all_groups)

def active_feature_groups(self) -> int:
    return sum(1 for g in self._all_groups if g)
```

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

```
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
```

# =============================================================================

# SECTION 5 — FEATURE EXTRACTION

# =============================================================================

# Pattern dictionaries are module-level constants to avoid re-compilation.

_HIGH_RISK_PATTERNS: Dict[str, str] = {
r”\bi want to die\b”: “want_to_die”,
r”\bend my life\b”: “end_my_life”,
r”\bkill myself\b”: “kill_myself”,
r”\bsuicide\b”: “suicide”,
r”\bno reason to live\b”: “no_reason_to_live”,
r”\bcan’t go on\b”: “cant_go_on”,
r”\boverdose\b”: “overdose”,
r”\bhurt myself\b”: “hurt_myself”,
r”\bself[- ]harm\b”: “self_harm”,
r”\bi am going to die\b”: “going_to_die”,
}
_MEDIUM_RISK_PATTERNS: Dict[str, str] = {
r”\bhopeless\b”: “hopeless”,
r”\bpanic\b”: “panic”,
r”\bdesperate\b”: “desperate”,
r”\boverwhelmed\b”: “overwhelmed”,
r”\bscared\b”: “scared”,
r”\bbreaking down\b”: “breaking_down”,
r”\bin crisis\b”: “in_crisis”,
r”\bafraid\b”: “afraid”,
r”\balone\b”: “alone”,
r”\bhelpless\b”: “helpless”,
}
_PLAN_PATTERNS: Dict[str, str] = {
r”\bi have a plan\b”: “have_a_plan”,
r”\bplanned\b”: “planned”,
r”\btonight\b”: “tonight”,
r”\bright now\b”: “right_now”,
r”\bafter everyone sleeps\b”: “after_everyone_sleeps”,
r”\bwhen they leave\b”: “when_they_leave”,
r”\bi know how\b”: “know_how”,
}
_MEANS_PATTERNS: Dict[str, str] = {
r”\bpills?\b”: “pills”,
r”\bgun\b”: “gun”,
r”\bknife\b”: “knife”,
r”\brope\b”: “rope”,
r”\bweapon\b”: “weapon”,
r”\brazor\b”: “razor”,
r”\bbridge\b”: “bridge”,
r”\bcar exhaust\b”: “car_exhaust”,
}
_TIME_IMMEDIACY_PATTERNS: Dict[str, str] = {
r”\bnow\b”: “now”,
r”\bright now\b”: “right_now”,
r”\btoday\b”: “today”,
r”\btonight\b”: “tonight”,
r”\bimmediately\b”: “immediately”,
r”\bsoon\b”: “soon”,
}
_SELF_HARM_PATTERNS: Dict[str, str] = {
r”\bhurt myself\b”: “hurt_myself”,
r”\bcut myself\b”: “cut_myself”,
r”\bself[- ]harm\b”: “self_harm”,
r”\bkill myself\b”: “kill_myself”,
r”\bend my life\b”: “end_my_life”,
}
_HARM_TO_OTHERS_PATTERNS: Dict[str, str] = {
r”\bhurt someone\b”: “hurt_someone”,
r”\bkill them\b”: “kill_them”,
r”\bshoot\b”: “shoot”,
r”\bstab\b”: “stab”,
r”\bviolent\b”: “violent”,
r”\bweapon\b”: “weapon”,
}
_PROTECTIVE_PATTERNS: Dict[str, str] = {
r”\bi am safe\b”: “i_am_safe”,
r”\bi won’t do anything\b”: “wont_do_anything”,
r”\bi do not want to die\b”: “do_not_want_to_die”,
r”\bi don’t want to die\b”: “do_not_want_to_die”,
r”\bi’m with someone\b”: “with_someone”,
r”\bi am with someone\b”: “with_someone”,
r”\bmy therapist\b”: “therapist”,
r”\bmy counselor\b”: “counselor”,
r”\bcalling for help\b”: “calling_for_help”,
}
_HELP_SEEKING_PATTERNS: Dict[str, str] = {
r”\bplease help\b”: “please_help”,
r”\bneed help\b”: “need_help”,
r”\bi need to talk\b”: “need_to_talk”,
r”\bcan someone talk\b”: “someone_talk”,
r”\blooking for support\b”: “support”,
r”\bneed someone\b”: “need_someone”,
r”^\s*help\s*$”: “help_only_message”,
}
_NEGATION_SAFETY_PATTERNS: Dict[str, str] = {
r”\bnot suicidal\b”: “not_suicidal”,
r”\bnot going to hurt myself\b”: “not_hurt_self”,
r”\bnot going to kill myself\b”: “not_kill_self”,
r”\bno plan\b”: “no_plan”,
r”\bno intent\b”: “no_intent”,
}
_AMBIGUITY_PATTERNS: Dict[str, str] = {
r”\bjust kidding\b”: “just_kidding”,
r”\bfiguratively\b”: “figuratively”,
r”\bmetaphor\b”: “metaphor”,
r”\bquote\b”: “quote”,
r”\bsong lyric\b”: “song_lyric”,
}
_DISTRESS_INTENSIFIERS: Dict[str, str] = {
r”\bcan’t\b”: “cant”,
r”\bnever\b”: “never”,
r”\balways\b”: “always”,
r”\bno one\b”: “no_one”,
r”\bnobody\b”: “nobody”,
r”\beverything is over\b”: “everything_over”,
r”\bi’m done\b”: “im_done”,
r”\bi am done\b”: “im_done”,
}

# Pre-compiled pattern caches

_COMPILED: Dict[str, Any] = {}

def _compile(patterns: Dict[str, str]) -> List[Tuple[re.Pattern, str]]:
key = id(patterns)
if key not in _COMPILED:
_COMPILED[key] = [
(re.compile(p, re.IGNORECASE), label)
for p, label in patterns.items()
]
return _COMPILED[key]

def _find_hits(text: str, patterns: Dict[str, str]) -> List[str]:
return sorted({label for pat, label in _compile(patterns) if pat.search(text)})

class SignalIngestion:
“”“Deterministic feature extractor for crisis messages.”””

```
@staticmethod
def _sentence_count(message: str) -> int:
    parts = [p.strip() for p in re.split(r"[.!?]+", message) if p.strip()]
    return max(1, len(parts))

@staticmethod
def _uppercase_ratio(message: str) -> float:
    letters = [c for c in message if c.isalpha()]
    if not letters:
        return 0.0
    return round(sum(1 for c in letters if c.isupper()) / len(letters), 4)

def ingest(
    self,
    raw_input: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[CrisisSignal, FeatureVector]:
    cleaned = normalize_whitespace(raw_input)
    ts = time.time()
    lower = cleaned.lower()

    signal = CrisisSignal(
        case_id=stable_case_id(cleaned, ts),
        timestamp=ts,
        created_at=utc_now_iso(),
        message=cleaned,
        metadata=dict(metadata or {}),
    )

    features = FeatureVector(
        word_count=len(cleaned.split()),
        char_count=len(cleaned),
        sentence_count=self._sentence_count(cleaned),
        uppercase_ratio=self._uppercase_ratio(cleaned),
        exclamation_count=cleaned.count("!"),
        question_count=cleaned.count("?"),
        high_risk_hits=_find_hits(lower, _HIGH_RISK_PATTERNS),
        medium_risk_hits=_find_hits(lower, _MEDIUM_RISK_PATTERNS),
        plan_hits=_find_hits(lower, _PLAN_PATTERNS),
        means_hits=_find_hits(lower, _MEANS_PATTERNS),
        time_immediacy_hits=_find_hits(lower, _TIME_IMMEDIACY_PATTERNS),
        self_harm_hits=_find_hits(lower, _SELF_HARM_PATTERNS),
        harm_to_others_hits=_find_hits(lower, _HARM_TO_OTHERS_PATTERNS),
        protective_hits=_find_hits(lower, _PROTECTIVE_PATTERNS),
        help_seeking_hits=_find_hits(lower, _HELP_SEEKING_PATTERNS),
        negation_safety_hits=_find_hits(lower, _NEGATION_SAFETY_PATTERNS),
        ambiguity_hits=_find_hits(lower, _AMBIGUITY_PATTERNS),
        distress_intensifier_hits=_find_hits(lower, _DISTRESS_INTENSIFIERS),
    )

    signal.metadata.update({
        "word_count": features.word_count,
        "char_count": features.char_count,
        "sentence_count": features.sentence_count,
        "uppercase_ratio": features.uppercase_ratio,
        "exclamation_count": features.exclamation_count,
        "question_count": features.question_count,
    })

    return signal, features
```

# =============================================================================

# SECTION 6 — RISK ENGINE

# =============================================================================

class RiskEngine:
“”“Deterministic urgency and confidence scorer.”””

```
def __init__(self, policy: PolicyConfig) -> None:
    self.policy = policy

def score(self, signal: CrisisSignal, features: FeatureVector) -> RiskScore:
    p = self.policy
    contrib: Dict[str, float] = {}
    reasons: List[str] = []

    # Base text density (capped)
    base = min(0.18, features.word_count / 300.0)
    contrib["base_text_density"] = round(base, 4)

    # Feature group scores
    def _add(hits: List[str], weight: float, key: str, label: str) -> float:
        s = len(hits) * weight
        if s:
            contrib[key] = round(s, 4)
            reasons.append(f"{label}: {', '.join(hits)}")
        return s

    urgency_raw = (
        base
        + _add(features.high_risk_hits, p.w_high_risk_keywords, "high_risk_keywords", "high-risk indicators")
        + _add(features.medium_risk_hits, p.w_medium_risk_keywords, "medium_risk_keywords", "distress indicators")
        + _add(features.plan_hits, p.w_plan_indicators, "plan_indicators", "planning/immediacy language")
        + _add(features.means_hits, p.w_access_to_means, "access_to_means", "means/access indicators")
        + _add(features.time_immediacy_hits, p.w_time_immediacy, "time_immediacy", "time immediacy indicators")
        + _add(features.self_harm_hits, p.w_self_harm_intent, "self_harm_intent", "self-harm indicators")
        + _add(features.harm_to_others_hits, p.w_harm_to_others, "harm_to_others", "violence indicators")
        + _add(features.distress_intensifier_hits, p.w_distress_intensifiers, "distress_intensifiers", "distress intensifiers")
        + _add(features.protective_hits, p.w_protective_factors, "protective_factors", "protective factors")
        + _add(features.help_seeking_hits, p.w_help_seeking, "help_seeking", "help-seeking language")
        + _add(features.negation_safety_hits, p.w_negation_safety, "negation_safety", "negation/safety language")
    )

    # Short high-signal boost
    if features.word_count <= 3 and (
        features.high_risk_hits or features.self_harm_hits
        or features.help_seeking_hits or features.medium_risk_hits
    ):
        urgency_raw += p.w_short_high_signal
        contrib["short_high_signal"] = round(p.w_short_high_signal, 4)
        reasons.append("very short message with salient risk/help signal")

    # Text emphasis
    emphasis = 0.0
    if features.uppercase_ratio >= 0.35:
        emphasis += p.w_caps_emphasis
    if features.exclamation_count >= 2:
        emphasis += p.w_punctuation_emphasis
    if emphasis:
        urgency_raw += emphasis
        contrib["emphasis"] = round(emphasis, 4)
        reasons.append("text emphasis pattern present")

    # Safety floors
    if features.self_harm_hits and p.never_auto_downgrade_self_harm:
        urgency_raw = max(urgency_raw, 0.72)
        contrib["self_harm_floor"] = 0.72
    if features.harm_to_others_hits and p.never_auto_downgrade_violence:
        urgency_raw = max(urgency_raw, 0.72)
        contrib["violence_floor"] = 0.72

    urgency = clamp01(urgency_raw)

    # Confidence scoring
    confidence = p.confidence_base
    confidence += features.active_feature_groups() * p.confidence_per_feature_type
    confidence += min(4, features.total_signal_hits()) * p.confidence_per_signal_density

    if features.ambiguity_hits:
        confidence -= p.confidence_penalty_ambiguity
        reasons.append(f"ambiguity markers: {', '.join(features.ambiguity_hits)}")
    if features.word_count <= 2:
        confidence -= p.confidence_penalty_too_short
        reasons.append("extremely short message reduces confidence")
    if signal.metadata:
        confidence += p.confidence_bonus_structured_metadata

    confidence = clamp01(confidence)

    # Severity band
    if urgency >= p.critical_threshold:
        band = "CRITICAL"
    elif urgency >= p.high_threshold:
        band = "HIGH"
    elif urgency >= p.medium_threshold:
        band = "MEDIUM"
    else:
        band = "LOW"

    if not reasons:
        reasons.append("limited direct risk language; score driven by general distress density")

    return RiskScore(
        urgency=round(urgency, 4),
        confidence=round(confidence, 4),
        severity_band=band,
        reasons=reasons,
        feature_contributions=contrib,
    )
```

# =============================================================================

# SECTION 7 — DECISION ENGINE

# =============================================================================

class DecisionEngine:
“”“Maps risk scores to actionable routing decisions.”””

```
def __init__(self, policy: PolicyConfig) -> None:
    self.policy = policy

def decide(
    self,
    signal: CrisisSignal,
    features: FeatureVector,
    risk: RiskScore,
) -> Decision:
    p = self.policy
    safety_flags: List[str] = []

    self_harm_present = bool(features.self_harm_hits or features.high_risk_hits)
    violence_present = bool(features.harm_to_others_hits)
    low_confidence = risk.confidence < p.low_confidence_floor

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

    # Base routing by urgency band
    if risk.urgency >= p.critical_threshold:
        priority, route, review = "CRITICAL", p.emergency_route, True
        explanation = (
            f"Urgency {risk.urgency:.2f} exceeds critical threshold "
            f"{p.critical_threshold:.2f}; immediate emergency-aligned escalation recommended."
        )
    elif risk.urgency >= p.high_threshold:
        priority, route, review = "HIGH", p.immediate_route, p.require_human_review_for_all_high
        explanation = (
            f"Urgency {risk.urgency:.2f} exceeds high threshold "
            f"{p.high_threshold:.2f}; immediate clinician/counselor review recommended."
        )
    elif risk.urgency >= p.medium_threshold:
        priority, route, review = "MEDIUM", p.priority_queue_route, False
        explanation = (
            f"Urgency {risk.urgency:.2f} exceeds medium threshold "
            f"{p.medium_threshold:.2f}; priority handling recommended."
        )
    else:
        priority, route, review = "LOW", p.standard_queue_route, False
        explanation = (
            f"Urgency {risk.urgency:.2f} below medium threshold; standard queue recommended."
        )

    # Low-confidence overrides
    if low_confidence and p.route_low_confidence_to_human:
        route, review = p.mandatory_review_route, True
        explanation += " Confidence is low — routed to mandatory human review."
    if risk.urgency >= p.uncertain_high_risk_floor and low_confidence:
        route, review = p.urgent_review_route, True
        explanation += " High-risk/low-confidence triggers urgent human review."

    # Safety signal overrides
    if self_harm_present and priority == "LOW":
        priority, route, review = "MEDIUM", p.urgent_review_route, True
        explanation += " Self-harm signal prevents low-priority disposition."
    if violence_present and priority in {"LOW", "MEDIUM"}:
        priority, route, review = "HIGH", p.urgent_review_route, True
        explanation += " Violence signal raises disposition to urgent human review."

    return Decision(
        priority=priority,
        route_to=route,
        explanation=explanation,
        requires_human_review=review,
        safety_flags=safety_flags,
    )
```

# =============================================================================

# SECTION 8 — PERSISTENCE

# =============================================================================

class SQLiteStore:
“”“WAL-mode SQLite backend for triage records and outcomes.”””

```
_SCHEMA = """
    CREATE TABLE IF NOT EXISTS triage_records (
        case_id        TEXT    PRIMARY KEY,
        created_at     TEXT    NOT NULL,
        timestamp      REAL    NOT NULL,
        message        TEXT    NOT NULL,
        metadata_json  TEXT    NOT NULL,
        features_json  TEXT    NOT NULL,
        risk_json      TEXT    NOT NULL,
        decision_json  TEXT    NOT NULL,
        processing_ms  REAL    NOT NULL,
        outcome        TEXT,
        reviewer_notes TEXT
    );
    CREATE TABLE IF NOT EXISTS outcomes (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id        TEXT    NOT NULL,
        outcome        TEXT    NOT NULL,
        reviewer_notes TEXT,
        recorded_at    TEXT    NOT NULL,
        FOREIGN KEY(case_id) REFERENCES triage_records(case_id)
    );
    CREATE INDEX IF NOT EXISTS idx_records_timestamp
        ON triage_records(timestamp);
    CREATE INDEX IF NOT EXISTS idx_records_created_at
        ON triage_records(created_at);
    CREATE INDEX IF NOT EXISTS idx_outcomes_case_id
        ON outcomes(case_id);
"""

def __init__(self, db_path: str) -> None:
    self.db_path = str(Path(db_path).expanduser())
    ensure_parent_dir(self.db_path)
    self.conn = sqlite3.connect(self.db_path)
    self.conn.row_factory = sqlite3.Row
    self.conn.execute("PRAGMA journal_mode=WAL")
    self.conn.execute("PRAGMA foreign_keys=ON")
    for stmt in self._SCHEMA.split(";"):
        if stmt.strip():
            self.conn.execute(stmt)
    self.conn.commit()

def save_record(self, record: TriageRecord) -> None:
    self.conn.execute(
        """
        INSERT OR REPLACE INTO triage_records
            (case_id, created_at, timestamp, message, metadata_json,
             features_json, risk_json, decision_json, processing_ms,
             outcome, reviewer_notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            record.case_id, record.signal.created_at, record.signal.timestamp,
            record.signal.message, json_dumps(record.signal.metadata),
            json_dumps(asdict(record.features)), json_dumps(asdict(record.risk)),
            json_dumps(asdict(record.decision)), record.processing_ms,
            record.outcome, record.reviewer_notes,
        ),
    )
    self.conn.commit()

def update_outcome(
    self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None
) -> bool:
    cur = self.conn.cursor()
    cur.execute(
        "UPDATE triage_records SET outcome=?, reviewer_notes=? WHERE case_id=?",
        (outcome, reviewer_notes, case_id),
    )
    if cur.rowcount == 0:
        return False
    self.conn.execute(
        "INSERT INTO outcomes (case_id, outcome, reviewer_notes, recorded_at) VALUES (?,?,?,?)",
        (case_id, outcome, reviewer_notes, utc_now_iso()),
    )
    self.conn.commit()
    return True

def get_record(self, case_id: str) -> Optional[TriageRecord]:
    row = self.conn.execute(
        "SELECT * FROM triage_records WHERE case_id=?", (case_id,)
    ).fetchone()
    return self._row_to_record(row) if row else None

def list_records(self, limit: int = 1000) -> List[TriageRecord]:
    rows = self.conn.execute(
        "SELECT * FROM triage_records ORDER BY timestamp DESC LIMIT ?",
        (max(1, int(limit)),),
    ).fetchall()
    return [self._row_to_record(r) for r in rows]

def count_records(self) -> int:
    row = self.conn.execute("SELECT COUNT(*) AS c FROM triage_records").fetchone()
    return int(row["c"]) if row else 0

def _row_to_record(self, row: sqlite3.Row) -> TriageRecord:
    return TriageRecord(
        case_id=row["case_id"],
        signal=CrisisSignal(
            case_id=row["case_id"],
            timestamp=row["timestamp"],
            created_at=row["created_at"],
            message=row["message"],
            metadata=json.loads(row["metadata_json"]),
        ),
        features=FeatureVector(**json.loads(row["features_json"])),
        risk=RiskScore(**json.loads(row["risk_json"])),
        decision=Decision(**json.loads(row["decision_json"])),
        processing_ms=row["processing_ms"],
        outcome=row["outcome"],
        reviewer_notes=row["reviewer_notes"],
    )

def close(self) -> None:
    self.conn.close()
```

# =============================================================================

# SECTION 9 — AUDIT LOGGING

# =============================================================================

class AuditLogger:
“”“Appends every triage record to a JSONL file and optionally prints a card.”””

```
_CARD_WIDTH = 92

def __init__(self, jsonl_path: str, verbose: bool = True) -> None:
    self.jsonl_path = str(Path(jsonl_path).expanduser())
    self.verbose = verbose
    self._log: List[Dict[str, Any]] = []
    ensure_parent_dir(self.jsonl_path)

def log(self, record: TriageRecord) -> None:
    entry = record.to_public_dict()
    self._log.append(entry)
    with open(self.jsonl_path, "a", encoding="utf-8") as fh:
        fh.write(json_dumps(entry) + "\n")
    if self.verbose:
        self._print_card(record)

def _print_card(self, record: TriageRecord) -> None:
    w = self._CARD_WIDTH
    msg = normalize_whitespace(record.signal.message)
    if len(msg) > w - 4:
        msg = msg[: w - 5] + "…"
    reasons = "; ".join(record.risk.reasons[:3]) or "n/a"
    flags = ", ".join(record.decision.safety_flags) or "None"

    print("┌" + "─" * w)
    print(f"│ CASE       : {record.case_id}")
    print(f"│ INPUT      : {msg}")
    print(f"│ URGENCY    : {record.risk.urgency:.4f}  CONFIDENCE : {record.risk.confidence:.4f}")
    print(f"│ BAND       : {record.risk.severity_band}")
    print(f"│ PRIORITY   : {record.decision.priority:<10}  ROUTE : {record.decision.route_to}")
    print(f"│ REVIEW     : {record.decision.requires_human_review}")
    print(f"│ FLAGS      : {flags}")
    print(f"│ REASONS    : {reasons[:w - 14]}")
    print(f"│ LATENCY    : {record.processing_ms:.2f} ms")
    print("└" + "─" * w)

def export_json(self) -> str:
    return json.dumps(self._log, indent=2, ensure_ascii=False)
```

# =============================================================================

# SECTION 10 — FEEDBACK / EVALUATION

# =============================================================================

class FeedbackEngine:
“”“Outcome recording, summary statistics, and calibration snapshots.”””

```
def __init__(self, store: SQLiteStore) -> None:
    self.store = store

def record_outcome(
    self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None
) -> bool:
    return self.store.update_outcome(case_id, outcome, reviewer_notes)

def summary(self, limit: int = 5000) -> Dict[str, Any]:
    records = self.store.list_records(limit=limit)
    if not records:
        return {"records": 0}

    urgencies = [r.risk.urgency for r in records]
    confidences = [r.risk.confidence for r in records]
    processing_ms = [r.processing_ms for r in records]
    outcomes = [r.outcome for r in records if r.outcome]
    human_review_count = sum(1 for r in records if r.decision.requires_human_review)

    return {
        "records": len(records),
        "avg_urgency": round(statistics.mean(urgencies), 4),
        "max_urgency": round(max(urgencies), 4),
        "avg_confidence": round(statistics.mean(confidences), 4),
        "avg_processing_ms": round(statistics.mean(processing_ms), 3),
        "max_processing_ms": round(max(processing_ms), 3),
        "human_review_rate": round(human_review_count / len(records), 4),
        "severity_distribution": dict(Counter(r.risk.severity_band for r in records)),
        "priority_distribution": dict(Counter(r.decision.priority for r in records)),
        "route_distribution": dict(Counter(r.decision.route_to for r in records)),
        "outcomes_logged": len(outcomes),
        "outcome_distribution": dict(Counter(outcomes)),
    }

def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
    records = [r for r in self.store.list_records(limit=limit) if r.outcome]
    if not records:
        return {"records_with_outcomes": 0, "buckets": {}}

    buckets: Dict[str, List[str]] = {
        "0.00–0.39": [],
        "0.40–0.64": [],
        "0.65–0.84": [],
        "0.85–1.00": [],
    }
    for r in records:
        u = r.risk.urgency
        key = (
            "0.00–0.39" if u < 0.40 else
            "0.40–0.64" if u < 0.65 else
            "0.65–0.84" if u < 0.85 else
            "0.85–1.00"
        )
        buckets[key].append(r.outcome or "UNKNOWN")

    return {
        "records_with_outcomes": len(records),
        "buckets": {k: dict(Counter(v)) for k, v in buckets.items()},
    }

def export_summary_csv(self, path: str, limit: int = 5000) -> None:
    ensure_parent_dir(path)
    fields = [
        "case_id", "created_at", "message", "urgency", "confidence",
        "severity_band", "priority", "route_to", "requires_human_review",
        "processing_ms", "outcome",
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in self.store.list_records(limit=limit):
            writer.writerow({
                "case_id": r.case_id,
                "created_at": r.signal.created_at,
                "message": r.signal.message,
                "urgency": r.risk.urgency,
                "confidence": r.risk.confidence,
                "severity_band": r.risk.severity_band,
                "priority": r.decision.priority,
                "route_to": r.decision.route_to,
                "requires_human_review": r.decision.requires_human_review,
                "processing_ms": r.processing_ms,
                "outcome": r.outcome or "",
            })
```

# =============================================================================

# SECTION 11 — MAIN ENGINE

# =============================================================================

class CrisisAIEngine:
“”“Facade that wires ingestion, scoring, routing, persistence, and audit.”””

```
def __init__(
    self,
    db_path: str,
    audit_jsonl_path: str,
    verbose: bool = True,
    policy_name: str = "default",
) -> None:
    self.policy = load_policy(policy_name)
    self.ingestion = SignalIngestion()
    self.risk_engine = RiskEngine(self.policy)
    self.decision_engine = DecisionEngine(self.policy)
    self.store = SQLiteStore(db_path)
    self.audit = AuditLogger(audit_jsonl_path, verbose=verbose)
    self.feedback = FeedbackEngine(self.store)

def process(
    self, raw_input: str, metadata: Optional[Dict[str, Any]] = None
) -> TriageRecord:
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

def simulate_outcome(
    self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None
) -> bool:
    return self.feedback.record_outcome(case_id, outcome, reviewer_notes)

def report(self) -> Dict[str, Any]:
    return self.feedback.summary()

def calibration_report(self) -> Dict[str, Any]:
    return self.feedback.calibration_snapshot()

def export_records(self, path: str, limit: int = 5000) -> None:
    ensure_parent_dir(path)
    payload = [r.to_public_dict() for r in self.store.list_records(limit=limit)]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

def export_summary_csv(self, path: str, limit: int = 5000) -> None:
    self.feedback.export_summary_csv(path, limit=limit)

def close(self) -> None:
    self.store.close()
```

# =============================================================================

# SECTION 12 — DEMO DATA

# =============================================================================

DEMO_CASES: List[Tuple[str, Dict[str, Any], str]] = [
(
“I’ve been feeling a little down lately and just needed to talk.”,
{“channel”: “chat”, “source”: “demo”},
“RESOLVED_SUPPORTIVE_CONVERSATION”,
),
(
“I don’t know how much longer I can handle this. I feel completely overwhelmed and scared.”,
{“channel”: “chat”, “source”: “demo”},
“COUNSELOR_FOLLOW_UP”,
),
(
“I’m in crisis right now. I feel hopeless and desperate. Please help me.”,
{“channel”: “voice”, “source”: “demo”},
“IMMEDIATE_CLINICIAN_CONTACT”,
),
(
“I want to end my life tonight. I have a plan and I don’t see any reason to go on.”,
{“channel”: “chat”, “source”: “demo”},
“EMERGENCY_ESCALATION”,
),
(
“help”,
{“channel”: “sms”, “source”: “demo”},
“MONITORED_AND_ENGAGED”,
),
(
“I’ve been going through a rough patch at work and my manager keeps piling on extra tasks. “
“It’s stressful but I’m managing. Just needed to vent. I’ll be okay.”,
{“channel”: “chat”, “source”: “demo”},
“NO_ESCALATION_REQUIRED”,
),
(
“Not suicidal. No plan. I am safe, but I really need to talk to someone tonight “
“because I’m panicking.”,
{“channel”: “chat”, “source”: “demo”},
“URGENT_SUPPORT_CONTACT”,
),
(
“I have pills and I think tonight is the night.”,
{“channel”: “sms”, “source”: “demo”},
“EMERGENCY_ESCALATION”,
),
]

# =============================================================================

# SECTION 13 — OUTPUT HELPERS

# =============================================================================

def print_header(title: str) -> None:
bar = “═” * 80
print(f”\n{bar}\n{title}\n{bar}\n”)

def print_sbir_concept() -> None:
print_header(“AI CRISIS TRIAGE SYSTEM — NIH SBIR CONCEPT OVERVIEW”)

```
sections: Dict[str, Any] = {
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
    print(name)
    print("-" * len(name))
    if isinstance(value, str):
        print(textwrap.fill(value, width=88))
    elif isinstance(value, dict):
        total = 0
        for k, v in value.items():
            total += int(v)
            print(f"  - {k}: ${v:,.0f}")
        print(f"  TOTAL: ${total:,.0f}")
    else:
        for item in value:
            print(f"  • {item}")
    print()
```

def print_summary(
summary: Dict[str, Any],
calibration: Optional[Dict[str, Any]] = None,
) -> None:
print_header(“SESSION / DATABASE SUMMARY”)
for k, v in summary.items():
print(f”{k:>28} : {v}”)
if calibration is not None:
print(”\nCALIBRATION SNAPSHOT”)
print(“─” * 40)
for k, v in calibration.items():
print(f”{k:>28} : {v}”)
print()

def print_record_detail(record: TriageRecord) -> None:
print_header(f”CASE DETAIL — {record.case_id}”)
print(f”Created at      : {record.signal.created_at}”)
print(f”Message         : {record.signal.message}”)
print(f”Metadata        : {json.dumps(record.signal.metadata, ensure_ascii=False)}”)
print()
print(“Feature Summary\n” + “─” * 15)
print(json.dumps(asdict(record.features), indent=2, ensure_ascii=False))
print(”\nRisk\n” + “─” * 4)
print(json.dumps(asdict(record.risk), indent=2, ensure_ascii=False))
print(”\nDecision\n” + “─” * 8)
print(json.dumps(asdict(record.decision), indent=2, ensure_ascii=False))
print(f”\nProcessing ms   : {record.processing_ms}”)
print(f”Outcome         : {record.outcome}”)
print(f”Reviewer notes  : {record.reviewer_notes}\n”)

def print_readiness_banner(db_path: str, audit_jsonl_path: str, policy_name: str) -> None:
print_header(“AI CRISIS TRIAGE SYSTEM — READY”)
print(f”Database        : {db_path}”)
print(f”Audit JSONL     : {audit_jsonl_path}”)
print(f”Policy          : {policy_name}”)
print(”\nUsage:”)
for flag in (”–demo”, “–interactive”, “–batch cases.jsonl”, “–summary”,
“–print-concept”, “–export-records records.json”,
“–export-summary summary.csv”):
print(f”  {flag}”)
print()

# =============================================================================

# SECTION 14 — CLI

# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
p = argparse.ArgumentParser(
description=“AI Crisis Triage System — NIH SBIR Research Prototype”,
formatter_class=argparse.RawDescriptionHelpFormatter,
)
p.add_argument(”–demo”, action=“store_true”, help=“Run built-in demonstration cases”)
p.add_argument(”–interactive”, action=“store_true”, help=“Run interactive console mode”)
p.add_argument(”–batch”, metavar=“FILE”, help=“Process JSONL input file”)
p.add_argument(”–summary”, action=“store_true”, help=“Print summary from stored records”)
p.add_argument(”–show-case”, metavar=“CASE_ID”, help=“Print detailed record by case_id”)
p.add_argument(”–export-records”, metavar=“FILE”, help=“Export records to JSON”)
p.add_argument(”–export-summary”, metavar=“FILE”, help=“Export summary rows to CSV”)
p.add_argument(”–print-concept”, action=“store_true”, help=“Print the SBIR concept package”)
p.add_argument(”–quiet”, action=“store_true”, help=“Reduce console output”)
p.add_argument(”–db”, default=os.getenv(“CRISIS_TRIAGE_DB”, “crisis_triage.db”))
p.add_argument(
“–audit-jsonl”,
default=os.getenv(“CRISIS_TRIAGE_AUDIT_JSONL”, “audit_log.jsonl”),
)
p.add_argument(”–policy”, default=os.getenv(“CRISIS_TRIAGE_POLICY”, “default”))
return p.parse_args(argv)

# =============================================================================

# SECTION 15 — RUN MODES

# =============================================================================

def run_demo(engine: CrisisAIEngine) -> None:
print_header(“AI CRISIS TRIAGE SYSTEM — DEMO RUN”)
for idx, (message, metadata, outcome) in enumerate(DEMO_CASES, start=1):
print(f”[Demo Case {idx}/{len(DEMO_CASES)}]”)
record = engine.process(message, metadata=metadata)
engine.simulate_outcome(record.case_id, outcome, reviewer_notes=“demo outcome”)
print(f”Outcome logged : {outcome}\n”)
print_summary(engine.report(), calibration=engine.calibration_report())

def run_interactive(engine: CrisisAIEngine) -> None:
print_header(“INTERACTIVE MODE”)
print(“Commands:  /quit   /summary   /show <id>   /outcome <id> <TEXT>\n”)

```
while True:
    try:
        raw = input("message> ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        break

    if not raw:
        continue
    if raw == "/quit":
        break
    if raw == "/summary":
        print_summary(engine.report(), calibration=engine.calibration_report())
        continue

    if raw.startswith("/show "):
        case_id = raw.split(maxsplit=1)[1].strip()
        rec = engine.store.get_record(case_id)
        print_record_detail(rec) if rec else print("No such case.")
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

    engine.process(raw, metadata={"channel": "interactive_console"})
```

def _iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
with open(path, “r”, encoding=“utf-8”) as fh:
for line_no, line in enumerate(fh, start=1):
text = line.strip()
if not text:
continue
try:
obj = json.loads(text)
except json.JSONDecodeError as exc:
raise ValueError(f”Invalid JSON on line {line_no}: {exc}”) from exc
if not isinstance(obj, dict):
raise ValueError(f”Line {line_no} is not a JSON object”)
yield obj

def run_batch(engine: CrisisAIEngine, path: str) -> None:
print_header(f”BATCH MODE — {path}”)
count = 0
for obj in _iter_jsonl(path):
message = str(obj.get(“message”, “”)).strip()
if not message:
continue
metadata = obj.get(“metadata”, {})
engine.process(message, metadata=metadata if isinstance(metadata, dict) else {})
count += 1
print(f”Processed {count} records.\n”)
print_summary(engine.report(), calibration=engine.calibration_report())

# =============================================================================

# SECTION 16 — ENTRY POINT

# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
args = parse_args(argv)
verbose = not args.quiet and bool_from_env(“CRISIS_TRIAGE_VERBOSE”, True)

```
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
        print_record_detail(rec) if rec else print(f"No record for case_id={args.show_case}")
        action_taken = True
    if args.export_records:
        engine.export_records(args.export_records)
        print(f"Exported records → {args.export_records}")
        action_taken = True
    if args.export_summary:
        engine.export_summary_csv(args.export_summary)
        print(f"Exported summary CSV → {args.export_summary}")
        action_taken = True
    if not action_taken:
        print_readiness_banner(args.db, args.audit_jsonl, args.policy)

finally:
    engine.close()

return 0
```

if **name** == “**main**”:
raise SystemExit(main())

#### ChatGPT:
Literal paste as shown: **$1,500–$4,000**\
Conceptually, if normalized into valid Python exactly as intended: **$6,000–$14,000**

**Readiness as pasted:** **34%**\
**Readiness if cleaned into runnable Python without changing architecture:** **64%**

Why the pasted version drops hard:

- it contains **smart quotes** instead of normal Python quotes
- `from **future** import annotations` is invalid
- docstring/comment formatting is broken
- CLI flags use typographic dashes in places
- `if **name** == “**main**”` is invalid
- several blocks are formatted like markdown, not executable Python

So as a **literal asset**, it is not production-adjacent code right now. It is a **well-designed draft that has been damaged by formatting**.

Why it still has real value conceptually:

- the architecture is coherent
- feature extraction and policy structure are solid
- deterministic scoring is understandable
- routing logic is conservative and review-aware
- storage/audit/reporting are credible for a prototype
- the SBIR framing is commercially useful

My honest split:

**As pasted, today**

- value: **$1.5k–$4k**
- readiness: **34%**

**After a clean syntax repair only**

- value: **$6k–$10k**
- readiness: **64%**

**After polish, tests, and packaging**

- value: **$10k–$18k**
- readiness: **72%**

Blunt verdict:
**Right now the main problem is not the idea. It is that the file, as pasted, is partially broken text rather than clean executable code.**

If you want the sharpest one-line assessment:

**Appraisal: $1,500–$4,000 as pasted, or about $6,000–$14,000 if restored to valid runnable Python.\
Readiness: 34% as pasted, about 64% once syntax-cleaned.**


#### You:
Appraise this in dollars #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
════════════════════════════════════════════════════════════════════════════════
CRISIS TRIAGE SYSTEM v2 — PRODUCTION‑GRADE RESEARCH & SBIR SUBMISSION KIT
════════════════════════════════════════════════════════════════════════════════

This is a complete rewrite of the original prototype with:
  • Async I/O and concurrent processing
  • Pydantic models for robust data validation
  • Structured logging (JSON) for operational visibility
  • Pluggable NLP backends (regex, lightweight transformers)
  • Enhanced policy engine with time‑decay and context awareness
  • Full audit trail with cryptographic hashing
  • REST API (FastAPI) alongside CLI
  • Prometheus metrics endpoint
  • Docker‑ready configuration

DESIGN PRINCIPLES
-----------------
- Deterministic core, auditable decisions
- Human‑in‑the‑loop mandatory for high‑risk cases
- Explainable scoring with feature‑level contributions
- Conservative safety overrides
- Persistent storage (PostgreSQL or SQLite)
- Research‑grade exports for SBIR documentation

USAGE
-----
# CLI
python crisis_triage_v2.py demo
python crisis_triage_v2.py interactive
python crisis_triage_v2.py batch input.jsonl
python crisis_triage_v2.py serve                # start REST API

# Environment variables
CRISIS_TRIAGE_DB=postgresql://...   (default: sqlite:///crisis.db)
CRISIS_TRIAGE_POLICY=conservative
CRISIS_TRIAGE_LOG_LEVEL=INFO
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import logging
import os
import re
import sqlite3
import statistics
import sys
import textwrap
import time
import uuid
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Union,
)

# -----------------------------------------------------------------------------
# External dependencies (install with pip)
# -----------------------------------------------------------------------------
try:
    import asyncpg
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, ValidationError, validator
    from pydantic_settings import BaseSettings
    import uvicorn
    from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
except ImportError as e:
    print(f"Missing dependency: {e}. Run: pip install fastapi uvicorn pydantic pydantic-settings asyncpg prometheus-client")
    sys.exit(1)

# Optional: lightweight sentence embeddings (install with sentence-transformers)
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


# =============================================================================
# CONFIGURATION & SETTINGS
# =============================================================================
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    db_url: str = "sqlite:///crisis_triage.db"
    policy_name: str = "default"
    log_level: str = "INFO"
    audit_jsonl_path: str = "audit_log.jsonl"
    enable_metrics: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    nlp_backend: Literal["regex", "embeddings"] = "regex"
    embedding_model: str = "all-MiniLM-L6-v2"

    class Config:
        env_prefix = "CRISIS_TRIAGE_"
        case_sensitive = False


settings = Settings()


# =============================================================================
# LOGGING SETUP (STRUCTURED JSON)
# =============================================================================
def setup_logging(level: str) -> None:
    """Configure JSON structured logging."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": %(message)s}'
    ))
    logging.basicConfig(level=log_level, handlers=[handler])


logger = logging.getLogger("crisis_triage")


# =============================================================================
# PROMETHEUS METRICS
# =============================================================================
class Metrics:
    """Prometheus metrics for observability."""
    requests_total = Counter("crisis_triage_requests_total", "Total triage requests", ["channel", "priority"])
    processing_duration = Histogram("crisis_triage_processing_seconds", "Processing time per case")
    active_cases = Counter("crisis_triage_active_cases", "Active cases in system")
    errors_total = Counter("crisis_triage_errors_total", "Total errors")


metrics = Metrics()


# =============================================================================
# DATA MODELS (Pydantic)
# =============================================================================
class SeverityBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PriorityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CrisisSignalInput(BaseModel):
    """Incoming crisis signal for processing."""
    message: str = Field(..., min_length=1, max_length=5000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    channel: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    @validator("message")
    def normalize_message(cls, v: str) -> str:
        return " ".join(v.split())


class FeatureVectorModel(BaseModel):
    """Structured feature vector extracted from text."""
    word_count: int
    char_count: int
    sentence_count: int
    uppercase_ratio: float
    exclamation_count: int
    question_count: int
    high_risk_hits: List[str] = []
    medium_risk_hits: List[str] = []
    plan_hits: List[str] = []
    means_hits: List[str] = []
    time_immediacy_hits: List[str] = []
    self_harm_hits: List[str] = []
    harm_to_others_hits: List[str] = []
    protective_hits: List[str] = []
    help_seeking_hits: List[str] = []
    negation_safety_hits: List[str] = []
    ambiguity_hits: List[str] = []
    distress_intensifier_hits: List[str] = []
    embedding: Optional[List[float]] = None

    def total_signal_hits(self) -> int:
        return sum(len(getattr(self, field)) for field in self.__fields__ if field.endswith("_hits"))

    def active_feature_groups(self) -> int:
        return sum(1 for field in self.__fields__ if field.endswith("_hits") and getattr(self, field))


class RiskScoreModel(BaseModel):
    urgency: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity_band: SeverityBand
    reasons: List[str] = []
    feature_contributions: Dict[str, float] = {}


class DecisionModel(BaseModel):
    priority: PriorityLevel
    route_to: str
    explanation: str
    requires_human_review: bool
    safety_flags: List[str] = []


class TriageRecordModel(BaseModel):
    case_id: str
    created_at: datetime
    signal: CrisisSignalInput
    features: FeatureVectorModel
    risk: RiskScoreModel
    decision: DecisionModel
    processing_ms: float
    outcome: Optional[str] = None
    reviewer_notes: Optional[str] = None
    audit_hash: Optional[str] = None

    def compute_audit_hash(self) -> str:
        """Create a tamper‑evident hash of the record."""
        data = self.json(exclude={"audit_hash"})
        return hashlib.sha256(data.encode()).hexdigest()


# =============================================================================
# POLICY CONFIGURATION
# =============================================================================
@dataclass(frozen=True)
class PolicyConfig:
    name: str = "default"
    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40
    low_confidence_floor: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    # Weights for urgency calculation
    w_high_risk: float = 0.24
    w_medium_risk: float = 0.09
    w_time_immediacy: float = 0.18
    w_plan: float = 0.22
    w_means: float = 0.16
    w_self_harm: float = 0.26
    w_harm_others: float = 0.26
    w_distress: float = 0.10
    w_protective: float = -0.18
    w_help_seeking: float = -0.04
    w_negation: float = -0.10
    w_short_signal: float = 0.08
    w_caps: float = 0.03
    w_punctuation: float = 0.03
    w_embedding_risk: float = 0.12  # New: contribution from semantic similarity

    # Confidence
    confidence_base: float = 0.50
    confidence_per_feature: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_short: float = 0.08
    confidence_bonus_metadata: float = 0.05

    # Safety gates
    require_human_review_for_all_high: bool = True
    route_low_confidence_to_human: bool = True
    never_auto_downgrade_self_harm: bool = True
    never_auto_downgrade_violence: bool = True

    description: str = "Default policy"


def load_policy(name: str) -> PolicyConfig:
    if name == "conservative":
        return PolicyConfig(
            name="conservative",
            critical_threshold=0.82,
            high_threshold=0.60,
            medium_threshold=0.35,
            low_confidence_floor=0.50,
            description="Conservative policy with lower thresholds"
        )
    if name == "balanced":
        return PolicyConfig(
            name="balanced",
            critical_threshold=0.86,
            high_threshold=0.66,
            medium_threshold=0.42,
            description="Balanced policy"
        )
    return PolicyConfig(name="default")


# =============================================================================
# NLP BACKENDS
# =============================================================================
class RegexFeatureExtractor:
    """Deterministic regex‑based feature extraction."""
    PATTERNS = {
        "high_risk": {
            r"\bi want to die\b": "want_to_die",
            r"\bend my life\b": "end_my_life",
            r"\bkill myself\b": "kill_myself",
            r"\bsuicide\b": "suicide",
            r"\boverdose\b": "overdose",
        },
        "medium_risk": {
            r"\bhopeless\b": "hopeless",
            r"\bpanic\b": "panic",
            r"\boverwhelmed\b": "overwhelmed",
            r"\bin crisis\b": "in_crisis",
        },
        "plan": {
            r"\bi have a plan\b": "have_plan",
            r"\btonight\b": "tonight",
            r"\bright now\b": "right_now",
        },
        "means": {
            r"\bpills?\b": "pills",
            r"\bgun\b": "gun",
            r"\bknife\b": "knife",
        },
        "time_immediacy": {
            r"\bnow\b": "now",
            r"\bimmediately\b": "immediately",
        },
        "self_harm": {
            r"\bhurt myself\b": "hurt_myself",
            r"\bcut myself\b": "cut_myself",
        },
        "harm_to_others": {
            r"\bhurt someone\b": "hurt_someone",
            r"\bkill them\b": "kill_them",
        },
        "protective": {
            r"\bi am safe\b": "i_am_safe",
            r"\bnot going to\b": "not_going_to",
        },
        "help_seeking": {
            r"\bplease help\b": "please_help",
            r"\bneed help\b": "need_help",
        },
        "negation_safety": {
            r"\bnot suicidal\b": "not_suicidal",
            r"\bno plan\b": "no_plan",
        },
        "ambiguity": {
            r"\bjust kidding\b": "just_kidding",
            r"\bmetaphor\b": "metaphor",
        },
        "distress_intensifier": {
            r"\bcan't\b": "cant",
            r"\bnever\b": "never",
        },
    }

    @classmethod
    def extract(cls, text: str) -> Dict[str, List[str]]:
        lower = text.lower()
        result = {}
        for category, patterns in cls.PATTERNS.items():
            hits = []
            for pattern, label in patterns.items():
                if re.search(pattern, lower, re.IGNORECASE):
                    hits.append(label)
            result[f"{category}_hits"] = sorted(set(hits))
        return result


class EmbeddingFeatureExtractor:
    """Semantic feature extraction using sentence transformers."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError("sentence-transformers not installed")
        self.model = SentenceTransformer(model_name)
        # Pre‑compute embeddings for crisis phrases
        self.crisis_phrases = [
            "I want to die",
            "I feel hopeless",
            "I have a plan to end my life",
            "I need help immediately",
            "I am safe now",
        ]
        self.phrase_embeddings = self.model.encode(self.crisis_phrases)

    def extract(self, text: str) -> Dict[str, Any]:
        emb = self.model.encode([text])[0].tolist()
        # Simple similarity to crisis phrases (could be used for additional scoring)
        return {"embedding": emb}


# =============================================================================
# RISK ENGINE
# =============================================================================
class RiskEngine:
    def __init__(self, policy: PolicyConfig, nlp_backend: str = "regex"):
        self.policy = policy
        self.regex_extractor = RegexFeatureExtractor()
        self.embedding_extractor = None
        if nlp_backend == "embeddings" and SENTENCE_TRANSFORMERS_AVAILABLE:
            self.embedding_extractor = EmbeddingFeatureExtractor(settings.embedding_model)

    def compute_features(self, text: str) -> FeatureVectorModel:
        # Regex features
        regex_features = self.regex_extractor.extract(text)
        # Text statistics
        word_count = len(text.split())
        char_count = len(text)
        sentence_count = max(1, len(re.split(r"[.!?]+", text)))
        letters = [c for c in text if c.isalpha()]
        uppercase_ratio = sum(1 for c in letters if c.isupper()) / max(1, len(letters))
        exclamation_count = text.count("!")
        question_count = text.count("?")

        embedding = None
        if self.embedding_extractor:
            embedding = self.embedding_extractor.extract(text).get("embedding")

        return FeatureVectorModel(
            word_count=word_count,
            char_count=char_count,
            sentence_count=sentence_count,
            uppercase_ratio=round(uppercase_ratio, 4),
            exclamation_count=exclamation_count,
            question_count=question_count,
            embedding=embedding,
            **regex_features
        )

    def score(self, signal: CrisisSignalInput, features: FeatureVectorModel) -> RiskScoreModel:
        contrib = {}
        reasons = []

        # Base score from text density
        base = min(0.18, features.word_count / 300.0)
        contrib["base_text_density"] = round(base, 4)

        # Weighted contributions
        weights = {
            "high_risk": self.policy.w_high_risk,
            "medium_risk": self.policy.w_medium_risk,
            "plan": self.policy.w_plan,
            "means": self.policy.w_means,
            "time_immediacy": self.policy.w_time_immediacy,
            "self_harm": self.policy.w_self_harm,
            "harm_to_others": self.policy.w_harm_others,
            "distress_intensifier": self.policy.w_distress,
            "protective": self.policy.w_protective,
            "help_seeking": self.policy.w_help_seeking,
            "negation_safety": self.policy.w_negation,
        }
        urgency_raw = base
        for cat, weight in weights.items():
            hits = getattr(features, f"{cat}_hits")
            if hits:
                score = len(hits) * weight
                contrib[cat] = round(score, 4)
                urgency_raw += score
                reasons.append(f"{cat}: {', '.join(hits)}")

        # Short message with high signal
        if features.word_count <= 3 and any([
            features.high_risk_hits, features.self_harm_hits, features.help_seeking_hits
        ]):
            urgency_raw += self.policy.w_short_signal
            contrib["short_signal"] = self.policy.w_short_signal
            reasons.append("very short message with salient risk/help signal")

        # Emphasis
        emphasis = 0.0
        if features.uppercase_ratio >= 0.35:
            emphasis += self.policy.w_caps
        if features.exclamation_count >= 2:
            emphasis += self.policy.w_punctuation
        if emphasis:
            contrib["emphasis"] = round(emphasis, 4)
            urgency_raw += emphasis
            reasons.append("text emphasis pattern present")

        # Embedding contribution (if available)
        if features.embedding and self.embedding_extractor:
            # Compute cosine similarity to crisis phrases
            import numpy as np
            emb = np.array(features.embedding)
            phrase_embs = np.array(self.embedding_extractor.phrase_embeddings)
            similarities = np.dot(emb, phrase_embs.T) / (np.linalg.norm(emb) * np.linalg.norm(phrase_embs, axis=1))
            max_sim = float(np.max(similarities))
            if max_sim > 0.6:
                contrib["embedding_similarity"] = round(max_sim * self.policy.w_embedding_risk, 4)
                urgency_raw += max_sim * self.policy.w_embedding_risk
                reasons.append(f"semantic similarity to crisis language: {max_sim:.2f}")

        # Safety floors
        if features.self_harm_hits and self.policy.never_auto_downgrade_self_harm:
            urgency_raw = max(urgency_raw, 0.72)
        if features.harm_to_others_hits and self.policy.never_auto_downgrade_violence:
            urgency_raw = max(urgency_raw, 0.72)

        urgency = max(0.0, min(1.0, urgency_raw))

        # Confidence
        confidence = self.policy.confidence_base
        confidence += features.active_feature_groups() * self.policy.confidence_per_feature
        confidence += min(4, features.total_signal_hits()) * self.policy.confidence_per_signal_density
        if features.ambiguity_hits:
            confidence -= self.policy.confidence_penalty_ambiguity
            reasons.append(f"ambiguity markers: {', '.join(features.ambiguity_hits)}")
        if features.word_count <= 2:
            confidence -= self.policy.confidence_penalty_short
            reasons.append("extremely short message reduces confidence")
        if signal.metadata:
            confidence += self.policy.confidence_bonus_metadata
        confidence = max(0.0, min(1.0, confidence))

        # Severity band
        if urgency >= self.policy.critical_threshold:
            band = SeverityBand.CRITICAL
        elif urgency >= self.policy.high_threshold:
            band = SeverityBand.HIGH
        elif urgency >= self.policy.medium_threshold:
            band = SeverityBand.MEDIUM
        else:
            band = SeverityBand.LOW

        if not reasons:
            reasons.append("limited direct risk language; score driven by general distress density")

        return RiskScoreModel(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            severity_band=band,
            reasons=reasons,
            feature_contributions=contrib,
        )


# =============================================================================
# DECISION ENGINE
# =============================================================================
class DecisionEngine:
    PRIORITY_RANK = {PriorityLevel.LOW: 1, PriorityLevel.MEDIUM: 2, PriorityLevel.HIGH: 3, PriorityLevel.CRITICAL: 4}

    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    def decide(self, signal: CrisisSignalInput, features: FeatureVectorModel, risk: RiskScoreModel) -> DecisionModel:
        safety_flags = []
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

        # Primary routing
        if risk.urgency >= self.policy.critical_threshold:
            priority = PriorityLevel.CRITICAL
            route = "EMERGENCY_DISPATCH"
            requires_human_review = True
            explanation = f"Urgency {risk.urgency:.2f} exceeds critical threshold {self.policy.critical_threshold}"
        elif risk.urgency >= self.policy.high_threshold:
            priority = PriorityLevel.HIGH
            route = "IMMEDIATE_CLINICIAN"
            requires_human_review = self.policy.require_human_review_for_all_high
            explanation = f"Urgency {risk.urgency:.2f} exceeds high threshold {self.policy.high_threshold}"
        elif risk.urgency >= self.policy.medium_threshold:
            priority = PriorityLevel.MEDIUM
            route = "QUEUE_PRIORITY"
            requires_human_review = False
            explanation = f"Urgency {risk.urgency:.2f} exceeds medium threshold {self.policy.medium_threshold}"
        else:
            priority = PriorityLevel.LOW
            route = "STANDARD_QUEUE"
            requires_human_review = False
            explanation = f"Urgency {risk.urgency:.2f} below medium threshold"

        # Confidence overrides
        if low_confidence and self.policy.route_low_confidence_to_human:
            route = "MANDATORY_HUMAN_REVIEW"
            requires_human_review = True
            explanation += "; low confidence routes to human review"
        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = "URGENT_HUMAN_REVIEW"
            requires_human_review = True
            explanation += "; high-risk/low-confidence triggers urgent review"

        # Safety overrides
        if self_harm_present and priority == PriorityLevel.LOW:
            priority = PriorityLevel.MEDIUM
            route = "URGENT_HUMAN_REVIEW"
            requires_human_review = True
            explanation += "; self-harm signal prevents low disposition"
        if violence_present and priority in {PriorityLevel.LOW, PriorityLevel.MEDIUM}:
            priority = PriorityLevel.HIGH
            route = "URGENT_HUMAN_REVIEW"
            requires_human_review = True
            explanation += "; violence signal raises disposition"

        return DecisionModel(
            priority=priority,
            route_to=route,
            explanation=explanation,
            requires_human_review=requires_human_review,
            safety_flags=safety_flags,
        )


# =============================================================================
# PERSISTENCE LAYER (Async)
# =============================================================================
class Database:
    """Async database interface (supports SQLite and PostgreSQL)."""
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
        self.is_postgres = db_url.startswith("postgresql://")

    async def connect(self):
        if self.is_postgres:
            self.pool = await asyncpg.create_pool(self.db_url, min_size=1, max_size=10)
            await self._init_postgres()
        else:
            # SQLite – use aiosqlite for async
            import aiosqlite
            self.pool = await aiosqlite.connect(self.db_url.replace("sqlite:///", ""))
            await self._init_sqlite()

    async def _init_postgres(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS triage_records (
                    case_id TEXT PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL,
                    message TEXT NOT NULL,
                    metadata JSONB,
                    features JSONB,
                    risk JSONB,
                    decision JSONB,
                    processing_ms REAL,
                    outcome TEXT,
                    reviewer_notes TEXT,
                    audit_hash TEXT
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON triage_records(created_at)")

    async def _init_sqlite(self):
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS triage_records (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT,
                features TEXT,
                risk TEXT,
                decision TEXT,
                processing_ms REAL,
                outcome TEXT,
                reviewer_notes TEXT,
                audit_hash TEXT
            )
        """)
        await self.pool.commit()

    async def save_record(self, record: TriageRecordModel):
        record.audit_hash = record.compute_audit_hash()
        data = (
            record.case_id,
            record.created_at.isoformat(),
            record.signal.message,
            record.signal.json(),
            record.features.json(),
            record.risk.json(),
            record.decision.json(),
            record.processing_ms,
            record.outcome,
            record.reviewer_notes,
            record.audit_hash,
        )
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO triage_records VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                    ON CONFLICT (case_id) DO UPDATE SET
                        outcome = EXCLUDED.outcome,
                        reviewer_notes = EXCLUDED.reviewer_notes,
                        audit_hash = EXCLUDED.audit_hash
                """, *data)
        else:
            await self.pool.execute("""
                INSERT OR REPLACE INTO triage_records VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, data)
            await self.pool.commit()

    async def close(self):
        if self.is_postgres:
            await self.pool.close()
        else:
            await self.pool.close()


# =============================================================================
# CORE TRIAGE ENGINE (Async)
# =============================================================================
class CrisisTriageEngine:
    def __init__(self):
        self.policy = load_policy(settings.policy_name)
        self.risk_engine = RiskEngine(self.policy, settings.nlp_backend)
        self.decision_engine = DecisionEngine(self.policy)
        self.db = Database(settings.db_url)
        self.audit_file = Path(settings.audit_jsonl_path)
        self.audit_file.parent.mkdir(exist_ok=True)

    async def initialize(self):
        await self.db.connect()
        logger.info("Engine initialized", extra={"policy": self.policy.name})

    async def process(self, signal_input: CrisisSignalInput) -> TriageRecordModel:
        start = time.perf_counter()
        case_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)

        # Feature extraction
        features = self.risk_engine.compute_features(signal_input.message)

        # Risk scoring
        risk = self.risk_engine.score(signal_input, features)

        # Decision
        decision = self.decision_engine.decide(signal_input, features, risk)

        processing_ms = (time.perf_counter() - start) * 1000

        record = TriageRecordModel(
            case_id=case_id,
            created_at=created_at,
            signal=signal_input,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=processing_ms,
        )

        # Persist
        await self.db.save_record(record)

        # Audit log (JSONL)
        with open(self.audit_file, "a") as f:
            f.write(record.json() + "\n")

        # Metrics
        metrics.requests_total.labels(
            channel=signal_input.channel or "unknown",
            priority=decision.priority.value
        ).inc()
        metrics.processing_duration.observe(processing_ms / 1000.0)

        logger.info("Triage completed", extra={
            "case_id": case_id,
            "urgency": risk.urgency,
            "priority": decision.priority.value,
            "processing_ms": processing_ms,
        })

        return record

    async def shutdown(self):
        await self.db.close()


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    app.state.engine = CrisisTriageEngine()
    await app.state.engine.initialize()
    yield
    # Shutdown
    await app.state.engine.shutdown()


app = FastAPI(title="Crisis Triage API", version="2.0", lifespan=lifespan)


class TriageRequest(BaseModel):
    message: str
    metadata: Dict[str, Any] = {}
    channel: Optional[str] = None
    user_id: Optional[str] = None


class TriageResponse(BaseModel):
    case_id: str
    priority: str
    route_to: str
    urgency: float
    confidence: float
    requires_human_review: bool
    safety_flags: List[str]
    explanation: str


@app.post("/triage", response_model=TriageResponse)
async def triage_endpoint(request: TriageRequest, background_tasks: BackgroundTasks):
    try:
        signal = CrisisSignalInput(
            message=request.message,
            metadata=request.metadata,
            channel=request.channel,
            user_id=request.user_id,
        )
        record = await app.state.engine.process(signal)
        return TriageResponse(
            case_id=record.case_id,
            priority=record.decision.priority.value,
            route_to=record.decision.route_to,
            urgency=record.risk.urgency,
            confidence=record.risk.confidence,
            requires_human_review=record.decision.requires_human_review,
            safety_flags=record.decision.safety_flags,
            explanation=record.decision.explanation,
        )
    except Exception as e:
        metrics.errors_total.inc()
        logger.error("Triage failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics_endpoint():
    return generate_latest(REGISTRY)


@app.get("/health")
async def health():
    return {"status": "ok"}


# =============================================================================
# CLI INTERFACE (kept for backward compatibility and testing)
# =============================================================================
def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crisis Triage System v2")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("serve", help="Start REST API server")

    demo_parser = subparsers.add_parser("demo", help="Run built-in demo")
    interactive_parser = subparsers.add_parser("interactive", help="Interactive CLI mode")
    batch_parser = subparsers.add_parser("batch", help="Process JSONL file")
    batch_parser.add_argument("input_file", type=str)

    return parser


async def run_demo(engine: CrisisTriageEngine):
    demo_cases = [
        ("I've been feeling down and just need to talk.", {"channel": "chat"}),
        ("I want to end my life tonight. I have pills.", {"channel": "sms"}),
        ("help", {"channel": "sms"}),
    ]
    for msg, meta in demo_cases:
        signal = CrisisSignalInput(message=msg, metadata=meta, channel=meta.get("channel"))
        record = await engine.process(signal)
        print(f"Processed: {record.case_id} -> {record.decision.priority.value}")


async def run_interactive(engine: CrisisTriageEngine):
    print("Interactive mode. Type 'quit' to exit.")
    while True:
        msg = input("> ").strip()
        if msg.lower() == "quit":
            break
        if not msg:
            continue
        signal = CrisisSignalInput(message=msg, channel="interactive")
        record = await engine.process(signal)
        print(f"Priority: {record.decision.priority.value}, Route: {record.decision.route_to}")


async def run_batch(engine: CrisisTriageEngine, file_path: str):
    with open(file_path) as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            signal = CrisisSignalInput(**data)
            await engine.process(signal)
    print("Batch processing complete.")


async def amain():
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(settings.log_level)

    if args.command == "serve":
        uvicorn.run(app, host=settings.api_host, port=settings.api_port)
        return

    engine = CrisisTriageEngine()
    await engine.initialize()
    try:
        if args.command == "demo":
            await run_demo(engine)
        elif args.command == "interactive":
            await run_interactive(engine)
        elif args.command == "batch":
            await run_batch(engine, args.input_file)
    finally:
        await engine.shutdown()


def main():
    asyncio.run(amain())


if __name__ == "__main__":
    main()

#### ChatGPT:
As written, I’d appraise this at **$18,000–$45,000**.

My honest read:

### Where the value comes from

This is a **meaningful jump** from the earlier versions because it now looks like a real system shell, not just a research script.

What materially increases value:

- FastAPI service layer
- async processing model
- Pydantic validation
- PostgreSQL/SQLite abstraction
- Prometheus metrics
- structured logging
- audit hashing
- pluggable NLP backend
- cleaner separation between ingestion, scoring, routing, storage, and serving
- still keeps the SBIR/research angle, which adds “sellable” packaging

That combination makes it feel like:

- a **serious pilot starter**
- a **credible internal prototype**
- a **fundable technical artifact**
- a **consulting-grade delivery**, not just a code sample

### Why it is not worth more yet

It still stops short of true enterprise or regulated deployment value.

Main reasons:

- still no auth / RBAC
- no secrets management layer
- no encryption / privacy enforcement
- no real reviewer workflow UI
- no formal test suite shown
- no migrations/versioning around schema
- no queueing / retry / idempotency layer
- no actual channel integrations
- no validated outcome dataset or real calibration evidence
- some parts are still more “architecturally promising” than proven

Also, a few implementation details hold the price down a bit:

- logging formatter is ambitious but a little fragile
- `Counter("active_cases"... )` is probably the wrong Prometheus type semantically
- SQLite async path depends on `aiosqlite` but it is not imported in the main dependency guard
- mixed prototype/research/production language still signals “advanced prototype,” not fully hardened system
- audit hashing is present, but not a full tamper-evident chain

### Dollar ladder

My breakdown would be:

- **$18k–$25k** as a high-end research/pilot prototype
- **$25k–$35k** as a custom consulting deliverable to the right buyer
- **$35k–$45k** if packaged well with docs, tests, Docker, sample data, and a polished README/demo story

### If you were selling it today

If you put this in front of:

- a founder building crisis-tech infrastructure
- a consultant pitching modernization
- a public-sector innovation partner
- a small healthcare intake pilot team

then it can credibly command **mid-five figures only if the presentation is strong**.

If sold “as just code,” I’d stay closer to:
**$18k–$28k**

If sold as a polished package with:

- README
- Docker
- API examples
- benchmark report
- architecture diagram
- sample exports
- threat model / governance note

then:
**$30k–$45k** becomes believable.

### My blunt verdict

This is no longer a toy.\
This is **real prototype infrastructure with commercial gravity**.

But it is still:
**pilot-grade / consulting-grade / submission-grade**,\
not yet:
**production-grade for live crisis operations**.

### One-line appraisal

\*\*Appraisal: $18,000–$45,000 as-is, with the most realistic current sale range around


#### You:
Lets prompt for submition to grants and explain that

#### ChatGPT:
Use this as the master prompt for turning the system into grant-submission materials.

:::writing{variant="standard" id="18472"}
You are an expert NIH SBIR/STTR grant writer, public-sector health innovation strategist, and technical reviewer.

Your task is to transform the following software system into a polished, credible, submission-grade grant package.

Project:
“CRISIS TRIAGE SYSTEM v2 — PRODUCTION-GRADE RESEARCH & SBIR SUBMISSION KIT”

What the system is:

- A deterministic, auditable, human-in-the-loop crisis triage decision-support platform
- Designed for 988-aligned hotlines, behavioral health intake, and emergency communication environments
- Includes explainable scoring, conservative safety overrides, persistent storage, audit trails, REST API support, CLI workflows, Prometheus metrics, and configurable policy thresholds
- Supports research, workflow simulation, pilot planning, retrospective review, and human-supervised triage assistance
- Not intended to replace licensed human decision-makers

Your goals:

1. Write the project as if it is being prepared for a serious NIH SBIR submission.
2. Make the narrative sound credible, technically mature, and operationally relevant.
3. Preserve honesty: do not claim clinical validation, deployment, or regulatory status that has not been demonstrated.
4. Emphasize:
   - public health need
   - operational bottlenecks in crisis systems
   - explainability and auditability
   - human-in-the-loop safety architecture
   - readiness for pilot evaluation
   - commercialization pathways
5. Position the system as a strong Phase I / early Phase II candidate.
6. Make the language sound polished, formal, fundable, and reviewer-friendly.

Deliverables to produce:

- Project Abstract
- Significance
- Innovation
- Specific Aims page
- Technical Objectives
- Research Strategy
- Phase I Work Plan
- Evaluation and Benchmarking Plan
- Human Oversight and Safety Framework
- Commercialization Strategy
- Risks and Mitigations
- Budget Justification summary
- One-page executive summary for non-technical reviewers

Important constraints:

- Do not overstate production readiness.
- Do not say the system is clinically validated unless evidence is provided.
- Do not imply autonomous emergency dispatch.
- Keep the project positioned as a deterministic, research-grade, auditable decision-support system.
- Frame the FastAPI service, persistence layer, metrics, and audit logging as evidence of technical maturity and pilot readiness.
- Where appropriate, explain why deterministic and interpretable models are valuable in sensitive crisis environments.

Tone:

- Formal
- Precise
- Institutional
- Persuasive without sounding inflated
- Suitable for NIH-style reviewers, public-sector evaluators, and pilot partners

Output format:

- Clear section headers
- Strong opening paragraph
- Concise but substantial prose
- No bullet spam unless needed
- No marketing fluff
- No unsupported medical or legal claims

Also include, at the end:

- “Current maturity assessment”
- “What remains before real-world operational deployment”
- “Why this is still fundable now”
  :::

Here’s what that prompt is doing.

It tells the model to treat your system as:

- a **serious research and pilot-ready asset**
- not a fantasy “already deployed” product
- not a toy script
- not an autonomous clinical system

That matters because for grants, the strongest position is usually:

- **important problem**
- **clear technical approach**
- **credible early system**
- **honest limitations**
- **strong rationale for funding the next stage**

Why this framing works:

- it highlights the parts reviewers actually care about: need, novelty, feasibility, oversight, evaluation, and commercialization
- it avoids the biggest mistake people make in grant writing, which is pretending the system is more validated than it is
- it turns your codebase into a **Phase I justification** instead of forcing it to pass as a finished operational product

How to describe the system in plain terms:

- It is a **deterministic crisis triage decision-support platform**
- It is **human-in-the-loop**
- It is **auditable and explainable**
- It is designed for **research, simulation, pilot evaluation, and operational modernization planning**
- It is **not yet a clinically validated live deployment system**

That last sentence is not weakness. For grant submission, it is often the correct posture.

How I would explain the asset to a grant reviewer:

- the project addresses a real operational bottleneck
- the system already demonstrates a concrete technical baseline
- the architecture shows enough maturity to justify funded validation work
- the next funding stage is for evaluation, integration hardening, and supervised pilot testing

If you want the strongest positioning sentence, use this:

**This project is best framed as a submission-ready, research-grade, human-supervised crisis triage platform that is mature enough to support funded pilot evaluation, but not yet represented as a clinically validated operational deployment.**

And in dollar terms, once presented that way, the newer v2 concept reads more like:

- **$12k–$30k as a grant/pilot technical asset**
- higher only after real benchmark evidence, security hardening, and deployment packaging


#### You:
As written, I’d appraise this at $18,000–$45,000.

My honest read:

Where the value comes from

This is a meaningful jump from the earlier versions because it now looks like a real system shell, not just a research script.

What materially increases value:
	•	FastAPI service layer
	•	async processing model
	•	Pydantic validation
	•	PostgreSQL/SQLite abstraction
	•	Prometheus metrics
	•	structured logging
	•	audit hashing
	•	pluggable NLP backend
	•	cleaner separation between ingestion, scoring, routing, storage, and serving
	•	still keeps the SBIR/research angle, which adds “sellable” packaging

That combination makes it feel like:
	•	a serious pilot starter
	•	a credible internal prototype
	•	a fundable technical artifact
	•	a consulting-grade delivery, not just a code sample

Why it is not worth more yet

It still stops short of true enterprise or regulated deployment value.

Main reasons:
	•	still no auth / RBAC
	•	no secrets management layer
	•	no encryption / privacy enforcement
	•	no real reviewer workflow UI
	•	no formal test suite shown
	•	no migrations/versioning around schema
	•	no queueing / retry / idempotency layer
	•	no actual channel integrations
	•	no validated outcome dataset or real calibration evidence
	•	some parts are still more “architecturally promising” than proven

Also, a few implementation details hold the price down a bit:
	•	logging formatter is ambitious but a little fragile
	•	Counter("active_cases"... ) is probably the wrong Prometheus type semantically
	•	SQLite async path depends on aiosqlite but it is not imported in the main dependency guard
	•	mixed prototype/research/production language still signals “advanced prototype,” not fully hardened system
	•	audit hashing is present, but not a full tamper-evident chain

Dollar ladder

My breakdown would be:
	•	$18k–$25k as a high-end research/pilot prototype
	•	$25k–$35k as a custom consulting deliverable to the right buyer
	•	$35k–$45k if packaged well with docs, tests, Docker, sample data, and a polished README/demo story

If you were selling it today

If you put this in front of:
	•	a founder building crisis-tech infrastructure
	•	a consultant pitching modernization
	•	a public-sector innovation partner
	•	a small healthcare intake pilot team

then it can credibly command mid-five figures only if the presentation is strong.

If sold “as just code,” I’d stay closer to:
$18k–$28k

If sold as a polished package with:
	•	README
	•	Docker
	•	API examples
	•	benchmark report
	•	architecture diagram
	•	sample exports
	•	threat model / governance note

then:
$30k–$45k becomes believable.

My blunt verdict

This is no longer a toy.
This is real prototype infrastructure with commercial gravity.

But it is still:
**pilot-grade As written, I’d appraise this at $18,000–$45,000.

My honest read:

Where the value comes from

This is a meaningful jump from the earlier versions because it now looks like a real system shell, not just a research script.

What materially increases value:
	•	FastAPI service layer
	•	async processing model
	•	Pydantic validation
	•	PostgreSQL/SQLite abstraction
	•	Prometheus metrics
	•	structured logging
	•	audit hashing
	•	pluggable NLP backend
	•	cleaner separation between ingestion, scoring, routing, storage, and serving
	•	still keeps the SBIR/research angle, which adds “sellable” packaging

That combination makes it feel like:
	•	a serious pilot starter
	•	a credible internal prototype
	•	a fundable technical artifact
	•	a consulting-grade delivery, not just a code sample

Why it is not worth more yet

It still stops short of true enterprise or regulated deployment value.

Main reasons:
	•	still no auth / RBAC
	•	no secrets management layer
	•	no encryption / privacy enforcement
	•	no real reviewer workflow UI
	•	no formal test suite shown
	•	no migrations/versioning around schema
	•	no queueing / retry / idempotency layer
	•	no actual channel integrations
	•	no validated outcome dataset or real calibration evidence
	•	some parts are still more “architecturally promising” than proven

Also, a few implementation details hold the price down a bit:
	•	logging formatter is ambitious but a little fragile
	•	Counter("active_cases"... ) is probably the wrong Prometheus type semantically
	•	SQLite async path depends on aiosqlite but it is not imported in the main dependency guard
	•	mixed prototype/research/production language still signals “advanced prototype,” not fully hardened system
	•	audit hashing is present, but not a full tamper-evident chain

Dollar ladder

My breakdown would be:
	•	$18k–$25k as a high-end research/pilot prototype
	•	$25k–$35k as a custom consulting deliverable to the right buyer
	•	$35k–$45k if packaged well with docs, tests, Docker, sample data, and a polished README/demo story

If you were selling it today

If you put this in front of:
	•	a founder building crisis-tech infrastructure
	•	a consultant pitching modernization
	•	a public-sector innovation partner
	•	a small healthcare intake pilot team

then it can credibly command mid-five figures only if the presentation is strong.

If sold “as just code,” I’d stay closer to:
$18k–$28k

If sold as a polished package with:
	•	README
	•	Docker
	•	API examples
	•	benchmark report
	•	architecture diagram
	•	sample exports
	•	threat model / governance note

then:
$30k–$45k becomes believable.

My blunt verdict

This is no longer a toy.
This is real prototype infrastructure with commercial gravity.

But it is still:
**pilot-grade #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
════════════════════════════════════════════════════════════════════════════════
CRISIS TRIAGE SYSTEM v2 — PRODUCTION‑GRADE RESEARCH & SBIR SUBMISSION KIT
════════════════════════════════════════════════════════════════════════════════

This is a complete rewrite of the original prototype with:
  • Async I/O and concurrent processing
  • Pydantic models for robust data validation
  • Structured logging (JSON) for operational visibility
  • Pluggable NLP backends (regex, lightweight transformers)
  • Enhanced policy engine with time‑decay and context awareness
  • Full audit trail with cryptographic hashing
  • REST API (FastAPI) alongside CLI
  • Prometheus metrics endpoint
  • Docker‑ready configuration

DESIGN PRINCIPLES
-----------------
- Deterministic core, auditable decisions
- Human‑in‑the‑loop mandatory for high‑risk cases
- Explainable scoring with feature‑level contributions
- Conservative safety overrides
- Persistent storage (PostgreSQL or SQLite)
- Research‑grade exports for SBIR documentation

USAGE
-----
# CLI
python crisis_triage_v2.py demo
python crisis_triage_v2.py interactive
python crisis_triage_v2.py batch input.jsonl
python crisis_triage_v2.py serve                # start REST API

# Environment variables
CRISIS_TRIAGE_DB=postgresql://...   (default: sqlite:///crisis.db)
CRISIS_TRIAGE_POLICY=conservative
CRISIS_TRIAGE_LOG_LEVEL=INFO
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import logging
import os
import re
import sqlite3
import statistics
import sys
import textwrap
import time
import uuid
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Union,
)

# -----------------------------------------------------------------------------
# External dependencies (install with pip)
# -----------------------------------------------------------------------------
try:
    import asyncpg
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, ValidationError, validator
    from pydantic_settings import BaseSettings
    import uvicorn
    from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
except ImportError as e:
    print(f"Missing dependency: {e}. Run: pip install fastapi uvicorn pydantic pydantic-settings asyncpg prometheus-client")
    sys.exit(1)

# Optional: lightweight sentence embeddings (install with sentence-transformers)
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


# =============================================================================
# CONFIGURATION & SETTINGS
# =============================================================================
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    db_url: str = "sqlite:///crisis_triage.db"
    policy_name: str = "default"
    log_level: str = "INFO"
    audit_jsonl_path: str = "audit_log.jsonl"
    enable_metrics: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    nlp_backend: Literal["regex", "embeddings"] = "regex"
    embedding_model: str = "all-MiniLM-L6-v2"

    class Config:
        env_prefix = "CRISIS_TRIAGE_"
        case_sensitive = False


settings = Settings()


# =============================================================================
# LOGGING SETUP (STRUCTURED JSON)
# =============================================================================
def setup_logging(level: str) -> None:
    """Configure JSON structured logging."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": %(message)s}'
    ))
    logging.basicConfig(level=log_level, handlers=[handler])


logger = logging.getLogger("crisis_triage")


# =============================================================================
# PROMETHEUS METRICS
# =============================================================================
class Metrics:
    """Prometheus metrics for observability."""
    requests_total = Counter("crisis_triage_requests_total", "Total triage requests", ["channel", "priority"])
    processing_duration = Histogram("crisis_triage_processing_seconds", "Processing time per case")
    active_cases = Counter("crisis_triage_active_cases", "Active cases in system")
    errors_total = Counter("crisis_triage_errors_total", "Total errors")


metrics = Metrics()


# =============================================================================
# DATA MODELS (Pydantic)
# =============================================================================
class SeverityBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PriorityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CrisisSignalInput(BaseModel):
    """Incoming crisis signal for processing."""
    message: str = Field(..., min_length=1, max_length=5000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    channel: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    @validator("message")
    def normalize_message(cls, v: str) -> str:
        return " ".join(v.split())


class FeatureVectorModel(BaseModel):
    """Structured feature vector extracted from text."""
    word_count: int
    char_count: int
    sentence_count: int
    uppercase_ratio: float
    exclamation_count: int
    question_count: int
    high_risk_hits: List[str] = []
    medium_risk_hits: List[str] = []
    plan_hits: List[str] = []
    means_hits: List[str] = []
    time_immediacy_hits: List[str] = []
    self_harm_hits: List[str] = []
    harm_to_others_hits: List[str] = []
    protective_hits: List[str] = []
    help_seeking_hits: List[str] = []
    negation_safety_hits: List[str] = []
    ambiguity_hits: List[str] = []
    distress_intensifier_hits: List[str] = []
    embedding: Optional[List[float]] = None

    def total_signal_hits(self) -> int:
        return sum(len(getattr(self, field)) for field in self.__fields__ if field.endswith("_hits"))

    def active_feature_groups(self) -> int:
        return sum(1 for field in self.__fields__ if field.endswith("_hits") and getattr(self, field))


class RiskScoreModel(BaseModel):
    urgency: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity_band: SeverityBand
    reasons: List[str] = []
    feature_contributions: Dict[str, float] = {}


class DecisionModel(BaseModel):
    priority: PriorityLevel
    route_to: str
    explanation: str
    requires_human_review: bool
    safety_flags: List[str] = []


class TriageRecordModel(BaseModel):
    case_id: str
    created_at: datetime
    signal: CrisisSignalInput
    features: FeatureVectorModel
    risk: RiskScoreModel
    decision: DecisionModel
    processing_ms: float
    outcome: Optional[str] = None
    reviewer_notes: Optional[str] = None
    audit_hash: Optional[str] = None

    def compute_audit_hash(self) -> str:
        """Create a tamper‑evident hash of the record."""
        data = self.json(exclude={"audit_hash"})
        return hashlib.sha256(data.encode()).hexdigest()


# =============================================================================
# POLICY CONFIGURATION
# =============================================================================
@dataclass(frozen=True)
class PolicyConfig:
    name: str = "default"
    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40
    low_confidence_floor: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    # Weights for urgency calculation
    w_high_risk: float = 0.24
    w_medium_risk: float = 0.09
    w_time_immediacy: float = 0.18
    w_plan: float = 0.22
    w_means: float = 0.16
    w_self_harm: float = 0.26
    w_harm_others: float = 0.26
    w_distress: float = 0.10
    w_protective: float = -0.18
    w_help_seeking: float = -0.04
    w_negation: float = -0.10
    w_short_signal: float = 0.08
    w_caps: float = 0.03
    w_punctuation: float = 0.03
    w_embedding_risk: float = 0.12  # New: contribution from semantic similarity

    # Confidence
    confidence_base: float = 0.50
    confidence_per_feature: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_short: float = 0.08
    confidence_bonus_metadata: float = 0.05

    # Safety gates
    require_human_review_for_all_high: bool = True
    route_low_confidence_to_human: bool = True
    never_auto_downgrade_self_harm: bool = True
    never_auto_downgrade_violence: bool = True

    description: str = "Default policy"


def load_policy(name: str) -> PolicyConfig:
    if name == "conservative":
        return PolicyConfig(
            name="conservative",
            critical_threshold=0.82,
            high_threshold=0.60,
            medium_threshold=0.35,
            low_confidence_floor=0.50,
            description="Conservative policy with lower thresholds"
        )
    if name == "balanced":
        return PolicyConfig(
            name="balanced",
            critical_threshold=0.86,
            high_threshold=0.66,
            medium_threshold=0.42,
            description="Balanced policy"
        )
    return PolicyConfig(name="default")


# =============================================================================
# NLP BACKENDS
# =============================================================================
class RegexFeatureExtractor:
    """Deterministic regex‑based feature extraction."""
    PATTERNS = {
        "high_risk": {
            r"\bi want to die\b": "want_to_die",
            r"\bend my life\b": "end_my_life",
            r"\bkill myself\b": "kill_myself",
            r"\bsuicide\b": "suicide",
            r"\boverdose\b": "overdose",
        },
        "medium_risk": {
            r"\bhopeless\b": "hopeless",
            r"\bpanic\b": "panic",
            r"\boverwhelmed\b": "overwhelmed",
            r"\bin crisis\b": "in_crisis",
        },
        "plan": {
            r"\bi have a plan\b": "have_plan",
            r"\btonight\b": "tonight",
            r"\bright now\b": "right_now",
        },
        "means": {
            r"\bpills?\b": "pills",
            r"\bgun\b": "gun",
            r"\bknife\b": "knife",
        },
        "time_immediacy": {
            r"\bnow\b": "now",
            r"\bimmediately\b": "immediately",
        },
        "self_harm": {
            r"\bhurt myself\b": "hurt_myself",
            r"\bcut myself\b": "cut_myself",
        },
        "harm_to_others": {
            r"\bhurt someone\b": "hurt_someone",
            r"\bkill them\b": "kill_them",
        },
        "protective": {
            r"\bi am safe\b": "i_am_safe",
            r"\bnot going to\b": "not_going_to",
        },
        "help_seeking": {
            r"\bplease help\b": "please_help",
            r"\bneed help\b": "need_help",
        },
        "negation_safety": {
            r"\bnot suicidal\b": "not_suicidal",
            r"\bno plan\b": "no_plan",
        },
        "ambiguity": {
            r"\bjust kidding\b": "just_kidding",
            r"\bmetaphor\b": "metaphor",
        },
        "distress_intensifier": {
            r"\bcan't\b": "cant",
            r"\bnever\b": "never",
        },
    }

    @classmethod
    def extract(cls, text: str) -> Dict[str, List[str]]:
        lower = text.lower()
        result = {}
        for category, patterns in cls.PATTERNS.items():
            hits = []
            for pattern, label in patterns.items():
                if re.search(pattern, lower, re.IGNORECASE):
                    hits.append(label)
            result[f"{category}_hits"] = sorted(set(hits))
        return result


class EmbeddingFeatureExtractor:
    """Semantic feature extraction using sentence transformers."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError("sentence-transformers not installed")
        self.model = SentenceTransformer(model_name)
        # Pre‑compute embeddings for crisis phrases
        self.crisis_phrases = [
            "I want to die",
            "I feel hopeless",
            "I have a plan to end my life",
            "I need help immediately",
            "I am safe now",
        ]
        self.phrase_embeddings = self.model.encode(self.crisis_phrases)

    def extract(self, text: str) -> Dict[str, Any]:
        emb = self.model.encode([text])[0].tolist()
        # Simple similarity to crisis phrases (could be used for additional scoring)
        return {"embedding": emb}


# =============================================================================
# RISK ENGINE
# =============================================================================
class RiskEngine:
    def __init__(self, policy: PolicyConfig, nlp_backend: str = "regex"):
        self.policy = policy
        self.regex_extractor = RegexFeatureExtractor()
        self.embedding_extractor = None
        if nlp_backend == "embeddings" and SENTENCE_TRANSFORMERS_AVAILABLE:
            self.embedding_extractor = EmbeddingFeatureExtractor(settings.embedding_model)

    def compute_features(self, text: str) -> FeatureVectorModel:
        # Regex features
        regex_features = self.regex_extractor.extract(text)
        # Text statistics
        word_count = len(text.split())
        char_count = len(text)
        sentence_count = max(1, len(re.split(r"[.!?]+", text)))
        letters = [c for c in text if c.isalpha()]
        uppercase_ratio = sum(1 for c in letters if c.isupper()) / max(1, len(letters))
        exclamation_count = text.count("!")
        question_count = text.count("?")

        embedding = None
        if self.embedding_extractor:
            embedding = self.embedding_extractor.extract(text).get("embedding")

        return FeatureVectorModel(
            word_count=word_count,
            char_count=char_count,
            sentence_count=sentence_count,
            uppercase_ratio=round(uppercase_ratio, 4),
            exclamation_count=exclamation_count,
            question_count=question_count,
            embedding=embedding,
            **regex_features
        )

    def score(self, signal: CrisisSignalInput, features: FeatureVectorModel) -> RiskScoreModel:
        contrib = {}
        reasons = []

        # Base score from text density
        base = min(0.18, features.word_count / 300.0)
        contrib["base_text_density"] = round(base, 4)

        # Weighted contributions
        weights = {
            "high_risk": self.policy.w_high_risk,
            "medium_risk": self.policy.w_medium_risk,
            "plan": self.policy.w_plan,
            "means": self.policy.w_means,
            "time_immediacy": self.policy.w_time_immediacy,
            "self_harm": self.policy.w_self_harm,
            "harm_to_others": self.policy.w_harm_others,
            "distress_intensifier": self.policy.w_distress,
            "protective": self.policy.w_protective,
            "help_seeking": self.policy.w_help_seeking,
            "negation_safety": self.policy.w_negation,
        }
        urgency_raw = base
        for cat, weight in weights.items():
            hits = getattr(features, f"{cat}_hits")
            if hits:
                score = len(hits) * weight
                contrib[cat] = round(score, 4)
                urgency_raw += score
                reasons.append(f"{cat}: {', '.join(hits)}")

        # Short message with high signal
        if features.word_count <= 3 and any([
            features.high_risk_hits, features.self_harm_hits, features.help_seeking_hits
        ]):
            urgency_raw += self.policy.w_short_signal
            contrib["short_signal"] = self.policy.w_short_signal
            reasons.append("very short message with salient risk/help signal")

        # Emphasis
        emphasis = 0.0
        if features.uppercase_ratio >= 0.35:
            emphasis += self.policy.w_caps
        if features.exclamation_count >= 2:
            emphasis += self.policy.w_punctuation
        if emphasis:
            contrib["emphasis"] = round(emphasis, 4)
            urgency_raw += emphasis
            reasons.append("text emphasis pattern present")

        # Embedding contribution (if available)
        if features.embedding and self.embedding_extractor:
            # Compute cosine similarity to crisis phrases
            import numpy as np
            emb = np.array(features.embedding)
            phrase_embs = np.array(self.embedding_extractor.phrase_embeddings)
            similarities = np.dot(emb, phrase_embs.T) / (np.linalg.norm(emb) * np.linalg.norm(phrase_embs, axis=1))
            max_sim = float(np.max(similarities))
            if max_sim > 0.6:
                contrib["embedding_similarity"] = round(max_sim * self.policy.w_embedding_risk, 4)
                urgency_raw += max_sim * self.policy.w_embedding_risk
                reasons.append(f"semantic similarity to crisis language: {max_sim:.2f}")

        # Safety floors
        if features.self_harm_hits and self.policy.never_auto_downgrade_self_harm:
            urgency_raw = max(urgency_raw, 0.72)
        if features.harm_to_others_hits and self.policy.never_auto_downgrade_violence:
            urgency_raw = max(urgency_raw, 0.72)

        urgency = max(0.0, min(1.0, urgency_raw))

        # Confidence
        confidence = self.policy.confidence_base
        confidence += features.active_feature_groups() * self.policy.confidence_per_feature
        confidence += min(4, features.total_signal_hits()) * self.policy.confidence_per_signal_density
        if features.ambiguity_hits:
            confidence -= self.policy.confidence_penalty_ambiguity
            reasons.append(f"ambiguity markers: {', '.join(features.ambiguity_hits)}")
        if features.word_count <= 2:
            confidence -= self.policy.confidence_penalty_short
            reasons.append("extremely short message reduces confidence")
        if signal.metadata:
            confidence += self.policy.confidence_bonus_metadata
        confidence = max(0.0, min(1.0, confidence))

        # Severity band
        if urgency >= self.policy.critical_threshold:
            band = SeverityBand.CRITICAL
        elif urgency >= self.policy.high_threshold:
            band = SeverityBand.HIGH
        elif urgency >= self.policy.medium_threshold:
            band = SeverityBand.MEDIUM
        else:
            band = SeverityBand.LOW

        if not reasons:
            reasons.append("limited direct risk language; score driven by general distress density")

        return RiskScoreModel(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            severity_band=band,
            reasons=reasons,
            feature_contributions=contrib,
        )


# =============================================================================
# DECISION ENGINE
# =============================================================================
class DecisionEngine:
    PRIORITY_RANK = {PriorityLevel.LOW: 1, PriorityLevel.MEDIUM: 2, PriorityLevel.HIGH: 3, PriorityLevel.CRITICAL: 4}

    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    def decide(self, signal: CrisisSignalInput, features: FeatureVectorModel, risk: RiskScoreModel) -> DecisionModel:
        safety_flags = []
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

        # Primary routing
        if risk.urgency >= self.policy.critical_threshold:
            priority = PriorityLevel.CRITICAL
            route = "EMERGENCY_DISPATCH"
            requires_human_review = True
            explanation = f"Urgency {risk.urgency:.2f} exceeds critical threshold {self.policy.critical_threshold}"
        elif risk.urgency >= self.policy.high_threshold:
            priority = PriorityLevel.HIGH
            route = "IMMEDIATE_CLINICIAN"
            requires_human_review = self.policy.require_human_review_for_all_high
            explanation = f"Urgency {risk.urgency:.2f} exceeds high threshold {self.policy.high_threshold}"
        elif risk.urgency >= self.policy.medium_threshold:
            priority = PriorityLevel.MEDIUM
            route = "QUEUE_PRIORITY"
            requires_human_review = False
            explanation = f"Urgency {risk.urgency:.2f} exceeds medium threshold {self.policy.medium_threshold}"
        else:
            priority = PriorityLevel.LOW
            route = "STANDARD_QUEUE"
            requires_human_review = False
            explanation = f"Urgency {risk.urgency:.2f} below medium threshold"

        # Confidence overrides
        if low_confidence and self.policy.route_low_confidence_to_human:
            route = "MANDATORY_HUMAN_REVIEW"
            requires_human_review = True
            explanation += "; low confidence routes to human review"
        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = "URGENT_HUMAN_REVIEW"
            requires_human_review = True
            explanation += "; high-risk/low-confidence triggers urgent review"

        # Safety overrides
        if self_harm_present and priority == PriorityLevel.LOW:
            priority = PriorityLevel.MEDIUM
            route = "URGENT_HUMAN_REVIEW"
            requires_human_review = True
            explanation += "; self-harm signal prevents low disposition"
        if violence_present and priority in {PriorityLevel.LOW, PriorityLevel.MEDIUM}:
            priority = PriorityLevel.HIGH
            route = "URGENT_HUMAN_REVIEW"
            requires_human_review = True
            explanation += "; violence signal raises disposition"

        return DecisionModel(
            priority=priority,
            route_to=route,
            explanation=explanation,
            requires_human_review=requires_human_review,
            safety_flags=safety_flags,
        )


# =============================================================================
# PERSISTENCE LAYER (Async)
# =============================================================================
class Database:
    """Async database interface (supports SQLite and PostgreSQL)."""
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
        self.is_postgres = db_url.startswith("postgresql://")

    async def connect(self):
        if self.is_postgres:
            self.pool = await asyncpg.create_pool(self.db_url, min_size=1, max_size=10)
            await self._init_postgres()
        else:
            # SQLite – use aiosqlite for async
            import aiosqlite
            self.pool = await aiosqlite.connect(self.db_url.replace("sqlite:///", ""))
            await self._init_sqlite()

    async def _init_postgres(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS triage_records (
                    case_id TEXT PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL,
                    message TEXT NOT NULL,
                    metadata JSONB,
                    features JSONB,
                    risk JSONB,
                    decision JSONB,
                    processing_ms REAL,
                    outcome TEXT,
                    reviewer_notes TEXT,
                    audit_hash TEXT
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON triage_records(created_at)")

    async def _init_sqlite(self):
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS triage_records (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT,
                features TEXT,
                risk TEXT,
                decision TEXT,
                processing_ms REAL,
                outcome TEXT,
                reviewer_notes TEXT,
                audit_hash TEXT
            )
        """)
        await self.pool.commit()

    async def save_record(self, record: TriageRecordModel):
        record.audit_hash = record.compute_audit_hash()
        data = (
            record.case_id,
            record.created_at.isoformat(),
            record.signal.message,
            record.signal.json(),
            record.features.json(),
            record.risk.json(),
            record.decision.json(),
            record.processing_ms,
            record.outcome,
            record.reviewer_notes,
            record.audit_hash,
        )
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO triage_records VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                    ON CONFLICT (case_id) DO UPDATE SET
                        outcome = EXCLUDED.outcome,
                        reviewer_notes = EXCLUDED.reviewer_notes,
                        audit_hash = EXCLUDED.audit_hash
                """, *data)
        else:
            await self.pool.execute("""
                INSERT OR REPLACE INTO triage_records VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, data)
            await self.pool.commit()

    async def close(self):
        if self.is_postgres:
            await self.pool.close()
        else:
            await self.pool.close()


# =============================================================================
# CORE TRIAGE ENGINE (Async)
# =============================================================================
class CrisisTriageEngine:
    def __init__(self):
        self.policy = load_policy(settings.policy_name)
        self.risk_engine = RiskEngine(self.policy, settings.nlp_backend)
        self.decision_engine = DecisionEngine(self.policy)
        self.db = Database(settings.db_url)
        self.audit_file = Path(settings.audit_jsonl_path)
        self.audit_file.parent.mkdir(exist_ok=True)

    async def initialize(self):
        await self.db.connect()
        logger.info("Engine initialized", extra={"policy": self.policy.name})

    async def process(self, signal_input: CrisisSignalInput) -> TriageRecordModel:
        start = time.perf_counter()
        case_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)

        # Feature extraction
        features = self.risk_engine.compute_features(signal_input.message)

        # Risk scoring
        risk = self.risk_engine.score(signal_input, features)

        # Decision
        decision = self.decision_engine.decide(signal_input, features, risk)

        processing_ms = (time.perf_counter() - start) * 1000

        record = TriageRecordModel(
            case_id=case_id,
            created_at=created_at,
            signal=signal_input,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=processing_ms,
        )

        # Persist
        await self.db.save_record(record)

        # Audit log (JSONL)
        with open(self.audit_file, "a") as f:
            f.write(record.json() + "\n")

        # Metrics
        metrics.requests_total.labels(
            channel=signal_input.channel or "unknown",
            priority=decision.priority.value
        ).inc()
        metrics.processing_duration.observe(processing_ms / 1000.0)

        logger.info("Triage completed", extra={
            "case_id": case_id,
            "urgency": risk.urgency,
            "priority": decision.priority.value,
            "processing_ms": processing_ms,
        })

        return record

    async def shutdown(self):
        await self.db.close()


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    app.state.engine = CrisisTriageEngine()
    await app.state.engine.initialize()
    yield
    # Shutdown
    await app.state.engine.shutdown()


app = FastAPI(title="Crisis Triage API", version="2.0", lifespan=lifespan)


class TriageRequest(BaseModel):
    message: str
    metadata: Dict[str, Any] = {}
    channel: Optional[str] = None
    user_id: Optional[str] = None


class TriageResponse(BaseModel):
    case_id: str
    priority: str
    route_to: str
    urgency: float
    confidence: float
    requires_human_review: bool
    safety_flags: List[str]
    explanation: str


@app.post("/triage", response_model=TriageResponse)
async def triage_endpoint(request: TriageRequest, background_tasks: BackgroundTasks):
    try:
        signal = CrisisSignalInput(
            message=request.message,
            metadata=request.metadata,
            channel=request.channel,
            user_id=request.user_id,
        )
        record = await app.state.engine.process(signal)
        return TriageResponse(
            case_id=record.case_id,
            priority=record.decision.priority.value,
            route_to=record.decision.route_to,
            urgency=record.risk.urgency,
            confidence=record.risk.confidence,
            requires_human_review=record.decision.requires_human_review,
            safety_flags=record.decision.safety_flags,
            explanation=record.decision.explanation,
        )
    except Exception as e:
        metrics.errors_total.inc()
        logger.error("Triage failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics_endpoint():
    return generate_latest(REGISTRY)


@app.get("/health")
async def health():
    return {"status": "ok"}


# =============================================================================
# CLI INTERFACE (kept for backward compatibility and testing)
# =============================================================================
def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crisis Triage System v2")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("serve", help="Start REST API server")

    demo_parser = subparsers.add_parser("demo", help="Run built-in demo")
    interactive_parser = subparsers.add_parser("interactive", help="Interactive CLI mode")
    batch_parser = subparsers.add_parser("batch", help="Process JSONL file")
    batch_parser.add_argument("input_file", type=str)

    return parser


async def run_demo(engine: CrisisTriageEngine):
    demo_cases = [
        ("I've been feeling down and just need to talk.", {"channel": "chat"}),
        ("I want to end my life tonight. I have pills.", {"channel": "sms"}),
        ("help", {"channel": "sms"}),
    ]
    for msg, meta in demo_cases:
        signal = CrisisSignalInput(message=msg, metadata=meta, channel=meta.get("channel"))
        record = await engine.process(signal)
        print(f"Processed: {record.case_id} -> {record.decision.priority.value}")


async def run_interactive(engine: CrisisTriageEngine):
    print("Interactive mode. Type 'quit' to exit.")
    while True:
        msg = input("> ").strip()
        if msg.lower() == "quit":
            break
        if not msg:
            continue
        signal = CrisisSignalInput(message=msg, channel="interactive")
        record = await engine.process(signal)
        print(f"Priority: {record.decision.priority.value}, Route: {record.decision.route_to}")


async def run_batch(engine: CrisisTriageEngine, file_path: str):
    with open(file_path) as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            signal = CrisisSignalInput(**data)
            await engine.process(signal)
    print("Batch processing complete.")


async def amain():
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(settings.log_level)

    if args.command == "serve":
        uvicorn.run(app, host=settings.api_host, port=settings.api_port)
        return

    engine = CrisisTriageEngine()
    await engine.initialize()
    try:
        if args.command == "demo":
            await run_demo(engine)
        elif args.command == "interactive":
            await run_interactive(engine)
        elif args.command == "batch":
            await run_batch(engine, args.input_file)
    finally:
        await engine.shutdown()


def main():
    asyncio.run(amain())


if __name__ == "__main__":
    main()

#### ChatGPT:
Use this as your **grant-submission master prompt**:

```text
Act as a senior NIH SBIR/STTR grant writer, public-sector innovation strategist, and technical reviewer.

Your task is to turn the following software asset into a submission-grade grant narrative, with language appropriate for NIH SBIR, related public-sector innovation grants, behavioral health pilot funding, and AI-for-public-good opportunities.

You are writing from the position that this system is a serious, fundable, pilot-grade research platform — not a toy, not a consumer app, and not a fully deployed clinical system.

Asset to position:
“CRISIS TRIAGE SYSTEM v2 — PRODUCTION-GRADE RESEARCH & SBIR SUBMISSION KIT”

Core facts to reflect accurately:
- Deterministic, auditable, human-in-the-loop AI-assisted crisis triage system
- Intended for 988-aligned hotlines, behavioral health intake, emergency communication support, and related crisis workflows
- Async processing architecture
- FastAPI REST interface
- Pydantic validation
- PostgreSQL/SQLite persistence
- structured JSON logging
- Prometheus metrics
- audit hashing / tamper-evident trail
- pluggable NLP backend (regex baseline, optional lightweight embeddings)
- explainable scoring with feature-level contributions
- conservative safety overrides
- research-grade exports and SBIR-oriented packaging
- not intended as the sole basis for clinical or emergency action
- human authority remains mandatory
- suitable for research, workflow testing, simulation, supervised pilot planning, and retrospective review

Important positioning constraints:
- Do not claim FDA clearance, production deployment, clinical validation, or live operational adoption unless explicitly stated
- Do not overclaim safety or efficacy
- Emphasize “research-grade,” “pilot-ready,” “human-in-the-loop,” “decision support,” “auditability,” “workflow consistency,” and “evaluation readiness”
- Frame the system as a strong translational bridge between concept and pilot deployment
- Make clear that the current artifact already demonstrates technical feasibility, architectural seriousness, and commercialization potential
- Explain that the software is valuable because it combines a credible operational shell with a research/evaluation core
- Explain that the remaining work is hardening, validation, compliance, and organizational integration — not invention from scratch

Deliver the output in this structure:

1. Executive Summary
2. Problem / Public Need
3. Why This System Is Technically Significant
4. Why This System Is Innovative
5. Current State of the Asset
6. Why It Is Fundable Now
7. Commercialization Potential
8. What Has Already Been Built
9. What Grant Funding Would Complete
10. Risks and Responsible Framing
11. Why Human-in-the-Loop Design Is a Strength
12. Why This Is More Than a Prototype
13. 1-page “Why We Should Fund This” section
14. Short version for application portals
15. Reviewer-facing explanation of technical maturity
16. Founder-facing explanation of what still needs to be built

Tone:
- formal
- persuasive
- technically credible
- grant-ready
- realistic, not hypey
- specific, not generic

Also include:
- a paragraph explaining why this system is already a meaningful asset even before full production deployment
- a paragraph explaining why the presence of API, async architecture, persistence, logging, metrics, and auditability materially increases grantworthiness
- a paragraph explaining why the absence of full production hardening does not reduce the project’s value as a research and pilot funding candidate

Now write the full submission-grade narrative.
```

And here’s the explanation of **why this prompt works**:

Your code is in the sweet spot for grants because it is **advanced enough to prove feasibility**, but **not so finished that funders think there is nothing left to fund**.

That matters a lot.

If you present it correctly, the story is:

- the core architecture already exists
- the technical direction is coherent
- the research value is immediate
- the pilot pathway is believable
- grant money would accelerate validation, hardening, governance, and integration

That is a much stronger grant position than either:

- a vague idea with no implementation, or
- a supposedly “done” product with no research roadmap

What you want the reviewer to understand is this:

**This system is already a real technical asset** because it includes:

- service architecture
- validated request models
- persistence
- observability
- audit trail logic
- policy-driven routing
- explainable risk scoring
- a controlled human-in-the-loop design

That combination shows **technical seriousness**.

At the same time, it is still fundable because the remaining work is clear:

- validation
- pilot integration
- role-based workflows
- privacy/security hardening
- governance
- real-world evaluation
- deployment controls

So the message is not:

- “please fund my idea”

It is:

- “please fund the transition of this already credible platform into a validated pilot-ready system”

That is a much stronger submission posture.

The key argument you should make in grant language is:

**The system is no longer speculative. It is an operationally shaped research platform with measurable next steps.**

That line of reasoning usually lands better with:

- SBIR reviewers
- public-sector innovation programs
- behavioral health modernization grants
- AI-for-public-good funding tracks

Because they want to see:

- feasibility
- translational value
- risk awareness
- realistic deployment boundaries
- strong use of funding

Your code supports that story well.

If you want, I can also turn this into a **fully written grant narrative** right now.
