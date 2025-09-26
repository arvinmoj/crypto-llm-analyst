-- Create database initialization script
CREATE DATABASE IF NOT EXISTS crypto_llm_analyst;
CREATE USER IF NOT EXISTS crypto_user WITH ENCRYPTED PASSWORD 'crypto_pass';
GRANT ALL PRIVILEGES ON DATABASE crypto_llm_analyst TO crypto_user;