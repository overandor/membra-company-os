"""README, license, security, and docs quality scoring."""
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class QualityScore:
    readme_score: float  # 0-100
    license_score: float  # 0-100
    security_score: float  # 0-100
    docs_score: float  # 0-100
    ci_score: float  # 0-100
    tests_score: float  # 0-100
    overall_quality: float  # weighted average 0-100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "readme_score": round(self.readme_score, 1),
            "license_score": round(self.license_score, 1),
            "security_score": round(self.security_score, 1),
            "docs_score": round(self.docs_score, 1),
            "ci_score": round(self.ci_score, 1),
            "tests_score": round(self.tests_score, 1),
            "overall_quality": round(self.overall_quality, 1),
        }


class QualityScorer:
    def score_repo(self, repo_summary: Any) -> QualityScore:
        """Score a RepoSummary for quality dimensions."""
        # README: exists + length proxy via description
        readme = 100 if repo_summary.has_readme else 0
        if repo_summary.description and len(repo_summary.description) > 100:
            readme = min(100, readme + 10)

        # License: exists + OSI-approved bonus
        license_val = 0
        if repo_summary.license:
            osi_approved = ["MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "GPL-3.0", "LGPL-3.0", "MPL-2.0", "ISC"]
            if any(l in (repo_summary.license or "") for l in osi_approved):
                license_val = 100
            else:
                license_val = 60

        # Security: SECURITY.md + has_actions
        security = 0
        if repo_summary.has_security:
            security += 70
        if repo_summary.has_actions:
            security += 30
        security = min(100, security)

        # Docs: README + has_actions (CI implies docs) + releases
        docs = 0
        if repo_summary.has_readme:
            docs += 40
        if repo_summary.has_actions:
            docs += 30
        if repo_summary.releases > 0:
            docs += 30
        docs = min(100, docs)

        # CI: has_actions + activity
        ci = 0
        if repo_summary.has_actions:
            ci += 70
        if repo_summary.commits_90d > 5:
            ci += 30
        ci = min(100, ci)

        # Tests: has_tests + activity
        tests = 0
        if repo_summary.has_tests:
            tests += 80
        if repo_summary.contributors > 1:
            tests += 20
        tests = min(100, tests)

        overall = (
            readme * 0.20 +
            license_val * 0.20 +
            security * 0.15 +
            docs * 0.15 +
            ci * 0.15 +
            tests * 0.15
        )

        return QualityScore(
            readme_score=readme,
            license_score=license_val,
            security_score=security,
            docs_score=docs,
            ci_score=ci,
            tests_score=tests,
            overall_quality=overall,
        )
