import assert from "node:assert/strict";
import test from "node:test";

import { firebaseReady } from "../js/firebase-config.js";
import {
  STREAK_MIN,
  calendarKind,
  earliestStudyDay,
  chunkMap,
  masteredCount,
  medalValues,
  mergeCardState,
  mergeStates,
  perfectDays,
  qualifies,
  shareLink,
  streakFromLog,
  unchunkMap,
} from "../js/progress.js";

test("an empty Firebase config stays guest-only", () => {
  assert.equal(firebaseReady({ apiKey: "", authDomain: "", projectId: "", appId: "" }), false);
  assert.equal(firebaseReady({ apiKey: "YOUR_API_KEY", authDomain: "x.firebaseapp.com", projectId: "demo", appId: "1:2:web:abcdef" }), false);
});

test("calendar stays neutral before the first study day and in the future", () => {
  assert.equal(earliestStudyDay({}), "");
  assert.equal(earliestStudyDay({ "2026-11-10": { reviews: 3 } }), "2026-11-10");
  assert.equal(calendarKind("2026-11-09", "2026-11-14", "2026-11-10", {}), "");
  assert.equal(calendarKind("2026-11-10", "2026-11-14", "2026-11-10", { reviews: 4 }), "missed");
  assert.equal(calendarKind("2026-11-11", "2026-11-14", "2026-11-10", { reviews: 20 }), "studied");
  assert.equal(calendarKind("2026-11-12", "2026-11-14", "2026-11-10", { reviews: 0, frozen: true }), "frozen");
  assert.equal(calendarKind("2026-11-14", "2026-11-14", "2026-11-10", { reviews: 2 }), "");
  assert.equal(calendarKind("2026-11-20", "2026-11-14", "2026-11-10", {}), "");
  assert.equal(calendarKind("2026-11-01", "2026-11-14", "", {}), "");
});

test("a day counts only at the 20-card line", () => {
  assert.equal(STREAK_MIN, 20);
  assert.equal(qualifies({ reviews: 19 }), false);
  assert.equal(qualifies({ reviews: 20 }), true);
  assert.equal(qualifies({ reviews: 0, frozen: true }), true);
  assert.equal(qualifies(undefined), false);
});

test("streak keeps earlier days and does not break on an unfinished today", () => {
  const log = {
    "2026-11-12": { reviews: 20, correct: 20 },
    "2026-11-13": { reviews: 22, correct: 10 },
    "2026-11-14": { reviews: 19, correct: 19 },
  };
  const streak = streakFromLog(log, "2026-11-14");
  assert.equal(streak.streak, 2);
  assert.equal(streak.last, "2026-11-13");
  assert.equal(streak.best, 2);
});

test("a missed day breaks the streak unless it was frozen", () => {
  const broken = streakFromLog({
    "2026-11-12": { reviews: 20, correct: 20 },
    "2026-11-14": { reviews: 20, correct: 20 },
  }, "2026-11-14");
  assert.equal(broken.streak, 1);
  assert.equal(broken.best, 1);

  const frozen = streakFromLog({
    "2026-11-12": { reviews: 20, correct: 20 },
    "2026-11-13": { reviews: 3, correct: 1, frozen: true },
    "2026-11-14": { reviews: 20, correct: 20 },
  }, "2026-11-14");
  assert.equal(frozen.streak, 3);
  assert.equal(frozen.best, 3);
});

test("best streak remembers a longer run than the current one", () => {
  const log = {
    "2026-11-01": { reviews: 20, correct: 20 },
    "2026-11-02": { reviews: 21, correct: 21 },
    "2026-11-03": { reviews: 25, correct: 25 },
    "2026-11-10": { reviews: 20, correct: 10 },
  };
  const streak = streakFromLog(log, "2026-11-14");
  assert.equal(streak.streak, 0);
  assert.equal(streak.best, 3);
});

test("merge keeps the card reviewed later, then the more advanced one", () => {
  const later = mergeCardState(
    { reps: 1, interval: 1, last: "2026-11-14", ef: 2.5 },
    { reps: 8, interval: 180, last: "2026-11-01", ef: 2.6 },
  );
  assert.equal(later.last, "2026-11-14");
  assert.equal(later.reps, 1);

  const advanced = mergeCardState(
    { reps: 2, interval: 6, last: "2026-11-10", ef: 2.5 },
    { reps: 6, interval: 30, last: "2026-11-10", ef: 2.3 },
  );
  assert.equal(advanced.reps, 6);
  assert.equal(advanced.interval, 30);
});

test("merge unions words, medals, and log counts, and recomputes the streak", () => {
  const local = {
    updatedAt: 10,
    settings: { theme: "dark", levels: ["B1"] },
    cards: { a: { reps: 1, interval: 1, last: "2026-11-14", ef: 2.5 } },
    log: { "2026-11-14": { reviews: 20, correct: 18, added: 0 } },
    own: [{ id: "o1", word: "bánh", meaning: "cake" }],
    medals: ["streak-3"],
    xp: 40,
    shared: 1,
    invites: 0,
    freeze: { bank: 1, progress: 2, streak: 9, best: 9 },
    picPrefs: { a: "f:1" },
    localId: "g_local",
  };
  const cloud = {
    updatedAt: 50,
    settings: { theme: "sea", levels: ["B2"] },
    cards: { a: { reps: 4, interval: 12, last: "2026-11-13", ef: 2.6 }, b: { reps: 2, interval: 3, last: "2026-11-12", ef: 2.5 } },
    log: { "2026-11-13": { reviews: 20, correct: 20, added: 1 }, "2026-11-14": { reviews: 4, correct: 4, added: 0 } },
    own: [{ id: "o2", word: "trà", meaning: "tea" }],
    medals: ["words-50"],
    xp: 12,
    shared: 2,
    invites: 1,
    freeze: { bank: 0, progress: 0, streak: 1, best: 4 },
    picPrefs: { b: "o:2" },
    localId: "g_cloud",
  };
  const merged = mergeStates(local, cloud, "2026-11-14");
  assert.equal(merged.cards.a.last, "2026-11-14");
  assert.equal(merged.cards.b.reps, 2);
  assert.equal(merged.log["2026-11-14"].reviews, 20);
  assert.equal(merged.log["2026-11-13"].correct, 20);
  assert.deepEqual(merged.own.map((item) => item.id).sort(), ["o1", "o2"]);
  assert.deepEqual(merged.medals.sort(), ["streak-3", "words-50"]);
  assert.equal(merged.xp, 40);
  assert.equal(merged.shared, 2);
  assert.equal(merged.invites, 1);
  assert.equal(merged.settings.theme, "sea");
  assert.equal(merged.picPrefs.b, "o:2");
  assert.equal(merged.freeze.streak, 2);
  assert.equal(merged.freeze.bank, 1);
  assert.equal(merged.localId, "g_local");
});

test("progress chunks round-trip and stay separate", () => {
  const cards = {};
  for (let i = 0; i < 40; i += 1) cards[`word-${i}-noun`] = { reps: i, interval: 1, last: "2026-11-01" };
  const chunks = chunkMap(cards);
  assert.ok(Object.keys(chunks).length > 1);
  for (const chunk of Object.values(chunks)) {
    assert.ok(JSON.stringify(chunk).length < 1_000_000);
  }
  assert.deepEqual(unchunkMap(chunks), cards);
});

test("medal counters see a perfect day, a mastered card, and shares", () => {
  const values = medalValues({
    streak: 10,
    cards: {
      a: { reps: 6, interval: 10 },
      b: { reps: 1, interval: 1 },
    },
    log: {
      "2026-11-01": { reviews: 100, correct: 100 },
      "2026-11-02": { reviews: 20, correct: 19 },
    },
    ownCount: 1,
    shared: 2,
    invites: 2,
  });
  assert.equal(values.day, 100);
  assert.equal(values.words, 2);
  assert.equal(values.mastered, 1);
  assert.equal(values.perfect, 1);
  assert.equal(perfectDays({ "2026-11-02": { reviews: 19, correct: 19 } }), 0);
  assert.equal(masteredCount({ a: { reps: 1, interval: 200 } }), 1);
  assert.equal(values.share, 2);
  assert.equal(values.invite, 2);
  assert.equal(shareLink("abc"), "https://tuanlmogle.github.io/flashfree/?ref=abc");
});
