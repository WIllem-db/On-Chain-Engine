import os
import requests
from dotenv import load_dotenv
import seaborn as sns
from datetime import datetime
import time
from models import *
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
import io
from PIL import Image


# Load environment variables from .env
load_dotenv()


class TokenDashboard:
    """This class will mainly use the Coin Lore API to fetch general crypto data."""

    def __init__(self):
        self.general_data = []
        self.coingecko_key = os.getenv("COINGECKO_KEY")
        self.moralis_key = os.getenv("MORALIS_KEY")
        self.coinapi_key = os.getenv("COINAPI_KEY")
        self.headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": self.coingecko_key,
        }

    def coingecko_top500(self):
        """This method will handle fetching the top500 coins from Coingecko API."""
        URLS = [
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=2&",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=3&",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=4&",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=5&",
        ]

        params = {"price_change_percentage": "1h,24h,7d,30d"}

        top500_coingecko = []  # Initialize an empty list

        for url in URLS:
            response = requests.get(
                url,
                headers={
                    "accept": "application/json",
                    "x-cg-demo-api-key": self.coingecko_key,
                },
                params=params,
            )
            if response.status_code == 200:
                coingecko_data = response.json()  # Parse JSON object

                for token in coingecko_data:
                    top500_coingecko.append(
                        {
                            "id": token["id"],
                            "symbol": token["symbol"],
                            "image": token["image"],
                            "current_price": float(token["current_price"]),
                            "market_cap_rank": token["market_cap_rank"],
                            "price_change_percentage_24": (
                                float(token["price_change_percentage_24h"])
                                if token.get("price_change_percentage_24h") is not None
                                else 0.0
                            ),
                            "price_change_percentage_1h": (
                                float(token["price_change_percentage_1h_in_currency"])
                                if token.get("price_change_percentage_1h_in_currency")
                                   is not None
                                else 0.0
                            ),
                            "price_change_percentage_7d": (
                                float(token["price_change_percentage_7d_in_currency"])
                                if token.get("price_change_percentage_7d_in_currency")
                                   is not None
                                else 0.0
                            ),
                            "price_change_percentage_30d": (
                                float(token["price_change_percentage_30d_in_currency"])
                                if token.get("price_change_percentage_30d_in_currency")
                                   is not None
                                else 0.0
                            ),
                            "total_volume": float(token["total_volume"]),
                            "market_cap": float(token["market_cap"]),
                        }
                    )
            else:
                print(f"Failed to fetch data from {url}")

        self.coingecko_data = (
            top500_coingecko  # Store the fetched data in the class attribute
        )
        return top500_coingecko  # Return the processed top500 data

    def get_top1k_currencies(self):
        """Method currently not in use"""
        URLS = [
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=2",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=3",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=4",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=5",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=6",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=7",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=8",
        ]

        top1000_coingecko = []  # Initialize an empty list to store all 1k coins

        for url in URLS:
            response = requests.get(
                url,
                headers={
                    "accept": "application/json",
                    "x-cg-demo-api-key": self.coingecko_key,
                },
            )

            if response.status_code == 200:
                coingecko_data = response.json()
                top1000_coingecko.extend(
                    coingecko_data
                )  # Add the current page's data to the list

        # Print the top 1k names
        for data in top1000_coingecko:
            print(data["id"])

        return top1000_coingecko

    def fetch_price_history_by_symbol(self, symbol):
        """Fetch price history data for a cryptocurrency by symbol"""
        print(f"Attempting to fetch price history for {symbol}")

        # Check for existing data
        symbol = symbol.upper()
        coin_record = PriceHistory.objects(symbol=symbol).first()

        if coin_record and (datetime.utcnow() - coin_record.last_updated).total_seconds() < 3600:
            print(f"Using cached data for {symbol}")
            return coin_record.history

        # Map common symbols to their CoinGecko IDs
        symbol_to_id = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "BNB": "binancecoin",
            "SOL": "solana",
            "XRP": "ripple",
            "USDC": "usd-coin",
            "ADA": "cardano",
            "AVAX": "avalanche-2",
            "DOGE": "dogecoin"
        }

        # Get the correct coin ID
        coin_id = symbol_to_id.get(symbol, symbol.lower())
        print(f"Using coin ID: {coin_id}")

        # Fetch new data from API
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
        print(f"Requesting data from: {url}")

        try:
            response = requests.get(url, headers=self.headers)
            print(f"API response status: {response.status_code}")

            if response.status_code != 200:
                print(f"API request failed: {response.text}")
                return coin_record.history if coin_record else []

            price_data = response.json().get('prices', [])
            print(f"Retrieved {len(price_data)} data points from API")

            # Process data (sample every 4 hours)
            processed_data = []
            for i in range(0, len(price_data), 4):
                if i < len(price_data):
                    timestamp_ms, price = price_data[i]
                    timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                    processed_data.append({
                        'timestamp': timestamp,
                        'price': price
                    })

            print(f"Processed {len(processed_data)} data points for storage")

            # Save to database
            if coin_record:
                coin_record.history = processed_data
                coin_record.last_updated = datetime.utcnow()
                coin_record.save()
                print(f"Updated existing record for {symbol}")
            else:
                new_record = PriceHistory(
                    symbol=symbol,
                    name=symbol,
                    history=processed_data,
                    last_updated=datetime.utcnow()
                )
                new_record.save()
                print(f"Created new record for {symbol}")

            return processed_data

        except Exception as e:
            print(f"Error fetching price data: {str(e)}")
            return coin_record.history if coin_record else []

    def fetch_price_history_by_id(self, coin_id, symbol):
        """
        Fetch 7-day price history data using the coin's ID directly

        Parameters:
            coin_id (str): CoinGecko ID of the cryptocurrency
            symbol (str): Symbol for database storage and reference

        Returns:
            list: Processed price history data
        """
        print(f"Fetching price history for {coin_id} ({symbol})")

        # Check for existing data
        symbol = symbol.upper()
        coin_record = PriceHistory.objects(symbol=symbol).first()

        if coin_record and (datetime.utcnow() - coin_record.last_updated).total_seconds() < 3600:
            print(f"Using cached data for {symbol}")
            return coin_record.history

        # Fetch new data from API
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
        print(f"Requesting data from: {url}")

        try:
            response = requests.get(url, headers=self.headers)
            print(f"API response status: {response.status_code}")

            if response.status_code != 200:
                print(f"API request failed: {response.text}")
                return []

            price_data = response.json().get('prices', [])
            print(f"Retrieved {len(price_data)} data points from API")

            # Sample every 4 hours for efficiency
            processed_data = []
            for i in range(0, len(price_data), 4):
                if i < len(price_data):
                    timestamp_ms, price = price_data[i]
                    timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                    processed_data.append({
                        'timestamp': timestamp,
                        'price': price
                    })

            print(f"Processed {len(processed_data)} data points for storage")

            # Save to database
            if coin_record:
                coin_record.history = processed_data
                coin_record.last_updated = datetime.utcnow()
                coin_record.save()
                print(f"Updated existing record for {symbol}")
            else:
                new_record = PriceHistory(
                    symbol=symbol,
                    name=coin_id,
                    history=processed_data,
                    last_updated=datetime.utcnow()
                )
                new_record.save()
                print(f"Created new record for {symbol}")

            return processed_data

        except Exception as e:
            print(f"Error fetching price data for {coin_id}: {str(e)}")
            return []

    def initialize_price_history_data(self, limit=50):
        """Initialize price history data for top cryptocurrencies"""
        print(f"Starting data collection for top {limit} cryptocurrencies...")

        # Get top cryptocurrencies
        top_coins = self.coingecko_top500()[:limit]

        # Track metrics
        successful = 0
        failed = 0

        # Process each coin
        for index, coin in enumerate(top_coins):
            try:
                coin_id = coin["id"]
                symbol = coin["symbol"].upper()

                print(f"Processing {index + 1}/{limit}: {symbol}")

                # Use the ID-based method for more reliable API calls
                result = self.fetch_price_history_by_id(coin_id, symbol)

                if result:
                    successful += 1
                else:
                    failed += 1

                # Avoid rate limiting
                time.sleep(1)

            except Exception as e:
                failed += 1
                print(f"Error processing {coin_id}: {str(e)}")

        print(f"Data collection completed: {successful} successful, {failed} failed")
        return successful, failed

    def plot_7d_price_graph(self):
        # Connect to local MongoDB database
        client = MongoClient("mongodb://localhost:27017/")

        # Acces database and collection
        db = client["crypto_tracker"]
        collection = db["price_history"]

        # Create a dictionary to store data for each symbol
        crypto_data = {}

        # Get documents for all cryptocurrencies
        for document in collection.find():
            symbol = document["symbol"]
            history = document["history"]

            # Extract timestamps and prices for this cryptocurrency
            timestamps = [entry["timestamp"] for entry in history]
            prices = [entry["price"] for entry in history]

            # Store data for this symbol
            crypto_data[symbol] = {
                "timestamps": timestamps,
                "prices": prices
            }

        # Close connection
        client.close()

        # Turn crypto_data into a pandas dataframe
        df = pd.DataFrame.from_dict(crypto_data)

        # Dictionary to store the image buffers
        plot_buffers = {}

        # Loop through each currency column in your DataFrame
        for currency in df.columns:
            # Extract timestamps and prices for this currency
            timestamps = df.loc['timestamps', currency]
            prices = df.loc['prices', currency]

            # Create the plot
            plt.figure()
            plt.plot(timestamps, prices)
            plt.title(currency)
            plt.show()

            # Save to buffer instead of file
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)

            # Store the buffer in our dictionary
            plot_buffers[currency] = buffer

            # Close the figure
            plt.close()


# Instance for direct testing
ds = TokenDashboard()
ds.plot_7d_price_graph()