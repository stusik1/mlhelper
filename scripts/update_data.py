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
    MILESTONE 2 (we do this next, together):
    Pull fresh counters/builds from a live source and return a list of hero
    dicts in the SAME shape as the "heroes" list in data.js.

    Until that is wired up, return None and we keep the existing hero data.

    Good source options (pick one):
      - A Google Sheet you maintain  -> publish as CSV, read it here. Easiest,
        fully legal, and you control the data.
      - A community stats website    -> scrape it. Powerful, but check the
        site's Terms of Service / robots.txt first, and it can break when the
        site changes.
    """
    return None


def main():
    data = load_data()

    live = fetch_live_data()
    if live:
        data["heroes"] = live
        print("Merged %d heroes from live source." % len(live))
    else:
        print("No live source connected yet - keeping existing %d heroes." %
              len(data["heroes"]))

    data["updated"] = datetime.date.today().isoformat()
    save_data(data)
    print("Wrote data.js  (updated = %s)" % data["updated"])


if __name__ == "__main__":
    main()
