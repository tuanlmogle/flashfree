#!/usr/bin/env python3
"""Attach a ranked list of picture candidates to each card.

Sets, pinned so a rebuild picks the same files:
  - Microsoft Fluent Emoji 3D, commit 1ffb34c, MIT
  - Twemoji 14.0.2 graphics, CC BY 4.0
  - Google Noto Emoji svg tag v2.047, SIL OFL 1.1
  - OpenMoji 17.0.0, CC BY-SA 4.0
  - Wikimedia Commons photos already stored on the card (not re-fetched)

The browser loads one thumbnail at a time from a CDN. This script only
writes short ids (emoji hex, fluent path, commons file already on the card).
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DATA = ROOT / "data"
FLUENT_SHA = "1ffb34c752ecf5d402f04cfb4b392c77f57c54bc"
UA = "FlashFreeBuilder/1.0 (educational vocabulary app)"

GENERIC = {
    "face", "person", "people", "man", "woman", "boy", "girl", "child", "happy",
    "smile", "red", "blue", "green", "yellow", "black", "white", "object",
    "symbol", "sign", "button", "hand", "skin", "tone", "fun", "cool", "nice",
    "good", "bad", "big", "small", "new", "old", "love", "icon", "square",
    "circle", "arrow", "right", "left", "open", "close", "one", "two", "three",
    "group", "thing", "color", "colour", "light", "dark",
}

TOPIC_HEX = {
    "food": "1f372",
    "drinks": "1f964",
    "kitchen": "1f373",
    "cooking": "1f373",
    "restaurant": "1f37d",
    "family": "1f46a",
    "body": "1fac0",
    "health": "1fa7a",
    "medicine": "1f48a",
    "emotions": "1f60a",
    "personality": "1f9d0",
    "appearance": "1f485",
    "clothes": "1f455",
    "house": "1f3e0",
    "rooms": "1f6cb",
    "furniture": "1fa91",
    "city": "1f3d9",
    "places": "1f5fa",
    "travel": "1f9f3",
    "transport": "1f68c",
    "airport": "2708",
    "hotel": "1f3e8",
    "work": "1f4bc",
    "office": "1f4c4",
    "business": "1f4ca",
    "money": "1f4b0",
    "shopping": "1f6d2",
    "education": "1f4da",
    "science": "1f52c",
    "technology": "1f4f1",
    "computers": "1f4bb",
    "math": "2797",
    "nature": "1f333",
    "animals": "1f43e",
    "plants": "1f33f",
    "weather": "1f324",
    "environment": "267b",
    "space": "1f30c",
    "sports": "26bd",
    "music": "1f3b5",
    "art": "1f3a8",
    "movies": "1f3ac",
    "books": "1f4d6",
    "media": "1f4f0",
    "language": "1f4ac",
    "communication": "1f4ac",
    "law": "2696",
    "politics": "1f5f3",
    "military": "1fa96",
    "religion": "1f54a",
    "tools": "1f6e0",
    "materials": "1f9f1",
    "energy": "26a1",
    "shapes": "2b1c",
    "colors": "1f3a8",
    "time": "23f0",
    "numbers": "1f522",
    "people": "1f9d1",
    "social": "1f91d",
    "daily": "1f305",
    "holidays": "1f389",
    "phrasal": "1f4ac",
    "adjectives": "2728",
}


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def fluent_paths() -> dict[str, str]:
    cache = RAW / "fluent-tree.json"
    if not cache.exists():
        url = f"https://api.github.com/repos/microsoft/fluentui-emoji/git/trees/{FLUENT_SHA}?recursive=1"
        cache.write_text(json.dumps(fetch_json(url)), encoding="utf-8")
    tree = json.loads(cache.read_text(encoding="utf-8"))
    paths = {}
    for item in tree.get("tree") or []:
        path = item.get("path") or ""
        if not path.endswith(".png") or "/3D/" not in path:
            continue
        parts = path.split("/")
        if "3D" not in parts:
            continue
        index = parts.index("3D")
        folder = parts[index - 1]
        rank = 1
        if folder == "Default" and index >= 2:
            folder = parts[index - 2]
            rank = 0
        previous = paths.get(folder)
        if previous and previous[0] >= rank:
            continue
        relative = path[len("assets/"):]
        paths[folder] = (rank, relative)
    return {folder: relative for folder, (_, relative) in paths.items()}


def keyword_index(fluent_meta: dict[str, dict]) -> dict[str, str]:
    chosen: dict[str, tuple[int, str]] = {}

    def add(word: str, uni: str, priority: int) -> None:
        word = word.strip().lower().replace("_", " ")
        if not word or word in GENERIC or len(word) < 2 or " " in word:
            return
        uni = uni.lower()
        previous = chosen.get(word)
        if previous is None or priority < previous[0]:
            chosen[word] = (priority, uni)

    openmoji_path = RAW / "openmoji.json"
    if openmoji_path.exists():
        for item in json.loads(openmoji_path.read_text(encoding="utf-8")):
            if item.get("skintone") or item.get("skintone_combination"):
                continue
            hexcode = (item.get("hexcode") or "").lower()
            if not hexcode or "-" in hexcode:
                continue
            add(item.get("annotation") or "", hexcode, 0)
            for tag in (item.get("tags") or "").split(","):
                add(tag, hexcode, 3)
    for folder, meta in fluent_meta.items():
        uni = (meta.get("unicode") or "").lower().replace(" ", "-")
        if not uni:
            continue
        add(meta.get("cldr") or "", uni, 1)
        for keyword in meta.get("keywords") or []:
            add(keyword, uni, 2)
        for alias in meta.get("mappedToEmoticons") or []:
            add(alias, uni, 2)
    return {word: uni for word, (_, uni) in chosen.items()}


def load_fluent_meta(paths: dict[str, str]) -> tuple[dict[str, dict], dict[str, dict]]:
    root = RAW / "fluentui-emoji" / "assets"
    by_hex: dict[str, dict] = {}
    meta_by_folder: dict[str, dict] = {}
    if not root.exists():
        return by_hex, meta_by_folder
    for path in root.glob("*/metadata.json"):
        meta = json.loads(path.read_text(encoding="utf-8"))
        folder = path.parent.name
        meta_by_folder[folder] = meta
        uni = (meta.get("unicode") or "").lower().replace(" ", "-")
        relative = paths.get(folder)
        if not uni or not relative:
            continue
        if "-" in uni and "200d" not in uni:
            continue
        by_hex[uni] = {"f": relative}
    return by_hex, meta_by_folder


def openmoji_authors(index: dict[str, dict]) -> None:
    path = RAW / "openmoji.json"
    if not path.exists():
        return
    for item in json.loads(path.read_text(encoding="utf-8")):
        if item.get("skintone"):
            continue
        hexcode = (item.get("hexcode") or "")
        if not hexcode or "-" in hexcode:
            continue
        key = hexcode.lower()
        row = index.setdefault(key, {})
        row["oh"] = hexcode
        row["oa"] = item.get("openmoji_author") or "OpenMoji"


def related_words(en, word: str, pos: str) -> tuple[list[str], list[str]]:
    wanted = {"noun": "n", "verb": "v", "adj": "a", "adv": "r"}.get(pos)
    if not wanted:
        return [], []
    matches = []
    for item in en.words(word.replace(" ", "_")):
        if item.lemma().lower() != word.lower():
            continue
        if wanted == "a" and item.pos not in {"a", "s"}:
            continue
        if wanted != "a" and item.pos != wanted:
            continue
        matches.append(item)
        break
    if not matches:
        return [], []
    synonyms = []
    hyper = []
    for sense in matches[0].senses()[:2]:
        for lemma in sense.synset().lemmas():
            text = lemma.lower().replace("_", " ")
            if text != word.lower() and " " not in text:
                synonyms.append(text)
        for parent in sense.synset().hypernyms()[:1]:
            lemmas = parent.lemmas()
            if lemmas:
                text = lemmas[0].lower().replace("_", " ")
                if " " not in text:
                    hyper.append(text)
    return synonyms[:5], hyper[:2]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    paths = fluent_paths()
    by_hex, meta_by_folder = load_fluent_meta(paths)
    words = keyword_index(meta_by_folder)
    openmoji_authors(by_hex)
    print(f"fluent paths {len(paths)} indexed emoji {len(by_hex)} keywords {len(words)}")
    (DATA / "emoji-index.json").write_text(
        json.dumps(by_hex, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )

    import wn
    en = wn.Wordnet("oewn:2024")
    level_rank = ["A1", "A2", "B1", "B2", "C1", "C2"]
    before = {level: 0 for level in level_rank}
    after = {level: 0 for level in level_rank}
    totals = {level: 0 for level in level_rank}
    cache: dict[tuple[str, str], tuple[list[str], list[str]]] = {}

    def lookup_related(word: str, pos: str):
        key = (word, pos)
        if key not in cache:
            cache[key] = related_words(en, word, pos)
        return cache[key]

    for level in level_rank:
        path = DATA / f"level-{level.lower()}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        for card in payload.get("cards") or []:
            totals[level] += 1
            had = bool(card.get("img") or card.get("emo"))
            if had:
                before[level] += 1
            hexes = []

            def push(token: str) -> None:
                uni = words.get(token.lower())
                if not uni or uni in hexes:
                    return
                hexes.append(uni)

            push(card["word"])
            if len(hexes) < 2:
                synonyms, _hyper = lookup_related(card["word"], card.get("pos") or "")
                for token in synonyms:
                    if len(token) < 4:
                        continue
                    push(token)
                    if len(hexes) >= 2:
                        break
            if not hexes:
                for topic in card.get("topics") or []:
                    uni = TOPIC_HEX.get(topic)
                    if uni:
                        hexes.append(uni.lower())
                        break
            if (card.get("img") or {}).get("t") != "c":
                card.pop("img", None)
            card["emo"] = hexes[:3]
            if not card["emo"]:
                card.pop("emo", None)
            if card.get("img") or card.get("emo"):
                after[level] += 1
        path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(level, "before", before[level], "after", after[level], "of", totals[level])

    meta_path = DATA / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["imageCounts"] = after
    meta["withImage"] = sum(after.values())
    meta["imageBefore"] = before
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("pictures", meta["withImage"], "was", sum(before.values()))


if __name__ == "__main__":
    main()
