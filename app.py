import os
import requests
from bs4 import BeautifulSoup
import sqlite3
from flask import Flask, jsonify, request
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
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

# ---------- Scraper Rabble.se ----------
def scrape_rabble():
    url = "https://rabble.se/rabattkoder"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    koder = []

    for card in soup.select(".coupon-card"):
        butik = card.select_one(".coupon-card__brand")
        butik = butik.get_text(strip=True) if butik else "Okänd"

        kod_el = card.select_one(".coupon-code")
        kod = kod_el.get_text(strip=True) if kod_el else ""

        beskrivning_el = card.select_one(".coupon-card__title")
        beskrivning = beskrivning_el.get_text(strip=True) if beskrivning_el else ""

        länk_el = card.select_one("a")
        länk = länk_el["href"] if länk_el and länk_el.has_attr("href") else url

        if kod:
            koder.append({
                "butik": butik,
                "kod": kod,
                "beskrivning": beskrivning,
                "url": länk
            })

    return koder

# ---------- Scraper Kampanjjakt.se ----------
def scrape_kampanjjakt():
    url = "https://kampanjjakt.se/rabattkoder"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    koder = []

    for card in soup.select(".coupon"):
        butik_el = card.select_one(".store-name")
        butik = butik_el.get_text(strip=True) if butik_el else "Okänd"

        kod_el = card.select_one(".code")
        kod = kod_el.get_text(strip=True) if kod_el else ""

        beskrivning_el = card.select_one(".description")
        beskrivning = beskrivning_el.get_text(strip=True) if beskrivning_el else ""

        länk_el = card.select_one("a")
        länk = länk_el["href"] if länk_el and länk_el.has_attr("href") else url

        if kod:
            koder.append({
                "butik": butik,
                "kod": kod,
                "beskrivning": beskrivning,
                "url": länk
            })

    return koder

# ---------- Scraper Flashback Forum ----------
def scrape_flashback():
    url = "https://www.flashback.org/forum/81-rabattkoder"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    koder = []

    for tråd in soup.select(".topic-list__item")[:5]:
        titel_el = tråd.select_one(".topic-list__title")
        titel = titel_el.get_text(strip=True) if titel_el else ""
        länk_el = tråd.select_one("a")
        länk = "https://www.flashback.org" + länk_el["href"] if länk_el and länk_el.has_attr("href") else url

        kod = ""
        if "kod" in titel.lower():
            delar = titel.split()
            for del_str in delar:
                if len(del_str) >= 4 and del_str.isalnum():
                    kod = del_str
                    break

        if kod:
            koder.append({
                "butik": "Flashback",
                "kod": kod,
                "beskrivning": titel,
                "url": länk
            })

    return koder

# ---------- Spara koder i DB ----------
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

# ---------- Kör scraper och spara resultat ----------
def run_scrape_save():
    print("Startar scraping...")
    alla_koder = []
    for scraper in [scrape_rabble, scrape_kampanjjakt, scrape_flashback]:
        try:
            koder = scraper()
            print(f"Hämtade {len(koder)} från {scraper.__name__}")
            alla_koder.extend(koder)
        except Exception as e:
            print(f"Fel i {scraper.__name__}: {e}")

    save_koder(alla_koder)
    print(f"Totalt sparade koder: {len(alla_koder)}")

# ---------- API ----------
@app.route("/api/koder")
def api_koder():
    butik_filter = request.args.get("butik")
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        query = "SELECT butik, kod, beskrivning, url FROM rabattkoder"
        params = []
        if butik_filter:
            query += " WHERE butik LIKE ?"
            params.append(f"%{butik_filter}%")
        query += " ORDER BY hämtad_datum DESC"
        c.execute(query, params)
        rows = c.fetchall()
        koder = [{
            "butik": r[0],
            "kod": r[1],
            "beskrivning": r[2],
            "url": r[3]
        } for r in rows]
    return jsonify({"koder": koder})

# ---------- Starta scraping direkt + schemalägg ----------
scheduler = BackgroundScheduler()
scheduler.add_job(run_scrape_save, 'interval', hours=6)
scheduler.start()
run_scrape_save()

# ---------- Huvudkörning ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
