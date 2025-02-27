import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class TokenDashboard:
    """This class will mainly use the Coin Lore API to fetch general crypto data."""

    def __init__(self):
        self.general_data = []
        self.coingecko_key = os.getenv("COINGECKO_KEY")

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
                    top500.append(
                        {
                            "name": token["name"],
                            "ticker": token["symbol"],
                            "price": float(token["price_usd"]),
                            "change_24h": float(
                                token["percent_change_24h"]
                            ),  # Corrected key
                            "change_1h": float(token["percent_change_1h"]),
                            "change_7d": float(token["percent_change_7d"]),
                            "market_cap": float(token["market_cap_usd"]),
                            "volume_24h": float(token["volume24"]),
                            "rank": token["rank"],
                            "sector": None,
                        }
                    )
            else:
                print(f"Failed to fetch data from {url}")

        self.general_data = top500  # Store the fetched data
        return top500

    def coingecko_top500(self):
        """This method will handle fetching the top500 coins from Coingecko API."""
        URLS = [
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1",
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=2",
        ]

        params = {
            "price_change_percentage": "1h,24h,7d,30d"
        }

        top500_coingecko = []  # Initialize an empty list

        for url in URLS:
            response = requests.get(url,
                                    headers={"accept": "application/json", "x-cg-demo-api-key": self.coingecko_key},
                                    params=params)
            if response.status_code == 200:
                coingecko_data = response.json()  # Parse JSON object

                for token in coingecko_data:
                    top500_coingecko.append(
                        {
                            "id": token["id"],
                            "symbol": token["symbol"],
                            "image": token["image"],  # Assuming image is available in 'thumb'
                            "current_price": float(token["current_price"]),
                            "market_cap_rank": token["market_cap_rank"],
                            "price_change_percentage_24": float(token["price_change_percentage_24h"]),
                            "price_change_percentage_1h": float(
                                token["price_change_percentage_1h_in_currency"]) if token.get(
                                "price_change_percentage_1h_in_currency") is not None else 0.0,
                            "price_change_percentage_7d": float(
                                token["price_change_percentage_7d_in_currency"]) if token.get(
                                "price_change_percentage_7d_in_currency") is not None else 0.0,
                            "price_change_percentage_30d": float(
                                token["price_change_percentage_30d_in_currency"]) if token.get(
                                "price_change_percentage_30d_in_currency") is not None else 0.0,
                            "total_volume": float(token["total_volume"]),
                            "market_cap": float(token["market_cap"]),
                        }
                    )
            else:
                print(f"Failed to fetch data from {url}")

        self.coingecko_data = top500_coingecko  # Store the fetched data in the class attribute
        print(top500_coingecko)  # Optional: print the data for debugging
        return top500_coingecko  # Return the processed top500 data


# Run methods here
ds = TokenDashboard()
ds.general_token_data()
ds.coingecko_top500()
