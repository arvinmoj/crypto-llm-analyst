"""Main application orchestrator for the crypto LLM analyst system."""

import asyncio
import logging
import os
from typing import Optional
from contextlib import asynccontextmanager

from .data_sources import BitqueryClient
from .database import SupabaseManager
from .llm import LangChainManager
from .rag import CryptoRAGSystem
from .mcp import MCPProtocol
from .workflows import N8NManager
from .api import app, set_crypto_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CryptoLLMAnalyst:
    """Main orchestrator for the crypto LLM analyst system."""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize the crypto LLM analyst system.
        
        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config or {}
        
        # Initialize components
        self.data_source: Optional[BitqueryClient] = None
        self.database: Optional[SupabaseManager] = None
        self.llm_manager: Optional[LangChainManager] = None
        self.rag_system: Optional[CryptoRAGSystem] = None
        self.mcp_protocol: Optional[MCPProtocol] = None
        self.n8n_manager: Optional[N8NManager] = None
        
        # Component status
        self.components_initialized = False
        self.data_streaming = False
    
    async def initialize(self) -> bool:
        """Initialize all system components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing Crypto LLM Analyst system...")
            
            # Initialize database
            if self.config.get("supabase_url") and self.config.get("supabase_key"):
                self.database = SupabaseManager(
                    url=self.config["supabase_url"],
                    key=self.config["supabase_key"],
                    db_url=self.config.get("database_url")
                )
                
                # Create necessary tables
                await self.database.create_ohlc_table()
                await self.database.create_analysis_table()
                logger.info("Database initialized")
            else:
                logger.warning("Supabase credentials not provided, skipping database initialization")
            
            # Initialize LLM manager
            if self.config.get("openai_api_key"):
                self.llm_manager = LangChainManager(
                    openai_api_key=self.config["openai_api_key"],
                    model=self.config.get("openai_model", "gpt-4"),
                    temperature=self.config.get("temperature", 0.7)
                )
                logger.info("LLM manager initialized")
            else:
                logger.warning("OpenAI API key not provided, skipping LLM initialization")
            
            # Initialize RAG system
            if self.config.get("openai_api_key"):
                self.rag_system = CryptoRAGSystem(
                    openai_api_key=self.config["openai_api_key"],
                    chroma_persist_directory=self.config.get("chroma_db_path", "./chroma_db")
                )
                logger.info("RAG system initialized")
            else:
                logger.warning("OpenAI API key not provided, skipping RAG initialization")
            
            # Initialize data source
            if self.config.get("bitquery_api_key"):
                self.data_source = BitqueryClient(
                    api_key=self.config["bitquery_api_key"],
                    websocket_url=self.config.get("bitquery_websocket_url", "wss://streaming.bitquery.io/graphql")
                )
                
                # Set up data callback
                if self.database:
                    self.data_source.add_callback(self._handle_ohlc_data)
                
                logger.info("Data source initialized")
            else:
                logger.warning("Bitquery API key not provided, skipping data source initialization")
            
            # Initialize MCP protocol
            self.mcp_protocol = MCPProtocol("crypto-llm-analyst")
            self.mcp_protocol.set_connectors(
                data_source=self.data_source,
                database=self.database,
                llm_manager=self.llm_manager,
                rag_system=self.rag_system
            )
            logger.info("MCP protocol initialized")
            
            # Initialize N8N manager
            if self.config.get("n8n_url"):
                self.n8n_manager = N8NManager(
                    n8n_url=self.config["n8n_url"],
                    api_key=self.config.get("n8n_api_key"),
                    webhook_url=self.config.get("n8n_webhook_url")
                )
                self.n8n_manager.set_crypto_system(self)
                logger.info("N8N manager initialized")
            else:
                logger.warning("N8N URL not provided, skipping N8N initialization")
            
            self.components_initialized = True
            logger.info("✅ Crypto LLM Analyst system initialized successfully")
            
            # Set system in FastAPI app
            set_crypto_system(self)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize system: {e}")
            return False
    
    async def start_data_streaming(self) -> bool:
        """Start real-time data streaming.
        
        Returns:
            True if streaming started successfully, False otherwise
        """
        if not self.data_source:
            logger.warning("Data source not initialized, cannot start streaming")
            return False
        
        try:
            await self.data_source.connect()
            
            # Start streaming in background task
            asyncio.create_task(self._streaming_task())
            
            self.data_streaming = True
            logger.info("🔄 Started real-time data streaming")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start data streaming: {e}")
            return False
    
    async def stop_data_streaming(self) -> None:
        """Stop real-time data streaming."""
        if self.data_source and self.data_streaming:
            try:
                await self.data_source.disconnect()
                self.data_streaming = False
                logger.info("⏹️ Stopped data streaming")
            except Exception as e:
                logger.error(f"Error stopping data streaming: {e}")
    
    async def _streaming_task(self) -> None:
        """Background task for data streaming."""
        try:
            if self.data_source:
                await self.data_source.subscribe_btcusdt_5min()
        except Exception as e:
            logger.error(f"Streaming task error: {e}")
            self.data_streaming = False
    
    async def _handle_ohlc_data(self, ohlc_data: dict) -> None:
        """Handle incoming OHLC data.
        
        Args:
            ohlc_data: OHLC data from BitQuery
        """
        try:
            # Store in database
            if self.database:
                await self.database.insert_ohlc_data(ohlc_data)
            
            # Index in RAG system
            if self.rag_system and self.database:
                # Get recent data for indexing
                recent_data = await self.database.get_latest_ohlc(
                    ohlc_data["symbol"], 
                    limit=10
                )
                if not recent_data.empty:
                    await self.rag_system.index_ohlc_data(recent_data, ohlc_data["symbol"])
            
            # Notify MCP subscribers
            if self.mcp_protocol:
                await self.mcp_protocol.notify_subscribers(
                    f"crypto://market/{ohlc_data['symbol']}/ohlc",
                    ohlc_data
                )
            
            logger.debug(f"Processed OHLC data for {ohlc_data['symbol']}")
            
        except Exception as e:
            logger.error(f"Error handling OHLC data: {e}")
    
    async def setup_n8n_workflows(self) -> bool:
        """Set up N8N workflows for automation.
        
        Returns:
            True if workflows created successfully, False otherwise
        """
        if not self.n8n_manager:
            logger.warning("N8N manager not initialized")
            return False
        
        try:
            async with self.n8n_manager:
                workflow_ids = await self.n8n_manager.setup_crypto_workflows()
                logger.info(f"✅ Created {len(workflow_ids)} N8N workflows")
                return len(workflow_ids) > 0
                
        except Exception as e:
            logger.error(f"❌ Failed to setup N8N workflows: {e}")
            return False
    
    async def analyze_market(
        self, 
        symbol: str = "BTCUSDT",
        query: str = "Analyze current market conditions",
        analysis_type: str = "general"
    ) -> dict:
        """Perform market analysis.
        
        Args:
            symbol: Trading symbol
            query: Analysis query
            analysis_type: Type of analysis
            
        Returns:
            Analysis result dictionary
        """
        try:
            if not self.llm_manager or not self.database:
                raise ValueError("LLM manager or database not initialized")
            
            # Get market data
            market_data = await self.database.get_market_summary(symbol)
            ohlc_data = await self.database.get_latest_ohlc(symbol, 50)
            
            # Perform analysis based on type
            if analysis_type == "market":
                result, confidence = await self.llm_manager.analyze_market(
                    query, market_data, ohlc_data
                )
            elif analysis_type == "prediction":
                result, confidence = await self.llm_manager.predict_price(query, ohlc_data)
            elif analysis_type == "technical":
                result, confidence = await self.llm_manager.technical_analysis(query, ohlc_data)
            else:
                result = await self.llm_manager.general_query(query, market_data)
                confidence = 0.8
            
            # Store analysis result
            await self.database.save_analysis(
                symbol, analysis_type, query, result, confidence
            )
            
            return {
                "analysis": result,
                "confidence": confidence,
                "symbol": symbol,
                "analysis_type": analysis_type,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return {"error": str(e)}
    
    async def get_market_summary(self, symbol: str = "BTCUSDT") -> dict:
        """Get market summary for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Market summary dictionary
        """
        try:
            if not self.database:
                raise ValueError("Database not initialized")
            
            return await self.database.get_market_summary(symbol)
            
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_data(self, days_to_keep: int = 7) -> dict:
        """Clean up old data across all systems.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Cleanup results
        """
        results = {}
        
        try:
            # Cleanup RAG system
            if self.rag_system:
                rag_cleaned = await self.rag_system.cleanup_old_data(days_to_keep)
                results["rag_documents_removed"] = rag_cleaned
            
            # Note: Database cleanup would require SQL operations
            # This could be implemented as a scheduled task
            
            logger.info(f"Cleanup completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}
    
    def get_system_status(self) -> dict:
        """Get system component status.
        
        Returns:
            Status dictionary
        """
        return {
            "components_initialized": self.components_initialized,
            "data_streaming": self.data_streaming,
            "database": self.database is not None,
            "llm_manager": self.llm_manager is not None,
            "data_source": self.data_source is not None,
            "rag_system": self.rag_system is not None,
            "mcp_protocol": self.mcp_protocol is not None,
            "n8n_manager": self.n8n_manager is not None
        }
    
    async def shutdown(self) -> None:
        """Shutdown the system gracefully."""
        logger.info("🔄 Shutting down Crypto LLM Analyst system...")
        
        try:
            # Stop data streaming
            await self.stop_data_streaming()
            
            # Close N8N manager
            if self.n8n_manager and hasattr(self.n8n_manager, 'session') and self.n8n_manager.session:
                await self.n8n_manager.session.close()
            
            logger.info("✅ System shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


@asynccontextmanager
async def create_crypto_system(config: dict):
    """Context manager for creating and managing crypto system.
    
    Args:
        config: System configuration
        
    Yields:
        CryptoLLMAnalyst instance
    """
    system = CryptoLLMAnalyst(config)
    
    try:
        await system.initialize()
        yield system
    finally:
        await system.shutdown()


def load_config_from_env() -> dict:
    """Load configuration from environment variables.
    
    Returns:
        Configuration dictionary
    """
    return {
        # API Keys
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "bitquery_api_key": os.getenv("BITQUERY_API_KEY"),
        "supabase_url": os.getenv("SUPABASE_URL"),
        "supabase_key": os.getenv("SUPABASE_KEY"),
        "n8n_api_key": os.getenv("N8N_API_KEY"),
        
        # URLs
        "database_url": os.getenv("DATABASE_URL"),
        "bitquery_websocket_url": os.getenv("BITQUERY_WEBSOCKET_URL"),
        "n8n_url": os.getenv("N8N_URL", "http://localhost:5678"),
        "n8n_webhook_url": os.getenv("N8N_WEBHOOK_URL"),
        
        # Settings
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4"),
        "temperature": float(os.getenv("TEMPERATURE", "0.7")),
        "chroma_db_path": os.getenv("CHROMA_DB_PATH", "./chroma_db"),
        
        # Server settings
        "api_host": os.getenv("API_HOST", "0.0.0.0"),
        "api_port": int(os.getenv("API_PORT", "8000")),
        "enable_streaming": os.getenv("ENABLE_STREAMING", "true").lower() == "true",
        "enable_n8n": os.getenv("ENABLE_N8N", "false").lower() == "true",
    }


async def main():
    """Main function for running the complete system."""
    # Load configuration
    config = load_config_from_env()
    
    # Validate required configuration
    required_keys = ["openai_api_key"]
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        logger.error(f"❌ Missing required configuration: {missing_keys}")
        logger.info("Please set the following environment variables:")
        for key in missing_keys:
            logger.info(f"  {key.upper()}")
        return
    
    # Create and run system
    async with create_crypto_system(config) as system:
        logger.info("🚀 Crypto LLM Analyst system is running")
        
        # Start data streaming if enabled
        if config.get("enable_streaming", True):
            await system.start_data_streaming()
        
        # Setup N8N workflows if enabled
        if config.get("enable_n8n", False):
            await system.setup_n8n_workflows()
        
        # Print system status
        status = system.get_system_status()
        logger.info(f"📊 System Status: {status}")
        
        # Keep running (in a real deployment, this would run the API server)
        logger.info("System ready. Press Ctrl+C to shutdown.")
        try:
            while True:
                await asyncio.sleep(60)  # Status check every minute
                if system.data_streaming:
                    logger.debug("📡 Data streaming active")
        except KeyboardInterrupt:
            logger.info("👋 Received shutdown signal")


if __name__ == "__main__":
    asyncio.run(main())