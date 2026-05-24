"""Kernel — The core autonomous loop of the LLM OS.

The Kernel is the "brain" of the OS. It runs a continuous loop:
1. SENSE: Gather data about opportunities, costs, system health
2. DECIDE: Use economic evaluation to choose the best action
3. PLAN: Break decision into cost-estimated tasks
4. EXECUTE: Run tasks through subsystems
5. VERIFY: Validate outputs and check results
6. LEARN: Update memory and models based on outcomes
7. ACCOUNT: Record all costs and revenue in Treasury

Safety:
- Every loop iteration checks governance status
- Emergency halt stops all non-safe actions
- Daily cost limits enforced by Treasury + Governance
- No real money moves without explicit policy gates
"""

import json
import os
import signal
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from llm_os.economic_engine import EconomicEngine, Opportunity
from llm_os.governance import ActionClass, ApprovalState, Governance, Policy
from llm_os.llm_factory import LLMFactory
from llm_os.system_builder import SystemBuilder
from llm_os.treasury import Treasury
from llm_os.zk_popc_bridge import ZKPoPCBridge


@dataclass
class OSState:
    """Current state of the OS."""
    mode: str = "simulation"  # "simulation" or "production"
    running: bool = False
    loop_count: int = 0
    last_loop_time: float = 0.0
    uptime_start: float = 0.0
    current_focus: Optional[str] = None  # What the OS is currently working on
    health: dict = field(default_factory=dict)


class Kernel:
    """The LLM OS Kernel — autonomous operating system for LLM-driven economics."""

    def __init__(self, policy: Policy = None, starting_balance_usd: float = 0.0):
        # Core governance and treasury
        self.governance = Governance(policy=policy)
        self.treasury = Treasury(starting_balance_usd=starting_balance_usd)

        # ZK-PoPC bridge (initialize before economic engine so it can be injected)
        self.zk_popc = ZKPoPCBridge(self.governance, self.treasury)

        # Subsystems
        self.economic_engine = EconomicEngine(self.governance, self.treasury, zk_popc=self.zk_popc)
        self.system_builder = SystemBuilder(self.governance, self.treasury)
        self.llm_factory = LLMFactory(self.governance, self.treasury)

        # State
        self.state = OSState()
        self.memory: Dict[str, any] = {}
        self.loop_interval_seconds: float = 60.0  # Default: check every minute
        self._shutdown_requested = False

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n[KERNEL] Received signal {signum}, shutting down gracefully...")
        self._shutdown_requested = True
        self.stop()

    def start(self, autonomous: bool = True, max_loops: int = None):
        """Start the OS kernel loop.

        Args:
            autonomous: If True, run continuous loop. If False, run one cycle.
            max_loops: Maximum number of loops (None = infinite).
        """
        self.state.running = True
        self.state.uptime_start = time.time()

        print(f"[KERNEL] LLM OS v0.1.0 starting...")
        print(f"[KERNEL] Mode: {self.governance.policy.name}")
        print(f"[KERNEL] Simulation: {self.governance.policy.simulation_mode}")
        print(f"[KERNEL] Daily limit: ${self.governance.policy.daily_cost_limit_usd}")
        print(f"[KERNEL] Treasury balance: ${self.treasury.balance_usd:.2f}")
        print(f"[KERNEL] Press Ctrl+C to stop\n")

        if autonomous:
            self._run_loop(max_loops)
        else:
            self._loop_cycle()
            self.state.running = False

    def stop(self):
        """Stop the kernel gracefully."""
        self.state.running = False
        # Stop trading if running
        self.economic_engine.stop_trading()
        print("[KERNEL] Stopped.")

    def _safe_json(self, obj: any) -> str:
        """Serialize to JSON, falling back to str() for non-serializable objects."""
        def _default(o):
            if hasattr(o, "__dataclass_fields__"):
                return {k: getattr(o, k) for k in o.__dataclass_fields__}
            if hasattr(o, "value"):
                return o.value
            return str(o)
        try:
            return json.dumps(obj, indent=2, default=_default)
        except Exception:
            return str(obj)

    def _run_loop(self, max_loops: int = None):
        """Run the main autonomous loop."""
        while self.state.running and not self._shutdown_requested:
            if max_loops and self.state.loop_count >= max_loops:
                print(f"[KERNEL] Max loops ({max_loops}) reached. Stopping.")
                break

            self._loop_cycle()

            if self.state.running and not self._shutdown_requested:
                time.sleep(self.loop_interval_seconds)

    def _loop_cycle(self):
        """Execute one full OS cycle."""
        self.state.loop_count += 1
        self.state.last_loop_time = time.time()
        loop_num = self.state.loop_count

        print(f"\n{'='*60}")
        print(f"[KERNEL] Loop {loop_num} | {time.strftime('%H:%M:%S')}")
        print(f"{'='*60}")

        # 1. SENSE — Check system health, governance, treasury
        health = self._sense()
        print(f"[SENSE] Health: {self._safe_json(health)}")

        if self.governance.is_halted():
            print("[SENSE] OS is HALTED. Skipping cycle.")
            return

        # 2. DECIDE — What should we do?
        decision = self._decide()
        print(f"[DECIDE] Decision: {self._safe_json(decision)}")

        if decision.get("action") == "wait":
            print("[DECIDE] No profitable action. Waiting.")
            self._learn(decision, {}, [], {"all_ok": True, "errors": [], "results_checked": 0})
            self._account()
            print(f"[KERNEL] Loop {loop_num} complete.")
            return

        # 3. PLAN — Break into tasks
        plan = self._plan(decision)
        print(f"[PLAN] Plan: {self._safe_json(plan)}")

        # 4. EXECUTE — Run tasks
        results = self._execute(plan)
        print(f"[EXECUTE] Results: {self._safe_json(results)}")

        # 5. VERIFY — Check outputs
        verified = self._verify(results)
        print(f"[VERIFY] Verified: {self._safe_json(verified)}")

        # 6. LEARN — Update memory
        self._learn(decision, plan, results, verified)

        # 7. ACCOUNT — Final accounting
        self._account()

        # 8. ZK-PoPC — Attest and mint from verified productive work
        self.run_zk_popc_cycle()

        print(f"[KERNEL] Loop {loop_num} complete.")

    def _sense(self) -> dict:
        """Gather system state and health metrics."""
        gov_status = self.governance.get_status()
        treasury_status = self.treasury.get_status()
        econ_status = self.economic_engine.get_status()
        builder_status = self.system_builder.get_status()
        factory_status = self.llm_factory.get_status()
        zkpopc_status = self.zk_popc.get_stats()

        # System health
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            sys_health = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
            }
        except ImportError:
            sys_health = {"note": "psutil not installed"}

        health = {
            "governance": gov_status,
            "treasury": {
                "balance_usd": treasury_status["balance_usd"],
                "runway_days": treasury_status["runway_days"],
                "daily_burn": treasury_status["daily_burn_7d"],
            },
            "economic_engine": econ_status,
            "system_builder": builder_status,
            "llm_factory": factory_status,
            "zk_popc": zkpopc_status,
            "system": sys_health,
            "loop_count": self.state.loop_count,
            "uptime_seconds": time.time() - self.state.uptime_start,
        }

        self.state.health = health
        return health

    def _decide(self) -> dict:
        """Decide what action to take based on current state."""
        # Check if we have budget
        if self.treasury.balance_usd <= 0 and not self.governance.policy.simulation_mode:
            return {"action": "wait", "reason": "No funds available"}

        # Scan for opportunities
        opportunities = self.economic_engine.scan_opportunities()
        if not opportunities:
            return {"action": "wait", "reason": "No opportunities detected"}

        # Evaluate each opportunity
        best_opp = None
        best_score = -float("inf")

        for opp in opportunities:
            eval_result = self.economic_engine.evaluate_opportunity(opp)
            if eval_result.get("decision") != "accept":
                continue

            # Score = expected profit * confidence
            score = opp.expected_profit * opp.confidence
            if score > best_score:
                best_score = score
                best_opp = opp

        if best_opp:
            return {
                "action": "execute_opportunity",
                "opportunity_id": best_opp.opportunity_id,
                "activity": best_opp.activity.value,
                "expected_profit": best_opp.expected_profit,
                "confidence": best_opp.confidence,
                "description": best_opp.description,
            }

        # No good opportunities — consider building capacity
        # If we have idle resources, build a model or system
        if self.treasury.balance_usd > 20 or self.governance.policy.simulation_mode:
            # Check if we should train a model
            if len(self.llm_factory.models) < 2:
                return {
                    "action": "build_capacity",
                    "subtype": "train_model",
                    "reason": "Low model inventory. Building LLM capacity.",
                }
            # Check if we should build a system
            if len(self.system_builder.build_history) < 2:
                return {
                    "action": "build_capacity",
                    "subtype": "build_system",
                    "reason": "Low system inventory. Building software capacity.",
                }

        return {"action": "wait", "reason": "No profitable action identified"}

    def _plan(self, decision: dict) -> dict:
        """Create a plan for the decided action."""
        action = decision.get("action")

        if action == "execute_opportunity":
            opp_id = decision.get("opportunity_id")
            opp = next((o for o in self.economic_engine.opportunities if o.opportunity_id == opp_id), None)
            if not opp:
                return {"error": "Opportunity not found"}
            return {
                "tasks": [
                    {"subsystem": "economic_engine", "method": "execute_opportunity", "args": [opp]},
                ],
                "estimated_cost": opp.estimated_cost_usd,
                "expected_revenue": opp.estimated_revenue_usd,
            }

        elif action == "build_capacity":
            subtype = decision.get("subtype")
            if subtype == "train_model":
                return {
                    "tasks": [
                        {"subsystem": "llm_factory", "method": "create_and_train", "args": []},
                    ],
                    "estimated_cost": 5.0,
                    "expected_revenue": 0.0,  # Capacity building, not immediate revenue
                }
            elif subtype == "build_system":
                return {
                    "tasks": [
                        {"subsystem": "system_builder", "method": "create_and_build", "args": ["api_service"]},
                    ],
                    "estimated_cost": 3.0,
                    "expected_revenue": 0.0,
                }

        return {"tasks": [], "estimated_cost": 0.0, "expected_revenue": 0.0}

    def _execute(self, plan: dict) -> List[dict]:
        """Execute the planned tasks."""
        results = []
        tasks = plan.get("tasks", [])

        for task in tasks:
            subsystem = task.get("subsystem")
            method = task.get("method")
            args = task.get("args", [])

            try:
                if subsystem == "economic_engine":
                    target = self.economic_engine
                elif subsystem == "system_builder":
                    target = self.system_builder
                elif subsystem == "llm_factory":
                    target = self.llm_factory
                else:
                    results.append({"subsystem": subsystem, "error": "Unknown subsystem"})
                    continue

                # Handle special methods
                if method == "execute_opportunity" and args:
                    result = target.execute_opportunity(args[0])
                elif method == "create_and_train":
                    spec = target.create_model_spec("auto_model", "General purpose LLM")
                    result = target.train_model(spec.model_id)
                elif method == "create_and_build":
                    plan_obj = target.analyze_requirements({
                        "type": args[0] if args else "generic",
                        "description": "Autonomous build",
                        "requirements": ["functional", "tested"],
                    })
                    result = target.generate_code(plan_obj)
                    if result.get("success"):
                        test_result = target.run_tests(plan_obj.plan_id)
                        final = target.finalize_build(plan_obj.plan_id)
                        result = {"generate": result, "test": test_result, "finalize": final}
                else:
                    func = getattr(target, method, None)
                    if func:
                        result = func(*args)
                    else:
                        result = {"error": f"Method {method} not found"}

                results.append({"subsystem": subsystem, "method": method, "result": result})
            except Exception as e:
                results.append({"subsystem": subsystem, "method": method, "error": str(e)})

        return results

    def _verify(self, results: List[dict]) -> dict:
        """Verify that execution results are valid."""
        all_ok = True
        errors = []

        for r in results:
            if "error" in r:
                all_ok = False
                errors.append(f"{r.get('subsystem')}/{r.get('method')}: {r['error']}")
            elif "result" in r:
                res = r["result"]
                if isinstance(res, dict) and not res.get("success", True):
                    all_ok = False
                    errors.append(f"{r.get('subsystem')}/{r.get('method')}: {res.get('error', 'Failed')}")

        return {
            "all_ok": all_ok,
            "errors": errors,
            "results_checked": len(results),
        }

    def _learn(self, decision: dict, plan: dict, results: List[dict], verified: dict):
        """Update OS memory based on cycle outcomes."""
        cycle_record = {
            "loop": self.state.loop_count,
            "timestamp": time.time(),
            "decision": decision,
            "plan": plan,
            "results": results,
            "verified": verified,
        }
        self.memory[f"cycle_{self.state.loop_count}"] = cycle_record

        # Update focus based on results
        if verified.get("all_ok") and decision.get("action") != "wait":
            self.state.current_focus = decision.get("activity") or decision.get("subtype")
        else:
            self.state.current_focus = None

    def _account(self):
        """Record final accounting for the cycle."""
        # This is handled by individual subsystems calling treasury
        # Here we just log the state
        pnl = self.treasury.get_pnl(days=1)
        print(f"[ACCOUNT] Daily P&L: ${pnl['profit_usd']:.2f} (Revenue: ${pnl['revenue_usd']:.2f}, Costs: ${pnl['costs_usd']:.2f})")

    def run_zk_popc_cycle(self) -> dict:
        """Run the ZK-PoPC attestation and mint cycle."""
        results = {"attested": 0, "minted": {}}

        # In simulation mode, auto-attest pending proofs from verifier nodes
        if self.governance.policy.simulation_mode:
            for proof_id, proof in list(self.zk_popc.proofs.items()):
                if proof.status.value == "pending" and proof.attestation_count < self.zk_popc.MIN_VERIFIERS_REQUIRED:
                    # Simulate two independent verifiers
                    self.zk_popc.attest_proof(proof_id, "simulated_verifier_1", {})
                    self.zk_popc.attest_proof(proof_id, "simulated_verifier_2", {})
                    results["attested"] += 1

        # Mint all verified proofs
        results["minted"] = self.zk_popc.batch_mint_verified_proofs()
        total_minted = sum(results["minted"].values())
        if total_minted > 0:
            print(f"[ZK-PoPC] Minted {len(results['minted'])} proofs, total tokens: {total_minted}")
        return results

    def get_status(self) -> dict:
        """Get full OS status."""
        return {
            "os_version": "0.1.0",
            "state": {
                "running": self.state.running,
                "mode": self.state.mode,
                "loop_count": self.state.loop_count,
                "uptime_seconds": time.time() - self.state.uptime_start if self.state.uptime_start else 0,
                "current_focus": self.state.current_focus,
            },
            "governance": self.governance.get_status(),
            "treasury": self.treasury.get_status(),
            "economic_engine": self.economic_engine.get_status(),
            "system_builder": self.system_builder.get_status(),
            "llm_factory": self.llm_factory.get_status(),
            "zk_popc": self.zk_popc.get_stats(),
        }

    def approve_pending(self, request_id: str) -> bool:
        """Human operator approves a pending governance request."""
        return self.governance.approve_request(request_id)

    def reject_pending(self, request_id: str, reason: str = "") -> bool:
        """Human operator rejects a pending governance request."""
        return self.governance.reject_request(request_id, reason)

    def emergency_halt(self, reason: str):
        """Emergency halt the OS."""
        self.governance.halt(reason)
        self.economic_engine.stop_trading()

    def emergency_resume(self):
        """Resume from halt."""
        self.governance.resume()
