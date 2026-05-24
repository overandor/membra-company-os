#!/usr/bin/env python3
"""
ADVANCED GATE.IO TRADING BOT - FULL ACCOUNT INTEGRATION
- Real account balance detection
- Cross-account fund shuffling
- Maximized futures trading (coin-margined + delivery)
- Real order execution
- Actual $7.38 budget usage
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
from typing import Dict, List, Optional, Set, Tuple
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

class AccountType(Enum):
    SPOT = "spot"
    MARGIN = "margin"
    FUTURES = "futures"
    DELIVERY = "delivery"

class FuturesType(Enum):
    USDT_MARGINED = "USDT-MARGINED"
    COIN_MARGINED = "COIN-MARGINED"
    DELIVERY = "DELIVERY"

@dataclass
class AccountBalance:
    account_type: AccountType
    currency: str
    available: float
    frozen: float
    total: float

@dataclass
class FuturesContract:
    symbol: str
    contract_type: FuturesType
    base_currency: str
    quote_currency: str
    last_price: float
    nominal_value: float
    volume_24h: float
    leverage: int
    margin_mode: str

@dataclass
class LivePosition:
    symbol: str
    contract_type: FuturesType
    side: str
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    margin_used: float
    leverage: int
    funding_rate: float = 0.0

class AdvancedGateioBot:
    """Advanced Gate.io bot with full account integration"""
    
    def __init__(self):
        # REAL API CREDENTIALS
        self.api_key = os.getenv("GATE_API_KEY", os.environ.get("GATE_API_KEY", ""))
        self.api_secret = os.getenv("GATE_API_SECRET", os.environ.get("GATE_API_SECRET", ""))
        self.base_url = "https://api.gateio.ws"
        self.dry_run = False  # LIVE TRADING ENABLED
        
        # Account balances (will be fetched from real account)
        self.account_balances = {}
        self.total_usdt_balance = 0.0
        self.available_balance = 0.0
        
        # Trading configuration
        self.micro_cap_range = (0.001, 0.10)  # $0.001-$0.10
        self.pump_threshold = 0.10  # 10% pump
        self.profit_target = 0.05   # 5% profit
        self.stop_loss = 0.03       # 3% stop loss
        self.max_positions = 10
        
        # Futures optimization
        self.futures_contracts = []
        self.active_positions = []
        self.profit_symbols_today = set()
        
        # Statistics
        self.total_trades = 0
        self.successful_trades = 0
        self.total_pnl = 0.0
        self.fees_paid = 0.0
        
        logger.info("🚀 ADVANCED GATE.IO BOT INITIALIZED")
        logger.info(f"🔑 API Key: {self.api_key[:10]}...")
        logger.info(f"⚡ Live Trading: {not self.dry_run}")
        
        # Note: Account initialization will be called separately
    
    def generate_signature(self, method: str, url: str, params: dict = None, timestamp: str = None) -> str:
        """Generate Gate.io API signature"""
        if timestamp is None:
            timestamp = str(int(time.time()))
        
        if params is None:
            params = {}
        
        query_string = urlencode(sorted(params.items()))
        message = method + '\n' + url + '\n' + query_string
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return signature
    
    async def make_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Make authenticated API request"""
        try:
            url = f"{self.base_url}{endpoint}"
            timestamp = str(int(time.time()))
            
            headers = {
                'KEY': self.api_key,
                'Timestamp': timestamp,
                'SIGN': self.generate_signature(method, endpoint, params, timestamp)
            }
            
            if method == 'GET':
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params, timeout=10) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"Request failed: {response.status} - {error_text}")
                            return {}
            
            elif method == 'POST':
                headers['Content-Type'] = 'application/json'
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=params, timeout=10) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"Request failed: {response.status} - {error_text}")
                            return {}
        
        except Exception as e:
            logger.error(f"API request error: {e}")
            return {}
    
    async def initialize_account(self):
        """Initialize account connection and get real balances"""
        logger.info("🔌 Connecting to Gate.io account...")
        
        # Get spot account balance
        spot_data = await self.make_request('GET', '/api/v4/spot/accounts')
        if spot_data:
            for balance in spot_data:
                currency = balance['currency']
                available = float(balance['available'])
                frozen = float(balance['frozen'])
                total = float(balance['total'])
                
                if total > 0:
                    self.account_balances[f"spot_{currency}"] = AccountBalance(
                        account_type=AccountType.SPOT,
                        currency=currency,
                        available=available,
                        frozen=frozen,
                        total=total
                    )
                    
                    if currency == 'USDT':
                        self.total_usdt_balance += total
                        self.available_balance += available
        
        # Get futures account balance
        futures_data = await self.make_request('GET', '/api/v4/futures/accounts')
        if futures_data:
            for balance in futures_data:
                currency = balance['currency']
                available = float(balance['available'])
                frozen = float(balance['frozen'])
                total = float(balance['total'])
                
                if total > 0:
                    self.account_balances[f"futures_{currency}"] = AccountBalance(
                        account_type=AccountType.FUTURES,
                        currency=currency,
                        available=available,
                        frozen=frozen,
                        total=total
                    )
        
        # Get delivery account balance
        delivery_data = await self.make_request('GET', '/api/v4/delivery/accounts')
        if delivery_data:
            for balance in delivery_data:
                currency = balance['currency']
                available = float(balance['available'])
                frozen = float(balance['frozen'])
                total = float(balance['total'])
                
                if total > 0:
                    self.account_balances[f"delivery_{currency}"] = AccountBalance(
                        account_type=AccountType.DELIVERY,
                        currency=currency,
                        available=available,
                        frozen=frozen,
                        total=total
                    )
        
        logger.info(f"💰 Account Connected - Total USDT: ${self.total_usdt_balance:.2f}")
        logger.info(f"💸 Available: ${self.available_balance:.2f}")
        
        # Get all futures contracts
        await self.load_futures_contracts()
    
    async def load_futures_contracts(self):
        """Load all available futures contracts"""
        logger.info("📊 Loading futures contracts...")
        
        # Get USDT-margined futures
        usdt_futures = await self.make_request('GET', '/api/v4/futures/usdt/contracts')
        if usdt_futures:
            for contract in usdt_futures:
                if contract['status'] == 'open':
                    futures_contract = FuturesContract(
                        symbol=contract['name'],
                        contract_type=FuturesType.USDT_MARGINED,
                        base_currency=contract['base'],
                        quote_currency='USDT',
                        last_price=float(contract['last']),
                        nominal_value=float(contract['contract_size']) * float(contract['last']),
                        volume_24h=float(contract['volume_24h']),
                        leverage=int(contract['leverage']),
                        margin_mode=contract['margin_mode']
                    )
                    self.futures_contracts.append(futures_contract)
        
        # Get coin-margined futures
        coin_futures = await self.make_request('GET', '/api/v4/futures/contracts')
        if coin_futures:
            for contract in coin_futures:
                if contract['status'] == 'open':
                    futures_contract = FuturesContract(
                        symbol=contract['name'],
                        contract_type=FuturesType.COIN_MARGINED,
                        base_currency=contract['base'],
                        quote_currency=contract['quote'],
                        last_price=float(contract['last']),
                        nominal_value=float(contract['contract_size']) * float(contract['last']),
                        volume_24h=float(contract['volume_24h']),
                        leverage=int(contract['leverage']),
                        margin_mode=contract['margin_mode']
                    )
                    self.futures_contracts.append(futures_contract)
        
        # Get delivery futures
        delivery_futures = await self.make_request('GET', '/api/v4/delivery/contracts')
        if delivery_futures:
            for contract in delivery_futures:
                if contract['status'] == 'open':
                    futures_contract = FuturesContract(
                        symbol=contract['name'],
                        contract_type=FuturesType.DELIVERY,
                        base_currency=contract['base'],
                        quote_currency=contract['quote'],
                        last_price=float(contract['last']),
                        nominal_value=float(contract['contract_size']) * float(contract['last']),
                        volume_24h=float(contract['volume_24h']),
                        leverage=int(contract['leverage']),
                        margin_mode=contract['margin_mode']
                    )
                    self.futures_contracts.append(futures_contract)
        
        # Filter for micro-cap contracts
        self.futures_contracts = [
            c for c in self.futures_contracts 
            if self.micro_cap_range[0] <= c.nominal_value <= self.micro_cap_range[1]
        ]
        
        logger.info(f"📊 Loaded {len(self.futures_contracts)} micro-cap futures contracts")
    
    async def shuffle_funds(self, from_account: AccountType, to_account: AccountType, currency: str, amount: float):
        """Shuffle funds between accounts"""
        logger.info(f"💸 Shuffling ${amount:.2f} {currency} from {from_account.value} to {to_account.value}")
        
        if from_account == AccountType.SPOT and to_account == AccountType.FUTURES:
            # Transfer from spot to futures
            params = {
                'currency': currency,
                'amount': str(amount),
                'to': 'futures'
            }
            result = await self.make_request('POST', '/api/v4/wallet/transfers', params)
            
        elif from_account == AccountType.FUTURES and to_account == AccountType.SPOT:
            # Transfer from futures to spot
            params = {
                'currency': currency,
                'amount': str(amount),
                'from': 'futures'
            }
            result = await self.make_request('POST', '/api/v4/wallet/transfers', params)
        
        else:
            logger.error(f"Transfer from {from_account.value} to {to_account.value} not implemented")
            return False
        
        if result:
            logger.info(f"✅ Fund transfer successful: {result}")
            return True
        else:
            logger.error(f"❌ Fund transfer failed")
            return False
    
    async def get_micro_cap_opportunities(self) -> List[FuturesContract]:
        """Get micro-cap contracts with pump opportunities"""
        opportunities = []
        
        for contract in self.futures_contracts:
            # Get ticker data for price change
            ticker_data = await self.make_request('GET', f'/api/v4/futures/usdt/tickers', {'contract': contract.symbol})
            
            if ticker_data:
                ticker = ticker_data[0]
                price_change = float(ticker['change_percentage']) / 100
                
                # Check for pump opportunity
                if price_change >= self.pump_threshold:
                    if contract.symbol not in self.profit_symbols_today:
                        opportunities.append(contract)
                        logger.info(f"🚀 PUMP OPPORTUNITY: {contract.symbol} +{price_change*100:.1f}% | Nominal: ${contract.nominal_value:.6f}")
        
        # Sort by nominal value (smallest first)
        opportunities.sort(key=lambda x: x.nominal_value)
        
        return opportunities
    
    async def place_futures_order(self, contract: FuturesContract, side: str, size: float, price: float = None) -> dict:
        """Place real futures order"""
        try:
            if contract.contract_type == FuturesType.USDT_MARGINED:
                endpoint = '/api/v4/futures/usdt/orders'
            elif contract.contract_type == FuturesType.COIN_MARGINED:
                endpoint = '/api/v4/futures/orders'
            elif contract.contract_type == FuturesType.DELIVERY:
                endpoint = '/api/v4/delivery/orders'
            else:
                logger.error(f"Unknown contract type: {contract.contract_type}")
                return {}
            
            order_data = {
                'contract': contract.symbol,
                'size': str(size),
                'price': str(price) if price else '0',  # Market order if no price
                'tif': 'ioc'  # Immediate or Cancel
            }
            
            if not price:
                order_data['type'] = 'market'
            else:
                order_data['type'] = 'limit'
            
            if self.dry_run:
                logger.info(f"🧪 DRY RUN: Would place {side} {contract.symbol} - Size: {size}")
                return {'id': f'dry_{int(time.time())}', 'status': 'filled'}
            
            result = await self.make_request('POST', endpoint, order_data)
            
            if result:
                logger.info(f"✅ ORDER PLACED: {side} {contract.symbol} - Size: {size} - ID: {result.get('id')}")
                return result
            else:
                logger.error(f"❌ ORDER FAILED: {side} {contract.symbol}")
                return {}
        
        except Exception as e:
            logger.error(f"Failed to place order for {contract.symbol}: {e}")
            return {}
    
    async def place_micro_short(self, contract: FuturesContract) -> bool:
        """Place micro short position"""
        try:
            # Calculate position size based on available balance
            position_value = min(self.available_balance * 0.1, 1.0)  # Use 10% of available, max $1
            size = position_value / contract.nominal_value
            
            # Place short order
            order_result = await self.place_futures_order(contract, 'sell', size)
            
            if order_result and 'id' in order_result:
                position = LivePosition(
                    symbol=contract.symbol,
                    contract_type=contract.contract_type,
                    side='short',
                    size=size,
                    entry_price=contract.last_price,
                    mark_price=contract.last_price,
                    unrealized_pnl=0.0,
                    margin_used=position_value / contract.leverage,
                    leverage=contract.leverage
                )
                
                self.active_positions.append(position)
                self.total_trades += 1
                self.available_balance -= position_value
                
                logger.info(f"📉 MICRO SHORT OPENED: {contract.symbol}")
                logger.info(f"   Size: {size:.6f} | Value: ${position_value:.4f}")
                logger.info(f"   Leverage: {contract.leverage}x | Margin: ${position.margin_used:.4f}")
                
                return True
            else:
                return False
        
        except Exception as e:
            logger.error(f"Failed to place micro short for {contract.symbol}: {e}")
            return False
    
    async def close_position(self, position: LivePosition) -> bool:
        """Close position with opposite order"""
        try:
            # Find the contract
            contract = next((c for c in self.futures_contracts if c.symbol == position.symbol), None)
            if not contract:
                logger.error(f"Contract not found for {position.symbol}")
                return False
            
            # Place opposite order
            close_side = 'buy' if position.side == 'sell' else 'sell'
            order_result = await self.place_futures_order(contract, close_side, position.size)
            
            if order_result and 'id' in order_result:
                # Calculate realized PnL
                realized_pnl = position.unrealized_pnl
                self.total_pnl += realized_pnl
                self.successful_trades += 1
                
                # Release margin back to available balance
                self.available_balance += position.margin_used
                
                # Add to profit symbols
                self.profit_symbols_today.add(position.symbol)
                
                logger.info(f"✅ POSITION CLOSED: {position.symbol}")
                logger.info(f"   Realized PnL: ${realized_pnl:.4f}")
                logger.info(f"   Margin Released: ${position.margin_used:.4f}")
                
                return True
            else:
                logger.error(f"Failed to close position for {position.symbol}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to close position for {position.symbol}: {e}")
            return False
    
    async def monitor_positions(self):
        """Monitor and manage active positions"""
        for position in self.active_positions[:]:
            try:
                # Get current position data
                if position.contract_type == FuturesType.USDT_MARGINED:
                    endpoint = '/api/v4/futures/usdt/positions'
                elif position.contract_type == FuturesType.COIN_MARGINED:
                    endpoint = '/api/v4/futures/positions'
                elif position.contract_type == FuturesType.DELIVERY:
                    endpoint = '/api/v4/delivery/positions'
                else:
                    continue
                
                positions_data = await self.make_request('GET', endpoint, {'contract': position.symbol})
                
                if positions_data:
                    current_pos = positions_data[0]
                    position.mark_price = float(current_pos['mark_price'])
                    position.unrealized_pnl = float(current_pos['unrealised_pnl'])
                    
                    # Calculate PnL percentage
                    pnl_pct = (position.unrealized_pnl / position.margin_used) * 100 if position.margin_used > 0 else 0
                    
                    # Check for profit taking
                    if pnl_pct >= self.profit_target * 100:
                        logger.info(f"💰 PROFIT TARGET HIT: {position.symbol} (+{pnl_pct:.2f}%)")
                        if await self.close_position(position):
                            self.active_positions.remove(position)
                    
                    # Check for stop loss
                    elif pnl_pct <= -self.stop_loss * 100:
                        logger.info(f"❌ STOP LOSS HIT: {position.symbol} ({pnl_pct:.2f}%)")
                        if await self.close_position(position):
                            self.active_positions.remove(position)
            
            except Exception as e:
                logger.error(f"Error monitoring position {position.symbol}: {e}")
    
    async def run_trading_cycle(self):
        """Main trading cycle"""
        logger.info("🔄 Starting trading cycle...")
        
        # Get opportunities
        opportunities = await self.get_micro_cap_opportunities()
        logger.info(f"🎯 Found {len(opportunities)} micro-cap opportunities")
        
        # Place new positions
        for contract in opportunities[:3]:  # Limit to 3 new positions per cycle
            if len(self.active_positions) < self.max_positions:
                if self.available_balance > 1.0:  # Need at least $1 available
                    if await self.place_micro_short(contract):
                        logger.info(f"✅ New position opened for {contract.symbol}")
        
        # Monitor existing positions
        await self.monitor_positions()
        
        # Optimize fund allocation
        await self.optimize_fund_allocation()
    
    async def optimize_fund_allocation(self):
        """Optimize fund allocation across accounts"""
        try:
            # Check if we need more funds in futures
            futures_usdt = self.account_balances.get('futures_USDT')
            spot_usdt = self.account_balances.get('spot_USDT')
            
            if futures_usdt and spot_usdt:
                # If futures has less than $2 and spot has more than $5, transfer $2
                if futures_usdt.available < 2.0 and spot_usdt.available > 5.0:
                    transfer_amount = min(2.0, spot_usdt.available - 1.0)
                    await self.shuffle_funds(AccountType.SPOT, AccountType.FUTURES, 'USDT', transfer_amount)
                
                # If futures has excess (> $10) and spot has less than $2, transfer back
                elif futures_usdt.available > 10.0 and spot_usdt.available < 2.0:
                    transfer_amount = min(5.0, futures_usdt.available - 5.0)
                    await self.shuffle_funds(AccountType.FUTURES, AccountType.SPOT, 'USDT', transfer_amount)
        
        except Exception as e:
            logger.error(f"Error optimizing fund allocation: {e}")
    
    def get_account_summary(self) -> dict:
        """Get comprehensive account summary"""
        return {
            'total_balance': self.total_usdt_balance,
            'available_balance': self.available_balance,
            'active_positions': len(self.active_positions),
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'total_pnl': self.total_pnl,
            'win_rate': (self.successful_trades / max(1, self.total_trades)) * 100,
            'account_balances': {k: v.__dict__ for k, v in self.account_balances.items()},
            'futures_contracts': len(self.futures_contracts),
            'blocked_symbols': len(self.profit_symbols_today)
        }

class AdvancedBotUI:
    """Advanced UI for the Gate.io trading bot"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 ADVANCED GATE.IO TRADING BOT - LIVE ACCOUNT")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        
        # Initialize bot
        self.bot = AdvancedGateioBot()
        self.running = False
        
        # Create UI
        self.create_widgets()
        
        # Initialize account connection in background
        threading.Thread(target=self.initialize_bot_account, daemon=True).start()
        
        # Start update loop
        self.update_ui()
    
    def initialize_bot_account(self):
        """Initialize bot account in background"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.bot.initialize_account())
        self.log_activity(f"💰 Account connected - Balance: ${self.bot.total_usdt_balance:.2f}")
    
    def create_widgets(self):
        """Create advanced UI widgets"""
        # Title Frame
        title_frame = tk.Frame(self.root, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(title_frame, text="🚀 ADVANCED GATE.IO TRADING BOT - LIVE ACCOUNT", 
                               font=('Arial', 18, 'bold'), fg='#00ff00', bg='#2a2a2a')
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(title_frame, text="Real Account Connection | Cross-Account Shuffling | Maximized Futures", 
                                 font=('Arial', 12), fg='#ffff00', bg='#2a2a2a')
        subtitle_label.pack()
        
        # Main Container
        main_container = tk.Frame(self.root, bg='#1a1a1a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create panels
        self.create_account_panel(main_container)
        self.create_positions_panel(main_container)
        self.create_contracts_panel(main_container)
        self.create_activity_panel(main_container)
        
        # Control Panel
        self.create_control_panel()
    
    def create_account_panel(self, parent):
        """Create account balance panel"""
        account_frame = tk.Frame(parent, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        account_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(account_frame, text="💰 ACCOUNT BALANCES", 
                font=('Arial', 14, 'bold'), fg='#00ffff', bg='#2a2a2a').pack(pady=10)
        
        self.account_tree = ttk.Treeview(account_frame, columns=('Currency', 'Available', 'Frozen', 'Total'), 
                                        show='tree headings', height=12)
        self.account_tree.heading('#0', text='Account')
        self.account_tree.heading('Currency', text='Currency')
        self.account_tree.heading('Available', text='Available')
        self.account_tree.heading('Frozen', text='Frozen')
        self.account_tree.heading('Total', text='Total')
        
        self.account_tree.pack(padx=10, pady=5)
        
        # Summary labels
        self.summary_frame = tk.Frame(account_frame, bg='#2a2a2a')
        self.summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.total_balance_label = tk.Label(self.summary_frame, text="Total Balance: $0.00", 
                                           font=('Arial', 12, 'bold'), fg='#00ff00', bg='#2a2a2a')
        self.total_balance_label.pack()
        
        self.available_label = tk.Label(self.summary_frame, text="Available: $0.00", 
                                       font=('Arial', 12), fg='#ffff00', bg='#2a2a2a')
        self.available_label.pack()
    
    def create_positions_panel(self, parent):
        """Create positions panel"""
        positions_frame = tk.Frame(parent, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        positions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(positions_frame, text="📊 ACTIVE POSITIONS", 
                font=('Arial', 14, 'bold'), fg='#00ffff', bg='#2a2a2a').pack(pady=10)
        
        self.positions_tree = ttk.Treeview(positions_frame, 
                                          columns=('Symbol', 'Type', 'Side', 'Size', 'PnL', 'Margin'), 
                                          show='tree headings', height=12)
        self.positions_tree.heading('#0', text='ID')
        self.positions_tree.heading('Symbol', text='Symbol')
        self.positions_tree.heading('Type', text='Type')
        self.positions_tree.heading('Side', text='Side')
        self.positions_tree.heading('Size', text='Size')
        self.positions_tree.heading('PnL', text='P&L')
        self.positions_tree.heading('Margin', text='Margin')
        
        self.positions_tree.pack(padx=10, pady=5)
    
    def create_contracts_panel(self, parent):
        """Create contracts panel"""
        contracts_frame = tk.Frame(parent, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        contracts_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(contracts_frame, text="📈 MICRO-CAP CONTRACTS", 
                font=('Arial', 14, 'bold'), fg='#00ffff', bg='#2a2a2a').pack(pady=10)
        
        self.contracts_tree = ttk.Treeview(contracts_frame, 
                                          columns=('Symbol', 'Type', 'Price', 'Nominal', 'Volume'), 
                                          show='tree headings', height=12)
        self.contracts_tree.heading('#0', text='ID')
        self.contracts_tree.heading('Symbol', text='Symbol')
        self.contracts_tree.heading('Type', text='Type')
        self.contracts_tree.heading('Price', text='Price')
        self.contracts_tree.heading('Nominal', text='Nominal')
        self.contracts_tree.heading('Volume', text='Volume')
        
        self.contracts_tree.pack(padx=10, pady=5)
    
    def create_activity_panel(self, parent):
        """Create activity log panel"""
        activity_frame = tk.Frame(parent, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        activity_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        tk.Label(activity_frame, text="📝 ACTIVITY LOG", 
                font=('Arial', 14, 'bold'), fg='#00ffff', bg='#2a2a2a').pack(pady=10)
        
        self.activity_log = scrolledtext.ScrolledText(activity_frame, height=12, width=40, 
                                                     bg='#000000', fg='#ffff00', font=('Courier', 9))
        self.activity_log.pack(padx=10, pady=5)
        
        # Statistics
        self.stats_frame = tk.Frame(activity_frame, bg='#2a2a2a')
        self.stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.trades_label = tk.Label(self.stats_frame, text="Trades: 0", 
                                    font=('Arial', 10), fg='white', bg='#2a2a2a')
        self.trades_label.pack()
        
        self.pnl_label = tk.Label(self.stats_frame, text="P&L: $0.00", 
                                 font=('Arial', 10), fg='white', bg='#2a2a2a')
        self.pnl_label.pack()
        
        self.winrate_label = tk.Label(self.stats_frame, text="Win Rate: 0%", 
                                     font=('Arial', 10), fg='white', bg='#2a2a2a')
        self.winrate_label.pack()
    
    def create_control_panel(self):
        """Create control panel"""
        control_panel = tk.Frame(self.root, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        control_panel.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_button = tk.Button(control_panel, text="🚀 START LIVE TRADING", command=self.start_trading,
                                      bg='#00aa00', fg='white', font=('Arial', 12, 'bold'),
                                      width=20, height=2)
        self.start_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.stop_button = tk.Button(control_panel, text="⏹️ STOP TRADING", command=self.stop_trading,
                                     bg='#aa0000', fg='white', font=('Arial', 12, 'bold'),
                                     width=20, height=2, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=10)
        
        self.shuffle_button = tk.Button(control_panel, text="💸 SHUFFLE FUNDS", command=self.shuffle_funds,
                                       bg='#0000aa', fg='white', font=('Arial', 12, 'bold'),
                                       width=20, height=2)
        self.shuffle_button.pack(side=tk.LEFT, padx=5, pady=10)
        
        self.scan_button = tk.Button(control_panel, text="🔍 SCAN NOW", command=self.manual_scan,
                                     bg='#aa5500', fg='white', font=('Arial', 12, 'bold'),
                                     width=20, height=2)
        self.scan_button.pack(side=tk.LEFT, padx=5, pady=10)
        
        self.log_activity("🚀 Advanced Gate.io Bot initialized")
        self.log_activity("💰 Real account connection ready")
        self.log_activity("📊 Cross-account shuffling enabled")
        self.log_activity("⚡ Maximized futures trading ready")
    
    def log_activity(self, message):
        """Log activity to UI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.activity_log.see(tk.END)
        logger.info(message)
    
    def update_ui(self):
        """Update UI with current data"""
        if self.running:
            self.update_account_display()
            self.update_positions_display()
            self.update_contracts_display()
            self.update_statistics()
        
        # Schedule next update
        self.root.after(3000, self.update_ui)  # Update every 3 seconds
    
    def update_account_display(self):
        """Update account balances display"""
        # Clear existing items
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        
        # Add account balances
        for key, balance in self.bot.account_balances.items():
            self.account_tree.insert('', 'end', text=key,
                                    values=(balance.currency,
                                           f"{balance.available:.4f}",
                                           f"{balance.frozen:.4f}",
                                           f"{balance.total:.4f}"))
        
        # Update summary
        self.total_balance_label.config(text=f"Total Balance: ${self.bot.total_usdt_balance:.2f}")
        self.available_label.config(text=f"Available: ${self.bot.available_balance:.2f}")
    
    def update_positions_display(self):
        """Update positions display"""
        # Clear existing items
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)
        
        # Add active positions
        for i, position in enumerate(self.bot.active_positions):
            pnl_color = 'green' if position.unrealized_pnl > 0 else 'red'
            
            self.positions_tree.insert('', 'end', iid=i, text=f"#{i+1}",
                                      values=(position.symbol,
                                             position.contract_type.value,
                                             position.side,
                                             f"{position.size:.6f}",
                                             f"${position.unrealized_pnl:.4f}",
                                             f"${position.margin_used:.4f}"))
    
    def update_contracts_display(self):
        """Update contracts display"""
        # Clear existing items
        for item in self.contracts_tree.get_children():
            self.contracts_tree.delete(item)
        
        # Add top contracts (by nominal value)
        top_contracts = sorted(self.bot.futures_contracts, key=lambda x: x.nominal_value)[:20]
        
        for i, contract in enumerate(top_contracts):
            self.contracts_tree.insert('', 'end', iid=i, text=f"#{i+1}",
                                      values=(contract.symbol,
                                             contract.contract_type.value,
                                             f"${contract.last_price:.6f}",
                                             f"${contract.nominal_value:.6f}",
                                             f"${contract.volume_24h:.0f}"))
    
    def update_statistics(self):
        """Update statistics display"""
        self.trades_label.config(text=f"Trades: {self.bot.total_trades}")
        self.pnl_label.config(text=f"P&L: ${self.bot.total_pnl:.4f}")
        win_rate = (self.bot.successful_trades / max(1, self.bot.total_trades)) * 100
        self.winrate_label.config(text=f"Win Rate: {win_rate:.1f}%")
    
    async def trading_loop(self):
        """Main trading loop"""
        while self.running:
            try:
                await self.bot.run_trading_cycle()
                await asyncio.sleep(30)  # Run every 30 seconds
            except Exception as e:
                self.log_activity(f"❌ Trading loop error: {e}")
                await asyncio.sleep(10)
    
    def start_trading(self):
        """Start live trading"""
        if not self.running:
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.log_activity("🚀 LIVE TRADING STARTED!")
            self.log_activity(f"💰 Using real account balance: ${self.bot.total_usdt_balance:.2f}")
            
            # Start trading loop
            threading.Thread(target=self.run_trading_loop, daemon=True).start()
    
    def stop_trading(self):
        """Stop trading"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_activity("⏹️ TRADING STOPPED!")
    
    def run_trading_loop(self):
        """Run trading loop in thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.trading_loop())
    
    def shuffle_funds(self):
        """Manual fund shuffling"""
        threading.Thread(target=self.run_fund_shuffle, daemon=True).start()
    
    async def run_fund_shuffle_async(self):
        """Run fund shuffling"""
        await self.bot.optimize_fund_allocation()
        self.log_activity("💸 Fund shuffling completed")
    
    def run_fund_shuffle(self):
        """Run fund shuffling in thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_fund_shuffle_async())
    
    def manual_scan(self):
        """Manual market scan"""
        threading.Thread(target=self.run_manual_scan, daemon=True).start()
    
    async def run_manual_scan_async(self):
        """Run manual scan"""
        opportunities = await self.bot.get_micro_cap_opportunities()
        self.log_activity(f"🔍 Manual scan: {len(opportunities)} opportunities found")
        
        for contract in opportunities[:5]:
            self.log_activity(f"   🚀 {contract.symbol}: ${contract.nominal_value:.6f} | {contract.contract_type.value}")
    
    def run_manual_scan(self):
        """Run manual scan in thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_manual_scan_async())
    
    def run(self):
        """Run the UI"""
        self.root.mainloop()

def main():
    """Main function"""
    print("🚀 ADVANCED GATE.IO TRADING BOT - FULL ACCOUNT INTEGRATION")
    print("="*80)
    print("💰 Real Account Balance Detection")
    print("💸 Cross-Account Fund Shuffling")
    print("📊 Maximized Futures Trading (USDT/Coin/Delivery)")
    print("⚡ Real Order Execution")
    print("🎯 Micro-Cap Optimization ($0.001-$0.10)")
    print("="*80)
    
    # Create and run UI
    ui = AdvancedBotUI()
    ui.run()

if __name__ == "__main__":
    main()
