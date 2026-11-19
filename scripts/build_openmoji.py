#!/usr/bin/env python3
"""Map vocabulary words to OpenMoji and vendor only those SVGs.

Prefer no icon over a wrong one. An automatic match is kept only when the
OpenMoji annotation is exactly the word, or exactly one WordNet synonym or
hypernym. A short override list covers everyday A1–B2 words whose annotation
is a phrase (red apple, open book).
"""

from __future__ import annotations

import json
import random
import re
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "openmoji.json"
OUT_ICONS = ROOT / "data" / "icons.json"
OUT_SVG = ROOT / "assets" / "openmoji"
DATA_URL = "https://raw.githubusercontent.com/hfg-gmuend/openmoji/17.0.0/data/openmoji.json"
SVG_URL = "https://raw.githubusercontent.com/hfg-gmuend/openmoji/17.0.0/color/svg/{hex}.svg"
LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
SKIP_GROUP = {"extras-openmoji", "extras-unicode", "component"}
SKIP_HYPER = {
    "entity", "object", "thing", "person", "artifact", "instrumentality",
    "whole", "physical entity", "abstraction", "psychological feature",
    "attribute", "group", "act", "event", "process", "phenomenon", "state",
    "cognition", "communication", "relation", "measure", "quantity", "shape",
    "matter", "substance", "causal agent", "living thing", "organism",
    "animal", "plant", "device", "container", "structure", "body part",
}

# Everyday words whose OpenMoji name is a phrase, checked by hand.
OVERRIDES = {
    "apple": "1F34E",
    "book": "1F4D6",
    "books": "1F4DA",
    "water": "1F4A7",
    "car": "1F697",
    "rain": "1F327",
    "phone": "1F4F1",
    "telephone": "1F4F1",
    "music": "1F3B5",
    "coffee": "2615",
    "milk": "1F95B",
    "tree": "1F333",
    "heart": "2764",
    "love": "2764",
    "moon": "1F319",
    "tea": "1F375",
    "computer": "1F4BB",
    "laptop": "1F4BB",
    "clock": "23F0",
    "time": "23F0",
    "shirt": "1F455",
    "shoe": "1F45F",
    "shoes": "1F45F",
    "hat": "1F9E2",
    "bag": "1F45C",
    "plane": "2708",
    "airplane": "2708",
    "boat": "26F5",
    "bicycle": "1F6B2",
    "bike": "1F6B2",
    "doctor": "1F9D1-200D-2695-FE0F",
    "nurse": "1F9D1-200D-2695-FE0F",
    "hospital": "1F3E5",
    "money": "1F4B0",
    "friend": "1F91D",
    "friends": "1F91D",
    "home": "1F3E0",
    "food": "1F372",
    "happy": "1F642",
    "sad": "1F641",
    "angry": "1F620",
    "bread": "1F35E",
    "cheese": "1F9C0",
    "egg": "1F95A",
    "fish": "1F41F",
    "bird": "1F426",
    "cat": "1F408",
    "dog": "1F415",
    "house": "1F3E0",
    "school": "1F3EB",
    "sun": "2600",
    "star": "2B50",
    "key": "1F511",
    "door": "1F6AA",
    "bed": "1F6CF",
    "bus": "1F68C",
    "train": "1F686",
    "fire": "1F525",
    "family": "1F46A",
    "baby": "1F476",
    "child": "1F9D2",
    "boy": "1F466",
    "girl": "1F467",
    "man": "1F468",
    "woman": "1F469",
    "teacher": "1F9D1-200D-1F3EB",
    "flower": "1F338",
    "rose": "1F339",
    "pizza": "1F355",
    "cake": "1F370",
    "ice": "1F9CA",
    "snow": "2744",
    "cloud": "2601",
    "mountain": "26F0",
    "beach": "1F3D6",
    "camera": "1F4F7",
    "movie": "1F3AC",
    "football": "26BD",
    "soccer": "26BD",
    "basketball": "1F3C0",
    "tennis": "1F3BE",
    "guitar": "1F3B8",
    "piano": "1F3B9",
    "pencil": "270F",
    "pen": "1F58A",
    "letter": "2709",
    "email": "1F4E7",
    "gift": "1F381",
    "birthday": "1F382",
    "party": "1F389",
    "light": "1F4A1",
    "idea": "1F4A1",
    "question": "2753",
    "warning": "26A0",
    "stop": "1F6D1",
    "yes": "2705",
    "no": "274C",
    "ok": "1F44C",
    "hello": "1F44B",
    "goodbye": "1F44B",
    "thanks": "1F64F",
    "please": "1F64F",
    "sleep": "1F634",
    "eat": "1F37D",
    "drink": "1F964",
    "walk": "1F6B6",
    "run": "1F3C3",
    "swim": "1F3CA",
    "read": "1F4D6",
    "write": "270D",
    "listen": "1F442",
    "speak": "1F5E3",
    "see": "1F441",
    "watch": "231A",
    "buy": "1F6D2",
    "shop": "1F6D2",
    "work": "1F4BC",
    "job": "1F4BC",
    "office": "1F3E2",
    "city": "1F3D9",
    "town": "1F3D8",
    "country": "1F30D",
    "world": "1F30D",
    "map": "1F5FA",
    "weather": "1F324",
    "wind": "1F32C",
    "hot": "1F525",
    "cold": "1F976",
    "spring": "1F331",
    "summer": "1F31E",
    "autumn": "1F342",
    "winter": "2744",
    "morning": "1F305",
    "night": "1F319",
    "week": "1F4C5",
    "month": "1F4C5",
    "year": "1F4C5",
    "calendar": "1F4C5",
    "hour": "23F0",
    "minute": "23F1",
    "second": "23F2",
    "number": "1F522",
    "color": "1F3A8",
    "colour": "1F3A8",
    "red": "1F534",
    "blue": "1F535",
    "green": "1F7E2",
    "yellow": "1F7E1",
    "black": "26AB",
    "white": "26AA",
    "orange": "1F7E0",
    "purple": "1F7E3",
    "pink": "1FA77",
    "brown": "1F7E4",
}


def download_data() -> list[dict]:
    RAW.parent.mkdir(parents=True, exist_ok=True)
    if not RAW.exists() or RAW.stat().st_size < 1000:
        urllib.request.urlretrieve(DATA_URL, RAW)
    return json.loads(RAW.read_text(encoding="utf-8"))


def load_cards() -> list[dict]:
    cards = []
    for path in sorted((ROOT / "data").glob("level-*.json")):
        cards.extend(json.loads(path.read_text(encoding="utf-8")).get("cards") or [])
    return cards


def exact_index(entries: list[dict]) -> dict[str, str]:
    groups: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        if entry.get("skintone") or entry.get("skintone_combination"):
            continue
        if entry.get("group") in SKIP_GROUP:
            continue
        name = (entry.get("annotation") or "").strip().lower()
        if not name or "skin tone" in name:
            continue
        groups[name].append(entry["hexcode"])
    return {name: hexes[0] for name, hexes in groups.items() if len(hexes) == 1}


def wordnet_links() -> dict[str, set[str]]:
    """Noun -> one concrete hypernym name, not synonyms (those collide: endure/bear)."""
    try:
        import wn
    except ImportError:
        print("wordnet not installed; using overrides and exact names only")
        return {}
    try:
        lexicon = wn.Wordnet("oewn:2024")
    except Exception as error:
        print("wordnet unavailable", error)
        return {}
    links: dict[str, set[str]] = defaultdict(set)
    for syn in lexicon.synsets(pos="n"):
        lemmas = []
        for word in syn.words():
            lemma = word.lemma().replace("_", " ").lower()
            if lemma.isascii() and " " not in lemma and lemma not in SKIP_HYPER:
                lemmas.append(lemma)
        hyper_name = ""
        for hyper in syn.hypernyms()[:1]:
            for word in hyper.words()[:1]:
                lemma = word.lemma().replace("_", " ").lower()
                if lemma in SKIP_HYPER or " " in lemma:
                    continue
                hyper_name = lemma
                break
        if not hyper_name:
            continue
        for lemma in lemmas:
            if lemma != hyper_name:
                links[lemma].add(hyper_name)
    return links


def choose(word: str, exact: dict[str, str], links: dict[str, set[str]], level: str) -> str:
    """Exact OpenMoji name, or the hand-checked list.

    WordNet hypernyms were measured and not applied. On a 50-word B1–B2 sample
    they attached the wrong picture about as often as the right one
    (submarine → sandwich, behalf → the drink sake, strain → a musical note).
    """
    del links, level
    if word in OVERRIDES:
        return OVERRIDES[word]
    return exact.get(word, "")


def slim_svg(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<\?xml[^>]*\?>", "", text)
    text = re.sub(r"\s(?:inkscape|sodipodi):[^=\s]+=\"[^\"]*\"", "", text)
    text = re.sub(r">\s+<", "><", text)
    return text.strip() + "\n"


def fetch_svg(hexcode: str) -> None:
    dest = OUT_SVG / f"{hexcode}.svg"
    if dest.exists() and dest.stat().st_size > 80:
        dest.write_text(slim_svg(dest.read_text(encoding="utf-8")), encoding="utf-8")
        return
    request = urllib.request.Request(SVG_URL.format(hex=hexcode), headers={"User-Agent": "FlashFree/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read().decode("utf-8")
    dest.write_text(slim_svg(raw), encoding="utf-8")


def main() -> None:
    entries = download_data()
    exact = exact_index(entries)
    known = {entry["hexcode"] for entry in entries}
    for word, hexcode in list(OVERRIDES.items()):
        if hexcode not in known:
            raise SystemExit(f"override {word} -> {hexcode} is not an OpenMoji hex")
    links = wordnet_links()
    cards = load_cards()
    icons: dict[str, str] = {}
    by_level = {level: {"n": 0, "icon": 0} for level in LEVELS}
    annotated = {entry["hexcode"]: entry["annotation"] for entry in entries}
    for card in cards:
        word = (card.get("word") or "").strip().lower()
        level = card.get("level") or ""
        if level not in by_level or " " in word or not word.isascii():
            continue
        by_level[level]["n"] += 1
        hexcode = choose(word, exact, links, level)
        if not hexcode:
            continue
        icons[word] = hexcode
        by_level[level]["icon"] += 1
    OUT_ICONS.write_text(json.dumps(icons, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    hexes = sorted(set(icons.values()))
    OUT_SVG.mkdir(parents=True, exist_ok=True)
    # Drop SVGs we no longer use.
    for path in OUT_SVG.glob("*.svg"):
        if path.stem not in set(hexes):
            path.unlink()
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(fetch_svg, hexes))
    size = sum(path.stat().st_size for path in OUT_SVG.glob("*.svg"))
    print("words", len(icons), "svgs", len(hexes), "bytes", size)
    for level in LEVELS:
        row = by_level[level]
        pct = (100 * row["icon"] / row["n"]) if row["n"] else 0
        print(f"{level} {row['icon']}/{row['n']} {pct:.1f}%")
    pool = [card for card in cards if card.get("level") in {"B1", "B2"} and (card.get("word") or "").lower() in icons]
    random.Random(19).shuffle(pool)
    print("SPOT")
    for card in pool[:50]:
        word = card["word"].lower()
        hexcode = icons[word]
        print(f"{card['level']}\t{word}\t{hexcode}\t{annotated.get(hexcode, '')}")


if __name__ == "__main__":
    main()
