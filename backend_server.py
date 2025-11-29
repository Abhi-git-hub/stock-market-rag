# backend_server.py (replace your existing file with this)
from flask import Flask, jsonify, request
from flask_cors import CORS
from groq import Groq
from sentence_transformers import SentenceTransformer
import yfinance as yf
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv
import threading
import time
import math

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize
print("🚀 Initializing Production RAG Backend...")
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY') or os.getenv('groqapi'))
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Global storage
stock_data = []
embeddings_store = []

# Keep the list you had (STOCKS)
STOCKS = [
    'HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN',
    'BAJFINANCE', 'BAJAJFINSV', 'HDFCLIFE', 'SBILIFE', 'ICICIGI',
    'TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM',
    'LTIM', 'PERSISTENT', 'COFORGE',
    'RELIANCE', 'ONGC', 'POWERGRID', 'NTPC', 'COALINDIA',
    'HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR',
    'MARICO', 'GODREJCP', 'MARUTI', 'TATAMOTORS', 'M&M',
    'BAJAJ-AUTO', 'EICHERMOT', 'HEROMOTOCO', 'SUNPHARMA',
    'DRREDDY', 'CIPLA', 'DIVISLAB', 'APOLLOHOSP', 'BHARTIARTL',
    'INDUSINDBK', 'TATASTEEL', 'HINDALCO', 'JSWSTEEL', 'VEDL',
    'LT', 'ULTRACEMCO', 'GRASIM', 'ADANIPORTS', 'ADANIENT',
    'ASIANPAINT', 'TITAN', 'BPCL', 'HINDZINC', 'INDIGO',
    'TATACONSUM', 'PIDILITIND', 'SBICARD'
]

print(f"📊 Tracking {len(STOCKS)} stocks across multiple sectors")

def safe_fetch_symbol(symbol, max_attempts=3, base_sleep=0.6):
    """Fetch one symbol with retries and safe checks. Returns dict or None."""
    ticker_symbol = f"{symbol}.NS"
    for attempt in range(1, max_attempts + 1):
        try:
            ticker = yf.Ticker(ticker_symbol)
            # history can return empty; widen period to 5d as fallback
            hist = ticker.history(period='1d', timeout=10)
            if hist.empty:
                # try a slightly longer range as fallback
                hist = ticker.history(period='5d', timeout=10)
                if hist.empty:
                    raise ValueError("Empty history")

            latest = hist.iloc[-1]
            # safe access to info
            info = {}
            try:
                info = ticker.info or {}
            except Exception:
                info = {}

            current_price = float(latest.get('Close', math.nan))
            open_price = float(info.get('regularMarketOpen', latest.get('Open', current_price)))
            change = current_price - open_price
            change_percent = (change / open_price * 100) if open_price else 0

            market_cap = info.get('marketCap') or 0
            pe_ratio = info.get('trailingPE')
            sector = info.get('sector') or 'Unknown'

            return {
                'symbol': symbol,
                'sector': sector,
                'price': current_price,
                'change': change,
                'change_percent': change_percent,
                'open': open_price,
                'high': float(latest.get('High', current_price)),
                'low': float(latest.get('Low', current_price)),
                'volume': int(latest.get('Volume', 0)),
                'market_cap': market_cap,
                'pe_ratio': pe_ratio if isinstance(pe_ratio, (int, float)) else None,
                'timestamp': datetime.now().isoformat(),
                'text': None  # set by caller
            }

        except Exception as e:
            wait = base_sleep * (2 ** (attempt - 1))
            print(f"⚠️ [{symbol}] fetch attempt {attempt} failed: {e} — sleeping {wait:.2f}s before retry")
            time.sleep(wait)

    print(f"❌ [{symbol}] all {max_attempts} attempts failed. Skipping.")
    return None

def fetch_stocks():
    """Background task: Fetch stock data every UPDATE_INTERVAL seconds"""
    interval = int(os.getenv('UPDATE_INTERVAL', 60))
    print("\n🔄 Starting production stock stream...\n")
    fetch_count = 0
    consecutive_failures = 0

    while True:
        fetch_count += 1
        start_time = time.time()
        successful = 0
        failed = 0

        print(f"\n[Fetch #{fetch_count}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        print("-" * 70)

        for symbol in STOCKS:
            # small delay to avoid hitting Yahoo too fast
            time.sleep(0.5)
            result = safe_fetch_symbol(symbol)
            if not result:
                failed += 1
                continue

            # prepare rich text and embedding
            text = f"""Stock: {symbol}
Sector: {result['sector']}
Current Price: ₹{result['price']:.2f}
Change: ₹{result['change']:.2f} ({result['change_percent']:+.2f}%)
Day Range: ₹{result['low']:.2f} - ₹{result['high']:.2f}
Open: ₹{result['open']:.2f}
Volume: {result['volume']:,}
Market Cap: ₹{result['market_cap']:,}
PE Ratio: {result['pe_ratio']}
52 Week High: {result.get('fiftyTwoWeekHigh', 'N/A')}
52 Week Low: {result.get('fiftyTwoWeekLow', 'N/A')}
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"""

            result['text'] = text
            try:
                embedding = embedder.encode(text).tolist()
            except Exception as e:
                print(f"Embedding error for {symbol}: {e}")
                embedding = [0.0] * 384

            stock_data.append(result)
            embeddings_store.append(embedding)

            if len(stock_data) > 2000:
                stock_data[:] = stock_data[-2000:]
                embeddings_store[:] = embeddings_store[-2000:]

            successful += 1
            status = "📈" if result['change_percent'] > 0 else "📉" if result['change_percent'] < 0 else "➡️"
            print(f"{status} {symbol:15} ₹{result['price']:8.2f} ({result['change_percent']:+6.2f}%) | Vol: {result['volume']:>12,}")

        elapsed = time.time() - start_time
        print("-" * 70)
        print(f"✅ Fetch complete: {successful} success, {failed} failed | Time: {elapsed:.1f}s")
        print(f"💾 Total data points: {len(stock_data)} | Embeddings: {len(embeddings_store)}")
        print(f"⏳ Next update in {interval} seconds...\n")

        # if too many failures, back off longer (avoid hammering Yahoo)
        if failed > len(STOCKS) * 0.6:
            print("⚠️ High failure rate detected. Backing off for 30s to avoid rate-limits.")
            time.sleep(30)

        time.sleep(interval)

# Start background thread
print("\n🔄 Starting background stock fetcher thread...")
thread = threading.Thread(target=fetch_stocks, daemon=True)
thread.start()
print("✅ Background thread started\n")

# (rest of your endpoints remain the same — keep them, but they are identical to what you had,
#  or copy/paste your endpoints code here, unchanged, to preserve logic.)
# ... (keep your /stocks, /alerts, /query, /health, etc, with small changes if you want)
# For brevity, I assume you append your working endpoint implementations below.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=False, threaded=True)
