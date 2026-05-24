#!/usr/bin/env python3
"""
SOLANA SPL TOKEN DEPLOYMENT SCRIPT
Deploys $LAT (Laptop Asset Token) to Solana blockchain

Requirements:
    pip install solana solders spl-token

Usage:
    python deploy_solana_token.py --network mainnet|devnet --keypair ~/.config/solana/id.json
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Optional

# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class SolanaTokenConfig:
    name: str = "Laptop Asset Token"
    symbol: str = "LAT"
    decimals: int = 6
    total_supply: int = 9_251_500_000_000  # 9,251,500 with 6 decimals
    uri: str = "https://ipfs.io/ipfs/TO_BE_SET"  # IPFS metadata URI
    
    # Metadata
    description: str = "Tokenized laptop software assets — $9.25M appraised value (file-level adjusted)"
    image: str = "https://ipfs.io/ipfs/TO_BE_SET"
    
    # Proofs
    merkle_root: str = ""  # Will be computed
    appraisal_doc_hash: str = ""  # Will be computed
    github_repo: str = ""


class SolanaDeployer:
    """Deploys SPL token to Solana."""
    
    def __init__(self, config: SolanaTokenConfig, network: str = "devnet"):
        self.config = config
        self.network = network
        self.token_address: Optional[str] = None
        self.mint_address: Optional[str] = None
    
    def check_dependencies(self) -> bool:
        """Verify solana CLI and spl-token are installed."""
        try:
            subprocess.run(["solana", "--version"], capture_output=True, check=True)
            subprocess.run(["spl-token", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: Install Solana CLI and SPL Token CLI:")
            print("  sh -c \"$(curl -sSfL https://release.solana.com/stable/install)\"")
            print("  cargo install spl-token-cli")
            return False
    
    def set_network(self):
        """Set Solana network."""
        subprocess.run(
            ["solana", "config", "set", "--url", 
             "https://api.mainnet-beta.solana.com" if self.network == "mainnet" 
             else "https://api.devnet.solana.com"],
            check=True
        )
        print(f"[✓] Network set to {self.network}")
    
    def check_balance(self) -> float:
        """Check SOL balance."""
        result = subprocess.run(["solana", "balance"], capture_output=True, text=True)
        balance_str = result.stdout.strip().replace(" SOL", "")
        return float(balance_str)
    
    def create_token(self) -> str:
        """Create SPL token."""
        print("\n[1] Creating SPL token...")
        result = subprocess.run(
            ["spl-token", "create-token", "--decimals", str(self.config.decimals)],
            capture_output=True, text=True, check=True
        )
        
        # Parse token address from output
        for line in result.stdout.split('\n'):
            if 'Creating token' in line:
                self.token_address = line.split()[-1]
                break
        
        print(f"    Token Address: {self.token_address}")
        return self.token_address
    
    def create_account(self, owner: str = None) -> str:
        """Create token account."""
        print("\n[2] Creating token account...")
        cmd = ["spl-token", "create-account", self.token_address]
        if owner:
            cmd.extend(["--owner", owner])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        for line in result.stdout.split('\n'):
            if 'Creating account' in line:
                account = line.split()[-1]
                print(f"    Account Address: {account}")
                return account
        return ""
    
    def mint_tokens(self, account: str):
        """Mint total supply."""
        print(f"\n[3] Minting {self.config.total_supply:,} tokens...")
        subprocess.run(
            ["spl-token", "mint", self.token_address, 
             str(self.config.total_supply), account],
            check=True
        )
        print(f"    [✓] {self.config.total_supply:,} LAT minted")
    
    def set_metadata(self):
        """Set token metadata via Metaplex."""
        print("\n[4] Setting token metadata...")
        
        metadata = {
            "name": self.config.name,
            "symbol": self.config.symbol,
            "description": self.config.description,
            "image": self.config.image,
            "external_url": self.config.github_repo,
            "attributes": [
                {"trait_type": "Appraisal Value", "value": "$9,251,500"},
                {"trait_type": "Code LOC", "value": "427,227"},
                {"trait_type": "Total Systems", "value": "100+"},
                {"trait_type": "Methodology", "value": "File-Level Complexity-Adjusted"},
                {"trait_type": "Merkle Root", "value": self.config.merkle_root[:32]},
            ],
            "properties": {
                "files": [{"uri": self.config.uri, "type": "application/json"}],
                "category": "tokenized-asset"
            }
        }
        
        # Save metadata for IPFS upload
        meta_path = "/Users/alep/Downloads/tokenization/solana_metadata.json"
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"    Metadata saved to {meta_path}")
        print("    Upload this to IPFS and update the URI in config")
    
    def deploy(self) -> dict:
        """Full deployment pipeline."""
        print("=" * 60)
        print("SOLANA $LAT TOKEN DEPLOYMENT")
        print(f"Network: {self.network}")
        print(f"Total Supply: {self.config.total_supply:,}")
        print("=" * 60)
        
        if not self.check_dependencies():
            sys.exit(1)
        
        self.set_network()
        
        balance = self.check_balance()
        print(f"\nCurrent SOL Balance: {balance} SOL")
        
        if balance < 0.05:
            print("WARNING: Low SOL balance. You need ~0.05 SOL for deployment.")
            if self.network == "mainnet":
                print("Fund your wallet before proceeding.")
        
        self.create_token()
        account = self.create_account()
        self.mint_tokens(account)
        self.set_metadata()
        
        result = {
            "network": self.network,
            "token_address": self.token_address,
            "token_account": account,
            "total_supply": self.config.total_supply,
            "symbol": self.config.symbol,
            "deployed_at": time.time()
        }
        
        # Save deployment info
        deploy_path = "/Users/alep/Downloads/tokenization/solana_deployment.json"
        with open(deploy_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n[✓] Deployment info saved to {deploy_path}")
        print(f"\nToken Address: {self.token_address}")
        print(f"View on Explorer: https://solscan.io/token/{self.token_address}")
        
        return result


def main():
    parser = argparse.ArgumentParser(description="Deploy $LAT to Solana")
    parser.add_argument("--network", choices=["mainnet", "devnet"], 
                        default="devnet", help="Solana network")
    parser.add_argument("--keypair", default="~/.config/solana/id.json",
                        help="Path to keypair file")
    args = parser.parse_args()
    
    config = SolanaTokenConfig()
    deployer = SolanaDeployer(config, args.network)
    deployer.deploy()


if __name__ == "__main__":
    main()
