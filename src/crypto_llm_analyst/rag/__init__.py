"""RAG (Retrieval-Augmented Generation) system for cryptocurrency analysis."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.retrievers import VectorStoreRetriever
import chromadb

logger = logging.getLogger(__name__)


class CryptoRAGSystem:
    """RAG system for cryptocurrency analysis with vector embeddings."""
    
    def __init__(
        self,
        openai_api_key: str,
        chroma_persist_directory: str = "./chroma_db",
        collection_name: str = "crypto_analysis"
    ):
        """Initialize RAG system.
        
        Args:
            openai_api_key: OpenAI API key for embeddings
            chroma_persist_directory: Directory for persistent vector storage
            collection_name: Name of the Chroma collection
        """
        self.openai_api_key = openai_api_key
        self.persist_directory = chroma_persist_directory
        self.collection_name = collection_name
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key,
            model="text-embedding-ada-002"
        )
        
        # Initialize Chroma vector store
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=chroma_persist_directory
        )
        
        # Initialize retriever
        self.retriever = VectorStoreRetriever(
            vectorstore=self.vectorstore,
            search_kwargs={"k": 5}  # Retrieve top 5 most relevant documents
        )
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
    
    async def index_ohlc_data(
        self,
        ohlc_data: pd.DataFrame,
        symbol: str = "BTCUSDT"
    ) -> int:
        """Index OHLC data into vector store for retrieval.
        
        Args:
            ohlc_data: OHLC data to index
            symbol: Trading symbol
            
        Returns:
            Number of documents indexed
        """
        try:
            documents = []
            
            # Create documents from OHLC data chunks
            chunk_size = 10  # Process 10 OHLC records at a time
            for i in range(0, len(ohlc_data), chunk_size):
                chunk = ohlc_data.iloc[i:i+chunk_size]
                
                if chunk.empty:
                    continue
                
                # Create text content from OHLC chunk
                content = self._create_ohlc_content(chunk, symbol)
                
                # Create metadata
                metadata = {
                    "type": "ohlc_data",
                    "symbol": symbol,
                    "start_time": chunk['timestamp'].min().isoformat(),
                    "end_time": chunk['timestamp'].max().isoformat(),
                    "record_count": len(chunk),
                    "avg_price": float(chunk['close'].mean()),
                    "price_range": f"{float(chunk['low'].min())}-{float(chunk['high'].max())}",
                    "total_volume": float(chunk['volume'].sum()),
                    "indexed_at": datetime.now().isoformat()
                }
                
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                documents.append(doc)
            
            # Add documents to vector store
            if documents:
                self.vectorstore.add_documents(documents)
                self.vectorstore.persist()
                
                logger.info(f"Indexed {len(documents)} OHLC document chunks for {symbol}")
                return len(documents)
            else:
                logger.warning("No documents created from OHLC data")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to index OHLC data: {e}")
            return 0
    
    async def index_analysis_results(
        self,
        analysis_results: List[Dict[str, Any]]
    ) -> int:
        """Index LLM analysis results into vector store.
        
        Args:
            analysis_results: List of analysis result dictionaries
            
        Returns:
            Number of documents indexed
        """
        try:
            documents = []
            
            for result in analysis_results:
                # Create content from analysis
                content = self._create_analysis_content(result)
                
                # Create metadata
                metadata = {
                    "type": "analysis_result",
                    "symbol": result.get("symbol", "UNKNOWN"),
                    "analysis_type": result.get("analysis_type", "general"),
                    "timestamp": result.get("timestamp", datetime.now().isoformat()),
                    "confidence": result.get("confidence", 0.0),
                    "query": result.get("query", ""),
                    "indexed_at": datetime.now().isoformat()
                }
                
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                documents.append(doc)
            
            # Add documents to vector store
            if documents:
                self.vectorstore.add_documents(documents)
                self.vectorstore.persist()
                
                logger.info(f"Indexed {len(documents)} analysis result documents")
                return len(documents)
            else:
                logger.warning("No documents created from analysis results")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to index analysis results: {e}")
            return 0
    
    async def index_market_knowledge(
        self,
        knowledge_texts: List[str],
        metadata_list: Optional[List[Dict]] = None
    ) -> int:
        """Index general cryptocurrency market knowledge.
        
        Args:
            knowledge_texts: List of knowledge text content
            metadata_list: Optional metadata for each text
            
        Returns:
            Number of documents indexed
        """
        try:
            documents = []
            
            for i, text in enumerate(knowledge_texts):
                # Split text into chunks
                chunks = self.text_splitter.split_text(text)
                
                for j, chunk in enumerate(chunks):
                    metadata = {
                        "type": "market_knowledge",
                        "source_index": i,
                        "chunk_index": j,
                        "indexed_at": datetime.now().isoformat()
                    }
                    
                    # Add custom metadata if provided
                    if metadata_list and i < len(metadata_list):
                        metadata.update(metadata_list[i])
                    
                    doc = Document(
                        page_content=chunk,
                        metadata=metadata
                    )
                    documents.append(doc)
            
            # Add documents to vector store
            if documents:
                self.vectorstore.add_documents(documents)
                self.vectorstore.persist()
                
                logger.info(f"Indexed {len(documents)} market knowledge documents")
                return len(documents)
            else:
                logger.warning("No documents created from knowledge texts")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to index market knowledge: {e}")
            return 0
    
    async def retrieve_relevant_context(
        self,
        query: str,
        symbol: str = "BTCUSDT",
        max_docs: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Retrieve relevant context for a query.
        
        Args:
            query: User query
            symbol: Trading symbol to focus on
            max_docs: Maximum number of documents to retrieve
            filters: Optional metadata filters
            
        Returns:
            List of relevant documents
        """
        try:
            # Update retriever with current parameters
            self.retriever.search_kwargs["k"] = max_docs
            
            # Add symbol filter if not in custom filters
            if filters is None:
                filters = {"symbol": symbol}
            elif "symbol" not in filters:
                filters["symbol"] = symbol
            
            # Perform retrieval
            docs = self.retriever.get_relevant_documents(query)
            
            # Filter by metadata if needed
            if filters:
                filtered_docs = []
                for doc in docs:
                    match = True
                    for key, value in filters.items():
                        if key not in doc.metadata or doc.metadata[key] != value:
                            match = False
                            break
                    if match:
                        filtered_docs.append(doc)
                docs = filtered_docs
            
            logger.debug(f"Retrieved {len(docs)} relevant documents for query")
            return docs
            
        except Exception as e:
            logger.error(f"Failed to retrieve relevant context: {e}")
            return []
    
    async def get_market_context(
        self,
        query: str,
        time_range_hours: int = 24,
        include_analysis: bool = True
    ) -> str:
        """Get comprehensive market context for a query.
        
        Args:
            query: User query
            time_range_hours: Hours of historical context to include
            include_analysis: Whether to include previous analysis results
            
        Returns:
            Formatted context string
        """
        try:
            # Retrieve relevant documents
            relevant_docs = await self.retrieve_relevant_context(query, max_docs=8)
            
            if not relevant_docs:
                return "No relevant market context found."
            
            # Filter by time range
            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
            recent_docs = []
            
            for doc in relevant_docs:
                doc_time_str = doc.metadata.get("timestamp") or doc.metadata.get("indexed_at")
                if doc_time_str:
                    try:
                        doc_time = datetime.fromisoformat(doc_time_str.replace('Z', '+00:00'))
                        if doc_time >= cutoff_time:
                            recent_docs.append(doc)
                    except ValueError:
                        # Include document if time parsing fails
                        recent_docs.append(doc)
                else:
                    recent_docs.append(doc)
            
            # Organize context by type
            context_sections = {
                "ohlc_data": [],
                "analysis_result": [],
                "market_knowledge": []
            }
            
            for doc in recent_docs:
                doc_type = doc.metadata.get("type", "unknown")
                if doc_type in context_sections:
                    context_sections[doc_type].append(doc)
            
            # Build formatted context
            context = self._format_context_sections(context_sections, include_analysis)
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get market context: {e}")
            return f"Error retrieving market context: {str(e)}"
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.7
    ) -> List[Tuple[Document, float]]:
        """Perform similarity search with scores.
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of (document, score) tuples
        """
        try:
            # Perform similarity search with scores
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            # Filter by score threshold
            filtered_results = [
                (doc, score) for doc, score in results 
                if score >= score_threshold
            ]
            
            logger.debug(f"Found {len(filtered_results)} similar documents above threshold")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    def _create_ohlc_content(self, ohlc_chunk: pd.DataFrame, symbol: str) -> str:
        """Create text content from OHLC data chunk."""
        if ohlc_chunk.empty:
            return ""
        
        start_time = ohlc_chunk['timestamp'].min()
        end_time = ohlc_chunk['timestamp'].max()
        
        # Calculate summary statistics
        open_price = ohlc_chunk.iloc[0]['open']
        close_price = ohlc_chunk.iloc[-1]['close']
        high_price = ohlc_chunk['high'].max()
        low_price = ohlc_chunk['low'].min()
        total_volume = ohlc_chunk['volume'].sum()
        avg_price = ohlc_chunk['close'].mean()
        
        # Calculate price change
        price_change = close_price - open_price
        price_change_percent = (price_change / open_price) * 100 if open_price > 0 else 0
        
        content = f"""
        {symbol} Market Data Summary
        Period: {start_time} to {end_time}
        
        Price Action:
        - Opening Price: ${open_price:,.2f}
        - Closing Price: ${close_price:,.2f}
        - Highest Price: ${high_price:,.2f}
        - Lowest Price: ${low_price:,.2f}
        - Average Price: ${avg_price:,.2f}
        - Price Change: ${price_change:,.2f} ({price_change_percent:+.2f}%)
        
        Volume Analysis:
        - Total Volume: {total_volume:,.2f}
        - Average Volume per Period: {total_volume / len(ohlc_chunk):,.2f}
        
        Market Characteristics:
        - Number of 5-minute periods: {len(ohlc_chunk)}
        - Price Volatility: {ohlc_chunk['close'].std():.2f}
        - Trading Range: ${low_price:,.2f} - ${high_price:,.2f}
        """.strip()
        
        return content
    
    def _create_analysis_content(self, analysis_result: Dict[str, Any]) -> str:
        """Create text content from analysis result."""
        query = analysis_result.get("query", "")
        response = analysis_result.get("response", "")
        analysis_type = analysis_result.get("analysis_type", "general")
        confidence = analysis_result.get("confidence", 0.0)
        symbol = analysis_result.get("symbol", "BTCUSDT")
        timestamp = analysis_result.get("timestamp", "")
        
        content = f"""
        Cryptocurrency Analysis Result
        Symbol: {symbol}
        Analysis Type: {analysis_type}
        Timestamp: {timestamp}
        Confidence Score: {confidence:.2f}
        
        Original Query:
        {query}
        
        Analysis Response:
        {response}
        """.strip()
        
        return content
    
    def _format_context_sections(
        self, 
        context_sections: Dict[str, List[Document]], 
        include_analysis: bool
    ) -> str:
        """Format context sections into readable text."""
        context_parts = []
        
        # OHLC Data Section
        if context_sections["ohlc_data"]:
            context_parts.append("=== Recent Market Data ===")
            for doc in context_sections["ohlc_data"][:3]:  # Limit to 3 most relevant
                context_parts.append(doc.page_content)
                context_parts.append("")
        
        # Market Knowledge Section
        if context_sections["market_knowledge"]:
            context_parts.append("=== Market Knowledge ===")
            for doc in context_sections["market_knowledge"][:2]:  # Limit to 2 most relevant
                context_parts.append(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
                context_parts.append("")
        
        # Analysis Results Section
        if include_analysis and context_sections["analysis_result"]:
            context_parts.append("=== Previous Analysis Results ===")
            for doc in context_sections["analysis_result"][:2]:  # Limit to 2 most relevant
                context_parts.append(doc.page_content)
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    async def cleanup_old_data(self, days_to_keep: int = 7) -> int:
        """Clean up old indexed data to manage storage.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Number of documents removed
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_time.isoformat()
            
            # Get all documents
            collection = self.vectorstore._collection
            all_docs = collection.get()
            
            # Find documents to remove
            ids_to_remove = []
            for i, metadata in enumerate(all_docs['metadatas']):
                indexed_time_str = metadata.get('indexed_at', '')
                if indexed_time_str and indexed_time_str < cutoff_str:
                    ids_to_remove.append(all_docs['ids'][i])
            
            # Remove old documents
            if ids_to_remove:
                collection.delete(ids=ids_to_remove)
                self.vectorstore.persist()
                
                logger.info(f"Removed {len(ids_to_remove)} old documents")
                return len(ids_to_remove)
            else:
                logger.info("No old documents found for cleanup")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0


# Convenience class for RAG system integration
class RAGSystem(CryptoRAGSystem):
    """Alias for CryptoRAGSystem for backward compatibility."""
    pass


# Example usage
async def example_usage():
    """Example of how to use CryptoRAGSystem."""
    import os
    from datetime import datetime, timedelta
    
    # Initialize RAG system
    rag = CryptoRAGSystem(
        openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        chroma_persist_directory="./example_chroma",
        collection_name="crypto_test"
    )
    
    # Sample OHLC data
    timestamps = [datetime.now() - timedelta(minutes=5*i) for i in range(20, 0, -1)]
    sample_ohlc = pd.DataFrame({
        'timestamp': timestamps,
        'open': [45000 + i*10 for i in range(20)],
        'high': [45100 + i*10 for i in range(20)],
        'low': [44900 + i*10 for i in range(20)],
        'close': [45050 + i*10 for i in range(20)],
        'volume': [1000 + i*50 for i in range(20)]
    })
    
    # Index OHLC data
    indexed_count = await rag.index_ohlc_data(sample_ohlc, "BTCUSDT")
    print(f"Indexed {indexed_count} OHLC document chunks")
    
    # Sample analysis results
    sample_analyses = [
        {
            "symbol": "BTCUSDT",
            "analysis_type": "technical",
            "query": "What's the trend direction?",
            "response": "The trend appears bullish with higher highs and higher lows.",
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    # Index analysis results
    analysis_count = await rag.index_analysis_results(sample_analyses)
    print(f"Indexed {analysis_count} analysis documents")
    
    # Retrieve relevant context
    query = "What's the current Bitcoin price trend?"
    context = await rag.get_market_context(query, time_range_hours=2)
    print(f"Retrieved context:\n{context}")
    
    # Perform similarity search
    similar_docs = await rag.similarity_search(query, k=3, score_threshold=0.5)
    print(f"Found {len(similar_docs)} similar documents")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())