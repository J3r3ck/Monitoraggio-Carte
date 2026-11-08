import os, re, sys, time, requests
from bs4 import BeautifulSoup

URL = "https://www.hareruyamtg.com/en/products/detail/194809?lang=JP"
CHECKS = int(os.getenv("CHECKS", "1"))
INTERVAL = int(os.getenv("INTERVAL", "30"))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en,ja;q=0.8",
}
# es. "NM 40,000 JPY 0"
PATTERN = re.compile(r"\b(NM|SP|MP|HP)\s*[￥¥]?\s*([\d,]+)\s*(?:JPY|円)?\s*(\d+)\b")

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
    for t in soup(["script", "style"]):
        t.decompose()
    text = soup.get_text(" ", strip=True)
    head = text.split("Weekly Sold")[0]  # solo la tabella dell'articolo, non gli altri
    rows = PATTERN.findall(head)
    if not rows:
        raise RuntimeError("Righe di stock non trovate: la pagina potrebbe essere cambiata")
    print("Letto:", rows)
    return [f"{c} {p} JPY (stock: {s})" for c, p, s in rows if int(s) > 0]

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
