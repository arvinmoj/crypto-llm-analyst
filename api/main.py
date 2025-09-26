"""
Main FastAPI application for the crypto-llm-analyst service.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Optional, Any
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Internal imports
from ..ai.langchain_agent import CryptoAnalysisAgent, AnalysisRequest, AnalysisResponse
from ..ai.mcp_tools import MCPToolOrchestrator
from ..ai.rag_system import CryptoRAGSystem, RAGQuery
from ..data.bitquery_stream import BitqueryStreamer, create_streamer_from_env
from ..data.data_processor import DataProcessor, MarketSignal
from ..database.models import (
    create_database_engine, create_session_factory,
    CryptocurrencySymbol, OHLCData, MarketSignal as DBMarketSignal,
    AnalysisResult, MarketSentiment
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for services
analysis_agent: Optional[CryptoAnalysisAgent] = None
mcp_orchestrator: Optional[MCPToolOrchestrator] = None
rag_system: Optional[CryptoRAGSystem] = None
data_processor: Optional[DataProcessor] = None
bitquery_streamer: Optional[BitqueryStreamer] = None
db_engine = None
SessionLocal = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global analysis_agent, mcp_orchestrator, rag_system, data_processor, bitquery_streamer, db_engine, SessionLocal
    
    # Initialize services
    try:
        logger.info("Initializing services...")
        
        # Database
        db_engine = create_database_engine()
        SessionLocal = create_session_factory(db_engine)
        
        # AI services
        analysis_agent = CryptoAnalysisAgent()
        mcp_orchestrator = MCPToolOrchestrator()
        rag_system = CryptoRAGSystem()
        data_processor = DataProcessor()
        
        # Data streaming (optional)
        if os.getenv("BITQUERY_API_KEY"):
            bitquery_streamer = create_streamer_from_env()
        
        logger.info("Services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Continue without failing services
    
    yield
    
    # Cleanup
    logger.info("Shutting down services...")
    if bitquery_streamer:
        await bitquery_streamer.disconnect()


# Create FastAPI app
app = FastAPI(
    title="Crypto LLM Analyst API",
    description="AI-powered cryptocurrency analysis and trading recommendations",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, bool]
    timestamp: datetime


class QuickAnalysisResponse(BaseModel):
    symbol: str
    current_price: Optional[float]
    trend: str
    rsi: Optional[float]
    signal_type: str
    confidence: float
    recommendation: str
    timestamp: datetime


class ComprehensiveAnalysisResponse(BaseModel):
    symbol: str
    analysis_type: str
    summary: str
    technical_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    recommendations: List[str]
    confidence: float
    risk_assessment: Dict[str, Any]
    timestamp: datetime


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime


class AlertRequest(BaseModel):
    symbol: str
    alert_type: str
    message: str
    metadata: Optional[Dict[str, Any]] = None


class MarketSummaryResponse(BaseModel):
    symbols: List[Dict[str, Any]]
    market_sentiment: Dict[str, Any]
    top_signals: List[Dict[str, Any]]
    timestamp: datetime


# Dependency injection
def get_db():
    """Get database session"""
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_analysis_agent():
    """Get analysis agent"""
    if analysis_agent is None:
        raise HTTPException(status_code=503, detail="Analysis agent not available")
    return analysis_agent


def get_rag_system():
    """Get RAG system"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not available")
    return rag_system


# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Crypto LLM Analyst API",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services_status = {
        "analysis_agent": analysis_agent is not None,
        "mcp_orchestrator": mcp_orchestrator is not None,
        "rag_system": rag_system is not None,
        "data_processor": data_processor is not None,
        "database": db_engine is not None,
        "bitquery_streamer": bitquery_streamer is not None
    }
    
    all_services_up = all(services_status.values())
    
    return HealthResponse(
        status="healthy" if all_services_up else "degraded",
        version="1.0.0",
        services=services_status,
        timestamp=datetime.now()
    )


@app.get("/api/v1/analysis/{symbol}/quick", response_model=QuickAnalysisResponse)
async def quick_analysis(
    symbol: str,
    agent: CryptoAnalysisAgent = Depends(get_analysis_agent)
):
    """Quick analysis endpoint"""
    try:
        symbol = symbol.upper()
        
        # Create quick analysis request
        request = AnalysisRequest(
            symbol=symbol,
            analysis_type="quick",
            include_recommendations=True
        )
        
        # Get analysis
        response = await agent.analyze(request)
        
        # Extract key metrics (mock data for demo)
        return QuickAnalysisResponse(
            symbol=symbol,
            current_price=50000.0,  # Would come from real data
            trend="bullish",
            rsi=65.5,
            signal_type="HOLD",
            confidence=response.confidence,
            recommendation=response.recommendations[0] if response.recommendations else "Monitor market conditions",
            timestamp=response.timestamp
        )
        
    except Exception as e:
        logger.error(f"Quick analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analysis/{symbol}/comprehensive", response_model=ComprehensiveAnalysisResponse)
async def comprehensive_analysis(
    symbol: str,
    agent: CryptoAnalysisAgent = Depends(get_analysis_agent)
):
    """Comprehensive analysis endpoint"""
    try:
        symbol = symbol.upper()
        
        # Create comprehensive analysis request
        request = AnalysisRequest(
            symbol=symbol,
            analysis_type="comprehensive",
            include_recommendations=True
        )
        
        # Get analysis
        response = await agent.analyze(request)
        
        # Structure comprehensive response
        return ComprehensiveAnalysisResponse(
            symbol=symbol,
            analysis_type=response.analysis_type,
            summary=response.summary,
            technical_analysis={
                "rsi": 65.5,
                "macd": {"value": 120.5, "signal": "bullish"},
                "bollinger_bands": {"position": "middle"},
                "support_levels": [48000, 46500],
                "resistance_levels": [52000, 54000]
            },
            sentiment_analysis={
                "overall_score": 0.65,
                "social_sentiment": 0.7,
                "news_sentiment": 0.6,
                "fear_greed_index": 58
            },
            recommendations=response.recommendations,
            confidence=response.confidence,
            risk_assessment={
                "risk_score": 0.45,
                "volatility": 0.78,
                "var_1d": -0.05,
                "recommended_position_size": 0.75
            },
            timestamp=response.timestamp
        )
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent: CryptoAnalysisAgent = Depends(get_analysis_agent)
):
    """Chat endpoint for interactive analysis"""
    try:
        response = await agent.chat(request.message)
        
        session_id = request.session_id or f"session_{datetime.now().timestamp()}"
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/knowledge/query")
async def knowledge_query(
    q: str = Query(..., description="Query string"),
    max_results: int = Query(5, description="Maximum number of results"),
    rag: CryptoRAGSystem = Depends(get_rag_system)
):
    """Query the knowledge base"""
    try:
        query = RAGQuery(query=q, max_results=max_results)
        response = await rag.query(query)
        
        return {
            "query": q,
            "answer": response.answer,
            "confidence": response.confidence,
            "sources": [
                {
                    "title": source.metadata.get("title", "Unknown"),
                    "category": source.metadata.get("category", "general"),
                    "content_preview": source.content[:200] + "..."
                }
                for source in response.sources
            ],
            "processing_time": response.processing_time
        }
        
    except Exception as e:
        logger.error(f"Knowledge query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/summary", response_model=MarketSummaryResponse)
async def market_summary():
    """Get market summary"""
    try:
        # Mock data for demo - would integrate with real data sources
        symbols_data = [
            {
                "symbol": "BTC",
                "price": 50000.0,
                "change_24h": 2.5,
                "volume_24h": 28000000000,
                "signal": "HOLD"
            },
            {
                "symbol": "ETH",
                "price": 3000.0,
                "change_24h": 1.8,
                "volume_24h": 15000000000,
                "signal": "BUY"
            }
        ]
        
        return MarketSummaryResponse(
            symbols=symbols_data,
            market_sentiment={
                "overall": "neutral_positive",
                "score": 0.62,
                "fear_greed_index": 58
            },
            top_signals=[
                {
                    "symbol": "ETH",
                    "signal": "BUY",
                    "confidence": 0.78,
                    "reason": "Technical breakout pattern"
                }
            ],
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Market summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/alerts/create")
async def create_alert(request: AlertRequest, background_tasks: BackgroundTasks):
    """Create an alert"""
    try:
        # Store alert in database (would implement properly)
        alert_id = f"alert_{datetime.now().timestamp()}"
        
        # Add background task for alert processing
        background_tasks.add_task(process_alert, alert_id, request)
        
        return {
            "alert_id": alert_id,
            "status": "created",
            "message": "Alert created successfully"
        }
        
    except Exception as e:
        logger.error(f"Create alert failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/data/store")
async def store_data(data: Dict[str, Any]):
    """Store analysis data"""
    try:
        # Would implement proper data storage
        logger.info(f"Storing data: {data}")
        
        return {
            "status": "success",
            "message": "Data stored successfully",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Store data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sentiment/aggregate")
async def aggregate_sentiment():
    """Get aggregated market sentiment"""
    try:
        # Mock aggregated sentiment data
        return {
            "overall_sentiment": -0.2,  # Slightly bearish
            "sentiment_label": "neutral_bearish",
            "sources": {
                "social_media": -0.15,
                "news": -0.25,
                "on_chain": -0.18
            },
            "trending_topics": ["regulation", "institutional", "volatility"],
            "confidence": 0.72,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Aggregate sentiment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background tasks
async def process_alert(alert_id: str, request: AlertRequest):
    """Process alert in background"""
    logger.info(f"Processing alert {alert_id}: {request.alert_type} for {request.symbol}")
    # Would implement alert processing logic (email, webhook, etc.)


# WebSocket endpoint for real-time data
@app.websocket("/ws/analysis/{symbol}")
async def websocket_analysis(websocket, symbol: str):
    """WebSocket endpoint for real-time analysis updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(30)  # Update every 30 seconds
            
            # Mock real-time data
            update = {
                "symbol": symbol.upper(),
                "timestamp": datetime.now().isoformat(),
                "price": 50000.0,
                "change": 1.5,
                "signal": "HOLD"
            }
            
            await websocket.send_json(update)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("API_DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )