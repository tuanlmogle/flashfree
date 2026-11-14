/* FlashFree — SM-2 flashcards. Biết = grade 4, Chưa biết = grade 1.
   A failed card is shown once more in the same session; the stored grade stays the first answer. */

const LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];
const LEVEL_NAME = {
  A1: "Mới bắt đầu",
  A2: "Cơ bản",
  B1: "Trung cấp",
  B2: "Trung cấp cao",
  C1: "Nâng cao",
  C2: "Thành thạo",
};
const POS_VI = {
  noun: "danh từ",
  verb: "động từ",
  adj: "tính từ",
  adv: "trạng từ",
  pron: "đại từ",
  prep: "giới từ",
  det: "hạn định từ",
  conj: "liên từ",
  num: "số từ",
  intj: "thán từ",
  particle: "tiểu từ",
  phrase: "cụm từ",
  contraction: "dạng rút gọn",
};
const WEEK = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
const KEY = "latu-state-v1";
const NEW_STEPS = [5, 10, 15, 20, 25, 30, 35, 40];
const MEDALS = [
  { id: "streak-3", kind: "streak", n: 3, name: "Ba ngày", mark: "🌱" },
  { id: "streak-7", kind: "streak", n: 7, name: "Một tuần", mark: "🍀" },
  { id: "streak-14", kind: "streak", n: 14, name: "Hai tuần", mark: "🌙" },
  { id: "streak-30", kind: "streak", n: 30, name: "Một tháng", mark: "🌻" },
  { id: "streak-60", kind: "streak", n: 60, name: "Hai tháng", mark: "🍁" },
  { id: "streak-100", kind: "streak", n: 100, name: "Trăm ngày", mark: "⭐" },
  { id: "streak-200", kind: "streak", n: 200, name: "Hai trăm", mark: "🏔️" },
  { id: "streak-365", kind: "streak", n: 365, name: "Một năm", mark: "☀️" },
  { id: "words-50", kind: "words", n: 50, name: "50 từ", mark: "✏️" },
  { id: "words-100", kind: "words", n: 100, name: "100 từ", mark: "📘" },
  { id: "words-250", kind: "words", n: 250, name: "250 từ", mark: "📗" },
  { id: "words-500", kind: "words", n: 500, name: "500 từ", mark: "📚" },
  { id: "words-1000", kind: "words", n: 1000, name: "1000 từ", mark: "🎓" },
  { id: "words-2500", kind: "words", n: 2500, name: "2500 từ", mark: "🏆" },
];

const main = document.getElementById("main");
const topmeta = document.getElementById("topmeta");
let DATA = null;
let ICONS = {};
let INDEX = new Map();
let STATE = null;
let view = "study";
let returnView = "decks";
let editingId = "";
let session = null;
let busy = false;
let drag = null;
let suppressClick = false;
let toastTimer = 0;
const toastQueue = [];
let toastOn = false;
let lastAuto = { stamp: "", at: 0 };

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

function todayISO() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function addDays(iso, amount) {
  const [year, month, day] = iso.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  date.setUTCDate(date.getUTCDate() + amount);
  return date.toISOString().slice(0, 10);
}

function hash(text) {
  let value = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    value = Math.imul(value ^ text.charCodeAt(i), 16777619);
  }
  return value >>> 0;
}

function defaultState() {
  return {
    settings: { newPerDay: 10, levels: ["B1", "B2"], topics: [], autoSpeak: true, ownDeck: true },
    cards: {},
    introduced: {},
    log: {},
    own: [],
    xp: 0,
    medals: [],
    freeze: { bank: 0, progress: 0, streak: 0, last: null },
  };
}

function clampInt(value, min, max) {
  const number = Number(value);
  if (!Number.isFinite(number)) return min;
  return Math.min(max, Math.max(min, Math.round(number)));
}

function legacyStreak(log) {
  const reviewed = (day) => !!(log[day] && log[day].reviews > 0);
  let day = todayISO();
  if (!reviewed(day)) day = addDays(day, -1);
  let count = 0;
  let last = null;
  while (reviewed(day) && count < 5000) {
    if (!last) last = day;
    count += 1;
    day = addDays(day, -1);
  }
  return { count, last };
}

function normalizeFreeze(raw, log) {
  const saved = raw && typeof raw === "object" && ("streak" in raw || "last" in raw || "bank" in raw);
  if (!saved) {
    const legacy = legacyStreak(log);
    return {
      bank: Math.min(2, Math.floor(legacy.count / 7)),
      progress: legacy.count % 7,
      streak: legacy.count,
      last: legacy.last,
    };
  }
  const last = typeof raw.last === "string" && /^\d{4}-\d{2}-\d{2}$/.test(raw.last) ? raw.last : null;
  return {
    bank: clampInt(raw.bank, 0, 2),
    progress: clampInt(raw.progress, 0, 6),
    streak: Math.max(0, Number(raw.streak) || 0),
    last,
  };
}

function backfillXp(log) {
  let xp = 0;
  for (const row of Object.values(log)) xp += (row.reviews || 0) + 2 * (row.correct || 0);
  return xp;
}

function loadState() {
  const base = defaultState();
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return base;
    const parsed = JSON.parse(raw);
    const settings = { ...base.settings, ...(parsed.settings || {}) };
    settings.levels = (settings.levels || []).filter((level) => LEVELS.includes(level));
    settings.topics = Array.isArray(settings.topics) ? settings.topics : [];
    if (!NEW_STEPS.includes(Number(settings.newPerDay))) settings.newPerDay = 10;
    settings.autoSpeak = settings.autoSpeak !== false;
    settings.ownDeck = settings.ownDeck !== false;
    const log = parsed.log && typeof parsed.log === "object" ? parsed.log : {};
    const knownMedals = new Set(MEDALS.map((medal) => medal.id));
    return {
      settings,
      cards: parsed.cards && typeof parsed.cards === "object" ? parsed.cards : {},
      introduced: parsed.introduced && typeof parsed.introduced === "object" ? parsed.introduced : {},
      log,
      own: cleanOwn(parsed.own),
      xp: Number.isFinite(Number(parsed.xp)) ? Math.max(0, Number(parsed.xp)) : backfillXp(log),
      medals: Array.isArray(parsed.medals) ? parsed.medals.filter((id) => knownMedals.has(id)) : [],
      freeze: normalizeFreeze(parsed.freeze, log),
    };
  } catch {
    return base;
  }
}

function save() {
  const cutoff = addDays(todayISO(), -120);
  for (const day of Object.keys(STATE.log)) {
    if (day < cutoff) delete STATE.log[day];
  }
  localStorage.setItem(KEY, JSON.stringify(STATE));
}

function newOwnId() {
  return `own-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

function cleanIcon(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  if (/[<>&"'A-Za-z0-9]/.test(text)) return null;
  if ([...text].length > 8) return null;
  return text;
}

function cleanOwn(list) {
  if (!Array.isArray(list)) return [];
  const out = [];
  const ids = new Set();
  for (const item of list) {
    if (!item || typeof item !== "object") continue;
    const word = String(item.word || "").trim().slice(0, 80);
    const meaning = String(item.meaning || "").trim().slice(0, 240);
    if (!word || !meaning) continue;
    let id = String(item.id || "");
    if (!/^own-[a-z0-9-]+$/i.test(id) || ids.has(id)) id = newOwnId();
    ids.add(id);
    const icon = cleanIcon(item.icon);
    out.push({
      id,
      word,
      meaning,
      pos: POS_VI[item.pos] ? item.pos : "",
      example: String(item.example || "").trim().slice(0, 300),
      icon: icon || "",
    });
  }
  return out;
}

function ownAsCards() {
  return (STATE.own || []).map((item) => ({
    id: item.id,
    word: item.word,
    pos: item.pos || "",
    level: "A1",
    meaning: item.meaning,
    example: item.example || "",
    own: true,
    icon: item.icon || "",
    topics: [],
  }));
}

function pool() {
  if (!STATE || STATE.settings.ownDeck === false) return DATA.cards;
  return DATA.cards.concat(ownAsCards());
}

function reindex() {
  INDEX = new Map(DATA.cards.map((card) => [card.id, card]));
  for (const card of ownAsCards()) INDEX.set(card.id, card);
}

function reconcileFreezes() {
  const freeze = STATE.freeze;
  if (!freeze) return false;
  const today = todayISO();
  if (!freeze.last || freeze.last >= today) return false;
  const gap = [];
  let day = addDays(freeze.last, 1);
  while (day < today) {
    gap.push(day);
    day = addDays(day, 1);
  }
  if (!gap.length) return false;
  if (gap.length <= freeze.bank) {
    for (const missed of gap) {
      const row = STATE.log[missed] || { reviews: 0, correct: 0, added: 0 };
      row.frozen = true;
      STATE.log[missed] = row;
    }
    freeze.bank -= gap.length;
    freeze.streak += gap.length;
    freeze.last = gap[gap.length - 1];
    return true;
  }
  freeze.streak = 0;
  freeze.progress = 0;
  freeze.last = null;
  return true;
}

function noteStudyDay() {
  reconcileFreezes();
  const today = todayISO();
  const freeze = STATE.freeze;
  if (freeze.last === today) return false;
  freeze.streak = (freeze.last ? freeze.streak : 0) + 1;
  freeze.last = today;
  freeze.progress += 1;
  if (freeze.progress < 7) return false;
  freeze.progress = 0;
  if (freeze.bank >= 2) return false;
  freeze.bank += 1;
  return true;
}

function learnedCount() {
  let count = 0;
  for (const state of Object.values(STATE.cards)) {
    if (state && state.reps >= 1) count += 1;
  }
  return count;
}

function checkMedals() {
  const have = new Set(STATE.medals || []);
  const streak = streakCount();
  const learned = learnedCount();
  const fresh = [];
  for (const medal of MEDALS) {
    if (have.has(medal.id)) continue;
    if ((medal.kind === "streak" ? streak : learned) >= medal.n) fresh.push(medal);
  }
  if (fresh.length) STATE.medals = [...have, ...fresh.map((medal) => medal.id)];
  return fresh;
}

function topicName(id) {
  const found = (DATA.topics || []).find((topic) => topic.id === id);
  return found ? found.name : id;
}

function inDeck(card) {
  if (card.own) return STATE.settings.ownDeck !== false;
  const settings = STATE.settings;
  if (!settings.levels.includes(card.level)) return false;
  if (!settings.topics.length) return true;
  return (card.topics || []).some((id) => settings.topics.includes(id));
}

function sessionKey() {
  const settings = STATE.settings;
  const topics = settings.topics.length ? settings.topics.slice().sort().join(",") : "*";
  const own = settings.ownDeck === false ? "off" : (STATE.own || []).map((item) => item.id).join(",");
  return `${todayISO()}|${settings.newPerDay}|${settings.levels.join(",")}|${topics}|${own}`;
}

function planToday(today) {
  const due = [];
  const unseen = [];
  for (const card of pool()) {
    if (!inDeck(card)) continue;
    const state = STATE.cards[card.id];
    if (!state) unseen.push(card);
    else if (state.due <= today && state.last !== today) due.push(card);
  }
  due.sort((a, b) => {
    const left = STATE.cards[a.id].due;
    const right = STATE.cards[b.id].due;
    if (left !== right) return left < right ? -1 : 1;
    return hash(a.id) - hash(b.id);
  });
  unseen.sort((a, b) => {
    if (!!a.own !== !!b.own) return a.own ? -1 : 1;
    return LEVELS.indexOf(a.level) - LEVELS.indexOf(b.level) || hash(a.id) - hash(b.id);
  });

  const kept = (STATE.introduced[today] || []).filter((id) => {
    const card = INDEX.get(id);
    if (!card || !inDeck(card)) return false;
    const state = STATE.cards[id];
    return !state || state.last === today;
  });
  const keptSet = new Set(kept);
  const keptOwn = kept.filter((id) => String(id).startsWith("own-"));
  const keptBuilt = kept.filter((id) => !String(id).startsWith("own-"));
  let room = Math.max(0, STATE.settings.newPerDay - keptBuilt.length);
  const addedOwn = [];
  const addedBuilt = [];
  for (const card of unseen) {
    if (keptSet.has(card.id)) continue;
    if (card.own) {
      addedOwn.push(card.id);
      continue;
    }
    if (room <= 0) continue;
    addedBuilt.push(card.id);
    room -= 1;
  }
  STATE.introduced = { [today]: keptOwn.concat(addedOwn, keptBuilt, addedBuilt) };
  const fresh = STATE.introduced[today]
    .filter((id) => !STATE.cards[id])
    .map((id) => INDEX.get(id))
    .filter(Boolean);
  save();
  return { due, fresh };
}

function ensureSession() {
  const key = sessionKey();
  if (session && session.key === key) return;
  const today = todayISO();
  const plan = planToday(today);
  const queue = plan.due.concat(plan.fresh).map((card) => ({ id: card.id, retry: false }));
  session = { key, queue, index: 0, total: queue.length, done: 0 };
}

function currentItem() {
  return session ? session.queue[session.index] || null : null;
}

function currentCard() {
  const item = currentItem();
  return item ? INDEX.get(item.id) : null;
}

function applySm2(id, quality) {
  const today = todayISO();
  const prev = STATE.cards[id] || { ef: 2.5, reps: 0, interval: 0, lapses: 0 };
  let ef = prev.ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
  if (ef < 1.3) ef = 1.3;
  let reps = prev.reps;
  let interval = prev.interval || 0;
  let lapses = prev.lapses || 0;
  if (quality < 3) {
    reps = 0;
    interval = 1;
    lapses += 1;
  } else if (reps === 0) {
    interval = 1;
    reps += 1;
  } else if (reps === 1) {
    interval = 6;
    reps += 1;
  } else {
    interval = Math.max(1, Math.round(interval * ef));
    reps += 1;
  }
  STATE.cards[id] = {
    ef: Math.round(ef * 100) / 100,
    reps,
    interval,
    lapses,
    due: addDays(today, interval),
    last: today,
  };
}

function bumpLog(know) {
  const today = todayISO();
  const row = STATE.log[today] || { reviews: 0, correct: 0, added: 0 };
  row.reviews += 1;
  if (know) row.correct += 1;
  STATE.log[today] = row;
}

function bumpAdded() {
  const today = todayISO();
  const row = STATE.log[today] || { reviews: 0, correct: 0, added: 0 };
  row.added = (row.added || 0) + 1;
  STATE.log[today] = row;
}

function studied(day) {
  return (STATE.log[day] && STATE.log[day].reviews > 0) || false;
}

function streakCount() {
  reconcileFreezes();
  const today = todayISO();
  const last = STATE.freeze.last;
  if (!last) return 0;
  if (last === today || last === addDays(today, -1)) return STATE.freeze.streak;
  return 0;
}

function newRemaining() {
  const today = todayISO();
  const ids = STATE.introduced[today] || [];
  if (!ids.length) return STATE.settings.newPerDay;
  return ids.filter((id) => {
    const card = INDEX.get(id);
    return card && inDeck(card) && !STATE.cards[id];
  }).length;
}

function totals() {
  let learned = 0;
  let reviews = 0;
  let correct = 0;
  for (const state of Object.values(STATE.cards)) {
    if (state.reps >= 1) learned += 1;
  }
  for (const row of Object.values(STATE.log)) {
    reviews += row.reviews || 0;
    correct += row.correct || 0;
  }
  let due = 0;
  const today = todayISO();
  for (const card of pool()) {
    if (!inDeck(card)) continue;
    const state = STATE.cards[card.id];
    if (state && state.due <= today && state.last !== today) due += 1;
  }
  const todayRow = STATE.log[today] || { reviews: 0, correct: 0 };
  return { learned, reviews, correct, due, todayRow, xp: STATE.xp || 0 };
}

function speak(text, quiet) {
  const synth = window.speechSynthesis;
  if (!synth || !text) {
    if (!quiet) toast("Trình duyệt này không đọc được tiếng Anh.");
    return false;
  }
  try {
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = "en-US";
    utter.rate = 0.92;
    const voices = synth.getVoices();
    const voice = voices.find((item) => item.lang === "en-US")
      || voices.find((item) => /^en([-_]|$)/i.test(item.lang || ""));
    if (voice) utter.voice = voice;
    synth.cancel();
    synth.speak(utter);
    synth.resume();
    return true;
  } catch {
    if (!quiet) toast("Trình duyệt này không đọc được tiếng Anh.");
    return false;
  }
}

function gestureActive() {
  const activation = navigator.userActivation;
  if (!activation || typeof activation.isActive !== "boolean") return true;
  return activation.isActive;
}

function autoSpeak(card, mode) {
  if (!card || STATE.settings.autoSpeak === false) return;
  if (mode === "show" && !gestureActive()) return;
  const stamp = `${card.id}:${session ? session.index : 0}`;
  const now = Date.now();
  if (mode !== "flip" && lastAuto.stamp === stamp && now - lastAuto.at < 1000) return;
  if (speak(card.word, true)) lastAuto = { stamp, at: Date.now() };
}

function toast(message) {
  toastQueue.push({ message, celebrate: false });
  pumpToast();
}

function celebrate(medals) {
  const message = medals.length === 1
    ? `Huy chương mới: ${medals[0].name}`
    : `Mở khoá ${medals.length} huy chương mới`;
  toastQueue.push({ message, celebrate: true });
  pumpToast();
}

function pumpToast() {
  if (toastOn || !toastQueue.length) return;
  toastOn = true;
  const item = toastQueue.shift();
  const node = document.getElementById("toast");
  node.hidden = false;
  node.textContent = item.message;
  node.classList.toggle("celebrate", item.celebrate);
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => {
    node.hidden = true;
    node.classList.remove("celebrate");
    toastOn = false;
    pumpToast();
  }, 2200);
}

function speakerButton() {
  return `<button type="button" class="speak" data-act="speak" aria-label="Nghe phát âm tiếng Anh">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10v4h3.5L12 18V6L7.5 10H4z" fill="currentColor"/><path d="M16 9a4 4 0 0 1 0 6" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
  </button>`;
}

function wordClass(word) {
  if (word.length > 18) return "word xlong";
  if (word.length > 12) return "word long";
  return "word";
}

function memoryIcon(card) {
  if (!card) return "";
  if (card.own) return card.icon || "";
  return ICONS[String(card.word || "").toLowerCase()] || "";
}

function cardFaces(card, item) {
  const pos = card.pos ? (POS_VI[card.pos] || card.pos) : "";
  const retry = item.retry ? `<span class="pill retry">Ôn lại</span>` : "";
  const ipa = card.ipa ? `<p class="ipa">/${esc(card.ipa)}/</p>` : "";
  const also = card.also && card.also.length ? `<p class="also">Cũng viết: ${esc(card.also.join(", "))}</p>` : "";
  const topic = (card.topics || [])[0];
  const topicPill = topic ? `<span class="pill">${esc(topicName(topic))}</span>` : "";
  const meta = card.own ? (pos ? `Của tôi · ${pos}` : "Của tôi") : `${card.level} · ${pos}`;
  const icon = memoryIcon(card);
  const memo = icon ? `<p class="memo" aria-hidden="true">${esc(icon)}</p>` : "";
  let example = `<p class="hint">Chưa có câu ví dụ cho từ này.</p>`;
  if (card.example) {
    const ref = card.tatoeba || {};
    const who = ref.author ? ` · ${esc(ref.author)}` : "";
    const link = ref.id
      ? `<a href="https://tatoeba.org/en/sentences/show/${encodeURIComponent(ref.id)}" target="_blank" rel="noopener">Tatoeba #${esc(ref.id)}</a>${who}`
      : "";
    example = `<div class="example">
      <p class="ex-en">${esc(card.example)}</p>
      ${card.exampleVi ? `<p class="ex-vi">${esc(card.exampleVi)}</p>` : ""}
      ${link ? `<p class="creditline">${link}</p>` : ""}
    </div>`;
  }
  return `<div class="face front">
      <div class="stamps" aria-hidden="true"><span class="stamp miss">Chưa biết</span><span class="stamp know">Biết</span></div>
      ${speakerButton()}
      <div class="pillrow"><span class="pill">${esc(meta)}</span>${topicPill}${retry}</div>
      <div class="wordwrap">
        ${memo}
        <h1 class="${wordClass(card.word)}">${esc(card.word)}</h1>
        ${ipa}
        ${also}
      </div>
      <p class="hint">Chạm để lật</p>
    </div>
    <div class="face back">
      ${speakerButton()}
      <div class="pillrow"><span class="pill">${esc(meta)}</span>${retry}</div>
      <div class="wordwrap">
        <p class="meaning">${esc(card.meaning)}</p>
        ${example}
      </div>
    </div>`;
}

function updateStudyChrome() {
  const remain = session ? session.queue.length - session.index : 0;
  const pct = session && session.total ? Math.min(100, Math.round((session.done / session.total) * 100)) : 0;
  const bar = document.querySelector(".bar > span");
  if (bar) bar.style.width = `${pct}%`;
  const levels = STATE.settings.levels.join(" · ") || "Chưa chọn";
  topmeta.textContent = remain > 0 ? `${levels} · còn ${remain}` : levels;
}

function fillCard() {
  const card = currentCard();
  const item = currentItem();
  const node = document.getElementById("card");
  if (!card || !node) return;
  node.classList.remove("is-flipped");
  node.innerHTML = cardFaces(card, item);
  updateStudyChrome();
  autoSpeak(card, "show");
}

function studyShell() {
  return `<section class="study">
    <div class="bar" aria-hidden="true"><span></span></div>
    <div class="stage"><div class="tilt" id="tilt"><article class="card" id="card"></article></div></div>
    <p class="gesture">Vuốt phải: biết · vuốt trái: chưa biết</p>
    <div class="actions">
      <button type="button" class="missbtn" data-act="miss">Chưa biết</button>
      <button type="button" class="knowbtn" data-act="know">Biết</button>
    </div>
  </section>`;
}

function canStudy() {
  if (STATE.settings.levels.length) return true;
  return STATE.settings.ownDeck !== false && (STATE.own || []).length > 0;
}

function doneHtml() {
  if (!canStudy()) {
    return `<section class="empty">
      <h1>Chưa chọn trình độ</h1>
      <p>Mở Bộ thẻ và chọn ít nhất một mức từ A1 đến C2, hoặc thêm từ của bạn. Lần đầu, B1 và B2 được chọn sẵn.</p>
      <button type="button" class="primary" data-act="goto" data-goto="decks">Chọn bộ thẻ</button>
    </section>`;
  }
  const numbers = totals();
  return `<section class="empty">
    <h1>Hết phần hôm nay</h1>
    <p>Bạn đã ôn ${numbers.todayRow.reviews} lượt. Từ chưa biết sẽ trở lại vào ngày mai. Muốn học thêm, hãy tăng số thẻ mới.</p>
    <button type="button" class="primary" data-act="goto" data-goto="decks">Đổi bộ thẻ hoặc thêm thẻ mới</button>
    <p style="height:8px"></p>
    <button type="button" class="ghost" data-act="goto" data-goto="stats">Xem thống kê</button>
  </section>`;
}

function renderStudy() {
  ensureSession();
  if (!currentItem()) {
    main.innerHTML = doneHtml();
    topmeta.textContent = STATE.settings.levels.join(" · ") || "Chưa chọn";
    return;
  }
  main.innerHTML = studyShell();
  fillCard();
  bindSwipe();
}

function countLevel(level) {
  return DATA.cards.reduce((sum, card) => sum + (card.level === level ? 1 : 0), 0);
}

function countTopic(id) {
  return DATA.cards.reduce((sum, card) => {
    if (!STATE.settings.levels.includes(card.level)) return sum;
    return sum + ((card.topics || []).includes(id) ? 1 : 0);
  }, 0);
}

function ownDeckHtml() {
  const on = STATE.settings.ownDeck !== false;
  const words = STATE.own || [];
  const rows = words.map((item) => `<div class="ownrow">
      <span class="ownemo" aria-hidden="true">${item.icon ? esc(item.icon) : "·"}</span>
      <span class="owntext"><b>${esc(item.word)}</b><small>${esc(item.meaning)}</small></span>
      <button type="button" data-act="edit-word" data-id="${esc(item.id)}">Sửa</button>
      <button type="button" data-act="delete-word" data-id="${esc(item.id)}">Xóa</button>
    </div>`).join("");
  return `<button type="button" class="level ownlevel${on ? " on" : ""}" data-act="own-deck" aria-pressed="${on}">
      <b>Từ của tôi</b><span>${words.length.toLocaleString("vi-VN")} từ · cùng lịch ôn</span>
    </button>
    <p class="note">Bộ này không phụ thuộc trình độ. Tắt nếu bạn chỉ muốn ôn bộ có sẵn. Bấm + ở góc trên để thêm từ.</p>
    ${rows || `<p class="note">Chưa có từ nào.</p>`}`;
}

function posOptions(selected) {
  const blank = `<option value=""${!selected ? " selected" : ""}>— không chọn —</option>`;
  const rest = Object.entries(POS_VI).map(([id, name]) =>
    `<option value="${id}"${selected === id ? " selected" : ""}>${esc(name)}</option>`).join("");
  return blank + rest;
}

function builtinMatches(word) {
  const key = word.trim().toLowerCase();
  if (!key) return [];
  const out = [];
  const seen = new Set();
  for (const card of DATA.cards) {
    if (card.word.toLowerCase() !== key) continue;
    if (seen.has(card.meaning)) continue;
    seen.add(card.meaning);
    out.push(card);
    if (out.length >= 3) break;
  }
  return out;
}

function prefillHtml(word) {
  const matches = builtinMatches(word);
  if (!matches.length) return `<div class="prefill" hidden></div>`;
  const buttons = matches.map((card) =>
    `<button type="button" data-act="prefill" data-meaning="${esc(card.meaning)}">Điền nghĩa: ${esc(card.meaning.slice(0, 72))}</button>`).join("");
  return `<div class="prefill"><p>Từ này có trong bộ sẵn.</p>${buttons}</div>`;
}

function renderForm() {
  const current = (STATE.own || []).find((item) => item.id === editingId) || {
    word: "", meaning: "", pos: "", example: "", icon: "",
  };
  main.innerHTML = `<form class="composer" id="word-form" data-id="${esc(editingId)}">
    <h1>${editingId ? "Sửa từ" : "Thêm từ"}</h1>
    <p>Từ được lưu trong bộ <strong>Từ của tôi</strong> trên máy này và ôn cùng lịch SM-2.</p>
    <label>Từ tiếng Anh<input name="word" required maxlength="80" autocomplete="off" autocapitalize="off" value="${esc(current.word)}"></label>
    ${prefillHtml(current.word)}
    <label>Nghĩa tiếng Việt<textarea name="meaning" required maxlength="240">${esc(current.meaning)}</textarea></label>
    <label>Từ loại<select name="pos">${posOptions(current.pos)}</select></label>
    <label>Câu ví dụ<input name="example" maxlength="300" value="${esc(current.example)}"></label>
    <label>Biểu tượng<input name="icon" maxlength="16" value="${esc(current.icon)}" placeholder="Ví dụ một emoji"></label>
    <button type="submit" class="primary">${editingId ? "Lưu sửa" : "Lưu vào bộ của tôi"}</button>
    <button type="button" class="ghost" data-act="close-form">Huỷ</button>
  </form>`;
  topmeta.textContent = "Từ của tôi";
}

function updatePrefill(form) {
  const box = form.querySelector(".prefill");
  if (!box) return;
  const matches = builtinMatches(form.elements.word.value);
  if (!matches.length) {
    box.hidden = true;
    box.innerHTML = "";
    return;
  }
  box.hidden = false;
  box.innerHTML = `<p>Từ này có trong bộ sẵn.</p>` + matches.map((card) =>
    `<button type="button" data-act="prefill" data-meaning="${esc(card.meaning)}">Điền nghĩa: ${esc(card.meaning.slice(0, 72))}</button>`).join("");
}

function openForm(id) {
  editingId = id || "";
  returnView = view === "form" ? returnView : view;
  view = "form";
  render();
}

function saveOwn(form) {
  const word = form.elements.word.value.trim();
  const meaning = form.elements.meaning.value.trim();
  if (!word || !meaning) return;
  const icon = cleanIcon(form.elements.icon.value);
  if (form.elements.icon.value.trim() && icon == null) {
    toast("Biểu tượng chỉ dùng emoji");
    return;
  }
  const pos = POS_VI[form.elements.pos.value] ? form.elements.pos.value : "";
  const example = form.elements.example.value.trim().slice(0, 300);
  const id = form.dataset.id || "";
  const dup = (STATE.own || []).find((item) => item.word.toLowerCase() === word.toLowerCase() && item.id !== id);
  if (dup) {
    toast("Từ này đã có trong Từ của tôi");
    return;
  }
  if (id) {
    const item = STATE.own.find((entry) => entry.id === id);
    if (!item) return;
    Object.assign(item, { word: word.slice(0, 80), meaning: meaning.slice(0, 240), pos, example, icon: icon || "" });
  } else {
    STATE.own.push({
      id: newOwnId(),
      word: word.slice(0, 80),
      meaning: meaning.slice(0, 240),
      pos,
      example,
      icon: icon || "",
    });
    bumpAdded();
    STATE.settings.ownDeck = true;
  }
  reindex();
  session = null;
  save();
  toast(id ? "Đã sửa từ" : "Đã thêm vào Từ của tôi");
  view = "decks";
  render();
}

function deleteOwn(id) {
  const item = (STATE.own || []).find((entry) => entry.id === id);
  if (!item) return;
  if (!window.confirm(`Xóa «${item.word}» khỏi bộ Từ của tôi?`)) return;
  STATE.own = STATE.own.filter((entry) => entry.id !== id);
  delete STATE.cards[id];
  for (const day of Object.keys(STATE.introduced)) {
    STATE.introduced[day] = (STATE.introduced[day] || []).filter((cardId) => cardId !== id);
  }
  reindex();
  session = null;
  save();
  toast("Đã xóa từ");
  render();
}

function renderDecks() {
  const settings = STATE.settings;
  const levels = LEVELS.map((level) => {
    const on = settings.levels.includes(level) ? " on" : "";
    const pressed = settings.levels.includes(level) ? "true" : "false";
    return `<button type="button" class="level${on}" data-act="level" data-id="${level}" aria-pressed="${pressed}">
      <b>${level}</b><span>${LEVEL_NAME[level]} · ${countLevel(level).toLocaleString("vi-VN")} từ</span>
    </button>`;
  }).join("");
  const allOn = settings.topics.length === 0;
  const chips = [`<button type="button" class="chip${allOn ? " on" : ""}" data-act="topic-all" aria-pressed="${allOn}">Tất cả chủ đề</button>`];
  for (const topic of DATA.topics || []) {
    const count = countTopic(topic.id);
    if (!count) continue;
    const on = settings.topics.includes(topic.id);
    chips.push(`<button type="button" class="chip${on ? " on" : ""}" data-act="topic" data-id="${esc(topic.id)}" aria-pressed="${on}">
      ${esc(topic.name)} <small>${count}</small>
    </button>`);
  }
  const chosen = settings.levels.length ? settings.levels.join(", ") : "chưa chọn";
  main.innerHTML = `<section class="lede">
    <h1>Bộ thẻ</h1>
    <p>Chọn trình độ và, nếu muốn, một vài chủ đề. Lần đầu mở app, <strong>B1 và B2</strong> được chọn sẵn cho người học trung cấp.</p>
    <button type="button" class="primary" data-act="goto" data-goto="study">Bắt đầu học</button>
    <h2 class="section-title">Trình độ · đang chọn ${esc(chosen)}</h2>
    <div class="levels">${levels}</div>
    <h2 class="section-title">Thẻ mới mỗi ngày</h2>
    <div class="stepper">
      <button type="button" data-act="new-dec" aria-label="Giảm số thẻ mới">−</button>
      <strong>${settings.newPerDay} thẻ mới</strong>
      <button type="button" data-act="new-inc" aria-label="Tăng số thẻ mới">+</button>
    </div>
    <h2 class="section-title">Đọc thẻ</h2>
    <label class="switch">
      <input type="checkbox" data-act="auto-speak" ${settings.autoSpeak !== false ? "checked" : ""}>
      <span>Tự đọc khi lật thẻ</span>
    </label>
    <h2 class="section-title">Từ của tôi</h2>
    ${ownDeckHtml()}
    <h2 class="section-title">Chủ đề</h2>
    <p class="note">Để “Tất cả chủ đề” nếu bạn muốn học mọi từ trong trình độ đã chọn. Chọn một chủ đề để chỉ ôn phần đó.</p>
    <div class="chips">${chips.join("")}</div>
  </section>`;
  topmeta.textContent = chosen;
}

function medalGrid(kind) {
  const have = new Set(STATE.medals || []);
  return MEDALS.filter((medal) => medal.kind === kind).map((medal) => {
    const on = have.has(medal.id);
    const label = medal.kind === "streak" ? `Chuỗi ${medal.n} ngày` : `${medal.n} từ`;
    return `<article class="medal${on ? "" : " locked"}">
      <div class="medal-face" aria-hidden="true"><span>${medal.mark}</span></div>
      <b>${esc(medal.name)}</b>
      <small>${esc(label)}</small>
    </article>`;
  }).join("");
}

function stripHtml() {
  const today = todayISO();
  let day = addDays(today, -13);
  const cells = [];
  for (let i = 0; i < 14; i += 1) {
    const row = STATE.log[day] || {};
    const reviews = row.reviews || 0;
    const added = row.added || 0;
    const frozen = row.frozen && !reviews;
    const date = new Date(`${day}T12:00:00`);
    const extra = added ? `+${added}` : (frozen ? "❄️" : "");
    cells.push(`<div class="cell${day === today ? " today" : ""}">
      <span class="n">${reviews}</span>
      <span class="a">${extra}</span>
      <span class="d">${WEEK[date.getDay()]}</span>
    </div>`);
    day = addDays(day, 1);
  }
  return cells.join("");
}

function renderStats() {
  const numbers = totals();
  const accuracy = numbers.reviews ? `${Math.round((numbers.correct / numbers.reviews) * 100)}%` : "—";
  const streak = streakCount();
  const today = todayISO();
  const yesterday = addDays(today, -1);
  const frozenYesterday = STATE.log[yesterday] && STATE.log[yesterday].frozen && !(STATE.log[yesterday].reviews > 0);
  const streakNote = frozenYesterday
    ? "Hôm qua dùng đóng băng, chuỗi vẫn giữ."
    : streak
      ? (studied(today) ? "Bạn đã học hôm nay." : "Học một lượt hôm nay để giữ chuỗi.")
      : "Học một lượt để bắt đầu chuỗi.";
  const freeze = STATE.freeze;
  const freezeNote = freeze.bank >= 2
    ? `Đóng băng: ${freeze.bank}/2 · đã trữ đủ.`
    : `Đóng băng: ${freeze.bank}/2 · còn ${7 - freeze.progress} ngày học để thêm một lần.`;
  const leftNew = newRemaining();
  main.innerHTML = `<section>
    <h1 class="section-title" style="margin-top:4px">Thống kê</h1>
    <div class="stats">
      <article class="stat wide"><div class="k">Chuỗi ngày</div><div class="v">${streak}</div><div class="s">${esc(streakNote)} ${esc(freezeNote)}</div></article>
      <article class="stat"><div class="k">Đã học</div><div class="v">${numbers.learned.toLocaleString("vi-VN")}</div><div class="s">nhớ được ít nhất một lần</div></article>
      <article class="stat"><div class="k">Điểm XP</div><div class="v">${numbers.xp.toLocaleString("vi-VN")}</div><div class="s">+1 mỗi lượt, +2 khi biết</div></article>
      <article class="stat"><div class="k">Đến hạn hôm nay</div><div class="v">${numbers.due.toLocaleString("vi-VN")}</div><div class="s">trong bộ đang chọn</div></article>
      <article class="stat"><div class="k">Độ chính xác</div><div class="v">${accuracy}</div><div class="s">${numbers.reviews.toLocaleString("vi-VN")} lượt ôn</div></article>
      <article class="stat"><div class="k">Hôm nay</div><div class="v">${numbers.todayRow.reviews}</div><div class="s">${numbers.todayRow.correct} lần biết</div></article>
    </div>
    <h2 class="section-title">14 ngày</h2>
    <div class="strip" aria-label="14 ngày gần đây">${stripHtml()}</div>
    <p class="note">Số lớn là lượt ôn. Số nhỏ có dấu + là từ bạn thêm. ❄️ là ngày được đóng băng chuỗi.</p>
    <h2 class="section-title">Huy chương chuỗi</h2>
    <div class="medals">${medalGrid("streak")}</div>
    <h2 class="section-title">Huy chương từ vựng</h2>
    <div class="medals">${medalGrid("words")}</div>
    <p class="note">${leftNew ? `Còn ${leftNew} thẻ mới trong hạn hôm nay. ` : ""}Tiến độ chỉ nằm trên trình duyệt này. Đổi máy hoặc xóa dữ liệu trang là mất chuỗi. Xóa tiến độ vẫn giữ từ bạn tự thêm.</p>
    <button type="button" class="ghost" data-act="reset">Xóa tiến độ trên máy này</button>
  </section>`;
  topmeta.textContent = streak ? `${streak} ngày` : "Chưa có chuỗi";
}

function renderCredits() {
  const counts = DATA.counts || {};
  const bits = LEVELS.map((level) => `${level} ${Number(counts[level] || 0).toLocaleString("vi-VN")}`).join(" · ");
  main.innerHTML = `<section class="lede">
    <h1>Nguồn dữ liệu</h1>
    <p>Bộ thẻ này có ${Number(DATA.total || 0).toLocaleString("vi-VN")} từ (${esc(bits)}). Nghĩa và phiên âm lấy từ Wiktionary, mức CEFR lấy từ CEFR-J và Octanove, câu ví dụ lấy từ Tatoeba khi có câu chứa từ đó. Dữ liệu đã được chọn lọc và rút gọn cho người học — không phải bản đầy đủ của các nguồn.</p>
    <article class="source">
      <div class="badge">CC BY-SA 4.0 và GFDL</div>
      <h2>Wiktionary tiếng Việt</h2>
      <p>Nghĩa tiếng Việt và IPA của mục từ tiếng Anh. Trích xuất máy đọc được qua kaikki.org (wiktextract), từ bản dump khoảng 2026-10-02. Văn bản Wiktionary được cấp dưới giấy phép Creative Commons Ghi công – Chia sẻ tương tự 4.0 và GFDL.</p>
      <p><a href="https://vi.wiktionary.org/" target="_blank" rel="noopener">vi.wiktionary.org</a><br>
      <a href="https://kaikki.org/viwiktionary/rawdata.html" target="_blank" rel="noopener">Bản trích kaikki.org</a><br>
      <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.vi" target="_blank" rel="noopener">CC BY-SA 4.0</a></p>
    </article>
    <article class="source">
      <div class="badge">Dùng được, kể cả thương mại, nếu ghi nguồn</div>
      <h2>CEFR-J Wordlist 1.5</h2>
      <p>Mức A1–B2 và nhóm chủ đề. Bản quyền thuộc phòng thí nghiệm của Yukio Tono, Đại học Ngoại ngữ Tokyo. Danh sách được phép dùng cho nghiên cứu, giáo dục và mục đích thương mại nếu trích dẫn đúng.</p>
      <p>The CEFR-J Wordlist Version 1.5. Compiled by Yukio Tono, Tokyo University of Foreign Studies. Tệp lấy từ kho Open Language Profiles ngày 13/11/2026.</p>
      <p><a href="https://www.cefr-j.org/download.html" target="_blank" rel="noopener">cefr-j.org</a><br>
      <a href="https://github.com/openlanguageprofiles/olp-en-cefrj" target="_blank" rel="noopener">openlanguageprofiles/olp-en-cefrj</a></p>
    </article>
    <article class="source">
      <div class="badge">CC BY-SA 4.0</div>
      <h2>Octanove Vocabulary Profile C1/C2 1.0</h2>
      <p>Mức C1 và C2, do Octanove Labs lập, phát hành kèm bộ CEFR-J trên Open Language Profiles theo Creative Commons Ghi công – Chia sẻ tương tự 4.0.</p>
      <p><a href="https://github.com/openlanguageprofiles/olp-en-cefrj" target="_blank" rel="noopener">Kho dữ liệu</a> ·
      <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.vi" target="_blank" rel="noopener">Giấy phép</a></p>
    </article>
    <article class="source">
      <div class="badge">CC BY 2.0 FR</div>
      <h2>Tatoeba</h2>
      <p>Câu ví dụ Anh–Việt. Mỗi câu giữ id và tên người đóng góp khi có. Một số câu tiếng Anh xuất phát từ Tanaka Corpus (phạm vi công cộng).</p>
      <p><a href="https://tatoeba.org/en/downloads" target="_blank" rel="noopener">tatoeba.org/downloads</a> ·
      <a href="https://creativecommons.org/licenses/by/2.0/fr/deed.vi" target="_blank" rel="noopener">CC BY 2.0 FR</a></p>
    </article>
    <p class="note">Phần nghĩa, IPA và danh sách C1/C2 là tác phẩm phái sinh, giữ điều kiện chia sẻ tương tự của CC BY-SA 4.0. Câu Tatoeba giữ giấy phép CC BY 2.0 FR. Mức A1–B2 cần giữ lời trích CEFR-J. Mã nguồn ứng dụng tách riêng, xem LICENSE.</p>
  </section>`;
  topmeta.textContent = "Giấy phép và trích dẫn";
}

function errorHtml() {
  return `<section class="empty">
    <h1>Không tải được dữ liệu</h1>
    <p>Bộ từ vựng không mở được. Hãy chạy app qua một máy chủ tĩnh, không mở file HTML trực tiếp.</p>
    <button type="button" class="primary" data-act="retry-load">Thử lại</button>
  </section>`;
}

function setNav() {
  const current = view === "form" ? returnView : view;
  document.querySelectorAll("[data-nav]").forEach((button) => {
    button.setAttribute("aria-current", button.dataset.nav === current ? "page" : "false");
  });
}

function render() {
  if (!DATA) return;
  setNav();
  if (view === "study") renderStudy();
  else if (view === "decks") renderDecks();
  else if (view === "stats") renderStats();
  else if (view === "form") renderForm();
  else renderCredits();
  main.scrollTop = 0;
}

function grade(know) {
  if (busy || view !== "study") return;
  const item = currentItem();
  if (!item) return;
  busy = true;
  const retry = item.retry;
  let freezeEarned = false;
  if (!retry) {
    applySm2(item.id, know ? 4 : 1);
    bumpLog(know);
    STATE.xp = (STATE.xp || 0) + 1 + (know ? 2 : 0);
    freezeEarned = noteStudyDay();
    session.done += 1;
    if (!know) session.queue.push({ id: item.id, retry: true });
  }
  session.index += 1;
  const medals = checkMedals();
  save();
  const next = currentCard();
  if (next) autoSpeak(next, "advance");
  if (freezeEarned) toast("Bạn được 1 lần đóng băng chuỗi");
  if (medals.length) celebrate(medals);
  if (navigator.vibrate) navigator.vibrate(12);
  const tilt = document.getElementById("tilt");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (tilt && !reduced) {
    tilt.classList.add("is-leaving");
    tilt.style.transform = `translateX(${know ? 130 : -130}%) rotate(${know ? 12 : -12}deg)`;
  }
  window.setTimeout(() => {
    busy = false;
    renderStudy();
  }, tilt && !reduced ? 230 : 0);
}

function flip() {
  const card = document.getElementById("card");
  if (!card) return;
  card.classList.toggle("is-flipped");
  const word = currentCard();
  if (word) autoSpeak(word, "flip");
}

function bindSwipe() {
  const tilt = document.getElementById("tilt");
  if (!tilt) return;
  const stamps = () => {
    const miss = tilt.querySelector(".stamp.miss");
    const know = tilt.querySelector(".stamp.know");
    return { miss, know };
  };
  tilt.addEventListener("pointerdown", (event) => {
    if (event.button) return;
    if (event.target.closest("button, a")) return;
    drag = { pid: event.pointerId, x: event.clientX, y: event.clientY, dx: 0, moved: false };
    tilt.setPointerCapture(event.pointerId);
  });
  tilt.addEventListener("pointermove", (event) => {
    if (!drag || drag.pid !== event.pointerId) return;
    const dx = event.clientX - drag.x;
    const dy = event.clientY - drag.y;
    if (!drag.moved) {
      if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
      if (Math.abs(dy) > Math.abs(dx)) {
        drag = null;
        return;
      }
      drag.moved = true;
    }
    drag.dx = dx;
    const rot = Math.max(-12, Math.min(12, dx / 18));
    tilt.style.transform = `translateX(${dx}px) rotate(${rot}deg)`;
    const pair = stamps();
    if (pair.know) pair.know.style.opacity = String(Math.min(1, Math.max(0, dx / 90)));
    if (pair.miss) pair.miss.style.opacity = String(Math.min(1, Math.max(0, -dx / 90)));
  });
  const finish = (event) => {
    if (!drag || drag.pid !== event.pointerId) return;
    const info = drag;
    drag = null;
    tilt.style.transform = "";
    const pair = stamps();
    if (pair.know) pair.know.style.opacity = "0";
    if (pair.miss) pair.miss.style.opacity = "0";
    if (!info.moved) {
      flip();
      return;
    }
    if (info.dx > 96 || info.dx < -96) {
      suppressClick = true;
      window.setTimeout(() => { suppressClick = false; }, 450);
    }
    if (info.dx > 96) grade(true);
    else if (info.dx < -96) grade(false);
  };
  tilt.addEventListener("pointerup", finish);
  tilt.addEventListener("pointercancel", () => {
    drag = null;
    tilt.style.transform = "";
  });
}

function toggleLevel(id) {
  const selected = new Set(STATE.settings.levels);
  if (selected.has(id)) selected.delete(id);
  else selected.add(id);
  STATE.settings.levels = LEVELS.filter((level) => selected.has(level));
  save();
  session = null;
  render();
}

function toggleTopic(id) {
  const selected = new Set(STATE.settings.topics);
  if (selected.has(id)) selected.delete(id);
  else selected.add(id);
  STATE.settings.topics = [...selected];
  save();
  session = null;
  render();
}

function changeNew(delta) {
  const index = NEW_STEPS.indexOf(STATE.settings.newPerDay);
  const next = NEW_STEPS[Math.min(NEW_STEPS.length - 1, Math.max(0, index + (delta > 0 ? 1 : -1)))];
  if (next === STATE.settings.newPerDay) return;
  STATE.settings.newPerDay = next;
  save();
  session = null;
  render();
}

function resetProgress() {
  if (!window.confirm("Xóa toàn bộ tiến độ ôn trên máy này? Từ bạn tự thêm vẫn được giữ.")) return;
  const own = STATE.own || [];
  const autoSpeak = STATE.settings.autoSpeak !== false;
  const ownDeck = STATE.settings.ownDeck !== false;
  localStorage.removeItem(KEY);
  STATE = loadState();
  STATE.own = own;
  STATE.settings.autoSpeak = autoSpeak;
  STATE.settings.ownDeck = ownDeck;
  reindex();
  save();
  session = null;
  view = "stats";
  render();
  toast("Đã xóa tiến độ trên máy này");
}

document.addEventListener("click", (event) => {
  const nav = event.target.closest("[data-nav]");
  if (nav) {
    if (!DATA) return;
    view = nav.dataset.nav;
    render();
    return;
  }
  const act = event.target.closest("[data-act]");
  if (!act) return;
  const name = act.dataset.act;
  if (name === "speak") {
    event.preventDefault();
    event.stopPropagation();
    const card = currentCard();
    if (card) speak(card.word);
    return;
  }
  if (name === "know" || name === "miss") {
    if (suppressClick) return;
    grade(name === "know");
  }
  if (name === "goto") {
    view = act.dataset.goto;
    render();
  }
  if (name === "level") toggleLevel(act.dataset.id);
  if (name === "topic-all") {
    STATE.settings.topics = [];
    save();
    session = null;
    render();
  }
  if (name === "topic") toggleTopic(act.dataset.id);
  if (name === "new-dec") changeNew(-1);
  if (name === "new-inc") changeNew(1);
  if (name === "reset") resetProgress();
  if (name === "retry-load") boot();
  if (name === "add-word") {
    if (!DATA) return;
    openForm("");
  }
  if (name === "edit-word") openForm(act.dataset.id);
  if (name === "delete-word") deleteOwn(act.dataset.id);
  if (name === "own-deck") {
    STATE.settings.ownDeck = STATE.settings.ownDeck === false;
    save();
    session = null;
    reindex();
    render();
  }
  if (name === "close-form") {
    view = returnView || "decks";
    render();
  }
  if (name === "prefill") {
    const form = act.closest("form");
    if (form && form.elements.meaning) form.elements.meaning.value = act.dataset.meaning || "";
  }
});

document.addEventListener("change", (event) => {
  const act = event.target.closest("[data-act]");
  if (!act || act.dataset.act !== "auto-speak") return;
  STATE.settings.autoSpeak = event.target.checked;
  save();
});

document.addEventListener("input", (event) => {
  const form = event.target.form;
  if (!form || form.id !== "word-form" || event.target.name !== "word") return;
  updatePrefill(form);
});

document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!form || form.id !== "word-form") return;
  event.preventDefault();
  saveOwn(form);
});

document.addEventListener("keydown", (event) => {
  if (view !== "study" || !DATA) return;
  if (event.key === "ArrowRight") { event.preventDefault(); grade(true); }
  else if (event.key === "ArrowLeft") { event.preventDefault(); grade(false); }
  else if (event.key === " " || event.key === "Enter") {
    if (event.target.closest("button, a")) return;
    event.preventDefault();
    flip();
  } else if (event.key === "s" || event.key === "S") {
    const card = currentCard();
    if (card) speak(card.word);
  }
});

async function boot() {
  main.innerHTML = `<section class="empty"><h1>Đang mở bộ thẻ…</h1><p>Một lát thôi.</p></section>`;
  topmeta.textContent = "";
  try {
    const [vocabRes, iconRes] = await Promise.all([
      fetch("data/vocab.json"),
      fetch("data/icons.json").catch(() => null),
    ]);
    if (!vocabRes.ok) throw new Error("bad status");
    DATA = await vocabRes.json();
    ICONS = iconRes && iconRes.ok ? await iconRes.json() : {};
    STATE = loadState();
    reindex();
    const known = new Set((DATA.topics || []).map((topic) => topic.id));
    STATE.settings.topics = STATE.settings.topics.filter((id) => known.has(id));
    const changed = reconcileFreezes();
    const fresh = checkMedals();
    if (changed || fresh.length) save();
    if (window.speechSynthesis) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.addEventListener("voiceschanged", () => window.speechSynthesis.getVoices());
    }
    render();
    if (fresh.length) celebrate(fresh);
  } catch {
    main.innerHTML = errorHtml();
    topmeta.textContent = "";
  }
}

boot();
