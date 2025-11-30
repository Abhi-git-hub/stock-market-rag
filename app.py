import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import numpy as np
import os
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8080')


# Page configuration
st.set_page_config(
    page_title="Indian Stock Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None
if 'show_tech_analysis' not in st.session_state:
    st.session_state.show_tech_analysis = False

def toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

# Custom CSS with beautiful stock cards
def load_css():
    theme = st.session_state.theme

    if theme == 'dark':
        bg_color = "#0E1117"
        secondary_bg = "#1E2127"
        text_color = "#FAFAFA"
        border_color = "#2E3440"
        card_bg = "#1A1D24"
        card_hover_bg = "#252830"
        accent_color = "#00D9FF"
        accent_gradient = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    else:
        bg_color = "#FFFFFF"
        secondary_bg = "#F0F2F6"
        text_color = "#31333F"
        border_color = "#E0E0E0"
        card_bg = "#FFFFFF"
        card_hover_bg = "#F8F9FA"
        accent_color = "#667eea"
        accent_gradient = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"

    st.markdown(f"""
    <style>
    /* Main App Background */
    .stApp {{
        background-color: {bg_color};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: {secondary_bg};
        border-right: 1px solid {border_color};
    }}

    /* Main Header */
    .main-header {{
        background: {accent_gradient};
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }}

    .main-header h1 {{
        color: white;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }}

    .main-header p {{
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
    }}

    /* BEAUTIFUL STOCK CARDS */
    .stock-card {{
        background: {card_bg};
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid {border_color};
        border-left: 4px solid {accent_color};
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        margin-bottom: 1rem;
        position: relative;
        overflow: hidden;
    }}

    .stock-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: {accent_gradient};
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }}

    .stock-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(102, 126, 234, 0.15);
        background: {card_hover_bg};
        border-left-width: 6px;
    }}

    .stock-card:hover::before {{
        transform: scaleX(1);
    }}

    .stock-symbol {{
        font-size: 1.1rem;
        font-weight: 700;
        color: {text_color};
        margin-bottom: 0.5rem;
        letter-spacing: 0.5px;
    }}

    .stock-price {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {text_color};
        margin: 0.5rem 0;
    }}

    .stock-change {{
        font-size: 1rem;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        display: inline-block;
    }}

    .stock-change.positive {{
        background: rgba(76, 175, 80, 0.15);
        color: #4caf50;
    }}

    .stock-change.negative {{
        background: rgba(244, 67, 54, 0.15);
        color: #f44336;
    }}

    .stock-sector {{
        font-size: 0.75rem;
        color: {accent_color};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.25rem;
    }}

    .stock-volume {{
        font-size: 0.8rem;
        color: #888;
        margin-top: 0.5rem;
    }}

    /* Status Badge */
    .status-online {{
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        background: rgba(76, 175, 80, 0.1);
        border: 1px solid #4caf50;
        border-radius: 20px;
        color: #4caf50;
        font-weight: 600;
    }}

    /* Footer */
    .footer {{
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        border-top: 1px solid {border_color};
        color: {text_color};
    }}

    .footer a {{
        color: {accent_color};
        text-decoration: none;
        font-weight: 600;
    }}

    /* Hide Streamlit Elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    /* Custom Scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: {secondary_bg};
    }}

    ::-webkit-scrollbar-thumb {{
        background: {accent_color};
        border-radius: 4px;
    }}
    </style>
    """, unsafe_allow_html=True)

load_css()

# Theme toggle
col1, col2 = st.columns([10, 1])
with col2:
    if st.button("🌙" if st.session_state.theme == 'dark' else "☀️", key="theme_toggle"):
        toggle_theme()
        st.rerun()

# Header
st.markdown("""
<div class="main-header">
    <h1>📈 Indian Stock Market Intelligence</h1>
    <p>Real-time AI-powered analysis of 60+ major stocks</p>
</div>
""", unsafe_allow_html=True)

# Backend health
try:
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:8080')
    health = requests.get(f"{backend_url}/health", timeout=2).json()

    backend_status = "online"
    total_stocks = health.get('total_stocks_tracked', 0)
    stock_count = health.get('stock_count', 0)
except Exception:
    backend_status = "offline"
    total_stocks = 0
    stock_count = 0

# Sidebar
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")

    if backend_status == "online":
        st.markdown('<div class="status-online">● Backend Online</div>', unsafe_allow_html=True)
        st.metric("📊 Total Stocks", total_stocks)
        st.metric("💾 Data Points", stock_count)
    else:
        st.error("❌ Backend Offline")
        st.warning("Start: `python backend_server.py`")

    st.divider()

    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

    st.divider()

    if backend_status == "online":
        st.info("🤖 AI: Mixtral-8x7b")
        st.info("🔄 Update: Every 60s")
        st.info("💰 Cost: $0")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 All Stocks", 
    "🤖 AI Assistant",
    "📈 Market Overview",
    "⚠️ Alerts"
])

# TAB 1: All Stocks with Beautiful Cards
with tab1:
    if backend_status == "offline":
        st.error("Backend offline. Start backend to see stocks.")
    else:
        try:
            response = requests.get(f"{backend_url}/stocks", timeout=5)
            if response.status_code == 200:
                data = response.json()
                stocks = data.get('stocks', [])

                if stocks:
                    df = pd.DataFrame(stocks)

                    # Filters
                    sectors = df['sector'].unique().tolist() if 'sector' in df.columns else []
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        selected_sector = st.selectbox(
                            "🏢 Filter by Sector",
                            ["All Sectors"] + sorted(sectors),
                            key="sector_filter"
                        )

                    with col2:
                        sort_by = st.selectbox(
                            "📊 Sort By",
                            ["Change %", "Symbol", "Price", "Volume"],
                            key="sort_filter"
                        )

                    with col3:
                        view_mode = st.selectbox(
                            "👁️ View",
                            ["Grid", "Table"],
                            key="view_mode"
                        )

                    # Filter and sort
                    if selected_sector != "All Sectors":
                        df = df[df['sector'] == selected_sector]

                    sort_map = {
                        "Symbol": "symbol",
                        "Change %": "change_percent",
                        "Price": "price",
                        "Volume": "volume"
                    }
                    df = df.sort_values(
                        by=sort_map[sort_by],
                        ascending=(sort_by == "Symbol")
                    )

                    st.markdown(f"### Showing {len(df)} stocks")

                    # GRID VIEW with Beautiful Cards
                    if view_mode == "Grid":
                        cols_per_row = 5
                        rows = (len(df) + cols_per_row - 1) // cols_per_row

                        for row_idx in range(rows):
                            cols = st.columns(cols_per_row)
                            for col_idx in range(cols_per_row):
                                stock_idx = row_idx * cols_per_row + col_idx
                                if stock_idx < len(df):
                                    stock = df.iloc[stock_idx]
                                    with cols[col_idx]:
                                        # Beautiful stock card HTML
                                        change_class = "positive" if stock['change_percent'] > 0 else "negative"
                                        arrow = "▲" if stock['change_percent'] > 0 else "▼"

                                        card_html = f"""
                                        <div class="stock-card" onclick="window.location.href='#'">
                                            <div class="stock-sector">{str(stock.get('sector', 'N/A'))[:20]}</div>
                                            <div class="stock-symbol">{stock['symbol']}</div>
                                            <div class="stock-price">₹{stock['price']:.2f}</div>
                                            <div class="stock-change {change_class}">
                                                {arrow} {abs(stock['change_percent']):.2f}%
                                            </div>
                                            <div class="stock-volume">Vol: {stock['volume']:,.0f}</div>
                                        </div>
                                        """

                                        st.markdown(card_html, unsafe_allow_html=True)

                                        # Hidden button for click handling
                                        if st.button(
                                            "📊 Analyze",
                                            key=f"analyze_{stock['symbol']}",
                                            use_container_width=True
                                        ):
                                            st.session_state.selected_stock = stock['symbol']
                                            st.session_state.show_tech_analysis = True
                                            st.rerun()

                    # TABLE VIEW
                    else:
                        st.dataframe(
                            df[['symbol', 'sector', 'price', 'change_percent', 'volume', 'market_cap']],
                            use_container_width=True,
                            height=600
                        )

                    # TECHNICAL ANALYSIS SECTION
                    if st.session_state.show_tech_analysis and st.session_state.selected_stock:
                        st.markdown("---")
                        st.markdown(f"## 📊 Technical Analysis: {st.session_state.selected_stock}")

                        col1, col2 = st.columns([5, 1])
                        with col2:
                            if st.button("✖ Close", key="close_analysis"):
                                st.session_state.show_tech_analysis = False
                                st.session_state.selected_stock = None
                                st.rerun()

                        # Get stock data
                        stock_symbol = st.session_state.selected_stock
                        stock_data_list = df[df['symbol'] == stock_symbol].to_dict('records')

                        if stock_data_list:
                            stock_info = stock_data_list[0]

                            # Key Metrics
                            col1, col2, col3, col4, col5 = st.columns(5)
                            with col1:
                                st.metric("Current Price", f"₹{stock_info['price']:.2f}")
                            with col2:
                                st.metric("Change", f"{stock_info['change_percent']:.2f}%", 
                                         delta=f"{stock_info['change']:.2f}")
                            with col3:
                                st.metric("Day High", f"₹{stock_info['high']:.2f}")
                            with col4:
                                st.metric("Day Low", f"₹{stock_info['low']:.2f}")
                            with col5:
                                st.metric("Volume", f"{stock_info['volume']:,.0f}")

                            st.divider()

                            # Charts
                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown("#### 📈 Price Action")

                                fig = go.Figure()
                                fig.add_trace(go.Candlestick(
                                    x=[datetime.now()],
                                    open=[stock_info['open']],
                                    high=[stock_info['high']],
                                    low=[stock_info['low']],
                                    close=[stock_info['price']],
                                    name=stock_symbol
                                ))

                                fig.update_layout(
                                    height=400,
                                    template='plotly_dark' if st.session_state.theme == 'dark' else 'plotly_white',
                                    xaxis_title="Time",
                                    yaxis_title="Price (₹)",
                                    showlegend=False
                                )

                                st.plotly_chart(fig, use_container_width=True)

                            with col2:
                                st.markdown("#### 📊 Price Position")

                                price_range = stock_info['high'] - stock_info['low']
                                price_position = ((stock_info['price'] - stock_info['low']) / price_range * 100) if price_range > 0 else 50

                                fig = go.Figure(go.Indicator(
                                    mode="gauge+number+delta",
                                    value=price_position,
                                    title={'text': "Position in Day Range (%)"},
                                    delta={'reference': 50},
                                    gauge={
                                        'axis': {'range': [0, 100]},
                                        'bar': {'color': "#667eea"},
                                        'steps': [
                                            {'range': [0, 33], 'color': "#f44336"},
                                            {'range': [33, 66], 'color': "#ffc107"},
                                            {'range': [66, 100], 'color': "#4caf50"}
                                        ]
                                    }
                                ))

                                fig.update_layout(
                                    height=400,
                                    template='plotly_dark' if st.session_state.theme == 'dark' else 'plotly_white'
                                )

                                st.plotly_chart(fig, use_container_width=True)

                            # Additional Info
                            col1, col2 = st.columns(2)

                            with col1:
                                st.info(f"""
                                **Sector:** {stock_info.get('sector', 'N/A')}  
                                **Market Cap:** ₹{stock_info.get('market_cap', 0):,.0f}  
                                **PE Ratio:** {stock_info.get('pe_ratio', 'N/A')}
                                """)

                            with col2:
                                volatility = (price_range / stock_info['open'] * 100) if stock_info['open'] > 0 else 0
                                trend = "Bullish 🐂" if stock_info['change_percent'] > 2 else "Bearish 🐻" if stock_info['change_percent'] < -2 else "Neutral ➡️"

                                st.success(f"""
                                **Day Volatility:** {volatility:.2f}%  
                                **Trend:** {trend}  
                                **Last Updated:** {datetime.now().strftime('%H:%M:%S')}
                                """)

                else:
                    st.warning("⏳ Loading stocks... Wait 60 seconds.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# TAB 2: AI Assistant
with tab2:
    st.markdown("### 🤖 AI-Powered Analysis")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💡 Top gainers?", use_container_width=True):
            st.session_state.ai_question = "Which stocks gained the most today?"
    with col2:
        if st.button("💡 Volatile stocks?", use_container_width=True):
            st.session_state.ai_question = "Which stocks are most volatile?"
    with col3:
        if st.button("💡 Sector analysis?", use_container_width=True):
            st.session_state.ai_question = "Compare sector performance"

    question = st.text_area(
        "Your Question:",
        value=st.session_state.get('ai_question', ''),
        placeholder="e.g., Compare banking vs IT stocks",
        height=100
    )

    if st.button("🔍 Analyze", type="primary"):
        if question:
            with st.spinner("🧠 Analyzing..."):
                try:
                    response = requests.post(
                        f"{backend_url}/query",
                        json={"question": question},
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Analysis Complete")
                        st.markdown(result['answer'])

                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"📊 Sources: {', '.join(result.get('sources', [])[:5])}")
                        with col2:
                            st.info(f"🕐 {result.get('timestamp', '')[:19]}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# TAB 3: Market Overview
with tab3:
    st.markdown("### 📈 Market Overview")

    try:
        gainers_resp = requests.get(f"{backend_url}/stocks/top-gainers", timeout=5)
        losers_resp = requests.get(f"{backend_url}/stocks/top-losers", timeout=5)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🚀 Top Gainers")
            if gainers_resp.status_code == 200:
                for stock in gainers_resp.json().get('gainers', [])[:5]:
                    st.success(f"**{stock['symbol']}** - ₹{stock['price']:.2f} (+{stock['change_percent']:.2f}%)")

        with col2:
            st.markdown("#### 📉 Top Losers")
            if losers_resp.status_code == 200:
                for stock in losers_resp.json().get('losers', [])[:5]:
                    st.error(f"**{stock['symbol']}** - ₹{stock['price']:.2f} ({stock['change_percent']:.2f}%)")
    except Exception:
        st.warning("Unavailable")

# TAB 4: Alerts
with tab4:
    st.markdown("### ⚠️ Volatility Alerts")

    try:
        response = requests.get(f"{backend_url}/alerts", timeout=5)
        if response.status_code == 200:
            alerts = response.json().get('alerts', [])

            if alerts:
                for alert in alerts[:15]:
                    if alert['change_percent'] > 0:
                        st.success(f"🚀 **{alert['symbol']}** +{alert['change_percent']:.2f}%")
                    else:
                        st.error(f"📉 **{alert['symbol']}** {alert['change_percent']:.2f}%")
            else:
                st.info("✅ Market is stable")
    except Exception:
        st.warning("Unavailable")

# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>Powered by <strong>Groq AI</strong> • Yahoo Finance</p>
    <p style="font-size: 1.1rem; font-weight: 600;">
        Made by <a href="#" target="_blank">CodeVitals</a>
    </p>
    <p style="font-size: 0.8rem; color: #888;">© 2025 All rights reserved</p>
</div>
""", unsafe_allow_html=True)
