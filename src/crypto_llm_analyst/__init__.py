"""Crypto LLM Analyst - LLM-Powered Applications for OHLC Data Analysis."""

__version__ = "0.1.0"
__author__ = "arvin"
__description__ = "LLM-Powered Applications for OHLC Data Analysis"

from .data_sources import BitqueryClient
from .database import SupabaseManager
from .llm import LangChainManager
from .rag import RAGSystem
from .mcp import MCPProtocol

__all__ = [
    "BitqueryClient",
    "SupabaseManager", 
    "LangChainManager",
    "RAGSystem",
    "MCPProtocol",
]