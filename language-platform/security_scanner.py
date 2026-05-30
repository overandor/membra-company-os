"""
CollateralOps — Security scanning module (T12, T13, T14, T15).
Dependency vulnerability checks, license compliance, secret detection.
"""
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import httpx

# OSV API for CVE lookups
OSV_BASE = "https://api.osv.dev/v1"

# Common secret patterns
SECRET_PATTERNS = [
    (r"api[_-]?key\s*[:=]\s*['\"]([a-zA-Z0-9_-]{16,})['\"]", "API Key"),
    (r"secret\s*[:=]\s*['\"]([a-zA-Z0-9_-]{16,})['\"]", "Secret"),
    (r"password\s*[:=]\s*['\"]([^'\"]{8,})['\"]", "Password"),
    (r"private[_-]?key\s*[:=]\s*['\"]([a-zA-Z0-9_/+=]{20,})['\"]", "Private Key"),
    (r"gh[pousr]_[A-Za-z0-9_]{36}", "GitHub Token"),
    (r"ghp_[A-Za-z0-9_]{36}", "GitHub PAT"),
    (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
]

# SPDX license compatibility matrix (simplified)
COPYLEFT_LICENSES = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1", "LGPL-3.0", "MPL-2.0", "CC-BY-SA-4.0"}
PERMISSIVE_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unlicense", "CC0-1.0"}


def scan_secrets_in_text(text: str, filename: str = "unknown") -> List[Dict]:
    """Scan text content for hardcoded secrets."""
    findings = []
    for pattern, label in SECRET_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            findings.append({
                "file": filename,
                "type": label,
                "match": match.group(0),
                "line": text[:match.start()].count("\n") + 1,
                "severity": "critical",
            })
    return findings


def scan_repo_secrets(repo_path: str) -> List[Dict]:
    """Scan a local repo for secrets."""
    findings = []
    repo = Path(repo_path)
    for file_path in repo.rglob("*"):
        if file_path.is_file() and file_path.stat().st_size < 1024 * 1024:  # Skip files > 1MB
            try:
                text = file_path.read_text(errors="ignore")
                rel = str(file_path.relative_to(repo))
                # Skip common non-source files
                if any(rel.endswith(ext) for ext in [".png", ".jpg", ".gif", ".ico", ".ttf", ".woff", ".mp4", ".zip"]):
                    continue
                findings.extend(scan_secrets_in_text(text, rel))
            except Exception:
                pass
    return findings


async def query_osv(package_name: str, version: str, ecosystem: str = "PyPI") -> List[Dict]:
    """Query OSV API for vulnerabilities in a package."""
    payload = {"package": {"name": package_name, "ecosystem": ecosystem}, "version": version}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(f"{OSV_BASE}/query", json=payload)
            if r.status_code == 200:
                data = r.json()
                return [{"id": v.get("id"), "severity": v.get("severity", "UNKNOWN"),
                         "summary": v.get("summary", ""), "aliases": v.get("aliases", [])}
                        for v in data.get("vulns", [])]
        except Exception:
            pass
    return []


def check_license_conflict(licenses: List[str]) -> List[Dict]:
    """Check for license conflicts. Returns list of conflicts."""
    conflicts = []
    has_copyleft = any(l in COPYLEFT_LICENSES for l in licenses)
    has_permissive = any(l in PERMISSIVE_LICENSES for l in licenses)
    if has_copyleft and has_permissive:
        conflicts.append({
            "type": "copyleft_infection",
            "severity": "high",
            "description": "Copyleft license detected alongside permissive licenses. Derivative work may be infected.",
        })
    unknown = [l for l in licenses if l not in COPYLEFT_LICENSES and l not in PERMISSIVE_LICENSES]
    if unknown:
        conflicts.append({
            "type": "unclassified_license",
            "severity": "medium",
            "description": f"Unclassified licenses require legal review: {', '.join(unknown)}",
        })
    return conflicts


def detect_risk_flags(repo_path: Optional[str] = None, repo_metadata: Optional[Dict] = None) -> List[Dict]:
    """Automated risk flag detection (T15)."""
    flags = []
    if repo_path:
        secrets = scan_repo_secrets(repo_path)
        if secrets:
            flags.append({
                "category": "security",
                "severity": "critical",
                "reason": f"{len(secrets)} secret(s) detected in codebase",
                "remediation": "Rotate credentials, add pre-commit hooks (detect-secrets), remove from history",
            })
    if repo_metadata:
        if not repo_metadata.get("license"):
            flags.append({
                "category": "license",
                "severity": "high",
                "reason": "No recognized license file in repository",
                "remediation": "Add LICENSE file (MIT/Apache-2.0 recommended)",
            })
        if repo_metadata.get("stars", 0) == 0 and repo_metadata.get("forks", 0) == 0:
            flags.append({
                "category": "originality",
                "severity": "low",
                "reason": "Zero community engagement (stars/forks) — may be unmaintained or non-original",
                "remediation": "Verify originality, document provenance",
            })
    return flags
