"""
Main package initialization for crypto-llm-analyst.
"""

__version__ = "1.0.0"
__author__ = "Arvin"
__description__ = "LLM-Powered Applications for OHLC Data Analysis"

# Import main components for easy access
from .config import config
from .ai.langchain_agent import CryptoAnalysisAgent
from .data.bitquery_stream import BitqueryStreamer
from .data.data_processor import DataProcessor

__all__ = [
    "config",
    "CryptoAnalysisAgent", 
    "BitqueryStreamer",
    "DataProcessor"
]