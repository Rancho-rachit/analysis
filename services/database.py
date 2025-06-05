from typing import Optional, List, Any, Dict
from mysql.connector import pooling
from mysql.connector.errors import Error as MySQLError
from .config import DatabaseConfig
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = self._create_connection_pool()

    def _create_connection_pool(self) -> pooling.MySQLConnectionPool:
        try:
            pool_config = {
                "pool_name": "mypool",
                "pool_size": 5,
                "host": self.config.host,
                "port": self.config.port,
                "user": self.config.user,
                "password": self.config.password,
                "database": self.config.database
            }
            return pooling.MySQLConnectionPool(**pool_config)
        except MySQLError as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    def get_connection(self):
        try:
            return self.pool.get_connection()
        except MySQLError as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise

    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Any]]:
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
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

    def fetch_recent_tweets(self, twitter_handle: str, limit: int = 10) -> Optional[List[str]]:
        """
        Fetch multiple recent tweets for a given Twitter handle.
        
        Args:
            twitter_handle: The Twitter handle to fetch tweets for
            limit: Number of tweets to fetch (default: 10)
            
        Returns:
            List of tweet texts or None if no tweets found
        """
        query = """
            SELECT body
            FROM enhanced_tweets
            WHERE author_handle = %s
            ORDER BY tweet_create_time DESC
            LIMIT %s
        """
        result = self.execute_query(query, (twitter_handle, limit))
        return [row[0] for row in result] if result and len(result) > 0 else None

    def fetch_limited_tokens(self, limit: int = 3) -> List[tuple[str, str, str, str]]:
        """
        Fetch a limited number of tokens from the token_leaderboard table.
        
        Args:
            limit: Maximum number of tokens to fetch
            
        Returns:
            List of tuples containing (token_id, pair_id, twitter, chain)
        """
        query = """
            SELECT token_id, pair_id, twitter, chain
            FROM token_leaderboard 
            WHERE is_coin = 0 
            AND is_cmc_listed = 1 
            AND twitter IS NOT NULL 
            AND pair_id IS NOT NULL
            AND chain IS NOT NULL
            ORDER BY RAND() 
            LIMIT %s
        """
        result = self.execute_query(query, (limit,))
        return result if result else []