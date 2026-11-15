#!/usr/bin/env python3
"""Add common phrasal verbs, idioms, and collocations.

New cards go in data/fields/deck-phrasal.json and deck-collocation.json
so the phone loads them only when those topics are opened. Cards that
already exist keep their ids; this script only adds a topic tag.

Sources (see DATA_SOURCES.md):
  English Wiktionary via kaikki.org, CC BY-SA 4.0 and GFDL
  Vietnamese Wiktionary via kaikki.org, CC BY-SA 4.0 and GFDL
  Open English WordNet, CC BY 4.0
  Tatoeba, CC BY 2.0 FR
  wordfreq, CC BY-SA 4.0
"""

from __future__ import annotations

import bz2
import gzip
import json
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_vocab  # noqa: E402
from phrase_select import (  # noqa: E402
    TOPIC_COLLOCATION,
    TOPIC_NAME,
    TOPIC_PHRASE,
    collocations_in,
    keep_common,
    keep_frequent,
    phrase_kind,
)
from topics import topic_levels  # noqa: E402
from wordfreq import zipf_frequency  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
FIELDS = DATA / "fields"
WIKT_URL = "https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz"
WIKT_GZ = RAW / "enwiktionary.jsonl.gz"
CACHE = RAW / "en-mwe.jsonl"
UA = "FlashFreeBuilder/1.0 (educational vocabulary app; github.com/tuanlmogle/flashfree)"

PHRASE_CAP = 2200
COLLOCATION_CAP = 1400
EMO = {TOPIC_PHRASE: "1f4ac", TOPIC_COLLOCATION: "1f517"}


def download_wikt() -> None:
    if WIKT_GZ.exists() and WIKT_GZ.stat().st_size > 1_000_000:
        return
    RAW.mkdir(parents=True, exist_ok=True)
    print("downloading English Wiktionary extract…")
    request = urllib.request.Request(WIKT_URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=180) as response, WIKT_GZ.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    print(f"saved {WIKT_GZ.name} {WIKT_GZ.stat().st_size}")


def _gloss(sense: dict) -> str:
    if set(sense.get("tags") or []) & {"form-of", "alt-of", "no-gloss"} or sense.get("form_of"):
        return ""
    for gloss in sense.get("glosses") or []:
        if not isinstance(gloss, str):
            continue
        low = gloss.lower()
        if low.startswith(("form of ", "alternative form", "synonym of ", "abbreviation of ")):
            continue
        cleaned = build_vocab.tidy_english(gloss)
        if len(cleaned) >= 8:
            return cleaned
    return ""


def _vi(entry: dict) -> str:
    for item in entry.get("translations") or []:
        if item.get("lang_code") != "vi" and item.get("lang") != "Vietnamese":
            continue
        word = (item.get("word") or "").strip()
        if word and word.lower() != (entry.get("word") or "").lower():
            return word
    return ""


def extract_mwe() -> list[dict]:
    if CACHE.exists() and CACHE.stat().st_size > 1000:
        rows = []
        with CACHE.open(encoding="utf-8") as handle:
            for line in handle:
                rows.append(json.loads(line))
        print(f"cached wiktionary phrases: {len(rows)}")
        return rows
    download_wikt()
    rows = []
    seen = set()
    scanned = 0
    with gzip.open(WIKT_GZ, "rt", encoding="utf-8") as handle:
        for line in handle:
            scanned += 1
            if scanned % 400000 == 0:
                print(f"scanned {scanned} kept {len(rows)}")
            if " " not in line[:240] and "idiom" not in line and "phrasal" not in line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("lang_code") != "en":
                continue
            word = (entry.get("word") or "").strip()
            if " " not in word or any(ch.isupper() for ch in word):
                continue
            senses = entry.get("senses") or []
            entry_tags = list(entry.get("tags") or [])
            cats = []
            for cat in entry.get("categories") or []:
                name = cat.get("name") if isinstance(cat, dict) else ""
                if name:
                    cats.append(name)
            pos = (entry.get("pos") or "").lower()
            best = None
            for sense in senses:
                tags = entry_tags + list(sense.get("tags") or []) + cats
                gloss = _gloss(sense)
                if not gloss:
                    continue
                kind = phrase_kind(word, pos, tags)
                if not kind and collocations_in(word.lower().split()):
                    kind = "collocation"
                if not kind:
                    continue
                blob = " ".join(str(tag).lower() for tag in tags)
                priority = 2 if ("idiom" in blob or "phrasal" in blob) else 1
                if best is None or priority > best[0]:
                    best = (priority, kind, gloss)
            if not best:
                continue
            _priority, kind, gloss = best
            key = word.lower()
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "word": key,
                "pos": "verb" if kind == "phrasal" else "phrase",
                "kind": kind,
                "en": gloss,
                "vi": _vi(entry),
            })
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wiktionary phrases kept: {len(rows)} from {scanned} lines")
    return rows


def score_rows(rows: list[dict], counts: dict[str, int]) -> None:
    for row in rows:
        row["zipf"] = zipf_frequency(row["word"], "en")
        row["count"] = counts.get(row["word"], 0)


def tatoeba_scan(phrases: set[str]) -> tuple[dict[str, int], dict[str, dict], dict[str, int]]:
    """Count collocations and keep the shortest linked example for each phrase."""
    eng_path = build_vocab.FILES["eng"]
    vie_path = build_vocab.FILES["vie"]
    link_path = build_vocab.FILES["links"]
    token_re = re.compile(r"[A-Za-z']+")
    by_first: dict[str, list[str]] = defaultdict(list)
    for phrase in phrases:
        by_first[phrase.split()[0]].append(phrase)
    collocation_counts: dict[str, int] = defaultdict(int)
    phrase_counts: dict[str, int] = defaultdict(int)
    pending: dict[str, tuple[int, str, str]] = {}
    if not eng_path.exists():
        print("tatoeba english file missing")
        return collocation_counts, {}, phrase_counts

    def remember(phrase: str, sid: int, text: str, author: str) -> None:
        previous = pending.get(phrase)
        if previous is None or len(text) < len(previous[1]):
            pending[phrase] = (sid, text, author)

    with bz2.open(eng_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            try:
                sid = int(parts[0])
            except ValueError:
                continue
            text = parts[2].strip()
            if not text or len(text) > 140 or "http" in text.lower():
                continue
            tokens = token_re.findall(text)
            if not 3 <= len(tokens) <= 16:
                continue
            author = parts[3]
            if author in {"\\N", r"\N", "NULL"}:
                author = ""
            low_tokens = [tok.lower() for tok in tokens]
            for phrase in collocations_in(low_tokens):
                collocation_counts[phrase] += 1
                remember(phrase, sid, text, author)
            padded = f" {' '.join(low_tokens)} "
            seen_tok = set(low_tokens)
            for tok in seen_tok:
                for phrase in by_first.get(tok, ()):
                    if f" {phrase} " in padded:
                        phrase_counts[phrase] += 1
                        remember(phrase, sid, text, author)
    print(f"collocation types: {len(collocation_counts)}; example candidates: {len(pending)}")

    links = {}
    wanted_eng = {sid for sid, _text, _author in pending.values()}
    if link_path.exists():
        with bz2.open(link_path, "rt", encoding="utf-8") as handle:
            for line in handle:
                bits = line.rstrip("\n").split("\t")
                if len(bits) < 2:
                    continue
                try:
                    vie_id, eng_id = int(bits[0]), int(bits[1])
                except ValueError:
                    continue
                if eng_id in wanted_eng and eng_id not in links:
                    links[eng_id] = vie_id
    vie_text = {}
    wanted_vie = set(links.values())
    if vie_path.exists() and wanted_vie:
        with bz2.open(vie_path, "rt", encoding="utf-8") as handle:
            for line in handle:
                bits = line.rstrip("\n").split("\t")
                if len(bits) < 3:
                    continue
                try:
                    sid = int(bits[0])
                except ValueError:
                    continue
                if sid in wanted_vie and build_vocab.has_diacritic(bits[2]):
                    vie_text[sid] = bits[2].strip()
    examples = {}
    with_vi = 0
    for phrase, (sid, text, author) in pending.items():
        vi = vie_text.get(links.get(sid, -1), "")
        if vi:
            with_vi += 1
        examples[phrase] = {"en": text, "vi": vi, "id": sid, "author": author}
    print(f"tatoeba examples: {len(examples)}; with Vietnamese: {with_vi}")
    return collocation_counts, examples, phrase_counts


def load_cards() -> tuple[list[tuple[Path, dict]], dict[str, list[dict]], set[str]]:
    grouped = []
    by_word: dict[str, list[dict]] = defaultdict(list)
    ids = set()
    for path in sorted(DATA.glob("level-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        grouped.append((path, payload))
        for card in payload.get("cards") or []:
            card["_src"] = path
            ids.add(card["id"])
            by_word[card["word"].lower()].append(card)
    if FIELDS.exists():
        for path in sorted(FIELDS.glob("*.json")):
            if path.name.startswith("deck-"):
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            grouped.append((path, payload))
            for card in payload.get("cards") or []:
                card["_src"] = path
                ids.add(card["id"])
                by_word[card["word"].lower()].append(card)
    return grouped, by_word, ids


def attach_example(card: dict, example: dict | None) -> None:
    if not example or card.get("example"):
        return
    card["example"] = example["en"]
    if example.get("vi"):
        card["exampleVi"] = example["vi"]
    ref = {"id": example["id"]}
    if example.get("author"):
        ref["author"] = example["author"]
    card["tatoeba"] = ref


def new_card(word: str, pos: str, level: str, meaning: str, lang: str, topic: str, ids: set[str]) -> dict:
    card_id = build_vocab.slug(word, pos)
    if card_id in ids:
        suffix = 2
        while f"{card_id}-{suffix}" in ids:
            suffix += 1
        card_id = f"{card_id}-{suffix}"
    ids.add(card_id)
    card = {
        "id": card_id,
        "word": word,
        "pos": pos,
        "level": level,
        "meaning": meaning,
        "topics": [topic],
        "emo": [EMO[topic]],
    }
    if lang == "en":
        card["meaningLang"] = "en"
    return card


def meaning_for(word: str, pos: str, vi: str, en: str, bank, wn) -> tuple[str, str]:
    if vi:
        return vi, "vi"
    if bank:
        entries = build_vocab.lookup(bank, word, pos if pos != "phrase" else "noun")
        if not entries and " " in word:
            entries = build_vocab.lookup(bank, word, "phrase")
        if entries:
            text, _ipas = build_vocab.pick_meaning(entries, word, entries[0]["pos"])
            if text:
                return text, "vi"
    if en:
        return en, "en"
    if wn is not None:
        for try_pos in (pos, "noun", "verb"):
            text = build_vocab.english_meaning(wn, word, try_pos if try_pos != "phrase" else "noun")
            if text:
                return text, "en"
        noun = word.split()[-1]
        text = build_vocab.english_meaning(wn, noun, "noun")
        if text:
            return text, "en"
    return "", ""


def write_outputs(grouped, new_cards: list[dict], changed_paths: set[Path]) -> None:
    for path, payload in grouped:
        for card in payload.get("cards") or []:
            card.pop("_src", None)
        if path not in changed_paths:
            continue
        path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"updated {path.name}")
    FIELDS.mkdir(parents=True, exist_ok=True)
    by_topic = {TOPIC_PHRASE: [], TOPIC_COLLOCATION: []}
    for card in new_cards:
        topic = (card.get("topics") or [TOPIC_PHRASE])[0]
        by_topic.setdefault(topic, []).append(card)
    files = {
        TOPIC_PHRASE: FIELDS / "deck-phrasal.json",
        TOPIC_COLLOCATION: FIELDS / "deck-collocation.json",
    }
    for topic, path in files.items():
        group = by_topic.get(topic) or []
        group.sort(key=lambda card: (build_vocab.LEVEL_RANK.get(card["level"], 9), card["word"]))
        path.write_text(json.dumps({"cards": group}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"wrote {path.name} {len(group)} {path.stat().st_size}")


def refresh_meta() -> None:
    meta_path = DATA / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    cards = []
    for path in sorted(DATA.glob("level-*.json")):
        cards.extend(json.loads(path.read_text(encoding="utf-8")).get("cards") or [])
    field_cards = []
    sources: dict[str, list[str]] = defaultdict(list)
    for path in sorted(FIELDS.glob("*.json")):
        group = json.loads(path.read_text(encoding="utf-8")).get("cards") or []
        field_cards.extend(group)
        seen = set()
        for card in group:
            for topic in card.get("topics") or []:
                if topic not in seen:
                    seen.add(topic)
                    sources[topic].append(path.stem)
    all_cards = cards + field_cards
    counts = {level: 0 for level in build_vocab.LEVEL_RANK}
    image_counts = {level: 0 for level in build_vocab.LEVEL_RANK}
    vi_n = en_n = ipa_n = example_n = image_n = 0
    topic_counts = defaultdict(int)
    for card in all_cards:
        counts[card["level"]] += 1
        if card.get("meaningLang") == "en":
            en_n += 1
        else:
            vi_n += 1
        ipa_n += "ipa" in card
        example_n += "example" in card
        if card.get("img") or card.get("emo"):
            image_n += 1
            image_counts[card["level"]] += 1
        for topic in card.get("topics") or []:
            topic_counts[topic] += 1
    topics = []
    seen_ids = set()
    for item in meta.get("topics") or []:
        if item["id"] == TOPIC_PHRASE:
            item = dict(item)
            item["name"] = TOPIC_NAME[TOPIC_PHRASE]
        count = topic_counts.get(item["id"], 0)
        if count <= 0:
            continue
        item = dict(item)
        item["count"] = count
        topics.append(item)
        seen_ids.add(item["id"])
    if TOPIC_COLLOCATION not in seen_ids and topic_counts.get(TOPIC_COLLOCATION, 0) > 0:
        topics.append({
            "id": TOPIC_COLLOCATION,
            "name": TOPIC_NAME[TOPIC_COLLOCATION],
            "count": topic_counts[TOPIC_COLLOCATION],
        })
    meta.update({
        "counts": counts,
        "total": len(all_cards),
        "withVi": vi_n,
        "withEn": en_n,
        "withIpa": ipa_n,
        "withExample": example_n,
        "withImage": image_n,
        "imageCounts": image_counts,
        "topics": topics,
        "topicLevels": topic_levels(all_cards),
        "topicFiles": sorted(path.stem for path in FIELDS.glob("*.json")),
        "topicSources": {topic: ids for topic, ids in sorted(sources.items())},
    })
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    phrase_levels = meta["topicLevels"].get(TOPIC_PHRASE, {})
    collo_levels = meta["topicLevels"].get(TOPIC_COLLOCATION, {})
    print("phrase levels", phrase_levels, "count", topic_counts[TOPIC_PHRASE])
    print("collocation levels", collo_levels, "count", topic_counts[TOPIC_COLLOCATION])
    print("total", meta["total"])


def main() -> None:
    extracted = extract_mwe()
    # A cheap first score so Tatoeba only indexes phrases we might keep.
    for row in extracted:
        row["zipf"] = zipf_frequency(row["word"], "en")
    phrase_set = {row["word"] for row in extracted if row.get("kind") in {"phrasal", "idiom"}}
    collocation_counts, examples, phrase_counts = tatoeba_scan(phrase_set)
    for row in extracted:
        row["count"] = phrase_counts.get(row["word"], 0)
    phrase_rows = [row for row in extracted if row.get("kind") in {"phrasal", "idiom"}]
    common = [row for row in phrase_rows if (row.get("zipf") or 0) >= 4.5]
    rarer = [row for row in phrase_rows if 3.5 <= (row.get("zipf") or 0) < 4.5]
    phrases = keep_common(common, cap=4500, min_zipf=4.5, min_count=0)
    phrases += keep_common(rarer, cap=400, min_zipf=3.5, min_count=0)
    wiki_collo = {row["word"]: row for row in extracted if row.get("kind") == "collocation"}
    collo_rows = []
    for phrase, count in collocation_counts.items():
        if phrase in {row["word"] for row in phrases}:
            continue
        info = wiki_collo.get(phrase) or {}
        collo_rows.append({
            "word": phrase,
            "zipf": zipf_frequency(phrase, "en"),
            "count": count,
            "vi": info.get("vi") or "",
            "en": info.get("en") or "",
        })
    collocations = keep_frequent(collo_rows, cap=COLLOCATION_CAP, min_count=20)
    print(f"selected phrases {len(phrases)} collocations {len(collocations)}")

    wanted = {row["word"] for row in phrases} | {row["word"] for row in collocations}
    missing_vi = {word for word in wanted if not any(row["word"] == word and row.get("vi") for row in phrases)}
    bank = build_vocab.load_wiktionary(missing_vi) if missing_vi else {}
    wn = build_vocab.english_wordnet()

    grouped, by_word, ids = load_cards()
    changed_paths = set()
    new_cards = []
    tagged = 0

    def place(word: str, pos: str, topic: str, vi: str, en: str) -> None:
        nonlocal tagged
        existing = by_word.get(word) or []
        if existing:
            for card in existing:
                topics = list(card.get("topics") or [])
                if topic not in topics and len(topics) < 6:
                    topics.append(topic)
                    card["topics"] = topics
                    tagged += 1
                    if card.get("_src"):
                        changed_paths.add(card["_src"])
            before = existing[0].get("example")
            attach_example(existing[0], examples.get(word))
            if existing[0].get("example") != before and existing[0].get("_src"):
                changed_paths.add(existing[0]["_src"])
            return
        level = build_vocab.level_from_zipf(zipf_frequency(word, "en") or 0)
        meaning, lang = meaning_for(word, pos, vi, en, bank, wn)
        if not meaning:
            return
        if topic == TOPIC_COLLOCATION and word not in examples:
            return
        card = new_card(word, pos, level, meaning, lang, topic, ids)
        attach_example(card, examples.get(word))
        new_cards.append(card)
        by_word[word].append(card)

    for row in phrases:
        place(row["word"], row.get("pos") or "phrase", TOPIC_PHRASE, row.get("vi") or "", row.get("en") or "")
    for row in collocations:
        place(row["word"], "phrase", TOPIC_COLLOCATION, row.get("vi") or "", row.get("en") or "")
    print(f"tagged existing {tagged}; new cards {len(new_cards)}")
    write_outputs(grouped, new_cards, changed_paths)
    refresh_meta()
    samples = [card["word"] for card in new_cards[:8]]
    print("samples", samples)


if __name__ == "__main__":
    main()
