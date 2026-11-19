/* Turn a Gemini JSON string into a safe card. No HTML, no extra fields. */

const POS = new Set([
  "noun", "verb", "adj", "adv", "pron", "prep", "det", "conj", "num", "intj", "phrase",
]);
const LEVELS = new Set(["A1", "A2", "B1", "B2", "C1", "C2"]);

export function stripHtml(value) {
  return String(value || "")
    .replace(/<[^>]*>/g, "")
    .replace(/[<>]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function clip(value, max) {
  const text = stripHtml(value);
  return text.length > max ? text.slice(0, max).trim() : text;
}

export function cleanEmoji(value) {
  const text = String(value || "").trim();
  if (!text || /[<>A-Za-z0-9]/.test(text)) return "";
  const chars = [...text];
  if (chars.length > 8) return "";
  return text;
}

export function parseAiJson(raw, word) {
  let data;
  try {
    const text = String(raw || "").trim().replace(/^```(?:json)?/i, "").replace(/```$/i, "").trim();
    data = JSON.parse(text);
  } catch {
    return null;
  }
  if (!data || typeof data !== "object" || Array.isArray(data)) return null;
  const meaning = clip(data.meaning, 180);
  if (!meaning) return null;
  const examples = [];
  const list = Array.isArray(data.examples) ? data.examples : [];
  for (const item of list) {
    if (!item || typeof item !== "object") continue;
    const en = clip(item.en, 160);
    const vi = clip(item.vi, 160);
    if (!en || !vi) continue;
    examples.push({ en, vi });
    if (examples.length === 2) break;
  }
  const head = clip(word || data.word, 80);
  if (!head) return null;
  return {
    word: head,
    pos: POS.has(data.pos) ? data.pos : "",
    ipa: clip(String(data.ipa || "").replace(/[^0-9A-Za-zˈˌ.ːˑ\sæɑɒɔəɛɪʊʌθðʃʒŋɡ]/g, ""), 40),
    meaning,
    explain: clip(data.explain, 280),
    level: LEVELS.has(data.level) ? data.level : "",
    examples,
    emoji: cleanEmoji(data.emoji),
  };
}
