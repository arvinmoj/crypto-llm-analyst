# Development setup script for crypto-llm-analyst

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/macOS
    source venv/bin/activate
fi

# Upgrade pip
pip install --upgrade pip

# Install package in development mode
echo "Installing package and dependencies..."
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Create necessary directories
echo "Creating directories..."
mkdir -p chroma_db
mkdir -p logs
mkdir -p data

# Copy environment template
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your API keys"
else
    echo ".env file already exists"
fi

# Install pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

echo "Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'python examples/demo.py' to test the system"
echo "3. Run 'python examples/run_api.py' to start the API server"
echo "4. Run 'python examples/run_web.py' to start the web interface"