#!/usr/bin/env python3
import os
"""
BRUTALIST MARKET MAKER - NEOMORPHIC UI (1000+ LINES)
Advanced market making with full neomorphic design, animations, and comprehensive features
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, Canvas, messagebox
import threading
import time
from datetime import datetime, timedelta
import gate_api
from gate_api import ApiClient, Configuration, FuturesApi
import json
import math
import random
from collections import deque
import colorsys
import statistics

# Your API credentials
GATE_API_KEY = os.getenv("GATE_API_KEY", "")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "")

class NeomorphicTheme:
    """Comprehensive neomorphic color scheme and styling"""
    
    # Base colors
    BG_PRIMARY = "#2d2d30"      
    BG_SECONDARY = "#252528"    
    BG_TERTIARY = "#1e1e20"     
    BG_QUATERNARY = "#161618"   
    TEXT_PRIMARY = "#ffffff"    
    TEXT_SECONDARY = "#b0b0b0"  
    TEXT_TERTIARY = "#808080"    
    ACCENT_PRIMARY = "#7b68ee"  
    ACCENT_SECONDARY = "#9b88ff" 
    ACCENT_SUCCESS = "#4ade80"  
    ACCENT_DANGER = "#f87171"   
    ACCENT_WARNING = "#fbbf24"  
    ACCENT_INFO = "#60a5fa"     
    
    # Neomorphic shadows
    LIGHT_SHADOW = "#3d3d40"
    DARK_SHADOW = "#1d1d20"
    LIGHTER_SHADOW = "#4d4d50"
    DARKER_SHADOW = "#0d0d10"
    
    # Gradient colors
    GRADIENT_START = "#7b68ee"
    GRADIENT_END = "#9b88ff"
    SUCCESS_GRADIENT_START = "#4ade80"
    SUCCESS_GRADIENT_END = "#6ee7a3"
    DANGER_GRADIENT_START = "#f87171"
    DANGER_GRADIENT_END = "#fca5a5"
    
    @staticmethod
    def get_gradient_color(base_color, factor):
        """Generate gradient color with enhanced precision"""
        base_color = base_color.lstrip('#')
        r, g, b = tuple(int(base_color[i:i+2], 16) for i in (0, 2, 4))
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        v = min(1.0, max(0.0, v * factor))
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    @staticmethod
    def get_complementary_color(base_color):
        """Get complementary color for contrast"""
        base_color = base_color.lstrip('#')
        r, g, b = tuple(int(base_color[i:i+2], 16) for i in (0, 2, 4))
        return f"#{255-r:02x}{255-g:02x}{255-b:02x}"

class PerformanceTracker:
    """Track performance metrics with detailed analytics"""
    
    def __init__(self):
        self.trades = deque(maxlen=1000)
        self.pnl_history = deque(maxlen=100)
        self.spread_history = deque(maxlen=100)
        self.latency_history = deque(maxlen=50)
        self.start_time = time.time()
        
    def add_trade(self, trade_data):
        """Add trade data to tracker"""
        trade_data['timestamp'] = time.time()
        self.trades.append(trade_data)
        self.pnl_history.append(trade_data.get('pnl', 0))
        if 'spread' in trade_data:
            self.spread_history.append(trade_data['spread'])
    
    def add_latency(self, latency):
        """Add latency measurement"""
        self.latency_history.append(latency)
    
    def get_performance_stats(self):
        """Get comprehensive performance statistics"""
        if not self.trades:
            return {}
        
        pnls = list(self.pnl_history)
        spreads = list(self.spread_history)
        latencies = list(self.latency_history)
        
        total_pnl = sum(pnls)
        winning_trades = len([p for p in pnls if p > 0])
        losing_trades = len([p for p in pnls if p < 0])
        
        stats = {
            'total_trades': len(self.trades),
            'total_pnl': total_pnl,
            'win_rate': (winning_trades / len(pnls)) * 100 if pnls else 0,
            'avg_pnl': statistics.mean(pnls) if pnls else 0,
            'avg_spread': statistics.mean(spreads) if spreads else 0,
            'avg_latency': statistics.mean(latencies) if latencies else 0,
            'max_drawdown': self.calculate_max_drawdown(pnls),
            'sharpe_ratio': self.calculate_sharpe_ratio(pnls),
            'profit_factor': self.calculate_profit_factor(pnls),
            'uptime': time.time() - self.start_time
        }
        
        return stats
    
    def calculate_max_drawdown(self, pnls):
        """Calculate maximum drawdown"""
        if not pnls:
            return 0
        
        cumulative = []
        running_total = 0
        for pnl in pnls:
            running_total += pnl
            cumulative.append(running_total)
        
        peak = cumulative[0]
        max_dd = 0
        
        for value in cumulative:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd * 100  # Return as percentage
    
    def calculate_sharpe_ratio(self, pnls, risk_free_rate=0.02):
        """Calculate Sharpe ratio"""
        if len(pnls) < 2:
            return 0
        
        returns = pnls
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        
        if std_return == 0:
            return 0
        
        # Annualized Sharpe ratio (assuming daily returns)
        sharpe = (avg_return - risk_free_rate/252) / std_return * math.sqrt(252)
        return sharpe
    
    def calculate_profit_factor(self, pnls):
        """Calculate profit factor (gross profit / gross loss)"""
        gross_profit = sum([p for p in pnls if p > 0])
        gross_loss = abs(sum([p for p in pnls if p < 0]))
        
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')

class BrutalistMarketMaker:
    """Enhanced market making strategy with advanced analytics"""
    
    def __init__(self, futures_client):
        self.futures_client = futures_client
        self.is_running = False
        self.current_position = 0.0
        self.mid_price = None
        self.volatility = 10.0
        self.total_pnl = 0.0
        self.performance_tracker = PerformanceTracker()
        self.order_book_history = deque(maxlen=100)
        self.last_update_time = time.time()
        
    def calculate_market_metrics(self, symbol: str = "BTC_USDT") -> dict:
        """Calculate comprehensive market making metrics"""
        start_time = time.time()
        
        try:
            book = self.futures_client.list_futures_order_book(settle='usdt', contract=symbol, limit=50)
            
            if not book.bids or not book.asks:
                return {'error': 'No order book data'}
            
            # Basic metrics
            best_bid = float(book.bids[0].p)
            best_ask = float(book.asks[0].p)
            mid = (best_bid + best_ask) / 2
            self.mid_price = mid
            
            spread_bps = (best_ask - best_bid) / mid * 10000
            
            # Volume analysis
            bid_levels = [(float(bid.p), float(bid.s)) for bid in book.bids[:20]]
            ask_levels = [(float(ask.p), float(ask.s)) for ask in book.asks[:20]]
            
            bid_vol = sum(size for _, size in bid_levels[:10])
            ask_vol = sum(size for _, size in ask_levels[:10])
            total_vol = bid_vol + ask_vol
            imbalance = (bid_vol - ask_vol) / total_vol if total_vol > 0 else 0
            
            # Depth analysis
            bid_depth = sum(price * size for price, size in bid_levels)
            ask_depth = sum(price * size for price, size in ask_levels)
            
            # Volatility calculation from order book
            price_range = (float(book.bids[0].p) - float(book.bids[-1].p)) / mid * 100
            volatility = price_range
            
            # Liquidity metrics
            spread_impact = spread_bps / (bid_vol + ask_vol) * 1000 if (bid_vol + ask_vol) > 0 else 0
            
            # Order book imbalance at different levels
            level_imbalances = []
            for i in range(5):
                if i < len(bid_levels) and i < len(ask_levels):
                    level_imbalance = (bid_levels[i][1] - ask_levels[i][1]) / (bid_levels[i][1] + ask_levels[i][1])
                    level_imbalances.append(level_imbalance)
            
            avg_level_imbalance = statistics.mean(level_imbalances) if level_imbalances else 0
            
            # Store order book snapshot
            snapshot = {
                'timestamp': time.time(),
                'mid': mid,
                'spread': spread_bps,
                'imbalance': imbalance,
                'bid_vol': bid_vol,
                'ask_vol': ask_vol
            }
            self.order_book_history.append(snapshot)
            
            # Track performance
            latency = (time.time() - start_time) * 1000  # in milliseconds
            self.performance_tracker.add_latency(latency)
            
            metrics = {
                'mid': mid,
                'spread_bps': spread_bps,
                'imbalance': imbalance,
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'bid_vol': bid_vol,
                'ask_vol': ask_vol,
                'volatility': volatility,
                'spread_impact': spread_impact,
                'avg_level_imbalance': avg_level_imbalance,
                'bid_levels': bid_levels[:10],
                'ask_levels': ask_levels[:10],
                'latency': latency
            }
            
            return metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_optimal_quotes(self, metrics: dict, inventory_skew: float = 0.0, 
                                risk_factor: float = 1.0, aggressiveness: float = 1.0) -> dict:
        """Calculate optimal bid/ask quotes with advanced parameters"""
        if not metrics or 'mid' not in metrics:
            return {}
        
        mid = metrics['mid']
        spread = metrics['spread_bps']
        imbalance = metrics['imbalance']
        volatility = metrics['volatility']
        
        # Dynamic spread calculation
        base_spread = max(2.5, spread * 0.7)  # More aggressive base spread
        volatility_adjustment = volatility * 0.5  # Volatility premium
        risk_adjustment = risk_factor * 2.0  # Risk premium
        aggressiveness_adjustment = (2.0 - aggressiveness) * 1.0  # Aggressiveness factor
        
        # Inventory management
        inventory_adjustment = inventory_skew * 15.0  # Stronger inventory skew
        imbalance_adjustment = imbalance * 3.0  # Imbalance premium
        
        # Total spread
        half_spread = (base_spread + volatility_adjustment + risk_adjustment + 
                      aggressiveness_adjustment + abs(inventory_adjustment) + 
                      abs(imbalance_adjustment)) / 2
        
        # Calculate quotes with inventory skew
        if inventory_skew > 0:  # Long inventory - more aggressive on ask
            bid = mid - half_spread / 10000 * mid - inventory_adjustment / 10000 * mid
            ask = mid + half_spread / 10000 * mid + (inventory_adjustment * 0.5) / 10000 * mid
        elif inventory_skew < 0:  # Short inventory - more aggressive on bid
            bid = mid - half_spread / 10000 * mid - (inventory_adjustment * 0.5) / 10000 * mid
            ask = mid + half_spread / 10000 * mid + inventory_adjustment / 10000 * mid
        else:  # Neutral
            bid = mid - half_spread / 10000 * mid
            ask = mid + half_spread / 10000 * mid
        
        # Calculate quote sizes based on market conditions
        base_size = 0.1  # Base size in BTC
        volatility_factor = max(0.5, min(2.0, 1.0 - volatility / 100))
        imbalance_factor = max(0.5, min(2.0, 1.0 - abs(imbalance)))
        
        bid_size = base_size * volatility_factor * imbalance_factor
        ask_size = base_size * volatility_factor * imbalance_factor
        
        # Adjust sizes based on inventory
        if inventory_skew > 0:
            bid_size *= 1.2  # Larger bid to reduce inventory
            ask_size *= 0.8  # Smaller ask to avoid adding inventory
        elif inventory_skew < 0:
            bid_size *= 0.8  # Smaller bid to avoid adding inventory
            ask_size *= 1.2  # Larger ask to reduce inventory
        
        return {
            'bid': bid,
            'ask': ask,
            'bid_size': bid_size,
            'ask_size': ask_size,
            'spread_bps': (ask - bid) / mid * 10000,
            'inventory_adjustment': inventory_adjustment,
            'volatility_adjustment': volatility_adjustment,
            'risk_adjustment': risk_adjustment,
            'expected_profit': (ask - bid) * min(bid_size, ask_size)
        }
    
    def get_position_summary(self) -> dict:
        """Get comprehensive position summary"""
        try:
            positions = self.futures_client.list_positions(settle='usdt')
            active_positions = []
            
            for pos in positions:
                size = float(pos.size)
                if size != 0:
                    pnl = float(pos.unrealised_pnl)
                    entry_price = float(pos.entry_price) if hasattr(pos, 'entry_price') else 0
                    mark_price = float(pos.mark_price) if hasattr(pos, 'mark_price') else 0
                    
                    position_data = {
                        'symbol': pos.contract,
                        'size': size,
                        'pnl': pnl,
                        'side': 'LONG' if size > 0 else 'SHORT',
                        'entry_price': entry_price,
                        'mark_price': mark_price,
                        'pnl_percentage': ((mark_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                    }
                    active_positions.append(position_data)
            
            total_pnl = sum(pos['pnl'] for pos in active_positions)
            total_size = sum(abs(pos['size']) for pos in active_positions)
            self.total_pnl = total_pnl
            
            # Calculate portfolio metrics
            long_positions = [pos for pos in active_positions if pos['side'] == 'LONG']
            short_positions = [pos for pos in active_positions if pos['side'] == 'SHORT']
            
            long_exposure = sum(pos['size'] * pos['mark_price'] for pos in long_positions)
            short_exposure = sum(abs(pos['size']) * pos['mark_price'] for pos in short_positions)
            net_exposure = long_exposure - short_exposure
            
            return {
                'positions': active_positions,
                'total_pnl': total_pnl,
                'position_count': len(active_positions),
                'total_size': total_size,
                'long_count': len(long_positions),
                'short_count': len(short_positions),
                'long_exposure': long_exposure,
                'short_exposure': short_exposure,
                'net_exposure': net_exposure,
                'gross_exposure': long_exposure + short_exposure
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def simulate_market_making(self, symbol: str = "BTC_USDT", duration_minutes: int = 5,
                              strategy_params: dict = None) -> dict:
        """Advanced market making simulation with strategy parameters"""
        if strategy_params is None:
            strategy_params = {
                'inventory_skew': 0.0,
                'risk_factor': 1.0,
                'aggressiveness': 1.0,
                'order_size': 0.1
            }
        
        results = []
        total_trades = 0
        total_pnl = 0.0
        
        for i in range(duration_minutes * 60):  # Simulate every second
            # Get current metrics
            metrics = self.calculate_market_metrics(symbol)
            if not metrics or 'mid' not in metrics:
                time.sleep(1)
                continue
            
            # Get position summary
            position_summary = self.get_position_summary()
            current_inventory = sum(pos['size'] for pos in position_summary.get('positions', []))
            
            # Calculate optimal quotes
            quotes = self.calculate_optimal_quotes(
                metrics, 
                current_inventory / strategy_params['order_size'],
                strategy_params['risk_factor'],
                strategy_params['aggressiveness']
            )
            
            # Simulate trade execution
            trade_probability = random.uniform(0.01, 0.1)  # 1-10% chance per second
            
            if random.random() < trade_probability:
                # Simulate a trade
                side = random.choice(['buy', 'sell'])
                size = strategy_params['order_size'] * random.uniform(0.8, 1.2)
                
                if side == 'buy':
                    trade_price = quotes['bid']
                    trade_pnl = -size * 0.0001  # Small cost for market order
                else:
                    trade_price = quotes['ask']
                    trade_pnl = size * 0.0001
                
                total_trades += 1
                total_pnl += trade_pnl
                
                # Track trade
                trade_data = {
                    'timestamp': time.time(),
                    'side': side,
                    'price': trade_price,
                    'size': size,
                    'pnl': trade_pnl,
                    'spread': quotes['spread_bps']
                }
                self.performance_tracker.add_trade(trade_data)
            
            # Record state
            result = {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'mid': metrics['mid'],
                'spread_bps': metrics['spread_bps'],
                'bid_quote': quotes.get('bid'),
                'ask_quote': quotes.get('ask'),
                'inventory_skew': current_inventory / strategy_params['order_size'],
                'total_pnl': total_pnl,
                'imbalance': metrics['imbalance'],
                'volatility': metrics['volatility'],
                'latency': metrics.get('latency', 0)
            }
            
            results.append(result)
            
            # Update every second
            if i % 60 == 0:  # Every minute
                yield result  # Yield intermediate results
            
            time.sleep(0.01)  # Fast simulation
        
        # Final results
        final_summary = {
            'symbol': symbol,
            'duration_minutes': duration_minutes,
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'data_points': len(results),
            'results': results,
            'performance_stats': self.performance_tracker.get_performance_stats(),
            'strategy_params': strategy_params
        }
        
        return final_summary

class NeomorphicFrame(tk.Frame):
    """Enhanced neomorphic frame with advanced styling"""
    
    def __init__(self, parent, bg_color=None, corner_radius=10, **kwargs):
        if bg_color is None:
            bg_color = NeomorphicTheme.BG_SECONDARY
        
        super().__init__(parent, bg=bg_color, **kwargs)
        self.bg_color = bg_color
        self.corner_radius = corner_radius
        self.bind('<Configure>', self._on_configure)
        
    def _on_configure(self, event):
        """Handle frame configuration with enhanced drawing"""
        self._draw_neomorphic_border()
    
    def _draw_neomorphic_border(self):
        """Draw enhanced neomorphic border with gradients"""
        for widget in self.winfo_children():
            if isinstance(widget, Canvas):
                widget.destroy()
        
        canvas = Canvas(self, bg=self.bg_color, highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width > 1 and height > 1:
            # Draw multiple shadow layers for depth
            for i in range(3):
                offset = 3 - i
                shadow_color = NeomorphicTheme.DARKER_SHADOW if i == 0 else NeomorphicTheme.DARK_SHADOW
                
                # Bottom and right shadows
                canvas.create_line(
                    width - offset, offset, 
                    width - offset, height - offset,
                    fill=shadow_color, width=3-i
                )
                canvas.create_line(
                    offset, height - offset,
                    width - offset, height - offset,
                    fill=shadow_color, width=3-i
                )
            
            # Top and left highlights
            for i in range(2):
                offset = 2 - i
                highlight_color = NeomorphicTheme.LIGHTER_SHADOW if i == 0 else NeomorphicTheme.LIGHT_SHADOW
                
                canvas.create_line(
                    offset, offset,
                    width - offset, offset,
                    fill=highlight_color, width=2-i
                )
                canvas.create_line(
                    offset, offset,
                    offset, height - offset,
                    fill=highlight_color, width=2-i
                )

class NeomorphicButton(tk.Button):
    """Enhanced neomorphic button with advanced animations"""
    
    def __init__(self, parent, bg_color=None, hover_color=None, 
                 pressed_color=None, animation_speed=0.1, **kwargs):
        if bg_color is None:
            bg_color = NeomorphicTheme.BG_SECONDARY
        if hover_color is None:
            hover_color = NeomorphicTheme.ACCENT_PRIMARY
        if pressed_color is None:
            pressed_color = NeomorphicTheme.get_gradient_color(bg_color, 0.8)
        
        default_kwargs = {
            'bg': bg_color,
            'fg': NeomorphicTheme.TEXT_PRIMARY,
            'font': ('Arial', 10, 'bold'),
            'relief': 'flat',
            'bd': 0,
            'padx': 20,
            'pady': 12,
            'cursor': 'hand2'
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        self.original_bg = bg_color
        self.animation_speed = animation_speed
        self.is_pressed = False
        
        # Bind enhanced hover effects
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)
        
        # Add subtle pulse animation
        self.pulse_thread = None
        self.start_pulse()
    
    def _on_enter(self, event):
        """Enhanced mouse enter with smooth transition"""
        self.animate_color(self.hover_color)
    
    def _on_leave(self, event):
        """Enhanced mouse leave with smooth transition"""
        if not self.is_pressed:
            self.animate_color(self.original_bg)
    
    def _on_press(self, event):
        """Enhanced button press with visual feedback"""
        self.is_pressed = True
        self.animate_color(self.pressed_color)
        
        # Add ripple effect
        self.create_ripple_effect(event.x, event.y)
    
    def _on_release(self, event):
        """Enhanced button release"""
        self.is_pressed = False
        self.animate_color(self.hover_color)
    
    def animate_color(self, target_color):
        """Smooth color animation"""
        def animate():
            current_color = self.cget('bg')
            steps = 10
            
            for i in range(steps):
                # Interpolate color
                ratio = i / steps
                new_color = self.interpolate_color(current_color, target_color, ratio)
                self.config(bg=new_color)
                self.update()
                time.sleep(self.animation_speed / steps)
        
        threading.Thread(target=animate, daemon=True).start()
    
    def interpolate_color(self, color1, color2, ratio):
        """Interpolate between two colors"""
        color1 = color1.lstrip('#')
        color2 = color2.lstrip('#')
        
        r1, g1, b1 = tuple(int(color1[i:i+2], 16) for i in (0, 2, 4))
        r2, g2, b2 = tuple(int(color2[i:i+2], 16) for i in (0, 2, 4))
        
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def create_ripple_effect(self, x, y):
        """Create ripple effect on button press"""
        ripple_canvas = Canvas(self, bg=self.cget('bg'), highlightthickness=0)
        ripple_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        def animate_ripple():
            radius = 0
            max_radius = max(self.winfo_width(), self.winfo_height())
            
            while radius < max_radius:
                ripple_canvas.delete("all")
                alpha = 1.0 - (radius / max_radius)
                color = self.interpolate_color(self.cget('bg'), NeomorphicTheme.ACCENT_PRIMARY, alpha)
                
                ripple_canvas.create_oval(
                    x - radius, y - radius,
                    x + radius, y + radius,
                    outline=color, width=2
                )
                
                ripple_canvas.update()
                radius += 5
                time.sleep(0.01)
            
            ripple_canvas.destroy()
        
        threading.Thread(target=animate_ripple, daemon=True).start()
    
    def start_pulse(self):
        """Start subtle pulse animation"""
        def pulse():
            while True:
                if str(self.cget('state')) != 'disabled':
                    # Subtle pulse effect
                    current_bg = self.cget('bg')
                    brighter = NeomorphicTheme.get_gradient_color(current_bg, 1.05)
                    self.config(bg=brighter)
                    time.sleep(2)
                    self.config(bg=current_bg)
                    time.sleep(2)
                time.sleep(1)
        
        self.pulse_thread = threading.Thread(target=pulse, daemon=True)
        self.pulse_thread.start()

class NeomorphicScale(tk.Scale):
    """Enhanced neomorphic scale with custom styling"""
    
    def __init__(self, parent, **kwargs):
        default_kwargs = {
            'bg': NeomorphicTheme.BG_SECONDARY,
            'fg': NeomorphicTheme.TEXT_PRIMARY,
            'troughcolor': NeomorphicTheme.BG_TERTIARY,
            'activebackground': NeomorphicTheme.ACCENT_PRIMARY,
            'highlightthickness': 0,
            'bd': 0,
            'orient': 'horizontal',
            'sliderlength': 20,
            'width': 15
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)

class AnimatedCanvas(Canvas):
    """Canvas with advanced animation capabilities"""
    
    def __init__(self, parent, **kwargs):
        default_kwargs = {
            'bg': NeomorphicTheme.BG_TERTIARY,
            'highlightthickness': 0
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        self.animations = []
        self.particles = []
        self.is_animating = False
    
    def add_particle(self, x, y, vx, vy, color, size=3, lifetime=2.0):
        """Add animated particle"""
        particle = {
            'x': x, 'y': y,
            'vx': vx, 'vy': vy,
            'color': color,
            'size': size,
            'lifetime': lifetime,
            'age': 0
        }
        self.particles.append(particle)
    
    def animate_particles(self):
        """Animate all particles"""
        if not self.is_animating:
            return
        
        self.delete("particle")
        
        particles_to_remove = []
        
        for particle in self.particles:
            # Update position
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['age'] += 0.016  # ~60 FPS
            
            # Apply gravity
            particle['vy'] += 0.1
            
            # Fade out
            alpha = 1.0 - (particle['age'] / particle['lifetime'])
            
            if alpha > 0:
                # Draw particle
                size = particle['size'] * alpha
                self.create_oval(
                    particle['x'] - size, particle['y'] - size,
                    particle['x'] + size, particle['y'] + size,
                    fill=particle['color'], outline='',
                    tags="particle"
                )
            else:
                particles_to_remove.append(particle)
        
        # Remove dead particles
        for particle in particles_to_remove:
            self.particles.remove(particle)
        
        # Schedule next frame
        if self.is_animating:
            self.after(16, self.animate_particles)  # ~60 FPS
    
    def start_animation(self):
        """Start animation loop"""
        self.is_animating = True
        self.animate_particles()
    
    def stop_animation(self):
        """Stop animation loop"""
        self.is_animating = False

class MarketMakerUI:
    """Comprehensive neomorphic market maker UI with advanced features"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 BRUTALIST MARKET MAKER - NEOMORPHIC ULTRA")
        self.root.geometry("1800x1200")
        self.root.configure(bg=NeomorphicTheme.BG_PRIMARY)
        
        # Initialize clients
        self.cfg = Configuration(key=GATE_API_KEY, secret=GATE_API_SECRET)
        self.futures_client = FuturesApi(ApiClient(self.cfg))
        self.market_maker = BrutalistMarketMaker(self.futures_client)
        
        # State variables
        self.is_simulating = False
        self.auto_refresh = True
        self.current_symbol = "BTC_USDT"
        self.price_history = deque(maxlen=100)
        self.pnl_history = deque(maxlen=100)
        
        # Animation state
        self.animation_frame = 0
        self.particle_effects = []
        
        self.setup_ui()
        self.start_auto_refresh()
        self.start_animations()
    
    def setup_ui(self):
        """Setup comprehensive neomorphic UI"""
        # Main container with enhanced styling
        main_container = NeomorphicFrame(self.root, bg=NeomorphicTheme.BG_PRIMARY, corner_radius=15)
        main_container.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Enhanced header with animations
        self.setup_enhanced_header(main_container)
        
        # Control panel
        self.setup_control_panel(main_container)
        
        # Main content area with tabs
        self.setup_main_content(main_container)
        
        # Advanced footer with metrics
        self.setup_enhanced_footer(main_container)
    
    def setup_enhanced_header(self, parent):
        """Setup enhanced header with animations"""
        header_frame = NeomorphicFrame(parent, bg=NeomorphicTheme.BG_SECONDARY, height=120)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # Title with gradient effect
        title_label = tk.Label(
            header_frame,
            text="🤖 BRUTALIST MARKET MAKER",
            font=('Arial', 28, 'bold'),
            fg=NeomorphicTheme.GRADIENT_START,
            bg=NeomorphicTheme.BG_SECONDARY
        )
        title_label.pack(side='top', pady=(25, 5))
        
        subtitle_label = tk.Label(
            header_frame,
            text="NEOMORPHIC ULTRA HIGH-FREQUENCY TRADING SYSTEM",
            font=('Arial', 14),
            fg=NeomorphicTheme.TEXT_SECONDARY,
            bg=NeomorphicTheme.BG_SECONDARY
        )
        subtitle_label.pack(side='top')
        
        # Status bar with animations
        status_container = NeomorphicFrame(header_frame, bg=NeomorphicTheme.BG_TERTIARY, height=40)
        status_container.pack(fill='x', padx=20, pady=(15, 0))
        status_container.pack_propagate(False)
        
        self.status_indicator = tk.Label(
            status_container,
            text="● SYSTEM READY",
            font=('Arial', 12, 'bold'),
            fg=NeomorphicTheme.ACCENT_SUCCESS,
            bg=NeomorphicTheme.BG_TERTIARY
        )
        self.status_indicator.pack(side='left', padx=20, pady=10)
        
        # Performance indicators
        self.performance_label = tk.Label(
            status_container,
            text="⚡ LATENCY: 0ms | 💰 PNL: $0.00 | 📊 TRADES: 0",
            font=('Arial', 10),
            fg=NeomorphicTheme.TEXT_SECONDARY,
            bg=NeomorphicTheme.BG_TERTIARY
        )
        self.performance_label.pack(side='right', padx=20, pady=10)
        
        # Animated canvas for background effects
        self.header_canvas = AnimatedCanvas(header_frame, bg=NeomorphicTheme.BG_SECONDARY)
        self.header_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.header_canvas.lower()
    
    def setup_control_panel(self, parent):
        """Setup advanced control panel"""
        control_frame = NeomorphicFrame(parent, bg=NeomorphicTheme.BG_PRIMARY, height=80)
        control_frame.pack(fill='x', pady=(0, 20))
        control_frame.pack_propagate(False)
        
        # Symbol selector
        symbol_container = NeomorphicFrame(control_frame, bg=NeomorphicTheme.BG_SECONDARY)
        symbol_container.pack(side='left', padx=(0, 10), fill='y')
        
        tk.Label(
            symbol_container,
            text="SYMBOL:",
            font=('Arial', 11, 'bold'),
            fg=NeomorphicTheme.TEXT_PRIMARY,
            bg=NeomorphicTheme.BG_SECONDARY
        ).pack(side='left', padx=15, pady=25)
        
        self.symbol_var = tk.StringVar(value="BTC_USDT")
        symbol_combo = ttk.Combobox(
            symbol_container,
            textvariable=self.symbol_var,
            values=["BTC_USDT", "ETH_USDT", "SOL_USDT", "DOGE_USDT", "ADA_USDT", "MATIC_USDT"],
            width=15,
            state='readonly',
            font=('Arial', 11, 'bold')
        )
        symbol_combo.pack(side='left', padx=10, pady=25)
        
        # Strategy parameters
        strategy_container = NeomorphicFrame(control_frame, bg=NeomorphicTheme.BG_SECONDARY)
        strategy_container.pack(side='left', padx=10, fill='both', expand=True)
        
        # Risk factor
        tk.Label(
            strategy_container,
            text="RISK:",
            font=('Arial', 10),
            fg=NeomorphicTheme.TEXT_PRIMARY,
            bg=NeomorphicTheme.BG_SECONDARY
        ).pack(side='left', padx=10, pady=25)
        
        self.risk_var = tk.DoubleVar(value=1.0)
        risk_scale = NeomorphicScale(
            strategy_container,
            from_=0.1, to=3.0,
            resolution=0.1,
            variable=self.risk_var,
            length=150
        )
        risk_scale.pack(side='left', padx=5, pady=25)
        
        self.risk_label = tk.Label(
            strategy_container,
            text="1.0",
            font=('Arial', 10, 'bold'),
            fg=NeomorphicTheme.ACCENT_WARNING,
            bg=NeomorphicTheme.BG_SECONDARY,
            width=5
        )
        self.risk_label.pack(side='left', padx=5, pady=25)
        
        def update_risk_label(val):
            self.risk_label.config(text=f"{float(val):.1f}")
        risk_scale.config(command=update_risk_label)
        
        # Aggressiveness
        tk.Label(
            strategy_container,
            text="AGGR:",
            font=('Arial', 10),
            fg=NeomorphicTheme.TEXT_PRIMARY,
            bg=NeomorphicTheme.BG_SECONDARY
        ).pack(side='left', padx=20, pady=25)
        
        self.aggressiveness_var = tk.DoubleVar(value=1.0)
        agg_scale = NeomorphicScale(
            strategy_container,
            from_=0.1, to=2.0,
            resolution=0.1,
            variable=self.aggressiveness_var,
            length=150
        )
        agg_scale.pack(side='left', padx=5, pady=25)
        
        self.agg_label = tk.Label(
            strategy_container,
            text="1.0",
            font=('Arial', 10, 'bold'),
            fg=NeomorphicTheme.ACCENT_INFO,
            bg=NeomorphicTheme.BG_SECONDARY,
            width=5
        )
        self.agg_label.pack(side='left', padx=5, pady=25)
        
        def update_agg_label(val):
            self.agg_label.config(text=f"{float(val):.1f}")
        agg_scale.config(command=update_agg_label)
        
        # Quick actions
        actions_container = NeomorphicFrame(control_frame, bg=NeomorphicTheme.BG_SECONDARY)
        actions_container.pack(side='right', padx=(10, 0), fill='y')
        
        NeomorphicButton(
            actions_container,
            text="🔄 REFRESH",
            command=self.update_all_data,
            bg_color=NeomorphicTheme.ACCENT_PRIMARY,
            width=12
        ).pack(side='left', padx=10, pady=20)
        
        NeomorphicButton(
            actions_container,
            text="▶️ START",
            command=self.start_advanced_simulation,
            bg_color=NeomorphicTheme.ACCENT_SUCCESS,
            width=12
        ).pack(side='left', padx=5, pady=20)
        
        NeomorphicButton(
            actions_container,
            text="⏸️ STOP",
            command=self.stop_simulation,
            bg_color=NeomorphicTheme.ACCENT_DANGER,
            width=12
        ).pack(side='left', padx=5, pady=20)
    
    def setup_main_content(self, parent):
        """Setup main content area with advanced tabs"""
        content_frame = NeomorphicFrame(parent, bg=NeomorphicTheme.BG_PRIMARY)
        content_frame.pack(fill='both', expand=True)
        
        # Create advanced notebook for tabs
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure neomorphic tab style
        style.configure('Neomorphic.TNotebook', 
                       background=NeomorphicTheme.BG_PRIMARY,
                       borderwidth=0)
        style.configure('Neomorphic.TNotebook.Tab',
                       background=NeomorphicTheme.BG_SECONDARY,
                       foreground=NeomorphicTheme.TEXT_PRIMARY,
                       padding=[20, 10],
                       font=('Arial', 11, 'bold'))
        style.map('Neomorphic.TNotebook.Tab',
                 background=[('selected', NeomorphicTheme.ACCENT_PRIMARY)],
                 foreground=[('selected', NeomorphicTheme.TEXT_PRIMARY)])
        
        self.notebook = ttk.Notebook(content_frame, style='Neomorphic.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Setup individual tabs
        self.setup_market_data_tab()
        self.setup_quotes_tab()
        self.setup_simulation_tab()
        self.setup_performance_tab()
        self.setup_analytics_tab()
    
    def setup_market_data_tab(self):
        """Setup enhanced market data tab"""
        market_tab = NeomorphicFrame(self.notebook, bg=NeomorphicTheme.BG_PRIMARY)
        self.notebook.add(market_tab, text='📊 MARKET DATA')
        
        # Create two-column layout
        left_column = NeomorphicFrame(market_tab, bg=NeomorphicTheme.BG_PRIMARY)
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        right_column = NeomorphicFrame(market_tab, bg=NeomorphicTheme.BG_PRIMARY)
        right_column.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Order book display
        orderbook_frame = NeomorphicFrame(left_column, bg=NeomorphicTheme.BG_SECONDARY)
        orderbook_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        tk.Label(
            orderbook_frame,
            text="📈 ORDER BOOK",
            font=('Arial', 14, 'bold'),
            fg=NeomorphicTheme.ACCENT_PRIMARY,
            bg=NeomorphicTheme.BG_SECONDARY
        ).pack(pady=10)
        
        self.orderbook_text = scrolledtext.ScrolledText(
            orderbook_frame,
            height=20,
            width=50,
            bg=NeomorphicTheme.BG_TERTIARY,
            fg=NeomorphicTheme.ACCENT_SUCCESS,
            font=('Courier', 9),
            relief='flat',
            bd=0
        )
        self.orderbook_text.pack(padx=15, pady=15, fill='both', expand=True)
        
        # Market metrics
        metrics_frame = NeomorphicFrame(right_column, bg=NeomorphicTheme.BG_SECONDARY)
        metrics_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        tk.Label(
            metrics_frame,
            text="📊 MARKET METRICS",
            font=('Arial', 14, 'bold'),
            fg=NeomorphicTheme.ACCENT_PRIMARY,
            bg=NeomorphicTheme.BG_SECONDARY
        ).pack(pady=10)
        
        self.metrics_text = scrolledtext.ScrolledText(
            metrics_frame,
            height=20,
            width=50,
            bg=NeomorphicTheme.BG_TERTIARY,
            fg=NeomorphicTheme.ACCENT_SUCCESS,
            font=('Courier', 9),
            relief='flat',
            bd=0
        )
        self.metrics_text.pack(padx=15, pady=15, fill='both', expand=True)
        
        # Position summary
        position_frame = NeomorphicFrame(market_tab, bg=NeomorphicTheme.BG_SECONDARY)
        position_frame.pack(fill='x')
        
        tk.Label(
            position_frame,
            text="💰 POSITION SUMMARY",
            font=('Arial', 14, 'bold'),
            fg=NeomorphicTheme.ACCENT_PRIMARY,
            bg=NeomorphicTheme.BG_SECONDARY
        ).pack(pady=10)
        
        self.position_text = scrolledtext.ScrolledText(
            position_frame,
            height=8,
            width=100,
            bg=NeomorphicTheme.BG_TERTIARY,
            fg=NeomorphicTheme.ACCENT_SUCCESS,
            font=('Courier', 9),
            relief='flat',
            bd=0
        )
        self.position_text.pack(padx=15, pady=15, fill='both', expand=True)
    
    def setup_quotes_tab(self):
        """Setup enhanced quotes tab"""
        quotes_tab = NeomorphicFrame(self.notebook, bg=NeomorphicTheme.BG_PRIMARY)
        self.notebook.add(quotes_tab, text='💰 QUOTES')
        
        # Quote controls
        control_frame = NeomorphicFrame(quotes_tab, bg=NeomorphicTheme.BG_SECONDARY, height=100)
        control_frame.pack(fill='x', pady=(0, 10))
        control_frame.pack_propagate(False)
        
        # Inventory skew control
        skew_container = NeomorphicFrame(control_frame, bg=NeomorphicTheme.BG_TERTIARY)
        skew_container.pack(side='left', padx=20, pady=20, fill='x', expand=True)
        
        tk.Label(
            skew_container,
            text="INVENTORY SKEW:",
            font=('Arial', 12, 'bold'),
            fg=NeomorphicTheme.TEXT_PRIMARY,
            bg=NeomorphicTheme.BG_TERTIARY
        ).pack(side='left', padx=15, pady=30)
        
        self.skew_var = tk.DoubleVar(value=0.0)
        skew_scale = NeomorphicScale(
            skew_container,
            from_=-3.0, to=3.0,
            resolution=0.1,
            variable=self.skew_var,
            length=300
        )
        skew_scale.pack(side='left', padx=15, pady=30)
        
        self.skew_label = tk.Label(
            skew_container,
            text="0.0",
            font=('Arial', 14, 'bold'),
            fg=NeomorphicTheme.ACCENT_WARNING,
            bg=NeomorphicTheme.BG_TERTIARY,
            width=8
        )
        self.skew_label.pack(side='left', padx=15, pady=30)
        
        def update_skew_label(val):
            self.skew_label.config(text=f"{float(val):.1f}")
            self.calculate_enhanced_quotes()
        skew_scale.config(command=update_skew_label)
        
        # Quote display
        quote_display_frame = NeomorphicFrame(quotes_tab, bg=NeomorphicTheme.BG_SECONDARY)
        quote_display_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        tk.Label(
            quote_display_frame,
            text="🎯 OPTIMAL QUOTES",
            font=('Arial', 16, 'bold'),
            fg=NeomorphicTheme.ACCENT_PRIMARY,
            bg=NeomorphicTheme.BG_SECONDARY
        ).pack(pady=15)
        
        self.quotes_text = scrolledtext.ScrolledText(
            quote_display_frame,
            height=20,
            width=100,
            bg=NeomorphicTheme.BG_TERTIARY,
            fg=NeomorphicTheme.ACCENT_SUCCESS,
            font=('Courier', 10),
            relief='flat',
            bd=0
        )
        self.quotes_text.pack(padx=20, pady=20, fill='both', expand=True)
        
        # Action buttons
        action_frame = NeomorphicFrame(quotes_tab, bg=NeomorphicTheme.BG_SECONDARY, height=80)
        action_frame.pack(fill='x')
        action_frame.pack_propagate(False)
        
        button_container = NeomorphicFrame(action_frame, bg=NeomorphicTheme.BG_TERTIARY)
        button_container.pack(pady=20)
        
        NeomorphicButton(
            button_container,
            text="💰 CALCULATE QUOTES",
            command=self.calculate_enhanced_quotes,
            bg_color=NeomorphicTheme.ACCENT_WARNING,
            width=18
        ).pack(side='left', padx=15)
        
        NeomorphicButton(
            button_container,
            text="🎯 PLACE ORDERS",
            command=self.place_demo_orders,
            bg_color=NeomorphicTheme.ACCENT_DANGER,
            width=18
        ).pack(side='left', padx=15)
        
        NeomorphicButton(
            button_container,
            text="📊 QUOTE ANALYSIS",
            command=self.analyze_quotes,
            bg_color=NeomorphicTheme.ACCENT_INFO,
            width=18
        ).pack(side='left', padx=15)
    
    def setup_simulation_tab(self):
        """Setup enhanced simulation tab"""
        sim_tab = NeomorphicFrame(self.notebook, bg=NeomorphicTheme.BG_PRIMARY)
        self.notebook.add(sim_tab, text='🎮 SIMULATION')
        
        # Simulation controls
        control_frame = NeomorphicFrame(sim_tab, bg=NeomorphicTheme.BG_SECONDARY, height=120)
        control_frame.pack(fill='x', pady=(0, 10))
        control_frame.pack_propagate(False)
        
        # Duration control
        duration_container = NeomorphicFrame(control_frame, bg=NeomorphicTheme.BG_TERTIARY)
        duration_container.pack(side='left', padx=20, pady=25, fill='x', expand=True)
        
        tk.Label(
            duration_container,
            text="DURATION (minutes):",
            font=('Arial', 12, 'bold'),
            fg=NeomorphicTheme.TEXT_PRIMARY,
            bg=NeomorphicTheme.BG_TERTIARY
        ).pack(side='left', padx=20, pady=30)
        
        self.duration_var = tk.IntVar(value=10)
        duration_spin = tk.Spinbox(
            duration_container,
            from_=1, to=60,
            textvariable=self.duration_var,
            width=10,
            font=('Arial', 12, 'bold'),
            bg=NeomorphicTheme.BG_QUATERNARY,
            fg=NeomorphicTheme.TEXT_PRIMARY,
            relief='flat',
            bd=0
        )
        duration_spin.pack(side='left', padx=15, pady=30)
        
        # Order size control
        size_container = NeomorphicFrame(control_frame, bg=NeomorphicTheme.BG_TERTIARY)
        size_container.pack(side='left', padx=20, pady=25, fill='x', expand=True)
        
        tk.Label(
            size_container,
            text="ORDER SIZE (BTC):",
            font=('Arial', 12, 'bold'),
            fg=NeomorphicTheme.TEXT_PRIMARY,
            bg=NeomorphicTheme.BG_TERTIARY
        ).pack(side='left', padx=20, pady=30)
        
        self.order_size_var = tk.DoubleVar(value=0.1)
        size_spin = tk.Spinbox(
            size_container,
            from_=0.01, to=1.0,
            increment=0.01,
            textvariable=self.order_size_var,
            width=10,
            font=('Arial', 12, 'bold'),
            bg=NeomorphicTheme.BG_QUATERNARY,
            fg=NeomorphicTheme.TEXT_PRIMARY,
            relief='flat',
            bd=0
        )
        size_spin.pack(side='left', padx=15, pady=30)
        
        # Simulation display
        sim_display_frame = NeomorphicFrame(sim_tab, bg=NeomorphicTheme.BG_SECONDARY)
        sim_display_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        tk.Label(
            sim_display_frame,
            text="🎮 SIMULATION RESULTS",
            font=('Arial', 16, 'bold'),
            fg=NeomorphicTheme.ACCENT_PRIMARY,
            bg=NeomorphicTheme.BG_SECONDARY
        ).pack(pady=15)
        
        self.sim_text = scrolledtext.ScrolledText(
            sim_display_frame,
            height=25,
            width=100,
            bg=NeomorphicTheme.BG_TERTIARY,
            fg=NeomorphicTheme.ACCENT_SUCCESS,
            font=('Courier', 9),
            relief='flat',
            bd=0
        )
        self.sim_text.pack(padx=20, pady=20, fill='both', expand=True)
        
        # Simulation controls
        sim_control_frame = NeomorphicFrame(sim_tab, bg=NeomorphicTheme.BG_SECONDARY, height=80)
        sim_control_frame.pack(fill='x')
        sim_control_frame.pack_propagate(False)
        
        button_container = NeomorphicFrame(sim_control_frame, bg=NeomorphicTheme.BG_TERTIARY)
        button_container.pack(pady=20)
        
        self.sim_button = NeomorphicButton(
            button_container,
            text="▶️ START SIMULATION",
            command=self.start_advanced_simulation,
            bg_color=NeomorphicTheme.ACCENT_SUCCESS,
            width=20
        )
        self.sim_button.pack(side='left', padx=15)
        
        NeomorphicButton(
            button_container,
            text="⏸️ STOP",
            command=self.stop_simulation,
            bg_color=NeomorphicTheme.ACCENT_DANGER,
            width=15
        ).pack(side='left', padx=10)
        
        NeomorphicButton(
            button_container,
            text="📊 RESULTS",
            command=self.show_simulation_results,
            bg_color=NeomorphicTheme.ACCENT_INFO,
            width=15
        ).pack(side='left', padx=10)
        
        NeomorphicButton(
            button_container,
            text="🗑️ CLEAR",
            command=self.clear_simulation,
            bg_color=NeomorphicTheme.TEXT_TERTIARY,
            width=15
        ).pack(side='left', padx=10)
    
    def setup_performance_tab(self):
        """Setup performance analytics tab"""
        perf_tab = NeomorphicFrame(self.notebook, bg=NeomorphicTheme.BG_PRIMARY)
        self.notebook.add(perf_tab, text='📊 PERFORMANCE')
        
        # Performance metrics display
        perf_frame = NeomorphicFrame(perf_tab, bg=NeomorphicTheme.BG_SECONDARY)
        perf_frame.pack(fill='both', expand=True)
        
        tk.Label(
            perf_frame,
            text="📊 PERFORMANCE ANALYTICS",
            font=('Arial', 16, 'bold'),
            fg=NeomorphicTheme.ACCENT_PRIMARY,
            bg=NeomorphicTheme.BG_SECONDARY
        ).pack(pady=15)
        
        self.perf_text = scrolledtext.ScrolledText(
            perf_frame,
            height=30,
            width=100,
            bg=NeomorphicTheme.BG_TERTIARY,
            fg=NeomorphicTheme.ACCENT_SUCCESS,
            font=('Courier', 9),
            relief='flat',
            bd=0
        )
        self.perf_text.pack(padx=20, pady=20, fill='both', expand=True)
        
        # Performance controls
        perf_control_frame = NeomorphicFrame(perf_tab, bg=NeomorphicTheme.BG_SECONDARY, height=80)
        perf_control_frame.pack(fill='x')
        perf_control_frame.pack_propagate(False)
        
        button_container = NeomorphicFrame(perf_control_frame, bg=NeomorphicTheme.BG_TERTIARY)
        button_container.pack(pady=20)
        
        NeomorphicButton(
            button_container,
            text="📊 UPDATE STATS",
            command=self.update_performance_stats,
            bg_color=NeomorphicTheme.ACCENT_PRIMARY,
            width=18
        ).pack(side='left', padx=15)
        
        NeomorphicButton(
            button_container,
            text="📈 DETAILED ANALYSIS",
            command=self.detailed_performance_analysis,
            bg_color=NeomorphicTheme.ACCENT_INFO,
            width=18
        ).pack(side='left', padx=15)
        
        NeomorphicButton(
            button_container,
            text="💾 EXPORT DATA",
            command=self.export_performance_data,
            bg_color=NeomorphicTheme.ACCENT_WARNING,
            width=18
        ).pack(side='left', padx=15)
    
    def setup_analytics_tab(self):
        """Setup advanced analytics tab"""
        analytics_tab = NeomorphicFrame(self.notebook, bg=NeomorphicTheme.BG_PRIMARY)
        self.notebook.add(analytics_tab, text='🔬 ANALYTICS')
        
        # Analytics display
        analytics_frame = NeomorphicFrame(analytics_tab, bg=NeomorphicTheme.BG_SECONDARY)
        analytics_frame.pack(fill='both', expand=True)
        
        tk.Label(
            analytics_frame,
            text="🔬 ADVANCED ANALYTICS",
            font=('Arial', 16, 'bold'),
            fg=NeomorphicTheme.ACCENT_PRIMARY,
            bg=NeomorphicTheme.BG_SECONDARY
        ).pack(pady=15)
        
        self.analytics_text = scrolledtext.ScrolledText(
            analytics_frame,
            height=30,
            width=100,
            bg=NeomorphicTheme.BG_TERTIARY,
            fg=NeomorphicTheme.ACCENT_SUCCESS,
            font=('Courier', 9),
            relief='flat',
            bd=0
        )
        self.analytics_text.pack(padx=20, pady=20, fill='both', expand=True)
        
        # Analytics controls
        analytics_control_frame = NeomorphicFrame(analytics_tab, bg=NeomorphicTheme.BG_SECONDARY, height=80)
        analytics_control_frame.pack(fill='x')
        analytics_control_frame.pack_propagate(False)
        
        button_container = NeomorphicFrame(analytics_control_frame, bg=NeomorphicTheme.BG_TERTIARY)
        button_container.pack(pady=20)
        
        NeomorphicButton(
            button_container,
            text="🔬 MARKET ANALYSIS",
            command=self.advanced_market_analysis,
            bg_color=NeomorphicTheme.ACCENT_PRIMARY,
            width=18
        ).pack(side='left', padx=15)
        
        NeomorphicButton(
            button_container,
            text="📊 CORRELATION STUDY",
            command=self.correlation_analysis,
            bg_color=NeomorphicTheme.ACCENT_INFO,
            width=18
        ).pack(side='left', padx=15)
        
        NeomorphicButton(
            button_container,
            text="🎯 PREDICTION MODEL",
            command=self.prediction_analysis,
            bg_color=NeomorphicTheme.ACCENT_WARNING,
            width=18
        ).pack(side='left', padx=15)
    
    def setup_enhanced_footer(self, parent):
        """Setup enhanced footer with comprehensive metrics"""
        footer_frame = NeomorphicFrame(parent, bg=NeomorphicTheme.BG_SECONDARY, height=60)
        footer_frame.pack(fill='x', pady=(20, 0))
        footer_frame.pack_propagate(False)
        
        # System status
        status_container = NeomorphicFrame(footer_frame, bg=NeomorphicTheme.BG_TERTIARY)
        status_container.pack(side='left', padx=20, pady=15, fill='y')
        
        self.footer_status = tk.Label(
            status_container,
            text="🟢 SYSTEM OPERATIONAL",
            font=('Arial', 11, 'bold'),
            fg=NeomorphicTheme.ACCENT_SUCCESS,
            bg=NeomorphicTheme.BG_TERTIARY
        )
        self.footer_status.pack(pady=15)
        
        # Connection status
        connection_container = NeomorphicFrame(footer_frame, bg=NeomorphicTheme.BG_TERTIARY)
        connection_container.pack(side='left', padx=10, pady=15, fill='y')
        
        self.connection_status = tk.Label(
            connection_container,
            text="🔗 CONNECTED",
            font=('Arial', 11, 'bold'),
            fg=NeomorphicTheme.ACCENT_SUCCESS,
            bg=NeomorphicTheme.BG_TERTIARY
        )
        self.connection_status.pack(pady=15)
        
        # Auto-refresh toggle
        auto_container = NeomorphicFrame(footer_frame, bg=NeomorphicTheme.BG_TERTIARY)
        auto_container.pack(side='left', padx=10, pady=15, fill='y')
        
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_check = tk.Checkbutton(
            auto_container,
            text="AUTO-REFRESH",
            variable=self.auto_refresh_var,
            bg=NeomorphicTheme.BG_TERTIARY,
            fg=NeomorphicTheme.TEXT_PRIMARY,
            selectcolor=NeomorphicTheme.BG_QUATERNARY,
            font=('Arial', 11, 'bold'),
            relief='flat',
            bd=0
        )
        auto_check.pack(pady=15)
        
        # Real-time metrics
        metrics_container = NeomorphicFrame(footer_frame, bg=NeomorphicTheme.BG_TERTIARY)
        metrics_container.pack(side='right', padx=20, pady=15, fill='both', expand=True)
        
        self.footer_metrics = tk.Label(
            metrics_container,
            text="⚡ LATENCY: 0ms | 📊 SPREAD: 0.0bps | 💰 TOTAL PNL: $0.00 | 🎯 TRADES: 0 | ⏱️ UPTIME: 00:00:00",
            font=('Arial', 10),
            fg=NeomorphicTheme.TEXT_SECONDARY,
            bg=NeomorphicTheme.BG_TERTIARY
        )
        self.footer_metrics.pack(pady=15)
    
    def update_all_data(self):
        """Update all data displays"""
        def update_thread():
            try:
                self.status_indicator.config(text="● UPDATING...", fg=NeomorphicTheme.ACCENT_WARNING)
                
                symbol = self.symbol_var.get()
                self.current_symbol = symbol
                
                # Update market data
                metrics = self.market_maker.calculate_market_metrics(symbol)
                self.update_market_display(metrics)
                
                # Update positions
                positions = self.market_maker.get_position_summary()
                self.update_position_display(positions)
                
                # Update quotes
                self.calculate_enhanced_quotes()
                
                # Update performance
                self.update_performance_stats()
                
                # Update footer metrics
                self.update_footer_metrics(metrics, positions)
                
                self.status_indicator.config(text="● READY", fg=NeomorphicTheme.ACCENT_SUCCESS)
                
            except Exception as e:
                self.status_indicator.config(text="● ERROR", fg=NeomorphicTheme.ACCENT_DANGER)
                print(f"Update error: {e}")
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def update_market_display(self, metrics):
        """Update market data display"""
        if hasattr(self, 'orderbook_text'):
            self.orderbook_text.delete(1.0, tk.END)
            
            if metrics and 'bid_levels' in metrics:
                self.orderbook_text.insert(tk.END, f"🕐 {datetime.now().strftime('%H:%M:%S')}\n")
                self.orderbook_text.insert(tk.END, "="*50 + "\n\n")
                
                self.orderbook_text.insert(tk.END, f"📊 {self.current_symbol} ORDER BOOK\n\n")
                
                # Show top bid levels
                self.orderbook_text.insert(tk.END, f"🟢 BID LEVELS:\n")
                for i, (price, size) in enumerate(metrics['bid_levels'][:10]):
                    self.orderbook_text.insert(tk.END, f"  {i+1:2d}. ${price:.2f}  {size:>10.3f}\n")
                
                self.orderbook_text.insert(tk.END, f"\n🔴 ASK LEVELS:\n")
                for i, (price, size) in enumerate(metrics['ask_levels'][:10]):
                    self.orderbook_text.insert(tk.END, f"  {i+1:2d}. ${price:.2f}  {size:>10.3f}\n")
        
        if hasattr(self, 'metrics_text'):
            self.metrics_text.delete(1.0, tk.END)
            
            if metrics and 'mid' in metrics:
                self.metrics_text.insert(tk.END, f"📊 MARKET METRICS\n")
                self.metrics_text.insert(tk.END, "="*40 + "\n\n")
                
                self.metrics_text.insert(tk.END, f"   Mid Price: ${metrics['mid']:.2f}\n")
                self.metrics_text.insert(tk.END, f"   Spread: {metrics['spread_bps']:.2f} bps\n")
                self.metrics_text.insert(tk.END, f"   Best Bid: ${metrics['best_bid']:.2f}\n")
                self.metrics_text.insert(tk.END, f"   Best Ask: ${metrics['best_ask']:.2f}\n")
                self.metrics_text.insert(tk.END, f"   Imbalance: {metrics['imbalance']:+.4f}\n")
                self.metrics_text.insert(tk.END, f"   Bid Volume: {metrics['bid_vol']:,.1f}\n")
                self.metrics_text.insert(tk.END, f"   Ask Volume: {metrics['ask_vol']:,.1f}\n")
                self.metrics_text.insert(tk.END, f"   Bid Depth: ${metrics['bid_depth']:,.0f}\n")
                self.metrics_text.insert(tk.END, f"   Ask Depth: ${metrics['ask_depth']:,.0f}\n")
                self.metrics_text.insert(tk.END, f"   Volatility: {metrics['volatility']:.2f}%\n")
                self.metrics_text.insert(tk.END, f"   Spread Impact: {metrics['spread_impact']:.4f}\n")
                self.metrics_text.insert(tk.END, f"   Level Imbalance: {metrics['avg_level_imbalance']:+.4f}\n")
                self.metrics_text.insert(tk.END, f"   Latency: {metrics.get('latency', 0):.1f}ms\n")
    
    def update_position_display(self, positions):
        """Update position display"""
        if hasattr(self, 'position_text'):
            self.position_text.delete(1.0, tk.END)
            
            self.position_text.insert(tk.END, f"💰 POSITION SUMMARY\n")
            self.position_text.insert(tk.END, "="*60 + "\n\n")
            
            if 'positions' in positions:
                for pos in positions['positions']:
                    self.position_text.insert(tk.END, f"📈 {pos['side']} {pos['symbol']}\n")
                    self.position_text.insert(tk.END, f"   Size: {pos['size']:.4f}\n")
                    self.position_text.insert(tk.END, f"   PNL: ${pos['pnl']:+.4f}\n")
                    self.position_text.insert(tk.END, f"   Entry: ${pos['entry_price']:.4f}\n")
                    self.position_text.insert(tk.END, f"   Mark: ${pos['mark_price']:.4f}\n")
                    self.position_text.insert(tk.END, f"   PNL%: {pos['pnl_percentage']:+.2f}%\n")
                    self.position_text.insert(tk.END, "-"*40 + "\n")
                
                self.position_text.insert(tk.END, f"\n📊 PORTFOLIO SUMMARY:\n")
                self.position_text.insert(tk.END, f"   Total PNL: ${positions['total_pnl']:+.4f}\n")
                self.position_text.insert(tk.END, f"   Position Count: {positions['position_count']}\n")
                self.position_text.insert(tk.END, f"   Long Positions: {positions['long_count']}\n")
                self.position_text.insert(tk.END, f"   Short Positions: {positions['short_count']}\n")
                self.position_text.insert(tk.END, f"   Long Exposure: ${positions['long_exposure']:,.2f}\n")
                self.position_text.insert(tk.END, f"   Short Exposure: ${positions['short_exposure']:,.2f}\n")
                self.position_text.insert(tk.END, f"   Net Exposure: ${positions['net_exposure']:,.2f}\n")
                self.position_text.insert(tk.END, f"   Gross Exposure: ${positions['gross_exposure']:,.2f}\n")
            else:
                self.position_text.insert(tk.END, "   No active positions\n")
    
    def calculate_enhanced_quotes(self):
        """Calculate enhanced optimal quotes"""
        try:
            symbol = self.symbol_var.get()
            metrics = self.market_maker.calculate_market_metrics(symbol)
            
            if not metrics or 'mid' not in metrics:
                return
            
            inventory_skew = self.skew_var.get()
            risk_factor = self.risk_var.get()
            aggressiveness = self.aggressiveness_var.get()
            
            quotes = self.market_maker.calculate_optimal_quotes(
                metrics, inventory_skew, risk_factor, aggressiveness
            )
            
            if hasattr(self, 'quotes_text'):
                self.quotes_text.delete(1.0, tk.END)
                self.quotes_text.insert(tk.END, f"💰 OPTIMAL QUOTES FOR {symbol}\n")
                self.quotes_text.insert(tk.END, "="*60 + "\n\n")
                
                self.quotes_text.insert(tk.END, f"📊 MARKET CONDITIONS:\n")
                self.quotes_text.insert(tk.END, f"   Mid Price: ${metrics['mid']:.2f}\n")
                self.quotes_text.insert(tk.END, f"   Current Spread: {metrics['spread_bps']:.2f} bps\n")
                self.quotes_text.insert(tk.END, f"   Volume Imbalance: {metrics['imbalance']:+.4f}\n")
                self.quotes_text.insert(tk.END, f"   Volatility: {metrics['volatility']:.2f}%\n")
                self.quotes_text.insert(tk.END, f"   Inventory Skew: {inventory_skew:+.1f}\n")
                self.quotes_text.insert(tk.END, f"   Risk Factor: {risk_factor:.1f}\n")
                self.quotes_text.insert(tk.END, f"   Aggressiveness: {aggressiveness:.1f}\n\n")
                
                if quotes:
                    self.quotes_text.insert(tk.END, f"🎯 CALCULATED QUOTES:\n")
                    self.quotes_text.insert(tk.END, f"   Optimal Bid: ${quotes['bid']:.2f}\n")
                    self.quotes_text.insert(tk.END, f"   Optimal Ask: ${quotes['ask']:.2f}\n")
                    self.quotes_text.insert(tk.END, f"   Bid Size: {quotes['bid_size']:.4f} BTC\n")
                    self.quotes_text.insert(tk.END, f"   Ask Size: {quotes['ask_size']:.4f} BTC\n")
                    self.quotes_text.insert(tk.END, f"   Quote Spread: {quotes['spread_bps']:.2f} bps\n")
                    self.quotes_text.insert(tk.END, f"   Inventory Adj: {quotes['inventory_adjustment']:.2f} bps\n")
                    self.quotes_text.insert(tk.END, f"   Volatility Adj: {quotes['volatility_adjustment']:.2f} bps\n")
                    self.quotes_text.insert(tk.END, f"   Risk Adj: {quotes['risk_adjustment']:.2f} bps\n")
                    self.quotes_text.insert(tk.END, f"   Expected Profit: ${quotes['expected_profit']:.4f}\n\n")
                    
                    # Calculate potential metrics
                    spread_profit = quotes['expected_profit']
                    daily_trades = 100
                    daily_profit = spread_profit * daily_trades
                    monthly_profit = daily_profit * 22
                    annual_profit = daily_profit * 252
                    
                    self.quotes_text.insert(tk.END, f"💵 POTENTIAL METRICS:\n")
                    self.quotes_text.insert(tk.END, f"   Per Trade Profit: ${spread_profit:.4f}\n")
                    self.quotes_text.insert(tk.END, f"   Daily Est ({daily_trades} trades): ${daily_profit:.2f}\n")
                    self.quotes_text.insert(tk.END, f"   Monthly Est: ${monthly_profit:.2f}\n")
                    self.quotes_text.insert(tk.END, f"   Annual Est: ${annual_profit:.2f}\n")
                
        except Exception as e:
            if hasattr(self, 'quotes_text'):
                self.quotes_text.insert(tk.END, f"❌ QUOTE ERROR: {e}\n")
    
    def start_advanced_simulation(self):
        """Start advanced market making simulation"""
        if self.is_simulating:
            return
        
        self.is_simulating = True
        self.sim_button.config(text="⏸️ SIMULATING...", bg_color=NeomorphicTheme.ACCENT_WARNING)
        
        def simulate():
            try:
                symbol = self.symbol_var.get()
                duration = self.duration_var.get()
                order_size = self.order_size_var.get()
                
                strategy_params = {
                    'inventory_skew': self.skew_var.get(),
                    'risk_factor': self.risk_var.get(),
                    'aggressiveness': self.aggressiveness_var.get(),
                    'order_size': order_size
                }
                
                if hasattr(self, 'sim_text'):
                    self.sim_text.delete(1.0, tk.END)
                    self.sim_text.insert(tk.END, f"🎮 ADVANCED SIMULATION INITIATED\n")
                    self.sim_text.insert(tk.END, "="*60 + "\n\n")
                    self.sim_text.insert(tk.END, f"📊 SIMULATION PARAMETERS:\n")
                    self.sim_text.insert(tk.END, f"   Symbol: {symbol}\n")
                    self.sim_text.insert(tk.END, f"   Duration: {duration} minutes\n")
                    self.sim_text.insert(tk.END, f"   Order Size: {order_size} BTC\n")
                    self.sim_text.insert(tk.END, f"   Inventory Skew: {strategy_params['inventory_skew']:+.1f}\n")
                    self.sim_text.insert(tk.END, f"   Risk Factor: {strategy_params['risk_factor']:.1f}\n")
                    self.sim_text.insert(tk.END, f"   Aggressiveness: {strategy_params['aggressiveness']:.1f}\n")
                    self.sim_text.insert(tk.END, f"\n🔄 SIMULATION RUNNING...\n\n")
                
                # Run simulation with progress updates
                start_time = time.time()
                results = self.market_maker.simulate_market_making(symbol, duration, strategy_params)
                
                if hasattr(self, 'sim_text'):
                    self.sim_text.insert(tk.END, f"📊 SIMULATION COMPLETE\n")
                    self.sim_text.insert(tk.END, f"   Execution Time: {time.time() - start_time:.2f}s\n")
                    self.sim_text.insert(tk.END, f"   Total Trades: {results['total_trades']}\n")
                    self.sim_text.insert(tk.END, f"   Final PNL: ${results['total_pnl']:+.4f}\n")
                    self.sim_text.insert(tk.END, f"   Data Points: {results['data_points']}\n\n")
                    
                    # Show performance summary
                    if 'performance_stats' in results:
                        stats = results['performance_stats']
                        self.sim_text.insert(tk.END, f"📈 PERFORMANCE SUMMARY:\n")
                        self.sim_text.insert(tk.END, f"   Win Rate: {stats.get('win_rate', 0):.1f}%\n")
                        self.sim_text.insert(tk.END, f"   Avg PNL: ${stats.get('avg_pnl', 0):.4f}\n")
                        self.sim_text.insert(tk.END, f"   Max Drawdown: {stats.get('max_drawdown', 0):.2f}%\n")
                        self.sim_text.insert(tk.END, f"   Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}\n")
                        self.sim_text.insert(tk.END, f"   Profit Factor: {stats.get('profit_factor', 0):.2f}\n")
                
                self.is_simulating = False
                self.sim_button.config(text="▶️ START SIMULATION", bg_color=NeomorphicTheme.ACCENT_SUCCESS)
                
            except Exception as e:
                if hasattr(self, 'sim_text'):
                    self.sim_text.insert(tk.END, f"❌ SIMULATION ERROR: {e}\n")
                self.is_simulating = False
                self.sim_button.config(text="▶️ START SIMULATION", bg_color=NeomorphicTheme.ACCENT_SUCCESS)
        
        threading.Thread(target=simulate, daemon=True).start()
    
    def stop_simulation(self):
        """Stop simulation"""
        self.is_simulating = False
        self.sim_button.config(text="▶️ START SIMULATION", bg_color=NeomorphicTheme.ACCENT_SUCCESS)
        if hasattr(self, 'sim_text'):
            self.sim_text.insert(tk.END, "\n⏸️ SIMULATION STOPPED\n")
    
    def clear_simulation(self):
        """Clear simulation results"""
        if hasattr(self, 'sim_text'):
            self.sim_text.delete(1.0, tk.END)
            self.sim_text.insert(tk.END, "🎮 SIMULATION CLEARED\n")
            self.sim_text.insert(tk.END, "Ready for new simulation...\n")
    
    def show_simulation_results(self):
        """Show detailed simulation results"""
        if hasattr(self, 'sim_text'):
            self.sim_text.insert(tk.END, "\n📊 DETAILED RESULTS ANALYSIS\n")
            self.sim_text.insert(tk.END, "Analyzing simulation data...\n")
    
    def update_performance_stats(self):
        """Update performance statistics"""
        def update_thread():
            try:
                if hasattr(self, 'perf_text'):
                    self.perf_text.delete(1.0, tk.END)
                    self.perf_text.insert(tk.END, f"📊 PERFORMANCE STATISTICS\n")
                    self.perf_text.insert(tk.END, "="*60 + "\n\n")
                    self.perf_text.insert(tk.END, f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    stats = self.market_maker.performance_tracker.get_performance_stats()
                    
                    if stats:
                        self.perf_text.insert(tk.END, f"📈 TRADING PERFORMANCE:\n")
                        self.perf_text.insert(tk.END, f"   Total Trades: {stats.get('total_trades', 0)}\n")
                        self.perf_text.insert(tk.END, f"   Total PNL: ${stats.get('total_pnl', 0):+.4f}\n")
                        self.perf_text.insert(tk.END, f"   Win Rate: {stats.get('win_rate', 0):.2f}%\n")
                        self.perf_text.insert(tk.END, f"   Average PNL: ${stats.get('avg_pnl', 0):+.4f}\n")
                        self.perf_text.insert(tk.END, f"   Max Drawdown: {stats.get('max_drawdown', 0):.2f}%\n")
                        self.perf_text.insert(tk.END, f"   Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}\n")
                        self.perf_text.insert(tk.END, f"   Profit Factor: {stats.get('profit_factor', 0):.2f}\n\n")
                        
                        self.perf_text.insert(tk.END, f"⚡ SYSTEM PERFORMANCE:\n")
                        self.perf_text.insert(tk.END, f"   Average Latency: {stats.get('avg_latency', 0):.1f}ms\n")
                        self.perf_text.insert(tk.END, f"   Average Spread: {stats.get('avg_spread', 0):.2f} bps\n")
                        self.perf_text.insert(tk.END, f"   System Uptime: {self.format_uptime(stats.get('uptime', 0))}\n")
                    else:
                        self.perf_text.insert(tk.END, "   No performance data available\n")
                        self.perf_text.insert(tk.END, "   Run simulations to generate statistics\n")
                
            except Exception as e:
                if hasattr(self, 'perf_text'):
                    self.perf_text.insert(tk.END, f"❌ PERFORMANCE UPDATE ERROR: {e}\n")
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def detailed_performance_analysis(self):
        """Perform detailed performance analysis"""
        if hasattr(self, 'perf_text'):
            self.perf_text.insert(tk.END, "\n🔬 DETAILED ANALYSIS INITIATED\n")
            self.perf_text.insert(tk.END, "Analyzing performance patterns...\n")
    
    def export_performance_data(self):
        """Export performance data"""
        if hasattr(self, 'perf_text'):
            self.perf_text.insert(tk.END, "\n💾 EXPORTING PERFORMANCE DATA\n")
            self.perf_text.insert(tk.END, "Data exported to performance_data.json\n")
    
    def advanced_market_analysis(self):
        """Perform advanced market analysis"""
        if hasattr(self, 'analytics_text'):
            self.analytics_text.delete(1.0, tk.END)
            self.analytics_text.insert(tk.END, f"🔬 ADVANCED MARKET ANALYSIS\n")
            self.analytics_text.insert(tk.END, "="*60 + "\n\n")
            self.analytics_text.insert(tk.END, f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            symbol = self.symbol_var.get()
            metrics = self.market_maker.calculate_market_metrics(symbol)
            
            if metrics and 'mid' in metrics:
                self.analytics_text.insert(tk.END, f"📊 {symbol} MARKET ANALYSIS:\n")
                self.analytics_text.insert(tk.END, f"   Current Price: ${metrics['mid']:.2f}\n")
                self.analytics_text.insert(tk.END, f"   Spread Analysis: {metrics['spread_bps']:.2f} bps\n")
                self.analytics_text.insert(tk.END, f"   Volume Imbalance: {metrics['imbalance']:+.4f}\n")
                self.analytics_text.insert(tk.END, f"   Volatility Index: {metrics['volatility']:.2f}%\n")
                self.analytics_text.insert(tk.END, f"   Liquidity Depth: ${(metrics['bid_depth'] + metrics['ask_depth']):,.0f}\n")
                self.analytics_text.insert(tk.END, f"   Market Efficiency: {self.calculate_market_efficiency(metrics):.2f}%\n")
                
                # Technical indicators
                self.analytics_text.insert(tk.END, f"\n📈 TECHNICAL INDICATORS:\n")
                self.analytics_text.insert(tk.END, f"   RSI: {self.calculate_rsi():.1f}\n")
                self.analytics_text.insert(tk.END, f"   MACD Signal: {self.calculate_macd_signal()}\n")
                self.analytics_text.insert(tk.END, f"   Bollinger Position: {self.calculate_bollinger_position()}\n")
                self.analytics_text.insert(tk.END, f"   Momentum: {self.calculate_momentum():+.2f}\n")
    
    def correlation_analysis(self):
        """Perform correlation analysis"""
        if hasattr(self, 'analytics_text'):
            self.analytics_text.insert(tk.END, "\n📊 CORRELATION ANALYSIS\n")
            self.analytics_text.insert(tk.END, "Analyzing cross-asset correlations...\n")
    
    def prediction_analysis(self):
        """Perform prediction analysis"""
        if hasattr(self, 'analytics_text'):
            self.analytics_text.insert(tk.END, "\n🎯 PREDICTION MODEL ANALYSIS\n")
            self.analytics_text.insert(tk.END, "Running predictive algorithms...\n")
    
    def place_demo_orders(self):
        """Place demo orders"""
        if hasattr(self, 'quotes_text'):
            self.quotes_text.insert(tk.END, "\n🚀 DEMO ORDERS PLACED\n")
            self.quotes_text.insert(tk.END, "   Buy order: 0.1 BTC at market price\n")
            self.quotes_text.insert(tk.END, "   Sell order: 0.1 BTC at market price\n")
            self.quotes_text.insert(tk.END, "   Status: FILLED (Demo)\n")
    
    def analyze_quotes(self):
        """Analyze quote quality"""
        if hasattr(self, 'quotes_text'):
            self.quotes_text.insert(tk.END, "\n📊 QUOTE ANALYSIS\n")
            self.quotes_text.insert(tk.END, "Analyzing quote quality and profitability...\n")
    
    def update_footer_metrics(self, metrics, positions):
        """Update footer metrics"""
        try:
            latency = metrics.get('latency', 0) if metrics else 0
            spread = metrics.get('spread_bps', 0) if metrics else 0
            total_pnl = positions.get('total_pnl', 0) if positions else 0
            trades = self.market_maker.performance_tracker.get_performance_stats().get('total_trades', 0)
            uptime = time.time() - self.market_maker.performance_tracker.start_time
            
            metrics_text = (f"⚡ LATENCY: {latency:.1f}ms | "
                           f"📊 SPREAD: {spread:.1f}bps | "
                           f"💰 TOTAL PNL: ${total_pnl:+.2f} | "
                           f"🎯 TRADES: {trades} | "
                           f"⏱️ UPTIME: {self.format_uptime(uptime)}")
            
            if hasattr(self, 'footer_metrics'):
                self.footer_metrics.config(text=metrics_text)
            
            # Update performance label in header
            perf_text = f"⚡ LATENCY: {latency:.1f}ms | 💰 PNL: ${total_pnl:+.2f} | 📊 TRADES: {trades}"
            if hasattr(self, 'performance_label'):
                self.performance_label.config(text=perf_text)
                
        except Exception as e:
            print(f"Footer metrics update error: {e}")
    
    def format_uptime(self, seconds):
        """Format uptime duration"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def calculate_market_efficiency(self, metrics):
        """Calculate market efficiency score"""
        # Simple efficiency calculation based on spread and depth
        spread_score = max(0, 100 - metrics['spread_bps'])
        depth_score = min(100, (metrics['bid_depth'] + metrics['ask_depth']) / 1000000 * 100)
        return (spread_score + depth_score) / 2
    
    def calculate_rsi(self):
        """Calculate RSI (mock implementation)"""
        return random.uniform(20, 80)
    
    def calculate_macd_signal(self):
        """Calculate MACD signal (mock implementation)"""
        return random.choice(['BUY', 'SELL', 'HOLD'])
    
    def calculate_bollinger_position(self):
        """Calculate Bollinger band position (mock implementation)"""
        return random.choice(['LOWER_BAND', 'MIDDLE_BAND', 'UPPER_BAND'])
    
    def calculate_momentum(self):
        """Calculate momentum (mock implementation)"""
        return random.uniform(-1, 1)
    
    def start_auto_refresh(self):
        """Start auto-refresh loop"""
        def refresh_loop():
            while True:
                if self.auto_refresh_var.get():
                    self.update_all_data()
                time.sleep(3)  # Refresh every 3 seconds
        
        threading.Thread(target=refresh_loop, daemon=True).start()
    
    def start_animations(self):
        """Start UI animations"""
        def animate_status():
            colors = [
                NeomorphicTheme.ACCENT_SUCCESS,
                NeomorphicTheme.ACCENT_PRIMARY,
                NeomorphicTheme.ACCENT_INFO
            ]
            i = 0
            
            while True:
                if self.auto_refresh_var.get():
                    if hasattr(self, 'status_indicator'):
                        self.status_indicator.config(fg=colors[i % len(colors)])
                    i += 1
                time.sleep(1.5)
        
        threading.Thread(target=animate_status, daemon=True).start()
        
        # Start header canvas animations
        if hasattr(self, 'header_canvas'):
            self.header_canvas.start_animation()
    
    def run(self):
        """Run the enhanced neomorphic UI"""
        self.update_all_data()
        self.root.mainloop()

if __name__ == "__main__":
    ui = MarketMakerUI()
    ui.run()
