# Database migration information
# This directory contains database migration files for the crypto-llm-analyst application

## Migration Files:
- 001_initial.py: Initial database schema with all core tables
- Future migrations will be added here as the schema evolves

## To apply migrations manually:
1. Ensure PostgreSQL is running
2. Create the database: `createdb crypto_llm_analyst`
3. Run the migration scripts in order

## Tables created:
- cryptocurrency_symbols: Store cryptocurrency symbol information
- ohlc_data: Store OHLC price data
- technical_indicators: Store calculated technical indicators
- market_signals: Store trading signals
- analysis_results: Store AI analysis results
- market_sentiment: Store sentiment analysis data
- knowledge_documents: Store knowledge base documents
- user_sessions: Track user sessions
- user_interactions: Log user interactions
- system_metrics: Store system performance metrics