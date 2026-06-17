#!/usr/bin/env python3
"""
ML Counter Helper - daily data updater.

WHAT THIS DOES TODAY
  1. Reads data.js (the file the website loads).
  2. Refreshes the "updated" date.
  3. (Optional) merges in fresh data from a live source - see fetch_live_data().
  4. Writes data.js back out in the same format.

It is built to run automatically every day on GitHub Actions
(see .github/workflows/update.yml). You can also run it by hand:

    python scripts/update_data.py

Because data.js is just `window.MLBB_DATA = { ...valid JSON... };`, this script
strips the wrapper, edits the JSON, and writes the wrapper back. No extra files.
"""

import datetime
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data.js"

PREFIX = "window.MLBB_DATA ="
SUFFIX = ";"


def load_data():
    """Read data.js and return the data as a normal Python dict."""
    text = DATA_FILE.read_text(encoding="utf-8")
    start = text.index("{")
    end = text.rindex("}")
    return json.loads(text[start:end + 1])


def save_data(data):
    """Write the dict back to data.js in the format the website expects."""
    body = json.dumps(data, indent=2, ensure_ascii=False)
    DATA_FILE.write_text(PREFIX + "\n" + body + "\n" + SUFFIX + "\n", encoding="utf-8")


def fetch_live_data():
    """
    Scrapes current meta builds and counters from mlbbhub.com (Legend+ data).
    Returns True if successful, False if something went wrong.
    The scraper writes directly to data.js, so we return a flag not a list.
    """
    try:
        from scripts.scrape_builds import run as scrape_run
        ok, fail = scrape_run(verbose=False)
        print("Scraped %d heroes from mlbbhub.com (%d kept existing)" % (len(ok), len(fail)))
        return True
    except Exception as e:
        print("Scraper error: %s  — keeping existing data." % e)
        return False


def main():
    # scraper writes data.js directly; we reload afterwards to stamp the date
    success = fetch_live_data()
    data = load_data()
    data["updated"] = datetime.date.today().isoformat()
    save_data(data)
    status = "live scrape OK" if success else "scrape failed, kept existing"
    print("Wrote data.js  (updated = %s, %s)" % (data["updated"], status))


if __name__ == "__main__":
    main()
