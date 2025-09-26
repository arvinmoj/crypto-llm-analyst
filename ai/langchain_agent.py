"""
LangChain agent for cryptocurrency analysis and trading recommendations.
"""

import os
import logging
from typing import List, Dict, Optional, Any, Union, Type
import asyncio
from datetime import datetime
from dataclasses import dataclass

# LangChain imports
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain.schema import AgentAction, AgentFinish
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks import AsyncCallbackHandler
from langchain.schema import HumanMessage, AIMessage

# Internal imports
from .mcp_tools import MCPToolOrchestrator, MCPToolRequest, ToolType
from .rag_system import CryptoRAGSystem, RAGQuery
from ..data.data_processor import DataProcessor, MarketSignal

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """Request for cryptocurrency analysis"""
    symbol: str
    analysis_type: str  # 'quick', 'comprehensive', 'technical', 'fundamental'
    context: Optional[Dict[str, Any]] = None
    user_query: Optional[str] = None
    include_recommendations: bool = True


@dataclass
class AnalysisResponse:
    """Response from cryptocurrency analysis"""
    symbol: str
    analysis_type: str
    summary: str
    detailed_analysis: Dict[str, Any]
    recommendations: List[str]
    confidence: float
    timestamp: datetime
    sources: List[str]


class CryptoPriceAnalysisTool(BaseTool):
    """Tool for cryptocurrency price analysis"""
    
    name = "crypto_price_analysis"
    description = "Analyze cryptocurrency price movements, trends, and technical indicators"
    
    def __init__(self, mcp_orchestrator: MCPToolOrchestrator):
        super().__init__()
        self.mcp_orchestrator = mcp_orchestrator
    
    def _run(self, symbol: str, timeframe: str = "1h") -> str:
        """Execute price analysis"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._arun(symbol, timeframe))
        finally:
            loop.close()
    
    async def _arun(self, symbol: str, timeframe: str = "1h") -> str:
        """Async execution of price analysis"""
        try:
            # Create MCP tool request
            request = MCPToolRequest(
                tool_type=ToolType.PRICE_ANALYSIS,
                symbol=symbol.upper(),
                parameters={'timeframe': timeframe, 'analysis_type': 'comprehensive'}
            )
            
            result = await self.mcp_orchestrator.registry.execute_tool(request)
            
            if result.success:
                data = result.data
                return f"""
Price Analysis for {symbol}:
- Current Trend: {data.get('current_trend', 'Unknown')}
- Trend Strength: {data.get('trend_strength', 0):.2f}
- Support Levels: {', '.join(map(str, data.get('support_levels', [])))}
- Resistance Levels: {', '.join(map(str, data.get('resistance_levels', [])))}
- Price Predictions: {data.get('price_prediction', {})}
- Confidence: {data.get('confidence_score', 0):.2f}
                """
            else:
                return f"Price analysis failed: {result.error}"
                
        except Exception as e:
            logger.error(f"Price analysis tool error: {e}")
            return f"Error executing price analysis: {str(e)}"


class CryptoTechnicalAnalysisTool(BaseTool):
    """Tool for technical indicator analysis"""
    
    name = "crypto_technical_analysis"
    description = "Analyze technical indicators like RSI, MACD, Bollinger Bands for cryptocurrencies"
    
    def __init__(self, mcp_orchestrator: MCPToolOrchestrator):
        super().__init__()
        self.mcp_orchestrator = mcp_orchestrator
    
    def _run(self, symbol: str, indicators: str = "RSI,MACD,BB") -> str:
        """Execute technical analysis"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._arun(symbol, indicators))
        finally:
            loop.close()
    
    async def _arun(self, symbol: str, indicators: str = "RSI,MACD,BB") -> str:
        """Async execution of technical analysis"""
        try:
            indicator_list = [i.strip() for i in indicators.split(',')]
            
            request = MCPToolRequest(
                tool_type=ToolType.TECHNICAL_INDICATOR,
                symbol=symbol.upper(),
                parameters={'indicators': indicator_list, 'period': 14}
            )
            
            result = await self.mcp_orchestrator.registry.execute_tool(request)
            
            if result.success:
                data = result.data
                indicators_data = data.get('indicators', {})
                
                analysis_text = f"Technical Analysis for {symbol}:\n"
                
                for indicator, values in indicators_data.items():
                    if isinstance(values, dict):
                        analysis_text += f"\n{indicator}:\n"
                        analysis_text += f"  - Value: {values.get('value', 'N/A')}\n"
                        analysis_text += f"  - Signal: {values.get('signal', 'N/A')}\n"
                        analysis_text += f"  - Interpretation: {values.get('interpretation', 'N/A')}\n"
                
                analysis_text += f"\nOverall Signal: {data.get('overall_signal', 'N/A')}"
                analysis_text += f"\nConfidence: {data.get('confidence', 0):.2f}"
                
                return analysis_text
            else:
                return f"Technical analysis failed: {result.error}"
                
        except Exception as e:
            logger.error(f"Technical analysis tool error: {e}")
            return f"Error executing technical analysis: {str(e)}"


class CryptoSentimentAnalysisTool(BaseTool):
    """Tool for market sentiment analysis"""
    
    name = "crypto_sentiment_analysis"
    description = "Analyze market sentiment from social media, news, and on-chain data"
    
    def __init__(self, mcp_orchestrator: MCPToolOrchestrator):
        super().__init__()
        self.mcp_orchestrator = mcp_orchestrator
    
    def _run(self, symbol: str, sources: str = "social,news") -> str:
        """Execute sentiment analysis"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._arun(symbol, sources))
        finally:
            loop.close()
    
    async def _arun(self, symbol: str, sources: str = "social,news") -> str:
        """Async execution of sentiment analysis"""
        try:
            source_list = [s.strip() for s in sources.split(',')]
            
            request = MCPToolRequest(
                tool_type=ToolType.MARKET_SENTIMENT,
                symbol=symbol.upper(),
                parameters={'sources': source_list, 'timeframe': '24h'}
            )
            
            result = await self.mcp_orchestrator.registry.execute_tool(request)
            
            if result.success:
                data = result.data
                return f"""
Sentiment Analysis for {symbol}:
- Overall Sentiment: {data.get('sentiment_label', 'Unknown')} ({data.get('overall_sentiment', 0):.2f})
- Social Media Score: {data.get('sources', {}).get('social_media', {}).get('score', 'N/A')}
- News Sentiment Score: {data.get('sources', {}).get('news', {}).get('score', 'N/A')}
- Trending Topics: {', '.join(data.get('sources', {}).get('social_media', {}).get('trending_topics', []))}
- Confidence: {data.get('confidence', 0):.2f}
                """
            else:
                return f"Sentiment analysis failed: {result.error}"
                
        except Exception as e:
            logger.error(f"Sentiment analysis tool error: {e}")
            return f"Error executing sentiment analysis: {str(e)}"


class CryptoKnowledgeQueryTool(BaseTool):
    """Tool for querying cryptocurrency knowledge base"""
    
    name = "crypto_knowledge_query"
    description = "Query the cryptocurrency knowledge base for information about trading, analysis, and market concepts"
    
    def __init__(self, rag_system: CryptoRAGSystem):
        super().__init__()
        self.rag_system = rag_system
    
    def _run(self, query: str) -> str:
        """Execute knowledge query"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._arun(query))
        finally:
            loop.close()
    
    async def _arun(self, query: str) -> str:
        """Async execution of knowledge query"""
        try:
            rag_query = RAGQuery(query=query, max_results=3)
            response = await self.rag_system.query(rag_query)
            
            knowledge_text = f"Knowledge Base Response:\n{response.answer}\n\n"
            
            if response.sources:
                knowledge_text += "Sources:\n"
                for i, source in enumerate(response.sources[:2], 1):
                    title = source.metadata.get('title', 'Unknown Source')
                    category = source.metadata.get('category', 'general')
                    knowledge_text += f"{i}. {title} ({category})\n"
            
            knowledge_text += f"\nConfidence: {response.confidence:.2f}"
            
            return knowledge_text
            
        except Exception as e:
            logger.error(f"Knowledge query tool error: {e}")
            return f"Error querying knowledge base: {str(e)}"


class CryptoAnalysisAgent:
    """Main LangChain agent for cryptocurrency analysis"""
    
    def __init__(
        self, 
        openai_api_key: Optional[str] = None,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.1
    ):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize components
        self.mcp_orchestrator = MCPToolOrchestrator()
        self.rag_system = CryptoRAGSystem()
        self.data_processor = DataProcessor()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            openai_api_key=self.openai_api_key,
            model_name=model_name,
            temperature=temperature
        )
        
        # Setup memory
        self.memory = ConversationBufferWindowMemory(
            k=10,  # Keep last 10 exchanges
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent_executor = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create the tools for the agent"""
        return [
            CryptoPriceAnalysisTool(self.mcp_orchestrator),
            CryptoTechnicalAnalysisTool(self.mcp_orchestrator),
            CryptoSentimentAnalysisTool(self.mcp_orchestrator),
            CryptoKnowledgeQueryTool(self.rag_system)
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the ReAct agent"""
        # Define the prompt template
        template = """You are an expert cryptocurrency analyst and trading advisor. You have access to various tools to analyze cryptocurrencies, market sentiment, and trading information.

TOOLS:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Remember to:
1. Always use multiple tools to get comprehensive analysis
2. Provide clear, actionable recommendations
3. Explain your reasoning and confidence levels
4. Consider both technical and fundamental factors
5. Warn about risks and limitations

Previous conversation:
{chat_history}

Question: {input}
{agent_scratchpad}"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["input", "chat_history", "agent_scratchpad", "tools", "tool_names"]
        )
        
        # Create the ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    async def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """Perform comprehensive cryptocurrency analysis"""
        start_time = datetime.now()
        
        # Construct the query based on request
        query = self._construct_analysis_query(request)
        
        try:
            # Execute the agent
            result = await asyncio.to_thread(
                self.agent_executor.run,
                query
            )
            
            # Parse the result and create response
            analysis_response = AnalysisResponse(
                symbol=request.symbol,
                analysis_type=request.analysis_type,
                summary=result[:500] + "..." if len(result) > 500 else result,
                detailed_analysis={"full_analysis": result},
                recommendations=self._extract_recommendations(result),
                confidence=0.8,  # Default confidence
                timestamp=start_time,
                sources=["Technical Analysis", "Market Sentiment", "Knowledge Base"]
            )
            
            return analysis_response
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return AnalysisResponse(
                symbol=request.symbol,
                analysis_type=request.analysis_type,
                summary=f"Analysis failed: {str(e)}",
                detailed_analysis={"error": str(e)},
                recommendations=["Unable to provide recommendations due to analysis failure"],
                confidence=0.0,
                timestamp=start_time,
                sources=[]
            )
    
    def _construct_analysis_query(self, request: AnalysisRequest) -> str:
        """Construct the analysis query based on request"""
        base_query = f"Analyze {request.symbol} cryptocurrency"
        
        if request.analysis_type == "quick":
            query = f"{base_query} quickly. Provide current price trend, key technical indicators, and a brief recommendation."
        elif request.analysis_type == "comprehensive":
            query = f"{base_query} comprehensively. Include price analysis, technical indicators, market sentiment, and detailed trading recommendations with risk assessment."
        elif request.analysis_type == "technical":
            query = f"{base_query} from a technical analysis perspective. Focus on price patterns, technical indicators, support/resistance levels, and entry/exit points."
        elif request.analysis_type == "fundamental":
            query = f"{base_query} from a fundamental perspective. Consider project fundamentals, adoption, market position, and long-term outlook."
        else:
            query = base_query
        
        if request.user_query:
            query += f" Additionally, please answer this specific question: {request.user_query}"
        
        if request.context:
            context_info = ", ".join([f"{k}: {v}" for k, v in request.context.items()])
            query += f" Consider this context: {context_info}"
        
        return query
    
    def _extract_recommendations(self, analysis_text: str) -> List[str]:
        """Extract recommendations from analysis text"""
        recommendations = []
        
        # Simple keyword-based extraction
        lines = analysis_text.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider', 'advice']):
                if line and not line.startswith('Thought:') and not line.startswith('Action:'):
                    recommendations.append(line)
        
        # If no recommendations found, provide generic ones
        if not recommendations:
            recommendations = [
                "Conduct thorough research before making investment decisions",
                "Consider your risk tolerance and investment timeline",
                "Never invest more than you can afford to lose",
                "Monitor market conditions and adjust strategy accordingly"
            ]
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    async def chat(self, user_message: str) -> str:
        """Chat interface for interactive analysis"""
        try:
            response = await asyncio.to_thread(
                self.agent_executor.run,
                user_message
            )
            return response
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        messages = self.memory.chat_memory.messages
        history = []
        
        for message in messages:
            if isinstance(message, HumanMessage):
                history.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                history.append({"role": "assistant", "content": message.content})
        
        return history
    
    def clear_history(self):
        """Clear conversation history"""
        self.memory.clear()


# Example usage
async def main():
    """Example usage of the crypto analysis agent"""
    agent = CryptoAnalysisAgent()
    
    # Example analysis request
    request = AnalysisRequest(
        symbol="BTC",
        analysis_type="comprehensive",
        user_query="Should I buy Bitcoin now or wait?"
    )
    
    print("=== Comprehensive Bitcoin Analysis ===")
    response = await agent.analyze(request)
    
    print(f"Symbol: {response.symbol}")
    print(f"Analysis Type: {response.analysis_type}")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"\nSummary:\n{response.summary}")
    
    print(f"\nRecommendations:")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"{i}. {rec}")
    
    print(f"\nSources: {', '.join(response.sources)}")
    
    # Example chat interaction
    print("\n=== Chat Example ===")
    chat_response = await agent.chat("What's the current sentiment for Ethereum?")
    print(f"Agent: {chat_response}")


if __name__ == "__main__":
    asyncio.run(main())