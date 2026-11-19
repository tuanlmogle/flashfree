#!/usr/bin/env python3
"""Map vocabulary words to OpenMoji and vendor only those SVGs.

Prefer no icon over a wrong one. An automatic match is kept only when the
word is part of exactly one OpenMoji or CLDR name. A hand-checked override
list covers everyday A1–B2 words whose picture name is a phrase (red apple).
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
    "mate": "1F91D",
    "mates": "1F91D",
    "home": "1F3E0",
    "food": "1F372",
    "happy": "1F642",
    "sad": "1F641",
    "angry": "1F620",
    "bread": "1F35E",
    "cheese": "1F9C0",
    "hang out": "1F465",
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
    "aeroplane": "2708",
    "airplane": "2708",
    "airport": "1F6EB",
    "afraid": "1F628",
    "answer": "1F4AC",
    "art": "1F3A8",
    "ball": "26BD",
    "bathroom": "1F6BB",
    "bean": "1FAD8",
    "bee": "1F41D",
    "beef": "1F969",
    "bedroom": "1F6CF",
    "biscuit": "1F36A",
    "cookie": "1F36A",
    "bottle": "1F37E",
    "box": "1F4E6",
    "breakfast": "1F373",
    "bridge": "1F309",
    "brush": "1F9F4",
    "building": "1F3E2",
    "cafe": "2615",
    "camp": "26FA",
    "cap": "1F9E2",
    "carrot": "1F955",
    "chicken": "1F414",
    "chocolate": "1F36B",
    "church": "26EA",
    "classroom": "1F3EB",
    "clothes": "1F455",
    "cow": "1F404",
    "cup": "1F964",
    "dance": "1F483",
    "daughter": "1F467",
    "dictionary": "1F4D6",
    "dinner": "1F37D",
    "dress": "1F457",
    "driver": "1F697",
    "ear": "1F442",
    "earth": "1F30D",
    "elephant": "1F418",
    "evening": "1F307",
    "eye": "1F441",
    "factory": "1F3ED",
    "farm": "1F33E",
    "father": "1F468",
    "mother": "1F469",
    "film": "1F3AC",
    "finger": "1F91F",
    "foot": "1F9B6",
    "forest": "1F332",
    "fork": "1F374",
    "fruit": "1F34E",
    "game": "1F3AE",
    "garden": "1FAB4",
    "girl": "1F467",
    "glass": "1F943",
    "gold": "1F947",
    "grandfather": "1F474",
    "grandmother": "1F475",
    "grandma": "1F475",
    "grandpa": "1F474",
    "hair": "1F487",
    "hill": "26F0",
    "holiday": "1F3D6",
    "horse": "1F40E",
    "hotel": "1F3E8",
    "hungry": "1F37D",
    "husband": "1F468",
    "wife": "1F469",
    "island": "1F3DD",
    "jacket": "1F9E5",
    "jeans": "1F456",
    "juice": "1F9C3",
    "king": "1F451",
    "queen": "1F451",
    "kitchen": "1F373",
    "knife": "1F52A",
    "lake": "1F30A",
    "lamp": "1F4A1",
    "laugh": "1F602",
    "leaf": "1F342",
    "leg": "1F9B5",
    "lemon": "1F34B",
    "library": "1F4DA",
    "lion": "1F981",
    "lock": "1F512",
    "lunch": "1F37D",
    "magazine": "1F4F0",
    "mail": "1F4E7",
    "market": "1F3EA",
    "meat": "1F969",
    "medicine": "1F48A",
    "monkey": "1F412",
    "mouse": "1F401",
    "mouth": "1F444",
    "newspaper": "1F4F0",
    "nose": "1F443",
    "ocean": "1F30A",
    "oil": "1F6E2",
    "paint": "1F58C",
    "pants": "1F456",
    "paper": "1F4C4",
    "park": "1F3DE",
    "pepper": "1FAD1",
    "pet": "1F415",
    "photo": "1F4F7",
    "picture": "1F5BC",
    "pig": "1F416",
    "pizza": "1F355",
    "plant": "1F331",
    "police": "1F693",
    "potato": "1F954",
    "rabbit": "1F407",
    "radio": "1F4FB",
    "restaurant": "1F37D",
    "rice": "1F35A",
    "ring": "1F48D",
    "river": "1F30A",
    "road": "1F6E3",
    "salt": "1F9C2",
    "scissors": "2702",
    "sea": "1F30A",
    "sheep": "1F411",
    "ship": "1F6A2",
    "sing": "1F3A4",
    "sister": "1F467",
    "ski": "26F7",
    "sky": "1F324",
    "smile": "1F642",
    "smoke": "1F6AC",
    "soap": "1F9FC",
    "sock": "1F9E6",
    "soup": "1F372",
    "space": "1F680",
    "sport": "26BD",
    "station": "1F689",
    "store": "1F3EA",
    "storm": "1F329",
    "street": "1F6E3",
    "student": "1F393",
    "television": "1F4FA",
    "tv": "1F4FA",
    "think": "1F914",
    "ticket": "1F3AB",
    "tiger": "1F405",
    "toilet": "1F6BD",
    "tomato": "1F345",
    "tooth": "1F9B7",
    "tower": "1F5FC",
    "toy": "1F9F8",
    "truck": "1F69A",
    "umbrella": "2602",
    "uncle": "1F468",
    "university": "1F3EB",
    "vegetable": "1F955",
    "village": "1F3D8",
    "window": "1FA9F",
    "color": "1F3A8",
    "colour": "1F3A8",
    "colours": "1F3A8",
    "red": "1F534",
    "blue": "1F535",
    "green": "1F7E2",
    "yellow": "1F7E1",
    "black": "26AB",
    "white": "26AA",
    "orange": "1F34A",
    "purple": "1F7E3",
    "pink": "1FA77",
    "brown": "1F7E4",
    "actor": "1F3AD",
    "actress": "1F3AD",
    "aunt": "1F469",
    "boyfriend": "1F468",
    "brother": "1F466",
    "cook": "1F373",
    "couch": "1F6CB",
    "sofa": "1F6CB",
    "cream": "1F366",
    "cry": "1F622",
    "dad": "1F468",
    "daddy": "1F468",
    "air": "1F32C",
    "beer": "1F37A",
    "blood": "1FA78",
    "bulb": "1F4A1",
    "cab": "1F695",
    "taxi": "1F695",
    "cash": "1F4B5",
    "dollar": "1F4B5",
    "chef": "1F373",
    "coast": "1F30A",
    "corn": "1F33D",
    "duck": "1F986",
    "alcohol": "1F377",
    "ape": "1F412",
    "arrow": "27A1",
    "artist": "1F3A8",
    "aspirin": "1F48A",
    "bowl": "1F963",
    "garbage": "1F5D1",
    "trash": "1F5D1",
    "flag": "1F6A9",
    "goal": "1F945",
    "honey": "1F36F",
    "onion": "1F9C5",
    "peach": "1F351",
    "pear": "1F350",
    "shark": "1F988",
    "whale": "1F40B",
    "wolf": "1F43A",
    "wine": "1F377",
    "mushroom": "1F344",
    "spider": "1F577",
    "sandwich": "1F96A",
    "salad": "1F957",
    "hammer": "1F528",
    "luggage": "1F9F3",
    "suitcase": "1F9F3",
    "shower": "1F6BF",
    "violin": "1F3BB",
    "robot": "1F916",
    "garlic": "1F9C4",
    "farmer": "1F9D1-200D-1F33E",
    "astronaut": "1F9D1-200D-1F680",
    "pilot": "1F9D1-200D-2708-FE0F",
    "pill": "1F48A",
    "medicine": "1F48A",
}


def download_data() -> list[dict]:
    RAW.parent.mkdir(parents=True, exist_ok=True)
    if not RAW.exists() or RAW.stat().st_size < 1000:
        urllib.request.urlretrieve(DATA_URL, RAW)
    return json.loads(RAW.read_text(encoding="utf-8"))


def load_cards() -> list[dict]:
    cards = []
    paths = list(sorted((ROOT / "data").glob("level-*.json")))
    paths += list(sorted((ROOT / "data" / "fields").glob("deck-*.json")))
    for path in paths:
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


# Keywords that sit on many pictures and would pick one at random.
# Automatic matches that looked right as a unique name-word and were wrong
# for the vocabulary sense. Overrides can still assign these on purpose.
DENY_AUTO = {
    "amount", "spiral", "handle", "line", "aid", "utility", "grade", "cricket",
    "bullet", "round", "tire", "tyre", "customs", "venture", "trim", "melted",
    "behalf", "submarine", "endure", "fat", "fabulous", "hang", "root", "bars",
    "eighteen", "reserved", "parked", "sealed", "greens", "hated", "exchange",
    "service", "viewing", "shooting", "blowing", "stuffed", "cooked", "rolled",
    "board", "cricket", "leo", "territory", "tear", "dot",
    "feeding", "fly", "flies", "score", "crossed", "struck", "slash",
    "rex", "saw",
}


KEYWORD_STOP = SKIP_HYPER | DENY_AUTO | {
    "face", "person", "people", "man", "woman", "boy", "girl", "happy", "sad",
    "love", "good", "bad", "big", "small", "new", "old", "red", "blue", "green",
    "yellow", "black", "white", "orange", "purple", "pink", "brown", "food",
    "animal", "nature", "symbol", "sign", "button", "hand", "skin", "tone",
    "eye", "eyes", "smile", "smiling", "comic", "object", "clothing", "clothes",
    "vehicle", "feeling", "emotion", "fun", "nice", "great", "heart", "square",
    "circle", "tool", "sport", "weather", "water", "music", "book", "car",
    "phone", "apple", "rain", "tree", "house", "home", "time", "money",
}
PHRASE_STOP = {
    "a", "an", "the", "of", "to", "in", "on", "at", "for", "with", "and", "or",
    "up", "out", "off", "down", "away", "back", "over", "into", "from", "by",
    "as", "if", "not", "no", "your", "my", "our", "it", "me", "you", "we",
}
CLDR_URL = (
    "https://raw.githubusercontent.com/unicode-org/cldr-json/main/"
    "cldr-json/cldr-annotations-full/annotations/en/annotations.json"
)
CLDR_PATH = ROOT / "data" / "raw" / "cldr-annotations-en.json"


def emoji_hexes(emoji: str) -> list[str]:
    parts = []
    for char in emoji:
        code = ord(char)
        if code == 0xFE0F:
            continue
        parts.append(f"{code:X}")
    full = "-".join(f"{ord(char):X}" for char in emoji)
    dropped = "-".join(parts)
    found = []
    for item in (dropped, full):
        if item and item not in found:
            found.append(item)
    return found


def content_tokens(name: str) -> list[str]:
    """Alphabetic words in an emoji name, before stop-word filtering.

    Stop words are not removed here. Dropping "face" or "aid" and then
    keeping whatever is left is how "slightly smiling face" claimed the
    word slightly, and "hearing aid" claimed hearing.
    """
    if "japanese" in (name or "").lower() or "skin tone" in (name or "").lower():
        return []
    if (name or "").lower().startswith("flag:"):
        # "flag: Switzerland" may match Switzerland. A leftover word such as
        # territory (British Indian Ocean Territory) is not a picture of that word.
        parts = re.split(r"[^A-Za-z]+", name.split(":", 1)[-1])
    else:
        parts = re.split(r"[^A-Za-z]+", name or "")
    tokens = []
    for token in parts:
        if not token or any(ord(char) > 127 for char in token):
            continue
        word = token.lower()
        if word.isalpha():
            tokens.append(word)
    return tokens


def name_words(name: str) -> list[str]:
    """The name itself, when it is a single word ("spoon", not "light bulb")."""
    tokens = [word for word in content_tokens(name) if len(word) >= 3]
    if len(tokens) == 1 and tokens[0] not in KEYWORD_STOP:
        return tokens
    return []


def head_words(name: str) -> list[str]:
    """Last word of a longer name, when that word is the thing in the picture.

    If the last word is generic ("face", "sign", "up"), the name does not
    match. The word before it is not used.
    """
    tokens = content_tokens(name)
    if len(tokens) < 2:
        return []
    head = tokens[-1]
    if len(head) < 3 or head in KEYWORD_STOP:
        return []
    return [head]


def keyword_index(entries: list[dict], known: set[str]) -> dict[str, str]:
    """A word maps to an emoji only when it is a word in exactly one emoji name.

    Loose keywords (fat → hamster, hang → call-me hand) are ignored. CLDR and
    OpenMoji names are both read; a keyword counts only if it is also a word
    in that emoji's name.
    """
    groups: dict[str, set[str]] = defaultdict(set)

    def add(keyword: str, hexcode: str) -> None:
        if hexcode not in known or keyword in KEYWORD_STOP:
            return
        groups[keyword].add(hexcode)

    for entry in entries:
        if entry.get("skintone") or entry.get("skintone_combination"):
            continue
        if entry.get("group") in SKIP_GROUP:
            continue
        name = entry.get("annotation") or ""
        if "skin tone" in name.lower() or "japanese" in name.lower():
            continue
        for word in name_words(name) + head_words(name):
            add(word, entry["hexcode"])
    if not CLDR_PATH.exists() or CLDR_PATH.stat().st_size < 1000:
        CLDR_PATH.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(CLDR_URL, CLDR_PATH)
    payload = json.loads(CLDR_PATH.read_text(encoding="utf-8"))
    annotations = payload.get("annotations", {}).get("annotations", {})
    by_hex = {entry["hexcode"] for entry in entries}
    for emoji, info in annotations.items():
        hexcode = ""
        for candidate in emoji_hexes(emoji):
            if candidate in by_hex:
                hexcode = candidate
                break
        if not hexcode:
            continue
        tts = " ".join(info.get("tts") or [])
        allowed = set(name_words(tts) + head_words(tts))
        for word in allowed:
            add(word, hexcode)
        for keyword in info.get("default") or []:
            keyword = str(keyword).strip().lower()
            if keyword in allowed:
                add(keyword, hexcode)
    return {word: next(iter(hexes)) for word, hexes in groups.items() if len(hexes) == 1}


COLOR_WORDS = {
    "red", "blue", "green", "yellow", "black", "white", "orange", "purple", "pink", "brown",
}
GENERIC_TAIL = {
    "face", "button", "sign", "symbol", "wedge", "circle", "square", "mark", "emoji",
}
# -ing/-ed forms only fold onto these hand-checked verbs, not onto nouns (hated → hat).
VERB_LEMMAS = {
    "run", "eat", "walk", "swim", "sleep", "read", "write", "listen", "speak", "see",
    "buy", "shop", "work", "drink", "stop", "cry",
}


def stem_forms(word: str) -> list[tuple[str, str]]:
    """(lemma, kind). -ing/-ed only counts later if the lemma was hand-checked."""
    forms = []
    if word.endswith("ies") and len(word) > 4:
        forms.append((word[:-3] + "y", "plural"))
    if word.endswith("es") and len(word) > 4:
        forms.append((word[:-1], "plural"))
        forms.append((word[:-2], "plural"))
    elif word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        forms.append((word[:-1], "plural"))
    if word.endswith("ing") and len(word) > 5:
        base = word[:-3]
        forms.append((base, "ing"))
        forms.append((base + "e", "ing"))
        if len(base) > 2 and base[-1] == base[-2]:
            forms.append((base[:-1], "ing"))
    if word.endswith("ed") and len(word) > 4:
        base = word[:-2]
        forms.append((base, "ed"))
        forms.append((base + "e", "ed"))
        if len(base) > 2 and base[-1] == base[-2]:
            forms.append((base[:-1], "ed"))
    seen = []
    for form, kind in forms:
        if form and form != word and (form, kind) not in seen:
            seen.append((form, kind))
    return seen


def choose(word: str, exact: dict[str, str], keywords: dict[str, str]) -> str:
    if word in OVERRIDES:
        return OVERRIDES[word]
    if word in DENY_AUTO:
        return ""
    if word in exact:
        return exact[word]
    return keywords.get(word, "")


def phrase_icon(phrase: str, singles: dict[str, str]) -> str:
    if phrase in OVERRIDES:
        return OVERRIDES[phrase]
    hits = []
    for part in phrase.split():
        if part in PHRASE_STOP or len(part) < 3:
            continue
        hexcode = OVERRIDES.get(part, "")
        if not hexcode:
            for form, _kind in stem_forms(part):
                hexcode = OVERRIDES.get(form, "")
                if hexcode:
                    break
        if hexcode and hexcode not in hits:
            hits.append(hexcode)
    return hits[0] if len(hits) == 1 else ""


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
    keywords = keyword_index(entries, known)
    cards = load_cards()
    base: dict[str, str] = {}
    for card in cards:
        word = (card.get("word") or "").strip().lower()
        if " " in word or not word.isascii():
            continue
        hexcode = choose(word, exact, keywords)
        if hexcode:
            base[word] = hexcode
    icons = dict(base)
    for card in cards:
        word = (card.get("word") or "").strip().lower()
        if " " in word or not word.isascii() or word in icons:
            continue
        for form, kind in stem_forms(word):
            if form not in base or form in COLOR_WORDS:
                continue
            if kind in {"ing", "ed"} and form not in VERB_LEMMAS:
                continue
            # Plurals of a phrase-head ("bars" → "bar" → chocolate) stay out.
            # Only fold onto a one-word picture or a hand-checked word.
            if kind == "plural" and form not in OVERRIDES and form not in exact:
                continue
            icons[word] = base[form]
            break
    for card in cards:
        word = (card.get("word") or "").strip().lower()
        if " " not in word or word in icons:
            continue
        hexcode = phrase_icon(word, base)
        if hexcode:
            icons[word] = hexcode
    by_level = {level: {"n": 0, "icon": 0} for level in LEVELS}
    seen_level = {level: set() for level in LEVELS}
    annotated = {entry["hexcode"]: entry["annotation"] for entry in entries}
    for card in cards:
        word = (card.get("word") or "").strip().lower()
        level = card.get("level") or ""
        if level not in by_level or " " in word or not word.isascii():
            continue
        if word in seen_level[level]:
            continue
        seen_level[level].add(word)
        by_level[level]["n"] += 1
        if word in icons:
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
    ab = by_level["A1"]["icon"] + by_level["A2"]["icon"] + by_level["B1"]["icon"] + by_level["B2"]["icon"]
    ab_n = by_level["A1"]["n"] + by_level["A2"]["n"] + by_level["B1"]["n"] + by_level["B2"]["n"]
    print(f"A1-B2 {ab}/{ab_n} {(100 * ab / ab_n) if ab_n else 0:.1f}%")
    seen = set()
    pool = []
    for card in cards:
        word = (card.get("word") or "").strip().lower()
        if card.get("level") not in {"B1", "B2"} or " " in word or word not in icons or word in seen:
            continue
        seen.add(word)
        pool.append(card)
    random.Random(23).shuffle(pool)
    print("SPOT")
    for card in pool[:50]:
        word = card["word"].lower()
        hexcode = icons[word]
        print(f"{card['level']}\t{word}\t{hexcode}\t{annotated.get(hexcode, '')}")


if __name__ == "__main__":
    main()
