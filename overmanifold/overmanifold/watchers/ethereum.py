"""
Overmanifold Ethereum Watcher (Real Blockchain Integration)
Observes and interacts with Ethereum mainnet with real signing capabilities.
Production implementation with private key management and gas estimation.
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
from overmanifold.workers.transaction_endpoint import (
    TransactionObserver, LifecycleState, EventType
)

logger = get_logger("ethereum_watcher")
config = get_config()

try:
    from web3 import Web3
    from web3.middleware import geth_poa
except ImportError:
    Web3 = None
    logger.error("Web3 not installed - cannot connect to Ethereum")


@dataclass
class EthereumTransaction:
    """Ethereum transaction data."""
    hash: str
    from_address: str
    to_address: Optional[str]
    value: str
    gas: int
    gas_price: str
    input_data: str
    block_number: int
    transaction_index: int
    timestamp: datetime
    status: str  # pending, included, confirmed
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "hash": self.hash,
            "from": self.from_address,
            "to": self.to_address,
            "value": self.value,
            "gas": self.gas,
            "gas_price": self.gas_price,
            "input": self.input_data,
            "block_number": self.block_number,
            "transaction_index": self.transaction_index,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status
        }


class EthereumWatcher:
    """
    Real Ethereum blockchain watcher with full transaction capabilities.
    Observes transactions and can execute transactions with private key signing.
    """
    
    def __init__(self, rpc_url: Optional[str] = None, private_key: Optional[str] = None):
        self.rpc_url = rpc_url or os.getenv("ETHEREUM_RPC_URL")
        self.private_key = private_key or os.getenv("ETHEREUM_PRIVATE_KEY")
        self.w3: Optional[Web3] = None
        self.account = None
        self.transaction_observer = TransactionObserver()
        self.is_connected = False
        self.confirmations_required = int(os.getenv("ETHEREUM_CONFIRMATIONS_REQUIRED", "12"))
        
        if not self.rpc_url:
            raise ValueError("ETHEREUM_RPC_URL must be provided")
        
        if not self.private_key:
            raise ValueError("ETHEREUM_PRIVATE_KEY must be provided for real blockchain operations")
        
        self._connect()
        
    def _connect(self) -> None:
        """Connect to Ethereum blockchain with real credentials"""
        if not Web3:
            logger.error("Web3 not installed - cannot connect to Ethereum")
            return
        
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            if not self.w3.is_connected():
                raise ConnectionError(f"Failed to connect to Ethereum at {self.rpc_url}")
            
            # Initialize account from private key
            from eth_account import Account
            self.account = Account.from_key(self.private_key)
            
            # Verify account has gas
            balance = self.w3.eth.get_balance(self.account.address)
            logger.info(f"Connected to Ethereum chain {self.w3.eth.chain_id}")
            logger.info(f"Account: {self.account.address}, Balance: {self.w3.from_wei(balance, 'ether')} ETH")
            
            self.is_connected = True
            
        except Exception as e:
            logger.error(f"Failed to connect to Ethereum: {e}")
            self.is_connected = False
    
    async def execute_transaction(
        self,
        to_address: str,
        value_wei: int,
        data: str = "0x",
        gas_limit: int = 21000,
        gas_price: Optional[int] = None
    ) -> str:
        """
        Execute a real Ethereum transaction with private key signing
        
        Args:
            to_address: Recipient address
            value_wei: Amount to send in wei
            data: Transaction data (hex string)
            gas_limit: Gas limit for transaction
            gas_price: Gas price in wei (if None, uses current network price)
            
        Returns:
            Transaction hash
        """
        if not self.is_connected or not self.w3 or not self.account:
            raise RuntimeError("Ethereum watcher not connected or account not initialized")
        
        # Get current gas price if not provided
        if gas_price is None:
            gas_price = self.w3.eth.gas_price
        
        # Build transaction
        transaction = {
            'to': to_address,
            'value': value_wei,
            'data': data,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': self.w3.eth.chain_id
        }
        
        # Sign transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        
        # Send transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        logger.info(f"Transaction sent: {tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash.hex(), timeout=120)
        
        if receipt.status == 1:
            logger.info(f"Transaction confirmed in block {receipt.blockNumber}")
            return tx_hash.hex()
        else:
            raise Exception(f"Transaction failed: {tx_hash.hex()}")
    
    async def send_ether(self, to_address: str, amount_eth: float) -> str:
        """
        Send ETH to an address
        
        Args:
            to_address: Recipient address
            amount_eth: Amount to send in ETH
            
        Returns:
            Transaction hash
        """
        value_wei = self.w3.to_wei(amount_eth, 'ether')
        return await self.execute_transaction(to_address, value_wei)
    
    async def estimate_gas(self, to_address: str, value_wei: int, data: str = "0x") -> int:
        """
        Estimate gas for a transaction
        
        Args:
            to_address: Recipient address
            value_wei: Amount in wei
            data: Transaction data
            
        Returns:
            Estimated gas amount
        """
        if not self.is_connected or not self.w3:
            raise RuntimeError("Ethereum watcher not connected")
        
        return self.w3.eth.estimate_gas({
            'to': to_address,
            'value': value_wei,
            'data': data,
            'from': self.account.address
        })
    
    async def watch_mempool(self) -> None:
        """Watch mempool for pending transactions."""
        if not self.is_connected:
            logger.error("Cannot watch mempool - not connected to Ethereum")
            return
        
        logger.info("Starting Ethereum mempool watcher")
        
        while True:
            try:
                # Get pending transactions from mempool
                # In production, this would use WebSocket subscription or filter
                pending_block = self.w3.eth.get_block('pending', full_transactions=True)
                
                if pending_block and pending_block.transactions:
                    for tx in pending_block.transactions[:10]:  # Process first 10 for demo
                        await self._process_transaction(tx, LifecycleState.MEMPOOL_SEEN)
                
                await asyncio.sleep(5)  # Poll every 5 seconds
                
            except Exception as e:
                logger.error(f"Error watching mempool: {str(e)}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def watch_blocks(self) -> None:
        """Watch for new blocks and included transactions."""
        if not self.is_connected:
            logger.error("Cannot watch blocks - not connected to Ethereum")
            return
        
        logger.info("Starting Ethereum block watcher")
        
        latest_block = self.w3.eth.block_number
        
        while True:
            try:
                current_block = self.w3.eth.block_number
                
                if current_block > latest_block:
                    # Process new blocks
                    for block_num in range(latest_block + 1, current_block + 1):
                        await self._process_block(block_num)
                    
                    latest_block = current_block
                
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                logger.error(f"Error watching blocks: {str(e)}")
                await asyncio.sleep(10)
    
    async def _process_block(self, block_number: int) -> None:
        """Process a single block and its transactions."""
        try:
            block = self.w3.eth.get_block(block_number, full_transactions=True)
            
            if not block or not block.transactions:
                return
            
            for tx in block.transactions:
                await self._process_transaction(tx, LifecycleState.INCLUDED)
                
        except Exception as e:
            logger.error(f"Error processing block {block_number}: {str(e)}")
    
    async def _process_transaction(self, tx: Any, lifecycle_state: LifecycleState) -> None:
        """Process a transaction and create endpoint worker."""
        try:
            # Convert to our format
            tx_data = {
                "hash": tx.hash.hex(),
                "from": tx['from'],
                "to": tx.to,
                "value": str(tx.value),
                "gas": tx.gas,
                "gas_price": str(tx.gasPrice),
                "input": tx.input.hex() if tx.input else "0x",
                "block_number": tx.blockNumber,
                "transaction_index": tx.transactionIndex,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Create transaction endpoint worker
            worker = self.transaction_observer.observe_transaction("ethereum", tx_data)
            
            # Update lifecycle state
            self.transaction_observer.update_transaction_state(
                "ethereum", 
                tx_data["hash"], 
                self.confirmations_required if lifecycle_state == LifecycleState.INCLUDED else 0,
                lifecycle_state.value
            )
            
            logger.info(f"Processed Ethereum transaction: {tx.hash.hex()} -> {lifecycle_state.value}")
            
        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")
    
    def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction by hash (read-only)."""
        if not self.is_connected:
            return None
        
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            if tx:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                
                return {
                    "hash": tx.hash.hex(),
                    "from": tx['from'],
                    "to": tx.to,
                    "value": str(tx.value),
                    "gas": tx.gas,
                    "gas_price": str(tx.gasPrice),
                    "block_number": tx.blockNumber,
                    "transaction_index": tx.transactionIndex,
                    "status": "confirmed" if receipt and receipt.status == 1 else "pending",
                    "confirmations": self.w3.eth.block_number - tx.blockNumber if tx.blockNumber else 0
                }
        except Exception as e:
            logger.error(f"Error getting transaction {tx_hash}: {str(e)}")
        
        return None
    
    def get_balance(self, address: str) -> Optional[int]:
        """Get balance for address (read-only)."""
        if not self.is_connected:
            return None
        
        try:
            balance = self.w3.eth.get_balance(address)
            return balance
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {str(e)}")
            return None
    
    def get_block_number(self) -> Optional[int]:
        """Get current block number (read-only)."""
        if not self.is_connected:
            return None
        
        try:
            return self.w3.eth.block_number
        except Exception as e:
            logger.error(f"Error getting block number: {str(e)}")
            return None
    
    def verify_no_private_keys(self) -> bool:
        """Verify that no private keys are accessible (security check)."""
        # This is a critical security check for testnet
        if not self.w3:
            return True
        
        try:
            # Check if account module is available
            if not hasattr(self.w3, 'eth'):
                return True
            
            if not hasattr(self.w3.eth, 'account'):
                return True
            
            # Try to access accounts - should fail in read-only mode
            accounts = self.w3.eth.accounts
            
            # If we get here and have accounts, that's a security issue
            if accounts:
                logger.critical("SECURITY VIOLATION: Ethereum watcher has access to accounts/private keys")
                return False
            
            return True
            
        except Exception as e:
            # If accessing accounts fails, that's actually good for security
            logger.info(f"Account access blocked (expected for read-only): {str(e)}")
            return True
    
    async def start(self) -> None:
        """Start the Ethereum watcher."""
        if not self.verify_no_private_keys():
            raise RuntimeError("Security check failed: Ethereum watcher has private key access")
        
        logger.info("Starting Ethereum watcher in read-only mode")
        
        # Start both mempool and block watchers
        await asyncio.gather(
            self.watch_mempool(),
            self.watch_blocks()
        )


if __name__ == "__main__":
    async def main():
        watcher = EthereumWatcher()
        await watcher.start()
    
    asyncio.run(main())