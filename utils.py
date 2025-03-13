import os
from socketserver import DatagramRequestHandler

import requests
from dotenv import load_dotenv
from datetime import datetime
import time
from models import PriceHistory
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO


# Load environment variables from .env
load_dotenv()


class TokenDashboard:
    """This class handles cryptocurrency data fetching and processing."""

    def __init__(self):
        self.coingecko_data = []  # Initialize this in the constructor
        self.symbol_to_id_map = (
            {}
        )  # Will store mapping of symbols to their CoinGecko IDs
        self.coingecko_key = os.getenv("COINGECKO_KEY")
        self.headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": self.coingecko_key,
        }

    def coingecko_top500(self):
        """Fetch the top 500 coins from Coingecko API and build symbol-to-id mapping."""
        # If we already have the data, return it
        if self.coingecko_data:
            return self.coingecko_data

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
                headers=self.headers,
                params=params,
            )
            if response.status_code == 200:
                coingecko_data = response.json()  # Parse JSON object

                for token in coingecko_data:
                    # Store the symbol to ID mapping as we process the data
                    self.symbol_to_id_map[token["symbol"].upper()] = token["id"]

                    top500_coingecko.append(
                        {
                            "id": token["id"].replace("-", " "),
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

    def fetch_price_history_by_symbol(self, symbol):
        """Fetch price history data for a cryptocurrency by symbol"""
        print(f"Attempting to fetch price history for {symbol}")

        # Check for existing data
        symbol = symbol.upper()
        coin_record = PriceHistory.objects(symbol=symbol).first()

        # If we have recent data (last update was less than 1 hour ago), use it
        if (
            coin_record
            and (datetime.utcnow() - coin_record.last_updated).total_seconds() < 3600
        ):
            print(f"Using cached data for {symbol}")
            return coin_record.history

        # Ensure we have mapping data available
        if not self.symbol_to_id_map and not self.coingecko_data:
            print("Loading top cryptocurrency data to create symbol-to-id mapping...")
            self.coingecko_top500()  # This will populate self.symbol_to_id_map

        # Get the correct coin ID from our mapping
        if symbol in self.symbol_to_id_map:
            coin_id = self.symbol_to_id_map[symbol]
            print(f"Found coin ID in mapping: {coin_id}")
        else:
            print(f"No mapping found for {symbol}, cannot fetch price history")
            return []

        # Call the ID-based method to fetch data
        return self.fetch_price_history_by_id(coin_id, symbol)

    def fetch_price_history_by_id(self, coin_id, symbol):
        """
        Fetch 7-day price history data using the coin's ID directly
        Only updates if latest data point is more than 4 hours old

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

        # Check if we have recent data (less than 4 hours old)
        if coin_record and coin_record.history:
            latest_timestamp = max(entry["timestamp"] for entry in coin_record.history)
            time_diff = (
                datetime.utcnow() - latest_timestamp
            ).total_seconds() / 3600  # hours

            if time_diff < 4:
                print(
                    f"Using fresh data for {symbol} (latest point is {time_diff:.1f} hours old)"
                )
                return coin_record.history
            else:
                print(f"Data for {symbol} is {time_diff:.1f} hours old, updating...")

        # Fetch new data from API
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
        print(f"Requesting data from: {url}")

        try:
            response = requests.get(url, headers=self.headers)
            print(f"API response status: {response.status_code}")

            if response.status_code != 200:
                print(f"API request failed: {response.text}")
                return (
                    coin_record.history if coin_record and coin_record.history else []
                )

            price_data = response.json().get("prices", [])
            print(f"Retrieved {len(price_data)} data points from API")

            # Sample every 4 hours for efficiency
            processed_data = []
            for i in range(0, len(price_data), 4):
                if i < len(price_data):
                    timestamp_ms, price = price_data[i]
                    timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                    processed_data.append({"timestamp": timestamp, "price": price})

            print(f"Processed {len(processed_data)} data points")

            # Save to database
            if coin_record:
                if time_diff >= 4 and coin_record.history:
                    # If data is stale, remove the last point and append new data
                    coin_record.history = coin_record.history[:-1] + processed_data[-1:]
                    print(f"Updated last data point for {symbol}")
                else:
                    coin_record.history = processed_data
                    print(f"Replaced all data points for {symbol}")

                coin_record.last_updated = datetime.utcnow()
                coin_record.save()
            else:
                new_record = PriceHistory(
                    symbol=symbol,
                    name=coin_id,
                    history=processed_data,
                    last_updated=datetime.utcnow(),
                )
                new_record.save()
                print(f"Created new record for {symbol}")

            return coin_record.history if coin_record else processed_data

        except Exception as e:
            print(f"Error fetching price data for {coin_id}: {str(e)}")
            return coin_record.history if coin_record and coin_record.history else []

    def initialize_price_history_data(self, limit=10):
        """Initialize price history data for top cryptocurrencies

        This is useful for initial setup and can be run as a background task.
        By default, only initializes data for top 10 cryptocurrencies to avoid rate limiting.
        """
        print(f"Starting data collection for top {limit} cryptocurrencies...")

        # First ensure we have top cryptocurrency data
        if not self.coingecko_data:
            print("Loading top cryptocurrency data...")
            self.coingecko_top500()

        # Get top cryptocurrencies
        top_coins = self.coingecko_data[:limit]

        # Track metrics
        successful = 0
        failed = 0

        # Process each coin
        for index, coin in enumerate(top_coins):
            try:
                coin_id = coin["id"]
                symbol = coin["symbol"].upper()

                print(f"Processing {index + 1}/{limit}: {symbol} (ID: {coin_id})")

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
                print(f"Error processing {coin.get('id', 'unknown')}: {str(e)}")

        print(f"Data collection completed: {successful} successful, {failed} failed")
        return successful, failed

    def plot_7d_chart(self, limit=50):
        """
        This method works fine, but for trouble shooting purposes, we will limit to 50 plots
        We will also have to implement threading/background running in order to not slow the website down by 50x

        Also the charts are being made properly, but they might be getting fucked because of the buffer (buffer should be able to handle 500 charts, but it maybe causing loading issues on the server side)
        """
        client = MongoClient("mongodb://localhost:27017/")
        db = client["crypto_tracker"]
        collection = db["price_history"]
        history_docs = collection.find().limit(limit)
        plot_data = {}

        for doc in history_docs:
            ticker = doc["symbol"]
            prices = []
            timestamps = []

            for x in doc["history"]:
                # print(f"({ticker}):", x["timestamp"])  # Reduce decimals except for currencies under $1 (TODO, will implement this later on)
                prices.append(x["price"])
                timestamps.append(x["timestamp"])

            plt.figure(figsize=(10, 5))

            # Change colors based on upward or downward chart
            if prices[0] > prices[-1]:
                color = "#EF4444"
            elif prices[0] < prices[-1]:
                color = "#10B981"
            else:
                color = "#D3D3D3"  # Neutral (light grey)  # When working with multiple decimals, this kinda becomes useless, this is just in case

            lineplot = sns.lineplot(x=timestamps, y=prices, color=color)
            plt.fill_between(timestamps, prices, color=color, alpha=0.2)

            # Calculation to setup appropriate y-axis limits (chart centering)
            max_price = max(prices)
            min_price = min(prices)
            price_range = max_price - min_price
            padding = price_range * 0.2
            y_min = max(0, min_price - padding)
            y_max = max_price + padding
            plt.ylim(y_min, y_max)

            lineplot.set_xticks([])
            lineplot.set_yticks([])
            lineplot.set_xticklabels([])
            lineplot.set_yticklabels([])

            for spine in lineplot.spines.values():
                spine.set_visible(False)

            lineplot.grid(False)
            lineplot.set_title(False)
            plt.tight_layout()
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

            filename = f"temp_chart_{ticker}.png"
            plt.savefig(filename, format="png", dpi=300)
            plt.close()

            with open(filename, "rb") as f:
                image_data = f.read()

                if image_data[:8] == b'\x89PNG\r\n\x1a\n':
                    print(f"Valid PNG data for {ticker}")
                    plot_data[ticker] = image_data
                else:
                    print(f"Invalid PNG data for {ticker}")

            os.remove(filename)

        client.close() # Remove the temporary file
        return plot_data

    def store_charts_in_mongodb(self, chart_data):
        """Storing the results from plot_7d_chart method in mongodb collection"""
        client = MongoClient("mongodb://localhost:27017/")
        db = client["crypto_tracker"]
        collection = db["price_history"]

        success_count = 0

        for ticker, image_data in chart_data.items():
            result = collection.update_one(
                {"symbol": ticker.upper()},
                {
                    "$set": {
                        "chart_image": image_data,
                        "chart_updated_at": datetime.utcnow()
                    }
                }
            )
            if result.matched_count > 0:
                success_count += 1
                print(f"Successfully stored {ticker} chart")
            else:
                print(f"No docs found for {ticker}")

        print(f"{success_count} charts stored")
        client.close()
        return success_count



# Run tests here
ds = TokenDashboard()
