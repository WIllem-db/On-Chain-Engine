from flask import Flask, render_template
from utils import *

app = Flask(__name__)


@app.route("/")
# Index will already provide some utility for the end-user
def index():
    # TokenDashboard methods
    dashboard = TokenDashboard()
    top500 = dashboard.coingecko_top500()  # Fetches the top 500 crypto currencies
    sector = dashboard.map_sectors()  # Self.coingecko_data with an extra sector row # This method seems to slow down the website, came up with a proper solution (see solution file)

    return render_template("index.html", top500=top500, sector=sector, abs=abs)


if __name__ == "__main__":
    app.run(debug=True)
