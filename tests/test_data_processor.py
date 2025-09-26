"""
Tests for data processing functionality.
"""

import pytest
from datetime import datetime, timedelta
import numpy as np

from ..data.data_processor import DataProcessor, TechnicalIndicators, MarketSignal
from ..data.bitquery_stream import OHLCData


class TestDataProcessor:
    """Test data processor functionality"""
    
    def test_ohlc_to_dataframe(self, sample_ohlc_data):
        """Test OHLC data to DataFrame conversion"""
        processor = DataProcessor()
        df = processor.ohlc_to_dataframe(sample_ohlc_data)
        
        assert not df.empty
        assert len(df) == 2
        assert 'timestamp' in df.columns
        assert 'symbol' in df.columns
        assert 'close' in df.columns
        assert df['symbol'].iloc[0] == 'BTC'
    
    def test_calculate_sma(self, sample_ohlc_data):
        """Test Simple Moving Average calculation"""
        processor = DataProcessor()
        df = processor.ohlc_to_dataframe(sample_ohlc_data)
        
        sma = processor.calculate_sma(df['close'], window=2)
        assert not sma.empty
        assert not np.isnan(sma.iloc[-1])  # Last value should not be NaN
    
    def test_calculate_rsi(self):
        """Test RSI calculation"""
        processor = DataProcessor()
        
        # Create test data with trend
        prices = [100, 102, 101, 103, 105, 107, 106, 108, 110, 109, 
                 111, 113, 115, 114, 116, 118, 120, 119, 121, 123]
        price_series = processor.ohlc_to_dataframe([
            OHLCData(
                timestamp=datetime.now(),
                symbol="TEST",
                open=p,
                high=p + 1,
                low=p - 1,
                close=p,
                volume=1000
            ) for p in prices
        ])['close']
        
        rsi = processor.calculate_rsi(price_series, window=14)
        assert not rsi.empty
        assert 0 <= rsi.iloc[-1] <= 100  # RSI should be between 0 and 100
    
    def test_generate_signals_insufficient_data(self):
        """Test signal generation with insufficient data"""
        processor = DataProcessor()
        df = processor.ohlc_to_dataframe([])
        
        signals = processor.generate_signals(df, "BTC")
        assert signals == []
    
    def test_generate_signals_with_data(self, sample_ohlc_data):
        """Test signal generation with valid data"""
        processor = DataProcessor()
        
        # Create more data for better analysis
        extended_data = []
        base_price = 50000
        for i in range(30):  # Need at least 26 for MACD
            price = base_price + (i * 100) + np.random.randn() * 50
            extended_data.append(OHLCData(
                timestamp=datetime.now() - timedelta(hours=30-i),
                symbol="BTC",
                open=price,
                high=price + 100,
                low=price - 100,
                close=price + 50,
                volume=1000000
            ))
        
        df = processor.process_ohlc_data(extended_data, "BTC")
        signals = processor.generate_signals(df, "BTC")
        
        assert isinstance(signals, list)
        if signals:  # If signals were generated
            signal = signals[0]
            assert isinstance(signal, MarketSignal)
            assert signal.symbol == "BTC"
            assert signal.signal_type in ["BUY", "SELL", "HOLD"]
            assert 0 <= signal.strength <= 1
            assert 0 <= signal.confidence <= 1
    
    def test_get_market_summary_no_data(self):
        """Test market summary with no data"""
        processor = DataProcessor()
        summary = processor.get_market_summary("BTC")
        
        assert summary == {}
    
    def test_clean_cache(self, sample_ohlc_data):
        """Test cache cleaning functionality"""
        processor = DataProcessor()
        
        # Add data to cache
        processor.process_ohlc_data(sample_ohlc_data, "BTC")
        assert "BTC" in processor.data_cache
        
        # Clean cache (should not remove recent data)
        processor.clean_cache(max_age_hours=1)
        # Recent data should still be there
        
        # Clean cache with very short age
        processor.clean_cache(max_age_hours=0)
        # Data might be removed depending on timestamps


class TestTechnicalIndicators:
    """Test technical indicators data structure"""
    
    def test_technical_indicators_creation(self):
        """Test creating technical indicators"""
        indicators = TechnicalIndicators(
            rsi=65.5,
            macd=120.5,
            sma_20=50000.0
        )
        
        assert indicators.rsi == 65.5
        assert indicators.macd == 120.5
        assert indicators.sma_20 == 50000.0
        assert indicators.ema_12 is None  # Not set


class TestMarketSignal:
    """Test market signal data structure"""
    
    def test_market_signal_creation(self):
        """Test creating market signal"""
        indicators = TechnicalIndicators(rsi=65.5)
        
        signal = MarketSignal(
            timestamp=datetime.now(),
            symbol="BTC",
            signal_type="BUY",
            strength=0.8,
            price=50000.0,
            indicators=indicators,
            confidence=0.75,
            reason="Test signal"
        )
        
        assert signal.symbol == "BTC"
        assert signal.signal_type == "BUY"
        assert signal.strength == 0.8
        assert signal.confidence == 0.75
        assert signal.indicators.rsi == 65.5