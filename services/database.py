from typing import Optional, List, Any
from mysql.connector import pooling
from mysql.connector.errors import Error as MySQLError
from .config import DatabaseConfig
from .constants import FETCH_RECENT_TWEETS_QUERY, FETCH_LIMITED_TOKENS_QUERY
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    def __init__(self, config: DatabaseConfig, pool_size: int = 5):
        self.config = config
        self.pool = self._create_connection_pool(pool_size)

    def _create_connection_pool(self, pool_size: int) -> pooling.MySQLConnectionPool:
        try:
            pool_config = {
                "pool_name": "mypool",
                "pool_size": pool_size,
                "host": self.config.host,
                "port": self.config.port,
                "user": self.config.user,
                "password": self.config.password,
            }
            return pooling.MySQLConnectionPool(**pool_config)
        except MySQLError as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    def _get_connection(self):
        try:
            return self.pool.get_connection()
        except MySQLError as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise

    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Any]]:
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
        except MySQLError as e:
            logger.error(f"Database query error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def fetch_recent_tweets(
        self, twitter_handle: str, limit: int = 10
    ) -> Optional[List[str]]:
        """
        Fetch multiple recent tweets for a given Twitter handle.

        Args:
            twitter_handle: The Twitter handle to fetch tweets for
            limit: Number of tweets to fetch (default: 10)

        Returns:
            List of tweet texts or None if no tweets found
        """
        query = FETCH_RECENT_TWEETS_QUERY
        result = self.execute_query(query, (twitter_handle, limit))

        if not result or len(result) == 0:
            return None

        tweet_dict = {
            "recent_tweet": {
                "tweet_id": result[0][0],
                "body": result[0][1],
                "tweet_create_time": result[0][2].strftime("%Y-%m-%d %H:%M:%S"),
                "author_handle": result[0][3],
            },
            "past_tweets": [
                {
                    "tweet_id": t[0],
                    "body": t[1],
                    "tweet_create_time": t[2].strftime("%Y-%m-%d %H:%M:%S"),
                    "author_handle": t[3],
                }
                for t in result[1:]
            ],
        }

        return tweet_dict

    def fetch_limited_tokens(
        self, limit: int = 3
    ) -> List[tuple[str, str, str, str, float, float]]:
        """
        Fetch a limited number of tokens from the token_leaderboard table.

        Args:
            limit: Maximum number of tokens to fetch

        Returns:
            List of tuples containing (token_id, pair_id, twitter, chain, marketcap, volume_24hrs)
        """
        query = FETCH_LIMITED_TOKENS_QUERY
        result = self.execute_query(query, (limit,))
        return result if result else []
