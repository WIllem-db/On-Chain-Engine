from flask import Flask, render_template
from utils import *

app = Flask(__name__)


@app.route("/")
# Index will already provide some utility for the end-user
def index():
    dashboard = TokenDashboard()
    top1k_tokens = dashboard.get_top1k_tokens()
    return render_template("index.html", top1k_tokens=top1k_tokens, abs=abs)


if __name__ == "__main__":
    app.run(debug=True)
