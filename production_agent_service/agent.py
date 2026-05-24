#!/usr/bin/env python3
"""
Production Agent — orchestrates scanning, readiness evaluation, and appraisal.
Runs autonomously or on-demand via the API.
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from scanner import scan_workspace, Project, ScanResult
from readiness import evaluate_project as evaluate_readiness
from appraiser import appraise_project, report_to_dict


@dataclass
class AgentJob:
    job_id: str
    status: str  # pending, running, completed, failed
    root_path: str
    started_at: str
    completed_at: Optional[str] = None
    projects_scanned: int = 0
    projects_appraised: int = 0
    total_value_usd: int = 0
    avg_readiness: float = 0.0
    results: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ProductionAgent:
    def __init__(self, workspace_root: str = "/Users/alep/Downloads"):
        self.workspace_root = Path(workspace_root).expanduser().resolve()
        self.jobs: Dict[str, AgentJob] = {}
        self.latest_scan: Optional[ScanResult] = None
        self.latest_results: List[Dict] = []

    def run_scan(self, job_id: Optional[str] = None) -> AgentJob:
        job_id = job_id or f"scan-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        job = AgentJob(
            job_id=job_id,
            status="running",
            root_path=str(self.workspace_root),
            started_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        self.jobs[job_id] = job

        try:
            scan_result = scan_workspace(self.workspace_root, max_depth=6)
            self.latest_scan = scan_result
            job.projects_scanned = len(scan_result.projects)

            for proj in scan_result.projects:
                try:
                    root = Path(proj.root)
                    readiness = evaluate_readiness(root, proj.name, proj.project_type)
                    appraisal = appraise_project(root, proj.project_type)
                    appraisal_dict = report_to_dict(appraisal)

                    # Merge readiness into appraisal
                    appraisal_dict["readiness_score"] = readiness.overall_score
                    appraisal_dict["readiness_details"] = {
                        "ci_cd": readiness.ci_cd,
                        "tests": readiness.tests,
                        "docs": readiness.docs,
                        "typing": readiness.typing,
                        "linting": readiness.linting,
                        "docker": readiness.docker,
                        "secrets": readiness.secrets,
                        "dependencies": readiness.dependencies,
                        "structure": readiness.structure,
                    }
                    appraisal_dict["readiness_recommendations"] = readiness.recommendations
                    appraisal_dict["readiness_issues"] = readiness.issues[:5]

                    job.results.append(appraisal_dict)
                    job.projects_appraised += 1
                    job.total_value_usd += appraisal_dict.get("estimated_value_usd", 0)
                except Exception as e:
                    job.errors.append(f"{proj.name}: {str(e)}")

            if job.results:
                job.avg_readiness = round(
                    sum(r["overall_score"] for r in job.results) / len(job.results), 1
                )

            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self.latest_results = job.results
        except Exception as e:
            job.status = "failed"
            job.errors.append(str(e))

        return job

    def get_summary(self) -> Dict:
        if not self.latest_results:
            return {"status": "no_data", "message": "Run scan first"}

        grades = {}
        types = {}
        for r in self.latest_results:
            g = r["readiness_grade"]
            grades[g] = grades.get(g, 0) + 1
            t = r["project_type"]
            types[t] = types.get(t, 0) + 1

        return {
            "projects": len(self.latest_results),
            "total_value_usd": sum(r["estimated_value_usd"] for r in self.latest_results),
            "avg_overall_score": round(sum(r["overall_score"] for r in self.latest_results) / len(self.latest_results), 1),
            "avg_readiness_score": round(sum(r["readiness_score"] for r in self.latest_results) / len(self.latest_results), 1),
            "grade_distribution": grades,
            "type_distribution": types,
            "top_projects": sorted(self.latest_results, key=lambda x: x["overall_score"], reverse=True)[:5],
            "urgent_issues": [
                {"project": r["project_name"], "issues": r["readiness_issues"]}
                for r in self.latest_results if r.get("readiness_issues")
            ],
        }

    def export_report(self, out_path: Optional[Path] = None) -> Path:
        out = out_path or (self.workspace_root / "PRODUCTION_AGENT_REPORT.json")
        summary = self.get_summary()
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "workspace_root": str(self.workspace_root),
            "summary": summary,
            "projects": self.latest_results,
        }
        out.write_text(json.dumps(payload, indent=2, default=str))
        return out


if __name__ == "__main__":
    agent = ProductionAgent()
    print("Starting full workspace scan + appraisal...")
    job = agent.run_scan()
    print(f"Job {job.job_id}: {job.status}")
    print(f"  Projects scanned: {job.projects_scanned}")
    print(f"  Projects appraised: {job.projects_appraised}")
    print(f"  Total value: ${job.total_value_usd:,}")
    print(f"  Avg readiness: {job.avg_readiness}")
    if job.errors:
        print(f"  Errors: {len(job.errors)}")
    report = agent.export_report()
    print(f"  Report saved: {report}")
