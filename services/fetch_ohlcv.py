import requests
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
from .config import GeckoTerminalConfig

logger = logging.getLogger(__name__)


class OHLCVService:
    def __init__(self, config: GeckoTerminalConfig):
        self.config = config
        logger.info(f"Initialized OHLCVService with base URL: {config.base_url}")

    def fetch_ohlcv(
        self, tweet_create_time: datetime, chain: str, pair_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch OHLCV data for a given pair on a specific chain.

        Args:
            chain: The blockchain network (ethereum, binance, polygon, avalanche)
            pair_id: The pair ID to fetch data for

        Returns:
            List of OHLCV data points or None if the request fails
        """
        try:
            current_epoch = int(tweet_create_time.timestamp())
            logger.info(f"Fetching OHLCV data for chain: {chain}, pair: {pair_id}")

            api_chain = chain.lower()
            if api_chain == "ethereum":
                api_chain = "eth"
            if api_chain == "binance":
                api_chain = "bsc"
            if api_chain == "polygon":
                api_chain = "polygon_pos"
            if api_chain == "avalanche":
                api_chain = "avax"

            url = f"{self.config.base_url}/networks/{api_chain}/pools/{pair_id}/ohlcv/hour?aggregate=1&before_timestamp={current_epoch}&limit=240&currency=usd&include_empty_intervals=false"
            logger.debug(f"Request URL: {url}")

            response = requests.get(url)
            response.raise_for_status()  # Raise exception for bad status codes

            data = response.json()

            # Log response details
            if "data" in data and "attributes" in data["data"]:
                ohlcv_list = data["data"]["attributes"].get("ohlcv_list", [])
                logger.info(f"Successfully fetched {len(ohlcv_list)} OHLCV data points")
                if ohlcv_list:
                    latest_price = ohlcv_list[0][
                        4
                    ]  # Close price of the most recent data point
                    logger.info(f"Latest price: ${float(latest_price):.8f}")
            else:
                logger.warning("Response data structure is not as expected")
                logger.debug(f"Response data: {data}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching OHLCV data: {e}")
            if hasattr(e.response, "text"):
                logger.error(f"API Error Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            return None
