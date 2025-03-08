from flask import Flask, render_template
from utils import *
from mongoengine import connect
import threading
import os

app = Flask(__name__)


# MongoDB connection
def setup_mongodb():
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("Warning: MONGODB_URI not found in environment variables")
        mongodb_uri = "mongodb://localhost:27017/crypto_tracker"

    try:
        connect(host=mongodb_uri)
        print("MongoDB connection established")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")


# Define the initialization function here
def initialize_price_history_data():
    dashboard = TokenDashboard()
    dashboard.initialize_price_history_data(50)  # Call the method on the instance


# Call this function at application startup
setup_mongodb()


@app.route("/")
# Index will already provide some utility for the end-user
def index():
    # TokenDashboard methods
    dashboard = TokenDashboard()
    coins = dashboard.coingecko_top500()  # Fetches the top 500 crypto currencies

    return render_template("index.html", coins=coins, abs=abs)


@app.route("/token-panel")
# This route will showcase the core on-chain metrics
def token_panel():
    return render_template("token-panel.html")


@app.route('/coin/<symbol>')
def coin_detail(symbol):
    # Uppercase the symbol for consistency
    symbol = symbol.upper()

    # Create a dashboard instance and fetch data
    dashboard = TokenDashboard()
    price_data = dashboard.fetch_price_history_by_symbol(symbol)

    return render_template('token-panel.html',
                          symbol=symbol,
                          price_data=price_data,
                          is_detail_view=True)  # Flag to indicate detail view


if __name__ == "__main__":
    # Create a dashboard instance
    dashboard = TokenDashboard()

    # Create and start the background thread
    data_thread = threading.Thread(
        target=dashboard.initialize_price_history_data,
        args=(50,)  # Limit to first 50 coins
    )
    data_thread.daemon = True
    data_thread.start()

    # Start the Flask application
    app.run(debug=True)