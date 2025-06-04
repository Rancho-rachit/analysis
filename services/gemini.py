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
    ) -> Optional[Literal["buy", "fake"]]:
        try:
            # Combine all tweets for context
            all_tweets = [recent_tweet] + historical_tweets
            combined_tweets = "\n".join(all_tweets)


            prompt = (
                "Analyze these tweets from a crypto project's official account and their recent price history. "
                "The first tweet is the most recent, followed by older tweets.\n\n"
                f"Tweets:\n{combined_tweets}\n\n"
                "Task: Determine if the most recent tweet (first one) contains unique, new information "
                "that could impact the token's price, or if it's just repeating old information. "
                "Consider the price history context when making your decision.\n\n"
                "Respond with exactly one word:\n"
                "- 'buy' if the recent tweet contains unique, impactful information\n"
                "- 'fake' if it's just repeating old information"
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