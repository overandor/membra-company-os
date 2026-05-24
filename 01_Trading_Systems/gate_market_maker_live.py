#!/usr/bin/env python3
"""
Gate.io Market Maker Bot - Live Trading
Uses official gate_api SDK (working API keys)
Places bid/ask orders around current price
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

try:
    import gate_api
    from gate_api import ApiClient, Configuration, SpotApi, FuturesApi
    from gate_api.exceptions import GateApiException
    GATE_AVAILABLE = True
except ImportError:
    print("Installing gate-api...")
    import subprocess
    subprocess.run(["pip", "install", "gate-api"], check=True)
    import gate_api
    from gate_api import ApiClient, Configuration, SpotApi, FuturesApi
    from gate_api.exceptions import GateApiException
    GATE_AVAILABLE = True

# API Keys
API_KEY = "2b29d118d4fe92628f33a8f298416548"
API_SECRET = "09b7b2c7af4ba6ee1bd93823591a5216945030d760e27b94aa26fed337e05d35"

# Configuration
SYMBOL = "BTC_USDT"  # Trading pair
SPREAD_PERCENT = 0.1  # 0.1% spread
ORDER_SIZE = 0.001  # Order size in BTC
MAX_POSITIONS = 2  # Max open positions
REFRESH_INTERVAL = 5  # Seconds between checks

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/Users/alep/Downloads/market_maker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GateMarketMaker:
    def __init__(self):
        self.configuration = Configuration(key=API_KEY, secret=API_SECRET)
        self.configuration.host = "https://api.gateio.ws"
        
        self.api_client = ApiClient(self.configuration)
        self.spot_api = SpotApi(self.api_client)
        self.futures_api = FuturesApi(self.api_client)
        
        self.running = False
        self.last_orders = {}
        
    def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker price"""
        try:
            ticker = self.spot_api.list_tickers(currency_pair=symbol)
            if ticker:
                return {
                    'price': float(ticker[0].last),
                    'bid': float(ticker[0].highest_bid),
                    'ask': float(ticker[0].lowest_ask),
                    'volume': float(ticker[0].base_volume)
                }
        except Exception as e:
            logger.error(f"Error getting ticker: {e}")
        return {}
    
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
        """Cancel all open orders"""
        try:
            orders = self.get_open_orders(symbol)
            for order in orders:
                try:
                    self.spot_api.cancel_order(order.id, currency_pair=symbol)
                    logger.info(f"Cancelled order {order.id}")
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
            logger.info(f"Placed {side.upper()} order: {amount} @ ${price} - ID: {result.id}")
            return result.id
        except GateApiException as e:
            logger.error(f"Gate API error placing order: {e}")
        except Exception as e:
            logger.error(f"Error placing order: {e}")
        return None
    
    def calculate_spread(self, mid_price: float) -> tuple:
        """Calculate bid/ask prices"""
        spread_amount = mid_price * (SPREAD_PERCENT / 100)
        bid_price = mid_price - spread_amount
        ask_price = mid_price + spread_amount
        return bid_price, ask_price
    
    def run(self):
        """Main market making loop"""
        logger.info("🚀 Starting Gate.io Market Maker")
        logger.info(f"Symbol: {SYMBOL}")
        logger.info(f"Spread: {SPREAD_PERCENT}%")
        logger.info(f"Order Size: {ORDER_SIZE}")
        logger.info(f"USDT Balance: ${self.get_balance():.2f}")
        
        self.running = True
        
        while self.running:
            try:
                # Get current price
                ticker = self.get_ticker(SYMBOL)
                if not ticker:
                    logger.warning("Could not get ticker data")
                    time.sleep(REFRESH_INTERVAL)
                    continue
                
                current_price = ticker['price']
                logger.info(f"Current Price: ${current_price:.2f} | Volume: {ticker['volume']:.2f}")
                
                # Get open orders
                open_orders = self.get_open_orders(SYMBOL)
                logger.info(f"Open Orders: {len(open_orders)}")
                
                # Cancel old orders if we have too many
                if len(open_orders) >= MAX_POSITIONS:
                    logger.info("Max positions reached, cancelling old orders")
                    self.cancel_all_orders(SYMBOL)
                    time.sleep(2)
                    open_orders = []
                
                # Calculate spread
                bid_price, ask_price = self.calculate_spread(current_price)
                logger.info(f"Spread: Bid ${bid_price:.2f} | Ask ${ask_price:.2f}")
                
                # Place orders if we have capacity
                if len(open_orders) < MAX_POSITIONS:
                    # Place bid order
                    bid_id = self.place_order(SYMBOL, 'buy', ORDER_SIZE, bid_price)
                    if bid_id:
                        self.last_orders['bid'] = bid_id
                    
                    # Place ask order
                    ask_id = self.place_order(SYMBOL, 'sell', ORDER_SIZE, ask_price)
                    if ask_id:
                        self.last_orders['ask'] = ask_id
                
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
        self.cancel_all_orders(SYMBOL)
        logger.info("Market Maker stopped")

def main():
    mm = GateMarketMaker()
    try:
        mm.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        mm.cancel_all_orders(SYMBOL)

if __name__ == "__main__":
    main()
