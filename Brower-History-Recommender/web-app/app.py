from flask import Flask, jsonify, render_template, request

from recommender import recommend

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/recommend")
def api_recommend():
    data = request.get_json(silent=True) or {}
    try:
        result = recommend(data)
    except Exception as exc:
        return jsonify({"error": f"Server error: {exc}"}), 500
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
