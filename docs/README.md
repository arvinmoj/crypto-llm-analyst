# Crypto LLM Analyst - Project Documentation

## Overview

The Crypto LLM Analyst is a sophisticated cryptocurrency analysis platform that leverages artificial intelligence, real-time data processing, and automated workflows to provide comprehensive market insights and trading recommendations.

## Architecture

### System Components

1. **Data Layer**
   - Real-time cryptocurrency data streaming via Bitquery WebSocket API
   - OHLC (Open, High, Low, Close) data processing and storage
   - Technical indicator calculations (RSI, MACD, Bollinger Bands)

2. **AI/ML Layer** 
   - LangChain-based analysis agents
   - OpenAI GPT integration for natural language processing
   - RAG (Retrieval-Augmented Generation) system for knowledge enhancement
   - MCP (Model Context Protocol) tools for modular analysis

3. **API Layer**
   - FastAPI REST endpoints
   - WebSocket support for real-time updates
   - Authentication and rate limiting

4. **Database Layer**
   - PostgreSQL for persistent data storage
   - Redis for caching and session management
   - Optimized indexes for time-series queries

5. **Automation Layer**
   - N8N workflows for automated analysis
   - Alert generation and notification systems
   - Scheduled data processing tasks

### Data Flow

```
Bitquery API → Data Processor → Technical Indicators → AI Analysis → API Response
     ↓              ↓               ↓                    ↓
Database ← Redis Cache ← Knowledge Base ← Market Signals
```

## API Documentation

### Authentication
Currently using API key authentication. Include your API key in the header:
```
Authorization: Bearer YOUR_API_KEY
```

### Core Endpoints

#### GET /api/v1/analysis/{symbol}/quick
Quick analysis for a cryptocurrency symbol.

**Parameters:**
- `symbol` (path): Cryptocurrency symbol (e.g., BTC, ETH)

**Response:**
```json
{
  "symbol": "BTC",
  "current_price": 50000.0,
  "trend": "bullish",
  "rsi": 65.5,
  "signal_type": "HOLD",
  "confidence": 0.75,
  "recommendation": "Monitor for breakout above resistance",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET /api/v1/analysis/{symbol}/comprehensive
Comprehensive analysis including technical indicators, sentiment, and risk assessment.

**Response:**
```json
{
  "symbol": "BTC",
  "analysis_type": "comprehensive",
  "summary": "Bitcoin shows mixed signals...",
  "technical_analysis": {
    "rsi": 65.5,
    "macd": {"value": 120.5, "signal": "bullish"},
    "support_levels": [48000, 46500],
    "resistance_levels": [52000, 54000]
  },
  "sentiment_analysis": {
    "overall_score": 0.65,
    "social_sentiment": 0.7,
    "news_sentiment": 0.6
  },
  "recommendations": ["Consider DCA strategy", "Set stop-loss at $48,000"],
  "confidence": 0.78,
  "risk_assessment": {
    "risk_score": 0.45,
    "volatility": 0.78,
    "var_1d": -0.05
  }
}
```

#### POST /api/v1/chat
Interactive chat interface for natural language queries.

**Request Body:**
```json
{
  "message": "Should I buy Bitcoin now?",
  "session_id": "optional_session_id"
}
```

**Response:**
```json
{
  "response": "Based on current analysis, Bitcoin shows...",
  "session_id": "session_123",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET /api/v1/knowledge/query
Query the knowledge base using RAG system.

**Parameters:**
- `q` (query): Search query
- `max_results` (optional): Maximum number of results (default: 5)

**Response:**
```json
{
  "query": "What is technical analysis?",
  "answer": "Technical analysis is the study of price charts...",
  "confidence": 0.9,
  "sources": [
    {
      "title": "Technical Analysis Fundamentals",
      "category": "analysis",
      "content_preview": "Technical analysis involves studying..."
    }
  ],
  "processing_time": 0.5
}
```

## Configuration Guide

### Environment Variables

The application uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/crypto_llm_analyst
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/crypto_llm_analyst_test

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Bitquery Configuration
BITQUERY_API_KEY=your_bitquery_api_key_here
BITQUERY_ENDPOINT=https://streaming.bitquery.io/graphql

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

### Database Setup

1. **Create PostgreSQL database:**
   ```sql
   CREATE DATABASE crypto_llm_analyst;
   CREATE USER crypto_user WITH ENCRYPTED PASSWORD 'crypto_pass';
   GRANT ALL PRIVILEGES ON DATABASE crypto_llm_analyst TO crypto_user;
   ```

2. **Initialize tables:**
   ```python
   from database.models import init_database
   init_database()
   ```

3. **Apply migrations:**
   ```bash
   # Migrations are in database/migrations/
   # Apply them in order: 001_initial.py, etc.
   ```

## Development Guide

### Setting Up Development Environment

1. **Clone repository:**
   ```bash
   git clone https://github.com/arvinmoj/crypto-llm-analyst.git
   cd crypto-llm-analyst
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Setup pre-commit hooks:**
   ```bash
   pre-commit install
   ```

5. **Run tests:**
   ```bash
   pytest
   ```

### Code Structure Guidelines

- **Modules**: Each major component is in its own module (data/, ai/, api/, etc.)
- **Models**: Database models in `database/models.py`
- **Configuration**: Centralized in `config/settings.py`
- **Tests**: Mirror the source structure in `tests/`
- **Documentation**: Keep docs up to date in `docs/`

### Adding New Features

1. **Create feature branch:** `git checkout -b feature/new-feature`
2. **Write tests first:** Add tests in appropriate test file
3. **Implement feature:** Follow existing patterns and conventions
4. **Update documentation:** Update relevant docs and API documentation
5. **Run tests:** Ensure all tests pass
6. **Submit PR:** Create pull request with clear description

## Deployment Guide

### Docker Deployment

The easiest way to deploy is using Docker Compose:

```bash
# Set required environment variables
export OPENAI_API_KEY="your_key"
export BITQUERY_API_KEY="your_key"

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs crypto-llm-analyst
```

### Production Deployment

1. **Server Requirements:**
   - 4+ GB RAM
   - 2+ CPU cores
   - 50+ GB disk space
   - Ubuntu 20.04+ or similar

2. **Install Dependencies:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install PostgreSQL
   sudo apt install postgresql postgresql-contrib
   
   # Install Redis
   sudo apt install redis-server
   
   # Install Python 3.9+
   sudo apt install python3.9 python3.9-venv python3.9-dev
   ```

3. **Setup Application:**
   ```bash
   # Create application user
   sudo useradd -m -s /bin/bash crypto-analyst
   
   # Clone repository
   sudo -u crypto-analyst git clone https://github.com/arvinmoj/crypto-llm-analyst.git /home/crypto-analyst/app
   
   # Setup virtual environment
   cd /home/crypto-analyst/app
   sudo -u crypto-analyst python3.9 -m venv venv
   sudo -u crypto-analyst ./venv/bin/pip install -r requirements.txt
   ```

4. **Configure Services:**
   ```bash
   # Copy systemd service file
   sudo cp deployment/crypto-llm-analyst.service /etc/systemd/system/
   
   # Enable and start service
   sudo systemctl enable crypto-llm-analyst
   sudo systemctl start crypto-llm-analyst
   ```

5. **Setup Reverse Proxy (Nginx):**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

### Monitoring and Logging

The application includes built-in monitoring:

1. **Health Checks:**
   - Endpoint: `/health`
   - Checks all service dependencies

2. **Prometheus Metrics:**
   - Available on port 9090
   - Custom metrics for API performance, AI processing times

3. **Structured Logging:**
   - JSON format logs
   - Configurable log levels
   - Centralized logging with ELK stack support

4. **Grafana Dashboards:**
   - Pre-configured dashboards for monitoring
   - Real-time metrics visualization

## Troubleshooting

### Common Issues

1. **Database Connection Errors:**
   ```bash
   # Check PostgreSQL service
   sudo systemctl status postgresql
   
   # Check connection
   psql -h localhost -U crypto_user -d crypto_llm_analyst
   ```

2. **Redis Connection Issues:**
   ```bash
   # Check Redis service
   sudo systemctl status redis-server
   
   # Test connection
   redis-cli ping
   ```

3. **OpenAI API Errors:**
   - Verify API key is correct
   - Check API usage limits
   - Monitor rate limiting

4. **Memory Issues:**
   - Monitor AI model memory usage
   - Implement model caching
   - Consider using smaller models for development

### Performance Optimization

1. **Database Optimization:**
   - Use connection pooling
   - Optimize queries with proper indexes
   - Implement data archiving for old records

2. **Caching Strategy:**
   - Cache frequent API responses in Redis
   - Implement application-level caching
   - Use CDN for static content

3. **API Performance:**
   - Implement request rate limiting
   - Use async/await for I/O operations
   - Monitor endpoint response times

## Security Considerations

1. **API Security:**
   - Use HTTPS in production
   - Implement proper authentication
   - Validate all input parameters
   - Use CORS appropriately

2. **Database Security:**
   - Use strong passwords
   - Limit database user permissions
   - Enable SSL connections
   - Regular security updates

3. **Environment Security:**
   - Keep dependencies updated
   - Use secrets management
   - Monitor for vulnerabilities
   - Implement proper logging and monitoring

## Support and Contributing

### Getting Help
- Check the documentation first
- Search existing GitHub issues
- Join our Discord community (if available)
- Create a new issue with detailed information

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

### Code of Conduct
Please be respectful and constructive in all interactions. We welcome contributions from developers of all skill levels.