#!/usr/bin/env python3
"""
ML Counter Helper - dataset builder (run this to get the FULL hero roster).

What it does:
  - Loads the current data.js (keeps every hero already in there, including the
    hand-written detailed ones).
  - Adds every other Mobile Legends hero from the ROSTER below, giving each a
    sensible role-based build + counters so nothing is empty.
  - Writes data.js back out with all heroes, sorted by name.

Run it whenever you want to (re)generate the roster:

    python scripts/build_dataset.py

A brand-new hero released after this was written? Add one line to ROSTER
(e.g.  ("NewHero", "Fighter"),) and run it again.
"""

import datetime
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data.js"
PREFIX = "window.MLBB_DATA ="
SUFFIX = ";"

# ---------------------------------------------------------------------------
# The full hero roster: (Hero Name, Primary Role)
# Roles: Marksman / Assassin / Mage / Fighter / Tank / Support
# ---------------------------------------------------------------------------
ROSTER = [
    # --- Tanks ---
    ("Akai", "Tank"), ("Atlas", "Tank"), ("Baxia", "Tank"), ("Belerick", "Tank"),
    ("Edith", "Tank"), ("Franco", "Tank"), ("Gatotkaca", "Tank"), ("Gloo", "Tank"),
    ("Grock", "Tank"), ("Hilda", "Tank"), ("Hylos", "Tank"), ("Johnson", "Tank"),
    ("Khufra", "Tank"), ("Lolita", "Tank"), ("Minotaur", "Tank"), ("Tigreal", "Tank"),
    ("Uranus", "Tank"),
    # --- Fighters ---
    ("Aldous", "Fighter"), ("Alpha", "Fighter"), ("Alucard", "Fighter"),
    ("Argus", "Fighter"), ("Arlott", "Fighter"), ("Aulus", "Fighter"),
    ("Badang", "Fighter"), ("Balmond", "Fighter"), ("Barats", "Fighter"),
    ("Chou", "Fighter"), ("Cici", "Fighter"), ("Dyrroth", "Fighter"),
    ("Fredrinn", "Fighter"), ("Freya", "Fighter"), ("Guinevere", "Fighter"),
    ("Jawhead", "Fighter"), ("Julian", "Fighter"), ("Khaleed", "Fighter"),
    ("Lapu-Lapu", "Fighter"), ("Leomord", "Fighter"), ("Lukas", "Fighter"),
    ("Martis", "Fighter"), ("Masha", "Fighter"), ("Minsitthar", "Fighter"),
    ("Paquito", "Fighter"), ("Phoveus", "Fighter"), ("Roger", "Fighter"),
    ("Ruby", "Fighter"), ("Silvanna", "Fighter"), ("Sun", "Fighter"),
    ("Suyou", "Fighter"), ("Terizla", "Fighter"), ("Thamuz", "Fighter"),
    ("X.Borg", "Fighter"), ("Yu Zhong", "Fighter"), ("Zilong", "Fighter"),
    # --- Assassins ---
    ("Aamon", "Assassin"), ("Benedetta", "Assassin"), ("Fanny", "Assassin"),
    ("Gusion", "Assassin"), ("Hanzo", "Assassin"), ("Hayabusa", "Assassin"),
    ("Helcurt", "Assassin"), ("Joy", "Assassin"), ("Karina", "Assassin"),
    ("Lancelot", "Assassin"), ("Ling", "Assassin"), ("Natalia", "Assassin"),
    ("Nolan", "Assassin"), ("Saber", "Assassin"), ("Selena", "Assassin"),
    ("Yin", "Assassin"),
    # --- Mages ---
    ("Alice", "Mage"), ("Aurora", "Mage"), ("Cecilion", "Mage"), ("Chang'e", "Mage"),
    ("Cyclops", "Mage"), ("Esmeralda", "Mage"), ("Eudora", "Mage"), ("Gord", "Mage"),
    ("Harith", "Mage"), ("Harley", "Mage"), ("Kadita", "Mage"), ("Kagura", "Mage"),
    ("Lunox", "Mage"), ("Luo Yi", "Mage"), ("Lylia", "Mage"), ("Nana", "Mage"),
    ("Novaria", "Mage"), ("Odette", "Mage"), ("Pharsa", "Mage"), ("Vale", "Mage"),
    ("Valentina", "Mage"), ("Valir", "Mage"), ("Vexana", "Mage"), ("Xavier", "Mage"),
    ("Yve", "Mage"), ("Zhask", "Mage"), ("Zhuxin", "Mage"),
    # --- Marksmen ---
    ("Beatrix", "Marksman"), ("Brody", "Marksman"), ("Bruno", "Marksman"),
    ("Claude", "Marksman"), ("Clint", "Marksman"), ("Granger", "Marksman"),
    ("Hanabi", "Marksman"), ("Irithel", "Marksman"), ("Ixia", "Marksman"),
    ("Karrie", "Marksman"), ("Kimmy", "Marksman"), ("Layla", "Marksman"),
    ("Lesley", "Marksman"), ("Melissa", "Marksman"), ("Miya", "Marksman"),
    ("Moskov", "Marksman"), ("Natan", "Marksman"), ("Popol and Kupa", "Marksman"),
    ("Wanwan", "Marksman"), ("Yi Sun-shin", "Marksman"),
    # --- Supports ---
    ("Angela", "Support"), ("Carmilla", "Support"), ("Chip", "Support"),
    ("Diggie", "Support"), ("Estes", "Support"), ("Faramis", "Support"),
    ("Floryn", "Support"), ("Kaja", "Support"), ("Mathilda", "Support"),
    ("Rafaela", "Support"),
]

ROLE_EMOJI = {
    "Marksman": "🏹", "Assassin": "🗡️", "Mage": "🔮",
    "Fighter": "⚔️", "Tank": "🛡️", "Support": "💫",
}

# Default builds per role (used for heroes that don't have a hand-written one).
ROLE_BUILD = {
    "Marksman": {
        "boots": "Swift Boots",
        "items": ["Berserker's Fury", "Blade of Despair", "Hunter Strike", "Malefic Roar", "Wind of Nature"],
        "note": "Stay behind your tank, hit the closest threat, and kite backwards while attacking.",
    },
    "Assassin": {
        "boots": "Tough Boots",
        "items": ["Hunter Strike", "Blade of Despair", "Endless Battle", "Malefic Roar", "Immortality"],
        "note": "Wait for the enemy carry to be exposed, burst them down, then get out. Don't dive the whole team.",
    },
    "Mage": {
        "boots": "Magic Shoes",
        "items": ["Clock of Destiny", "Lightning Truncheon", "Divine Glaive", "Holy Crystal", "Blood Wings"],
        "note": "Poke from max range and keep your burst ready for when the enemy commits.",
    },
    "Fighter": {
        "boots": "Warrior Boots",
        "items": ["Bloodlust Axe", "Endless Battle", "Blade of Despair", "Malefic Roar", "Immortality"],
        "note": "Pressure the side lane and join fights from the flank, not head-on into CC.",
    },
    "Tank": {
        "boots": "Tough Boots",
        "items": ["Dominance Ice", "Antique Cuirass", "Athena's Shield", "Immortality", "Blade Armor"],
        "note": "Start the fight by locking the enemy carry, then peel for your own damage dealers.",
    },
    "Support": {
        "boots": "Arcane Boots",
        "items": ["Enchanted Talisman", "Oracle", "Fleeting Time", "Immortality", "Athena's Shield"],
        "note": "Stay close to your carry, save them with your skills, and keep key areas warded.",
    },
}

# Who is generally good against each role (these hero ids all exist in the roster).
ROLE_COUNTERS = {
    "Marksman": ["saber", "fanny", "lancelot", "gusion", "hayabusa"],
    "Mage": ["fanny", "ling", "lancelot", "saber", "gusion"],
    "Assassin": ["khufra", "franco", "kaja", "tigreal", "akai"],
    "Fighter": ["khufra", "franco", "valir", "eudora", "diggie"],
    "Tank": ["granger", "lesley", "valir", "karrie", "kimmy"],
    "Support": ["fanny", "gusion", "ling", "lancelot", "saber"],
}

ROLE_VSTIP = {
    "Marksman": "Squishy with little or no escape — dive them with an assassin or lock them with CC and they fall fast. Don't let them free-hit from the backline.",
    "Assassin": "Lives on mobility and burst. Hard CC (stun / suppress / knock-up) stops them cold, and a little armor blunts their combo. Group up so they can't catch you alone.",
    "Mage": "Big burst from range but fragile. Dodge their skill-shots, then gap-close — assassins punish them while their combo is on cooldown.",
    "Fighter": "Strong in long fights. Kite them with slows and poke, and don't duel head-on — collapse with your team or out-range them.",
    "Tank": "Hard to kill but low damage — don't waste burst on them. Poke them down, bring anti-heal, and focus the carry behind them.",
    "Support": "Keeps their team alive. Dive past them to kill the carry, or burst the support first with an assassin if they're out of position.",
}


def slug(name):
    s = name.lower().replace("'", "").replace(".", "")
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s


def load_data():
    text = DATA_FILE.read_text(encoding="utf-8")
    start = text.index("{")
    end = text.rindex("}")
    return json.loads(text[start:end + 1])


def save_data(data):
    body = json.dumps(data, indent=2, ensure_ascii=False)
    DATA_FILE.write_text(PREFIX + "\n" + body + "\n" + SUFFIX + "\n", encoding="utf-8")


def main():
    data = load_data()
    existing = {h["id"]: h for h in data["heroes"]}

    # All hero ids that will exist after this run (used to clean counter lists).
    all_ids = set(existing) | {slug(name) for name, _ in ROSTER}

    added = 0
    for name, role in ROSTER:
        hid = slug(name)
        if hid in existing:
            continue  # keep the detailed, hand-written entry as-is
        counters = [c for c in ROLE_COUNTERS[role] if c in all_ids and c != hid]
        existing[hid] = {
            "id": hid,
            "name": name,
            "role": role,
            "emoji": ROLE_EMOJI[role],
            "difficulty": "Medium",
            "counters": counters,
            "vsTip": ROLE_VSTIP[role],
            "build": ROLE_BUILD[role],
        }
        added += 1

    # Drop counter ids that point to heroes that don't exist (safety).
    for h in existing.values():
        h["counters"] = [c for c in h.get("counters", []) if c in all_ids]

    data["heroes"] = sorted(existing.values(), key=lambda h: h["name"].lower())
    data["updated"] = datetime.date.today().isoformat()
    save_data(data)

    print("Total heroes: %d  (added %d new, kept %d detailed)" %
          (len(data["heroes"]), added, len(data["heroes"]) - added))


if __name__ == "__main__":
    main()
