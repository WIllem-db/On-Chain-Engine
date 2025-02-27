import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class TokenDashboard:
    """This class will mainly use the Coin Lore API to fetch general crypto data."""

    def __init__(self):
        self.general_data = []

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
                data = response.json().get("data", [])  # Extract the list from "data" key

                for token in data:
                    top500.append({
                        "name": token["name"],
                        "ticker": token["symbol"],
                        "price": float(token["price_usd"]),
                        "change_24h": float(token["percent_change_24h"]),  # Corrected key
                        "change_1h": float(token["percent_change_1h"]),
                        "change_7d": float(token["percent_change_7d"]),
                        "market_cap": float(token["market_cap_usd"]),
                        "volume_24h": float(token["volume24"]),
                        "rank": token["rank"],
                        "sector": None
                    })
            else:
                print(f"Failed to fetch data from {url}")

        self.general_data = top500  # Store the fetched data
        return top500


# Run methods here
ds = TokenDashboard()
ds.general_token_data()
