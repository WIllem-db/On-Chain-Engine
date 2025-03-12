import base64

from flask import Flask, render_template, jsonify, send_file, current_app
from utils import TokenDashboard
from mongoengine import connect
import threading
import os
from datetime import datetime


app = Flask(__name__)

# Global cache for price histories
price_history_cache = {}
is_fetching = False


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


# Background thread function to fetch price histories
def fetch_price_histories_background(coins, num_coins=50):
    global price_history_cache, is_fetching

    try:
        dashboard = TokenDashboard()
        # Start with the top N coins to prioritize popular ones
        for coin in coins[:num_coins]:
            symbol = coin['symbol'].upper()
            try:
                price_history_cache[symbol] = dashboard.fetch_price_history_by_symbol(symbol)
                print(f"Fetched price history for {symbol}")
            except Exception as e:
                print(f"Error fetching price history for {symbol}: {e}")
    finally:
        is_fetching = False
        print("Background fetching completed")


# Call this function at application startup
setup_mongodb()


@app.route("/")
def index():
    global is_fetching

    dashboard = TokenDashboard()
    coins = dashboard.coingecko_top500()  # Fetches basic info
    plots = dashboard.plot_7d_chart()  # All plots are stored in a buffer

    app.config["PLOT_BUFFERS"] = plots  # Acces this from chart route

    # Start a background thread to fetch price histories if not already fetching
    if not is_fetching:
        is_fetching = True
        # Start background thread to fetch price histories
        threading.Thread(
            target=fetch_price_histories_background,
            args=(coins,)
        ).start()

    # Return the page without waiting for price histories
    return render_template('dashboard.html', coins=coins, abs=abs)


@app.route('/api/price-chart/<symbol>')
def get_price_chart(symbol):
    """Endpoint to get price history data for a specific coin"""
    symbol = symbol.upper()

    # Get from cache if available
    if symbol in price_history_cache:
        price_data = price_history_cache[symbol]
    else:
        # Fetch if not in cache
        dashboard = TokenDashboard()
        price_data = dashboard.fetch_price_history_by_symbol(symbol)
        price_history_cache[symbol] = price_data

    # Convert to format suitable for charts
    chart_data = []
    for entry in price_data:
        chart_data.append({
            'timestamp': entry['timestamp'].isoformat(),
            'price': entry['price']
        })

    return jsonify(chart_data)


@app.route('/coin/<symbol>')
def coin_detail(symbol):
    symbol = symbol.upper()
    dashboard = TokenDashboard()

    # Get basic coin info
    coins = dashboard.coingecko_top500()
    coin_info = next((coin for coin in coins if coin['symbol'].upper() == symbol), None)

    if not coin_info:
        return f"Cryptocurrency {symbol} not found", 404

    # Get price history (either from cache or fetch it)
    if symbol in price_history_cache:
        price_data = price_history_cache[symbol]
    else:
        price_data = dashboard.fetch_price_history_by_symbol(symbol)
        price_history_cache[symbol] = price_data

    return render_template('token-panel.html',
                           symbol=symbol,
                           coin_info=coin_info,
                           price_data=price_data,
                           is_detail_view=True)


@app.route("/chart/<ticker>")
def get_chart(ticker):
    plots = current_app.config.get("PLOT_BUFFERS", {})

    if ticker in plots:
        buffer = plots[ticker]
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype="image/png",
            as_attachment=False,
            download_name=f"{ticker}_chart.png"
        )
    else:
        # Return a placeholder or error if chart doesn't exist, this shouldn't be a possible since I already handled cases like this in the plot_7d_chart method
        return send_file(
            "static/img/loading-chart.png",
            mimetype="image/png"
        ), f404



if __name__ == "__main__":
    app.run(debug=True)