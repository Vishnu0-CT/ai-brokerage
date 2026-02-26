"""
Standalone Yahoo Finance API Server
Run this to test Yahoo Finance endpoints without the full application

Usage:
    python yahoo_server.py

Then visit:
    http://localhost:8000/docs - API documentation
    http://localhost:8000/api/yahoo/quote/AAPL - Example endpoint
    ws://localhost:8000/api/yahoo/stream - WebSocket endpoint
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Yahoo Finance API",
    description="Comprehensive Yahoo Finance REST API with WebSocket streaming",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register Yahoo Finance router
from app.routes.yahoo_finance import router as yahoo_finance_router
app.include_router(yahoo_finance_router)

@app.get("/")
async def root():
    return {
        "message": "Yahoo Finance API Server",
        "docs": "/docs",
        "endpoints": {
            "quote": "/api/yahoo/quote/{symbol}",
            "quotes": "/api/yahoo/quotes?symbols=AAPL,MSFT",
            "fast_info": "/api/yahoo/fast-info/{symbol}",
            "historical": "/api/yahoo/historical/{symbol}",
            "options": "/api/yahoo/options/{symbol}",
            "company": "/api/yahoo/company/{symbol}",
            "insider": "/api/yahoo/insider/{symbol}",
            "holders": "/api/yahoo/holders/{symbol}",
            "analyst": "/api/yahoo/analyst/{symbol}",
            "estimates": "/api/yahoo/estimates/{symbol}",
            "earnings": "/api/yahoo/earnings/{symbol}",
            "news": "/api/yahoo/news/{symbol}",
            "trending": "/api/yahoo/trending/{region}",
            "indices_us": "/api/yahoo/indices/us",
            "indices_india": "/api/yahoo/indices/india",
            "websocket": "ws://localhost:8000/api/yahoo/stream"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Yahoo Finance API Server...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/api/yahoo/stream")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
