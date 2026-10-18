import os, sys, time, requests
from bs4 import BeautifulSoup

URL = "https://shops.hareruyamtg.com/osaka/products/detail/194809?lang=JP"
CHECKS = int(os.getenv("CHECKS", "1"))
INTERVAL = int(os.getenv("INTERVAL", "30"))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.8",
}

def telegram(text):
    r = requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
        data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": text},
        timeout=15,
    )
    r.raise_for_status()

def check():
    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        head = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
        if "在庫" not in head:
            continue
        idx = head.index("在庫")
        found = []
        for tr in rows[1:]:
            cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
            if len(cells) > idx and cells[idx].isdigit() and int(cells[idx]) > 0:
                found.append(f"{cells[0]} {cells[1]} (stock: {cells[idx]})")
        return found
    raise RuntimeError("Tabella stock non trovata: la pagina potrebbe essere cambiata")

def main():
    if os.getenv("TEST_TELEGRAM"):
        telegram("✅ Test: il bot funziona")
        return
    ok = 0
    for i in range(CHECKS):
        try:
            found = check()
            ok += 1
            print("Disponibile:" if found else "Esaurito", found)
            if found:
                telegram("🚨 DISPONIBILE!\n" + "\n".join(found) + "\n" + URL)
                return
        except Exception as e:
            print("Errore:", e)
        if i < CHECKS - 1:
            time.sleep(INTERVAL)
    if ok == 0:
        sys.exit(1)

main()
