from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Enkel in-memory-databas (nollställs varje gång Render startar om)
all_koder = []

@app.route("/")
def home():
    return "Rabattkods-API är igång!"

@app.route("/api/koder", methods=["GET"])
def get_koder():
    return jsonify({"koder": all_koder})

@app.route("/api/koder", methods=["POST"])
def post_koder():
    global all_koder
    data = request.get_json()
    if not data or "koder" not in data:
        return jsonify({"error": "Ingen data skickades."}), 400
    all_koder = data["koder"]
    return jsonify({"message": f"{len(all_koder)} koder sparade."})

# Debug-endpoint (valfritt)
@app.route("/debug/db", methods=["GET"])
def debug_db():
    return jsonify(all_koder)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))  # Render använder env PORT
    app.run(host="0.0.0.0", port=port)
