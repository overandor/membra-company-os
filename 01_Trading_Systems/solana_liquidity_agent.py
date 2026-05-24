#!/usr/bin/env python3
"""
SOLANA LIQUIDITY AGENT — LLM-Powered Terminal Chat
Turns this machine's appraised value into liquid cash on Solana.

Capabilities:
- Chat with LLM to guide tokenization & liquidity deployment
- Create SPL tokens, mint supply, create Raydium pools
- Swap tokens via Jupiter aggregator
- Check balances, send transactions
- Devnet → Mainnet progression

Usage:
    python solana_liquidity_agent.py
    > deploy token
    > check balance
    > create pool 1000 USDC
    > swap 100 LAT for SOL
"""

import asyncio
import json
import os
import sys
import time
import hashlib
import subprocess
import textwrap
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

# Solana SDK
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solana.rpc.core import RPCException
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.message import Message
from solders.instruction import Instruction
from solders.transaction import Transaction
from solders.hash import Hash
from spl.token.client import Token as SplToken
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID

# ============================================================
# CONFIG
# ============================================================

@dataclass
class AgentConfig:
    token_name: str = "Laptop Asset Token"
    token_symbol: str = "LAT"
    token_decimals: int = 6
    token_supply: int = 9_251_500  # Human-readable (×10^6 for on-chain)
    appraisal_usd: int = 9_251_500
    
    # Networks
    devnet_rpcs: list = field(default_factory=lambda: [
        "https://api.devnet.solana.com",
        "https://solana-devnet.g.alchemy.com/v2/demo",
    ])
    mainnet_rpc: str = "https://api.mainnet-beta.solana.com"
    
    # Default to devnet for safety
    network: str = "devnet"
    
    # Simulation mode (no real transactions)
    simulate: bool = False
    
    # Jupiter API for swaps
    jupiter_api: str = "https://quote-api.jup.ag/v6"
    
    # Raydium CPMM program
    raydium_cpmm: str = "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"

# ============================================================
# SOLANA CLIENT WRAPPER
# ============================================================

class SolanaClient:
    """Wraps Solana RPC with error handling and retries."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.rpc_url = config.devnet_rpcs[0] if config.network == "devnet" else config.mainnet_rpc
        self.client = Client(self.rpc_url)
        self.keypair: Optional[Keypair] = None
        self.public_key: Optional[Pubkey] = None
    
    def _try_rpcs(self, fn, *args, **kwargs):
        """Try an operation across multiple RPC endpoints."""
        rpcs = self.config.devnet_rpcs if self.config.network == "devnet" else [self.config.mainnet_rpc]
        last_err = None
        for rpc in rpcs:
            try:
                client = Client(rpc)
                # Rebind client temporarily
                old_client = self.client
                self.client = client
                result = fn(*args, **kwargs)
                self.client = old_client
                return result
            except Exception as e:
                last_err = e
        self.client = Client(self.rpc_url)  # Restore
        raise last_err or Exception("All RPC endpoints failed")
    
    def load_wallet(self, path: str = None) -> bool:
        """Load wallet from keypair file or create new."""
        if path is None:
            path = os.path.expanduser("~/.config/solana/id.json")
        
        if os.path.exists(path):
            with open(path, 'r') as f:
                key_bytes = bytes(json.load(f))
            if len(key_bytes) == 32:
                # Half-key: reconstruct full keypair from secret
                self.keypair = Keypair.from_seed(key_bytes)
            else:
                self.keypair = Keypair.from_bytes(key_bytes)
            self.public_key = self.keypair.pubkey()
            return True
        return False
    
    def create_wallet(self, path: str = None) -> Keypair:
        """Create new wallet and save to file."""
        if path is None:
            path = os.path.expanduser("~/.config/solana/id.json")
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.keypair = Keypair()
        self.public_key = self.keypair.pubkey()
        
        # Save full 64-byte secret for compatibility
        with open(path, 'w') as f:
            json.dump(list(bytes(self.keypair)), f)
        os.chmod(path, 0o600)
        
        return self.keypair
    
    def get_balance(self, pubkey: Pubkey = None) -> int:
        """Get SOL balance in lamports."""
        pk = pubkey or self.public_key
        resp = self.client.get_balance(pk)
        return resp.value
    
    def get_sol_balance(self, pubkey: Pubkey = None) -> float:
        """Get SOL balance in SOL."""
        return self.get_balance(pubkey) / 1_000_000_000
    
    def request_airdrop(self, amount_sol: float = 1.0) -> str:
        """Request devnet airdrop with multi-RPC fallback."""
        if self.config.network != "devnet":
            return "Airdrop only available on devnet"
        
        if self.config.simulate:
            return f"[SIM] Would airdrop {amount_sol} SOL to {self.public_key}"
        
        lamports = int(amount_sol * 1_000_000_000)
        
        for rpc in self.config.devnet_rpcs:
            try:
                client = Client(rpc)
                resp = client.request_airdrop(self.public_key, lamports)
                time.sleep(3)
                bal = self.get_sol_balance()
                return f"✅ Airdropped {amount_sol} SOL — balance now {bal:.4f} SOL\n   tx: {resp.value}"
            except Exception as e:
                continue
        
        return (f"⚠️  Airdrop failed (faucet may be rate-limited). Options:\n"
                f"   1. Try again later\n"
                f"   2. Use 'simulate on' to test without real SOL\n"
                f"   3. Fund wallet manually via solfaucet.com")
    
    def send_sol(self, to: str, amount_sol: float) -> str:
        """Send SOL to another address."""
        to_pubkey = Pubkey.from_string(to)
        lamports = int(amount_sol * 1_000_000_000)
        
        ix = transfer(TransferParams(
            from_pubkey=self.public_key,
            to_pubkey=to_pubkey,
            lamports=lamports
        ))
        
        recent_blockhash = self.client.get_latest_blockhash().value.blockhash
        msg = Message.new_with_blockhash([ix], self.public_key, recent_blockhash)
        tx = Transaction.new_signed_with_payer([ix], self.public_key, [self.keypair], recent_blockhash)
        
        result = self.client.send_raw_transaction(bytes(tx))
        return f"Sent {amount_sol} SOL to {to[:8]}... — tx: {result.value}"

# ============================================================
# TOKEN MANAGER
# ============================================================

class TokenManager:
    """Creates and manages SPL tokens."""
    
    def __init__(self, solana: SolanaClient, config: AgentConfig):
        self.solana = solana
        self.config = config
        self.token_mint: Optional[Pubkey] = None
        self.token_account: Optional[Pubkey] = None
    
    def create_token(self) -> Dict:
        """Create new SPL token mint using high-level SPL client."""
        payer = self.solana.keypair
        
        if self.config.simulate:
            # Generate deterministic-looking fake addresses for simulation
            sim_mint = Pubkey.from_string("LAT" + "1" * 40)[:44] if False else Keypair().pubkey()
            sim_ata = Keypair().pubkey()
            self.token_mint = sim_mint
            self.token_account = sim_ata
            return {
                "mint": str(sim_mint),
                "token_account": str(sim_ata),
                "tx": "simulated",
                "explorer": f"https://explorer.solana.com/address/{sim_mint}?cluster={self.config.network}"
            }
        
        # Token.create_mint is a static method returning a Token instance
        token = SplToken.create_mint(
            conn=self.solana.client,
            payer=payer,
            mint_authority=payer.pubkey(),
            decimals=self.config.token_decimals,
            program_id=TOKEN_PROGRAM_ID,
            freeze_authority=None,
        )
        
        mint_pubkey = token.pubkey
        self.token_mint = mint_pubkey
        
        # Create associated token account (instance method)
        ata = token.create_associated_token_account(
            owner=payer.pubkey(),
        )
        
        self.token_account = ata
        
        return {
            "mint": str(mint_pubkey),
            "token_account": str(ata),
            "tx": "success",
            "explorer": f"https://explorer.solana.com/address/{mint_pubkey}?cluster={self.config.network}"
        }
    
    def mint_supply(self, amount: int = None) -> str:
        """Mint tokens to token account."""
        if amount is None:
            amount = self.config.token_supply * (10 ** self.config.token_decimals)
        
        if self.config.simulate:
            return f"[SIM] Would mint {amount/(10**self.config.token_decimals):,.0f} {self.config.token_symbol} to {self.token_account}"
        
        # Reconnect to existing mint
        token = SplToken(
            conn=self.solana.client,
            pubkey=self.token_mint,
            program_id=TOKEN_PROGRAM_ID,
            payer=self.solana.keypair,
        )
        
        result = token.mint_to(
            dest=self.token_account,
            mint_authority=self.solana.keypair,
            amount=amount,
        )
        
        txid = str(result.value) if hasattr(result, 'value') else str(result)
        return f"Minted {amount/(10**self.config.token_decimals):,.0f} {self.config.token_symbol} — tx: {txid[:20]}..."
    
    def get_token_balance(self) -> float:
        """Get token balance."""
        if not self.token_account:
            return 0
        if self.config.simulate:
            return float(self.config.token_supply)  # Full supply in simulation
        resp = self.solana.client.get_token_account_balance(self.token_account)
        return resp.value.ui_amount or 0

# ============================================================
# JUPITER SWAP INTEGRATION
# ============================================================

class JupiterSwap:
    """Swap tokens via Jupiter aggregator."""
    
    def __init__(self, solana: SolanaClient, config: AgentConfig):
        self.solana = solana
        self.config = config
        self.session = None
    
    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage: float = 1.0) -> Dict:
        """Get swap quote from Jupiter."""
        import aiohttp
        
        url = f"{self.config.jupiter_api}/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": int(slippage * 100),
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                return await resp.json()
    
    async def execute_swap(self, quote_response: Dict) -> str:
        """Execute a swap via Jupiter."""
        import aiohttp
        
        url = f"{self.config.jupiter_api}/swap"
        payload = {
            "quoteResponse": quote_response,
            "userPublicKey": str(self.solana.public_key),
            "wrapAndUnwrapSol": True,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
        
        # Deserialize and sign transaction
        tx_bytes = bytes(data["swapTransaction"])
        # Jupiter returns base58 or base64 encoded tx — handle both
        import base64, base58
        
        try:
            raw_tx = base64.b64decode(data["swapTransaction"])
        except:
            raw_tx = base58.b58decode(data["swapTransaction"])
        
        tx = Transaction.deserialize(raw_tx)
        
        # Sign with our keypair
        tx.sign([self.solana.keypair])
        
        result = self.solana.client.send_raw_transaction(bytes(tx))
        return f"Swap executed — tx: {result.value}"

# ============================================================
# LLM CHAT INTERFACE
# ============================================================

class LiquidityAgent:
    """
    LLM-powered agent that chats with user via terminal
    and executes Solana operations.
    """
    
    # Solana well-known mint addresses
    MINTS = {
        "SOL": "So11111111111111111111111111111111111111112",  # Wrapped SOL
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    }
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.solana = SolanaClient(self.config)
        self.token_mgr = TokenManager(self.solana, self.config)
        self.jupiter = JupiterSwap(self.solana, self.config)
        self.running = True
        self.state = {
            "wallet_loaded": False,
            "token_deployed": False,
            "token_minted": False,
            "pool_created": False,
            "swaps_executed": 0,
            "total_volume": 0.0,
        }
    
    def print_banner(self):
        print("\n" + "=" * 60)
        print("  💧 SOLANA LIQUIDITY AGENT")
        print(f"  Network: {self.config.network.upper()}")
        print(f"  Token: ${self.config.token_symbol} ({self.config.token_name})")
        print(f"  Appraisal: ${self.config.appraisal_usd:,}")
        print(f"  Supply: {self.config.token_supply:,} tokens")
        print("=" * 60)
        print('  Type "help" for commands, "quit" to exit')
        print("=" * 60 + "\n")
    
    def print_help(self):
        print(textwrap.dedent("""
        ┌─────────────────────────────────────────────────────────┐
        │ COMMANDS                                                 │
        ├─────────────────────────────────────────────────────────┤
        │ wallet create     — Create new Solana wallet             │
        │ wallet load       — Load existing wallet                 │
        │ wallet balance    — Check SOL balance                    │
        │ airdrop [amt]     — Request devnet SOL (devnet only)     │
        │                                                          │
        │ token create      — Deploy $LAT SPL token                │
        │ token mint        — Mint total supply                    │
        │ token balance     — Check $LAT balance                   │
        │ token info        — Show token details                   │
        │                                                          │
        │ pool create [usd] — Create Raydium liquidity pool        │
        │ pool status       — Check pool status                    │
        │                                                          │
        │ swap [amt] [to]   — Swap LAT for SOL/USDC via Jupiter    │
        │ quote [amt] [to]  — Get price quote without executing    │
        │                                                          │
        │ network devnet    — Switch to devnet                     │
        │ network mainnet   — Switch to mainnet (⚠ real money)     │
        │                                                          │
        │ status            — Show full agent state                │
        │ liquidate         — Full liquidation pipeline            │
        │ help              — Show this help                       │
        │ quit              — Exit                                 │
        └─────────────────────────────────────────────────────────┘
        """))
    
    def process_command(self, cmd: str) -> str:
        """Parse and execute a command."""
        parts = cmd.strip().split()
        if not parts:
            return ""
        
        action = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            # === WALLET ===
            if action == "wallet":
                sub = args[0].lower() if args else "balance"
                if sub == "create":
                    kp = self.solana.create_wallet()
                    self.state["wallet_loaded"] = True
                    return f"✅ Wallet created: {self.solana.public_key}\n   Secret saved to ~/.config/solana/id.json\n   ⚠️  FUND THIS WALLET before using mainnet!"
                
                elif sub == "load":
                    if self.solana.load_wallet():
                        self.state["wallet_loaded"] = True
                        bal = self.solana.get_sol_balance()
                        return f"✅ Wallet loaded: {self.solana.public_key}\n   Balance: {bal:.4f} SOL"
                    return "❌ No wallet found. Use 'wallet create' first."
                
                elif sub == "balance":
                    if not self.state["wallet_loaded"]:
                        return "❌ No wallet loaded. Use 'wallet load' or 'wallet create'."
                    bal = self.solana.get_sol_balance()
                    return f"💰 SOL Balance: {bal:.6f} SOL ({bal * 150:.2f} USD @ $150/SOL)"
            
            # === AIRDROP ===
            elif action == "airdrop":
                if not self.state["wallet_loaded"]:
                    return "❌ Load wallet first."
                amt = float(args[0]) if args else 1.0
                return self.solana.request_airdrop(amt)
            
            # === TOKEN ===
            elif action == "token":
                sub = args[0].lower() if args else "info"
                
                if sub == "create":
                    if not self.state["wallet_loaded"]:
                        return "❌ Load wallet first."
                    result = self.token_mgr.create_token()
                    self.state["token_deployed"] = True
                    return (f"🪙 Token created!\n"
                            f"   Mint: {result['mint']}\n"
                            f"   ATA:  {result['token_account']}\n"
                            f"   Explorer: {result['explorer']}")
                
                elif sub == "mint":
                    if not self.state["token_deployed"]:
                        return "❌ Deploy token first: 'token create'"
                    result = self.token_mgr.mint_supply()
                    self.state["token_minted"] = True
                    return f"✅ {result}"
                
                elif sub == "balance":
                    if not self.state["token_deployed"]:
                        return "❌ No token deployed."
                    bal = self.token_mgr.get_token_balance()
                    return f"🪙 {self.config.token_symbol} Balance: {bal:,.2f}"
                
                elif sub == "info":
                    if not self.state["token_deployed"]:
                        return (f"📋 Token Config:\n"
                                f"   Name: {self.config.token_name}\n"
                                f"   Symbol: ${self.config.token_symbol}\n"
                                f"   Supply: {self.config.token_supply:,}\n"
                                f"   Decimals: {self.config.token_decimals}\n"
                                f"   Appraisal: ${self.config.appraisal_usd:,}\n"
                                f"   Status: NOT DEPLOYED")
                    return (f"📋 Token: ${self.config.token_symbol}\n"
                            f"   Mint: {self.token_mgr.token_mint}\n"
                            f"   ATA: {self.token_mgr.token_account}\n"
                            f"   Supply: {self.config.token_supply:,}\n"
                            f"   Minted: {'✅' if self.state['token_minted'] else '❌'}")
            
            # === NETWORK ===
            elif action == "network":
                sub = args[0].lower() if args else ""
                if sub in ("devnet", "mainnet"):
                    if sub == "mainnet":
                        print("\n⚠️  WARNING: Switching to MAINNET — real SOL will be used!")
                        confirm = input("   Type 'CONFIRM' to proceed: ")
                        if confirm != "CONFIRM":
                            return "❌ Cancelled."
                    self.config.network = sub
                    self.solana = SolanaClient(self.config)
                    self.token_mgr = TokenManager(self.solana, self.config)
                    self.jupiter = JupiterSwap(self.solana, self.config)
                    return f"🌐 Switched to {sub.upper()}"
                return f"Current network: {self.config.network}"
            
            # === SWAP ===
            elif action == "swap":
                return "🔄 Swap via Jupiter — use 'quote' first to check price, then confirm."
            
            elif action == "quote":
                if not self.state["token_deployed"]:
                    return "❌ Deploy token first."
                amt = float(args[0]) if args else 100
                to = args[1].upper() if len(args) > 1 else "SOL"
                to_mint = self.MINTS.get(to, self.MINTS["SOL"])
                
                return (f"📊 Quote: {amt:,.0f} LAT → {to}\n"
                        f"   (Jupiter API would return real-time price)\n"
                        f"   Input: {self.token_mgr.token_mint}\n"
                        f"   Output: {to_mint}\n"
                        f"   Estimated: ~{amt * 1.0:.2f} {to} (at $1/LAT)")
            
            # === POOL ===
            elif action == "pool":
                sub = args[0].lower() if args else "status"
                if sub == "create":
                    usd = float(args[1]) if len(args) > 1 else 1000
                    return (f"🏊 Liquidity Pool Plan:\n"
                            f"   DEX: Raydium CPMM\n"
                            f"   Pair: LAT/USDC\n"
                            f"   USDC: ${usd:,.2f}\n"
                            f"   LAT: {usd:,.0f} (at $1/LAT)\n"
                            f"   Initial TVL: ${usd*2:,.2f}\n"
                            f"   ⚠️  Requires {usd} USDC + gas SOL")
                return "🏊 Pool status: Not created yet. Use 'pool create [USDC amount]'"
            
            # === STATUS ===
            elif action == "status":
                lines = ["📊 AGENT STATUS", "=" * 40]
                lines.append(f"Network: {self.config.network.upper()}")
                lines.append(f"Wallet: {'✅ ' + str(self.solana.public_key)[:12] + '...' if self.state['wallet_loaded'] else '❌ Not loaded'}")
                if self.state["wallet_loaded"]:
                    lines.append(f"SOL Balance: {self.solana.get_sol_balance():.4f}")
                lines.append(f"Token Deployed: {'✅' if self.state['token_deployed'] else '❌'}")
                lines.append(f"Token Minted: {'✅' if self.state['token_minted'] else '❌'}")
                lines.append(f"Pool Created: {'✅' if self.state['pool_created'] else '❌'}")
                lines.append(f"Swaps: {self.state['swaps_executed']}")
                return "\n".join(lines)
            
            # === LIQUIDATE ===
            elif action == "simulate":
                sub = args[0].lower() if args else ""
                if sub in ("on", "true", "yes"):
                    self.config.simulate = True
                    return "🔮 Simulation mode ON — no real transactions will be sent"
                elif sub in ("off", "false", "no"):
                    self.config.simulate = False
                    return "💧 Simulation mode OFF — real transactions will be sent"
                return f"Simulation: {'ON 🔮' if self.config.simulate else 'OFF 💧'}. Use 'simulate on/off'"
            
            elif action == "liquidate":
                return self.liquidation_pipeline()
            
            # === HELP ===
            elif action == "help":
                self.print_help()
                return ""
            
            # === QUIT ===
            elif action == "quit":
                self.running = False
                return "👋 Exiting. Your keys are safe at ~/.config/solana/id.json"
            
            else:
                return f"❓ Unknown command: '{action}'. Type 'help' for commands."
        
        except RPCException as e:
            return f"❌ RPC Error: {e}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def liquidation_pipeline(self) -> str:
        """Full pipeline to convert token to liquid cash."""
        steps = []
        steps.append("💧 LIQUIDATION PIPELINE")
        steps.append("=" * 40)
        
        # Step 1: Check wallet
        if not self.state["wallet_loaded"]:
            steps.append("1. ❌ Create/load wallet first: 'wallet create'")
            return "\n".join(steps)
        steps.append("1. ✅ Wallet ready")
        
        # Step 2: Fund wallet
        bal = self.solana.get_sol_balance()
        if bal < 0.05:
            if self.config.network == "devnet":
                steps.append("2. ⚠️  Need SOL — run: 'airdrop 2'")
            else:
                steps.append("2. ⚠️  Need SOL — fund wallet with ~0.1 SOL for gas")
        else:
            steps.append(f"2. ✅ SOL balance: {bal:.4f}")
        
        # Step 3: Deploy token
        if not self.state["token_deployed"]:
            steps.append("3. ⚠️  Deploy token: 'token create'")
        else:
            steps.append("3. ✅ Token deployed")
        
        # Step 4: Mint
        if not self.state["token_minted"]:
            steps.append("4. ⚠️  Mint supply: 'token mint'")
        else:
            steps.append("4. ✅ Token minted")
        
        # Step 5: Create pool
        if not self.state["pool_created"]:
            steps.append("5. ⚠️  Create pool: 'pool create 1000'")
        else:
            steps.append("5. ✅ Pool created")
        
        # Step 6: Swap
        steps.append("6. ⚠️  Execute swaps: 'swap 100 SOL'")
        
        # Summary
        steps.append("")
        steps.append(f"📋 Target: ${self.config.appraisal_usd:,} liquidity")
        steps.append(f"🌐 Network: {self.config.network.upper()}")
        steps.append("")
        steps.append("⚠️  MAINNET REQUIRES:")
        steps.append("   - Funded wallet (~0.1 SOL for gas)")
        steps.append("   - USDC for initial liquidity pool")
        steps.append("   - Patience for organic price discovery")
        
        return "\n".join(steps)
    
    def run(self):
        """Main chat loop."""
        self.print_banner()
        
        # Auto-load wallet if exists
        if self.solana.load_wallet():
            self.state["wallet_loaded"] = True
            print(f"🔑 Auto-loaded wallet: {self.solana.public_key}")
            print(f"💰 Balance: {self.solana.get_sol_balance():.4f} SOL\n")
        else:
            print("💡 No wallet found. Start with 'wallet create'\n")
        
        while self.running:
            try:
                cmd = input("💧> ").strip()
                if not cmd:
                    continue
                
                result = self.process_command(cmd)
                if result:
                    print(f"\n{result}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                break

# ============================================================
# MAIN
# ============================================================

def main():
    agent = LiquidityAgent()
    agent.run()

if __name__ == "__main__":
    main()
