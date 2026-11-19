/* Ask Gemini for a learner card. The SDK loads only when a signed-in user asks.
   Results stay in localStorage and, when signed in, under users/{uid}/ai. */

import { currentUser, ensureFirebaseApp, firebaseCdn, saveAiNote } from "./account.js";
import { parseAiJson } from "./ai-text.js";

export const GEMINI_MODEL = "gemini-2.5-flash-lite";
export const AI_LIMIT = 30;
const CACHE_KEY = "latu-ai-v1";
const QUOTA_KEY = "latu-ai-day";

export const AI_MESSAGES = {
  "signed-out": "Đăng nhập bằng Google để nhờ AI viết nghĩa và ví dụ.",
  limit: "Hôm nay đã nhờ AI đủ 30 từ. Mai thử lại nhé.",
  offline: "Không có mạng. Hãy thử lại khi có mạng.",
  unavailable: "Chưa bật AI Logic trên Firebase, hoặc dịch vụ chưa trả lời. Bạn vẫn học được như thường.",
  bad: "AI chưa viết được cho từ này. Bạn có thể tự điền.",
};

export function normWord(word) {
  return String(word || "").trim().toLowerCase().replace(/\s+/g, " ").slice(0, 80);
}

export function aiSlug(word) {
  const slug = normWord(word).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return (slug || "word").slice(0, 60);
}

function todayISO() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

export function readAiCache() {
  try {
    const parsed = JSON.parse(localStorage.getItem(CACHE_KEY) || "{}");
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function writeAiCache(cache) {
  try { localStorage.setItem(CACHE_KEY, JSON.stringify(cache)); } catch { /* full */ }
}

export function getAiNote(word) {
  return readAiCache()[normWord(word)] || null;
}

export function rememberAiNote(note) {
  if (!note || !note.word) return;
  const cache = readAiCache();
  cache[normWord(note.word)] = note;
  writeAiCache(cache);
}

export function mergeRemoteNotes(notes) {
  const cache = readAiCache();
  for (const note of notes || []) {
    if (!note || !note.word || !note.meaning) continue;
    const key = normWord(note.word);
    const prev = cache[key];
    if (!prev || (note.at || 0) >= (prev.at || 0)) cache[key] = note;
  }
  writeAiCache(cache);
}

function quotaLeft() {
  try {
    const raw = JSON.parse(localStorage.getItem(QUOTA_KEY) || "{}");
    if (!raw || raw.day !== todayISO()) return AI_LIMIT;
    return Math.max(0, AI_LIMIT - (Number(raw.n) || 0));
  } catch {
    return AI_LIMIT;
  }
}

function bumpQuota() {
  let n = 1;
  try {
    const raw = JSON.parse(localStorage.getItem(QUOTA_KEY) || "{}");
    if (raw && raw.day === todayISO()) n = (Number(raw.n) || 0) + 1;
  } catch { /* start at 1 */ }
  try { localStorage.setItem(QUOTA_KEY, JSON.stringify({ day: todayISO(), n })); } catch { /* ignore */ }
}

function promptFor(word) {
  return [
    "Write a learner card for a Vietnamese speaker learning American English.",
    "Return only JSON with keys:",
    "pos (noun, verb, adj, adv, pron, prep, det, conj, num, intj, or phrase),",
    "ipa (IPA without slashes, or empty),",
    "meaning (a short Vietnamese gloss, no HTML),",
    "explain (one or two Vietnamese sentences on how Americans actually use the word, including slang or informal notes when they matter),",
    "level (A1, A2, B1, B2, C1, or C2),",
    "examples (exactly 2 items of {en, vi}: natural everyday English and a Vietnamese translation),",
    "emoji (one emoji that pictures the word).",
    `Word: ${JSON.stringify(word)}`,
  ].join("\n");
}

export async function writeWithAi(word) {
  const clean = String(word || "").trim().replace(/\s+/g, " ").slice(0, 80);
  const key = normWord(clean);
  if (!key) return { ok: false, reason: "bad" };
  const cached = readAiCache()[key];
  if (cached && cached.meaning) return { ok: true, note: cached, cached: true };
  if (!currentUser()) return { ok: false, reason: "signed-out" };
  if (typeof navigator !== "undefined" && navigator.onLine === false) return { ok: false, reason: "offline" };
  if (quotaLeft() <= 0) return { ok: false, reason: "limit" };
  let raw = "";
  try {
    const app = await ensureFirebaseApp();
    if (!app) return { ok: false, reason: "unavailable" };
    const { getAI, getGenerativeModel, GoogleAIBackend } = await import(`${firebaseCdn()}/firebase-ai.js`);
    const ai = getAI(app, { backend: new GoogleAIBackend() });
    const model = getGenerativeModel(ai, {
      model: GEMINI_MODEL,
      generationConfig: { responseMimeType: "application/json", temperature: 0.4 },
    });
    const result = await model.generateContent(promptFor(clean));
    raw = result.response.text();
  } catch (error) {
    const message = String((error && (error.code || error.message)) || "");
    if (/network|offline|failed to fetch|unavailable/i.test(message)) return { ok: false, reason: "offline" };
    return { ok: false, reason: "unavailable" };
  }
  const note = parseAiJson(raw, clean);
  if (!note) return { ok: false, reason: "bad" };
  note.at = Date.now();
  rememberAiNote(note);
  bumpQuota();
  try { await saveAiNote(aiSlug(clean), note); } catch { /* the phone copy is enough until the next sign-in */ }
  return { ok: true, note };
}

export async function saveEditedNote(note) {
  if (!note || !note.word || !note.meaning) return;
  const next = { ...note, at: Date.now() };
  rememberAiNote(next);
  if (!currentUser()) return;
  try { await saveAiNote(aiSlug(next.word), next); } catch { /* local copy remains */ }
}
