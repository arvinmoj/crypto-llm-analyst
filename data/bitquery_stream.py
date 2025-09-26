"""
Bitquery streaming client for real-time cryptocurrency data.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, List, Optional, Any
import websockets
import aiohttp
from dataclasses import dataclass
from datetime import datetime
import os

logger = logging.getLogger(__name__)


@dataclass
class OHLCData:
    """OHLC data structure"""
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    exchange: Optional[str] = None


@dataclass
class StreamConfig:
    """Configuration for Bitquery streaming"""
    api_key: str
    endpoint: str = "wss://streaming.bitquery.io/graphql"
    symbols: List[str] = None
    timeframe: str = "1m"
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["BTC/USD", "ETH/USD"]


class BitqueryStreamer:
    """Real-time cryptocurrency data streamer using Bitquery API"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.websocket = None
        self.is_streaming = False
        
    async def connect(self) -> bool:
        """Connect to Bitquery websocket"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            self.websocket = await websockets.connect(
                self.config.endpoint,
                extra_headers=headers
            )
            self.is_streaming = True
            logger.info("Connected to Bitquery stream")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Bitquery: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from websocket"""
        if self.websocket:
            await self.websocket.close()
            self.is_streaming = False
            logger.info("Disconnected from Bitquery stream")
    
    async def subscribe_to_ohlc(self, symbols: Optional[List[str]] = None) -> AsyncGenerator[OHLCData, None]:
        """Subscribe to OHLC data stream"""
        if not self.is_streaming:
            await self.connect()
            
        symbols = symbols or self.config.symbols
        
        # GraphQL subscription for OHLC data
        subscription = {
            "query": """
            subscription {
                EVM(dataset: combined, network: ethereum) {
                    DEXTrades(
                        orderBy: {descending: Block_Time}
                        where: {Trade: {Currency: {Symbol: {in: ["%s"]}}}}
                    ) {
                        Block {
                            Time(interval: {in: minute, count: 1})
                        }
                        Trade {
                            Currency {
                                Symbol
                            }
                            Buy {
                                Price
                            }
                            Sell {
                                Price
                            }
                            Amount
                        }
                        volume: sum(of: Trade_Amount)
                        priceOpen: minimum(of: Trade_Buy_Price)
                        priceClose: maximum(of: Trade_Buy_Price)
                        priceHigh: maximum(of: Trade_Buy_Price)
                        priceLow: minimum(of: Trade_Buy_Price)
                    }
                }
            }
            """ % '", "'.join(symbols)
        }
        
        try:
            await self.websocket.send(json.dumps(subscription))
            
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    if "data" in data and data["data"]:
                        trades_data = data["data"]["EVM"]["DEXTrades"]
                        
                        for trade in trades_data:
                            ohlc = OHLCData(
                                timestamp=datetime.fromisoformat(trade["Block"]["Time"]),
                                symbol=trade["Trade"]["Currency"]["Symbol"],
                                open=float(trade["priceOpen"]),
                                high=float(trade["priceHigh"]),
                                low=float(trade["priceLow"]),
                                close=float(trade["priceClose"]),
                                volume=float(trade["volume"])
                            )
                            yield ohlc
                            
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except KeyError as e:
                    logger.error(f"Missing key in data: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Streaming error: {e}")
        finally:
            self.is_streaming = False
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        timeframe: str = "1h"
    ) -> List[OHLCData]:
        """Fetch historical OHLC data"""
        
        query = """
        query GetHistoricalData($symbol: String!, $startDate: DateTime!, $endDate: DateTime!, $timeframe: String!) {
            EVM(dataset: combined, network: ethereum) {
                DEXTrades(
                    where: {
                        Block: {Time: {since: $startDate, till: $endDate}}
                        Trade: {Currency: {Symbol: {is: $symbol}}}
                    }
                    orderBy: {ascending: Block_Time}
                ) {
                    Block {
                        Time(interval: {in: hour, count: 1})
                    }
                    Trade {
                        Currency {
                            Symbol
                        }
                    }
                    volume: sum(of: Trade_Amount)
                    priceOpen: minimum(of: Trade_Buy_Price)
                    priceClose: maximum(of: Trade_Buy_Price)
                    priceHigh: maximum(of: Trade_Buy_Price)
                    priceLow: minimum(of: Trade_Buy_Price)
                }
            }
        }
        """
        
        variables = {
            "symbol": symbol,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "timeframe": timeframe
        }
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query,
                "variables": variables
            }
            
            async with session.post(
                "https://graphql.bitquery.io/", 
                json=payload, 
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    trades = data.get("data", {}).get("EVM", {}).get("DEXTrades", [])
                    
                    return [
                        OHLCData(
                            timestamp=datetime.fromisoformat(trade["Block"]["Time"]),
                            symbol=trade["Trade"]["Currency"]["Symbol"],
                            open=float(trade["priceOpen"]),
                            high=float(trade["priceHigh"]),
                            low=float(trade["priceLow"]),
                            close=float(trade["priceClose"]),
                            volume=float(trade["volume"])
                        )
                        for trade in trades
                    ]
                else:
                    logger.error(f"Failed to fetch historical data: {response.status}")
                    return []


def create_streamer_from_env() -> BitqueryStreamer:
    """Create BitqueryStreamer from environment variables"""
    config = StreamConfig(
        api_key=os.getenv("BITQUERY_API_KEY", ""),
        endpoint=os.getenv("BITQUERY_ENDPOINT", "wss://streaming.bitquery.io/graphql"),
        symbols=os.getenv("BITQUERY_SYMBOLS", "BTC,ETH").split(",")
    )
    return BitqueryStreamer(config)


# Example usage
async def main():
    """Example usage of BitqueryStreamer"""
    streamer = create_streamer_from_env()
    
    try:
        async for ohlc_data in streamer.subscribe_to_ohlc(["BTC", "ETH"]):
            print(f"Received OHLC: {ohlc_data}")
    except KeyboardInterrupt:
        print("Stopping stream...")
    finally:
        await streamer.disconnect()


if __name__ == "__main__":
    asyncio.run(main())