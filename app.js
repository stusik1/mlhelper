/* ML Counter Helper — app logic (plain JavaScript, no frameworks)
 *
 * Beginner notes:
 *  - The hero data lives in data.js (loaded before this file).
 *  - This file draws two screens: the hero LIST and a hero DETAIL page.
 *  - When you tap an enemy hero, we show who counters them + each counter's build.
 */

(function () {
  "use strict";

  const DATA = window.MLBB_DATA || { heroes: [] };

  // Sort heroes alphabetically and make a quick lookup table by id.
  const heroes = DATA.heroes.slice().sort((a, b) => a.name.localeCompare(b.name));
  const byId = {};
  heroes.forEach(function (h) { byId[h.id] = h; });

  const ROLES = ["All", "Marksman", "Assassin", "Mage", "Fighter", "Tank", "Support"];

  const els = {
    search: document.getElementById("search"),
    filters: document.getElementById("filters"),
    content: document.getElementById("content"),
    updated: document.getElementById("updated"),
  };

  // Screen state. selectedId = the enemy hero we're viewing (null = list view).
  const state = { search: "", role: "All", selectedId: null };

  /* ---------- small helpers ---------- */

  function roleClass(role) {
    return "role-" + role.toLowerCase();
  }

  // Builds the little "items" row + note for a hero.
  function buildBlockHTML(h) {
    const items = [h.build.boots].concat(h.build.items);
    const itemTags = items.map(function (it) {
      return '<span class="item">' + it + "</span>";
    }).join("");
    return (
      '<div class="build">' +
        '<div class="build-items">' + itemTags + "</div>" +
        '<p class="build-note">💡 ' + h.build.note + "</p>" +
      "</div>"
    );
  }

  /* ---------- list view ---------- */

  function renderFilters() {
    els.filters.innerHTML = "";
    ROLES.forEach(function (role) {
      const chip = document.createElement("button");
      chip.className = "chip" + (state.role === role ? " active" : "");
      chip.textContent = role;
      chip.addEventListener("click", function () {
        state.role = role;
        render();
      });
      els.filters.appendChild(chip);
    });
  }

  function renderList() {
    const q = state.search.trim().toLowerCase();
    const list = heroes.filter(function (h) {
      const matchRole = state.role === "All" || h.role === state.role;
      const matchText = !q || h.name.toLowerCase().indexOf(q) !== -1;
      return matchRole && matchText;
    });

    els.content.innerHTML = "";

    if (list.length === 0) {
      els.content.innerHTML =
        '<p class="empty">No hero found for “' + state.search + '”.<br>Try another name.</p>';
      return;
    }

    const grid = document.createElement("div");
    grid.className = "grid";
    list.forEach(function (h) {
      const card = document.createElement("button");
      card.className = "hero-card " + roleClass(h.role);
      card.innerHTML =
        '<span class="hero-emoji">' + h.emoji + "</span>" +
        '<span class="hero-name">' + h.name + "</span>" +
        '<span class="hero-role">' + h.role + "</span>";
      card.addEventListener("click", function () { selectHero(h.id); });
      grid.appendChild(card);
    });
    els.content.appendChild(grid);
  }

  /* ---------- detail view ---------- */

  function renderDetail(h) {
    els.content.innerHTML = "";

    const back = document.createElement("button");
    back.className = "back";
    back.textContent = "← All heroes";
    back.addEventListener("click", function () {
      state.selectedId = null;
      render();
    });
    els.content.appendChild(back);

    const header = document.createElement("div");
    header.className = "detail-header " + roleClass(h.role);
    header.innerHTML =
      '<span class="hero-emoji big">' + h.emoji + "</span>" +
      "<div>" +
        "<h2>Enemy: " + h.name + "</h2>" +
        '<span class="hero-role">' + h.role + " · " + h.difficulty + " to play</span>" +
      "</div>";
    els.content.appendChild(header);

    const tip = document.createElement("div");
    tip.className = "vs-tip";
    tip.innerHTML = "<strong>How to beat " + h.name + ":</strong> " + h.vsTip;
    els.content.appendChild(tip);

    const cTitle = document.createElement("h3");
    cTitle.textContent = "✅ Pick one of these to counter them";
    els.content.appendChild(cTitle);

    const counters = (h.counters || []).map(function (id) { return byId[id]; })
                                       .filter(Boolean);

    counters.forEach(function (c) {
      const wrap = document.createElement("div");
      wrap.className = "counter " + roleClass(c.role);

      const head = document.createElement("button");
      head.className = "counter-head";
      head.innerHTML =
        '<span class="hero-emoji">' + c.emoji + "</span>" +
        '<span class="hero-name">' + c.name + "</span>" +
        '<span class="hero-role">' + c.role + "</span>" +
        '<span class="chev">▼</span>';

      const body = document.createElement("div");
      body.className = "counter-body hidden";
      body.innerHTML = "<h4>" + c.name + "’s recommended build</h4>" + buildBlockHTML(c);

      head.addEventListener("click", function () {
        body.classList.toggle("hidden");
        wrap.classList.toggle("open");
      });

      wrap.appendChild(head);
      wrap.appendChild(body);
      els.content.appendChild(wrap);
    });

    // Also show the enemy hero's own build (collapsed by default).
    const own = document.createElement("details");
    own.className = "own-build";
    own.innerHTML = "<summary>📦 " + h.name + "’s own build (if YOU play them)</summary>" +
                    buildBlockHTML(h);
    els.content.appendChild(own);
  }

  /* ---------- glue ---------- */

  function selectHero(id) {
    state.selectedId = id;
    window.scrollTo(0, 0);
    render();
  }

  function render() {
    renderFilters();
    if (state.selectedId && byId[state.selectedId]) {
      renderDetail(byId[state.selectedId]);
    } else {
      renderList();
    }
  }

  els.search.addEventListener("input", function (e) {
    state.search = e.target.value;
    state.selectedId = null; // go back to the list while typing
    render();
  });

  if (DATA.updated) {
    els.updated.textContent = "📅 Data updated: " + DATA.updated;
  }

  render();
})();
