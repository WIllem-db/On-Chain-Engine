from flask import Flask, render_template, jsonify
import os
from datetime import datetime
import mongoengine as me
from utils import *
from models import *

app = Flask(__name__)

# Connect to MongoDB using MongoEngine
me.connect('crypto_dashboard', host='mongodb://localhost:27017/crypto_dashboard')

# Start the scheduler for periodic data updates
scheduler = start_scheduler()


@app.route("/")
def index():
    """Main dashboard page."""
    # Get top cryptocurrencies sorted by market cap
    top_coins = Coin.objects.order_by('market_cap_rank')[:50]

    return render_template("index.html", top_coins=top_coins, abs=abs)


@app.route("/api/coins")
def get_coins():
    """API endpoint to get all coins."""
    coins = Coin.objects.order_by('market_cap_rank')

    # Convert to JSON-serializable format
    result = []
    for coin in coins:
        result.append({
            "id": coin.id,
            "symbol": coin.symbol,
            "name": coin.name,
            "market_cap_rank": coin.market_cap_rank,
            "current_price": coin.current_price,
            "price_change_percentage_24h": coin.price_change_percentage_24h,
            "price_change_percentage_7d": coin.price_change_percentage_7d,
            "market_cap": coin.market_cap,
            "total_volume": coin.total_volume,
            "image": coin.image
        })

    return jsonify(result)


@app.route("/api/history/<symbol>")
def get_price_history(symbol):
    """API endpoint to get 7-day price history for a specific coin."""
    dashboard = TokenDashboard()
    history = dashboard.get_price_history(symbol)

    # Format for JSON response
    formatted_history = []
    for point in history:
        formatted_history.append({
            "timestamp": point.timestamp.isoformat(),
            "price": point.price
        })

    return jsonify({
        "symbol": symbol.upper(),
        "history": formatted_history
    })


@app.route("/api/refresh")
def refresh_data():
    """Manually trigger a data refresh."""
    dashboard = TokenDashboard()
    dashboard.coingecko_top500()
    return jsonify({"success": True, "message": "Data refresh initiated"})


@app.route("/coin/<coin_id>")
def coin_detail(coin_id):
    """Detail page for a specific coin."""
    coin = Coin.objects(id=coin_id).first_or_404()

    # Get historical data
    dashboard = TokenDashboard()
    history = dashboard.get_price_history(coin.symbol)

    return render_template("coin_detail.html", coin=coin, history=history)


if __name__ == "__main__":
    # Create necessary directories
    if not os.path.exists('static/js'):
        os.makedirs('static/js')

    # When app starts, ensure we have the latest data if database is empty
    if Coin.objects.count() == 0:
        print("Initial data load...")
        dashboard = TokenDashboard()
        dashboard.coingecko_top500()

    app.run(debug=True)