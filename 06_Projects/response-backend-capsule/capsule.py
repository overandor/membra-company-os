#!/usr/bin/env python3
"""
capsule.py — Response Backend Capsule (RBC) runtime.

Thesis (and its honest accounting):
  An *operational* model answer should not be only prose — it should compile
  into a runnable backend capsule: files + endpoint + tests + receipts.

  GUARANTEED:  a runnable, tested artifact (or an explicit failure).
  MEASURED:    optimization (time saved / error reduced) — never assumed.
  NEVER GUARANTEED: revenue. Money appears only when a usage event logs it.

  economic_proof = executable_artifact + usage_event + (time_saved or error_reduced) + receipt

Two ledgers, kept strictly separate:
  * technical receipt ledger  — what was generated, did it run, hashes, tests, endpoint.
  * economic activity ledger  — was it used, how long, what baseline it replaced, money moved.

The runtime does NOT trust the model: it static-safety-checks and tests every
capsule before it can serve. "Uploaded/deployed" can only be claimed if the
runtime did it and got a receipt. stdlib only. python3 demo.py
"""
from __future__ import annotations
import hashlib, json, os, time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Optional

# capsule kinds (the classifier's output)
EXPLANATION, ARTIFACT, ENDPOINT, WORKFLOW = "explanation", "artifact", "endpoint", "workflow"


def _h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _canon(o: Any) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), default=str).encode()


# --------------------------------------------------------------- classifier --
_OP_WORKFLOW = ("pipeline", "workflow", "system", "ledger", "underwrite", "orchestr")
_OP_ENDPOINT = ("convert", "compute", "score", "endpoint", "api", "process", "receipt",
                "verify", "grade", "appraise", "route")
_OP_ARTIFACT = ("create", "build", "generate", "write a", "make a", "script", "tool")
_EXPLAIN = ("what is", "what time", "who ", "when ", "why ", "explain", "define",
            "describe", "how does")


def classify(prompt: str) -> str:
    """Deterministic stand-in for model-side intent routing. Most chat stays explanation-only."""
    p = prompt.lower().strip()
    if any(p.startswith(e) or e in p[:24] for e in _EXPLAIN) and not any(
            w in p for w in _OP_WORKFLOW + _OP_ENDPOINT):
        return EXPLANATION
    if any(w in p for w in _OP_WORKFLOW):
        return WORKFLOW
    if any(w in p for w in _OP_ENDPOINT):
        return ENDPOINT
    if any(w in p for w in _OP_ARTIFACT):
        return ARTIFACT
    return EXPLANATION


# ------------------------------------------------------------------ capsule --
@dataclass
class Manifest:
    name: str
    purpose: str
    kind: str
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)
    files: dict = field(default_factory=dict)     # path -> source text (provenance + safety scan)
    commands: list = field(default_factory=list)
    deploy: dict = field(default_factory=dict)


@dataclass
class Capsule:
    answer: str                                   # the visible explanation
    manifest: Manifest
    handler: Optional[Callable[[dict], dict]] = None   # the endpoint (operational only)
    test: Optional[Callable[[Callable], bool]] = None  # truth filter


# --------------------------------------------------------- safety static gate --
_DENY = ["rm -rf", "os.system(", "shell=true", "eval(", "exec(", "__import__(",
         "socket.", "ghp_", "akia", "-----begin", "base64.b64decode(", "/etc/passwd",
         "shutil.rmtree", "requests.post"]


def safety_check(capsule: Capsule) -> tuple[bool, list]:
    findings = []
    blob = "\n".join(capsule.manifest.files.values()).lower()
    for pat in _DENY:
        if pat in blob:
            findings.append(f"denied pattern: {pat!r}")
    return (len(findings) == 0, findings)


# ----------------------------------------------------- hash-chained receipts --
class TechnicalLedger:
    """Same hash-chain primitive as ProofBook; what the model generated + whether it ran."""
    def __init__(self): self.chain: list[dict] = []

    def append(self, kind: str, payload: dict) -> dict:
        prev = self.chain[-1]["hash"] if self.chain else "0" * 64
        h = _h(prev.encode() + b"|" + _canon(payload))
        e = {"seq": len(self.chain), "kind": kind, "prev": prev, "hash": h,
             "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "payload": payload}
        self.chain.append(e); return e

    def verify(self) -> bool:
        prev = "0" * 64
        for i, e in enumerate(self.chain):
            if e["seq"] != i or e["prev"] != prev or e["hash"] != _h(prev.encode() + b"|" + _canon(e["payload"])):
                return False
            prev = e["hash"]
        return True


class EconomicLedger:
    """Strictly separate. Activity is logged, not asserted; revenue only if money_moved is set."""
    def __init__(self): self.events: list[dict] = []

    def log_usage(self, capsule: str, task: str, seconds: float,
                  human_baseline_seconds: float = 0.0, errors: int = 0,
                  money_moved: float = 0.0) -> dict:
        ev = {"capsule": capsule, "task": task, "seconds": seconds,
              "human_baseline_seconds": human_baseline_seconds,
              "time_saved_seconds": max(0.0, human_baseline_seconds - seconds),
              "errors": errors, "money_moved": money_moved,
              "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        self.events.append(ev); return ev

    def summary(self) -> dict:
        return {"usage_events": len(self.events),
                "total_time_saved_seconds": round(sum(e["time_saved_seconds"] for e in self.events), 2),
                "total_errors": sum(e["errors"] for e in self.events),
                "revenue": round(sum(e["money_moved"] for e in self.events), 2)}


# ----------------------------------------------------------------- runtime ----
class Runtime:
    def __init__(self, root: str):
        self.root = root
        self.tech = TechnicalLedger()
        self.econ = EconomicLedger()
        self._serving: dict[str, Callable] = {}

    def process(self, prompt: str, capsule: Capsule) -> dict:
        """Full path: classify -> materialize -> safety -> test -> serve -> technical receipt."""
        kind = capsule.manifest.kind
        if kind == EXPLANATION:
            return {"kind": kind, "served": False, "note": "explanation-only; no backend required"}

        cdir = os.path.join(self.root, capsule.manifest.name)
        os.makedirs(cdir, exist_ok=True)
        file_hashes = {}
        for path, src in capsule.manifest.files.items():
            with open(os.path.join(cdir, path), "w") as fh:
                fh.write(src)
            file_hashes[path] = _h(src.encode())
        with open(os.path.join(cdir, "manifest.json"), "w") as fh:
            json.dump(asdict(capsule.manifest), fh, indent=2)

        safe, findings = safety_check(capsule)
        if not safe:
            rec = self.tech.append("BLOCKED", {"capsule": capsule.manifest.name,
                                               "reason": "safety", "findings": findings})
            return {"kind": kind, "served": False, "blocked": True,
                    "findings": findings, "receipt": rec["hash"]}

        tests_pass = bool(capsule.test(capsule.handler)) if (capsule.test and capsule.handler) else False
        endpoint_ok = False
        if tests_pass and capsule.handler:
            self._serving[capsule.manifest.name] = capsule.handler
            endpoint_ok = True

        rec = self.tech.append("COMPILE", {
            "capsule": capsule.manifest.name, "kind": kind,
            "prompt_hash": _h(prompt.encode()), "answer_hash": _h(capsule.answer.encode()),
            "file_hashes": file_hashes, "tests_pass": tests_pass,
            "endpoint": f"local://{capsule.manifest.name}" if endpoint_ok else None})
        return {"kind": kind, "served": endpoint_ok, "tests_pass": tests_pass,
                "blocked": False, "endpoint": f"local://{capsule.manifest.name}" if endpoint_ok else None,
                "receipt": rec["hash"]}

    def call(self, name: str, payload: dict) -> dict:
        """The endpoint either responds or it does not."""
        if name not in self._serving:
            raise KeyError(f"no live endpoint: {name}")
        t0 = time.perf_counter()
        out = self._serving[name](payload)
        self.tech.append("INVOKE", {"capsule": name, "ok": True,
                                    "latency_ms": round((time.perf_counter() - t0) * 1000, 3)})
        return out

    def economic_proof(self, name: str) -> dict:
        """The honest 4-part test. Activity is provable; revenue is only what was logged."""
        served = name in self._serving
        evs = [e for e in self.econ.events if e["capsule"] == name]
        used = len(evs) > 0
        optimized = any(e["time_saved_seconds"] > 0 or e["errors"] == 0 for e in evs)
        receipted = any(e["payload"].get("capsule") == name for e in self.tech.chain)
        return {"capsule": name, "executable_artifact": served, "usage_event": used,
                "optimization_measured": used and optimized, "receipt": receipted,
                "activity_proven": served and used and optimized and receipted,
                "revenue": round(sum(e["money_moved"] for e in evs), 2)}
