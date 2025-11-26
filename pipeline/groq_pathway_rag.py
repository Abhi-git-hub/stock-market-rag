import pathway as pw
from groq import Groq
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
sys.path.append('..')
from connectors.indian_stock_connector import create_stock_stream

load_dotenv()

# Initialize Groq client (FREE)
groq_client = Groq(api_key=os.getenv('groqapi'))

# Initialize local embedder (runs on your machine, 100% free)
embedder = SentenceTransformer('all-MiniLM-L6-v2')  # Small, fast, free

print("🚀 Initializing Groq + Pathway RAG Pipeline...")

# Step 1: Create streaming stock data
stock_stream = create_stock_stream()

# Step 2: Generate embeddings for stock data
def generate_embedding(text: str):
    """Generate embeddings using free local model"""
    try:
        embedding = embedder.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        print(f"Embedding error: {e}")
        return [0.0] * 384  # Fallback

# Add embeddings to stream
stock_with_embeddings = stock_stream.select(
    symbol=pw.this.symbol,
    price=pw.this.price,
    change=pw.this.change,
    change_percent=pw.this.change_percent,
    open=pw.this.open,
    high=pw.this.high,
    low=pw.this.low,
    volume=pw.this.volume,
    timestamp=pw.this.timestamp,
    text=pw.this.text,
    embedding=pw.apply(generate_embedding, pw.this.text)
)

# Step 3: Detect volatility alerts
volatility_alerts = stock_with_embeddings.filter(
    abs(pw.this.change_percent) > 3.0  # Alert if >3% change
).select(
    symbol=pw.this.symbol,
    price=pw.this.price,
    change_percent=pw.this.change_percent,
    alert_type=pw.apply(
        lambda change: "SURGE 🚀" if change > 0 else "DROP 📉",
        pw.this.change_percent
    ),
    timestamp=pw.this.timestamp,
    message=pw.apply(
        lambda sym, pct: f"⚠️ {sym} moved {pct:.2f}% - High volatility detected!",
        pw.this.symbol,
        pw.this.change_percent
    )
)

# Step 4: Calculate moving statistics
stock_analytics = stock_with_embeddings.windowby(
    pw.this.symbol,
    window=pw.temporal.sliding(
        duration=pw.Duration(minutes=5),
        hop=pw.Duration(minutes=1)
    ),
    instance=pw.this.timestamp
).reduce(
    symbol=pw.this._pw_key,
    avg_price=pw.reducers.avg(pw.this.price),
    max_price=pw.reducers.max(pw.this.price),
    min_price=pw.reducers.min(pw.this.price),
    total_volume=pw.reducers.sum(pw.this.volume),
    price_swing=pw.reducers.max(pw.this.price) - pw.reducers.min(pw.this.price)
)

# Step 5: Vector search for RAG
class VectorStore:
    """Simple in-memory vector store"""
    
    def __init__(self):
        self.documents = []
        self.embeddings = []
        
    def add(self, doc, embedding):
        self.documents.append(doc)
        self.embeddings.append(embedding)
        
        # Keep only last 500 entries (memory efficient)
        if len(self.documents) > 500:
            self.documents = self.documents[-500:]
            self.embeddings = self.embeddings[-500:]
    
    def search(self, query_embedding, k=5):
        """Find k most similar documents"""
        if not self.embeddings:
            return []
        
        # Cosine similarity
        similarities = [
            np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
            for emb in self.embeddings
        ]
        
        # Get top k indices
        top_k_idx = np.argsort(similarities)[-k:][::-1]
        
        return [self.documents[i] for i in top_k_idx]

vector_store = VectorStore()

# Step 6: RAG Query Function with Groq
def query_market_with_groq(question: str, k=5):
    """
    RAG query using Groq (FREE, fast)
    """
    print(f"💭 Processing query: {question}")
    
    # Generate query embedding
    query_embedding = embedder.encode(question, convert_to_numpy=True)
    
    # Retrieve relevant context
    relevant_docs = vector_store.search(query_embedding, k=k)
    
    if not relevant_docs:
        return {
            'answer': "No stock data available yet. Please wait for data stream to initialize.",
            'sources': [],
            'timestamp': datetime.now().isoformat()
        }
    
    # Build context
    context = "\n\n".join(relevant_docs)
    
    # Query Groq (FREE, unlimited)
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # RECOMMENDED - Best quality

            messages=[
                {
                    "role": "system",
                    "content": """You are an expert Indian stock market analyst with real-time data access.
                    
Provide insights based on:
- Current prices and trends
- Volatility analysis
- Volume patterns
- Historical context

Be specific, data-driven, and actionable. Focus on Indian market context (NSE/BSE)."""
                },
                {
                    "role": "user",
                    "content": f"""Real-time Stock Data:
{context}

Question: {question}

Provide detailed analysis based on the data above."""
                }
            ],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False
        )
        
        answer = response.choices[0].message.content
        
        # Extract symbols from context
        sources = list(set([
            line.split(':')[1].strip() 
            for line in context.split('\n') 
            if line.startswith('Stock:')
        ]))
        
        return {
            'answer': answer,
            'sources': sources,
            'timestamp': datetime.now().isoformat(),
            'model': 'llama-3.3-70b-versatile'
        }
        
    except Exception as e:
        print(f"❌ Groq error: {e}")
        return {
            'answer': f"Error querying Groq: {str(e)}",
            'sources': [],
            'timestamp': datetime.now().isoformat()
        }

# Step 7: Update vector store continuously
def update_vector_store(table):
    """Background task to update vector store"""
    for row in table:
        vector_store.add(row['text'], row['embedding'])

# Apply updates
pw.io.subscribe(stock_with_embeddings, update_vector_store)

# Step 8: Output to files
pw.io.jsonlines.write(stock_with_embeddings, "output/stock_data.jsonl")
pw.io.jsonlines.write(volatility_alerts, "output/alerts.jsonl")
pw.io.jsonlines.write(stock_analytics, "output/analytics.jsonl")

# Step 9: REST API Endpoints
class StockAPI:
    @staticmethod
    @pw.io.http.rest_endpoint(method="POST", path="/query")
    def handle_query(request):
        """AI query endpoint"""
        question = request.json().get('question', '')
        result = query_market_with_groq(question)
        return result
    
    @staticmethod
    @pw.io.http.rest_endpoint(method="GET", path="/stocks")
    def get_stocks(request):
        """Get latest stock data"""
        # Return last 50 entries
        data = stock_with_embeddings.tail(50).to_dict()
        return {"stocks": data, "count": len(data)}
    
    @staticmethod
    @pw.io.http.rest_endpoint(method="GET", path="/alerts")
    def get_alerts(request):
        """Get volatility alerts"""
        alerts = volatility_alerts.tail(20).to_dict()
        return {"alerts": alerts, "count": len(alerts)}
    
    @staticmethod
    @pw.io.http.rest_endpoint(method="GET", path="/analytics")
    def get_analytics(request):
        """Get analytics"""
        analytics = stock_analytics.tail(10).to_dict()
        return {"analytics": analytics}

print("✅ Pipeline ready! Starting server on http://localhost:8080")

# Step 10: Run the pipeline
if __name__ == "__main__":
    pw.run(
        monitoring_level=pw.MonitoringLevel.INFO,
        host="0.0.0.0",
        port=8080
    )

