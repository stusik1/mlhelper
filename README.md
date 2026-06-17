# ⚔️ ML Counter Helper

A simple web app for **Mobile Legends**: type the **enemy hero** you're up against
and instantly see **who counters them** plus the **recommended build & items**.

Works on your phone (and PC) in any browser. No install needed.

---

## ✅ How to open it RIGHT NOW (on your PC)

1. Open the `MLhelper` folder.
2. Double-click **`index.html`**.
3. It opens in your browser. Type an enemy hero name and tap them. Done!

> Everything runs in the browser — there's no server to start.

---

## 📱 How to use it on your PHONE

You have two easy options:

### Option A — Put it online for free (best, recommended)
This also turns on the **daily auto-update**. We'll do it together, but the short version:

1. Make a free account at [github.com](https://github.com).
2. Create a new repository and upload this whole folder.
3. Turn on **GitHub Pages** (Settings → Pages → deploy from `main` branch).
4. GitHub gives you a link like `https://yourname.github.io/MLhelper/`.
5. Open that link on your phone and "Add to Home Screen" — it acts like an app.

### Option B — Quick test today (no account)
Copy the `MLhelper` folder to your phone (USB / Google Drive) and open
`index.html` with your phone's browser. Good for a quick look; Option A is better long-term.

---

## 🔄 The daily auto-update

- `scripts/update_data.py` is the updater. Right now it refreshes the date and
  keeps the data tidy.
- `.github/workflows/update.yml` runs it **automatically every day** once the app
  is on GitHub (Option A above).
- **Next milestone (we do this together):** connect a real data source so builds &
  counters refresh from the live meta. Open `scripts/update_data.py` and read the
  `fetch_live_data()` function — it explains the two options (a Google Sheet you
  control, or scraping a stats site).

---

## ➕ How to add or edit heroes

All the game data is in **`data.js`**. Each hero looks like this:

```js
{
  "id": "layla",                       // lowercase, no spaces, must be unique
  "name": "Layla",
  "role": "Marksman",                  // Marksman / Assassin / Mage / Fighter / Tank / Support
  "emoji": "🏹",
  "difficulty": "Easy",
  "counters": ["fanny", "saber"],      // hero IDs that are GOOD against this hero
  "vsTip": "How to beat this enemy...",
  "build": {
    "boots": "Swift Boots",
    "items": ["Berserker's Fury", "Blade of Despair", "..."],
    "note": "A short tip about the build."
  }
}
```

To add a hero: copy one block, change the values, and make sure the `id`s inside
`counters` match real heroes in the file. Save, refresh the page — that's it.

---

## 📁 What's in the folder

| File | What it is |
|------|------------|
| `index.html` | The page |
| `style.css`  | The looks (colors, layout) |
| `app.js`     | The logic (search, counters, builds) |
| `data.js`    | **The hero data — edit this to add heroes** |
| `scripts/update_data.py` | The daily updater |
| `.github/workflows/update.yml` | Runs the updater every day |

---

*Counter and build suggestions are general guidance for drafting and laning, not a
guarantee — skill and team play still decide the match. Mobile Legends: Bang Bang is
a trademark of Moonton; this is a fan-made helper.*
