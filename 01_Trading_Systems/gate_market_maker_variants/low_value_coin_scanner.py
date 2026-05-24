#!/usr/bin/env python3
import os
"""
LOW VALUE COIN SCANNER
Find coins trading below $0.10 at nominal minimum values
"""

import gate_api
from gate_api import ApiClient, Configuration, FuturesApi, SpotApi
import json
import time
from datetime import datetime
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

class LowValueCoinScanner:
    def __init__(self):
        # API Configuration
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        
        # Initialize clients
        self.cfg = Configuration(key=self.api_key, secret=self.api_secret)
        self.futures_client = FuturesApi(ApiClient(self.cfg))
        self.spot_client = SpotApi(ApiClient(self.cfg))
        
        # Target criteria
        self.max_price = 0.10  # 10 cents
        self.min_volume_24h = 100000  # Minimum $100k volume
        
    def get_all_futures_contracts(self):
        """Get all available futures contracts"""
        try:
            contracts = self.futures_client.list_futures_contracts(settle='usdt')
            return contracts
        except Exception as e:
            print(f"Error fetching contracts: {e}")
            return []
    
    def get_all_spot_pairs(self):
        """Get all available spot pairs"""
        try:
            pairs = self.spot_client.list_spot_currency_pairs()
            return pairs
        except Exception as e:
            print(f"Error fetching spot pairs: {e}")
            return []
    
    def get_futures_ticker(self, contract):
        """Get futures ticker data"""
        try:
            tickers = self.futures_client.list_futures_tickers(settle='usdt')
            for ticker in tickers:
                if ticker.contract == contract:
                    return ticker
            return None
        except Exception as e:
            print(f"Error fetching futures ticker for {contract}: {e}")
            return None
    
    def get_spot_ticker(self, pair):
        """Get spot ticker data"""
        try:
            tickers = self.spot_client.list_tickers()
            for ticker in tickers:
                if ticker.currency_pair == pair:
                    return ticker
            return None
        except Exception as e:
            print(f"Error fetching spot ticker for {pair}: {e}")
            return None
    
    def scan_low_value_coins(self):
        """Scan for coins below $0.10 with good volume"""
        print("🔍 SCANNING FOR LOW VALUE COINS (< $0.10)")
        print("=" * 60)
        
        opportunities = []
        
        # Scan futures contracts
        print("\n📈 SCANNING FUTURES CONTRACTS...")
        contracts = self.get_all_futures_contracts()
        
        for contract in contracts:
            if contract.quoted_currency == 'USDT':
                ticker = self.get_futures_ticker(contract.name)
                if ticker:
                    price = float(ticker.last)
                    volume = float(ticker.base_volume)
                    
                    if price > 0 and price < self.max_price:
                        opportunities.append({
                            'type': 'FUTURES',
                            'symbol': contract.name,
                            'price': price,
                            'volume_24h': volume * price,  # Convert to USD
                            'change_24h': float(ticker.change_percentage),
                            'high_24h': float(ticker.high_24h),
                            'low_24h': float(ticker.low_24h)
                        })
        
        # Scan spot pairs
        print("\n💰 SCANNING SPOT PAIRS...")
        pairs = self.get_all_spot_pairs()
        
        for pair in pairs:
            if pair.quote == 'USDT' and pair.trade_status == 'tradable':
                ticker = self.get_spot_ticker(pair.id)
                if ticker:
                    price = float(ticker.last)
                    volume = float(ticker.base_volume)
                    
                    if price > 0 and price < self.max_price:
                        opportunities.append({
                            'type': 'SPOT',
                            'symbol': pair.id,
                            'price': price,
                            'volume_24h': volume * price,  # Convert to USD
                            'change_24h': float(ticker.change_percentage),
                            'high_24h': float(ticker.high_24h),
                            'low_24h': float(ticker.low_24h)
                        })
        
        # Filter by minimum volume
        filtered_opportunities = [
            opp for opp in opportunities 
            if opp['volume_24h'] >= self.min_volume_24h
        ]
        
        # Sort by price (lowest first)
        filtered_opportunities.sort(key=lambda x: x['price'])
        
        return filtered_opportunities
    
    def analyze_opportunity(self, opportunity):
        """Analyze a specific opportunity"""
        analysis = []
        
        # Price analysis
        price = opportunity['price']
        if price < 0.01:
            price_category = "SUB-PENNY (< 1¢)"
        elif price < 0.05:
            price_category = "PENNY STOCK (1-5¢)"
        else:
            price_category = "LOW VALUE (5-10¢)"
        
        analysis.append(f"💰 Price Category: {price_category}")
        
        # Volume analysis
        volume = opportunity['volume_24h']
        if volume > 1000000:
            volume_category = "HIGH VOLUME"
        elif volume > 500000:
            volume_category = "MEDIUM VOLUME"
        else:
            volume_category = "MINIMUM VOLUME"
        
        analysis.append(f"📊 Volume: {volume_category} (${volume:,.0f})")
        
        # 24h change analysis
        change = opportunity['change_24h']
        if change > 10:
            trend = "🚀 STRONG UP"
        elif change > 5:
            trend = "📈 MODERATE UP"
        elif change < -10:
            trend = "📉 STRONG DOWN"
        elif change < -5:
            trend = "📉 MODERATE DOWN"
        else:
            trend = "⚖️ STABLE"
        
        analysis.append(f"📈 24h Trend: {trend} ({change:+.2f}%)")
        
        # Range analysis
        high = opportunity['high_24h']
        low = opportunity['low_24h']
        range_pct = ((high - low) / low) * 100
        
        if range_pct > 50:
            volatility = "🔴 EXTREME VOLATILITY"
        elif range_pct > 25:
            volatility = "🟡 HIGH VOLATILITY"
        elif range_pct > 10:
            volatility = "🟢 MODERATE VOLATILITY"
        else:
            volatility = "🔵 LOW VOLATILITY"
        
        analysis.append(f"🌊 Volatility: {volatility} ({range_pct:.1f}% range)")
        
        # Trading recommendation
        if price < 0.01 and volume > 500000 and abs(change) < 20:
            recommendation = "✅ GOOD OPPORTUNITY - Low price, decent volume"
        elif price < 0.05 and volume > 1000000:
            recommendation = "✅ POTENTIAL OPPORTUNITY - Monitor closely"
        elif abs(change) > 30:
            recommendation = "⚠️ HIGH RISK - Extreme volatility"
        else:
            recommendation = "⚖️ OBSERVE - Wait for better setup"
        
        analysis.append(f"🎯 Recommendation: {recommendation}")
        
        return analysis

class LowValueScannerUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔍 LOW VALUE COIN SCANNER")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0a0a')
        
        self.scanner = LowValueCoinScanner()
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#0a0a0a', height=80)
        title_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(title_frame, text="🔍 LOW VALUE COIN SCANNER", 
                font=('Arial', 18, 'bold'), fg='#00ff88', bg='#0a0a0a').pack(side='top')
        tk.Label(title_frame, text="Find coins trading below $0.10 with good volume", 
                font=('Arial', 11), fg='#666', bg='#0a0a0a').pack(side='top')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel - Controls
        left_panel = tk.Frame(main_frame, bg='#1a1a1a', width=300)
        left_panel.pack(side='left', fill='y', padx=(0, 5))
        left_panel.pack_propagate(False)
        
        self.setup_controls(left_panel)
        
        # Right panel - Results
        right_panel = tk.Frame(main_frame, bg='#1a1a1a')
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        self.setup_results(right_panel)
        
        # Status bar
        self.setup_status_bar()
    
    def setup_controls(self, parent):
        tk.Label(parent, text="⚙️ SCAN SETTINGS", 
                font=('Arial', 14, 'bold'), fg='#00ff88', bg='#1a1a1a').pack(pady=10)
        
        # Max price setting
        price_frame = tk.Frame(parent, bg='#1a1a1a')
        price_frame.pack(pady=10, padx=10, fill='x')
        
        tk.Label(price_frame, text="Max Price ($):", fg='#fff', bg='#1a1a1a').pack(anchor='w')
        self.max_price_var = tk.DoubleVar(value=0.10)
        price_scale = tk.Scale(price_frame, from_=0.001, to=0.50, resolution=0.001,
                              orient='horizontal', variable=self.max_price_var, 
                              bg='#1a1a1a', fg='#fff', highlightthickness=0)
        price_scale.pack(fill='x')
        
        # Min volume setting
        volume_frame = tk.Frame(parent, bg='#1a1a1a')
        volume_frame.pack(pady=10, padx=10, fill='x')
        
        tk.Label(volume_frame, text="Min Volume ($):", fg='#fff', bg='#1a1a1a').pack(anchor='w')
        self.min_volume_var = tk.IntVar(value=100000)
        volume_scale = tk.Scale(volume_frame, from_=10000, to=10000000, resolution=10000,
                               orient='horizontal', variable=self.min_volume_var,
                               bg='#1a1a1a', fg='#fff', highlightthickness=0)
        volume_scale.pack(fill='x')
        
        # Scan button
        self.scan_button = tk.Button(parent, text="🔍 START SCAN", 
                                    command=self.start_scan,
                                    bg='#00ff88', fg='#000', font=('Arial', 12, 'bold'),
                                    height=2)
        self.scan_button.pack(pady=20, padx=10, fill='x')
        
        # Auto-scan checkbox
        self.auto_scan_var = tk.BooleanVar(value=False)
        auto_check = tk.Checkbutton(parent, text="Auto-scan every 30 seconds", 
                                   variable=self.auto_scan_var,
                                   bg='#1a1a1a', fg='#fff', selectcolor='#1a1a1a')
        auto_check.pack(pady=10)
    
    def setup_results(self, parent):
        tk.Label(parent, text="📊 SCAN RESULTS", 
                font=('Arial', 14, 'bold'), fg='#00ff88', bg='#1a1a1a').pack(pady=10)
        
        # Results display
        self.results_text = scrolledtext.ScrolledText(parent, height=35, width=80,
                                                     bg='#0a0a0a', fg='#00ff88', 
                                                     font=('Courier', 9))
        self.results_text.pack(padx=10, pady=10, fill='both', expand=True)
        
        # Initial message
        self.results_text.insert(tk.END, "🚀 READY TO SCAN FOR LOW VALUE COINS\n\n")
        self.results_text.insert(tk.END, "💡 This scanner finds coins trading below $0.10\n")
        self.results_text.insert(tk.END, "📊 Filters for minimum trading volume\n")
        self.results_text.insert(tk.END, "🎯 Identifies potential opportunities\n\n")
        self.results_text.insert(tk.END, "Click 'START SCAN' to begin...\n")
    
    def setup_status_bar(self):
        status_frame = tk.Frame(self.root, bg='#1a1a1a', height=30)
        status_frame.pack(fill='x', side='bottom', padx=10, pady=5)
        
        self.status_label = tk.Label(status_frame, text="🟢 READY TO SCAN", 
                                    font=('Arial', 10), fg='#00ff88', bg='#1a1a1a')
        self.status_label.pack(side='left')
    
    def start_scan(self):
        """Start scanning for low value coins"""
        self.scan_button.config(state='disabled', text="🔄 SCANNING...")
        self.status_label.config(text="🔍 SCANNING FOR OPPORTUNITIES...")
        
        def scan():
            try:
                # Update scanner settings
                self.scanner.max_price = self.max_price_var.get()
                self.scanner.min_volume_24h = self.min_volume_var.get()
                
                # Perform scan
                opportunities = self.scanner.scan_low_value_coins()
                
                # Display results
                self.display_results(opportunities)
                
            except Exception as e:
                self.results_text.insert(tk.END, f"\n❌ SCAN ERROR: {e}\n")
            finally:
                self.scan_button.config(state='normal', text="🔍 START SCAN")
                self.status_label.config(text="✅ SCAN COMPLETE")
                
                # Auto-scan logic
                if self.auto_scan_var.get():
                    self.root.after(30000, self.start_scan)  # Scan again in 30 seconds
        
        threading.Thread(target=scan, daemon=True).start()
    
    def display_results(self, opportunities):
        """Display scan results"""
        self.results_text.delete(1.0, tk.END)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.results_text.insert(tk.END, f"🔍 SCAN RESULTS - {timestamp}\n")
        self.results_text.insert(tk.END, "="*70 + "\n\n")
        
        if not opportunities:
            self.results_text.insert(tk.END, "❌ No opportunities found matching criteria\n")
            self.results_text.insert(tk.END, "💡 Try adjusting price/volume filters\n")
            return
        
        self.results_text.insert(tk.END, f"🎯 FOUND {len(opportunities)} OPPORTUNITIES\n\n")
        
        for i, opp in enumerate(opportunities, 1):
            # Header
            self.results_text.insert(tk.END, f"{i}. {opp['type']}: {opp['symbol']}\n")
            self.results_text.insert(tk.END, "-"*50 + "\n")
            
            # Basic info
            self.results_text.insert(tk.END, f"💰 Price: ${opp['price']:.6f}\n")
            self.results_text.insert(tk.END, f"📊 Volume 24h: ${opp['volume_24h']:,.0f}\n")
            self.results_text.insert(tk.END, f"📈 Change 24h: {opp['change_24h']:+.2f}%\n")
            self.results_text.insert(tk.END, f"📊 Range: ${opp['low_24h']:.6f} - ${opp['high_24h']:.6f}\n")
            
            # AI Analysis
            analysis = self.scanner.analyze_opportunity(opp)
            self.results_text.insert(tk.END, f"\n🤖 AI ANALYSIS:\n")
            for line in analysis:
                self.results_text.insert(tk.END, f"   {line}\n")
            
            self.results_text.insert(tk.END, "\n")
        
        # Summary
        self.results_text.insert(tk.END, "="*70 + "\n")
        self.results_text.insert(tk.END, f"📈 SUMMARY: {len(opportunities)} coins under ${self.scanner.max_price:.3f}\n")
        self.results_text.insert(tk.END, f"💰 Total Volume: ${sum(opp['volume_24h'] for opp in opportunities):,.0f}\n")
        
        # Scroll to top
        self.results_text.see(tk.END)
    
    def run(self):
        """Run the UI"""
        self.root.mainloop()

if __name__ == "__main__":
    ui = LowValueScannerUI()
    ui.run()
