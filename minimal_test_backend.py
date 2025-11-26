from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

print("=" * 60)
print("MINIMAL TEST BACKEND - Isolating 500 Error")
print("=" * 60)

# Test 1: Check Groq API Key
GROQ_API_KEY = os.getenv('groqapi')
print(f"\n1. Groq API Key Check:")
if GROQ_API_KEY:
    print(f"   ✅ Found (starts with: {GROQ_API_KEY[:10]}...)")
else:
    print("   ❌ NOT FOUND - This is your problem!")
    print("   Create .env file with: groqapi=your_key")

# Test 2: Try importing Groq
print(f"\n2. Groq Library Check:")
try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY or "test")
    print("   ✅ Groq library imported successfully")
except ImportError:
    print("   ❌ Groq not installed - Run: pip install groq")
except Exception as e:
    print(f"   ⚠️  Groq import issue: {e}")

# Test 3: Try importing sentence transformers
print(f"\n3. Sentence Transformers Check:")
try:
    from sentence_transformers import SentenceTransformer
    print("   ✅ sentence-transformers imported successfully")
except ImportError:
    print("   ❌ Not installed - Run: pip install sentence-transformers")
except Exception as e:
    print(f"   ⚠️  Import issue: {e}")

# Test 4: Try importing yfinance
print(f"\n4. YFinance Check:")
try:
    import yfinance as yf
    print("   ✅ yfinance imported successfully")
except ImportError:
    print("   ❌ Not installed - Run: pip install yfinance")

print("\n" + "=" * 60)
print("Starting minimal test server on port 8080...")
print("=" * 60 + "\n")

@app.route('/health', methods=['GET'])
def health():
    """Super simple health check"""
    return jsonify({'status': 'ok', 'message': 'Minimal backend is running'})

@app.route('/test-groq', methods=['GET'])
def test_groq():
    """Test if Groq API works"""
    try:
        from groq import Groq

        if not GROQ_API_KEY:
            return jsonify({
                'error': 'No Groq API key found',
                'fix': 'Create .env file with: groqapi=your_key'
            }), 500

        client = Groq(api_key=GROQ_API_KEY)

        # Simple test call
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )

        return jsonify({
            'status': 'success',
            'message': 'Groq API is working!',
            'response': response.choices[0].message.content
        })

    except Exception as e:
        return jsonify({
            'error': 'Groq API test failed',
            'details': str(e),
            'fix': 'Check your API key at console.groq.com'
        }), 500

@app.route('/test-embedder', methods=['GET'])
def test_embedder():
    """Test if embedder works"""
    try:
        from sentence_transformers import SentenceTransformer

        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        embedding = embedder.encode("test text")

        return jsonify({
            'status': 'success',
            'message': 'Embedder is working!',
            'embedding_size': len(embedding)
        })

    except Exception as e:
        return jsonify({
            'error': 'Embedder test failed',
            'details': str(e)
        }), 500

@app.route('/query', methods=['POST'])
def minimal_query():
    """Minimal query endpoint to test"""
    try:
        data = request.json
        question = data.get('question', '')

        return jsonify({
            'answer': f'Test response to: {question}',
            'status': 'This is a minimal test - if you see this, basic routing works!'
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)