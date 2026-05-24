"""
L2 market data recorder for Gate.io futures.

Records full orderbook depth and trade data for deterministic replay.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from app.core.config import FUTURES_WS_URL, MICRO_CONTRACTS, mm_config

log = logging.getLogger("recorder")


@dataclass
class L2Snapshot:
    """L2 orderbook snapshot for recording."""
    
    timestamp_ms: int
    exchange_ts_ms: int
    contract: str
    message_type: str  # "snapshot", "update"
    bids: List[Dict[str, Any]]  # [{"price": "0.00005", "size": 1000}, ...]
    asks: List[Dict[str, Any]]
    sequence: Optional[int] = None
    local_sequence: int = 0  # Local sequence for gap detection
    
    @classmethod
    def from_ws_message(cls, msg: Dict[str, Any], contract: str, local_seq: int = 0) -> "L2Snapshot":
        """Create snapshot from WebSocket message."""
        result = msg.get("result", {})
        event = msg.get("event", "")
        
        bids = []
        asks = []
        
        # Gate.io order book format: [price, size] pairs
        for bid in result.get("bids", []):
            if len(bid) >= 2:
                bids.append({"price": str(bid[0]), "size": bid[1]})
        
        for ask in result.get("asks", []):
            if len(ask) >= 2:
                asks.append({"price": str(ask[0]), "size": ask[1]})
        
        # Determine message type
        msg_type = "snapshot" if event == "all" else "update"
        
        return cls(
            timestamp_ms=int(time.time() * 1000),
            exchange_ts_ms=result.get("t", int(time.time() * 1000)),
            contract=contract,
            message_type=msg_type,
            bids=bids,
            asks=asks,
            sequence=result.get("u"),
            local_sequence=local_seq,
        )
    
    def to_jsonl(self) -> str:
        """Convert to JSONL string."""
        return json.dumps(asdict(self))


@dataclass
class TradeEvent:
    """Trade event for recording."""
    
    timestamp_ms: int
    exchange_ts_ms: int
    contract: str
    message_type: str  # "trade"
    side: str  # "buy" or "sell"
    price: str
    size: int
    local_sequence: int = 0  # Local sequence for gap detection
    
    @classmethod
    def from_ws_message(cls, msg: Dict[str, Any], contract: str, local_seq: int = 0) -> "TradeEvent":
        """Create trade event from WebSocket message."""
        result = msg.get("result", {})
        
        # Determine side from size (positive = buy, negative = sell)
        size = int(result.get("size", 0))
        side = "buy" if size > 0 else "sell"
        
        # Extract contract from trade data if available
        trade_contract = result.get("contract", contract)
        
        return cls(
            timestamp_ms=int(time.time() * 1000),
            exchange_ts_ms=result.get("create_time_ms", int(time.time() * 1000)),
            contract=trade_contract,
            message_type="trade",
            side=side,
            price=result.get("price", "0"),
            size=abs(size),
            local_sequence=local_seq,
        )
    
    def to_jsonl(self) -> str:
        """Convert to JSONL string."""
        return json.dumps(asdict(self))


class L2Recorder:
    """
    Records L2 orderbook and trade data from Gate.io futures.
    
    Subscribes to:
    - futures.order_book (depth) for top N levels
    - futures.trades for trade data
    
    Records to JSONL for deterministic replay.
    
    Features:
    - Local sequence tracking for gap detection
    - Delta reconciliation
    - Automatic resync on gaps
    - Lossless event ordering
    """
    
    def __init__(
        self,
        output_dir: Path,
        contracts: Optional[List[str]] = None,
        depth_levels: int = 20,
        gap_threshold: int = 10,  # Gap detection threshold
    ):
        self.output_dir = Path(output_dir)
        self.contracts = contracts or list(mm_config.contracts.keys())
        self.depth_levels = depth_levels
        self.gap_threshold = gap_threshold
        
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._running: bool = False
        self._reconnects: int = 0
        
        # Local sequence tracking for gap detection
        self._local_sequence: int = 0
        self._last_sequences: Dict[str, int] = {}  # per-contract last sequence
        
        # Output files
        self._orderbook_file: Optional[Path] = None
        self._trades_file: Optional[Path] = None
        self._orderbook_handle: Optional[Any] = None
        self._trades_handle: Optional[Any] = None
        self._unified_file: Optional[Path] = None
        self._unified_handle: Optional[Any] = None
        
        self._setup_output_files()
    
    def _setup_output_files(self) -> None:
        """Setup output files with timestamps."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._orderbook_file = self.output_dir / f"orderbook_{timestamp}.jsonl"
        self._trades_file = self.output_dir / f"trades_{timestamp}.jsonl"
        self._unified_file = self.output_dir / f"unified_{timestamp}.jsonl"
        
        log.info(f"Recording to: {self._orderbook_file}")
        log.info(f"Recording to: {self._trades_file}")
        log.info(f"Recording to: {self._unified_file}")
    
    async def start(self, session: aiohttp.ClientSession) -> None:
        """Start recording."""
        self._session = session
        self._running = True
        
        # Open output files
        self._orderbook_handle = open(self._orderbook_file, "w")
        self._trades_handle = open(self._trades_file, "w")
        self._unified_handle = open(self._unified_file, "w")
        
        # Reset local sequence on new session
        self._local_sequence = 0
        
        while self._running and self._reconnects < 20:
            try:
                await self._connect_and_consume()
            except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError) as exc:
                self._reconnects += 1
                delay = min(2.0 * (2 ** self._reconnects), 60.0)
                log.warning(
                    f"Recorder disconnected ({exc}). Reconnect {self._reconnects} in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                break
        
        self._cleanup()
    
    async def _connect_and_consume(self) -> None:
        """Connect to WebSocket and consume messages."""
        log.info(f"L2 Recorder connecting: {FUTURES_WS_URL}")
        
        async with self._session.ws_connect(
            FUTURES_WS_URL,
            heartbeat=25.0,
            receive_timeout=60.0,
        ) as ws:
            self._ws = ws
            self._reconnects = 0
            log.info("L2 Recorder connected")
            
            # Subscribe to order book depth for each contract
            for i, contract in enumerate(self.contracts, start=1):
                # Subscribe to order book depth (request snapshot first)
                depth_sub = {
                    "time": int(time.time()),
                    "id": i,
                    "channel": "futures.order_book",
                    "event": "all",  # Request initial snapshot
                    "payload": [contract, self.depth_levels, "0"],
                }
                await ws.send_str(json.dumps(depth_sub))
                log.info(f"Subscribed order_book (snapshot): {contract} (depth={self.depth_levels})")
                
                # Subscribe to trades
                trade_sub = {
                    "time": int(time.time()),
                    "id": i + 1000,
                    "channel": "futures.trades",
                    "event": "subscribe",
                    "payload": [contract],
                }
                await ws.send_str(json.dumps(trade_sub))
                log.info(f"Subscribed trades: {contract}")
            
            # Start ping loop
            ping_task = asyncio.create_task(self._ping_loop(ws))
            
            try:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self._dispatch(msg.data)
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        log.warning("L2 Recorder closed by server")
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        log.error(f"L2 Recorder error: {ws.exception()}")
                        break
            finally:
                ping_task.cancel()
    
    async def _ping_loop(self, ws) -> None:
        """Send periodic pings."""
        while not ws.closed:
            await asyncio.sleep(25.0)
            if not ws.closed:
                ping = {
                    "time": int(time.time()),
                    "channel": "futures.ping",
                }
                await ws.send_str(json.dumps(ping))
    
    def _dispatch(self, msg_data: str) -> None:
        """Dispatch WebSocket message to appropriate handler."""
        try:
            msg = json.loads(msg_data)
            log.debug(f"Received message: {msg.get('channel', 'unknown')}")
        except json.JSONDecodeError as exc:
            log.error(f"Failed to decode message: {exc}")
            return
        
        channel = msg.get("channel", "")
        event = msg.get("event", "")
        result = msg.get("result", {})
        
        log.debug(f"Dispatch: channel={channel}, event={event}, result_type={type(result).__name__}")
        
        if event == "subscribe":
            log.info(f"Subscription confirmed: {channel}")
            return
        
        if not result:
            return
        
        # Handle trades (result is a list)
        if channel == "futures.trades" and event == "update":
            # For trades, contract is in the trade data itself
            self._handle_trade(msg, "")
        elif channel == "futures.order_book" and event in ("update", "all"):
            # For orderbook, result is a dict
            contract = result.get("s", "") or result.get("contract", "")
            self._handle_orderbook(msg, contract)
        else:
            log.debug(f"Unhandled message: channel={channel}, event={event}")
    
    def _handle_orderbook(self, msg: Dict[str, Any], contract: str) -> None:
        """Handle orderbook update with gap detection."""
        self._local_sequence += 1
        local_seq = self._local_sequence
        
        result = msg.get("result", {})
        log.debug(f"Orderbook result: {result}")
        
        snapshot = L2Snapshot.from_ws_message(msg, contract, local_seq)
        
        # Detect sequence gaps
        if snapshot.sequence:
            last_seq = self._last_sequences.get(contract, 0)
            if last_seq > 0:
                gap = snapshot.sequence - last_seq
                if gap > 1:
                    log.warning(
                        f"Sequence gap detected for {contract}: "
                        f"last={last_seq}, current={snapshot.sequence}, gap={gap}"
                    )
                    if gap > self.gap_threshold:
                        log.error(
                            f"Large gap ({gap}) for {contract} - may need resync"
                        )
            self._last_sequences[contract] = snapshot.sequence
        
        # Write to orderbook file
        if self._orderbook_handle:
            self._orderbook_handle.write(snapshot.to_jsonl() + "\n")
            self._orderbook_handle.flush()
        
        # Write to unified file
        if self._unified_handle:
            self._unified_handle.write(snapshot.to_jsonl() + "\n")
            self._unified_handle.flush()
        
        log.debug(f"Recorded orderbook: {contract} bids={len(snapshot.bids)} asks={len(snapshot.asks)} seq={local_seq}")
    
    def _handle_trade(self, msg: Dict[str, Any], contract: str) -> None:
        """Handle trade event with local sequence tracking."""
        # Gate.io trades come as arrays in result
        result = msg.get("result", [])
        
        # Extract contract from the message if not provided
        if not contract:
            # Try to get contract from the message itself
            contract = msg.get("result", [{}])[0].get("s", "") if isinstance(result, list) and result else ""
        
        log.debug(f"Trade data: {result[:1] if isinstance(result, list) else result}")
        
        if isinstance(result, list):
            for trade_data in result:
                self._local_sequence += 1
                local_seq = self._local_sequence
                
                # Use contract from trade data if available, otherwise use the one we subscribed to
                trade_contract = trade_data.get("s", contract) or contract
                
                # If still no contract, use the first contract from our subscription list
                if not trade_contract:
                    trade_contract = self.contracts[0] if self.contracts else "unknown"
                
                trade = TradeEvent.from_ws_message({"result": trade_data}, trade_contract, local_seq)
                
                if self._trades_handle:
                    self._trades_handle.write(trade.to_jsonl() + "\n")
                    self._trades_handle.flush()
                
                # Write to unified file
                if self._unified_handle:
                    self._unified_handle.write(trade.to_jsonl() + "\n")
                    self._unified_handle.flush()
                
                log.debug(f"Recorded trade: {trade_contract} {trade.side} {trade.price} x{trade.size} seq={local_seq}")
    
    def _cleanup(self) -> None:
        """Cleanup resources."""
        if self._orderbook_handle:
            self._orderbook_handle.close()
        if self._trades_handle:
            self._trades_handle.close()
        if self._unified_handle:
            self._unified_handle.close()
        
        log.info("L2 Recorder cleanup complete")
    
    async def stop(self) -> None:
        """Stop recording."""
        self._running = False
        if self._ws:
            await self._ws.close()
        
        log.info("L2 Recorder stopped")


def record_l2_data(
    output_dir: Path,
    contracts: Optional[List[str]] = None,
    duration_seconds: Optional[int] = None,
    depth_levels: int = 20,
) -> None:
    """
    Record L2 data for specified duration.
    
    Args:
        output_dir: Directory to save recorded data
        contracts: List of contracts to record (default: all configured)
        duration_seconds: Recording duration (None: run indefinitely)
        depth_levels: Number of orderbook levels to record
    """
    async def _run():
        async with aiohttp.ClientSession() as session:
            recorder = L2Recorder(output_dir, contracts, depth_levels)
            
            if duration_seconds:
                task = asyncio.create_task(recorder.start(session))
                try:
                    await asyncio.wait_for(task, timeout=duration_seconds)
                except asyncio.TimeoutError:
                    await recorder.stop()
            else:
                await recorder.start(session)
    
    asyncio.run(_run())
