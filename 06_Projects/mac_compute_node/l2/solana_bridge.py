#!/usr/bin/env python3
"""
Solana Bridge for Mac Compute Node L2
Connects the rollup to Solana devnet/mainnet for settlement and token bridging.
"""
import json
import os
import time
from typing import Dict, Optional

from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.instruction import Instruction
from solders.transaction import Transaction


class SolanaBridge:
    """Bridge between Mac Compute L2 and Solana L1."""

    def __init__(self, config: Dict):
        self.rpc_url = config.get("solana_rpc", "https://api.devnet.solana.com")
        self.network = config.get("solana_network", "devnet")
        self.client = Client(self.rpc_url)
        self.keypair: Optional[Keypair] = None
        self.wallet_path = os.path.expanduser("~/.mac_compute_node/solana_wallet.json")
        self._load_or_create_wallet()

    def _load_or_create_wallet(self):
        """Load existing Solana wallet or create one."""
        if os.path.exists(self.wallet_path):
            with open(self.wallet_path) as f:
                secret = json.load(f)
            self.keypair = Keypair.from_seed(bytes(secret[:32]))
        else:
            os.makedirs(os.path.dirname(self.wallet_path), exist_ok=True)
            self.keypair = Keypair()
            with open(self.wallet_path, "w") as f:
                json.dump(list(self.keypair.secret()[:32]), f)
        print(f"[BRIDGE] Wallet: {self.keypair.pubkey()} on {self.network}")

    def get_balance(self) -> float:
        """Get SOL balance."""
        try:
            resp = self.client.get_balance(self.keypair.pubkey())
            return resp.value / 1e9 if resp.value else 0.0
        except Exception:
            return 0.0

    def bridge_tokens(self, amount: float, target_address: str) -> Dict:
        """Bridge COMPUTE tokens from L2 to Solana (simulated if no SPL token)."""
        try:
            # In production: invoke SPL token bridge program
            # Here we simulate a cross-chain transfer
            tx_sig = f"sim_{hash(str(time.time()))}"
            return {
                "status": "simulated",
                "amount": amount,
                "target": target_address,
                "signature": tx_sig,
                "network": self.network,
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def settle_batch_root(self, root_hash: str, batch_count: int) -> Dict:
        """Post a batch root hash to Solana as a settlement transaction."""
        try:
            if self.network == "devnet":
                # Devnet: actually try to send a tiny memo transaction
                memo = f"MCL2|{root_hash[:32]}|{batch_count}"
                # Memo program ID
                memo_prog = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
                ix = Instruction(
                    keys=[],
                    program_id=memo_prog,
                    data=memo.encode(),
                )
                # Would need recent blockhash - simulated for now
                return {
                    "status": "simulated",
                    "memo": memo,
                    "root": root_hash,
                    "batches": batch_count,
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_status(self) -> Dict:
        return {
            "network": self.network,
            "rpc": self.rpc_url,
            "wallet": str(self.keypair.pubkey()) if self.keypair else None,
            "balance_sol": self.get_balance(),
        }
