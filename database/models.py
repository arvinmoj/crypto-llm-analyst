"""
Database models for the crypto-llm-analyst application.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    Text, JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import os

Base = declarative_base()


class CryptocurrencySymbol(Base):
    """Model for cryptocurrency symbols"""
    __tablename__ = 'cryptocurrency_symbols'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    market_cap_rank = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ohlc_data = relationship("OHLCData", back_populates="symbol_info")
    analysis_results = relationship("AnalysisResult", back_populates="symbol_info")
    market_signals = relationship("MarketSignal", back_populates="symbol_info")


class OHLCData(Base):
    """Model for OHLC (Open, High, Low, Close) data"""
    __tablename__ = 'ohlc_data'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey('cryptocurrency_symbols.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    exchange = Column(String(50), nullable=True)
    timeframe = Column(String(10), default='1m')  # 1m, 5m, 1h, 1d, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    symbol_info = relationship("CryptocurrencySymbol", back_populates="ohlc_data")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('symbol_id', 'timestamp', 'timeframe', name='unique_ohlc_entry'),
        Index('idx_ohlc_symbol_timestamp', 'symbol_id', 'timestamp'),
    )


class TechnicalIndicator(Base):
    """Model for technical indicators"""
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey('cryptocurrency_symbols.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    indicator_name = Column(String(50), nullable=False)  # RSI, MACD, BB_UPPER, etc.
    value = Column(Float, nullable=False)
    parameters = Column(JSON, nullable=True)  # Store indicator parameters
    timeframe = Column(String(10), default='1h')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    symbol_info = relationship("CryptocurrencySymbol")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('symbol_id', 'timestamp', 'indicator_name', 'timeframe', 
                        name='unique_indicator_entry'),
        Index('idx_indicator_symbol_timestamp', 'symbol_id', 'timestamp'),
    )


class MarketSignal(Base):
    """Model for market signals and trading recommendations"""
    __tablename__ = 'market_signals'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey('cryptocurrency_symbols.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    signal_type = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    strength = Column(Float, nullable=False)  # 0.0 to 1.0
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    price = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    indicators_used = Column(JSON, nullable=True)  # List of indicators used
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    symbol_info = relationship("CryptocurrencySymbol", back_populates="market_signals")
    
    # Indexes
    __table_args__ = (
        Index('idx_signal_symbol_timestamp', 'symbol_id', 'timestamp'),
        Index('idx_signal_type_timestamp', 'signal_type', 'timestamp'),
    )


class AnalysisResult(Base):
    """Model for storing analysis results from AI agents"""
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey('cryptocurrency_symbols.id'), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # technical, fundamental, sentiment
    analysis_data = Column(JSON, nullable=False)  # Store full analysis data
    summary = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    confidence_score = Column(Float, nullable=True)
    agent_version = Column(String(20), nullable=True)
    execution_time = Column(Float, nullable=True)  # Analysis execution time in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    symbol_info = relationship("CryptocurrencySymbol", back_populates="analysis_results")
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_symbol_type', 'symbol_id', 'analysis_type'),
        Index('idx_analysis_timestamp', 'created_at'),
    )


class MarketSentiment(Base):
    """Model for market sentiment data"""
    __tablename__ = 'market_sentiment'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey('cryptocurrency_symbols.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    overall_sentiment = Column(Float, nullable=False)  # -1.0 to 1.0
    sentiment_label = Column(String(20), nullable=False)  # positive, negative, neutral
    sources = Column(JSON, nullable=True)  # Sentiment from different sources
    volume_indicators = Column(JSON, nullable=True)  # Social volume, mentions, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    symbol_info = relationship("CryptocurrencySymbol")
    
    # Indexes
    __table_args__ = (
        Index('idx_sentiment_symbol_timestamp', 'symbol_id', 'timestamp'),
    )


class KnowledgeDocument(Base):
    """Model for storing knowledge base documents"""
    __tablename__ = 'knowledge_documents'
    
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=True, index=True)
    symbols = Column(JSON, nullable=True)  # Related cryptocurrency symbols
    metadata = Column(JSON, nullable=True)
    source = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_knowledge_category', 'category'),
        Index('idx_knowledge_active', 'is_active'),
    )


class UserSession(Base):
    """Model for user sessions and interactions"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=True)  # Optional user identification
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    session_data = Column(JSON, nullable=True)  # Store session preferences, history, etc.
    
    # Relationships
    interactions = relationship("UserInteraction", back_populates="session")


class UserInteraction(Base):
    """Model for tracking user interactions with the system"""
    __tablename__ = 'user_interactions'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey('user_sessions.session_id'), nullable=False)
    interaction_type = Column(String(50), nullable=False)  # query, analysis, chat, etc.
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    processing_time = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("UserSession", back_populates="interactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_interaction_session_time', 'session_id', 'timestamp'),
        Index('idx_interaction_type_time', 'interaction_type', 'timestamp'),
    )


class SystemMetric(Base):
    """Model for system performance metrics"""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_metric_name_time', 'metric_name', 'timestamp'),
    )


# Database configuration
def create_database_engine(database_url: str = None):
    """Create database engine"""
    if database_url is None:
        database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://user:password@localhost:5432/crypto_llm_analyst"
        )
    
    engine = create_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    
    return engine


def create_session_factory(engine):
    """Create session factory"""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database(database_url: str = None):
    """Initialize database with tables"""
    engine = create_database_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine


# Utility functions
def get_or_create_symbol(session, symbol: str, name: str = None) -> CryptocurrencySymbol:
    """Get or create a cryptocurrency symbol"""
    crypto_symbol = session.query(CryptocurrencySymbol).filter(
        CryptocurrencySymbol.symbol == symbol.upper()
    ).first()
    
    if not crypto_symbol:
        crypto_symbol = CryptocurrencySymbol(
            symbol=symbol.upper(),
            name=name or symbol,
            is_active=True
        )
        session.add(crypto_symbol)
        session.commit()
        session.refresh(crypto_symbol)
    
    return crypto_symbol


def get_latest_ohlc(session, symbol: str, timeframe: str = '1h', limit: int = 100):
    """Get latest OHLC data for a symbol"""
    symbol_obj = session.query(CryptocurrencySymbol).filter(
        CryptocurrencySymbol.symbol == symbol.upper()
    ).first()
    
    if not symbol_obj:
        return []
    
    return session.query(OHLCData).filter(
        OHLCData.symbol_id == symbol_obj.id,
        OHLCData.timeframe == timeframe
    ).order_by(OHLCData.timestamp.desc()).limit(limit).all()


def get_latest_signals(session, symbol: str = None, limit: int = 10):
    """Get latest market signals"""
    query = session.query(MarketSignal).join(CryptocurrencySymbol)
    
    if symbol:
        query = query.filter(CryptocurrencySymbol.symbol == symbol.upper())
    
    return query.order_by(MarketSignal.timestamp.desc()).limit(limit).all()


def cleanup_old_data(session, days: int = 30):
    """Clean up old data from the database"""
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Clean up old OHLC data (keep daily and above)
    session.query(OHLCData).filter(
        OHLCData.created_at < cutoff_date,
        OHLCData.timeframe.in_(['1m', '5m', '15m'])
    ).delete()
    
    # Clean up old technical indicators
    session.query(TechnicalIndicator).filter(
        TechnicalIndicator.created_at < cutoff_date
    ).delete()
    
    # Clean up old user interactions
    session.query(UserInteraction).filter(
        UserInteraction.timestamp < cutoff_date
    ).delete()
    
    # Clean up old system metrics
    session.query(SystemMetric).filter(
        SystemMetric.timestamp < cutoff_date
    ).delete()
    
    session.commit()
    print(f"Cleaned up data older than {days} days")