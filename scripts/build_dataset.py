#!/usr/bin/env python3
"""
ML Counter Helper - dataset builder.
Run this any time to rebuild data.js with all 126 heroes + matchup tags.

    python scripts/build_dataset.py
"""

import datetime
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data.js"
PREFIX = "window.MLBB_DATA ="
SUFFIX = ";"

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

# Tags describe what the hero DOES so the matchup engine can give smart advice.
# dmg: what kind of damage they deal (physical / magic / mixed / true)
# cc:  how much crowd-control they have (none / low / high)
# mobility: how mobile they are (low / medium / high)
# style: their main style (burst / sustain / poke / tank / support)
ROLE_TAGS = {
    "Marksman": {"dmg": "physical", "cc": "low",  "mobility": "low",    "style": "poke"},
    "Assassin": {"dmg": "physical", "cc": "low",  "mobility": "high",   "style": "burst"},
    "Mage":     {"dmg": "magic",    "cc": "low",  "mobility": "low",    "style": "burst"},
    "Fighter":  {"dmg": "physical", "cc": "low",  "mobility": "medium", "style": "sustain"},
    "Tank":     {"dmg": "physical", "cc": "high", "mobility": "low",    "style": "tank"},
    "Support":  {"dmg": "magic",    "cc": "medium","mobility": "low",   "style": "support"},
}

# Per-hero overrides for anything that differs from their role default.
HERO_TAGS = {
    "franco":     {"cc": "high", "style": "tank"},
    "tigreal":    {"cc": "high", "style": "tank"},
    "khufra":     {"cc": "high", "mobility": "medium"},
    "atlas":      {"cc": "high"},
    "akai":       {"cc": "high"},
    "lolita":     {"cc": "high"},
    "minotaur":   {"cc": "high"},
    "johnson":    {"cc": "high", "mobility": "medium"},
    "gatotkaca":  {"cc": "high"},
    "badang":     {"cc": "high"},
    "minsitthar": {"cc": "high"},
    "kaja":       {"cc": "high"},
    "eudora":     {"cc": "high"},
    "aurora":     {"cc": "high"},
    "nana":       {"cc": "high"},
    "odette":     {"cc": "high"},
    "luo-yi":     {"cc": "high"},
    "selena":     {"cc": "high"},
    "chou":       {"cc": "high", "mobility": "high"},
    "ruby":       {"cc": "high", "style": "sustain"},
    "fanny":      {"mobility": "high"},
    "ling":       {"mobility": "high"},
    "lancelot":   {"mobility": "high"},
    "hayabusa":   {"mobility": "high"},
    "gusion":     {"mobility": "high"},
    "benedetta":  {"mobility": "high"},
    "joy":        {"mobility": "high"},
    "harith":     {"mobility": "high"},
    "mathilda":   {"mobility": "high"},
    "wanwan":     {"mobility": "high"},
    "esmeralda":  {"dmg": "magic", "style": "sustain"},
    "kagura":     {"cc": "medium"},
    "valir":      {"cc": "medium", "style": "poke"},
    "alice":      {"style": "sustain"},
    "alucard":    {"style": "sustain"},
    "yu-zhong":   {"style": "sustain"},
    "uranus":     {"style": "sustain", "dmg": "mixed"},
    "masha":      {"style": "sustain"},
    "thamuz":     {"style": "sustain"},
    "kimmy":      {"dmg": "mixed"},
    "natan":      {"dmg": "mixed"},
    "roger":      {"dmg": "mixed"},
    "karrie":     {"dmg": "true"},
    "argus":      {"style": "sustain"},
    "helcurt":    {"cc": "high"},
    "diggie":     {"cc": "medium"},
    "carmilla":   {"cc": "medium"},
    "rafaela":    {"cc": "medium"},
    "estes":      {"style": "support", "cc": "low"},
    "floryn":     {"style": "support"},
    "angela":     {"style": "support"},
}

ROLE_BUILD = {
    "Marksman": {
        "boots": "Swift Boots",
        "items": ["Berserker's Fury", "Blade of Despair", "Hunter Strike", "Malefic Roar", "Wind of Nature"],
        "note": "Stay behind your tank, hit the closest threat, and kite backwards while attacking.",
    },
    "Assassin": {
        "boots": "Tough Boots",
        "items": ["Hunter Strike", "Blade of Despair", "Endless Battle", "Malefic Roar", "Immortality"],
        "note": "Wait for the enemy carry to be exposed, burst them down, then get out.",
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

ROLE_COUNTERS = {
    "Marksman": ["saber", "fanny", "lancelot", "gusion", "hayabusa"],
    "Mage":     ["fanny", "ling", "lancelot", "saber", "gusion"],
    "Assassin": ["khufra", "franco", "kaja", "tigreal", "akai"],
    "Fighter":  ["khufra", "franco", "valir", "eudora", "diggie"],
    "Tank":     ["granger", "lesley", "valir", "karrie", "kimmy"],
    "Support":  ["fanny", "gusion", "ling", "lancelot", "saber"],
}

ROLE_VSTIP = {
    "Marksman": "Squishy with little escape — dive them with an assassin or lock them with CC and they fall fast.",
    "Assassin": "Lives on mobility and burst. Hard CC stops them cold. Group up so they can't catch you alone.",
    "Mage": "Big burst from range but fragile. Dodge their skill-shots, then gap-close while they're on cooldown.",
    "Fighter": "Strong in long fights. Kite them with slows and poke — don't duel them straight up.",
    "Tank": "Hard to kill but low damage. Ignore them, focus the carry, and bring penetration items.",
    "Support": "Keeps their team alive. Dive past them to kill the carry, or assassinate them first if out of position.",
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


def make_tags(role, hid):
    tags = dict(ROLE_TAGS[role])
    tags.update(HERO_TAGS.get(hid, {}))
    return tags


def main():
    data = load_data()
    existing = {h["id"]: h for h in data["heroes"]}
    all_ids = set(existing) | {slug(name) for name, _ in ROSTER}

    added = 0
    for name, role in ROSTER:
        hid = slug(name)
        tags = make_tags(role, hid)
        if hid in existing:
            # Always refresh tags even on detailed heroes so engine stays current.
            existing[hid]["tags"] = tags
            continue
        counters = [c for c in ROLE_COUNTERS[role] if c in all_ids and c != hid]
        existing[hid] = {
            "id": hid,
            "name": name,
            "role": role,
            "emoji": ROLE_EMOJI[role],
            "difficulty": "Medium",
            "tags": tags,
            "counters": counters,
            "vsTip": ROLE_VSTIP[role],
            "build": ROLE_BUILD[role],
        }
        added += 1

    for h in existing.values():
        # Ensure every hero has tags (back-fill any that were hand-written without them).
        if "tags" not in h:
            h["tags"] = make_tags(h["role"], h["id"])
        h["counters"] = [c for c in h.get("counters", []) if c in all_ids]

    data["heroes"] = sorted(existing.values(), key=lambda h: h["name"].lower())
    data["updated"] = datetime.date.today().isoformat()
    save_data(data)

    print("Total heroes: %d  (added %d new, refreshed %d)" %
          (len(data["heroes"]), added, len(data["heroes"]) - added))


if __name__ == "__main__":
    main()
