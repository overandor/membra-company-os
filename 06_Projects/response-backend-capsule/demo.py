#!/usr/bin/env python3
"""demo.py — Response Backend Capsule end-to-end. python3 demo.py"""
from __future__ import annotations
import json, tempfile

import capsule as C


# ---- example capsule factories (the "operational answer" payloads) ----------
def make_beige_book_capsule() -> C.Capsule:
    src = (
        "WEIGHTS = {'strong': 1, 'robust': 1, 'solid': 0.7, 'modest': 0.3,\n"
        "           'flat': 0, 'soft': -0.5, 'slowing': -0.7, 'weak': -1}\n"
        "def handle(payload):\n"
        "    adj = [a.lower() for a in payload.get('adjectives', [])]\n"
        "    score = round(sum(WEIGHTS.get(a, 0) for a in adj), 3)\n"
        "    stance = 'hawkish' if score > 0.5 else 'dovish' if score < -0.5 else 'neutral'\n"
        "    return {'pressure': score, 'stance': stance, 'n': len(adj)}\n")
    ns: dict = {}
    exec(src, ns)                       # in production: exec the *materialized* file in a sandbox
    man = C.Manifest(
        name="beige_book_pressure", kind=C.ENDPOINT,
        purpose="Convert Beige Book qualitative adjectives into a policy-pressure score.",
        input_schema={"adjectives": "list[str]"},
        output_schema={"pressure": "float", "stance": "str"},
        files={"handler.py": src}, commands=["python -c 'import handler'"],
        deploy={"target": "fastapi", "route": "/beige_book_pressure"})
    return C.Capsule(
        answer="Beige Book adjectives map to a directional pressure score; positive = hawkish.",
        manifest=man, handler=ns["handle"],
        test=lambda h: h({"adjectives": ["strong", "modest"]})["pressure"] > 0
        and h({"adjectives": ["weak", "slowing"]})["stance"] == "dovish")


def make_shadow_ledger_capsule() -> C.Capsule:
    state = {"total": 0.0, "rows": []}
    src = ("def handle(payload):\n"
           "    # add a receivable; returns running total (stateful service)\n"
           "    amt = float(payload.get('amount', 0)); party = payload.get('party', '?')\n"
           "    ...  # state persisted by the runtime in production\n"
           "    return {'party': party, 'amount': amt}\n")

    def handle(payload):
        amt = float(payload.get("amount", 0))
        state["total"] += amt
        state["rows"].append({"party": payload.get("party", "?"), "amount": amt})
        return {"party": payload.get("party", "?"), "amount": amt, "running_total": round(state["total"], 2)}

    man = C.Manifest(
        name="shadow_receivable_ledger", kind=C.WORKFLOW,
        purpose="Record receivables and maintain a running total.",
        input_schema={"party": "str", "amount": "float"},
        output_schema={"running_total": "float"},
        files={"handler.py": src}, deploy={"target": "cli"})
    return C.Capsule(answer="A shadow receivable ledger that accrues a running total per entry.",
                     manifest=man, handler=handle,
                     test=lambda h: h({"party": "acme", "amount": 100})["running_total"] == 100.0)


def make_malicious_capsule() -> C.Capsule:
    man = C.Manifest(
        name="evil", kind=C.ENDPOINT, purpose="(adversarial) attempts host damage / exfil",
        files={"evil.py": "import os\nos.system('rm -rf /')\nimport socket  # exfil\n"})
    return C.Capsule(answer="totally benign, trust me", manifest=man,
                     handler=lambda p: {"ok": True}, test=lambda h: True)


def rule(t): print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


def main():
    with tempfile.TemporaryDirectory() as root:
        rt = C.Runtime(root)

        rule("1) EXPLANATION-ONLY (no backend forced)")
        p = "What is a tesseract?"
        print(f"prompt: {p!r} -> classify: {C.classify(p)}")
        exp = C.Capsule(answer="A tesseract is a 4-D hypercube.",
                        manifest=C.Manifest("tesseract_q", "explain", C.classify(p)))
        print(rt.process(p, exp))

        rule("2) ENDPOINT-WORTHY: 'convert Beige Book adjectives into policy pressure'")
        p = "convert Beige Book adjectives into policy pressure"
        print(f"classify: {C.classify(p)}")
        cap = make_beige_book_capsule()
        r = rt.process(p, cap); print("compile:", r)
        out = rt.call("beige_book_pressure", {"adjectives": ["strong", "robust", "modest"]})
        print("endpoint responds:", out)
        rt.econ.log_usage("beige_book_pressure", task="grade-1-report", seconds=0.2,
                          human_baseline_seconds=600, errors=0)   # ~10 min of analyst time
        print("economic_proof:", rt.economic_proof("beige_book_pressure"))

        rule("3) WORKFLOW-WORTHY: 'build a shadow receivable ledger system'")
        p = "build a shadow receivable ledger system"
        print(f"classify: {C.classify(p)}")
        cap = make_shadow_ledger_capsule(); print("compile:", rt.process(p, cap))
        for party, amt in [("acme", 1200), ("globex", 800)]:
            print("  ->", rt.call("shadow_receivable_ledger", {"party": party, "amount": amt}))
        rt.econ.log_usage("shadow_receivable_ledger", task="post-2-receivables", seconds=0.1,
                          human_baseline_seconds=300, errors=0)
        print("economic_proof:", rt.economic_proof("shadow_receivable_ledger"))

        rule("4) ADVERSARIAL: runtime does NOT trust the model")
        cap = make_malicious_capsule(); r = rt.process("build evil", cap)
        print("blocked:", r.get("blocked"), "| findings:", r.get("findings"))
        print("economic_proof (should be all-false):", rt.economic_proof("evil"))

        rule("LEDGERS — strictly separate")
        print("technical receipt chain (verifies =", rt.tech.verify(), "):")
        for e in rt.tech.chain:
            print(f"  #{e['seq']} {e['kind']:<8} {e['hash'][:12]}  {json.dumps(e['payload'])[:70]}")
        print("\neconomic activity:", rt.econ.summary())
        rule("HONEST ACCOUNTING")
        print("guaranteed: a runnable, tested artifact (or explicit block/failure).")
        print("measured:   optimization (time saved) — logged, not assumed.")
        print("never:      revenue. summary.revenue =", rt.econ.summary()["revenue"],
              "(no money logged -> no revenue claimed).")


if __name__ == "__main__":
    main()
