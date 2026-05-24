"""
LLM-Based Custom Blockchain System
Proprietary blockchain without Web3 - custom implementation with LLM transaction understanding
"""

import asyncio
import logging
import json
import hashlib
import secrets
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import os
import asyncio
import time

from openai import AsyncOpenAI

from overmanifold.infrastructure.logging_config import get_logger

logger = get_logger("llm_custom_blockchain")


class TransactionType(Enum):
    """Custom blockchain transaction types"""
    PAYMENT = "payment"
    VERIFICATION = "verification"
    REGISTRATION = "registration"
    SPONSORSHIP = "sponsorship"
    GOVERNANCE = "governance"
    REWARD = "reward"
    SMART_CONTRACT = "smart_contract"


class TransactionStatus(Enum):
    """Transaction lifecycle status"""
    PENDING = "pending"
    VALIDATED = "validated"
    EXECUTED = "executed"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REVERTED = "reverted"


@dataclass
class Block:
    """Custom blockchain block structure"""
    block_number: int
    timestamp: datetime
    transactions: List[str]  # Transaction IDs
    parent_hash: str
    block_hash: str = ""
    state_root: str = ""
    validator: str = ""
    gas_used: int = 0
    gas_limit: int = 1000000
    
    def __post_init__(self):
        if not self.block_hash:
            self.block_hash = self._calculate_block_hash()
    
    def _calculate_block_hash(self) -> str:
        """Calculate block hash"""
        block_data = f"{self.block_number}{self.timestamp.isoformat()}{self.parent_hash}{self.transactions}{self.validator}{self.gas_used}"
        return hashlib.sha256(block_data.encode()).hexdigest()


@dataclass
class Transaction:
    """Custom blockchain transaction structure"""
    tx_id: str
    from_address: str
    to_address: str
    amount: float
    transaction_type: TransactionType
    timestamp: datetime
    status: TransactionStatus = TransactionStatus.PENDING
    gas_limit: int = 21000
    gas_used: int = 0
    gas_price: float = 0.0
    data: str = ""
    signature: str = ""
    block_number: int = 0
    confirmation_count: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.tx_id:
            self.tx_id = self._generate_transaction_id()
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        data = f"{self.from_address}{self.to_address}{self.amount}{self.timestamp.isoformat()}{secrets.token_hex(8)}"
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class Account:
    """Custom blockchain account structure"""
    address: str
    balance: float = 0.0
    nonce: int = 0
    storage: Dict[str, str] = field(default_factory=dict)
    code: str = ""  # Smart contract code
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.address:
            self.address = self._generate_address()
    
    def _generate_address(self) -> str:
        """Generate custom address"""
        data = f"overmanifold{secrets.token_bytes(20).hex()}{datetime.utcnow().isoformat()}"
        return "0x" + hashlib.sha256(data.encode()).hexdigest()[:40]


class LLMTransactionValidator:
    """LLM-based transaction validation system"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if self.openai_api_key:
            self.llm_client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.llm_client = None
            logger.warning("No OpenAI API key, LLM features limited")
        
        self.validation_prompt = self._build_validation_prompt()
    
    def _build_validation_prompt(self) -> str:
        """Build proprietary prompt for transaction validation"""
        return """You are an intelligent transaction validator for Overmanifold Protocol. Validate blockchain transactions for security and correctness.

VALIDATION RULES:
1. SENDER_VALID: Sender address must be valid format and exist
2. RECIPIENT_VALID: Recipient address must be valid format and exist
3. AMOUNT_VALID: Amount must be positive and within limits
4. BALANCE_SUFFICIENT: Sender must have sufficient balance
5. NONCE_VALID: Nonce must be correct for sender
6. SIGNATURE_VALID: Signature must be valid for sender address
7. DATA_SAFE: Transaction data must not contain malicious content
8. GAS_SUFFICIENT: Gas limit must be sufficient for transaction
9. TYPE_VALID: Transaction type must be supported
10. COMPLIANCE_OK: Transaction must comply with regulatory requirements

VALIDATION FORMAT:
Return JSON with this exact structure:
{
  "is_valid": true|false,
  "confidence": 0.0-1.0,
  "validation_checks": {
    "sender_valid": true|false,
    "recipient_valid": true|false,
    "amount_valid": true|false,
    "balance_sufficient": true|false,
    "nonce_valid": true|false,
    "signature_valid": true|false,
    "data_safe": true|false,
    "gas_sufficient": true|false,
    "type_valid": true|false,
    "compliance_ok": true|false
  },
  "errors": ["error1", "error2"],
  "warnings": ["warning1", "warning2"],
  "reasoning": "explain validation decision",
  "gas_estimate": 0
}

Be thorough and security-conscious. Reject any transaction that could be malicious or invalid."""

    async def validate_transaction(
        self,
        transaction: Transaction,
        sender_balance: float,
        sender_nonce: int
    ) -> Dict[str, Any]:
        """Validate transaction using LLM analysis"""
        
        if not self.llm_client:
            # Fallback to rule-based validation
            return self._fallback_validation(transaction, sender_balance, sender_nonce)
        
        try:
            # Prepare validation context
            validation_context = {
                "transaction_type": transaction.transaction_type.value,
                "from_address": transaction.from_address,
                "to_address": transaction.to_address,
                "amount": transaction.amount,
                "gas_limit": transaction.gas_limit,
                "gas_price": transaction.gas_price,
                "data": transaction.data[:200] if transaction.data else "",
                "sender_balance": sender_balance,
                "sender_nonce": sender_nonce,
                "timestamp": transaction.timestamp.isoformat()
            }
            
            validation_prompt = f"{self.validation_prompt}\n\nTransaction: {json.dumps(validation_context, indent=2)}"
            
            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.validation_prompt},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent validation
                response_format={"type": "json_object"}
            )
            
            validation_result = json.loads(response.choices[0].message.content)
            
            logger.info(f"LLM transaction validation: {validation_result['is_valid']} "
                        f"(confidence: {validation_result['confidence']})")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"LLM validation failed: {e}, using fallback")
            return self._fallback_validation(transaction, sender_balance, sender_nonce)
    
    def _fallback_validation(self, transaction: Transaction, sender_balance: float, sender_nonce: int) -> Dict[str, Any]:
        """Fallback rule-based transaction validation"""
        validation_checks = {}
        errors = []
        warnings = []
        
        # Validate amount
        validation_checks["amount_valid"] = transaction.amount > 0 and transaction.amount <= 1000000
        
        if not validation_checks["amount_valid"]:
            errors.append("Invalid amount")
        
        # Validate balance
        validation_checks["balance_sufficient"] = sender_balance >= transaction.amount
        
        if not validation_checks["balance_sufficient"]:
            errors.append("Insufficient balance")
        
        # Validate nonce
        validation_checks["nonce_valid"] = transaction.nonce == sender_nonce
        
        if not validation_checks["nonce_valid"]:
            errors.append("Invalid nonce")
        
        # Validate addresses
        validation_checks["sender_valid"] = self._validate_address(transaction.from_address)
        validation_checks["recipient_valid"] = _validate_address(transaction.to_address)
        
        if not validation_checks["sender_valid"]:
            errors.append("Invalid sender address")
        
        if not validation_checks["recipient_valid"]:
            errors.append("Invalid recipient address")
        
        # Validate gas
        validation_checks["gas_sufficient"] = transaction.gas_limit >= 21000
        
        if not validation_checks["gas_sufficient"]:
            warnings.append("Low gas limit")
        
        is_valid = all(validation_checks.values()) and len(errors) == 0
        
        return {
            "is_valid": is_valid,
            "confidence": 0.85,
            "validation_checks": validation_checks,
            "errors": errors,
            "warnings": warnings,
            "reasoning": "Rule-based validation",
            "gas_estimate": transaction.gas_limit
        }
    
    def _validate_address(self, address: str) -> bool:
        """Validate custom address format"""
        return address.startswith("0x") and len(address) == 42


class CustomBlockchain:
    """Proprietary LLM-based blockchain implementation"""
    
    def __init__(self, openai_api_key: str = None, chain_id: str = "overmanifold-1"):
        self.chain_id = chain_id
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize LLM validator
        self.validator = LLMTransactionValidator(self.openai_api_key)
        
        # Initialize LLM client for consensus
        if self.openai_api_key:
            self.llm_client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.llm_client = None
        
        # Blockchain state
        self.accounts: Dict[str, Account] = {}
        self.blocks: Dict[int, Block] = {}
        self.transactions: Dict[str, Transaction] = {}
        self.pending_transactions: List[str] = []
        
        # Chain configuration
        self.block_number = 0
        self.difficulty = 1
        self.block_time = 15  # seconds
        self.miner_address = None
        self.is_running = False
        
        # Initialize genesis accounts
        self._initialize_genesis()
        
        # Build LLM consensus prompt
        self.consensus_prompt = self._build_consensus_prompt()
    
    def _initialize_genesis(self):
        """Initialize genesis block and accounts"""
        # Create genesis block
        genesis_block = Block(
            block_number=0,
            timestamp=datetime.utcnow(),
            transactions=[],
            parent_hash="0" * 64,
            validator="genesis"
        )
        
        self.blocks[0] = genesis_block
        self.block_number = 1
        
        # Create initial accounts
        self._create_account("0x0000000000000000000000000000000000000001", balance=1000000)  # Treasury
        self._create_account("0x0000000000000000000000000000000000000002", balance=1000000)  # Initial distribution
        self._create_account("0x0000000000000000000000000000000000000003", balance=1000000)  # Team
        
        # Set miner address
        self.miner_address = "0x0000000000000000000000000000000000000001"
        
        logger.info(f"Genesis block created: {genesis_block.block_hash}")
        logger.info(f"Genesis accounts created: {len(self.accounts)}")
    
    def _build_consensus_prompt(self) -> str:
        """Build proprietary prompt for consensus decision making"""
        return """You are the consensus algorithm for Overmanifold Protocol. Make decisions about block production and transaction ordering.

CONSENSUS RULES:
1. BLOCK_VALID: Block must be valid and properly formed
2. TRANSACTIONS_VALID: All transactions must be valid
3. STATE_CONSISTENT: State transitions must be consistent
4. ECONOMIC_SOUND: Transactions must be economically sound
5. SECURITY_SAFE: No malicious or unsafe transactions
6. ORDERING: Transactions should be ordered by fee and time
7. REWARD_FAIR: Block rewards should be fair to validators
8. FINALITY: Achieve reasonable finality within acceptable time

DECISION FORMAT:
Return JSON with this exact structure:
{
  "should_produce_block": true|false,
    "confidence": 0.0-1.0,
    "block_size": 0,
    "transaction_count": 0,
    "selected_transactions": ["tx1", "tx2"],
    "block_reward": 0,
    "reasoning": "explain consensus decision",
    "estimated_gas": 0,
    "estimated_time": 0
}

Consider block size, transaction fees, economic impact, and network security when making decisions."""

    def _create_account(self, address: str = None, balance: float = 0.0) -> Account:
        """Create a new account"""
        if not address:
            account = Account()
            address = account.address
        else:
            account = Account(address=address, balance=balance)
        
        self.accounts[address] = account
        return account
    
    def get_balance(self, address: str) -> float:
        """Get account balance"""
        if address in self.accounts:
            return self.accounts[address].balance
        return 0.0
    
    def get_account(self, address: str) -> Optional[Account]:
        """Get account by address"""
        return self.accounts.get(address)
    
    def create_transaction(
        self,
        from_address: str,
        to_address: str,
        amount: float,
        transaction_type: TransactionType,
        data: str = ""
    ) -> Transaction:
        """Create a new transaction"""
        
        # Get sender account
        sender = self.get_account(from_address)
        if not sender:
            sender = self._create_account(from_address)
        
        # Get recipient account
        recipient = self.get_account(to_address)
        if not recipient:
            recipient = self._create_account(to_address)
        
        # Create transaction
        transaction = Transaction(
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            transaction_type=transaction_type,
            data=data,
            gas_limit=21000,
            gas_price=0.00001
        )
        
        return transaction
    
    def submit_transaction(self, transaction: Transaction) -> str:
        """Submit transaction to pending pool"""
        self.transactions[transaction.tx_id] = transaction
        self.pending_transactions.append(transaction.tx_id)
        
        logger.info(f"Transaction submitted: {transaction.tx_id} "
                   f"({transaction.transaction_type.value} from {transaction.from_address} to {transaction.to_address})")
        
        return transaction.tx_id
    
    async def validate_and_execute_transaction(self, tx_id: str) -> Dict[str, Any]:
        """Validate and execute transaction using LLM"""
        if tx_id not in self.transactions:
            return {
                "success": False,
                "error": "Transaction not found"
            }
        
        transaction = self.transactions[tx_id]
        sender = self.get_account(transaction.from_address)
        
        if not sender:
            return {
                "success": False,
                "error": "Sender account not found"
            }
        
        # Validate transaction using LLM
        validation = await self.validator.validate_transaction(transaction, sender.balance, sender.nonce)
        
        if not validation["is_valid"]:
            transaction.status = TransactionStatus.FAILED
            return {
                "success": False,
                "error": "Transaction validation failed",
                "validation": validation
            }
        
        # Execute transaction
        try:
            # Update balances
            sender.balance -= transaction.amount
            sender.nonce += 1
            
            recipient = self.get_account(transaction.to_address)
            recipient.balance += transaction.amount
            
            transaction.status = TransactionStatus.EXECUTED
            transaction.gas_used = validation.get("gas_estimate", 21000)
            
            # Calculate transaction cost
            tx_cost = transaction.gas_used * transaction.gas_price
            sender.balance -= tx_cost
            
            # Remove from pending
            if tx_id in self.pending_transactions:
                self.pending_transactions.remove(tx_id)
            
            logger.info(f"Transaction executed: {tx_id} (cost: {tx_cost})")
            
            return {
                "success": True,
                "tx_id": tx_id,
                "validation": validation,
                "gas_used": transaction.gas_used,
                "tx_cost": tx_cost,
                "new_sender_balance": sender.balance,
                "new_recipient_balance": recipient.balance
            }
            
        except Exception as e:
            logger.error(f"Transaction execution failed: {e}")
            transaction.status = TransactionStatus.FAILED
            return {
                "success": False,
                "error": str(e)
            }
    
    async def produce_block(self, validator_address: str = None) -> Block:
        """Produce a new block using LLM consensus"""
        
        validator = validator_address or self.miner_address
        
        if not self.pending_transactions:
            # Create empty block
            last_block = self.blocks[self.block_number - 1]
            
            new_block = Block(
                block_number=self.block_number,
                timestamp=datetime.utcnow(),
                transactions=[],
                parent_hash=last_block.block_hash,
                validator=validator
            )
            
            self.blocks[self.block_number] = new_block
            self.block_number += 1
            
            return new_block
        
        # Use LLM to decide which transactions to include
        if self.openai_api_key:
            selected_transactions = await self._select_transactions_with_llm()
        else:
            # Fallback to simple fee-based ordering
            selected_transactions = self._select_transactions_fallback()
        
        # Calculate block reward
        block_reward = self._calculate_block_reward()
        
        # Create block
        last_block = self.blocks[self.block_number - 1]
        
        new_block = Block(
            block_number=self.block_number,
            timestamp=datetime.utcnow(),
            transactions=selected_transactions,
            parent_hash=last_block.block_hash,
            validator=validator,
            gas_limit=sum(self.transactions[tx_id].gas_limit for tx_id in selected_transactions),
            gas_used=sum(self.transactions[tx_id].gas_used for tx_id in selected_transactions)
        )
        
        # Execute transactions
        for tx_id in selected_transactions:
            await self.validate_and_execute_transaction(tx_id)
        
        self.blocks[self.block_number] = new_block
        self.block_number += 1
        
        # Reward validator
        validator_account = self.get_account(validator)
        if validator_account:
            validator_account.balance += block_reward
        
        logger.info(f"Block {new_block.block_number} produced with {len(selected_transactions)} transactions")
        
        return new_block
    
    async def _select_transactions_with_llm(self) -> List[str]:
        """Use LLM to select optimal transactions for block"""
        try:
            # Prepare transaction data for LLM
            pending_txs_data = []
            for tx_id in self.pending_transactions[:100]:  # Limit to 100 for LLM efficiency
                tx = self.transactions[tx_id]
                pending_txs_data.append({
                    "tx_id": tx_id,
                    "from": tx.from_address,
                    "to": tx.to_address,
                    "amount": tx.amount,
                    "type": tx.transaction_type.value,
                    "gas_limit": tx.gas_limit,
                    "gas_price": tx.gas_price,
                    "timestamp": tx.timestamp.isoformat()
                })
            
            decision_prompt = f"{self.consensus_prompt}\n\nPending Transactions: {json.dumps(pending_txs_data, indent=2)}"
            
            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.consensus_prompt},
                    {"role": "user", "content": decision_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            decision = json.loads(response.choices[0].message.content)
            
            if decision["should_produce_block"]:
                return decision.get("selected_transactions", [])[:10]  # Limit to 10 transactions per block
            else:
                return []
            
        except Exception as e:
            logger.error(f"LLM transaction selection failed: {e}, using fallback")
            return self._select_transactions_fallback()
    
    def _select_transactions_fallback(self) -> List[str]:
        """Fallback transaction selection (simple fee-based)"""
        # Sort by gas price (higher fees first)
        sorted_txs = sorted(
            self.pending_transactions,
            key=lambda tx_id: self.transactions[tx_id].gas_price,
            reverse=True
        )
        
        # Take top 10 transactions
        return [tx.tx_id for tx in sorted_txs[:10]]
    
    def _calculate_block_reward(self) -> float:
        """Calculate block reward"""
        # Base reward + transaction fees
        base_reward = 2.0  # Base block reward
        total_gas_fees = sum(
            self.transactions[tx_id].gas_used * self.transactions[tx_id].gas_price
            for tx_id in self.pending_transactions
        )
        
        return base_reward + total_gas_fees
    
    async def get_transaction_status(self, tx_id: str) -> Dict[str, Any]:
        """Get transaction status"""
        if tx_id not in self.transactions:
            return {
                "tx_id": tx_id,
                "status": "not_found"
            }
        
        transaction = self.transactions[tx_id]
        
        return {
            "tx_id": tx_id,
            "status": transaction.status.value,
            "block_number": transaction.block_number,
            "confirmations": self._calculate_confirmations(transaction),
            "gas_used": transaction.gas_used,
            "gas_cost": transaction.gas_used * transaction.gas_price,
            "timestamp": transaction.timestamp.isoformat()
        }
    
    def _calculate_confirmations(self, transaction: Transaction) -> int:
        """Calculate number of confirmations"""
        if transaction.block_number == 0:
            return 0
        
        return self.block_number - transaction.block_number
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        total_transactions = len(self.transactions)
        total_accounts = len(self.accounts)
        total_supply = sum(acc.balance for acc in self.accounts.values())
        latest_block = self.blocks.get(self.block_number - 1)
        
        return {
            "chain_id": self.chain_id,
            "block_number": self.block_number,
            "total_transactions": total_transactions,
            "pending_transactions": len(self.pending_transactions),
            "total_accounts": total_accounts,
            "total_supply": total_supply,
            "latest_block_hash": latest_block.block_hash if latest_block else None,
            "difficulty": self.difficulty,
            "block_time": self.block_time
        }
    
    async def start_mining(self):
        """Start block production loop"""
        self.is_running = True
        logger.info("Mining started")
        
        while self.is_running:
            try:
                # Wait for block time
                await asyncio.sleep(self.block_time)
                
                # Produce block
                await self.produce_block()
                
                # Log chain stats
                stats = self.get_chain_stats()
                logger.info(f"Block {stats['block_number']} produced - "
                           f"Transactions: {stats['total_transactions']}, "
                           f"Supply: {stats['total_supply']}")
                
            except Exception as e:
                logger.error(f"Mining error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def stop_mining(self):
        """Stop block production"""
        self.is_running = False
        logger.info("Mining stopped")


# Global custom blockchain instance
custom_blockchain = CustomBlockchain()