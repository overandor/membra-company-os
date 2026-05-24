"""
Membra Phone Registration Dashboard
Web dashboard for phone wallet registration and SMS transaction monitoring.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import hashlib
import secrets
import re

from fastapi import FastAPI, HTTPException, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pathlib import Path

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.membra_integration.membra_bridge_client import MembraBridgeClient, MembraWallet, SMSMiningReward
from overmanifold.membra_integration.sms_payment_gateway import SMSPaymentGateway, SMSPaymentRequest, SMSPaymentResponse
from overmanifold.membra_integration.free_transaction_sponsor import FreeTransactionSponsor
from overmanifold.membra_integration.oracle_integration import MembraOracleIntegration, OracleEndpoint
from overmanifold.membra_integration.monitoring import sms_monitoring, TransactionLog, MetricType
from overmanifold.llm_integration import (
    LLMSMSProcessor,
    CustomSMSGateway,
    LLMCustomEmailSystem,
    CustomBlockchain,
    CustomMembraBridge,
    LLMOrchestrator
)

logger = get_logger("membra_dashboard")

app = FastAPI(title="Membra Phone Registration Dashboard", version="1.0.0")

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize clients
membra_client = MembraBridgeClient()
sms_gateway = SMSPaymentGateway(membra_client)
sponsor_system = FreeTransactionSponsor()
oracle_integration = MembraOracleIntegration()

# Monitoring system will be started on app startup
@app.on_event("startup")
async def startup_event():
    """Start monitoring system on app startup"""
    sms_monitoring.start_monitoring()
    logger.info("Dashboard startup complete - monitoring system active")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop monitoring system on app shutdown"""
    await sms_monitoring.stop_monitoring()
    logger.info("Dashboard shutdown complete - monitoring system stopped")

# In-memory storage for demo (replace with database in production)
registered_phones: Dict[str, Dict] = {}
transactions: Dict[str, Dict] = {}
verification_codes: Dict[str, str] = {}


@dataclass
class PhoneRegistration:
    """Phone registration data"""
    phone_number: str
    wallet_address: str
    public_key: str
    email: Optional[str] = None
    verification_status: str = "pending"
    registered_at: datetime = None
    balance: int = 0
    premined_tokens: int = 1000
    merkle_root: str = ""
    
    def __post_init__(self):
        if self.registered_at is None:
            self.registered_at = datetime.utcnow()
        if not self.merkle_root:
            self.merkle_root = self.generate_merkle_root()
    
    def generate_merkle_root(self) -> str:
        """Generate merkle root from phone number and public key"""
        data = f"{self.phone_number}{self.public_key}{self.registered_at.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class SMSTransaction:
    """SMS transaction data"""
    transaction_id: str
    sender_phone: str
    recipient_phone: str
    amount: int
    message: str
    status: str = "pending"
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    transaction_hash: Optional[str] = None
    mining_reward: int = 0
    sponsor_bonus: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
    
    def generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        data = f"{self.sender_phone}{self.recipient_phone}{self.amount}{self.created_at.isoformat()}{secrets.token_hex(8)}"
        return hashlib.sha256(data.encode()).hexdigest()


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Dashboard home page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": get_dashboard_stats()
    })


@app.get("/register", response_class=HTMLResponse)
async def registration_page(request: Request):
    """Phone registration page"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/api/register-phone")
async def register_phone(
    phone_number: str = Form(...),
    email: str = Form(None),
    accept_terms: bool = Form(False)
):
    """Register a new phone wallet"""
    try:
        # Validate phone number
        if not validate_phone_number(phone_number):
            raise HTTPException(status_code=400, detail="Invalid phone number format")
        
        if not accept_terms:
            raise HTTPException(status_code=400, detail="Must accept terms and conditions")
        
        # Check if phone already registered
        if phone_number in registered_phones:
            raise HTTPException(status_code=400, detail="Phone number already registered")
        
        # Generate wallet for phone
        wallet_response = membra_client.register_phone_wallet(phone_number, email)
        
        if not wallet_response.get("success"):
            raise HTTPException(status_code=500, detail="Failed to register wallet")
        
        # Create registration record
        registration = PhoneRegistration(
            phone_number=phone_number,
            wallet_address=wallet_response["wallet_address"],
            public_key=wallet_response["public_key"],
            email=email,
            verification_status="pending",
            balance=wallet_response.get("balance", 0),
            premined_tokens=wallet_response.get("premined_tokens", 1000)
        )
        
        registered_phones[phone_number] = asdict(registration)
        
        # Generate and send verification code
        verification_code = generate_verification_code()
        verification_codes[phone_number] = verification_code
        
        # In production, send SMS with verification code
        logger.info(f"Verification code for {phone_number}: {verification_code}")
        
        return {
            "success": True,
            "message": "Phone registered successfully. Please verify with the code sent via SMS.",
            "wallet_address": registration.wallet_address,
            "phone_number": phone_number
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering phone: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/verify-phone")
async def verify_phone(
    phone_number: str = Form(...),
    verification_code: str = Form(...)
):
    """Verify phone number with code"""
    try:
        if phone_number not in registered_phones:
            raise HTTPException(status_code=404, detail="Phone number not found")
        
        if phone_number not in verification_codes:
            raise HTTPException(status_code=400, detail="No verification code sent")
        
        if verification_codes[phone_number] != verification_code:
            raise HTTPException(status_code=400, detail="Invalid verification code")
        
        # Update verification status
        registered_phones[phone_number]["verification_status"] = "verified"
        del verification_codes[phone_number]
        
        return {
            "success": True,
            "message": "Phone verified successfully",
            "wallet_address": registered_phones[phone_number]["wallet_address"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying phone: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wallet/{phone_number}")
async def get_wallet_info(phone_number: str):
    """Get wallet information for phone number"""
    try:
        if phone_number not in registered_phones:
            raise HTTPException(status_code=404, detail="Phone number not registered")
        
        wallet_info = registered_phones[phone_number]
        
        # Get fresh data from membra bridge
        membra_wallet = membra_client.get_phone_wallet(phone_number)
        
        return {
            "success": True,
            "wallet": {
                **wallet_info,
                "balance": membra_wallet.get("balance", wallet_info["balance"]),
                "premined_tokens": membra_wallet.get("premined_tokens", wallet_info["premined_tokens"])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send-sms")
async def send_sms_payment(
    sender_phone: str = Form(...),
    recipient_phone: str = Form(...),
    amount: int = Form(...),
    message: str = Form(...)
):
    """Send SMS payment"""
    try:
        # Validate inputs
        if not validate_phone_number(sender_phone):
            raise HTTPException(status_code=400, detail="Invalid sender phone number")
        
        if not validate_phone_number(recipient_phone):
            raise HTTPException(status_code=400, detail="Invalid recipient phone number")
        
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        
        # Check if phones are registered
        if sender_phone not in registered_phones:
            raise HTTPException(status_code=400, detail="Sender phone not registered")
        
        if recipient_phone not in registered_phones:
            # Auto-register recipient
            wallet_response = membra_client.register_phone_wallet(recipient_phone)
            if wallet_response.get("success"):
                registration = PhoneRegistration(
                    phone_number=recipient_phone,
                    wallet_address=wallet_response["wallet_address"],
                    public_key=wallet_response["public_key"],
                    verification_status="auto_registered"
                )
                registered_phones[recipient_phone] = asdict(registration)
        
        # Create transaction record
        transaction = SMSTransaction(
            sender_phone=sender_phone,
            recipient_phone=recipient_phone,
            amount=amount,
            message=message,
            status="processing"
        )
        
        transactions[transaction.transaction_id] = asdict(transaction)
        
        # Process payment asynchronously
        asyncio.create_task(process_sms_payment(transaction.transaction_id))
        
        return {
            "success": True,
            "message": "SMS payment initiated",
            "transaction_id": transaction.transaction_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending SMS payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transaction/{transaction_id}")
async def get_transaction_status(transaction_id: str):
    """Get transaction status"""
    try:
        if transaction_id not in transactions:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return {
            "success": True,
            "transaction": transactions[transaction_id]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions")
async def list_transactions(
    phone_number: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """List transactions with optional filters"""
    try:
        filtered_transactions = list(transactions.values())
        
        if phone_number:
            filtered_transactions = [
                t for t in filtered_transactions 
                if t["sender_phone"] == phone_number or t["recipient_phone"] == phone_number
            ]
        
        if status:
            filtered_transactions = [t for t in filtered_transactions if t["status"] == status]
        
        # Sort by created_at descending
        filtered_transactions.sort(
            key=lambda x: x["created_at"], 
            reverse=True
        )
        
        return {
            "success": True,
            "transactions": filtered_transactions[:limit],
            "total": len(filtered_transactions)
        }
        
    except Exception as e:
        logger.error(f"Error listing transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_api_stats():
    """Get API statistics"""
    return get_dashboard_stats()


@app.get("/api/sponsors")
async def list_sponsors():
    """List available sponsors"""
    try:
        sponsors = sponsor_system.get_available_sponsors()
        return {
            "success": True,
            "sponsors": sponsors
        }
    except Exception as e:
        logger.error(f"Error listing sponsors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/oracle/validate-phone/{phone_number}")
async def oracle_validate_phone(phone_number: str):
    """Validate phone number via oracle"""
    try:
        response = await oracle_integration.validate_phone_number(phone_number)
        return {
            "success": response.success,
            "valid": response.data.get("valid", False) if response.data else False,
            "data": response.data,
            "error": response.error
        }
    except Exception as e:
        logger.error(f"Error validating phone via oracle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/oracle/wallet-balance/{wallet_address}")
async def oracle_wallet_balance(wallet_address: str):
    """Get wallet balance via oracle"""
    try:
        response = await oracle_integration.get_wallet_balance(wallet_address)
        return {
            "success": response.success,
            "balance": response.data.get("balance", 0) if response.data else 0,
            "data": response.data,
            "error": response.error
        }
    except Exception as e:
        logger.error(f"Error getting wallet balance via oracle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/oracle/transaction/{tx_hash}")
async def oracle_transaction_status(tx_hash: str):
    """Get transaction status via oracle"""
    try:
        response = await oracle_integration.get_transaction_status(tx_hash)
        return {
            "success": response.success,
            "status": response.data.get("status", "unknown") if response.data else "unknown",
            "data": response.data,
            "error": response.error
        }
    except Exception as e:
        logger.error(f"Error getting transaction status via oracle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/oracle/network-status")
async def oracle_network_status():
    """Get network status via oracle"""
    try:
        response = await oracle_integration.get_network_status()
        return {
            "success": response.success,
            "status": response.data,
            "error": response.error
        }
    except Exception as e:
        logger.error(f"Error getting network status via oracle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/oracle/token-prices")
async def oracle_token_prices(tokens: str = None):
    """Get token prices via oracle"""
    try:
        token_list = tokens.split(",") if tokens else None
        response = await oracle_integration.get_token_prices(token_list)
        return {
            "success": response.success,
            "prices": response.data,
            "error": response.error
        }
    except Exception as e:
        logger.error(f"Error getting token prices via oracle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/oracle/cache-stats")
async def oracle_cache_stats():
    """Get oracle cache statistics"""
    try:
        stats = oracle_integration.get_cache_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting oracle cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/oracle/cache-clear")
async def oracle_cache_clear(endpoint: str = None):
    """Clear oracle cache"""
    try:
        oracle_endpoint = OracleEndpoint(endpoint) if endpoint else None
        oracle_integration.clear_cache(oracle_endpoint)
        return {
            "success": True,
            "message": f"Cache cleared for {'all' if not endpoint else endpoint}"
        }
    except Exception as e:
        logger.error(f"Error clearing oracle cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/metrics")
async def get_monitoring_metrics():
    """Get monitoring metrics summary"""
    try:
        summary = sms_monitoring.get_metrics_summary()
        return {
            "success": True,
            "metrics": summary
        }
    except Exception as e:
        logger.error(f"Error getting monitoring metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/alerts")
async def get_monitoring_alerts(limit: int = 100):
    """Get monitoring alerts"""
    try:
        alerts = sms_monitoring.get_recent_alerts(limit)
        return {
            "success": True,
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error getting monitoring alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/transaction-logs")
async def get_transaction_logs(phone_number: str = None, status: str = None, limit: int = 100):
    """Get transaction logs with optional filters"""
    try:
        logs = sms_monitoring.get_transaction_logs(phone_number, status, limit)
        return {
            "success": True,
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Error getting transaction logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/metrics/export")
async def export_metrics(format: str = "prometheus"):
    """Export metrics in specified format"""
    try:
        metrics = sms_monitoring.export_metrics(format)
        return Response(
            content=metrics,
            media_type="text/plain" if format == "prometheus" else "application/json"
        )
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitoring/metrics/record")
async def record_metric(
    name: str = Form(...),
    value: float = Form(...),
    metric_type: str = Form("gauge")
):
    """Record a custom metric"""
    try:
        metric_type_enum = MetricType(metric_type)
        sms_monitoring.record_metric(name, value, metric_type_enum)
        return {
            "success": True,
            "message": f"Metric {name} recorded with value {value}"
        }
    except Exception as e:
        logger.error(f"Error recording metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_sms_payment(transaction_id: str):
    """Process SMS payment asynchronously"""
    start_time = datetime.utcnow()
    processing_steps = []
    
    try:
        transaction = transactions[transaction_id]
        
        # Update status to processing
        transaction["status"] = "processing"
        processing_steps.append({"step": "processing_started", "status": "success", "timestamp": datetime.utcnow().isoformat()})
        
        # Record monitoring metric
        sms_monitoring.increment_counter("sms_payments_initiated")
        
        # Create payment request
        payment_request = SMSPaymentRequest(
            sender_phone=transaction["sender_phone"],
            recipient_phone=transaction["recipient_phone"],
            amount=transaction["amount"],
            message=transaction["message"]
        )
        
        processing_steps.append({"step": "payment_request_created", "status": "success", "timestamp": datetime.utcnow().isoformat()})
        
        # Process payment through SMS gateway
        response = await sms_gateway.process_payment(payment_request)
        
        processing_steps.append({"step": "payment_processed", "status": "success", "timestamp": datetime.utcnow().isoformat()})
        
        # Update transaction with response
        transaction["status"] = "completed" if response.success else "failed"
        transaction["completed_at"] = datetime.utcnow().isoformat()
        transaction["transaction_hash"] = response.transaction_hash
        transaction["mining_reward"] = response.mining_reward
        transaction["sponsor_bonus"] = response.sponsor_bonus
        
        # Calculate processing time
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create transaction log
        transaction_log = TransactionLog(
            transaction_id=transaction_id,
            phone_number=transaction["sender_phone"],
            transaction_type="sms_payment",
            amount=transaction["amount"],
            status=transaction["status"],
            processing_time_ms=processing_time_ms,
            error_message="",
            steps=processing_steps
        )
        
        # Log transaction to monitoring system
        sms_monitoring.log_transaction(transaction_log)
        
        # Record processing time metric
        sms_monitoring.set_gauge("sms_payment_processing_time_ms", processing_time_ms)
        
        logger.info(f"Transaction {transaction_id} completed: {transaction['status']} in {processing_time_ms:.2f}ms")
        
    except Exception as e:
        logger.error(f"Error processing transaction {transaction_id}: {e}")
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        if transaction_id in transactions:
            transactions[transaction_id]["status"] = "failed"
            transactions[transaction_id]["completed_at"] = datetime.utcnow().isoformat()
        
        # Create failed transaction log
        transaction_log = TransactionLog(
            transaction_id=transaction_id,
            phone_number=transaction.get("sender_phone", "unknown"),
            transaction_type="sms_payment",
            amount=transaction.get("amount", 0),
            status="failed",
            processing_time_ms=processing_time_ms,
            error_message=str(e),
            steps=processing_steps
        )
        
        # Log failed transaction
        sms_monitoring.log_transaction(transaction_log)
        
        # Record error metric
        sms_monitoring.increment_counter("sms_payment_errors")


def validate_phone_number(phone_number: str) -> bool:
    """Validate phone number format"""
    # Remove all non-numeric characters
    cleaned = re.sub(r'[^\d+]', '', phone_number)
    
    # Check if it starts with + and has 10-15 digits
    pattern = r'^\+[1-9]\d{9,14}$'
    return bool(re.match(pattern, cleaned))


def generate_verification_code() -> str:
    """Generate 6-digit verification code"""
    return str(secrets.randbelow(900000) + 100000)


def get_dashboard_stats() -> Dict[str, Any]:
    """Get dashboard statistics"""
    total_phones = len(registered_phones)
    verified_phones = len([p for p in registered_phones.values() if p["verification_status"] == "verified"])
    
    total_transactions = len(transactions)
    completed_transactions = len([t for t in transactions.values() if t["status"] == "completed"])
    pending_transactions = len([t for t in transactions.values() if t["status"] == "pending"])
    
    total_volume = sum(t["amount"] for t in transactions.values() if t["status"] == "completed")
    
    sponsors = sponsor_system.get_available_sponsors()
    total_sponsor_budget = sum(s.get("remaining_budget", 0) for s in sponsors)
    
    return {
        "total_registered_phones": total_phones,
        "verified_phones": verified_phones,
        "total_transactions": total_transactions,
        "completed_transactions": completed_transactions,
        "pending_transactions": pending_transactions,
        "total_transaction_volume": total_volume,
        "available_sponsors": len(sponsors),
        "total_sponsor_budget": total_sponsor_budget,
        "system_status": "operational"
    }


def start_dashboard(host: str = "0.0.0.0", port: int = 8000):
    """Start the dashboard server"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_dashboard()