from flask import Flask, jsonify, request
from flask_cors import CORS
from groq import Groq
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv
import threading
import time
import random

load_dotenv()

app = Flask(__name__)
CORS(app)

print("🚀 Initializing Backend with Groq Failover...")

# Initialize Groq with proper error handling
groq_client = None
groq_available = False

try:
    api_key = os.getenv('groqapi')
    if not api_key:
        print("⚠️  GROQ API KEY NOT SET - Using offline analysis mode")
        print("    Set groqapi environment variable to enable Groq")
        groq_available = False
    else:
        groq_client = Groq(api_key=api_key)
        # Test connection
        try:
            test = groq_client.models.list()
            groq_available = True
            print("✅ Groq API Connected Successfully")
        except Exception as e:
            print(f"⚠️  Groq connection test failed: {str(e)}")
            groq_available = False
except Exception as e:
    print(f"⚠️  Groq initialization failed: {str(e)}")
    groq_available = False

# Initialize Embedder
embedder = None
try:
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Embedder loaded successfully")
except Exception as e:
    print(f"⚠️  Embedder error: {str(e)}")
    embedder = None

# Global storage
stock_data = []
embeddings_store = []

# Indian stocks
STOCKS = {
    'HDFCBANK.NS': 'HDFC Bank',
    'ICICIBANK.NS': 'ICICI Bank',
    'KOTAKBANK.NS': 'Kotak Bank',
    'AXISBANK.NS': 'Axis Bank',
    'SBIN.NS': 'State Bank of India',
    'BAJFINANCE.NS': 'Bajaj Finance',
    'BAJAJFINSV.NS': 'Bajaj Financial Services',
    'HDFCLIFE.NS': 'HDFC Life Insurance',
    'SBILIFE.NS': 'SBI Life Insurance',
    'ICICIGI.NS': 'ICICI General Insurance',
    'TCS.NS': 'Tata Consultancy Services',
    'INFY.NS': 'Infosys Limited',
    'WIPRO.NS': 'Wipro Limited',
    'HCLTECH.NS': 'HCL Technologies',
    'TECHM.NS': 'Tech Mahindra',
    'LTIM.NS': 'LT Infotech',
    'PERSISTENT.NS': 'Persistent Systems',
    'COFORGE.NS': 'Coforge',
    'RELIANCE.NS': 'Reliance Industries',
    'ONGC.NS': 'Oil and Natural Gas Corporation',
    'POWERGRID.NS': 'Power Grid Corporation',
    'NTPC.NS': 'NTPC Limited',
    'COALINDIA.NS': 'Coal India Limited',
    'HINDUNILVR.NS': 'Hindustan Unilever',
    'ITC.NS': 'ITC Limited',
    'NESTLEIND.NS': 'Nestlé India',
    'BRITANNIA.NS': 'Britannia Industries',
    'DABUR.NS': 'Dabur India',
    'MARICO.NS': 'Marico',
    'GODREJCP.NS': 'Godrej Consumer Products',
    'MARUTI.NS': 'Maruti Suzuki India',
    'TATAMOTORS.NS': 'Tata Motors',
    'M&M.NS': 'Mahindra & Mahindra',
    'BAJAJ-AUTO.NS': 'Bajaj Auto',
    'EICHERMOT.NS': 'Eicher Motors',
    'HEROMOTOCO.NS': 'Hero MotoCorp',
    'SUNPHARMA.NS': 'Sun Pharmaceutical',
    'DRREDDY.NS': 'Dr. Reddy\'s Laboratories',
    'CIPLA.NS': 'Cipla',
    'DIVISLAB.NS': 'Divi\'s Laboratories',
    'APOLLOHOSP.NS': 'Apollo Hospitals',
    'ASIANPAINT.NS': 'Asian Paints',
    'TITAN.NS': 'Titan Company',
    'BHARTIARTL.NS': 'Bharti Airtel',
    'INDIGO.NS': 'IndiGo',
    'LT.NS': 'Larsen & Toubro',
}

FALLBACK_PRICES = {
    'HDFCBANK.NS': 1685.50, 'ICICIBANK.NS': 892.45, 'KOTAKBANK.NS': 1745.60,
    'AXISBANK.NS': 936.80, 'SBIN.NS': 674.35, 'BAJFINANCE.NS': 6547.00,
    'BAJAJFINSV.NS': 1850.00, 'HDFCLIFE.NS': 682.50, 'SBILIFE.NS': 2180.00,
    'ICICIGI.NS': 1840.00, 'TCS.NS': 3945.75, 'INFY.NS': 1658.90,
    'WIPRO.NS': 445.30, 'HCLTECH.NS': 1785.50, 'TECHM.NS': 1310.20,
    'LTIM.NS': 4890.00, 'PERSISTENT.NS': 4895.50, 'COFORGE.NS': 9350.00,
    'RELIANCE.NS': 1287.65, 'ONGC.NS': 318.50, 'POWERGRID.NS': 298.90,
    'NTPC.NS': 398.30, 'COALINDIA.NS': 878.50, 'HINDUNILVR.NS': 2456.75,
    'ITC.NS': 445.25, 'NESTLEIND.NS': 2385.50, 'BRITANNIA.NS': 4785.00,
    'DABUR.NS': 648.50, 'MARICO.NS': 698.30, 'GODREJCP.NS': 1245.50,
    'MARUTI.NS': 12840.00, 'TATAMOTORS.NS': 895.50, 'M&M.NS': 2985.75,
    'BAJAJ-AUTO.NS': 8945.00, 'EICHERMOT.NS': 3850.50, 'HEROMOTOCO.NS': 6875.00,
    'SUNPHARMA.NS': 728.50, 'DRREDDY.NS': 2385.50, 'CIPLA.NS': 1485.50,
    'DIVISLAB.NS': 6285.00, 'APOLLOHOSP.NS': 8945.00, 'ASIANPAINT.NS': 3256.50,
    'TITAN.NS': 3248.50, 'BHARTIARTL.NS': 1485.50, 'INDIGO.NS': 3985.50,
    'LT.NS': 3648.50,
}

print(f"📊 Tracking {len(STOCKS)} stocks")

def fetch_stocks_smart():
    """Fetch stocks with smart fallback"""
    print(f"\n{'='*70}")
    print("🔄 Starting Smart Stock Fetcher")
    print(f"{'='*70}\n")

    import yfinance as yf
    fetch_count = 0
    rate_limited = False

    while True:
        fetch_count += 1
        successful = 0
        fallback = 0

        print(f"[Fetch #{fetch_count}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")

        for idx, (symbol, name) in enumerate(list(STOCKS.items())):
            try:
                if idx > 0:
                    time.sleep(random.uniform(0.5, 1.5))

                if not rate_limited:
                    try:
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(period='1d', progress=False, timeout=5)

                        if hist.empty or len(hist) == 0:
                            raise Exception("Empty data")

                        latest = hist.iloc[-1]
                        current_price = float(latest['Close'])
                        prev_close = float(hist.iloc[-2]['Close']) if len(hist) > 1 else current_price
                        change = current_price - prev_close
                        change_percent = (change / prev_close * 100) if prev_close else 0

                        stock_entry = {
                            'symbol': symbol.replace('.NS', ''),
                            'name': name,
                            'price': round(current_price, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2),
                            'high': round(float(latest['High']), 2),
                            'low': round(float(latest['Low']), 2),
                            'volume': int(latest['Volume']),
                            'timestamp': datetime.now().isoformat(),
                            'text': f"{symbol} {name} at ₹{current_price:.2f} ({change_percent:+.2f}%)",
                            'source': 'yfinance'
                        }

                        stock_data.append(stock_entry)
                        if embedder:
                            try:
                                emb = embedder.encode(stock_entry['text']).tolist()
                                embeddings_store.append(emb)
                            except:
                                pass

                        successful += 1
                        print(f"✓ {symbol:15} | ₹{current_price:8.2f} | {change_percent:+6.2f}% [yfinance]")
                        continue

                    except Exception as e:
                        if "429" in str(e):
                            rate_limited = True
                        pass

                # Fallback
                base_price = FALLBACK_PRICES.get(symbol, 1000)
                daily_change_percent = random.uniform(-3, 3)
                current_price = base_price * (1 + daily_change_percent / 100)

                stock_entry = {
                    'symbol': symbol.replace('.NS', ''),
                    'name': name,
                    'price': round(current_price, 2),
                    'change': round(current_price - base_price, 2),
                    'change_percent': round(daily_change_percent, 2),
                    'high': round(current_price * random.uniform(1.005, 1.015), 2),
                    'low': round(current_price * random.uniform(0.985, 0.995), 2),
                    'volume': random.randint(1000000, 50000000),
                    'timestamp': datetime.now().isoformat(),
                    'text': f"{symbol} {name} at ₹{current_price:.2f} ({daily_change_percent:+.2f}%)",
                    'source': 'fallback'
                }

                stock_data.append(stock_entry)
                if embedder:
                    try:
                        emb = embedder.encode(stock_entry['text']).tolist()
                        embeddings_store.append(emb)
                    except:
                        pass

                fallback += 1
                print(f"⚠ {symbol:15} | ₹{current_price:8.2f} | {daily_change_percent:+6.2f}% [fallback]")

            except Exception as e:
                print(f"❌ {symbol:15} | Error: {str(e)[:30]}")

        if len(stock_data) > 500:
            stock_data[:] = stock_data[-500:]
            embeddings_store[:] = embeddings_store[-500:]

        print(f"✅ {successful} yfinance, {fallback} fallback\n")
        time.sleep(60)

thread = threading.Thread(target=fetch_stocks_smart, daemon=True)
thread.start()

# ============================================================================
# OFFLINE ANALYSIS (When Groq fails)
# ============================================================================

def offline_analysis(question: str, context: str) -> str:
    """
    Fallback analysis when Groq is unavailable
    Provides template-based responses
    """
    question_lower = question.lower()

    # Analyze context
    lines = context.split('\n')
    prices = []
    for line in lines:
        if 'at ₹' in line:
            try:
                price_str = line.split('₹')[1].split(' ')[0]
                prices.append(float(price_str))
            except:
                pass

    # Template responses
    if any(word in question_lower for word in ['gain', 'up', 'increase']):
        avg_price = np.mean(prices) if prices else 0
        return f"""Based on the latest market data:

**Top Performers Today:**
- Multiple stocks showing positive movement
- Average price level: ₹{avg_price:.2f}
- Market sentiment: Mixed to positive

**Analysis:**
The stocks in focus are demonstrating varied performance. Those with positive changes are likely driven by sector-specific developments or market corrections from oversold levels.

**Recommendation:** Monitor volume and support levels for confirmation."""

    elif any(word in question_lower for word in ['lose', 'down', 'fall', 'decline']):
        return f"""Based on the latest market data:

**Market Overview:**
- Mixed performance across portfolio
- Some stocks showing correction
- Typical intraday volatility observed

**Analysis:**
Market corrections are a normal part of trading. Key factors to consider:
1. Check support levels
2. Volume analysis
3. Sector rotation patterns

**Note:** Consult financial advisors for trading decisions."""

    elif any(word in question_lower for word in ['best', 'high', 'top']):
        if prices:
            highest = max(prices)
            return f"""Based on the latest market data:

**Highest Valued Stock:**
Current price level: ₹{highest:.2f}

**Analysis:**
Premium-priced stocks often reflect:
- Strong fundamentals
- Consistent growth
- Market confidence

Monitor for any support level breaks or resistance breakthroughs."""

    else:
        return f"""Based on the latest market data provided:

The Indian stock market is showing typical intraday volatility with multiple stocks across sectors. 

**Key Observations:**
- Mixed sector performance
- Normal trading ranges observed
- Volume patterns intact

**Suggestion:** For AI-powered analysis, ensure Groq API is configured. Otherwise, refer to manual chart analysis tools."""

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    latest = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest:
            latest[s['symbol']] = s

    return jsonify({
        'status': 'online',
        'stocks': len(latest),
        'groq_available': groq_available,
        'groq_status': 'Connected' if groq_available else 'Using offline analysis',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/stocks', methods=['GET'])
def get_stocks():
    if not stock_data:
        return jsonify({'stocks': [], 'message': 'Initializing...'}), 200

    latest = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest:
            latest[s['symbol']] = s

    return jsonify({'stocks': list(latest.values())}), 200

@app.route('/stocks/top-gainers', methods=['GET'])
def top_gainers():
    if not stock_data:
        return jsonify({'gainers': []}), 200

    latest = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest:
            latest[s['symbol']] = s

    sorted_stocks = sorted(latest.values(), key=lambda x: x['change_percent'], reverse=True)
    return jsonify({'gainers': sorted_stocks[:5]}), 200

@app.route('/stocks/top-losers', methods=['GET'])
def top_losers():
    if not stock_data:
        return jsonify({'losers': []}), 200

    latest = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest:
            latest[s['symbol']] = s

    sorted_stocks = sorted(latest.values(), key=lambda x: x['change_percent'])
    return jsonify({'losers': sorted_stocks[:5]}), 200

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Get high volatility alerts (>3% change)"""
    alerts = []
    seen_symbols = set()

    for s in reversed(stock_data[-200:]):
        if s['symbol'] not in seen_symbols and abs(s['change_percent']) > 3.0:
            alerts.append({
                'symbol': s['symbol'],
                'sector': s.get('sector', 'Unknown'),
                'price': s['price'],
                'change_percent': s['change_percent'],
                'alert_type': 'SURGE 🚀' if s['change_percent'] > 0 else 'DROP 📉',
                'timestamp': s['timestamp'],
                'message': f"⚠️ {s['symbol']} moved {s['change_percent']:.2f}% - High volatility!"
            })
            seen_symbols.add(s['symbol'])

    return jsonify({
        'alerts': alerts[:20],
        'count': len(alerts)
    })

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Get comprehensive analytics"""
    if not stock_data:
        return jsonify({'analytics': [], 'message': 'No data yet'})

    analytics = []
    for symbol in STOCKS:
        symbol_data = [s for s in stock_data[-100:] if s['symbol'] == symbol]
        if symbol_data:
            prices = [s['price'] for s in symbol_data]
            analytics.append({
                'symbol': symbol,
                'sector': symbol_data[-1].get('sector', 'Unknown'),
                'current_price': symbol_data[-1]['price'],
                'avg_price': np.mean(prices),
                'max_price': max(prices),
                'min_price': min(prices),
                'price_swing': max(prices) - min(prices),
                'total_volume': sum(s['volume'] for s in symbol_data),
                'avg_change_percent': np.mean([s['change_percent'] for s in symbol_data])
            })

    return jsonify({
        'analytics': analytics,
        'summary': {
            'total_stocks': len(analytics),
            'avg_market_change': np.mean([a['avg_change_percent'] for a in analytics])
        }
    })

@app.route('/query', methods=['POST'])
def query():
    """Query endpoint with Groq failover to offline analysis"""
    question = request.json.get('question', '')

    if not stock_data:
        return jsonify({
            'answer': 'Loading data...',
            'sources': [],
            'mode': 'initializing'
        }), 200

    try:
        # Build context
        if embedder and embeddings_store:
            query_emb = embedder.encode(question)
            similarities = [
                np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb) + 1e-10)
                for emb in embeddings_store
            ]
            top_10_idx = np.argsort(similarities)[-10:][::-1]
            context = "\n\n".join([stock_data[i]['text'] for i in top_10_idx if i < len(stock_data)])
            sources = [stock_data[i]['symbol'] for i in top_10_idx if i < len(stock_data)]
        else:
            context = "\n\n".join([s['text'] for s in stock_data[-10:]])
            sources = [s['symbol'] for s in stock_data[-10:]]

        # Try Groq first
        if groq_available and groq_client:
            try:
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an Indian stock market expert. Provide brief analysis based on the data."
                        },
                        {
                            "role": "user",
                            "content": f"Stock Data:\n{context}\n\nQuestion: {question}"
                        }
                    ],
                    temperature=0.7,
                    max_tokens=256,
                    timeout=10
                )

                return jsonify({
                    'answer': response.choices[0].message.content,
                    'sources': sources,
                    'mode': 'groq_ai'
                }), 200

            except Exception as e:
                print(f"⚠️  Groq API error: {str(e)}")
                # Fall through to offline analysis
                pass

        # Fallback to offline analysis
        answer = offline_analysis(question, context)
        return jsonify({
            'answer': answer,
            'sources': sources,
            'mode': 'offline_analysis',
            'note': 'Groq API unavailable - using template-based analysis'
        }), 200

    except Exception as e:
        print(f"❌ Query Error: {str(e)}")
        return jsonify({
            'answer': f'Error processing query: {str(e)[:100]}',
            'error': str(e),
            'mode': 'error'
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    print("=" * 70)
    print("🚀 Groq-Safe Stock Market Backend")
    print("=" * 70)
    print(f"✅ Server on 0.0.0.0:{port}")
    print(f"🤖 Groq Status: {'Connected ✅' if groq_available else 'Offline - Using fallback ⚠️'}")
    print(f"📊 Data Source: Smart yfinance + fallback")
    print(f"⏳ First data in ~60 seconds")
    print("=" * 70)
    print()
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
