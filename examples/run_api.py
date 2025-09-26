#!/usr/bin/env python3
"""
Run the FastAPI server for the crypto LLM analyst API.
"""

import asyncio
import logging
import os
import sys
import uvicorn

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from crypto_llm_analyst.main import CryptoLLMAnalyst, load_config_from_env
from crypto_llm_analyst.api import app, set_crypto_system

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def startup_system():
    """Initialize and start the crypto system."""
    config = load_config_from_env()
    
    # Create and initialize system
    system = CryptoLLMAnalyst(config)
    success = await system.initialize()
    
    if not success:
        logger.error("Failed to initialize crypto system")
        return None
    
    # Start data streaming if enabled
    if config.get("enable_streaming", True) and system.data_source:
        await system.start_data_streaming()
    
    # Setup N8N workflows if enabled
    if config.get("enable_n8n", False) and system.n8n_manager:
        await system.setup_n8n_workflows()
    
    # Set system in FastAPI app
    set_crypto_system(system)
    
    return system


def main():
    """Main function to run the API server."""
    config = load_config_from_env()
    
    # Validate required configuration
    if not config.get("openai_api_key"):
        logger.error("OPENAI_API_KEY environment variable is required")
        sys.exit(1)
    
    # Initialize system
    logger.info("🚀 Starting Crypto LLM Analyst API Server...")
    
    # Note: In a production setup, you'd want to handle system initialization
    # in FastAPI's lifespan events. For this example, we'll start it manually.
    
    # Get server configuration
    host = config.get("api_host", "0.0.0.0")
    port = config.get("api_port", 8000)
    
    logger.info(f"Server will be available at: http://{host}:{port}")
    logger.info("API documentation: http://localhost:8000/docs")
    
    # Run the FastAPI server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        reload=False  # Set to True for development
    )


if __name__ == "__main__":
    main()