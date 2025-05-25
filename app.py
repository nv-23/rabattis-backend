from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/koder")
def get_koder():
    rabattkoder = [
        {"butik": "H&M", "kod": "SOMMAR15", "beskrivning": "15% på allt", "url": "https://www.hm.com"},
        {"butik": "Zalando", "kod": "VÅR2025", "beskrivning": "20% på vårkollektionen", "url": "https://www.zalando.se"},
        {"butik": "Lyko", "kod": "BEAUTY20", "beskrivning": "20% på hudvård", "url": "https://www.lyko.com"},
        {"butik": "CDON", "kod": "TECH10", "beskrivning": "10% på elektronik", "url": "https://www.cdon.se"},
        {"butik": "Apotek Hjärtat", "kod": "VITAMIN10", "beskrivning": "10% på vitaminer", "url": "https://www.apotekhjartat.se"},
        {"butik": "Dahl Skincare", "kod": "DAHL2025", "beskrivning": "20% ny kund", "url": "https://dahlskincare.se"}
    ]
    return jsonify({"koder": rabattkoder})

if __name__ == "__main__":
    app.run(debug=True)
