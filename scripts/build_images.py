#!/usr/bin/env python3
"""Attach OpenMoji icons and Wikimedia Commons photos to vocabulary cards.

OpenMoji 17 (CC BY-SA 4.0) covers a wide set of concrete words. For nouns,
a Wikipedia lead image is used when the page is not a disambiguation and the
Commons file has a free license we can attribute. Thumbnails are not stored
in the repo; cards keep a short mapping and the app requests a 320px preview.
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DATA = ROOT / "data"
UA = "FlashFreeBuilder/1.0 (educational vocabulary app; https://github.com/tuanlmogle/flashfree)"
OPENMOJI = "17.0.0"

GENERIC = {
    "face", "person", "people", "man", "woman", "boy", "girl", "child", "happy",
    "smile", "red", "blue", "green", "yellow", "black", "white", "object",
    "symbol", "sign", "button", "hand", "skin", "tone", "fun", "cool", "nice",
    "good", "bad", "big", "small", "new", "old", "love", "icon", "square",
    "circle", "arrow", "right", "left", "open", "close", "one", "two", "three",
    "group", "thing", "stuff", "color", "colour", "light", "dark",
}

DENY_DESC = re.compile(
    r"\b(surname|given name|family name|fictional character|album by|song by|"
    r"single by|film by|directed by|television series|tv series|episode|"
    r"disambiguation|wikimedia|list of|magazine|newspaper|video game|novel by|"
    r"band from|singer|actor|actress|politician|footballer|businessperson|"
    r"corporation|company based|born \d)\b",
    re.I,
)
BAD_FILE = (
    "logo", "signature", "autograph", "coat_of_arms", "locator_map", "map_of",
    "pictogram", "diagram_of", "icon_", "wordmark", "seal_of",
)


def load_cards() -> list[tuple[str, dict]]:
    found = []
    for path in sorted(DATA.glob("level-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for card in payload.get("cards") or []:
            found.append((path.name, card))
    return found


def openmoji_index() -> dict[str, dict]:
    path = RAW / "openmoji.json"
    if not path.exists():
        url = f"https://raw.githubusercontent.com/hfg-gmuend/openmoji/{OPENMOJI}/data/openmoji.json"
        path.write_bytes(fetch(url))
    items = json.loads(path.read_text(encoding="utf-8"))
    buckets: dict[str, list[dict]] = {}

    def add(key: str, item: dict, weight: int) -> None:
        key = key.strip().lower()
        if not key or key in GENERIC or len(key) < 2:
            return
        buckets.setdefault(key, []).append((weight, item))

    for item in items:
        if item.get("skintone") or item.get("skintone_combination"):
            continue
        hexcode = item.get("hexcode") or ""
        if any(tone in hexcode for tone in ("1F3FB", "1F3FC", "1F3FD", "1F3FE", "1F3FF")):
            continue
        record = {"t": "o", "h": hexcode, "a": item.get("openmoji_author") or "OpenMoji", "order": item.get("order") or 9999}
        annotation = (item.get("annotation") or "").lower().strip()
        add(annotation, record, 0)
        for tag in (item.get("tags") or "").split(","):
            tag = tag.strip().lower()
            if " " in tag:
                continue
            add(tag, record, 2)
        tokens = annotation.split()
        if 1 <= len(tokens) <= 3 and tokens[-1] not in GENERIC:
            add(tokens[-1], record, 3 if len(tokens) > 1 else 1)
    chosen = {}
    for key, group in buckets.items():
        group.sort(key=lambda pair: (pair[0], pair[1]["order"], len(pair[1]["h"])))
        best = group[0][1]
        chosen[key] = {"t": "o", "h": best["h"], "a": best["a"]}
    print(f"openmoji keys: {len(chosen)}")
    return chosen


def fetch(url: str, retries: int = 4) -> bytes:
    delay = 1.2
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code in {429, 503} and attempt + 1 < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except urllib.error.URLError:
            if attempt + 1 < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError(f"failed {url}")


def wiki_title(word: str) -> str:
    if word.lower() == "i":
        return "I"
    return word[:1].upper() + word[1:]


def license_code(name: str) -> str | None:
    text = (name or "").lower()
    if any(bit in text for bit in ("noncommercial", "non-commercial", "-nc", "noderiv", "-nd", "all rights")):
        return None
    if "cc0" in text or ("zero" in text and "creative commons" in text):
        return "cc0"
    if "public domain" in text or "no restrictions" in text or text.strip() in {"pd", "pdm"}:
        return "pd"
    if "gfdl" in text or "free documentation" in text:
        return "gfdl-1.2" if "1.2" in text else "gfdl-1.3"
    share = "share" in text or "-sa" in text or "sa " in text
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    version = match.group(1) if match else "4.0"
    if version.endswith(".0"):
        version = version[:-2]
    if "attribution" in text or "cc by" in text or text.startswith("by") or " by " in text or "creative commons" in text:
        return ("by-sa-" if share else "by-") + version
    return None


def clean_author(raw: str, username: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip(" \t-–—|,;/")
    text = re.sub(r"(?i)^(creator|author|photographer)\s*:\s*", "", text).strip()
    if re.search(r"https?://|\{|\}|wikimedia|permission|description", text, re.I) or not 2 <= len(text) <= 80:
        text = ""
    if text:
        return text
    if username and username.lower() not in {"", "flickr", "unknown"}:
        return username
    return "Wikimedia Commons"


def file_ok(name: str, word: str) -> bool:
    lowered = name.lower()
    if any(bit in lowered for bit in BAD_FILE):
        return False
    if "flag" in lowered and word.lower() not in {"flag", "banner"}:
        return False
    return True


def cached_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def wiki_lookup(words: list[str], cache: dict) -> None:
    pending = [word for word in words if word not in cache]
    print(f"wikipedia lookups: {len(pending)}")
    for start in range(0, len(pending), 40):
        batch = pending[start:start + 40]
        titles = "|".join(wiki_title(word) for word in batch)
        query = urllib.parse.urlencode({
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": titles,
            "redirects": "1",
            "prop": "pageimages|pageprops",
            "piprop": "name|thumbnail",
            "pithumbsize": "320",
            "pilimit": "50",
            "maxlag": "5",
        })
        try:
            payload = json.loads(fetch("https://en.wikipedia.org/w/api.php?" + query))
        except Exception as error:
            print("wiki batch failed", error)
            time.sleep(2)
            continue
        redirects = {}
        for item in payload.get("query", {}).get("redirects") or []:
            redirects[item.get("from", "").lower()] = item.get("to", "")
        pages = {}
        for page in payload.get("query", {}).get("pages") or []:
            pages[page.get("title", "").lower()] = page
        for word in batch:
            title = wiki_title(word)
            target = redirects.get(title.lower(), title).lower()
            page = pages.get(target) or pages.get(title.lower())
            cache[word] = page_record(word, page)
        if start % 400 == 0:
            save_json(RAW / "wiki-pages.json", cache)
            print(f"  wiki {start + len(batch)}/{len(pending)}")
        time.sleep(0.12)
    save_json(RAW / "wiki-pages.json", cache)


def page_record(word: str, page: dict | None) -> dict | None:
    if not page or page.get("missing") or page.get("invalid"):
        return None
    props = page.get("pageprops") or {}
    if "disambiguation" in props:
        return None
    desc = props.get("wikibase-shortdesc") or ""
    if DENY_DESC.search(desc):
        return None
    filename = props.get("page_image_free") or page.get("pageimage")
    thumb = page.get("thumbnail") or {}
    if not filename or not file_ok(filename, word):
        return None
    width = thumb.get("width") or 0
    height = thumb.get("height") or 0
    if width and height:
        ratio = width / height
        if height < 70 or ratio > 3.1 or ratio < 0.32:
            return None
    return {"f": filename.replace(" ", "_"), "d": desc[:140]}


def commons_lookup(files: list[str], cache: dict) -> None:
    pending = [name for name in files if name not in cache]
    print(f"commons metadata: {len(pending)}")
    for start in range(0, len(pending), 40):
        batch = pending[start:start + 40]
        query = urllib.parse.urlencode({
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": "|".join(f"File:{name}" for name in batch),
            "prop": "imageinfo",
            "iiprop": "user|extmetadata",
            "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl",
            "maxlag": "5",
        })
        try:
            payload = json.loads(fetch("https://commons.wikimedia.org/w/api.php?" + query))
        except Exception as error:
            print("commons batch failed", error)
            time.sleep(2)
            continue
        by_title = {}
        for page in payload.get("query", {}).get("pages") or []:
            title = (page.get("title") or "").lower().replace(" ", "_")
            if title.startswith("file:"):
                title = title[5:]
            by_title[title] = page
        for name in batch:
            page = by_title.get(name.lower().replace(" ", "_"))
            cache[name] = commons_record(page)
        if start % 400 == 0:
            save_json(RAW / "commons-meta.json", cache)
            print(f"  commons {start + len(batch)}/{len(pending)}")
        time.sleep(0.12)
    save_json(RAW / "commons-meta.json", cache)


def commons_record(page: dict | None) -> dict | None:
    if not page or page.get("missing"):
        return None
    info = (page.get("imageinfo") or [None])[0] or {}
    meta = info.get("extmetadata") or {}
    license_name = (meta.get("LicenseShortName") or {}).get("value") or ""
    code = license_code(license_name)
    if not code:
        return None
    author = clean_author((meta.get("Artist") or {}).get("value") or "", info.get("user") or "")
    return {"a": author, "l": code}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    cards = load_cards()
    icons = openmoji_index()
    nouns = []
    seen = set()
    level_rank = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}
    ordered = sorted(cards, key=lambda pair: level_rank.get(pair[1].get("level"), 9))
    for _, card in ordered:
        if card.get("pos") != "noun":
            continue
        word = card["word"].lower()
        if " " in word or word in seen:
            continue
        seen.add(word)
        nouns.append(word)
    wiki_cache = cached_json(RAW / "wiki-pages.json")
    wiki_lookup(nouns, wiki_cache)
    files = []
    seen_files = set()
    for word in nouns:
        record = wiki_cache.get(word)
        if record and record.get("f") and record["f"] not in seen_files:
            seen_files.add(record["f"])
            files.append(record["f"])
    commons_cache = cached_json(RAW / "commons-meta.json")
    commons_lookup(files, commons_cache)

    images: dict[str, dict] = {}
    open_n = commons_n = 0
    for _, card in cards:
        word = card["word"].lower()
        if word not in images and word in icons:
            images[word] = icons[word]
            open_n += 1
    skip_commons = {
        "hello", "information", "nothing", "sign", "idea", "word", "memory", "brush",
        "size", "number", "cartoon", "hope", "chirp", "addition", "clerk", "must",
        "blue", "present", "time", "four", "vote", "cry", "water", "could", "mind",
        "sight", "december", "week", "being", "area", "force", "research",
        "creativity", "chart", "leg", "a", "i",
    }
    for word in nouns:
        if word in skip_commons:
            continue
        page = wiki_cache.get(word) or {}
        meta = commons_cache.get(page.get("f") or "")
        if not page or not meta:
            continue
        filename = page["f"]
        if filename.lower().endswith(".svg"):
            folded = filename.lower().replace("_", " ").replace("-", " ")
            if word not in folded.split() and word not in folded:
                continue
        images[f"{word}|noun"] = {"t": "c", "f": filename, "a": meta["a"], "l": meta["l"]}
        commons_n += 1
    save_json(RAW / "images.json", images)
    print(f"openmoji words {open_n}, commons nouns {commons_n}")

    per_level = {level: 0 for level in level_rank}
    totals = {level: 0 for level in level_rank}
    for name, card in cards:
        word = card["word"].lower()
        image = images.get(f"{word}|{card.get('pos')}") or images.get(word)
        if image:
            card["img"] = image
            per_level[card["level"]] += 1
        else:
            card.pop("img", None)
        totals[card["level"]] += 1
    grouped: dict[str, list] = {}
    for name, card in cards:
        grouped.setdefault(name, []).append(card)
    for name, group in grouped.items():
        path = DATA / name
        path.write_text(json.dumps({"cards": group}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    meta_path = DATA / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["withImage"] = sum(per_level.values())
    meta["imageCounts"] = per_level
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("image counts", per_level, "of", totals)
    review = []
    for _, card in cards:
        if card.get("level") in {"A1", "A2"} and card.get("pos") == "noun" and (card.get("img") or {}).get("t") == "c":
            page = wiki_cache.get(card["word"].lower()) or {}
            review.append(f"{card['level']}\t{card['word']}\t{page.get('d','')}\t{card['img'].get('f')}\t{card['img'].get('a')}\t{card['img'].get('l')}")
    (RAW / "image-review.tsv").write_text("\n".join(review), encoding="utf-8")
    print(f"review rows {len(review)}")


if __name__ == "__main__":
    main()
