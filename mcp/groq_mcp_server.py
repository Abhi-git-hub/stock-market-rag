from mcp.server import Server
from mcp.types import Tool, TextContent
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize MCP server
mcp_server = Server("indian-stock-market-mcp")

print("🚀 Starting MCP Server for Indian Stock Market...")

@mcp_server.list_tools()
async def list_tools():
    """Register available tools"""
    return [
        Tool(
            name="query_live_stocks",
            description="Query real-time Indian stock market data with AI analysis using Groq",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question about Indian stock market (NSE/BSE)"
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="get_stock_price",
            description="Get current price of a specific Indian stock",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., RELIANCE, TCS, HDFCBANK)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_volatility_alerts",
            description="Get stocks with high volatility (>3% change)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    
    if name == "query_live_stocks":
        try:
            response = requests.post(
                "http://localhost:8501/query",
                json={"question": arguments['question']},
                timeout=30
            )
            
            result = response.json()
            
            return [TextContent(
                type="text",
                text=f"""📊 Indian Stock Market Analysis (Real-time)

{result['answer']}

Data Sources: {', '.join(result.get('sources', []))}
Model: Groq {result.get('model', 'llama-3.3-70b-versatile')}
Timestamp: {result.get('timestamp', '')}
"""
            )]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "get_stock_price":
        try:
            symbol = arguments['symbol'].upper()
            
            response = requests.get("http://localhost:8501/stocks", timeout=5)
            stocks = response.json().get('stocks', [])
            
            # Find matching stock
            stock = next((s for s in stocks if s['symbol'] == symbol), None)
            
            if stock:
                return [TextContent(
                    type="text",
                    text=f"""📈 {stock['symbol']} - Real-time Data

Price: ₹{stock['price']:.2f}
Change: {stock['change']:.2f} ({stock['change_percent']:.2f}%)
Range: ₹{stock['low']:.2f} - ₹{stock['high']:.2f}
Volume: {stock['volume']:,}
Last Update: {stock['timestamp']}
"""
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Stock {symbol} not found in current data stream"
                )]
                
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "get_volatility_alerts":
        try:
            response = requests.get("http://localhost:8501/alerts", timeout=5)
            alerts = response.json().get('alerts', [])
            
            if alerts:
                alert_text = "⚠️ High Volatility Alerts (>3% change):\n\n"
                
                for alert in alerts[:10]:
                    alert_text += f"{alert['alert_type']} {alert['symbol']}: {alert['change_percent']:.2f}%\n"
                
                return [TextContent(type="text", text=alert_text)]
            else:
                return [TextContent(type="text", text="No high volatility alerts currently")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

# Run MCP server
if __name__ == "__main__":
    import asyncio
    
    async def main():
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options()
            )
    
    asyncio.run(main())
