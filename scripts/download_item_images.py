#!/usr/bin/env python3
"""
Downloads Mobile Legends item images from the wiki.
Saves them to images/items/ so they work locally and on GitHub Pages.

Run once:
    python scripts/download_item_images.py
"""

import hashlib
import os
import pathlib
import re
import time
import urllib.request
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT  = ROOT / "images" / "items"
OUT.mkdir(parents=True, exist_ok=True)

# Every item used in our builds
ITEMS = [
    # Boots
    "Swift Boots", "Tough Boots", "Magic Shoes", "Warrior Boots", "Arcane Boots",
    # Marksman
    "Berserker's Fury", "Scarlet Phantom", "Blade of Despair", "Malefic Roar",
    "Wind of Nature", "Windtalker", "Corrosion Scythe", "Demon Hunter Sword",
    "Golden Staff", "Hunter Strike", "Sea Halberd",
    # Mage
    "Clock of Destiny", "Lightning Truncheon", "Divine Glaive", "Holy Crystal",
    "Blood Wings", "Calamity Reaper", "Genius Wand", "Enchanted Talisman",
    "Oracle", "Necklace of Durance", "Concentrated Energy",
    # Fighter / Assassin
    "Endless Battle", "Bloodlust Axe", "Fleeting Time",
    # Tank / Defense
    "Dominance Ice", "Antique Cuirass", "Athena's Shield", "Immortality",
    "Blade Armor", "Cursed Helmet",
]


def slug(name):
    """Item name → safe filename (no special chars)."""
    s = name.lower()
    s = s.replace("'", "").replace(".", "").replace(" ", "_")
    return s + ".png"


def wiki_filename(name):
    """Convert item name to MediaWiki canonical filename."""
    s = name.replace(" ", "_")
    if s:
        s = s[0].upper() + s[1:]
    return s + ".png"


def wiki_url(name):
    """Build the Fandom CDN URL using MediaWiki's MD5-based path."""
    fn = wiki_filename(name)
    md5 = hashlib.md5(fn.encode("utf-8")).hexdigest()
    encoded = urllib.parse.quote(fn, safe="()'")
    return (
        f"https://static.wikia.nocookie.net/mobile-legends/images/"
        f"{md5[0]}/{md5[0:2]}/{encoded}"
        f"/revision/latest/scale-to-width-down/64?cb=20200101000000"
    )


def try_download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status == 200:
                data = r.read()
                if len(data) > 500:       # real image, not an error page
                    dest.write_bytes(data)
                    return True
    except Exception:
        pass
    return False


def download_from_page(name, dest):
    """Fallback: scrape the wiki article page for the og:image URL."""
    article = "https://mobile-legends.fandom.com/wiki/" + urllib.parse.quote(
        name.replace(" ", "_"), safe="()'")
    req = urllib.request.Request(article, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="replace")
        m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if m:
            img_url = m.group(1).split("?")[0]   # strip query string
            # request a 64-px scaled version
            img_url += "/revision/latest/scale-to-width-down/64"
            return try_download(img_url, dest)
    except Exception:
        pass
    return False


def main():
    ok, fail = [], []
    for name in ITEMS:
        dest = OUT / slug(name)
        if dest.exists():
            print(f"  skip  {name} (already downloaded)")
            ok.append(name)
            continue

        print(f"  get   {name} ...", end=" ", flush=True)
        url = wiki_url(name)
        if try_download(url, dest):
            print("ok (CDN)")
            ok.append(name)
        else:
            # CDN path didn't work — try scraping the wiki page
            time.sleep(0.4)
            if download_from_page(name, dest):
                print("ok (page)")
                ok.append(name)
            else:
                print("FAILED")
                fail.append(name)
        time.sleep(0.3)   # be polite to the wiki

    print(f"\nDone: {len(ok)} downloaded, {len(fail)} failed")
    if fail:
        print("Failed items:", fail)

    # Write the JS mapping so app.js can look up images by item name
    mapping = {name: "images/items/" + slug(name) for name in ok}
    js = "window.ITEM_IMAGES = " + __import__("json").dumps(mapping, indent=2) + ";\n"
    (ROOT / "item_images.js").write_text(js, encoding="utf-8")
    print("Wrote item_images.js")


if __name__ == "__main__":
    main()
