"""
Configuration module for crypto-llm-analyst.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    url: str = Field(default="postgresql://user:password@localhost:5432/crypto_llm_analyst", env="DATABASE_URL")
    test_url: str = Field(default="postgresql://user:password@localhost:5432/crypto_llm_analyst_test", env="TEST_DATABASE_URL")
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True
    
    class Config:
        env_prefix = "DB_"


class RedisConfig(BaseSettings):
    """Redis configuration"""
    url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    decode_responses: bool = True
    max_connections: int = 100
    
    class Config:
        env_prefix = "REDIS_"


class APIConfig(BaseSettings):
    """API configuration"""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="API_DEBUG")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    class Config:
        env_prefix = "API_"


class OpenAIConfig(BaseSettings):
    """OpenAI configuration"""
    api_key: str = Field(env="OPENAI_API_KEY")
    model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    
    class Config:
        env_prefix = "OPENAI_"


class BitqueryConfig(BaseSettings):
    """Bitquery configuration"""
    api_key: str = Field(env="BITQUERY_API_KEY")
    endpoint: str = Field(default="https://streaming.bitquery.io/graphql", env="BITQUERY_ENDPOINT")
    symbols: List[str] = Field(default=["BTC", "ETH"], env="BITQUERY_SYMBOLS")
    
    class Config:
        env_prefix = "BITQUERY_"


class LoggingConfig(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")
    file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    class Config:
        env_prefix = "LOG_"


class SecurityConfig(BaseSettings):
    """Security configuration"""
    secret_key: str = Field(env="SECRET_KEY")
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=1440, env="JWT_EXPIRE_MINUTES")
    
    class Config:
        env_prefix = "SECURITY_"


class MonitoringConfig(BaseSettings):
    """Monitoring configuration"""
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    health_check_interval: int = Field(default=60, env="HEALTH_CHECK_INTERVAL")
    
    class Config:
        env_prefix = "MONITORING_"


class N8NConfig(BaseSettings):
    """N8N configuration"""
    webhook_url: str = Field(default="http://localhost:5678/webhook", env="N8N_WEBHOOK_URL")
    api_key: str = Field(default="", env="N8N_API_KEY")
    
    class Config:
        env_prefix = "N8N_"


class AppConfig(BaseSettings):
    """Main application configuration"""
    name: str = "crypto-llm-analyst"
    version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Sub-configurations
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    api: APIConfig = APIConfig()
    openai: OpenAIConfig = OpenAIConfig()
    bitquery: BitqueryConfig = BitqueryConfig()
    logging: LoggingConfig = LoggingConfig()
    security: SecurityConfig = SecurityConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    n8n: N8NConfig = N8NConfig()
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global configuration instance
config = AppConfig()