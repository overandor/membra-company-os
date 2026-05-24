#!/usr/bin/env python3
import os
"""
BRUTALIST MARKET MAKER
High-frequency market making strategy with advanced analytics and UI
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
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class CascadeAIAssistant:
    """Cascade AI Assistant - Intelligent Trading Decision Maker"""
    
    def __init__(self, config, ui):
        self.config = config
        self.ui = ui
        self.market_analysis = {}
        self.hedge_opportunities = []
        self.risk_assessment = {}
        self.last_analysis_time = 0
        
    def analyze_market_conditions(self, bids, asks, mid_price, position, balance):
        """Cascade AI market analysis for intelligent decisions"""
        current_time = time.time()
        
        if not bids or not asks:
            return {'action': 'WAIT', 'reason': 'No market data'}
        
        # Market structure analysis
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        spread_bps = (best_ask - best_bid) / mid_price * 10000
        
        # Volume and liquidity analysis
        bid_volume = sum(float(bid[1]) for bid in bids[:5])
        ask_volume = sum(float(ask[1]) for ask in asks[:5])
        total_volume = bid_volume + ask_volume
        volume_imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
        
        # Price momentum analysis
        price_pressure = volume_imbalance * 0.5  # Volume-driven pressure
        spread_pressure = max(0, (spread_bps - 5) / 20)  # Spread-driven pressure
        
        # Position risk analysis
        position_risk = abs(position) / self.config.max_hedge_position if self.config.max_hedge_position > 0 else 0
        balance_risk = max(0, (10 - balance) / 10)  # Higher risk when balance < $10
        
        # Cascade AI Decision Logic
        decision = self._make_trading_decision(
            spread_bps, volume_imbalance, position_risk, balance_risk,
            price_pressure, spread_pressure, mid_price, position
        )
        
        # Update analysis cache
        self.market_analysis = {
            'spread_bps': spread_bps,
            'volume_imbalance': volume_imbalance,
            'total_volume': total_volume,
            'price_pressure': price_pressure,
            'spread_pressure': spread_pressure,
            'position_risk': position_risk,
            'balance_risk': balance_risk,
            'decision': decision,
            'timestamp': current_time
        }
        
        return decision
    
    def _make_trading_decision(self, spread_bps, volume_imbalance, position_risk, 
                              balance_risk, price_pressure, spread_pressure, mid_price, position):
        """Cascade AI core decision making logic"""
        
        # Risk assessment
        overall_risk = (position_risk * 0.4 + balance_risk * 0.3 + 
                       max(0, spread_pressure) * 0.2 + abs(volume_imbalance) * 0.1)
        
        # Opportunity scoring
        opportunity_score = 0
        
        # Spread opportunity (higher spread = better opportunity)
        if spread_bps > 3:
            opportunity_score += min(spread_bps / 10, 0.4)
        
        # Volume imbalance opportunity
        if abs(volume_imbalance) > 0.2:
            opportunity_score += min(abs(volume_imbalance) * 0.5, 0.3)
        
        # Price pressure opportunity
        if abs(price_pressure) > 0.1:
            opportunity_score += min(abs(price_pressure) * 0.3, 0.3)
        
        # Cascade AI Decision Tree
        if overall_risk > 0.8:
            return {
                'action': 'REDUCE',
                'reason': f'High risk detected ({overall_risk:.2f}) - reducing exposure',
                'confidence': 0.9,
                'risk_level': 'HIGH'
            }
        
        elif opportunity_score > 0.6 and spread_bps > self.config.min_profit_bps * 2:
            return {
                'action': 'HEDGE_AGGRESSIVE',
                'reason': f'High opportunity ({opportunity_score:.2f}) - aggressive hedging',
                'confidence': min(0.95, 0.7 + opportunity_score * 0.25),
                'opportunity_score': opportunity_score,
                'risk_level': 'MEDIUM'
            }
        
        elif opportunity_score > 0.3 and spread_bps > self.config.min_profit_bps:
            return {
                'action': 'HEDGE_CONSERVATIVE',
                'reason': f'Moderate opportunity ({opportunity_score:.2f}) - conservative hedging',
                'confidence': 0.6 + opportunity_score * 0.2,
                'opportunity_score': opportunity_score,
                'risk_level': 'LOW'
            }
        
        elif position_risk > 0.6:
            return {
                'action': 'WAIT',
                'reason': f'Position risk too high ({position_risk:.2f}) - waiting',
                'confidence': 0.8,
                'risk_level': 'MEDIUM'
            }
        
        else:
            return {
                'action': 'MONITOR',
                'reason': f'Market conditions neutral - monitoring',
                'confidence': 0.5,
                'opportunity_score': opportunity_score,
                'risk_level': 'LOW'
            }
    
    def get_hedge_recommendations(self, decision, bids, asks, mid_price):
        """Get specific hedge recommendations based on AI decision"""
        if decision['action'] not in ['HEDGE_AGGRESSIVE', 'HEDGE_CONSERVATIVE']:
            return []
        
        recommendations = []
        
        # Calculate optimal hedge sizes
        available_balance = 5.56  # From your log
        base_size_usd = self.config.hedge_order_size_usd
        
        if decision['action'] == 'HEDGE_AGGRESSIVE':
            # Aggressive hedging - larger sizes, tighter spreads
            size_multiplier = 1.5
            price_improvement = 0.0002
        else:
            # Conservative hedging - smaller sizes, standard spreads
            size_multiplier = 1.0
            price_improvement = self.config.hedge_price_improvement
        
        # Calculate hedge size
        hedge_usd = min(base_size_usd * size_multiplier, available_balance * 0.3)
        hedge_size = hedge_usd / mid_price
        
        # Get best prices
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        
        # Calculate improved prices
        buy_price = best_bid + price_improvement
        sell_price = best_ask - price_improvement
        
        # Ensure minimum profit
        expected_spread_bps = (sell_price - buy_price) / mid_price * 10000
        if expected_spread_bps < self.config.min_profit_bps:
            # Adjust to minimum profit
            half_spread = self.config.min_profit_bps / 2 / 10000 * mid_price
            buy_price = mid_price - half_spread
            sell_price = mid_price + half_spread
        
        recommendations.append({
            'action': 'PLACE_HEDGE_PAIR',
            'buy_price': buy_price,
            'sell_price': sell_price,
            'size': hedge_size,
            'expected_profit_bps': expected_spread_bps,
            'confidence': decision['confidence'],
            'reason': decision['reason']
        })
        
        return recommendations
    
    def log_ai_decision(self, decision):
        """Log AI decision with detailed reasoning"""
        risk_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}
        action_emoji = {
            'HEDGE_AGGRESSIVE': '🚀',
            'HEDGE_CONSERVATIVE': '🛡️',
            'WAIT': '⏳',
            'MONITOR': '👁️',
            'REDUCE': '⚠️'
        }
        
        emoji = action_emoji.get(decision['action'], '🤖')
        risk_emoji = risk_emoji.get(decision.get('risk_level', 'LOW'), '🟢')
        
        self.ui.add_log(f"🧠 CASCADE AI DECISION:")
        self.ui.add_log(f"   {emoji} Action: {decision['action']}")
        self.ui.add_log(f"   📊 Reason: {decision['reason']}")
        self.ui.add_log(f"   🎯 Confidence: {decision['confidence']:.2f}")
        self.ui.add_log(f"   {risk_emoji} Risk Level: {decision.get('risk_level', 'LOW')}")
        
        if 'opportunity_score' in decision:
            self.ui.add_log(f"   💎 Opportunity Score: {decision['opportunity_score']:.3f}")

class TradingModel:
    """Machine Learning Trading Model for Market Making"""
    
    def __init__(self):
        self.price_history = deque(maxlen=100)
        self.volume_history = deque(maxlen=100)
        self.spread_history = deque(maxlen=100)
        self.imbalance_history = deque(maxlen=100)
        self.volatility_history = deque(maxlen=50)
        self.position_history = deque(maxlen=50)
        
        # Model parameters
        self.lookback_period = 20
        self.volatility_threshold = 0.02  # 2%
        self.trend_strength = 0.0
        self.mean_reversion_signal = 0.0
        self.momentum_signal = 0.0
        self.volatility_signal = 0.0
        self.position_signal = 0.0
        
    def update_market_data(self, mid_price: float, volume: float, spread: float, imbalance: float, position: float):
        """Update model with new market data"""
        self.price_history.append(mid_price)
        self.volume_history.append(volume)
        self.spread_history.append(spread)
        self.imbalance_history.append(imbalance)
        self.position_history.append(position)
        
        # Calculate volatility
        if len(self.price_history) >= 10:
            prices = np.array(list(self.price_history))
            returns = np.diff(np.log(prices))
            volatility = np.std(returns) * np.sqrt(3600)  # Annualized hourly
            self.volatility_history.append(volatility)
    
    def calculate_signals(self) -> Dict:
        """Calculate trading signals using ML-inspired logic"""
        if len(self.price_history) < self.lookback_period:
            return {'signal': 'HOLD', 'confidence': 0.0, 'reason': 'Insufficient data'}
        
        prices = np.array(list(self.price_history))
        volumes = np.array(list(self.volume_history))
        spreads = np.array(list(self.spread_history))
        imbalances = np.array(list(self.imbalance_history))
        positions = np.array(list(self.position_history))
        
        # 1. Mean Reversion Signal
        recent_mean = np.mean(prices[-10:])
        current_price = prices[-1]
        price_deviation = (current_price - recent_mean) / recent_mean
        self.mean_reversion_signal = -np.tanh(price_deviation * 10)  # Stronger signal for larger deviations
        
        # 2. Momentum Signal (short-term trend)
        if len(prices) >= 5:
            short_ma = np.mean(prices[-5:])
            long_ma = np.mean(prices[-20:])
            momentum = (short_ma - long_ma) / long_ma
            self.momentum_signal = np.tanh(momentum * 20)
        
        # 3. Volatility Signal
        if len(self.volatility_history) >= 10:
            recent_vol = np.mean(list(self.volatility_history)[-5:])
            historical_vol = np.mean(list(self.volatility_history)[-20:])
            vol_ratio = recent_vol / historical_vol if historical_vol > 0 else 1.0
            # Reduce trading in high volatility
            self.volatility_signal = 1.0 / (1.0 + vol_ratio)
        
        # 4. Volume Imbalance Signal
        if len(imbalances) >= 5:
            avg_imbalance = np.mean(imbalances[-5:])
            self.volume_signal = np.tanh(avg_imbalance * 5)
        
        # 5. Position Management Signal
        current_pos = positions[-1] if len(positions) > 0 else 0
        self.position_signal = -np.tanh(current_pos * 10)  # Reduce position size when too large
        
        # Combine signals with weights
        signal_strength = (
            self.mean_reversion_signal * 0.3 +
            self.momentum_signal * 0.25 +
            self.volatility_signal * 0.2 +
            getattr(self, 'volume_signal', 0) * 0.15 +
            self.position_signal * 0.1
        )
        
        # Generate trading decision
        confidence = abs(signal_strength)
        
        if signal_strength > 0.3:
            decision = 'BUY'
            reason = f"Strong buy signal ({signal_strength:.3f})"
        elif signal_strength < -0.3:
            decision = 'SELL'
            reason = f"Strong sell signal ({signal_strength:.3f})"
        else:
            decision = 'HOLD'
            reason = f"Neutral signal ({signal_strength:.3f})"
        
        return {
            'signal': decision,
            'confidence': confidence,
            'strength': signal_strength,
            'mean_reversion': self.mean_reversion_signal,
            'momentum': self.momentum_signal,
            'volatility': self.volatility_signal,
            'position_mgmt': self.position_signal,
            'reason': reason
        }
    
    def get_optimal_spread(self, base_spread: float, volatility: float) -> float:
        """Adjust spread based on model predictions"""
        if len(self.volatility_history) < 5:
            return base_spread
        
        recent_vol = np.mean(list(self.volatility_history)[-5:])
        vol_multiplier = 1.0 + min(recent_vol * 50, 2.0)  # Max 3x spread
        
        # Widen spread in high volatility, narrow in low volatility
        return base_spread * vol_multiplier
    
    def should_adjust_inventory(self, current_position: float, max_position: float) -> Tuple[str, float]:
        """Determine if inventory should be adjusted"""
        position_ratio = abs(current_position) / max_position if max_position > 0 else 0
        
        if position_ratio > 0.8:  # Too much inventory
            if current_position > 0:
                return 'REDUCE_LONG', position_ratio
            else:
                return 'REDUCE_SHORT', position_ratio
        elif position_ratio < 0.2:  # Can increase position
            return 'INCREASE', position_ratio
        else:
            return 'MAINTAIN', position_ratio

class MarketMakerConfig:
    def __init__(self):
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        self.symbol = "ENA_USDT"  # Default to ENA/USDT for hedging
        self.order_size_usd = 1.0  # Reduced to $1 for small balance
        self.order_refresh_ms = 100  # 100ms for high TPS
        self.ricci_levels = 5
        self.max_position_usd = 5.0  # Reduced to $5 for small balance
        self.max_orders_per_second = 50
        self.spread_bps = 5.0
        self.inventory_limit = 10.0  # 10 ENA tokens for small balance
        
        # Enhanced hedging mode settings for ENA/USDT
        self.hedging_mode = True  # Enable hedging mode by default
        self.min_profit_bps = 1.5  # Reduced to 1.5 bps for more opportunities
        self.max_hedge_position = 50.0  # Increased to 50 ENA for better hedging
        self.hedge_order_size_usd = 3.0  # Increased to $3 for better hedging
        self.hedge_price_improvement = 0.0001  # Price improvement for best bid/ask
        self.market_sell_threshold = 3.0  # 3 bps threshold for market selling
        self.max_hedge_age_seconds = 300  # Close hedges after 5 minutes max

class TradingStats:
    def __init__(self):
        self.total_trades = 0
        self.total_volume = 0.0
        self.total_pnl = 0.0
        self.fees_paid = 0.0
        self.orders_placed = 0
        self.orders_filled = 0
        self.orders_cancelled = 0
        self.tps_history = deque(maxlen=100)
        self.pnl_history = deque(maxlen=1000)
        self.start_time = time.time()
        self.last_tps_calc = time.time()
        self.orders_this_second = 0
        self.current_tps = 0.0
        
        # Balance tracking
        self.available_balance = 0.0
        self.total_balance = 0.0
        self.unrealized_pnl = 0.0
        self.margin_used = 0.0
        self.margin_free = 0.0
        
        # Hedging statistics
        self.hedge_orders_placed = 0
        self.hedge_orders_filled = 0
        self.hedge_profit_trades = 0
        self.hedge_loss_trades = 0
        self.hedge_total_pnl = 0.0
        self.hedge_fees_paid = 0.0
        self.active_hedges = []  # Track active hedge positions

class MarketMakerUI:
    def __init__(self, config: MarketMakerConfig, stats: TradingStats):
        self.config = config
        self.stats = stats
        self.root = None
        self.running = False
        self.log_queue = deque(maxlen=500)
        
    def create_ui(self):
        self.root = tk.Tk()
        self.root.title("🔥 BRUTALIST MARKET MAKER - HIGH TPS")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a2e')
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#1a1a2e')
        style.configure('TLabel', background='#1a1a2e', foreground='#00ff88', font=('Consolas', 10))
        style.configure('Title.TLabel', font=('Consolas', 14, 'bold'), foreground='#ff6b6b')
        style.configure('Stats.TLabel', font=('Consolas', 11), foreground='#4ecdc4')
        style.configure('TButton', font=('Consolas', 10, 'bold'))
        
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(main_frame, text="⚡ BRUTALIST MARKET MAKER ⚡", style='Title.TLabel')
        header.pack(pady=10)
        
        # Stats frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Left stats
        left_stats = ttk.Frame(stats_frame)
        left_stats.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.tps_label = ttk.Label(left_stats, text="TPS: 0.00", style='Stats.TLabel')
        self.tps_label.pack(anchor=tk.W)
        
        self.orders_label = ttk.Label(left_stats, text="Orders: 0 placed | 0 filled | 0 cancelled", style='Stats.TLabel')
        self.orders_label.pack(anchor=tk.W)
        
        self.volume_label = ttk.Label(left_stats, text="Volume: $0.00", style='Stats.TLabel')
        self.volume_label.pack(anchor=tk.W)
        
        # Right stats
        right_stats = ttk.Frame(stats_frame)
        right_stats.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        
        self.balance_label = ttk.Label(right_stats, text="Balance: $0.00", style='Stats.TLabel')
        self.balance_label.pack(anchor=tk.E)
        
        self.pnl_label = ttk.Label(right_stats, text="PnL: $0.00", style='Stats.TLabel')
        self.pnl_label.pack(anchor=tk.E)
        
        self.position_label = ttk.Label(right_stats, text="Position: 0.00000", style='Stats.TLabel')
        self.position_label.pack(anchor=tk.E)
        
        self.mid_label = ttk.Label(right_stats, text="Mid: $0.00", style='Stats.TLabel')
        self.mid_label.pack(anchor=tk.E)
        
        # Futures wallet details frame
        wallet_frame = ttk.Frame(main_frame)
        wallet_frame.pack(fill=tk.X, pady=5)
        
        self.wallet_label = ttk.Label(wallet_frame, text="💼 FUTURES WALLET", style='Title.TLabel')
        self.wallet_label.pack(side=tk.LEFT, padx=10)
        
        self.available_label = ttk.Label(wallet_frame, text="Available: $0.00", style='Stats.TLabel')
        self.available_label.pack(side=tk.LEFT, padx=20)
        
        self.margin_label = ttk.Label(wallet_frame, text="Margin: $0.00", style='Stats.TLabel')
        self.margin_label.pack(side=tk.LEFT, padx=20)
        
        self.unrealized_label = ttk.Label(wallet_frame, text="Unrealized: $0.00", style='Stats.TLabel')
        self.unrealized_label.pack(side=tk.LEFT, padx=20)
        
        self.equity_label = ttk.Label(wallet_frame, text="Equity: $0.00", style='Stats.TLabel')
        self.equity_label.pack(side=tk.LEFT, padx=20)
        
        # Market data frame
        market_frame = ttk.Frame(main_frame)
        market_frame.pack(fill=tk.X, pady=10)
        
        self.spread_label = ttk.Label(market_frame, text="Spread: 0.00 bps | Imbalance: 0.00%", style='Stats.TLabel')
        self.spread_label.pack()
        
        self.ricci_label = ttk.Label(market_frame, text="Ricci: 0.00 | Z-Score: 0.00 | σ: 0.00 bps", style='Stats.TLabel')
        self.ricci_label.pack()
        
        # AI Model signals frame
        model_frame = ttk.Frame(main_frame)
        model_frame.pack(fill=tk.X, pady=5)
        
        self.model_label = ttk.Label(model_frame, text="🤖 AI TRADING MODEL", style='Title.TLabel')
        self.model_label.pack(side=tk.LEFT, padx=10)
        
        self.signal_label = ttk.Label(model_frame, text="Signal: HOLD", style='Stats.TLabel')
        self.signal_label.pack(side=tk.LEFT, padx=20)
        
        self.confidence_label = ttk.Label(model_frame, text="Confidence: 0.00", style='Stats.TLabel')
        self.confidence_label.pack(side=tk.LEFT, padx=20)
        
        self.strength_label = ttk.Label(model_frame, text="Strength: 0.00", style='Stats.TLabel')
        self.strength_label.pack(side=tk.LEFT, padx=20)
        
        # Hedging mode frame
        hedge_frame = ttk.Frame(main_frame)
        hedge_frame.pack(fill=tk.X, pady=5)
        
        self.hedge_label = ttk.Label(hedge_frame, text="🛡️ HEDGING MODE", style='Title.TLabel')
        self.hedge_label.pack(side=tk.LEFT, padx=10)
        
        self.hedge_status_label = ttk.Label(hedge_frame, text="Status: ACTIVE", style='Stats.TLabel')
        self.hedge_status_label.pack(side=tk.LEFT, padx=20)
        
        self.hedge_pnl_label = ttk.Label(hedge_frame, text="Hedge PnL: $0.00", style='Stats.TLabel')
        self.hedge_pnl_label.pack(side=tk.LEFT, padx=20)
        
        self.hedge_orders_label = ttk.Label(hedge_frame, text="Hedge Orders: 0", style='Stats.TLabel')
        self.hedge_orders_label.pack(side=tk.LEFT, padx=20)
        
        # Order book visualization
        book_frame = ttk.Frame(main_frame)
        book_frame.pack(fill=tk.X, pady=10)
        
        self.bid_canvas = tk.Canvas(book_frame, width=580, height=100, bg='#0d0d1a', highlightthickness=0)
        self.bid_canvas.pack(side=tk.LEFT, padx=5)
        
        self.ask_canvas = tk.Canvas(book_frame, width=580, height=100, bg='#0d0d1a', highlightthickness=0)
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
        
        self.start_btn = ttk.Button(btn_frame, text="▶ START", command=self.on_start)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ STOP", command=self.on_stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.balance_btn = ttk.Button(btn_frame, text="💰 REFRESH BALANCE", command=self.on_refresh_balance)
        self.balance_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(btn_frame, text="⏸ IDLE", style='Stats.TLabel')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        self.running = True
        self.update_ui()
        
    def on_start(self):
        """Start trading with confirmation"""
        # Show warning dialog for real trading
        result = messagebox.askyesno(
            "⚠️ REAL TRADING CONFIRMATION",
            "⚠️ WARNING: This will place REAL orders with your Gate.io account!\n\n"
            "• REAL MONEY will be used\n"
            "• Orders will be placed on the live market\n"
            "• You can lose money\n\n"
            "Do you want to proceed with REAL trading?",
            icon='warning'
        )
        
        if result:
            self.start_btn.configure(state=tk.DISABLED)
            self.stop_btn.configure(state=tk.NORMAL)
            self.status_label.configure(text="🔥 REAL TRADING", foreground='#ff6b6b')
            self.add_log("⚠️ REAL TRADING ACTIVATED - USING REAL MONEY!")
            if hasattr(self, 'start_callback'):
                self.start_callback()
        else:
            self.add_log("❌ Real trading cancelled by user")
    
    def on_stop(self):
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="⏸ STOPPED", foreground='#ff6b6b')
        if hasattr(self, 'stop_callback'):
            self.stop_callback()
    
    def on_refresh_balance(self):
        """Refresh balance callback"""
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
        max_vol = max(max(s for _, s in bids[:10]), max(s for _, s in asks[:10])) if bids and asks else 1
        for i, (price, size) in enumerate(bids[:10]):
            width = (size / max_vol) * 560
            y = i * 10
            self.bid_canvas.create_rectangle(580 - width, y, 580, y + 8, fill='#00ff88', outline='')
            self.bid_canvas.create_text(5, y + 4, text=f"{price:.2f}", fill='#00ff88', anchor='w', font=('Consolas', 7))
        
        # Draw ask bars (red)
        for i, (price, size) in enumerate(asks[:10]):
            width = (size / max_vol) * 560
            y = i * 10
            self.ask_canvas.create_rectangle(0, y, width, y + 8, fill='#ff6b6b', outline='')
            self.ask_canvas.create_text(575, y + 4, text=f"{price:.2f}", fill='#ff6b6b', anchor='e', font=('Consolas', 7))
    
    def update_ui(self):
        if not self.running:
            return
        
        # Update stats labels
        self.tps_label.configure(text=f"TPS: {self.stats.current_tps:.2f}")
        self.orders_label.configure(text=f"Orders: {self.stats.orders_placed} placed | {self.stats.orders_filled} filled | {self.stats.orders_cancelled} cancelled")
        self.volume_label.configure(text=f"Volume: ${self.stats.total_volume:.2f}")
        
        # Update balance
        balance_color = '#00ff88' if self.stats.total_balance >= 0 else '#ff6b6b'
        self.balance_label.configure(text=f"Balance: ${self.stats.total_balance:.2f}", foreground=balance_color)
        
        pnl_color = '#00ff88' if self.stats.total_pnl >= 0 else '#ff6b6b'
        self.pnl_label.configure(text=f"PnL: ${self.stats.total_pnl:.4f}", foreground=pnl_color)
        
        # Update futures wallet details
        available_color = '#00ff88' if self.stats.available_balance >= 0 else '#ff6b6b'
        self.available_label.configure(text=f"Available: ${self.stats.available_balance:.2f}", foreground=available_color)
        
        margin_color = '#ff6b6b' if self.stats.margin_used > 0 else '#00ff88'
        self.margin_label.configure(text=f"Margin: ${self.stats.margin_used:.2f}", foreground=margin_color)
        
        unrealized_color = '#00ff88' if self.stats.unrealized_pnl >= 0 else '#ff6b6b'
        self.unrealized_label.configure(text=f"Unrealized: ${self.stats.unrealized_pnl:.4f}", foreground=unrealized_color)
        
        total_equity = self.stats.available_balance + self.stats.margin_used + self.stats.unrealized_pnl
        equity_color = '#00ff88' if total_equity >= 0 else '#ff6b6b'
        self.equity_label.configure(text=f"Equity: ${total_equity:.2f}", foreground=equity_color)
        
        # Update AI model signals if available
        if hasattr(self, 'model_signal'):
            signal_color = '#00ff88' if self.model_signal.get('signal') == 'BUY' else '#ff6b6b' if self.model_signal.get('signal') == 'SELL' else '#4ecdc4'
            self.signal_label.configure(text=f"Signal: {self.model_signal.get('signal', 'HOLD')}", foreground=signal_color)
            self.confidence_label.configure(text=f"Confidence: {self.model_signal.get('confidence', 0.0):.3f}")
            self.strength_label.configure(text=f"Strength: {self.model_signal.get('strength', 0.0):.3f}")
        
        # Update hedging statistics
        hedge_pnl_color = '#00ff88' if self.stats.hedge_total_pnl >= 0 else '#ff6b6b'
        self.hedge_pnl_label.configure(text=f"Hedge PnL: ${self.stats.hedge_total_pnl:.4f}", foreground=hedge_pnl_color)
        self.hedge_orders_label.configure(text=f"Hedge Orders: {self.stats.hedge_orders_filled}")
        
        # Update hedging status
        if self.config.hedging_mode:
            hedge_status_color = '#00ff88'
            hedge_status = "ACTIVE"
        else:
            hedge_status_color = '#ff6b6b'
            hedge_status = "INACTIVE"
        self.hedge_status_label.configure(text=f"Status: {hedge_status}", foreground=hedge_status_color)
        
        # Update log
        while self.log_queue:
            msg = self.log_queue.popleft()
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
        
        # Schedule next update
        self.root.after(50, self.update_ui)  # 20 FPS UI update
    
    def run(self):
        self.create_ui()
        self.root.mainloop()
    
    def close(self):
        self.running = False
        if self.root:
            self.root.quit()

class HighFrequencyMarketMaker:
    def __init__(self, config: MarketMakerConfig, stats: TradingStats, ui: MarketMakerUI):
        self.config = config
        self.stats = stats
        self.ui = ui
        
        # Trading state
        self._running = False
        self._trading = False
        self.position = 0.0
        self.mid = 0.0
        self.bids = []
        self.asks = []
        
        # Order management
        self.active_orders = {}
        self.order_queue = asyncio.Queue()
        self.last_order_time = 0
        
        # AI Trading Model
        self.model = TradingModel()
        
        # 🧠 CASCADE AI ASSISTANT - INTEGRATED
        self.cascade_ai = CascadeAIAssistant(config, ui)
        
        # Bollinger bands
        self.price_history = deque(maxlen=20)
        
        # Initialize API
        cfg = Configuration(key=config.api_key, secret=config.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
    
    async def get_balance(self):
        """Get detailed futures account balance from Gate.io"""
        try:
            # Get futures account balance
            accounts = self.api.list_futures_accounts(settle='usdt')
            if accounts:
                account = accounts[0] if isinstance(accounts, list) else accounts
                
                # Update detailed balance information
                self.stats.total_balance = float(account.total) if hasattr(account, 'total') else float(account.available) + float(account.locked)
                self.stats.available_balance = float(account.available)
                self.stats.margin_used = float(account.locked) if hasattr(account, 'locked') else 0.0
                self.stats.margin_free = float(account.available)
                
                # Log detailed wallet information
                self.ui.add_log(f"� FUTURES WALLET UPDATE:")
                self.ui.add_log(f"   Total Balance: ${self.stats.total_balance:.2f}")
                self.ui.add_log(f"   Available: ${self.stats.available_balance:.2f}")
                self.ui.add_log(f"   Margin Used: ${self.stats.margin_used:.2f}")
                self.ui.add_log(f"   Unrealized PnL: ${self.stats.unrealized_pnl:.4f}")
                
                # Calculate and log total equity
                total_equity = self.stats.available_balance + self.stats.margin_used + self.stats.unrealized_pnl
                self.ui.add_log(f"   Total Equity: ${total_equity:.2f}")
                
            else:
                self.ui.add_log("❌ No futures account data found")
                
        except Exception as e:
            self.ui.add_log(f"❌ Balance fetch error: {e}")
    
    async def get_positions(self):
        """Get current positions and calculate detailed unrealized PnL"""
        try:
            positions = self.api.list_positions(settle='usdt')
            total_unrealized = 0.0
            total_position = 0.0
            position_details = []
            
            for pos in positions:
                size = float(pos.size)
                if size != 0:
                    pnl = float(pos.unrealised_pnl)
                    entry_price = float(pos.entry_price) if hasattr(pos, 'entry_price') else 0
                    mark_price = float(pos.mark_price) if hasattr(pos, 'mark_price') else 0
                    contract = pos.contract
                    
                    total_unrealized += pnl
                    total_position += size
                    
                    position_details.append({
                        'contract': contract,
                        'size': size,
                        'side': 'LONG' if size > 0 else 'SHORT',
                        'entry_price': entry_price,
                        'mark_price': mark_price,
                        'pnl': pnl,
                        'pnl_percent': ((mark_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                    })
            
            self.stats.unrealized_pnl = total_unrealized
            self.position = total_position
            
            # Log position details
            if position_details:
                self.ui.add_log(f"📊 POSITION DETAILS:")
                for pos in position_details:
                    side_color = "🟢" if pos['side'] == 'LONG' else "🔴"
                    pnl_color = "+" if pos['pnl'] >= 0 else ""
                    self.ui.add_log(f"   {side_color} {pos['contract']}: {pos['side']} {abs(pos['size']):.6f}")
                    self.ui.add_log(f"      Entry: ${pos['entry_price']:.2f} | Mark: ${pos['mark_price']:.2f}")
                    self.ui.add_log(f"      PnL: ${pnl_color}{pos['pnl']:.4f} ({pnl_color}{pos['pnl_percent']:+.2f}%)")
            else:
                self.ui.add_log(f"📊 No open positions")
                
        except Exception as e:
            self.ui.add_log(f"❌ Position fetch error: {e}")
    
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
            
            # Subscribe to trades
            trades_msg = {
                "time": int(time.time()),
                "channel": "futures.trades",
                "event": "subscribe",
                "payload": [self.config.symbol]
            }
            await self.ws.send(json.dumps(trades_msg))
            
            return True
        except Exception as e:
            self.ui.add_log(f"❌ WebSocket error: {e}")
            return False
    
    async def process_messages(self):
        """Process incoming WebSocket messages"""
        try:
            async for message in self.ws:
                if not self._running:
                    break
                
                data = json.loads(message)
                channel = data.get('channel', '')
                
                if channel == 'futures.order_book' and data.get('event') == 'update':
                    await self.process_orderbook(data.get('result', {}))
                elif channel == 'futures.trades' and data.get('event') == 'update':
                    await self.process_trade(data.get('result', []))
                    
        except Exception as e:
            self.ui.add_log(f"❌ Message processing error: {e}")
    
    async def process_orderbook(self, result: Dict):
        """Process order book update"""
        if not result:
            return
        
        # Parse bids and asks
        if 'b' in result:
            self.bids = [[float(p), float(s)] for p, s in result['b']]
        if 'a' in result:
            self.asks = [[float(p), float(s)] for p, s in result['a']]
        
        if self.bids and self.asks:
            self.mid = (self.bids[0][0] + self.asks[0][0]) / 2
            
            # Update volatility
            if self.last_mid > 0:
                ret = abs(math.log(self.mid / self.last_mid)) if self.last_mid else 0.0
                self.sigma_bps = self.sigma_bps * 0.9 + ret * 10000 * 0.1
            self.last_mid = self.mid
            
            # Update price history for Bollinger bands
            self.price_history.append(self.mid)
            
            # Calculate imbalance
            bid_vol = sum(s for _, s in self.bids[:5])
            ask_vol = sum(s for _, s in self.asks[:5])
            total = bid_vol + ask_vol
            self.imbalance = (bid_vol - ask_vol) / total if total > 0 else 0.0
            
            # Calculate other metrics
            self.calculate_metrics()
            
            # Update UI
            self.update_market_ui()
    
    async def process_trade(self, trades: List):
        """Process trade updates"""
        for trade in trades:
            # Update statistics
            self.stats.total_trades += 1
            trade_price = float(trade.get('price', 0))
            trade_size = float(trade.get('size', 0))
            self.stats.total_volume += trade_price * trade_size
            
            # Update TPS
            current_time = time.time()
            if current_time - self.stats.last_tps_calc >= 1.0:
                self.stats.current_tps = self.stats.orders_this_second
                self.stats.tps_history.append(self.stats.current_tps)
                self.stats.orders_this_second = 0
                self.stats.last_tps_calc = current_time
    
    def calculate_metrics(self):
        """Calculate trading metrics"""
        # Z-score
        if len(self.price_history) >= 2:
            prices = list(self.price_history)
            mean = sum(prices) / len(prices)
            variance = sum((p - mean) ** 2 for p in prices) / len(prices)
            std = math.sqrt(variance) if variance > 0 else 1.0
            self.zscore = (self.mid - mean) / std
        
        # Ricci curvature (simplified)
        if len(self.bids) >= self.config.ricci_levels and len(self.asks) >= self.config.ricci_levels:
            bid_vol = sum(s for _, s in self.bids[:self.config.ricci_levels])
            ask_vol = sum(s for _, s in self.asks[:self.config.ricci_levels])
            total = bid_vol + ask_vol
            if total > 0:
                self.ricci = (bid_vol - ask_vol) / total * 100
    
    def update_market_ui(self):
        """Update market data UI"""
        if self.mid > 0:
            spread_bps = (self.asks[0][0] - self.bids[0][0]) / self.mid * 10000 if self.bids and self.asks else 0
            
            self.ui.mid_label.configure(text=f"Mid: ${self.mid:.2f}")
            self.ui.spread_label.configure(text=f"Spread: {spread_bps:.2f} bps | Imbalance: {self.imbalance:+.2%}")
            self.ui.ricci_label.configure(text=f"Ricci: {self.ricci:.2f} | Z-Score: {self.zscore:.2f} | σ: {self.sigma_bps:.2f} bps")
            self.ui.position_label.configure(text=f"Position: {self.position:.5f}")
            
            # Update order book visualization
            self.ui.update_book_viz(self.bids, self.asks)
    
    async def place_order(self, side: str, price: float, size: float):
        """Place REAL limit order with safety checks for small balance"""
        try:
            # Safety checks
            if size <= 0:
                self.ui.add_log(f"❌ Invalid order size: {size}")
                return None
            
            if price <= 0:
                self.ui.add_log(f"❌ Invalid price: ${price}")
                return None
            
            # Check minimum order value (reduced to $1 for small balance)
            order_value = price * size
            if order_value < 1.0:  # $1 minimum (reduced from $10)
                self.ui.add_log(f"❌ Order too small: ${order_value:.2f} (minimum $1)")
                return None
            
            # Create REAL order
            order = gate_api.FuturesOrder(
                contract=self.config.symbol,
                size=size,
                price=price,
                side=side,
                type='limit',
                time_in_force='post_only',  # Maker only
                client_order_id=f"brutalist_mm_{int(time.time() * 1000)}"
            )
            
            # Place the REAL order
            result = self.api.create_futures_order(settle='usdt', order=order)
            self.stats.orders_placed += 1
            self.stats.orders_this_second += 1
            
            # Update position tracking
            if side == 'buy':
                self.position += size
            else:
                self.position -= size
            
            self.ui.add_log(f"🚨 REAL ORDER: {side.upper()} {size:.6f} @ ${price:.2f} (ID: {result.id})")
            self.ui.add_log(f"💰 Value: ${order_value:.2f} | Balance: ${self.stats.available_balance:.2f}")
            
            return result.id
            
        except Exception as e:
            self.ui.add_log(f"❌ ORDER FAILED: {e}")
            return None
    
    async def cancel_order(self, order_id: str):
        """Cancel order"""
        try:
            self.api.cancel_futures_order(settle='usdt', order_id=order_id)
            self.stats.orders_cancelled += 1
            self.ui.add_log(f"📉 Cancelled order: {order_id}")
        except Exception as e:
            self.ui.add_log(f"❌ Cancel error: {e}")
    
    async def cancel_all_orders(self):
        """Cancel all open orders"""
        try:
            orders = self.api.list_futures_orders(settle='usdt', status='open')
            for order in orders:
                await self.cancel_order(order.id)
        except Exception as e:
            self.ui.add_log(f"❌ Cancel all error: {e}")
    
    async def place_hedge_order(self, side: str, price: float, size: float):
        """Place a hedge order for profit taking"""
        try:
            # Create hedge order
            order = gate_api.FuturesOrder(
                contract=self.config.symbol,
                size=size,
                price=price,
                side=side,
                type='limit',
                time_in_force='post_only',
                client_order_id=f"hedge_{int(time.time() * 1000)}"
            )
            
            # Place the hedge order
            result = self.api.create_futures_order(settle='usdt', order=order)
            self.stats.hedge_orders_placed += 1
            
            # Track hedge position
            hedge_info = {
                'order_id': result.id,
                'side': side,
                'price': price,
                'size': size,
                'timestamp': time.time(),
                'status': 'active'
            }
            self.stats.active_hedges.append(hedge_info)
            
            self.ui.add_log(f"🛡️ HEDGE PLACED: {side.upper()} {size:.6f} ENA @ ${price:.4f} (ID: {result.id})")
            
            return result.id
            
        except Exception as e:
            self.ui.add_log(f"❌ Hedge order failed: {e}")
            return None
    
    async def check_hedge_profitability(self):
        """Enhanced hedge profitability check with market selling and age-based closing"""
        if not self.bids or not self.asks:
            return
        
        current_bid = float(self.bids[0][0])
        current_ask = float(self.asks[0][0])
        current_mid = (current_bid + current_ask) / 2
        current_time = time.time()
        
        profitable_hedges = []
        aged_hedges = []
        
        for hedge in self.stats.active_hedges:
            if hedge['status'] != 'active':
                continue
            
            hedge_price = hedge['price']
            hedge_side = hedge['side']
            hedge_size = hedge['size']
            hedge_age = current_time - hedge['timestamp']
            
            # Calculate potential profit
            if hedge_side == 'buy':
                # We bought at hedge_price, can sell at current_bid
                profit_per_unit = current_bid - hedge_price
                total_profit = profit_per_unit * hedge_size
                profit_bps = profit_per_unit / hedge_price * 10000
                close_price = current_bid
            else:
                # We sold at hedge_price, can buy back at current_ask
                profit_per_unit = hedge_price - current_ask
                total_profit = profit_per_unit * hedge_size
                profit_bps = profit_per_unit / hedge_price * 10000
                close_price = current_ask
            
            # Check if profit meets minimum threshold
            min_profit = self.config.min_profit_bps / 10000 * hedge_price * hedge_size
            
            # Market selling logic - close immediately if profit is good
            if profit_bps >= self.config.market_sell_threshold:
                profitable_hedges.append({
                    'hedge': hedge,
                    'profit': total_profit,
                    'close_price': close_price,
                    'reason': f'PROFITABLE ({profit_bps:.1f} bps)',
                    'use_market': True
                })
            elif total_profit > min_profit:
                profitable_hedges.append({
                    'hedge': hedge,
                    'profit': total_profit,
                    'close_price': close_price,
                    'reason': f'MIN PROFIT ({profit_bps:.1f} bps)',
                    'use_market': False
                })
            
            # Age-based closing - close old hedges to free up capital
            elif hedge_age > self.config.max_hedge_age_seconds:
                aged_hedges.append({
                    'hedge': hedge,
                    'profit': total_profit,
                    'close_price': close_price,
                    'reason': f'AGED ({hedge_age:.0f}s old)',
                    'use_market': True
                })
        
        # Close profitable hedges first
        for hedge_info in profitable_hedges:
            await self.close_hedge_position(hedge_info)
        
        # Close aged hedges
        for hedge_info in aged_hedges:
            await self.close_hedge_position(hedge_info)
    
    async def close_hedge_position(self, hedge_info):
        """Close a hedge position with enhanced logging"""
        hedge = hedge_info['hedge']
        profit = hedge_info['profit']
        close_price = hedge_info['close_price']
        reason = hedge_info['reason']
        use_market = hedge_info.get('use_market', False)
        
        try:
            close_side = 'sell' if hedge['side'] == 'buy' else 'buy'
            
            # Determine order type based on urgency
            order_type = 'market' if use_market else 'limit'
            
            if order_type == 'limit':
                # For limit orders, place slightly better price
                if close_side == 'sell':
                    close_price = close_price - 0.0001  # Slightly lower for quick fill
                else:
                    close_price = close_price + 0.0001  # Slightly higher for quick fill
            
            close_order = gate_api.FuturesOrder(
                contract=self.config.symbol,
                size=hedge['size'],
                price=close_price if order_type == 'limit' else None,
                side=close_side,
                type=order_type,
                time_in_force='ioc' if order_type == 'limit' else None,  # Immediate or Cancel for limit
                client_order_id=f"close_hedge_{int(time.time() * 1000)}"
            )
            
            result = self.api.create_futures_order(settle='usdt', order=close_order)
            
            # Update statistics
            self.stats.hedge_orders_filled += 2  # One for hedge, one for close
            self.stats.hedge_total_pnl += profit
            self.stats.total_pnl += profit
            
            if profit > 0:
                self.stats.hedge_profit_trades += 1
            else:
                self.stats.hedge_loss_trades += 1
            
            # Mark hedge as closed
            hedge['status'] = 'closed'
            hedge['close_price'] = close_price
            hedge['profit'] = profit
            hedge['close_reason'] = reason
            
            profit_color = "+" if profit >= 0 else ""
            order_type_text = "MARKET" if use_market else "LIMIT"
            
            self.ui.add_log(f"💰 ENA HEDGE CLOSED ({reason}):")
            self.ui.add_log(f"   {order_type_text} {close_side.upper()} {hedge['size']:.6f} @ ${close_price:.4f}")
            self.ui.add_log(f"   Profit: ${profit_color}{profit:.4f} | Hedge PnL: ${profit_color}{self.stats.hedge_total_pnl:.4f}")
            
        except Exception as e:
            self.ui.add_log(f"❌ Failed to close hedge ({reason}): {e}")
    
    async def cascade_ai_hedging_strategy(self):
        """🧠 CASCADE AI-DRIVEN HEDGING STRATEGY"""
        if not self.bids or not self.asks:
            return
        
        # 🧠 CASCADE AI MARKET ANALYSIS
        ai_decision = self.cascade_ai.analyze_market_conditions(
            self.bids, self.asks, self.mid, self.position, self.stats.available_balance
        )
        
        # Log AI decision
        self.cascade_ai.log_ai_decision(ai_decision)
        
        # Get AI recommendations
        recommendations = self.cascade_ai.get_hedge_recommendations(
            ai_decision, self.bids, self.asks, self.mid
        )
        
        # Execute AI recommendations
        for rec in recommendations:
            if rec['action'] == 'PLACE_HEDGE_PAIR':
                # Check position limits
                current_hedge_size = sum(h['size'] for h in self.stats.active_hedges if h['status'] == 'active')
                
                if current_hedge_size < self.config.max_hedge_position:
                    # Place AI-recommended hedge pair
                    buy_result = await self.place_hedge_order('buy', rec['buy_price'], rec['size'])
                    await asyncio.sleep(0.1)  # Small delay
                    sell_result = await self.place_hedge_order('sell', rec['sell_price'], rec['size'])
                    
                    if buy_result and sell_result:
                        self.ui.add_log(f"🧠 AI HEDGE PAIR EXECUTED:")
                        self.ui.add_log(f"   🎯 Confidence: {rec['confidence']:.2f}")
                        self.ui.add_log(f"   💰 Expected Profit: {rec['expected_profit_bps']:.1f} bps")
                        self.ui.add_log(f"   📊 Reason: {rec['reason']}")
                    elif buy_result:
                        self.ui.add_log(f"🧠 PARTIAL AI HEDGE: Buy {rec['size']:.6f} @ ${rec['buy_price']:.4f}")
                    elif sell_result:
                        self.ui.add_log(f"🧠 PARTIAL AI HEDGE: Sell {rec['size']:.6f} @ ${rec['sell_price']:.4f}")
                else:
                    self.ui.add_log(f"⚠️ AI: Max hedge position reached ({current_hedge_size:.2f} ENA)")
        
        # Handle AI risk management decisions
        if ai_decision['action'] == 'REDUCE':
            self.ui.add_log(f"🧠 AI RISK MANAGEMENT: {ai_decision['reason']}")
            # Could implement position reduction logic here
        elif ai_decision['action'] == 'WAIT':
            self.ui.add_log(f"🧠 AI WAITING: {ai_decision['reason']}")
        elif ai_decision['action'] == 'MONITOR':
            # Silent monitoring - no action needed
            pass
    
    async def trading_loop(self):
        """Main trading loop with AI model-driven decisions and hedging"""
        balance_update_counter = 0
        hedge_counter = 0
        
        while self._running and self._trading:
            try:
                # Update balance every 30 seconds
                balance_update_counter += 1
                if balance_update_counter >= 300:  # 30 seconds at 100ms intervals
                    await self.get_balance()
                    await self.get_positions()
                    balance_update_counter = 0
                
                # Rate limiting
                current_time = time.time()
                if current_time - self.last_order_time < self.config.order_refresh_ms / 1000:
                    await asyncio.sleep(0.01)
                    continue
                
                # 🧠 CASCADE AI HEDGING STRATEGY - Priority #1
                if self.config.hedging_mode:
                    hedge_counter += 1
                    
                    # Check for profitable hedge closures every 2 seconds
                    if hedge_counter % 20 == 0:
                        await self.check_hedge_profitability()
                    
                    # 🧠 CASCADE AI-DRIVEN HEDGING every 5 seconds
                    if hedge_counter % 50 == 0:
                        await self.cascade_ai_hedging_strategy()
                
                # Cancel old orders (non-hedge orders)
                await self.cancel_all_orders()
                
                # AI MARKET MAKING STRATEGY - Priority #2 (if not fully hedged)
                current_hedge_size = sum(h['size'] for h in self.stats.active_hedges if h['status'] == 'active')
                
                # Only do market making if we have room for more positions
                if current_hedge_size < self.config.max_hedge_position * 0.7:  # Leave 30% room for hedges
                    if self.bids and self.asks:
                        # Update model with current market data
                        volume = sum(float(bid[1]) for bid in self.bids[:5]) + sum(float(ask[1]) for ask in self.asks[:5])
                        spread = (float(self.asks[0][0]) - float(self.bids[0][0])) / self.mid * 10000
                        imbalance = (sum(float(bid[1]) for bid in self.bids[:5]) - sum(float(ask[1]) for ask in self.asks[:5])) / volume
                        
                        self.model.update_market_data(self.mid, volume, spread, imbalance, self.position)
                        
                        # Get AI trading signals
                        model_signals = self.model.calculate_signals()
                        self.ui.model_signal = model_signals  # Update UI with model signals
                        
                        # Log model decision
                        self.ui.add_log(f"🤖 AI Signal: {model_signals['signal']} (Confidence: {model_signals['confidence']:.3f})")
                        self.ui.add_log(f"   Reason: {model_signals['reason']}")
                        
                        # Get AI-adjusted spread
                        ai_spread = self.model.get_optimal_spread(self.config.spread_bps, spread)
                        
                        # Calculate bid/ask prices
                        bid_price = self.mid - ai_spread / 10000 * self.mid
                        ask_price = self.mid + ai_spread / 10000 * self.mid
                        
                        # Check inventory recommendations
                        inventory_action, position_ratio = self.model.should_adjust_inventory(self.position, self.config.inventory_limit)
                        
                        # Calculate order size based on available balance and AI signals
                        available_usd = self.stats.available_balance
                        if available_usd > 2.0:  # Minimum $2 to trade
                            # Adjust order size based on model confidence
                            base_order_size = min(self.config.order_size_usd, available_usd * 0.2)
                            confidence_multiplier = 0.5 + (model_signals['confidence'] * 0.5)  # 0.5 to 1.0 based on confidence
                            order_size_usd = base_order_size * confidence_multiplier
                            order_size = order_size_usd / self.mid
                            
                            # AI-driven order placement (reduced size when hedging is active)
                            mm_size_multiplier = 0.5 if self.config.hedging_mode else 1.0
                            
                            if model_signals['signal'] == 'BUY' and model_signals['confidence'] > 0.4:
                                if inventory_action in ['INCREASE', 'MAINTAIN']:
                                    buy_result = await self.place_order('buy', bid_price, order_size * mm_size_multiplier)
                                    if buy_result:
                                        self.ui.add_log(f"🟢 AI BUY: {order_size * mm_size_multiplier:.6f} ENA @ ${bid_price:.4f} (${order_size_usd * mm_size_multiplier:.2f})")
                                        self.ui.add_log(f"   AI Confidence: {model_signals['confidence']:.3f}")
                            
                            elif model_signals['signal'] == 'SELL' and model_signals['confidence'] > 0.4:
                                if inventory_action in ['INCREASE', 'MAINTAIN']:
                                    sell_result = await self.place_order('sell', ask_price, order_size * mm_size_multiplier)
                                    if sell_result:
                                        self.ui.add_log(f"🔴 AI SELL: {order_size * mm_size_multiplier:.6f} ENA @ ${ask_price:.4f} (${order_size_usd * mm_size_multiplier:.2f})")
                                        self.ui.add_log(f"   AI Confidence: {model_signals['confidence']:.3f}")
                            
                            # Market making mode (neutral signal)
                            elif model_signals['signal'] == 'HOLD':
                                # Place balanced orders for market making
                                if inventory_action != 'REDUCE_LONG':
                                    buy_result = await self.place_order('buy', bid_price, order_size * 0.5 * mm_size_multiplier)
                                    if buy_result:
                                        self.ui.add_log(f"🤖 MM BUY: {order_size * 0.5 * mm_size_multiplier:.6f} ENA @ ${bid_price:.4f}")
                                
                                if inventory_action != 'REDUCE_SHORT':
                                    sell_result = await self.place_order('sell', ask_price, order_size * 0.5 * mm_size_multiplier)
                                    if sell_result:
                                        self.ui.add_log(f"🤖 MM SELL: {order_size * 0.5 * mm_size_multiplier:.6f} ENA @ ${ask_price:.4f}")
                            
                            else:
                                self.ui.add_log(f"⚠️ AI Signal too weak: {model_signals['confidence']:.3f} (need >0.4)")
                        else:
                            self.ui.add_log(f"⚠️ LOW BALANCE: ${available_usd:.2f} (need $2+)")
                            await asyncio.sleep(10)  # Wait longer if balance is too low
                            continue
                
                self.last_order_time = current_time
                await asyncio.sleep(self.config.order_refresh_ms / 1000)
                
            except Exception as e:
                self.ui.add_log(f"❌ AI Trading loop error: {e}")
                await asyncio.sleep(1)
    
    async def start(self):
        """Start market making with real-time updates"""
        self._running = True
        self._trading = True
        
        # Initial balance fetch
        await self.get_balance()
        await self.get_positions()
        
        # Connect WebSocket
        if not await self.connect_websocket():
            return
        
        # Start tasks
        tasks = [
            asyncio.create_task(self.process_messages()),
            asyncio.create_task(self.trading_loop()),
            asyncio.create_task(self.real_time_update_loop())  # NEW: Real-time updates every second
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.ui.add_log(f"❌ Runtime error: {e}")
        finally:
            await self.stop()
    
    async def real_time_update_loop(self):
        """Real-time update loop - runs every second"""
        update_counter = 0
        
        while self._running:
            try:
                update_counter += 1
                
                # Update model and metrics every second
                if self.bids and self.asks and self.mid > 0:
                    # Calculate current market metrics
                    volume = sum(float(bid[1]) for bid in self.bids[:5]) + sum(float(ask[1]) for ask in self.asks[:5])
                    spread = (float(self.asks[0][0]) - float(self.bids[0][0])) / self.mid * 10000
                    imbalance = (sum(float(bid[1]) for bid in self.bids[:5]) - sum(float(ask[1]) for ask in self.asks[:5])) / volume
                    
                    # Update AI model with latest data
                    self.model.update_market_data(self.mid, volume, spread, imbalance, self.position)
                    
                    # Get fresh AI signals
                    model_signals = self.model.calculate_signals()
                    self.ui.model_signal = model_signals
                    
                    # Update UI with fresh data
                    self.ui.mid_label.configure(text=f"Mid: ${self.mid:.2f}")
                    self.ui.spread_label.configure(text=f"Spread: {spread:.2f} bps | Imbalance: {imbalance:+.2%}")
                    
                    # Update AI model display
                    signal_color = '#00ff88' if model_signals['signal'] == 'BUY' else '#ff6b6b' if model_signals['signal'] == 'SELL' else '#4ecdc4'
                    self.ui.signal_label.configure(text=f"Signal: {model_signals['signal']}", foreground=signal_color)
                    self.ui.confidence_label.configure(text=f"Confidence: {model_signals['confidence']:.3f}")
                    self.ui.strength_label.configure(text=f"Strength: {model_signals['strength']:.3f}")
                    
                    # Log detailed model analysis every 10 seconds
                    if update_counter % 10 == 0:
                        self.ui.add_log(f"🔄 Real-time Update #{update_counter}:")
                        self.ui.add_log(f"   📊 Mid: ${self.mid:.2f} | Spread: {spread:.1f}bps | Vol: {volume:.0f}")
                        self.ui.add_log(f"   🤖 AI: {model_signals['signal']} (Conf: {model_signals['confidence']:.3f})")
                        self.ui.add_log(f"   📈 MeanRev: {model_signals['mean_reversion']:.3f} | Mom: {model_signals['momentum']:.3f}")
                        self.ui.add_log(f"   🌊 Volatility: {model_signals['volatility']:.3f} | PosMgmt: {model_signals['position_mgmt']:.3f}")
                
                # Update balance every 30 seconds (already handled in trading loop)
                # Update positions every 15 seconds
                if update_counter % 15 == 0:
                    await self.get_positions()
                
                # Update order book visualization every 2 seconds
                if update_counter % 2 == 0:
                    self.ui.update_book_viz(self.bids, self.asks)
                
                # Wait exactly 1 second
                await asyncio.sleep(1)
                
            except Exception as e:
                self.ui.add_log(f"❌ Real-time update error: {e}")
                await asyncio.sleep(1)
    
    async def stop(self):
        """Stop market making"""
        self._running = False
        self._trading = False
        
        if self.ws:
            await self.ws.close()
        
        await self.cancel_all_orders()
        self.ui.add_log("⏹ Market maker stopped")

class BrutalistMarketMakerApp:
    def __init__(self):
        self.config = MarketMakerConfig()
        self.stats = TradingStats()
        self.ui = MarketMakerUI(self.config, self.stats)
        self.market_maker = HighFrequencyMarketMaker(self.config, self.stats, self.ui)
        
        # Set UI callbacks
        self.ui.start_callback = self.start_trading
        self.ui.stop_callback = self.stop_trading
        self.ui.balance_callback = self.refresh_balance
    
    def start_trading(self):
        """Start trading in separate thread"""
        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.market_maker.start())
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
    
    def stop_trading(self):
        """Stop trading"""
        # Create a new event loop for the stop call
        def run_stop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.market_maker.stop())
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_stop, daemon=True)
        thread.start()
    
    def refresh_balance(self):
        """Refresh balance in separate thread"""
        def run_balance():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.refresh_balance_async())
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_balance, daemon=True)
        thread.start()
    
    async def refresh_balance_async(self):
        """Async balance refresh"""
        await self.market_maker.get_balance()
        await self.market_maker.get_positions()
    
    def run(self):
        """Run the application"""
        try:
            # Initial balance fetch
            self.refresh_balance()
            
            # Start UI in main thread
            self.ui.run()
            
        except KeyboardInterrupt:
            print("\n⏹ Application interrupted by user")
            if hasattr(self.ui, 'add_log'):
                self.ui.add_log("⏹ Application interrupted")
        except Exception as e:
            print(f"❌ Application error: {e}")
            if hasattr(self.ui, 'add_log'):
                self.ui.add_log(f"❌ Application error: {e}")
        finally:
            if hasattr(self.ui, 'close'):
                self.ui.close()

if __name__ == "__main__":
    app = BrutalistMarketMakerApp()
    app.run()
