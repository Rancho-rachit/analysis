import logging
from typing import Optional, List, Dict
import argparse
from services.config import Config
from services.database import DatabaseService
from services.gemini import SentimentAnalyzer
from services.fetch_ohlcv import OHLCVService
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Suppress specific logging
logging.getLogger("google.genai.models").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class SentimentAnalysisService:
    def __init__(self):
        self.config = Config.from_env()
        self.db_service = DatabaseService(self.config.db)
        self.sentiment_analyzer = SentimentAnalyzer(self.config.gemini)
        self.ohlcv_service = OHLCVService(self.config.gecko_terminal)

    def analyze_token_sentiment(
        self, token_id: str, twitter_handle: str, pair_id: str, chain: str
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Analyze a token's tweets and price data to determine if the recent tweet contains unique information.

        Args:
            token_id: The ID of the token to analyze
            twitter_handle: The Twitter handle associated with the token
            pair_id: The pair ID for fetching price data
            chain: The blockchain network the token is on

        Returns:
            decision: 'positive', 'negative' or None if analysis fails
        """
        try:
            # Step 1: Fetch recent tweets
            tweets_data = self.db_service.fetch_recent_tweets(twitter_handle, limit=21)
            if not tweets_data:
                return (
                    None,
                    f"No recent tweets found for Twitter handle: {twitter_handle}",
                )

            # Step 2: Extract recent tweet timestamp for OHLCV data
            tweet_datetime = datetime.strptime(
                tweets_data["recent_tweet"]["tweet_create_time"], "%Y-%m-%d %H:%M:%S"
            )

            # Step 3: Fetch OHLCV data
            ohlcv_data = self.ohlcv_service.formatted_fetch_ohlcv(
                tweet_datetime, chain, pair_id
            )
            if not ohlcv_data:
                logger.warning(f"Could not fetch OHLCV data for token {token_id}")
                return None, "Failed to fetch OHLCV data"

            # Step 4: Analyze uniqueness of information with price context
            decision, reason = self.sentiment_analyzer.analyze_sentiment(
                tweets_data, ohlcv_data
            )
            if not decision:
                return None, reason if reason else "Sentiment analysis failed"

            # Map decision to professional terminology
            if decision == "positive":
                return "positive", reason
            else:
                return "negative", reason

        except Exception as e:
            return None, f"Error in analysis pipeline: {str(e)}"

    def analyze_multiple_tokens(
        self, token_data: List[tuple[str, str, str, str, float, float]]
    ) -> Dict[str, tuple[Optional[str], Optional[str]]]:
        """
        Analyze multiple tokens sequentially.

        Args:
            token_data: List of tuples containing (token_id, pair_id, twitter_handle, chain, marketcap, volume_24hrs)

        Returns:
            Dictionary mapping token IDs to their (decision, reason)
        """
        results = {}

        for (
            token_id,
            pair_id,
            twitter_handle,
            chain,
            marketcap,
            volume_24hrs,
        ) in token_data:
            try:
                logger.info(
                    f"\n{'='*60}\n"
                    f"Analyzing Token: {token_id}\n"
                    f"   Pair ID     : {pair_id}\n"
                    f"   Twitter     : {twitter_handle}\n"
                    f"   Chain       : {chain}\n"
                    f"   Market Cap  : {marketcap}\n"
                    f"   Volume 24h  : {volume_24hrs}\n"
                    f"{'='*60}"
                )
                decision, reason = self.analyze_token_sentiment(
                    token_id, twitter_handle, pair_id, chain
                )
                results[token_id] = (decision, reason)

                if decision:
                    logger.info(f"Token {token_id}: {decision.upper()} - {reason}")
                else:
                    logger.warning(f"Token {token_id}: FAIL - {reason}")

            except Exception as e:
                logger.error(f"Error processing token {token_id}: {e}")
                results[token_id] = (None, f"Unexpected error: {str(e)}")

        return results


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze token sentiment based on tweets"
    )
    parser.add_argument(
        "--tokens", type=int, default=3, help="Number of tokens to analyze (default: 3)"
    )
    return parser.parse_args()


def fetch_tokens(service: SentimentAnalysisService, limit: int):
    logger.info(f"Fetching {limit} tokens from database...")
    try:
        token_data = service.db_service.fetch_limited_tokens(limit=limit)
        logger.info(f"Database query completed. Found {len(token_data)} token/s")
        return token_data
    except Exception as db_error:
        logger.error(f"Error fetching tokens from database: {db_error}")
        return None


def print_summary(results: Dict[str, tuple[Optional[str], Optional[str]]]):
    positive_count = sum(
        1 for decision, _ in results.values() if decision == "positive"
    )
    negative_count = sum(
        1 for decision, _ in results.values() if decision == "negative"
    )
    fail_count = sum(1 for decision, _ in results.values() if decision is None)

    logger.info("\nAnalysis Summary:")
    logger.info(f"Total tokens analyzed: {len(results)}")
    logger.info(f"Positive signals: {positive_count}")
    logger.info(f"Negative signals: {negative_count}")
    logger.info(f"Failed analysis: {fail_count}")


def print_detailed_results(results: Dict[str, tuple[Optional[str], Optional[str]]]):
    logger.info("\nDetailed Analysis Results:")
    for token_id, (decision, reason) in results.items():
        if decision:
            logger.info(f"Token {token_id}: {decision.upper()} - {reason}")
        else:
            logger.warning(f"Token {token_id}: FAIL - {reason}")


def main():
    args = parse_args()

    try:
        logger.info("Initializing SentimentAnalysisService...")
        service = SentimentAnalysisService()

        token_data = fetch_tokens(service, args.tokens)
        if not token_data:
            logger.error("No tokens found in the database")
            return

        logger.info("Starting token analysis...")
        results = service.analyze_multiple_tokens(token_data)

        print_summary(results)
        print_detailed_results(results)

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
