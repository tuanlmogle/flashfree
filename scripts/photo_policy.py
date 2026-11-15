#!/usr/bin/env python3
"""Decide which Commons photos are safe to show first, or at all.

A photo leads Tự động mode only when the Wikipedia article title is the
word itself, the card is a noun, and the short description is not a person,
place, brand, logo, or screenshot. A different article title, or a page
about a person/place/brand, drops the photo. The decision file is committed
so later rebuilds repeat the same choice without calling Wikipedia again.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = ROOT / "data" / "raw"
OUT = DATA / "photo-confidence.json"
UA = "FlashFreeBuilder/1.0 (educational vocabulary app; https://github.com/tuanlmogle/flashfree)"

DROP_DESC = re.compile(
    r"disambiguation|topics referred to by the same term|"
    r"surname|given name|family name|birth name|"
    r"\b(actor|actress|singer|rapper|politician|footballer|businessperson|novelist|poet|painter|composer|philosopher|prophet|pharaoh)\b|"
    r"wife of|husband of|king of|queen of|in the bible|biblical|"
    r"\bborn\b|city in|town in|village in|commune in|county in|"
    r"capital city|capital of|shopping mall|shopping centre|shopping center|"
    r"retail chain|department store|corporation|company based|brand of|"
    r"\blogo\b|album by|song by|film by|television series|tv series|"
    r"video game|screenshot|screen shot",
    re.I,
)
DROP_FILE = (
    "logo", "wordmark", "screenshot", "screencap", "coat_of_arms", "locator",
    "map_of", "flag_of", "signature", "autograph", "mall", "shopping_centre",
    "shopping_center",
)


def titles_match(word: str, title: str) -> bool:
    left = (word or "").strip().lower()
    right = (title or "").strip().lower()
    if not left or not right:
        return False
    if right == left:
        return True
    if right in {left + "s", left + "es"}:
        return True
    if left.endswith("y") and right == left[:-1] + "ies":
        return True
    return False


def verdict(word: str, pos: str, info: dict | None) -> str:
    """Return drop, lead, or keep."""
    if not info:
        return "drop"
    title = info.get("title") or ""
    desc = info.get("desc") or ""
    filename = (info.get("file") or "").lower()
    if info.get("disambiguation"):
        return "drop"
    if any(bit in filename for bit in DROP_FILE):
        return "drop"
    if not titles_match(word, title):
        return "drop"
    if DROP_DESC.search(desc) or DROP_DESC.search(title):
        return "drop"
    if pos == "noun" and desc and not DROP_DESC.search(desc):
        return "lead"
    return "keep"


def load_decisions() -> dict[str, dict]:
    if not OUT.exists():
        return {}
    return json.loads(OUT.read_text(encoding="utf-8"))


def apply_to_card(card: dict, decisions: dict[str, dict]) -> str:
    """Mutate card.img. Returns drop, lead, keep, or none."""
    img = card.get("img") or {}
    if img.get("t") != "c" or not img.get("f"):
        return "none"
    word = card["word"].lower()
    info = decisions.get(word)
    action = verdict(word, card.get("pos") or "", info)
    if action == "drop":
        card.pop("img", None)
        return "drop"
    if action == "lead":
        img["lead"] = True
    else:
        img.pop("lead", None)
    card["img"] = img
    return action


def _wiki_title(word: str) -> str:
    if word.lower() == "i":
        return "I"
    return word[:1].upper() + word[1:]


def fetch_pages(words: list[str]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for start in range(0, len(words), 40):
        batch = words[start:start + 40]
        query = urllib.parse.urlencode({
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": "|".join(_wiki_title(word) for word in batch),
            "redirects": "1",
            "prop": "pageprops",
            "maxlag": "5",
        })
        request = urllib.request.Request(
            "https://en.wikipedia.org/w/api.php?" + query,
            headers={"User-Agent": UA},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
        redirects = {}
        for item in payload.get("query", {}).get("redirects") or []:
            redirects[(item.get("from") or "").lower()] = item.get("to") or ""
        pages = {}
        for page in payload.get("query", {}).get("pages") or []:
            pages[(page.get("title") or "").lower()] = page
        for word in batch:
            asked = _wiki_title(word)
            target = redirects.get(asked.lower(), asked)
            page = pages.get(target.lower()) or {}
            props = page.get("pageprops") or {}
            found[word] = {
                "title": page.get("title") or "",
                "desc": props.get("wikibase-shortdesc") or "",
                "disambiguation": "disambiguation" in props,
                "file": "",
            }
        if start % 400 == 0:
            print(f"  wiki titles {start + len(batch)}/{len(words)}")
        time.sleep(0.12)
    return found


def refresh(words_files: dict[str, str]) -> dict[str, dict]:
    """words_files maps lowercase word -> commons filename."""
    pages = fetch_pages(sorted(words_files))
    for word, filename in words_files.items():
        if word in pages:
            pages[word]["file"] = filename
    OUT.write_text(json.dumps(pages, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT.name} ({len(pages)} words)")
    return pages


if __name__ == "__main__":
    photos = {}
    for path in sorted(DATA.glob("level-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for card in payload.get("cards") or []:
            img = card.get("img") or {}
            if img.get("t") == "c" and img.get("f"):
                photos.setdefault(card["word"].lower(), img["f"])
    refresh(photos)
