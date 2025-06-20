from google import genai
from typing import Optional, Literal, List, Dict, Any
from .config import GeminiConfig
import logging
import json
import re
from .constants import RESPONSE_THRESHOLD

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def __init__(self, config: GeminiConfig):
        self.config = config
        self.client = genai.Client(api_key=config.api_key)

    def analyze_sentiment(
        self,
        tweets_data: Dict[str, Any],
        ohlcv_data: Optional[List[List[Any]]] = None,
    ) -> Optional[tuple[Literal["positive", "negative"], str]]:
        try:

            # Format the tweets data for the prompt
            tweets_json = json.dumps(tweets_data, indent=2)

            prompt = (
                "You are a crypto market analyst. Analyze the tweet data from a crypto project's official account.\n\n"
                "Context:\n"
                "- Focus on identifying unique, new information that could impact the token's price\n"
                "- The data contains the most recent tweet and historical tweets with timestamps\n\n"
                f"Tweet Data (JSON):\n{tweets_json}\n\n"
            )

            if ohlcv_data:
                # Format OHLCV data as user-friendly JSON
                price_data = []
                for entry in ohlcv_data:
                    if isinstance(entry, list) and len(entry) >= 2:
                        price_data.append(
                            {"timestamp": entry[0], "price": f"${entry[1]:.8f}"}
                        )

                price_json = json.dumps(price_data, indent=2)
                prompt += f"Recent Price Data (last 10 days):\n{price_json}\n\n"

            prompt += (
                "Task: Analyze the most recent tweet (in 'recent_tweet') compared to historical tweets (in 'past_tweets') "
                "to determine if it contains unique, impactful information that could affect the token's price.\n\n"
                "Consider:\n"
                "1. Is the recent tweet's content new information or a repeat of previous announcements?\n"
                "2. Does it have potential to impact the token's price?\n"
                "3. How does the timing relate to recent price movements?\n"
                "4. Compare the tweet content and timestamps to identify patterns or uniqueness\n\n"
                "Respond with EXACTLY one line in the following format (no explanation):\n"
                "Score: <number between 0 and 100>\n\n"
                "Where 0 means no impact and 100 means extremely likely to have a positive impact."
            )

            print(prompt)

            response = self.client.models.generate_content(
                model=self.config.model_name, contents=prompt
            )

            match = re.search(r"Score:\s*(\d{1,3})", response.text)
            if not match:
                logger.warning(f"Unexpected response from model: {response.text}")
                return None, f"Unexpected model response: {response.text}"
            score = int(match.group(1))
            if score < 0 or score > 100:
                logger.warning(f"Score out of range: {score}")
                return None, f"Score out of range: {score}"

            decision = "positive" if score >= RESPONSE_THRESHOLD else "negative"

            print(f"GEMINI RESPONSE: {response.text} (score={score}, decision={decision})")

            return decision, f"Score: {score}"

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return None, f"Error in sentiment analysis: {str(e)}"