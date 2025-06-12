import requests
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
from .config import GeckoTerminalConfig

logger = logging.getLogger(__name__)


class OHLCVService:
    def __init__(self, config: GeckoTerminalConfig):
        self.config = config

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

            response = requests.get(url)
            response.raise_for_status()

            data = response.json()

            ohlcv_list = data["data"]["attributes"].get("ohlcv_list", [])
            logger.info(f"Successfully fetched {len(ohlcv_list)} OHLCV data points")

            return ohlcv_list

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching OHLCV data: {e}")
            if hasattr(e.response, "text"):
                logger.error(f"API Error Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            return None

    def formatted_fetch_ohlcv(
        self, tweet_create_time: datetime, chain: str, pair_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Format the OHLCV data to ensure timestamps are datetime objects and prices are floats.

        Args:
            tweet_create_time: The creation time of the tweet
            chain: The blockchain network the token is on
            pair_id: The pair ID for fetching price data

        Returns:
            List of formatted OHLCV data points or None if no valid data found
        """

        try:
            ohlcv_list = self.fetch_ohlcv(tweet_create_time, chain, pair_id)

            if not ohlcv_list:
                logger.warning("No OHLCV data fetched")
                return None

            formatted_ohlcv = []
            for entry in ohlcv_list:
                if isinstance(entry, list) and len(entry) >= 5:
                    # Create formatted entry with timestamp and close price
                    time_str = datetime.fromtimestamp(entry[0]).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    close_price = float(entry[4])
                    new_entry = [time_str, close_price]
                    formatted_ohlcv.append(new_entry)

            if not formatted_ohlcv:
                logger.warning("No valid OHLCV data found")
                return None
            return formatted_ohlcv
        except Exception as e:
            logger.error(f"Error formatting OHLCV data: {e}")
            return None
