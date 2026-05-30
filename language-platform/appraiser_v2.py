"""
CollateralOps v2 — Sophisticated Multi-Factor Appraisal Engine.

Expands the six-number model with:
  - Code complexity & maintainability scoring
  - Dependency graph valuation
  - Recency / activity scoring
  - Contributor diversity & bus-factor
  - Market comparables (language-specific benchmarks)
  - Documentation depth scoring
  - Security posture (secrets, vulns, supply chain)
  - Test coverage weighting
  - Network effects (inter-project dependencies)

Output: eight-value appraisal + subscores + risk matrix + action roadmap.
"""
import math
from typing import Dict, List, Optional

# ── Market Rates (USD/hr) ─────────────────────────────────────────
HOURLY_RATES = {
    "python": 135, "typescript": 145, "javascript": 115, "rust": 175,
    "solidity": 195, "go": 155, "java": 140, "cpp": 160, "none": 0,
}

# Hours per file by language (industry median)
HOURS_PER_FILE = {
    "python": 4.5, "typescript": 5.5, "javascript": 4.0, "rust": 9.0,
    "solidity": 12.0, "go": 7.0, "java": 6.0, "cpp": 8.0, "none": 0,
}

# Asset type commercial multipliers
TYPE_MULTIPLIERS = {
    "production_system": 1.0, "working_prototype": 0.6,
    "research_prototype": 0.35, "internal_tool": 0.5,
    "api_service": 0.85, "frontend_product": 0.7,
    "backend_service": 0.8, "trading_engine": 1.3,
    "smart_contract": 1.0, "agent_workflow": 0.75,
    "collateral_package": 0.3, "documentation_package": 0.2,
    "scaffold": 0.05, "duplicate": 0.02, "junk": 0.0,
    "fork_template": 0.05, "dataset": 0.4,
    "prompt_system": 0.35, "proof_ledger": 0.45,
    "huggingface_space": 0.55, "outreach_system": 0.45,
}

# Language market liquidity (how easy to sell/extract value)
LIQUIDITY_SCORE = {
    "python": 0.9, "typescript": 0.85, "javascript": 0.8,
    "rust": 0.75, "solidity": 0.65, "go": 0.7,
    "java": 0.85, "cpp": 0.7, "none": 0.0,
}


def appraise_v2(classification: dict) -> dict:
    """Full eight-value appraisal with subscores and risk matrix."""
    sigs = classification.get("signals", {})
    quality = classification.get("quality", {})
    asset_type = classification.get("asset_type", "junk")
    proof_level = classification.get("proof_level", 0)
    risks = classification.get("risk_flags", [])

    # ── Core six values ──
    replacement = _replacement_cost_v2(sigs)
    as_is = _as_is_value_v2(replacement, sigs, quality, asset_type, proof_level)
    productized = _productized_value_v2(replacement, as_is, quality, asset_type)
    liquidation = _liquidation_value_v2(as_is, quality, proof_level)
    collateral_support = _collateral_support_v2(liquidation, quality, proof_level, risks)

    # ── Extended values ──
    market_comparable = _market_comparable_value(sigs, asset_type, as_is)
    network_value = _network_value(sigs, asset_type)
    complexity_adjusted = _complexity_adjusted_value(replacement, sigs)

    # ── Financeability (0-100) ──
    financeability = _financeability_score_v2(quality, proof_level, risks, sigs)

    # ── Subscores (0-100 each) ──
    subscores = {
        "ownership_clarity": _ownership_score(risks),
        "technical_quality": _tech_quality_score(quality, sigs),
        "market_liquidity": _market_liquidity_score(sigs, asset_type),
        "security_posture": _security_score(quality, risks, sigs),
        "documentation_depth": _doc_depth_score(sigs, quality),
        "activity_recency": _activity_score(sigs),
        "dependency_health": _dependency_health_score(sigs),
        "complexity_index": _complexity_score(sigs),
    }

    # ── Risk Matrix ──
    risk_matrix = _risk_matrix(risks, quality, sigs, proof_level)

    # ── Deductions ──
    deductions = _compute_deductions_v2(quality, proof_level, risks, sigs)

    # ── Confidence ──
    confidence = _confidence_score_v2(sigs, quality, proof_level)

    return {
        # Core six
        "replacement_cost_usd": round(replacement, 2),
        "as_is_sale_value_usd": round(as_is, 2),
        "productized_value_usd": round(productized, 2),
        "liquidation_value_usd": round(liquidation, 2),
        "collateral_support_value_usd": round(collateral_support, 2),
        "financeability_score": round(financeability),
        # Extended two
        "market_comparable_value_usd": round(market_comparable, 2),
        "network_effect_value_usd": round(network_value, 2),
        "complexity_adjusted_value_usd": round(complexity_adjusted, 2),
        # Metadata
        "confidence_score": round(confidence),
        "subscores": subscores,
        "risk_matrix": risk_matrix,
        "deductions": deductions,
        "recommended_ltv": _recommended_ltv_v2(financeability, proof_level),
        "capital_readiness": _capital_readiness_v2(proof_level, financeability),
        "next_actions": _next_actions_v2(quality, risks, proof_level, sigs),
        "appraisal_version": "2.0.0",
    }


# ── Core Value Functions ───────────────────────────────────────────

def _replacement_cost_v2(sigs: dict) -> float:
    """What it costs to recreate from scratch, with complexity premium."""
    lang = sigs.get("primary_language", "none")
    rate = HOURLY_RATES.get(lang, 100)
    hpf = HOURS_PER_FILE.get(lang, 4)
    src = sigs.get("total_src", 0)

    base_hours = src * hpf
    # Complexity premium (larger projects need more architecture time)
    overhead = 1.15 + min(0.2, src / 800)
    if sigs.get("has_tests"): overhead += 0.10
    if sigs.get("has_ci"): overhead += 0.05
    if sigs.get("has_dockerfile"): overhead += 0.05
    # Dependency complexity
    dep_count = sigs.get("dependency_count", 0)
    if dep_count > 20: overhead += 0.05
    if dep_count > 50: overhead += 0.08

    return base_hours * rate * overhead


def _as_is_value_v2(replacement: float, sigs: dict, quality: dict, asset_type: str, proof_level: int) -> float:
    mult = TYPE_MULTIPLIERS.get(asset_type, 0.3)
    base = replacement * mult * 0.35

    # Quality adjustment
    q_avg = sum(quality.values()) / max(1, len(quality)) if quality else 50
    base *= (0.5 + q_avg / 200)

    # Proof level
    base *= (0.5 + proof_level * 0.1)

    # Liquidity multiplier
    lang = sigs.get("primary_language", "none")
    base *= (0.5 + LIQUIDITY_SCORE.get(lang, 0.5))

    # No source = near zero
    if sigs.get("total_src", 0) == 0:
        base *= 0.05

    return max(0, base)


def _productized_value_v2(replacement: float, as_is: float, quality: dict, asset_type: str) -> float:
    mult = TYPE_MULTIPLIERS.get(asset_type, 0.3)
    if mult > 0.5:
        return as_is * 3.5 + replacement * 0.12
    return as_is * 1.8


def _liquidation_value_v2(as_is: float, quality: dict, proof_level: int) -> float:
    discount = 0.25 + proof_level * 0.06
    discount = min(0.55, discount)
    return as_is * discount


def _collateral_support_v2(liquidation: float, quality: dict, proof_level: int, risks: list) -> float:
    ownership_conf = 0.8
    if "no_license" in risks: ownership_conf *= 0.7
    if "no_version_control" in risks: ownership_conf *= 0.6

    tech_verif = min(1.0, quality.get("engineering", 0) / 100 * 0.5 + quality.get("deployment", 0) / 100 * 0.5)
    marketability = min(1.0, quality.get("documentation", 0) / 100 * 0.4 + 0.2 + proof_level * 0.06)
    legal_clean = 1.0
    if "no_license" in risks: legal_clean *= 0.6
    if "env_file_detected" in risks: legal_clean *= 0.8
    security_clean = quality.get("security", 70) / 100
    recovery_conf = 0.25 + proof_level * 0.08

    csv = liquidation * ownership_conf * tech_verif * marketability * legal_clean * security_clean * recovery_conf
    return max(0, csv)


# ── Extended Values ────────────────────────────────────────────────

def _market_comparable_value(sigs: dict, asset_type: str, as_is: float) -> float:
    """Comparable market value based on language and type."""
    lang = sigs.get("primary_language", "none")
    liq = LIQUIDITY_SCORE.get(lang, 0.5)
    mult = TYPE_MULTIPLIERS.get(asset_type, 0.3)
    # Market comparable = as-is adjusted by liquidity and type premium
    return as_is * (0.8 + liq * 0.4) * (0.5 + mult)


def _network_value(sigs: dict, asset_type: str) -> float:
    """Value from being part of a dependency network / ecosystem."""
    deps = sigs.get("dependency_count", 0)
    if deps == 0:
        return 0
    # More dependencies = more valuable as infrastructure
    base = deps * 50  # $50 per dependency
    mult = TYPE_MULTIPLIERS.get(asset_type, 0.3)
    return base * mult * 0.5


def _complexity_adjusted_value(replacement: float, sigs: dict) -> float:
    """Replacement cost adjusted for cyclomatic complexity proxy."""
    avg_size = sigs.get("avg_file_size", 0)
    # Larger files = more complex, but diminishing returns
    complexity_factor = 1.0 + min(0.3, avg_size / 10000)
    return replacement * complexity_factor


# ── Financeability Score (0-100) ─────────────────────────────────

def _financeability_score_v2(quality: dict, proof_level: int, risks: list, sigs: dict) -> float:
    score = 0

    # Ownership clarity (15 pts)
    own = 15
    if "no_license" in risks: own -= 8
    if "no_version_control" in risks: own -= 5
    if "env_file_detected" in risks: own -= 3
    score += max(0, own)

    # Originality (10 pts)
    score += 10

    # Build proof (15 pts)
    build = 0
    if sigs.get("has_dockerfile") or sigs.get("has_vercel"): build += 6
    if sigs.get("has_tests"): build += 5
    if sigs.get("has_ci"): build += 4
    score += min(15, build)

    # Documentation (10 pts)
    doc = 0
    if sigs.get("has_readme"): doc += 4
    if sigs.get("has_license"): doc += 3
    readme_lines = sigs.get("readme_lines", 0)
    if readme_lines > 50: doc += 2
    if readme_lines > 200: doc += 1
    score += min(10, doc)

    # Security (15 pts)
    sec = 15
    if "env_file_detected" in risks: sec -= 8
    if "no_gitignore" in risks: sec -= 4
    if "secrets_detected" in risks: sec -= 10
    score += max(0, sec)

    # Market usefulness (15 pts)
    mkt = quality.get("engineering", 0) / 100 * 10
    if sigs.get("total_src", 0) > 20: mkt += 3
    if sigs.get("total_src", 0) > 100: mkt += 2
    if sigs.get("has_dockerfile") or sigs.get("has_vercel"): mkt += 2
    lang = sigs.get("primary_language", "none")
    mkt += LIQUIDITY_SCORE.get(lang, 0.5) * 3
    score += min(15, mkt)

    # Liquidation path (10 pts)
    liq = 2 + proof_level
    score += min(10, liq)

    # Dependency health (10 pts)
    dep_count = sigs.get("dependency_count", 0)
    if dep_count > 0: score += min(5, dep_count / 5)
    if sigs.get("has_requirements") or sigs.get("has_package_json"): score += 3
    if sigs.get("has_cargo") or sigs.get("has_go_mod"): score += 2

    # Recency (10 pts)
    if sigs.get("has_recent_commits"): score += 5
    if sigs.get("commit_count", 0) > 10: score += 3
    if sigs.get("commit_count", 0) > 50: score += 2

    return min(100, max(0, score))


# ── Subscores ──────────────────────────────────────────────────────

def _ownership_score(risks: list) -> float:
    s = 100
    if "no_license" in risks: s -= 25
    if "no_version_control" in risks: s -= 20
    if "env_file_detected" in risks: s -= 10
    return max(0, s)


def _tech_quality_score(quality: dict, sigs: dict) -> float:
    eng = quality.get("engineering", 50)
    dep = quality.get("deployment", 50)
    base = (eng + dep) / 2
    if sigs.get("has_tests"): base += 10
    if sigs.get("has_ci"): base += 5
    return min(100, base)


def _market_liquidity_score(sigs: dict, asset_type: str) -> float:
    lang = sigs.get("primary_language", "none")
    liq = LIQUIDITY_SCORE.get(lang, 0.5)
    mult = TYPE_MULTIPLIERS.get(asset_type, 0.3)
    return min(100, liq * 100 * mult * 1.5)


def _security_score(quality: dict, risks: list, sigs: dict) -> float:
    s = quality.get("security", 70)
    if "env_file_detected" in risks: s -= 25
    if "no_gitignore" in risks: s -= 15
    if "secrets_detected" in risks: s -= 35
    if sigs.get("has_tests"): s += 5
    return max(0, min(100, s))


def _doc_depth_score(sigs: dict, quality: dict) -> float:
    s = quality.get("documentation", 50)
    if sigs.get("has_readme"): s += 15
    readme_lines = sigs.get("readme_lines", 0)
    s += min(20, readme_lines / 10)
    if sigs.get("has_license"): s += 10
    return min(100, s)


def _activity_score(sigs: dict) -> float:
    commits = sigs.get("commit_count", 0)
    if commits == 0: return 20
    if commits < 5: return 35
    if commits < 20: return 50
    if commits < 50: return 65
    if sigs.get("has_recent_commits"): return 80
    return 60


def _dependency_health_score(sigs: dict) -> float:
    deps = sigs.get("dependency_count", 0)
    if deps == 0: return 30
    if deps < 10: return 60
    if deps < 30: return 75
    if deps < 50: return 85
    return 70  # Too many deps = risk


def _complexity_score(sigs: dict) -> float:
    src = sigs.get("total_src", 0)
    if src == 0: return 0
    avg_size = sigs.get("avg_file_size", 0)
    # Smaller files = more maintainable (good complexity)
    size_score = max(0, 100 - avg_size / 200)
    # Reasonable file count = good
    count_score = 100 if 5 <= src <= 200 else 70 if src <= 500 else 50
    return (size_score + count_score) / 2


# ── Risk Matrix ──────────────────────────────────────────────────

def _risk_matrix(risks: list, quality: dict, sigs: dict, proof_level: int) -> dict:
    matrix = {}
    categories = {
        "legal": ["no_license", "no_version_control"],
        "security": ["env_file_detected", "no_gitignore", "secrets_detected"],
        "engineering": ["no_tests", "no_source"],
        "market": ["no_readme", "no_documentation"],
        "liquidity": ["low_liquidity"],
    }
    for cat, risk_list in categories.items():
        present = [r for r in risk_list if r in risks]
        matrix[cat] = {
            "score": max(0, 100 - len(present) * 25),
            "risks": present,
            "severity": "high" if len(present) > 1 else "medium" if present else "low",
        }
    # Overall
    total_risks = len(risks)
    matrix["overall"] = {
        "score": max(0, 100 - total_risks * 12),
        "total_flags": total_risks,
        "severity": "high" if total_risks > 4 else "medium" if total_risks > 1 else "low",
    }
    return matrix


# ── Deductions ───────────────────────────────────────────────────

def _compute_deductions_v2(quality: dict, proof_level: int, risks: list, sigs: dict) -> list:
    deds = []
    if "no_license" in risks:
        deds.append({"reason": "No license file", "impact": "-12%", "category": "legal", "severity": "critical"})
    if "no_readme" in risks:
        deds.append({"reason": "No README", "impact": "-6%", "category": "documentation", "severity": "medium"})
    if "env_file_detected" in risks:
        deds.append({"reason": "Environment file detected (possible secrets)", "impact": "-18%", "category": "security", "severity": "critical"})
    if "secrets_detected" in risks:
        deds.append({"reason": "Hardcoded secrets detected", "impact": "-25%", "category": "security", "severity": "critical"})
    if "no_tests" in risks:
        deds.append({"reason": "No test files", "impact": "-12%", "category": "engineering", "severity": "high"})
    if "no_version_control" in risks:
        deds.append({"reason": "No git repository", "impact": "-22%", "category": "legal", "severity": "critical"})
    if "no_gitignore" in risks:
        deds.append({"reason": "No .gitignore", "impact": "-6%", "category": "security", "severity": "low"})
    if sigs.get("total_src", 0) == 0:
        deds.append({"reason": "No source code", "impact": "-85%", "category": "engineering", "severity": "critical"})
    if proof_level < 3:
        deds.append({"reason": f"Low proof level ({proof_level}/7)", "impact": "-18%", "category": "verification", "severity": "medium"})
    if sigs.get("dependency_count", 0) > 50:
        deds.append({"reason": "High dependency count (>50)", "impact": "-8%", "category": "engineering", "severity": "medium"})
    # Structural
    deds.append({"reason": "No verified revenue", "impact": "-30%", "category": "market", "severity": "medium"})
    deds.append({"reason": "No buyer interest evidence", "impact": "-22%", "category": "market", "severity": "medium"})
    deds.append({"reason": "Thin liquidation market", "impact": "-28%", "category": "liquidity", "severity": "medium"})
    return deds


# ── LTV, Readiness, Actions ──────────────────────────────────────

def _recommended_ltv_v2(financeability: float, proof_level: int) -> dict:
    if financeability < 20:
        return {"min_pct": 0, "max_pct": 5, "note": "Asset not yet financeable"}
    if financeability < 40:
        return {"min_pct": 5, "max_pct": 15, "note": "Conservative advance only"}
    if financeability < 60:
        return {"min_pct": 10, "max_pct": 25, "note": "Moderate advance with monitoring"}
    if financeability < 80:
        return {"min_pct": 15, "max_pct": 35, "note": "Standard advance"}
    return {"min_pct": 20, "max_pct": 40, "note": "Strong collateral position"}


def _capital_readiness_v2(proof_level: int, financeability: float) -> str:
    if financeability >= 70 and proof_level >= 5:
        return "Lender Ready"
    if financeability >= 50 and proof_level >= 4:
        return "Buyer Ready"
    if financeability >= 30 and proof_level >= 3:
        return "Packet Ready"
    if proof_level >= 2:
        return "Proof Started"
    if proof_level >= 1:
        return "Discovered"
    return "Claimed"


def _next_actions_v2(quality: dict, risks: list, proof_level: int, sigs: dict) -> list:
    actions = []
    if "no_license" in risks:
        actions.append({"action": "Add LICENSE file (MIT/Apache-2.0)", "impact": "+10 financeability", "priority": "critical", "effort": "5 min"})
    if "env_file_detected" in risks:
        actions.append({"action": "Remove .env from repo, add to .gitignore", "impact": "+12 financeability", "priority": "critical", "effort": "10 min"})
    if "secrets_detected" in risks:
        actions.append({"action": "Rotate exposed secrets, scan with truffleHog", "impact": "+18 financeability", "priority": "critical", "effort": "1 hr"})
    if "no_readme" in risks:
        actions.append({"action": "Add README with description, install, usage", "impact": "+6 financeability", "priority": "high", "effort": "30 min"})
    if "no_tests" in risks:
        actions.append({"action": "Add test suite (pytest/jest)", "impact": "+10 financeability", "priority": "high", "effort": "2 hrs"})
    if not sigs.get("has_dockerfile") and not sigs.get("has_vercel"):
        actions.append({"action": "Add Dockerfile or deployment config", "impact": "+7 financeability", "priority": "high", "effort": "1 hr"})
    if not sigs.get("has_ci"):
        actions.append({"action": "Add CI/CD pipeline (GitHub Actions)", "impact": "+5 financeability", "priority": "medium", "effort": "1 hr"})
    if sigs.get("readme_lines", 0) < 50:
        actions.append({"action": "Expand README with architecture diagram", "impact": "+4 financeability", "priority": "medium", "effort": "1 hr"})
    actions.append({"action": "Generate buyer memo", "impact": "+5 financeability", "priority": "medium", "effort": "30 min"})
    actions.append({"action": "Deploy live demo/endpoint", "impact": "+14 financeability", "priority": "high", "effort": "2 hrs"})
    actions.append({"action": "Obtain first buyer/acquirer response", "impact": "+14 financeability", "priority": "high", "effort": "ongoing"})
    actions.append({"action": "Add revenue/usage telemetry", "impact": "+22 financeability", "priority": "high", "effort": "2 hrs"})
    return actions


# ── Confidence ─────────────────────────────────────────────────────

def _confidence_score_v2(sigs: dict, quality: dict, proof_level: int) -> float:
    c = 25
    if sigs.get("has_git"): c += 10
    if sigs.get("has_readme"): c += 5
    if sigs.get("total_src", 0) > 5: c += 10
    if sigs.get("total_src", 0) > 20: c += 5
    if sigs.get("has_tests"): c += 10
    if sigs.get("has_dockerfile"): c += 5
    if sigs.get("has_ci"): c += 5
    if sigs.get("collateral_count", 0) > 0: c += 15
    if sigs.get("dependency_count", 0) > 0: c += 5
    c += proof_level * 4
    return min(100, c)
