#!/usr/bin/env python3
import os
"""
SMART HEDGING DEMO - Check balance and simulate hedging without placing orders
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

class SmartHedgingConfig:
    def __init__(self):
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        self.symbol = "ENA_USDT"
        self.order_size = 10.0  # 10 ENA per order
        self.min_profit_margin = 0.002  # 0.2% minimum profit
        self.max_position = 100.0  # Maximum 100 ENA position
        self.dry_run = True  # NO REAL ORDERS

class SmartHedgingStats:
    def __init__(self):
        self.total_trades = 0
        self.total_profit = 0.0
        self.total_fees = 0.0
        self.successful_hedges = 0
        self.failed_hedges = 0
        self.simulated_orders = {}
        self.position = 0.0
        self.avg_entry_price = 0.0
        self.unrealized_pnl = 0.0
        self.start_time = time.time()

class SmartHedgingUI:
    def __init__(self, config: SmartHedgingConfig, stats: SmartHedgingStats):
        self.config = config
        self.stats = stats
        self.root = None
        self.running = False
        self.log_queue = deque(maxlen=500)
        
    def create_ui(self):
        self.root = tk.Tk()
        self.root.title("🧠 SMART HEDGING DEMO - DRY RUN")
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
        header = ttk.Label(main_frame, text="🧠 SMART HEDGING DEMO - DRY RUN MODE", style='Title.TLabel')
        header.pack(pady=10)
        
        # Dry run warning
        warning = ttk.Label(main_frame, text="⚠️ NO REAL ORDERS - SIMULATION ONLY", style='Stats.TLabel')
        warning.pack()
        
        # Top stats frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Balance info
        balance_frame = ttk.Frame(stats_frame)
        balance_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.balance_label = ttk.Label(balance_frame, text="Balance: $0.00", style='Stats.TLabel')
        self.balance_label.pack(anchor=tk.W)
        
        self.available_label = ttk.Label(balance_frame, text="Available: $0.00", style='Stats.TLabel')
        self.available_label.pack(anchor=tk.W)
        
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
        
        self.trades_label = ttk.Label(perf_frame, text="Simulated: 0", style='Stats.TLabel')
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
        
        self.opportunity_label = ttk.Label(market_frame, text="Opportunity: NONE", style='Stats.TLabel')
        self.opportunity_label.pack(side=tk.LEFT, padx=20)
        
        # Order book visualization
        book_frame = ttk.Frame(main_frame)
        book_frame.pack(fill=tk.X, pady=10)
        
        self.bid_canvas = tk.Canvas(book_frame, width=680, height=120, bg='#0d0d1a', highlightthickness=0)
        self.bid_canvas.pack(side=tk.LEFT, padx=5)
        
        self.ask_canvas = tk.Canvas(book_frame, width=680, height=120, bg='#0d0d1a', highlightthickness=0)
        self.ask_canvas.pack(side=tk.RIGHT, padx=5)
        
        # Strategy panel
        strategy_frame = ttk.Frame(main_frame)
        strategy_frame.pack(fill=tk.X, pady=10)
        
        self.strategy_label = ttk.Label(strategy_frame, text="🧠 SMART STRATEGY: WAITING", style='Title.TLabel')
        self.strategy_label.pack()
        
        # Log area
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, bg='#0d0d1a', fg='#00ff88', 
                                                   font=('Consolas', 9), insertbackground='#00ff88')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ START SMART HEDGING", command=self.on_start)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ STOP", command=self.on_stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.balance_btn = ttk.Button(btn_frame, text="💰 CHECK BALANCE", command=self.on_check_balance)
        self.balance_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(btn_frame, text="⏸ IDLE", style='Stats.TLabel')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        self.running = True
        self.update_ui()
        
    def on_start(self):
        """Start smart hedging simulation"""
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.status_label.configure(text="🧠 SMART HEDGING ACTIVE", foreground='#ff6b6b')
        self.add_log("🧠 SMART HEDGING SIMULATION STARTED - DRY RUN MODE")
        self.add_log("⚠️ NO REAL ORDERS WILL BE PLACED")
        if hasattr(self, 'start_callback'):
            self.start_callback()
    
    def on_stop(self):
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="⏸ STOPPED", foreground='#ff6b6b')
        if hasattr(self, 'stop_callback'):
            self.stop_callback()
    
    def on_check_balance(self):
        """Check account balance"""
        self.add_log("💰 Checking account balance...")
        if hasattr(self, 'balance_callback'):
            self.balance_callback()
    
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
        
        # Update balance info
        if hasattr(self, 'current_balance'):
            self.balance_label.configure(text=f"Balance: ${self.current_balance:.2f}")
            self.available_label.configure(text=f"Available: ${self.current_available:.2f}")
        
        # Update position info
        pos_color = '#00ff88' if self.stats.position >= 0 else '#ff6b6b'
        self.position_label.configure(text=f"Position: {self.stats.position:+.3f} ENA", foreground=pos_color)
        
        if self.stats.avg_entry_price > 0:
            self.avg_price_label.configure(text=f"Avg Entry: ${self.stats.avg_entry_price:.4f}")
        
        pnl_color = '#00ff88' if self.stats.unrealized_pnl >= 0 else '#ff6b6b'
        self.pnl_label.configure(text=f"PnL: ${self.stats.unrealized_pnl:+.4f}", foreground=pnl_color)
        
        # Update performance
        self.trades_label.configure(text=f"Simulated: {self.stats.total_trades}")
        
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

class SmartHedgingBot:
    def __init__(self, config: SmartHedgingConfig, stats: SmartHedgingStats, ui: SmartHedgingUI):
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
        
        # Balance tracking
        self.current_balance = 0.0
        self.current_available = 0.0
        
        # Order management
        self.simulated_orders = {}
        self.last_order_time = 0
        
        # Initialize API
        cfg = Configuration(key=config.api_key, secret=config.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
    
    async def check_balance(self):
        """Check account balance"""
        try:
            accounts = self.api.list_futures_accounts(settle='usdt')
            if accounts:
                account = accounts[0] if isinstance(accounts, list) else accounts
                self.current_balance = float(account.total)
                self.current_available = float(account.available)
                self.ui.current_balance = self.current_balance
                self.ui.current_available = self.current_available
                self.ui.add_log(f"💰 Balance: ${self.current_balance:.2f}")
                self.ui.add_log(f"💰 Available: ${self.current_available:.2f}")
                return True
        except Exception as e:
            self.ui.add_log(f"❌ Balance error: {e}")
        return False
    
    async def get_positions(self):
        """Get current positions"""
        try:
            positions = self.api.list_positions(settle='usdt')
            for pos in positions:
                if pos.contract == self.config.symbol:
                    size = float(pos.size)
                    if size != 0:
                        self.position = size
                        self.stats.position = size
                        self.stats.avg_entry_price = float(pos.entry_price)
                        self.stats.unrealized_pnl = float(pos.unrealised_pnl)
                        self.ui.add_log(f"📊 Position: {size:+.3f} ENA @ ${float(pos.entry_price):.4f}")
                        break
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
            await self.analyze_opportunity()
    
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
    
    async def analyze_opportunity(self):
        """Analyze hedging opportunities"""
        if not self.bids or not self.asks:
            return
        
        current_pos = self.stats.position
        best_bid = self.bids[0][0]
        best_ask = self.asks[0][0]
        
        # Smart strategy analysis
        if abs(current_pos) < 0.001:
            # No position - look for entry opportunities
            spread_bps = (best_ask - best_bid) / self.mid_price * 10000
            
            if spread_bps < 10:  # Tight spread
                self.ui.strategy_label.configure(text="🧠 STRATEGY: TIGHT SPREAD - READY TO ENTER")
                self.ui.opportunity_label.configure(text="🟢 ENTRY OPPORTUNITY", foreground='#00ff88')
                self.ui.add_log(f"🎯 Tight spread ({spread_bps:.1f}bps) - Good entry point")
            else:
                self.ui.strategy_label.configure(text="🧠 STRATEGY: WIDE SPREAD - WAIT")
                self.ui.opportunity_label.configure(text="🟡 WAIT FOR BETTER SPREAD", foreground='#ffaa00')
                
        elif current_pos > 0:  # Long position
            profit_margin = (best_ask - self.stats.avg_entry_price) / self.stats.avg_entry_price * 100
            
            if profit_margin > self.config.min_profit_margin * 100:
                self.ui.strategy_label.configure(text="🧠 STRATEGY: PROFITABLE EXIT - SELL")
                self.ui.opportunity_label.configure(text="🟢 TAKE PROFIT", foreground='#00ff88')
                self.ui.add_log(f"💰 Profit opportunity: {profit_margin:+.3f}%")
                await self.simulate_profit_taking('sell')
            else:
                self.ui.strategy_label.configure(text="🧠 STRATEGY: HOLD LONG - WAIT")
                self.ui.opportunity_label.configure(text="🟡 WAIT FOR PROFIT", foreground='#ffaa00')
                
        else:  # Short position
            profit_margin = (self.stats.avg_entry_price - best_bid) / self.stats.avg_entry_price * 100
            
            if profit_margin > self.config.min_profit_margin * 100:
                self.ui.strategy_label.configure(text="🧠 STRATEGY: PROFITABLE EXIT - BUY")
                self.ui.opportunity_label.configure(text="🟢 TAKE PROFIT", foreground='#00ff88')
                self.ui.add_log(f"💰 Profit opportunity: {profit_margin:+.3f}%")
                await self.simulate_profit_taking('buy')
            else:
                self.ui.strategy_label.configure(text="🧠 STRATEGY: HOLD SHORT - WAIT")
                self.ui.opportunity_label.configure(text="🟡 WAIT FOR PROFIT", foreground='#ffaa00')
    
    async def simulate_profit_taking(self, side: str):
        """Simulate profit taking without real orders"""
        if side == 'sell' and self.stats.position > 0:
            # Simulate selling long position
            sell_price = self.asks[0][0]
            profit = (sell_price - self.stats.avg_entry_price) * self.stats.position
            self.stats.total_profit += profit
            self.stats.successful_hedges += 1
            self.stats.total_trades += 1
            
            self.ui.add_log(f"💰 SIMULATED SELL: {self.stats.position:.3f} ENA @ ${sell_price:.4f}")
            self.ui.add_log(f"💰 SIMULATED PROFIT: ${profit:+.4f}")
            
            # Reset position
            self.stats.position = 0.0
            self.stats.avg_entry_price = 0.0
            
        elif side == 'buy' and self.stats.position < 0:
            # Simulate covering short position
            buy_price = self.bids[0][0]
            profit = (self.stats.avg_entry_price - buy_price) * abs(self.stats.position)
            self.stats.total_profit += profit
            self.stats.successful_hedges += 1
            self.stats.total_trades += 1
            
            self.ui.add_log(f"💰 SIMULATED BUY: {abs(self.stats.position):.3f} ENA @ ${buy_price:.4f}")
            self.ui.add_log(f"💰 SIMULATED PROFIT: ${profit:+.4f}")
            
            # Reset position
            self.stats.position = 0.0
            self.stats.avg_entry_price = 0.0
    
    async def smart_hedging_loop(self):
        """Main smart hedging loop"""
        while self._running and self._hedging:
            try:
                # Update position
                await self.get_positions()
                
                # Smart opportunity analysis is done in process_orderbook
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                self.ui.add_log(f"❌ Hedging loop error: {e}")
                await asyncio.sleep(1)
    
    async def start(self):
        """Start smart hedging bot"""
        self._running = True
        self._hedging = True
        
        # Initial setup
        await self.check_balance()
        await self.get_positions()
        
        # Connect WebSocket
        if not await self.connect_websocket():
            return
        
        # Start tasks
        tasks = [
            asyncio.create_task(self.process_messages()),
            asyncio.create_task(self.smart_hedging_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.ui.add_log(f"❌ Runtime error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop smart hedging bot"""
        self._running = False
        self._hedging = False
        
        if self.ws:
            await self.ws.close()
        
        self.ui.add_log("⏹ Smart hedging bot stopped")

class SmartHedgingApp:
    def __init__(self):
        self.config = SmartHedgingConfig()
        self.stats = SmartHedgingStats()
        self.ui = SmartHedgingUI(self.config, self.stats)
        self.bot = SmartHedgingBot(self.config, self.stats, self.ui)
        
        # Set UI callbacks
        self.ui.start_callback = self.start_hedging
        self.ui.stop_callback = self.stop_hedging
        self.ui.balance_callback = self.check_balance
    
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
    
    def check_balance(self):
        """Check balance"""
        def run_check():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.bot.check_balance())
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_check, daemon=True)
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
    app = SmartHedgingApp()
    app.run()
