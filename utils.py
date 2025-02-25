import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class TokenDashboard:
    """This class  will handle the basic token data."""

    # My methods will have similar names as in the API docs, so you can easily find the specific docs

    def __init__(self):
        self.api_key = os.getenv("COINGECKO_KEY")
        self.base_url = "https://api.coingecko.com/api/v3"

    def simple_request(self, endpoint, params=None):
        """Handles API requests dynamically with basic error handling."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"accept": "application/json", "x-cg-demo-api-key": self.api_key}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise error for bad responses
            return response.json()
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            return None

    def check_ping(self):
        # This method will check API server status
        # Keep in mind can check the API server status in multiple different ways
        url = "https://api.coingecko.com/api/v3/ping"

        headers = {"accept": "application/json", "x-cg-demo-api-key": self.api_key}

        response = requests.get(url, headers=headers)

        if response.text == '{"gecko_says":"(V3) To the Moon!"}':
            print("API Status: 200")
        else:
            print("API Status: 500")

    def supported_currencies_list(self):
        """This method should print a list of the top crypto currencies"""
        supported_currencies_list = (self.simple_request("simple/supported_vs_currencies"))  # No extra params needed
        # print(len(supported_currencies_list))  # For some reason we only get 64 elements, which is annoying, might have to find another method to load the top 1k tokens ordered by MKTCAP



# Run here
run = TokenDashboard()
run.check_ping()
run.supported_currencies_list()

