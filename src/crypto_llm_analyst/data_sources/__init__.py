"""Bitquery GraphQL WebSocket client for real-time OHLC data."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

import websockets
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.websockets import WebsocketsTransport
import pandas as pd

logger = logging.getLogger(__name__)


class BitqueryClient:
    """Client for fetching BTCUSDT OHLC data from Bitquery GraphQL API."""
    
    def __init__(self, api_key: str, websocket_url: str = "wss://streaming.bitquery.io/graphql"):
        """Initialize Bitquery client.
        
        Args:
            api_key: Bitquery API key for authentication
            websocket_url: WebSocket URL for real-time data
        """
        self.api_key = api_key
        self.websocket_url = websocket_url
        self.client: Optional[Client] = None
        self.transport: Optional[WebsocketsTransport] = None
        self.callbacks: List[Callable] = []
        
    async def connect(self) -> None:
        """Establish connection to Bitquery WebSocket API."""
        try:
            # Set up WebSocket transport with authentication
            self.transport = WebsocketsTransport(
                url=self.websocket_url,
                headers={"X-API-KEY": self.api_key}
            )
            self.client = Client(transport=self.transport, fetch_schema_from_transport=False)
            await self.client.connect_async()
            logger.info("Connected to Bitquery WebSocket API")
        except Exception as e:
            logger.error(f"Failed to connect to Bitquery: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection to Bitquery API."""
        if self.client:
            await self.client.close_async()
            logger.info("Disconnected from Bitquery API")
    
    def add_callback(self, callback: Callable[[Dict], None]) -> None:
        """Add callback function to handle incoming OHLC data.
        
        Args:
            callback: Function to call with OHLC data
        """
        self.callbacks.append(callback)
    
    async def subscribe_btcusdt_5min(self) -> None:
        """Subscribe to BTCUSDT 5-minute OHLC data stream."""
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        # GraphQL subscription for BTCUSDT 5-minute OHLC data
        subscription = gql("""
            subscription {
                EVM(network: bsc) {
                    DEXTradeByTokens(
                        where: {
                            Trade: {
                                Buy: {
                                    Currency: {
                                        SmartContract: {
                                            is: "0x55d398326f99059fF775485246999027B3197955"
                                        }
                                    }
                                },
                                Sell: {
                                    Currency: {
                                        SmartContract: {
                                            is: "0x2170Ed0880ac9A755fd29B2688956BD959F933F8"
                                        }
                                    }
                                }
                            }
                        }
                    ) {
                        Block {
                            Time(interval: {count: 5, in: minutes})
                        }
                        Trade {
                            high: PriceInUSD(maximum: Trade_Buy_Amount)
                            low: PriceInUSD(minimum: Trade_Buy_Amount)
                            open: PriceInUSD(minimum: Block_Number)
                            close: PriceInUSD(maximum: Block_Number)
                        }
                        volume: sum(of: Trade_Buy_Amount)
                        count
                    }
                }
            }
        """)
        
        try:
            async for result in self.client.subscribe_async(subscription):
                await self._process_ohlc_data(result)
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            raise
    
    async def _process_ohlc_data(self, data: Dict[str, Any]) -> None:
        """Process incoming OHLC data and notify callbacks.
        
        Args:
            data: Raw data from Bitquery subscription
        """
        try:
            # Extract OHLC data from response
            trades = data.get("EVM", {}).get("DEXTradeByTokens", [])
            
            for trade in trades:
                ohlc_data = {
                    "timestamp": trade["Block"]["Time"],
                    "symbol": "BTCUSDT",
                    "timeframe": "5m",
                    "open": float(trade["Trade"]["open"]),
                    "high": float(trade["Trade"]["high"]),
                    "low": float(trade["Trade"]["low"]),
                    "close": float(trade["Trade"]["close"]),
                    "volume": float(trade["volume"]),
                    "count": int(trade["count"])
                }
                
                # Notify all registered callbacks
                for callback in self.callbacks:
                    try:
                        await callback(ohlc_data)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                        
        except Exception as e:
            logger.error(f"Error processing OHLC data: {e}")
    
    async def get_historical_data(
        self, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 1000
    ) -> pd.DataFrame:
        """Fetch historical BTCUSDT 5-minute OHLC data.
        
        Args:
            start_time: Start time for historical data
            end_time: End time for historical data
            limit: Maximum number of records to fetch
            
        Returns:
            DataFrame with historical OHLC data
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        query = gql("""
            query GetHistoricalOHLC($startTime: DateTime!, $endTime: DateTime!, $limit: Int!) {
                EVM(network: bsc) {
                    DEXTradeByTokens(
                        where: {
                            Block: {Time: {since: $startTime, till: $endTime}},
                            Trade: {
                                Buy: {
                                    Currency: {
                                        SmartContract: {
                                            is: "0x55d398326f99059fF775485246999027B3197955"
                                        }
                                    }
                                },
                                Sell: {
                                    Currency: {
                                        SmartContract: {
                                            is: "0x2170Ed0880ac9A755fd29B2688956BD959F933F8"
                                        }
                                    }
                                }
                            }
                        }
                        limit: {count: $limit}
                        orderBy: {ascending: Block_Time}
                    ) {
                        Block {
                            Time(interval: {count: 5, in: minutes})
                        }
                        Trade {
                            high: PriceInUSD(maximum: Trade_Buy_Amount)
                            low: PriceInUSD(minimum: Trade_Buy_Amount)
                            open: PriceInUSD(minimum: Block_Number)
                            close: PriceInUSD(maximum: Block_Number)
                        }
                        volume: sum(of: Trade_Buy_Amount)
                        count
                    }
                }
            }
        """)
        
        variables = {
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "limit": limit
        }
        
        try:
            result = await self.client.execute_async(query, variable_values=variables)
            trades = result.get("EVM", {}).get("DEXTradeByTokens", [])
            
            # Convert to DataFrame
            data_list = []
            for trade in trades:
                data_list.append({
                    "timestamp": pd.to_datetime(trade["Block"]["Time"]),
                    "symbol": "BTCUSDT",
                    "timeframe": "5m",
                    "open": float(trade["Trade"]["open"]),
                    "high": float(trade["Trade"]["high"]),
                    "low": float(trade["Trade"]["low"]),
                    "close": float(trade["Trade"]["close"]),
                    "volume": float(trade["volume"]),
                    "count": int(trade["count"])
                })
            
            return pd.DataFrame(data_list)
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise


# Example usage
async def example_usage():
    """Example of how to use BitqueryClient."""
    
    # Initialize client (you'll need a real API key)
    client = BitqueryClient(api_key="your_bitquery_api_key")
    
    # Define callback for handling real-time data
    async def handle_ohlc_data(data: Dict[str, Any]) -> None:
        print(f"Received OHLC data: {data}")
        # Here you would typically save to database or process further
    
    try:
        # Connect and subscribe
        await client.connect()
        client.add_callback(handle_ohlc_data)
        
        # Start real-time subscription
        await client.subscribe_btcusdt_5min()
        
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())