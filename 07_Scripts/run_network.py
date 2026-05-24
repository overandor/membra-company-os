#!/usr/bin/env python3
"""Quick demo runner for Membra network."""
import asyncio
import sys
sys.path.insert(0, '/Users/alep/Downloads/mac_compute_node')

from membra_l3 import MembraL3Node

async def main():
    node = MembraL3Node()
    print("=" * 60)
    print("  MEMBRA L3 NETWORK — LIVE")
    print("  C++ Core | Go P2P | Rust Runtime | Solana Fallback")
    print("=" * 60)
    print()

    s = node.get_status()
    print(f"  Agent ID:  {s['agent_id']}")
    print(f"  SOL:       {s['solana_balance']:.4f}")
    print(f"  COMPUTE:   {s['token_balance']:,.0f}")
    print(f"  Token:     {'DEPLOYED' if s['token_deployed'] else 'not deployed'}")
    print(f"  Peers:     {s['p2p']['peers']}")
    print()

    # Start node
    task = asyncio.create_task(node.run())
    await asyncio.sleep(2)

    print("  [LIVE] Network running — processing compute tasks...")
    print()

    for i in range(1, 21):
        s = node.get_status()
        print(f"  T+{i:>2}s  Ops: {s['ops_processed']:>4}  Pending: {s['pending_ops']:>3}  "
              f"Consensus: {s['consensus']['finalized']:>2}  Peers: {s['p2p']['peers']}")
        await asyncio.sleep(1)

    print()
    print("  [STOP] Shutting down...")
    node.running = False
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    print("=" * 60)
    print("  Network stopped")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  Stopped.")
