"""N8N workflow automation integration for multi-step AI agent workflows."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class N8NWorkflowTrigger:
    """N8N workflow trigger configuration."""
    name: str
    type: str  # webhook, manual, cron, etc.
    config: Dict[str, Any]
    active: bool = True


@dataclass
class N8NWorkflowNode:
    """N8N workflow node definition."""
    name: str
    type: str
    position: List[int]
    parameters: Dict[str, Any]
    credentials: Optional[Dict[str, str]] = None
    typeVersion: int = 1


@dataclass
class N8NWorkflow:
    """N8N workflow definition for crypto analysis."""
    name: str
    nodes: List[N8NWorkflowNode]
    connections: Dict[str, Any]
    active: bool = True
    settings: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to N8N format."""
        return {
            "name": self.name,
            "nodes": [asdict(node) for node in self.nodes],
            "connections": self.connections,
            "active": self.active,
            "settings": self.settings or {},
            "tags": self.tags or []
        }


class N8NManager:
    """Manager for N8N workflow automation and AI agent orchestration."""
    
    def __init__(
        self,
        n8n_url: str,
        api_key: Optional[str] = None,
        webhook_url: Optional[str] = None
    ):
        """Initialize N8N manager.
        
        Args:
            n8n_url: N8N instance URL
            api_key: N8N API key for authentication
            webhook_url: Base URL for webhooks
        """
        self.n8n_url = n8n_url.rstrip('/')
        self.api_key = api_key
        self.webhook_url = webhook_url or n8n_url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Workflow templates
        self.workflow_templates = {
            "crypto_analysis_pipeline": self._create_analysis_pipeline_template,
            "price_alert_system": self._create_price_alert_template,
            "market_report_generator": self._create_market_report_template,
            "trading_signal_processor": self._create_trading_signal_template
        }
        
        # External system connectors
        self.crypto_system = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def set_crypto_system(self, crypto_system):
        """Set crypto analysis system for integration.
        
        Args:
            crypto_system: Main crypto analysis system instance
        """
        self.crypto_system = crypto_system
    
    async def create_workflow(self, workflow: N8NWorkflow) -> Dict[str, Any]:
        """Create a new workflow in N8N.
        
        Args:
            workflow: Workflow definition
            
        Returns:
            Created workflow data
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        headers = self._get_headers()
        workflow_data = workflow.to_dict()
        
        try:
            async with self.session.post(
                f"{self.n8n_url}/api/v1/workflows",
                headers=headers,
                json=workflow_data
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    logger.info(f"Created N8N workflow: {workflow.name}")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Failed to create workflow: {error}")
                    raise Exception(f"Workflow creation failed: {error}")
                    
        except Exception as e:
            logger.error(f"Error creating N8N workflow: {e}")
            raise
    
    async def trigger_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Trigger a workflow execution.
        
        Args:
            workflow_id: N8N workflow ID
            input_data: Input data for workflow
            
        Returns:
            Execution result
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        headers = self._get_headers()
        payload = {"data": input_data or {}}
        
        try:
            async with self.session.post(
                f"{self.n8n_url}/api/v1/workflows/{workflow_id}/execute",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Triggered workflow {workflow_id}")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Failed to trigger workflow: {error}")
                    raise Exception(f"Workflow trigger failed: {error}")
                    
        except Exception as e:
            logger.error(f"Error triggering N8N workflow: {e}")
            raise
    
    async def webhook_trigger(
        self,
        webhook_path: str,
        data: Dict[str, Any],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """Trigger workflow via webhook.
        
        Args:
            webhook_path: Webhook path (e.g., "webhook/crypto-analysis")
            data: Data to send to webhook
            method: HTTP method
            
        Returns:
            Webhook response
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        webhook_url = f"{self.webhook_url}/{webhook_path.lstrip('/')}"
        
        try:
            async with self.session.request(
                method,
                webhook_url,
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json() if response.headers.get('content-type', '').startswith('application/json') else await response.text()
                logger.info(f"Webhook triggered: {webhook_path}")
                return {"status": response.status, "data": result}
                
        except Exception as e:
            logger.error(f"Error triggering webhook: {e}")
            raise
    
    async def get_workflow_executions(
        self,
        workflow_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get workflow execution history.
        
        Args:
            workflow_id: Workflow ID
            limit: Number of executions to retrieve
            
        Returns:
            List of execution records
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        headers = self._get_headers()
        
        try:
            async with self.session.get(
                f"{self.n8n_url}/api/v1/executions",
                headers=headers,
                params={"workflowId": workflow_id, "limit": limit}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("data", [])
                else:
                    logger.error(f"Failed to get executions: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting workflow executions: {e}")
            return []
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for N8N API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers
    
    def _create_analysis_pipeline_template(self) -> N8NWorkflow:
        """Create crypto analysis pipeline workflow template."""
        
        # Webhook trigger node
        webhook_node = N8NWorkflowNode(
            name="Webhook Trigger",
            type="n8n-nodes-base.webhook",
            position=[250, 300],
            parameters={
                "httpMethod": "POST",
                "path": "crypto-analysis",
                "responseMode": "responseNode"
            }
        )
        
        # Get market data node
        market_data_node = N8NWorkflowNode(
            name="Get Market Data",
            type="n8n-nodes-base.httpRequest",
            position=[450, 300],
            parameters={
                "url": "http://localhost:8000/api/market/summary",
                "method": "GET",
                "sendQuery": True,
                "queryParameters": {
                    "parameters": [
                        {"name": "symbol", "value": "={{$json.symbol || 'BTCUSDT'}}"}
                    ]
                }
            }
        )
        
        # LLM analysis node
        llm_analysis_node = N8NWorkflowNode(
            name="LLM Analysis",
            type="n8n-nodes-base.httpRequest",
            position=[650, 300],
            parameters={
                "url": "http://localhost:8000/api/analysis/market",
                "method": "POST",
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {"name": "symbol", "value": "={{$json.symbol}}"},
                        {"name": "query", "value": "={{$json.query || 'Analyze current market conditions'}}"},
                        {"name": "market_data", "value": "={{$node['Get Market Data'].json}}"}
                    ]
                }
            }
        )
        
        # Store analysis node
        store_analysis_node = N8NWorkflowNode(
            name="Store Analysis",
            type="n8n-nodes-base.httpRequest",
            position=[850, 300],
            parameters={
                "url": "http://localhost:8000/api/analysis/store",
                "method": "POST",
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {"name": "analysis", "value": "={{$node['LLM Analysis'].json}}"},
                        {"name": "timestamp", "value": "={{new Date().toISOString()}}"}
                    ]
                }
            }
        )
        
        # Response node
        response_node = N8NWorkflowNode(
            name="Response",
            type="n8n-nodes-base.respondToWebhook",
            position=[1050, 300],
            parameters={
                "responseBody": "={{$node['LLM Analysis'].json}}",
                "responseContentType": "application/json"
            }
        )
        
        # Define connections
        connections = {
            "Webhook Trigger": {
                "main": [
                    [{"node": "Get Market Data", "type": "main", "index": 0}]
                ]
            },
            "Get Market Data": {
                "main": [
                    [{"node": "LLM Analysis", "type": "main", "index": 0}]
                ]
            },
            "LLM Analysis": {
                "main": [
                    [
                        {"node": "Store Analysis", "type": "main", "index": 0},
                        {"node": "Response", "type": "main", "index": 0}
                    ]
                ]
            }
        }
        
        return N8NWorkflow(
            name="Crypto Analysis Pipeline",
            nodes=[webhook_node, market_data_node, llm_analysis_node, store_analysis_node, response_node],
            connections=connections,
            tags=["crypto", "analysis", "ai"]
        )
    
    def _create_price_alert_template(self) -> N8NWorkflow:
        """Create price alert system workflow template."""
        
        # Cron trigger (every 5 minutes)
        cron_node = N8NWorkflowNode(
            name="Price Check Timer",
            type="n8n-nodes-base.cron",
            position=[250, 300],
            parameters={
                "rule": {
                    "interval": [{"field": "minute", "rule": "*/5"}]
                }
            }
        )
        
        # Get current price
        price_node = N8NWorkflowNode(
            name="Get Current Price",
            type="n8n-nodes-base.httpRequest",
            position=[450, 300],
            parameters={
                "url": "http://localhost:8000/api/market/price",
                "method": "GET",
                "sendQuery": True,
                "queryParameters": {
                    "parameters": [
                        {"name": "symbol", "value": "BTCUSDT"}
                    ]
                }
            }
        )
        
        # Check alert conditions
        condition_node = N8NWorkflowNode(
            name="Check Alert Conditions",
            type="n8n-nodes-base.if",
            position=[650, 300],
            parameters={
                "conditions": {
                    "number": [
                        {
                            "value1": "={{$json.current_price}}",
                            "operation": "largerEqual",
                            "value2": 50000
                        }
                    ]
                },
                "combineOperation": "any"
            }
        )
        
        # Send alert
        alert_node = N8NWorkflowNode(
            name="Send Alert",
            type="n8n-nodes-base.httpRequest",
            position=[850, 200],
            parameters={
                "url": "http://localhost:8000/api/alerts/send",
                "method": "POST",
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {"name": "symbol", "value": "BTCUSDT"},
                        {"name": "price", "value": "={{$node['Get Current Price'].json.current_price}}"},
                        {"name": "alert_type", "value": "price_threshold"},
                        {"name": "message", "value": "Bitcoin price alert: ${{$node['Get Current Price'].json.current_price}}"}
                    ]
                }
            }
        )
        
        connections = {
            "Price Check Timer": {
                "main": [
                    [{"node": "Get Current Price", "type": "main", "index": 0}]
                ]
            },
            "Get Current Price": {
                "main": [
                    [{"node": "Check Alert Conditions", "type": "main", "index": 0}]
                ]
            },
            "Check Alert Conditions": {
                "main": [
                    [{"node": "Send Alert", "type": "main", "index": 0}],
                    []  # False branch - no action
                ]
            }
        }
        
        return N8NWorkflow(
            name="Bitcoin Price Alert System",
            nodes=[cron_node, price_node, condition_node, alert_node],
            connections=connections,
            tags=["crypto", "alerts", "monitoring"]
        )
    
    def _create_market_report_template(self) -> N8NWorkflow:
        """Create automated market report generation workflow."""
        
        # Daily trigger
        schedule_node = N8NWorkflowNode(
            name="Daily Report Schedule",
            type="n8n-nodes-base.cron",
            position=[250, 300],
            parameters={
                "rule": {
                    "interval": [
                        {"field": "hour", "rule": "9"},
                        {"field": "minute", "rule": "0"}
                    ]
                }
            }
        )
        
        # Get market summary
        summary_node = N8NWorkflowNode(
            name="Get Market Summary",
            type="n8n-nodes-base.httpRequest",
            position=[450, 300],
            parameters={
                "url": "http://localhost:8000/api/market/daily-summary",
                "method": "GET"
            }
        )
        
        # Generate report with AI
        report_node = N8NWorkflowNode(
            name="Generate AI Report",
            type="n8n-nodes-base.httpRequest",
            position=[650, 300],
            parameters={
                "url": "http://localhost:8000/api/analysis/report",
                "method": "POST",
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {"name": "market_data", "value": "={{$json}}"},
                        {"name": "report_type", "value": "daily_market_summary"}
                    ]
                }
            }
        )
        
        # Send report (email/slack)
        send_report_node = N8NWorkflowNode(
            name="Send Report",
            type="n8n-nodes-base.emailSend",
            position=[850, 300],
            parameters={
                "subject": "Daily Crypto Market Report - {{new Date().toLocaleDateString()}}",
                "text": "={{$node['Generate AI Report'].json.report}}",
                "toEmail": "team@example.com",
                "fromEmail": "reports@crypto-analyst.com"
            }
        )
        
        connections = {
            "Daily Report Schedule": {
                "main": [
                    [{"node": "Get Market Summary", "type": "main", "index": 0}]
                ]
            },
            "Get Market Summary": {
                "main": [
                    [{"node": "Generate AI Report", "type": "main", "index": 0}]
                ]
            },
            "Generate AI Report": {
                "main": [
                    [{"node": "Send Report", "type": "main", "index": 0}]
                ]
            }
        }
        
        return N8NWorkflow(
            name="Daily Market Report Generator",
            nodes=[schedule_node, summary_node, report_node, send_report_node],
            connections=connections,
            tags=["crypto", "reports", "automation"]
        )
    
    def _create_trading_signal_template(self) -> N8NWorkflow:
        """Create trading signal processing workflow."""
        
        # Webhook for signal input
        webhook_node = N8NWorkflowNode(
            name="Signal Webhook",
            type="n8n-nodes-base.webhook",
            position=[250, 300],
            parameters={
                "httpMethod": "POST",
                "path": "trading-signal",
                "responseMode": "responseNode"
            }
        )
        
        # Validate signal
        validate_node = N8NWorkflowNode(
            name="Validate Signal",
            type="n8n-nodes-base.code",
            position=[450, 300],
            parameters={
                "jsCode": """
                const signal = items[0].json;
                
                // Basic signal validation
                const requiredFields = ['symbol', 'signal_type', 'confidence', 'price'];
                const isValid = requiredFields.every(field => signal.hasOwnProperty(field));
                
                if (!isValid) {
                    throw new Error('Invalid signal: missing required fields');
                }
                
                if (signal.confidence < 0.7) {
                    throw new Error('Signal confidence too low');
                }
                
                return items;
                """
            }
        )
        
        # Get market context
        context_node = N8NWorkflowNode(
            name="Get Market Context",
            type="n8n-nodes-base.httpRequest",
            position=[650, 300],
            parameters={
                "url": "http://localhost:8000/api/market/context",
                "method": "GET",
                "sendQuery": True,
                "queryParameters": {
                    "parameters": [
                        {"name": "symbol", "value": "={{$json.symbol}}"}
                    ]
                }
            }
        )
        
        # AI signal analysis
        analysis_node = N8NWorkflowNode(
            name="AI Signal Analysis",
            type="n8n-nodes-base.httpRequest",
            position=[850, 300],
            parameters={
                "url": "http://localhost:8000/api/analysis/signal",
                "method": "POST",
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {"name": "signal", "value": "={{$node['Signal Webhook'].json}}"},
                        {"name": "market_context", "value": "={{$node['Get Market Context'].json}}"}
                    ]
                }
            }
        )
        
        # Response
        response_node = N8NWorkflowNode(
            name="Response",
            type="n8n-nodes-base.respondToWebhook",
            position=[1050, 300],
            parameters={
                "responseBody": "={{$json}}",
                "responseContentType": "application/json"
            }
        )
        
        connections = {
            "Signal Webhook": {
                "main": [
                    [{"node": "Validate Signal", "type": "main", "index": 0}]
                ]
            },
            "Validate Signal": {
                "main": [
                    [{"node": "Get Market Context", "type": "main", "index": 0}]
                ]
            },
            "Get Market Context": {
                "main": [
                    [{"node": "AI Signal Analysis", "type": "main", "index": 0}]
                ]
            },
            "AI Signal Analysis": {
                "main": [
                    [{"node": "Response", "type": "main", "index": 0}]
                ]
            }
        }
        
        return N8NWorkflow(
            name="Trading Signal Processor",
            nodes=[webhook_node, validate_node, context_node, analysis_node, response_node],
            connections=connections,
            tags=["crypto", "trading", "signals"]
        )
    
    async def setup_crypto_workflows(self) -> List[str]:
        """Set up all predefined crypto analysis workflows.
        
        Returns:
            List of created workflow IDs
        """
        workflow_ids = []
        
        for template_name, template_func in self.workflow_templates.items():
            try:
                workflow = template_func()
                result = await self.create_workflow(workflow)
                workflow_ids.append(result.get("id"))
                logger.info(f"Created workflow: {template_name}")
            except Exception as e:
                logger.error(f"Failed to create workflow {template_name}: {e}")
        
        return workflow_ids
    
    async def create_custom_workflow(
        self,
        name: str,
        nodes: List[Dict[str, Any]],
        connections: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a custom workflow from node definitions.
        
        Args:
            name: Workflow name
            nodes: List of node definitions
            connections: Node connections
            tags: Optional tags
            
        Returns:
            Created workflow data
        """
        # Convert dict nodes to N8NWorkflowNode objects
        workflow_nodes = []
        for node_data in nodes:
            node = N8NWorkflowNode(
                name=node_data["name"],
                type=node_data["type"],
                position=node_data.get("position", [0, 0]),
                parameters=node_data.get("parameters", {}),
                credentials=node_data.get("credentials"),
                typeVersion=node_data.get("typeVersion", 1)
            )
            workflow_nodes.append(node)
        
        workflow = N8NWorkflow(
            name=name,
            nodes=workflow_nodes,
            connections=connections,
            tags=tags or []
        )
        
        return await self.create_workflow(workflow)


# Example usage
async def example_usage():
    """Example of how to use N8NManager."""
    
    async with N8NManager(
        n8n_url="http://localhost:5678",
        api_key="your-n8n-api-key"
    ) as n8n:
        
        # Set up crypto analysis workflows
        workflow_ids = await n8n.setup_crypto_workflows()
        print(f"Created {len(workflow_ids)} workflows")
        
        # Trigger analysis workflow via webhook
        analysis_data = {
            "symbol": "BTCUSDT",
            "query": "What's the current market sentiment?"
        }
        
        result = await n8n.webhook_trigger(
            "webhook/crypto-analysis",
            analysis_data
        )
        print(f"Analysis result: {result}")
        
        # Get workflow executions
        if workflow_ids:
            executions = await n8n.get_workflow_executions(workflow_ids[0])
            print(f"Found {len(executions)} executions")


if __name__ == "__main__":
    asyncio.run(example_usage())