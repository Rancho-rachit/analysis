import logging
from typing import Optional, List, Dict
import argparse
from services.config import Config
from services.database import DatabaseService
from services.gemini import SentimentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress specific logging
logging.getLogger('google.genai.models').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)


logger = logging.getLogger(__name__)

class SentimentAnalysisService:
    def __init__(self):
        self.config = Config.from_env()
        self.db_service = DatabaseService(self.config.db)
        self.sentiment_analyzer = SentimentAnalyzer(self.config.gemini)

    def analyze_token_sentiment(self, token_id: str, twitter_handle: str) -> tuple[Optional[str], Optional[str]]:
        """
        Analyze a token's tweets to determine if the recent tweet contains unique information.
        
        Args:
            token_id: The ID of the token to analyze
            twitter_handle: The Twitter handle associated with the token
            
        Returns:
            Tuple of (decision, reason)
            decision: 'positive', 'negative', or None
            reason: Explanation for the decision or failure
        """
        try:
            if not twitter_handle:
                return None, "No Twitter handle found for token"

            # Step 1: Fetch recent tweets (most recent + 20 historical)
            recent_tweets = self.db_service.fetch_recent_tweets(twitter_handle, limit=21)
            if not recent_tweets:
                return None, f"No recent tweets found for Twitter handle: {twitter_handle}"

            # Separate most recent tweet from historical tweets
            most_recent_tweet = recent_tweets[0]
            historical_tweets = recent_tweets[1:]

            # Step 2: Analyze uniqueness of information
            decision = self.sentiment_analyzer.analyze_sentiment(
                most_recent_tweet, 
                historical_tweets
            )
            if not decision:
                return None, "Failed to generate sentiment analysis"

            # Map decision to professional terminology
            if decision == "buy":
                return "positive", "Recent tweet contains unique, impactful information"
            else:
                return "negative", "Recent tweet contains repetitive or non-significant information"

        except Exception as e:
            return None, f"Error in analysis pipeline: {str(e)}"

    def analyze_multiple_tokens(self, token_data: List[tuple[str, str, str]]) -> Dict[str, tuple[Optional[str], Optional[str]]]:
        """
        Analyze multiple tokens sequentially.
        
        Args:
            token_data: List of tuples containing (token_id, pair_id, twitter_handle)
            
        Returns:
            Dictionary mapping token IDs to their (decision, reason)
        """
        results = {}
        
        for token_id, pair_id, twitter_handle in token_data:
            try:
                logger.info(f"Analyzing token: {token_id} (pair: {pair_id}, twitter: {twitter_handle})")
                decision, reason = self.analyze_token_sentiment(token_id, twitter_handle)
                results[token_id] = (decision, reason)
                
                if decision:
                    logger.info(f"Token {token_id}: {decision.upper()} - {reason}")
                else:
                    logger.warning(f"Token {token_id}: FAIL - {reason}")
                    
            except Exception as e:
                logger.error(f"Error processing token {token_id}: {e}")
                results[token_id] = (None, f"Unexpected error: {str(e)}")
        
        return results
    
def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze token sentiment based on tweets')
    parser.add_argument('--tokens', type=int, default=3, help='Number of tokens to analyze (default: 3)')
    args = parser.parse_args()

    try:
        logger.info("Initializing SentimentAnalysisService...")
        service = SentimentAnalysisService()
        
        # Fetch tokens from the database
        logger.info(f"Fetching {args.tokens} tokens from database...")
        try:
            token_data = service.db_service.fetch_limited_tokens(limit=args.tokens)
            logger.info(f"Database query completed. Found {len(token_data)} tokens")
        except Exception as db_error:
            logger.error(f"Error fetching tokens from database: {db_error}")
            return
        
        if not token_data:
            logger.error("No tokens found in the database")
            return
        
        logger.info(f"Found {len(token_data)} tokens to analyze")
        
        # Analyze all tokens sequentially
        logger.info("Starting token analysis...")
        results = service.analyze_multiple_tokens(token_data)
        
        # Print results summary
        positive_count = sum(1 for decision, _ in results.values() if decision == "positive")
        negative_count = sum(1 for decision, _ in results.values() if decision == "negative")
        fail_count = sum(1 for decision, _ in results.values() if decision is None)
        
        logger.info("\nAnalysis Summary:")
        logger.info(f"Total tokens analyzed: {len(results)}")
        logger.info(f"Positive signals: {positive_count}")
        logger.info(f"Negative signals: {negative_count}")
        logger.info(f"Failed analysis: {fail_count}")
        
        # Print detailed results
        logger.info("\nDetailed Analysis Results:")
        for token_id, (decision, reason) in results.items():
            if decision:
                logger.info(f"Token {token_id}: {decision.upper()} - {reason}")
            else:
                logger.warning(f"Token {token_id}: FAIL - {reason}")

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
