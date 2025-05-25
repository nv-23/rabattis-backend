import requests
from bs4 import BeautifulSoup
from models import db, Rabattkod

def scrape_kampanjjakt():
    url = "https://kampanjjakt.se"
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        kampanjer = soup.select(".kampanj")[:10]

        for kampanj in kampanjer:
            butik = kampanj.select_one(".kampanjbutik").text.strip()
            beskrivning = kampanj.select_one(".kampanjtext").text.strip()
            kod = kampanj.select_one(".kod span")
            kod = kod.text.strip() if kod else ""
            länk = kampanj.select_one("a")["href"]

            rabatt = Rabattkod(
                butik=butik,
                kod=kod or "Ingen kod",
                beskrivning=beskrivning,
                url=länk,
                kategori="okänd",
                utgår=""
            )
            db.session.add(rabatt)
        db.session.commit()
    except Exception as e:
        print("Scrapingfel:", e)
