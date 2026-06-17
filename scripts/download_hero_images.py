#!/usr/bin/env python3
"""
Downloads Mobile Legends hero portrait images from the wiki CDN.
Saves them to images/heroes/ so they work locally and on GitHub Pages.

Run once:
    python scripts/download_hero_images.py
"""

import hashlib
import json
import pathlib
import re
import time
import urllib.request
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT  = ROOT / "images" / "heroes"
OUT.mkdir(parents=True, exist_ok=True)

DATA_FILE = ROOT / "data.js"

# Some heroes have a different filename on the wiki than their in-game name
WIKI_NAME_OVERRIDES = {
    # Add any overrides here if discovered during download
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://mobile-legends.fandom.com/",
    "Accept": "image/webp,image/png,*/*",
}


def load_hero_names():
    text  = DATA_FILE.read_text(encoding="utf-8")
    start = text.index("{")
    end   = text.rindex("}")
    data  = json.loads(text[start:end + 1])
    return [h["name"] for h in data["heroes"]]


def local_slug(name):
    """Hero name → safe local filename."""
    s = name.lower()
    s = s.replace("'", "").replace(".", "").replace(" ", "_")
    s = re.sub(r"_+", "_", s).strip("_")
    return s + ".png"


def wiki_filename(name):
    """Hero name → MediaWiki filename (spaces become underscores, case kept)."""
    wiki_name = WIKI_NAME_OVERRIDES.get(name, name)
    return wiki_name.replace(" ", "_") + ".png"


def cdn_url(name, size=128):
    """Build Fandom CDN URL for the hero portrait."""
    fn  = wiki_filename(name)
    md5 = hashlib.md5(fn.encode("utf-8")).hexdigest()
    encoded = urllib.parse.quote(fn, safe="()'.")
    return (
        f"https://static.wikia.nocookie.net/mobile-legends/images/"
        f"{md5[0]}/{md5[0:2]}/{encoded}"
        f"/revision/latest/scale-to-width-down/{size}"
    )


def try_download(url, dest):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            if r.status == 200:
                data = r.read()
                if len(data) > 500:
                    dest.write_bytes(data)
                    return True
    except Exception:
        pass
    return False


def main():
    names = load_hero_names()
    print(f"Downloading portraits for {len(names)} heroes...\n")

    ok, fail = [], []
    for name in names:
        dest = OUT / local_slug(name)
        if dest.exists():
            print(f"  skip  {name}")
            ok.append(name)
            continue

        print(f"  get   {name} ...", end=" ", flush=True)
        url = cdn_url(name)
        if try_download(url, dest):
            print("ok")
            ok.append(name)
        else:
            print("FAILED")
            fail.append(name)

        time.sleep(0.3)

    print(f"\nDone: {len(ok)} downloaded, {len(fail)} failed")
    if fail:
        print("Failed:", fail)

    # Write JS mapping so app.js can look up portraits by hero name
    mapping = {name: "images/heroes/" + local_slug(name) for name in ok}
    js = "window.HERO_IMAGES = " + json.dumps(mapping, indent=2, ensure_ascii=False) + ";\n"
    (ROOT / "hero_images.js").write_text(js, encoding="utf-8")
    print("Wrote hero_images.js")


if __name__ == "__main__":
    main()
