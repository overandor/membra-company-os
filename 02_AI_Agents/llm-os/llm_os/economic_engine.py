"""Economic Engine — Real revenue generation for the LLM OS.

The Economic Engine manages all income-generating activities:
1. Marketplace builds — Software development for paying buyers
2. Trading — Gate.io futures market making (wraps existing systems)
3. Compute rental — Renting out inference/validation capacity
4. Model licensing — Selling access to specialized trained models
5. Proof services — Verification/timestamping for external clients

Design principles:
- Every activity has a cost estimate BEFORE execution
- Every activity reports actual revenue AFTER execution
- Trading is policy-gated with circuit breakers
- No activity may exceed its budget without Treasury approval
- All activities integrate with Governance for safety
"""

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from llm_os.governance import ActionClass, Governance
from llm_os.treasury import Treasury


class RevenueActivity(Enum):
    MARKETPLACE_BUILD = "marketplace_build"
    TRADING = "trading"
    COMPUTE_RENTAL = "compute_rental"
    MODEL_LICENSE = "model_license"
    PROOF_SERVICE = "proof_service"


@dataclass
class Opportunity:
    """A detected economic opportunity."""
    opportunity_id: str
    activity: RevenueActivity
    description: str
    estimated_revenue_usd: float
    estimated_cost_usd: float
    confidence: float  # 0.0 to 1.0
    payload: dict = field(default_factory=dict)
    detected_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None

    @property
    def expected_profit(self) -> float:
        return self.estimated_revenue_usd - self.estimated_cost_usd

    @property
    def expected_roi(self) -> float:
        if self.estimated_cost_usd <= 0:
            return float("inf")
        return (self.expected_profit / self.estimated_cost_usd) * 100


class EconomicEngine:
    """Manages all revenue-generating activities for the LLM OS."""

    def __init__(self, governance: Governance, treasury: Treasury,
                 storage_path: str = None, zk_popc=None):
        self.governance = governance
        self.treasury = treasury
        self.zk_popc = zk_popc
        self.storage_path = storage_path or "/tmp/llm_os_econ.json"
        self.opportunities: List[Opportunity] = []
        self.active_activities: Dict[str, dict] = {}
        self.activity_history: List[dict] = []
        self.trading_enabled = False
        self.trading_process: Optional[subprocess.Popen] = None
        self._load()

    def scan_opportunities(self) -> List[Opportunity]:
        """Scan for economic opportunities across all channels."""
        new_opps = []

        # 1. Check marketplace for pending jobs
        marketplace_opps = self._scan_marketplace()
        new_opps.extend(marketplace_opps)

        # 2. Check trading conditions
        trading_opps = self._scan_trading()
        new_opps.extend(trading_opps)

        # 3. Check compute rental demand
        compute_opps = self._scan_compute_rental()
        new_opps.extend(compute_opps)

        # 4. Check model licensing interest
        license_opps = self._scan_model_licensing()
        new_opps.extend(license_opps)

        self.opportunities.extend(new_opps)
        self._persist()
        return new_opps

    def _scan_marketplace(self) -> List[Opportunity]:
        """Scan membra marketplace for high-value jobs."""
        opps = []
        try:
            # Try to import and check membra marketplace
            from membra_sdk.marketplace.jobs import JobBoard
            board = JobBoard()
            # Look for jobs with high budget and clear requirements
            for job in board.jobs.values():
                if job.status.value == "open" and job.budget_usd > 20:
                    opps.append(Opportunity(
                        opportunity_id=f"mkt-{job.job_id}",
                        activity=RevenueActivity.MARKETPLACE_BUILD,
                        description=f"Build job: {job.title}",
                        estimated_revenue_usd=job.budget_usd * 0.45,  # Builder gets 45%
                        estimated_cost_usd=job.budget_usd * 0.15,   # Infrastructure cost
                        confidence=0.7,
                        payload={"job_id": job.job_id, "budget": job.budget_usd},
                    ))
        except ImportError:
            pass
        except Exception:
            pass
        return opps

    def _scan_trading(self) -> List[Opportunity]:
        """Evaluate if trading conditions are favorable."""
        opps = []
        if not self.trading_enabled:
            return opps

        # Check if we have trading infrastructure and API keys
        has_gate_keys = bool(os.environ.get("GATE_API_KEY")) and bool(os.environ.get("GATE_API_SECRET"))
        if has_gate_keys and self.treasury.balance_usd > 100:
            opps.append(Opportunity(
                opportunity_id=f"trade-{int(time.time())}",
                activity=RevenueActivity.TRADING,
                description="Gate.io micro market making on memecoin futures",
                estimated_revenue_usd=5.0,   # Conservative daily estimate
                estimated_cost_usd=2.0,    # API, compute, potential loss
                confidence=0.4,            # Trading is inherently uncertain
                payload={"exchange": "gate.io", "strategy": "micro_mm"},
                expires_at=time.time() + 86400,
            ))
        return opps

    def _scan_compute_rental(self) -> List[Opportunity]:
        """Check for compute rental demand."""
        opps = []
        # Check if workers are idle and could take jobs
        try:
            from membra_sdk.coordinator.coordinator import Coordinator
            coord = Coordinator()
            if len(coord.workers) > 0 and len(coord.queue.list_pending()) == 0:
                opps.append(Opportunity(
                    opportunity_id=f"compute-{int(time.time())}",
                    activity=RevenueActivity.COMPUTE_RENTAL,
                    description="Rent idle compute for inference/validation",
                    estimated_revenue_usd=10.0,
                    estimated_cost_usd=1.0,
                    confidence=0.5,
                    payload={"workers_available": len(coord.workers)},
                ))
        except ImportError:
            pass
        return opps

    def _scan_model_licensing(self) -> List[Opportunity]:
        """Check if trained models could be licensed."""
        opps = []
        # Check for trained model checkpoints
        checkpoint_dirs = [
            "/Users/alep/Downloads/membra-core/cpp_llmgpt/checkpoints",
            "/tmp/llmgpt_checkpoints",
        ]
        for cp_dir in checkpoint_dirs:
            if os.path.exists(cp_dir) and os.listdir(cp_dir):
                opps.append(Opportunity(
                    opportunity_id=f"license-{hashlib.sha256(cp_dir.encode()).hexdigest()[:8]}",
                    activity=RevenueActivity.MODEL_LICENSE,
                    description=f"License trained model from {cp_dir}",
                    estimated_revenue_usd=50.0,
                    estimated_cost_usd=0.5,
                    confidence=0.3,
                    payload={"checkpoint_dir": cp_dir},
                ))
        return opps

    def evaluate_opportunity(self, opp: Opportunity) -> dict:
        """Evaluate whether to pursue an opportunity based on OS state."""
        # Check treasury budget
        budget = self.treasury.get_budget_for("economic_engine", opp.activity.value)
        if opp.estimated_cost_usd > budget:
            return {
                "decision": "reject",
                "reason": f"Cost ${opp.estimated_cost_usd} exceeds budget ${budget:.2f}",
                "opportunity": opp.opportunity_id,
            }

        # Check expected ROI
        if opp.expected_roi < 10 and opp.confidence < 0.6:
            return {
                "decision": "reject",
                "reason": f"Low ROI ({opp.expected_roi:.1f}%) and low confidence ({opp.confidence})",
                "opportunity": opp.opportunity_id,
            }

        # Check runway
        runway = self.treasury.get_runway_days()
        if runway is not None and runway < 7 and opp.estimated_cost_usd > 5:
            return {
                "decision": "reject",
                "reason": f"Low runway ({runway:.1f} days), conserving funds",
                "opportunity": opp.opportunity_id,
            }

        return {
            "decision": "accept",
            "reason": f"Expected profit ${opp.expected_profit:.2f} (ROI {opp.expected_roi:.1f}%)",
            "opportunity": opp.opportunity_id,
            "recommended_budget": min(opp.estimated_cost_usd, budget),
        }

    def execute_opportunity(self, opp: Opportunity) -> dict:
        """Execute a revenue-generating opportunity."""
        # Request governance approval
        action_class = ActionClass.RISKY if opp.activity == RevenueActivity.TRADING else ActionClass.STANDARD
        if opp.estimated_cost_usd > 50:
            action_class = ActionClass.CRITICAL

        req = self.governance.request_action(
            action_type=f"execute_{opp.activity.value}",
            action_class=action_class,
            description=opp.description,
            estimated_cost_usd=opp.estimated_cost_usd,
            actor="economic_engine",
            payload=opp.payload,
        )

        if req.approval_state.value not in ("approved", "bypassed_simulation"):
            return {
                "success": False,
                "error": f"Not approved: {req.approval_state.value}",
                "request_id": req.request_id,
            }

        # Record cost estimate
        self.treasury.record_estimate("economic_engine", opp.activity.value,
                                       opp.estimated_cost_usd, opp.description)

        # Execute based on activity type
        if opp.activity == RevenueActivity.MARKETPLACE_BUILD:
            result = self._execute_marketplace_build(opp)
        elif opp.activity == RevenueActivity.TRADING:
            result = self._execute_trading(opp)
        elif opp.activity == RevenueActivity.COMPUTE_RENTAL:
            result = self._execute_compute_rental(opp)
        elif opp.activity == RevenueActivity.MODEL_LICENSE:
            result = self._execute_model_license(opp)
        else:
            result = {"success": False, "error": "Unknown activity type"}

        # Record actual results
        actual_cost = result.get("actual_cost_usd", opp.estimated_cost_usd)
        revenue = result.get("revenue_usd", 0.0)

        self.governance.record_execution(req.request_id, result, actual_cost)
        self.treasury.record_cost("economic_engine", opp.activity.value, actual_cost,
                                   opp.description, result)
        if revenue > 0:
            self.treasury.record_revenue("economic_engine", opp.activity.value, revenue,
                                         opp.description, result)

        # Submit ZK-PoPC proof for successful productive work
        if self.zk_popc and result.get("success"):
            self.zk_popc.submit_proof_from_activity(
                activity_id=opp.opportunity_id,
                prover="economic_engine",
                circuit_identifier=opp.activity.value,
                estimated_cost_usd=actual_cost,
                revenue_usd=revenue,
                compute_units=result.get("compute_units", 0),
            )

        self.active_activities[opp.opportunity_id] = {
            "opportunity": opp,
            "result": result,
            "started_at": time.time(),
        }
        self._persist()
        return result

    def _execute_marketplace_build(self, opp: Opportunity) -> dict:
        """Execute a marketplace build job."""
        job_id = opp.payload.get("job_id")
        if not job_id:
            return {"success": False, "error": "No job_id in payload"}

        try:
            from membra_sdk.profit_loop import MembraProfitLoop
            loop = MembraProfitLoop()
            # In simulation, we would claim and build
            # In production, this needs real buyer interaction
            return {
                "success": True,
                "job_id": job_id,
                "revenue_usd": 0.0,  # Revenue only realized on buyer approval
                "actual_cost_usd": 0.5,
                "status": "claimed_pending_build",
                "note": "Real revenue requires buyer approval and payment settlement",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "actual_cost_usd": 0.1}

    def _execute_trading(self, opp: Opportunity) -> dict:
        """Start or manage trading activity."""
        if self.trading_process and self.trading_process.poll() is None:
            return {
                "success": True,
                "status": "already_running",
                "revenue_usd": 0.0,
                "actual_cost_usd": 0.0,
            }

        trading_script = "/Users/alep/Downloads/membra-economics/membra-finance/01_Trading_Systems/gate_micro_mm.py"
        if not os.path.exists(trading_script):
            return {
                "success": False,
                "error": f"Trading script not found: {trading_script}",
                "actual_cost_usd": 0.0,
            }

        try:
            # Start trading as a subprocess (with dry-run if no real keys)
            env = os.environ.copy()
            if self.governance.policy.simulation_mode:
                env["DRY_RUN"] = "1"
                env["LOG_LEVEL"] = "INFO"

            self.trading_process = subprocess.Popen(
                ["python3", trading_script],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return {
                "success": True,
                "status": "started",
                "pid": self.trading_process.pid,
                "revenue_usd": 0.0,
                "actual_cost_usd": 0.0,
                "warning": "Trading is HIGH RISK. Monitor closely.",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "actual_cost_usd": 0.0}

    def _execute_compute_rental(self, opp: Opportunity) -> dict:
        """Execute compute rental — advertise capacity and process jobs."""
        return {
            "success": True,
            "status": "advertising_capacity",
            "workers": opp.payload.get("workers_available", 0),
            "revenue_usd": 0.0,
            "actual_cost_usd": 0.1,
            "note": "Compute rental requires buyer network. Revenue on job completion.",
        }

    def _execute_model_license(self, opp: Opportunity) -> dict:
        """Execute model licensing — prepare license package."""
        cp_dir = opp.payload.get("checkpoint_dir")
        return {
            "success": True,
            "status": "license_package_prepared",
            "checkpoint_dir": cp_dir,
            "revenue_usd": 0.0,
            "actual_cost_usd": 0.1,
            "note": "Licensing requires sales channel. Revenue on license purchase.",
        }

    def stop_trading(self) -> dict:
        """Stop trading process immediately."""
        if self.trading_process and self.trading_process.poll() is None:
            self.trading_process.terminate()
            try:
                self.trading_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.trading_process.kill()
            return {"success": True, "status": "trading_stopped"}
        return {"success": True, "status": "trading_not_running"}

    def get_status(self) -> dict:
        return {
            "trading_enabled": self.trading_enabled,
            "trading_running": self.trading_process is not None and self.trading_process.poll() is None,
            "active_opportunities": len(self.opportunities),
            "active_activities": len(self.active_activities),
            "total_history": len(self.activity_history),
        }

    def _persist(self):
        try:
            data = {
                "trading_enabled": self.trading_enabled,
                "active_activities": {k: {
                    "started_at": v["started_at"],
                    "opportunity_id": v["opportunity"].opportunity_id,
                } for k, v in self.active_activities.items()},
                "activity_history": self.activity_history[-100:],  # Keep last 100
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass

    def _load(self):
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            self.trading_enabled = data.get("trading_enabled", False)
        except Exception:
            pass
