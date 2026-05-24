#!/usr/bin/env python3
"""
ANCHOR TO SOLANA — Send a real devnet memo transaction.
Uses the existing real_chain.py SolanaBridge infrastructure.
"""
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, "/Users/alep/Downloads/mac_compute_node")

from real_chain import RealSolanaClient, ChainConfig


def main():
    print("=" * 70)
    print("  ANCHOR TO SOLANA DEVNET")
    print("  Sending a real memo transaction with batch root hash")
    print("=" * 70)
    print()

    # Use the batch root from the 3-agent consensus test
    # (or generate a fresh one for this run)
    batch_ops = [
        {"file": "contract.rs", "value": 0.85},
        {"file": "bridge.sol", "value": 0.92},
        {"file": "network.go", "value": 0.78},
        {"file": "consensus.cpp", "value": 0.88},
        {"file": "runtime.rs", "value": 0.90},
    ]
    state_root = hashlib.sha256(json.dumps(batch_ops, sort_keys=True).encode()).hexdigest()

    print(f"  Batch Root: {state_root[:32]}...")
    print(f"  Operations: {len(batch_ops)}")
    print()

    # Initialize client (loads or creates wallet)
    config = ChainConfig()
    client = RealSolanaClient(config)
    print(f"  Wallet: {client.pubkey}")

    # Check balance
    balance = client.balance_sol()
    print(f"  Balance: {balance:.4f} SOL")
    print()

    # Request airdrop if needed (< 0.01 SOL)
    if balance < 0.01:
        print("  [AIRDROP] Requesting devnet SOL...")
        result = client.request_airdrop(sol=2.0)
        print(f"  {result}")
        if "failed" in result.lower():
            print("  You may need to request airdrop manually:")
            print(f"  https://faucet.solana.com/?address={client.pubkey}")
        else:
            print("  Waiting 10s for confirmation...")
            time.sleep(10)
            balance = client.balance_sol()
            print(f"  New balance: {balance:.4f} SOL")

    if balance < 0.0005:
        print()
        print("  ❌ Insufficient SOL for transaction. Cannot proceed.")
        print(f"  Get devnet SOL: https://faucet.solana.com/?address={client.pubkey}")
        return 1

    # Send memo transaction
    print()
    print("  [SEND] Submitting memo to Solana devnet...")
    memo = f"MEMBRA|PROOF|{state_root[:32]}|ops={len(batch_ops)}|ts={int(time.time())}"
    print(f"  Memo: {memo[:60]}...")

    try:
        tx_sig = client.submit_memo(memo)
        if "failed" in tx_sig.lower():
            print(f"  ❌ Transaction failed: {tx_sig}")
            return 1

        print(f"  ✅ Transaction sent: {tx_sig}")
        print()
        print("=" * 70)
        print("  RECEIPT")
        print("=" * 70)
        print(f"  Transaction: {tx_sig}")
        print(f"  Explorer:    https://explorer.solana.com/tx/{tx_sig}?cluster=devnet")
        print(f"  Memo:        {memo}")
        print()
        print("  This is a REAL transaction on Solana devnet.")
        print("  The memo contains the batch root hash as proof-of-proof.")
        print()
        return 0

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
