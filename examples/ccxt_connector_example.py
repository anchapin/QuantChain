"""Example of using the CCXT data connector."""

from datetime import datetime, timedelta

from quantchain.connectors.ccxt_connector import CCXTDataConnector


def main():
    """Demonstrate CCXT data connector usage."""

    # Initialize connector with default exchange (binance)
    print("Initializing CCXT connector with Binance exchange...")
    connector = CCXTDataConnector()

    # Example 1: Get historical data
    print("\n=== Getting Historical Data ===")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Get BTC/USDT daily data for the last week
        df = connector.get_historical_data(
            symbol="BTC/USDT",
            timeframe="1D",
            start_date=start_date,
            end_date=end_date,
            limit=10,
        )

        print(f"Fetched {len(df)} candles of BTC/USDT data:")
        print(df.head())

    except Exception as e:
        print(f"Error fetching historical data: {e}")

    # Example 2: Get real-time price
    print("\n=== Getting Real-time Data ===")
    try:
        price_data = connector.get_real_time_data("BTC/USDT")
        print(f"Current BTC/USDT price: ${price_data['price']:.2f}")
        print(f"Bid: ${price_data['bid']:.2f}, Ask: ${price_data['ask']:.2f}")

    except Exception as e:
        print(f"Error fetching real-time data: {e}")

    # Example 3: Get detailed quote
    print("\n=== Getting Detailed Quote ===")
    try:
        quote = connector.get_quote("BTC/USDT")
        print("Quote for BTC/USDT:")
        print(f"  Last Price: ${quote['last_price']:.2f}")
        print(f"  Bid Price: ${quote['bid_price']:.2f} (Size: {quote['bid_size']})")
        print(f"  Ask Price: ${quote['ask_price']:.2f} (Size: {quote['ask_size']})")

    except Exception as e:
        print(f"Error fetching quote: {e}")

    # Example 4: Get available symbols
    print("\n=== Getting Available Symbols ===")
    try:
        symbols = connector.get_available_symbols(limit=10)
        print("First 10 available symbols:")
        for symbol in symbols:
            print(f"  - {symbol}")

    except Exception as e:
        print(f"Error fetching symbols: {e}")

    # Example 5: Get symbol info
    print("\n=== Getting Symbol Information ===")
    try:
        info = connector.get_symbol_info("BTC/USDT")
        print("BTC/USDT Symbol Info:")
        print(f"  Market: {info['market']}")
        print(f"  Currency: {info['currency']}")
        print(f"  Min Order Size: {info['min_order_size']}")
        print(f"  Price Precision: {info['price_precision']} decimals")
        print(f"  Size Precision: {info['size_precision']} decimals")

    except Exception as e:
        print(f"Error fetching symbol info: {e}")

    # Example 6: Check if market is open
    print("\n=== Checking Market Status ===")
    try:
        is_open = connector.is_market_open()
        print(f"Crypto market is open: {is_open}")
        print("Note: Crypto markets are 24/7, so this should always be True")

    except Exception as e:
        print(f"Error checking market status: {e}")

    # Example 7: Using a different exchange
    print("\n=== Using Different Exchange ===")
    try:
        print("Initializing CCXT connector with Kraken exchange...")
        kraken_connector = CCXTDataConnector(exchange="kraken")

        # Get symbol info from Kraken
        kraken_info = kraken_connector.get_symbol_info("BTC/USD")
        print("BTC/USD on Kraken:")
        print(f"  Market: {kraken_info['market']}")
        print(f"  Currency: {kraken_info['currency']}")

    except Exception as e:
        print(f"Error with Kraken connector: {e}")


if __name__ == "__main__":
    main()
