# connectors/indian_stock_connector.py (replace)
import pathway as pw
import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class IndianStockConnector(pw.io.python.ConnectorSubject):
    """
    Real-time Indian stock market data connector
    Streams NSE/BSE data continuously
    """
    
    def __init__(self, symbols, interval=60):
        super().__init__()
        self.symbols = symbols
        self.interval = interval
        # fallback to local backend if not provided
        self.base_url = os.getenv('STOCK_API_URL', 'http://localhost:8080')
        
    def run(self):
        print(f"🚀 Starting stock stream for: {', '.join(self.symbols)} -> {self.base_url}")
        
        while True:
            for symbol in self.symbols:
                try:
                    response = requests.get(
                        f"{self.base_url}/stock?symbol={symbol}",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get('status') == 'success':
                            stock_data = data['data']
                            
                            text_content = self._create_rich_text(symbol, stock_data)
                            
                            self.next(
                                symbol=symbol,
                                price=float(stock_data.get('current_price', 0)),
                                change=float(stock_data.get('change', 0)),
                                change_percent=float(stock_data.get('change_percent', 0)),
                                open=float(stock_data.get('open', 0)),
                                high=float(stock_data.get('high', 0)),
                                low=float(stock_data.get('low', 0)),
                                volume=int(stock_data.get('volume', 0)),
                                timestamp=datetime.now().isoformat(),
                                text=text_content
                            )
                            
                            print(f"✅ {symbol}: ₹{stock_data.get('current_price')} ({stock_data.get('change_percent')}%)")
                        else:
                            print(f"⚠️ {symbol} API returned non-success: {data.get('message')}")
                    else:
                        print(f"⚠️ {symbol} fetch returned status {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error fetching {symbol}: {e}")
                    
            time.sleep(self.interval)
    
    def _create_rich_text(self, symbol, data):
        """Create detailed text for RAG context"""
        return f"""
Stock: {symbol}
Current Price: ₹{data.get('current_price', 'N/A')}
Change: {data.get('change', 'N/A')} ({data.get('change_percent', 'N/A')}%)
Day Range: ₹{data.get('low', 'N/A')} - ₹{data.get('high', 'N/A')}
Open: ₹{data.get('open', 'N/A')}
Volume: {data.get('volume', 'N/A')}
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""".strip()

def create_stock_stream():
    stocks = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
        'HINDUNILVR', 'BHARTIARTL', 'ITC', 'SBIN', 'LT'
    ]
    
    connector = IndianStockConnector(
        symbols=stocks,
        interval=int(os.getenv('UPDATE_INTERVAL', 60))
    )
    
    stock_table = pw.io.python.read(
        connector,
        schema=pw.schema_from_types(
            symbol=str,
            price=float,
            change=float,
            change_percent=float,
            open=float,
            high=float,
            low=float,
            volume=int,
            timestamp=str,
            text=str
        )
    )
    
    return stock_table
