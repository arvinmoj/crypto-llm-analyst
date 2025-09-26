"""
Test configuration and fixtures for crypto-llm-analyst.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..database.models import Base
from ..config.settings import config


@pytest.fixture
def mock_openai_api_key(monkeypatch):
    """Mock OpenAI API key"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")


@pytest.fixture
def mock_bitquery_api_key(monkeypatch):
    """Mock Bitquery API key"""
    monkeypatch.setenv("BITQUERY_API_KEY", "test-bitquery-key")


@pytest.fixture
def test_db_engine():
    """Create test database engine"""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_db_session(test_db_engine):
    """Create test database session"""
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_mcp_orchestrator():
    """Mock MCP orchestrator"""
    mock = Mock()
    mock.execute_analysis_pipeline = AsyncMock(return_value={
        "price_analysis": Mock(success=True, data={"trend": "bullish"}),
        "technical_indicator": Mock(success=True, data={"rsi": 65.5}),
        "market_sentiment": Mock(success=True, data={"sentiment": 0.7}),
        "risk_assessment": Mock(success=True, data={"risk_score": 0.4})
    })
    return mock


@pytest.fixture
def mock_rag_system():
    """Mock RAG system"""
    mock = Mock()
    mock.query = AsyncMock(return_value=Mock(
        answer="Bitcoin is a cryptocurrency",
        confidence=0.9,
        sources=[],
        processing_time=0.5
    ))
    return mock


@pytest.fixture
def sample_ohlc_data():
    """Sample OHLC data for testing"""
    from datetime import datetime
    from ..data.bitquery_stream import OHLCData
    
    return [
        OHLCData(
            timestamp=datetime.now(),
            symbol="BTC",
            open=50000.0,
            high=51000.0,
            low=49500.0,
            close=50500.0,
            volume=1000000.0
        ),
        OHLCData(
            timestamp=datetime.now(),
            symbol="BTC",
            open=50500.0,
            high=51500.0,
            low=50000.0,
            close=51000.0,
            volume=1200000.0
        )
    ]


@pytest.fixture
def sample_market_signals():
    """Sample market signals for testing"""
    from datetime import datetime
    from ..data.data_processor import MarketSignal, TechnicalIndicators
    
    indicators = TechnicalIndicators(
        rsi=65.5,
        macd=120.5,
        macd_signal=115.2,
        bb_upper=52000.0,
        bb_middle=50000.0,
        bb_lower=48000.0
    )
    
    return [
        MarketSignal(
            timestamp=datetime.now(),
            symbol="BTC",
            signal_type="BUY",
            strength=0.8,
            price=50500.0,
            indicators=indicators,
            confidence=0.75,
            reason="Strong bullish indicators"
        )
    ]