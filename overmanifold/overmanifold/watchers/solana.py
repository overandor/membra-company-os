"""
Overmanifold Solana Watcher (Real Blockchain Integration)
Observes and interacts with Solana mainnet with real signing capabilities.
Production implementation with private key management and transaction execution.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import sys
import os

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.infrastructure.config import get_config

logger = get_logger("solana_watcher")
config = get_config()

try:
    from solana.rpc.async_api import AsyncClient
    from solana.transaction import Transaction
    from solana.publickey import PublicKey
except ImportError:
    AsyncClient = None
    Transaction = None
    PublicKey = None
    logger.error("Solana library not installed - cannot connect to Solana")
from overmanifold.workers.transaction_endpoint import (
    TransactionObserver, LifecycleState, EventType
)

logger = get_logger("solana_watcher")
config = get_config()


@dataclass
class SolanaTransaction:
    """Solana transaction data."""
    signature: str
    slot: int
    block_time: Optional[datetime]
    fee: int
    status: str
    error: Optional[str]
    accounts: List[str]
    instructions: List[Dict]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "signature": self.signature,
            "slot": self.slot,
            "block_time": self.block_time.isoformat() if self.block_time else None,
            "fee": self.fee,
            "status": self.status,
            "error": self.error,
            "accounts": self.accounts,
            "instructions": self.instructions
        }


class SolanaWatcher:
    """
    Real Solana blockchain watcher with full transaction capabilities.
    Observes transactions and can execute transactions with keypair signing.
    """
    
    def __init__(self, rpc_url: Optional[str] = None, private_key: Optional[str] = None):
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL")
        self.private_key = private_key or os.getenv("SOLANA_PRIVATE_KEY")
        self.client: Optional[AsyncClient] = None
        self.keypair = None
        self.transaction_observer = TransactionObserver()
        self.is_connected = False
        self.confirmations_required = int(os.getenv("SOLANA_CONFIRMATIONS_REQUIRED", "32"))
        
        if not self.rpc_url:
            raise ValueError("SOLANA_RPC_URL must be provided")
        
        if not self.private_key:
            raise ValueError("SOLANA_PRIVATE_KEY must be provided for real blockchain operations")
        
        self._connect()
    
    def _connect(self) -> None:
        """Connect to Solana blockchain with real credentials"""
        if not AsyncClient:
            logger.error("Solana library not installed - cannot connect to Solana")
            return
        
        try:
            self.client = AsyncClient(self.rpc_url)
            
            # Test connection
            version = asyncio.run(self.client.get_version())
            if version:
                logger.info(f"Connected to Solana network. Version: {version}")
                
                # Initialize keypair from private key
                from solders.keypair import Keypair
                from solders.pubkey import Pubkey
                import base58
                
                # Decode private key (assuming base58 encoding)
                private_key_bytes = base58.b58decode(self.private_key)
                self.keypair = Keypair.from_bytes(private_key_bytes)
                
                # Get balance
                balance = asyncio.run(self.client.get_balance(self.keypair.pubkey()))
                logger.info(f"Solana address: {self.keypair.pubkey()}")
                logger.info(f"Balance: {balance.value / 1e9} SOL")
                
                self.is_connected = True
            else:
                raise ConnectionError("Failed to connect to Solana network")
                
        except Exception as e:
            logger.error(f"Failed to connect to Solana: {e}")
            self.is_connected = False
    
    async def execute_transaction(
        self,
        instructions: list,
        signers: list = None
    ) -> str:
        """
        Execute a real Solana transaction
        
        Args:
            instructions: List of Solana instructions
            signers: List of signers (defaults to keypair)
            
        Returns:
            Transaction signature
        """
        if not self.is_connected or not self.client or not self.keypair:
            raise RuntimeError("Solana watcher not connected or keypair not initialized")
        
        from solana.transaction import Transaction
        
        signers = signers or [self.keypair]
        
        # Create transaction
        transaction = Transaction()
        for instruction in instructions:
            transaction.add(instruction)
        
        # Send transaction
        response = await self.client.send_transaction(transaction, *signers)
        
        logger.info(f"Transaction sent: {response.value}")
        
        # Confirm transaction
        confirmation = await self.client.confirm_transaction(
            response.value,
            commitment="confirmed"
        )
        
        if confirmation.value[0].err is None:
            logger.info("Transaction confirmed successfully")
            return response.value
        else:
            raise Exception(f"Transaction failed: {confirmation.value[0].err}")
    
    async def send_sol(self, to_address: str, amount_sol: float) -> str:
        """
        Send SOL to an address
        
        Args:
            to_address: Recipient address (base58 encoded)
            amount_sol: Amount to send in SOL
            
        Returns:
            Transaction signature
        """
        from solders.pubkey import Pubkey
        from solders.keypair import Keypair
        from solana.system_program import TransferParams, transfer
        from solana.transaction import Transaction
        
        # Convert to lamports
        amount_lamports = int(amount_sol * 1e9)
        
        # Create transfer instruction
        to_pubkey = Pubkey.from_string(to_address)
        transfer_instruction = transfer(
            TransferParams(
                from_pubkey=self.keypair.pubkey(),
                to_pubkey=to_pubkey,
                lamports=amount_lamports
            )
        )
        
        return await self.execute_transaction([transfer_instruction])
    
    async def watch_slots(self) -> None:
        """Watch for new slots and transactions."""
        if not self.is_connected:
            logger.error("Cannot watch slots - not connected to Solana")
            return
        
        logger.info("Starting Solana slot watcher")
        
        last_slot = None
        
        while True:
            try:
                # Get current slot
                slot_info = await self.client.get_slot()
                current_slot = slot_info['result']
                
                if last_slot is None:
                    last_slot = current_slot
                elif current_slot > last_slot:
                    # Process new slots
                    for slot_num in range(last_slot + 1, current_slot + 1):
                        await self._process_slot(slot_num)
                    
                    last_slot = current_slot
                
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                logger.error(f"Error watching slots: {str(e)}")
                await asyncio.sleep(10)
    
    async def _process_slot(self, slot_number: int) -> None:
        """Process a single slot and its transactions."""
        try:
            # Get confirmed block for this slot
            block = await self.client.get_confirmed_block(slot_number)
            
            if not block or 'result' not in block:
                return
            
            block_data = block['result']
            transactions = block_data.get('transactions', [])
            
            for tx in transactions:
                if 'transaction' in tx:
                    await self._process_transaction(tx['transaction'], slot_number)
                
        except Exception as e:
            logger.error(f"Error processing slot {slot_number}: {str(e)}")
    
    async def _process_transaction(self, tx: Dict, slot_number: int) -> None:
        """Process a Solana transaction and create endpoint worker."""
        try:
            signature = tx.get('signatures', [''])[0] if isinstance(tx, dict) else str(tx)
            
            if not signature:
                return
            
            # Get transaction details
            tx_detail = await self.client.get_confirmed_transaction(signature)
            
            if not tx_detail or 'result' not in tx_detail:
                return
            
            tx_data = tx_detail['result']
            
            # Convert to our format
            tx_dict = {
                "hash": signature,
                "slot": slot_number,
                "fee": tx_data.get('meta', {}).get('fee', 0),
                "status": "confirmed" if tx_data.get('meta') else "pending",
                "accounts": [str(acc) for acc in tx_data.get('message', {}).get('accountKeys', [])],
                "instructions": self._parse_instructions(tx_data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Create transaction endpoint worker
            worker = self.transaction_observer.observe_transaction("solana", tx_dict)
            
            # Update lifecycle state
            self.transaction_observer.update_transaction_state(
                "solana", 
                signature, 
                self.confirmations_required,
                LifecycleState.INCLUDED.value
            )
            
            logger.info(f"Processed Solana transaction: {signature} -> included")
            
        except Exception as e:
            logger.error(f"Error processing Solana transaction: {str(e)}")
    
    def _parse_instructions(self, tx_data: Dict) -> List[Dict]:
        """Parse transaction instructions."""
        instructions = []
        
        try:
            message = tx_data.get('message', {})
            ix_list = message.get('instructions', [])
            
            for ix in ix_list:
                instructions.append({
                    "program_id": str(ix.get('programIdIndex', '')),
                    "accounts": ix.get('accounts', []),
                    "data": ix.get('data', '')
                })
        except Exception as e:
            logger.error(f"Error parsing instructions: {str(e)}")
        
        return instructions
    
    async def get_transaction(self, signature: str) -> Optional[Dict]:
        """Get transaction by signature (read-only)."""
        if not self.is_connected:
            return None
        
        try:
            tx_detail = await self.client.get_confirmed_transaction(signature)
            
            if tx_detail and 'result' in tx_detail:
                tx_data = tx_detail['result']
                
                return {
                    "signature": signature,
                    "slot": tx_data.get('slot'),
                    "fee": tx_data.get('meta', {}).get('fee', 0),
                    "status": "confirmed",
                    "accounts": [str(acc) for acc in tx_data.get('message', {}).get('accountKeys', [])]
                }
        except Exception as e:
            logger.error(f"Error getting Solana transaction {signature}: {str(e)}")
        
        return None
    
    async def get_balance(self, address: str) -> Optional[int]:
        """Get balance for address (read-only)."""
        if not self.is_connected:
            return None
        
        try:
            balance = await self.client.get_balance(PublicKey(address))
            return balance['result'] if 'result' in balance else None
        except Exception as e:
            logger.error(f"Error getting Solana balance for {address}: {str(e)}")
            return None
    
    async def get_slot(self) -> Optional[int]:
        """Get current slot (read-only)."""
        if not self.is_connected:
            return None
        
        try:
            slot_info = await self.client.get_slot()
            return slot_info['result'] if 'result' in slot_info else None
        except Exception as e:
            logger.error(f"Error getting Solana slot: {str(e)}")
            return None
    
    def verify_no_private_keys(self) -> bool:
        """Verify that no private keys are accessible (security check)."""
        # This is a critical security check for testnet
        # Solana AsyncClient doesn't have direct account access by default
        # But we should still verify our configuration
        
        if not self.read_only:
            logger.critical("SECURITY VIOLATION: Solana watcher is not in read-only mode")
            return False
        
        # Check for any keypair files or environment variables
        if os.getenv("SOLANA_PRIVATE_KEY"):
            logger.critical("SECURITY VIOLATION: Solana private key found in environment")
            return False
        
        keyfile_paths = [
            "~/.config/solana/id.json",
            "~/keypairs.json",
            "./keypairs.json"
        ]
        
        for keyfile_path in keyfile_paths:
            expanded_path = os.path.expanduser(keyfile_path)
            if os.path.exists(expanded_path):
                logger.critical(f"SECURITY VIOLATION: Solana keyfile found at {expanded_path}")
                return False
        
        logger.info("Solana watcher security check passed - no private keys found")
        return True
    
    async def start(self) -> None:
        """Start the Solana watcher."""
        if not self.verify_no_private_keys():
            raise RuntimeError("Security check failed: Solana watcher has private key access")
        
        logger.info("Starting Solana watcher in read-only mode")
        
        # Start slot watcher
        await self.watch_slots()


if __name__ == "__main__":
    async def main():
        watcher = SolanaWatcher()
        await watcher.start()
    
    asyncio.run(main())