# grpq_mcp_server.py (replace)
from mcp.server import Server
from mcp.types import Tool, TextContent
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8080')

mcp_server = Server("indian-stock-market-mcp")
print("🚀 Starting MCP Server for Indian Stock Market...")

@mcp_server.list_tools()
async def list_tools():
    return [
        Tool(
            name="query_live_stocks",
            description="Query real-time Indian stock market data with AI analysis using Groq",
            inputSchema={
                "type": "object",
                "properties": { "question": {"type": "string"} },
                "required": ["question"]
            }
        ),
        Tool(
            name="get_stock_price",
            description="Get current price of a specific Indian stock",
            inputSchema={
                "type": "object",
                "properties": { "symbol": {"type": "string"} },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_volatility_alerts",
            description="Get stocks with high volatility (>3% change)",
            inputSchema={ "type": "object", "properties": {} }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "query_live_stocks":
            response = requests.post(
                f"{BACKEND_URL}/query",
                json={"question": arguments['question']},
                timeout=30
            )
            result = response.json() if response.ok else {"answer": f"Backend error: {response.status_code}"}
            return [TextContent(type="text", text=f"📊 Indian Stock Market Analysis\n\n{result.get('answer')}\n\nSources: {', '.join(result.get('sources', []))}\nTimestamp: {result.get('timestamp','')}")]
        
        elif name == "get_stock_price":
            symbol = arguments['symbol'].upper()
            response = requests.get(f"{BACKEND_URL}/stocks", timeout=10)
            if not response.ok:
                return [TextContent(type="text", text=f"Error fetching stocks: {response.status_code}")]
            stocks = response.json().get('stocks', [])
            stock = next((s for s in stocks if s['symbol'] == symbol), None)
            if stock:
                return [TextContent(type="text", text=f"📈 {stock['symbol']} - Price: ₹{stock['price']:.2f} Change: {stock['change']:.2f} ({stock['change_percent']:.2f}% )")]
            return [TextContent(type="text", text=f"Stock {symbol} not found")]
        
        elif name == "get_volatility_alerts":
            response = requests.get(f"{BACKEND_URL}/alerts", timeout=10)
            if not response.ok:
                return [TextContent(type="text", text=f"Error fetching alerts: {response.status_code}")]
            alerts = response.json().get('alerts', [])
            if alerts:
                alert_text = "⚠️ High Volatility Alerts (>3% change):\n\n"
                for a in alerts[:10]:
                    alert_text += f"{a.get('alert_type','')} {a.get('symbol','')} : {a.get('change_percent',0):.2f}%\n"
                return [TextContent(type="text", text=alert_text)]
            return [TextContent(type="text", text="No high volatility alerts currently")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
