import os
import requests
from dotenv import load_dotenv
import seaborn as sns
from datetime import datetime, timedelta
import time
from flask_pymongo import PyMongo
import pymongo
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables from .env
load_dotenv()

# MongoDB instance to be initialized in the main app
mongo = None


def init_mongo(app):
    """Initialize MongoDB connection and return instance"""
    global mongo
    mongo = PyMongo(app)
    setup_database()
    return mongo


def setup_database():
    """Set up database indexes for efficient queries"""
    # Create indexes for historical prices collection
    mongo.db.historical_prices.create_index(
        [("symbol", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)]
    )

    # Create index for coin collection
    mongo.db.coins.create_index([("rank", pymongo.ASCENDING)])
    mongo.db.coins.create_index([("symbol", pymongo.ASCENDING)], unique=True)


def store_historical_prices(price_data):
    """Store historical prices for multiple coins efficiently"""
    if not price_data:
        return

    bulk_ops = []

    for item in price_data:
        bulk_ops.append(
            pymongo.UpdateOne(
                {"symbol": item["symbol"], "timestamp": item["timestamp"]},
                {"$set": {"price": item["price"]}},
                upsert=True
            )
        )

    if bulk_ops:
        mongo.db.historical_prices.bulk_write(bulk_ops)
        print(f"Stored {len(bulk_ops)} historical price points")


def get_coin_history(symbol, days=7):
    """Get historical price data for a specific coin for the last N days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    history = list(
        mongo.db.historical_prices.find(
            {"symbol": symbol.upper(), "timestamp": {"$gte": cutoff_date}}
        ).sort("timestamp", pymongo.ASCENDING)
    )

    # Format the data for frontend use
    return [{"timestamp": point["timestamp"], "price": point["price"]} for point in history]


def update_coin_data(coins_data):
    """Update the coins collection with latest data"""
    if not coins_data:
        return

    bulk_ops = []

    for coin in coins_data:
        bulk_ops.append(
            pymongo.UpdateOne(
                {"symbol": coin["symbol"].upper()},
                {"$set": coin},
                upsert=True
            )
        )

    if bulk_ops:
        mongo.db.coins.bulk_write(bulk_ops)
        print(f"Updated {len(bulk_ops)} coins in database")


class TokenDashboard:
    """This class will mainly use the Coin Lore API to fetch general crypto data."""

    def __init__(self):
        self.general_data = []
        self.coingecko_data = []
        self.coingecko_key = os.getenv("COINGECKO_KEY")
        self.moralis_key = os.getenv("MORALIS_KEY")
        self.coinapi_key = os.getenv("COINAPI_KEY")

    def general_token_data(self):
        """Fetch all data needed for the dashboard on the index page."""
        URLS = [
            "https://api.coinlore.net/api/tickers/?start=0&limit=100",
            "https://api.coinlore.net/api/tickers/?start=100&limit=100",
            "https://api.coinlore.net/api/tickers/?start=200&limit=100",
            "https://api.coinlore.net/api/tickers/?start=300&limit=100",
            "https://api.coinlore.net/api/tickers/?start=400&limit=100",
        ]

        top500 = []  # Initialize an empty list

        for url in URLS:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json().get(
                    "data", []
                )  # Extract the list from "data" key

                for token in data:
                    token_data = {
                        "name": token["name"],
                        "symbol": token["symbol"].upper(),
                        "price": float(token["price_usd"]),
                        "change_24h": float(token["percent_change_24h"]),
                        "change_1h": float(token["percent_change_1h"]),
                        "change_7d": float(token["percent_change_7d"]),
                        "market_cap": float(token["market_cap_usd"]),
                        "volume_24h": float(token["volume24"]),
                        "rank": token["rank"],
                        "sector": None,
                        "last_updated": datetime.utcnow()
                    }

                    top500.append(token_data)
            else:
                print(f"Failed to fetch data from {url}")

        self.general_data = top500  # Store the fetched data

        # Update MongoDB with the data
        if mongo:
            update_coin_data(top500)

            # Store current prices in historical collection
            historical_points = []
            current_time = datetime.utcnow()

            for token in top500:
                historical_points.append({
                    "symbol": token["symbol"],
                    "price": token["price"],
                    "timestamp": current_time
                })

            store_historical_prices(historical_points)

        return top500

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
        historical_points = []
        current_time = datetime.utcnow()

        for url in URLS:
            try:
                response = requests.get(
                    url,
                    headers={
                        "accept": "application/json",
                        "x-cg-demo-api-key": self.coingecko_key,
                    },
                    params=params,
                )

                # Add a delay to respect rate limits
                time.sleep(1.5)

                if response.status_code == 200:
                    coingecko_data = response.json()  # Parse JSON object

                    for token in coingecko_data:
                        # Create historical price point for this token
                        historical_points.append({
                            "symbol": token["symbol"].upper(),
                            "price": float(token["current_price"]),
                            "timestamp": current_time
                        })

                        top500_coingecko.append({
                            "id": token["id"],
                            "symbol": token["symbol"].upper(),
                            "image": token["image"],
                            "current_price": float(token["current_price"]),
                            "market_cap_rank": token["market_cap_rank"],
                            "price_change_percentage_24h": (
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
                            "last_updated": current_time
                        })
                else:
                    print(f"Failed to fetch data from {url}: Status code {response.status_code}")
                    print(f"Response: {response.text}")
            except Exception as e:
                print(f"Error fetching data from {url}: {str(e)}")

        self.coingecko_data = top500_coingecko  # Store the fetched data in the class attribute

        # Update MongoDB with the data
        if mongo:
            update_coin_data(top500_coingecko)
            store_historical_prices(historical_points)

        return top500_coingecko  # Return the processed top500 data

    def get_token_metadata(self):
        """This method is insanely slow due to individual HTTP requests."""
        top500_names = []

        # Get all top500 names
        for data in self.general_data:
            top500_names.append(data["name"].lower())

        # Fetch the top 500 in 5 batches of 100
        all_coins_data = []
        for page_num in range(1, 6):  # 5 pages to cover 500 coins
            batch_str = ",".join(top500_names[(page_num - 1) * 100: page_num * 100])

            url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={batch_str}&order=market_cap_desc&per_page=100&page={page_num}"

            response = requests.get(
                url,
                headers={
                    "accept": "application/json",
                    "x-cg-demo-api-key": self.coingecko_key,
                },
            )

            if response.status_code == 200:
                coins_data = response.json()
                all_coins_data.extend(coins_data)

        # Now fetch categories for each coin
        for coin in all_coins_data:
            coin_id = coin["id"]
            coin_details_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"

            coin_details_response = requests.get(
                coin_details_url,
                headers={
                    "accept": "application/json",
                    "x-cg-demo-api-key": self.coingecko_key,
                },
            )

            if coin_details_response.status_code == 200:
                coin_details = coin_details_response.json()
                categories = coin_details.get("categories", [])
                print(f"Coin: {coin['name']}, Categories: {categories}")

    def get_top1k_currencies(self):
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

    def fetch_historical_data(self, coin_id, days=7):
        """Fetch historical price data for a coin from CoinGecko"""
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days,
            "interval": "hourly"
        }

        try:
            response = requests.get(
                url,
                headers={
                    "accept": "application/json",
                    "x-cg-demo-api-key": self.coingecko_key,
                },
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                prices = data.get("prices", [])

                # Get the coin symbol
                coin_data = mongo.db.coins.find_one({"id": coin_id})
                if not coin_data:
                    # Try to find by lowercase symbol as id
                    coin_data = mongo.db.coins.find_one({"symbol": coin_id.upper()})
                    if not coin_data:
                        print(f"Coin with ID {coin_id} not found in database")
                        return []

                symbol = coin_data["symbol"]

                # Format the data for our database
                price_points = []
                for price_point in prices:
                    timestamp = datetime.fromtimestamp(price_point[0] / 1000)  # Convert milliseconds to datetime
                    price = price_point[1]

                    price_points.append({
                        "symbol": symbol,
                        "price": price,
                        "timestamp": timestamp
                    })

                # Store historical prices
                if mongo and price_points:
                    store_historical_prices(price_points)

                return price_points
            else:
                print(f"Failed to fetch historical data for {coin_id}: {response.status_code}")
                return []

        except Exception as e:
            print(f"Error fetching historical data for {coin_id}: {str(e)}")
            return []

    def plot_7d_price_chart(self, symbol):
        """Get 7-day price chart data for a symbol"""
        symbol = symbol.upper()

        # Get price history from the database
        history = get_coin_history(symbol, days=7)

        # If we don't have enough data points, try to backfill
        if len(history) < 24:  # Arbitrary threshold for "enough" data points
            # Find the coin ID for this symbol
            coin_data = mongo.db.coins.find_one({"symbol": symbol})

            if coin_data and "id" in coin_data:
                # Use the CoinGecko ID to fetch historical data
                self.fetch_historical_data(coin_data["id"], days=7)

                # Get the updated history
                history = get_coin_history(symbol, days=7)
            else:
                # Try using symbol as ID (lowercase)
                self.fetch_historical_data(symbol.lower(), days=7)

                # Get the updated history
                history = get_coin_history(symbol, days=7)

        return history


# Scheduler for periodic data updates
def start_scheduler():
    """Start the background scheduler for periodic updates"""
    scheduler = BackgroundScheduler()
    dashboard = TokenDashboard()

    # Schedule hourly updates of price data
    scheduler.add_job(
        dashboard.coingecko_top500,
        'interval',
        hours=1,
        next_run_time=datetime.now()
    )

    scheduler.start()
    print("Scheduler started for hourly price updates")
    return scheduler