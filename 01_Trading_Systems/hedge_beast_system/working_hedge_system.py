#!/usr/bin/env python3
import os
"""
WORKING HEDGE SYSTEM - BEST BID/ASK STRATEGY
Actually places hedge orders at best bid and ask prices
Sells at best ask when profitable, buys at best bid when profitable
"""

import asyncio
import websockets
import json
import time
import logging
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict, List, Optional
from datetime import datetime
import gate_api
from gate_api import ApiClient, Configuration, FuturesApi

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class HedgeConfig:
    """Configuration for ultra-safe hedging with $6 balance"""
    
    def __init__(self):
        # API Credentials
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        self.symbol = "ENA_USDT"
        
        # Ultra-Conservative Risk Management for $6 Balance
        self.max_order_value_usd = 0.05  # Maximum $0.05 per order
        self.max_total_exposure_usd = 0.15  # Maximum $0.15 total exposure
        self.min_balance_usd = 2.00  # Stop if balance below $2
        self.emergency_stop_balance_usd = 1.00  # Emergency stop at $1
        
        # Hedging Parameters
        self.min_profit_bps = 10.0  # Minimum 10 bps profit (0.1%)
        self.max_hedge_age_seconds = 60  # Close hedges after 1 minute
        self.max_concurrent_hedges = 2  # Maximum 2 hedge pairs
        
        # Trading Settings
        self.price_improvement = 0.00001  # Minimal price improvement
        self.order_refresh_ms = 1000  # Check every second

class HedgeStats:
    """Statistics tracking"""
    
    def __init__(self):
        self.orders_placed = 0
        self.orders_filled = 0
        self.hedge_pairs_placed = 0
        self.hedge_pairs_closed = 0
        self.total_pnl = 0.0
        self.active_hedges = []
        self.start_time = time.time()

class HedgeUI:
    """Simple UI for hedge system"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛡️ Working Hedge System - Best Bid/Ask")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0a0a')
        
        # Create UI elements
        self.create_widgets()
        
    def create_widgets(self):
        """Create UI widgets"""
        # Title
        title = tk.Label(self.root, text="🛡️ HEDGE SYSTEM - BEST BID/ASK", 
                        font=('Arial', 16, 'bold'), fg='#00ff88', bg='#0a0a0a')
        title.pack(pady=10)
        
        # Info frame
        info_frame = tk.Frame(self.root, bg='#1a1a1a')
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.balance_label = tk.Label(info_frame, text="Balance: $0.00", 
                                     font=('Courier', 12), fg='#00ff88', bg='#1a1a1a')
        self.balance_label.pack(side='left', padx=10)
        
        self.pnl_label = tk.Label(info_frame, text="PnL: $0.00", 
                                 font=('Courier', 12), fg='#00ff88', bg='#1a1a1a')
        self.pnl_label.pack(side='left', padx=10)
        
        # Status frame
        status_frame = tk.Frame(self.root, bg='#1a1a1a')
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_label = tk.Label(status_frame, text="🟢 READY", 
                                    font=('Courier', 12), fg='#00ff88', bg='#1a1a1a')
        self.status_label.pack(side='left', padx=10)
        
        self.hedge_count_label = tk.Label(status_frame, text="Active Hedges: 0", 
                                          font=('Courier', 12), fg='#00ff88', bg='#1a1a1a')
        self.hedge_count_label.pack(side='left', padx=10)
        
        # Control buttons
        button_frame = tk.Frame(self.root, bg='#1a1a1a')
        button_frame.pack(fill='x', padx=10, pady=10)
        
        self.start_button = tk.Button(button_frame, text="🚀 START HEDGING", 
                                     command=self.start_trading,
                                     bg='#00ff00', fg='#000000', font=('Arial', 12, 'bold'),
                                     width=15)
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = tk.Button(button_frame, text="⏹️ STOP HEDGING", 
                                    command=self.stop_trading,
                                    bg='#ff0000', fg='#ffffff', font=('Arial', 12, 'bold'),
                                    width=15, state='disabled')
        self.stop_button.pack(side='left', padx=5)
        
        # Log area
        log_frame = tk.Frame(self.root, bg='#1a1a1a')
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        tk.Label(log_frame, text="📝 ACTIVITY LOG", 
                font=('Arial', 12, 'bold'), fg='#ff0040', bg='#1a1a1a').pack()
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80,
                                                  bg='#0a0a0a', fg='#00ff88', 
                                                  font=('Courier', 9))
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Clear button
        tk.Button(log_frame, text="🗑️ CLEAR LOG", command=self.clear_log,
                 bg='#ff6b6b', fg='#ffffff', font=('Arial', 10, 'bold')).pack(pady=5)
    
    def add_log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Limit log size
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 500:
            self.log_text.delete(1.0, f"{len(lines)-500}.0")
    
    def clear_log(self):
        """Clear log"""
        self.log_text.delete(1.0, tk.END)
    
    def start_trading(self):
        """Start trading"""
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="🟢 HEDGING ACTIVE", fg='#00ff00')
        self.add_log("🚀 Hedging started")
    
    def stop_trading(self):
        """Stop trading"""
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="🔴 STOPPED", fg='#ff4444')
        self.add_log("⏹️ Hedging stopped")
    
    def update_stats(self, stats, balance):
        """Update statistics display"""
        self.balance_label.config(text=f"Balance: ${balance:.2f}")
        self.pnl_label.config(text=f"PnL: ${stats.total_pnl:.4f}")
        
        # Color code PnL
        pnl_color = '#00ff00' if stats.total_pnl >= 0 else '#ff4444'
        self.pnl_label.config(fg=pnl_color)
        
        active_hedges = len([h for h in stats.active_hedges if h['status'] == 'active'])
        self.hedge_count_label.config(text=f"Active Hedges: {active_hedges}")
    
    def run(self):
        """Run the UI"""
        self.root.mainloop()

class HedgeSystem:
    """Main hedge system with best bid/ask strategy"""
    
    def __init__(self):
        self.config = HedgeConfig()
        self.stats = HedgeStats()
        self.ui = HedgeUI()
        
        # Trading state
        self.running = False
        self.trading = False
        self.ws = None
        
        # Market data
        self.bids = []
        self.asks = []
        self.mid_price = 0.0
        self.balance = 0.0
        
        # Initialize API
        cfg = Configuration(key=self.config.api_key, secret=self.config.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
        
        # UI callbacks
        self.ui.start_button.config(command=self.start_trading)
        self.ui.stop_button.config(command=self.stop_trading)
    
    async def connect_websocket(self):
        """Connect to WebSocket"""
        try:
            self.ws = await websockets.connect("wss://fx-ws.gateio.ws/v4/ws/usdt")
            self.ui.add_log("✅ WebSocket connected")
            
            # Subscribe to order book
            subscribe_msg = {
                "time": int(time.time()),
                "channel": "futures.order_book",
                "event": "subscribe",
                "payload": [self.config.symbol, 5, 0]
            }
            await self.ws.send(json.dumps(subscribe_msg))
            self.ui.add_log(f"📊 Subscribed to {self.config.symbol} order book")
            return True
            
        except Exception as e:
            self.ui.add_log(f"❌ WebSocket error: {e}")
            return False
    
    async def get_balance(self):
        """Get account balance"""
        try:
            account = self.api.get_futures_account(settle='usdt')
            self.balance = float(account.available)
            
            # Check balance limits
            if self.balance < self.config.emergency_stop_balance_usd:
                self.ui.add_log(f"🚨 EMERGENCY STOP: Balance ${self.balance:.2f} below ${self.config.emergency_stop_balance_usd}")
                self.trading = False
                self.ui.stop_trading()
            elif self.balance < self.config.min_balance_usd:
                self.ui.add_log(f"⚠️ Balance ${self.balance:.2f} below minimum ${self.config.min_balance_usd}")
                self.trading = False
                self.ui.stop_trading()
            
            return self.balance
            
        except Exception as e:
            self.ui.add_log(f"❌ Balance error: {e}")
            return 0.0
    
    async def place_hedge_order(self, side: str, price: float, size: float) -> Optional[str]:
        """Place a hedge order"""
        try:
            # Check order value
            order_value = size * price
            if order_value > self.config.max_order_value_usd:
                self.ui.add_log(f"⚠️ Order value ${order_value:.4f} exceeds maximum ${self.config.max_order_value_usd}")
                return None
            
            # Check total exposure
            current_exposure = sum(h['size'] * h['price'] for h in self.stats.active_hedges if h['status'] == 'active')
            if current_exposure + order_value > self.config.max_total_exposure_usd:
                self.ui.add_log(f"⚠️ Total exposure would exceed maximum ${self.config.max_total_exposure_usd}")
                return None
            
            order = gate_api.FuturesOrder(
                contract=self.config.symbol,
                size=size,
                price=price,
                side=side,
                type='limit',
                time_in_force='post_only',
                client_order_id=f"hedge_{int(time.time() * 1000)}"
            )
            
            result = self.api.create_futures_order(settle='usdt', order=order)
            self.stats.orders_placed += 1
            
            hedge_info = {
                'order_id': result.id,
                'side': side,
                'price': price,
                'size': size,
                'timestamp': time.time(),
                'status': 'active'
            }
            self.stats.active_hedges.append(hedge_info)
            
            self.ui.add_log(f"🛡️ HEDGE PLACED: {side.upper()} {size:.6f} @ ${price:.6f}")
            return result.id
            
        except Exception as e:
            self.ui.add_log(f"❌ Hedge order failed: {e}")
            return None
    
    async def place_hedge_pair(self):
        """Place a hedge pair at best bid/ask"""
        if not self.bids or not self.asks:
            return
        
        best_bid = float(self.bids[0][0])
        best_ask = float(self.asks[0][0])
        
        # Calculate order size based on balance
        max_size_usd = min(self.config.max_order_value_usd, self.balance * 0.05)
        buy_size = max_size_usd / best_ask
        sell_size = max_size_usd / best_bid
        
        # Place buy order slightly above best bid
        buy_price = best_bid + self.config.price_improvement
        
        # Place sell order slightly below best ask  
        sell_price = best_ask - self.config.price_improvement
        
        # Check if profitable
        expected_spread_bps = (sell_price - buy_price) / best_bid * 10000
        if expected_spread_bps < self.config.min_profit_bps:
            self.ui.add_log(f"📊 Spread {expected_spread_bps:.1f} bps below minimum {self.config.min_profit_bps} bps")
            return
        
        # Place the hedge pair
        buy_order_id = await self.place_hedge_order('buy', buy_price, buy_size)
        await asyncio.sleep(0.1)
        sell_order_id = await self.place_hedge_order('sell', sell_price, sell_size)
        
        if buy_order_id and sell_order_id:
            self.stats.hedge_pairs_placed += 1
            self.ui.add_log(f"🚀 HEDGE PAIR PLACED: Expected profit {expected_spread_bps:.1f} bps")
    
    async def check_hedge_profitability(self):
        """Check and close profitable hedges"""
        if not self.bids or not self.asks:
            return
        
        current_bid = float(self.bids[0][0])
        current_ask = float(self.asks[0][0])
        current_time = time.time()
        
        for hedge in self.stats.active_hedges[:]:
            if hedge['status'] != 'active':
                continue
            
            hedge_price = hedge['price']
            hedge_side = hedge['side']
            hedge_size = hedge['size']
            hedge_age = current_time - hedge['timestamp']
            
            # Calculate profit
            if hedge_side == 'buy':
                # We bought, now we can sell at current bid
                profit_per_unit = current_bid - hedge_price
                total_profit = profit_per_unit * hedge_size
                profit_bps = profit_per_unit / hedge_price * 10000
                close_price = current_bid
                close_side = 'sell'
            else:
                # We sold, now we can buy back at current ask
                profit_per_unit = hedge_price - current_ask
                total_profit = profit_per_unit * hedge_size
                profit_bps = profit_per_unit / hedge_price * 10000
                close_price = current_ask
                close_side = 'buy'
            
            # Close if profitable or too old
            if profit_bps >= self.config.min_profit_bps or hedge_age > self.config.max_hedge_age_seconds:
                await self.close_hedge_position(hedge, total_profit, close_price, close_side, 
                                               f"PROFITABLE ({profit_bps:.1f} bps)" if profit_bps >= self.config.min_profit_bps else f"AGED ({hedge_age:.0f}s)")
    
    async def close_hedge_position(self, hedge, profit, close_price, close_side, reason):
        """Close a hedge position"""
        try:
            close_order = gate_api.FuturesOrder(
                contract=self.config.symbol,
                size=hedge['size'],
                side=close_side,
                type='market',
                client_order_id=f"close_hedge_{int(time.time() * 1000)}"
            )
            
            result = self.api.create_futures_order(settle='usdt', order=close_order)
            
            # Update statistics
            self.stats.orders_filled += 2
            self.stats.hedge_pairs_closed += 1
            self.stats.total_pnl += profit
            
            # Mark as closed
            hedge['status'] = 'closed'
            hedge['profit'] = profit
            
            profit_color = "+" if profit >= 0 else ""
            self.ui.add_log(f"💰 HEDGE CLOSED ({reason}): ${profit_color}{profit:.4f}")
            
        except Exception as e:
            self.ui.add_log(f"❌ Failed to close hedge: {e}")
    
    async def process_messages(self):
        """Process WebSocket messages"""
        try:
            async for message in self.ws:
                if not self.running:
                    break
                
                data = json.loads(message)
                
                if data.get('channel') == 'futures.order_book' and data.get('event') == 'update':
                    bids = data.get('result', {}).get('bids', [])
                    asks = data.get('result', {}).get('asks', [])
                    
                    if bids and asks:
                        self.bids = bids
                        self.asks = asks
                        self.mid_price = (float(bids[0][0]) + float(asks[0][0])) / 2
                        
        except Exception as e:
            self.ui.add_log(f"❌ Message processing error: {e}")
    
    async def trading_loop(self):
        """Main trading loop"""
        balance_counter = 0
        hedge_counter = 0
        
        while self.running:
            try:
                # Update balance every 30 seconds
                balance_counter += 1
                if balance_counter >= 300:
                    await self.get_balance()
                    balance_counter = 0
                
                # Check if trading is enabled
                if not self.trading:
                    await asyncio.sleep(1)
                    continue
                
                # Check hedge profitability every 2 seconds
                hedge_counter += 1
                if hedge_counter % 20 == 0:
                    await self.check_hedge_profitability()
                
                # Place new hedge pairs every 5 seconds
                if hedge_counter % 50 == 0:
                    active_hedges = len([h for h in self.stats.active_hedges if h['status'] == 'active'])
                    if active_hedges < self.config.max_concurrent_hedges:
                        await self.place_hedge_pair()
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.ui.add_log(f"❌ Trading loop error: {e}")
                await asyncio.sleep(1)
    
    async def ui_update_loop(self):
        """Update UI loop"""
        while self.running:
            try:
                self.ui.update_stats(self.stats, self.balance)
                await asyncio.sleep(1)
            except Exception as e:
                log.error(f"UI update error: {e}")
                await asyncio.sleep(1)
    
    def start_trading(self):
        """Start trading"""
        self.trading = True
        self.ui.start_trading()
    
    def stop_trading(self):
        """Stop trading"""
        self.trading = False
        self.ui.stop_trading()
    
    async def start(self):
        """Start the hedge system"""
        self.running = True
        
        # Initial balance check
        await self.get_balance()
        
        # Connect WebSocket
        if not await self.connect_websocket():
            self.ui.add_log("❌ Failed to connect WebSocket")
            return
        
        # Start all tasks
        tasks = [
            asyncio.create_task(self.process_messages()),
            asyncio.create_task(self.trading_loop()),
            asyncio.create_task(self.ui_update_loop()),
            asyncio.create_task(self.ui.run())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.ui.add_log(f"❌ Runtime error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the hedge system"""
        self.running = False
        self.trading = False
        
        if self.ws:
            await self.ws.close()
        
        self.ui.add_log("⏹️ System stopped")

async def main():
    """Main entry point"""
    print("🛡️ WORKING HEDGE SYSTEM - BEST BID/ASK STRATEGY")
    print("💰 Ultra-conservative risk management for $6 balance")
    print("🎯 Places orders at best bid/ask prices")
    print("=" * 60)
    
    system = HedgeSystem()
    
    try:
        await system.start()
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
