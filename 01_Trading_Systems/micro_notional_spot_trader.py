#!/usr/bin/env python3
"""
Gate.io Micro Notional Spot Trader - Live Trading
Trades all coins under $0.10 (micro notional)
Uses working API keys
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

try:
    import gate_api
    from gate_api import ApiClient, Configuration, SpotApi
    from gate_api.exceptions import GateApiException
    GATE_AVAILABLE = True
except ImportError:
    print("Installing gate-api...")
    import subprocess
    subprocess.run(["pip", "install", "gate-api"], check=True)
    import gate_api
    from gate_api import ApiClient, Configuration, SpotApi
    from gate_api.exceptions import GateApiException
    GATE_AVAILABLE = True

# API Keys
API_KEY = "2b29d118d4fe92628f33a8f298416548"
API_SECRET = "09b7b2c7af4ba6ee1bd93823591a5216945030d760e27b94aa26fed337e05d35"

# Configuration
MAX_PRICE = 0.10  # Maximum price $0.10 (10 cents)
MIN_VOLUME = 1000  # Minimum 24h volume in USDT
ORDER_SIZE_USDT = 10  # Order size in USDT
MAX_POSITIONS = 5  # Max open positions
REFRESH_INTERVAL = 5  # Seconds between checks

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/Users/alep/Downloads/micro_spot_trader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MicroNotionalSpotTrader:
    def __init__(self):
        self.configuration = Configuration(key=API_KEY, secret=API_SECRET)
        self.configuration.host = "https://api.gateio.ws"
        
        self.api_client = ApiClient(self.configuration)
        self.spot_api = SpotApi(self.api_client)
        
        self.running = False
        self.positions = {}
        
    def get_all_tickers(self) -> List[Dict]:
        """Get all spot tickers"""
        try:
            tickers = self.spot_api.list_tickers()
            result = []
            for t in tickers:
                try:
                    symbol = t.currency_pair
                    if not symbol.endswith("_USDT"):
                        continue
                    
                    price = float(t.last)
                    volume = float(t.quote_volume)
                    change = float(t.change_percentage)
                    
                    if price > 0 and volume > 0:
                        result.append({
                            'symbol': symbol.replace("_USDT", ""),
                            'full_symbol': symbol,
                            'price': price,
                            'volume': volume,
                            'change_24h': change
                        })
                except (ValueError, TypeError):
                    continue
            
            return result
        except Exception as e:
            logger.error(f"Error getting tickers: {e}")
        return []
    
    def get_micro_coins(self) -> List[Dict]:
        """Get coins under MAX_PRICE with minimum volume"""
        all_tickers = self.get_all_tickers()
        
        micro_coins = []
        for ticker in all_tickers:
            if ticker['price'] <= MAX_PRICE and ticker['volume'] >= MIN_VOLUME:
                micro_coins.append(ticker)
        
        # Sort by volume (highest first)
        micro_coins.sort(key=lambda x: x['volume'], reverse=True)
        return micro_coins
    
    def get_balance(self, currency: str = "USDT") -> float:
        """Get account balance"""
        try:
            accounts = self.spot_api.list_spot_accounts()
            for acc in accounts:
                if acc.currency == currency:
                    return float(acc.available)
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
        return 0.0
    
    def get_open_orders(self, symbol: str) -> List:
        """Get open orders"""
        try:
            orders = self.spot_api.list_orders(currency_pair=symbol, status='open')
            return orders
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
        return []
    
    def cancel_all_orders(self, symbol: str):
        """Cancel all open orders for a symbol"""
        try:
            orders = self.get_open_orders(symbol)
            for order in orders:
                try:
                    self.spot_api.cancel_order(order.id, currency_pair=symbol)
                    logger.info(f"Cancelled order {order.id} for {symbol}")
                except Exception as e:
                    logger.error(f"Error cancelling order {order.id}: {e}")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
    
    def place_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[str]:
        """Place a limit order"""
        try:
            order = gate_api.Order(
                amount=str(amount),
                price=str(price),
                side=side,
                currency_pair=symbol,
                type='limit'
            )
            result = self.spot_api.create_order(order)
            logger.info(f"✅ Placed {side.upper()} order: {amount} {symbol} @ ${price} - ID: {result.id}")
            return result.id
        except GateApiException as e:
            logger.error(f"❌ Gate API error placing order: {e}")
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
        return None
    
    def calculate_order_size(self, symbol: str, price: float) -> float:
        """Calculate order size based on USDT amount"""
        return ORDER_SIZE_USDT / price
    
    def run(self):
        """Main trading loop"""
        logger.info("🚀 Starting Gate.io Micro Notional Spot Trader")
        logger.info(f"Max Price: ${MAX_PRICE}")
        logger.info(f"Min Volume: ${MIN_VOLUME}")
        logger.info(f"Order Size: ${ORDER_SIZE_USDT}")
        
        # Get balance
        usdt_balance = self.get_balance("USDT")
        logger.info(f"USDT Balance: ${usdt_balance:.2f}")
        
        if usdt_balance < ORDER_SIZE_USDT:
            logger.warning(f"⚠️  Insufficient balance. Need ${ORDER_SIZE_USDT}, have ${usdt_balance:.2f}")
        
        self.running = True
        
        while self.running:
            try:
                # Get micro coins
                micro_coins = self.get_micro_coins()
                logger.info(f"📊 Found {len(micro_coins)} micro coins under ${MAX_PRICE}")
                
                if not micro_coins:
                    logger.warning("No micro coins found with minimum volume")
                    time.sleep(REFRESH_INTERVAL)
                    continue
                
                # Show top 10
                logger.info("Top 10 micro coins:")
                for coin in micro_coins[:10]:
                    change_symbol = "🟢" if coin['change_24h'] >= 0 else "🔴"
                    logger.info(f"  {coin['symbol']:12} ${coin['price']:8.6f}  {change_symbol} {coin['change_24h']:+6.2f}%  Vol: ${coin['volume']:12,.0f}")
                
                # Check current positions
                total_open_orders = 0
                for coin in micro_coins[:MAX_POSITIONS]:
                    orders = self.get_open_orders(coin['full_symbol'])
                    total_open_orders += len(orders)
                    
                    if len(orders) == 0:
                        # Place a buy order for this coin
                        order_size = self.calculate_order_size(coin['full_symbol'], coin['price'])
                        if order_size > 0:
                            # Place buy order slightly below current price
                            buy_price = coin['price'] * 0.995  # 0.5% below
                            self.place_order(coin['full_symbol'], 'buy', order_size, buy_price)
                
                logger.info(f"📈 Total open orders: {total_open_orders}")
                
                # Wait before next cycle
                time.sleep(REFRESH_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(REFRESH_INTERVAL)
        
        # Cleanup
        logger.info("Cancelling all orders...")
        micro_coins = self.get_micro_coins()
        for coin in micro_coins:
            self.cancel_all_orders(coin['full_symbol'])
        logger.info("Micro Notional Spot Trader stopped")

def main():
    trader = MicroNotionalSpotTrader()
    try:
        trader.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")

if __name__ == "__main__":
    main()
