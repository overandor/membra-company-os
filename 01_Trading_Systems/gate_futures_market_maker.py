#!/usr/bin/env python3
"""
Gate.io Futures Market Maker Bot - Live Trading
Uses official gate_api SDK (working API keys)
Places bid/ask orders around current price on futures
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

try:
    import gate_api
    from gate_api import ApiClient, Configuration, FuturesApi
    from gate_api.exceptions import GateApiException
    GATE_AVAILABLE = True
except ImportError:
    print("Installing gate-api...")
    import subprocess
    subprocess.run(["pip", "install", "gate-api"], check=True)
    import gate_api
    from gate_api import ApiClient, Configuration, FuturesApi
    from gate_api.exceptions import GateApiException
    GATE_AVAILABLE = True

# API Keys
API_KEY = "2b29d118d4fe92628f33a8f298416548"
API_SECRET = "09b7b2c7af4ba6ee1bd93823591a5216945030d760e27b94aa26fed337e05d35"

# Configuration
SETTLE = "usdt"  # USDT settled futures
SYMBOL = "BTC_USDT"  # Trading pair
SPREAD_PERCENT = 0.05  # 0.05% spread
ORDER_SIZE = 1  # Order size in contracts
MAX_POSITIONS = 4  # Max open orders
REFRESH_INTERVAL = 10  # Seconds between checks
LEVERAGE = 5  # Leverage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/Users/alep/Downloads/futures_market_maker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GateFuturesMarketMaker:
    def __init__(self):
        self.configuration = Configuration(key=API_KEY, secret=API_SECRET)
        self.configuration.host = "https://api.gateio.ws"
        
        self.api_client = ApiClient(self.configuration)
        self.futures_api = FuturesApi(self.api_client)
        
        self.running = False
        self.last_orders = {}
        
    def get_ticker(self, settle: str, symbol: str) -> Dict:
        """Get current futures ticker price"""
        try:
            ticker = self.futures_api.list_futures_tickers(settle=settle, contract=symbol)
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
    
    def get_account(self, settle: str) -> Dict:
        """Get futures account info"""
        try:
            account = self.futures_api.get_futures_account(settle=settle)
            return {
                'total': float(account.total),
                'available': float(account.available),
                'unrealised_pnl': float(account.unrealised_pnl)
            }
        except Exception as e:
            logger.error(f"Error getting account: {e}")
        return {}
    
    def get_positions(self, settle: str) -> List:
        """Get open positions"""
        try:
            positions = self.futures_api.list_positions(settle=settle, limit=100)
            return [p for p in positions if float(p.size) != 0]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
        return []
    
    def get_open_orders(self, settle: str, symbol: str) -> List:
        """Get open orders"""
        try:
            orders = self.futures_api.list_orders(settle=settle, contract=symbol, status='open')
            return orders
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
        return []
    
    def cancel_all_orders(self, settle: str, symbol: str):
        """Cancel all open orders"""
        try:
            orders = self.get_open_orders(settle, symbol)
            for order in orders:
                try:
                    self.futures_api.cancel_order(order.id, settle=settle, contract=symbol)
                    logger.info(f"Cancelled order {order.id}")
                except Exception as e:
                    logger.error(f"Error cancelling order {order.id}: {e}")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
    
    def set_leverage(self, settle: str, leverage: int):
        """Set leverage for futures"""
        try:
            self.futures_api.update_leverage(settle=settle, leverage=leverage)
            logger.info(f"Set leverage to {leverage}x")
        except Exception as e:
            logger.error(f"Error setting leverage: {e}")
    
    def place_order(self, settle: str, symbol: str, side: str, size: int, price: float) -> Optional[str]:
        """Place a limit order"""
        try:
            order = gate_api.Order(
                size=str(size),
                price=str(price),
                side=side,
                contract=symbol,
                tif='gtc'  # Good till cancelled
            )
            result = self.futures_api.create_order(order, settle=settle)
            logger.info(f"Placed {side.upper()} order: {size} @ ${price} - ID: {result.id}")
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
        logger.info("🚀 Starting Gate.io Futures Market Maker")
        logger.info(f"Settle: {SETTLE}")
        logger.info(f"Symbol: {SYMBOL}")
        logger.info(f"Spread: {SPREAD_PERCENT}%")
        logger.info(f"Order Size: {ORDER_SIZE}")
        logger.info(f"Leverage: {LEVERAGE}x")
        
        # Set leverage
        self.set_leverage(SETTLE, LEVERAGE)
        
        # Get account balance
        account = self.get_account(SETTLE)
        logger.info(f"Account Balance: ${account.get('total', 0):.2f}")
        
        self.running = True
        
        while self.running:
            try:
                # Get current price
                ticker = self.get_ticker(SETTLE, SYMBOL)
                if not ticker:
                    logger.warning("Could not get ticker data")
                    time.sleep(REFRESH_INTERVAL)
                    continue
                
                current_price = ticker['price']
                logger.info(f"Current Price: ${current_price:.2f} | Volume: {ticker['volume']:.2f}")
                
                # Get open orders
                open_orders = self.get_open_orders(SETTLE, SYMBOL)
                logger.info(f"Open Orders: {len(open_orders)}")
                
                # Get positions
                positions = self.get_positions(SETTLE)
                logger.info(f"Open Positions: {len(positions)}")
                
                # Cancel old orders if we have too many
                if len(open_orders) >= MAX_POSITIONS:
                    logger.info("Max positions reached, cancelling old orders")
                    self.cancel_all_orders(SETTLE, SYMBOL)
                    time.sleep(2)
                    open_orders = []
                
                # Calculate spread
                bid_price, ask_price = self.calculate_spread(current_price)
                logger.info(f"Spread: Bid ${bid_price:.2f} | Ask ${ask_price:.2f}")
                
                # Place orders if we have capacity
                if len(open_orders) < MAX_POSITIONS:
                    # Place bid order (long)
                    bid_id = self.place_order(SETTLE, SYMBOL, 'buy', ORDER_SIZE, bid_price)
                    if bid_id:
                        self.last_orders['bid'] = bid_id
                    
                    # Place ask order (short)
                    ask_id = self.place_order(SETTLE, SYMBOL, 'sell', ORDER_SIZE, ask_price)
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
        self.cancel_all_orders(SETTLE, SYMBOL)
        logger.info("Futures Market Maker stopped")

def main():
    mm = GateFuturesMarketMaker()
    try:
        mm.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        mm.cancel_all_orders(SETTLE, SYMBOL)

if __name__ == "__main__":
    main()
