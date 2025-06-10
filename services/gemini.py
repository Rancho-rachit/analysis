from google import genai
from typing import Optional, Literal, List, Dict, Any
from .config import GeminiConfig
import logging
import json


logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self, config: GeminiConfig):
        self.config = config
        self.client = genai.Client(api_key=config.api_key)

    def analyze_sentiment(
        self, 
        tweets_data: Dict[str, Any],
        ohlcv_data: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Literal["buy", "skip"]]:
        try:
            # Format OHLCV data if available
            price_context = ""
            if ohlcv_data and isinstance(ohlcv_data, dict) and 'data' in ohlcv_data:
                ohlcv_list = ohlcv_data['data'].get('attributes', {}).get('ohlcv_list', [])
                if ohlcv_list:
                    # Get the last 24 hours of data
                    recent_prices = ohlcv_list[-24:] if len(ohlcv_list) > 24 else ohlcv_list
                    price_changes = []
                    for data in recent_prices:
                        if isinstance(data, list) and len(data) >= 5:
                            timestamp = data[0]  # Unix timestamp
                            close_price = data[4]  # Close price
                            price_changes.append(f"Time: {timestamp}, Price: ${float(close_price):.8f}")
                    price_context = "\n".join(price_changes)

            # Format the tweets data for the prompt
            tweets_json = json.dumps(tweets_data, indent=2)

            prompt = (
                "You are a crypto market analyst. Analyze the tweet data from a crypto project's official account.\n\n"
                "Context:\n"
                "- Focus on identifying unique, new information that could impact the token's price\n"
                "- The data contains the most recent tweet and historical tweets with timestamps\n\n"
                f"Tweet Data (JSON):\n{tweets_json}\n\n"
            )

            if price_context:
                prompt += f"Recent Price Data (last 10 days):\n{price_context}\n\n"

            prompt += (
                "Task: Analyze the most recent tweet (in 'recent_tweet') compared to historical tweets (in 'past_tweets') "
                "to determine if it contains unique, impactful information that could affect the token's price.\n\n"
                "Consider:\n"
                "1. Is the recent tweet's content new information or a repeat of previous announcements?\n"
                "2. Does it have potential to impact the token's price?\n"
                "3. How does the timing relate to recent price movements?\n"
                "4. Compare the tweet content and timestamps to identify patterns or uniqueness\n\n"
                "Respond with EXACTLY one word:\n"
                "- 'buy' if the recent tweet contains unique, impactful information that could move the price\n"
                "- 'skip' if it's just repeating old information or contains no significant news\n\n"
                "Important: Only respond with 'buy' or 'skip', nothing else."
            )

            response = self.client.models.generate_content(
                model=self.config.model_name,
                contents=prompt
            )
            
            print(prompt)
            # Process response
            decision = response.text.strip().lower()
            if decision not in ['buy', 'skip']:
                logger.warning(f"Unexpected response from model: {decision}")
                return None
                
            return decision

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return None
