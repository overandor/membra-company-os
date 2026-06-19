#!/usr/bin/env python3
"""
Repo Underwriting Pipeline
==========================

Turns a GitHub subject (account + body of work) into a collateral-grade
underwriting decision, the way a lender would:

    intake -> collect -> value -> benchmark -> risk -> eligibility -> decide -> memo

Deterministic given inputs + config. Run:

    python underwrite.py --input sample_input_overandor.json --out out/

Inputs are a JSON metrics file (see sample_input_overandor.json). A `collect`
stage for live GitHub/local-git data is stubbed with the exact queries to run
so the numbers are reproducible by a third party ("receipts").
"""
from __future__ import annotations
import argparse, json, math, datetime, os, statistics
from dataclasses import dataclass, field, asdict
from typing import Any

import config as C


# ----------------------------------------------------------------- helpers ----
def _cocomo_pm(kloc: float) -> float:
    return C.VALUATION["cocomo_a"] * (kloc ** C.VALUATION["cocomo_b"])


def _age_months(created: str, as_of: str) -> float:
    d0 = datetime.date.fromisoformat(created[:10])
    d1 = datetime.date.fromisoformat(as_of[:10])
    return max((d1 - d0).days, 1) / 30.44


# --------------------------------------------------------------- valuation ----
def value(m: dict) -> dict:
    v = C.VALUATION
    code, comm = m["code"], m["commercial"]
    sloc = code["portfolio_sloc"]
    unique_kloc = sloc * code.get("dedup_factor", v["dedup_default"]) / 1000.0

    # 1. replacement (COCOMO, conservative, heavily haircut)
    gross = _cocomo_pm(unique_kloc) * v["cocomo_rate_per_pm"]
    m1 = gross * v["replacement_net_multiplier"]

    # 2. functional bill-of-materials
    bom = (code["deployable_units"] * v["bom_deployable_unit"]
           + code.get("platforms", 0) * v["bom_platform_unit"]
           + code.get("experiments", 0) * v["bom_experiment_unit"])
    m2 = bom * v["bom_haircut"]

    # 3. quality-adjusted (only tested+deployable counts as asset)
    m3 = (code["deployable_units"] * v["quality_tested_unit"]
          + m["portfolio"]["public_repos"] * v["quality_scrap_per_repo"]) * v["quality_haircut"]

    # 4. embodied-cost floor
    months = _age_months(m["subject"]["account_created"], m["subject"]["as_of"])
    m4 = months * v["embodied_monthly"] + v["embodied_ai_tooling"]

    # 5. income approach
    arr = comm.get("recurring_revenue_usd", 0) or 0
    m5 = arr * v["income_arr_multiple"] if arr > 0 else v["income_option_value"]

    methods = {"replacement": m1, "functional_bom": m2, "quality_adjusted": m3,
               "embodied_cost": m4, "income": m5}
    nets = sorted(methods.values())
    central = statistics.mean(nets[1:-1]) if len(nets) >= 3 else statistics.mean(nets)
    return {
        "methods_usd": {k: round(v_) for k, v_ in methods.items()},
        "gross_replacement_ceiling_usd": round(gross),
        "central_net_realizable_usd": round(central),
        "supported_range_usd": [round(min(nets)), round(max(nets[:-1]) if len(nets) > 1 else max(nets))],
        "unique_kloc": round(unique_kloc),
        "tenure_months": round(months, 1),
    }


# --------------------------------------------------------------- benchmark ----
def benchmark(m: dict) -> dict:
    pop = C.GITHUB_POPULATION
    repos = m["portfolio"]["public_repos"]
    fol = m["portfolio"]["followers"]

    # largest measured threshold <= subject value gives ~users strictly above subject
    thr = max([t for t in pop["repos_gt"] if t <= repos], default=None)
    above_repos = pop["repos_gt"][thr] if thr is not None else pop["users_with_repo"]
    fol_thr = max([t for t in pop["followers_gt"] if t <= fol], default=None)
    above_fol = pop["followers_gt"][fol_thr] if fol_thr is not None else pop["users_with_repo"]

    tot = pop["total_users"]
    repo_pct_top = above_repos / tot * 100
    fol_pct_top = above_fol / tot * 100
    return {
        "repo_rank_approx": above_repos + 1,
        "repo_top_percent_all": round(repo_pct_top, 4),
        "repo_top_percent_repo_havers": round(above_repos / pop["users_with_repo"] * 100, 3),
        "follower_top_percent_all": round(fol_pct_top, 3),
        "claim": (f"top {repo_pct_top:.3f}% of {tot:,} GitHub users by public-repository "
                  f"output (~#{above_repos + 1:,}); built in {value(m)['tenure_months']:.0f} months"),
    }


# ------------------------------------------------------------------- risk ------
def risk_score(m: dict) -> dict:
    code, comm = m["code"], m["commercial"]
    cov = code["test_functions"] / max(code["implemented_defs"], 1)
    f = {
        "no_recurring_revenue": 1.0 if (comm.get("recurring_revenue_usd", 0) or 0) == 0 else 0.2,
        "ip_not_entity_owned": 0.0 if comm.get("ip_assigned_entity") else 1.0,
        "illiquid_market": 1.0,  # private software IP is inherently illiquid
        "key_person_single_author": 1.0 if m["portfolio"].get("primary_authors", 1) <= 1 else 0.4,
        "low_test_coverage": max(0.0, 1.0 - min(1.0, cov / C.TEST_COVERAGE_TARGET)),
        "security_hygiene": 0.5 if comm.get("secrets_remediated") else 1.0,
        "duplication_concentration": 1.0 - code.get("dedup_factor", C.VALUATION["dedup_default"]),
        "weak_deployability": 0.3 if code["deployable_units"] >= 5 else 0.8,
    }
    score = sum(f[k] * C.RISK_WEIGHTS[k] for k in C.RISK_WEIGHTS)
    grade = next(g for cap, g in C.RISK_GRADE_BANDS if score <= cap)
    return {"score": round(score, 3), "grade": grade, "factors": {k: round(v, 2) for k, v in f.items()}}


# ------------------------------------------------------------- eligibility -----
def eligibility(val: dict, risk: dict) -> dict:
    eligible = val["central_net_realizable_usd"] * C.VALUATION["eligible_exclusion"]
    rate = C.ADVANCE_RATE[risk["grade"]]
    base = eligible * rate
    return {
        "eligible_collateral_usd": round(eligible),
        "advance_rate": rate,
        "borrowing_base_usd": round(base),
    }


# -------------------------------------------------------- conditions/scenario --
def with_conditions(m: dict) -> dict:
    """Recompute as if conditions precedent were met (IP assigned, modest revenue)."""
    m2 = json.loads(json.dumps(m))
    m2["commercial"]["ip_assigned_entity"] = True
    if (m2["commercial"].get("recurring_revenue_usd", 0) or 0) == 0:
        m2["commercial"]["recurring_revenue_usd"] = 100_000  # illustrative first ARR
    v, r = value(m2), risk_score(m2)
    e = eligibility(v, r)
    return {"value": v, "risk": r, "eligibility": e}


# ---------------------------------------------------------------- decide -------
def decide(val, bench, risk, elig) -> dict:
    base = elig["borrowing_base_usd"]
    rules = C.DECISION_RULES
    if base < rules["min_borrowing_base_to_offer"]:
        outcome = "DECLINE (insufficient borrowing base on as-is basis)"
    elif risk["grade"] in rules["grades_requiring_conditions"]:
        outcome = "APPROVE — WITH CONDITIONS PRECEDENT"
    else:
        outcome = "APPROVE"
    conditions = [
        "Assign all IP to a borrowable entity (e.g., Membra LLC/C-corp).",
        "Obtain a licensed third-party appraisal citing this methodology.",
        "Complete security remediation: rotate/scrub any historical secrets from git history.",
        "Provide revenue/usage evidence to unlock ARR-multiple advance terms.",
        "Consolidate duplicated variant projects to raise the unique-SLOC (dedup) factor.",
    ]
    covenants = [
        "No hardcoded secrets committed; CI secret-scan must stay green.",
        "Maintain test + deploy CI on the pledged repositories.",
        "Quarterly re-underwrite; borrowing base recalculated on revenue and code metrics.",
    ]
    return {"outcome": outcome, "conditions_precedent": conditions, "covenants": covenants}


# ----------------------------------------------------------------- render ------
def render_memo(m, val, bench, risk, elig, dec, scenario) -> str:
    s = m["subject"]
    L = []
    L.append(f"# Underwriting Memo — {s.get('name', s['login'])} (@{s['login']})")
    L.append(f"\n**Effective:** {s['as_of']} · **Subject:** body of work across "
             f"{m['portfolio']['public_repos']} public repos · **Pipeline:** repo-underwriting v1")
    L.append("\n> Model-based credit screen, **not** a certified appraisal, audit, or commitment "
             "to lend. Advance terms are illustrative; a lender sets its own value and rate.\n")
    L.append("## Decision")
    L.append(f"**{dec['outcome']}**  ·  Risk grade **{risk['grade']}** (score {risk['score']})  ·  "
             f"Borrowing base **${elig['borrowing_base_usd']:,}** "
             f"(advance {int(elig['advance_rate']*100)}% on ${elig['eligible_collateral_usd']:,} eligible)")
    L.append("\n## 1. Valuation (conclusion of value)")
    L.append(f"- **Central net realizable:** ${val['central_net_realizable_usd']:,} "
             f"(range ${val['supported_range_usd'][0]:,}–${val['supported_range_usd'][1]:,})")
    L.append(f"- Gross replacement ceiling (context): ${val['gross_replacement_ceiling_usd']:,}")
    L.append("- Methods: " + ", ".join(f"{k} ${v:,}" for k, v in val["methods_usd"].items()))
    L.append("\n## 2. Benchmark / rank claim")
    L.append(f"- **{bench['claim']}**")
    L.append(f"- Repo rank ≈ #{bench['repo_rank_approx']:,} · top {bench['repo_top_percent_all']}% of all "
             f"users · top {bench['follower_top_percent_all']}% by followers")
    L.append("\n## 3. Risk profile")
    for k, vv in risk["factors"].items():
        L.append(f"  - {k}: {vv}")
    L.append("\n## 4. Conditions precedent (to fund / improve terms)")
    L.extend(f"  {i+1}. {c}" for i, c in enumerate(dec["conditions_precedent"]))
    L.append("\n## 5. Covenants")
    L.extend(f"  - {c}" for c in dec["covenants"])
    L.append("\n## 6. Scenario — conditions met (IP assigned + first $100k ARR)")
    sv, sr, se = scenario["value"], scenario["risk"], scenario["eligibility"]
    L.append(f"- Risk grade **{sr['grade']}** (score {sr['score']}), advance {int(se['advance_rate']*100)}%")
    L.append(f"- Borrowing base rises to **${se['borrowing_base_usd']:,}** "
             f"(central value ${sv['central_net_realizable_usd']:,})")
    L.append(f"- Δ borrowing base: **+${se['borrowing_base_usd']-elig['borrowing_base_usd']:,}** "
             "— the revenue + IP-assignment lever, quantified.")
    L.append("\n## 7. Receipts (reproduce the benchmark)")
    L.append("```")
    L.append("GET api.github.com/search/users?q=repos:>175+type:user        -> users above you on repos")
    L.append("GET api.github.com/search/users?q=followers:>4+type:user       -> users above you on followers")
    L.append("GET api.github.com/search/users?q=followers:>=0+type:user      -> total user population")
    L.append("```")
    L.append("\n*Generated by repo-underwriting-pipeline. Estimates only; not financial advice.*")
    return "\n".join(L)


# ------------------------------------------------------------------ main -------
def run(metrics: dict) -> dict:
    val = value(metrics)
    bench = benchmark(metrics)
    risk = risk_score(metrics)
    elig = eligibility(val, risk)
    dec = decide(val, bench, risk, elig)
    scen = with_conditions(metrics)
    memo = render_memo(metrics, val, bench, risk, elig, dec, scen)
    return {"valuation": val, "benchmark": bench, "risk": risk, "eligibility": elig,
            "decision": dec, "scenario_conditions_met": scen, "memo_markdown": memo}


def main() -> None:
    ap = argparse.ArgumentParser(description="Repo underwriting pipeline")
    ap.add_argument("--input", required=True, help="metrics JSON path")
    ap.add_argument("--out", default="out", help="output directory")
    a = ap.parse_args()
    with open(a.input) as fh:
        metrics = json.load(fh)
    result = run(metrics)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "decision.json"), "w") as fh:
        json.dump({k: v for k, v in result.items() if k != "memo_markdown"}, fh, indent=2)
    with open(os.path.join(a.out, "underwriting_memo.md"), "w") as fh:
        fh.write(result["memo_markdown"])
    d, e = result["decision"], result["eligibility"]
    print(f"{d['outcome']}  | grade {result['risk']['grade']}  | "
          f"borrowing base ${e['borrowing_base_usd']:,}")
    print(f"wrote {a.out}/underwriting_memo.md and {a.out}/decision.json")


if __name__ == "__main__":
    main()
