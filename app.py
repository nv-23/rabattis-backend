import requests
from bs4 import BeautifulSoup
import sqlite3
from flask import Flask, jsonify
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
DB = "rabattkoder.db"

# Initiera DB och tabell
def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rabattkoder (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                butik TEXT,
                kod TEXT,
                beskrivning TEXT,
                url TEXT,
                hämtad_datum TEXT
            )
        """)
init_db()

# Scraper för Rabble.se (exempel)
def scrape_rabble():
    url = "https://rabble.se/rabattkoder"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    koder = []

    # Anpassa efter Rabble:s HTML-struktur, här ett exempel:
    for card in soup.select(".coupon-card"):  # ändra selector vid behov
        butik = card.select_one(".coupon-card__brand").get_text(strip=True) if card.select_one(".coupon-card__brand") else "Okänd"
        kod = card.select_one(".coupon-code") and card.select_one(".coupon-code").get_text(strip=True) or ""
        beskrivning = card.select_one(".coupon-card__title") and card.select_one(".coupon-card__title").get_text(strip=True) or ""
        länk = card.select_one("a")["href"] if card.select_one("a") else url

        if kod:
            koder.append({
                "butik": butik,
                "kod": kod,
                "beskrivning": beskrivning,
                "url": länk
            })

    return koder

# Spara koder i DB (uppdaterar gamla om kod finns)
def save_koder(koder):
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        for k in koder:
            c.execute("""
                SELECT id FROM rabattkoder WHERE kod=? AND butik=?
            """, (k["kod"], k["butik"]))
            res = c.fetchone()
            if res:
                c.execute("""
                    UPDATE rabattkoder SET beskrivning=?, url=?, hämtad_datum=?
                    WHERE id=?
                """, (k["beskrivning"], k["url"], datetime.utcnow().isoformat(), res[0]))
            else:
                c.execute("""
                    INSERT INTO rabattkoder (butik, kod, beskrivning, url, hämtad_datum)
                    VALUES (?, ?, ?, ?, ?)
                """, (k["butik"], k["kod"], k["beskrivning"], k["url"], datetime.utcnow().isoformat()))
        conn.commit()

# Kör scraper och spara resultat
def run_scrape_save():
    print("Startar scraping av rabattkoder...")
    koder = scrape_rabble()
    print(f"Hämtade {len(koder)} koder från Rabble.se")
    save_koder(koder)
    print("Sparade koder i databasen.")

# API-endpoint som returnerar alla koder
@app.route("/api/koder")
def api_koder():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute("SELECT butik, kod, beskrivning, url FROM rabattkoder ORDER BY hämtad_datum DESC")
        rows = c.fetchall()
        koder = [{
            "butik": r[0],
            "kod": r[1],
            "beskrivning": r[2],
            "url": r[3]
        } for r in rows]
    return jsonify({"koder": koder})

# Schemalägg scraping var 6:e timme
scheduler = BackgroundScheduler()
scheduler.add_job(run_scrape_save, 'interval', hours=6)
scheduler.start()

# Kör en gång direkt vid start
run_scrape_save()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
