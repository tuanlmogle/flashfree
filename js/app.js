(function () {
  "use strict";

  var KEY = "flashfree.v1";
  var LEVELS = ["A1", "A2", "B1", "B2", "C1"];
  var POS = {
    noun: "danh từ",
    verb: "động từ",
    adjective: "tính từ",
    adverb: "trạng từ",
    conjunction: "liên từ",
    interjection: "thán từ",
  };

  var vocab = [];
  var byId = {};
  var state = loadState();
  var sessionQueue = [];
  var queueKey = "";
  var flipped = false;
  var reviewNonce = 0;

  var views = {
    decks: document.getElementById("view-decks"),
    study: document.getElementById("view-study"),
    stats: document.getElementById("view-stats"),
    credits: document.getElementById("view-credits"),
  };

  function freshState() {
    return { levels: ["B1", "B2"], status: {}, reviewed: 0, currentId: null };
  }

  function loadState() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return freshState();
      var data = JSON.parse(raw);
      if (!data || !Array.isArray(data.levels)) return freshState();
      return {
        levels: data.levels.filter(function (level) { return LEVELS.indexOf(level) !== -1; }),
        status: data.status && typeof data.status === "object" ? data.status : {},
        reviewed: Number.isFinite(data.reviewed) ? data.reviewed : 0,
        currentId: typeof data.currentId === "string" ? data.currentId : null,
      };
    } catch (err) {
      return freshState();
    }
  }

  function save() {
    localStorage.setItem(KEY, JSON.stringify(state));
  }

  function shuffle(list) {
    for (var i = list.length - 1; i > 0; i -= 1) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = list[i];
      list[i] = list[j];
      list[j] = tmp;
    }
    return list;
  }

  function selectedCards() {
    return vocab.filter(function (card) { return state.levels.indexOf(card.level) !== -1; });
  }

  function tally(cards) {
    var known = 0;
    var unknown = 0;
    var unseen = 0;
    cards.forEach(function (card) {
      var mark = state.status[card.id];
      if (mark === "known") known += 1;
      else if (mark === "unknown") unknown += 1;
      else unseen += 1;
    });
    return { known: known, unknown: unknown, unseen: unseen, total: cards.length };
  }

  function currentView() {
    var hash = (location.hash || "#decks").replace("#", "");
    return views[hash] ? hash : "decks";
  }

  function show(name) {
    Object.keys(views).forEach(function (key) {
      views[key].hidden = key !== name;
    });
    document.querySelectorAll("[data-nav]").forEach(function (link) {
      if (link.getAttribute("data-nav") === name) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  }

  function renderDecks() {
    var host = document.getElementById("level-chips");
    host.replaceChildren();
    LEVELS.forEach(function (level) {
      var count = vocab.filter(function (card) { return card.level === level; }).length;
      if (!count) return;
      var button = document.createElement("button");
      button.type = "button";
      button.className = "chip";
      button.dataset.level = level;
      button.setAttribute("aria-pressed", state.levels.indexOf(level) !== -1 ? "true" : "false");
      button.append(level);
      var note = document.createElement("span");
      note.textContent = String(count);
      button.append(note);
      button.addEventListener("click", function () {
        var index = state.levels.indexOf(level);
        if (index === -1) state.levels.push(level);
        else state.levels.splice(index, 1);
        state.levels.sort(function (a, b) { return LEVELS.indexOf(a) - LEVELS.indexOf(b); });
        queueKey = "";
        save();
        renderDecks();
      });
      host.append(button);
    });
    var cards = selectedCards();
    document.getElementById("deck-count").textContent = cards.length
      ? cards.length + " từ trong bộ đã chọn"
      : "Chọn ít nhất một trình độ";
    document.getElementById("start").disabled = cards.length === 0;
  }

  function rebuildQueue(includeKnown) {
    var chosen = selectedCards();
    var unseen = [];
    var unknown = [];
    var known = [];
    chosen.forEach(function (card) {
      var mark = state.status[card.id];
      if (mark === "known") known.push(card.id);
      else if (mark === "unknown") unknown.push(card.id);
      else unseen.push(card.id);
    });
    if (includeKnown) {
      sessionQueue = shuffle(known.concat(unknown, unseen));
    } else {
      shuffle(unseen);
      shuffle(unknown);
      sessionQueue = unseen.concat(unknown);
    }
    if (!includeKnown && state.currentId && sessionQueue.indexOf(state.currentId) !== -1) {
      sessionQueue = [state.currentId].concat(sessionQueue.filter(function (id) {
        return id !== state.currentId;
      }));
    } else {
      state.currentId = sessionQueue[0] || null;
    }
  }

  function ensureQueue() {
    var includeKnown = reviewNonce > 0;
    var key = state.levels.slice().sort().join(",") + ":" + (includeKnown ? "all" + reviewNonce : "learn");
    if (key === queueKey) return;
    queueKey = key;
    rebuildQueue(includeKnown);
  }

  function setText(id, value) {
    document.getElementById(id).textContent = value || "";
  }

  function renderCard() {
    var card = byId[state.currentId];
    var done = document.getElementById("study-done");
    var board = document.getElementById("study-card");
    if (!card) {
      var empty = selectedCards().length === 0;
      done.hidden = false;
      board.hidden = true;
      done.querySelector("h2").textContent = empty ? "Chưa có bộ từ" : "Hết bộ rồi";
      done.querySelector("p").textContent = empty
        ? "Hãy chọn ít nhất một trình độ."
        : "Mọi từ trong bộ đang chọn đều được đánh dấu là đã biết.";
      document.getElementById("review-all").hidden = empty;
      setText("study-meta", empty ? "FlashFree · chưa chọn bộ" : "FlashFree · không còn từ trong bộ này");
      return;
    }
    document.getElementById("review-all").hidden = false;
    done.hidden = true;
    board.hidden = false;
    flipped = false;
    document.getElementById("card-inner").classList.remove("is-flipped");
    document.getElementById("swipe").style.transform = "";
    setText("stamp-known", "Biết");
    document.getElementById("stamp-known").style.opacity = "0";
    document.getElementById("stamp-unknown").style.opacity = "0";
    var counts = tally(selectedCards());
    setText("study-meta", "FlashFree · còn " + sessionQueue.length + " · đã biết " + counts.known);
    setText("card-level", card.level);
    setText("card-pos", POS[card.pos] || card.pos);
    setText("card-word", card.en);
    setText("card-ipa", card.ipa);
    setText("card-vi", card.vi);
    setText("card-example", card.example);
    setText("card-example-vi", card.exampleVi);
    document.getElementById("card").setAttribute("aria-pressed", "false");
  }

  function renderStudy() {
    ensureQueue();
    renderCard();
  }

  function answer(kind) {
    if (!state.currentId || !byId[state.currentId]) return;
    var id = state.currentId;
    state.status[id] = kind;
    state.reviewed += 1;
    sessionQueue = sessionQueue.filter(function (item) { return item !== id; });
    if (kind === "unknown") sessionQueue.push(id);
    state.currentId = sessionQueue[0] || null;
    save();
    renderCard();
  }

  function renderStats() {
    var cards = selectedCards();
    var counts = tally(cards);
    var label = state.levels.length ? state.levels.join(", ") : "chưa chọn bộ";
    setText("stat-scope", "Bộ đang chọn: " + label + " · " + counts.total + " từ");
    setText("stat-known", String(counts.known));
    setText("stat-unknown", String(counts.unknown));
    setText("stat-unseen", String(counts.unseen));
    setText("stat-reviewed", String(state.reviewed));
    var list = document.getElementById("stat-levels");
    list.replaceChildren();
    LEVELS.forEach(function (level) {
      var group = vocab.filter(function (card) { return card.level === level; });
      if (!group.length) return;
      var row = tally(group);
      var item = document.createElement("li");
      var name = document.createElement("span");
      name.textContent = level;
      var detail = document.createElement("span");
      detail.textContent = row.known + "/" + row.total + " đã biết";
      item.append(name, detail);
      list.append(item);
    });
  }

  function render() {
    var name = currentView();
    show(name);
    if (name === "decks") renderDecks();
    if (name === "study") renderStudy();
    if (name === "stats") renderStats();
  }

  function bindStudy() {
    var scene = document.getElementById("card");
    var swipe = document.getElementById("swipe");
    var startX = 0;
    var startY = 0;
    var dx = 0;
    var active = false;
    var axis = "";

    function flip() {
      flipped = !flipped;
      document.getElementById("card-inner").classList.toggle("is-flipped", flipped);
      scene.setAttribute("aria-pressed", flipped ? "true" : "false");
    }

    function resetDrag() {
      active = false;
      axis = "";
      dx = 0;
      swipe.style.transform = "";
      document.getElementById("stamp-known").style.opacity = "0";
      document.getElementById("stamp-unknown").style.opacity = "0";
    }

    scene.addEventListener("pointerdown", function (event) {
      if (!state.currentId) return;
      active = true;
      axis = "";
      dx = 0;
      startX = event.clientX;
      startY = event.clientY;
      scene.setPointerCapture(event.pointerId);
    });

    scene.addEventListener("pointermove", function (event) {
      if (!active) return;
      var moveX = event.clientX - startX;
      var moveY = event.clientY - startY;
      if (!axis) {
        if (Math.abs(moveX) < 8 && Math.abs(moveY) < 8) return;
        axis = Math.abs(moveX) > Math.abs(moveY) ? "x" : "y";
      }
      if (axis !== "x") return;
      dx = moveX;
      swipe.style.transform = "translateX(" + dx + "px) rotate(" + dx / 22 + "deg)";
      document.getElementById("stamp-known").style.opacity = String(Math.min(1, Math.max(0, dx / 110)));
      document.getElementById("stamp-unknown").style.opacity = String(Math.min(1, Math.max(0, -dx / 110)));
    });

    function finish() {
      if (!active) return;
      var moved = dx;
      var horizontal = axis === "x";
      var tap = axis === "";
      resetDrag();
      if (horizontal && moved >= 88) answer("known");
      else if (horizontal && moved <= -88) answer("unknown");
      else if (tap) flip();
    }

    scene.addEventListener("pointerup", finish);
    scene.addEventListener("pointercancel", function () { resetDrag(); });
    scene.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        flip();
      }
    });

    document.getElementById("btn-known").addEventListener("click", function () { answer("known"); });
    document.getElementById("btn-unknown").addEventListener("click", function () { answer("unknown"); });
    document.getElementById("review-all").addEventListener("click", function () {
      reviewNonce += 1;
      queueKey = "";
      renderStudy();
    });

    document.addEventListener("keydown", function (event) {
      if (currentView() !== "study") return;
      if (event.target && event.target.closest && event.target.closest("input, textarea")) return;
      if (event.key === "ArrowRight") answer("known");
      if (event.key === "ArrowLeft") answer("unknown");
    });
  }

  function bindChrome() {
    document.getElementById("start").addEventListener("click", function () {
      reviewNonce = 0;
      queueKey = "";
      if ((location.hash || "#decks") === "#study") render();
      else location.hash = "#study";
    });
    document.getElementById("reset").addEventListener("click", function () {
      document.getElementById("reset-confirm").hidden = false;
    });
    document.getElementById("reset-cancel").addEventListener("click", function () {
      document.getElementById("reset-confirm").hidden = true;
    });
    document.getElementById("reset-yes").addEventListener("click", function () {
      var levels = state.levels.slice();
      state = freshState();
      state.levels = levels;
      reviewNonce = 0;
      queueKey = "";
      save();
      document.getElementById("reset-confirm").hidden = true;
      render();
    });
    window.addEventListener("hashchange", render);
  }

  bindStudy();
  bindChrome();

  fetch(new URL("data/vocab.json", document.baseURI))
    .then(function (response) {
      if (!response.ok) throw new Error(String(response.status));
      return response.json();
    })
    .then(function (cards) {
      if (!Array.isArray(cards)) throw new Error("vocab");
      vocab = cards;
      cards.forEach(function (card) { byId[card.id] = card; });
      render();
    })
    .catch(function () {
      document.getElementById("load-error").hidden = false;
      Object.keys(views).forEach(function (key) { views[key].hidden = true; });
    });
})();
