import json
import random
from datetime import datetime
from typing import Dict, List
from app.models.schemas import WorkerAppraisal

APPRAISAL_RUBRIC = {
    "base": {"code": 800, "ip": 500, "infra": 300, "doc": 200, "provenance": 200},
    "ai_complex": {"complexity": 500, "revenue": 800},
    "market_data": {"complexity": 400, "revenue": 600},
    "crawler": {"complexity": 300, "revenue": 500},
    "content": {"complexity": 200, "revenue": 400},
    "dev": {"complexity": 400, "revenue": 700},
}

AGENT_PROFILES = {
    "web_research": {"base": "crawler", "quality": 78, "risk": "low", "maintenance": 350, "hourly": 55, "y1_low": 12000, "y1_high": 48000},
    "academic_research": {"base": "ai_complex", "quality": 82, "risk": "low", "maintenance": 400, "hourly": 65, "y1_low": 18000, "y1_high": 72000},
    "seo_audit": {"base": "crawler", "quality": 74, "risk": "low", "maintenance": 320, "hourly": 50, "y1_low": 10000, "y1_high": 40000},
    "social_monitor": {"base": "crawler", "quality": 76, "risk": "medium", "maintenance": 380, "hourly": 52, "y1_low": 14000, "y1_high": 56000},
    "competitor_analysis": {"base": "ai_complex", "quality": 80, "risk": "medium", "maintenance": 420, "hourly": 60, "y1_low": 20000, "y1_high": 80000},
    "price_tracker": {"base": "market_data", "quality": 72, "risk": "medium", "maintenance": 300, "hourly": 48, "y1_low": 8000, "y1_high": 32000},
    "content_summarizer": {"base": "content", "quality": 75, "risk": "low", "maintenance": 280, "hourly": 45, "y1_low": 6000, "y1_high": 24000},
    "fact_checker": {"base": "ai_complex", "quality": 85, "risk": "low", "maintenance": 450, "hourly": 70, "y1_low": 22000, "y1_high": 88000},
    "trend_analyzer": {"base": "market_data", "quality": 79, "risk": "medium", "maintenance": 400, "hourly": 58, "y1_low": 16000, "y1_high": 64000},
    "news_aggregator": {"base": "crawler", "quality": 73, "risk": "medium", "maintenance": 340, "hourly": 50, "y1_low": 10000, "y1_high": 40000},
    "legal_analyzer": {"base": "ai_complex", "quality": 88, "risk": "low", "maintenance": 500, "hourly": 80, "y1_low": 30000, "y1_high": 120000},
    "patent_research": {"base": "ai_complex", "quality": 84, "risk": "low", "maintenance": 480, "hourly": 75, "y1_low": 28000, "y1_high": 112000},
    "job_market": {"base": "crawler", "quality": 71, "risk": "medium", "maintenance": 310, "hourly": 47, "y1_low": 8000, "y1_high": 32000},
    "real_estate": {"base": "market_data", "quality": 77, "risk": "medium", "maintenance": 360, "hourly": 55, "y1_low": 14000, "y1_high": 56000},
    "stock_data": {"base": "market_data", "quality": 81, "risk": "high", "maintenance": 440, "hourly": 62, "y1_low": 24000, "y1_high": 96000},
    "crypto_data": {"base": "market_data", "quality": 78, "risk": "high", "maintenance": 420, "hourly": 60, "y1_low": 20000, "y1_high": 80000},
    "review_analyzer": {"base": "content", "quality": 76, "risk": "low", "maintenance": 330, "hourly": 52, "y1_low": 12000, "y1_high": 48000},
    "sentiment": {"base": "ai_complex", "quality": 80, "risk": "medium", "maintenance": 380, "hourly": 58, "y1_low": 16000, "y1_high": 64000},
    "lead_gen": {"base": "crawler", "quality": 74, "risk": "medium", "maintenance": 350, "hourly": 53, "y1_low": 14000, "y1_high": 56000},
    "email_outreach": {"base": "content", "quality": 72, "risk": "medium", "maintenance": 300, "hourly": 48, "y1_low": 10000, "y1_high": 40000},
    "github_trends": {"base": "dev", "quality": 83, "risk": "low", "maintenance": 340, "hourly": 62, "y1_low": 18000, "y1_high": 72000},
    "doc_writer": {"base": "dev", "quality": 78, "risk": "low", "maintenance": 320, "hourly": 55, "y1_low": 12000, "y1_high": 48000},
    "code_review": {"base": "dev", "quality": 86, "risk": "low", "maintenance": 460, "hourly": 72, "y1_low": 26000, "y1_high": 104000},
    "security_audit": {"base": "dev", "quality": 89, "risk": "low", "maintenance": 520, "hourly": 85, "y1_low": 32000, "y1_high": 128000},
    "api_docs": {"base": "dev", "quality": 82, "risk": "low", "maintenance": 380, "hourly": 63, "y1_low": 20000, "y1_high": 80000},
    "devops_monitor": {"base": "dev", "quality": 84, "risk": "medium", "maintenance": 440, "hourly": 68, "y1_low": 24000, "y1_high": 96000},
    "customer_support": {"base": "content", "quality": 77, "risk": "low", "maintenance": 340, "hourly": 50, "y1_low": 12000, "y1_high": 48000},
    "translator": {"base": "content", "quality": 75, "risk": "low", "maintenance": 280, "hourly": 45, "y1_low": 6000, "y1_high": 24000},
    "data_viz": {"base": "dev", "quality": 81, "risk": "low", "maintenance": 360, "hourly": 60, "y1_low": 16000, "y1_high": 64000},
    "report_gen": {"base": "ai_complex", "quality": 80, "risk": "low", "maintenance": 400, "hourly": 62, "y1_low": 20000, "y1_high": 80000},
}

class AppraisalEngine:
    def appraise(self, agent_id: str) -> WorkerAppraisal:
        profile = AGENT_PROFILES.get(agent_id, AGENT_PROFILES["web_research"])
        base = APPRAISAL_RUBRIC["base"]
        premium = APPRAISAL_RUBRIC.get(profile["base"], APPRAISAL_RUBRIC["content"])
        total = base["code"] + base["ip"] + base["infra"] + base["doc"] + base["provenance"] + premium["complexity"] + premium["revenue"]
        return WorkerAppraisal(
            agent_id=agent_id,
            code_value=base["code"],
            ip_value=base["ip"],
            infra_value=base["infra"],
            doc_value=base["doc"],
            provenance_value=base["provenance"],
            complexity_premium=premium["complexity"],
            revenue_premium=premium["revenue"],
            total_value=total,
            roi_annual=45.0,
            payback_months=6.0,
            hourly_rate=float(profile["hourly"]),
            maintenance_monthly=float(profile["maintenance"]),
            revenue_year1_low=float(profile["y1_low"]),
            revenue_year1_high=float(profile["y1_high"]),
            quality_score=profile["quality"],
            risk_level=profile["risk"],
            certification="ISO/IEC 27001",
        )

    def appraise_all(self) -> Dict[str, WorkerAppraisal]:
        return {aid: self.appraise(aid) for aid in AGENT_PROFILES}

    def portfolio_summary(self) -> dict:
        appraisals = self.appraise_all()
        totals = sum(a.total_value for a in appraisals.values())
        avg = totals / len(appraisals)
        return {
            "total_agents": len(appraisals),
            "total_portfolio_value": totals,
            "average_value": avg,
            "highest_value": max(a.total_value for a in appraisals.values()),
            "lowest_value": min(a.total_value for a in appraisals.values()),
            "average_quality": sum(a.quality_score for a in appraisals.values()) / len(appraisals),
            "annual_maintenance": sum(a.maintenance_monthly for a in appraisals.values()) * 12,
            "revenue_range_year1": {
                "low": sum(a.revenue_year1_low for a in appraisals.values()),
                "high": sum(a.revenue_year1_high for a in appraisals.values()),
            },
        }

appraisal_engine = AppraisalEngine()
