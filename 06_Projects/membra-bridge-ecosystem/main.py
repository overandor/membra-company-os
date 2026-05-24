"""
Main API Server for MEMBRA Bridge Ecosystem
FastAPI server that integrates all components and provides REST API endpoints.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime
import os
from contextlib import asynccontextmanager

# Import membra_bridge components
from membra_bridge import (
    FileTokenizer, IPFSManager, PhoneWalletMapper, SMSMiningEngine,
    OracleSystem, AdvancedKPITracker, ArbitrageEngine,
    DeviceProfiler, ZKProofGenerator, ZKProofVerifier, ValidatorNetwork,
    LLMValidatorNetwork, LLMOracle,
    LiquidityPoolManager, CrossChainBridge, ArbitrageEngine as LiquidityArbitrageEngine,
    AutomatedMarketMaker, LiquidityLayerCoordinator
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
file_tokenizer: Optional[FileTokenizer] = None
ipfs_manager: Optional[IPFSManager] = None
phone_wallet_mapper: Optional[PhoneWalletMapper] = None
sms_mining_engine: Optional[SMSMiningEngine] = None
oracle_system: Optional[OracleSystem] = None
kpi_tracker: Optional[AdvancedKPITracker] = None
arbitrage_engine: Optional[ArbitrageEngine] = None
zk_coordinator: Optional[ValidatorNetwork] = None
llm_validator_network: Optional[LLMValidatorNetwork] = None
llm_oracle: Optional[LLMOracle] = None
liquidity_coordinator: Optional[LiquidityLayerCoordinator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting MEMBRA Bridge Ecosystem...")
    
    global file_tokenizer, ipfs_manager, phone_wallet_mapper, sms_mining_engine
    global oracle_system, kpi_tracker, arbitrage_engine
    global zk_coordinator, llm_validator_network, llm_oracle, liquidity_coordinator
    
    # Initialize components
    try:
        # File Tokenizer
        file_tokenizer = FileTokenizer("/app/data")
        
        # IPFS Manager
        ipfs_manager = IPFSManager()
        
        # Phone Wallet System
        phone_wallet_mapper = PhoneWalletMapper()
        sms_mining_engine = SMSMiningEngine(phone_wallet_mapper)
        
        # Oracle System
        oracle_system = OracleSystem()
        await oracle_system.__aenter__()
        
        # KPI Tracker
        kpi_tracker = AdvancedKPITracker()
        arbitrage_engine = ArbitrageEngine(kpi_tracker)
        
        # ZK Verifier
        zk_coordinator = ValidatorNetwork()
        
        # LLM Validator
        llm_validator_network = LLMValidatorNetwork()
        llm_oracle = LLMOracle(llm_validator_network)
        
        # Liquidity Layer
        liquidity_coordinator = LiquidityLayerCoordinator()
        liquidity_coordinator.initialize_default_pools()
        
        logger.info("All components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down MEMBRA Bridge Ecosystem...")
    if oracle_system:
        await oracle_system.__aexit__(None, None, None)
    logger.info("Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="MEMBRA Bridge Ecosystem API",
    description="Comprehensive Solana bridging system with hierarchical merkle root taxonomy",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class TokenizeRequest(BaseModel):
    path: str
    pattern: str = "*"


class PhoneRegisterRequest(BaseModel):
    phone_number: str
    custom_premined: Optional[int] = None


class SMSMiningRequest(BaseModel):
    phone_number: str
    sms_type: str  # 'sent' or 'received'
    content: str
    sponsor_address: Optional[str] = None


class InferenceRequest(BaseModel):
    prompt: str
    model_id: str = "mock-gpt"
    temperature: float = 0.7
    max_tokens: int = 500


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "file_tokenizer": file_tokenizer is not None,
            "ipfs_manager": ipfs_manager is not None,
            "phone_wallet_mapper": phone_wallet_mapper is not None,
            "oracle_system": oracle_system is not None,
            "kpi_tracker": kpi_tracker is not None,
            "llm_validator_network": llm_validator_network is not None,
            "liquidity_coordinator": liquidity_coordinator is not None
        }
    }


# File Tokenization endpoints
@app.post("/api/tokenize")
async def tokenize_files(request: TokenizeRequest, background_tasks: BackgroundTasks):
    """Tokenize files in a directory"""
    try:
        tokenizer = FileTokenizer(request.path)
        result = await tokenizer.scan_and_tokenize_async()
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Tokenization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/merkle/{root_hash}")
async def get_merkle_tree(root_hash: str):
    """Get merkle tree by root hash"""
    # This would query the database for stored merkle trees
    return {"root_hash": root_hash, "message": "Merkle tree retrieval endpoint"}


# Phone Wallet endpoints
@app.post("/api/wallet/register")
async def register_phone_wallet(request: PhoneRegisterRequest):
    """Register phone number as wallet"""
    try:
        wallet = phone_wallet_mapper.register_phone(
            request.phone_number,
            request.custom_premined
        )
        return {"success": True, "data": wallet.to_dict()}
    except Exception as e:
        logger.error(f"Wallet registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wallet/{phone_number}")
async def get_wallet(phone_number: str):
    """Get wallet by phone number"""
    wallet = phone_wallet_mapper.get_wallet(phone_number)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return {"success": True, "data": wallet.to_dict()}


# SMS Mining endpoints
@app.post("/api/sms/process")
async def process_sms(request: SMSMiningRequest):
    """Process SMS for mining rewards"""
    try:
        reward = sms_mining_engine.process_sms(
            request.phone_number,
            request.sms_type,
            request.content,
            request.sponsor_address
        )
        if reward:
            return {"success": True, "data": reward.to_dict()}
        else:
            raise HTTPException(status_code=400, detail="SMS processing failed")
    except Exception as e:
        logger.error(f"SMS processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Oracle endpoints
@app.get("/api/oracle/prices")
async def get_oracle_prices():
    """Get prices from oracle system"""
    try:
        prices = await oracle_system.fetch_all_endpoints()
        return {"success": True, "data": [dp.to_dict() for dp in prices]}
    except Exception as e:
        logger.error(f"Oracle price fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/oracle/kpi")
async def get_kpi_signals():
    """Get KPI signals from tracker"""
    try:
        signals = kpi_tracker.calculate_composite_signal()
        return {"success": True, "data": signals}
    except Exception as e:
        logger.error(f"KPI signal generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# LLM Validator endpoints
@app.post("/api/llm/inference")
async def submit_inference(request: InferenceRequest):
    """Submit LLM inference request"""
    try:
        response = await llm_validator_network.submit_inference_request(
            prompt=request.prompt,
            model_id=request.model_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return {"success": True, "data": response.to_dict()}
    except Exception as e:
        logger.error(f"LLM inference failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/llm/oracle/predict")
async def get_price_prediction(asset: str):
    """Get LLM-based price prediction"""
    try:
        prediction = await llm_oracle.get_price_prediction(asset, {})
        return {"success": True, "data": prediction}
    except Exception as e:
        logger.error(f"Price prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Liquidity Layer endpoints
@app.get("/api/liquidity/pools")
async def get_liquidity_pools():
    """Get all liquidity pools"""
    if not liquidity_coordinator:
        raise HTTPException(status_code=503, detail="Liquidity coordinator not initialized")
    
    pools = {
        pool_id: pool.to_dict()
        for pool_id, pool in liquidity_coordinator.pool_manager.pools.items()
    }
    return {"success": True, "data": pools}


@app.get("/api/liquidity/arbitrage")
async def get_arbitrage_opportunities():
    """Get current arbitrage opportunities"""
    if not liquidity_coordinator:
        raise HTTPException(status_code=503, detail="Liquidity coordinator not initialized")
    
    opportunities = liquidity_coordinator.arbitrage_engine.scan_cross_chain_arbitrage()
    return {
        "success": True,
        "data": [opp.to_dict() for opp in opportunities]
    }


# System status endpoint
@app.get("/api/status")
async def get_system_status():
    """Get comprehensive system status"""
    return {
        "timestamp": datetime.now().isoformat(),
        "components": {
            "file_tokenization": {
                "status": "active" if file_tokenizer else "inactive",
                "files_processed": len(file_tokenizer.file_metadata) if file_tokenizer else 0
            },
            "phone_wallets": {
                "status": "active" if phone_wallet_mapper else "inactive",
                "registered_wallets": len(phone_wallet_mapper.wallets) if phone_wallet_mapper else 0
            },
            "oracle_system": {
                "status": "active" if oracle_system else "inactive",
                "endpoints_configured": len(oracle_system.endpoints) if oracle_system else 0
            },
            "llm_validators": {
                "status": "active" if llm_validator_network else "inactive",
                "active_validators": len(llm_validator_network.validators) if llm_validator_network else 0
            },
            "liquidity_layer": {
                "status": "active" if liquidity_coordinator else "inactive",
                "total_pools": len(liquidity_coordinator.pool_manager.pools) if liquidity_coordinator else 0
            }
        }
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "MEMBRA Bridge Ecosystem",
        "version": "0.1.0",
        "description": "Comprehensive Solana bridging system with hierarchical merkle root taxonomy",
        "endpoints": {
            "health": "/health",
            "tokenize": "/api/tokenize",
            "wallet": "/api/wallet/{phone_number}",
            "sms": "/api/sms/process",
            "oracle": "/api/oracle/prices",
            "kpi": "/api/oracle/kpi",
            "llm": "/api/llm/inference",
            "liquidity": "/api/liquidity/pools",
            "status": "/api/status"
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)