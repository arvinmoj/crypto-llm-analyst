# Crypto LLM Analyst

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**LLM-Powered Applications for Cryptocurrency OHLC Data Analysis**

A comprehensive cryptocurrency analysis platform that combines real-time data streaming, advanced AI analysis, and automated trading recommendations using Large Language Models (LLMs), RAG systems, and modern data processing techniques.

## 🚀 Features

### Core Capabilities
- **Real-time Data Streaming**: Bitquery integration for live cryptocurrency data
- **AI-Powered Analysis**: LangChain agents with OpenAI GPT models
- **Technical Analysis**: RSI, MACD, Bollinger Bands, and custom indicators
- **Sentiment Analysis**: Multi-source sentiment aggregation (social, news, on-chain)
- **RAG System**: Knowledge-enhanced responses using retrieval-augmented generation
- **MCP Tools**: Modular analysis tools for comprehensive market assessment
- **Risk Management**: Advanced risk assessment and portfolio optimization

### Technology Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis
- **AI/ML**: LangChain, OpenAI, HuggingFace Transformers
- **Data**: Pandas, NumPy, real-time WebSocket streaming
- **Automation**: N8N workflows for automated analysis and alerts
- **Monitoring**: Prometheus, Grafana, structured logging
- **Containerization**: Docker, Docker Compose

## 📁 Project Structure

```
crypto-llm-analyst/
├── data/                          # Data processing and streaming
│   ├── __init__.py
│   ├── bitquery_stream.py         # Bitquery WebSocket streaming client
│   └── data_processor.py          # OHLC data processing and indicators
├── ai/                            # AI and machine learning modules
│   ├── __init__.py
│   ├── mcp_tools.py              # Model Context Protocol tools
│   ├── rag_system.py             # Retrieval-Augmented Generation
│   └── langchain_agent.py        # LangChain-based analysis agent
├── database/                      # Database models and migrations
│   ├── __init__.py
│   ├── models.py                 # SQLAlchemy models
│   ├── init.sql                  # Database initialization
│   └── migrations/               # Database migration files
│       ├── README.md
│       └── 001_initial.py
├── api/                          # REST API endpoints
│   ├── __init__.py
│   └── main.py                   # FastAPI application
├── config/                       # Configuration management
│   ├── __init__.py
│   ├── settings.py               # Application settings
│   └── logging.py                # Logging configuration
├── n8n-workflows/                # Automation workflows
│   └── btc_analysis.json         # Bitcoin analysis workflow
├── tests/                        # Test suite
│   ├── conftest.py               # Test configuration
│   ├── test_data_processor.py    # Data processing tests
│   └── test_mcp_tools.py         # MCP tools tests
├── docs/                         # Documentation
├── monitoring/                   # Monitoring configuration
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Development dependencies
├── pyproject.toml               # Project configuration
├── docker-compose.yml           # Multi-service deployment
├── Dockerfile                   # Container image
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Docker (optional)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/arvinmoj/crypto-llm-analyst.git
   cd crypto-llm-analyst
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Initialize database**
   ```bash
   python -m database.models  # Create tables
   ```

6. **Run the application**
   ```bash
   python -m api.main
   ```

### Docker Deployment

1. **Using Docker Compose (Recommended)**
   ```bash
   # Set environment variables
   export OPENAI_API_KEY="your_openai_key"
   export BITQUERY_API_KEY="your_bitquery_key"
   
   # Start all services
   docker-compose up -d
   ```

2. **Access the services**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - N8N Workflows: http://localhost:5678
   - Grafana Dashboard: http://localhost:3000
   - Prometheus: http://localhost:9090

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/crypto_llm_analyst

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Bitquery
BITQUERY_API_KEY=your_bitquery_api_key_here
BITQUERY_ENDPOINT=https://streaming.bitquery.io/graphql

# API
API_HOST=0.0.0.0
API_PORT=8000

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

## 📖 Usage

### REST API Endpoints

#### Quick Analysis
```bash
curl http://localhost:8000/api/v1/analysis/BTC/quick
```

#### Comprehensive Analysis
```bash
curl http://localhost:8000/api/v1/analysis/BTC/comprehensive
```

#### Chat Interface
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Should I buy Bitcoin now?"}'
```

#### Knowledge Query
```bash
curl "http://localhost:8000/api/v1/knowledge/query?q=What%20is%20technical%20analysis"
```

### Python SDK Usage

```python
from crypto_llm_analyst.ai.langchain_agent import CryptoAnalysisAgent, AnalysisRequest

# Initialize the agent
agent = CryptoAnalysisAgent()

# Create analysis request
request = AnalysisRequest(
    symbol="BTC",
    analysis_type="comprehensive",
    user_query="Should I buy Bitcoin now?"
)

# Get analysis
response = await agent.analyze(request)
print(f"Recommendation: {response.summary}")
print(f"Confidence: {response.confidence}")
```

### Data Streaming

```python
from crypto_llm_analyst.data.bitquery_stream import create_streamer_from_env

# Create streamer
streamer = create_streamer_from_env()

# Stream OHLC data
async for ohlc in streamer.subscribe_to_ohlc(["BTC", "ETH"]):
    print(f"Price update: {ohlc.symbol} @ ${ohlc.close}")
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=crypto_llm_analyst

# Run specific test file
pytest tests/test_data_processor.py -v
```

## 📊 Monitoring

The application includes comprehensive monitoring:

- **Health Checks**: `/health` endpoint
- **Metrics**: Prometheus metrics on port 9090
- **Logging**: Structured JSON logs
- **Grafana**: Pre-configured dashboards

## 🤖 N8N Automation

The included N8N workflow (`n8n-workflows/btc_analysis.json`) provides:

- Scheduled analysis runs (every 15 minutes)
- Automated alert generation
- Volume spike detection
- Sentiment monitoring
- Data storage automation

## 🛡️ Security Features

- Environment-based configuration
- API key authentication
- Rate limiting
- Input validation
- SQL injection protection
- CORS configuration

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Production environment variables
   ENVIRONMENT=production
   DEBUG=false
   API_DEBUG=false
   LOG_LEVEL=WARNING
   ```

2. **Database Migration**
   ```bash
   # Apply database migrations
   python -c "from database.models import init_database; init_database()"
   ```

3. **Service Deployment**
   ```bash
   # Using systemd or supervisor
   sudo systemctl start crypto-llm-analyst
   sudo systemctl enable crypto-llm-analyst
   ```

### Scaling Considerations

- Use Redis for caching and session storage
- Implement database connection pooling
- Consider multiple API instances behind a load balancer
- Monitor memory usage for AI models

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Use type hints where possible

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Bitquery](https://bitquery.io/) for cryptocurrency data APIs
- [OpenAI](https://openai.com/) for GPT models
- [LangChain](https://langchain.com/) for AI framework
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

## 📞 Support

- Documentation: [/docs](http://localhost:8000/docs)
- Issues: [GitHub Issues](https://github.com/arvinmoj/crypto-llm-analyst/issues)
- Discussions: [GitHub Discussions](https://github.com/arvinmoj/crypto-llm-analyst/discussions)

---

**Disclaimer**: This software is for educational and research purposes only. Always conduct your own research before making investment decisions. Cryptocurrency trading carries inherent risks.
