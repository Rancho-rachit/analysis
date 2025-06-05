from google import genai
from typing import Optional, Literal, List, Dict, Any
from .config import GeminiConfig
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self, config: GeminiConfig):
        self.config = config
        self.client = genai.Client(api_key=config.api_key)

    def analyze_sentiment(
        self, 
        recent_tweet: str, 
        historical_tweets: List[str],
    ) -> Optional[Literal["buy", "skip"]]:
        try:

            prompt = (
                "You are a crypto market analyst. Analyze these tweets from a crypto project's official account.\n\n"
                "Context:\n"
                "- Focus on identifying unique, new information that could impact the token's price\n\n"
                f"Most Recent Tweet:\n{recent_tweet}\n\n"
                f"Historical Tweets:\n{chr(10).join(historical_tweets)}\n\n"
                "Task: Determine if the most recent tweet contains unique, impactful information "
                "that could affect the token's price, or if it's just repeating old information.\n\n"
                "Respond with EXACTLY one word:\n"
                "- 'buy' if the recent tweet contains unique, impactful information that could move the price\n"
                "- 'skip' if it's just repeating old information or contains no significant news\n\n"
                "Important: Only respond with 'buy' or 'skip', nothing else."
            )

            response = self.client.models.generate_content(
                model=self.config.model_name,
                contents=prompt
            )
            
            # Process response
            decision = response.text.strip().lower()
            if decision not in ['buy', 'skip']:
                logger.warning(f"Unexpected response from model: {decision}")
                return None
                
            return decision

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return None