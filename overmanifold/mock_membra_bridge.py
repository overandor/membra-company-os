#!/usr/bin/env python3
"""
Mock Membra Bridge Server
Provides mock responses without requiring real Membra bridge API keys
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import random
import hashlib
from datetime import datetime
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Membra Bridge")

# In-memory storage
mock_wallets: Dict[str, Dict] = {}
mock_transactions: Dict[str, Dict] = {}
mock_rewards: Dict[str, list] = {}

def generate_wallet_address(phone: str) -> str:
    """Generate mock wallet address from phone number"""
    hash_input = f"membra_{phone}_{datetime.utcnow().isoformat()}"
    return "0x" + hashlib.sha256(hash_input.encode()).hexdigest()[:40]

def generate_transaction_id() -> str:
    """Generate mock transaction ID"""
    return "0x" + hashlib.sha256(str(random.random()).encode()).hexdigest()[:64]

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Mock Membra Bridge",
        "status": "running",
        "mode": "mock",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/oracle/phone_validation")
async def validate_phone(phone: str) -> Dict[str, Any]:
    """Mock phone validation"""
    is_valid = len(phone) >= 10 and phone.startswith("+")
    
    return {
        "valid": is_valid,
        "phone": phone,
        "country": "US",
        "carrier": "Mock Carrier",
        "type": "mobile"
    }

@app.get("/oracle/wallet_balance")
async def get_wallet_balance(address: str) -> Dict[str, Any]:
    """Mock wallet balance"""
    return {
        "address": address,
        "balance": random.randint(1000, 10000),
        "premined_tokens": 1000,
        "currency": "USDC",
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/oracle/transaction/{tx_hash}")
async def get_transaction_status(tx_hash: str) -> Dict[str, Any]:
    """Mock transaction status"""
    statuses = ["pending", "confirmed", "completed"]
    
    return {
        "tx_hash": tx_hash,
        "status": random.choice(statuses),
        "confirmations": random.randint(1, 100),
        "block_height": random.randint(1000000, 2000000),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/oracle/network_status")
async def network_status() -> Dict[str, Any]:
    """Mock network status"""
    return {
        "status": "healthy",
        "block_height": random.randint(1000000, 2000000),
        "tps": random.randint(100, 1000),
        "active_validators": random.randint(10, 100),
        "total_supply": random.randint(1000000, 10000000),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/oracle/token_prices")
async def get_token_prices(tokens: str = None) -> Dict[str, Any]:
    """Mock token prices"""
    token_list = tokens.split(",") if tokens else ["USDC", "ETH", "BTC"]
    
    prices = {}
    for token in token_list:
        prices[token] = {
            "price": random.uniform(0.5, 50000),
            "change_24h": random.uniform(-10, 10),
            "volume_24h": random.randint(1000000, 100000000)
        }
    
    return {
        "prices": prices,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/register_phone_wallet")
async def register_wallet(phone: str, email: str = None) -> Dict[str, Any]:
    """Mock phone wallet registration"""
    wallet_address = generate_wallet_address(phone)
    public_key = "0x" + hashlib.sha256(phone.encode()).hexdigest()[:40]
    
    mock_wallets[phone] = {
        "phone_number": phone,
        "wallet_address": wallet_address,
        "public_key": public_key,
        "balance": 1000,
        "premined_tokens": 1000,
        "merkle_root": hashlib.sha256(wallet_address.encode()).hexdigest(),
        "is_active": True,
        "email": email,
        "registered_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Registered wallet for {phone}: {wallet_address}")
    
    return {
        "success": True,
        "wallet_address": wallet_address,
        "public_key": public_key,
        "balance": 1000,
        "premined_tokens": 1000
    }

@app.get("/phone_wallet/{phone}")
async def get_phone_wallet(phone: str) -> Dict[str, Any]:
    """Get phone wallet information"""
    if phone in mock_wallets:
        return mock_wallets[phone]
    else:
        # Auto-register
        logger.info(f"Auto-registering wallet for {phone}")
        return await register_wallet(phone)

@app.get("/sms_mining_rewards/{phone}")
async def get_mining_rewards(phone: str) -> Dict[str, Any]:
    """Get SMS mining rewards for phone number"""
    if phone not in mock_rewards:
        mock_rewards[phone] = []
    
    # Generate some mock rewards
    for _ in range(3):
        reward = {
            "phone_number": phone,
            "sms_type": random.choice(["sent", "received"]),
            "reward_amount": random.randint(1, 10),
            "timestamp": datetime.utcnow().isoformat(),
            "transaction_hash": generate_transaction_id()
        }
        mock_rewards[phone].append(reward)
    
    return {
        "phone_number": phone,
        "rewards": mock_rewards[phone],
        "total_rewards": sum(r["reward_amount"] for r in mock_rewards[phone])
    }

@app.post("/process_sms_payment")
async def process_sms_payment(
    sender_phone: str,
    recipient_phone: str,
    amount: int,
    message: str
) -> Dict[str, Any]:
    """Process SMS payment"""
    tx_id = generate_transaction_id()
    
    # Ensure wallets exist
    await get_phone_wallet(sender_phone)
    await get_phone_wallet(recipient_phone)
    
    transaction = {
        "transaction_id": tx_id,
        "sender_phone": sender_phone,
        "recipient_phone": recipient_phone,
        "amount": amount,
        "message": message,
        "status": "completed",
        "transaction_hash": tx_id,
        "timestamp": datetime.utcnow().isoformat(),
        "mining_reward": random.randint(1, 5),
        "sponsor_bonus": random.randint(1, 10)
    }
    
    mock_transactions[tx_id] = transaction
    
    logger.info(f"Processed SMS payment: {tx_id} - {sender_phone} -> {recipient_phone}: {amount}")
    
    return {
        "success": True,
        "transaction_id": tx_id,
        "status": "completed",
        "transaction_hash": tx_id,
        "amount": amount,
        "mining_reward": transaction["mining_reward"],
        "sponsor_bonus": transaction["sponsor_bonus"]
    }

@app.get("/transaction/{tx_id}")
async def get_transaction(tx_id: str) -> Dict[str, Any]:
    """Get transaction by ID"""
    if tx_id in mock_transactions:
        return mock_transactions[tx_id]
    else:
        return {
            "error": "Transaction not found",
            "transaction_id": tx_id
        }

@app.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get mock bridge statistics"""
    return {
        "total_wallets": len(mock_wallets),
        "total_transactions": len(mock_transactions),
        "total_rewards": sum(len(rewards) for rewards in mock_rewards.values()),
        "active_sponsors": 1,
        "total_sponsor_budget": 1000000,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Mock Membra Bridge Server on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)