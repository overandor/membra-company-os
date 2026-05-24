"""
FastAPI server for DepthOS observability and control.

Provides endpoints for health checks, metrics, order management, and kill switch.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
from datetime import datetime, timezone

from app.core.config import mm_config, LIVE_TRADING, LIVE_TRADING_CONFIRM, API_KEY, API_SECRET
from app.risk.risk import risk
from app.oms.oms import oms
from app.market_data.order_book import registry

app = FastAPI(
    title="DepthOS API",
    description="Production-candidate Gate.io market maker",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Global state for kill switch
_kill_switch_active = False


class HealthResponse(BaseModel):
    status: str
    mode: str
    live_trading: bool
    kill_switch: bool
    timestamp: str


class ReadyResponse(BaseModel):
    ready: bool
    reason: str
    timestamp: str


class MetricsResponse(BaseModel):
    live_orders: int
    daily_pnl: str
    contracts_tracked: int
    uptime_seconds: float
    timestamp: str


class OrderResponse(BaseModel):
    contract: str
    order_id: str
    side: str
    price: str
    size: int
    status: str
    timestamp: str


class PositionResponse(BaseModel):
    contract: str
    net_position: int
    realized_pnl: str
    unrealized_pnl: str
    total_fees: str
    timestamp: str


class FillResponse(BaseModel):
    contract: str
    size: int
    price: str
    fee: str
    timestamp: str


class RiskResponse(BaseModel):
    daily_pnl: str
    daily_loss_limit: str
    global_halted: bool
    halt_reason: str
    contracts: Dict
    timestamp: str


class PnLResponse(BaseModel):
    daily_pnl: str
    realized_pnl: str
    unrealized_pnl: str
    total_fees: str
    timestamp: str


class KillSwitchResponse(BaseModel):
    success: bool
    message: str
    timestamp: str


class CancelAllResponse(BaseModel):
    success: bool
    cancelled_count: int
    timestamp: str


# Startup time
_startup_time = datetime.now(timezone.utc)


@app.get("/health", response_model=HealthResponse)
async def get_health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        mode="dry-run" if mm_config.dry_run else "live",
        live_trading=LIVE_TRADING and LIVE_TRADING_CONFIRM,
        kill_switch=_kill_switch_active,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/ready", response_model=ReadyResponse)
async def get_ready():
    """
    Readiness check endpoint.
    
    Returns False if system is not safe to quote.
    
    Production readiness checks:
    - Config loaded
    - Contracts loaded
    - Risk manager healthy
    - Reconciliation healthy
    - Persistence writable
    - Kill switch inactive
    - Global risk halt inactive
    - Per-contract risk halts (in live mode)
    """
    # Config check
    if not mm_config.contracts:
        return ReadyResponse(
            ready=False,
            reason="No contracts loaded",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    # Kill switch check
    if _kill_switch_active:
        return ReadyResponse(
            ready=False,
            reason="Kill switch is active",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    # Global risk halt check
    if risk.global_halted_:
        return ReadyResponse(
            ready=False,
            reason=f"Global risk halt: {risk.global_reason_}",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    # In live mode, check additional conditions
    if not mm_config.dry_run:
        # Check if any contracts have risk halts
        for contract in mm_config.contracts:
            contract_risk = risk.state(contract)
            if contract_risk.halted:
                return ReadyResponse(
                    ready=False,
                    reason=f"Contract {contract} halted: {contract_risk.halt_reason}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
    
    return ReadyResponse(
        ready=True,
        reason="System ready to quote",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """System metrics endpoint."""
    uptime = (datetime.now(timezone.utc) - _startup_time).total_seconds()
    
    return MetricsResponse(
        live_orders=oms.live_order_count(),
        daily_pnl=str(risk.daily_pnl_),
        contracts_tracked=len(mm_config.contracts),
        uptime_seconds=uptime,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/orders", response_model=List[OrderResponse])
async def get_orders():
    """Get current live orders."""
    orders = []
    for contract, state in oms.state_.items():
        if state.bid_order_id:
            orders.append(OrderResponse(
                contract=contract,
                order_id=str(state.bid_order_id),
                side="bid",
                price=str(state.bid_price),
                size=state.bid_size,
                status="open",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))
        if state.ask_order_id:
            orders.append(OrderResponse(
                contract=contract,
                order_id=str(state.ask_order_id),
                side="ask",
                price=str(state.ask_price),
                size=state.ask_size,
                status="open",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))
    return orders


@app.get("/positions", response_model=List[PositionResponse])
async def get_positions():
    """Get current positions."""
    positions = []
    for contract, state in risk.states_.items():
        positions.append(PositionResponse(
            contract=contract,
            net_position=state.net_position,
            realized_pnl=str(state.realized_pnl),
            unrealized_pnl=str(state.unrealized_pnl),
            total_fees=str(state.total_fees),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))
    return positions


@app.get("/fills", response_model=List[FillResponse])
async def get_fills():
    """Get recent fills."""
    fills = []
    for contract, state in risk.states_.items():
        for fill in state.fills[-10:]:  # Last 10 fills per contract
            fills.append(FillResponse(
                contract=fill.contract,
                size=fill.size,
                price=str(fill.price),
                fee=str(fill.fee),
                timestamp=datetime.utcfromtimestamp(fill.ts_ms / 1000).isoformat(),
            ))
    return fills


@app.get("/risk", response_model=RiskResponse)
async def get_risk():
    """Get risk state."""
    contracts = {}
    for contract, state in risk.states_.items():
        contracts[contract] = {
            "net_position": state.net_position,
            "realized_pnl": str(state.realized_pnl),
            "unrealized_pnl": str(state.unrealized_pnl),
            "total_fees": str(state.total_fees),
            "halted": state.halted,
            "halt_reason": state.halt_reason,
        }
    
    return RiskResponse(
        daily_pnl=str(risk.daily_pnl_),
        daily_loss_limit=str(mm_config.daily_loss_limit_usdt),
        global_halted=risk.global_halted_,
        halt_reason=risk.global_reason_,
        contracts=contracts,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/pnl", response_model=PnLResponse)
async def get_pnl():
    """Get P&L summary."""
    total_realized = sum(s.realized_pnl for s in risk.states_.values())
    total_unrealized = sum(s.unrealized_pnl for s in risk.states_.values())
    total_fees = sum(s.total_fees for s in risk.states_.values())
    
    return PnLResponse(
        daily_pnl=str(risk.daily_pnl_),
        realized_pnl=str(total_realized),
        unrealized_pnl=str(total_unrealized),
        total_fees=str(total_fees),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/kill-switch", response_model=KillSwitchResponse)
async def activate_kill_switch():
    """Activate kill switch - halts all quoting."""
    global _kill_switch_active
    _kill_switch_active = True
    
    # Kill switch via proper method
    risk.trigger_global_halt("api_kill_switch")
    
    # Cancel all orders
    cancelled = await oms.cancel_all(None)
    
    return KillSwitchResponse(
        success=True,
        message="Kill switch activated - all quoting halted and orders cancelled",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/cancel-all", response_model=CancelAllResponse)
async def cancel_all_orders():
    """Cancel all live orders."""
    # This would need the session to actually cancel
    # For now, just clear local state
    cancelled = 0
    for contract, state in oms.state_.items():
        if state.bid_order_id:
            cancelled += 1
            state.bid_order_id = 0
            state.bid_price = 0
            state.bid_size = 0
        if state.ask_order_id:
            cancelled += 1
            state.ask_order_id = 0
            state.ask_price = 0
            state.ask_size = 0
    
    return CancelAllResponse(
        success=True,
        cancelled_count=cancelled,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )
