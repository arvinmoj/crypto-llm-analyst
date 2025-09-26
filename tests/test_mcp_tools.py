"""
Tests for MCP tools functionality.
"""

import pytest
import asyncio
from datetime import datetime

from ..ai.mcp_tools import (
    MCPToolRegistry, MCPToolOrchestrator, MCPToolRequest, 
    ToolType, PriceAnalysisTool, TechnicalIndicatorTool
)


class TestMCPToolRegistry:
    """Test MCP tool registry"""
    
    def test_registry_initialization(self):
        """Test registry initialization"""
        registry = MCPToolRegistry()
        
        assert ToolType.PRICE_ANALYSIS in registry.tools
        assert ToolType.TECHNICAL_INDICATOR in registry.tools
        assert ToolType.MARKET_SENTIMENT in registry.tools
        assert ToolType.RISK_ASSESSMENT in registry.tools
    
    def test_get_available_tools(self):
        """Test getting available tools"""
        registry = MCPToolRegistry()
        tools = registry.get_available_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        for tool in tools:
            assert 'type' in tool
            assert 'name' in tool
            assert 'description' in tool
    
    @pytest.mark.asyncio
    async def test_execute_tool_invalid_type(self):
        """Test executing invalid tool type"""
        registry = MCPToolRegistry()
        
        # Create request with invalid tool type (mock)
        class InvalidToolType:
            value = "invalid_tool"
        
        request = MCPToolRequest(
            tool_type=InvalidToolType(),
            symbol="BTC",
            parameters={}
        )
        
        response = await registry.execute_tool(request)
        assert not response.success
        assert "not found" in response.error


class TestPriceAnalysisTool:
    """Test price analysis tool"""
    
    @pytest.mark.asyncio
    async def test_price_analysis_execution(self):
        """Test price analysis tool execution"""
        tool = PriceAnalysisTool()
        
        response = await tool.execute(
            symbol="BTC",
            parameters={
                'timeframe': '1h',
                'analysis_type': 'comprehensive'
            }
        )
        
        assert response.success
        assert response.tool_type == ToolType.PRICE_ANALYSIS
        assert 'symbol' in response.data
        assert response.data['symbol'] == "BTC"
        assert 'current_trend' in response.data
        assert 'confidence_score' in response.data
        assert isinstance(response.execution_time, float)
        assert response.execution_time > 0


class TestTechnicalIndicatorTool:
    """Test technical indicator tool"""
    
    @pytest.mark.asyncio
    async def test_technical_indicator_execution(self):
        """Test technical indicator tool execution"""
        tool = TechnicalIndicatorTool()
        
        response = await tool.execute(
            symbol="BTC",
            parameters={
                'indicators': ['RSI', 'MACD', 'BB'],
                'period': 14
            }
        )
        
        assert response.success
        assert response.tool_type == ToolType.TECHNICAL_INDICATOR
        assert 'symbol' in response.data
        assert 'indicators' in response.data
        
        indicators = response.data['indicators']
        assert 'RSI' in indicators
        assert 'MACD' in indicators
        assert 'BB' in indicators
        
        # Check RSI structure
        rsi_data = indicators['RSI']
        assert 'value' in rsi_data
        assert 'signal' in rsi_data
        assert 'interpretation' in rsi_data


class TestMCPToolOrchestrator:
    """Test MCP tool orchestrator"""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        orchestrator = MCPToolOrchestrator()
        assert orchestrator.registry is not None
    
    @pytest.mark.asyncio
    async def test_execute_analysis_pipeline(self):
        """Test executing analysis pipeline"""
        orchestrator = MCPToolOrchestrator()
        
        results = await orchestrator.execute_analysis_pipeline(
            symbol="BTC",
            analysis_config={}
        )
        
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Check that all expected tools were executed
        expected_tools = [
            'price_analysis',
            'technical_indicator',
            'market_sentiment',
            'risk_assessment'
        ]
        
        for tool_name in expected_tools:
            assert tool_name in results
            assert hasattr(results[tool_name], 'success')
    
    def test_aggregate_analysis_results(self):
        """Test aggregating analysis results"""
        from ..ai.mcp_tools import MCPToolResponse
        
        orchestrator = MCPToolOrchestrator()
        
        # Mock results
        mock_results = {
            'price_analysis': MCPToolResponse(
                success=True,
                data={
                    'confidence': 0.8,
                    'current_trend': 'bullish',
                    'recommendations': {'position': 'Consider buying on dips'}
                }
            ),
            'technical_indicator': MCPToolResponse(
                success=True,
                data={
                    'confidence': 0.7,
                    'overall_sentiment': 0.6,
                    'recommendations': ['Set stop loss at support level']
                }
            ),
            'failed_tool': MCPToolResponse(
                success=False,
                data={},
                error="Tool failed"
            )
        }
        
        aggregated = orchestrator.aggregate_analysis_results(mock_results)
        
        assert 'successful_tools' in aggregated
        assert 'failed_tools' in aggregated
        assert 'confidence_score' in aggregated
        assert 'overall_sentiment' in aggregated
        assert 'recommendations' in aggregated
        
        assert aggregated['successful_tools'] == 2
        assert aggregated['failed_tools'] == 1
        assert aggregated['confidence_score'] > 0
        assert isinstance(aggregated['recommendations'], list)


class TestMCPToolRequest:
    """Test MCP tool request structure"""
    
    def test_request_creation(self):
        """Test creating MCP tool request"""
        request = MCPToolRequest(
            tool_type=ToolType.PRICE_ANALYSIS,
            symbol="BTC",
            parameters={'timeframe': '1h'}
        )
        
        assert request.tool_type == ToolType.PRICE_ANALYSIS
        assert request.symbol == "BTC"
        assert request.parameters['timeframe'] == '1h'
        assert isinstance(request.timestamp, datetime)
    
    def test_request_with_timestamp(self):
        """Test creating request with custom timestamp"""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        
        request = MCPToolRequest(
            tool_type=ToolType.TECHNICAL_INDICATOR,
            symbol="ETH",
            parameters={},
            timestamp=custom_time
        )
        
        assert request.timestamp == custom_time