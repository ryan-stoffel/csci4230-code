"""Day-cluster sample of GitHub repositories created 2019-01-01 to 2025-09-27.

For each calendar month, one day is drawn at random (seed 4230). Every repository
created on that day with >= 10 stars in the six target languages is enumerated
through the search API. Raw responses are stored under raw/ so the snapshot is fixed.
Set GITHUB_TOKEN to raise the search limit from 10 to 30 requests per minute.
"""
import calendar, json, os, random, time, urllib.error, urllib.parse, urllib.request
from datetime import date

LANGS = ["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java"]
END = date(2025, 9, 27)
TOKEN = os.environ.get("GITHUB_TOKEN")

def sample_days(seed=4230):
    rng = random.Random(seed)
    y, m = 2019, 1
    while date(y, m, 1) <= END:
        last = calendar.monthrange(y, m)[1]
        if (y, m) == (END.year, END.month):
            last = END.day
        yield date(y, m, rng.randint(1, last))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)

def get(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "csci4230-research"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    while True:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                remaining = int(r.headers.get("x-ratelimit-remaining", "1"))
                reset = int(r.headers.get("x-ratelimit-reset", "0"))
                body = json.load(r)
            if remaining == 0:
                time.sleep(max(reset - time.time(), 0) + 2)
            return body
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                reset = int(e.headers.get("x-ratelimit-reset", "0") or 0)
                time.sleep(max(reset - time.time(), 5) + 2)
            elif e.code >= 500:
                time.sleep(10)
            else:
                raise
        except Exception:
            time.sleep(10)

def main():
    os.makedirs("raw", exist_ok=True)
    for day in sample_days():
        for lang in LANGS:
            q = f"language:{lang} created:{day} stars:>=10 fork:false"
            page = 1
            while True:
                out = f"raw/{lang}_{day}_p{page}.json"
                if os.path.exists(out):
                    body = json.load(open(out))
                else:
                    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
                        {"q": q, "per_page": 100, "page": page})
                    body = get(url)
                    body["_query"] = q
                    body["_fetched"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    with open(out, "w") as f:
                        json.dump(body, f)
                    print(out, body.get("total_count"), len(body.get("items", [])), flush=True)
                total = min(body.get("total_count", 0), 1000)
                if page * 100 >= total or not body.get("items"):
                    break
                page += 1

if __name__ == "__main__":
    main()
