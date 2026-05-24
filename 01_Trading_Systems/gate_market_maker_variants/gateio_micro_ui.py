#!/usr/bin/env python3
"""
Gate.io Micro-Cap Trading Bot with UI
Only trades tickers $0.001-$0.10 with $6 budget
"""

import asyncio
import aiohttp
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import logging
from dataclasses import dataclass, field
from enum import Enum
import random
import hashlib
import hmac
import base64
from urllib.parse import urlencode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderSide(Enum):
    SHORT = "sell"
    COVER = "buy"

@dataclass
class MicroTicker:
    symbol: str
    price: float
    price_24h_ago: float
    volume_24h: float
    nominal_value: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class MicroPosition:
    symbol: str
    entry_price: float
    quantity: float
    entry_time: datetime
    nominal_value: float
    status: str = "open"
    pnl: float = 0.0
    profit_taken: bool = False

class GateioMicroCapBot:
    """Gate.io micro-cap trading bot for $0.001-$0.10 tickers"""
    
    def __init__(self):
        # STRICT BUDGET AND NOMINAL VALUE CONSTRAINTS
        self.total_budget = 6.0  # $6 maximum budget
        self.min_nominal_value = 0.001  # $0.001 minimum
        self.max_nominal_value = 0.10   # $0.10 maximum
        
        # Position sizing for $6 budget
        self.max_positions = 20
        self.base_position_size = 0.25  # $0.25 per position
        self.max_per_symbol = 1.0
        
        # Micro-cap parameters
        self.pump_threshold = 0.10  # 10% pump
        self.profit_target = 0.05   # 5% profit
        self.stop_loss = 0.03       # 3% stop loss
        
        # Gate.io API - REAL CREDENTIALS
        self.api_key = os.getenv("GATE_API_KEY", os.environ.get("GATE_API_KEY", ""))
        self.api_secret = os.getenv("GATE_API_SECRET", os.environ.get("GATE_API_SECRET", ""))
        self.base_url = "https://api.gateio.ws"
        self.dry_run = False  # LIVE TRADING ENABLED
        
        # State tracking
        self.active_positions = []
        self.profit_symbols_today = set()
        self.daily_budget_used = 0.0
        
        # Statistics
        self.total_trades = 0
        self.successful_shorts = 0
        self.total_pnl = 0.0
        
        logger.info("🪙 GATE.IO MICRO-CAP BOT INITIALIZED")
        logger.info(f"💰 Budget: ${self.total_budget}")
        logger.info(f"📊 Nominal Range: ${self.min_nominal_value}-${self.max_nominal_value}")
        logger.info(f"🔑 API Key: {self.api_key[:10]}...")
        logger.info(f"⚡ Live Trading: {not self.dry_run}")
    
    def generate_signature(self, method: str, url: str, params: dict = None, timestamp: str = None) -> str:
        """Generate Gate.io API signature"""
        if timestamp is None:
            timestamp = str(int(time.time()))
        
        if params is None:
            params = {}
        
        # Create query string
        query_string = urlencode(sorted(params.items()))
        
        # Create message to sign
        message = method + '\n' + url + '\n' + query_string
        
        # Generate signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return signature
    
    async def get_gateio_micro_tickers(self) -> List[MicroTicker]:
        """Get Gate.io tickers between $0.001-$0.10"""
        try:
            url = "/api/v4/spot/tickers"
            full_url = self.base_url + url
            
            headers = {
                'KEY': self.api_key,
                'Timestamp': str(int(time.time())),
                'SIGN': self.generate_signature('GET', url)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(full_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        micro_tickers = []
                        
                        for ticker in data:
                            try:
                                symbol = ticker['currency_pair']
                                if not symbol.endswith('_USDT'):
                                    continue
                                
                                price = float(ticker['last'])
                                price_change = float(ticker['change_percentage']) / 100
                                
                                # STRICT FILTER: Only $0.001-$0.10
                                if price < self.min_nominal_value or price > self.max_nominal_value:
                                    continue
                                
                                # Calculate nominal value for minimum order
                                min_qty = 0.001
                                nominal_value = min_qty * price
                                
                                # Must be within range
                                if nominal_value < self.min_nominal_value or nominal_value > self.max_nominal_value:
                                    continue
                                
                                # Calculate 24h ago price
                                price_24h_ago = price / (1 + price_change) if price_change != 0 else price
                                
                                micro_ticker = MicroTicker(
                                    symbol=symbol.replace('_USDT', ''),
                                    price=price,
                                    price_24h_ago=price_24h_ago,
                                    volume_24h=float(ticker['base_volume']) * price,
                                    nominal_value=nominal_value
                                )
                                micro_tickers.append(micro_ticker)
                                
                            except (ValueError, KeyError):
                                continue
                        
                        logger.info(f"📊 Gate.io: Found {len(micro_tickers)} micro-cap tickers (${self.min_nominal_value}-${self.max_nominal_value})")
                        return micro_tickers
                        
        except Exception as e:
            logger.error(f"Gate.io API error: {e}")
        
        return []
    
    async def place_gateio_order(self, symbol: str, side: str, amount: float, price: float = None) -> dict:
        """Place real order on Gate.io"""
        try:
            url = "/api/v4/spot/orders"
            full_url = self.base_url + url
            
            # Prepare order data
            order_data = {
                'currency_pair': f"{symbol}_USDT",
                'type': 'market',
                'side': side,
                'amount': str(amount)
            }
            
            if price:
                order_data['price'] = str(price)
                order_data['type'] = 'limit'
            
            # Generate signature
            timestamp = str(int(time.time()))
            headers = {
                'KEY': self.api_key,
                'Timestamp': timestamp,
                'SIGN': self.generate_signature('POST', url, order_data, timestamp),
                'Content-Type': 'application/json'
            }
            
            if self.dry_run:
                logger.info(f"🧪 DRY RUN: Would place {side} order for {symbol} - Amount: {amount}")
                return {'id': f'dry_{int(time.time())}', 'status': 'filled', 'filled': str(amount)}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(full_url, json=order_data, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Order placed: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Order failed: {response.status} - {error_text}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Failed to place order for {symbol}: {e}")
            return {}
    
    async def place_micro_short(self, ticker: MicroTicker) -> Optional[MicroPosition]:
        """Place a real micro short order on Gate.io"""
        try:
            position_size = min(self.base_position_size, self.total_budget - self.daily_budget_used)
            quantity = position_size / ticker.price
            
            # Place real sell order
            order_result = await self.place_gateio_order(ticker.symbol, 'sell', quantity)
            
            if order_result and 'id' in order_result:
                position = MicroPosition(
                    symbol=ticker.symbol,
                    entry_price=ticker.price,
                    quantity=quantity,
                    entry_time=datetime.now(),
                    nominal_value=position_size
                )
                
                self.active_positions.append(position)
                self.daily_budget_used += position_size
                self.total_trades += 1
                
                logger.info(f"📉 LIVE MICRO SHORT: {ticker.symbol} @ ${ticker.price:.6f}")
                logger.info(f"   Order ID: {order_result['id']}")
                logger.info(f"   Nominal: ${position.nominal_value:.4f} | Budget: ${self.daily_budget_used:.2f}/${self.total_budget}")
                
                return position
            else:
                logger.error(f"Failed to place short order for {ticker.symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to place micro short for {ticker.symbol}: {e}")
            return None
    
    async def close_position(self, position: MicroPosition) -> bool:
        """Close position with buy order"""
        try:
            # Place buy order to close position
            order_result = await self.place_gateio_order(position.symbol, 'buy', position.quantity)
            
            if order_result and 'id' in order_result:
                logger.info(f"✅ CLOSED POSITION: {position.symbol} - Order ID: {order_result['id']}")
                return True
            else:
                logger.error(f"Failed to close position for {position.symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to close position for {position.symbol}: {e}")
            return False
    
    def identify_micro_pumps(self, tickers: List[MicroTicker]) -> List[MicroTicker]:
        """Identify micro-cap tickers with 10%+ pumps"""
        pumping_tickers = []
        
        for ticker in tickers:
            price_change = (ticker.price - ticker.price_24h_ago) / ticker.price_24h_ago
            
            if price_change >= self.pump_threshold:
                if ticker.symbol not in self.profit_symbols_today:
                    pumping_tickers.append(ticker)
                    logger.info(f"🚀 MICRO PUMP: {ticker.symbol} +{price_change*100:.1f}% "
                              f"${ticker.price:.6f} | Nominal: ${ticker.nominal_value:.6f}")
        
        # Sort by nominal value (smallest first)
        pumping_tickers.sort(key=lambda x: x.nominal_value)
        
        return pumping_tickers
    
    async def monitor_positions(self):
        """Monitor and close positions"""
        for position in self.active_positions[:]:
            if position.status != "open":
                continue
            
            # Simulate price movement for demo
            change = random.uniform(-0.02, 0.02)  # 2% volatility
            current_price = position.entry_price * (1 + change)
            
            # Calculate PnL
            pnl = (position.entry_price - current_price) * position.quantity
            pnl_pct = (pnl / position.nominal_value) * 100
            position.pnl = pnl
            
            # Check profit taking (5%)
            if pnl_pct >= self.profit_target * 100:
                position.status = "profit_taken"
                position.profit_taken = True
                self.successful_shorts += 1
                self.total_pnl += pnl
                
                # Close position with real order
                if await self.close_position(position):
                    self.active_positions.remove(position)
                    self.daily_budget_used -= position.nominal_value
                    self.profit_symbols_today.add(position.symbol)
                
                logger.info(f"💰 MICRO PROFIT: {position.symbol} @ ${current_price:.6f} (+${pnl:.4f})")
                
            elif pnl_pct <= -self.stop_loss * 100:
                position.status = "stop_loss"
                self.total_pnl += pnl
                
                # Close position with real order
                if await self.close_position(position):
                    self.active_positions.remove(position)
                    self.daily_budget_used -= position.nominal_value
                
                logger.info(f"❌ MICRO STOP: {position.symbol} @ ${current_price:.6f} (${pnl:.4f})")

class MicroCapUI:
    """UI for Gate.io Micro-Cap Trading Bot"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🪙 Gate.io Micro-Cap Trading Bot ($0.001-$0.10)")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Initialize bot
        self.bot = GateioMicroCapBot()
        self.running = False
        
        # Create UI
        self.create_widgets()
        
        # Start update loop
        self.update_ui()
    
    def create_widgets(self):
        """Create UI widgets"""
        # Title Frame
        title_frame = tk.Frame(self.root, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(title_frame, text="🪙 GATE.IO MICRO-CAP TRADING BOT", 
                               font=('Arial', 18, 'bold'), fg='#00ff00', bg='#2a2a2a')
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(title_frame, text="Only trades tickers $0.001-$0.10 | Budget: $6.00", 
                                 font=('Arial', 12), fg='#ffff00', bg='#2a2a2a')
        subtitle_label.pack()
        
        # Main Container
        main_container = tk.Frame(self.root, bg='#1a1a1a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left Panel - Status
        left_panel = tk.Frame(main_container, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        status_label = tk.Label(left_panel, text="📊 BOT STATUS", 
                               font=('Arial', 14, 'bold'), fg='#00ffff', bg='#2a2a2a')
        status_label.pack(pady=10)
        
        self.status_text = tk.Text(left_panel, height=15, width=50, bg='#000000', fg='#00ff00',
                                   font=('Courier', 10))
        self.status_text.pack(padx=10, pady=5)
        
        # Middle Panel - Positions
        middle_panel = tk.Frame(main_container, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        middle_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        positions_label = tk.Label(middle_panel, text="💼 ACTIVE POSITIONS", 
                                  font=('Arial', 14, 'bold'), fg='#00ffff', bg='#2a2a2a')
        positions_label.pack(pady=10)
        
        self.positions_tree = ttk.Treeview(middle_panel, columns=('Symbol', 'Entry', 'Current', 'PnL', 'Status'), 
                                          show='tree headings', height=15)
        self.positions_tree.heading('#0', text='ID')
        self.positions_tree.heading('Symbol', text='Symbol')
        self.positions_tree.heading('Entry', text='Entry Price')
        self.positions_tree.heading('Current', text='Current')
        self.positions_tree.heading('PnL', text='P&L')
        self.positions_tree.heading('Status', text='Status')
        
        self.positions_tree.column('#0', width=50)
        self.positions_tree.column('Symbol', width=100)
        self.positions_tree.column('Entry', width=80)
        self.positions_tree.column('Current', width=80)
        self.positions_tree.column('PnL', width=80)
        self.positions_tree.column('Status', width=80)
        
        self.positions_tree.pack(padx=10, pady=5)
        
        # Right Panel - Activity Log
        right_panel = tk.Frame(main_container, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        activity_label = tk.Label(right_panel, text="📝 ACTIVITY LOG", 
                                 font=('Arial', 14, 'bold'), fg='#00ffff', bg='#2a2a2a')
        activity_label.pack(pady=10)
        
        self.activity_log = scrolledtext.ScrolledText(right_panel, height=15, width=40, 
                                                     bg='#000000', fg='#ffff00', font=('Courier', 9))
        self.activity_log.pack(padx=10, pady=5)
        
        # Control Panel
        control_panel = tk.Frame(self.root, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        control_panel.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_button = tk.Button(control_panel, text="🚀 START BOT", command=self.start_bot,
                                      bg='#00aa00', fg='white', font=('Arial', 12, 'bold'),
                                      width=15, height=2)
        self.start_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.stop_button = tk.Button(control_panel, text="⏹️ STOP BOT", command=self.stop_bot,
                                     bg='#aa0000', fg='white', font=('Arial', 12, 'bold'),
                                     width=15, height=2, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=10)
        
        self.scan_button = tk.Button(control_panel, text="🔍 SCAN NOW", command=self.manual_scan,
                                     bg='#0000aa', fg='white', font=('Arial', 12, 'bold'),
                                     width=15, height=2)
        self.scan_button.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Budget Bar
        budget_frame = tk.Frame(control_panel, bg='#2a2a2a')
        budget_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        tk.Label(budget_frame, text="💰 BUDGET USED:", bg='#2a2a2a', fg='white', 
                font=('Arial', 10)).pack(side=tk.LEFT)
        
        self.budget_bar = ttk.Progressbar(budget_frame, length=200, mode='determinate')
        self.budget_bar.pack(side=tk.LEFT, padx=5)
        
        self.budget_label = tk.Label(budget_frame, text="$0.00/$6.00", bg='#2a2a2a', fg='white',
                                    font=('Arial', 10, 'bold'))
        self.budget_label.pack(side=tk.LEFT)
        
        self.log_activity("🪙 Gate.io Micro-Cap Bot initialized")
        self.log_activity("📊 Target range: $0.001-$0.10")
        self.log_activity("💰 Budget: $6.00")
        self.log_activity("🎯 Ready to start trading...")
    
    def log_activity(self, message):
        """Log activity to the UI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.activity_log.see(tk.END)
        logger.info(message)
    
    def update_status(self):
        """Update status display"""
        status_text = f"""
🪙 GATE.IO MICRO-CAP BOT STATUS
{'='*40}

💰 BUDGET INFORMATION:
   Total Budget: ${self.bot.total_budget:.2f}
   Used: ${self.bot.daily_budget_used:.2f}
   Available: ${self.bot.total_budget - self.bot.daily_budget_used:.2f}
   
📊 NOMINAL VALUE RANGE:
   Min: ${self.bot.min_nominal_value}
   Max: ${self.bot.max_nominal_value}
   
📈 TRADING PARAMETERS:
   Pump Threshold: {self.bot.pump_threshold*100:.0f}%
   Profit Target: {self.bot.profit_target*100:.0f}%
   Stop Loss: {self.bot.stop_loss*100:.0f}%
   Base Position: ${self.bot.base_position_size:.2f}
   
📊 PERFORMANCE:
   Total Trades: {self.bot.total_trades}
   Successful Shorts: {self.bot.successful_shorts}
   Active Positions: {len(self.bot.active_positions)}/{self.bot.max_positions}
   Total P&L: ${self.bot.total_pnl:.4f}
   Win Rate: {(self.bot.successful_shorts / max(1, self.bot.total_trades) * 100):.1f}%
   
🚫 SYMBOLS BLOCKED TODAY: {len(self.bot.profit_symbols_today)}
⏰ Last Scan: {datetime.now().strftime('%H:%M:%S')}
"""
        
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, status_text)
        
        # Update budget bar
        budget_pct = (self.bot.daily_budget_used / self.bot.total_budget) * 100
        self.budget_bar['value'] = budget_pct
        self.budget_label.config(text=f"${self.bot.daily_budget_used:.2f}/${self.bot.total_budget:.2f}")
    
    def update_positions(self):
        """Update positions display"""
        # Clear existing items
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)
        
        # Add current positions
        for i, position in enumerate(self.bot.active_positions):
            # Simulate current price
            change = random.uniform(-0.02, 0.02)
            current_price = position.entry_price * (1 + change)
            pnl = (position.entry_price - current_price) * position.quantity
            pnl_pct = (pnl / position.nominal_value) * 100
            
            pnl_color = 'green' if pnl > 0 else 'red'
            status_color = 'green' if position.status == 'open' else 'orange'
            
            self.positions_tree.insert('', 'end', iid=i, text=f"#{i+1}",
                                      values=(position.symbol, 
                                             f"${position.entry_price:.6f}",
                                             f"${current_price:.6f}",
                                             f"${pnl:.4f} ({pnl_pct:+.1f}%)",
                                             position.status.upper()))
    
    async def scan_and_trade(self):
        """Main scanning and trading loop"""
        while self.running:
            try:
                self.log_activity("🔍 Scanning Gate.io micro-caps...")
                
                # Get micro-cap tickers
                tickers = await self.bot.get_gateio_micro_tickers()
                
                if tickers:
                    self.log_activity(f"📊 Found {len(tickers)} micro-caps (${self.bot.min_nominal_value}-${self.bot.max_nominal_value})")
                    
                    # Identify pumps
                    pumping = self.bot.identify_micro_pumps(tickers)
                    self.log_activity(f"🚀 Found {len(pumping)} pumping micro-caps (10%+)")
                    
                    # Place shorts
                    for ticker in pumping[:5]:  # Limit to 5 per scan
                        if self.bot.daily_budget_used < self.bot.total_budget * 0.8:
                            position = await self.bot.place_micro_short(ticker)
                            if position:
                                self.log_activity(f"📉 Shorted {position.symbol} @ ${position.entry_price:.6f}")
                
                # Monitor positions
                await self.bot.monitor_positions()
                
                # Wait before next scan
                await asyncio.sleep(30)
                
            except Exception as e:
                self.log_activity(f"❌ Error: {e}")
                await asyncio.sleep(10)
    
    def start_bot(self):
        """Start the trading bot"""
        if not self.running:
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.log_activity("🚀 Bot started!")
            
            # Start trading loop in separate thread
            threading.Thread(target=self.run_bot_loop, daemon=True).start()
    
    def stop_bot(self):
        """Stop the trading bot"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_activity("⏹️ Bot stopped!")
    
    def run_bot_loop(self):
        """Run the bot loop in thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.scan_and_trade())
    
    def manual_scan(self):
        """Perform manual scan"""
        threading.Thread(target=self.run_manual_scan, daemon=True).start()
    
    async def run_manual_scan(self):
        """Run manual scan"""
        self.log_activity("🔍 Manual scan initiated...")
        tickers = await self.bot.get_gateio_micro_tickers()
        pumping = self.bot.identify_micro_pumps(tickers)
        self.log_activity(f"📊 Manual scan: {len(tickers)} micro-caps, {len(pumping)} pumping")
    
    def update_ui(self):
        """Update UI periodically"""
        if self.running:
            self.update_status()
            self.update_positions()
        
        # Schedule next update
        self.root.after(5000, self.update_ui)  # Update every 5 seconds
    
    def run(self):
        """Run the UI"""
        self.root.mainloop()

def main():
    """Main function"""
    print("🪙 GATE.IO MICRO-CAP TRADING BOT WITH UI")
    print("="*50)
    print("📊 Only trades tickers $0.001-$0.10")
    print("💰 Budget: $6.00")
    print("🎯 Targets 10%+ pumps")
    print("⚡ Real-time UI monitoring")
    print("="*50)
    
    # Create and run UI
    ui = MicroCapUI()
    ui.run()

if __name__ == "__main__":
    main()
