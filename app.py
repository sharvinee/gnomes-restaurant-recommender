import csv
import os

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


def normalize(value):
    return (value or "").strip().lower()


def normalize_price(value):
    return (value or "").strip()

def load_restaurants():
    restaurants = []
    try:
        with open("restaurants.csv", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Filter out None keys that can appear if row has extra fields
                row = {k: v for k, v in row.items() if k is not None}
                row["dietary_tags"] = [tag.strip().lower() for tag in row["dietary_tags"].split(",")]
                restaurants.append(row)
    except FileNotFoundError:
        print("CSV file not found yet.")
    return restaurants


def get_filter_options(restaurants):
    cuisines = sorted({r["cuisine"] for r in restaurants if r.get("cuisine")})
    prices = sorted({r["price"] for r in restaurants if r.get("price")}, key=len)
    dietary = sorted({tag for r in restaurants for tag in r["dietary_tags"] if tag})
    return {
        "cuisines": cuisines,
        "prices": prices,
        "dietary": dietary,
    }


def filter_restaurants(restaurants, cuisine, price, dietary):
    cuisine_value = normalize(cuisine)
    price_value = normalize_price(price)
    dietary_value = normalize(dietary)

    filtered = []
    for restaurant in restaurants:
        if cuisine_value and cuisine_value != "any":
            if normalize(restaurant.get("cuisine")) != cuisine_value:
                continue

        if price_value and normalize(price_value) != "any" and restaurant.get("price") != price_value:
            continue

        if dietary_value and dietary_value not in {"any", "none", "no restriction"}:
            if dietary_value not in restaurant.get("dietary_tags", []):
                continue

        filtered.append(restaurant)

    return filtered, None

@app.route("/")
def home():
    restaurants = load_restaurants()
    options = get_filter_options(restaurants)
    return render_template("index.html", options=options, restaurants=restaurants)

@app.route("/spin-options", methods=["POST"])
def spin_options():
    payload = request.get_json(silent=True) or {}
    cuisine = payload.get("cuisine")
    price = payload.get("price")
    dietary = payload.get("dietary")

    restaurants = load_restaurants()
    filtered, error = filter_restaurants(restaurants, cuisine, price, dietary)

    if error:
        return jsonify({"ok": False, "message": error, "restaurants": []}), 400

    if not filtered:
        return jsonify({
            "ok": True,
            "message": "No restaurants matched those filters. Try changing price or dietary preference.",
            "restaurants": [],
        })

    return jsonify({
        "ok": True,
        "message": f"Found {len(filtered)} restaurant(s). Spin to choose one.",
        "restaurants": filtered,
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
