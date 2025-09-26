"""LangChain integration for LLM-powered cryptocurrency analysis."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain.llms.base import LLM
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
import pandas as pd

logger = logging.getLogger(__name__)


class CryptoAnalysisPrompts:
    """Collection of prompts for cryptocurrency analysis."""
    
    MARKET_ANALYSIS = """
    You are an expert cryptocurrency analyst. Analyze the following BTCUSDT market data and provide insights.
    
    Current Market Data:
    {market_data}
    
    Recent OHLC Data:
    {ohlc_data}
    
    Analysis Request: {query}
    
    Please provide a comprehensive analysis including:
    1. Current market sentiment
    2. Technical analysis observations
    3. Price trend analysis
    4. Volume analysis
    5. Key support/resistance levels
    6. Risk assessment
    7. Actionable insights
    
    Format your response in a clear, professional manner suitable for both technical and non-technical users.
    """
    
    PRICE_PREDICTION = """
    Based on the historical OHLC data for BTCUSDT, provide a price prediction analysis.
    
    Historical Data Summary:
    {data_summary}
    
    Recent Trends:
    {trend_analysis}
    
    Question: {query}
    
    Please provide:
    1. Short-term price outlook (1-4 hours)
    2. Medium-term outlook (1-7 days)  
    3. Key factors influencing price
    4. Confidence level of predictions
    5. Risk factors to consider
    
    Be clear about the limitations of predictions and include appropriate disclaimers.
    """
    
    TECHNICAL_INDICATORS = """
    You are analyzing BTCUSDT technical indicators. Use the provided data to answer technical analysis questions.
    
    OHLC Data:
    {ohlc_data}
    
    Calculated Indicators:
    {indicators}
    
    User Query: {query}
    
    Provide technical analysis focusing on:
    1. Moving average signals
    2. Momentum indicators
    3. Volume analysis
    4. Chart patterns
    5. Entry/exit points
    6. Risk management suggestions
    
    Use clear, actionable language appropriate for traders.
    """
    
    GENERAL_CRYPTO_QA = """
    You are a knowledgeable cryptocurrency analyst with access to real-time BTCUSDT data.
    
    Current Market Context:
    {market_context}
    
    User Question: {query}
    
    Provide a helpful, accurate response based on the available data and your knowledge of cryptocurrency markets.
    If the question requires real-time data not available in the context, clearly state this limitation.
    """


class LangChainManager:
    """Manager for LangChain LLM operations and cryptocurrency analysis."""
    
    def __init__(
        self, 
        openai_api_key: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """Initialize LangChain manager.
        
        Args:
            openai_api_key: OpenAI API key
            model: Model to use (gpt-4, gpt-3.5-turbo, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.openai_api_key = openai_api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Initialize memory for conversations
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Initialize prompts
        self.prompts = CryptoAnalysisPrompts()
        
        # Create analysis chains
        self._create_analysis_chains()
    
    def _create_analysis_chains(self) -> None:
        """Create LangChain chains for different analysis types."""
        
        # Market analysis chain
        self.market_analysis_prompt = PromptTemplate(
            input_variables=["market_data", "ohlc_data", "query"],
            template=self.prompts.MARKET_ANALYSIS
        )
        self.market_analysis_chain = LLMChain(
            llm=self.llm,
            prompt=self.market_analysis_prompt
        )
        
        # Price prediction chain
        self.price_prediction_prompt = PromptTemplate(
            input_variables=["data_summary", "trend_analysis", "query"],
            template=self.prompts.PRICE_PREDICTION
        )
        self.price_prediction_chain = LLMChain(
            llm=self.llm,
            prompt=self.price_prediction_prompt
        )
        
        # Technical analysis chain
        self.technical_analysis_prompt = PromptTemplate(
            input_variables=["ohlc_data", "indicators", "query"],
            template=self.prompts.TECHNICAL_INDICATORS
        )
        self.technical_analysis_chain = LLMChain(
            llm=self.llm,
            prompt=self.technical_analysis_prompt
        )
        
        # General Q&A chain
        self.general_qa_prompt = PromptTemplate(
            input_variables=["market_context", "query"],
            template=self.prompts.GENERAL_CRYPTO_QA
        )
        self.general_qa_chain = LLMChain(
            llm=self.llm,
            prompt=self.general_qa_prompt
        )
        
        # Conversation chain with memory
        self.conversation_chain = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            verbose=True
        )
    
    async def analyze_market(
        self, 
        query: str,
        market_data: Dict[str, Any],
        ohlc_data: pd.DataFrame
    ) -> Tuple[str, float]:
        """Perform market analysis based on current data.
        
        Args:
            query: User's analysis request
            market_data: Current market summary
            ohlc_data: Recent OHLC data
            
        Returns:
            Tuple of (analysis_response, confidence_score)
        """
        try:
            # Prepare data for prompt
            market_data_str = self._format_market_data(market_data)
            ohlc_data_str = self._format_ohlc_data(ohlc_data)
            
            # Run analysis
            result = await self.market_analysis_chain.arun(
                market_data=market_data_str,
                ohlc_data=ohlc_data_str,
                query=query
            )
            
            # Calculate confidence score (simplified)
            confidence = self._calculate_confidence(result, len(ohlc_data))
            
            logger.info(f"Completed market analysis with confidence {confidence}")
            return result, confidence
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return f"Analysis failed: {str(e)}", 0.0
    
    async def predict_price(
        self,
        query: str,
        ohlc_data: pd.DataFrame
    ) -> Tuple[str, float]:
        """Generate price predictions based on historical data.
        
        Args:
            query: User's prediction request
            ohlc_data: Historical OHLC data
            
        Returns:
            Tuple of (prediction_response, confidence_score)
        """
        try:
            # Prepare data summaries
            data_summary = self._generate_data_summary(ohlc_data)
            trend_analysis = self._analyze_trends(ohlc_data)
            
            # Run prediction
            result = await self.price_prediction_chain.arun(
                data_summary=data_summary,
                trend_analysis=trend_analysis,
                query=query
            )
            
            confidence = self._calculate_confidence(result, len(ohlc_data))
            
            logger.info(f"Completed price prediction with confidence {confidence}")
            return result, confidence
            
        except Exception as e:
            logger.error(f"Price prediction failed: {e}")
            return f"Prediction failed: {str(e)}", 0.0
    
    async def technical_analysis(
        self,
        query: str,
        ohlc_data: pd.DataFrame,
        indicators: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float]:
        """Perform technical analysis.
        
        Args:
            query: User's technical analysis request
            ohlc_data: OHLC data for analysis
            indicators: Pre-calculated technical indicators
            
        Returns:
            Tuple of (analysis_response, confidence_score)
        """
        try:
            # Calculate basic indicators if not provided
            if indicators is None:
                indicators = self._calculate_basic_indicators(ohlc_data)
            
            ohlc_data_str = self._format_ohlc_data(ohlc_data)
            indicators_str = self._format_indicators(indicators)
            
            result = await self.technical_analysis_chain.arun(
                ohlc_data=ohlc_data_str,
                indicators=indicators_str,
                query=query
            )
            
            confidence = self._calculate_confidence(result, len(ohlc_data))
            
            logger.info(f"Completed technical analysis with confidence {confidence}")
            return result, confidence
            
        except Exception as e:
            logger.error(f"Technical analysis failed: {e}")
            return f"Technical analysis failed: {str(e)}", 0.0
    
    async def general_query(
        self,
        query: str,
        market_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Handle general cryptocurrency questions.
        
        Args:
            query: User's question
            market_context: Optional market context
            
        Returns:
            Response string
        """
        try:
            if market_context:
                context_str = self._format_market_data(market_context)
                result = await self.general_qa_chain.arun(
                    market_context=context_str,
                    query=query
                )
            else:
                result = await self.conversation_chain.arun(input=query)
            
            logger.info("Completed general query")
            return result
            
        except Exception as e:
            logger.error(f"General query failed: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _format_market_data(self, market_data: Dict[str, Any]) -> str:
        """Format market data for prompt inclusion."""
        if not market_data:
            return "No market data available."
        
        return f"""
Symbol: {market_data.get('symbol', 'N/A')}
Current Price: ${market_data.get('current_price', 0):,.2f}
24h High: ${market_data.get('high_24h', 0):,.2f}
24h Low: ${market_data.get('low_24h', 0):,.2f}
24h Volume: {market_data.get('volume_24h', 0):,.2f}
24h Change: ${market_data.get('price_change_24h', 0):,.2f} ({market_data.get('price_change_percent_24h', 0):.2f}%)
Last Updated: {market_data.get('timestamp', 'N/A')}
        """.strip()
    
    def _format_ohlc_data(self, ohlc_data: pd.DataFrame) -> str:
        """Format OHLC data for prompt inclusion."""
        if ohlc_data.empty:
            return "No OHLC data available."
        
        # Get recent data (last 10 records)
        recent_data = ohlc_data.tail(10)
        
        formatted = "Recent OHLC Data:\n"
        formatted += "Timestamp | Open | High | Low | Close | Volume\n"
        formatted += "-" * 60 + "\n"
        
        for _, row in recent_data.iterrows():
            formatted += f"{row['timestamp']} | ${row['open']:,.2f} | ${row['high']:,.2f} | ${row['low']:,.2f} | ${row['close']:,.2f} | {row['volume']:,.2f}\n"
        
        return formatted
    
    def _format_indicators(self, indicators: Dict[str, Any]) -> str:
        """Format technical indicators for prompt inclusion."""
        if not indicators:
            return "No technical indicators calculated."
        
        formatted = "Technical Indicators:\n"
        for key, value in indicators.items():
            if isinstance(value, (int, float)):
                formatted += f"{key}: {value:.4f}\n"
            else:
                formatted += f"{key}: {value}\n"
        
        return formatted
    
    def _generate_data_summary(self, ohlc_data: pd.DataFrame) -> str:
        """Generate summary statistics from OHLC data."""
        if ohlc_data.empty:
            return "No data available for summary."
        
        summary = f"""
Data Period: {ohlc_data['timestamp'].min()} to {ohlc_data['timestamp'].max()}
Total Records: {len(ohlc_data)}
Price Range: ${ohlc_data['low'].min():,.2f} - ${ohlc_data['high'].max():,.2f}
Average Price: ${ohlc_data['close'].mean():,.2f}
Total Volume: {ohlc_data['volume'].sum():,.2f}
Volatility (Close Std): ${ohlc_data['close'].std():,.2f}
        """.strip()
        
        return summary
    
    def _analyze_trends(self, ohlc_data: pd.DataFrame) -> str:
        """Analyze trends in OHLC data."""
        if len(ohlc_data) < 2:
            return "Insufficient data for trend analysis."
        
        # Simple trend analysis
        recent_prices = ohlc_data['close'].tail(10).values
        price_change = recent_prices[-1] - recent_prices[0]
        price_change_percent = (price_change / recent_prices[0]) * 100
        
        trend_direction = "upward" if price_change > 0 else "downward" if price_change < 0 else "sideways"
        
        analysis = f"""
Recent Trend (last 10 periods): {trend_direction}
Price Change: ${price_change:,.2f} ({price_change_percent:.2f}%)
Current Price: ${recent_prices[-1]:,.2f}
Trend Strength: {'Strong' if abs(price_change_percent) > 2 else 'Moderate' if abs(price_change_percent) > 0.5 else 'Weak'}
        """.strip()
        
        return analysis
    
    def _calculate_basic_indicators(self, ohlc_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic technical indicators."""
        if ohlc_data.empty:
            return {}
        
        indicators = {}
        
        # Simple Moving Averages
        if len(ohlc_data) >= 5:
            indicators['SMA_5'] = ohlc_data['close'].tail(5).mean()
        if len(ohlc_data) >= 20:
            indicators['SMA_20'] = ohlc_data['close'].tail(20).mean()
        
        # Current price vs recent average
        current_price = ohlc_data['close'].iloc[-1]
        indicators['current_price'] = current_price
        
        # Volume analysis
        avg_volume = ohlc_data['volume'].mean()
        current_volume = ohlc_data['volume'].iloc[-1]
        indicators['volume_ratio'] = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Price volatility
        if len(ohlc_data) >= 5:
            recent_closes = ohlc_data['close'].tail(5)
            indicators['volatility_5'] = recent_closes.std()
        
        return indicators
    
    def _calculate_confidence(self, response: str, data_points: int) -> float:
        """Calculate confidence score for analysis (simplified).
        
        Args:
            response: LLM response text
            data_points: Number of data points used
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence on data availability
        data_confidence = min(data_points / 100, 1.0)  # More data = higher confidence
        
        # Adjust for response quality indicators
        response_lower = response.lower()
        uncertainty_words = ['uncertain', 'unclear', 'may', 'might', 'possibly', 'perhaps']
        confidence_words = ['confident', 'certain', 'clear', 'strong', 'definite']
        
        uncertainty_count = sum(1 for word in uncertainty_words if word in response_lower)
        confidence_count = sum(1 for word in confidence_words if word in response_lower)
        
        # Adjust confidence based on language used
        language_factor = 1.0 - (uncertainty_count * 0.1) + (confidence_count * 0.1)
        language_factor = max(0.3, min(1.0, language_factor))  # Keep within bounds
        
        final_confidence = (data_confidence * 0.7 + language_factor * 0.3)
        return max(0.1, min(0.95, final_confidence))  # Keep within reasonable bounds


# Example usage
async def example_usage():
    """Example of how to use LangChainManager."""
    import os
    from datetime import datetime, timedelta
    
    # Initialize manager
    manager = LangChainManager(
        openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-4",
        temperature=0.7
    )
    
    # Sample data for testing
    sample_market_data = {
        'symbol': 'BTCUSDT',
        'current_price': 45000.0,
        'high_24h': 46000.0,
        'low_24h': 44000.0,
        'volume_24h': 1000000.0,
        'price_change_24h': 500.0,
        'price_change_percent_24h': 1.12,
        'timestamp': datetime.now().isoformat()
    }
    
    # Sample OHLC data
    timestamps = [datetime.now() - timedelta(minutes=5*i) for i in range(10, 0, -1)]
    sample_ohlc = pd.DataFrame({
        'timestamp': timestamps,
        'open': [45000 + i*10 for i in range(10)],
        'high': [45100 + i*10 for i in range(10)],
        'low': [44900 + i*10 for i in range(10)],
        'close': [45050 + i*10 for i in range(10)],
        'volume': [1000 + i*50 for i in range(10)]
    })
    
    # Test market analysis
    analysis, confidence = await manager.analyze_market(
        query="What is the current market sentiment for Bitcoin?",
        market_data=sample_market_data,
        ohlc_data=sample_ohlc
    )
    
    print(f"Market Analysis (confidence: {confidence:.2f}):\n{analysis}\n")
    
    # Test general query
    general_response = await manager.general_query(
        query="What factors typically influence Bitcoin price movements?"
    )
    
    print(f"General Query Response:\n{general_response}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())