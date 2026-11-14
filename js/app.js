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

const main = document.getElementById("main");
const topmeta = document.getElementById("topmeta");
let DATA = null;
let INDEX = new Map();
let STATE = null;
let view = "study";
let session = null;
let busy = false;
let drag = null;
let suppressClick = false;
let toastTimer = 0;

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
    settings: { newPerDay: 10, levels: ["B1", "B2"], topics: [] },
    cards: {},
    introduced: {},
    log: {},
  };
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
    return {
      settings,
      cards: parsed.cards || {},
      introduced: parsed.introduced || {},
      log: parsed.log || {},
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

function topicName(id) {
  const found = (DATA.topics || []).find((topic) => topic.id === id);
  return found ? found.name : id;
}

function inDeck(card) {
  const settings = STATE.settings;
  if (!settings.levels.includes(card.level)) return false;
  if (!settings.topics.length) return true;
  return (card.topics || []).some((id) => settings.topics.includes(id));
}

function sessionKey() {
  const settings = STATE.settings;
  const topics = settings.topics.length ? settings.topics.slice().sort().join(",") : "*";
  return `${todayISO()}|${settings.newPerDay}|${settings.levels.join(",")}|${topics}`;
}

function planToday(today) {
  const due = [];
  const unseen = [];
  for (const card of DATA.cards) {
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
  unseen.sort((a, b) => LEVELS.indexOf(a.level) - LEVELS.indexOf(b.level) || hash(a.id) - hash(b.id));

  const kept = (STATE.introduced[today] || []).filter((id) => {
    const card = INDEX.get(id);
    if (!card || !inDeck(card)) return false;
    const state = STATE.cards[id];
    return !state || state.last === today;
  });
  const keptSet = new Set(kept);
  let room = Math.max(0, STATE.settings.newPerDay - kept.length);
  const added = [];
  for (const card of unseen) {
    if (room <= 0) break;
    if (keptSet.has(card.id)) continue;
    added.push(card.id);
    room -= 1;
  }
  STATE.introduced = { [today]: kept.concat(added) };
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
  const row = STATE.log[today] || { reviews: 0, correct: 0 };
  row.reviews += 1;
  if (know) row.correct += 1;
  STATE.log[today] = row;
}

function studied(day) {
  return (STATE.log[day] && STATE.log[day].reviews > 0) || false;
}

function streakCount() {
  let day = todayISO();
  if (!studied(day)) day = addDays(day, -1);
  let count = 0;
  while (studied(day) && count < 5000) {
    count += 1;
    day = addDays(day, -1);
  }
  return count;
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
  for (const card of DATA.cards) {
    if (!inDeck(card)) continue;
    const state = STATE.cards[card.id];
    if (state && state.due <= today && state.last !== today) due += 1;
  }
  const todayRow = STATE.log[today] || { reviews: 0, correct: 0 };
  return { learned, reviews, correct, due, todayRow };
}

function speak(text) {
  if (!window.speechSynthesis) {
    toast("Trình duyệt này không đọc được tiếng Anh.");
    return;
  }
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = "en-US";
  utter.rate = 0.92;
  const voices = window.speechSynthesis.getVoices();
  const voice = voices.find((item) => item.lang === "en-US")
    || voices.find((item) => /^en([-_]|$)/i.test(item.lang || ""));
  if (voice) utter.voice = voice;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utter);
}

function toast(message) {
  const node = document.getElementById("toast");
  node.hidden = false;
  node.textContent = message;
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { node.hidden = true; }, 2200);
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

function cardFaces(card, item) {
  const pos = POS_VI[card.pos] || card.pos;
  const retry = item.retry ? `<span class="pill retry">Ôn lại</span>` : "";
  const ipa = card.ipa ? `<p class="ipa">/${esc(card.ipa)}/</p>` : "";
  const also = card.also && card.also.length ? `<p class="also">Cũng viết: ${esc(card.also.join(", "))}</p>` : "";
  const topic = (card.topics || [])[0];
  const topicPill = topic ? `<span class="pill">${esc(topicName(topic))}</span>` : "";
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
      <div class="pillrow"><span class="pill">${esc(card.level)} · ${esc(pos)}</span>${topicPill}${retry}</div>
      <div class="wordwrap">
        <h1 class="${wordClass(card.word)}">${esc(card.word)}</h1>
        ${ipa}
        ${also}
      </div>
      <p class="hint">Chạm để lật</p>
    </div>
    <div class="face back">
      ${speakerButton()}
      <div class="pillrow"><span class="pill">${esc(card.level)} · ${esc(pos)}</span>${retry}</div>
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

function doneHtml() {
  const levels = STATE.settings.levels;
  if (!levels.length) {
    return `<section class="empty">
      <h1>Chưa chọn trình độ</h1>
      <p>Mở Bộ thẻ và chọn ít nhất một mức từ A1 đến C2. Lần đầu, B1 và B2 được chọn sẵn.</p>
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
    <h2 class="section-title">Chủ đề</h2>
    <p class="note">Để “Tất cả chủ đề” nếu bạn muốn học mọi từ trong trình độ đã chọn. Chọn một chủ đề để chỉ ôn phần đó.</p>
    <div class="chips">${chips.join("")}</div>
  </section>`;
  topmeta.textContent = chosen;
}

function renderStats() {
  const numbers = totals();
  const accuracy = numbers.reviews ? `${Math.round((numbers.correct / numbers.reviews) * 100)}%` : "—";
  const streak = streakCount();
  const today = todayISO();
  let day = addDays(today, -6);
  const days = [];
  let max = 1;
  for (let i = 0; i < 7; i += 1) {
    const count = (STATE.log[day] && STATE.log[day].reviews) || 0;
    if (count > max) max = count;
    const date = new Date(`${day}T12:00:00`);
    days.push({ label: WEEK[date.getDay()], count });
    day = addDays(day, 1);
  }
  const bars = days.map((item) => {
    const height = Math.max(4, Math.round((item.count / max) * 72));
    return `<div><i style="height:${height}px"></i><span>${item.label}</span></div>`;
  }).join("");
  const leftNew = newRemaining();
  const streakNote = streak
    ? (studied(today) ? "Bạn đã học hôm nay." : "Học một lượt hôm nay để giữ chuỗi.")
    : "Học một lượt để bắt đầu chuỗi.";
  main.innerHTML = `<section>
    <h1 class="section-title" style="margin-top:4px">Thống kê</h1>
    <div class="stats">
      <article class="stat wide"><div class="k">Chuỗi ngày</div><div class="v">${streak}</div><div class="s">${esc(streakNote)}</div></article>
      <article class="stat"><div class="k">Đã học</div><div class="v">${numbers.learned.toLocaleString("vi-VN")}</div><div class="s">nhớ được ít nhất một lần</div></article>
      <article class="stat"><div class="k">Đến hạn hôm nay</div><div class="v">${numbers.due.toLocaleString("vi-VN")}</div><div class="s">trong bộ đang chọn</div></article>
      <article class="stat"><div class="k">Độ chính xác</div><div class="v">${accuracy}</div><div class="s">${numbers.reviews.toLocaleString("vi-VN")} lượt ôn</div></article>
      <article class="stat"><div class="k">Hôm nay</div><div class="v">${numbers.todayRow.reviews}</div><div class="s">${numbers.todayRow.correct} lần biết</div></article>
    </div>
    <h2 class="section-title">7 ngày</h2>
    <div class="week" aria-hidden="true">${bars}</div>
    <p class="note">${leftNew ? `Còn ${leftNew} thẻ mới trong hạn hôm nay. ` : ""}Tiến độ chỉ nằm trên trình duyệt này. Đổi máy hoặc xóa dữ liệu trang là mất chuỗi.</p>
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
  document.querySelectorAll("[data-nav]").forEach((button) => {
    button.setAttribute("aria-current", button.dataset.nav === view ? "page" : "false");
  });
}

function render() {
  if (!DATA) return;
  setNav();
  if (view === "study") renderStudy();
  else if (view === "decks") renderDecks();
  else if (view === "stats") renderStats();
  else renderCredits();
  main.scrollTop = 0;
}

function grade(know) {
  if (busy || view !== "study") return;
  const item = currentItem();
  if (!item) return;
  busy = true;
  const retry = item.retry;
  if (!retry) {
    applySm2(item.id, know ? 4 : 1);
    bumpLog(know);
    session.done += 1;
    if (!know) session.queue.push({ id: item.id, retry: true });
  }
  session.index += 1;
  save();
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
  if (card) card.classList.toggle("is-flipped");
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
  if (!window.confirm("Xóa toàn bộ tiến độ ôn trên máy này?")) return;
  localStorage.removeItem(KEY);
  STATE = loadState();
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
    const response = await fetch("data/vocab.json");
    if (!response.ok) throw new Error("bad status");
    DATA = await response.json();
    INDEX = new Map(DATA.cards.map((card) => [card.id, card]));
    STATE = loadState();
    const known = new Set((DATA.topics || []).map((topic) => topic.id));
    STATE.settings.topics = STATE.settings.topics.filter((id) => known.has(id));
    if (window.speechSynthesis) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.addEventListener("voiceschanged", () => window.speechSynthesis.getVoices());
    }
    render();
  } catch {
    main.innerHTML = errorHtml();
    topmeta.textContent = "";
  }
}

boot();
