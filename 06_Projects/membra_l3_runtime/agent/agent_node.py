#!/usr/bin/env python3
"""
AGENT NODE — Python orchestrator for Membra L3
Connects LLM bridge, P2P network, and multi-chain settlement.
"""
import asyncio
import json
import os
import sys
from typing import Dict

# Add paths
sys.path.insert(0, os.path.dirname(__file__))

from llm_bridge import LLMBridge


class AgentNode:
    """Python agent node that runs alongside the Rust runtime."""

    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or f"agent-{os.getpid()}"
        self.bridge = LLMBridge()
        self.running = False
        self.prompts_processed = 0
        self.total_earnings = 0

    async def start(self):
        """Start the agent node."""
        self.running = True
        await self.bridge.connect_runtime()
        
        print(f"[AGENT] {self.agent_id} started")
        print("[AGENT] Ready for prompts. Type 'quit' to exit.")
        
        # Interactive loop
        while self.running:
            try:
                prompt = input("\n> ")
                if prompt.lower() in ("quit", "exit", "q"):
                    break
                
                result = await self.bridge.process_prompt(self.agent_id, prompt)
                self.prompts_processed += 1
                self.total_earnings += result["value_minted"]
                
                print(f"\n[RESPONSE] {result['response'][:200]}...")
                print(f"[EARNED]   {result['value_minted']} base units for {result['tokens']} tokens")
                print(f"[TX HASH]  {result['prompt_hash'][:16]}...")
                
            except EOFError:
                break
            except KeyboardInterrupt:
                break
        
        self.running = False
        print(f"\n[AGENT] {self.agent_id} stopped")
        print(f"[STATS] Prompts: {self.prompts_processed} | Earnings: {self.total_earnings}")

    async def run_autonomous(self):
        """Run autonomous file mining and processing."""
        self.running = True
        await self.bridge.connect_runtime()
        
        # Scan files and process them as prompts
        scan_paths = [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
        ]
        
        for path in scan_paths:
            if os.path.exists(path):
                for root, _, files in os.walk(path):
                    for fname in files[:20]:  # Limit to 20 files
                        if fname.endswith((".txt", ".md", ".py", ".js", ".json")):
                            fpath = os.path.join(root, fname)
                            try:
                                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                                    content = f.read()[:1000]
                                
                                prompt = f"Analyze and summarize this file: {fname}\n{content[:500]}"
                                result = await self.bridge.process_prompt(self.agent_id, prompt)
                                self.prompts_processed += 1
                                self.total_earnings += result["value_minted"]
                                
                                print(f"[AUTO] {fname}: {result['tokens']} tokens = {result['value_minted']} units")
                                await asyncio.sleep(2)  # Rate limit
                                
                            except Exception as e:
                                print(f"[AUTO] Error processing {fname}: {e}")
        
        print(f"\n[AGENT] Autonomous run complete")
        print(f"[STATS] Prompts: {self.prompts_processed} | Earnings: {self.total_earnings}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--autonomous", action="store_true", help="Autonomous file processing")
    parser.add_argument("--agent-id", default=None, help="Agent identifier")
    args = parser.parse_args()
    
    node = AgentNode(args.agent_id)
    
    if args.autonomous:
        asyncio.run(node.run_autonomous())
    else:
        asyncio.run(node.start())


if __name__ == "__main__":
    main()
