#!/usr/bin/env python3
"""
ML Counter Helper — live build scraper.

Fetches current meta builds and counters from mlbbhub.com (Legend+ ranked data).
Updates data.js with the fresh information.

Run manually any time:
    python scripts/scrape_builds.py

The daily GitHub Action calls update_data.py which calls fetch_live_data()
which imports and calls this module.

SOURCE: mlbbhub.com — stats updated from Legend+ matches, refreshed daily.
"""

import datetime
import html as html_module
import json
import pathlib
import re
import time
import urllib.request
import urllib.parse

ROOT      = pathlib.Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data.js"
PREFIX    = "window.MLBB_DATA ="
SUFFIX    = ";"

BASE_URL = "https://mlbbhub.com/heroes/"

# --------------------------------------------------------------------------
# Hero-name → URL slug mapping (handles special characters)
# --------------------------------------------------------------------------
SLUG_OVERRIDES = {
    "X.Borg": "x-borg",
    "Popol and Kupa": "popol-and-kupa",
}

def hero_slug(name):
    if name in SLUG_OVERRIDES:
        return SLUG_OVERRIDES[name]
    s = name.lower()
    s = s.replace("'", "")          # Chang'e → change
    s = s.replace(".", "-")         # X.Borg  → x-borg
    s = s.replace(" ", "-")         # Yi Sun-shin → yi-sun-shin (hyphens kept)
    s = re.sub(r"-+", "-", s)
    return s

# --------------------------------------------------------------------------
# HTTP fetch with retry
# --------------------------------------------------------------------------
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MLHelper-bot/1.0)"}

def fetch_url(url, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as r:
                if r.status == 200:
                    return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
    return None

# --------------------------------------------------------------------------
# HTML parsing helpers
# --------------------------------------------------------------------------
def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()

def find_section(html, *keywords):
    """Return the portion of HTML after the first keyword heading found."""
    for kw in keywords:
        idx = html.lower().find(kw.lower())
        if idx != -1:
            return html[idx:]
    return ""

# Map site item names → names used in our data.js / image files
ITEM_NAME_MAP = {
    "Magic Boots":  "Magic Shoes",
    "Brute Force Breastplate": "Antique Cuirass",
    "Oracle's Lens": "Oracle",
}

def extract_items(html):
    """
    Pull build items from JSON-LD HowTo structured data — much more reliable
    than scraping HTML links. Returns items from the first (primary) build.
    """
    blocks = re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    for b in blocks:
        try:
            d = json.loads(b)
            if d.get("@type") == "HowTo" and "supply" in d:
                names = [s["name"] for s in d["supply"] if s.get("@type") == "HowToSupply"]
                # Apply name normalization
                return [ITEM_NAME_MAP.get(n, n) for n in names if n]
        except Exception:
            continue
    return []

def extract_counters(html):
    """
    Find the 'Counters' section and pull hero names + win rates.
    Returns list of (hero_name, win_rate_float) sorted desc by win rate.
    """
    section = find_section(html, "counters", "counter")
    if not section:
        section = html          # fall back to whole page

    # Pattern from mlbbhub: >HeroName</span><span class="...text-mlbb-green...">57.1<!-- -->% WR</span>
    pairs = []
    for m in re.finditer(r'>([A-Z][^<>]{1,30})</span><span[^>]*text-mlbb-green[^>]*>(\d+\.?\d*)<!--', section):
        name = html_module.unescape(m.group(1).strip())
        wr   = float(m.group(2))
        if name and len(name) > 1:
            pairs.append((name, wr))

    # Keep top 5 by win rate, filter out the hero themselves
    pairs.sort(key=lambda x: -x[1])
    return pairs[:5]

# --------------------------------------------------------------------------
# Per-hero scrape
# --------------------------------------------------------------------------
def scrape_hero(name, verbose=False):
    slug = hero_slug(name)
    url  = BASE_URL + slug
    html = fetch_url(url)

    if not html:
        if verbose: print(f"    FAIL HTTP error for {name} ({url})")
        return None

    if "404" in html[:500] or "not found" in html[:500].lower():
        if verbose: print(f"    FAIL not found: {name} ({url})")
        return None

    items    = extract_items(html)
    counters = extract_counters(html)

    if len(items) < 6:
        if verbose: print(f"    FAIL could not parse build for {name} (got {len(items)} items)")
        return None

    # First build: boots + 5 items
    build = {
        "boots": items[0],
        "items": items[1:6],
        "note":  "Build from mlbbhub.com (Legend+ data, auto-updated daily).",
    }

    counter_names = [c[0] for c in counters]

    if verbose:
        print(f"    OK {name}: {items[0]} + {', '.join(items[1:6])}")
        if counter_names:
            print(f"      counters: {', '.join(counter_names)}")

    return {"build": build, "counters": counter_names}

# --------------------------------------------------------------------------
# Main — fetch all heroes and merge into data.js
# --------------------------------------------------------------------------
def load_data():
    text  = DATA_FILE.read_text(encoding="utf-8")
    start = text.index("{")
    end   = text.rindex("}")
    return json.loads(text[start:end + 1])

def save_data(data):
    body = json.dumps(data, indent=2, ensure_ascii=False)
    DATA_FILE.write_text(PREFIX + "\n" + body + "\n" + SUFFIX + "\n", encoding="utf-8")

def slug_to_id(name):
    """Convert hero name to the same id format used in data.js."""
    s = name.lower().replace("'", "").replace(".", "")
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s

def run(test_heroes=None, verbose=True):
    """
    Scrape and update.
    Pass test_heroes=["Granger","Layla"] to test a subset first.
    """
    data    = load_data()
    by_id   = {h["id"]: h for h in data["heroes"]}

    targets = test_heroes or [h["name"] for h in data["heroes"]]
    ok, fail = [], []

    for name in targets:
        hid = slug_to_id(name)
        if hid not in by_id:
            if verbose: print(f"  skip {name} (not in data.js)")
            continue

        if verbose: print(f"  {name} ...", end=" ", flush=True)
        result = scrape_hero(name, verbose=False)

        if result:
            by_id[hid]["build"]    = result["build"]
            # Only update counters if we got at least 3
            if len(result["counters"]) >= 3:
                # Convert counter names to ids
                cids = [slug_to_id(c) for c in result["counters"]]
                by_id[hid]["counters"] = [c for c in cids if c in by_id]
            ok.append(name)
            if verbose:
                print(f"   OK {result['build']['boots']} + "
                      f"{', '.join(result['build']['items'][:2])}")
        else:
            fail.append(name)
            if verbose: print("   kept existing")

        time.sleep(0.5)   # be polite — ~0.5s between requests

    data["heroes"]  = sorted(by_id.values(), key=lambda h: h["name"].lower())
    data["updated"] = datetime.date.today().isoformat()
    data["source"]  = "mlbbhub.com (Legend+ ranked matches)"
    save_data(data)

    print(f"\nUpdated {len(ok)} heroes  |  kept existing for {len(fail)}")
    print(f"   Data source: mlbbhub.com (Legend+ ranked matches)")
    if fail:
        print(f"   Could not scrape: {fail}")
    return ok, fail


if __name__ == "__main__":
    import sys
    # Quick test mode: python scripts/scrape_builds.py test
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("=== TEST MODE (5 heroes) ===")
        run(test_heroes=["Granger", "Layla", "Fanny", "Chou", "Esmeralda"],
            verbose=True)
    else:
        print("=== FULL SCRAPE ===")
        run(verbose=True)
