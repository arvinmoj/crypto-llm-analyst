#!/usr/bin/env python3
"""
Run the Streamlit web interface for the crypto LLM analyst.
"""

import os
import sys
import subprocess

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def main():
    """Main function to run the Streamlit app."""
    
    print("🚀 Starting Crypto LLM Analyst Web Interface...")
    print("=" * 50)
    print("Make sure your API server is running at http://localhost:8000")
    print("You can start it with: python examples/run_api.py")
    print()
    print("The web interface will be available at: http://localhost:8501")
    print("=" * 50)
    
    # Get the path to the Streamlit app
    streamlit_app = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'src', 
        'crypto_llm_analyst', 
        'web', 
        '__init__.py'
    )
    
    # Run Streamlit
    try:
        subprocess.run([
            sys.executable, 
            "-m", 
            "streamlit", 
            "run", 
            streamlit_app,
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--browser.gatherUsageStats=false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        print("Make sure Streamlit is installed: pip install streamlit")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down web interface...")


if __name__ == "__main__":
    main()