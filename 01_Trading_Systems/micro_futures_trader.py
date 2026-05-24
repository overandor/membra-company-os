#!/usr/bin/env python3
"""
Gate.io Micro Futures Trader - $40 Balance
Trades futures contracts with small notional values (<= $0.10)
Suitable for small accounts
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
GATE_API_KEY = "2b29d118d4fe92628f33a8f298416548"
GATE_API_SECRET = "09b7b2c7af4ba6ee1bd93823591a5216945030d760e27b94aa26fed337e05d35"

# Configuration
SETTLE = "usdt"
MAX_CONTRACT_NOTIONAL = 0.10  # Max $0.10 per contract
ACCOUNT_BALANCE = 40.0  # $40 balance
MAX_POSITIONS = 3  # Max open positions
LEVERAGE = 10  # 10x leverage
REFRESH_INTERVAL = 10  # Seconds
MIN_VOLUME = 1000  # Minimum 24h volume

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/Users/alep/Downloads/micro_futures.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MicroFuturesTrader:
    def __init__(self):
        cfg = Configuration(key=GATE_API_KEY, secret=GATE_API_SECRET)
        self.client = FuturesApi(ApiClient(cfg))
        self.running = False
        self.positions = {}
        
    def get_futures_tickers(self) -> List[Dict]:
        """Get all futures tickers"""
        try:
            tickers = list(self.client.list_futures_tickers(SETTLE))
            result = []
            for t in tickers:
                try:
                    contract = getattr(t, "contract", "")
                    if not contract:
                        continue
                    
                    # Skip BTC
                    if "BTC" in contract.upper():
                        continue
                    
                    last = float(getattr(t, "last", 0))
                    volume = float(getattr(t, "volume_24h_quote", 0))
                    change = float(getattr(t, "change_percentage", 0))
                    
                    if last > 0 and volume >= MIN_VOLUME:
                        result.append({
                            'contract': contract,
                            'price': last,
                            'volume': volume,
                            'change_24h': change
                        })
                except (ValueError, TypeError):
                    continue
            
            return result
        except Exception as e:
            logger.error(f"Error getting tickers: {e}")
        return []
    
    def get_account(self) -> Dict:
        """Get futures account info"""
        try:
            account = self.client.get_futures_account(SETTLE)
            return {
                'total': float(account.total),
                'available': float(account.available)
            }
        except Exception as e:
            logger.error(f"Error getting account: {e}")
        return {}
    
    def get_positions(self) -> List:
        """Get open positions"""
        try:
            positions = self.client.list_positions(SETTLE, limit=100)
            return [p for p in positions if float(p.size) != 0]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
        return []
    
    def get_open_orders(self, contract: str) -> List:
        """Get open orders"""
        try:
            orders = self.client.list_orders(SETTLE, contract=contract, status='open')
            return orders
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
        return []
    
    def cancel_all_orders(self, contract: str):
        """Cancel all open orders"""
        try:
            orders = self.get_open_orders(contract)
            for order in orders:
                try:
                    self.client.cancel_order(order.id, settle=SETTLE, contract=contract)
                    logger.info(f"Cancelled order {order.id}")
                except Exception as e:
                    logger.error(f"Error cancelling order: {e}")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
    
    def place_order(self, contract: str, side: str, size: int, price: float) -> Optional[str]:
        """Place a limit order"""
        try:
            order = gate_api.Order(
                size=str(size),
                price=str(price),
                side=side,
                contract=contract,
                tif='gtc'
            )
            result = self.client.create_order(order, settle=SETTLE)
            logger.info(f"✅ Placed {side.upper()} {size} {contract} @ ${price} - ID: {result.id}")
            return result.id
        except GateApiException as e:
            logger.error(f"❌ API error: {e}")
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
        return None
    
    def calculate_position_size(self, contract: str, price: float) -> int:
        """Calculate position size based on balance and contract notional"""
        # Max risk per position = 20% of balance
        max_risk = ACCOUNT_BALANCE * 0.20
        
        # With leverage, we can control more
        effective_balance = ACCOUNT_BALANCE * LEVERAGE
        
        # Calculate number of contracts
        max_contracts = int(effective_balance / (price * LEVERAGE))
        
        # Ensure notional per contract is small
        if price > MAX_CONTRACT_NOTIONAL:
            return 0
        
        return max(1, min(max_contracts, 10))  # Cap at 10 contracts
    
    def run(self):
        """Main trading loop"""
        logger.info("🚀 Starting Gate.io Micro Futures Trader")
        logger.info(f"Balance: ${ACCOUNT_BALANCE}")
        logger.info(f"Leverage: {LEVERAGE}x")
        logger.info(f"Max Contract Notional: ${MAX_CONTRACT_NOTIONAL}")
        logger.info(f"Skip: BTC contracts")
        
        # Get account
        account = self.get_account()
        logger.info(f"Account Total: ${account.get('total', 0):.2f}")
        logger.info(f"Available: ${account.get('available', 0):.2f}")
        
        self.running = True
        
        while self.running:
            try:
                # Get tickers
                tickers = self.get_futures_tickers()
                
                # Filter by price (small notional)
                small_contracts = [t for t in tickers if t['price'] <= MAX_CONTRACT_NOTIONAL]
                
                logger.info(f"📊 Total contracts: {len(tickers)} | Small notional: {len(small_contracts)}")
                
                if not small_contracts:
                    logger.warning("No contracts with small notional found")
                    time.sleep(REFRESH_INTERVAL)
                    continue
                
                # Show top 10
                logger.info("Top 10 small contracts:")
                for contract in small_contracts[:10]:
                    change_symbol = "🟢" if contract['change_24h'] >= 0 else "🔴"
                    logger.info(f"  {contract['contract']:20} ${contract['price']:8.6f}  {change_symbol} {contract['change_24h']:+6.2f}%  Vol: ${contract['volume']:12,.0f}")
                
                # Check current positions
                positions = self.get_positions()
                logger.info(f"📈 Open positions: {len(positions)}")
                
                # Trade top small contracts
                for contract in small_contracts[:MAX_POSITIONS]:
                    orders = self.get_open_orders(contract['contract'])
                    
                    if len(orders) == 0:
                        # Place a small order
                        size = self.calculate_position_size(contract['contract'], contract['price'])
                        if size > 0:
                            # Place order slightly below current price
                            buy_price = contract['price'] * 0.99
                            self.place_order(contract['contract'], 'buy', size, buy_price)
                
                # Wait
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
        tickers = self.get_futures_tickers()
        for contract in tickers:
            self.cancel_all_orders(contract['contract'])
        logger.info("Micro Futures Trader stopped")

def main():
    trader = MicroFuturesTrader()
    try:
        trader.run()
    except KeyboardInterrupt:
        logger.info("Interrupted")

if __name__ == "__main__":
    main()
