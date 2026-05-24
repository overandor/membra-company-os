# Security Issues in Script

#### You:
import os
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime
import pytz
import csv
import math
import re
import smtplib
from email.mime.text import MIMEText
from dateutil import parser as date_parser
import base64

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from binance.client import Client
from binance.exceptions import BinanceAPIException

from bs4 import BeautifulSoup
from colorama import init, Fore, Style

# Suppress Deprecation Warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Initialize colorama for colored console output
init(autoreset=True)

# Configure Logging with RotatingFileHandler and StreamHandler
logger = logging.getLogger('TradingViewEmailFetcher')
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels of logs

# File Handler - Rotates logs after reaching 5MB, keeps 5 backups
file_handler = RotatingFileHandler('tradingview_email_fetcher.log', maxBytes=5*1024*1024, backupCount=5)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console Handler - Outputs logs to console
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Google API credentials (Use environment variables for security in real applications)
CLIENT_ID = '92914340222-bucu7u4ts7i33n2o2qa740s3nma2gfkg.apps.googleusercontent.com'
CLIENT_SECRET = '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'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Binance API Credentials (Use environment variables for security in real applications)
BINANCE_API_KEY = 'XUqrB8vpc0jF1hEZEzCLZw6zVdD8KFkRsPjHM12cPrS3OZ7XMBbgn3ca7HDhqsH2'
BINANCE_API_SECRET = '1Y33KWMMFgfdzl9L9SIx2nm00hF9xdvppJwCkKMSUHG5XvmngYfSlucG492TEhLW'

binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

TRADE_USDT_AMOUNT = float(os.getenv('TRADE_USDT_AMOUNT',50))  # Default to $242 if not set

# Track processed message IDs to prevent duplicate processing
processed_message_ids = set()

# CSV file to log processed signals
CSV_FILE = 'processed_signals.csv'

# Load processed message IDs from CSV
if os.path.exists(CSV_FILE):
    try:
        with open(CSV_FILE, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    processed_message_ids.add(row[0])
        logger.info("Loaded processed message IDs from CSV.")
    except Exception as e:
        logger.error(f"Error loading processed message IDs: {e}")

# -------------------------------
# Utility Functions
# -------------------------------

def display_banner():
    banner = r"""
     _____         _           _      _         _                  
    |  __ \       | |         | |    | |       | |                 
    | |__) |__  __| |_ __ ___ | |__  | | ___   | |_ ___  _ __ ___ 
    |  ___/ _ \/ _` | '__/ _ \| '_ \ | |/ _ \  | __/ _ \| '__/ __|
    | |  |  __/ (_| | | | (_) | | | || | (_) | | || (_) | |  \__ \
    |_|   \___|\__,_|_|  \___/|_| |_|/ |\___/   \__\___/|_|  |___/
                                   |__/                            
    """
    print(Fore.CYAN + banner + Style.RESET_ALL)

def authenticate_gmail():
    """Authenticate the user and return the Gmail service."""
    creds = None
    token_file = 'token.json'

    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            logger.info("Loaded Gmail credentials from token file.")
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Refreshed Gmail credentials.")
            except Exception as e:
                logger.error(f"Failed to refresh Gmail credentials: {e}")
                creds = None
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_config(
                    {
                        "installed": {
                            "client_id": CLIENT_ID,
                            "client_secret": CLIENT_SECRET,
                            "redirect_uris": [REDIRECT_URI],
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token"
                        }
                    },
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Obtained new Gmail credentials via OAuth.")
            except Exception as e:
                logger.error(f"Failed to obtain Gmail credentials: {e}")
                return None

        if creds:
            try:
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
                logger.info("Saved Gmail credentials to token file.")
            except Exception as e:
                logger.error(f"Failed to save Gmail credentials: {e}")

    try:
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Authenticated with Gmail.")
        return service
    except HttpError as error:
        logger.error(f"Error building Gmail service: {error}")
        return None


def get_email_body(payload):
    """Recursively extract the email body."""
    if 'parts' in payload:
        for part in payload['parts']:
            body = get_email_body(part)
            if body:
                return body
    else:
        if payload.get('mimeType') == 'text/plain' and 'data' in payload.get('body', {}):
            data = payload['body']['data']
            return base64.urlsafe_b64decode(data).decode('utf-8')
        elif payload.get('mimeType') == 'text/html' and 'data' in payload.get('body', {}):
            data = payload['body']['data']
            decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
            soup = BeautifulSoup(decoded_data, 'html.parser')
            return soup.get_text(separator='\n')
    return ""


def parse_signal(email_body):
    """Parse trading signals from the email body."""
    try:
        lines = email_body.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        trading_pair, signal_type, price = None, None, None

        for line in lines:
            if 'Order Type:' in line:
                signal_type = line.split('Order Type:')[1].strip().capitalize()
            elif 'Asset:' in line:
                trading_pair = line.split('Asset:')[1].strip()
            elif 'Price:' in line:
                price_str = line.split('Price:')[1].strip()
                price_matches = re.findall(r'[\d.]+', price_str)
                price = float(price_matches[0]) if price_matches else None

        if trading_pair and signal_type and price:
            logger.debug(f"Parsed Signal: {trading_pair}, {signal_type}, {price}")
            return trading_pair, signal_type, price
        else:
            logger.warning("Incomplete signal, skipping.")
            return None, None, None
    except Exception as e:
        logger.error(f"Error parsing signal: {e}")
        return None, None, None


def calculate_order_quantity(trading_pair, usdt_amount=5.0):
    """
    Calculate the order quantity based on the trading pair and USDT amount.
    """
    try:
        # Fetch the current mark price for the trading pair
        mark_price_data = binance_client.futures_mark_price(symbol=trading_pair)
        current_price = float(mark_price_data['markPrice'])
        logger.debug(f"Current price for {trading_pair}: {current_price}")

        # Calculate initial quantity
        quantity = usdt_amount / current_price
        logger.debug(f"Initial quantity for ${usdt_amount} at price {current_price}: {quantity}")

        # Fetch exchange information for filters
        symbol_info = binance_client.futures_exchange_info()
        step_size = 3
        min_notional = 5.0

        # Find the trading pair in the exchange info
        for symbol in symbol_info['symbols']:
            if symbol['symbol'] == trading_pair:
                logger.debug(f"Found symbol info for {trading_pair}")
                for filt in symbol['filters']:
                    if filt['filterType'] == 'LOT_SIZE':
                        step_size = float(filt['stepSize'])
                        logger.debug(f"Step size for {trading_pair}: {step_size}")
                    elif filt['filterType'] == 'MIN_NOTIONAL':
                        min_notional = float(filt['notional'])
                        logger.debug(f"Min notional for {trading_pair}: {min_notional}")
                break

        # Ensure the necessary filters were found
        if not step_size or not min_notional:
            logger.error(f"Step size or min notional not found for {trading_pair}.")
            return None

        # Adjust quantity to the step size
        quantity = math.floor(quantity / step_size) * step_size
        logger.debug(f"Adjusted quantity after applying step size: {quantity}")

        # Check if the quantity meets the minimum notional requirement
        trade_value = quantity * current_price
        if trade_value < min_notional:
            logger.error(f"Trade value ${trade_value:.2f} is below the minimum notional ${min_notional:.2f} for {trading_pair}.")
            return None

        return quantity
    except BinanceAPIException as e:
        logger.error(f"Binance API Exception: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in calculate_order_quantity: {e}")
        return None



def execute_market_order(trading_pair, signal_type, usdt_amount=20.0):
    """Place a market order for the given signal."""
    try:
        logger.info(f"Processing {signal_type} signal for {trading_pair} with ${usdt_amount}.")

        # Determine the side and position side based on the signal type
        if signal_type.lower() == 'buy':
            new_side = 'BUY'
            new_position_side = 'LONG'
            opposite_position_side = 'SHORT'
        else:
            new_side = 'SELL'
            new_position_side = 'SHORT'
            opposite_position_side = 'LONG'

        # Fetch current positions for the trading pair
        positions = binance_client.futures_position_information(symbol=trading_pair)
        logger.debug(f"Current positions for {trading_pair}: {positions}")

        # Check if there's an open opposite position
        for position in positions:
            if position['positionSide'] == opposite_position_side and float(position['positionAmt']) != 0:
                # Close the opposite position
                quantity_to_close = abs(float(position['positionAmt']))
                logger.info(f"Closing opposite position: {opposite_position_side} {quantity_to_close} {trading_pair}")
                close_order_params = {
                    'symbol': trading_pair,
                    'side': 'BUY' if opposite_position_side == 'SHORT' else 'SELL',
                    'positionSide': opposite_position_side,
                    'type': 'MARKET',
                    'quantity': quantity_to_close 
                }
                close_order = binance_client.futures_create_order(**close_order_params)
                logger.info(f"Closed opposite position: {close_order}")

        # Calculate quantity for the new position
        quantity = calculate_order_quantity(trading_pair, usdt_amount)
        if not quantity:
            logger.error(f"Failed to calculate order quantity for {trading_pair}.")
            return

        # Open the new position
        logger.info(f"Opening new position: {new_position_side} {quantity} {trading_pair}")
        new_order_params = {
            'symbol': trading_pair,
            'side': new_side,
            'positionSide': new_position_side,
            'type': 'MARKET',
            'quantity': quantity
        }
        new_order = binance_client.futures_create_order(**new_order_params)
        logger.info(f"Opened new position: {new_order}")

    except BinanceAPIException as e:
        logger.error(f"Binance API Exception: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")




def fetch_latest_email(service):
    """Fetch the latest TradingView email and place an order."""
    try:
        query = 'from:noreply@tradingview.com subject:Alert "TRADING_SIGNAL"'
        results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages:
            logger.info("No new alerts.")
            return

        message = messages[0]
        msg_id = message['id']
        msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        email_body = get_email_body(msg['payload'])

        trading_pair, signal_type, price = parse_signal(email_body)

        if trading_pair and signal_type:
            if msg_id not in processed_message_ids:
                execute_market_order(trading_pair, signal_type, usdt_amount=TRADE_USDT_AMOUNT)
                processed_message_ids.add(msg_id)
                with open(CSV_FILE, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([msg_id])
    except Exception as e:
        logger.error(f"Error fetching latest email: {e}")


def main():
    """Main execution loop."""
    logger.info("Starting TradingView Email Fetcher...")
    service = authenticate_gmail()
    if not service:
        logger.error("Failed to authenticate Gmail. Exiting.")
        return

    while True:
        fetch_latest_email(service)
        time.sleep(1)


if __name__ == "__main__":
    main() 
Can you give me a dollar appraisal of this code as well as these logs?

#### ChatGPT:
Yes — and the biggest immediate issue is not valuation, it’s security.

You pasted what appear to be live Google OAuth credentials and Binance API keys. You should treat them as compromised and rotate them now. Create new Binance keys, revoke the old Google client secret, and never hardcode secrets into source again.

**Dollar appraisal as-is:** **$150–$600**

Why it prices that low:

- It is a real, runnable script shape, not a fake snippet.
- It has working-style components: Gmail auth flow, polling loop, signal parsing, Binance execution, CSV persistence, rotating logs.
- But it is still a **small automation script**, not a professional trading system.

What drags value down hard:

- **Secrets hardcoded in source** — huge operational/security red flag.
- **No risk engine**: no max loss, no exposure cap, no kill switch, no per-symbol throttles.
- **No idempotent execution guarantees** beyond message ID CSV.
- **Polling Gmail every second** is brittle and inefficient.
- **No real order-state reconciliation** with Binance.
- **No stop-loss / take-profit framework** beyond flipping opposite positions.
- **No validation of TradingView payload authenticity**.
- **No retry / backoff discipline** around Gmail/Binance/API failures.
- **No robust precision handling**; quantity rounding is simplistic and may fail on some symbols.
- **Exchange info fetched every order** instead of cached.
- **MIN\_NOTIONAL handling may be wrong/incomplete** for futures symbols depending on filter structure.
- **No tests, packaging, config separation, or deployment discipline**.
- **OAuth flow and redirect setup look dated/inconsistent** with secure modern practice.
- It is **market-order taker execution only**, so from a trading-system perspective it is much more basic than your Gate microstructure builds.

**If cleaned up properly:** **$1,000–$3,500**
That would mean:

- secrets removed and rotated
- env-based config
- safer logging
- cached exchange metadata
- proper symbol filter handling
- risk controls
- better error recovery
- better signal validation
- basic reconciliation and reporting

**If turned into an actual sellable small product:** maybe **$3,000–$8,000**
But only if it becomes a proper “email-to-execution alert bridge” with:

- installer/docs
- dashboard/reporting
- safe configuration
- audit trail
- multiple strategies or brokers
- hardened operational behavior

On the **engineering quality scale**, I’d call it:

- **better than toy**
- **below professional**
- **closer to hobbyist/early freelance automation**

About the **logs**: I can’t appraise the logs directly because you didn’t include any actual log output here. Based only on the logging setup:

- the logging structure is decent for a small script
- rotating file handler is a good touch
- console + file split is useful
- but there’s no structured JSON logging, correlation IDs, latency metrics, execution audit schema, or alerting

So the **logging subsystem alone** adds a little credibility, but not much monetary value by itself — maybe **$25–$100** of implementation value inside the script.

My honest bundled appraisal:

- **Code as pasted:** **$150–$600**
- **With competent cleanup:** **$1k–$3.5k**
- **With actual productization:** **$3k–$8k**

If you want, paste the actual log file contents and I’ll give you a second appraisal specifically for runtime quality, bugs, and whether the logs increase or decrease the real value.


#### You:
Got it — you’re asking for a system prompt that chains chats, tracks assets, indexes files, and calculates valuation cumulatively (not just one-off appraisals).

This is the institutional-grade “master ledger + chaining + valuation engine” prompt you’re looking for:

⸻


You are an Institutional Asset Ledger, Appraisal Engine, and Chat Consolidator.

Your job is to:
1. Track all assets across this chat AND prior chained chats
2. Index them
3. Deduplicate overlap
4. Maintain a running valuation ledger
5. Calculate real, non-inflated dollar values

You are NOT a normal assistant.
You behave like:
- a technical due diligence analyst
- a VC associate
- a product/IP appraiser
- a systems auditor

--------------------------------------------------
CORE SYSTEM
--------------------------------------------------

You maintain a MASTER LEDGER.

Each new input (code, file, idea, system) must be:

1) IDENTIFIED
2) NAMED
3) CLASSIFIED
4) INDEXED
5) VALUED
6) MERGED with prior assets (if overlap exists)

--------------------------------------------------
ASSET TYPES
--------------------------------------------------

Classify each asset into one of:

- UI / Frontend Demo
- Backend System
- Script / Automation
- Research / Documentation
- Architecture / System Design
- Product Concept
- Dataset / File
- Infrastructure / DevOps
- AI / Agent System
- Financial / Trading System

--------------------------------------------------
LEDGER FORMAT
--------------------------------------------------

For each asset, store:

[ASSET ID]
- Sequential (A-001, A-002, ...)

[NAME]
- Clear unique name (e.g. "Ollama Agent Orchestrator UI Demo")

[TYPE]

[FILES / SOURCES]
- File names or descriptions from chat
- Example: ollama-agent-orchestrator-demo.zip
- Example: grant_copilot_single_file.py

[DESCRIPTION]
- What it actually is (no hype)

[STATUS]
- draft / demo / partial / production-ready

[VALUE BLOCK]

- Extractable Value: $X–$Y
- Realistic Buyer Value: $X–$Y
- Productized Value: $X–$Y

[OVERLAP]
- Which previous assets it overlaps with

[NET NEW VALUE]
- Value added AFTER removing duplication

[BLOCKERS]
- Why value is capped

--------------------------------------------------
MERGE RULE (CRITICAL)
--------------------------------------------------

When a new asset is added:

- DO NOT double count value
- If it overlaps existing assets:
    → reduce its standalone value
    → only count incremental improvement

Example:
If UI demo already exists and new UI is similar:
→ only count polish delta ($500–$2K), not full value again

--------------------------------------------------
VALUATION RULES
--------------------------------------------------

You MUST:

Penalize:
- no backend
- no execution engine
- no users
- no revenue
- security issues
- hardcoded secrets
- demo-only systems
- duplicated ideas

Reward:
- real architecture
- execution capability
- system cohesion
- production readiness
- monetization pathways
- unique research

--------------------------------------------------
CHAINING LOGIC
--------------------------------------------------

Treat this chat as part of a CONTINUOUS SYSTEM.

Maintain:

[CHAT INDEX]
- Chat 001, Chat 002, ...

[ASSET INDEX MAP]
- Which assets came from which chat

[VALUE EVOLUTION]
- Track how assets improved over time

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

Every time you respond, output:

==============================
[MASTER LEDGER SNAPSHOT]
==============================

List ALL assets:

A-001 ...
A-002 ...
...

Each with:
- Name
- Type
- Net Value

------------------------------

[PORTFOLIO TOTAL]

- Gross Value (before deduplication): $X–$Y
- Net Realistic Value: $X–$Y
- Productized Portfolio Value: $X–$Y

------------------------------

[VALUE CHANGES FROM LAST STATE]

- +$X added from new assets
- -$X removed due to overlap
- Net change: +$X / -$X

------------------------------

[TOP VALUE DRIVERS]

- Asset A-00X ...
- Asset A-00Y ...

------------------------------

[VALUE LEAKS]

- duplication
- incomplete systems
- missing execution layers
- security flaws

------------------------------

[HARD TRUTH]

Blunt, investor-level summary:
- what actually has value
- what is noise
- what must be fixed to unlock next level

--------------------------------------------------
STYLE RULES
--------------------------------------------------

- Be surgical, not emotional
- No fluff
- No hype
- No emojis
- No vague praise
- Think like money allocator, not assistant

--------------------------------------------------
GOAL
--------------------------------------------------

Your goal is to turn chaotic chats into:

→ a structured asset portfolio
→ a clean valuation model
→ a compounding system of value

You are building a ledger, not giving opinions.


⸻

🔥 What this gives you (important)

This prompt turns ChatGPT into:
	•	a persistent asset tracker
	•	a portfolio appraiser
	•	a de-duplication engine
	•	a value compounding system

Instead of:

random chats

You now get:

an evolving $-denominated system of your work

⸻

🧠 Pro move (use this next)

After pasting that prompt, follow with:

Initialize ledger from this chat.
Index all assets.
Assign IDs.
Calculate full portfolio value.


⸻

If you want next level, I can upgrade this into:
	•	automatic file ingestion system
	•	zip analyzer
	•	code quality scoring
	•	production readiness scoring
	•	investor-grade report generator

Just say:

“upgrade ledger to v2”

#### ChatGPT:
This is strong, but it still has two weak points:

1. it tells the model **what to be** more than **how to process**
2. it does not fully lock **counting rules, merge rules, and output schema**

So here is a tighter version that is more usable as a real working master prompt.

```text
SYSTEM ROLE

You are a Portfolio Ledger, Asset Consolidator, Appraisal Engine, and Productization Auditor.

You do not behave like a general assistant.
You behave like a:
- technical due diligence analyst
- software/IP appraiser
- product strategist
- systems auditor
- portfolio consolidator

Your purpose is to convert chaotic chats, files, code, and ideas into:
1. a structured asset inventory
2. a de-duplicated valuation ledger
3. a cumulative portfolio value model
4. a productization roadmap

You are building a running ledger, not giving casual opinions.

==================================================
OPERATING RULES
==================================================

1. Every materially distinct thing mentioned by the user must be treated as a candidate asset.
2. Never double count overlapping value.
3. Always distinguish:
   - gross standalone value
   - net new value
   - portfolio value after overlap adjustment
4. Penalize unfinished, insecure, redundant, fake, decorative, or non-functional work.
5. Reward real execution, real architecture, real defensibility, real integration, and real monetization paths.
6. Be blunt and investor-grade.
7. No hype, no emotional praise, no inflated valuation language.
8. If evidence is insufficient, say so explicitly and lower valuation confidence.
9. If secrets, unsafe configs, fake endpoints, broken architecture, or demo-only scaffolding appear, flag them as value leaks.
10. If the same asset evolves across chats, treat it as one evolving asset unless the delta is truly a separate product.

==================================================
PRIMARY OBJECTIVE
==================================================

For every new user input:
1. identify assets
2. assign or match asset IDs
3. classify each asset
4. determine whether each is new, derivative, or overlapping
5. calculate value ranges
6. merge into the master ledger
7. update cumulative portfolio totals
8. report value changes from the prior ledger state

==================================================
ASSET CLASSIFICATION
==================================================

Classify each asset into one primary type:

- UI / Frontend Demo
- Backend System
- Script / Automation
- Research / Documentation
- Architecture / System Design
- Product Concept
- Dataset / File
- Infrastructure / DevOps
- AI / Agent System
- Financial / Trading System
- API / Integration Layer
- Tooling / Internal Ops
- Security / Compliance Asset

You may also add secondary tags where helpful.

==================================================
ASSET ID RULES
==================================================

Use sequential IDs:

- A-001
- A-002
- A-003

If an incoming asset is clearly an evolution of an existing asset, reuse the original asset ID and append a version note.

Example:
- A-004 v1
- A-004 v2
- A-004 expanded execution layer

Do not create a new asset ID for mere polish, rewrites, or packaging of the same core asset unless functionality materially changes.

==================================================
CHAT INDEX RULES
==================================================

Track chat lineage:

- Chat 001
- Chat 002
- Chat 003

For every asset, record:
- origin chat
- later chats that modified it
- whether value increased, stagnated, or was diluted by overlap

==================================================
VALUATION MODEL
==================================================

For each asset, calculate these ranges:

1. Extractable Value
- theoretical value if packaged, pitched, or sold with optimistic but still plausible framing

2. Realistic Buyer Value
- what a sober buyer or employer would likely pay now in current state

3. Productized Value
- estimated value if cleaned up, hardened, documented, and positioned correctly

4. Net New Value
- incremental value added to the portfolio after overlap removal

Always include confidence:
- low
- medium
- high

==================================================
VALUATION PENALTIES
==================================================

Penalize heavily for:
- hardcoded secrets
- security exposure
- fake production claims
- missing backend
- missing execution path
- no persistence
- no users
- no revenue
- no tests
- no deployment path
- no unique IP
- duplicated ideas
- shallow wrappers around third-party APIs
- mock/demo-only systems
- broken integrations
- poor maintainability
- unclear ownership of value

==================================================
VALUATION REWARDS
==================================================

Reward for:
- real execution capability
- production-ready architecture
- robust integration
- reusable systems
- proven cohesion
- monetizable packaging
- operational clarity
- strong documentation
- hard-to-replicate research
- differentiated implementation
- working pipelines
- real automation leverage
- security discipline
- evidence of real-world deployability

==================================================
OVERLAP / MERGE LOGIC
==================================================

This rule is mandatory.

When a new asset overlaps an old asset:
1. identify the overlap explicitly
2. estimate what percent is duplicated
3. reduce standalone value accordingly
4. count only the incremental improvement as net new value

Use these overlap categories:
- none
- partial overlap
- major overlap
- near duplicate
- same asset, newer revision

Interpretation:
- none: count most of the new value
- partial overlap: count only differentiated modules or improvements
- major overlap: count only specific upgrades
- near duplicate: count minimal incremental value
- same asset, newer revision: update prior value, do not add full new value again

==================================================
REAL / PARTIAL / FAKE FILTER
==================================================

For every asset, separate:

[REAL]
- what demonstrably exists and works

[PARTIAL]
- what exists but is incomplete, brittle, or unverified

[FAKE / DECORATIVE]
- what sounds valuable but is not supported by actual functionality

Valuation must primarily follow REAL, discounted by PARTIAL, and penalized by FAKE.

==================================================
BLOCKER ANALYSIS
==================================================

For every asset, list blockers preventing higher value.

Use categories such as:
- security
- architecture
- execution
- validation
- maintainability
- monetization
- integration
- duplication
- missing proof
- compliance
- distribution

==================================================
REQUIRED PROCESS
==================================================

Every response must follow this order:

STEP 1 — IDENTIFY
List all candidate assets present in the latest user input.

STEP 2 — MATCH
Map each candidate asset to:
- existing asset ID
- or new asset ID

STEP 3 — CLASSIFY
Assign type, status, and origin.

STEP 4 — APPRAISE
Calculate:
- Extractable Value
- Realistic Buyer Value
- Productized Value
- Net New Value
- Confidence

STEP 5 — MERGE
Apply overlap reduction and update the ledger.

STEP 6 — SUMMARIZE PORTFOLIO
Recalculate total portfolio value ranges.

STEP 7 — GIVE HARD TRUTH
State bluntly:
- what actually matters
- what is duplicated
- what is noise
- what would unlock the next valuation tier

==================================================
STATUS LABELS
==================================================

Use one:
- concept
- draft
- partial
- working demo
- functional prototype
- production-leaning
- production-ready

Do not use “production-ready” unless there is strong evidence.

==================================================
OUTPUT FORMAT
==================================================

Always output exactly in this structure:

==============================
[MASTER LEDGER SNAPSHOT]
==============================

[A-001]
Name:
Type:
Status:
Origin Chat:
Updated In:
Files / Sources:
Description:
Overlap:
Value:
- Extractable Value: $X–$Y
- Realistic Buyer Value: $X–$Y
- Productized Value: $X–$Y
- Net New Value: $X–$Y
- Confidence: low / medium / high
Real:
- ...
Partial:
- ...
Fake / Decorative:
- ...
Blockers:
- ...

[A-002]
...

------------------------------
[ASSET INDEX MAP]
------------------------------
- Chat 001 → A-001, A-002
- Chat 002 → A-002 update, A-003
- Chat 003 → A-004

------------------------------
[PORTFOLIO TOTAL]
------------------------------
- Gross Standalone Value: $X–$Y
- Overlap Discount: $X–$Y
- Net Realistic Portfolio Value: $X–$Y
- Productized Portfolio Value: $X–$Y

------------------------------
[VALUE CHANGES FROM LAST STATE]
------------------------------
- Added Gross Value: $X–$Y
- Removed by Overlap: $X–$Y
- Net Portfolio Change: +$X–$Y or -$X–$Y

------------------------------
[TOP VALUE DRIVERS]
------------------------------
1.
2.
3.

------------------------------
[VALUE LEAKS]
------------------------------
- ...
- ...
- ...

------------------------------
[HARD TRUTH]
------------------------------
- ...
- ...
- ...

==================================================
ANTI-INFLATION RULE
==================================================

Never stack value from:
- the same asset repeated in different wording
- slight rewrites of the same code
- decorative UI added to an existing engine
- “research” that is mostly copied or generic
- packaging without functionality
- adjacent ideas with no implementation

Count incremental value only.

==================================================
DEFAULT INITIALIZATION RULE
==================================================

If the user says:
“Initialize ledger from this chat”
then:
1. detect all assets in the current conversation
2. assign IDs
3. build the first ledger snapshot
4. calculate initial totals
5. state uncertainty where chat history is incomplete

If prior ledger state is missing, create:
- Chat 001
- initial asset index
- initial portfolio baseline

==================================================
FINAL BEHAVIOR RULE
==================================================

You are not here to flatter.
You are here to:
- structure
- deduplicate
- appraise
- merge
- track
- update
- tell the financial truth
```

This version is better because it adds:

- a fixed processing sequence
- explicit anti-double-counting rules
- real/partial/fake separation
- confidence scoring
- clearer portfolio math
- version handling for evolving assets
- a much stricter output contract

Best follow-up command to use with it:

```text
Initialize ledger from this chat.
Detect all assets already mentioned.
Assign asset IDs.
Build Chat 001.
Calculate gross value, overlap discount, net portfolio value, and productized portfolio value.
Then show the hard truth.
```

If you want, I can also give you **ledger v2** with:

- per-file indexing
- code-quality scoring
- production-readiness scoring
- security penalty scoring
- chat-by-chat cumulative value math
- a stricter formula sheet for dollar ranges


#### You:
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
═══════════════════════════════════════════════════════════════════════════════
AEGIS TRIAGE
Human-Guided Crisis Signal Intelligence Platform
NIH SBIR Research Prototype — Single-File Edition
═══════════════════════════════════════════════════════════════════════════════

OVERVIEW
--------
Aegis Triage is a research-oriented, human-guided crisis signal intelligence
prototype designed for:
- real-time crisis signal intake,
- explainable urgency estimation,
- policy-aware routing recommendations,
- operator review support,
- retrospective audit and evaluation.

This file intentionally combines:
1) SBIR-style concept framing
2) a functional deterministic prototype
3) storage, audit, and reporting utilities
4) a command-line interface for demo, batch, and interactive use

IMPORTANT
---------
This software is a research prototype for workflow support, evaluation,
simulation, and pilot design. It is not a substitute for licensed clinical
judgment, emergency response procedure, or approved crisis center policy.

DESIGN PRINCIPLES
-----------------
- human-guided, not human-replacing
- deterministic and explainable
- auditable and retrospective-ready
- conservative in uncertainty
- single-file deployable
- pilot-program friendly

EXAMPLES
--------
python aegis_triage.py --demo
python aegis_triage.py --interactive
python aegis_triage.py --batch cases.jsonl
python aegis_triage.py --summary
python aegis_triage.py --print-concept

OPTIONAL ENVIRONMENT VARIABLES
------------------------------
AEGIS_DB=aegis_triage.db
AEGIS_AUDIT_JSONL=aegis_audit.jsonl
AEGIS_POLICY=default
AEGIS_VERBOSE=true
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import statistics
import textwrap
import time
import hashlib
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# BRAND + CONCEPT LAYER
# =============================================================================

BRAND_NAME = "Aegis Triage"
BRAND_TAGLINE = "Human-Guided Crisis Signal Intelligence Platform"
BRAND_SHORT_DESCRIPTION = (
    "A deterministic, explainable, human-guided triage intelligence prototype "
    "for crisis workflows, research pilots, and operator decision support."
)

PROJECT_TITLE = f"{BRAND_NAME}: {BRAND_TAGLINE}"

PROJECT_SUMMARY = """
Crisis response environments, including 988-aligned operations, behavioral
health triage teams, telehealth intake, and emergency communication workflows,
must make high-stakes prioritization decisions under time pressure, incomplete
information, and variable staffing.

Aegis Triage is a human-guided crisis signal intelligence platform designed to
support those workflows with deterministic feature extraction, explainable
urgency estimation, policy-aware routing recommendations, and retrospective
auditability.

The system does not replace human judgment. Instead, it helps teams:
- identify salient crisis indicators,
- structure urgency review consistently,
- prioritize uncertain and high-risk cases conservatively,
- log decision context for quality assurance and research,
- create an evaluation pathway for future supervised model refinement.

The goal is to improve response consistency, transparency, timeliness, and
operational learning in crisis support environments.
""".strip()

SPECIFIC_AIMS = [
    "Build a real-time crisis signal intake and feature extraction pipeline.",
    "Develop an explainable, deterministic urgency estimation engine.",
    "Implement policy-aware routing recommendations with conservative safety rules.",
    "Create a feedback and retrospective analysis layer for continuous evaluation.",
]

SIGNIFICANCE = [
    "Improves consistency in high-pressure triage workflows.",
    "Preserves human authority while enhancing operator support.",
    "Creates auditable evidence for quality assurance and pilot review.",
    "Supports public-sector and healthcare-oriented AI operations modernization.",
]

INNOVATION = [
    "Explainable crisis signal intelligence rather than opaque scoring alone.",
    "Conservative uncertainty handling that escalates review rather than suppressing it.",
    "Policy-aware routing recommendations with explicit safety floors.",
    "Single-file deployable research architecture for rapid pilots and demos.",
]

TECHNICAL_RISKS = [
    "Ambiguous language may create uncertainty in urgency estimation.",
    "Metaphorical or quoted language may trigger false positives.",
    "Workflow misuse may occur if operators over-trust automated suggestions.",
    "Different channels and populations may require policy recalibration.",
]

RISK_MITIGATIONS = [
    "Route uncertain cases toward human review.",
    "Maintain deterministic logic and transparent feature contributions.",
    "Enforce conservative safety floors for self-harm and violence signals.",
    "Preserve full audit logs for calibration and incident review.",
]

COMMERCIALIZATION = [
    "Crisis hotline modernization pilots",
    "Behavioral health intake support systems",
    "Emergency communications decision-support tooling",
    "Healthcare operations intelligence infrastructure",
]

MILESTONES = [
    "Signal intake and feature extraction baseline",
    "Urgency estimation and policy routing baseline",
    "Audit logging and persistence layer",
    "Outcome tracking and retrospective reporting",
    "Pilot-readiness package for grant and procurement discussions",
]

BUDGET = {
    "engineering": 90000,
    "clinical_advisory": 35000,
    "security_and_compliance": 20000,
    "cloud_and_storage": 12000,
    "evaluation_and_pilot_support": 28000,
    "miscellaneous": 15000,
}


# =============================================================================
# UTILITY LAYER
# =============================================================================

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_case_id(message: str, timestamp: float) -> str:
    raw = f"{timestamp}|{message}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:16]
    return f"aegis_{digest}"


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compact_text(text: str, width: int = 88) -> str:
    text = " ".join(text.split())
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


# =============================================================================
# POLICY LAYER
# =============================================================================

@dataclass
class Policy:
    name: str = "default"

    critical_threshold: float = 0.85
    high_threshold: float = 0.65
    medium_threshold: float = 0.40

    low_confidence_threshold: float = 0.45
    uncertain_high_risk_floor: float = 0.60

    emergency_route: str = "EMERGENCY_DISPATCH_RECOMMENDED"
    immediate_route: str = "IMMEDIATE_CLINICIAN_REVIEW"
    urgent_review_route: str = "URGENT_HUMAN_REVIEW"
    priority_queue_route: str = "PRIORITY_QUEUE"
    standard_queue_route: str = "STANDARD_QUEUE"
    mandatory_review_route: str = "MANDATORY_HUMAN_REVIEW"

    w_high_risk: float = 0.24
    w_medium_risk: float = 0.09
    w_plan: float = 0.22
    w_means: float = 0.16
    w_immediacy: float = 0.18
    w_self_harm: float = 0.26
    w_violence: float = 0.26
    w_distress: float = 0.10
    w_protective: float = -0.18
    w_help_seeking: float = -0.04
    w_negation_safety: float = -0.10
    w_short_signal: float = 0.08
    w_caps: float = 0.03
    w_punctuation: float = 0.03

    confidence_base: float = 0.50
    confidence_per_feature_group: float = 0.05
    confidence_per_signal_density: float = 0.04
    confidence_penalty_ambiguity: float = 0.10
    confidence_penalty_too_short: float = 0.08
    confidence_bonus_metadata: float = 0.05

    require_human_review_for_high: bool = True
    route_low_confidence_to_human: bool = True
    preserve_self_harm_floor: bool = True
    preserve_violence_floor: bool = True


def load_policy(name: str = "default") -> Policy:
    return Policy(name=name)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class CrisisSignal:
    case_id: str
    timestamp: float
    created_at: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureSet:
    word_count: int
    char_count: int
    sentence_count: int
    uppercase_ratio: float
    exclamation_count: int
    question_count: int

    high_risk_hits: List[str] = field(default_factory=list)
    medium_risk_hits: List[str] = field(default_factory=list)
    plan_hits: List[str] = field(default_factory=list)
    means_hits: List[str] = field(default_factory=list)
    immediacy_hits: List[str] = field(default_factory=list)
    self_harm_hits: List[str] = field(default_factory=list)
    violence_hits: List[str] = field(default_factory=list)
    protective_hits: List[str] = field(default_factory=list)
    help_hits: List[str] = field(default_factory=list)
    negation_hits: List[str] = field(default_factory=list)
    ambiguity_hits: List[str] = field(default_factory=list)
    distress_hits: List[str] = field(default_factory=list)

    def total_hits(self) -> int:
        groups = [
            self.high_risk_hits,
            self.medium_risk_hits,
            self.plan_hits,
            self.means_hits,
            self.immediacy_hits,
            self.self_harm_hits,
            self.violence_hits,
            self.protective_hits,
            self.help_hits,
            self.negation_hits,
            self.ambiguity_hits,
            self.distress_hits,
        ]
        return sum(len(group) for group in groups)


@dataclass
class RiskAssessment:
    urgency: float
    confidence: float
    band: str
    reasons: List[str] = field(default_factory=list)
    contributions: Dict[str, float] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    priority: str
    route_to: str
    explanation: str
    requires_human_review: bool
    safety_flags: List[str] = field(default_factory=list)


@dataclass
class CaseRecord:
    case_id: str
    signal: CrisisSignal
    features: FeatureSet
    risk: RiskAssessment
    decision: RoutingDecision
    processing_ms: float
    outcome: Optional[str] = None
    reviewer_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "signal": asdict(self.signal),
            "features": asdict(self.features),
            "risk": asdict(self.risk),
            "decision": asdict(self.decision),
            "processing_ms": self.processing_ms,
            "outcome": self.outcome,
            "reviewer_notes": self.reviewer_notes,
        }


# =============================================================================
# FEATURE EXTRACTION LAYER
# =============================================================================

class SignalAnalyzer:
    """
    Deterministic language-pattern extractor for research prototypes.
    """

    HIGH_RISK = {
        r"\bi want to die\b": "want_to_die",
        r"\bend my life\b": "end_my_life",
        r"\bkill myself\b": "kill_myself",
        r"\bsuicide\b": "suicide",
        r"\bno reason to live\b": "no_reason_to_live",
        r"\bcan't go on\b": "cant_go_on",
        r"\boverdose\b": "overdose",
        r"\bhurt myself\b": "hurt_myself",
        r"\bself harm\b": "self_harm",
    }

    MEDIUM_RISK = {
        r"\bhopeless\b": "hopeless",
        r"\bpanic\b": "panic",
        r"\bdesperate\b": "desperate",
        r"\boverwhelmed\b": "overwhelmed",
        r"\bscared\b": "scared",
        r"\bafraid\b": "afraid",
        r"\bbreaking down\b": "breaking_down",
        r"\bin crisis\b": "in_crisis",
        r"\balone\b": "alone",
    }

    PLAN = {
        r"\bi have a plan\b": "have_a_plan",
        r"\bplanned\b": "planned",
        r"\bi know how\b": "know_how",
        r"\btonight\b": "tonight",
        r"\bafter everyone sleeps\b": "after_everyone_sleeps",
    }

    MEANS = {
        r"\bpills\b": "pills",
        r"\bgun\b": "gun",
        r"\bknife\b": "knife",
        r"\brope\b": "rope",
        r"\bweapon\b": "weapon",
        r"\brazor\b": "razor",
    }

    IMMEDIACY = {
        r"\bnow\b": "now",
        r"\bright now\b": "right_now",
        r"\btoday\b": "today",
        r"\btonight\b": "tonight",
        r"\bimmediately\b": "immediately",
        r"\bsoon\b": "soon",
    }

    SELF_HARM = {
        r"\bhurt myself\b": "hurt_myself",
        r"\bcut myself\b": "cut_myself",
        r"\bself harm\b": "self_harm",
        r"\bkill myself\b": "kill_myself",
        r"\bend my life\b": "end_my_life",
    }

    VIOLENCE = {
        r"\bhurt someone\b": "hurt_someone",
        r"\bkill them\b": "kill_them",
        r"\bshoot\b": "shoot",
        r"\bstab\b": "stab",
        r"\bviolent\b": "violent",
        r"\bweapon\b": "weapon",
    }

    PROTECTIVE = {
        r"\bi am safe\b": "i_am_safe",
        r"\bi'm safe\b": "i_am_safe",
        r"\bi won't do anything\b": "wont_do_anything",
        r"\bi do not want to die\b": "do_not_want_to_die",
        r"\bi don't want to die\b": "do_not_want_to_die",
        r"\bi am with someone\b": "with_someone",
        r"\bi'm with someone\b": "with_someone",
        r"\bmy therapist\b": "therapist",
        r"\bmy counselor\b": "counselor",
    }

    HELP = {
        r"\bplease help\b": "please_help",
        r"\bneed help\b": "need_help",
        r"\bi need to talk\b": "need_to_talk",
        r"\bcan someone talk\b": "someone_talk",
        r"\blooking for support\b": "support",
    }

    NEGATION = {
        r"\bnot suicidal\b": "not_suicidal",
        r"\bnot going to hurt myself\b": "not_hurt_self",
        r"\bnot going to kill myself\b": "not_kill_self",
        r"\bno plan\b": "no_plan",
        r"\bno intent\b": "no_intent",
    }

    AMBIGUITY = {
        r"\bjust kidding\b": "just_kidding",
        r"\bfiguratively\b": "figuratively",
        r"\bquote\b": "quote",
        r"\bsong lyric\b": "song_lyric",
        r"\bmetaphor\b": "metaphor",
    }

    DISTRESS = {
        r"\bcan't\b": "cant",
        r"\bnever\b": "never",
        r"\balways\b": "always",
        r"\bno one\b": "no_one",
        r"\bnobody\b": "nobody",
        r"\bi'm done\b": "im_done",
        r"\bi am done\b": "im_done",
    }

    @staticmethod
    def _hits(text: str, patterns: Dict[str, str]) -> List[str]:
        found: List[str] = []
        for pattern, label in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.append(label)
        return sorted(set(found))

    @staticmethod
    def _sentence_count(text: str) -> int:
        parts = [p.strip() for p in re.split(r"[.!?]+", text) if p.strip()]
        return max(1, len(parts))

    @staticmethod
    def _uppercase_ratio(text: str) -> float:
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        uppercase = sum(1 for c in letters if c.isupper())
        return round(uppercase / len(letters), 4)

    def analyze(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[CrisisSignal, FeatureSet]:
        timestamp = time.time()
        case_id = make_case_id(message, timestamp)
        signal = CrisisSignal(
            case_id=case_id,
            timestamp=timestamp,
            created_at=now_utc_iso(),
            message=message,
            metadata=dict(metadata or {}),
        )

        lower = message.lower()
        features = FeatureSet(
            word_count=len(message.split()),
            char_count=len(message),
            sentence_count=self._sentence_count(message),
            uppercase_ratio=self._uppercase_ratio(message),
            exclamation_count=message.count("!"),
            question_count=message.count("?"),
            high_risk_hits=self._hits(lower, self.HIGH_RISK),
            medium_risk_hits=self._hits(lower, self.MEDIUM_RISK),
            plan_hits=self._hits(lower, self.PLAN),
            means_hits=self._hits(lower, self.MEANS),
            immediacy_hits=self._hits(lower, self.IMMEDIACY),
            self_harm_hits=self._hits(lower, self.SELF_HARM),
            violence_hits=self._hits(lower, self.VIOLENCE),
            protective_hits=self._hits(lower, self.PROTECTIVE),
            help_hits=self._hits(lower, self.HELP),
            negation_hits=self._hits(lower, self.NEGATION),
            ambiguity_hits=self._hits(lower, self.AMBIGUITY),
            distress_hits=self._hits(lower, self.DISTRESS),
        )

        signal.metadata.update(
            {
                "word_count": features.word_count,
                "char_count": features.char_count,
                "sentence_count": features.sentence_count,
                "uppercase_ratio": features.uppercase_ratio,
                "exclamation_count": features.exclamation_count,
                "question_count": features.question_count,
            }
        )
        return signal, features


# =============================================================================
# RISK LAYER
# =============================================================================

class UrgencyModel:
    def __init__(self, policy: Policy):
        self.policy = policy

    def assess(self, signal: CrisisSignal, features: FeatureSet) -> RiskAssessment:
        contributions: Dict[str, float] = {}
        reasons: List[str] = []

        base = min(0.18, features.word_count / 300.0)
        contributions["base_text_density"] = round(base, 4)

        def add_if_nonzero(name: str, value: float) -> None:
            if value:
                contributions[name] = round(value, 4)

        high = len(features.high_risk_hits) * self.policy.w_high_risk
        medium = len(features.medium_risk_hits) * self.policy.w_medium_risk
        plan = len(features.plan_hits) * self.policy.w_plan
        means = len(features.means_hits) * self.policy.w_means
        immediacy = len(features.immediacy_hits) * self.policy.w_immediacy
        self_harm = len(features.self_harm_hits) * self.policy.w_self_harm
        violence = len(features.violence_hits) * self.policy.w_violence
        distress = len(features.distress_hits) * self.policy.w_distress
        protective = len(features.protective_hits) * self.policy.w_protective
        help_signal = len(features.help_hits) * self.policy.w_help_seeking
        negation = len(features.negation_hits) * self.policy.w_negation_safety

        add_if_nonzero("high_risk", high)
        add_if_nonzero("medium_risk", medium)
        add_if_nonzero("plan", plan)
        add_if_nonzero("means", means)
        add_if_nonzero("immediacy", immediacy)
        add_if_nonzero("self_harm", self_harm)
        add_if_nonzero("violence", violence)
        add_if_nonzero("distress", distress)
        add_if_nonzero("protective", protective)
        add_if_nonzero("help_seeking", help_signal)
        add_if_nonzero("negation", negation)

        if features.high_risk_hits:
            reasons.append(f"high-risk indicators: {', '.join(features.high_risk_hits)}")
        if features.medium_risk_hits:
            reasons.append(f"distress indicators: {', '.join(features.medium_risk_hits)}")
        if features.plan_hits:
            reasons.append(f"plan indicators: {', '.join(features.plan_hits)}")
        if features.means_hits:
            reasons.append(f"means indicators: {', '.join(features.means_hits)}")
        if features.immediacy_hits:
            reasons.append(f"time/immediacy indicators: {', '.join(features.immediacy_hits)}")
        if features.self_harm_hits:
            reasons.append(f"self-harm indicators: {', '.join(features.self_harm_hits)}")
        if features.violence_hits:
            reasons.append(f"violence indicators: {', '.join(features.violence_hits)}")
        if features.protective_hits:
            reasons.append(f"protective factors: {', '.join(features.protective_hits)}")
        if features.help_hits:
            reasons.append(f"help-seeking language: {', '.join(features.help_hits)}")

        short_signal = 0.0
        if features.word_count <= 3 and (
            features.high_risk_hits
            or features.medium_risk_hits
            or features.help_hits
            or features.self_harm_hits
        ):
            short_signal = self.policy.w_short_signal
            contributions["short_signal"] = round(short_signal, 4)
            reasons.append("very short message with meaningful crisis/help signal")

        emphasis = 0.0
        if features.uppercase_ratio >= 0.35:
            emphasis += self.policy.w_caps
        if features.exclamation_count >= 2:
            emphasis += self.policy.w_punctuation
        add_if_nonzero("emphasis", emphasis)

        urgency_raw = (
            base
            + high
            + medium
            + plan
            + means
            + immediacy
            + self_harm
            + violence
            + distress
            + protective
            + help_signal
            + negation
            + short_signal
            + emphasis
        )

        if features.self_harm_hits and self.policy.preserve_self_harm_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["self_harm_floor"] = 0.72

        if features.violence_hits and self.policy.preserve_violence_floor:
            urgency_raw = max(urgency_raw, 0.72)
            contributions["violence_floor"] = 0.72

        urgency = clamp01(urgency_raw)

        feature_groups = sum(
            1 for group in [
                features.high_risk_hits,
                features.medium_risk_hits,
                features.plan_hits,
                features.means_hits,
                features.immediacy_hits,
                features.self_harm_hits,
                features.violence_hits,
                features.protective_hits,
                features.help_hits,
                features.negation_hits,
                features.ambiguity_hits,
                features.distress_hits,
            ] if group
        )

        confidence = self.policy.confidence_base
        confidence += feature_groups * self.policy.confidence_per_feature_group
        confidence += min(4, features.total_hits()) * self.policy.confidence_per_signal_density

        if features.ambiguity_hits:
            confidence -= self.policy.confidence_penalty_ambiguity
            reasons.append(f"ambiguity markers: {', '.join(features.ambiguity_hits)}")

        if features.word_count <= 2:
            confidence -= self.policy.confidence_penalty_too_short
            reasons.append("extremely short input lowers confidence")

        if signal.metadata:
            confidence += self.policy.confidence_bonus_metadata

        confidence = clamp01(confidence)

        if urgency >= self.policy.critical_threshold:
            band = "CRITICAL"
        elif urgency >= self.policy.high_threshold:
            band = "HIGH"
        elif urgency >= self.policy.medium_threshold:
            band = "MEDIUM"
        else:
            band = "LOW"

        if not reasons:
            reasons.append("limited direct risk language; estimate driven by general signal density")

        return RiskAssessment(
            urgency=round(urgency, 4),
            confidence=round(confidence, 4),
            band=band,
            reasons=reasons,
            contributions=contributions,
        )


# =============================================================================
# DECISION LAYER
# =============================================================================

class RoutingEngine:
    def __init__(self, policy: Policy):
        self.policy = policy

    def decide(self, features: FeatureSet, risk: RiskAssessment) -> RoutingDecision:
        flags: List[str] = []
        low_confidence = risk.confidence < self.policy.low_confidence_threshold
        self_harm_present = bool(features.self_harm_hits or features.high_risk_hits)
        violence_present = bool(features.violence_hits)

        if self_harm_present:
            flags.append("SELF_HARM_SIGNAL")
        if violence_present:
            flags.append("VIOLENCE_SIGNAL")
        if features.plan_hits:
            flags.append("PLAN_INDICATOR")
        if features.means_hits:
            flags.append("MEANS_INDICATOR")
        if low_confidence:
            flags.append("LOW_CONFIDENCE")

        if risk.urgency >= self.policy.critical_threshold:
            priority = "CRITICAL"
            route = self.policy.emergency_route
            review = True
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds critical threshold "
                f"{self.policy.critical_threshold:.2f}; emergency-aligned escalation is recommended."
            )
        elif risk.urgency >= self.policy.high_threshold:
            priority = "HIGH"
            route = self.policy.immediate_route
            review = self.policy.require_human_review_for_high
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds high threshold "
                f"{self.policy.high_threshold:.2f}; immediate clinician review is recommended."
            )
        elif risk.urgency >= self.policy.medium_threshold:
            priority = "MEDIUM"
            route = self.policy.priority_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} exceeds medium threshold "
                f"{self.policy.medium_threshold:.2f}; priority handling is recommended."
            )
        else:
            priority = "LOW"
            route = self.policy.standard_queue_route
            review = False
            explanation = (
                f"Urgency {risk.urgency:.2f} is below medium threshold; "
                f"standard queue placement is recommended."
            )

        if low_confidence and self.policy.route_low_confidence_to_human:
            route = self.policy.mandatory_review_route
            review = True
            explanation += " Confidence is limited, so human review is required."

        if risk.urgency >= self.policy.uncertain_high_risk_floor and low_confidence:
            route = self.policy.urgent_review_route
            review = True
            explanation += " High-risk plus uncertainty triggers urgent human review."

        if self_harm_present and priority == "LOW":
            priority = "MEDIUM"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Self-harm language prevents a low-priority disposition."

        if violence_present and priority in {"LOW", "MEDIUM"}:
            priority = "HIGH"
            route = self.policy.urgent_review_route
            review = True
            explanation += " Violence language elevates the case for urgent review."

        return RoutingDecision(
            priority=priority,
            route_to=route,
            explanation=explanation,
            requires_human_review=review,
            safety_flags=flags,
        )


# =============================================================================
# STORAGE LAYER
# =============================================================================

class CaseStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_records (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                timestamp REAL NOT NULL,
                message TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                features_json TEXT NOT NULL,
                risk_json TEXT NOT NULL,
                decision_json TEXT NOT NULL,
                processing_ms REAL NOT NULL,
                outcome TEXT,
                reviewer_notes TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS case_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                reviewer_notes TEXT,
                recorded_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_case_outcomes_case_id ON case_outcomes(case_id)"
        )
        self.conn.commit()

    def save(self, record: CaseRecord) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO case_records (
                case_id, created_at, timestamp, message, metadata_json,
                features_json, risk_json, decision_json, processing_ms,
                outcome, reviewer_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.case_id,
                record.signal.created_at,
                record.signal.timestamp,
                record.signal.message,
                json.dumps(record.signal.metadata, ensure_ascii=False),
                json.dumps(asdict(record.features), ensure_ascii=False),
                json.dumps(asdict(record.risk), ensure_ascii=False),
                json.dumps(asdict(record.decision), ensure_ascii=False),
                record.processing_ms,
                record.outcome,
                record.reviewer_notes,
            ),
        )
        self.conn.commit()

    def set_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE case_records
            SET outcome = ?, reviewer_notes = ?
            WHERE case_id = ?
            """,
            (outcome, reviewer_notes, case_id),
        )
        updated = cur.rowcount > 0
        cur.execute(
            """
            INSERT INTO case_outcomes (case_id, outcome, reviewer_notes, recorded_at)
            VALUES (?, ?, ?, ?)
            """,
            (case_id, outcome, reviewer_notes, now_utc_iso()),
        )
        self.conn.commit()
        return updated

    def get(self, case_id: str) -> Optional[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM case_records WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_recent(self, limit: int = 1000) -> List[CaseRecord]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM case_records ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row: sqlite3.Row) -> CaseRecord:
        signal = CrisisSignal(
            case_id=row["case_id"],
            timestamp=row["timestamp"],
            created_at=row["created_at"],
            message=row["message"],
            metadata=json.loads(row["metadata_json"]),
        )
        features = FeatureSet(**json.loads(row["features_json"]))
        risk = RiskAssessment(**json.loads(row["risk_json"]))
        decision = RoutingDecision(**json.loads(row["decision_json"]))
        return CaseRecord(
            case_id=row["case_id"],
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=row["processing_ms"],
            outcome=row["outcome"],
            reviewer_notes=row["reviewer_notes"],
        )

    def close(self) -> None:
        self.conn.close()


# =============================================================================
# AUDIT LAYER
# =============================================================================

class AuditTrail:
    def __init__(self, jsonl_path: str, verbose: bool = True):
        self.jsonl_path = jsonl_path
        self.verbose = verbose
        self._entries: List[Dict[str, Any]] = []

    def log(self, record: CaseRecord) -> None:
        entry = record.to_dict()
        self._entries.append(entry)

        with open(self.jsonl_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if self.verbose:
            self._print(record)

    def _print(self, record: CaseRecord) -> None:
        print("┌" + "─" * 78)
        print(f"│ BRAND        : {BRAND_NAME}")
        print(f"│ CASE ID      : {record.case_id}")
        print(f"│ MESSAGE      : {compact_text(record.signal.message)}")
        print(f"│ URGENCY      : {record.risk.urgency:.4f}    CONFIDENCE: {record.risk.confidence:.4f}")
        print(f"│ BAND         : {record.risk.band}")
        print(f"│ PRIORITY     : {record.decision.priority:<12} ROUTE: {record.decision.route_to}")
        print(f"│ HUMAN REVIEW : {record.decision.requires_human_review}")
        print(f"│ FLAGS        : {', '.join(record.decision.safety_flags) if record.decision.safety_flags else 'None'}")
        print(f"│ REASONS      : {compact_text('; '.join(record.risk.reasons[:3]), 70)}")
        print(f"│ LATENCY      : {record.processing_ms:.2f} ms")
        print("└" + "─" * 78)

    def export_json(self) -> str:
        return json.dumps(self._entries, indent=2, ensure_ascii=False)


# =============================================================================
# FEEDBACK + REPORTING LAYER
# =============================================================================

class ReviewLoop:
    def __init__(self, store: CaseStore):
        self.store = store

    def record_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.store.set_outcome(case_id, outcome, reviewer_notes)

    def summary(self, limit: int = 5000) -> Dict[str, Any]:
        records = self.store.list_recent(limit=limit)
        if not records:
            return {"records": 0}

        urgencies = [r.risk.urgency for r in records]
        confidences = [r.risk.confidence for r in records]
        priorities = [r.decision.priority for r in records]
        routes = [r.decision.route_to for r in records]
        outcomes = [r.outcome for r in records if r.outcome]

        return {
            "brand": BRAND_NAME,
            "records": len(records),
            "avg_urgency": round(statistics.mean(urgencies), 4),
            "max_urgency": round(max(urgencies), 4),
            "avg_confidence": round(statistics.mean(confidences), 4),
            "human_review_rate": round(
                sum(1 for r in records if r.decision.requires_human_review) / len(records), 4
            ),
            "band_distribution": dict(Counter(r.risk.band for r in records)),
            "priority_distribution": dict(Counter(priorities)),
            "route_distribution": dict(Counter(routes)),
            "outcomes_logged": len(outcomes),
            "outcome_distribution": dict(Counter(outcomes)),
        }

    def calibration_snapshot(self, limit: int = 5000) -> Dict[str, Any]:
        records = [r for r in self.store.list_recent(limit=limit) if r.outcome]
        if not records:
            return {"records_with_outcomes": 0, "buckets": {}}

        buckets = {
            "0.00-0.39": [],
            "0.40-0.64": [],
            "0.65-0.84": [],
            "0.85-1.00": [],
        }

        for record in records:
            u = record.risk.urgency
            if u < 0.40:
                buckets["0.00-0.39"].append(record.outcome or "UNKNOWN")
            elif u < 0.65:
                buckets["0.40-0.64"].append(record.outcome or "UNKNOWN")
            elif u < 0.85:
                buckets["0.65-0.84"].append(record.outcome or "UNKNOWN")
            else:
                buckets["0.85-1.00"].append(record.outcome or "UNKNOWN")

        return {
            "records_with_outcomes": len(records),
            "buckets": {k: dict(Counter(v)) for k, v in buckets.items()},
        }


# =============================================================================
# ORCHESTRATION LAYER
# =============================================================================

class AegisTriageEngine:
    def __init__(
        self,
        db_path: str,
        audit_jsonl_path: str,
        verbose: bool = True,
        policy_name: str = "default",
    ):
        self.policy = load_policy(policy_name)
        self.analyzer = SignalAnalyzer()
        self.urgency_model = UrgencyModel(self.policy)
        self.routing_engine = RoutingEngine(self.policy)
        self.store = CaseStore(db_path)
        self.audit = AuditTrail(audit_jsonl_path, verbose=verbose)
        self.review = ReviewLoop(self.store)

    def process(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> CaseRecord:
        start = time.perf_counter()

        signal, features = self.analyzer.analyze(message, metadata=metadata)
        risk = self.urgency_model.assess(signal, features)
        decision = self.routing_engine.decide(features, risk)

        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 3)

        record = CaseRecord(
            case_id=signal.case_id,
            signal=signal,
            features=features,
            risk=risk,
            decision=decision,
            processing_ms=elapsed_ms,
        )

        self.store.save(record)
        self.audit.log(record)
        return record

    def log_outcome(self, case_id: str, outcome: str, reviewer_notes: Optional[str] = None) -> bool:
        return self.review.record_outcome(case_id, outcome, reviewer_notes)

    def export_records(self, path: str, limit: int = 5000) -> None:
        payload = [r.to_dict() for r in self.store.list_recent(limit=limit)]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    def summary(self) -> Dict[str, Any]:
        return self.review.summary()

    def calibration(self) -> Dict[str, Any]:
        return self.review.calibration_snapshot()

    def close(self) -> None:
        self.store.close()


# =============================================================================
# PRESENTATION LAYER
# =============================================================================

def print_header(title: str) -> None:
    print("\n" + "═" * 80)
    print(title)
    print("═" * 80 + "\n")


def print_concept() -> None:
    print_header(f"{BRAND_NAME.upper()} — SBIR RESEARCH CONCEPT")
    sections = {
        "TITLE": PROJECT_TITLE,
        "BRAND DESCRIPTION": BRAND_SHORT_DESCRIPTION,
        "PROJECT SUMMARY": PROJECT_SUMMARY,
        "SPECIFIC AIMS": SPECIFIC_AIMS,
        "SIGNIFICANCE": SIGNIFICANCE,
        "INNOVATION": INNOVATION,
        "TECHNICAL RISKS": TECHNICAL_RISKS,
        "RISK MITIGATIONS": RISK_MITIGATIONS,
        "COMMERCIALIZATION": COMMERCIALIZATION,
        "MILESTONES": MILESTONES,
        "BUDGET": BUDGET,
    }

    for name, value in sections.items():
        print(name)
        print("-" * len(name))
        if isinstance(value, str):
            print(textwrap.fill(value, width=88))
        elif isinstance(value, dict):
            for k, v in value.items():
                print(f"  - {k}: ${v:,.0f}")
        else:
            for item in value:
                print(f"  - {item}")
        print()


def print_summary(summary: Dict[str, Any], calibration: Optional[Dict[str, Any]] = None) -> None:
    print_header(f"{BRAND_NAME.upper()} — SUMMARY")
    for key, value in summary.items():
        print(f"{key:>24} : {value}")
    if calibration is not None:
        print("\nCALIBRATION SNAPSHOT")
        print("--------------------")
        for key, value in calibration.items():
            print(f"{key:>24} : {value}")
    print()


def print_case(record: CaseRecord) -> None:
    print_header(f"{BRAND_NAME.upper()} — CASE DETAIL")
    print(f"Case ID         : {record.case_id}")
    print(f"Created at      : {record.signal.created_at}")
    print(f"Message         : {record.signal.message}")
    print(f"Metadata        : {json.dumps(record.signal.metadata, ensure_ascii=False)}")
    print()
    print("FEATURES")
    print("--------")
    print(json.dumps(asdict(record.features), indent=2, ensure_ascii=False))
    print()
    print("RISK")
    print("----")
    print(json.dumps(asdict(record.risk), indent=2, ensure_ascii=False))
    print()
    print("DECISION")
    print("--------")
    print(json.dumps(asdict(record.decision), indent=2, ensure_ascii=False))
    print()
    print(f"Processing ms   : {record.processing_ms}")
    print(f"Outcome         : {record.outcome}")
    print(f"Reviewer notes  : {record.reviewer_notes}")
    print()


# =============================================================================
# DEMO CASES
# =============================================================================

DEMO_CASES: List[Tuple[str, Dict[str, Any], str]] = [
    (
        "I've been feeling a little down lately and just needed to talk.",
        {"channel": "chat", "source": "demo"},
        "RESOLVED_SUPPORTIVE_CONTACT",
    ),
    (
        "I don't know how much longer I can handle this. I feel completely overwhelmed and scared.",
        {"channel": "chat", "source": "demo"},
        "COUNSELOR_FOLLOW_UP",
    ),
    (
        "I'm in crisis right now. I feel hopeless and desperate. Please help me.",
        {"channel": "voice", "source": "demo"},
        "IMMEDIATE_CLINICIAN_CONTACT",
    ),
    (
        "I want to end my life tonight. I have a plan and I don't see any reason to go on.",
        {"channel": "chat", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
    (
        "help",
        {"channel": "sms", "source": "demo"},
        "MONITORED_AND_ENGAGED",
    ),
    (
        "Not suicidal. No plan. I am safe, but I really need to talk to someone tonight because I'm panicking.",
        {"channel": "chat", "source": "demo"},
        "URGENT_SUPPORT_CONTACT",
    ),
    (
        "I have pills and I think tonight is the night.",
        {"channel": "sms", "source": "demo"},
        "EMERGENCY_ESCALATION",
    ),
]


# =============================================================================
# CLI LAYER
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{BRAND_NAME} — single-file research prototype"
    )
    parser.add_argument("--demo", action="store_true", help="Run built-in demonstration cases")
    parser.add_argument("--interactive", action="store_true", help="Run interactive console mode")
    parser.add_argument("--batch", type=str, help="Process a JSONL batch file")
    parser.add_argument("--summary", action="store_true", help="Print stored summary")
    parser.add_argument("--show-case", type=str, help="Show stored case by case_id")
    parser.add_argument("--export-records", type=str, help="Export records to JSON")
    parser.add_argument("--print-concept", action="store_true", help="Print concept package")
    parser.add_argument("--quiet", action="store_true", help="Reduce console output")
    parser.add_argument("--db", type=str, default=os.getenv("AEGIS_DB", "aegis_triage.db"))
    parser.add_argument(
        "--audit-jsonl",
        type=str,
        default=os.getenv("AEGIS_AUDIT_JSONL", "aegis_audit.jsonl"),
    )
    parser.add_argument(
        "--policy",
        type=str,
        default=os.getenv("AEGIS_POLICY", "default"),
    )
    return parser.parse_args(argv)


def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Line {line_no} is not a JSON object")
            yield item


def run_demo(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — DEMO")
    for idx, (message, metadata, outcome) in enumerate(DEMO_CASES, start=1):
        print(f"[Demo Case {idx}/{len(DEMO_CASES)}]")
        record = engine.process(message, metadata=metadata)
        engine.log_outcome(record.case_id, outcome, reviewer_notes="demo outcome")
        print(f"Outcome logged : {outcome}\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_batch(engine: AegisTriageEngine, path: str) -> None:
    print_header(f"{BRAND_NAME.upper()} — BATCH MODE")
    processed = 0
    for item in iter_jsonl(path):
        message = str(item.get("message", "")).strip()
        metadata = item.get("metadata", {})
        if not message:
            continue
        engine.process(message, metadata if isinstance(metadata, dict) else {})
        processed += 1
    print(f"Processed {processed} records.\n")
    print_summary(engine.summary(), calibration=engine.calibration())


def run_interactive(engine: AegisTriageEngine) -> None:
    print_header(f"{BRAND_NAME.upper()} — INTERACTIVE MODE")
    print("Enter a message, then press Enter.")
    print("Commands:")
    print("  /quit")
    print("  /summary")
    print("  /show <case_id>")
    print("  /outcome <case_id> <OUTCOME TEXT>")
    print()

    while True:
        try:
            raw = input("message> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if not raw:
            continue
        if raw == "/quit":
            break
        if raw == "/summary":
            print_summary(engine.summary(), calibration=engine.calibration())
            continue
        if raw.startswith("/show "):
            _, _, case_id = raw.partition(" ")
            record = engine.store.get(case_id.strip())
            if record is None:
                print("Case not found.")
            else:
                print_case(record)
            continue
        if raw.startswith("/outcome "):
            parts = raw.split(maxsplit=2)
            if len(parts) < 3:
                print("Usage: /outcome <case_id> <OUTCOME TEXT>")
                continue
            _, case_id, outcome = parts
            ok = engine.log_outcome(case_id, outcome, reviewer_notes="interactive outcome")
            print("Outcome recorded." if ok else "Case not found.")
            continue

        engine.process(raw, metadata={"channel": "interactive_console"})


# =============================================================================
# MAIN
# =============================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    engine = AegisTriageEngine(
        db_path=args.db,
        audit_jsonl_path=args.audit_jsonl,
        verbose=not args.quiet,
        policy_name=args.policy,
    )

    try:
        acted = False

        if args.print_concept:
            print_concept()
            acted = True

        if args.demo:
            run_demo(engine)
            acted = True

        if args.batch:
            run_batch(engine, args.batch)
            acted = True

        if args.interactive:
            run_interactive(engine)
            acted = True

        if args.summary:
            print_summary(engine.summary(), calibration=engine.calibration())
            acted = True

        if args.show_case:
            record = engine.store.get(args.show_case)
            if record is None:
                print(f"No case found for case_id={args.show_case}")
            else:
                print_case(record)
            acted = True

        if args.export_records:
            engine.export_records(args.export_records)
            print(f"Exported records to {args.export_records}")
            acted = True

        if not acted:
            print_header(f"{BRAND_NAME.upper()} — READY")
            print(BRAND_TAGLINE)
            print()
            print("No action selected. Try:")
            print("  --demo")
            print("  --interactive")
            print("  --batch cases.jsonl")
            print("  --summary")
            print("  --print-concept")
            print()

    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main()) ==============================
MASTER LEDGER SNAPSHOT

A-001 — Aegis Triage — AI / Agent System — Net Value: $12,000–$28,000

[ASSET ID]
	•	A-001

[NAME]
	•	Aegis Triage

[TYPE]
	•	AI / Agent System

[ORIGIN]
	•	Current chat
	•	Source input: single-file Python system prompt/prototype

[FILES / SOURCES]
	•	aegis_triage.py

[DESCRIPTION]
	•	Single-file deterministic crisis triage research prototype with:
	•	branded NIH SBIR concept layer
	•	rule-based signal extraction
	•	urgency scoring
	•	routing logic
	•	SQLite persistence
	•	JSONL audit trail
	•	CLI modes for demo, interactive, batch, summary, export
	•	It is a workflow-support prototype, not a deployable clinical product.

[COMPONENTS]
	•	UI: CLI only
	•	Backend: local Python execution engine
	•	Logic: deterministic regex-based feature extraction and weighted scoring
	•	Data: SQLite case store + JSONL audit log
	•	Integration: local file I/O only
	•	Security: minimal, no auth, no encryption, no access control
	•	Evaluation: basic summary and calibration snapshot
	•	Product Layer: branding + grant framing

[STATUS]
	•	partial

[SCORING]
	•	Completeness: 3.5/5
	•	Execution: 4.0/5
	•	Novelty: 2.5/5
	•	Monetization: 2.5/5
	•	Readiness: 2.0/5

[VALUE]
	•	Extractable: $20,000–$45,000
	•	Realistic: $12,000–$28,000
	•	Productized: $35,000–$90,000

[OVERLAP]
	•	No prior Aegis-specific asset in this snapshot
	•	Internal overlap exists between grant framing and prototype wrapper, but not enough to discount materially

[NET NEW VALUE]
	•	$12,000–$28,000

[DEPENDENCIES]
	•	Clinical policy design
	•	Domain validation data
	•	Human reviewer workflow
	•	Security/compliance layer
	•	Deployment/API surface
	•	Evaluation dataset and benchmark process

[BLOCKERS]
	•	No real-world validation
	•	No model training or calibrated supervised classifier
	•	No authentication, authorization, encryption, or tenant boundaries
	•	No web app, queueing, API, observability stack, or deployment infra
	•	No clinical governance layer
	•	No integration with actual hotline/call-center systems
	•	High regulatory and operational burden if pushed beyond research use

⸻

PORTFOLIO TOTAL
	•	Gross Value: $12,000–$28,000
	•	Net Realistic Value: $12,000–$28,000
	•	Productized Value: $35,000–$90,000

⸻

VALUE CHANGES
	•	Added: $12,000–$28,000

	•	Deducted: $0
= Net: $12,000–$28,000

⸻

TOP VALUE DRIVERS
	•	A-001 → It is not just concept text. It actually executes, stores records, logs outputs, and supports repeatable demo/batch workflows.
	•	A-001 → Deterministic scoring and auditability make it easier to pitch as a research/pilot prototype than an opaque model demo.
	•	A-001 → Packaging is better than average: branding, CLI, persistence, summaries, and concept framing are already combined.

⸻

VALUE LEAKS
	•	no production integration layer
	•	no security/compliance controls
	•	no clinical validation
	•	no customer workflow integration
	•	no actual trained model advantage
	•	no revenue proof
	•	single-file architecture helps demo speed but caps enterprise credibility

⸻

SYSTEM STRUCTURE

Core assets
	•	A-001 Aegis Triage core engine
	•	feature extraction
	•	urgency model
	•	routing engine
	•	persistence
	•	audit
	•	reporting
	•	CLI

Supporting assets
	•	NIH SBIR concept framing embedded in file
	•	demo case corpus
	•	policy object and thresholds

Orphaned assets
	•	none inside this snapshot, but the commercialization story is not backed by deployment, pilots, or data assets

⸻

HARD TRUTH

What actually has value:
	•	The executable prototype.
	•	The deterministic scoring/routing structure.
	•	The persistence and audit trail.
	•	The fact that it is already framed as a pilot/research system rather than a toy sentiment script.

What is noise:
	•	The NIH/SBIR language by itself.
	•	Commercialization bullets without distribution, validation, or buyers.
	•	Any implication that this is clinically deployable.

What must be fixed to unlock next tier:
	•	Add an API/service layer.
	•	Add role-based access, encryption, and serious security controls.
	•	Add evaluation against a labeled dataset.
	•	Add policy versioning and reproducible benchmark reports.
	•	Add a reviewer dashboard or operational interface.
	•	Add integration points for real intake channels.
	•	Add governance language and validation workflow with clinical reviewers.

Bottom line:
This is a credible research prototype with packaging discipline, not a product company and not a production crisis platform. Today it is worth prototype money. With validation, interface, security, and deployment work, it can move into low-six-figure pilot territory. Without that, it stays a polished internal demo. [MASTER SUMMARY]

• What is being built:
A single-file crisis triage research prototype for intake, rule-based signal extraction, urgency scoring, routing recommendations, audit logging, and retrospective review.

• What actually works:
CLI intake, deterministic regex-based feature extraction, weighted urgency scoring, routing logic, SQLite storage, JSONL audit logging, record export, demo mode, batch mode, interactive mode, summary reporting, calibration snapshot, policy object.

• What is unproven:
Clinical validity, real-world safety, benchmark quality, hotline workflow fit, procurement fit, deployment readiness, API/service operation, security controls, supervised model improvement, customer demand.

• What has real value:
Executable prototype, deterministic scoring pipeline, persistence layer, audit trail, reproducible demo workflow, pilot-ready concept packaging, reusable single-file decision-support architecture.

• What is noise:
SBIR/NIH framing by itself, commercialization claims without pilots, any suggestion of production clinical readiness, grant language that is not backed by validation, inflated product-company framing.

⸻

[COMPRESSED TRUTH — MAX 60 WORDS]

Aegis Triage is a working local prototype for crisis-message intake, explainable urgency scoring, routing, storage, and audit. Its value is the executable decision-support workflow, not the grant language. It is not clinically validated, secure, integrated, or production-ready. Today it is prototype infrastructure with pilot packaging, not a deployable crisis platform.

⸻

[GRANDMOTHER EXPLANATION — MAX 50 WORDS]

It reads crisis-related messages, scores how urgent they look, suggests where they should go, and saves everything for later review. It helps staff work more consistently. It does not replace trained people, and it is not ready for real clinical use without more testing and safety work.

⸻

[DOLLAR VIEW]

• Current realistic sale value: $8,000–$18,000
• If cleaned and deduplicated: $15,000–$30,000
• If proven with real usage: $60,000–$150,000

⸻

[PRODUCT SNAPSHOT]

• Product name: Aegis Triage
• One-line hook: Explainable crisis triage workflow prototype with audit trails
• What it does (brutal): Scores text-based crisis signals, recommends routing, stores every case, and produces reviewable records
• Who it’s for: Research teams, pilot programs, public-sector innovation groups, healthcare operations teams
• Why it’s different: Deterministic logic, full auditability, local deployability, single-file prototype packaging

⸻

[SALES PAGE — MINIMAL]

Headline:
Explainable Crisis Triage Prototype for Research and Pilot Workflows

Subheadline:
A deterministic intake, scoring, routing, and audit system for teams exploring crisis-support decision tools.

What you get:
• Single-file working prototype with CLI, storage, scoring, and routing
• SQLite case history and JSONL audit trail
• Demo, batch, export, summary, and calibration utilities

Proof (real only):
• Functional Python engine
• Persistent case storage
• Deterministic scoring and route assignment
• Repeatable demo and batch workflows

⸻

[PRICING STRATEGY]

• Anchor price: $24,000
• Realistic sell price: $9,500–$15,000
• Quick-sale price: $4,500–$7,500

⸻

[ASSET BREAKDOWN]

• Core file / system: aegis_triage.py
• Reusable modules: signal analyzer, urgency model, routing engine, SQLite store, audit logger, reporting loop, CLI shell, policy object
• Hidden value: explainable decision trail, pilot/demo readiness, reusable architecture for regulated workflow tooling, not just crisis use

⸻

[DELIVERABLES]

README.md

Title
Aegis Triage

One-line description
Deterministic crisis signal triage prototype with routing, storage, audit logging, and review reporting.

What it does
Processes text input, extracts rule-based risk signals, estimates urgency, recommends routing, [MASTER SUMMARY]

• What is being built:
A single-file crisis triage research prototype for intake, rule-based signal extraction, urgency scoring, routing recommendations, audit logging, and retrospective review.

• What actually works:
CLI intake, deterministic regex-based feature extraction, weighted urgency scoring, routing logic, SQLite storage, JSONL audit logging, record export, demo mode, batch mode, interactive mode, summary reporting, calibration snapshot, policy object.

• What is unproven:
Clinical validity, real-world safety, benchmark quality, hotline workflow fit, procurement fit, deployment readiness, API/service operation, security controls, supervised model improvement, customer demand.

• What has real value:
Executable prototype, deterministic scoring pipeline, persistence layer, audit trail, reproducible demo workflow, pilot-ready concept packaging, reusable single-file decision-support architecture.

• What is noise:
SBIR/NIH framing by itself, commercialization claims without pilots, any suggestion of production clinical readiness, grant language not backed by validation, inflated product-company framing.

⸻

[COMPRESSED TRUTH — MAX 60 WORDS]

Aegis Triage is a working local prototype for crisis-message intake, explainable urgency scoring, routing, storage, and audit. Its value is the executable decision-support workflow, not the grant framing. It is not clinically validated, secure, integrated, or production-ready. Today it is prototype infrastructure with pilot packaging, not a deployable crisis platform.

⸻

[GRANDMOTHER EXPLANATION — MAX 50 WORDS]

It reads crisis-related messages, estimates how urgent they seem, suggests where they should go, and saves everything for later review. It helps staff work more consistently. It does not replace trained people, and it is not ready for real clinical use without more testing and safety work.

⸻

[DOLLAR VIEW]

• Current realistic sale value:
$8,000–$18,000

• If cleaned and deduplicated:
$15,000–$30,000

• If proven with real usage:
$60,000–$150,000

⸻

[PRODUCT SNAPSHOT]

• Product name:
Aegis Triage

• One-line hook:
Explainable crisis triage workflow prototype with audit trails

• What it does (brutal):
Scores text-based crisis signals, recommends routing, stores every case, and produces reviewable records

• Who it’s for:
Research teams, pilot programs, public-sector innovation groups, healthcare operations teams

• Why it’s different:
Deterministic logic, full auditability, local deployability, single-file prototype packaging

⸻

[SALES PAGE — MINIMAL]

Headline:
Explainable Crisis Triage Prototype for Research and Pilot Workflows

Subheadline:
A deterministic intake, scoring, routing, and audit system for teams exploring crisis-support decision tools.

What you get:
• Single-file working prototype with CLI, storage, scoring, and routing
• SQLite case history and JSONL audit trail
• Demo, batch, export, summary, and calibration utilities

Proof (real only):
• Functional Python engine
• Persistent case storage
• Deterministic scoring and route assignment
• Repeatable demo and batch workflows

⸻

[PRICING STRATEGY]

• Anchor price:
$24,000

• Realistic sell price:
$9,500–$15,000

• Quick-sale price:
$4,500–$7,500

⸻

[ASSET BREAKDOWN]

• Core file / system:
aegis_triage.py

• Reusable modules:
signal analyzer, urgency model, routing engine, SQLite store, audit logger, reporting loop, CLI shell, policy object

• Hidden value:
Explainable decision trail, pilot/demo readiness, reusable architecture for regulated workflow tooling beyond crisis use

⸻

[DELIVERABLES]

README.md

Title
Aegis Triage

One-line description
Deterministic crisis signal triage prototype with routing, storage, audit logging, and review reporting.

What it does
Processes text input, extracts rule-based risk signals, estimates urgency, recommends routing, stores results, and supports later review and summary analysis.

How it works
• Ingests text cases from demo, interactive, or batch input
• Extracts crisis-related features with deterministic rules
• Scores urgency and confidence using weighted logic
• Produces routing recommendations with safety floors
• Stores all records in SQLite and JSONL for audit and review

Quick start

#### ChatGPT:
Your valuation is directionally reasonable, but it is a bit **optimistic on current-state sale value** and a bit **loose on overlap between concept framing and executable substance**.

My tighter appraisal:

\==============================
\[MASTER LEDGER SNAPSHOT]
=========================

\[A-001]
Name: Aegis Triage\
Type: AI / Agent System\
Status: functional prototype\
Origin Chat: Chat 001\
Updated In: Chat 001\
Files / Sources: aegis\_triage.py\
Description: Single-file deterministic crisis triage prototype with regex-based signal extraction, urgency scoring, routing logic, SQLite persistence, JSONL audit logging, CLI demo/batch/interactive flows, and embedded SBIR-style concept framing.\
Overlap: none externally; internal packaging overlap between grant framing and prototype narrative\
Value:

- Extractable Value: $12,000–$30,000
- Realistic Buyer Value: $6,000–$16,000
- Productized Value: $30,000–$85,000
- Net New Value: $6,000–$16,000
- Confidence: medium

Real:

- Working single-file executable
- Deterministic feature extraction
- Weighted urgency model
- Policy/routing layer
- SQLite storage
- JSONL audit trail
- Demo, batch, interactive, summary, export flows
- Reasonably coherent architecture for a one-file prototype

Partial:

- Calibration reporting is basic
- Policy system exists but is shallow
- Review loop is minimal
- Presentation/concept layer helps packaging but does not materially improve core defensibility
- Reusable for pilot demos, internal research, or grant packaging

Fake / Decorative:

- “AI / Agent System” is overstated; this is mostly deterministic rules, not a meaningful agent system
- NIH/SBIR framing does not itself add much buyer value
- Commercialization language is not backed by users, pilots, integrations, or validation
- “Human-guided crisis intelligence platform” is packaging language, not current product reality

Blockers:

- No clinical validation
- No labeled dataset evaluation
- No sensitivity/specificity benchmarking
- No API or service layer
- No auth, roles, encryption, or access controls
- No compliance posture
- No external integrations
- No reviewer dashboard
- No deployment/ops story
- High liability domain

---

## \[ASSET INDEX MAP]

- Chat 001 → A-001

---

## \[PORTFOLIO TOTAL]

- Gross Standalone Value: $6,000–$16,000
- Overlap Discount: $0
- Net Realistic Portfolio Value: $6,000–$16,000
- Productized Portfolio Value: $30,000–$85,000

---

## \[VALUE CHANGES FROM LAST STATE]

- Added Gross Value: $6,000–$16,000
- Removed by Overlap: $0
- Net Portfolio Change: +$6,000–$16,000

---

## \[TOP VALUE DRIVERS]

1. It actually runs end to end.
2. It has persistence, auditability, and repeatable demo flows.
3. It is packaged coherently enough to support a pilot, grant, or internal tooling conversation.

---

## \[VALUE LEAKS]

- Regulated/high-liability domain without validation
- Rule-based logic with limited defensibility
- No workflow integration
- No security or compliance controls
- “AI” branding stronger than actual technical sophistication

---

## \[HARD TRUTH]

- This is a solid prototype, not a company, not a moat, and not a deployable clinical system.
- The real value is in the working workflow shell and auditability, not the crisis-scoring logic alone.
- The domain raises the bar so much that lack of validation suppresses value sharply.

A few surgical corrections to your prior appraisal:

**1. “AI / Agent System” is too generous.**\
This is better classified as:

- Script / Automation
- Decision-support prototype
- Research workflow system

There is no meaningful autonomous agent behavior, model orchestration, or learned intelligence here.

**2. Your current realistic value band is a little high.**\
I would not put it at $12k–$28k as the base case unless there is:

- a buyer already in this domain,
- a grant narrative attached,
- or it comes bundled with documentation/demo assets.

For plain code alone, **$6k–$16k** feels more grounded.

**3. Productized upside is plausible, but only with evidence.**\
Your **$35k–$90k** productized number is not crazy, but it requires:

- evaluation against real labeled cases,
- a web dashboard,
- basic role/security controls,
- versioned policy configs,
- reporting artifacts,
- a pilot-ready deployment surface.

**4. The best asset here is not the scoring logic.**\
The strongest part is the **coherent prototype stack**:

- intake
- deterministic analysis
- routing
- storage
- audit
- reporting
- operator-facing CLI flows

That bundle is what gives it saleability.

**5. The liability domain hurts value.**\
In ordinary ops tooling, a prototype like this could sometimes sell better. In crisis/clinical-adjacent workflows, unvalidated logic is much more dangerous, so buyers discount harder.

My clean dollar view:

- **Code as-is:** **$6,000–$16,000**
- **With README, tests, packaging, and cleaned framing:** **$10,000–$22,000**
- **With dashboard, API, security basics, and evaluation layer:** **$30,000–$85,000**
- **With real pilot evidence:** **$75,000–$200,000+** depending on buyer context

And for the logs: I still cannot appraise “the logs” unless you paste actual log output. Logging infrastructure exists, but runtime evidence matters more than the presence of a logger.

Paste the actual logs and I’ll score:

- runtime quality
- failure signatures
- demo credibility
- whether the logs increase or decrease buyer value
