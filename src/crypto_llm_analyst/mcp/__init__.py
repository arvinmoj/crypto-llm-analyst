"""Model Context Protocol (MCP) implementation for standardized AI-external system interactions."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """MCP message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPResourceType(Enum):
    """MCP resource types for crypto analysis."""
    MARKET_DATA = "market_data"
    OHLC_DATA = "ohlc_data"
    ANALYSIS_RESULT = "analysis_result"
    TECHNICAL_INDICATORS = "technical_indicators"
    MARKET_SUMMARY = "market_summary"


@dataclass
class MCPMessage:
    """MCP protocol message structure."""
    id: str
    type: MCPMessageType
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        data = asdict(self)
        data['type'] = self.type.value
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create message from dictionary."""
        data = data.copy()
        data['type'] = MCPMessageType(data['type'])
        return cls(**data)


@dataclass
class MCPResource:
    """MCP resource definition for crypto data."""
    id: str
    type: MCPResourceType
    name: str
    description: str
    uri: str
    metadata: Dict[str, Any]
    content: Optional[Any] = None
    last_updated: str = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary."""
        data = asdict(self)
        data['type'] = self.type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPResource':
        """Create resource from dictionary."""
        data = data.copy()
        data['type'] = MCPResourceType(data['type'])
        return cls(**data)


class MCPProtocol:
    """Model Context Protocol implementation for crypto analysis system."""
    
    def __init__(self, system_name: str = "crypto-llm-analyst"):
        """Initialize MCP protocol handler.
        
        Args:
            system_name: Name of the system implementing MCP
        """
        self.system_name = system_name
        self.capabilities = {
            "resources": True,
            "tools": True,
            "prompts": True,
            "logging": True
        }
        
        # Resource storage
        self.resources: Dict[str, MCPResource] = {}
        
        # Method handlers
        self.handlers: Dict[str, Callable] = {
            "initialize": self._handle_initialize,
            "list_resources": self._handle_list_resources,
            "read_resource": self._handle_read_resource,
            "list_tools": self._handle_list_tools,
            "call_tool": self._handle_call_tool,
            "list_prompts": self._handle_list_prompts,
            "get_prompt": self._handle_get_prompt,
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe
        }
        
        # Tool definitions
        self.tools = {
            "get_market_data": {
                "name": "get_market_data",
                "description": "Get current market data for a cryptocurrency symbol",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Trading symbol (e.g., BTCUSDT)"},
                        "timeframe": {"type": "string", "description": "Timeframe (e.g., 5m, 1h)"}
                    },
                    "required": ["symbol"]
                }
            },
            "get_ohlc_data": {
                "name": "get_ohlc_data",
                "description": "Get OHLC data for a specified time range",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Trading symbol"},
                        "start_time": {"type": "string", "description": "Start time (ISO format)"},
                        "end_time": {"type": "string", "description": "End time (ISO format)"},
                        "limit": {"type": "integer", "description": "Maximum number of records"}
                    },
                    "required": ["symbol", "start_time", "end_time"]
                }
            },
            "analyze_market": {
                "name": "analyze_market",
                "description": "Perform market analysis using LLM",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Trading symbol"},
                        "query": {"type": "string", "description": "Analysis query"},
                        "analysis_type": {"type": "string", "description": "Type of analysis"}
                    },
                    "required": ["symbol", "query"]
                }
            }
        }
        
        # Prompt templates
        self.prompts = {
            "market_analysis": {
                "name": "market_analysis",
                "description": "Prompt for comprehensive market analysis",
                "arguments": [
                    {"name": "symbol", "description": "Trading symbol", "required": True},
                    {"name": "timeframe", "description": "Analysis timeframe", "required": False}
                ]
            },
            "price_prediction": {
                "name": "price_prediction",
                "description": "Prompt for price prediction analysis",
                "arguments": [
                    {"name": "symbol", "description": "Trading symbol", "required": True},
                    {"name": "horizon", "description": "Prediction horizon", "required": False}
                ]
            }
        }
        
        # Subscribers for real-time updates
        self.subscribers: Dict[str, List[Callable]] = {}
        
        # External system connectors (to be injected)
        self.data_source = None
        self.database = None
        self.llm_manager = None
        self.rag_system = None
    
    def set_connectors(
        self,
        data_source=None,
        database=None,
        llm_manager=None,
        rag_system=None
    ):
        """Set external system connectors.
        
        Args:
            data_source: Data source connector (e.g., BitqueryClient)
            database: Database connector (e.g., SupabaseManager)
            llm_manager: LLM manager (e.g., LangChainManager)
            rag_system: RAG system (e.g., CryptoRAGSystem)
        """
        self.data_source = data_source
        self.database = database
        self.llm_manager = llm_manager
        self.rag_system = rag_system
    
    async def handle_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP message.
        
        Args:
            message_data: Message data dictionary
            
        Returns:
            Response message dictionary
        """
        try:
            message = MCPMessage.from_dict(message_data)
            
            if message.method in self.handlers:
                handler = self.handlers[message.method]
                result = await handler(message.params or {})
                
                response = MCPMessage(
                    id=message.id,
                    type=MCPMessageType.RESPONSE,
                    result=result
                )
                return response.to_dict()
            else:
                error_response = MCPMessage(
                    id=message.id,
                    type=MCPMessageType.ERROR,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {message.method}"
                    }
                )
                return error_response.to_dict()
                
        except Exception as e:
            logger.error(f"Error handling MCP message: {e}")
            error_response = MCPMessage(
                id=message_data.get("id", "unknown"),
                type=MCPMessageType.ERROR,
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )
            return error_response.to_dict()
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request."""
        return {
            "protocolVersion": "1.0.0",
            "capabilities": self.capabilities,
            "serverInfo": {
                "name": self.system_name,
                "version": "0.1.0"
            }
        }
    
    async def _handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list resources request."""
        resources = []
        for resource in self.resources.values():
            resources.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": "application/json"
            })
        
        return {"resources": resources}
    
    async def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle read resource request."""
        uri = params.get("uri")
        
        if not uri:
            raise ValueError("URI parameter required")
        
        # Find resource by URI
        resource = None
        for r in self.resources.values():
            if r.uri == uri:
                resource = r
                break
        
        if not resource:
            raise ValueError(f"Resource not found: {uri}")
        
        # Generate content based on resource type
        content = await self._generate_resource_content(resource)
        
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(content, indent=2)
                }
            ]
        }
    
    async def _handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list tools request."""
        tools = list(self.tools.values())
        return {"tools": tools}
    
    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise ValueError("Tool name required")
        
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")
        
        # Execute tool
        result = await self._execute_tool(name, arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }
    
    async def _handle_list_prompts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list prompts request."""
        prompts = list(self.prompts.values())
        return {"prompts": prompts}
    
    async def _handle_get_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get prompt request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise ValueError("Prompt name required")
        
        if name not in self.prompts:
            raise ValueError(f"Prompt not found: {name}")
        
        # Generate prompt content
        prompt_content = await self._generate_prompt_content(name, arguments)
        
        return {
            "description": self.prompts[name]["description"],
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": prompt_content
                    }
                }
            ]
        }
    
    async def _handle_subscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscribe request for real-time updates."""
        uri = params.get("uri")
        callback_id = params.get("callback_id")
        
        if not uri or not callback_id:
            raise ValueError("URI and callback_id required for subscription")
        
        if uri not in self.subscribers:
            self.subscribers[uri] = []
        
        # Store callback for notifications (simplified)
        self.subscribers[uri].append(callback_id)
        
        return {"subscribed": True}
    
    async def _handle_unsubscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unsubscribe request."""
        uri = params.get("uri")
        callback_id = params.get("callback_id")
        
        if uri in self.subscribers and callback_id in self.subscribers[uri]:
            self.subscribers[uri].remove(callback_id)
            if not self.subscribers[uri]:
                del self.subscribers[uri]
        
        return {"unsubscribed": True}
    
    async def _generate_resource_content(self, resource: MCPResource) -> Dict[str, Any]:
        """Generate content for a resource based on its type."""
        if resource.type == MCPResourceType.MARKET_DATA:
            return await self._get_market_data_content(resource.metadata.get("symbol", "BTCUSDT"))
        elif resource.type == MCPResourceType.OHLC_DATA:
            return await self._get_ohlc_data_content(resource.metadata)
        elif resource.type == MCPResourceType.ANALYSIS_RESULT:
            return await self._get_analysis_result_content(resource.metadata)
        else:
            return {"error": "Unsupported resource type"}
    
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given arguments."""
        if name == "get_market_data":
            return await self._tool_get_market_data(arguments)
        elif name == "get_ohlc_data":
            return await self._tool_get_ohlc_data(arguments)
        elif name == "analyze_market":
            return await self._tool_analyze_market(arguments)
        else:
            return {"error": f"Tool not implemented: {name}"}
    
    async def _generate_prompt_content(self, name: str, arguments: Dict[str, Any]) -> str:
        """Generate prompt content based on name and arguments."""
        symbol = arguments.get("symbol", "BTCUSDT")
        
        if name == "market_analysis":
            timeframe = arguments.get("timeframe", "1h")
            return f"Analyze the current market conditions for {symbol} over the {timeframe} timeframe. Consider price trends, volume patterns, and technical indicators."
        
        elif name == "price_prediction":
            horizon = arguments.get("horizon", "24h")
            return f"Provide a price prediction for {symbol} over the next {horizon}. Include confidence levels and key factors influencing the prediction."
        
        else:
            return f"Unknown prompt: {name}"
    
    async def _tool_get_market_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for getting market data."""
        if not self.database:
            return {"error": "Database not connected"}
        
        symbol = arguments.get("symbol", "BTCUSDT")
        
        try:
            market_summary = await self.database.get_market_summary(symbol)
            return {"market_data": market_summary}
        except Exception as e:
            return {"error": str(e)}
    
    async def _tool_get_ohlc_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for getting OHLC data."""
        if not self.database:
            return {"error": "Database not connected"}
        
        symbol = arguments.get("symbol", "BTCUSDT")
        start_time = arguments.get("start_time")
        end_time = arguments.get("end_time")
        limit = arguments.get("limit", 100)
        
        try:
            if start_time and end_time:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                df = await self.database.get_ohlc_range(symbol, start_dt, end_dt)
            else:
                df = await self.database.get_latest_ohlc(symbol, limit)
            
            ohlc_data = df.to_dict('records') if not df.empty else []
            return {"ohlc_data": ohlc_data}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _tool_analyze_market(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for market analysis."""
        if not self.llm_manager or not self.database:
            return {"error": "LLM manager or database not connected"}
        
        symbol = arguments.get("symbol", "BTCUSDT")
        query = arguments.get("query", "Analyze current market conditions")
        analysis_type = arguments.get("analysis_type", "general")
        
        try:
            # Get market data and OHLC data
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
                confidence = 0.8  # Default confidence for general queries
            
            return {
                "analysis": {
                    "result": result,
                    "confidence": confidence,
                    "analysis_type": analysis_type,
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_market_data_content(self, symbol: str) -> Dict[str, Any]:
        """Get market data content for a resource."""
        if self.database:
            try:
                return await self.database.get_market_summary(symbol)
            except Exception as e:
                return {"error": str(e)}
        return {"error": "Database not connected"}
    
    async def _get_ohlc_data_content(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get OHLC data content for a resource."""
        if self.database:
            try:
                symbol = metadata.get("symbol", "BTCUSDT")
                limit = metadata.get("limit", 100)
                df = await self.database.get_latest_ohlc(symbol, limit)
                return {"ohlc_data": df.to_dict('records') if not df.empty else []}
            except Exception as e:
                return {"error": str(e)}
        return {"error": "Database not connected"}
    
    async def _get_analysis_result_content(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get analysis result content for a resource."""
        if self.database:
            try:
                symbol = metadata.get("symbol", "BTCUSDT")
                analysis_type = metadata.get("analysis_type")
                limit = metadata.get("limit", 10)
                
                results = await self.database.get_recent_analysis(
                    symbol, analysis_type, limit
                )
                return {"analysis_results": results}
            except Exception as e:
                return {"error": str(e)}
        return {"error": "Database not connected"}
    
    async def register_resource(self, resource: MCPResource) -> None:
        """Register a new resource."""
        self.resources[resource.id] = resource
        logger.info(f"Registered MCP resource: {resource.name}")
    
    async def notify_subscribers(self, uri: str, data: Dict[str, Any]) -> None:
        """Notify subscribers of resource updates."""
        if uri in self.subscribers:
            notification = MCPMessage(
                id=f"notification_{datetime.now().timestamp()}",
                type=MCPMessageType.NOTIFICATION,
                method="resource_updated",
                params={"uri": uri, "data": data}
            )
            
            # In a real implementation, you would send notifications to actual clients
            logger.info(f"Notifying {len(self.subscribers[uri])} subscribers for {uri}")


# Example usage
async def example_usage():
    """Example of how to use MCPProtocol."""
    
    # Initialize MCP protocol
    mcp = MCPProtocol("crypto-llm-analyst")
    
    # Register some resources
    market_resource = MCPResource(
        id="btc_market_data",
        type=MCPResourceType.MARKET_DATA,
        name="Bitcoin Market Data",
        description="Real-time Bitcoin market data and statistics",
        uri="crypto://market/BTCUSDT",
        metadata={"symbol": "BTCUSDT"}
    )
    
    await mcp.register_resource(market_resource)
    
    # Example message handling
    request_message = {
        "id": "req_001",
        "type": "request",
        "method": "list_resources",
        "params": {}
    }
    
    response = await mcp.handle_message(request_message)
    print(f"MCP Response: {json.dumps(response, indent=2)}")
    
    # Example tool call
    tool_request = {
        "id": "req_002", 
        "type": "request",
        "method": "call_tool",
        "params": {
            "name": "get_market_data",
            "arguments": {"symbol": "BTCUSDT"}
        }
    }
    
    tool_response = await mcp.handle_message(tool_request)
    print(f"Tool Response: {json.dumps(tool_response, indent=2)}")


if __name__ == "__main__":
    asyncio.run(example_usage())