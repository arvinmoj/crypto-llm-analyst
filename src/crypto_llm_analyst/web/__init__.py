"""Streamlit web interface for crypto LLM analyst."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Crypto LLM Analyst",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .analysis-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    
    .confidence-high { color: #28a745; font-weight: bold; }
    .confidence-medium { color: #ffc107; font-weight: bold; }
    .confidence-low { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000"  # Default API URL

def get_api_url():
    """Get API URL from sidebar or default."""
    return st.sidebar.text_input("API URL", value=API_BASE_URL)

def make_api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
    """Make API request with error handling."""
    api_url = get_api_url()
    url = f"{api_url}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return {"success": False, "error": response.text}
    
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {str(e)}")
        return {"success": False, "error": str(e)}

def format_confidence(confidence: float) -> str:
    """Format confidence score with color coding."""
    if confidence >= 0.8:
        return f'<span class="confidence-high">{confidence:.1%}</span>'
    elif confidence >= 0.6:
        return f'<span class="confidence-medium">{confidence:.1%}</span>'
    else:
        return f'<span class="confidence-low">{confidence:.1%}</span>'

def create_ohlc_chart(ohlc_data: List[Dict]) -> go.Figure:
    """Create OHLC candlestick chart."""
    if not ohlc_data:
        return go.Figure()
    
    df = pd.DataFrame(ohlc_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Create candlestick chart
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('BTCUSDT Price', 'Volume'),
        row_heights=[0.7, 0.3]
    )
    
    # Add candlestick
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='BTCUSDT',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )
    
    # Add volume
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            name='Volume',
            marker_color='rgba(158,202,225,0.5)'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title="BTCUSDT Price Chart",
        xaxis_title="Time",
        yaxis_title="Price (USDT)",
        height=600,
        showlegend=False,
        xaxis_rangeslider_visible=False
    )
    
    return fig

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">📈 Crypto LLM Analyst</h1>', unsafe_allow_html=True)
    st.markdown("**LLM-Powered Applications for OHLC Data Analysis**")
    
    # Sidebar
    st.sidebar.title("🛠️ Configuration")
    
    # Symbol selection
    symbol = st.sidebar.selectbox(
        "Trading Symbol",
        ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT"],
        index=0
    )
    
    # Refresh data button
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    # API status check
    with st.sidebar.expander("📊 System Status"):
        status_response = make_api_request("/api/system/status")
        if status_response.get("success", True):  # Assume success if no 'success' key
            for component, status in status_response.items():
                if component != "timestamp":
                    emoji = "✅" if status else "❌"
                    st.write(f"{emoji} {component.replace('_', ' ').title()}: {'Online' if status else 'Offline'}")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "💬 Analysis", "🔮 Predictions", "📈 Technical Analysis", "📜 History"])
    
    with tab1:
        st.header("Market Dashboard")
        
        # Market summary
        with st.spinner("Loading market data..."):
            market_response = make_api_request(f"/api/market/summary?symbol={symbol}")
            
            if market_response.get("success"):
                market_data = market_response["data"]
                
                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Current Price",
                        f"${market_data.get('current_price', 0):,.2f}",
                        delta=f"${market_data.get('price_change_24h', 0):,.2f}"
                    )
                
                with col2:
                    st.metric(
                        "24h High",
                        f"${market_data.get('high_24h', 0):,.2f}"
                    )
                
                with col3:
                    st.metric(
                        "24h Low",
                        f"${market_data.get('low_24h', 0):,.2f}"
                    )
                
                with col4:
                    st.metric(
                        "24h Volume",
                        f"{market_data.get('volume_24h', 0):,.0f}",
                        delta=f"{market_data.get('price_change_percent_24h', 0):+.2f}%"
                    )
            else:
                st.error("Failed to load market data")
        
        # OHLC Chart
        st.subheader("Price Chart")
        ohlc_response = make_api_request(f"/api/market/ohlc?symbol={symbol}&limit=50")
        
        if ohlc_response.get("success"):
            ohlc_data = ohlc_response["data"]
            if ohlc_data:
                chart = create_ohlc_chart(ohlc_data)
                st.plotly_chart(chart, use_container_width=True)
            else:
                st.info("No OHLC data available")
        else:
            st.error("Failed to load OHLC data")
    
    with tab2:
        st.header("💬 AI Market Analysis")
        
        # Analysis input
        analysis_query = st.text_area(
            "What would you like to analyze?",
            placeholder="e.g., What's the current market sentiment? Should I buy or sell? What are the key resistance levels?",
            height=100
        )
        
        analysis_type = st.selectbox(
            "Analysis Type",
            ["general", "market", "sentiment", "risk_assessment"],
            index=0
        )
        
        if st.button("🔍 Analyze", type="primary"):
            if analysis_query:
                with st.spinner("Analyzing with AI..."):
                    analysis_data = {
                        "symbol": symbol,
                        "query": analysis_query,
                        "analysis_type": analysis_type
                    }
                    
                    analysis_response = make_api_request(
                        "/api/analysis/market", 
                        method="POST", 
                        data=analysis_data
                    )
                    
                    if analysis_response.get("success"):
                        result = analysis_response["data"]
                        
                        # Display confidence
                        confidence_html = format_confidence(result.get("confidence", 0))
                        st.markdown(f"**Confidence:** {confidence_html}", unsafe_allow_html=True)
                        
                        # Display analysis
                        st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
                        st.markdown(result.get("analysis", "No analysis available"))
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Display metadata
                        with st.expander("Analysis Details"):
                            st.json({
                                "timestamp": result.get("timestamp"),
                                "analysis_type": result.get("analysis_type"),
                                "context_used": result.get("context_used")
                            })
                    else:
                        st.error("Analysis failed")
            else:
                st.warning("Please enter your analysis question")
    
    with tab3:
        st.header("🔮 Price Predictions")
        
        # Prediction input
        prediction_query = st.text_area(
            "What would you like to predict?",
            placeholder="e.g., What will be the price in the next 24 hours? Will Bitcoin reach $50,000 this week?",
            height=100
        )
        
        horizon = st.selectbox(
            "Prediction Horizon",
            ["1h", "4h", "24h", "7d", "30d"],
            index=2
        )
        
        if st.button("🎯 Predict", type="primary"):
            if prediction_query:
                with st.spinner("Generating prediction..."):
                    prediction_data = {
                        "symbol": symbol,
                        "query": prediction_query,
                        "horizon": horizon
                    }
                    
                    prediction_response = make_api_request(
                        "/api/analysis/predict", 
                        method="POST", 
                        data=prediction_data
                    )
                    
                    if prediction_response.get("success"):
                        result = prediction_response["data"]
                        
                        # Display confidence
                        confidence_html = format_confidence(result.get("confidence", 0))
                        st.markdown(f"**Confidence:** {confidence_html}", unsafe_allow_html=True)
                        
                        # Display prediction
                        st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
                        st.markdown(result.get("analysis", "No prediction available"))
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Disclaimer
                        st.warning("⚠️ **Disclaimer:** Predictions are based on historical data and AI analysis. Cryptocurrency markets are highly volatile and unpredictable. This is not financial advice.")
                    else:
                        st.error("Prediction failed")
            else:
                st.warning("Please enter your prediction question")
    
    with tab4:
        st.header("📈 Technical Analysis")
        
        # Technical analysis input
        technical_query = st.text_area(
            "Technical analysis question:",
            placeholder="e.g., What do the moving averages indicate? Are we in overbought territory? What are the key support levels?",
            height=100
        )
        
        if st.button("📊 Analyze Technicals", type="primary"):
            if technical_query:
                with st.spinner("Performing technical analysis..."):
                    technical_data = {
                        "symbol": symbol,
                        "query": technical_query
                    }
                    
                    technical_response = make_api_request(
                        "/api/analysis/technical", 
                        method="POST", 
                        data=technical_data
                    )
                    
                    if technical_response.get("success"):
                        result = technical_response["data"]
                        
                        # Display confidence
                        confidence_html = format_confidence(result.get("confidence", 0))
                        st.markdown(f"**Confidence:** {confidence_html}", unsafe_allow_html=True)
                        
                        # Display analysis
                        st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
                        st.markdown(result.get("analysis", "No technical analysis available"))
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.error("Technical analysis failed")
            else:
                st.warning("Please enter your technical analysis question")
    
    with tab5:
        st.header("📜 Analysis History")
        
        # History filters
        col1, col2 = st.columns(2)
        with col1:
            history_type = st.selectbox(
                "Analysis Type Filter",
                ["All", "market", "technical_analysis", "price_prediction", "general"],
                index=0
            )
        
        with col2:
            history_limit = st.number_input("Number of Records", min_value=5, max_value=50, value=10)
        
        if st.button("📚 Load History"):
            with st.spinner("Loading analysis history..."):
                params = f"?symbol={symbol}&limit={history_limit}"
                if history_type != "All":
                    params += f"&analysis_type={history_type}"
                
                history_response = make_api_request(f"/api/history/analysis{params}")
                
                if history_response.get("analysis_history"):
                    history_data = history_response["analysis_history"]
                    
                    for i, analysis in enumerate(history_data):
                        with st.expander(f"Analysis {i+1}: {analysis.get('analysis_type', 'Unknown')} - {analysis.get('timestamp', 'Unknown time')[:19]}"):
                            st.markdown(f"**Query:** {analysis.get('query', 'N/A')}")
                            st.markdown(f"**Confidence:** {format_confidence(analysis.get('confidence', 0))}", unsafe_allow_html=True)
                            st.markdown("**Response:**")
                            st.markdown(analysis.get('response', 'No response available'))
                else:
                    st.info("No analysis history found")
    
    # Footer
    st.markdown("---")
    st.markdown("🤖 **Crypto LLM Analyst** - Powered by LangChain, RAG, and advanced AI models")

def run_streamlit():
    """Run the Streamlit application."""
    # This function can be called from the main application
    pass

if __name__ == "__main__":
    main()