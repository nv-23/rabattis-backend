import os
import requests
from bs4 import BeautifulSoup
import sqlite3
from flask import Flask, jsonify, request
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
DB = "rabattkoder.db"

# ---------- Initiera databas ----------
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

# ---------- Scrapingfunktioner ----------
def scrape_rabble():
    url = "https://rabble.se/rabattkoder"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
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
        print(f"[rabble] Hämtade {len(koder)} koder.")
        return koder
    except Exception as e:
        print(f"[rabble] Fel: {e}")
        return []

def scrape_kampanjjakt():
    url = "https://kampanjjakt.se/rabattkoder"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
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
        print(f"[kampanjjakt] Hämtade {len(koder)} koder.")
        return koder
    except Exception as e:
        print(f"[kampanjjakt] Fel: {e}")
        return []

def scrape_flashback():
    url = "https://www.flashback.org/forum/81-rabattkoder"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
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
        print(f"[flashback] Hämtade {len(koder)} koder.")
        return koder
    except Exception as e:
        print(f"[flashback] Fel: {e}")
        return []

# ---------- Spara till databas ----------
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
    print(f"[save_koder] Totalt sparade {len(koder)} koder.")

# ---------- Kör scraping och spara ----------
def run_scrape_save():
    print("🟢 Kör scraping...")
    alla_koder = []
    for scraper in [scrape_rabble, scrape_kampanjjakt, scrape_flashback]:
        koder = scraper()
        alla_koder.extend(koder)
    save_koder(alla_koder)

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

# ---------- Debug route för att se hela DB ----------
@app.route("/debug/db")
def debug_db():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM rabattkoder ORDER BY hämtad_datum DESC")
        rows = c.fetchall()
    return jsonify(rows)

# ---------- Starta appen ----------
if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_scrape_save, 'interval', hours=6)
    scheduler.start()

    run_scrape_save()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
