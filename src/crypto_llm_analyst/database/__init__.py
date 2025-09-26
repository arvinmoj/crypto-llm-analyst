"""Supabase database manager for storing and retrieving OHLC data."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from supabase import create_client, Client
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class SupabaseManager:
    """Manager for Supabase database operations."""
    
    def __init__(self, url: str, key: str, db_url: Optional[str] = None):
        """Initialize Supabase manager.
        
        Args:
            url: Supabase project URL
            key: Supabase service role key
            db_url: Optional direct database URL for SQLAlchemy
        """
        self.url = url
        self.key = key
        self.client: Client = create_client(url, key)
        
        # Optional SQLAlchemy engine for advanced queries
        if db_url:
            self.engine = create_engine(db_url)
            self.Session = sessionmaker(bind=self.engine)
        else:
            self.engine = None
            self.Session = None
    
    async def create_ohlc_table(self) -> bool:
        """Create OHLC data table if it doesn't exist.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create table using Supabase client
            result = self.client.table('ohlc_data').select('*').limit(1).execute()
            logger.info("OHLC table already exists")
            return True
        except Exception:
            # Table doesn't exist, create it
            try:
                # Use raw SQL to create table with proper schema
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS ohlc_data (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    timeframe VARCHAR(10) NOT NULL,
                    open DECIMAL(20, 8) NOT NULL,
                    high DECIMAL(20, 8) NOT NULL,
                    low DECIMAL(20, 8) NOT NULL,
                    close DECIMAL(20, 8) NOT NULL,
                    volume DECIMAL(30, 8) NOT NULL,
                    count INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(timestamp, symbol, timeframe)
                );
                
                CREATE INDEX IF NOT EXISTS idx_ohlc_timestamp 
                ON ohlc_data(timestamp DESC);
                
                CREATE INDEX IF NOT EXISTS idx_ohlc_symbol_timeframe 
                ON ohlc_data(symbol, timeframe);
                """
                
                if self.engine:
                    with self.engine.connect() as conn:
                        conn.execute(text(create_table_sql))
                        conn.commit()
                    logger.info("Created OHLC table successfully")
                    return True
                else:
                    logger.warning("Cannot create table without database URL")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to create OHLC table: {e}")
                return False
    
    async def insert_ohlc_data(self, data: Dict[str, Any]) -> bool:
        """Insert OHLC data into the database.
        
        Args:
            data: OHLC data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table('ohlc_data').upsert({
                'timestamp': data['timestamp'],
                'symbol': data['symbol'],
                'timeframe': data['timeframe'],
                'open': str(data['open']),
                'high': str(data['high']),
                'low': str(data['low']),
                'close': str(data['close']),
                'volume': str(data['volume']),
                'count': data.get('count', 0)
            }, on_conflict='timestamp,symbol,timeframe').execute()
            
            logger.debug(f"Inserted OHLC data for {data['symbol']} at {data['timestamp']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert OHLC data: {e}")
            return False
    
    async def get_latest_ohlc(self, symbol: str = "BTCUSDT", limit: int = 100) -> pd.DataFrame:
        """Get latest OHLC data for a symbol.
        
        Args:
            symbol: Trading symbol
            limit: Maximum number of records to retrieve
            
        Returns:
            DataFrame with OHLC data
        """
        try:
            result = self.client.table('ohlc_data')\
                .select('*')\
                .eq('symbol', symbol)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            if result.data:
                df = pd.DataFrame(result.data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                df[numeric_cols] = df[numeric_cols].astype(float)
                return df.sort_values('timestamp')
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to get latest OHLC data: {e}")
            return pd.DataFrame()
    
    async def get_ohlc_range(
        self, 
        symbol: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """Get OHLC data for a specific time range.
        
        Args:
            symbol: Trading symbol
            start_time: Start time
            end_time: End time
            
        Returns:
            DataFrame with OHLC data
        """
        try:
            result = self.client.table('ohlc_data')\
                .select('*')\
                .eq('symbol', symbol)\
                .gte('timestamp', start_time.isoformat())\
                .lte('timestamp', end_time.isoformat())\
                .order('timestamp')\
                .execute()
            
            if result.data:
                df = pd.DataFrame(result.data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                df[numeric_cols] = df[numeric_cols].astype(float)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to get OHLC range: {e}")
            return pd.DataFrame()
    
    async def get_market_summary(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Get market summary statistics.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with market summary
        """
        try:
            # Get latest data point
            latest_result = self.client.table('ohlc_data')\
                .select('*')\
                .eq('symbol', symbol)\
                .order('timestamp', desc=True)\
                .limit(1)\
                .execute()
            
            if not latest_result.data:
                return {}
            
            latest = latest_result.data[0]
            
            # Get 24h data for comparison
            day_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            day_result = self.client.table('ohlc_data')\
                .select('*')\
                .eq('symbol', symbol)\
                .gte('timestamp', day_ago.isoformat())\
                .order('timestamp')\
                .execute()
            
            summary = {
                'symbol': symbol,
                'current_price': float(latest['close']),
                'timestamp': latest['timestamp'],
                'volume_24h': 0.0,
                'high_24h': 0.0,
                'low_24h': 0.0,
                'price_change_24h': 0.0,
                'price_change_percent_24h': 0.0
            }
            
            if day_result.data:
                day_df = pd.DataFrame(day_result.data)
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                day_df[numeric_cols] = day_df[numeric_cols].astype(float)
                
                summary.update({
                    'volume_24h': float(day_df['volume'].sum()),
                    'high_24h': float(day_df['high'].max()),
                    'low_24h': float(day_df['low'].min()),
                })
                
                if len(day_df) > 0:
                    first_price = day_df.iloc[0]['open']
                    price_change = summary['current_price'] - first_price
                    summary.update({
                        'price_change_24h': price_change,
                        'price_change_percent_24h': (price_change / first_price) * 100
                    })
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get market summary: {e}")
            return {}
    
    async def create_analysis_table(self) -> bool:
        """Create table for storing LLM analysis results.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            create_analysis_table_sql = """
            CREATE TABLE IF NOT EXISTS llm_analysis (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                symbol VARCHAR(20) NOT NULL,
                analysis_type VARCHAR(50) NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                confidence DECIMAL(3, 2),
                data_context JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_analysis_timestamp 
            ON llm_analysis(timestamp DESC);
            
            CREATE INDEX IF NOT EXISTS idx_analysis_symbol 
            ON llm_analysis(symbol);
            """
            
            if self.engine:
                with self.engine.connect() as conn:
                    conn.execute(text(create_analysis_table_sql))
                    conn.commit()
                logger.info("Created analysis table successfully")
                return True
            else:
                logger.warning("Cannot create analysis table without database URL")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create analysis table: {e}")
            return False
    
    async def save_analysis(
        self, 
        symbol: str,
        analysis_type: str,
        query: str,
        response: str,
        confidence: Optional[float] = None,
        data_context: Optional[Dict] = None
    ) -> bool:
        """Save LLM analysis result.
        
        Args:
            symbol: Trading symbol
            analysis_type: Type of analysis performed
            query: Original query
            response: LLM response
            confidence: Confidence score
            data_context: Contextual data used
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table('llm_analysis').insert({
                'symbol': symbol,
                'analysis_type': analysis_type,
                'query': query,
                'response': response,
                'confidence': confidence,
                'data_context': data_context or {}
            }).execute()
            
            logger.debug(f"Saved analysis for {symbol}: {analysis_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
            return False
    
    async def get_recent_analysis(
        self, 
        symbol: str = "BTCUSDT", 
        analysis_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent analysis results.
        
        Args:
            symbol: Trading symbol
            analysis_type: Filter by analysis type
            limit: Maximum number of results
            
        Returns:
            List of analysis results
        """
        try:
            query = self.client.table('llm_analysis')\
                .select('*')\
                .eq('symbol', symbol)\
                .order('timestamp', desc=True)\
                .limit(limit)
            
            if analysis_type:
                query = query.eq('analysis_type', analysis_type)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get recent analysis: {e}")
            return []


# Example usage
async def example_usage():
    """Example of how to use SupabaseManager."""
    # Initialize with your Supabase credentials
    manager = SupabaseManager(
        url="https://your-project.supabase.co",
        key="your-service-role-key",
        db_url="postgresql://user:pass@host:5432/dbname"
    )
    
    # Create tables
    await manager.create_ohlc_table()
    await manager.create_analysis_table()
    
    # Insert sample OHLC data
    sample_data = {
        'timestamp': datetime.now().isoformat(),
        'symbol': 'BTCUSDT',
        'timeframe': '5m',
        'open': 45000.0,
        'high': 45100.0,
        'low': 44900.0,
        'close': 45050.0,
        'volume': 1234.56,
        'count': 42
    }
    
    await manager.insert_ohlc_data(sample_data)
    
    # Get latest data
    df = await manager.get_latest_ohlc()
    print(f"Retrieved {len(df)} OHLC records")
    
    # Get market summary
    summary = await manager.get_market_summary()
    print(f"Market summary: {summary}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())