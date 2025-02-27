from flask import Flask, render_template
from utils import *

app = Flask(__name__)


@app.route("/")
# Index will already provide some utility for the end-user
def index():
    # TokenDashboard methods
    dashboard = TokenDashboard()
    top500 = dashboard.general_token_data()

    return render_template("index.html", top500=top500, abs=abs)


if __name__ == "__main__":
    app.run(debug=True)
