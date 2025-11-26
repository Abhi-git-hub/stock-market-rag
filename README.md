# 📈 Indian Stock Market Intelligence - RAG Application

**A production-ready AI-powered stock market analysis platform using Retrieval-Augmented Generation (RAG)**

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?style=flat-square&logo=flask)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29-red?style=flat-square&logo=streamlit)
![Docker](https://img.shields.io/badge/Docker-24.0-blue?style=flat-square&logo=docker)
![Groq](https://img.shields.io/badge/Groq-AI-purple?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🎯 Overview

This is a **production-grade AI-powered stock market analysis platform** that combines:

- 🤖 **Groq LLM** for intelligent analysis (FREE tier available)
- 📊 **60+ Indian stocks** tracked in real-time from Yahoo Finance
- 🔍 **RAG (Retrieval-Augmented Generation)** for context-aware answers
- 💻 **Beautiful Streamlit UI** with dark/light theme support
- 🚀 **Fully containerized** with Docker for easy deployment
- 📱 **Responsive design** with advanced technical analysis charts
- ⚡ **Live market data** refreshing every 60 seconds

### ✨ Features

#### 🎨 **Frontend (Streamlit)**
- ✅ Display all 60 stocks in beautiful grid/table views
- ✅ Click any stock → Interactive technical analysis
- ✅ Candlestick charts, gauge indicators, volume analysis
- ✅ Filter by sector (Banking, IT, Energy, FMCG, Pharma, etc.)
- ✅ Sort by price, change%, volume, symbol
- ✅ Top gainers/losers dashboard
- ✅ AI assistant with quick suggestion buttons
- ✅ Real-time volatility alerts (>3% movement)
- ✅ Dark/Light theme toggle
- ✅ Professional code by **CodeVitals**

#### 🧠 **Backend (Flask + Groq AI)**
- ✅ 60 major Indian stocks across 9 sectors
- ✅ Real-time data from Yahoo Finance
- ✅ Vector embeddings with Sentence Transformers
- ✅ RAG pipeline for intelligent queries
- ✅ Health checks and automatic restarts
- ✅ CORS-enabled REST API

#### 📊 **Stocks Covered**
- **Banking** (10): HDFC Bank, ICICI Bank, Axis Bank, SBI, Kotak Bank, etc.
- **IT** (8): TCS, Infosys, Wipro, HCL Tech, Tech Mahindra, etc.
- **Energy** (5): Reliance, ONGC, Power Grid, NTPC, Coal India
- **FMCG** (7): HUL, ITC, Nestlé, Britannia, Dabur, Marico
- **Auto** (6): Maruti, Tata Motors, M&M, Bajaj Auto, Eicher, Hero
- **Pharma** (5): Sun Pharma, Dr. Reddy's, Cipla, Divi's, Apollo
- **Plus:** Telecom, Metals, Infrastructure sectors

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Groq API key (free from https://console.groq.com)

### One-Command Setup

```bash
# Clone repository
git clone https://github.com/codevitals/stock-market-rag.git
cd stock-market-rag

# Create .env file with your Groq API key
echo "groqapi=gsk_YOUR_API_KEY_HERE" > .env

# Build and start (Windows CMD)
docker-compose build
docker-compose up -d

# Or use Makefile (Mac/Linux)
make build
make up
```

### Access Your App

- 🌐 **Frontend:** http://localhost:8501
- 🔌 **Backend API:** http://localhost:8080

---

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Docker Deployment](#-docker-deployment)
- [Cloud Deployment](#-cloud-deployment)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 💻 Installation

### Local Development (Without Docker)

```bash
# Clone repository
git clone https://github.com/codevitals/stock-market-rag.git
cd stock-market-rag

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Or (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements_backend.txt
pip install -r requirements_frontend.txt

# Create .env file
echo "groqapi=gsk_YOUR_API_KEY" > .env

# Start backend (Terminal 1)
python backend_server.py

# Start frontend (Terminal 2)
streamlit run app.py
```

### Docker Deployment (Recommended)

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Windows CMD Commands

```cmd
# Build
docker-compose build

# Start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart
```

---

## 🎯 Usage

### Frontend Dashboard

1. **Browse Stocks**
   - View all 60 stocks in beautiful grid layout
   - Each card shows: Symbol, Price, Change%, Volume, Sector
   - Color-coded: Green for gains, Red for losses

2. **Filter & Sort**
   - Filter by sector (Banking, IT, Energy, etc.)
   - Sort by: Symbol, Change%, Price, Volume
   - Toggle between Grid and Table views

3. **Technical Analysis** (Click any stock)
   - Candlestick price chart
   - Price position gauge (0-100%)
   - Volume analysis bar chart
   - Key metrics: Price, Change, High, Low, Volume
   - Additional info: Sector, Market Cap, PE Ratio
   - Trend indicator: Bullish 🐂 / Bearish 🐻 / Neutral ➡️

4. **AI Assistant**
   - Ask questions about stocks
   - Quick suggestions: "Top gainers?", "Volatile stocks?", etc.
   - Real-time analysis with sources
   - Powered by Groq AI (FREE)

5. **Market Overview**
   - Top 5 gainers
   - Top 5 losers
   - High volatility alerts

### Backend API

```bash
# Health check
curl http://localhost:8080/health

# Get all stocks
curl http://localhost:8080/stocks

# Get top gainers
curl http://localhost:8080/stocks/top-gainers

# Get top losers
curl http://localhost:8080/stocks/top-losers

# Get most active stocks
curl http://localhost:8080/stocks/most-active

# Get alerts
curl http://localhost:8080/alerts

# Query AI
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which stocks are volatile today?"}'
```

---

## 📁 Project Structure

```
stock-market-rag/
├── backend_server.py              # Flask backend (60 stocks, Groq AI, RAG)
├── app.py                         # Streamlit frontend (UI, charts, analysis)
├── requirements_backend.txt       # Backend dependencies
├── requirements_frontend.txt      # Frontend dependencies
├── .env                           # Environment variables (GROQ_API_KEY)
├── .env.example                   # Example env file
├── .dockerignore                  # Docker ignore rules
├── Dockerfile.backend             # Backend container config
├── Dockerfile.frontend            # Frontend container config
├── docker-compose.yml             # Development setup
├── docker-compose.prod.yml        # Production setup
├── Makefile                       # Easy commands (Mac/Linux)
├── README.md                      # This file
└── DOCKER_DEPLOYMENT_GUIDE.md     # Detailed Docker guide
```

---

## 🔌 API Endpoints

### Stock Data

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Backend health check |
| `/stocks` | GET | All stocks (latest data) |
| `/stocks/sector/<sector>` | GET | Stocks by sector |
| `/stocks/top-gainers` | GET | Top 10 gaining stocks |
| `/stocks/top-losers` | GET | Top 10 losing stocks |
| `/stocks/most-active` | GET | Highest volume stocks |
| `/alerts` | GET | Volatility alerts (>3%) |
| `/analytics` | GET | Stock analytics & statistics |
| `/sectors` | GET | Sector breakdown |

### AI Queries

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | AI-powered stock analysis |

**Example Request:**
```json
{
  "question": "Which banking stocks are performing well today?"
}
```

**Example Response:**
```json
{
  "answer": "Based on today's data, HDFC Bank is up 2.5%...",
  "sources": ["HDFCBANK", "ICICIBANK", "KOTAKBANK"],
  "timestamp": "2025-11-26T20:30:00",
  "model": "mixtral-8x7b-32768"
}
```

---

## 🐳 Docker Deployment

### Development

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop
docker-compose down
```

### Production

```bash
# Build with production config
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# Monitor
docker stats
```

### Docker Features

- ✅ Health checks with auto-restart
- ✅ Resource limits (2GB RAM backend, 1GB frontend)
- ✅ Network isolation
- ✅ Log rotation
- ✅ Volume persistence
- ✅ Service dependencies

---

## ☁️ Cloud Deployment

### Option 1: Railway.app (Easiest! 🚀)

1. Push to GitHub
2. Go to https://railway.app
3. Connect GitHub repo
4. Add environment variables (GROQ_API_KEY)
5. Deploy! (auto-detects Docker)

**Cost:** Free tier available

### Option 2: AWS ECS

```bash
# Create ECR repositories
aws ecr create-repository --repository-name stock-rag-backend
aws ecr create-repository --repository-name stock-rag-frontend

# Push images
aws ecr get-login-password --region us-east-1 | docker login ...
docker tag stock-rag-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/...
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/...
```

### Option 3: Digital Ocean App Platform

1. Connect GitHub repository
2. Auto-detect Docker
3. Add environment variables
4. Deploy

**Cost:** $5-12/month

### Option 4: Azure Container Instances

```bash
az container create \
  --resource-group mygroup \
  --name stock-rag \
  --image <image> \
  --ports 8080 8501 \
  --environment-variables GROQ_API_KEY=$GROQ_API_KEY
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file:

```bash
# Required
groqapi=gsk_your_groq_api_key_here

# Optional (for production)
FLASK_ENV=production
PYTHONUNBUFFERED=1
BACKEND_URL=http://localhost:8080
```

### Stocks Configuration

Edit `backend_server.py` to add/remove stocks:

```python
STOCKS = [
    # Banking & Financial Services (10)
    'HDFCBANK', 'ICICIBANK', 'KOTAKBANK', ...
    # IT & Technology (8)
    'TCS', 'INFY', 'WIPRO', ...
    # ... more stocks
]
```

---

## 🔧 Troubleshooting

### "Backend Offline" in Frontend

**Check logs:**
```bash
docker-compose logs backend
```

**Verify API key:**
```bash
cat .env
```

**Restart:**
```bash
docker-compose restart backend
```

### Port Already in Use

**Find process:**
```bash
# Windows
netstat -ano | findstr :8080

# Mac/Linux
lsof -i :8080
```

**Kill process:**
```bash
# Windows
taskkill /PID <id> /F

# Mac/Linux
kill -9 <pid>
```

### Docker Build Fails

```bash
# Clean build
docker-compose build --no-cache

# Check disk space
docker system df

# Clean up
docker system prune -a
```

---

## 📈 Performance Tips

1. **Use production compose file** - Better resource management
2. **Monitor logs** - Early issue detection
3. **Health checks** - Automatic recovery
4. **Caching** - Docker layer caching
5. **Updates** - Regular dependency updates

---

## 🤝 Contributing

Contributions welcome! 

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📜 License

MIT License - See LICENSE file for details

---

## 🙏 Credits

**Built with:**
- [Groq AI](https://groq.com) - Fast LLM inference
- [Streamlit](https://streamlit.io) - Beautiful UI
- [Flask](https://flask.palletsprojects.com) - Backend framework
- [Sentence Transformers](https://www.sbert.net) - Embeddings
- [Plotly](https://plotly.com) - Interactive charts
- [Yahoo Finance](https://finance.yahoo.com) - Stock data

**Made with ❤️ by CodeVitals**

---

## 📞 Support

- 📖 Read [DOCKER_DEPLOYMENT_GUIDE.md](./DOCKER_DEPLOYMENT_GUIDE.md)
- 🐛 Report issues on GitHub
- 💬 Discussions for questions

---

## 🌟 Star History

If you find this project useful, please ⭐ star it on GitHub!

---

**Last Updated:** November 26, 2025  
**Version:** 2.0-production  
**Status:** 🟢 Production Ready
