#!/usr/bin/env python3
"""LLM OS CLI — Command-line interface for the autonomous operating system.

Usage:
    python -m llm_os status          Show OS status
    python -m llm_os start           Start autonomous loop
    python -m llm_os start --once    Run one cycle and exit
    python -m llm_os stop            Stop running OS
    python -m llm_os halt            Emergency halt
    python -m llm_os resume          Resume from halt
    python -m llm_os approve <id>    Approve pending request
    python -m llm_os scan            Scan for economic opportunities
    python -m llm_os build <type>    Build a system (web_app, api, bot, etc.)
    python -m llm_os train <name>    Train a new LLM
    python -m llm_os treasury        Show treasury status
    python -m llm_os history        Show decision history
    python -m llm_os serve          Start VM LLM OS Online web server
"""

import json
import sys
import time

from llm_os.governance import Policy
from llm_os.kernel import Kernel


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    command = args[0]

    # Initialize kernel
    from llm_os.governance import ActionClass
    policy = Policy(
        name="interactive_default",
        action_classes={ActionClass.SAFE, ActionClass.STANDARD, ActionClass.RISKY},
        daily_cost_limit_usd=50.0,
        single_action_cost_limit_usd=25.0,
        simulation_mode=True,
        allow_model_training=True,
        allow_real_payments=False,
        allow_production_deploy=False,
    )

    kernel = Kernel(policy=policy)

    if command == "status":
        status = kernel.get_status()
        print(json.dumps(status, indent=2, default=str))

    elif command == "start":
        once = "--once" in args
        max_loops = None
        for i, arg in enumerate(args):
            if arg == "--max-loops" and i + 1 < len(args):
                max_loops = int(args[i + 1])

        if once:
            kernel.start(autonomous=False)
        else:
            kernel.start(autonomous=True, max_loops=max_loops)

    elif command == "scan":
        print("[CLI] Scanning for opportunities...")
        opps = kernel.economic_engine.scan_opportunities()
        print(f"[CLI] Found {len(opps)} opportunities:")
        for opp in opps:
            print(f"  - {opp.opportunity_id}: {opp.description}")
            print(f"    Expected profit: ${opp.expected_profit:.2f} (cost: ${opp.estimated_cost_usd}, rev: ${opp.estimated_revenue_usd})")

    elif command == "build":
        build_type = args[1] if len(args) > 1 else "generic"
        print(f"[CLI] Building {build_type}...")
        plan = kernel.system_builder.analyze_requirements({
            "type": build_type,
            "description": f"CLI-requested {build_type}",
            "requirements": ["functional", "tested"],
        })
        result = kernel.system_builder.generate_code(plan)
        print(json.dumps(result, indent=2, default=str))

        if result.get("success"):
            test_result = kernel.system_builder.run_tests(plan.plan_id)
            print("[CLI] Test result:")
            print(json.dumps(test_result, indent=2, default=str))

            final = kernel.system_builder.finalize_build(plan.plan_id)
            print("[CLI] Finalization:")
            print(json.dumps(final, indent=2, default=str))

    elif command == "train":
        name = args[1] if len(args) > 1 else "auto_model"
        print(f"[CLI] Creating model spec: {name}")
        spec = kernel.llm_factory.create_model_spec(name, "General purpose LLM")
        print(f"[CLI] Training {spec.model_id}...")
        result = kernel.llm_factory.train_model(spec.model_id)
        print(json.dumps(result, indent=2, default=str))

    elif command == "treasury":
        print(json.dumps(kernel.treasury.get_status(), indent=2, default=str))

    elif command == "history":
        for key, record in sorted(kernel.memory.items()):
            print(f"\n--- {key} ---")
            print(json.dumps(record, indent=2, default=str))

    elif command == "halt":
        reason = " ".join(args[1:]) if len(args) > 1 else "CLI emergency halt"
        kernel.emergency_halt(reason)
        print("[CLI] OS halted.")

    elif command == "resume":
        kernel.emergency_resume()
        print("[CLI] OS resumed.")

    elif command == "approve":
        req_id = args[1] if len(args) > 1 else None
        if req_id:
            kernel.approve_pending(req_id)
            print(f"[CLI] Approved {req_id}")
        else:
            print("[CLI] Usage: approve <request_id>")

    elif command == "serve":
        port = 8080
        host = "0.0.0.0"
        for i, arg in enumerate(args):
            if arg == "--port" and i + 1 < len(args):
                port = int(args[i + 1])
            if arg == "--host" and i + 1 < len(args):
                host = args[i + 1]
        print(f"[CLI] Starting VM LLM OS Online on http://{host}:{port}")
        from llm_os.server import app
        import uvicorn
        uvicorn.run(app, host=host, port=port)

    else:
        print(f"[CLI] Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
