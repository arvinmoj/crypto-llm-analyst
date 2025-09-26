"""
RAG (Retrieval-Augmented Generation) system for cryptocurrency analysis.
"""

import os
import logging
from typing import List, Dict, Optional, Any, Tuple
import asyncio
from datetime import datetime
from dataclasses import dataclass
import json

# Vector store and embeddings
import numpy as np
from sentence_transformers import SentenceTransformer

# LangChain components
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeDocument:
    """Represents a knowledge document in the RAG system"""
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    doc_id: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if not self.doc_id:
            import hashlib
            self.doc_id = hashlib.md5(self.content.encode()).hexdigest()[:12]


@dataclass
class RAGQuery:
    """Represents a query to the RAG system"""
    query: str
    context: Dict[str, Any] = None
    max_results: int = 5
    similarity_threshold: float = 0.7
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class RAGResponse:
    """Response from the RAG system"""
    query: str
    answer: str
    sources: List[KnowledgeDocument]
    confidence: float
    processing_time: float


class CryptoKnowledgeBase:
    """Knowledge base for cryptocurrency information"""
    
    def __init__(self):
        self.documents = {}
        self.default_documents = self._get_default_crypto_knowledge()
    
    def _get_default_crypto_knowledge(self) -> List[Dict[str, str]]:
        """Default cryptocurrency knowledge documents"""
        return [
            {
                "content": """Bitcoin (BTC) is the first and largest cryptocurrency by market capitalization. 
                It was created by Satoshi Nakamoto in 2009 as a peer-to-peer electronic cash system. 
                Bitcoin uses a proof-of-work consensus mechanism and has a maximum supply of 21 million coins. 
                It's often considered digital gold and a store of value.""",
                "title": "Bitcoin Basics",
                "category": "fundamentals",
                "symbol": "BTC"
            },
            {
                "content": """Technical analysis in cryptocurrency trading involves studying price charts and patterns 
                to predict future price movements. Key indicators include RSI (Relative Strength Index), 
                MACD (Moving Average Convergence Divergence), Bollinger Bands, and support/resistance levels. 
                RSI above 70 indicates overbought conditions, while RSI below 30 indicates oversold conditions.""",
                "title": "Technical Analysis Fundamentals",
                "category": "analysis",
                "symbol": "general"
            },
            {
                "content": """Risk management is crucial in cryptocurrency trading. Key principles include: 
                position sizing (never risk more than 2-3% per trade), stop-loss orders, 
                diversification across different assets, and avoiding FOMO (Fear of Missing Out). 
                Value at Risk (VaR) calculations help quantify potential losses.""",
                "title": "Risk Management in Crypto Trading",
                "category": "risk_management",
                "symbol": "general"
            },
            {
                "content": """Market sentiment analysis involves gauging the overall mood of investors and traders. 
                Key sources include social media sentiment, news analysis, on-chain metrics, and funding rates. 
                Extreme fear often presents buying opportunities, while extreme greed suggests caution. 
                The Fear & Greed Index is a popular sentiment indicator.""",
                "title": "Market Sentiment Analysis",
                "category": "sentiment",
                "symbol": "general"
            },
            {
                "content": """Ethereum (ETH) is the second-largest cryptocurrency and a smart contract platform. 
                It transitioned from proof-of-work to proof-of-stake in 2022 (The Merge). 
                Ethereum hosts thousands of decentralized applications (DApps) and is the foundation 
                for DeFi (Decentralized Finance) and NFTs (Non-Fungible Tokens).""",
                "title": "Ethereum Overview",
                "category": "fundamentals",
                "symbol": "ETH"
            },
            {
                "content": """On-chain analysis involves studying blockchain data to understand network activity 
                and investor behavior. Key metrics include active addresses, transaction volume, 
                network value to transactions (NVT) ratio, and whale movements. 
                These metrics can provide insights into adoption and market trends.""",
                "title": "On-Chain Analysis",
                "category": "analysis",
                "symbol": "general"
            }
        ]
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> KnowledgeDocument:
        """Add a document to the knowledge base"""
        doc = KnowledgeDocument(content=content, metadata=metadata)
        self.documents[doc.doc_id] = doc
        return doc
    
    def get_documents_by_category(self, category: str) -> List[KnowledgeDocument]:
        """Get documents by category"""
        return [
            doc for doc in self.documents.values()
            if doc.metadata.get('category') == category
        ]
    
    def load_default_knowledge(self):
        """Load default cryptocurrency knowledge"""
        for doc_data in self.default_documents:
            content = doc_data.pop('content')
            self.add_document(content, doc_data)
    
    def export_knowledge(self, filename: str):
        """Export knowledge base to JSON file"""
        data = {
            doc.doc_id: {
                'content': doc.content,
                'metadata': doc.metadata,
                'timestamp': doc.timestamp.isoformat()
            }
            for doc in self.documents.values()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Knowledge base exported to {filename}")
    
    def import_knowledge(self, filename: str):
        """Import knowledge base from JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            for doc_id, doc_data in data.items():
                content = doc_data['content']
                metadata = doc_data['metadata']
                doc = KnowledgeDocument(content=content, metadata=metadata)
                doc.doc_id = doc_id
                doc.timestamp = datetime.fromisoformat(doc_data['timestamp'])
                self.documents[doc_id] = doc
            
            logger.info(f"Knowledge base imported from {filename}")
        except Exception as e:
            logger.error(f"Failed to import knowledge base: {e}")


class RAGEmbeddingModel:
    """Embedding model for RAG system"""
    
    def __init__(self, model_type: str = "openai"):
        self.model_type = model_type
        
        if model_type == "openai":
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        else:  # Default to HuggingFace
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        return self.embeddings.embed_documents(documents)
    
    def embed_query(self, query: str) -> List[float]:
        """Embed a single query"""
        return self.embeddings.embed_query(query)


class CryptoRAGSystem:
    """Complete RAG system for cryptocurrency analysis"""
    
    def __init__(self, embedding_model_type: str = "huggingface"):
        self.knowledge_base = CryptoKnowledgeBase()
        self.embedding_model = RAGEmbeddingModel(embedding_model_type)
        self.vector_store = None
        self.retrieval_chain = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # Initialize with default knowledge
        self.knowledge_base.load_default_knowledge()
    
    def _create_langchain_documents(self) -> List[Document]:
        """Convert knowledge documents to LangChain documents"""
        documents = []
        
        for doc in self.knowledge_base.documents.values():
            # Split long documents into chunks
            chunks = self.text_splitter.split_text(doc.content)
            
            for i, chunk in enumerate(chunks):
                metadata = doc.metadata.copy()
                metadata.update({
                    'doc_id': doc.doc_id,
                    'chunk_id': f"{doc.doc_id}_{i}",
                    'timestamp': doc.timestamp.isoformat(),
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                })
                
                documents.append(Document(
                    page_content=chunk,
                    metadata=metadata
                ))
        
        return documents
    
    def build_vector_store(self):
        """Build the vector store from knowledge documents"""
        try:
            documents = self._create_langchain_documents()
            
            if not documents:
                logger.warning("No documents found to build vector store")
                return
            
            # Create FAISS vector store
            self.vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embedding_model.embeddings
            )
            
            logger.info(f"Vector store built with {len(documents)} document chunks")
            
        except Exception as e:
            logger.error(f"Failed to build vector store: {e}")
            raise
    
    def setup_retrieval_chain(self, llm_model: str = "gpt-3.5-turbo"):
        """Setup the retrieval QA chain"""
        if self.vector_store is None:
            self.build_vector_store()
        
        # Create retriever
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Create LLM
        llm = OpenAI(
            model_name=llm_model,
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create custom prompt template
        template = """You are an expert cryptocurrency analyst. Use the following context to answer questions about cryptocurrency trading, analysis, and market conditions.

Context: {context}

Question: {question}

Provide a detailed, accurate answer based on the context. If the context doesn't contain enough information, clearly state what information is missing.

Answer:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Create retrieval chain
        self.retrieval_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        
        logger.info("Retrieval chain setup complete")
    
    async def query(self, rag_query: RAGQuery) -> RAGResponse:
        """Query the RAG system"""
        start_time = datetime.now()
        
        try:
            if self.retrieval_chain is None:
                self.setup_retrieval_chain()
            
            # Execute the query
            result = await asyncio.to_thread(
                self.retrieval_chain,
                {"query": rag_query.query}
            )
            
            # Process source documents
            source_docs = []
            for doc in result.get("source_documents", []):
                knowledge_doc = KnowledgeDocument(
                    content=doc.page_content,
                    metadata=doc.metadata
                )
                source_docs.append(knowledge_doc)
            
            # Calculate confidence (simple heuristic)
            confidence = min(0.9, len(source_docs) * 0.15 + 0.3)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return RAGResponse(
                query=rag_query.query,
                answer=result["result"],
                sources=source_docs,
                confidence=confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return RAGResponse(
                query=rag_query.query,
                answer=f"I apologize, but I encountered an error while processing your query: {str(e)}",
                sources=[],
                confidence=0.0,
                processing_time=processing_time
            )
    
    def add_market_update(self, symbol: str, analysis: Dict[str, Any]):
        """Add real-time market analysis to knowledge base"""
        content = f"""
        Market Analysis for {symbol} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:
        
        Current Price: ${analysis.get('current_price', 'N/A')}
        Price Change (24h): {analysis.get('price_change_pct', 'N/A')}%
        Volume: {analysis.get('volume', 'N/A')}
        RSI: {analysis.get('rsi', 'N/A')}
        
        Technical Analysis: {analysis.get('technical_summary', 'No summary available')}
        Market Sentiment: {analysis.get('sentiment', 'Neutral')}
        Risk Level: {analysis.get('risk_level', 'Unknown')}
        
        Key Insights:
        {chr(10).join([f"- {insight}" for insight in analysis.get('insights', [])])}
        """
        
        metadata = {
            'title': f'{symbol} Market Update',
            'category': 'market_update',
            'symbol': symbol,
            'data_type': 'real_time_analysis',
            'source': 'system_generated'
        }
        
        self.knowledge_base.add_document(content, metadata)
        
        # Rebuild vector store to include new document
        self.build_vector_store()
        
        logger.info(f"Added market update for {symbol} to knowledge base")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        return {
            'total_documents': len(self.knowledge_base.documents),
            'vector_store_size': self.vector_store.index.ntotal if self.vector_store else 0,
            'categories': list(set(
                doc.metadata.get('category', 'unknown') 
                for doc in self.knowledge_base.documents.values()
            )),
            'symbols_covered': list(set(
                doc.metadata.get('symbol', 'unknown') 
                for doc in self.knowledge_base.documents.values()
                if doc.metadata.get('symbol') != 'general'
            )),
            'embedding_model': self.embedding_model.model_type,
            'last_updated': max(
                doc.timestamp for doc in self.knowledge_base.documents.values()
            ).isoformat() if self.knowledge_base.documents else None
        }


# Example usage
async def main():
    """Example usage of the RAG system"""
    # Initialize RAG system
    rag_system = CryptoRAGSystem()
    
    # Example queries
    queries = [
        "What is Bitcoin and why is it valuable?",
        "How do I analyze cryptocurrency using technical indicators?",
        "What are the key risk management principles for crypto trading?",
        "How does market sentiment affect cryptocurrency prices?"
    ]
    
    for query_text in queries:
        print(f"\n=== Query: {query_text} ===")
        
        query = RAGQuery(query=query_text, max_results=3)
        response = await rag_system.query(query)
        
        print(f"Answer: {response.answer}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Processing time: {response.processing_time:.2f}s")
        print(f"Sources: {len(response.sources)}")
        
        for i, source in enumerate(response.sources[:2]):  # Show first 2 sources
            print(f"  Source {i+1}: {source.metadata.get('title', 'Unknown')}")
    
    # Show system stats
    stats = rag_system.get_system_stats()
    print(f"\n=== RAG System Stats ===")
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())