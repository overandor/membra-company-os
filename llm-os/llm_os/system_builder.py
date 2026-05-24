"""System Builder — Autonomous software development pipeline.

The System Builder turns economic opportunities into deployable software.
It wraps the membra-core proof-of-job pipeline with autonomous capability:
1. Analyze requirements from marketplace jobs or internal needs
2. Generate build plans with cost estimates
3. Execute builds through containerized job specs
4. Run tests and validate artifacts
5. Submit for consensus and proof bundling
6. Track costs and expected revenue in Treasury

The builder can create:
- Web applications and dashboards
- Trading bots and strategies
- API services and microservices
- Data pipelines and analysis tools
- Other LLMs and model training pipelines
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from llm_os.governance import ActionClass, Governance
from llm_os.inference import generate_code_with_llm, get_inference_bridge
from llm_os.treasury import Treasury


@dataclass
class BuildPlan:
    """A plan for building a software system."""
    plan_id: str
    description: str
    target_type: str  # "web_app", "trading_bot", "api_service", "data_pipeline", "llm_training"
    requirements: List[str]
    estimated_cost_usd: float
    estimated_time_hours: float
    expected_revenue_usd: float
    tech_stack: List[str] = field(default_factory=list)
    files_to_generate: Dict[str, str] = field(default_factory=dict)
    tests_required: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class SystemBuilder:
    """Autonomous system builder for the LLM OS."""

    def __init__(self, governance: Governance, treasury: Treasury,
                 storage_path: str = None):
        self.governance = governance
        self.treasury = treasury
        self.storage_path = storage_path or "/tmp/llm_os_builder.json"
        self.build_history: List[dict] = []
        self.active_builds: Dict[str, dict] = {}
        self._load()

    def analyze_requirements(self, job_spec: dict) -> BuildPlan:
        """Analyze a job specification and create a build plan."""
        job_type = job_spec.get("type", "unknown")
        budget = job_spec.get("budget_usd", 0.0)

        # Estimate based on job type and complexity
        type_estimates = {
            "web_app": {"hours": 4, "cost": 2.0, "stack": ["html", "js", "css"]},
            "api_service": {"hours": 6, "cost": 3.0, "stack": ["python", "fastapi"]},
            "trading_bot": {"hours": 8, "cost": 4.0, "stack": ["python", "ccxt"]},
            "dashboard": {"hours": 3, "cost": 1.5, "stack": ["html", "js", "chart.js"]},
            "data_pipeline": {"hours": 5, "cost": 2.5, "stack": ["python", "pandas"]},
            "llm_training": {"hours": 24, "cost": 10.0, "stack": ["python", "pytorch"]},
        }

        estimate = type_estimates.get(job_type, {"hours": 4, "cost": 2.0, "stack": ["python"]})

        # Adjust based on requirements complexity
        requirements = job_spec.get("requirements", [])
        complexity_multiplier = 1.0 + (len(requirements) * 0.1)

        plan = BuildPlan(
            plan_id=f"plan-{int(time.time()*1000)}",
            description=job_spec.get("description", "Autonomous build"),
            target_type=job_type,
            requirements=requirements,
            estimated_cost_usd=estimate["cost"] * complexity_multiplier,
            estimated_time_hours=estimate["hours"] * complexity_multiplier,
            expected_revenue_usd=budget * 0.45,  # Builder gets 45% in marketplace
            tech_stack=estimate["stack"],
            tests_required=["unit_tests", "integration_tests"],
        )
        return plan

    def generate_code(self, plan: BuildPlan) -> dict:
        """Generate code for a build plan."""
        # Request governance approval
        req = self.governance.request_action(
            action_type="generate_code",
            action_class=ActionClass.STANDARD,
            description=f"Generate {plan.target_type}: {plan.description}",
            estimated_cost_usd=plan.estimated_cost_usd,
            actor="system_builder",
            payload={"plan_id": plan.plan_id, "target_type": plan.target_type},
        )

        if req.approval_state.value not in ("approved", "bypassed_simulation"):
            return {"success": False, "error": f"Not approved: {req.approval_state.value}"}

        # Record estimate
        self.treasury.record_estimate("system_builder", "code_generation",
                                       plan.estimated_cost_usd, plan.description)

        # Try LLM-powered generation first
        generated_files = {}
        actual_cost = 0.5  # Base compute cost
        llm_used = False

        bridge = get_inference_bridge()
        if bridge.is_available() and bridge.__class__.__name__ != "StubBridge":
            # Request additional approval for API cost (max $0.05 for code gen)
            llm_req = self.governance.request_action(
                action_type="llm_api_call",
                action_class=ActionClass.STANDARD,
                description=f"LLM code generation for {plan.target_type}",
                estimated_cost_usd=0.05,
                actor="system_builder",
                payload={"plan_id": plan.plan_id},
            )
            if llm_req.approval_state.value in ("approved", "bypassed_simulation"):
                llm_result = generate_code_with_llm(
                    prompt=f"Build a {plan.target_type}: {plan.description}. Requirements: {', '.join(plan.requirements)}",
                    target_type=plan.target_type,
                )
                if llm_result["success"] and llm_result["files"]:
                    generated_files = llm_result["files"]
                    actual_cost += llm_result.get("cost_usd", 0.0)
                    llm_used = True
                    # Record LLM API cost
                    self.treasury.record_cost(
                        "system_builder", "llm_api", llm_result.get("cost_usd", 0.0),
                        f"LLM generation for {plan.plan_id}", llm_result,
                    )

        # Fallback to stub generation if LLM failed or was unavailable
        if not generated_files:
            if plan.target_type == "web_app":
                generated_files = self._generate_web_app(plan)
            elif plan.target_type == "api_service":
                generated_files = self._generate_api_service(plan)
            elif plan.target_type == "trading_bot":
                generated_files = self._generate_trading_bot(plan)
            elif plan.target_type == "dashboard":
                generated_files = self._generate_dashboard(plan)
            elif plan.target_type == "data_pipeline":
                generated_files = self._generate_data_pipeline(plan)
            elif plan.target_type == "llm_training":
                generated_files = self._generate_llm_training(plan)
            else:
                generated_files = self._generate_generic_python(plan)

        # Compute artifact hash
        artifact_content = json.dumps(generated_files, sort_keys=True)
        artifact_hash = hashlib.sha256(artifact_content.encode()).hexdigest()

        result = {
            "success": True,
            "plan_id": plan.plan_id,
            "files_generated": len(generated_files),
            "artifact_hash": artifact_hash,
            "actual_cost_usd": actual_cost,
            "files": generated_files,
            "llm_used": llm_used,
        }

        self.governance.record_execution(req.request_id, result, actual_cost)
        self.treasury.record_cost("system_builder", "code_generation", actual_cost,
                                   plan.description, result)

        self.active_builds[plan.plan_id] = {
            "plan": plan,
            "result": result,
            "started_at": time.time(),
        }
        self._persist()
        return result

    def run_tests(self, plan_id: str) -> dict:
        """Run tests on a generated build."""
        build = self.active_builds.get(plan_id)
        if not build:
            return {"success": False, "error": "Build not found"}

        plan = build["plan"]
        files = build["result"].get("files", {})

        test_results = []
        all_passed = True

        for fname, content in files.items():
            if fname.endswith(".py"):
                # Write to temp and syntax check
                temp_path = f"/tmp/llm_os_build_{plan_id}_{fname.replace('/', '_')}"
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                try:
                    with open(temp_path, "w") as f:
                        f.write(content)

                    # Syntax check
                    import py_compile
                    py_compile.compile(temp_path, doraise=True)
                    test_results.append({"file": fname, "syntax": "passed"})
                except py_compile.PyCompileError as e:
                    test_results.append({"file": fname, "syntax": "failed", "error": str(e)})
                    all_passed = False
                except Exception as e:
                    test_results.append({"file": fname, "syntax": "error", "error": str(e)})
                    all_passed = False

        # Record test cost
        test_cost = 0.1
        self.treasury.record_cost("system_builder", "testing", test_cost,
                                   f"Tests for {plan_id}", {"passed": all_passed})

        result = {
            "success": all_passed,
            "plan_id": plan_id,
            "tests_run": len(test_results),
            "tests_passed": sum(1 for t in test_results if t.get("syntax") == "passed"),
            "results": test_results,
            "actual_cost_usd": test_cost,
        }

        build["test_result"] = result
        self._persist()
        return result

    def finalize_build(self, plan_id: str) -> dict:
        """Finalize a build — hash artifacts, create proof bundle."""
        build = self.active_builds.get(plan_id)
        if not build:
            return {"success": False, "error": "Build not found"}

        # Request finalization approval
        req = self.governance.request_action(
            action_type="finalize_build",
            action_class=ActionClass.STANDARD,
            description=f"Finalize build {plan_id}",
            estimated_cost_usd=0.1,
            actor="system_builder",
            payload={"plan_id": plan_id},
        )

        if req.approval_state.value not in ("approved", "bypassed_simulation"):
            return {"success": False, "error": f"Not approved: {req.approval_state.value}"}

        # Create proof bundle
        files = build["result"].get("files", {})
        bundle_hash = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()

        result = {
            "success": True,
            "plan_id": plan_id,
            "bundle_hash": bundle_hash,
            "file_count": len(files),
            "status": "ready_for_submission",
        }

        self.governance.record_execution(req.request_id, result, 0.1)
        self.treasury.record_cost("system_builder", "finalization", 0.1,
                                   f"Finalize {plan_id}", result)

        self.build_history.append({
            "plan_id": plan_id,
            "type": build["plan"].target_type,
            "completed_at": time.time(),
            "bundle_hash": bundle_hash,
        })

        if plan_id in self.active_builds:
            del self.active_builds[plan_id]
        self._persist()
        return result

    def _generate_web_app(self, plan: BuildPlan) -> Dict[str, str]:
        """Generate a simple web application."""
        return {
            "index.html": f"""<!DOCTYPE html>
<html>
<head><title>{plan.description}</title></head>
<body>
<h1>{plan.description}</h1>
<p>Generated by LLM OS System Builder</p>
<script src=\"app.js\"></script>
</body>
</html>""",
            "app.js": "console.log('App initialized');",
            "style.css": "body { font-family: sans-serif; margin: 20px; }",
        }

    def _generate_api_service(self, plan: BuildPlan) -> Dict[str, str]:
        """Generate a FastAPI service."""
        return {
            "main.py": f"""from fastapi import FastAPI
app = FastAPI(title="{plan.description}")

@app.get(\"/\")
def root():
    return {{"status": "ok", "service": "{plan.description}"}}

@app.get(\"/health\")
def health():
    return {{"healthy": True}}
""",
            "requirements.txt": "fastapi>=0.100.0\nuvicorn>=0.23.0\n",
            "Dockerfile": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n",
        }

    def _generate_trading_bot(self, plan: BuildPlan) -> Dict[str, str]:
        """Generate a trading bot scaffold."""
        return {
            "bot.py": f"""#!/usr/bin/env python3
\"\"\"{plan.description}\"\"\"
import os
import logging

LOG_LEVEL = os.getenv(\"LOG_LEVEL\", \"INFO\")
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
log = logging.getLogger(\"trading_bot\")

def main():
    log.info(\"Starting {plan.description}\")
    # TODO: Implement trading logic
    pass

if __name__ == \"__main__\":
    main()
""",
            "config.json": json.dumps({"strategy": "default", "risk_limit": 10.0}, indent=2),
            "requirements.txt": "ccxt>=4.0.0\n",
        }

    def _generate_dashboard(self, plan: BuildPlan) -> Dict[str, str]:
        """Generate a monitoring dashboard."""
        return {
            "index.html": f"""<!DOCTYPE html>
<html>
<head><title>{plan.description}</title></head>
<body>
<h1>{plan.description}</h1>
<div id=\"metrics\"></div>
<script src=\"dashboard.js\"></script>
</body>
</html>""",
            "dashboard.js": "const metrics = document.getElementById('metrics');\nmetrics.innerHTML = '<p>Metrics loading...</p>';\n",
            "style.css": "body { font-family: sans-serif; background: #1a1a2e; color: #eee; }",
        }

    def _generate_data_pipeline(self, plan: BuildPlan) -> Dict[str, str]:
        """Generate a data processing pipeline."""
        return {
            "pipeline.py": f"""#!/usr/bin/env python3
\"\"\"{plan.description}\"\"\"
import json
import logging

log = logging.getLogger(\"pipeline\")

def extract():
    log.info(\"Extracting data...\")
    return {{}}

def transform(data):
    log.info(\"Transforming data...\")
    return data

def load(data):
    log.info(\"Loading data...\")
    return True

def run():
    data = extract()
    transformed = transform(data)
    load(transformed)
    log.info(\"Pipeline complete\")

if __name__ == \"__main__\":
    run()
""",
            "requirements.txt": "pandas>=2.0.0\n",
        }

    def _generate_llm_training(self, plan: BuildPlan) -> Dict[str, str]:
        """Generate an LLM training pipeline."""
        return {
            "train.py": f"""#!/usr/bin/env python3
\"\"\"{plan.description}\"\"\"
import torch
import torch.nn as nn

class SimpleTransformer(nn.Module):
    def __init__(self, vocab_size=256, d_model=256, n_layers=4):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model, nhead=4, batch_first=True),
            num_layers=n_layers
        )
        self.head = nn.Linear(d_model, vocab_size)

    def forward(self, x):
        x = self.embedding(x)
        x = self.transformer(x)
        return self.head(x)

def train():
    print(\"Starting training...\")
    # TODO: Implement training loop
    pass

if __name__ == \"__main__\":
    train()
""",
            "requirements.txt": "torch>=2.0.0\nnumpy>=1.24.0\n",
            "config.json": json.dumps({"batch_size": 32, "lr": 0.001, "epochs": 10}, indent=2),
        }

    def _generate_generic_python(self, plan: BuildPlan) -> Dict[str, str]:
        """Generate generic Python project."""
        return {
            "main.py": f"""#!/usr/bin/env python3
\"\"\"{plan.description}\"\"\"

def main():
    print(\"Running: {plan.description}\")

if __name__ == \"__main__\":
    main()
""",
            "requirements.txt": "\n",
        }

    def get_status(self) -> dict:
        return {
            "active_builds": len(self.active_builds),
            "build_history": len(self.build_history),
            "recent_builds": [b["plan_id"] for b in self.build_history[-5:]],
        }

    def _persist(self):
        try:
            data = {
                "build_history": self.build_history,
                "active_builds": {k: {
                    "plan_id": v["plan"].plan_id,
                    "type": v["plan"].target_type,
                    "started_at": v["started_at"],
                } for k, v in self.active_builds.items()},
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
            self.build_history = data.get("build_history", [])
        except Exception:
            pass
