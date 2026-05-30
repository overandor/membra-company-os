"""
Software Collateral Packet generator.
Produces the standard exportable object for lenders, buyers, brokers.
Four sections: Identity, Technical Proof, Economic Appraisal, Monetization Route.
"""
import hashlib
import json
import time
from datetime import datetime, timezone


def generate_packet(classification: dict, appraisal: dict, collateral_records: list) -> dict:
    """Generate a full Software Collateral Packet."""
    repo = classification.get("repo_name", "Unknown")
    sigs = classification.get("signals", {})
    quality = classification.get("quality", {})

    packet = {
        "packet_version": "1.0.0",
        "packet_type": "Software Collateral Packet",
        "generated_by": "CollateralOps v1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "packet_hash": "",  # filled at end

        # Section A: Identity and Ownership
        "identity": {
            "asset_name": repo,
            "asset_type": classification.get("asset_type", "unknown"),
            "owner": "Claimed — requires legal verification",
            "source_type": "local_folder",
            "source_path": classification.get("repo_path", ""),
            "primary_language": sigs.get("primary_language", "unknown"),
            "total_source_files": sigs.get("total_src", 0),
            "total_files": sigs.get("total_files", 0),
            "total_size_bytes": sigs.get("total_size_bytes", 0),
            "has_version_control": sigs.get("has_git", False),
            "license_status": "present" if sigs.get("has_license") else "missing",
            "ownership_declaration": "Self-reported. Not independently verified.",
            "fork_status": "Not scanned — manual review recommended",
            "contributor_risk": "Single-owner assumed",
        },

        # Section B: Technical Proof
        "technical_proof": {
            "proof_level": classification.get("proof_level", 0),
            "proof_level_name": classification.get("proof_level_name", "Claimed"),
            "has_readme": sigs.get("has_readme", False),
            "has_license": sigs.get("has_license", False),
            "has_tests": sigs.get("has_tests", False),
            "test_file_count": sigs.get("test_files", 0),
            "has_ci_cd": sigs.get("has_ci", False),
            "has_dockerfile": sigs.get("has_dockerfile", False),
            "has_deployment_config": sigs.get("has_vercel", False) or sigs.get("has_procfile", False),
            "build_status": "not_verified",
            "secret_scan": "env_file_detected" if sigs.get("has_env_file") else "no_env_files",
            "dependency_manifest": sigs.get("has_requirements") or sigs.get("has_package_json") or sigs.get("has_cargo"),
            "collateral_evidence": {
                "total_collateral_files": len(collateral_records),
                "workstreams_covered": len(classification.get("workstreams", [])),
                "all_hashed": all(r.get("raw_file_hash") for r in collateral_records) if collateral_records else False,
                "all_anchored": all(r.get("solana_tx_short") for r in collateral_records) if collateral_records else False,
            },
            "quality_scores": quality,
            "risk_flags": classification.get("risk_flags", []),
        },

        # Section C: Economic Appraisal
        "economic_appraisal": {
            "methodology": "Conservative rule-based appraisal with transparent deductions",
            "disclaimer": "This is a risk-adjusted appraisal based on observed evidence. It is not a guarantee of sale price, loan value, or market demand.",
            "replacement_cost_usd": appraisal["replacement_cost_usd"],
            "as_is_sale_value_usd": appraisal["as_is_sale_value_usd"],
            "productized_value_usd": appraisal["productized_value_usd"],
            "liquidation_value_usd": appraisal["liquidation_value_usd"],
            "collateral_support_value_usd": appraisal["collateral_support_value_usd"],
            "financeability_score": appraisal["financeability_score"],
            "confidence_score": appraisal["confidence_score"],
            "recommended_ltv": appraisal["recommended_ltv"],
            "deductions": appraisal["deductions"],
        },

        # Section D: Monetization and Recovery Route
        "monetization_route": {
            "capital_readiness": appraisal["capital_readiness"],
            "buyer_categories": _buyer_categories(classification),
            "liquidation_timeline": _liquidation_timeline(appraisal),
            "sale_route": _sale_route(classification, appraisal),
            "monitoring_plan": _monitoring_plan(classification),
            "default_recovery": _default_recovery(appraisal),
        },

        # Improvement Queue
        "improvement_queue": appraisal["next_actions"],
    }

    # Compute packet hash
    content = json.dumps(packet, sort_keys=True, default=str)
    packet["packet_hash"] = hashlib.sha256(content.encode()).hexdigest()

    return packet


def _buyer_categories(classification: dict) -> list:
    """Identify potential buyer categories."""
    at = classification.get("asset_type", "")
    cats = []

    # Universal buyers
    cats.append({"category": "Venture Studios", "fit": "medium", "reason": "May acquire for portfolio"})
    cats.append({"category": "Software Agencies", "fit": "medium", "reason": "Integration into client work"})

    if at in ("trading_engine", "smart_contract"):
        cats.append({"category": "Trading Firms", "fit": "high", "reason": "Direct operational use"})
        cats.append({"category": "Crypto Protocols", "fit": "high", "reason": "Technology acquisition"})
        cats.append({"category": "Hedge Funds", "fit": "medium", "reason": "Quantitative infrastructure"})
    if at in ("api_service", "backend_service", "production_system"):
        cats.append({"category": "SaaS Operators", "fit": "high", "reason": "Revenue-ready technology"})
        cats.append({"category": "Developer Tool Companies", "fit": "high", "reason": "Product extension"})
    if at in ("agent_workflow",):
        cats.append({"category": "AI Labs", "fit": "high", "reason": "Agent technology acquisition"})
        cats.append({"category": "Enterprise AI Buyers", "fit": "medium", "reason": "Automation capability"})
    if at in ("frontend_product",):
        cats.append({"category": "Micro-SaaS Buyers", "fit": "high", "reason": "Product acquisition"})

    cats.append({"category": "IP Brokers", "fit": "low", "reason": "Intermediary sale"})
    cats.append({"category": "Patent Monetization Firms", "fit": "low", "reason": "IP licensing potential"})

    return cats


def _liquidation_timeline(appraisal: dict) -> dict:
    fs = appraisal.get("financeability_score", 0)
    if fs >= 60:
        return {"expected_days": "30-90", "confidence": "moderate", "note": "Active buyer categories identified"}
    if fs >= 30:
        return {"expected_days": "90-180", "confidence": "low", "note": "Requires packaging and outreach"}
    return {"expected_days": "180+", "confidence": "very_low", "note": "Asset needs significant improvement before sale"}


def _sale_route(classification: dict, appraisal: dict) -> list:
    routes = []
    at = classification.get("asset_type", "")
    if at not in ("junk", "scaffold", "duplicate"):
        routes.append("Private buyer outreach")
        routes.append("IP broker submission")
    if appraisal.get("financeability_score", 0) >= 40:
        routes.append("Curated marketplace listing")
    if at in ("api_service", "frontend_product", "production_system"):
        routes.append("Micro-SaaS marketplace")
    routes.append("Technology licensing")
    return routes


def _monitoring_plan(classification: dict) -> dict:
    return {
        "frequency": "monthly",
        "checks": [
            "Repository hash snapshot",
            "Build verification attempt",
            "Secret scan",
            "License status check",
            "Deployment status check",
            "Owner attestation",
        ],
        "alert_triggers": [
            "Repository deleted or made private",
            "New secrets detected",
            "License changed",
            "Build failure after previous pass",
        ],
    }


def _default_recovery(appraisal: dict) -> dict:
    lv = appraisal.get("liquidation_value_usd", 0)
    csv = appraisal.get("collateral_support_value_usd", 0)
    return {
        "estimated_recovery_usd": f"${csv:.0f}–${lv:.0f}",
        "recovery_method": "Private buyer outreach + broker submission + marketplace listing",
        "legal_review_needed": True,
        "asset_transfer_method": "Repository transfer + documentation handoff",
        "note": "Recovery estimates are not guarantees. Actual recovery depends on market conditions and buyer availability.",
    }


def generate_lender_summary(packet: dict) -> dict:
    """Extract lender-readable summary from packet."""
    ea = packet.get("economic_appraisal", {})
    tp = packet.get("technical_proof", {})
    ident = packet.get("identity", {})
    mr = packet.get("monetization_route", {})

    return {
        "borrower": "Verified: No — Self-reported ownership",
        "asset_name": ident.get("asset_name"),
        "asset_type": ident.get("asset_type"),
        "collateral_description": f"{ident.get('primary_language', 'Unknown')} software system with {ident.get('total_source_files', 0)} source files",
        "proof_level": f"{tp.get('proof_level', 0)}/7 — {tp.get('proof_level_name', 'Unknown')}",
        "ownership_risk": "medium" if ident.get("license_status") == "missing" else "low",
        "build_verification": tp.get("build_status", "not_verified"),
        "license_risk": "high" if ident.get("license_status") == "missing" else "low",
        "secret_risk": "detected" if tp.get("secret_scan") == "env_file_detected" else "none_detected",
        "revenue_evidence": "none",
        "liquidation_market": mr.get("capital_readiness", "Unknown"),
        "estimated_recovery_usd": ea.get("liquidation_value_usd", 0),
        "collateral_support_usd": ea.get("collateral_support_value_usd", 0),
        "recommended_ltv": ea.get("recommended_ltv", {}),
        "monitoring": "Monthly hash + build + secret scan",
        "default_action": "Broker sale / marketplace listing / private acquisition outreach",
    }


def generate_buyer_summary(packet: dict) -> dict:
    """Extract buyer-readable summary from packet."""
    ea = packet.get("economic_appraisal", {})
    ident = packet.get("identity", {})
    tp = packet.get("technical_proof", {})
    mr = packet.get("monetization_route", {})

    return {
        "asset_name": ident.get("asset_name"),
        "what_it_does": f"{ident.get('asset_type', 'Software')} built in {ident.get('primary_language', 'unknown')}",
        "source_files": ident.get("total_source_files", 0),
        "proof_level": tp.get("proof_level_name", "Unknown"),
        "replacement_cost_usd": ea.get("replacement_cost_usd", 0),
        "asking_range_usd": f"${ea.get('as_is_sale_value_usd', 0):.0f}–${ea.get('productized_value_usd', 0):.0f}",
        "risks": tp.get("risk_flags", []),
        "quality": tp.get("quality_scores", {}),
        "buyer_categories": [c["category"] for c in mr.get("buyer_categories", []) if c.get("fit") in ("high", "medium")],
        "integration_difficulty": "moderate",
        "note": "Values are estimates. Buyer should conduct independent diligence.",
    }
