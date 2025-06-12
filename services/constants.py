FETCH_LIMITED_TOKENS_QUERY = """
            SELECT token_id, pair_id, twitter, chain, marketcap, volume_24hr
            FROM twitter.token_leaderboard AS tlb
            WHERE tlb.is_coin = 0
            AND tlb.is_cmc_listed = 1
            AND tlb.twitter IS NOT NULL
            AND tlb.pair_id IS NOT NULL
            AND tlb.chain IS NOT NULL
            AND tlb.best_symbol_rank = 1
            AND tlb.is_coinbase IS NULL
            AND tlb.is_gateio IS NULL
            AND tlb.is_bingx IS NULL
            AND tlb.is_mexc IS NULL
            AND tlb.is_okx IS NULL
            AND tlb.is_binance IS NULL
            AND tlb.is_bybit IS NULL
            AND tlb.is_kucoin IS NULL
            AND tlb.is_bitget IS NULL
            AND tlb.is_bitmart IS NULL
            AND tlb.marketcap < 100000000000
            AND tlb.name NOT LIKE '%WRAPPED%'
            AND tlb.symbol NOT LIKE '%USD%'
            AND tlb.symbol NOT LIKE '%ETH%'
            AND tlb.symbol NOT LIKE '%BTC%'
            AND tlb.chain != 'pulsechain'
            ORDER BY RAND()
            LIMIT %s
        """

FETCH_RECENT_TWEETS_QUERY = """
            SELECT tweet_id, body, tweet_create_time, author_handle
            FROM twitter.enhanced_tweets
            WHERE author_handle = %s
            ORDER BY tweet_create_time DESC
            LIMIT %s
        """
