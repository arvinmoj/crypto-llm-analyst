"""FastAPI application for crypto LLM analyst API endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd

logger = logging.getLogger(__name__)

# Pydantic models for API
class MarketDataRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="Trading symbol")
    timeframe: str = Field(default="5m", description="Data timeframe")


class OHLCRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="Trading symbol") 
    start_time: Optional[datetime] = Field(None, description="Start time for data range")
    end_time: Optional[datetime] = Field(None, description="End time for data range")
    limit: int = Field(default=100, description="Maximum number of records")


class AnalysisRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="Trading symbol")
    query: str = Field(..., description="Analysis query or question")
    analysis_type: str = Field(default="general", description="Type of analysis")
    include_context: bool = Field(default=True, description="Include market context")


class PredictionRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="Trading symbol")
    query: str = Field(..., description="Prediction query")
    horizon: str = Field(default="24h", description="Prediction time horizon")


class TechnicalAnalysisRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="Trading symbol")
    query: str = Field(..., description="Technical analysis query")
    indicators: Optional[List[str]] = Field(None, description="Specific indicators to analyze")


class AlertRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="Trading symbol")
    alert_type: str = Field(..., description="Type of alert")
    conditions: Dict[str, Any] = Field(..., description="Alert conditions")
    message: Optional[str] = Field(None, description="Custom alert message")


class SignalRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    signal_type: str = Field(..., description="Signal type (buy/sell/hold)")
    confidence: float = Field(..., description="Signal confidence score")
    price: float = Field(..., description="Signal price")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional signal context")


# API Response models
class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class AnalysisResponse(BaseModel):
    analysis: str
    confidence: float
    analysis_type: str
    symbol: str
    timestamp: datetime
    context_used: Optional[Dict[str, Any]] = None


class MarketSummaryResponse(BaseModel):
    symbol: str
    current_price: float
    high_24h: float
    low_24h: float
    volume_24h: float
    price_change_24h: float
    price_change_percent_24h: float
    timestamp: datetime


# Create FastAPI app
app = FastAPI(
    title="Crypto LLM Analyst API",
    description="LLM-Powered Applications for OHLC Data Analysis",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global system components (to be injected)
crypto_system = None


def get_crypto_system():
    """Dependency to get crypto system instance."""
    if crypto_system is None:
        raise HTTPException(status_code=500, detail="Crypto system not initialized")
    return crypto_system


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}


# Market data endpoints
@app.get("/api/market/summary", response_model=APIResponse)
async def get_market_summary(
    request: MarketDataRequest = Depends(),
    system=Depends(get_crypto_system)
):
    """Get market summary for a symbol."""
    try:
        if not system.database:
            raise HTTPException(status_code=500, detail="Database not available")
        
        summary = await system.database.get_market_summary(request.symbol)
        
        if not summary:
            raise HTTPException(status_code=404, detail="No market data found")
        
        return APIResponse(success=True, data=summary)
        
    except Exception as e:
        logger.error(f"Error getting market summary: {e}")
        return APIResponse(success=False, error=str(e))


@app.get("/api/market/price")
async def get_current_price(
    symbol: str = "BTCUSDT",
    system=Depends(get_crypto_system)
):
    """Get current price for a symbol."""
    try:
        if not system.database:
            raise HTTPException(status_code=500, detail="Database not available")
        
        summary = await system.database.get_market_summary(symbol)
        
        if not summary:
            raise HTTPException(status_code=404, detail="No price data found")
        
        return {
            "symbol": symbol,
            "current_price": summary.get("current_price", 0),
            "timestamp": summary.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"Error getting current price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/ohlc", response_model=APIResponse)
async def get_ohlc_data(
    request: OHLCRequest = Depends(),
    system=Depends(get_crypto_system)
):
    """Get OHLC data for a symbol."""
    try:
        if not system.database:
            raise HTTPException(status_code=500, detail="Database not available")
        
        if request.start_time and request.end_time:
            df = await system.database.get_ohlc_range(
                request.symbol, 
                request.start_time, 
                request.end_time
            )
        else:
            df = await system.database.get_latest_ohlc(
                request.symbol, 
                request.limit
            )
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No OHLC data found")
        
        # Convert DataFrame to records
        ohlc_records = df.to_dict('records')
        
        return APIResponse(success=True, data=ohlc_records)
        
    except Exception as e:
        logger.error(f"Error getting OHLC data: {e}")
        return APIResponse(success=False, error=str(e))


@app.get("/api/market/context")
async def get_market_context(
    symbol: str = "BTCUSDT",
    time_range_hours: int = 24,
    system=Depends(get_crypto_system)
):
    """Get market context for analysis."""
    try:
        # Get market summary
        market_summary = await system.database.get_market_summary(symbol) if system.database else {}
        
        # Get recent OHLC data
        recent_data = await system.database.get_latest_ohlc(symbol, 50) if system.database else pd.DataFrame()
        
        # Get RAG context if available
        rag_context = ""
        if system.rag_system:
            rag_context = await system.rag_system.get_market_context(
                f"Current market conditions for {symbol}",
                time_range_hours=time_range_hours
            )
        
        context = {
            "market_summary": market_summary,
            "recent_ohlc_count": len(recent_data) if not recent_data.empty else 0,
            "rag_context": rag_context[:1000] + "..." if len(rag_context) > 1000 else rag_context,
            "symbol": symbol,
            "generated_at": datetime.now().isoformat()
        }
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting market context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/daily-summary")
async def get_daily_summary(
    symbol: str = "BTCUSDT",
    system=Depends(get_crypto_system)
):
    """Get daily market summary."""
    try:
        if not system.database:
            return {"error": "Database not available"}
        
        # Get 24h data
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        df = await system.database.get_ohlc_range(symbol, start_time, end_time)
        
        if df.empty:
            return {"error": "No data available"}
        
        summary = {
            "symbol": symbol,
            "date": end_time.date().isoformat(),
            "records_count": len(df),
            "opening_price": float(df.iloc[0]['open']) if not df.empty else 0,
            "closing_price": float(df.iloc[-1]['close']) if not df.empty else 0,
            "high_price": float(df['high'].max()),
            "low_price": float(df['low'].min()),
            "total_volume": float(df['volume'].sum()),
            "average_price": float(df['close'].mean()),
            "price_volatility": float(df['close'].std()),
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting daily summary: {e}")
        return {"error": str(e)}


# Analysis endpoints
@app.post("/api/analysis/market", response_model=APIResponse)
async def analyze_market(
    request: AnalysisRequest,
    system=Depends(get_crypto_system)
):
    """Perform market analysis using LLM."""
    try:
        if not system.llm_manager or not system.database:
            raise HTTPException(status_code=500, detail="LLM or database not available")
        
        # Get market data
        market_data = await system.database.get_market_summary(request.symbol)
        ohlc_data = await system.database.get_latest_ohlc(request.symbol, 50)
        
        # Perform analysis
        analysis, confidence = await system.llm_manager.analyze_market(
            request.query, 
            market_data, 
            ohlc_data
        )
        
        # Store analysis result
        if system.database:
            await system.database.save_analysis(
                request.symbol,
                request.analysis_type,
                request.query,
                analysis,
                confidence
            )
        
        response_data = AnalysisResponse(
            analysis=analysis,
            confidence=confidence,
            analysis_type=request.analysis_type,
            symbol=request.symbol,
            timestamp=datetime.now(),
            context_used={"market_data": bool(market_data), "ohlc_records": len(ohlc_data)}
        )
        
        return APIResponse(success=True, data=response_data.dict())
        
    except Exception as e:
        logger.error(f"Error in market analysis: {e}")
        return APIResponse(success=False, error=str(e))


@app.post("/api/analysis/predict", response_model=APIResponse)
async def predict_price(
    request: PredictionRequest,
    system=Depends(get_crypto_system)
):
    """Generate price predictions."""
    try:
        if not system.llm_manager or not system.database:
            raise HTTPException(status_code=500, detail="LLM or database not available")
        
        # Get historical data
        ohlc_data = await system.database.get_latest_ohlc(request.symbol, 100)
        
        # Perform prediction
        prediction, confidence = await system.llm_manager.predict_price(
            request.query,
            ohlc_data
        )
        
        # Store analysis result
        if system.database:
            await system.database.save_analysis(
                request.symbol,
                "price_prediction",
                request.query,
                prediction,
                confidence
            )
        
        response_data = AnalysisResponse(
            analysis=prediction,
            confidence=confidence,
            analysis_type="price_prediction",
            symbol=request.symbol,
            timestamp=datetime.now(),
            context_used={"horizon": request.horizon, "data_points": len(ohlc_data)}
        )
        
        return APIResponse(success=True, data=response_data.dict())
        
    except Exception as e:
        logger.error(f"Error in price prediction: {e}")
        return APIResponse(success=False, error=str(e))


@app.post("/api/analysis/technical", response_model=APIResponse)
async def technical_analysis(
    request: TechnicalAnalysisRequest,
    system=Depends(get_crypto_system)
):
    """Perform technical analysis."""
    try:
        if not system.llm_manager or not system.database:
            raise HTTPException(status_code=500, detail="LLM or database not available")
        
        # Get OHLC data
        ohlc_data = await system.database.get_latest_ohlc(request.symbol, 100)
        
        # Perform technical analysis
        analysis, confidence = await system.llm_manager.technical_analysis(
            request.query,
            ohlc_data,
            indicators=None  # Let the system calculate basic indicators
        )
        
        # Store analysis result
        if system.database:
            await system.database.save_analysis(
                request.symbol,
                "technical_analysis",
                request.query,
                analysis,
                confidence
            )
        
        response_data = AnalysisResponse(
            analysis=analysis,
            confidence=confidence,
            analysis_type="technical_analysis",
            symbol=request.symbol,
            timestamp=datetime.now(),
            context_used={"indicators_requested": request.indicators, "data_points": len(ohlc_data)}
        )
        
        return APIResponse(success=True, data=response_data.dict())
        
    except Exception as e:
        logger.error(f"Error in technical analysis: {e}")
        return APIResponse(success=False, error=str(e))


@app.post("/api/analysis/general", response_model=APIResponse)
async def general_query(
    query: str,
    symbol: str = "BTCUSDT",
    system=Depends(get_crypto_system)
):
    """Handle general cryptocurrency questions."""
    try:
        if not system.llm_manager:
            raise HTTPException(status_code=500, detail="LLM not available")
        
        # Get market context
        market_context = None
        if system.database:
            market_context = await system.database.get_market_summary(symbol)
        
        # Perform general query
        response = await system.llm_manager.general_query(query, market_context)
        
        return APIResponse(
            success=True, 
            data={
                "response": response,
                "query": query,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error in general query: {e}")
        return APIResponse(success=False, error=str(e))


@app.post("/api/analysis/store")
async def store_analysis(
    analysis: dict,
    system=Depends(get_crypto_system)
):
    """Store analysis result (used by N8N workflows)."""
    try:
        if not system.database:
            raise HTTPException(status_code=500, detail="Database not available")
        
        success = await system.database.save_analysis(
            analysis.get("symbol", "BTCUSDT"),
            analysis.get("analysis_type", "general"),
            analysis.get("query", ""),
            analysis.get("response", ""),
            analysis.get("confidence", 0.0),
            analysis.get("context")
        )
        
        return {"success": success, "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"Error storing analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analysis/report")
async def generate_report(
    market_data: dict,
    report_type: str = "daily_market_summary",
    system=Depends(get_crypto_system)
):
    """Generate market report (used by N8N workflows)."""
    try:
        if not system.llm_manager:
            raise HTTPException(status_code=500, detail="LLM not available")
        
        # Create comprehensive report query
        report_query = f"Generate a {report_type} report based on the provided market data. Include key insights, trends, and actionable recommendations."
        
        # Generate report using general query
        report = await system.llm_manager.general_query(report_query, market_data)
        
        return {
            "report": report,
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "market_data_summary": {
                "symbols_analyzed": len(market_data.keys()) if isinstance(market_data, dict) else 1
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Signal processing endpoints
@app.post("/api/signals/process")
async def process_trading_signal(
    request: SignalRequest,
    system=Depends(get_crypto_system)
):
    """Process trading signal with AI analysis."""
    try:
        if not system.llm_manager or not system.database:
            raise HTTPException(status_code=500, detail="LLM or database not available")
        
        # Get market context
        market_context = await system.database.get_market_summary(request.symbol)
        ohlc_data = await system.database.get_latest_ohlc(request.symbol, 20)
        
        # Analyze signal with AI
        signal_query = f"Analyze this {request.signal_type} signal for {request.symbol} at ${request.price} with {request.confidence} confidence. Provide validation and recommendations."
        
        analysis, ai_confidence = await system.llm_manager.analyze_market(
            signal_query,
            market_context,
            ohlc_data
        )
        
        # Store signal analysis
        await system.database.save_analysis(
            request.symbol,
            "signal_analysis",
            signal_query,
            analysis,
            ai_confidence,
            data_context={
                "original_signal": request.dict(),
                "market_context": market_context
            }
        )
        
        return {
            "signal_validation": analysis,
            "ai_confidence": ai_confidence,
            "original_signal": request.dict(),
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analysis/signal")
async def analyze_signal(
    signal: dict,
    market_context: dict,
    system=Depends(get_crypto_system)
):
    """Analyze trading signal (used by N8N workflows)."""
    try:
        if not system.llm_manager:
            raise HTTPException(status_code=500, detail="LLM not available")
        
        # Create analysis query
        query = f"Analyze trading signal: {signal.get('signal_type')} {signal.get('symbol')} at ${signal.get('price')} with {signal.get('confidence')} confidence"
        
        # Perform analysis
        analysis = await system.llm_manager.general_query(query, market_context)
        
        return {
            "analysis": analysis,
            "signal": signal,
            "market_context_used": bool(market_context),
            "analyzed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Alert endpoints
@app.post("/api/alerts/send")
async def send_alert(request: AlertRequest):
    """Send alert notification."""
    try:
        # In a real implementation, integrate with notification services
        # For now, just log the alert
        alert_data = {
            "symbol": request.symbol,
            "alert_type": request.alert_type,
            "conditions": request.conditions,
            "message": request.message or f"Alert triggered for {request.symbol}",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Alert sent: {alert_data}")
        
        return {
            "alert_sent": True,
            "alert_data": alert_data
        }
        
    except Exception as e:
        logger.error(f"Error sending alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# History endpoints
@app.get("/api/history/analysis")
async def get_analysis_history(
    symbol: str = "BTCUSDT",
    analysis_type: Optional[str] = None,
    limit: int = 10,
    system=Depends(get_crypto_system)
):
    """Get analysis history."""
    try:
        if not system.database:
            raise HTTPException(status_code=500, detail="Database not available")
        
        history = await system.database.get_recent_analysis(
            symbol, 
            analysis_type, 
            limit
        )
        
        return {
            "analysis_history": history,
            "symbol": symbol,
            "analysis_type": analysis_type,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting analysis history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# System status endpoint
@app.get("/api/system/status")
async def get_system_status(system=Depends(get_crypto_system)):
    """Get system component status."""
    try:
        status = {
            "database": system.database is not None,
            "llm_manager": system.llm_manager is not None,
            "data_source": system.data_source is not None,
            "rag_system": system.rag_system is not None,
            "mcp_protocol": system.mcp_protocol is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        return status
        
    except Exception as e:
        return {"error": str(e)}


# Set the crypto system instance
def set_crypto_system(system):
    """Set the global crypto system instance."""
    global crypto_system
    crypto_system = system


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)