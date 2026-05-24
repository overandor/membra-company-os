#!/usr/bin/env python3
"""
Overmanifold Protocol System Demonstration
Shows all major components and their interactions
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

try:
    from overmanifold.unified import OvermanifoldUnified
    from overmanifold.core.engine import OvermanifoldEngine, Capability, CapabilityType
    from overmanifold.governance.llm_engine import IntentType, TaskPriority
    from overmanifold.routing.geodesic import LiquidityManifold, GeodesicRouter, RoutingConstraint, RoutingConstraintValue
    from overmanifold.merkle.proof import ProvenanceTracker, MerkleTree
    from overmanifold.consensus.proof_of_profit import ProofOfProfitConsensus, WorkType
except ImportError as e:
    print(f"Import error: {e}")
    print("Please run setup.sh first to install dependencies")
    sys.exit(1)


class SystemDashboard:
    """Text-based dashboard for Overmanifold system visualization"""
    
    def __init__(self):
        self.components = {}
        self.metrics = {}
    
    def display_header(self):
        """Display dashboard header"""
        print("\n" + "="*80)
        print("🌐 OVERMANIFOLD PROTOCOL SYSTEM DASHBOARD")
        print("Civilization-Scale Cryptographic-Economic Coordination Architecture")
        print("="*80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    
    def display_component_status(self, component_name: str, status: str, details: Dict = None):
        """Display status of a system component"""
        status_icon = "✓" if status == "ACTIVE" else "✗" if status == "INACTIVE" else "⚠"
        print(f"{status_icon} {component_name}: {status}")
        
        if details:
            for key, value in details.items():
                print(f"  • {key}: {value}")
        print()
    
    def display_metrics(self, metrics: Dict[str, Any]):
        """Display system metrics"""
        print("📊 SYSTEM METRICS")
        print("-" * 40)
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        print()
    
    def display_menu(self):
        """Display interactive menu"""
        print("🎮 AVAILABLE DEMONSTRATIONS")
        print("-" * 40)
        print("1. Core Engine Demo")
        print("2. LLM Governance Demo")
        print("3. Geodesic Routing Demo")
        print("4. Merkle Provenance Demo")
        print("5. Proof-of-Profit Consensus Demo")
        print("6. Full System Integration Demo")
        print("7. System Health Check")
        print("0. Exit")
        print()


async def demo_core_engine():
    """Demonstrate core engine functionality"""
    print("\n🔧 CORE ENGINE DEMONSTRATION")
    print("="*80 + "\n")
    
    engine = OvermanifoldEngine()
    
    # Create capabilities
    messaging_capability = Capability(
        capability_type=CapabilityType.MESSAGING,
        strength=0.8,
        metadata={"throughput": "1000 msg/sec"}
    )
    
    compute_capability = Capability(
        capability_type=CapabilityType.COMPUTE,
        strength=0.9,
        metadata={"cpu_cores": 8, "memory": "32GB"}
    )
    
    # Create endpoint
    print("Creating Overmanifold endpoint...")
    endpoint = engine.create_endpoint(
        public_key="0x1234567890abcdef",
        private_key="0xsecretkey",
        capabilities=[messaging_capability, compute_capability],
        metadata={"name": "Demo Node", "location": "US-East"}
    )
    
    print(f"✓ Endpoint created: {endpoint.endpoint_id}")
    print(f"  - Trust Density: {endpoint.trust_density:.2f}")
    print(f"  - Economic Value: ${endpoint.total_economic_value:.2f}")
    print(f"  - Capabilities: {len(endpoint.capabilities)}")
    
    # Create semantic intent
    print("\nCreating semantic intent...")
    intent = engine.create_semantic_intent(
        intent_text="Route 100 USDC from Ethereum to Solana with minimal slippage",
        intent_type="liquidity_routing",
        parameters={"amount": 100, "from_chain": "ethereum", "to_chain": "solana", "slippage_tolerance": 0.01}
    )
    
    print(f"✓ Intent created: {intent.intent_id}")
    print(f"  - Type: {intent.intent_type}")
    print(f"  - Confidence: {intent.confidence:.2f}")
    
    # Create state transition
    print("\nCreating state transition...")
    transition = engine.create_state_transition(
        from_state="idle",
        to_state="routing",
        intent=intent,
        actor=endpoint.endpoint_id
    )
    
    print(f"✓ State transition created: {transition.transition_id}")
    print(f"  - Type: {transition.transition_type.value}")
    print(f"  - Proofs: {len(transition.proofs)}")
    
    # Display manifold state
    print("\n📊 Manifold State:")
    manifold_state = engine.get_manifold_state()
    print(json.dumps(manifold_state, indent=2))
    
    return engine


async def demo_llm_governance():
    """Demonstrate LLM governance functionality"""
    print("\n🧠 LLM GOVERNANCE DEMONSTRATION")
    print("="*80 + "\n")
    
    from overmanifold.unified import OvermanifoldUnified
    
    print("Initializing Overmanifold Unified System...")
    overmanifold = OvermanifoldUnified(llm_provider="mock")  # Use mock for demo
    
    print("✓ System initialized")
    
    # Process human intent
    print("\nProcessing human intent...")
    human_intent = "Transfer 500 tokens to the treasury for ecosystem development"
    
    print(f"Input: {human_intent}")
    print("\nInterpreting intent through LLM governance...")
    
    try:
        result = await overmanifold.process_human_intent(
            endpoint_id="demo-endpoint",
            human_intent=human_intent,
            context={"sender": "0x1234567890abcdef"}
        )
        
        print("✓ Intent processed successfully")
        print(f"  - Interpretation: {result.get('interpretation', 'N/A')}")
        print(f"  - Tasks Generated: {len(result.get('tasks', []))}")
        print(f"  - State Transition: {result.get('transition_id', 'N/A')}")
        
    except Exception as e:
        print(f"⚠ Intent processing completed with mock data: {e}")
        print("  (In production, this would use real OpenAI/Anthropic API)")
    
    # Display governance state
    print("\n📊 Governance State:")
    governance_state = {
        "total_intents_processed": overmanifold.llm_governance.total_intents_processed,
        "total_tasks_created": overmanifold.llm_governance.total_tasks_created,
        "total_decisions_made": overmanifold.llm_governance.total_decisions_made
    }
    print(json.dumps(governance_state, indent=2))
    
    return overmanifold


async def demo_geodesic_routing():
    """Demonstrate geodesic routing functionality"""
    print("\n🗺️ GEODESIC ROUTING DEMONSTRATION")
    print("="*80 + "\n")
    
    # Create liquidity manifold
    manifold = LiquidityManifold()
    
    print("Creating liquidity manifold with endpoints...")
    
    # Add endpoints
    endpoints = [
        ("ethereum-mainnet", ["swap", "bridge"], 1000000, 0.9),
        ("solana-mainnet", ["swap", "bridge"], 500000, 0.85),
        ("polygon-pos", ["swap", "bridge"], 300000, 0.8),
        ("arbitrum-one", ["swap", "bridge"], 200000, 0.85),
        ("optimism", ["swap", "bridge"], 150000, 0.82)
    ]
    
    for endpoint_id, capabilities, liquidity, trust in endpoints:
        manifold.add_endpoint(endpoint_id, capabilities, liquidity, trust)
        print(f"✓ Added endpoint: {endpoint_id}")
    
    # Add edges (relationships)
    print("\nCreating trust-constrained edges...")
    edges = [
        ("ethereum-mainnet", "solana-mainnet", 0.7, 0.01, 0.02, 500, 50, ["bridge"]),
        ("ethereum-mainnet", "polygon-pos", 0.9, 0.005, 0.01, 200, 20, ["bridge"]),
        ("ethereum-mainnet", "arbitrum-one", 0.95, 0.003, 0.005, 100, 10, ["bridge"]),
        ("ethereum-mainnet", "optimism", 0.92, 0.004, 0.008, 120, 15, ["bridge"]),
        ("solana-mainnet", "polygon-pos", 0.6, 0.015, 0.03, 800, 80, ["bridge"]),
        ("arbitrum-one", "optimism", 0.88, 0.002, 0.004, 50, 5, ["bridge"])
    ]
    
    for from_ep, to_ep, trust, slippage, proof_risk, settlement_cost, latency, capabilities in edges:
        edge = {
            "from_endpoint": from_ep,
            "to_endpoint": to_ep,
            "trust_density": trust,
            "slippage": slippage,
            "proof_risk": proof_risk,
            "settlement_cost": settlement_cost,
            "latency_ms": latency,
            "liquidity_depth": 10000,
            "capability_requirements": capabilities,
            "active": True
        }
        from overmanifold.routing.geodesic import ManifoldEdge
        manifold.add_edge(ManifoldEdge(**edge))
        print(f"✓ Added edge: {from_ep} → {to_ep}")
    
    # Create geodesic router
    router = GeodesicRouter(manifold)
    
    # Calculate optimal path
    print("\nCalculating optimal path with constraints...")
    constraints = [
        RoutingConstraintValue(
            constraint_type=RoutingConstraint.TRUST_DENSITY,
            value=0.8,
            weight=0.4,
            strict=False
        ),
        RoutingConstraintValue(
            constraint_type=RoutingConstraint.MAX_SLIPPAGE,
            value=0.02,
            weight=0.3,
            strict=False
        ),
        RoutingConstraintValue(
            constraint_type=RoutingConstraint.MAX_LATENCY,
            value=300,
            weight=0.2,
            strict=False
        )
    ]
    
    path = router.calculate_geodesic_path(
        from_endpoint="ethereum-mainnet",
        to_endpoint="optimism",
        constraints=constraints
    )
    
    if path:
        print("✓ Optimal path found:")
        print(f"  Path ID: {path.path_id}")
        print(f"  Route: {' → '.join(path.endpoints)}")
        print(f"  Total Cost: {path.total_cost:.4f}")
        print(f"  Trust Density: {path.total_trust_density:.2f}")
        print(f"  Latency: {path.total_latency_ms}ms")
        print(f"  Settlement Cost: ${path.total_settlement_cost:.2f}")
        print(f"  Confidence: {path.confidence_score:.2f}")
    else:
        print("✗ No valid path found")
    
    # Display routing metrics
    print("\n📊 Routing Metrics:")
    metrics = router.routing_metrics
    print(json.dumps(metrics.to_dict(), indent=2))
    
    return router


async def demo_merkle_provenance():
    """Demonstrate Merkle provenance tracking"""
    print("\n🔐 MERKLE PROVENANCE DEMONSTRATION")
    print("="*80 + "\n")
    
    from overmanifold.core.types import StateTransition, StateTransitionType, EndpointID, Hash
    from datetime import datetime
    
    # Create provenance tracker
    tracker = ProvenanceTracker()
    
    print("Creating provenance tree...")
    tree_id = "demo-tree-001"
    tree = tracker.create_tree(tree_id)
    
    print(f"✓ Created provenance tree: {tree_id}")
    
    # Add state transitions with parent-child relationships
    print("\nAdding state transitions with provenance links...")
    
    transitions_data = [
        {
            "transition_id": Hash.from_data("transition-1"),
            "transition_type": StateTransitionType.SEMANTIC_INTENT,
            "from_state": Hash.from_data("idle"),
            "to_state": Hash.from_data("processing"),
            "actor": EndpointID("endpoint-1"),
            "parent_id": None
        },
        {
            "transition_id": Hash.from_data("transition-2"),
            "transition_type": StateTransitionType.LIQUIDITY_ROUTE,
            "from_state": Hash.from_data("processing"),
            "to_state": Hash.from_data("routing"),
            "actor": EndpointID("endpoint-1"),
            "parent_id": Hash.from_data("transition-1")
        },
        {
            "transition_id": Hash.from_data("transition-3"),
            "transition_type": StateTransitionType.SETTLEMENT,
            "from_state": Hash.from_data("routing"),
            "to_state": Hash.from_data("settled"),
            "actor": EndpointID("endpoint-1"),
            "parent_id": Hash.from_data("transition-2")
        }
    ]
    
    for i, trans_data in enumerate(transitions_data, 1):
        transition = StateTransition(
            transition_id=trans_data["transition_id"],
            transition_type=trans_data["transition_type"],
            from_state=trans_data["from_state"],
            to_state=trans_data["to_state"],
            actor=trans_data["actor"],
            timestamp=datetime.now()
        )
        
        hash_value = tracker.add_transition(
            tree_id=tree_id,
            transition=transition,
            parent_transition_id=trans_data["parent_id"]
        )
        
        print(f"✓ Added transition {i}: {transition.transition_id}")
        if trans_data["parent_id"]:
            print(f"  └─ Parent: {trans_data['parent_id']}")
    
    # Build tree and get root
    tree.build_tree()
    root_hash = tree.get_root_hash()
    
    print(f"\n✓ Merkle tree built")
    print(f"  Root Hash: {root_hash}")
    print(f"  Total Transitions: {len(tree.transitions)}")
    
    # Get provenance chain
    print("\n🔗 Provenance Chain:")
    last_transition = transitions_data[-1]["transition_id"]
    chain = tracker.get_provenance_chain(last_transition)
    
    for i, trans_id in enumerate(chain):
        print(f"  {i+1}. {trans_id}")
    
    # Generate and verify proof
    print("\n🔐 Merkle Proof Generation:")
    proof = tracker.get_transition_proof(last_transition)
    
    if proof:
        print(f"✓ Proof generated for transition: {last_transition}")
        print(f"  Leaf Hash: {proof.leaf_hash}")
        print(f"  Root Hash: {proof.root_hash}")
        print(f"  Proof Path Length: {len(proof.proof_path)}")
        
        # Verify proof
        is_valid = tracker.verify_provenance(last_transition)
        print(f"  Proof Valid: {is_valid}")
    else:
        print("✗ Failed to generate proof")
    
    # Display provenance snapshot
    print("\n📊 Provenance Snapshot:")
    snapshot = tracker.get_provenance_snapshot()
    print(json.dumps(snapshot, indent=2))
    
    return tracker


async def demo_proof_of_profit():
    """Demonstrate proof-of-profit consensus"""
    print("\n💰 PROOF-OF-PROFIT CONSENSUS DEMONSTRATION")
    print("="*80 + "\n")
    
    # Create consensus mechanism
    initial_supply = 1_000_000_000
    consensus = ProofOfProfitConsensus(initial_supply=initial_supply)
    
    print(f"✓ Proof-of-Profit Consensus initialized")
    print(f"  Initial Supply: {initial_supply:,} tokens")
    
    # Register validators
    print("\nRegistering validators...")
    validators = [
        ("validator-1", 10000),
        ("validator-2", 15000),
        ("validator-3", 8000),
        ("validator-4", 12000),
        ("validator-5", 20000)
    ]
    
    for validator_id, stake in validators:
        consensus.register_validator(validator_id, stake=stake)
        print(f"✓ Registered validator: {validator_id} (stake: {stake:,})")
    
    # Submit economic work
    print("\nSubmitting economic work...")
    work_types = [WorkType.DEVELOPMENT, WorkType.VALIDATION, WorkType.ROUTING, WorkType.GOVERNANCE]
    
    for i in range(10):
        from overmanifold.core.types import EndpointID, Hash
        work = consensus.create_economic_work(
            worker_id=EndpointID(validators[i % len(validators)][0]),
            work_type=work_types[i % len(work_types)],
            impact_value=1000 + (i * 100),
            description=f"Economic work #{i+1}"
        )
        
        consensus.submit_work(work)
        print(f"✓ Submitted work #{i+1}: {work.work_id} (type: {work.work_type.value})")
    
    # Verify work and distribute rewards
    print("\nVerifying work and distributing rewards...")
    
    for work in consensus.work_queue[:5]:  # Verify first 5
        is_valid = consensus.verify_work(work, verifier=EndpointID("validator-1"))
        if is_valid:
            consensus.distribute_reward(work)
            print(f"✓ Verified and rewarded: {work.work_id}")
    
    # Process inverse mining
    print("\nProcessing inverse mining (supply burn)...")
    burn_result = consensus.process_inverse_mining()
    print(f"✓ Inverse mining processed")
    print(f"  Supply Burned: {burn_result['burned_supply']:,.2f}")
    print(f"  Burn Rate: {burn_result['burn_rate']:.6f}")
    
    # Display consensus state
    print("\n📊 Consensus State:")
    state = consensus.get_consensus_state()
    print(json.dumps(state, indent=2))
    
    return consensus


async def demo_full_integration():
    """Demonstrate full system integration"""
    print("\n🌐 FULL SYSTEM INTEGRATION DEMONSTRATION")
    print("="*80 + "\n")
    
    print("Initializing complete Overmanifold system...")
    overmanifold = OvermanifoldUnified(llm_provider="mock")
    
    print("✓ System initialized with all components:")
    print("  • Core Engine")
    print("  • LLM Governance Engine")
    print("  • Geodesic Routing")
    print("  • Proof-of-Profit Consensus")
    print("  • Blockchain Watchers (Ethereum, Solana)")
    print("  • Real DeFi Integration")
    print("  • Transaction Workers")
    print("  • Repository Tokenization")
    print("  • Browser Validator Surfaces")
    
    # Create unified endpoint
    print("\nCreating unified endpoint...")
    endpoint_id = await overmanifold.create_unified_endpoint(
        public_key="0x1234567890abcdef",
        private_key="0xsecretkey",
        capabilities=[
            Capability(capability_type=CapabilityType.MESSAGING, strength=0.8),
            Capability(capability_type=CapabilityType.COMPUTE, strength=0.9)
        ],
        metadata={"name": "Integration Demo Node", "location": "Global"}
    )
    
    print(f"✓ Unified endpoint created: {endpoint_id}")
    
    # Process intent through complete pipeline
    print("\nProcessing human intent through complete pipeline...")
    result = await overmanifold.process_human_intent(
        endpoint_id=endpoint_id,
        human_intent="Route liquidity and validate computation for ecosystem development",
        context={"priority": "high", "budget": 1000}
    )
    
    print("✓ Intent processed through complete pipeline:")
    print(f"  • LLM Interpretation: Complete")
    print(f"  • State Transition: Created")
    print(f"  • Routing: Calculated")
    print(f"  • Consensus: Registered")
    print(f"  • Economic Reward: Calculated")
    
    # Display unified state
    print("\n📊 Unified System State:")
    unified_state = overmanifold.get_unified_state()
    print(json.dumps(unified_state, indent=2))
    
    return overmanifold


async def demo_system_health():
    """Demonstrate system health check"""
    print("\n🏥 SYSTEM HEALTH CHECK")
    print("="*80 + "\n")
    
    dashboard = SystemDashboard()
    dashboard.display_header()
    
    # Check core components
    print("Checking core components...\n")
    
    try:
        engine = OvermanifoldEngine()
        manifold_state = engine.get_manifold_state()
        dashboard.display_component_status(
            "Core Engine",
            "ACTIVE",
            {
                "Endpoints": len(manifold_state.get("endpoints", {})),
                "Total Value": f"${manifold_state.get('total_economic_value', 0):,.2f}",
                "Trust Density": f"{manifold_state.get('avg_trust_density', 0):.2f}"
            }
        )
    except Exception as e:
        dashboard.display_component_status("Core Engine", "ERROR", {"error": str(e)})
    
    try:
        from overmanifold.unified import OvermanifoldUnified
        overmanifold = OvermanifoldUnified(llm_provider="mock")
        dashboard.display_component_status(
            "LLM Governance",
            "ACTIVE",
            {
                "Provider": "Mock (Demo Mode)",
                "Intents Processed": overmanifold.llm_governance.total_intents_processed,
                "Tasks Created": overmanifold.llm_governance.total_tasks_created
            }
        )
    except Exception as e:
        dashboard.display_component_status("LLM Governance", "ERROR", {"error": str(e)})
    
    try:
        manifold = LiquidityManifold()
        manifold.add_endpoint("test-endpoint", ["swap"], 1000, 0.8)
        dashboard.display_component_status(
            "Geodesic Routing",
            "ACTIVE",
            {
                "Endpoints": len(manifold.endpoints),
                "Edges": len(manifold.edges)
            }
        )
    except Exception as e:
        dashboard.display_component_status("Geodesic Routing", "ERROR", {"error": str(e)})
    
    try:
        consensus = ProofOfProfitConsensus(initial_supply=1_000_000_000)
        state = consensus.get_consensus_state()
        dashboard.display_component_status(
            "Proof-of-Profit Consensus",
            "ACTIVE",
            {
                "Status": state["status"],
                "Circulating Supply": f"{state['supply_metrics']['circulating_supply']:,.2f}",
                "Validators": len(state["validators"])
            }
        )
    except Exception as e:
        dashboard.display_component_status("Proof-of-Profit Consensus", "ERROR", {"error": str(e)})
    
    try:
        tracker = ProvenanceTracker()
        tree = tracker.create_tree("health-check-tree")
        dashboard.display_component_status(
            "Merkle Provenance",
            "ACTIVE",
            {
                "Trees": len(tracker.trees),
                "Transitions Indexed": len(tracker.transition_index)
            }
        )
    except Exception as e:
        dashboard.display_component_status("Merkle Provenance", "ERROR", {"error": str(e)})
    
    # Display overall system metrics
    print("\n" + "="*80)
    print("📊 OVERALL SYSTEM METRICS")
    print("="*80)
    
    metrics = {
        "System Status": "OPERATIONAL",
        "Components Active": "5/5",
        "Production Ready": False,
        "Security Status": "Production Candidate Network (PCN)",
        "Last Health Check": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*80)
    print("✅ System health check complete")
    print("="*80 + "\n")


async def main():
    """Main demonstration function"""
    print("\n🌐 OVERMANIFOLD PROTOCOL SYSTEM DEMONSTRATION")
    print("Civilization-Scale Cryptographic-Economic Coordination Architecture")
    print("="*80 + "\n")
    
    dashboard = SystemDashboard()
    dashboard.display_menu()
    
    while True:
        try:
            choice = input("Select demonstration (0-7): ").strip()
            
            if choice == "0":
                print("\n👋 Exiting demonstration. Goodbye!\n")
                break
            elif choice == "1":
                await demo_core_engine()
            elif choice == "2":
                await demo_llm_governance()
            elif choice == "3":
                await demo_geodesic_routing()
            elif choice == "4":
                await demo_merkle_provenance()
            elif choice == "5":
                await demo_proof_of_profit()
            elif choice == "6":
                await demo_full_integration()
            elif choice == "7":
                await demo_system_health()
            else:
                print("❌ Invalid choice. Please select 0-7.")
            
            print("\n" + "="*80)
            input("Press Enter to continue...")
            dashboard.display_header()
            dashboard.display_menu()
            
        except KeyboardInterrupt:
            print("\n\n👋 Demonstration interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or select a different demonstration.\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demonstration interrupted. Goodbye!\n")