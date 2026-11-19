import assert from "node:assert/strict";
import test from "node:test";
import { cleanEmoji, parseAiJson, stripHtml } from "../js/ai-text.js";

const sample = `
\`\`\`json
{
  "pos": "phrase",
  "ipa": "hæŋ aʊt",
  "meaning": "<b>đi chơi</b>, dành thời gian với bạn",
  "explain": "Người Mỹ nói hang out khi rủ bạn gặp cho vui, không phải họp.",
  "level": "A2",
  "examples": [
    {"en": "We hang out after school.", "vi": "Tan học tụi mình đi chơi."},
    {"en": "Want to hang out?", "vi": "Đi chơi không?"}
  ],
  "emoji": "👋",
  "html": "<script>alert(1)</script>"
}
\`\`\`
`;

test("parse keeps a safe card and drops HTML", () => {
  const note = parseAiJson(sample, "hang out");
  assert.ok(note);
  assert.equal(note.word, "hang out");
  assert.equal(note.pos, "phrase");
  assert.equal(note.level, "A2");
  assert.equal(note.meaning, "đi chơi, dành thời gian với bạn");
  assert.equal(note.meaning.includes("<"), false);
  assert.equal(note.examples.length, 2);
  assert.equal(note.examples[0].en, "We hang out after school.");
  assert.equal(note.emoji, "👋");
  assert.equal("html" in note, false);
});

test("parse rejects a card with no Vietnamese meaning", () => {
  assert.equal(parseAiJson('{"meaning":"   ","examples":[]}', "x"), null);
  assert.equal(parseAiJson("not json", "x"), null);
});

test("emoji and html helpers stay strict", () => {
  assert.equal(cleanEmoji("👋"), "👋");
  assert.equal(cleanEmoji("<img>"), "");
  assert.equal(cleanEmoji("apple"), "");
  assert.equal(stripHtml("<b>xin chào</b>"), "xin chào");
});
