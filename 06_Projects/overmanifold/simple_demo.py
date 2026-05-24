#!/usr/bin/env python3
"""
Simple Overmanifold Component Demonstration
Shows basic functionality without requiring full configuration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

def demo_core_types():
    """Demonstrate core data types"""
    print("\n🔧 CORE DATA TYPES DEMONSTRATION")
    print("="*80 + "\n")
    
    try:
        from overmanifold.core.types import (
            Hash, EndpointID, Capability, CapabilityType,
            StateTransition, StateTransitionType, SemanticIntent
        )
        from datetime import datetime
        
        print("✓ Core types imported successfully\n")
        
        # Demonstrate Hash
        data = "test data for hashing"
        hash_obj = Hash.from_data(data)
        print(f"Hash Creation:")
        print(f"  Input: {data}")
        print(f"  Hash: {hash_obj}")
        print(f"  Algorithm: {hash_obj.algorithm}")
        print()
        
        # Demonstrate EndpointID
        endpoint_id = EndpointID("0x1234567890abcdef")
        print(f"Endpoint ID:")
        print(f"  ID: {endpoint_id}")
        print(f"  String: {str(endpoint_id)}")
        print()
        
        # Demonstrate Capability
        capability = Capability(
            capability_type=CapabilityType.MESSAGING,
            strength=0.85,
            metadata={"throughput": "1000 msg/sec", "latency": "50ms"}
        )
        print(f"Capability:")
        print(f"  Type: {capability.capability_type}")
        print(f"  Strength: {capability.strength}")
        print(f"  Metadata: {capability.metadata}")
        print()
        
        # Demonstrate SemanticIntent
        intent = SemanticIntent(
            intent_id=Hash.from_data("intent-1"),
            intent_text="Route 100 USDC from Ethereum to Solana",
            intent_type="liquidity_routing",
            parameters={"amount": 100, "from": "ethereum", "to": "solana"},
            confidence=0.92
        )
        print(f"Semantic Intent:")
        print(f"  ID: {intent.intent_id}")
        print(f"  Text: {intent.intent_text}")
        print(f"  Type: {intent.intent_type}")
        print(f"  Confidence: {intent.confidence}")
        print()
        
        # Demonstrate StateTransition
        transition = StateTransition(
            transition_id=Hash.from_data("transition-1"),
            transition_type=StateTransitionType.SEMANTIC_INTENT,
            from_state=Hash.from_data("idle"),
            to_state=Hash.from_data("processing"),
            actor=endpoint_id,
            timestamp=datetime.now()
        )
        print(f"State Transition:")
        print(f"  ID: {transition.transition_id}")
        print(f"  Type: {transition.transition_type.value}")
        print(f"  From: {transition.from_state}")
        print(f"  To: {transition.to_state}")
        print(f"  Actor: {transition.actor}")
        print(f"  Timestamp: {transition.timestamp}")
        
        print("\n✅ Core types demonstration complete\n")
        return True
        
    except Exception as e:
        print(f"❌ Error demonstrating core types: {e}\n")
        return False


def demo_merkle_system():
    """Demonstrate Merkle proof system"""
    print("\n🔐 MERKLE PROOF SYSTEM DEMONSTRATION")
    print("="*80 + "\n")
    
    try:
        from overmanifold.merkle.proof import MerkleTree, MerkleProof, ProvenanceTracker
        from overmanifold.core.types import Hash
        
        print("✓ Merkle system imported successfully\n")
        
        # Create Merkle tree
        print("Creating Merkle tree:")
        tree = MerkleTree()
        
        # Add leaves
        leaf_data = [
            {"transaction": "tx1", "amount": 100},
            {"transaction": "tx2", "amount": 200},
            {"transaction": "tx3", "amount": 150},
            {"transaction": "tx4", "amount": 300}
        ]
        
        for i, data in enumerate(leaf_data):
            hash_value = tree.add_leaf(data)
            print(f"  Added leaf {i+1}: {hash_value}")
        
        # Build tree
        print("\nBuilding Merkle tree...")
        tree.build_tree()
        root_hash = tree.get_root_hash()
        print(f"  Root hash: {root_hash}")
        print(f"  Total leaves: {len(tree.leaves)}")
        
        # Generate proof
        print("\nGenerating Merkle proof for leaf 1:")
        proof = tree.generate_proof(1)
        if proof:
            print(f"  Leaf hash: {proof.leaf_hash}")
            print(f"  Root hash: {proof.root_hash}")
            print(f"  Proof path length: {len(proof.proof_path)}")
            
            # Verify proof
            is_valid = proof.verify(root_hash)
            print(f"  Proof valid: {is_valid}")
        
        # Demonstrate ProvenanceTracker
        print("\nDemonstrating ProvenanceTracker:")
        tracker = ProvenanceTracker()
        tree_id = "demo-tree"
        tree = tracker.create_tree(tree_id)
        print(f"  Created provenance tree: {tree_id}")
        
        # Get snapshot
        snapshot = tracker.get_provenance_snapshot()
        print(f"  Total trees: {snapshot['total_trees']}")
        print(f"  Total transitions: {snapshot['total_transitions']}")
        
        print("\n✅ Merkle system demonstration complete\n")
        return True
        
    except Exception as e:
        print(f"❌ Error demonstrating Merkle system: {e}\n")
        return False


def demo_routing_system():
    """Demonstrate routing system"""
    print("\n🗺️ ROUTING SYSTEM DEMONSTRATION")
    print("="*80 + "\n")
    
    try:
        from overmanifold.routing.geodesic import LiquidityManifold, GeodesicRouter, RoutingConstraint, RoutingConstraintValue
        
        print("✓ Routing system imported successfully\n")
        
        # Create manifold
        print("Creating liquidity manifold:")
        manifold = LiquidityManifold()
        
        # Add endpoints
        endpoints = [
            ("ethereum-mainnet", ["swap", "bridge"], 1000000, 0.9),
            ("solana-mainnet", ["swap", "bridge"], 500000, 0.85),
            ("polygon-pos", ["swap", "bridge"], 300000, 0.8)
        ]
        
        for endpoint_id, capabilities, liquidity, trust in endpoints:
            manifold.add_endpoint(endpoint_id, capabilities, liquidity, trust)
            print(f"  Added endpoint: {endpoint_id}")
            print(f"    Capabilities: {capabilities}")
            print(f"    Liquidity: ${liquidity:,}")
            print(f"    Trust: {trust}")
        
        # Create router
        print("\nCreating geodesic router:")
        router = GeodesicRouter(manifold)
        print(f"  Router initialized")
        print(f"  Endpoints in manifold: {len(manifold.endpoints)}")
        
        # Display routing metrics
        print("\nRouting metrics:")
        metrics = router.routing_metrics
        print(f"  Total routes calculated: {metrics.total_routes_calculated}")
        print(f"  Successful routes: {metrics.successful_routes}")
        print(f"  Failed routes: {metrics.failed_routes}")
        print(f"  Average path length: {metrics.average_path_length}")
        
        # Display constraint types
        print("\nAvailable routing constraints:")
        for constraint in RoutingConstraint:
            print(f"  • {constraint.value}")
        
        print("\n✅ Routing system demonstration complete\n")
        return True
        
    except Exception as e:
        print(f"❌ Error demonstrating routing system: {e}\n")
        return False


def demo_consensus_system():
    """Demonstrate consensus system"""
    print("\n💰 CONSENSUS SYSTEM DEMONSTRATION")
    print("="*80 + "\n")
    
    try:
        from overmanifold.consensus.proof_of_profit import ProofOfProfitConsensus, WorkType, ConsensusStatus
        from overmanifold.core.types import EndpointID, Hash
        
        print("✓ Consensus system imported successfully\n")
        
        # Create consensus
        print("Creating Proof-of-Profit consensus:")
        initial_supply = 1_000_000_000
        consensus = ProofOfProfitConsensus(initial_supply=initial_supply)
        print(f"  Initial supply: {initial_supply:,} tokens")
        
        # Register validators
        print("\nRegistering validators:")
        validators = [
            ("validator-1", 10000),
            ("validator-2", 15000)
        ]
        
        for validator_id, stake in validators:
            consensus.register_validator(EndpointID(validator_id), stake=stake)
            print(f"  Registered: {validator_id} (stake: {stake:,})")
        
        # Create economic work
        print("\nCreating economic work:")
        work = consensus.create_economic_work(
            worker_id=EndpointID("validator-1"),
            work_type=WorkType.DEVELOPMENT,
            impact_value=5000,
            description="Developed core routing algorithm"
        )
        print(f"  Work ID: {work.work_id}")
        print(f"  Type: {work.work_type.value}")
        print(f"  Impact value: ${work.impact_value:,}")
        print(f"  Description: {work.description}")
        
        # Get consensus state
        print("\nConsensus state:")
        state = consensus.get_consensus_state()
        print(f"  Status: {state['status']}")
        print(f"  Circulating supply: {state['supply_metrics']['circulating_supply']:,.2f}")
        print(f"  Burned supply: {state['supply_metrics']['burned_supply']:,.2f}")
        print(f"  Total validators: {len(state['validators'])}")
        
        # Display work types
        print("\nAvailable work types:")
        for work_type in WorkType:
            print(f"  • {work_type.value}")
        
        print("\n✅ Consensus system demonstration complete\n")
        return True
        
    except Exception as e:
        print(f"❌ Error demonstrating consensus system: {e}\n")
        return False


def demo_governance_types():
    """Demonstrate governance data types"""
    print("\n🧠 GOVERNANCE DATA TYPES DEMONSTRATION")
    print("="*80 + "\n")
    
    try:
        from overmanifold.governance.llm_engine import IntentType, TaskPriority, TaskStatus
        
        print("✓ Governance types imported successfully\n")
        
        # Display intent types
        print("Available intent types:")
        for intent_type in IntentType:
            print(f"  • {intent_type.value}")
        
        # Display task priorities
        print("\nAvailable task priorities:")
        for priority in TaskPriority:
            print(f"  • {priority.value}")
        
        # Display task statuses
        print("\nAvailable task statuses:")
        for status in TaskStatus:
            print(f"  • {status.value}")
        
        print("\n✅ Governance types demonstration complete\n")
        return True
        
    except Exception as e:
        print(f"❌ Error demonstrating governance types: {e}\n")
        return False


def demo_worker_types():
    """Demonstrate worker data types"""
    print("\n⚙️ WORKER DATA TYPES DEMONSTRATION")
    print("="*80 + "\n")
    
    try:
        from overmanifold.workers.transaction_endpoint import (
            LifecycleState, EventType, FinalityType, WorkerMode, PushTarget
        )
        
        print("✓ Worker types imported successfully\n")
        
        # Display lifecycle states
        print("Transaction lifecycle states:")
        for state in LifecycleState:
            print(f"  • {state.value}")
        
        # Display event types
        print("\nTransaction event types:")
        for event in EventType:
            print(f"  • {event.value}")
        
        # Display finality types
        print("\nFinality types:")
        for finality in FinalityType:
            print(f"  • {finality.value}")
        
        # Display worker modes
        print("\nWorker modes:")
        for mode in WorkerMode:
            print(f"  • {mode.value}")
        
        # Display push targets
        print("\nPush targets:")
        for target in PushTarget:
            print(f"  • {target.value}")
        
        print("\n✅ Worker types demonstration complete\n")
        return True
        
    except Exception as e:
        print(f"❌ Error demonstrating worker types: {e}\n")
        return False


def display_system_overview():
    """Display system overview"""
    print("\n🌐 OVERMANIFOLD PROTOCOL SYSTEM OVERVIEW")
    print("="*80 + "\n")
    
    print("Civilization-Scale Cryptographic-Economic Coordination Architecture")
    print()
    print("⚠️  CRITICAL STATUS DISCLAIMER")
    print("-" * 80)
    print("Current Status: Production Candidate Network (PCN) / MVP Alpha")
    print()
    print("✅ SAFE FOR:")
    print("  • Component demonstrations and architecture exploration")
    print("  • Closed alpha testing with trusted participants")
    print("  • Read-only blockchain access and monitoring")
    print("  • Testnet deployments with zero-value transactions")
    print()
    print("❌ NOT SAFE FOR:")
    print("  • Unrestricted production deployment with user funds")
    print("  • Handling significant value without treasury controls")
    print("  • Public mainnet operation without security audits")
    print("  • Real transaction execution with user assets")
    print()
    print("Missing: Security audits, adversarial testing, treasury controls,")
    print("         compliance review, staged deployment hardening")
    print()
    print("See: OVERMANIFOLD_PRODUCTION_READINESS_GATES_V1.md")
    print("-" * 80)
    print()
    
    print("📦 COMPONENTS:")
    print("-" * 80)
    components = [
        ("Core Engine", "Endpoint management, state transitions, capabilities"),
        ("LLM Governance", "Intent interpretation, economic tasks, decisions"),
        ("Geodesic Routing", "Trust-constrained path finding, liquidity manifold"),
        ("Merkle Provenance", "Cryptographic provenance, hash chains, proofs"),
        ("Proof-of-Profit", "Economic consensus, rewards, inverse mining"),
        ("Transaction Workers", "Blockchain transaction lifecycle management"),
        ("Blockchain Watchers", "Ethereum/Solana integration (read-only)"),
        ("Real Validators", "WASM/WebGPU validation surfaces"),
        ("API Server", "FastAPI with health checks and monitoring")
    ]
    
    for name, description in components:
        print(f"  • {name:25} - {description}")
    
    print("\n🔧 INTEGRATIONS:")
    print("-" * 80)
    integrations = [
        ("OpenAI GPT-4", "Real LLM integration for governance"),
        ("Anthropic Claude", "Real LLM integration for governance"),
        ("Ethereum Mainnet", "Real blockchain integration"),
        ("Solana Mainnet", "Real blockchain integration"),
        ("WasmTime", "Real WebAssembly execution"),
        ("WGPU", "Real WebGPU compute shaders"),
        ("FastAPI", "Production API server"),
        ("PostgreSQL", "Production database"),
        ("Redis", "Caching and message queue")
    ]
    
    for name, description in integrations:
        print(f"  • {name:20} - {description}")
    
    print("\n📊 STATUS:")
    print("-" * 80)
    print(f"  System Status: Production Candidate Network (PCN) / MVP Alpha")
    print(f"  Security Status: Guarded Production Candidate")
    print(f"  Components Active: 9/9")
    print(f"  Real Infrastructure: ✅ Connected (Read-only)")
    print(f"  Security Audits: ⚠️  Pending")
    print(f"  Deployment Stage: Internal Devnet")
    print(f"  Safe for User Funds: ❌ NO")
    print(f"  Safe for Controlled Testing: ✅ YES")
    
    print("\n📚 DOCUMENTATION:")
    print("-" * 80)
    docs = [
        ("README.md", "Project overview and quick start"),
        ("SYSTEM_DEMO.md", "Component demonstrations and examples"),
        ("SECURITY_DEPLOYMENT_STATUS.md", "Security assessment and roadmap"),
        ("TECHNICAL_MATURATION_ANALYSIS.md", "Deep technical analysis"),
        ("IMPLEMENTATION_SUMMARY.md", "Implementation details")
    ]
    
    for filename, description in docs:
        print(f"  • {filename:35} - {description}")
    
    print("\n" + "="*80 + "\n")


def main():
    """Main demonstration function"""
    display_system_overview()
    
    print("🎮 AVAILABLE DEMONSTRATIONS:")
    print("-" * 80)
    print("1. Core Data Types")
    print("2. Merkle Proof System")
    print("3. Routing System")
    print("4. Consensus System")
    print("5. Governance Data Types")
    print("6. Worker Data Types")
    print("7. Run All Demonstrations")
    print("0. Exit")
    print()
    
    while True:
        try:
            choice = input("Select demonstration (0-7): ").strip()
            
            if choice == "0":
                print("\n👋 Exiting demonstration. Goodbye!\n")
                break
            elif choice == "1":
                demo_core_types()
            elif choice == "2":
                demo_merkle_system()
            elif choice == "3":
                demo_routing_system()
            elif choice == "4":
                demo_consensus_system()
            elif choice == "5":
                demo_governance_types()
            elif choice == "6":
                demo_worker_types()
            elif choice == "7":
                print("\n🚀 Running all demonstrations...\n")
                results = []
                results.append(("Core Data Types", demo_core_types()))
                results.append(("Merkle System", demo_merkle_system()))
                results.append(("Routing System", demo_routing_system()))
                results.append(("Consensus System", demo_consensus_system()))
                results.append(("Governance Types", demo_governance_types()))
                results.append(("Worker Types", demo_worker_types()))
                
                print("\n" + "="*80)
                print("📊 DEMONSTRATION SUMMARY")
                print("="*80)
                for name, success in results:
                    status = "✅ SUCCESS" if success else "❌ FAILED"
                    print(f"  {name:25} - {status}")
                print()
            else:
                print("❌ Invalid choice. Please select 0-7.\n")
            
            print("="*80)
            input("Press Enter to continue...")
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Demonstration interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or select a different demonstration.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demonstration interrupted. Goodbye!\n")