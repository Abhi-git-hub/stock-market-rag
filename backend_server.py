from flask import Flask, jsonify, request
from flask_cors import CORS
from groq import Groq
from sentence_transformers import SentenceTransformer
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
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

# INDIAN STOCKS - Using correct yfinance format (NSE symbols)
# These WILL work with yfinance
STOCKS = {
    # Banking & Financial Services (10)
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

    # IT & Technology (8)
    'TCS.NS': 'Tata Consultancy Services',
    'INFY.NS': 'Infosys Limited',
    'WIPRO.NS': 'Wipro Limited',
    'HCLTECH.NS': 'HCL Technologies',
    'TECHM.NS': 'Tech Mahindra',
    'LTIM.NS': 'LTIMindtree',
    'PERSISTENT.NS': 'Persistent Systems',
    'COFORGE.NS': 'Coforge',

    # Energy & Oil/Gas (5)
    'RELIANCE.NS': 'Reliance Industries',
    'ONGC.NS': 'Oil and Natural Gas Corporation',
    'POWERGRID.NS': 'Power Grid Corporation',
    'NTPC.NS': 'NTPC Limited',
    'COALINDIA.NS': 'Coal India Limited',

    # FMCG & Consumer (7)
    'HINDUNILVR.NS': 'Hindustan Unilever',
    'ITC.NS': 'ITC Limited',
    'NESTLEIND.NS': 'Nestlé India',
    'BRITANNIA.NS': 'Britannia Industries',
    'DABUR.NS': 'Dabur India',
    'MARICO.NS': 'Marico Limited',
    'GODREJCP.NS': 'Godrej Consumer Products',

    # Auto & Auto Components (6)
    'MARUTI.NS': 'Maruti Suzuki India',
    'TATAMOTORS.NS': 'Tata Motors Limited',
    'M&M.NS': 'Mahindra & Mahindra',
    'BAJAJ-AUTO.NS': 'Bajaj Auto Limited',
    'EICHERMOT.NS': 'Eicher Motors',
    'HEROMOTOCO.NS': 'Hero MotoCorp',

    # Pharma & Healthcare (5)
    'SUNPHARMA.NS': 'Sun Pharmaceutical',
    'DRREDDY.NS': 'Dr. Reddy's Laboratories',
    'CIPLA.NS': 'Cipla Limited',
    'DIVISLAB.NS': 'Divi's Laboratories',
    'APOLLOHOSP.NS': 'Apollo Hospitals',

    # Telecom (2)
    'BHARTIARTL.NS': 'Bharti Airtel Limited',
    'INDUSINDBK.NS': 'IndusInd Bank',

    # Metals & Mining (4)
    'TATASTEEL.NS': 'Tata Steel Limited',
    'HINDALCO.NS': 'Hindalco Industries',
    'JSWSTEEL.NS': 'JSW Steel Limited',
    'VEDL.NS': 'Vedanta Limited',

    # Infrastructure & Construction (5)
    'LT.NS': 'Larsen & Toubro',
    'ULTRACEMCO.NS': 'UltraTech Cement',
    'GRASIM.NS': 'Grasim Industries',
    'ADANIPORTS.NS': 'Adani Ports and Special Economic Zone',
    'ADANIENT.NS': 'Adani Enterprises',

    # Others - High Cap/Volume (8)
    'ASIANPAINT.NS': 'Asian Paints',
    'TITAN.NS': 'Titan Company Limited',
    'BPCL.NS': 'Bharat Petroleum',
    'HINDZINC.NS': 'Hindustan Zinc',
    'INDIGO.NS': 'IndiGo Airlines',
    'TATACONSUM.NS': 'Tata Consumer Products',
    'PIDILITIND.NS': 'Pidilite Industries',
    'SBICARD.NS': 'SBI Card and Payment Services'
}

print(f"📊 Tracking {len(STOCKS)} stocks across 9 sectors")

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

        for symbol, name in STOCKS.items():
            try:
                # Fetch with better error handling
                ticker = yf.Ticker(symbol)

                # Get last 5 days of data for better analysis
                end_date = datetime.now()
                start_date = end_date - timedelta(days=5)
                hist = ticker.history(start=start_date, end=end_date)

                if hist.empty or len(hist) == 0:
                    print(f"⏭️  {symbol:15} SKIPPED - No data available")
                    failed += 1
                    continue

                latest = hist.iloc[-1]
                current_price = float(latest['Close'])

                # Get previous close for change calculation
                if len(hist) > 1:
                    prev_close = float(hist.iloc[-2]['Close'])
                else:
                    prev_close = current_price

                change = current_price - prev_close
                change_percent = (change / prev_close * 100) if prev_close else 0

                # High and Low for the day
                high = float(latest['High'])
                low = float(latest['Low'])
                volume = int(latest['Volume'])

                # Create rich context for RAG
                text = f"""Stock: {symbol.replace('.NS', '')} ({name})
Current Price: ₹{current_price:.2f}
Previous Close: ₹{prev_close:.2f}
Change: ₹{change:.2f} ({change_percent:+.2f}%)
Day High: ₹{high:.2f}
Day Low: ₹{low:.2f}
Volume: {volume:,}
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"""

                try:
                    embedding = embedder.encode(text).tolist()
                except Exception as e:
                    print(f"🔴 Embedding error for {symbol}: {str(e)[:30]}")
                    failed += 1
                    continue

                stock_entry = {
                    'symbol': symbol.replace('.NS', ''),
                    'name': name,
                    'price': current_price,
                    'change': change,
                    'change_percent': change_percent,
                    'high': high,
                    'low': low,
                    'volume': volume,
                    'timestamp': datetime.now().isoformat(),
                    'text': text
                }

                stock_data.append(stock_entry)
                embeddings_store.append(embedding)

                # Keep last 1000 entries
                if len(stock_data) > 1000:
                    stock_data[:] = stock_data[-1000:]
                    embeddings_store[:] = embeddings_store[-1000:]

                successful += 1
                status = "📈" if change_percent > 0 else "📉" if change_percent < 0 else "➡️"
                print(f"{status} {symbol:15} | ₹{current_price:8.2f} | {change_percent:+6.2f}% | Vol: {volume:>10,}")

            except Exception as e:
                failed += 1
                print(f"❌ {symbol:15} ERROR: {str(e)[:45]}")

        elapsed = time.time() - start_time
        print("-" * 70)
        print(f"✅ Fetch complete: {successful} success, {failed} failed | Time: {elapsed:.1f}s")
        print(f"💾 Total entries: {len(stock_data)} | Embeddings: {len(embeddings_store)}")
        print(f"⏳ Next update in 60 seconds...")

        time.sleep(60)

# Start background thread
print("\n🔄 Starting background stock fetcher thread...")
thread = threading.Thread(target=fetch_stocks, daemon=True)
thread.start()
print("✅ Background thread started\n")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'message': 'Stock Market RAG Backend Running',
        'stock_entries': len(stock_data),
        'unique_stocks': len(set(s['symbol'] for s in stock_data)),
        'total_stocks_tracked': len(STOCKS),
        'embeddings': len(embeddings_store),
        'timestamp': datetime.now().isoformat(),
        'version': '2.0-production'
    }), 200

@app.route('/stocks', methods=['GET'])
def get_stocks():
    """Get latest stock data"""
    if not stock_data:
        return jsonify({
            'stocks': [],
            'message': 'Data loading... (wait 60 seconds for first update)',
            'timestamp': datetime.now().isoformat()
        }), 200

    # Get latest entry for each stock
    latest_stocks = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest_stocks:
            latest_stocks[s['symbol']] = s

    return jsonify({
        'stocks': list(latest_stocks.values()),
        'count': len(latest_stocks),
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/stocks/top-gainers', methods=['GET'])
def top_gainers():
    """Get top 5 gaining stocks"""
    if not stock_data:
        return jsonify({'gainers': [], 'message': 'No data yet'}), 200

    latest_stocks = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest_stocks:
            latest_stocks[s['symbol']] = s

    sorted_stocks = sorted(latest_stocks.values(), key=lambda x: x['change_percent'], reverse=True)
    return jsonify({
        'gainers': sorted_stocks[:5],
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/stocks/top-losers', methods=['GET'])
def top_losers():
    """Get top 5 losing stocks"""
    if not stock_data:
        return jsonify({'losers': [], 'message': 'No data yet'}), 200

    latest_stocks = {}
    for s in reversed(stock_data):
        if s['symbol'] not in latest_stocks:
            latest_stocks[s['symbol']] = s

    sorted_stocks = sorted(latest_stocks.values(), key=lambda x: x['change_percent'])
    return jsonify({
        'losers': sorted_stocks[:5],
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/query', methods=['POST'])
def query():
    """AI-powered RAG query"""
    if not stock_data or not embeddings_store:
        return jsonify({
            'answer': '⏳ Stock data still loading. Please wait 60 seconds for initial data fetch.',
            'status': 'loading'
        }), 200

    question = request.json.get('question', '')

    if not question:
        return jsonify({'error': 'Question parameter required'}), 400

    try:
        # Encode question
        query_emb = embedder.encode(question)

        # Calculate similarities
        similarities = []
        for emb in embeddings_store:
            try:
                sim = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb) + 1e-10)
                similarities.append(sim)
            except:
                similarities.append(0)

        # Get top 5 relevant stocks
        if similarities:
            top_5_idx = np.argsort(similarities)[-5:][::-1]
            context = "\n\n".join([stock_data[i]['text'] for i in top_5_idx if i < len(stock_data)])
            sources = [stock_data[i]['symbol'] for i in top_5_idx if i < len(stock_data)]
        else:
            context = "No relevant stock data found"
            sources = []

        # Query Groq
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Indian stock market analyst. Provide concise, data-driven insights based on real-time NSE stock data."
                },
                {
                    "role": "user",
                    "content": f"Real-time stock data:\n{context}\n\nQuestion: {question}"
                }
            ],
            temperature=0.7,
            max_tokens=512
        )

        return jsonify({
            'answer': response.choices[0].message.content,
            'sources': sources,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Query failed: {str(e)}',
            'answer': 'Sorry, unable to process query. Please try again.'
        }), 500

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Production Indian Stock Market RAG Backend v2.0")
    print("=" * 70)
    print(f"✅ Server: http://0.0.0.0:8080")
    print(f"📊 Stocks: {len(STOCKS)} across 9 sectors")
    print(f"⏳ First data in ~60 seconds")
    print("=" * 70)
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=False, threaded=True)
