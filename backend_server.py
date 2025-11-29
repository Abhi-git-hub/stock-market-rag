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

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize
print("🚀 Initializing Production RAG Backend...")
groq_client = Groq(api_key=os.getenv('groqapi'))
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Global storage
stock_data = []
embeddings_store = []

# EXPANDED STOCK UNIVERSE - 50+ Major Indian Stocks
# Nifty 50 companies + High volume stocks across sectors
STOCKS = [
    # Banking & Financial Services (10)
    'HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN',
    'BAJFINANCE', 'BAJAJFINSV', 'HDFCLIFE', 'SBILIFE', 'ICICIGI',

    # IT & Technology (8)
    'TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM',
    'LTIM', 'PERSISTENT', 'COFORGE',

    # Energy & Oil/Gas (5)
    'RELIANCE', 'ONGC', 'POWERGRID', 'NTPC', 'COALINDIA',

    # FMCG & Consumer (7)
    'HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR',
    'MARICO', 'GODREJCP',

    # Auto & Auto Components (6)
    'MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'EICHERMOT', 'HEROMOTOCO',

    # Pharma & Healthcare (5)
    'SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'APOLLOHOSP',

    # Telecom (2)
    'BHARTIARTL', 'INDUSINDBK',

    # Metals & Mining (4)
    'TATASTEEL', 'HINDALCO', 'JSWSTEEL', 'VEDL',

    # Infrastructure & Construction (5)
    'LT', 'ULTRACEMCO', 'GRASIM', 'ADANIPORTS', 'ADANIENT',

    # Others - High Cap/Volume (8)
    'ASIANPAINT', 'TITAN', 'BPCL', 'HINDZINC', 'INDIGO',
    'TATACONSUM', 'PIDILITIND', 'SBICARD'
]

print(f"📊 Tracking {len(STOCKS)} stocks across multiple sectors")
print(f"🏢 Sectors: Banking, IT, Energy, FMCG, Auto, Pharma, Telecom, Metals, Infrastructure")

def fetch_stocks():
    """Background task: Fetch stock data every 60 seconds"""
    print(f"\n{'='*70}")
    print(f"🔄 Starting production stock stream...")
    print(f"{'='*70}\n")

    fetch_count = 0

    while True:
        fetch_count += 1
        start_time = time.time()
        successful = 0
        failed = 0

        print(f"\n[Fetch #{fetch_count}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        print("-" * 70)

        for symbol in STOCKS:
            try:
                ticker = yf.Ticker(f"{symbol}.BO")
                hist = ticker.history(period='1d')
                info = ticker.info

                if not hist.empty:
                    latest = hist.iloc[-1]
                    current_price = float(latest['Close'])
                    open_price = float(info.get('regularMarketOpen', latest['Open']))
                    change = current_price - open_price
                    change_percent = (change / open_price * 100) if open_price else 0

                    # Get additional info
                    market_cap = info.get('marketCap', 0)
                    pe_ratio = info.get('trailingPE', 'N/A')
                    sector = info.get('sector', 'Unknown')

                    # Rich context for RAG
                    text = f"""Stock: {symbol}
Sector: {sector}
Current Price: ₹{current_price:.2f}
Change: ₹{change:.2f} ({change_percent:+.2f}%)
Day Range: ₹{float(latest['Low']):.2f} - ₹{float(latest['High']):.2f}
Open: ₹{open_price:.2f}
Volume: {int(latest['Volume']):,}
Market Cap: ₹{market_cap:,.0f}
PE Ratio: {pe_ratio}
52 Week High: ₹{info.get('fiftyTwoWeekHigh', 0):.2f}
52 Week Low: ₹{info.get('fiftyTwoWeekLow', 0):.2f}
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"""

                    embedding = embedder.encode(text).tolist()

                    stock_entry = {
                        'symbol': symbol,
                        'sector': sector,
                        'price': current_price,
                        'change': change,
                        'change_percent': change_percent,
                        'open': open_price,
                        'high': float(latest['High']),
                        'low': float(latest['Low']),
                        'volume': int(latest['Volume']),
                        'market_cap': market_cap,
                        'pe_ratio': pe_ratio if isinstance(pe_ratio, (int, float)) else None,
                        'timestamp': datetime.now().isoformat(),
                        'text': text
                    }

                    stock_data.append(stock_entry)
                    embeddings_store.append(embedding)

                    # Keep last 2000 entries (enough for all stocks with history)
                    if len(stock_data) > 2000:
                        stock_data[:] = stock_data[-2000:]
                        embeddings_store[:] = embeddings_store[-2000:]

                    successful += 1
                    status = "📈" if change_percent > 0 else "📉" if change_percent < 0 else "➡️"
                    print(f"{status} {symbol:15} ₹{current_price:8.2f} ({change_percent:+6.2f}%) | Vol: {int(latest['Volume']):>12,}")

            except Exception as e:
                failed += 1
                print(f"❌ {symbol:15} Error: {str(e)[:50]}")

        elapsed = time.time() - start_time
        print("-" * 70)
        print(f"✅ Fetch complete: {successful} success, {failed} failed | Time: {elapsed:.1f}s")
        print(f"💾 Total data points: {len(stock_data)} | Embeddings: {len(embeddings_store)}")
        print(f"⏳ Next update in 60 seconds...\n")

        time.sleep(60)

# Start background thread
print("\n🔄 Starting background stock fetcher thread...")
thread = threading.Thread(target=fetch_stocks, daemon=True)
thread.start()
print("✅ Background thread started\n")

@app.route('/stocks', methods=['GET'])
def get_stocks():
    """Get latest stock data"""
    # Return last entry for each stock
    latest_stocks = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest_stocks:
            latest_stocks[s['symbol']] = s

    return jsonify({
        'stocks': list(latest_stocks.values()),
        'count': len(stock_data),
        'unique_stocks': len(latest_stocks)
    })

@app.route('/stocks/sector/<sector>', methods=['GET'])
def get_stocks_by_sector(sector):
    """Get stocks filtered by sector"""
    sector_stocks = [s for s in stock_data if s.get('sector', '').lower() == sector.lower()]
    return jsonify({
        'sector': sector,
        'stocks': sector_stocks[-50:],
        'count': len(sector_stocks)
    })

@app.route('/stocks/top-gainers', methods=['GET'])
def top_gainers():
    """Get top gaining stocks"""
    latest_stocks = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest_stocks:
            latest_stocks[s['symbol']] = s

    sorted_stocks = sorted(latest_stocks.values(), key=lambda x: x['change_percent'], reverse=True)
    return jsonify({
        'gainers': sorted_stocks[:10],
        'count': len(sorted_stocks)
    })

@app.route('/stocks/top-losers', methods=['GET'])
def top_losers():
    """Get top losing stocks"""
    latest_stocks = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest_stocks:
            latest_stocks[s['symbol']] = s

    sorted_stocks = sorted(latest_stocks.values(), key=lambda x: x['change_percent'])
    return jsonify({
        'losers': sorted_stocks[:10],
        'count': len(sorted_stocks)
    })

@app.route('/stocks/most-active', methods=['GET'])
def most_active():
    """Get most actively traded stocks by volume"""
    latest_stocks = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest_stocks:
            latest_stocks[s['symbol']] = s

    sorted_stocks = sorted(latest_stocks.values(), key=lambda x: x['volume'], reverse=True)
    return jsonify({
        'most_active': sorted_stocks[:10],
        'count': len(sorted_stocks)
    })

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
    """AI-powered RAG query endpoint"""
    question = request.json.get('question', '')

    if not stock_data:
        return jsonify({
            'answer': '⏳ No stock data available yet. Please wait for data stream to initialize (takes ~60 seconds).',
            'sources': [],
            'timestamp': datetime.now().isoformat()
        })

    # Search similar documents using vector similarity
    query_emb = embedder.encode(question)
    similarities = [
        np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
        for emb in embeddings_store
    ]

    # Get top 10 most relevant stocks (more context for better answers)
    top_10_idx = np.argsort(similarities)[-10:][::-1]
    context = "\n\n".join([stock_data[i]['text'] for i in top_10_idx])
    sources = list(set([stock_data[i]['symbol'] for i in top_10_idx]))

    try:
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert Indian stock market analyst with access to real-time NSE/BSE data covering {len(STOCKS)} major stocks across all sectors.

Provide specific, data-driven insights with:
- Exact prices and percentages from the data
- Sector-wise analysis when relevant
- Comparative analysis across stocks
- Risk considerations
- Market trends

Be concise but thorough. Use Indian Rupee (₹) for prices."""
                },
                {
                    "role": "user",
                    "content": f"""Real-time Stock Market Data (Top 10 Relevant):
{context}

Question: {question}

Provide detailed analysis based on the real-time data above."""
                }
            ],
            temperature=0.7,
            max_tokens=1024
        )

        return jsonify({
            'answer': response.choices[0].message.content,
            'sources': sources,
            'sources_count': len(sources),
            'timestamp': datetime.now().isoformat(),
            'model': 'mixtral-8x7b-32768',
            'total_stocks_analyzed': len(STOCKS)
        })

    except Exception as e:
        return jsonify({
            'answer': f'Groq API Error: {str(e)}. Check your API key in .env file.',
            'sources': [],
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Comprehensive health check"""
    latest_stocks = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest_stocks:
            latest_stocks[s['symbol']] = s

    return jsonify({
        'status': 'online',
        'stock_count': len(stock_data),
        'unique_stocks': len(latest_stocks),
        'total_stocks_tracked': len(STOCKS),
        'stocks_tracked': STOCKS,
        'data_coverage': f"{len(latest_stocks)}/{len(STOCKS)} stocks active",
        'embeddings_count': len(embeddings_store),
        'timestamp': datetime.now().isoformat(),
        'version': '2.0-production'
    })

@app.route('/sectors', methods=['GET'])
def get_sectors():
    """Get list of sectors with stock counts"""
    sectors = {}
    for s in stock_data:
        sector = s.get('sector', 'Unknown')
        if sector not in sectors:
            sectors[sector] = []
        if s['symbol'] not in [stock['symbol'] for stock in sectors[sector]]:
            sectors[sector].append({
                'symbol': s['symbol'],
                'price': s['price'],
                'change_percent': s['change_percent']
            })

    return jsonify({
        'sectors': {k: len(v) for k, v in sectors.items()},
        'details': sectors
    })

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Production Indian Stock Market RAG Backend")
    print("=" * 70)
    print(f"✅ Server starting on http://localhost:8080")
    print(f"📊 Tracking {len(STOCKS)} stocks across multiple sectors")
    print(f"🏢 Sectors: Banking, IT, Energy, FMCG, Auto, Pharma, Telecom, Metals")
    print(f"⏳ First data will arrive in ~60 seconds")
    print(f"💾 Enhanced RAG with top-10 context retrieval")
    print("=" * 70)
    print("")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
