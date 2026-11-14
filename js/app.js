/* FlashFree — SM-2 flashcards. Biết = grade 4, Chưa biết = grade 1.
   A failed card is shown once more in the same session; the stored grade stays the first answer. */

import { accountEnabled, bindAccount, currentUser, scheduleSync, signInGoogle, signOutGoogle } from "./account.js";
import { STREAK_MIN, medalValues, shareLink, streakFromLog } from "./progress.js";

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
const THEME_KEY = "latu-theme";
const MODES = ["cards", "listen", "cloze"];
const RATES = [0.8, 1, 1.25, 1.5];
const REPEATS = [1, 2, 3, 0];
const THEMES = {
  paper: { name: "Giấy", color: "#f3ecdf" },
  sea: { name: "Biển", color: "#e7f1f4" },
  moss: { name: "Rêu", color: "#e7f2ea" },
  blossom: { name: "Hoa", color: "#f8ecee" },
  dark: { name: "Tối", color: "#161311" },
};
const TOPIC_MIGRATE = {
  hobbies: ["sports", "music", "art"],
  home: ["house", "furniture", "kitchen"],
  town: ["city", "shopping"],
  arts: ["art"],
  personal: ["body", "emotions", "personality"],
  colours: ["colors"],
  news: ["media", "politics"],
  technical: ["science", "technology", "computers"],
  services: ["shopping", "hotel"],
};
const LICENSE_NAME = {
  "by-sa-4": ["CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/"],
  "by-sa-4.0": ["CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/"],
  "by-sa-3": ["CC BY-SA 3.0", "https://creativecommons.org/licenses/by-sa/3.0/"],
  "by-sa-3.0": ["CC BY-SA 3.0", "https://creativecommons.org/licenses/by-sa/3.0/"],
  "by-sa-2.5": ["CC BY-SA 2.5", "https://creativecommons.org/licenses/by-sa/2.5/"],
  "by-sa-2": ["CC BY-SA 2.0", "https://creativecommons.org/licenses/by-sa/2.0/"],
  "by-sa-2.0": ["CC BY-SA 2.0", "https://creativecommons.org/licenses/by-sa/2.0/"],
  "by-4": ["CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"],
  "by-4.0": ["CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"],
  "by-3": ["CC BY 3.0", "https://creativecommons.org/licenses/by/3.0/"],
  "by-3.0": ["CC BY 3.0", "https://creativecommons.org/licenses/by/3.0/"],
  "by-2.5": ["CC BY 2.5", "https://creativecommons.org/licenses/by/2.5/"],
  "by-2": ["CC BY 2.0", "https://creativecommons.org/licenses/by/2.0/"],
  "by-2.0": ["CC BY 2.0", "https://creativecommons.org/licenses/by/2.0/"],
  cc0: ["CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"],
  pd: ["Public domain", "https://creativecommons.org/publicdomain/mark/1.0/"],
  gfdl: ["GFDL", "https://www.gnu.org/licenses/fdl-1.3.html"],
  "gfdl-1.2": ["GFDL 1.2", "https://www.gnu.org/licenses/old-licenses/fdl-1.2.html"],
  "gfdl-1.3": ["GFDL 1.3", "https://www.gnu.org/licenses/fdl-1.3.html"],
};
const OPENMOJI_SVG = "https://cdn.jsdelivr.net/gh/hfg-gmuend/openmoji@17.0.0/color/svg/";
const FLUENT_BASE = "https://cdn.jsdelivr.net/gh/microsoft/fluentui-emoji@1ffb34c752ecf5d402f04cfb4b392c77f57c54bc/assets/";
const TWEMOJI_SVG = "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/";
const NOTO_SVG = "https://cdn.jsdelivr.net/gh/googlefonts/noto-emoji@v2.047/svg/emoji_u";
const PIC_KEY = "latu-pic-v1";
const PIC_STYLES = ["auto", "sticker", "flat", "photo"];
const NEW_STEPS = [5, 10, 15, 20, 25, 30, 35, 40];
const MEDALS = [
  { id: "streak-3", kind: "streak", n: 3, name: "Ba ngày", mark: "🌱" },
  { id: "streak-7", kind: "streak", n: 7, name: "Một tuần", mark: "🍀" },
  { id: "streak-10", kind: "streak", n: 10, name: "Mười ngày", mark: "🔥" },
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
  { id: "day-100", kind: "day", n: 100, name: "100 thẻ một ngày", mark: "⚡" },
  { id: "own-1", kind: "own", n: 1, name: "Từ đầu tiên của tôi", mark: "➕" },
  { id: "perfect-7", kind: "perfect", n: 7, name: "Bảy ngày hoàn hảo", mark: "✨" },
  { id: "mastered-100", kind: "mastered", n: 100, name: "Thuộc 100 từ", mark: "🧠" },
  { id: "share-2", kind: "share", n: 2, name: "Chia sẻ 2 lần", mark: "📣" },
  { id: "invite-2", kind: "invite", n: 2, name: "Mời 2 bạn", mark: "🤝" },
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
const loadedLevels = new Set();
const loadedTopicFiles = new Set();
const listenRun = { token: 0, timer: 0, playing: false };
let EMOJI_INDEX = {};
let picPrefs = {};

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

function makeLocalId() {
  const bytes = new Uint8Array(9);
  if (window.crypto && crypto.getRandomValues) crypto.getRandomValues(bytes);
  else for (let i = 0; i < bytes.length; i += 1) bytes[i] = Math.floor(Math.random() * 256);
  return `g_${[...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join("")}`;
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
    settings: {
      newPerDay: 10, levels: ["B1", "B2"], topics: [], autoSpeak: true, ownDeck: true,
      theme: "paper", mode: "cards", listenRate: 1, listenRepeat: 1, picStyle: "auto",
    },
    cards: {},
    introduced: {},
    log: {},
    own: [],
    xp: 0,
    medals: [],
    freeze: { bank: 0, progress: 0, streak: 0, last: null, best: 0, rule: STREAK_MIN },
    shared: 0,
    invites: 0,
    localId: "",
    updatedAt: 0,
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
    best: Math.max(0, Number(raw.best) || 0),
    rule: Number(raw.rule) || 0,
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
    if (!raw) return applyStreakFromLog(base);
    const parsed = JSON.parse(raw);
    const settings = { ...base.settings, ...(parsed.settings || {}) };
    settings.levels = (settings.levels || []).filter((level) => LEVELS.includes(level));
    settings.topics = Array.isArray(settings.topics) ? settings.topics : [];
    if (!NEW_STEPS.includes(Number(settings.newPerDay))) settings.newPerDay = 10;
    settings.autoSpeak = settings.autoSpeak !== false;
    settings.ownDeck = settings.ownDeck !== false;
    if (!THEMES[settings.theme]) settings.theme = "paper";
    if (!MODES.includes(settings.mode)) settings.mode = "cards";
    if (!RATES.includes(Number(settings.listenRate))) settings.listenRate = 1;
    if (!REPEATS.includes(Number(settings.listenRepeat))) settings.listenRepeat = 1;
    if (!PIC_STYLES.includes(settings.picStyle)) settings.picStyle = "auto";
    settings.topics = migrateTopics(settings.topics);
    const log = parsed.log && typeof parsed.log === "object" ? parsed.log : {};
    const knownMedals = new Set(MEDALS.map((medal) => medal.id));
    return applyStreakFromLog({
      settings,
      cards: parsed.cards && typeof parsed.cards === "object" ? parsed.cards : {},
      introduced: parsed.introduced && typeof parsed.introduced === "object" ? parsed.introduced : {},
      log,
      own: cleanOwn(parsed.own),
      xp: Number.isFinite(Number(parsed.xp)) ? Math.max(0, Number(parsed.xp)) : backfillXp(log),
      medals: Array.isArray(parsed.medals) ? parsed.medals.filter((id) => knownMedals.has(id)) : [],
      freeze: normalizeFreeze(parsed.freeze, log),
      shared: Math.max(0, Number(parsed.shared) || 0),
      invites: Math.max(0, Number(parsed.invites) || 0),
      localId: typeof parsed.localId === "string" && parsed.localId ? parsed.localId : makeLocalId(),
      updatedAt: Math.max(0, Number(parsed.updatedAt) || 0),
    });
  } catch {
    return applyStreakFromLog(base);
  }
}

function applyStreakFromLog(state) {
  if (!state.localId) state.localId = makeLocalId();
  const computed = streakFromLog(state.log || {}, todayISO());
  const migrated = !state.freeze || state.freeze.rule !== STREAK_MIN;
  state.freeze.streak = computed.streak;
  state.freeze.last = computed.last;
  state.freeze.best = Math.max(Number(state.freeze.best) || 0, computed.best);
  if (migrated) {
    state.freeze.progress = computed.streak % 7;
    state.freeze.rule = STREAK_MIN;
  }
  return state;
}

function save(options) {
  const cutoff = addDays(todayISO(), -120);
  for (const day of Object.keys(STATE.log)) {
    if (day < cutoff) delete STATE.log[day];
  }
  STATE.updatedAt = Date.now();
  if (!STATE.localId) STATE.localId = makeLocalId();
  localStorage.setItem(KEY, JSON.stringify(STATE));
  try { localStorage.setItem(THEME_KEY, STATE.settings.theme || "paper"); } catch { /* ignore */ }
  if (!options || options.sync !== false) scheduleSync();
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
  const row = STATE.log[today] || {};
  if ((row.reviews || 0) < STREAK_MIN) return false;
  const freeze = STATE.freeze;
  if (freeze.last === today) return false;
  freeze.streak = (freeze.last ? freeze.streak : 0) + 1;
  freeze.last = today;
  freeze.best = Math.max(freeze.best || 0, freeze.streak);
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

function progressSnapshot() {
  return {
    streak: streakCount(),
    cards: STATE.cards,
    log: STATE.log,
    ownCount: (STATE.own || []).length,
    shared: STATE.shared || 0,
    invites: STATE.invites || 0,
  };
}

function checkMedals() {
  const have = new Set(STATE.medals || []);
  const values = medalValues(progressSnapshot());
  const fresh = [];
  for (const medal of MEDALS) {
    if (have.has(medal.id)) continue;
    if ((values[medal.kind] || 0) >= medal.n) fresh.push(medal);
  }
  if (fresh.length) STATE.medals = [...have, ...fresh.map((medal) => medal.id)];
  return fresh;
}

function migrateTopics(list) {
  const out = [];
  const seen = new Set();
  for (const id of Array.isArray(list) ? list : []) {
    const next = Object.prototype.hasOwnProperty.call(TOPIC_MIGRATE, id) ? TOPIC_MIGRATE[id] : [id];
    for (const item of next) {
      if (!item || seen.has(item)) continue;
      seen.add(item);
      out.push(item);
    }
  }
  return out;
}

function applyTheme(id) {
  const theme = THEMES[id] ? id : "paper";
  document.documentElement.setAttribute("data-theme", theme);
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", THEMES[theme].color);
  if (STATE && STATE.settings) STATE.settings.theme = theme;
  try { localStorage.setItem(THEME_KEY, theme); } catch { /* ignore */ }
}

function studyMode() {
  return MODES.includes(STATE.settings.mode) ? STATE.settings.mode : "cards";
}

function loadPicPrefs() {
  try {
    const raw = JSON.parse(localStorage.getItem(PIC_KEY) || "{}");
    picPrefs = raw && typeof raw === "object" ? raw : {};
  } catch {
    picPrefs = {};
  }
}

function savePicPrefs() {
  try { localStorage.setItem(PIC_KEY, JSON.stringify(picPrefs)); } catch { /* ignore */ }
}

function picKey(pic) {
  if (!pic) return "";
  if (pic.s === "c") return `c:${pic.f}`;
  return `${pic.s}:${String(pic.h || "").toLowerCase()}`;
}

function imageUrl(img) {
  if (!img) return "";
  const kind = img.s || img.t;
  if ((kind === "o") && img.h) return `${OPENMOJI_SVG}${encodeURIComponent(img.h)}.svg`;
  if (kind === "c" && img.f) {
    return `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(img.f)}?width=320`;
  }
  if (kind === "f" && img.path) {
    const parts = String(img.path).split("/").map((part) => encodeURIComponent(part)).join("/");
    return `${FLUENT_BASE}${parts}`;
  }
  if (kind === "w" && img.h) return `${TWEMOJI_SVG}${String(img.h).toLowerCase()}.svg`;
  if (kind === "n" && img.h) return `${NOTO_SVG}${String(img.h).toLowerCase().replace(/-/g, "_")}.svg`;
  return "";
}

function imageCredit(img) {
  if (!img) return "";
  const kind = img.s || img.t;
  if (kind === "o") {
    const who = img.a ? `${esc(img.a)} · ` : "";
    return `${who}OpenMoji, <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a> · <a href="https://openmoji.org/" target="_blank" rel="noopener">openmoji.org</a>`;
  }
  if (kind === "f") {
    return `Microsoft Fluent Emoji, <a href="https://opensource.org/license/mit" target="_blank" rel="noopener">MIT</a> · <a href="https://github.com/microsoft/fluentui-emoji" target="_blank" rel="noopener">fluentui-emoji</a>`;
  }
  if (kind === "w") {
    return `Twemoji, <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a> · <a href="https://github.com/twitter/twemoji" target="_blank" rel="noopener">twitter/twemoji</a>`;
  }
  if (kind === "n") {
    return `Google Noto Emoji, <a href="https://scripts.sil.org/OFL" target="_blank" rel="noopener">SIL OFL 1.1</a> · <a href="https://github.com/googlefonts/noto-emoji" target="_blank" rel="noopener">noto-emoji</a>`;
  }
  const lic = LICENSE_NAME[img.l] || ["Giấy phép mở", "https://commons.wikimedia.org/"];
  const file = `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(img.f || "")}`;
  const who = img.a ? esc(img.a) : "Wikimedia Commons";
  return `${who} · <a href="${esc(lic[1])}" target="_blank" rel="noopener">${esc(lic[0])}</a> · <a href="${file}" target="_blank" rel="noopener">Wikimedia Commons</a>`;
}

function pictureChoices(card) {
  const all = [];
  const seen = new Set();
  const push = (pic) => {
    const key = picKey(pic);
    if (!key || seen.has(key)) return;
    seen.add(key);
    all.push(pic);
  };
  if (card.img && card.img.t === "c" && card.img.f) {
    push({ s: "c", f: card.img.f, a: card.img.a || "", l: card.img.l || "", lead: card.img.lead === true });
  }
  if (card.img && card.img.t === "o" && card.img.h) {
    push({ s: "o", h: card.img.h, a: card.img.a || "" });
  }
  for (const hex of card.emo || []) {
    const h = String(hex || "").toLowerCase();
    if (!/^[0-9a-f-]+$/.test(h)) continue;
    const info = EMOJI_INDEX[h] || {};
    if (info.f) push({ s: "f", h, path: info.f });
    push({ s: "w", h });
    push({ s: "n", h });
    if (info.oh) push({ s: "o", h: info.oh, a: info.oa || "" });
  }
  return all;
}

function orderedPics(card) {
  const all = pictureChoices(card);
  const style = STATE && STATE.settings ? STATE.settings.picStyle : "auto";
  let list = all;
  if (style === "sticker") list = all.filter((pic) => pic.s === "f");
  else if (style === "flat") list = all.filter((pic) => pic.s === "w" || pic.s === "n" || pic.s === "o");
  else if (style === "photo") list = all.filter((pic) => pic.s === "c");
  else {
    const lead = all.filter((pic) => pic.s === "c" && pic.lead);
    const emoji = all.filter((pic) => pic.s !== "c");
    const weak = all.filter((pic) => pic.s === "c" && !pic.lead);
    list = lead.concat(emoji, weak);
  }
  if (!list.length) list = all;
  const saved = picPrefs[card.id];
  if (!saved) return list;
  const index = list.findIndex((pic) => picKey(pic) === saved);
  if (index <= 0) return list;
  return list.slice(index).concat(list.slice(0, index));
}

function chosenPic(card) {
  const list = orderedPics(card);
  return { pic: list[0] || null, list };
}

function pictureHtml(card) {
  const { pic, list } = chosenPic(card);
  const src = imageUrl(pic);
  const icon = memoryIcon(card);
  if (!src) return icon ? `<p class="memo" aria-hidden="true">${esc(icon)}</p>` : "";
  const swap = list.length > 1
    ? `<button type="button" class="swap" data-act="pic-swap" aria-label="Đổi hình">↻</button>`
    : "";
  return `<div class="picbox wait">
    <img class="pic" alt="" src="${esc(src)}" decoding="async">
    ${icon ? `<p class="memo" aria-hidden="true">${esc(icon)}</p>` : ""}
    ${swap}
    <button type="button" class="info" data-act="img-info" aria-label="Nguồn ảnh">i</button>
  </div>`;
}

function meaningHtml(card) {
  if (card.meaningLang === "en") {
    return `<p class="en-label">Giải nghĩa tiếng Anh</p><p class="meaning">${esc(card.meaning)}</p>`;
  }
  return `<p class="meaning">${esc(card.meaning)}</p>`;
}

function bindPicture(root) {
  const img = root.querySelector(".pic");
  const box = root.querySelector(".picbox");
  if (!img || !box) return;
  const ok = () => box.classList.add("has-pic");
  const bad = () => {
    box.classList.remove("wait");
    img.remove();
  };
  if (img.complete && img.naturalWidth > 0) ok();
  else {
    img.addEventListener("load", ok);
    img.addEventListener("error", bad);
  }
}

function showImageInfo() {
  const card = currentCard();
  const pic = card ? chosenPic(card).pic : null;
  if (!pic) return;
  let pop = document.getElementById("imgpop");
  if (!pop) {
    pop = document.createElement("div");
    pop.id = "imgpop";
    pop.className = "imgpop";
    document.getElementById("app").appendChild(pop);
  }
  pop.hidden = false;
  pop.innerHTML = `<p>${imageCredit(pic)}</p><button type="button" data-act="close-pop">Đóng</button>`;
}

function hideImageInfo() {
  const pop = document.getElementById("imgpop");
  if (pop) pop.hidden = true;
}

function modeSwitch() {
  const mode = studyMode();
  const button = (id, label) => `<button type="button" data-act="mode" data-id="${id}" class="${mode === id ? "on" : ""}" aria-pressed="${mode === id}">${label}</button>`;
  return `<div class="modes" role="group" aria-label="Cách học">${button("cards", "Thẻ")}${button("listen", "Nghe")}${button("cloze", "Điền")}</div>`;
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
    if (state && isMastered(state)) continue;
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
  if (session && session.key === key) {
    if (!session.graded) session.graded = new Set();
    return;
  }
  const today = todayISO();
  const plan = planToday(today);
  const queue = plan.due.concat(plan.fresh).map((card) => ({ id: card.id, retry: false }));
  session = { key, queue, index: 0, total: queue.length, done: 0, graded: new Set(), listenIndex: 0, clozeIndex: 0 };
}

function currentItem() {
  if (!session) return null;
  const mode = studyMode();
  if (mode === "listen") return session.queue[session.listenIndex] || null;
  if (mode === "cloze") return currentClozeItem();
  while (session.index < session.queue.length) {
    const item = session.queue[session.index];
    if (item.retry || !session.graded.has(item.id)) return item;
    session.index += 1;
  }
  return null;
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
  const value = last === today || last === addDays(today, -1) ? STATE.freeze.streak : 0;
  STATE.freeze.best = Math.max(STATE.freeze.best || 0, value, bestStreakNow());
  return value;
}

function bestStreakNow() {
  return streakFromLog(STATE.log || {}, todayISO()).best;
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
    if (state && !isMastered(state) && state.due <= today && state.last !== today) due += 1;
  }
  const todayRow = STATE.log[today] || { reviews: 0, correct: 0 };
  return { learned, reviews, correct, due, todayRow, xp: STATE.xp || 0 };
}

function speak(text, quiet, lang) {
  const synth = window.speechSynthesis;
  if (!synth || !text) {
    if (!quiet) toast("Trình duyệt này không đọc được tiếng Anh.");
    return false;
  }
  try {
    const utter = new SpeechSynthesisUtterance(text);
    const language = lang || "en-US";
    utter.lang = language;
    utter.rate = 0.92;
    const voices = synth.getVoices();
    const voice = voices.find((item) => item.lang === language)
      || voices.find((item) => new RegExp("^" + language.slice(0, 2) + "([-_]|$)", "i").test(item.lang || ""));
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
  const enPill = card.meaningLang === "en" ? `<span class="pill en">EN</span>` : "";
  const meta = card.own ? (pos ? `Của tôi · ${pos}` : "Của tôi") : `${card.level} · ${pos}`;
  const memo = pictureHtml(card);
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
      <div class="pillrow"><span class="pill">${esc(meta)}</span>${enPill}${topicPill}${retry}</div>
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
        ${meaningHtml(card)}
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
  bindPicture(node);
  updateStudyChrome();
  autoSpeak(card, "show");
}

function studyShell() {
  return `<section class="study">
    ${modeSwitch()}
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
  const mode = studyMode();
  if (mode === "listen") {
    renderListen();
    return;
  }
  if (mode === "cloze") {
    renderCloze();
    return;
  }
  if (!currentItem()) {
    main.innerHTML = doneHtml();
    topmeta.textContent = STATE.settings.levels.join(" · ") || "Chưa chọn";
    return;
  }
  main.innerHTML = studyShell();
  fillCard();
  bindSwipe();
}

function stopAudio() {
  listenRun.token += 1;
  listenRun.playing = false;
  window.clearTimeout(listenRun.timer);
  if (window.speechSynthesis) {
    try { window.speechSynthesis.cancel(); } catch { /* ignore */ }
  }
}

function formsOf(lemma) {
  const word = String(lemma || "").toLowerCase();
  const found = new Set([word]);
  if (!word || word.includes(" ") || word.length < 4) return found;
  ["s", "es", "ed", "ing", "d"].forEach((suffix) => found.add(word + suffix));
  if (word.endsWith("e")) {
    found.add(word.slice(0, -1) + "ing");
    found.add(word.slice(0, -1) + "ed");
  }
  if (word.endsWith("y") && !"aeiou".includes(word[word.length - 2])) {
    found.add(word.slice(0, -1) + "ies");
    found.add(word.slice(0, -1) + "ied");
  }
  if (word.length > 4 && !"aeiouy".includes(word[word.length - 1]) && "aeiou".includes(word[word.length - 2]) && !"aeiou".includes(word[word.length - 3])) {
    found.add(word + word[word.length - 1] + "ed");
    found.add(word + word[word.length - 1] + "ing");
  }
  return found;
}

function escapeReg(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function blankSentence(card) {
  if (!card || !card.example) return null;
  const forms = [...formsOf(card.word)].filter(Boolean).sort((a, b) => b.length - a.length);
  if (!forms.length) return null;
  const re = new RegExp(`(^|[^A-Za-z'])(${forms.map(escapeReg).join("|")})(?![A-Za-z'])`, "i");
  const match = card.example.match(re);
  if (!match) return null;
  const surface = match[2];
  const start = match.index + match[1].length;
  return {
    surface,
    before: card.example.slice(0, start),
    after: card.example.slice(start + surface.length),
  };
}

function mulberry32(seed) {
  let value = seed >>> 0;
  return () => {
    value = (value + 0x6D2B79F5) >>> 0;
    let t = Math.imul(value ^ (value >>> 15), 1 | value);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function clozeItems() {
  return session.queue.filter((item) => blankSentence(INDEX.get(item.id)));
}

function currentClozeItem() {
  const items = clozeItems();
  while (session.clozeIndex < items.length) {
    const item = items[session.clozeIndex];
    if (item.cloze && !item.cloze.done) return item;
    if (item.retry || !session.graded.has(item.id)) return item;
    session.clozeIndex += 1;
  }
  return null;
}

function clozeOptions(card, surface) {
  const pool = DATA.cards.filter((item) => item.id !== card.id && item.pos === card.pos && item.word && item.word.length < 24);
  const same = pool.filter((item) => item.level === card.level);
  const source = same.length >= 8 ? same : pool;
  const rand = mulberry32(hash(`${card.id}:${surface}`));
  const copy = source.slice();
  const picked = [];
  const used = new Set([card.word.toLowerCase(), surface.toLowerCase()]);
  while (picked.length < 3 && copy.length) {
    const index = Math.floor(rand() * copy.length);
    const [item] = copy.splice(index, 1);
    const key = item.word.toLowerCase();
    if (used.has(key)) continue;
    used.add(key);
    picked.push(item.word);
  }
  const options = picked.concat([surface]);
  for (let i = options.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rand() * (i + 1));
    [options[i], options[j]] = [options[j], options[i]];
  }
  return options;
}

function normAnswer(text) {
  return String(text || "").trim().toLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "");
}

function recordGrade(id, know, retry) {
  let freezeEarned = false;
  if (!retry) {
    applySm2(id, know ? 4 : 1);
    bumpLog(know);
    STATE.xp = (STATE.xp || 0) + 1 + (know ? 2 : 0);
    freezeEarned = noteStudyDay();
    session.done += 1;
    session.graded.add(id);
    if (!know) session.queue.push({ id, retry: true });
  }
  const medals = checkMedals();
  save();
  return { freezeEarned, medals };
}

function renderCloze() {
  const item = currentClozeItem();
  if (!clozeItems().length) {
    main.innerHTML = `<section class="empty">
      <h1>Chưa có câu để điền</h1>
      <p>Bài điền chỗ trống cần câu ví dụ. Bộ đang chọn chưa có câu, hoặc các câu không chứa đúng từ. Hãy học bằng thẻ, hoặc chọn thêm trình độ.</p>
      ${modeSwitch()}
    </section>`;
    topmeta.textContent = "Điền từ";
    return;
  }
  if (!item) {
    main.innerHTML = doneHtml();
    topmeta.textContent = STATE.settings.levels.join(" · ") || "Điền từ";
    return;
  }
  const card = INDEX.get(item.id);
  const blank = blankSentence(card);
  const options = clozeOptions(card, blank.surface);
  const answered = item.cloze && !item.cloze.done;
  const know = item.cloze && item.cloze.know;
  const given = item.cloze ? normAnswer(item.cloze.given) : "";
  const choices = options.map((option) => {
    const hit = normAnswer(option) === normAnswer(blank.surface) || normAnswer(option) === normAnswer(card.word);
    const picked = given && given === normAnswer(option);
    let mark = "";
    if (answered && hit) mark = " good";
    else if (answered && picked) mark = " bad";
    return `<button type="button" class="choice${mark}" data-act="cloze-choice" data-word="${esc(option)}" ${answered ? "disabled" : ""}>${esc(option)}</button>`;
  }).join("");
  const result = answered
    ? `<p class="cloze-result ${know ? "good" : "bad"}">${know ? "Đúng." : "Chưa đúng."} <b>${esc(blank.surface)}</b> · ${esc(card.meaning)}</p>
       ${card.exampleVi ? `<p class="ex-vi">${esc(card.exampleVi)}</p>` : ""}
       <button type="button" class="primary" data-act="cloze-next">Tiếp</button>`
    : `<form class="typebox" id="cloze-form">
        <input name="answer" autocomplete="off" autocapitalize="off" placeholder="Hoặc gõ từ tiếng Anh" aria-label="Gõ từ tiếng Anh">
        <button type="submit">Kiểm tra</button>
      </form>`;
  const remain = clozeItems().filter((row) => !(row.cloze && row.cloze.done) && (row.retry || !session.graded.has(row.id) || (row.cloze && !row.cloze.done))).length;
  main.innerHTML = `<section class="study cloze">
    ${modeSwitch()}
    <div class="bar" aria-hidden="true"><span style="width:${session.total ? Math.min(100, Math.round((session.done / session.total) * 100)) : 0}%"></span></div>
    <article class="cloze-card">
      <div class="pillrow"><span class="pill">${esc(card.level)} · ${esc(POS_VI[card.pos] || card.pos || "từ")}</span></div>
      ${card.meaningLang === "en" ? `<p class="en-label">Giải nghĩa tiếng Anh</p>` : ""}
      <p class="cloze-hint">${esc(card.meaning)}</p>
      <p class="cloze-sent">${esc(blank.before)}<span class="blank">${answered ? esc(blank.surface) : "_____"}</span>${esc(blank.after)}</p>
      <div class="choices">${choices}</div>
      ${result}
    </article>
  </section>`;
  topmeta.textContent = `Điền · còn ${remain}`;
}

function answerCloze(item, given) {
  if (!item || item.cloze || !String(given || "").trim()) return;
  const card = INDEX.get(item.id);
  const blank = blankSentence(card);
  if (!blank) return;
  const typed = normAnswer(given);
  const ok = typed === normAnswer(blank.surface) || typed === normAnswer(card.word);
  item.cloze = { know: ok, given, done: false };
  const result = recordGrade(item.id, ok, !!item.retry);
  if (result.freezeEarned) toast("Bạn được 1 lần đóng băng chuỗi");
  if (result.medals.length) celebrate(result.medals);
  if (navigator.vibrate) navigator.vibrate(12);
  renderCloze();
}

function hasViVoice() {
  const synth = window.speechSynthesis;
  if (!synth) return false;
  return synth.getVoices().some((voice) => /^vi([-_]|$)/i.test(voice.lang || ""));
}

function speakPiece(text, lang, rate, token) {
  return new Promise((resolve) => {
    const synth = window.speechSynthesis;
    if (!synth || !text || listenRun.token !== token) {
      resolve(false);
      return;
    }
    let settled = false;
    const finish = (ok) => {
      if (settled) return;
      settled = true;
      resolve(ok);
    };
    try {
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = lang;
      utter.rate = rate;
      const voices = synth.getVoices();
      const want = lang.toLowerCase();
      const voice = voices.find((item) => (item.lang || "").toLowerCase().replace("_", "-") === want)
        || voices.find((item) => (item.lang || "").toLowerCase().replace("_", "-").startsWith(want.slice(0, 2)));
      if (lang.toLowerCase().startsWith("vi") && !voice) {
        finish(false);
        return;
      }
      if (voice) utter.voice = voice;
      utter.onend = () => finish(listenRun.token === token);
      utter.onerror = () => finish(false);
      synth.speak(utter);
      window.setTimeout(() => finish(listenRun.token === token), Math.min(14000, 700 + text.length * 95 / rate));
    } catch {
      finish(false);
    }
  });
}

function waitMs(ms, token) {
  return new Promise((resolve) => {
    window.clearTimeout(listenRun.timer);
    listenRun.timer = window.setTimeout(() => resolve(listenRun.token === token && listenRun.playing), ms);
  });
}

function listenCard() {
  return session.queue[session.listenIndex] ? INDEX.get(session.queue[session.listenIndex].id) : null;
}

function renderListen() {
  const card = listenCard();
  const total = session.queue.length;
  if (!card) {
    main.innerHTML = `<section class="empty">
      <h1>Hết danh sách nghe</h1>
      <p>Bạn đã nghe hết các thẻ của hôm nay. Chế độ này không ghi vào lịch ôn. Quay lại thẻ nếu bạn muốn bấm Biết hoặc Chưa biết.</p>
      ${modeSwitch()}
      <button type="button" class="primary" data-act="listen-restart">Nghe lại từ đầu</button>
    </section>`;
    topmeta.textContent = "Nghe";
    return;
  }
  const rate = Number(STATE.settings.listenRate) || 1;
  const repeat = Number(STATE.settings.listenRepeat);
  const rates = RATES.map((value) => `<button type="button" data-act="listen-rate" data-value="${value}" class="${value === rate ? "on" : ""}">${value === 1 ? "1×" : `${value}×`}</button>`).join("");
  const repeats = REPEATS.map((value) => `<button type="button" data-act="listen-repeat" data-value="${value}" class="${value === repeat ? "on" : ""}">${value === 0 ? "∞" : `${value}×`}</button>`).join("");
  const viNote = hasViVoice() ? "" : `<p class="note">Máy này không có giọng tiếng Việt, nên nghĩa hiện bằng chữ.</p>`;
  main.innerHTML = `<section class="study listen">
    ${modeSwitch()}
    <div class="bar" aria-hidden="true"><span style="width:${total ? Math.min(100, Math.round((session.listenIndex / total) * 100)) : 0}%"></span></div>
    <article class="listen-card" id="listen-card">
      ${pictureHtml(card)}
      <div class="pillrow"><span class="pill">${esc(card.level)} · ${session.listenIndex + 1}/${total}</span></div>
      <h1 class="${wordClass(card.word)} step-word">${esc(card.word)}</h1>
      ${card.ipa ? `<p class="ipa">/${esc(card.ipa)}/</p>` : ""}
      ${card.meaningLang === "en" ? `<p class="en-label">Giải nghĩa tiếng Anh</p>` : ""}
      <p class="meaning step-vi">${esc(card.meaning)}</p>
      ${card.example ? `<p class="ex-en step-ex">${esc(card.example)}</p>` : `<p class="hint step-ex">Không có câu ví dụ.</p>`}
    </article>
    <div class="listen-controls">
      <button type="button" data-act="listen-prev" aria-label="Thẻ trước">‹</button>
      <button type="button" class="primary listen-go" data-act="listen-toggle">${listenRun.playing ? "Tạm dừng" : "Nghe"}</button>
      <button type="button" data-act="listen-next" aria-label="Thẻ sau">›</button>
    </div>
    <div class="tune"><span>Tốc độ</span><div class="pills">${rates}</div></div>
    <div class="tune"><span>Lặp</span><div class="pills">${repeats}</div></div>
    ${viNote}
    <p class="note">Nghe từ, nghĩa, rồi câu ví dụ. Bấm Nghe một lần — máy cần cử chỉ đó trước khi đọc, nhất là trên iPhone. Chế độ này không tính vào lịch SM-2.</p>
  </section>`;
  bindPicture(main);
  topmeta.textContent = `Nghe · ${session.listenIndex + 1}/${total}`;
}

function markListenStep(name) {
  const card = document.getElementById("listen-card");
  if (!card) return;
  card.querySelectorAll(".step-word, .step-vi, .step-ex").forEach((node) => node.classList.remove("live"));
  const target = card.querySelector(name === "word" ? ".step-word" : name === "vi" ? ".step-vi" : ".step-ex");
  if (target) target.classList.add("live");
}

async function playListenPass(token) {
  const card = listenCard();
  if (!card) return false;
  const rate = Number(STATE.settings.listenRate) || 1;
  markListenStep("word");
  await speakPiece(card.word, "en-US", rate, token);
  if (!(await waitMs(650 / rate, token))) return false;
  markListenStep("vi");
  if (card.meaningLang === "en") await speakPiece(card.meaning, "en-US", rate, token);
  else if (hasViVoice()) await speakPiece(card.meaning, "vi-VN", rate, token);
  else if (!(await waitMs(1100, token))) return false;
  if (!(await waitMs(500 / rate, token))) return false;
  if (card.example) {
    markListenStep("ex");
    await speakPiece(card.example, "en-US", Math.min(rate, 1.15), token);
    if (!(await waitMs(700 / rate, token))) return false;
  }
  return listenRun.token === token && listenRun.playing;
}

async function listenLoop(token) {
  let cycles = 0;
  while (listenRun.token === token && listenRun.playing) {
    const ok = await playListenPass(token);
    if (!ok) return;
    cycles += 1;
    const repeat = Number(STATE.settings.listenRepeat);
    if (repeat === 0) continue;
    if (cycles < repeat) continue;
    cycles = 0;
    session.listenIndex += 1;
    if (!listenCard()) {
      listenRun.playing = false;
      renderListen();
      return;
    }
    const playing = listenRun.playing;
    const kept = listenRun.token;
    renderListen();
    listenRun.playing = playing;
    listenRun.token = kept;
    const button = main.querySelector("[data-act='listen-toggle']");
    if (button) button.textContent = "Tạm dừng";
  }
}

function startListen() {
  if (!listenCard()) {
    session.listenIndex = 0;
  }
  listenRun.playing = true;
  listenRun.token += 1;
  const token = listenRun.token;
  renderListen();
  listenRun.playing = true;
  listenRun.token = token;
  const button = main.querySelector("[data-act='listen-toggle']");
  if (button) button.textContent = "Tạm dừng";
  listenLoop(token);
}

function pauseListen() {
  listenRun.playing = false;
  listenRun.token += 1;
  window.clearTimeout(listenRun.timer);
  if (window.speechSynthesis) {
    try { window.speechSynthesis.cancel(); } catch { /* ignore */ }
  }
  const button = main.querySelector("[data-act='listen-toggle']");
  if (button) button.textContent = "Nghe";
}

function countLevel(level) {
  return Number((DATA.counts && DATA.counts[level]) || 0);
}

function countTopic(id) {
  const row = (DATA.topicLevels && DATA.topicLevels[id]) || {};
  const levels = STATE.settings.levels;
  if (!levels.length) return Object.values(row).reduce((sum, n) => sum + Number(n || 0), 0);
  return levels.reduce((sum, level) => sum + Number(row[level] || 0), 0);
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
  const general = [];
  const fields = [];
  for (const topic of DATA.topics || []) {
    if (topic.group === "field") fields.push(topic);
    else general.push(topic);
  }
  fields.sort((a, b) => (a.order || 0) - (b.order || 0));
  const chip = (topic) => {
    const count = countTopic(topic.id);
    if (topic.group !== "field" && !count) return "";
    if (topic.group === "field" && !(topic.count > 0)) return "";
    const on = settings.topics.includes(topic.id);
    return `<button type="button" class="chip${on ? " on" : ""}" data-act="topic" data-id="${esc(topic.id)}" aria-pressed="${on}">
      ${esc(topic.name)} <small>${count}</small>
    </button>`;
  };
  const chips = [`<button type="button" class="chip${allOn ? " on" : ""}" data-act="topic-all" aria-pressed="${allOn}">Tất cả chủ đề</button>`]
    .concat(general.map(chip).filter(Boolean));
  const fieldChips = fields.map(chip).filter(Boolean);
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
    <h2 class="section-title">Cách học</h2>
    ${modeSwitch()}
    <p class="note">Thẻ lật như cũ. Nghe đọc từ, nghĩa và câu rồi sang thẻ sau. Điền chọn hoặc gõ từ còn thiếu trong câu ví dụ; đúng tính là Biết, sai tính là Chưa biết.</p>
    <h2 class="section-title">Kiểu hình</h2>
    <div class="styles">${[
      ["auto", "Tự động"],
      ["sticker", "Sticker 3D"],
      ["flat", "Emoji phẳng"],
      ["photo", "Ảnh thật"],
    ].map(([id, label]) => {
      const on = (settings.picStyle || "auto") === id;
      return `<button type="button" data-act="pic-style" data-id="${id}" class="${on ? "on" : ""}" aria-pressed="${on}">${label}</button>`;
    }).join("")}</div>
    <p class="note">Tự động chọn ảnh thật nếu có, rồi sticker. Đổi hình trên thẻ được nhớ cho từng từ.</p>
    <h2 class="section-title">Màu</h2>
    <div class="themes">${Object.entries(THEMES).map(([id, theme]) => {
      const on = (settings.theme || "paper") === id;
      return `<button type="button" class="swatch${on ? " on" : ""}" data-act="theme" data-id="${id}" aria-pressed="${on}"><i style="background:${theme.color}"></i>${esc(theme.name)}</button>`;
    }).join("")}</div>
    <h2 class="section-title">Đọc thẻ</h2>
    <label class="switch">
      <input type="checkbox" data-act="auto-speak" ${settings.autoSpeak !== false ? "checked" : ""}>
      <span>Tự đọc khi lật thẻ</span>
    </label>
    <h2 class="section-title">Từ của tôi</h2>
    ${ownDeckHtml()}
    <h2 class="section-title">Chủ đề · ${general.length}</h2>
    <p class="note">Để “Tất cả chủ đề” nếu bạn muốn học mọi từ trong trình độ đã chọn. Số trên mỗi chủ đề là số từ trong trình độ đang bật.</p>
    <div class="chips">${chips.join("")}</div>
    <h2 class="section-title">Ngành nghề · ${fields.length}</h2>
    <p class="note">Từ chuyên ngành, từ dễ đến khó. Số là từ trong trình độ đang bật. Một từ có thể ở nhiều chủ đề.</p>
    <div class="chips">${fieldChips.join("")}</div>
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
  const todayCount = (STATE.log[today] && STATE.log[today].reviews) || 0;
  const streakNote = frozenYesterday
    ? "Hôm qua dùng đóng băng, chuỗi vẫn giữ."
    : todayCount >= STREAK_MIN
      ? "Hôm nay đã đủ 20 thẻ cho chuỗi."
      : streak
        ? `Hôm nay ${todayCount}/20 thẻ. Đủ 20 thẻ thì chuỗi tính thêm một ngày.`
        : "Trả lời đủ 20 thẻ trong ngày để bắt đầu chuỗi.";
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
  const images = DATA.imageCounts || {};
  const imageBits = LEVELS.map((level) => `${level} ${Number(images[level] || 0).toLocaleString("vi-VN")}`).join(" · ");
  main.innerHTML = `<section class="lede">
    <h1>Nguồn dữ liệu</h1>
    <p>Bộ thẻ này có ${Number(DATA.total || 0).toLocaleString("vi-VN")} từ (${esc(bits)}). ${Number(DATA.withImage || 0).toLocaleString("vi-VN")} từ có ảnh (${esc(imageBits)}). Nghĩa tiếng Việt lấy từ Wiktionary, mức A1–C2 của từ đã có trong CEFR-J hoặc Octanove được giữ nguyên, từ mới được xếp mức theo tần suất wordfreq so với trung vị của từng mức CEFR. Chủ đề chung dựa trên Open English WordNet. Mục Ngành nghề thêm từ chuyên môn từ NGSL/NAWL/BSL/TSL, trang thuật ngữ Wikipedia, MeSH và WordNet. Câu ví dụ lấy từ Tatoeba khi có câu chứa từ. Ảnh là sticker hoặc ảnh tự do trên Wikimedia Commons. Dữ liệu đã được chọn lọc và rút gọn — không phải bản đầy đủ của các nguồn.</p>
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
    <article class="source">
      <div class="badge">CC BY-SA 4.0</div>
      <h2>wordfreq</h2>
      <p>Tần suất để xếp mức CEFR cho từ không có trong CEFR-J hay Octanove. Dữ liệu tần suất của Robyn Speer, giấy phép CC BY-SA 4.0. Nguồn gốc gồm Google Books Ngram (dùng tự do, nên ghi nhận), Wikipedia, ParaCrawl, Leeds Internet Corpus, OPUS OpenSubtitles 2018 (ghi nhận OpenSubtitles) và các bảng SUBTLEX của Marc Brysbaert và cộng sự (được phép dùng ngoài nghiên cứu nếu ghi tên).</p>
      <p><a href="https://github.com/rspeer/wordfreq" target="_blank" rel="noopener">github.com/rspeer/wordfreq</a> ·
      <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a> ·
      <a href="https://books.google.com/ngrams" target="_blank" rel="noopener">Google Books Ngram</a></p>
    </article>
    <article class="source">
      <div class="badge">CC BY-SA 4.0</div>
      <h2>NGSL, NAWL, BSL, TSL</h2>
      <p>New General Service List, New Academic Word List, Business Service List và TOEIC Service List của Charles Browne, Brent Culligan và Joseph Phillips. Dùng để gắn từ học thuật và thương mại vào ngành nghề. Giấy phép Creative Commons Ghi công – Chia sẻ tương tự 4.0.</p>
      <p><a href="https://www.newgeneralservicelist.com/" target="_blank" rel="noopener">newgeneralservicelist.com</a> ·
      <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a></p>
    </article>
    <article class="source">
      <div class="badge">CC BY-SA 4.0</div>
      <h2>Trang thuật ngữ Wikipedia và Wiktionary</h2>
      <p>Thuật ngữ nhiều chữ (ví dụ balance sheet, blood pressure) lấy từ các trang Glossary của Wikipedia tiếng Anh và phụ lục thuật ngữ của Wiktionary tiếng Anh. Định nghĩa được rút ngắn. Văn bản theo CC BY-SA.</p>
      <p><a href="https://en.wikipedia.org/wiki/Wikipedia:Glossaries" target="_blank" rel="noopener">Wikipedia glossaries</a> ·
      <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a></p>
    </article>
    <article class="source">
      <div class="badge">Phạm vi công cộng</div>
      <h2>MeSH</h2>
      <p>Medical Subject Headings của Thư viện Y khoa Quốc gia Hoa Kỳ, bản mô tả 2025. Thuật ngữ y, giải phẫu, dược và nha khoa. Tác phẩm của chính phủ Hoa Kỳ, phạm vi công cộng.</p>
      <p><a href="https://www.nlm.nih.gov/mesh/" target="_blank" rel="noopener">nlm.nih.gov/mesh</a></p>
    </article>
    <article class="source">
      <div class="badge">CC BY 4.0</div>
      <h2>Open English WordNet</h2>
      <p>Phân loại chủ đề bằng quan hệ thượng vị (hypernym) của Open English WordNet 2024, dự án Global WordNet, kế thừa Princeton WordNet. Giấy phép Creative Commons Ghi công 4.0.</p>
      <p><a href="https://github.com/globalwordnet/english-wordnet" target="_blank" rel="noopener">english-wordnet</a> ·
      <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a></p>
    </article>
    <article class="source">
      <div class="badge">CC BY 4.0</div>
      <h2>Open English WordNet, phần giải nghĩa</h2>
      <p>Từ không có nghĩa tiếng Việt vẫn được giữ, kèm một câu giải nghĩa tiếng Anh ngắn lấy từ định nghĩa synset của Open English WordNet. Thẻ đó có nhãn EN và dòng “Giải nghĩa tiếng Anh”.</p>
      <p><a href="https://github.com/globalwordnet/english-wordnet" target="_blank" rel="noopener">english-wordnet</a> ·
      <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a></p>
    </article>
    <article class="source">
      <div class="badge">MIT</div>
      <h2>Microsoft Fluent Emoji</h2>
      <p>Sticker 3D. Bản commit 1ffb34c. Tải lúc xem thẻ từ jsDelivr, không lưu file ảnh trong repo.</p>
      <p><a href="https://github.com/microsoft/fluentui-emoji" target="_blank" rel="noopener">fluentui-emoji</a> ·
      <a href="https://opensource.org/license/mit" target="_blank" rel="noopener">MIT</a></p>
    </article>
    <article class="source">
      <div class="badge">CC BY 4.0</div>
      <h2>Twemoji</h2>
      <p>Emoji phẳng của Twitter, phiên bản 14.0.2. Hình thuộc CC BY 4.0.</p>
      <p><a href="https://github.com/twitter/twemoji" target="_blank" rel="noopener">twitter/twemoji</a> ·
      <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a></p>
    </article>
    <article class="source">
      <div class="badge">SIL OFL 1.1</div>
      <h2>Google Noto Emoji</h2>
      <p>Emoji trong bộ Noto, thẻ svg v2.047. Giấy phép SIL Open Font License 1.1 (đã đối chiếu README của kho, không phải Apache).</p>
      <p><a href="https://github.com/googlefonts/noto-emoji" target="_blank" rel="noopener">noto-emoji</a> ·
      <a href="https://scripts.sil.org/OFL" target="_blank" rel="noopener">OFL 1.1</a></p>
    </article>
    <article class="source">
      <div class="badge">CC BY-SA 4.0</div>
      <h2>OpenMoji</h2>
      <p>Minh họa trên một số thẻ. Phiên bản 17.0.0. Từng hình ghi tên người vẽ trên nút i của thẻ. Giấy phép Creative Commons Ghi công – Chia sẻ tương tự 4.0.</p>
      <p><a href="https://openmoji.org/" target="_blank" rel="noopener">openmoji.org</a> ·
      <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a></p>
    </article>
    <article class="source">
      <div class="badge">Từng ảnh một giấy phép</div>
      <h2>Wikimedia Commons</h2>
      <p>Ảnh danh từ lấy từ trang Wikipedia tiếng Anh khi trang có ảnh tự do, rồi đối chiếu giấy phép trên Wikimedia Commons. Chỉ giữ ảnh thuộc phạm vi công cộng, CC0, CC BY, CC BY-SA hoặc GFDL. Tên tác giả và giấy phép nằm ở nút i trên thẻ. Ảnh không được lưu trong repo; trình duyệt tải bản thu nhỏ khoảng 320px.</p>
      <p><a href="https://commons.wikimedia.org/" target="_blank" rel="noopener">commons.wikimedia.org</a> ·
      <a href="https://www.wikidata.org/" target="_blank" rel="noopener">Wikidata</a></p>
    </article>
    <p class="note">Nghĩa, IPA, mức C1/C2 và dữ liệu wordfreq là tác phẩm phái sinh, giữ điều kiện chia sẻ tương tự của CC BY-SA 4.0 khi nguồn yêu cầu. Câu Tatoeba giữ CC BY 2.0 FR. Mức A1–B2 cần giữ lời trích CEFR-J. Emoji dự phòng là ký tự Unicode do app chọn, không lấy từ bộ tranh của ứng dụng khác. Mã nguồn ứng dụng tách riêng, xem LICENSE.</p>
  </section>`;
  topmeta.textContent = "Giấy phép và trích dẫn";
}

function monthCells() {
  const today = todayISO();
  const [year, month] = today.split("-").map(Number);
  const first = new Date(Date.UTC(year, month - 1, 1));
  const pad = first.getUTCDay();
  const count = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const cells = [];
  for (let i = 0; i < pad; i += 1) cells.push(`<i class="empty"></i>`);
  for (let day = 1; day <= count; day += 1) {
    const iso = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const row = STATE.log[iso] || {};
    let kind = "";
    if ((row.reviews || 0) >= STREAK_MIN) kind = "studied";
    else if (row.frozen) kind = "frozen";
    else if (iso < today) kind = "missed";
    const todayMark = iso === today ? " today" : "";
    cells.push(`<i class="${kind}${todayMark}" title="${iso}">${day}</i>`);
  }
  return cells.join("");
}

function medalCards() {
  const values = medalValues(progressSnapshot());
  const have = new Set(STATE.medals || []);
  return MEDALS.map((medal) => {
    const current = values[medal.kind] || 0;
    const earned = have.has(medal.id) || current >= medal.n;
    const shown = Math.min(current, medal.n);
    const width = medal.n ? Math.min(100, Math.round((shown / medal.n) * 100)) : 0;
    return `<article class="medal${earned ? "" : " locked"}">
      <div class="medal-face" aria-hidden="true"><span>${medal.mark}</span></div>
      <b>${esc(medal.name)}</b>
      <small>${shown}/${medal.n}</small>
      <div class="medal-bar" aria-hidden="true"><span style="width:${width}%"></span></div>
    </article>`;
  }).join("");
}

async function shareApp() {
  const person = currentUser();
  const ref = (person && person.uid) || STATE.localId || "guest";
  const url = shareLink(ref);
  const payload = { title: "FlashFree", text: "Học từ vựng tiếng Anh với FlashFree.", url };
  let shared = false;
  if (navigator.share) {
    try {
      await navigator.share(payload);
      shared = true;
    } catch (error) {
      if (error && error.name === "AbortError") return;
    }
  }
  if (!shared) {
    try {
      await navigator.clipboard.writeText(url);
      shared = true;
      toast("Đã chép liên kết");
    } catch {
      window.prompt("Chép liên kết này:", url);
      return;
    }
  }
  STATE.shared = (STATE.shared || 0) + 1;
  const medals = checkMedals();
  save();
  if (view === "profile") render();
  if (medals.length) celebrate(medals);
}

function paintAvatar() {
  const button = document.querySelector("[data-act='profile']");
  if (!button) return;
  const person = currentUser();
  if (person && person.photo) {
    button.innerHTML = `<img alt="" src="${esc(person.photo)}" referrerpolicy="no-referrer">`;
    return;
  }
  const name = person && person.name ? person.name : "Khách";
  const initial = name.trim().slice(0, 1).toUpperCase() || "K";
  button.innerHTML = `<span>${esc(initial)}</span>`;
}

function renderProfile() {
  const person = currentUser();
  const name = person ? (person.name || "Không tên") : "Khách";
  const email = person && person.email ? person.email : "Chưa đăng nhập";
  const photo = person && person.photo
    ? `<img class="profile-photo" alt="" src="${esc(person.photo)}" referrerpolicy="no-referrer">`
    : `<div class="profile-photo letter" aria-hidden="true">${esc(name.trim().slice(0, 1).toUpperCase() || "K")}</div>`;
  const enabled = accountEnabled();
  const authButton = person
    ? `<button type="button" class="ghost" data-act="logout">Đăng xuất</button>`
    : `<button type="button" class="primary" data-act="sign-in" ${enabled ? "" : "disabled"}>${enabled ? "Đăng nhập bằng Google" : "Chưa bật đăng nhập"}</button>`;
  const streak = streakCount();
  const best = STATE.freeze.best || 0;
  const today = todayISO();
  const todayCount = (STATE.log[today] && STATE.log[today].reviews) || 0;
  main.innerHTML = `<section class="lede profile">
    <div class="who">
      ${photo}
      <div>
        <h1>${esc(name)}</h1>
        <p class="note">${esc(email)}</p>
      </div>
    </div>
    ${authButton}
    <h2 class="section-title">Chuỗi ngày</h2>
    <div class="stats">
      <article class="stat"><div class="k">Hiện tại</div><div class="v">${streak}</div></article>
      <article class="stat"><div class="k">Dài nhất</div><div class="v">${best}</div></article>
    </div>
    <p class="note">Một ngày vào chuỗi khi bạn vuốt hoặc trả lời ít nhất ${STREAK_MIN} thẻ. Hôm nay: ${todayCount}/${STREAK_MIN}. Ngày đóng băng vẫn giữ chuỗi.</p>
    <div class="calhead">${WEEK.map((label) => `<span>${label}</span>`).join("")}</div>
    <div class="cal" aria-label="Lịch tháng này">${monthCells()}</div>
    <p class="legend"><i class="studied"></i> Đủ ${STREAK_MIN} thẻ <i class="frozen"></i> Đóng băng <i class="missed"></i> Chưa đủ</p>
    <h2 class="section-title">Huy chương</h2>
    <div class="medals">${medalCards()}</div>
    <h2 class="section-title">Mời bạn</h2>
    <p class="note">Đã chia sẻ ${STATE.shared || 0} lần. Bạn đã mời ${(STATE.invites || 0)} người đăng nhập.</p>
    <button type="button" class="primary" data-act="share">Chia sẻ FlashFree</button>
    <p class="note">Liên kết có mã của bạn. Trình duyệt nào không mở được bảng chia sẻ thì app chép liên kết.</p>
  </section>`;
  topmeta.textContent = "Hồ sơ";
  paintAvatar();
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

function isMastered(state) {
  if (!state) return false;
  return (state.interval || 0) >= 180 || (state.reps || 0) >= 6;
}

function memoryStrength(state) {
  if (!state || (state.reps || 0) <= 0) return 0;
  if (isMastered(state)) return 5;
  const interval = state.interval || 0;
  const reps = state.reps || 0;
  if (interval >= 30 || reps >= 4) return 4;
  if (interval >= 13 || reps >= 3) return 3;
  if (interval >= 6 || reps >= 2) return 2;
  return 1;
}

function memoryBucket(state) {
  const strength = memoryStrength(state);
  if (strength >= 5) return "known";
  if (strength <= 1) return "learn";
  return "practice";
}

const MINE_ROW = 108;
let mineQuery = "";
let mineFilter = "all";
let mineMenu = "";

function studiedEntries() {
  const rows = [];
  for (const [id, state] of Object.entries(STATE.cards || {})) {
    const card = INDEX.get(id);
    if (!card || !state) continue;
    rows.push({ card, state, bucket: memoryBucket(state), strength: memoryStrength(state) });
  }
  rows.sort((a, b) => a.card.word.localeCompare(b.card.word, "en") || a.card.pos.localeCompare(b.card.pos));
  return rows;
}

function mineVisible(rows) {
  const query = mineQuery.trim().toLowerCase();
  return rows.filter((row) => {
    if (mineFilter !== "all" && row.bucket !== mineFilter) return false;
    if (!query) return true;
    const card = row.card;
    return card.word.toLowerCase().includes(query)
      || String(card.meaning || "").toLowerCase().includes(query)
      || String(card.example || "").toLowerCase().includes(query);
  });
}

function strengthHtml(strength) {
  const bars = [0, 1, 2, 3, 4].map((step) => `<i class="${step < strength ? "on" : ""}"></i>`).join("");
  return `<span class="bars" aria-label="Độ nhớ ${strength} trên 5">${bars}</span>`;
}

function mineThumb(card) {
  const pic = chosenPic(card).pic;
  const src = imageUrl(pic);
  if (!src) {
    const icon = memoryIcon(card);
    return `<span class="mine-fallback">${icon ? esc(icon) : ""}</span>`;
  }
  return `<img class="mine-thumb" alt="" src="${esc(src)}" loading="lazy" decoding="async">`;
}

function paintMineRows() {
  const windowBox = document.getElementById("mine-window");
  const rowsBox = document.getElementById("mine-rows");
  if (!windowBox || !rowsBox || view !== "mine") return;
  const shown = mineVisible(studiedEntries());
  const total = shown.length;
  windowBox.style.height = `${Math.max(total, 1) * MINE_ROW}px`;
  const listTop = windowBox.offsetTop;
  const start = Math.max(0, Math.floor((main.scrollTop - listTop) / MINE_ROW) - 3);
  const count = Math.ceil(main.clientHeight / MINE_ROW) + 8;
  const slice = shown.slice(start, start + count);
  const empty = total ? "" : `<p class="note mine-empty">Chưa có thẻ nào trong nhóm này.</p>`;
  rowsBox.innerHTML = empty + slice.map((row, offset) => {
    const card = row.card;
    const en = card.meaningLang === "en";
    const example = card.example
      ? `<p class="mine-ex"><button type="button" class="tiny" data-act="mine-speak" data-text="${esc(card.example)}" aria-label="Nghe câu">▶</button> ${esc(card.example)}</p>`
      : "";
    const own = card.own ? `<button type="button" data-act="mine-edit" data-id="${esc(card.id)}">Sửa</button><button type="button" data-act="mine-delete" data-id="${esc(card.id)}">Xóa</button>` : "";
    return `<article class="mine-row" style="top:${(start + offset) * MINE_ROW}px">
      ${mineThumb(card)}
      <div class="mine-copy">
        <p class="mine-word"><button type="button" class="tiny" data-act="mine-speak" data-text="${esc(card.word)}" aria-label="Nghe từ">▶</button> ${esc(card.word)} ${en ? `<span class="pill en">EN</span>` : ""}</p>
        ${en ? `<p class="en-label">Giải nghĩa tiếng Anh</p>` : ""}
        <p class="mine-mean">${esc(card.meaning)}</p>
        ${example}
      </div>
      <div class="mine-side">
        ${strengthHtml(row.strength)}
        <button type="button" class="tiny more" data-act="mine-menu" data-id="${esc(card.id)}" aria-label="Việc với thẻ">⋯</button>
        <div class="rowmenu${mineMenu === card.id ? "" : " hidden"}">
          <button type="button" data-act="mine-reset" data-id="${esc(card.id)}">Đặt lại tiến độ</button>
          <button type="button" data-act="mine-retire" data-id="${esc(card.id)}">Đánh dấu đã thuộc</button>
          ${own}
        </div>
      </div>
    </article>`;
  }).join("");
  const countNode = document.getElementById("mine-shown");
  if (countNode) countNode.textContent = `${total.toLocaleString("vi-VN")} thẻ`;
}

function renderMine() {
  const all = studiedEntries();
  const counts = { learn: 0, practice: 0, known: 0 };
  for (const row of all) counts[row.bucket] += 1;
  const filters = [
    ["all", "Tất cả"],
    ["learn", "Cần học"],
    ["practice", "Đang luyện"],
    ["known", "Đã thuộc"],
  ].map(([id, label]) => `<button type="button" class="chip${mineFilter === id ? " on" : ""}" data-act="mine-filter" data-id="${id}">${label}</button>`).join("");
  main.innerHTML = `<section class="mine">
    <div class="mine-head">
      <h1>Thẻ của tôi</h1>
      <button type="button" class="addbtn" data-act="add-word" aria-label="Thêm từ">+</button>
    </div>
    <p class="note">Đã thuộc khi Biết liên tiếp 6 lần, hoặc lịch ôn cách từ 180 ngày — thẻ đó không còn được xếp lịch. Chưa biết đưa thẻ về sớm, theo SM-2.</p>
    <div class="mine-counts">
      <article><b>${counts.learn.toLocaleString("vi-VN")}</b><span>Cần học</span></article>
      <article><b>${counts.practice.toLocaleString("vi-VN")}</b><span>Đang luyện</span></article>
      <article><b>${counts.known.toLocaleString("vi-VN")}</b><span>Đã thuộc</span></article>
    </div>
    <input id="mine-search" type="search" placeholder="Tìm từ hoặc nghĩa" value="${esc(mineQuery)}" autocomplete="off">
    <div class="chips">${filters}</div>
    <div class="mine-tools">
      <span id="mine-shown"></span>
      <button type="button" data-act="mine-export">Tải CSV</button>
    </div>
    <div id="mine-window"><div id="mine-rows"></div></div>
  </section>`;
  topmeta.textContent = `${all.length.toLocaleString("vi-VN")} đã học`;
  paintMineRows();
}

function resetCardProgress(id) {
  delete STATE.cards[id];
  session = null;
  save();
  toast("Đã đặt lại tiến độ");
  renderMine();
}

function retireCard(id) {
  const prev = STATE.cards[id] || { ef: 2.5, reps: 0, interval: 0, lapses: 0, last: null };
  const interval = Math.max(prev.interval || 0, 180);
  STATE.cards[id] = {
    ef: prev.ef || 2.5,
    reps: Math.max(prev.reps || 0, 6),
    interval,
    lapses: prev.lapses || 0,
    due: addDays(todayISO(), interval),
    last: prev.last || todayISO(),
  };
  session = null;
  save();
  toast("Đã đánh dấu thuộc");
  renderMine();
}

function exportMineCsv() {
  const lines = ["word,pos,meaning,meaning_lang,example,level,strength,status"];
  for (const row of mineVisible(studiedEntries())) {
    const card = row.card;
    const cells = [card.word, card.pos || "", card.meaning || "", card.meaningLang || "vi", card.example || "", card.level || "", row.strength, row.bucket];
    lines.push(cells.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","));
  }
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "flashfree-the-cua-toi.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

function render() {
  if (!DATA) return;
  stopAudio();
  hideImageInfo();
  setNav();
  if (view === "study") renderStudy();
  else if (view === "decks") renderDecks();
  else if (view === "stats") renderStats();
  else if (view === "mine") renderMine();
  else if (view === "form") renderForm();
  else if (view === "profile") renderProfile();
  else renderCredits();
  main.scrollTop = 0;
  paintAvatar();
}

function grade(know) {
  if (busy || view !== "study" || studyMode() !== "cards") return;
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
    session.graded.add(item.id);
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
    if (view === "study") renderStudy();
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

async function toggleLevel(id) {
  const selected = new Set(STATE.settings.levels);
  if (selected.has(id)) selected.delete(id);
  else selected.add(id);
  STATE.settings.levels = LEVELS.filter((level) => selected.has(level));
  save();
  session = null;
  try {
    if (selected.has(id)) await ensureLevels([id]);
  } catch {
    toast("Không tải được trình độ này");
  }
  render();
}

function filesForTopics(ids) {
  const sources = DATA && DATA.topicSources ? DATA.topicSources : {};
  const out = [];
  for (const id of ids || []) {
    for (const file of sources[id] || []) {
      if (!out.includes(file)) out.push(file);
    }
  }
  return out;
}

async function ensureTopicFiles(fileIds) {
  const need = [...new Set(fileIds || [])].filter((id) => id && !loadedTopicFiles.has(id));
  if (!need.length) return;
  const parts = await Promise.all(need.map(async (id) => {
    const res = await fetch(`data/fields/${id}.json`);
    if (!res.ok) throw new Error(id);
    return res.json();
  }));
  const have = new Set(DATA.cards.map((card) => card.id));
  need.forEach((id, index) => {
    for (const card of (parts[index] && parts[index].cards) || []) {
      if (have.has(card.id)) continue;
      DATA.cards.push(card);
      have.add(card.id);
    }
    loadedTopicFiles.add(id);
  });
  reindex();
}

function prefetchTopicFiles() {
  const ids = (DATA.topicFiles || []).filter((id) => !loadedTopicFiles.has(id));
  if (!ids.length) return;
  let index = 0;
  const step = () => {
    if (!DATA || index >= ids.length) return;
    const batch = ids.slice(index, index + 3);
    index += batch.length;
    ensureTopicFiles(batch).then(() => {
      const card = document.getElementById("card");
      const flipped = card && card.classList.contains("is-flipped");
      if (view === "study" && session && session.index === 0 && session.done === 0 && !flipped) {
        session = null;
        render();
      }
      window.setTimeout(step, 60);
    }).catch(() => window.setTimeout(step, 200));
  };
  window.setTimeout(step, 800);
}

async function toggleTopic(id) {
  const selected = new Set(STATE.settings.topics);
  if (selected.has(id)) selected.delete(id);
  else selected.add(id);
  STATE.settings.topics = [...selected];
  save();
  session = null;
  if (selected.has(id)) {
    try {
      await ensureTopicFiles(filesForTopics([id]));
    } catch {
      toast("Không tải được chủ đề này");
    }
  }
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
  const theme = STATE.settings.theme || "paper";
  const mode = studyMode();
  const listenRate = STATE.settings.listenRate;
  const listenRepeat = STATE.settings.listenRepeat;
  const picStyle = STATE.settings.picStyle || "auto";
  localStorage.removeItem(KEY);
  STATE = loadState();
  STATE.own = own;
  STATE.settings.autoSpeak = autoSpeak;
  STATE.settings.ownDeck = ownDeck;
  STATE.settings.theme = theme;
  STATE.settings.mode = mode;
  STATE.settings.listenRate = listenRate;
  STATE.settings.listenRepeat = listenRepeat;
  STATE.settings.picStyle = picStyle;
  applyTheme(theme);
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
  if (name === "img-info") {
    event.preventDefault();
    event.stopPropagation();
    showImageInfo();
    return;
  }
  if (name === "close-pop") {
    hideImageInfo();
    return;
  }
  if (name === "mode") {
    const next = act.dataset.id;
    if (!MODES.includes(next) || next === studyMode()) return;
    STATE.settings.mode = next;
    save();
    view = "study";
    render();
    return;
  }
  if (name === "theme") {
    applyTheme(act.dataset.id);
    save();
    render();
    return;
  }
  if (name === "pic-style") {
    if (!PIC_STYLES.includes(act.dataset.id)) return;
    STATE.settings.picStyle = act.dataset.id;
    save();
    render();
    return;
  }
  if (name === "mine-filter") {
    mineFilter = act.dataset.id || "all";
    mineMenu = "";
    renderMine();
    return;
  }
  if (name === "mine-menu") {
    mineMenu = mineMenu === act.dataset.id ? "" : act.dataset.id;
    paintMineRows();
    return;
  }
  if (name === "mine-speak") {
    event.preventDefault();
    event.stopPropagation();
    speak(act.dataset.text || "", false, "en-US");
    return;
  }
  if (name === "mine-reset") {
    resetCardProgress(act.dataset.id);
    return;
  }
  if (name === "mine-retire") {
    retireCard(act.dataset.id);
    return;
  }
  if (name === "mine-edit") {
    openForm(act.dataset.id);
    return;
  }
  if (name === "mine-delete") {
    deleteOwn(act.dataset.id);
    return;
  }
  if (name === "mine-export") {
    exportMineCsv();
    return;
  }
  if (name === "pic-swap") {
    event.preventDefault();
    event.stopPropagation();
    const card = currentCard();
    if (!card) return;
    const list = orderedPics(card);
    if (list.length < 2) return;
    const current = picKey(list[0]);
    const index = list.findIndex((pic) => picKey(pic) === current);
    const next = list[(index + 1) % list.length];
    picPrefs[card.id] = picKey(next);
    savePicPrefs();
    const root = document.getElementById("card") || document.getElementById("listen-card");
    if (!root) return;
    const html = pictureHtml(card);
    const box = root.querySelector(".picbox") || root.querySelector(".memo");
    if (box) box.outerHTML = html;
    else root.insertAdjacentHTML("afterbegin", html);
    bindPicture(root);
    return;
  }
  if (name === "listen-toggle") {
    if (listenRun.playing) pauseListen();
    else startListen();
    return;
  }
  if (name === "listen-next" || name === "listen-prev" || name === "listen-restart") {
    pauseListen();
    if (name === "listen-restart") session.listenIndex = 0;
    else if (name === "listen-next") session.listenIndex += 1;
    else session.listenIndex = Math.max(0, session.listenIndex - 1);
    renderListen();
    return;
  }
  if (name === "listen-rate" || name === "listen-repeat") {
    const value = Number(act.dataset.value);
    if (name === "listen-rate" && RATES.includes(value)) STATE.settings.listenRate = value;
    if (name === "listen-repeat" && REPEATS.includes(value)) STATE.settings.listenRepeat = value;
    save();
    main.querySelectorAll(`[data-act="${name}"]`).forEach((button) => {
      const on = Number(button.dataset.value) === value;
      button.classList.toggle("on", on);
    });
    return;
  }
  if (name === "cloze-choice") {
    const item = currentClozeItem();
    answerCloze(item, act.dataset.word || "");
    return;
  }
  if (name === "cloze-next") {
    const item = currentClozeItem();
    if (item && item.cloze) item.cloze.done = true;
    session.clozeIndex += 1;
    renderCloze();
    return;
  }
  if (name === "know" || name === "miss") {
    if (suppressClick) return;
    grade(name === "know");
  }
  if (name === "profile") {
    view = "profile";
    render();
    return;
  }
  if (name === "sign-in") {
    signInGoogle().then((result) => {
      if (result && result.ok) return;
      if (result && result.reason === "disabled") toast("Chưa bật đăng nhập");
      else if (result && result.reason !== "auth/popup-closed-by-user") toast("Không đăng nhập được");
    });
    return;
  }
  if (name === "logout") {
    signOutGoogle().then(() => {
      toast("Đã đăng xuất. Máy này vẫn học được như khách.");
      view = "profile";
      render();
    });
    return;
  }
  if (name === "share") {
    shareApp();
    return;
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

main.addEventListener("scroll", () => {
  if (view === "mine") paintMineRows();
}, { passive: true });

document.addEventListener("input", (event) => {
  if (event.target.id === "mine-search") {
    mineQuery = event.target.value;
    paintMineRows();
    return;
  }
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

document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!form || form.id !== "cloze-form") return;
  event.preventDefault();
  const item = currentClozeItem();
  answerCloze(item, form.elements.answer.value);
});

document.addEventListener("keydown", (event) => {
  if (view !== "study" || !DATA || studyMode() !== "cards") return;
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

async function ensureLevels(levels) {
  const need = (levels || []).filter((level) => LEVELS.includes(level) && !loadedLevels.has(level));
  if (!need.length) return;
  const parts = await Promise.all(need.map(async (level) => {
    const res = await fetch(`data/level-${level.toLowerCase()}.json`);
    if (!res.ok) throw new Error(level);
    return res.json();
  }));
  need.forEach((level, index) => {
    DATA.cards.push(...((parts[index] && parts[index].cards) || []));
    loadedLevels.add(level);
  });
  reindex();
}

function prefetchLevels() {
  const rest = LEVELS.filter((level) => !loadedLevels.has(level));
  if (!rest.length) return;
  window.setTimeout(() => {
    ensureLevels(rest).catch(() => {});
  }, 700);
}

async function boot() {
  applyTheme(localStorage.getItem(THEME_KEY) || "paper");
  main.innerHTML = `<section class="empty"><h1>Đang mở bộ thẻ…</h1><p>Một lát thôi.</p></section>`;
  topmeta.textContent = "";
  try {
    loadPicPrefs();
    const [metaRes, iconRes, emojiRes] = await Promise.all([
      fetch("data/meta.json"),
      fetch("data/icons.json").catch(() => null),
      fetch("data/emoji-index.json").catch(() => null),
    ]);
    if (!metaRes.ok) throw new Error("bad status");
    DATA = await metaRes.json();
    DATA.cards = [];
    ICONS = iconRes && iconRes.ok ? await iconRes.json() : {};
    EMOJI_INDEX = emojiRes && emojiRes.ok ? await emojiRes.json() : {};
    STATE = loadState();
    try {
      const ref = new URLSearchParams(location.search).get("ref");
      if (ref) sessionStorage.setItem("latu-ref", ref);
    } catch { /* ignore */ }
    applyTheme(STATE.settings.theme);
    bindAccount({
      snapshot() {
        return {
          settings: STATE.settings,
          cards: STATE.cards,
          introduced: STATE.introduced,
          log: STATE.log,
          own: STATE.own,
          xp: STATE.xp || 0,
          medals: STATE.medals || [],
          freeze: STATE.freeze,
          shared: STATE.shared || 0,
          invites: STATE.invites || 0,
          localId: STATE.localId,
          picPrefs,
          updatedAt: STATE.updatedAt || 0,
        };
      },
      today: todayISO,
      apply(next) {
        const settings = { ...STATE.settings, ...(next.settings || {}) };
        settings.levels = (settings.levels || []).filter((level) => LEVELS.includes(level));
        if (!THEMES[settings.theme]) settings.theme = "paper";
        STATE.settings = settings;
        STATE.cards = next.cards || {};
        STATE.introduced = next.introduced || {};
        STATE.log = next.log || {};
        STATE.own = cleanOwn(next.own);
        STATE.xp = next.xp || 0;
        STATE.medals = Array.isArray(next.medals) ? next.medals : [];
        STATE.freeze = next.freeze || STATE.freeze;
        STATE.shared = next.shared || 0;
        STATE.invites = next.invites || 0;
        STATE.localId = next.localId || STATE.localId;
        picPrefs = next.picPrefs || {};
        savePicPrefs();
        applyStreakFromLog(STATE);
        applyTheme(settings.theme);
        reindex();
        session = null;
        save({ sync: false });
        render();
      },
      onUser() {
        paintAvatar();
        if (view === "profile") render();
      },
      setInvites(count) {
        if ((STATE.invites || 0) >= count) return;
        STATE.invites = count;
        const medals = checkMedals();
        save();
        if (medals.length) celebrate(medals);
        if (view === "profile") render();
      },
    });
    const known = new Set((DATA.topics || []).map((topic) => topic.id));
    STATE.settings.topics = migrateTopics(STATE.settings.topics).filter((id) => known.has(id));
    const initial = STATE.settings.levels.length ? STATE.settings.levels : ["B1", "B2"];
    await ensureLevels(initial);
    try {
      await ensureTopicFiles(filesForTopics(STATE.settings.topics));
    } catch { /* a field file can load later */ }
    const changed = reconcileFreezes();
    const fresh = checkMedals();
    if (changed || fresh.length) save();
    if (window.speechSynthesis) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.addEventListener("voiceschanged", () => window.speechSynthesis.getVoices());
    }
    render();
    if (fresh.length) celebrate(fresh);
    prefetchLevels();
    prefetchTopicFiles();
  } catch {
    main.innerHTML = errorHtml();
    topmeta.textContent = "";
  }
}

boot();
