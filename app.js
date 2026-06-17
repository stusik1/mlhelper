/*
 * ML Counter Helper — app.js
 *
 * Flow:
 *   Step 1 → pick YOUR hero
 *   Step 2 → pick the ENEMY hero in your lane
 *   Step 3 → see the best build for YOUR hero vs THAT specific enemy
 *
 * There's also a "Counter finder" tab: type an enemy, see who counters them.
 */

(function () {
  "use strict";

  const DATA = window.MLBB_DATA || { heroes: [] };
  const heroes = DATA.heroes.slice().sort((a, b) => a.name.localeCompare(b.name));
  const byId = {};
  heroes.forEach(h => { byId[h.id] = h; });

  const ROLES = ["All", "Marksman", "Assassin", "Mage", "Fighter", "Tank", "Support"];

  // ── DOM refs ──────────────────────────────────────────────────────────────
  const els = {
    tabMatchup:   document.getElementById("tab-matchup"),
    tabCounter:   document.getElementById("tab-counter"),
    viewMatchup:  document.getElementById("view-matchup"),
    viewCounter:  document.getElementById("view-counter"),

    // matchup flow
    step1:        document.getElementById("step1"),
    step2:        document.getElementById("step2"),
    step3:        document.getElementById("step3"),
    searchMe:     document.getElementById("search-me"),
    filtersMe:    document.getElementById("filters-me"),
    gridMe:       document.getElementById("grid-me"),
    meLabel:      document.getElementById("me-label"),
    searchEnemy:  document.getElementById("search-enemy"),
    filtersEnemy: document.getElementById("filters-enemy"),
    gridEnemy:    document.getElementById("grid-enemy"),
    matchupResult:document.getElementById("matchup-result"),
    btnBack1:     document.getElementById("btn-back1"),
    btnBack2:     document.getElementById("btn-back2"),

    // counter finder
    searchCounter:document.getElementById("search-counter"),
    filtersCounter:document.getElementById("filters-counter"),
    counterContent:document.getElementById("counter-content"),

    updated:      document.getElementById("updated"),
  };

  // ── App state ─────────────────────────────────────────────────────────────
  const state = {
    tab: "matchup",        // "matchup" | "counter"
    myHero: null,          // hero object I'm playing
    enemyHero: null,       // hero object I'm facing
    searchMe: "",
    searchEnemy: "",
    searchCounter: "",
    roleMe: "All",
    roleEnemy: "All",
    roleCounter: "All",
    // which step of the matchup flow: 1 = pick me, 2 = pick enemy, 3 = result
    step: 1,
    // counter finder: null = list, string = detail view
    counterDetailId: null,
  };

  // ── Utility ───────────────────────────────────────────────────────────────
  function roleClass(role) {
    return "role-" + role.toLowerCase();
  }

  function itemHTML(name, isBoots) {
    const imgs = window.ITEM_IMAGES || {};
    const src  = imgs[name];
    const img  = src ? '<img class="item-img" src="' + src + '" alt="">' : "";
    return (
      '<div class="item' + (isBoots ? " boots" : "") + '">' +
        img +
        '<span class="item-name">' + name + "</span>" +
      "</div>"
    );
  }

  function buildBlockHTML(boots, items, note) {
    const tags = itemHTML(boots, true) +
                 items.map(it => itemHTML(it, false)).join("");
    return (
      '<div class="build-items">' + tags + "</div>" +
      (note ? '<p class="build-note">💡 ' + note + "</p>" : "")
    );
  }

  function fuzzyMatch(q, name) {
    if (name.includes(q)) return true;
    // Allow 1 wrong/extra character at the end (e.g. "hanabe" → "hanabi")
    if (q.length >= 4 && name.includes(q.slice(0, -1))) return true;
    // Allow 2 wrong/extra characters at the end (e.g. "hanabee" → "hanabi")
    if (q.length >= 6 && name.includes(q.slice(0, -2))) return true;
    return false;
  }

  function filterHeroes(search, role) {
    const q = search.trim().toLowerCase();
    return heroes.filter(h =>
      (role === "All" || h.role === role) &&
      (!q || fuzzyMatch(q, h.name.toLowerCase()))
    );
  }

  // ── Hero grid ─────────────────────────────────────────────────────────────
  function makeGrid(list, onPick) {
    if (list.length === 0) {
      return '<p class="empty">No hero found. Try another name.</p>';
    }
    const cards = list.map(h =>
      '<button class="hero-card ' + roleClass(h.role) + '" data-id="' + h.id + '">' +
        '<span class="hero-emoji">' + h.emoji + "</span>" +
        '<span class="hero-name">' + h.name + "</span>" +
        '<span class="hero-role">' + h.role + "</span>" +
      "</button>"
    ).join("");
    return '<div class="grid">' + cards + "</div>";
  }

  function bindGrid(container, onPick) {
    container.querySelectorAll(".hero-card").forEach(btn => {
      btn.addEventListener("click", () => onPick(byId[btn.dataset.id]));
    });
  }

  // ── Filters / chips ───────────────────────────────────────────────────────
  function renderChips(container, activeRole, onSelect) {
    container.innerHTML = "";
    ROLES.forEach(role => {
      const chip = document.createElement("button");
      chip.className = "chip" + (activeRole === role ? " active" : "");
      chip.textContent = role;
      chip.addEventListener("click", () => onSelect(role));
      container.appendChild(chip);
    });
  }

  // ═════════════════════════════════════════════════════════════════════════
  //  MATCHUP ENGINE
  //  Given MY hero + ENEMY hero, produce an adjusted build and tips.
  // ═════════════════════════════════════════════════════════════════════════
  function getMatchup(me, enemy) {
    const et = enemy.tags || {};
    let boots = me.build.boots;
    let items = me.build.items.slice();   // copy so we don't mutate original
    const tips = [];
    const keyItems = [];

    // ── Boots adjustment ────────────────────────────────────────────────────
    if (et.cc === "high") {
      if (me.role === "Marksman") {
        // MM can't afford Tough Boots (need Swift for DPS), suggest Purify spell instead
        tips.push("⚡ Enemy has strong CC — take <strong>Purify</strong> as your battle spell so you can break free.");
      } else if (me.role === "Mage" || me.role === "Support") {
        boots = "Tough Boots";
        keyItems.push("Tough Boots");
        tips.push("🥾 Switching to <strong>Tough Boots</strong> — " + enemy.name + "'s CC will hurt less.");
      } else {
        boots = "Tough Boots";
        keyItems.push("Tough Boots");
        tips.push("🥾 <strong>Tough Boots</strong> reduce CC duration — key against " + enemy.name + ".");
      }
    }

    // ── vs Magic damage ─────────────────────────────────────────────────────
    if (et.dmg === "magic" || et.dmg === "mixed") {
      if (me.role === "Marksman" || me.role === "Assassin") {
        // Swap last item for Athena's Shield
        items[items.length - 1] = "Athena's Shield";
        keyItems.push("Athena's Shield");
        tips.push("🛡️ <strong>Athena's Shield</strong> blocks a chunk of their magic burst — build it 4th or 5th.");
      } else if (me.role === "Fighter") {
        items[items.length - 1] = "Athena's Shield";
        keyItems.push("Athena's Shield");
        tips.push("🛡️ Swap your last item for <strong>Athena's Shield</strong> to survive their magic damage.");
      } else if (me.role === "Tank") {
        if (!items.includes("Athena's Shield")) {
          items[1] = "Athena's Shield";
          keyItems.push("Athena's Shield");
        }
        tips.push("🛡️ Prioritize <strong>Athena's Shield</strong> early — their magic damage can chunk tanks.");
      }
    }

    // ── vs Sustain / healers ────────────────────────────────────────────────
    if (et.style === "sustain" || et.style === "support") {
      if (et.dmg === "physical" || et.dmg === "mixed" || me.tags.dmg === "physical") {
        keyItems.push("Sea Halberd");
        items[items.length - 1] = "Sea Halberd";
        tips.push("💀 <strong>Sea Halberd</strong> cuts their healing by 50% — buy this right after your boots.");
      } else {
        keyItems.push("Necklace of Durance");
        items[items.length - 1] = "Necklace of Durance";
        tips.push("💀 <strong>Necklace of Durance</strong> halves their healing — rush it early as a mage.");
      }
    }

    // ── vs High-mobility burst assassins ────────────────────────────────────
    if (et.style === "burst" && et.mobility === "high") {
      if (me.role === "Marksman") {
        if (!items.includes("Wind of Nature")) {
          items[items.length - 1] = "Wind of Nature";
          keyItems.push("Wind of Nature");
        }
        tips.push("💨 <strong>Wind of Nature</strong> makes you immune for 2s — activate it RIGHT as " + enemy.name + " dives you.");
      } else {
        if (!items.includes("Immortality")) {
          items[items.length - 1] = "Immortality";
          keyItems.push("Immortality");
        }
        tips.push("💀 <strong>Immortality</strong> gives you a second chance — " + enemy.name + " will try to one-shot you.");
      }
    }

    // ── vs Tanks (need penetration) ──────────────────────────────────────────
    if (et.style === "tank") {
      if (me.tags.dmg === "physical" || me.tags.dmg === "mixed") {
        if (!items.includes("Malefic Roar")) {
          items[2] = "Malefic Roar";
          keyItems.push("Malefic Roar");
        }
        tips.push("🔩 <strong>Malefic Roar</strong> shreds their armor — build it 3rd so your damage sticks.");
      } else {
        if (!items.includes("Divine Glaive")) {
          items[2] = "Divine Glaive";
          keyItems.push("Divine Glaive");
        }
        tips.push("🔩 <strong>Divine Glaive</strong> pierces magic resistance — build it 3rd against this tank.");
      }
    }

    // ── vs True-damage heroes (Karrie, etc.) ─────────────────────────────────
    if (et.dmg === "true") {
      tips.push("⚠️ " + enemy.name + " deals <strong>true damage</strong> — armor and magic resist won't help. Win by outplaying, not out-iteming. Stay mobile and call for help.");
    }

    // ── Matchup-specific hand-written tips ───────────────────────────────────
    const specificTip = getSpecificTip(me, enemy);
    if (specificTip) tips.unshift("📌 " + specificTip);

    // ── Fallback tip if nothing fired ────────────────────────────────────────
    if (tips.length === 0 || (tips.length === 1 && specificTip)) {
      tips.push(getRoleTip(me.role, enemy));
    }

    return { boots, items, tips, keyItems, baseNote: me.build.note };
  }

  // A small set of hand-written hero-vs-hero tips for common matchups.
  function getSpecificTip(me, enemy) {
    const key = me.id + "vs" + enemy.id;
    const tips = {
      // Granger vs common enemies
      "grangervslayla":     "You out-range Layla easily — bully her in lane. Her zero escape means you win every 1v1 if you land your 6th bullet.",
      "grangervsesmeralda": "Esmeralda's shield absorbs magic — your physical shots ignore it. Stay at range and poke; don't let her roll into you.",
      "grangervsfranco":    "Franco's hook is your biggest threat. Stay in a bush or behind minions so the hook has no clear line to you.",
      "grangervsvalir":     "Valir has no dash — your mobility beats his poke. Sidestep his fire skills and punish from max range.",
      // Layla vs common enemies
      "layla vsfanny":      "Fanny can dive you hard — stay under tower in early game. Buy Wind of Nature and activate it the second she grabs your cable.",
      "laylavskhufra":      "Khufra stops dashes — but you have no dash anyway. Kite him backwards and poke from range; he can't catch you if you don't panic.",
      // Fanny vs tanks
      "fannyvstigreal":     "Tigreal's ult pulls everyone together — don't cable through his team during his ult or you'll be in the middle of it.",
      "fannyvskhufra":      "Khufra's ball blocks your cables. Never cable through him — cable to a wall above or beside him instead.",
      // Chou vs common enemies
      "chouvsvalir":        "Valir's S2 pushes you away and cleanses CC. Bait it, then go in — once it's on cooldown you can land your full combo.",
      "chouvsdiggie":       "Diggie's ult removes your stun. Time your combo for AFTER his ult is used, not before.",
      // Kagura vs common foes
      "kaguravsling":       "Ling can dodge your umbrella on the walls. Wait until he comes down from a wall before throwing it.",
      "kaguravsfanny":      "Fanny can cable onto you very fast. Keep your distance from walls and save your blink for when she dives.",
    };
    // try exact key, then just enemy tip if available
    return tips[key] || null;
  }

  // Generic role matchup tips (used when no specific tip exists).
  function getRoleTip(myRole, enemy) {
    const et = enemy.tags || {};
    if (et.style === "burst" && et.mobility === "high") {
      return "Don't get caught alone — " + enemy.name + " is at their strongest in a 1v1. Stick with your team and activate your defensive item the moment they dive.";
    }
    if (et.style === "tank") {
      return "Don't waste your burst on " + enemy.name + " — focus the carries behind them. Your penetration item is your best friend here.";
    }
    if (et.cc === "high") {
      return enemy.name + " has strong crowd-control. Watch their skill animations carefully and sidestep or activate Purify before the CC lands.";
    }
    if (et.dmg === "magic") {
      return enemy.name + " deals magic damage — position behind your minions to block skill-shots, and build your magic defense item early.";
    }
    if (et.style === "poke") {
      return "Don't fight " + enemy.name + " in the open — poke them from behind minions, then all-in when they're below 60% HP.";
    }
    const fallbacks = {
      "Marksman": "Play safe early, farm under tower if needed. You out-scale them — once you have two core items, look for a fight.",
      "Assassin": "Deny them easy kills. Group with your team and make them waste their burst. Without a kill, they fall behind.",
      "Mage":     "Dodge their main skill-shot and engage right after. Their combo has a gap — that's your window.",
      "Fighter":  "Don't duel them straight up unless you're ahead. Poke from range and only go all-in when they're below half HP.",
      "Tank":     "Ignore them and kill the carries. Keep your gap-closer ready for the right moment.",
      "Support":  "Kill their carry first, then the support. Or if the support is out of position, assassinate them to shut down their heals.",
    };
    return fallbacks[myRole] || "";
  }

  // ═════════════════════════════════════════════════════════════════════════
  //  RENDER — MATCHUP FLOW
  // ═════════════════════════════════════════════════════════════════════════
  function showStep(n) {
    els.step1.hidden = n !== 1;
    els.step2.hidden = n !== 2;
    els.step3.hidden = n !== 3;
    state.step = n;
    window.scrollTo(0, 0);
  }

  function renderStep1() {
    renderChips(els.filtersMe, state.roleMe, role => {
      state.roleMe = role;
      renderStep1();
    });
    const list = filterHeroes(state.searchMe, state.roleMe);
    els.gridMe.innerHTML = makeGrid(list);
    bindGrid(els.gridMe, hero => {
      state.myHero = hero;
      state.searchEnemy = "";
      state.roleEnemy = "All";
      renderStep2();
      showStep(2);
    });
  }

  function renderStep2() {
    els.meLabel.innerHTML =
      '<span class="pill ' + roleClass(state.myHero.role) + '">' +
        state.myHero.emoji + " " + state.myHero.name +
      "</span>";
    renderChips(els.filtersEnemy, state.roleEnemy, role => {
      state.roleEnemy = role;
      renderStep2();
    });
    const list = filterHeroes(state.searchEnemy, state.roleEnemy)
                 .filter(h => h.id !== state.myHero.id);
    els.gridEnemy.innerHTML = makeGrid(list);
    bindGrid(els.gridEnemy, hero => {
      state.enemyHero = hero;
      renderStep3();
      showStep(3);
    });
  }

  function renderStep3() {
    const me = state.myHero;
    const enemy = state.enemyHero;
    const matchup = getMatchup(me, enemy);

    const keyBadges = matchup.keyItems.length
      ? '<div class="key-items">' +
          '<span class="key-label">🔑 Priority vs ' + enemy.name + ':</span>' +
          matchup.keyItems.map(it => {
            const imgs = window.ITEM_IMAGES || {};
            const src  = imgs[it];
            const img  = src ? '<img class="key-img" src="' + src + '" alt="">' : "";
            return '<span class="key-item">' + img + it + "</span>";
          }).join("") +
        "</div>"
      : "";

    const tipsHTML = matchup.tips.map(t =>
      '<li class="tip-item">' + t + "</li>"
    ).join("");

    els.matchupResult.innerHTML =
      // Header
      '<div class="matchup-header">' +
        '<div class="matchup-side me ' + roleClass(me.role) + '">' +
          '<span class="hero-emoji big">' + me.emoji + "</span>" +
          '<span class="matchup-name">' + me.name + "</span>" +
          '<span class="matchup-role">' + me.role + "</span>" +
        "</div>" +
        '<div class="vs-badge">VS</div>' +
        '<div class="matchup-side enemy ' + roleClass(enemy.role) + '">' +
          '<span class="hero-emoji big">' + enemy.emoji + "</span>" +
          '<span class="matchup-name">' + enemy.name + "</span>" +
          '<span class="matchup-role">' + enemy.role + "</span>" +
        "</div>" +
      "</div>" +

      // Key items callout
      (keyBadges ? '<div class="section">' + keyBadges + "</div>" : "") +

      // Build
      '<div class="section">' +
        '<h3>⚔️ Your build as ' + me.name + ' vs ' + enemy.name + '</h3>' +
        buildBlockHTML(matchup.boots, matchup.items, matchup.baseNote) +
      "</div>" +

      // Tips
      '<div class="section">' +
        '<h3>📋 How to win this matchup</h3>' +
        '<ul class="tip-list">' + tipsHTML + "</ul>" +
      "</div>" +

      // Enemy warning
      '<div class="section warning-box">' +
        '<h3>⚠️ Watch out for ' + enemy.name + '</h3>' +
        '<p>' + (enemy.vsTip || "Play carefully and don't underestimate them.") + "</p>" +
      "</div>";
  }

  // ═════════════════════════════════════════════════════════════════════════
  //  RENDER — COUNTER FINDER TAB
  // ═════════════════════════════════════════════════════════════════════════
  function renderCounterList() {
    renderChips(els.filtersCounter, state.roleCounter, role => {
      state.roleCounter = role;
      state.counterDetailId = null;
      renderCounterList();
    });

    if (state.counterDetailId) {
      renderCounterDetail(byId[state.counterDetailId]);
      return;
    }

    const list = filterHeroes(state.searchCounter, state.roleCounter);
    els.counterContent.innerHTML = makeGrid(list);
    bindGrid(els.counterContent, hero => {
      state.counterDetailId = hero.id;
      renderCounterList();
    });
  }

  function renderCounterDetail(h) {
    const counters = (h.counters || []).map(id => byId[id]).filter(Boolean);

    let countersHTML = "";
    counters.forEach(c => {
      countersHTML +=
        '<div class="counter ' + roleClass(c.role) + '">' +
          '<button class="counter-head">' +
            '<span class="hero-emoji">' + c.emoji + "</span>" +
            '<span class="hero-name">' + c.name + "</span>" +
            '<span class="hero-role">' + c.role + "</span>" +
            '<span class="chev">▼</span>' +
          "</button>" +
          '<div class="counter-body hidden">' +
            '<h4>' + c.name + "'s build</h4>" +
            buildBlockHTML(c.build.boots, c.build.items, c.build.note) +
          "</div>" +
        "</div>";
    });

    els.counterContent.innerHTML =
      '<button class="back" id="counter-back">← All heroes</button>' +
      '<div class="detail-header ' + roleClass(h.role) + '">' +
        '<span class="hero-emoji big">' + h.emoji + "</span>" +
        '<div><h2>Enemy: ' + h.name + "</h2>" +
          '<span class="hero-role">' + h.role + " · " + (h.difficulty || "Medium") + " to play</span></div>" +
      "</div>" +
      '<div class="vs-tip"><strong>How to beat ' + h.name + ":</strong> " + h.vsTip + "</div>" +
      '<h3>✅ Pick one of these to counter them</h3>' +
      countersHTML +
      '<details class="own-build"><summary>📦 ' + h.name + "'s own build</summary>" +
        buildBlockHTML(h.build.boots, h.build.items, h.build.note) +
      "</details>";

    document.getElementById("counter-back").addEventListener("click", () => {
      state.counterDetailId = null;
      renderCounterList();
    });

    els.counterContent.querySelectorAll(".counter-head").forEach(btn => {
      const body = btn.nextElementSibling;
      const wrap = btn.parentElement;
      btn.addEventListener("click", () => {
        body.classList.toggle("hidden");
        wrap.classList.toggle("open");
      });
    });
  }

  // ═════════════════════════════════════════════════════════════════════════
  //  TAB SWITCHING
  // ═════════════════════════════════════════════════════════════════════════
  function switchTab(tab) {
    state.tab = tab;
    els.tabMatchup.classList.toggle("active", tab === "matchup");
    els.tabCounter.classList.toggle("active", tab === "counter");
    els.viewMatchup.hidden = tab !== "matchup";
    els.viewCounter.hidden = tab !== "counter";
    if (tab === "counter") renderCounterList();
  }

  // ── Wire up events ────────────────────────────────────────────────────────
  els.tabMatchup.addEventListener("click", () => switchTab("matchup"));
  els.tabCounter.addEventListener("click", () => switchTab("counter"));

  els.btnBack1.addEventListener("click", () => showStep(1));
  els.btnBack2.addEventListener("click", () => {
    showStep(1);
    renderStep1();
  });

  els.searchMe.addEventListener("input", e => { state.searchMe = e.target.value; renderStep1(); });
  els.searchEnemy.addEventListener("input", e => { state.searchEnemy = e.target.value; renderStep2(); });
  els.searchCounter.addEventListener("input", e => {
    state.searchCounter = e.target.value;
    state.counterDetailId = null;
    renderCounterList();
  });

  // ── Init ──────────────────────────────────────────────────────────────────
  if (DATA.updated) {
    els.updated.textContent = "📅 Data updated: " + DATA.updated;
  }

  renderStep1();
  showStep(1);
  switchTab("matchup");

})();
