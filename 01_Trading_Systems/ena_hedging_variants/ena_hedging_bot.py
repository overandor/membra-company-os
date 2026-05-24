#!/usr/bin/env python3
import os
"""
ENA HEDGING BOT
Hedging strategy for ENA_USDT - Place limit orders at best bid/ask, sell at market when profitable
"""

import asyncio
import websockets
import json
import time
import math
import logging
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import deque
import gate_api
from gate_api import ApiClient, Configuration, FuturesApi

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class HedgingConfig:
    def __init__(self):
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        self.symbol = "ENA_USDT"
        self.order_size = 10.0  # 10 ENA per order
        self.min_profit_margin = 0.001  # 0.1% minimum profit
        self.max_position = 100.0  # Maximum 100 ENA position
        self.order_refresh_ms = 100  # 100ms refresh
        self.hedge_ratio = 1.0  # 1:1 hedge ratio

class HedgingStats:
    def __init__(self):
        self.total_trades = 0
        self.total_profit = 0.0
        self.total_fees = 0.0
        self.successful_hedges = 0
        self.failed_hedges = 0
        self.active_orders = {}
        self.position = 0.0
        self.avg_entry_price = 0.0
        self.unrealized_pnl = 0.0
        self.start_time = time.time()

class HedgingUI:
    def __init__(self, config: HedgingConfig, stats: HedgingStats):
        self.config = config
        self.stats = stats
        self.root = None
        self.running = False
        self.log_queue = deque(maxlen=500)
        
    def create_ui(self):
        self.root = tk.Tk()
        self.root.title("🛡️ ENA HEDGING BOT")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0a0a')
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#0a0a0a')
        style.configure('TLabel', background='#0a0a0a', foreground='#00ff88', font=('Consolas', 10))
        style.configure('Title.TLabel', font=('Consolas', 14, 'bold'), foreground='#ff6b6b')
        style.configure('Stats.TLabel', font=('Consolas', 11), foreground='#4ecdc4')
        style.configure('TButton', font=('Consolas', 10, 'bold'))
        
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(main_frame, text="🛡️ ENA HEDGING STRATEGY", style='Title.TLabel')
        header.pack(pady=10)
        
        # Top stats frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Position info
        pos_frame = ttk.Frame(stats_frame)
        pos_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.position_label = ttk.Label(pos_frame, text="Position: 0.000 ENA", style='Stats.TLabel')
        self.position_label.pack(anchor=tk.W)
        
        self.avg_price_label = ttk.Label(pos_frame, text="Avg Entry: $0.0000", style='Stats.TLabel')
        self.avg_price_label.pack(anchor=tk.W)
        
        self.pnl_label = ttk.Label(pos_frame, text="PnL: $0.0000", style='Stats.TLabel')
        self.pnl_label.pack(anchor=tk.W)
        
        # Performance info
        perf_frame = ttk.Frame(stats_frame)
        perf_frame.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        
        self.trades_label = ttk.Label(perf_frame, text="Trades: 0", style='Stats.TLabel')
        self.trades_label.pack(anchor=tk.E)
        
        self.profit_label = ttk.Label(perf_frame, text="Profit: $0.00", style='Stats.TLabel')
        self.profit_label.pack(anchor=tk.E)
        
        self.hedges_label = ttk.Label(perf_frame, text="Hedges: 0/0", style='Stats.TLabel')
        self.hedges_label.pack(anchor=tk.E)
        
        # Market data frame
        market_frame = ttk.Frame(main_frame)
        market_frame.pack(fill=tk.X, pady=10)
        
        self.mid_label = ttk.Label(market_frame, text="Mid: $0.0000", style='Stats.TLabel')
        self.mid_label.pack(side=tk.LEFT, padx=20)
        
        self.spread_label = ttk.Label(market_frame, text="Spread: 0.00 bps", style='Stats.TLabel')
        self.spread_label.pack(side=tk.LEFT, padx=20)
        
        self.margin_label = ttk.Label(market_frame, text="Margin: 0.00%", style='Stats.TLabel')
        self.margin_label.pack(side=tk.LEFT, padx=20)
        
        # Order book visualization
        book_frame = ttk.Frame(main_frame)
        book_frame.pack(fill=tk.X, pady=10)
        
        self.bid_canvas = tk.Canvas(book_frame, width=680, height=120, bg='#0d0d1a', highlightthickness=0)
        self.bid_canvas.pack(side=tk.LEFT, padx=5)
        
        self.ask_canvas = tk.Canvas(book_frame, width=680, height=120, bg='#0d0d1a', highlightthickness=0)
        self.ask_canvas.pack(side=tk.RIGHT, padx=5)
        
        # Log area
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, bg='#0d0d1a', fg='#00ff88', 
                                                   font=('Consolas', 9), insertbackground='#00ff88')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ START HEDGING", command=self.on_start)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ STOP", command=self.on_stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.close_btn = ttk.Button(btn_frame, text="🔄 CLOSE POSITION", command=self.on_close_position)
        self.close_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(btn_frame, text="⏸ IDLE", style='Stats.TLabel')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        self.running = True
        self.update_ui()
        
    def on_start(self):
        """Start hedging with confirmation"""
        result = messagebox.askyesno(
            "⚠️ HEDGING CONFIRMATION",
            "⚠️ WARNING: This will start REAL hedging with ENA_USDT!\n\n"
            "• REAL MONEY will be used\n"
            "• Limit orders at best bid/ask\n"
            "• Market orders when profitable\n"
            "• You can lose money\n\n"
            "Do you want to proceed with REAL hedging?",
            icon='warning'
        )
        
        if result:
            self.start_btn.configure(state=tk.DISABLED)
            self.stop_btn.configure(state=tk.NORMAL)
            self.status_label.configure(text="🛡️ HEDGING ACTIVE", foreground='#ff6b6b')
            self.add_log("⚠️ REAL HEDGING ACTIVATED - ENA_USDT")
            if hasattr(self, 'start_callback'):
                self.start_callback()
        else:
            self.add_log("❌ Hedging cancelled by user")
    
    def on_stop(self):
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="⏸ STOPPED", foreground='#ff6b6b')
        if hasattr(self, 'stop_callback'):
            self.stop_callback()
    
    def on_close_position(self):
        """Close current position"""
        if hasattr(self, 'close_callback'):
            self.close_callback()
    
    def add_log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_queue.append(f"[{timestamp}] {msg}")
    
    def update_book_viz(self, bids: List, asks: List):
        # Clear canvases
        self.bid_canvas.delete("all")
        self.ask_canvas.delete("all")
        
        if not bids or not asks:
            return
        
        # Draw bid bars (green)
        max_vol = max(max(s for _, s in bids[:15]), max(s for _, s in asks[:15])) if bids and asks else 1
        for i, (price, size) in enumerate(bids[:15]):
            width = (size / max_vol) * 660
            y = i * 8
            self.bid_canvas.create_rectangle(680 - width, y, 680, y + 6, fill='#00ff88', outline='')
            self.bid_canvas.create_text(5, y + 3, text=f"{price:.4f}", fill='#00ff88', anchor='w', font=('Consolas', 7))
        
        # Draw ask bars (red)
        for i, (price, size) in enumerate(asks[:15]):
            width = (size / max_vol) * 660
            y = i * 8
            self.ask_canvas.create_rectangle(0, y, width, y + 6, fill='#ff6b6b', outline='')
            self.ask_canvas.create_text(675, y + 3, text=f"{price:.4f}", fill='#ff6b6b', anchor='e', font=('Consolas', 7))
    
    def update_ui(self):
        if not self.running:
            return
        
        # Update position info
        pos_color = '#00ff88' if self.stats.position >= 0 else '#ff6b6b'
        self.position_label.configure(text=f"Position: {self.stats.position:+.3f} ENA", foreground=pos_color)
        
        if self.stats.avg_entry_price > 0:
            self.avg_price_label.configure(text=f"Avg Entry: ${self.stats.avg_entry_price:.4f}")
        
        pnl_color = '#00ff88' if self.stats.unrealized_pnl >= 0 else '#ff6b6b'
        self.pnl_label.configure(text=f"PnL: ${self.stats.unrealized_pnl:+.4f}", foreground=pnl_color)
        
        # Update performance
        self.trades_label.configure(text=f"Trades: {self.stats.total_trades}")
        
        profit_color = '#00ff88' if self.stats.total_profit >= 0 else '#ff6b6b'
        self.profit_label.configure(text=f"Profit: ${self.stats.total_profit:+.4f}", foreground=profit_color)
        
        self.hedges_label.configure(text=f"Hedges: {self.stats.successful_hedges}/{self.stats.successful_hedges + self.stats.failed_hedges}")
        
        # Update log
        while self.log_queue:
            msg = self.log_queue.popleft()
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
        
        # Schedule next update
        self.root.after(50, self.update_ui)
    
    def run(self):
        self.create_ui()
        self.root.mainloop()
    
    def close(self):
        self.running = False
        if self.root:
            self.root.quit()

class ENAHedgingBot:
    def __init__(self, config: HedgingConfig, stats: HedgingStats, ui: HedgingUI):
        self.config = config
        self.stats = stats
        self.ui = ui
        
        # Trading state
        self._running = False
        self._hedging = False
        self.position = 0.0
        self.mid_price = 0.0
        self.bids = []
        self.asks = []
        
        # Order management
        self.active_orders = {}
        self.last_order_time = 0
        
        # Initialize API
        cfg = Configuration(key=config.api_key, secret=config.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
    
    async def get_balance(self):
        """Get account balance"""
        try:
            accounts = self.api.list_futures_accounts(settle='usdt')
            if accounts:
                account = accounts[0] if isinstance(accounts, list) else accounts
                self.ui.add_log(f"💰 Balance: ${float(account.available):.2f}")
                return float(account.available)
        except Exception as e:
            self.ui.add_log(f"❌ Balance error: {e}")
        return 0.0
    
    async def get_positions(self):
        """Get current positions"""
        try:
            positions = self.api.list_positions(settle='usdt')
            total_size = 0.0
            total_cost = 0.0
            total_unrealized = 0.0
            position_count = 0
            
            # Aggregate all ENA positions
            for pos in positions:
                if pos.contract == self.config.symbol:
                    size = float(pos.size)
                    if size != 0:
                        total_size += size
                        total_cost += size * float(pos.entry_price)
                        total_unrealized += float(pos.unrealised_pnl)
                        position_count += 1
                        
                        side = "LONG" if size > 0 else "SHORT"
                        self.ui.add_log(f"📊 {side} {abs(size):.3f} ENA @ ${float(pos.entry_price):.4f} (PnL: ${float(pos.unrealised_pnl):+4f})")
            
            # Update aggregated position
            if total_size != 0:
                self.position = total_size
                self.stats.position = total_size
                self.stats.avg_entry_price = total_cost / total_size if total_size != 0 else 0.0
                self.stats.unrealized_pnl = total_unrealized
                
                net_side = "LONG" if total_size > 0 else "SHORT"
                self.ui.add_log(f"📊 NET {net_side}: {abs(total_size):.3f} ENA @ ${self.stats.avg_entry_price:.4f} (Total PnL: ${total_unrealized:+.4f})")
            else:
                self.position = 0.0
                self.stats.position = 0.0
                self.stats.avg_entry_price = 0.0
                self.stats.unrealized_pnl = 0.0
                self.ui.add_log(f"📊 No ENA positions")
                
        except Exception as e:
            self.ui.add_log(f"❌ Position error: {e}")
    
    async def connect_websocket(self):
        """Connect to Gate.io futures WebSocket"""
        ws_url = "wss://fx-ws.gateio.ws/v4/ws/usdt"
        
        try:
            self.ws = await websockets.connect(ws_url, ping_interval=20)
            self.ui.add_log("✅ WebSocket connected")
            
            # Subscribe to order book
            subscribe_msg = {
                "time": int(time.time()),
                "channel": "futures.order_book",
                "event": "subscribe",
                "payload": [self.config.symbol, "5", "100ms"]
            }
            await self.ws.send(json.dumps(subscribe_msg))
            
            return True
        except Exception as e:
            self.ui.add_log(f"❌ WebSocket error: {e}")
            return False
    
    async def process_messages(self):
        """Process WebSocket messages"""
        try:
            async for message in self.ws:
                if not self._running:
                    break
                
                data = json.loads(message)
                channel = data.get('channel', '')
                
                if channel == 'futures.order_book' and data.get('event') == 'update':
                    await self.process_orderbook(data.get('result', {}))
                    
        except Exception as e:
            self.ui.add_log(f"❌ Message processing error: {e}")
    
    async def process_orderbook(self, result: Dict):
        """Process order book updates"""
        if not result:
            return
        
        # Parse bids and asks
        if 'b' in result:
            self.bids = [[float(p), float(s)] for p, s in result['b']]
        if 'a' in result:
            self.asks = [[float(p), float(s)] for p, s in result['a']]
        
        if self.bids and self.asks:
            self.mid_price = (self.bids[0][0] + self.asks[0][0]) / 2
            
            # Update UI
            self.update_market_ui()
    
    def update_market_ui(self):
        """Update market data UI"""
        if self.mid_price > 0 and self.bids and self.asks:
            spread_bps = (self.asks[0][0] - self.bids[0][0]) / self.mid_price * 10000
            
            self.ui.mid_label.configure(text=f"Mid: ${self.mid_price:.4f}")
            self.ui.spread_label.configure(text=f"Spread: {spread_bps:.2f} bps")
            
            # Calculate profit margin if we have position
            if self.stats.position != 0 and self.stats.avg_entry_price > 0:
                if self.stats.position > 0:  # Long position
                    margin = (self.asks[0][0] - self.stats.avg_entry_price) / self.stats.avg_entry_price * 100
                else:  # Short position
                    margin = (self.stats.avg_entry_price - self.bids[0][0]) / self.stats.avg_entry_price * 100
                
                margin_color = '#00ff88' if margin > self.config.min_profit_margin * 100 else '#ff6b6b'
                self.ui.margin_label.configure(text=f"Margin: {margin:+.3f}%", foreground=margin_color)
            
            # Update order book visualization
            self.ui.update_book_viz(self.bids, self.asks)
    
    async def place_limit_order(self, side: str, price: float, size: float):
        """Place limit order"""
        try:
            order = gate_api.FuturesOrder(
                contract=self.config.symbol,
                size=size,
                price=price,
                side=side,
                type='limit',
                time_in_force='post_only',
                client_order_id=f"hedge_{side}_{int(time.time() * 1000)}"
            )
            
            result = self.api.create_futures_order(settle='usdt', order=order)
            self.stats.total_trades += 1
            self.ui.add_log(f"🛡️ LIMIT ORDER: {side.upper()} {size:.3f} ENA @ ${price:.4f}")
            
            return result.id
            
        except Exception as e:
            self.ui.add_log(f"❌ Limit order failed: {e}")
            return None
    
    async def place_market_order(self, side: str, size: float):
        """Place market order for profit taking"""
        try:
            order = gate_api.FuturesOrder(
                contract=self.config.symbol,
                size=size,
                side=side,
                type='market',
                client_order_id=f"profit_{side}_{int(time.time() * 1000)}"
            )
            
            result = self.api.create_futures_order(settle='usdt', order=order)
            self.stats.total_trades += 1
            
            # Calculate profit
            if side == 'sell' and self.stats.position > 0:
                profit = (self.mid_price - self.stats.avg_entry_price) * size
                self.stats.total_profit += profit
                self.stats.successful_hedges += 1
                self.ui.add_log(f"💰 PROFIT: SOLD {size:.3f} ENA @ ${self.mid_price:.4f} - Profit: ${profit:+.4f}")
            elif side == 'buy' and self.stats.position < 0:
                profit = (self.stats.avg_entry_price - self.mid_price) * abs(size)
                self.stats.total_profit += profit
                self.stats.successful_hedges += 1
                self.ui.add_log(f"💰 PROFIT: BOUGHT {abs(size):.3f} ENA @ ${self.mid_price:.4f} - Profit: ${profit:+.4f}")
            
            return result.id
            
        except Exception as e:
            self.ui.add_log(f"❌ Market order failed: {e}")
            self.stats.failed_hedges += 1
            return None
    
    async def cancel_all_orders(self):
        """Cancel all open orders"""
        try:
            orders = self.api.list_futures_orders(settle='usdt', status='open')
            for order in orders:
                if order.contract == self.config.symbol:
                    self.api.cancel_futures_order(settle='usdt', order_id=order.id)
        except Exception as e:
            self.ui.add_log(f"❌ Cancel orders error: {e}")
    
    async def close_position(self):
        """Close current position at market"""
        if abs(self.stats.position) < 0.001:
            self.ui.add_log("⚠️ No position to close")
            return
        
        self.ui.add_log(f"🔄 Closing position: {self.stats.position:+.3f} ENA")
        
        if self.stats.position > 0:
            await self.place_market_order('sell', abs(self.stats.position))
        else:
            await self.place_market_order('buy', abs(self.stats.position))
        
        await self.get_positions()
    
    async def hedging_loop(self):
        """Main hedging loop"""
        while self._running and self._hedging:
            try:
                # Update position
                await self.get_positions()
                
                # Check if we can place hedge orders
                if self.bids and self.asks:
                    current_pos = self.stats.position
                    best_bid = self.bids[0][0]
                    best_ask = self.asks[0][0]
                    
                    # If no net position, place limit orders at best bid/ask
                    if abs(current_pos) < 0.001:
                        self.ui.add_log(f"🎯 No net position - placing limit orders at best prices")
                        # Place buy at best bid
                        buy_order = await self.place_limit_order('buy', best_bid, self.config.order_size)
                        if buy_order:
                            self.active_orders['buy'] = buy_order
                        
                        # Place sell at best ask
                        sell_order = await self.place_limit_order('sell', best_ask, self.config.order_size)
                        if sell_order:
                            self.active_orders['sell'] = sell_order
                    
                    # If we have position, check for profit opportunity
                    elif current_pos != 0 and self.stats.avg_entry_price > 0:
                        profit_target_buy = self.stats.avg_entry_price * (1 + self.config.min_profit_margin)
                        profit_target_sell = self.stats.avg_entry_price * (1 - self.config.min_profit_margin)
                        
                        if current_pos > 0:  # Net long position
                            # Check if we can sell at profit
                            if best_ask > profit_target_buy:
                                profit_pct = (best_ask - self.stats.avg_entry_price) / self.stats.avg_entry_price * 100
                                self.ui.add_log(f"💰 Profit opportunity: SELL at ${best_ask:.4f} (Target: ${profit_target_buy:.4f}, Profit: {profit_pct:.3f}%)")
                                await self.cancel_all_orders()
                                await self.place_market_order('sell', current_pos)
                            else:
                                self.ui.add_log(f"⏳ Long position waiting: Need ask > ${profit_target_buy:.4f} (Current: ${best_ask:.4f})")
                        
                        else:  # Net short position
                            # Check if we can buy at profit
                            if best_bid < profit_target_sell:
                                profit_pct = (self.stats.avg_entry_price - best_bid) / self.stats.avg_entry_price * 100
                                self.ui.add_log(f"💰 Profit opportunity: BUY at ${best_bid:.4f} (Target: ${profit_target_sell:.4f}, Profit: {profit_pct:.3f}%)")
                                await self.cancel_all_orders()
                                await self.place_market_order('buy', abs(current_pos))
                            else:
                                self.ui.add_log(f"⏳ Short position waiting: Need bid < ${profit_target_sell:.4f} (Current: ${best_bid:.4f})")
                        
                        # Show current position status
                        self.ui.add_log(f"📊 Net Position: {current_pos:+.3f} ENA @ ${self.stats.avg_entry_price:.4f}")
                        self.ui.add_log(f"💰 Current PnL: ${self.stats.unrealized_pnl:+.4f}")
                
                # Check order status and manage
                await self.manage_orders()
                
                await asyncio.sleep(self.config.order_refresh_ms / 1000)
                
            except Exception as e:
                self.ui.add_log(f"❌ Hedging loop error: {e}")
                await asyncio.sleep(1)
    
    async def manage_orders(self):
        """Manage active orders"""
        try:
            orders = self.api.list_futures_orders(settle='usdt', status='open')
            open_order_ids = {order.id for order in orders if order.contract == self.config.symbol}
            
            # Clean up filled/cancelled orders from tracking
            filled_orders = []
            for order_type, order_id in self.active_orders.items():
                if order_id not in open_order_ids:
                    filled_orders.append(order_type)
            
            for order_type in filled_orders:
                del self.active_orders[order_type]
                self.ui.add_log(f"✅ {order_type.upper()} order filled")
                
        except Exception as e:
            self.ui.add_log(f"❌ Order management error: {e}")
    
    async def start(self):
        """Start hedging bot"""
        self._running = True
        self._hedging = True
        
        # Initial setup
        await self.get_balance()
        await self.get_positions()
        
        # Connect WebSocket
        if not await self.connect_websocket():
            return
        
        # Start tasks
        tasks = [
            asyncio.create_task(self.process_messages()),
            asyncio.create_task(self.hedging_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.ui.add_log(f"❌ Runtime error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop hedging bot"""
        self._running = False
        self._hedging = False
        
        if self.ws:
            await self.ws.close()
        
        await self.cancel_all_orders()
        self.ui.add_log("⏹ Hedging bot stopped")

class HedgingApp:
    def __init__(self):
        self.config = HedgingConfig()
        self.stats = HedgingStats()
        self.ui = HedgingUI(self.config, self.stats)
        self.bot = ENAHedgingBot(self.config, self.stats, self.ui)
        
        # Set UI callbacks
        self.ui.start_callback = self.start_hedging
        self.ui.stop_callback = self.stop_hedging
        self.ui.close_callback = self.close_position
    
    def start_hedging(self):
        """Start hedging in separate thread"""
        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.bot.start())
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
    
    def stop_hedging(self):
        """Stop hedging"""
        def run_stop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.bot.stop())
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_stop, daemon=True)
        thread.start()
    
    def close_position(self):
        """Close position"""
        def run_close():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.bot.close_position())
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_close, daemon=True)
        thread.start()
    
    def run(self):
        """Run the application"""
        try:
            self.ui.run()
        except KeyboardInterrupt:
            print("\n⏹ Application interrupted")
        finally:
            if hasattr(self.ui, 'close'):
                self.ui.close()

if __name__ == "__main__":
    app = HedgingApp()
    app.run()
