"""
Data processing module for OHLC and market data analysis.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from .bitquery_stream import OHLCData

logger = logging.getLogger(__name__)


@dataclass
class TechnicalIndicators:
    """Technical indicators for market analysis"""
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    sma_20: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    volume_sma: Optional[float] = None


@dataclass
class MarketSignal:
    """Market signal structure"""
    timestamp: datetime
    symbol: str
    signal_type: str  # BUY, SELL, HOLD
    strength: float  # 0-1
    price: float
    indicators: TechnicalIndicators
    confidence: float
    reason: str


class DataProcessor:
    """Process OHLC data and generate technical indicators"""
    
    def __init__(self):
        self.data_cache: Dict[str, pd.DataFrame] = {}
        
    def ohlc_to_dataframe(self, ohlc_data: List[OHLCData]) -> pd.DataFrame:
        """Convert OHLC data list to pandas DataFrame"""
        data = []
        for ohlc in ohlc_data:
            data.append({
                'timestamp': ohlc.timestamp,
                'symbol': ohlc.symbol,
                'open': ohlc.open,
                'high': ohlc.high,
                'low': ohlc.low,
                'close': ohlc.close,
                'volume': ohlc.volume,
                'exchange': ohlc.exchange
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def calculate_sma(self, data: pd.Series, window: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=window).mean()
    
    def calculate_ema(self, data: pd.Series, span: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=span).mean()
    
    def calculate_rsi(self, data: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD, Signal line, and Histogram"""
        ema_fast = self.calculate_ema(data, fast)
        ema_slow = self.calculate_ema(data, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(self, data: pd.Series, window: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = self.calculate_sma(data, window)
        std = data.rolling(window=window).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band, sma, lower_band
    
    def process_ohlc_data(self, ohlc_data: List[OHLCData], symbol: str) -> pd.DataFrame:
        """Process OHLC data and add technical indicators"""
        df = self.ohlc_to_dataframe(ohlc_data)
        
        if df.empty or len(df) < 26:  # Need at least 26 periods for MACD
            logger.warning(f"Insufficient data for {symbol}: {len(df)} periods")
            return df
        
        # Calculate technical indicators
        df['sma_20'] = self.calculate_sma(df['close'], 20)
        df['ema_12'] = self.calculate_ema(df['close'], 12)
        df['ema_26'] = self.calculate_ema(df['close'], 26)
        df['rsi'] = self.calculate_rsi(df['close'])
        
        macd, macd_signal, macd_histogram = self.calculate_macd(df['close'])
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_histogram'] = macd_histogram
        
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(df['close'])
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower
        
        df['volume_sma'] = self.calculate_sma(df['volume'], 20)
        
        # Store in cache
        self.data_cache[symbol] = df
        
        return df
    
    def generate_signals(self, df: pd.DataFrame, symbol: str) -> List[MarketSignal]:
        """Generate trading signals based on technical indicators"""
        signals = []
        
        if df.empty or len(df) < 2:
            return signals
        
        # Get the latest data point
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest
        
        # Initialize indicators
        indicators = TechnicalIndicators(
            rsi=latest.get('rsi'),
            macd=latest.get('macd'),
            macd_signal=latest.get('macd_signal'),
            bb_upper=latest.get('bb_upper'),
            bb_middle=latest.get('bb_middle'),
            bb_lower=latest.get('bb_lower'),
            sma_20=latest.get('sma_20'),
            ema_12=latest.get('ema_12'),
            ema_26=latest.get('ema_26'),
            volume_sma=latest.get('volume_sma')
        )
        
        # Signal generation logic
        signal_type = "HOLD"
        strength = 0.0
        confidence = 0.0
        reason = "No clear signal"
        
        signals_count = 0
        buy_signals = 0
        sell_signals = 0
        
        # RSI signals
        if pd.notna(latest.get('rsi')):
            if latest['rsi'] < 30:  # Oversold
                buy_signals += 1
                signals_count += 1
            elif latest['rsi'] > 70:  # Overbought
                sell_signals += 1
                signals_count += 1
        
        # MACD signals
        if pd.notna(latest.get('macd')) and pd.notna(previous.get('macd')):
            if (latest['macd'] > latest['macd_signal'] and 
                previous['macd'] <= previous['macd_signal']):  # Bullish crossover
                buy_signals += 1
                signals_count += 1
            elif (latest['macd'] < latest['macd_signal'] and 
                  previous['macd'] >= previous['macd_signal']):  # Bearish crossover
                sell_signals += 1
                signals_count += 1
        
        # Bollinger Bands signals
        if (pd.notna(latest.get('bb_lower')) and pd.notna(latest.get('bb_upper'))):
            if latest['close'] <= latest['bb_lower']:  # Oversold
                buy_signals += 1
                signals_count += 1
            elif latest['close'] >= latest['bb_upper']:  # Overbought
                sell_signals += 1
                signals_count += 1
        
        # Moving Average signals
        if pd.notna(latest.get('ema_12')) and pd.notna(latest.get('ema_26')):
            if latest['ema_12'] > latest['ema_26'] and previous['ema_12'] <= previous['ema_26']:
                buy_signals += 1
                signals_count += 1
            elif latest['ema_12'] < latest['ema_26'] and previous['ema_12'] >= previous['ema_26']:
                sell_signals += 1
                signals_count += 1
        
        # Determine final signal
        if signals_count > 0:
            if buy_signals > sell_signals:
                signal_type = "BUY"
                strength = buy_signals / signals_count
                confidence = min(strength * 0.8, 0.9)
                reason = f"Buy signals: {buy_signals}/{signals_count}"
            elif sell_signals > buy_signals:
                signal_type = "SELL"
                strength = sell_signals / signals_count
                confidence = min(strength * 0.8, 0.9)
                reason = f"Sell signals: {sell_signals}/{signals_count}"
            else:
                signal_type = "HOLD"
                strength = 0.5
                confidence = 0.3
                reason = f"Mixed signals: {buy_signals} buy, {sell_signals} sell"
        
        signal = MarketSignal(
            timestamp=latest['timestamp'],
            symbol=symbol,
            signal_type=signal_type,
            strength=strength,
            price=latest['close'],
            indicators=indicators,
            confidence=confidence,
            reason=reason
        )
        
        signals.append(signal)
        return signals
    
    def get_market_summary(self, symbol: str) -> Dict:
        """Get market summary for a symbol"""
        if symbol not in self.data_cache:
            return {}
        
        df = self.data_cache[symbol]
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        
        # Calculate price change
        if len(df) > 1:
            previous_close = df.iloc[-2]['close']
            price_change = latest['close'] - previous_close
            price_change_pct = (price_change / previous_close) * 100
        else:
            price_change = 0
            price_change_pct = 0
        
        return {
            'symbol': symbol,
            'current_price': latest['close'],
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'volume': latest['volume'],
            'high_24h': df.tail(24)['high'].max() if len(df) >= 24 else latest['high'],
            'low_24h': df.tail(24)['low'].min() if len(df) >= 24 else latest['low'],
            'rsi': latest.get('rsi'),
            'timestamp': latest['timestamp']
        }
    
    def clean_cache(self, max_age_hours: int = 24):
        """Clean old data from cache"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for symbol in list(self.data_cache.keys()):
            df = self.data_cache[symbol]
            if not df.empty:
                # Keep only recent data
                recent_data = df[df['timestamp'] >= cutoff_time]
                if not recent_data.empty:
                    self.data_cache[symbol] = recent_data
                else:
                    del self.data_cache[symbol]
    
    def export_data(self, symbol: str, format: str = 'csv') -> Optional[str]:
        """Export processed data to file"""
        if symbol not in self.data_cache:
            return None
        
        df = self.data_cache[symbol]
        filename = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        
        try:
            if format.lower() == 'csv':
                df.to_csv(filename, index=False)
            elif format.lower() == 'json':
                df.to_json(filename, orient='records', date_format='iso')
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
            
            logger.info(f"Data exported to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return None


# Example usage and testing
def test_processor():
    """Test data processor with sample data"""
    from datetime import datetime, timedelta
    
    # Create sample OHLC data
    sample_data = []
    base_time = datetime.now() - timedelta(hours=100)
    base_price = 50000.0
    
    for i in range(100):
        # Simulate price movement
        price_change = np.random.randn() * 1000
        open_price = base_price + price_change
        close_price = open_price + np.random.randn() * 500
        high_price = max(open_price, close_price) + abs(np.random.randn() * 200)
        low_price = min(open_price, close_price) - abs(np.random.randn() * 200)
        volume = abs(np.random.randn() * 1000000)
        
        ohlc = OHLCData(
            timestamp=base_time + timedelta(hours=i),
            symbol="BTC",
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume
        )
        sample_data.append(ohlc)
        base_price = close_price
    
    # Process data
    processor = DataProcessor()
    df = processor.process_ohlc_data(sample_data, "BTC")
    signals = processor.generate_signals(df, "BTC")
    summary = processor.get_market_summary("BTC")
    
    print(f"Processed {len(df)} data points")
    print(f"Generated {len(signals)} signals")
    print(f"Latest signal: {signals[-1] if signals else 'None'}")
    print(f"Market summary: {summary}")


if __name__ == "__main__":
    test_processor()