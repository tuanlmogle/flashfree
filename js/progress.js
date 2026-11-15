/* Pure progress helpers: streak rule, medal counts, and cloud merge.
   No DOM and no Firebase, so node can test this file directly. */

export const STREAK_MIN = 20;
export const LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];
export const NEW_LIMITS = [5, 10, 15, 20, 30, 50];
export const DEFAULT_NEW = 15;
export const EXTRA_STEP = 5;
export const LEVEL_UNLOCK = 0.8;

export function normalizeNewPerDay(value) {
  const n = Number(value);
  if (NEW_LIMITS.includes(n)) return n;
  if (!Number.isFinite(n) || n <= 0) return DEFAULT_NEW;
  let best = DEFAULT_NEW;
  let dist = Infinity;
  for (const option of NEW_LIMITS) {
    const gap = Math.abs(option - n);
    if (gap < dist || (gap === dist && option > best)) {
      dist = gap;
      best = option;
    }
  }
  return best;
}

export function extraToday(extra, today) {
  if (!extra || extra.day !== today) return 0;
  const n = Number(extra.n) || 0;
  return n > 0 ? n : 0;
}

export function newCap(limit, extraCount) {
  return normalizeNewPerDay(limit) + Math.max(0, Number(extraCount) || 0);
}

export function slotsLeft(introduced, cap) {
  return Math.max(0, cap - Math.max(0, Number(introduced) || 0));
}

export function mergeExtra(left, right, today) {
  return { day: today || "", n: Math.max(extraToday(left, today), extraToday(right, today)) };
}

/** Highest selected level at 80% seen unlocks the next one. No auto-switch. */
export function unlockTarget(levels, stats) {
  const selected = LEVELS.filter((level) => (levels || []).includes(level));
  const current = selected[selected.length - 1];
  if (!current) return null;
  const next = LEVELS[LEVELS.indexOf(current) + 1];
  if (!next || (levels || []).includes(next)) return null;
  const row = (stats && stats[current]) || { seen: 0, total: 0 };
  const total = Number(row.total) || 0;
  const seen = Number(row.seen) || 0;
  if (total < 1 || seen / total < LEVEL_UNLOCK) return null;
  return { current, next, seen, total };
}
export const SITE_ORIGIN = "https://tuanlmogle.github.io/flashfree/";

export function addDays(iso, amount) {
  const [year, month, day] = String(iso).split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  date.setUTCDate(date.getUTCDate() + amount);
  return date.toISOString().slice(0, 10);
}

export function qualifies(row) {
  if (!row) return false;
  return (row.reviews || 0) >= STREAK_MIN || !!row.frozen;
}

export function earliestStudyDay(log) {
  let earliest = "";
  for (const [day, row] of Object.entries(log || {})) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) continue;
    if (!(row && row.reviews > 0)) continue;
    if (!earliest || day < earliest) earliest = day;
  }
  return earliest;
}

/** studied | frozen | missed | "" (neutral: before the first study day, today still open, or a future day). */
export function calendarKind(iso, today, firstStudy, row) {
  const reviews = (row && row.reviews) || 0;
  if (!iso || iso > today || !firstStudy || iso < firstStudy) return "";
  if (reviews >= STREAK_MIN) return "studied";
  if (row && row.frozen) return "frozen";
  if (iso < today) return "missed";
  return "";
}

export function streakFromLog(log, today) {
  const book = log && typeof log === "object" ? log : {};
  let day = today;
  if (!qualifies(book[day])) day = addDays(today, -1);
  let streak = 0;
  let last = null;
  let guard = 0;
  while (qualifies(book[day]) && guard < 5000) {
    streak += 1;
    if (!last) last = day;
    day = addDays(day, -1);
    guard += 1;
  }
  return { streak, last, best: bestStreak(book, today) };
}

export function bestStreak(log, today) {
  const book = log && typeof log === "object" ? log : {};
  const days = Object.keys(book).filter((day) => /^\d{4}-\d{2}-\d{2}$/.test(day) && day <= today).sort();
  if (!days.length) return 0;
  let best = 0;
  let run = 0;
  let day = days[0];
  let guard = 0;
  while (day <= today && guard < 5000) {
    const openToday = day === today && !qualifies(book[day]);
    if (openToday) break;
    if (qualifies(book[day])) {
      run += 1;
      if (run > best) best = run;
    } else {
      run = 0;
    }
    day = addDays(day, 1);
    guard += 1;
  }
  return best;
}

export function isMastered(state) {
  if (!state) return false;
  return (state.interval || 0) >= 180 || (state.reps || 0) >= 6;
}

export function learnedCount(cards) {
  let count = 0;
  for (const state of Object.values(cards || {})) {
    if (state && state.reps >= 1) count += 1;
  }
  return count;
}

export function masteredCount(cards) {
  let count = 0;
  for (const state of Object.values(cards || {})) {
    if (isMastered(state)) count += 1;
  }
  return count;
}

export function maxDayReviews(log) {
  let max = 0;
  for (const row of Object.values(log || {})) max = Math.max(max, row.reviews || 0);
  return max;
}

export function perfectDays(log) {
  let count = 0;
  for (const row of Object.values(log || {})) {
    const reviews = row.reviews || 0;
    if (reviews >= STREAK_MIN && (row.correct || 0) >= reviews) count += 1;
  }
  return count;
}

export function medalValues(snapshot) {
  const cards = snapshot.cards || {};
  const log = snapshot.log || {};
  return {
    streak: snapshot.streak || 0,
    words: learnedCount(cards),
    day: maxDayReviews(log),
    own: snapshot.ownCount || 0,
    perfect: perfectDays(log),
    mastered: masteredCount(cards),
    share: snapshot.shared || 0,
    invite: snapshot.invites || 0,
  };
}

function cardRank(state) {
  if (!state) return ["", -1, -1, -1];
  return [state.last || "", state.reps || 0, state.interval || 0, state.ef || 0];
}

export function mergeCardState(local, cloud) {
  if (!local) return cloud ? { ...cloud } : null;
  if (!cloud) return { ...local };
  const left = cardRank(local);
  const right = cardRank(cloud);
  for (let i = 0; i < left.length; i += 1) {
    if (left[i] === right[i]) continue;
    return { ...(left[i] > right[i] ? local : cloud) };
  }
  return { ...local };
}

export function chunkId(cardId, buckets = 32) {
  let value = 2166136261;
  const text = String(cardId || "");
  for (let i = 0; i < text.length; i += 1) {
    value = Math.imul(value ^ text.charCodeAt(i), 16777619);
  }
  return `p${(value >>> 0) % buckets}`;
}

export function chunkMap(map, buckets = 32) {
  const chunks = {};
  for (const [id, value] of Object.entries(map || {})) {
    const key = chunkId(id, buckets);
    if (!chunks[key]) chunks[key] = {};
    chunks[key][id] = value;
  }
  return chunks;
}

export function unchunkMap(chunks) {
  const map = {};
  for (const chunk of Object.values(chunks || {})) {
    if (!chunk || typeof chunk !== "object") continue;
    Object.assign(map, chunk);
  }
  return map;
}

function mergeLog(local, cloud) {
  const log = {};
  const days = new Set([...Object.keys(local || {}), ...Object.keys(cloud || {})]);
  for (const day of days) {
    const a = (local && local[day]) || {};
    const b = (cloud && cloud[day]) || {};
    log[day] = {
      reviews: Math.max(a.reviews || 0, b.reviews || 0),
      correct: Math.max(a.correct || 0, b.correct || 0),
      added: Math.max(a.added || 0, b.added || 0),
    };
    if (a.frozen || b.frozen) log[day].frozen = true;
  }
  return log;
}

function mergeOwn(local, cloud) {
  const map = new Map();
  for (const item of cloud || []) {
    if (item && item.id) map.set(item.id, item);
  }
  for (const item of local || []) {
    if (item && item.id) map.set(item.id, item);
  }
  return [...map.values()];
}

function mergeIntroduced(local, cloud) {
  const out = {};
  for (const source of [cloud || {}, local || {}]) {
    for (const [day, ids] of Object.entries(source)) {
      const prev = out[day] || [];
      out[day] = [...new Set([...prev, ...(Array.isArray(ids) ? ids : [])])];
    }
  }
  return out;
}

function mergePrefs(local, cloud, localWins) {
  const older = localWins ? cloud : local;
  const newer = localWins ? local : cloud;
  return { ...(older || {}), ...(newer || {}) };
}

export function mergeStates(local, cloud, today) {
  const left = local || {};
  const right = cloud || {};
  const localWins = (left.updatedAt || 0) >= (right.updatedAt || 0);
  const newer = localWins ? left : right;
  const log = mergeLog(left.log, right.log);
  const cards = { ...(right.cards || {}) };
  for (const [id, state] of Object.entries(left.cards || {})) {
    cards[id] = mergeCardState(state, cards[id]);
  }
  const streak = streakFromLog(log, today);
  const freeze = {
    bank: Math.min(2, Math.max((left.freeze && left.freeze.bank) || 0, (right.freeze && right.freeze.bank) || 0)),
    progress: (newer.freeze && newer.freeze.progress) || 0,
    streak: streak.streak,
    last: streak.last,
    best: Math.max(
      (left.freeze && left.freeze.best) || 0,
      (right.freeze && right.freeze.best) || 0,
      streak.best,
    ),
    rule: STREAK_MIN,
  };
  return {
    settings: { ...(left.settings || {}), ...(right.settings || {}), ...(newer.settings || {}) },
    cards,
    introduced: mergeIntroduced(left.introduced, right.introduced),
    log,
    own: mergeOwn(left.own, right.own),
    xp: Math.max(left.xp || 0, right.xp || 0),
    medals: [...new Set([...(left.medals || []), ...(right.medals || [])])],
    freeze,
    shared: Math.max(left.shared || 0, right.shared || 0),
    invites: Math.max(left.invites || 0, right.invites || 0),
    localId: left.localId || right.localId || "",
    firstStudy: [left.firstStudy, right.firstStudy, earliestStudyDay(log)].filter(Boolean).sort()[0] || "",
    extraNew: mergeExtra(left.extraNew, right.extraNew, today),
    picPrefs: mergePrefs(left.picPrefs, right.picPrefs, localWins),
    updatedAt: Date.now(),
  };
}

export function shareLink(ref) {
  const id = encodeURIComponent(ref || "guest");
  return `${SITE_ORIGIN}?ref=${id}`;
}
