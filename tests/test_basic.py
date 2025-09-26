"""Basic tests for crypto LLM analyst components."""

import pytest
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from crypto_llm_analyst.main import CryptoLLMAnalyst
from crypto_llm_analyst.data_sources import BitqueryClient
from crypto_llm_analyst.database import SupabaseManager
from crypto_llm_analyst.llm import LangChainManager
from crypto_llm_analyst.rag import CryptoRAGSystem
from crypto_llm_analyst.mcp import MCPProtocol, MCPMessage, MCPMessageType
from crypto_llm_analyst.workflows import N8NManager


class TestCryptoLLMAnalyst:
    """Test the main system orchestrator."""
    
    def test_initialization(self):
        """Test system initialization."""
        config = {"openai_api_key": "test-key"}
        system = CryptoLLMAnalyst(config)
        
        assert system.config == config
        assert not system.components_initialized
        assert not system.data_streaming
    
    def test_get_system_status(self):
        """Test system status reporting."""
        system = CryptoLLMAnalyst()
        status = system.get_system_status()
        
        assert isinstance(status, dict)
        assert "components_initialized" in status
        assert "data_streaming" in status


class TestBitqueryClient:
    """Test Bitquery client."""
    
    def test_initialization(self):
        """Test client initialization."""
        client = BitqueryClient("test-api-key")
        
        assert client.api_key == "test-api-key"
        assert client.client is None
        assert len(client.callbacks) == 0
    
    def test_add_callback(self):
        """Test callback registration."""
        client = BitqueryClient("test-api-key")
        
        def test_callback(data):
            pass
        
        client.add_callback(test_callback)
        assert len(client.callbacks) == 1


class TestSupabaseManager:
    """Test Supabase manager."""
    
    def test_initialization(self):
        """Test manager initialization."""
        manager = SupabaseManager("https://test.supabase.co", "test-key")
        
        assert manager.url == "https://test.supabase.co"
        assert manager.key == "test-key"
        assert manager.client is not None


class TestLangChainManager:
    """Test LangChain manager."""
    
    def test_initialization(self):
        """Test manager initialization."""
        manager = LangChainManager("test-openai-key")
        
        assert manager.openai_api_key == "test-openai-key"
        assert manager.model == "gpt-4"
        assert manager.temperature == 0.7
        assert manager.llm is not None
    
    def test_prompt_templates(self):
        """Test prompt templates."""
        manager = LangChainManager("test-openai-key")
        
        assert hasattr(manager, 'prompts')
        assert manager.market_analysis_chain is not None


class TestCryptoRAGSystem:
    """Test RAG system."""
    
    def test_initialization(self):
        """Test RAG system initialization."""
        rag = CryptoRAGSystem("test-openai-key", "./test_chroma")
        
        assert rag.openai_api_key == "test-openai-key"
        assert rag.persist_directory == "./test_chroma"
        assert rag.embeddings is not None


class TestMCPProtocol:
    """Test MCP protocol."""
    
    def test_initialization(self):
        """Test MCP protocol initialization."""
        mcp = MCPProtocol("test-system")
        
        assert mcp.system_name == "test-system"
        assert "resources" in mcp.capabilities
        assert "tools" in mcp.capabilities
    
    def test_message_creation(self):
        """Test MCP message creation."""
        message = MCPMessage(
            id="test-id",
            type=MCPMessageType.REQUEST,
            method="test_method",
            params={"test": "param"}
        )
        
        assert message.id == "test-id"
        assert message.type == MCPMessageType.REQUEST
        assert message.method == "test_method"
        assert message.params["test"] == "param"
    
    def test_message_serialization(self):
        """Test message serialization."""
        message = MCPMessage(
            id="test-id",
            type=MCPMessageType.REQUEST,
            method="test_method"
        )
        
        data = message.to_dict()
        assert data["id"] == "test-id"
        assert data["type"] == "request"
        assert data["method"] == "test_method"
        
        # Test deserialization
        restored = MCPMessage.from_dict(data)
        assert restored.id == message.id
        assert restored.type == message.type


class TestN8NManager:
    """Test N8N manager."""
    
    def test_initialization(self):
        """Test N8N manager initialization."""
        manager = N8NManager("http://localhost:5678", "test-api-key")
        
        assert manager.n8n_url == "http://localhost:5678"
        assert manager.api_key == "test-api-key"
    
    def test_workflow_templates(self):
        """Test workflow template creation."""
        manager = N8NManager("http://localhost:5678")
        
        assert "crypto_analysis_pipeline" in manager.workflow_templates
        assert "price_alert_system" in manager.workflow_templates
        
        # Test template creation
        template = manager._create_analysis_pipeline_template()
        assert template.name == "Crypto Analysis Pipeline"
        assert len(template.nodes) > 0
        assert template.connections is not None


# Integration tests (require async)
class TestAsyncComponents:
    """Test async functionality."""
    
    @pytest.mark.asyncio
    async def test_mcp_message_handling(self):
        """Test MCP message handling."""
        mcp = MCPProtocol("test-system")
        
        # Test initialize message
        request = {
            "id": "test-001",
            "type": "request", 
            "method": "initialize",
            "params": {}
        }
        
        response = await mcp.handle_message(request)
        
        assert response["id"] == "test-001"
        assert "result" in response
        assert "capabilities" in response["result"]
    
    @pytest.mark.asyncio
    async def test_system_shutdown(self):
        """Test system shutdown."""
        system = CryptoLLMAnalyst()
        
        # Should not raise an error
        await system.shutdown()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])