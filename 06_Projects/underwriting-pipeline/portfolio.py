#!/usr/bin/env python3
"""
portfolio.py — underwrite a whole portfolio of repos and roll up a borrowing base.

For each repo: coarse metrics -> value -> risk -> eligibility -> decision, then
hash the decision into ProofBook. Rolls up total eligible collateral, total
borrowing base, grade distribution, and the top contributors.

    python portfolio.py --repos sample_portfolio.json --out out
"""
from __future__ import annotations
import argparse, collections, json, os

import underwrite as U
import collect as COL
from proofbook import ProofBook


def underwrite_portfolio(repos: list[dict], pb: ProofBook,
                         local_overrides: dict | None = None) -> dict:
    """local_overrides: {repo_name: checkout_path} -> use precise local-git metrics."""
    local_overrides = local_overrides or {}
    rows, grades = [], collections.Counter()
    tot_central = tot_eligible = tot_base = 0
    for repo in repos:
        name = repo.get("name")
        if name in local_overrides:
            m = COL.local_git_metrics(local_overrides[name], login="overandor",
                                      followers=4, public_repos=len(repos))
            m["_fidelity"] = "precise(local-git)"
        else:
            m = COL.github_repo_metrics(repo)
            m["_fidelity"] = "coarse(size-proxy)"
        v = U.value(m); r = U.risk_score(m); e = U.eligibility(v, r)
        dec = U.decide(v, {}, r, e)
        grades[r["grade"]] += 1
        tot_central += v["central_net_realizable_usd"]
        tot_eligible += e["eligible_collateral_usd"]
        tot_base += e["borrowing_base_usd"]
        entry = pb.append("underwrite_decision", {
            "repo": repo.get("name"), "grade": r["grade"],
            "central_value_usd": v["central_net_realizable_usd"],
            "borrowing_base_usd": e["borrowing_base_usd"], "outcome": dec["outcome"]})
        rows.append({"repo": name, "language": repo.get("language"),
                     "grade": r["grade"], "central_usd": v["central_net_realizable_usd"],
                     "borrowing_base_usd": e["borrowing_base_usd"],
                     "fidelity": m["_fidelity"], "proof": entry["hash"][:12]})
    rows.sort(key=lambda x: -x["borrowing_base_usd"])
    return {
        "n_repos": len(repos),
        "portfolio_central_value_usd": tot_central,
        "portfolio_eligible_collateral_usd": tot_eligible,
        "portfolio_borrowing_base_usd": tot_base,
        "grade_distribution": dict(grades),
        "top_contributors": rows[:10],
        "all_rows": rows,
        "proofbook_head": pb.head,
        "proofbook_verified": pb.verify_chain(),
    }


def render(report: dict) -> str:
    L = ["# Portfolio Underwriting Roll-Up", ""]
    L.append(f"- Repos underwritten: **{report['n_repos']}**")
    L.append(f"- Portfolio central value: **${report['portfolio_central_value_usd']:,}**")
    L.append(f"- Eligible collateral: **${report['portfolio_eligible_collateral_usd']:,}**")
    L.append(f"- **Portfolio borrowing base: ${report['portfolio_borrowing_base_usd']:,}**")
    L.append(f"- Grade distribution: {report['grade_distribution']}")
    L.append(f"- ProofBook head: `{report['proofbook_head'][:16]}…` · chain verified: {report['proofbook_verified']}")
    L.append("\n## Top contributors")
    L.append("| Repo | Lang | Grade | Central $ | Borrowing base $ | Fidelity | Proof |")
    L.append("|---|---|---|---|---|---|---|")
    for r in report["top_contributors"]:
        L.append(f"| {r['repo']} | {r['language'] or '-'} | {r['grade']} | "
                 f"${r['central_usd']:,} | ${r['borrowing_base_usd']:,} | {r['fidelity']} | `{r['proof']}` |")
    L.append("\n*Each decision is hash-chained in ProofBook (`out/proofbook.jsonl`). "
             "Per-repo metrics are coarse (size/language proxies, no clone); the flagship "
             "uses precise local-git metrics. Credit screen — not a lending commitment.*")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", required=True)
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    repos = json.load(open(a.repos))
    if isinstance(repos, dict):
        repos = repos.get("items") or repos.get("repos") or list(repos.values())
    os.makedirs(a.out, exist_ok=True)
    pb = ProofBook(os.path.join(a.out, "proofbook.jsonl"))
    # the flagship is checked out here -> use precise local-git metrics for it
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    overrides = {"membra-company-os": repo_root}
    report = underwrite_portfolio(repos, pb, local_overrides=overrides)
    json.dump(report, open(os.path.join(a.out, "portfolio.json"), "w"), indent=2)
    open(os.path.join(a.out, "portfolio_report.md"), "w").write(render(report))
    print(f"underwrote {report['n_repos']} repos | portfolio borrowing base "
          f"${report['portfolio_borrowing_base_usd']:,} | proofbook verified={report['proofbook_verified']}")


if __name__ == "__main__":
    main()
