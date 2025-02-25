from flask import Flask, render_template


app = Flask(__name__)


@app.route("/")
# Index will already provide some utility for the end-user
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
