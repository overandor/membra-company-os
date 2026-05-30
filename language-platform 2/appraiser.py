"""
CollateralOps six-number appraisal engine.
Conservative, transparent, deduction-based.
Produces: replacement cost, as-is sale value, productized value,
liquidation value, collateral support value, and financeability score.
"""
import math

# Engineering hourly rate estimates by language/complexity
HOURLY_RATES = {
    "python": 120, "typescript": 130, "javascript": 110, "rust": 160,
    "solidity": 180, "go": 140, "none": 0,
}

# Hours per source file (rough industry estimate)
HOURS_PER_FILE = {
    "python": 4, "typescript": 5, "javascript": 3.5, "rust": 8,
    "solidity": 10, "go": 6, "none": 0,
}

# Asset type multipliers for commercial potential
TYPE_MULTIPLIERS = {
    "production_system": 1.0, "working_prototype": 0.6,
    "research_prototype": 0.4, "internal_tool": 0.5,
    "api_service": 0.8, "frontend_product": 0.7,
    "backend_service": 0.75, "trading_engine": 1.2,
    "smart_contract": 0.9, "agent_workflow": 0.7,
    "collateral_package": 0.3, "documentation_package": 0.2,
    "scaffold": 0.05, "duplicate": 0.02, "junk": 0.0,
    "fork_template": 0.05, "dataset": 0.4,
    "prompt_system": 0.3, "proof_ledger": 0.4,
    "huggingface_space": 0.5, "outreach_system": 0.4,
}


def appraise(classification: dict) -> dict:
    """Generate six-number appraisal from classification."""
    sigs = classification.get("signals", {})
    quality = classification.get("quality", {})
    asset_type = classification.get("asset_type", "junk")
    proof_level = classification.get("proof_level", 0)
    risks = classification.get("risk_flags", [])

    # 1. Replacement Cost
    replacement = _replacement_cost(sigs)

    # 2. As-Is Sale Value
    as_is = _as_is_value(replacement, sigs, quality, asset_type, proof_level)

    # 3. Productized Value
    productized = _productized_value(replacement, as_is, quality, asset_type)

    # 4. Liquidation Value
    liquidation = _liquidation_value(as_is, quality, proof_level)

    # 5. Collateral Support Value
    collateral_support = _collateral_support(liquidation, quality, proof_level, risks)

    # 6. Financeability Score
    financeability = _financeability_score(quality, proof_level, risks, sigs)

    # Deductions breakdown
    deductions = _compute_deductions(quality, proof_level, risks, sigs)

    # Confidence
    confidence = _confidence_score(sigs, quality, proof_level)

    return {
        "replacement_cost_usd": round(replacement, 2),
        "as_is_sale_value_usd": round(as_is, 2),
        "productized_value_usd": round(productized, 2),
        "liquidation_value_usd": round(liquidation, 2),
        "collateral_support_value_usd": round(collateral_support, 2),
        "financeability_score": round(financeability),
        "confidence_score": round(confidence),
        "deductions": deductions,
        "recommended_ltv": _recommended_ltv(financeability, proof_level),
        "capital_readiness": _capital_readiness(proof_level, financeability),
        "next_actions": _next_actions(quality, risks, proof_level, sigs),
    }


def _replacement_cost(sigs: dict) -> float:
    """What would it cost to recreate from scratch."""
    lang = sigs.get("primary_language", "none")
    rate = HOURLY_RATES.get(lang, 100)
    hpf = HOURS_PER_FILE.get(lang, 4)
    src = sigs.get("total_src", 0)

    base_hours = src * hpf
    # Architecture overhead (15-30% for larger projects)
    overhead = 1.15 + min(0.15, src / 1000)
    # Test/CI adds value
    if sigs.get("has_tests"): overhead += 0.10
    if sigs.get("has_ci"): overhead += 0.05
    if sigs.get("has_dockerfile"): overhead += 0.05

    return base_hours * rate * overhead


def _as_is_value(replacement: float, sigs: dict, quality: dict, asset_type: str, proof_level: int) -> float:
    """What a buyer would pay today without more work."""
    mult = TYPE_MULTIPLIERS.get(asset_type, 0.3)

    # Base: fraction of replacement cost
    base = replacement * mult * 0.35

    # Quality adjustments
    q_avg = sum(quality.values()) / max(1, len(quality))
    base *= (0.5 + q_avg / 200)

    # Proof level bonus
    base *= (0.5 + proof_level * 0.1)

    # No source = near zero
    if sigs.get("total_src", 0) == 0:
        base *= 0.05

    return max(0, base)


def _productized_value(replacement: float, as_is: float, quality: dict, asset_type: str) -> float:
    """Value after packaging, docs, deployment, and polish."""
    mult = TYPE_MULTIPLIERS.get(asset_type, 0.3)
    # Productized is usually 2-5x as-is for viable types
    if mult > 0.5:
        return as_is * 3.0 + replacement * 0.1
    return as_is * 1.5


def _liquidation_value(as_is: float, quality: dict, proof_level: int) -> float:
    """Forced-sale value under time pressure."""
    # Liquidation is typically 30-60% of as-is
    discount = 0.3 + proof_level * 0.05
    discount = min(0.6, discount)
    return as_is * discount


def _collateral_support(liquidation: float, quality: dict, proof_level: int, risks: list) -> float:
    """Underwriting formula: what a lender can safely rely on."""
    ownership_conf = 0.8  # Base: claimed but not legally verified
    if "no_license" in risks: ownership_conf *= 0.7
    if "no_version_control" in risks: ownership_conf *= 0.6

    tech_verif = min(1.0, quality.get("engineering", 0) / 100 * 0.5 + quality.get("deployment", 0) / 100 * 0.5)
    marketability = min(1.0, quality.get("documentation", 0) / 100 * 0.4 + 0.2 + proof_level * 0.06)
    legal_clean = 1.0
    if "no_license" in risks: legal_clean *= 0.6
    if "env_file_detected" in risks: legal_clean *= 0.8
    security_clean = quality.get("security", 70) / 100
    recovery_conf = 0.3 + proof_level * 0.08

    csv = liquidation * ownership_conf * tech_verif * marketability * legal_clean * security_clean * recovery_conf
    return max(0, csv)


def _financeability_score(quality: dict, proof_level: int, risks: list, sigs: dict) -> float:
    """0-100 score: how close to being accepted by money."""
    score = 0

    # Ownership clarity (15 pts)
    own = 15
    if "no_license" in risks: own -= 8
    if "no_version_control" in risks: own -= 5
    score += max(0, own)

    # Originality (15 pts)
    orig = 12  # Assumed original unless proven otherwise
    score += orig

    # Build proof (15 pts)
    build = 0
    if sigs.get("has_dockerfile") or sigs.get("has_vercel"): build += 6
    if sigs.get("has_tests"): build += 5
    if sigs.get("has_ci"): build += 4
    score += min(15, build)

    # Documentation (5 pts)
    doc = 0
    if sigs.get("has_readme"): doc += 3
    if sigs.get("has_license"): doc += 2
    score += doc

    # Security (15 pts)
    sec = 15
    if "env_file_detected" in risks: sec -= 8
    if "no_gitignore" in risks: sec -= 4
    score += max(0, sec)

    # Market usefulness (15 pts)
    mkt = quality.get("engineering", 0) / 100 * 10
    if sigs.get("total_src", 0) > 20: mkt += 3
    if sigs.get("has_dockerfile") or sigs.get("has_vercel"): mkt += 2
    score += min(15, mkt)

    # Liquidation path (10 pts)
    liq = 2 + proof_level
    score += min(10, liq)

    # Revenue/adoption (10 pts) — none available from scan
    score += 0

    return min(100, max(0, score))


def _compute_deductions(quality: dict, proof_level: int, risks: list, sigs: dict) -> list:
    """Transparent deduction list."""
    deds = []
    if "no_license" in risks:
        deds.append({"reason": "No license file", "impact": "-10%", "category": "legal"})
    if "no_readme" in risks:
        deds.append({"reason": "No README", "impact": "-5%", "category": "documentation"})
    if "env_file_detected" in risks:
        deds.append({"reason": "Environment file detected (possible secrets)", "impact": "-15%", "category": "security"})
    if "no_tests" in risks:
        deds.append({"reason": "No test files", "impact": "-10%", "category": "engineering"})
    if "no_version_control" in risks:
        deds.append({"reason": "No git repository", "impact": "-20%", "category": "ownership"})
    if "no_gitignore" in risks:
        deds.append({"reason": "No .gitignore", "impact": "-5%", "category": "security"})
    if sigs.get("total_src", 0) == 0:
        deds.append({"reason": "No source code", "impact": "-80%", "category": "engineering"})
    if proof_level < 3:
        deds.append({"reason": f"Low proof level ({proof_level}/7)", "impact": "-20%", "category": "verification"})
    # Always add these structural deductions
    deds.append({"reason": "No verified revenue", "impact": "-35%", "category": "market"})
    deds.append({"reason": "No buyer interest evidence", "impact": "-25%", "category": "market"})
    deds.append({"reason": "Thin liquidation market", "impact": "-30%", "category": "liquidity"})
    return deds


def _recommended_ltv(financeability: float, proof_level: int) -> dict:
    if financeability < 20:
        return {"min_pct": 0, "max_pct": 5, "note": "Asset not yet financeable"}
    if financeability < 40:
        return {"min_pct": 5, "max_pct": 15, "note": "Conservative advance only"}
    if financeability < 60:
        return {"min_pct": 10, "max_pct": 25, "note": "Moderate advance with monitoring"}
    if financeability < 80:
        return {"min_pct": 15, "max_pct": 35, "note": "Standard advance"}
    return {"min_pct": 20, "max_pct": 40, "note": "Strong collateral position"}


def _capital_readiness(proof_level: int, financeability: float) -> str:
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


def _confidence_score(sigs: dict, quality: dict, proof_level: int) -> float:
    """How confident we are in the appraisal (0-100)."""
    c = 20  # Base
    if sigs.get("has_git"): c += 10
    if sigs.get("has_readme"): c += 5
    if sigs.get("total_src", 0) > 5: c += 10
    if sigs.get("total_src", 0) > 20: c += 5
    if sigs.get("has_tests"): c += 10
    if sigs.get("has_dockerfile"): c += 5
    if sigs.get("collateral_count", 0) > 0: c += 15
    c += proof_level * 3
    return min(100, c)


def _next_actions(quality: dict, risks: list, proof_level: int, sigs: dict) -> list:
    """Ranked actions by financeability impact."""
    actions = []
    if "no_license" in risks:
        actions.append({"action": "Add LICENSE file", "impact": "+8 financeability", "priority": "critical"})
    if "env_file_detected" in risks:
        actions.append({"action": "Remove or secure .env files", "impact": "+10 financeability", "priority": "critical"})
    if "no_readme" in risks:
        actions.append({"action": "Add README with description and usage", "impact": "+5 financeability", "priority": "high"})
    if "no_tests" in risks:
        actions.append({"action": "Add test suite", "impact": "+8 financeability", "priority": "high"})
    if not sigs.get("has_dockerfile") and not sigs.get("has_vercel"):
        actions.append({"action": "Add Dockerfile or deployment config", "impact": "+6 financeability", "priority": "high"})
    if not sigs.get("has_ci"):
        actions.append({"action": "Add CI/CD pipeline", "impact": "+4 financeability", "priority": "medium"})
    actions.append({"action": "Generate buyer memo", "impact": "+5 financeability", "priority": "medium"})
    actions.append({"action": "Deploy demo/endpoint", "impact": "+12 financeability", "priority": "high"})
    actions.append({"action": "Obtain first buyer response", "impact": "+12 financeability", "priority": "high"})
    actions.append({"action": "Add revenue/usage evidence", "impact": "+20 financeability", "priority": "high"})
    return actions


def _confidence_score(sigs: dict, quality: dict, proof_level: int) -> float:
    c = 20
    if sigs.get("has_git"): c += 10
    if sigs.get("has_readme"): c += 5
    if sigs.get("total_src", 0) > 5: c += 10
    if sigs.get("total_src", 0) > 20: c += 5
    if sigs.get("has_tests"): c += 10
    if sigs.get("has_dockerfile"): c += 5
    if sigs.get("collateral_count", 0) > 0: c += 15
    c += proof_level * 3
    return min(100, c)
