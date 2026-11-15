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
    EVERYDAY_PHRASES,
    TOPIC_COLLOCATION,
    TOPIC_NAME,
    TOPIC_PHRASE,
    assign_usage_levels,
    association,
    collocations_in,
    gloss_rank,
    has_pronoun,
    phrase_kind,
    reject_usage,
    usable_phrase,
)
from topics import topic_levels  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
FIELDS = DATA / "fields"
WIKT_URL = "https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz"
WIKT_GZ = RAW / "enwiktionary.jsonl.gz"
CACHE = RAW / "en-mwe-v2.jsonl"
UA = "FlashFreeBuilder/1.0 (educational vocabulary app; github.com/tuanlmogle/flashfree)"

PHRASE_CAP = 3200
PHRASE_MIN_COUNT = 2
COLLOCATION_CAP = 1200
COLLOCATION_MIN_COUNT = 15
# Below this, the words co-occur about as often as chance, so it is not a phrase.
MIN_ASSOCIATION = 0.6
# "run out of" is not a Wiktionary headword. The base entry covers it.
BASE_WHEN_MISSING = {"run out of": "run out"}
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
        if "used other than figuratively" in low or "used other than with a figurative" in low:
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
    rows_by_word = {}
    seen = {}
    scanned = 0
    with gzip.open(WIKT_GZ, "rt", encoding="utf-8") as handle:
        for line in handle:
            scanned += 1
            if scanned % 400000 == 0:
                print(f"scanned {scanned} kept {len(rows_by_word)}")
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
            for index, sense in enumerate(senses):
                tags = entry_tags + list(sense.get("tags") or []) + cats
                if reject_usage(tags):
                    continue
                gloss = _gloss(sense)
                if not gloss:
                    continue
                kind = phrase_kind(word, pos, tags)
                if not kind and collocations_in(word.lower().split()):
                    kind = "collocation"
                if not kind:
                    continue
                rank = gloss_rank(word.lower(), pos, tags, gloss, index)
                blob = " ".join(str(tag).lower() for tag in tags)
                slang = "slang" in blob or "vulgar" in blob or "offensive" in blob
                if best is None or rank < best[0]:
                    best = (rank, kind, gloss, slang)
            if not best:
                continue
            _rank, kind, gloss, slang = best
            key = word.lower()
            row = {
                "word": key,
                "pos": "verb" if kind == "phrasal" else "phrase",
                "kind": kind,
                "en": gloss,
                "vi": _vi(entry),
                "slang": slang,
            }
            previous_rank = seen.get(key)
            if previous_rank is not None and best[0] >= previous_rank:
                if row["vi"] and not rows_by_word[key].get("vi"):
                    rows_by_word[key]["vi"] = row["vi"]
                continue
            if previous_rank is not None and rows_by_word[key].get("vi") and not row["vi"]:
                row["vi"] = rows_by_word[key]["vi"]
            seen[key] = best[0]
            rows_by_word[key] = row
    rows = list(rows_by_word.values())
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wiktionary phrases kept: {len(rows)} from {scanned} lines")
    return rows


VULGAR_TOKENS = build_vocab.BAD_WORD | {
    "piss", "pissed", "pissing", "goddamn", "crap", "arse", "ass",
}
BAD_PHRASE_GLOSS = (
    "cognition", "homogeneous mixture", "spermatozoa", "grammatical category",
    "sexual intercourse",
)


def vulgar_text(word: str, gloss: str) -> bool:
    bits = set(re.findall(r"[a-z']+", (word or "").lower()))
    if bits & VULGAR_TOKENS:
        return True
    blob = (gloss or "").lower()
    return any(bit in blob for bit in ("vulgar", "obscene", "offensive term", "slur", "sexual intercourse"))


def phrase_gloss(wn, phrase: str) -> str:
    """Pick the noun sense whose examples actually use this phrase."""
    parts = [part for part in phrase.split() if part not in {"a", "an", "the"}]
    if len(parts) < 2 or wn is None:
        return ""
    head = parts[-1]
    others = [part for part in parts[:-1] if len(part) >= 3]
    found = []
    for item in wn.words(head.replace(" ", "_")):
        if item.pos != "n" or item.lemma().lower() != head:
            continue
        if item.lemma()[:1].isupper():
            return ""
        for sense in item.senses()[:8]:
            definition = build_vocab.tidy_english(sense.synset().definition() or "")
            if ";" in definition:
                head, rest = definition.split(";", 1)
                if any(bit in rest.lower() for bit in ("pronoun", "grammar", "singular", "quantifier")):
                    definition = head.strip()
            if len(definition) < 8:
                continue
            if any(bit in definition.lower() for bit in BAD_PHRASE_GLOSS):
                continue
            blob = (definition + " " + " ".join(sense.synset().examples())).lower()
            score = sum(1 for other in others if other in blob)
            found.append((score, len(found), definition))
        break
    if not found:
        return ""
    found.sort(key=lambda item: (-item[0], item[1]))
    return found[0][2]


def tatoeba_scan(phrases: set[str]) -> tuple[dict[str, int], dict[str, dict], dict[str, int], dict[str, int], int]:
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
    unigram: dict[str, int] = defaultdict(int)
    sentences = 0
    pending: dict[str, tuple[int, str, str]] = {}
    if not eng_path.exists():
        print("tatoeba english file missing")
        return collocation_counts, {}, phrase_counts, {}, 0

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
            sentences += 1
            for tok in set(low_tokens):
                unigram[tok] += 1
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
    print(f"tatoeba examples: {len(examples)}; with Vietnamese: {with_vi}; sentences {sentences}")
    return collocation_counts, examples, phrase_counts, unigram, sentences


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


def new_card(word: str, pos: str, level: str, meaning: str, lang: str, topic: str, ids: set[str], freq: int) -> dict:
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
    if freq:
        card["freq"] = freq
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
        text = phrase_gloss(wn, word)
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
        group.sort(key=lambda card: (
            build_vocab.LEVEL_RANK.get(card["level"], 9),
            0 if card.get("example") else 1,
            -(card.get("freq") or 0),
            card["word"],
        ))
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


def _row_usable(row: dict, count: int, minimum: int, unigram: dict, sentences: int) -> bool:
    if has_pronoun(row["word"]):
        return False
    if count < minimum:
        return False
    if row["word"] not in EVERYDAY_PHRASES and association(row["word"], count, unigram, sentences) < MIN_ASSOCIATION:
        return False
    return usable_phrase(
        row["word"],
        count,
        slang=bool(row.get("slang")),
        vulgar=vulgar_text(row["word"], row.get("en") or ""),
    )


def select_phrases(extracted: list[dict], counts: dict[str, int], unigram: dict, sentences: int) -> list[dict]:
    by_word = {row["word"]: row for row in extracted if row.get("kind") in {"phrasal", "idiom"}}
    kept = []
    for row in by_word.values():
        count = counts.get(row["word"], 0)
        if not _row_usable(row, count, PHRASE_MIN_COUNT, unigram, sentences):
            continue
        chosen = dict(row)
        chosen["count"] = count
        kept.append(chosen)
    have = {row["word"] for row in kept}
    for longer, base in BASE_WHEN_MISSING.items():
        if base in have or longer in have:
            continue
        row = by_word.get(base)
        count = counts.get(base, 0)
        if not row or count <= 0 or vulgar_text(base, row.get("en") or ""):
            print(f"missing base for {longer}")
            continue
        chosen = dict(row)
        chosen["count"] = count
        chosen["slang"] = False
        kept.append(chosen)
        have.add(base)
        print(f"covered {longer} with {base} ({count})")
    kept.sort(key=lambda row: (-row["count"], row["word"]))
    return assign_usage_levels(kept[:PHRASE_CAP])


def select_collocations(counts: dict[str, int], examples: dict, wiki: dict, phrase_words: set[str], unigram: dict, sentences: int) -> list[dict]:
    rows = []
    for phrase, count in counts.items():
        if phrase in phrase_words or phrase not in examples:
            continue
        info = wiki.get(phrase) or {}
        row = {
            "word": phrase,
            "count": count,
            "vi": info.get("vi") or "",
            "en": info.get("en") or "",
            "slang": bool(info.get("slang")),
            "kind": "collocation",
        }
        if not _row_usable(row, count, COLLOCATION_MIN_COUNT, unigram, sentences):
            continue
        rows.append(row)
    rows.sort(key=lambda row: (-row["count"], row["word"]))
    return assign_usage_levels(rows[:COLLOCATION_CAP])


def drop_stale_topics(grouped, phrase_words: set[str], collo_words: set[str]) -> set[Path]:
    changed = set()
    for _path, payload in grouped:
        for card in payload.get("cards") or []:
            topics = list(card.get("topics") or [])
            word = (card.get("word") or "").lower()
            kept_topics = [
                topic for topic in topics
                if not (topic == TOPIC_PHRASE and word not in phrase_words)
                and not (topic == TOPIC_COLLOCATION and word not in collo_words)
            ]
            if kept_topics == topics:
                continue
            card["topics"] = kept_topics
            card.pop("freq", None)
            if card.get("_src"):
                changed.add(card["_src"])
    return changed


def learner_preview(cards: list[dict], levels=("B1", "B2")) -> list[dict]:
    pool = [card for card in cards if card.get("level") in levels]
    pool.sort(key=lambda card: (
        build_vocab.LEVEL_RANK.get(card["level"], 9),
        0 if card.get("example") else 1,
        -(card.get("freq") or 0),
        card.get("word") or "",
    ))
    return pool[:15]


def main() -> None:
    extracted = extract_mwe()
    phrase_set = {row["word"] for row in extracted if row.get("kind") in {"phrasal", "idiom"}}
    collocation_counts, examples, phrase_counts, unigram, sentences = tatoeba_scan(phrase_set)
    phrases = select_phrases(extracted, phrase_counts, unigram, sentences)
    wiki_collo = {row["word"]: row for row in extracted if row.get("kind") == "collocation"}
    collocations = select_collocations(
        collocation_counts, examples, wiki_collo, {row["word"] for row in phrases}, unigram, sentences
    )
    print(f"selected phrases {len(phrases)} collocations {len(collocations)}")
    for word in ("give up", "figure out", "find out", "come on", "pick up", "look for",
                 "get up", "run out", "hang out", "make sure", "take care of", "by the way", "of course"):
        row = next((item for item in phrases + collocations if item["word"] == word), None)
        if row:
            print(f"anchor {word}: {row['level']} count={row['count']} deck={row.get('kind')} | {row.get('en','')[:80]}")
        else:
            print(f"anchor {word}: MISSING")

    wanted = {row["word"] for row in phrases} | {row["word"] for row in collocations}
    have_vi = {row["word"] for row in phrases + collocations if row.get("vi")}
    missing_vi = wanted - have_vi
    bank = build_vocab.load_wiktionary(missing_vi) if missing_vi else {}
    wn = build_vocab.english_wordnet()

    grouped, by_word, ids = load_cards()
    changed_paths = drop_stale_topics(
        grouped,
        {row["word"] for row in phrases},
        {row["word"] for row in collocations},
    )
    new_cards = []
    placed = {TOPIC_PHRASE: [], TOPIC_COLLOCATION: []}
    tagged = 0

    def place(row: dict, topic: str, pos: str) -> None:
        nonlocal tagged
        word = row["word"]
        freq = int(row.get("freq") or row.get("count") or 0)
        example = examples.get(word)
        if not example:
            return
        existing = by_word.get(word) or []
        if existing:
            for card in existing:
                topics = list(card.get("topics") or [])
                changed = False
                if topic not in topics and len(topics) < 6:
                    topics.append(topic)
                    card["topics"] = topics
                    tagged += 1
                    changed = True
                if card.get("freq") != freq:
                    card["freq"] = freq
                    changed = True
                if changed and card.get("_src"):
                    changed_paths.add(card["_src"])
            before = existing[0].get("example")
            attach_example(existing[0], example)
            if existing[0].get("example") != before and existing[0].get("_src"):
                changed_paths.add(existing[0]["_src"])
            placed[topic].append(existing[0])
            return
        meaning, lang = meaning_for(word, pos, row.get("vi") or "", row.get("en") or "", bank, wn)
        if not meaning:
            return
        card = new_card(word, pos, row["level"], meaning, lang, topic, ids, freq)
        attach_example(card, example)
        new_cards.append(card)
        placed[topic].append(card)
        by_word[word].append(card)

    for row in phrases:
        place(row, TOPIC_PHRASE, row.get("pos") or "phrase")
    for row in collocations:
        place(row, TOPIC_COLLOCATION, "phrase")
    print(f"tagged existing {tagged}; new cards {len(new_cards)}")
    write_outputs(grouped, new_cards, changed_paths)
    refresh_meta()
    for topic, label in ((TOPIC_PHRASE, "phrasal"), (TOPIC_COLLOCATION, "collocation")):
        cards = placed[topic]
        with_example = sum(1 for card in cards if card.get("example"))
        with_vi = sum(1 for card in cards if card.get("meaningLang") != "en" and card.get("meaning"))
        print(f"{label} placed {len(cards)} examples {with_example} vi {with_vi}")
        print(f"{label} B1+B2 first 15:")
        for card in learner_preview(cards):
            print(f"  {card['level']} {card.get('freq')} {card['word']} | {(card.get('example') or '')[:70]}")


if __name__ == "__main__":
    main()
