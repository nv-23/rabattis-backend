from flask import Flask, jsonify, request
from flask_cors import CORS
from models import db, Rabattkod, init_db
from scraper import scrape_kampanjjakt

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///koder.db'
db.init_app(app)

@app.route("/api/koder")
def get_koder():
    query = Rabattkod.query
    butik = request.args.get("butik")
    kategori = request.args.get("kategori")

    if butik:
        query = query.filter(Rabattkod.butik.ilike(f"%{butik}%"))
    if kategori:
        query = query.filter(Rabattkod.kategori.ilike(f"%{kategori}%"))

    resultat = [{
        "butik": k.butik,
        "kod": k.kod,
        "beskrivning": k.beskrivning,
        "url": k.url,
        "kategori": k.kategori,
        "utgår": k.utgår
    } for k in query.all()]
    return jsonify({"koder": resultat})

if __name__ == "__main__":
    import os
    with app.app_context():
        init_db()
        scrape_kampanjjakt()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

