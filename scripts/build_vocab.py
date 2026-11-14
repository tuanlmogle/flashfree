#!/usr/bin/env python3
"""Build data/vocab.json from sources whose licenses allow redistribution.

Downloads (cached in data/raw/, not committed):
  - Vietnamese Wiktionary via kaikki.org (CC BY-SA 4.0 and GFDL)
  - CEFR-J Vocabulary Profile 1.5 (TUFS, free with citation)
  - Octanove C1/C2 profile 1.0 (CC BY-SA 4.0)
  - Tatoeba English–Vietnamese sentences (CC BY 2.0 FR)

See DATA_SOURCES.md.
"""

from __future__ import annotations

import bz2
import csv
import gzip
import json
import re
import shutil
import sys
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "vocab.json"

UA = "LatTuBuilder/1.0 (English-Vietnamese vocabulary flashcards; educational static app)"

SOURCES = {
    "viwikt": "https://kaikki.org/viwiktionary/raw-wiktextract-data.jsonl.gz",
    "cefrj": "https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/cefrj-vocabulary-profile-1.5.csv",
    "octanove": "https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/octanove-vocabulary-profile-c1c2-1.0.csv",
    "vie": "https://downloads.tatoeba.org/exports/per_language/vie/vie_sentences_detailed.tsv.bz2",
    "links": "https://downloads.tatoeba.org/exports/per_language/vie/vie-eng_links.tsv.bz2",
    "eng": "https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences_detailed.tsv.bz2",
}

FILES = {
    "viwikt": RAW / "viwiktionary.jsonl.gz",
    "cefrj": RAW / "cefrj-vocabulary-profile-1.5.csv",
    "octanove": RAW / "octanove-vocabulary-profile-c1c2-1.0.csv",
    "vie": RAW / "vie_sentences_detailed.tsv.bz2",
    "links": RAW / "vie-eng_links.tsv.bz2",
    "eng": RAW / "eng_sentences_detailed.tsv.bz2",
}

LEVEL_RANK = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

CEFR_POS = {
    "noun": "noun",
    "verb": "verb",
    "adjective": "adj",
    "adverb": "adv",
    "pronoun": "pron",
    "preposition": "prep",
    "determiner": "det",
    "conjunction": "conj",
    "number": "num",
    "modal auxiliary": "verb",
    "be-verb": "verb",
    "do-verb": "verb",
    "have-verb": "verb",
    "interjection": "intj",
    "infinitive-to": "particle",
}

WIKI_POS = {
    "noun": "noun",
    "verb": "verb",
    "adj": "adj",
    "adjective": "adj",
    "adv": "adv",
    "adverb": "adv",
    "pron": "pron",
    "pronoun": "pron",
    "prep": "prep",
    "preposition": "prep",
    "det": "det",
    "determiner": "det",
    "article": "det",
    "conj": "conj",
    "conjunction": "conj",
    "num": "num",
    "numeral": "num",
    "number": "num",
    "intj": "intj",
    "interj": "intj",
    "interjection": "intj",
    "particle": "particle",
    "phrase": "phrase",
    "prep_phrase": "prep",
    "contraction": "contraction",
    "abbrev": "abbrev",
    "prefix": "prefix",
    "suffix": "suffix",
}

TOPIC_MAP = {
    "Work and Jobs": "work",
    "Work and jobs": "work",
    "Education": "education",
    "Objects and rooms": "home",
    "News, lifestyles and current affairs": "news",
    "Things in the town, shops and shopping": "town",
    "Food and drink": "food",
    "Travel and services vocab": "travel",
    "Hobbies and pastimes": "hobbies",
    "Hobbies and lifestyles": "hobbies",
    "Nationalities and countries": "places",
    "Family life": "family",
    "Clothes": "clothes",
    "Leisure activities": "hobbies",
    "Books and literature": "books",
    "Media": "media",
    "Film": "media",
    "Shopping": "town",
    "Personal information": "personal",
    "Ways of travelling": "travel",
    "Ways of traveling": "travel",
    "Arts": "arts",
    "Art": "arts",
    "Colours": "colours",
    "Technical and legal language": "technical",
    "Scientific development": "technical",
    "Holidays": "holidays",
    "Personal identification": "personal",
    "Free time, entertainment": "hobbies",
    "House and home, environment": "home",
    "Travel": "travel",
    "Health and body care": "health",
    "Relations with other people": "people",
    "Services": "services",
    "Language": "language",
    "Daily life": "daily",
    "Weather": "weather",
    "Places": "places",
}

TOPIC_NAMES = {
    "food": "Đồ ăn và thức uống",
    "clothes": "Quần áo",
    "family": "Gia đình",
    "education": "Giáo dục",
    "work": "Công việc",
    "travel": "Du lịch",
    "hobbies": "Sở thích và giải trí",
    "home": "Nhà cửa",
    "town": "Thành phố và mua sắm",
    "media": "Truyền thông",
    "arts": "Nghệ thuật",
    "books": "Sách và văn học",
    "personal": "Bản thân",
    "places": "Địa điểm và quốc gia",
    "colours": "Màu sắc",
    "holidays": "Ngày lễ",
    "news": "Tin tức và đời sống",
    "technical": "Khoa học và kỹ thuật",
    "health": "Sức khỏe",
    "people": "Quan hệ",
    "services": "Dịch vụ",
    "language": "Ngôn ngữ",
    "daily": "Đời sống hằng ngày",
    "weather": "Thời tiết",
}

VI_DIAC = set(
    "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
    "ùúủũụưừứửữựỳýỷỹỵđ"
    "ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢ"
    "ÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ"
)

BAD_SENSE = {"obsolete", "archaic", "dated"}
IPA_MARK = set("ˈˌəɪʊæɑɒɔɛʌθðʃʒŋɾɡɚɝɐɜɨøœ")
IPA_REJECT = set("ʹ͞āēīōūăĕŏ")


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"cached {dest.name}")
        return
    print(f"download {url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(req, timeout=180) as response, tmp.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    tmp.replace(dest)


def has_diacritic(text: str) -> bool:
    return any(ch in VI_DIAC for ch in text)


def variants(headword: str) -> list[str]:
    parts = [part.strip() for part in headword.split("/")]
    seen = []
    for part in parts:
        if part and part not in seen:
            seen.append(part)
    return seen


def topics_from(row: dict) -> list[str]:
    found = []
    for column in ("CoreInventory 1", "CoreInventory 2", "Threshold"):
        label = (row.get(column) or "").strip()
        topic = TOPIC_MAP.get(label)
        if topic and topic not in found:
            found.append(topic)
    return found


def clean_gloss(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = text.replace(" ,", ",").replace(" ;", ";")
    text = re.sub(r"\s+", " ", text).strip(" \t.;:")
    text = re.sub(r"\s+([,;])", r"\1", text)
    return text.strip()


def gloss_ok(text: str, word: str) -> bool:
    if not text or len(text) > 160:
        return False
    if "{{" in text or "}}" in text or "http" in text.lower():
        return False
    lowered = text.lower().strip()
    if lowered == word.lower():
        return False
    if lowered.startswith(("xem ", "như ", "see ", "the ", "a ", "an ", "to ", "of ")):
        return False
    if re.match(r"^(a|an|the|to|of)\b", lowered):
        return False
    letters = [ch for ch in text if ch.isalpha()]
    if len(letters) < 2 and not has_diacritic(text):
        return False
    if not has_diacritic(text):
        tokens = re.findall(r"[A-Za-zÀ-ỹ'-]+", text)
        if not tokens or len(text) > 24:
            return False
        if any(ch.isupper() for ch in text[1:]):
            return False
        if any(len(token) > 8 for token in tokens):
            return False
        stops = {
            "the", "of", "to", "and", "or", "for", "with", "from", "that", "this",
            "obsolete", "archaic", "see", "also", "plural", "form", "which",
        }
        if any(token.lower() in stops for token in tokens):
            return False
    return True


# Glosses that are explicit or not useful on a general learner card.
VULGAR_BITS = (
    "giao cấu", "giao hợp", "khiêu dâm", "mãi dâm", "dương vật", "âm hộ", "âm đạo",
    "xuất tinh", "địt", "đụ ", "lồn", "buồi", "đĩ", "làm tình", "thủ dâm",
)

# When the first Wiktionary sense is a rare homograph, prefer a gloss that
# contains one of these phrases. The phrase must already be in the source.
PREFER = {
    ("spring", "noun"): ("mùa xuân",),
    ("date", "noun"): ("ngày",),
    ("bank", "noun"): ("ngân hàng",),
    ("light", "adj"): ("nhẹ",),
    ("watch", "noun"): ("đồng hồ",),
    ("right", "adj"): ("đúng", "phải"),
    ("right", "noun"): ("bên phải", "quyền"),
    ("mean", "verb"): ("có nghĩa", "nghĩa là"),
    ("kind", "adj"): ("tử tế", "tốt"),
    ("course", "noun"): ("khóa học", "khoá học"),
    ("present", "noun"): ("quà",),
    ("state", "noun"): ("trạng thái", "tiểu bang", "nhà nước"),
    ("park", "noun"): ("công viên",),
    ("match", "noun"): ("trận đấu", "que diêm"),
    ("letter", "noun"): ("thư", "chữ cái"),
    ("term", "noun"): ("học kỳ", "kì học", "thuật ngữ"),
    ("significant", "adj"): ("quan trọng",),
    ("development", "noun"): ("phát triển",),
    ("stage", "noun"): ("sân khấu",),
    ("bank", "verb"): ("ngân hàng", "gửi"),
    ("right", "adv"): ("đúng", "ngay"),
    ("fall", "noun"): ("mùa thu",),
    ("fall", "verb"): ("rơi", "ngã"),
    ("capital", "noun"): ("thủ đô",),
    ("degree", "noun"): ("bằng",),
    ("diploma", "noun"): ("bằng",),
    ("he", "pron"): ("anh ấy", "ông ấy"),
    ("run", "verb"): ("chạy",),
    ("run", "noun"): ("sự chạy",),
    ("conversation", "noun"): ("nói chuyện", "chuyện trò"),
    ("can", "verb"): ("có thể",),
    ("will", "verb"): ("sẽ",),
    ("may", "verb"): ("có thể",),
    ("play", "verb"): ("chơi",),
    ("change", "verb"): ("thay đổi", "đổi"),
    ("change", "noun"): ("thay đổi", "sự đổi"),
    ("interest", "noun"): ("quan tâm", "hứng thú"),
    ("issue", "noun"): ("vấn đề",),
    ("train", "noun"): ("tàu hỏa", "tàu hoả", "xe lửa"),
    ("trip", "noun"): ("chuyến đi", "cuộc đi"),
    ("rock", "noun"): ("đá",),
    ("rest", "verb"): ("nghỉ",),
    ("rest", "noun"): ("nghỉ ngơi", "sự nghỉ"),
    ("fair", "adj"): ("công bằng",),
    ("fine", "adj"): ("tốt",),
    ("lie", "verb"): ("nói dối",),
    ("hard", "adj"): ("khó",),
    ("sound", "noun"): ("âm thanh", "tiếng"),
    ("point", "noun"): ("điểm",),
    ("place", "noun"): ("nơi", "chỗ", "địa điểm"),
    ("figure", "noun"): ("con số", "hình"),
    ("subject", "noun"): ("chủ đề", "môn"),
    ("address", "noun"): ("địa chỉ",),
    ("bear", "noun"): ("gấu",),
    ("study", "verb"): ("học",),
    ("work", "verb"): ("làm việc",),
    ("work", "noun"): ("công việc",),
    ("watch", "verb"): ("xem",),
    ("miss", "verb"): ("nhớ", "bỏ lỡ"),
    ("light", "noun"): ("ánh sáng",),
    ("left", "noun"): ("bên trái", "phía bên trái"),
    ("left", "adj"): ("trái",),
    ("record", "verb"): ("ghi",),
    ("book", "verb"): ("đặt chỗ", "giữ chỗ"),
    ("check", "verb"): ("kiểm tra",),
    ("patient", "noun"): ("bệnh nhân",),
    ("patient", "adj"): ("kiên nhẫn",),
    ("novel", "noun"): ("tiểu thuyết",),
    ("novel", "adj"): ("mới",),
    ("object", "noun"): ("vật", "đồ vật"),
    ("stick", "noun"): ("cái gậy", "cây gậy"),
    ("stick", "verb"): ("dán",),
    ("suit", "noun"): ("bộ com", "bộ vest", "kiện"),
    ("wave", "noun"): ("sóng",),
    ("band", "noun"): ("ban nhạc", "dải"),
    ("club", "noun"): ("câu lạc bộ",),
    ("pool", "noun"): ("bể bơi", "hồ bơi"),
    ("ring", "noun"): ("chiếc nhẫn", "nhẫn", "vòng"),
    ("sentence", "noun"): ("câu",),
}


def vulgar(text: str) -> bool:
    lowered = text.lower()
    return any(bit in lowered for bit in VULGAR_BITS)


def tidy_meaning(text: str) -> str:
    text = text.replace("&", " ")
    text = text.replace("(", " ").replace(")", " ")
    text = re.sub(r"\s+", " ", text).strip(" \t.;:,/")
    segments = []
    seen = set()
    for segment in re.split(r"\s*;\s*", text):
        bits = []
        bit_seen = set()
        for bit in re.split(r"\s*,\s*", segment):
            bit = bit.strip(" \t.;:,/")
            key = bit.lower()
            if not bit or key in bit_seen:
                continue
            bit_seen.add(key)
            bits.append(bit)
        segment = ", ".join(bits)
        key = segment.lower()
        if not segment or key in seen:
            continue
        seen.add(key)
        segments.append(segment)
    return "; ".join(segments)


def nice_meaning(text: str) -> str:
    text = tidy_meaning(text)
    if not text:
        return text
    return text[0].upper() + text[1:]


def prepare_gloss(text: str) -> str:
    text = clean_gloss(text)
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" \t.;:,+/")
    return text


def shorten(text: str) -> str:
    if len(text) <= 72:
        return text
    cut = text[:72]
    for sep in (";", ","):
        index = cut.rfind(sep)
        if index >= 18:
            return cut[:index].rstrip(" ,;")
    return cut.rstrip(" ,;")


def niche_stub(original: str, cleaned: str) -> bool:
    """Skip a one-word gloss that only survived by deleting a domain note."""
    if "(" not in original:
        return False
    return " " not in cleaned and len(cleaned) <= 12


def gloss_candidates(entries: list[dict], word: str) -> list[tuple[int, int, str]]:
    found = []
    for entry_index, entry in enumerate(entries):
        for sense_index, item in enumerate(entry["glosses"][:8]):
            if item.get("slang"):
                continue
            text = prepare_gloss(item["text"])
            if not text or text[0] in "+,;/:":
                continue
            if niche_stub(item["text"], text) or not gloss_ok(text, word) or vulgar(text):
                continue
            found.append((entry_index, sense_index, text))
    return found


def pick_meaning(entries: list[dict], word: str, pos: str) -> tuple[str | None, list]:
    candidates = gloss_candidates(entries, word)
    if not candidates:
        return None, []
    preferred = PREFER.get((word.lower(), pos), ())
    if preferred:
        hits = [item for item in candidates if any(phrase in item[2].lower() for phrase in preferred)]
        if hits:
            hits.sort(key=lambda item: (item[1], len(item[2]), item[0]))
            entry_index, _, text = hits[0]
            return nice_meaning(shorten(text)), entries[entry_index]["ipas"]
    # Main etymology first, and the earliest plain sense inside it.
    candidates.sort(key=lambda item: (item[0], item[1], len(item[2])))
    entry_index, _, text = candidates[0]
    return nice_meaning(shorten(text)), entries[entry_index]["ipas"]


def good_ipa(text: str) -> bool:
    if not text or len(text) > 46:
        return False
    if any(ch in IPA_REJECT for ch in text):
        return False
    if not any(ch in IPA_MARK for ch in text):
        return False
    allowed = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        "ɑɒæɐəɚɝɛɜɪɔʊʌɨøœʏːˑˈˌ.̯̩̥̬̃ʰʲʷθðʃʒŋɡɣβɾɹɻɽɴʔçʝxɥ()[]/ "
    )
    return all(ch in allowed for ch in text)


def pick_ipa(candidates: list[tuple[int, str]]) -> str | None:
    cleaned = []
    seen = set()
    for rank, raw in candidates:
        text = raw.strip().strip("/").strip("[]").strip()
        if not good_ipa(text):
            continue
        key = text
        if key in seen:
            continue
        seen.add(key)
        stress = 0 if "ˈ" in text else 1
        cleaned.append((rank, stress, len(text), text))
    if not cleaned:
        return None
    cleaned.sort()
    return cleaned[0][3]


def ipa_rank(sound: dict) -> int:
    tags = " ".join((sound.get("tags") or []) + (sound.get("raw_tags") or [])).lower()
    if any(mark in tags for mark in ("mỹ", "mĩ", "us", "american", "genam")):
        return 0
    if any(mark in tags for mark in ("uk", "british", "anh-anh", "rp")):
        return 2
    return 1


def wanted_lemmas(rows: list[dict]) -> set[str]:
    lemmas = set()
    for row in rows:
        for variant in variants(row["headword"]):
            lemmas.add(variant.lower())
    return lemmas


def load_level_rows() -> list[dict]:
    rows = []
    with FILES["cefrj"].open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("CEFR") in LEVEL_RANK and row.get("headword") and row.get("pos"):
                rows.append(row)
    with FILES["octanove"].open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("CEFR") in {"C1", "C2"} and row.get("headword") and row.get("pos"):
                rows.append(
                    {
                        "headword": row["headword"],
                        "pos": row["pos"],
                        "CEFR": row["CEFR"],
                        "CoreInventory 1": "",
                        "CoreInventory 2": "",
                        "Threshold": "",
                    }
                )
    return rows


def load_wiktionary(lemmas: set[str]) -> dict[str, list[dict]]:
    bank = defaultdict(list)
    parsed = 0
    with gzip.open(FILES["viwikt"], "rt", encoding="utf-8") as handle:
        for line in handle:
            if '"lang_code": "en"' not in line[:500] and '"lang_code":"en"' not in line[:500]:
                continue
            match = re.match(r'\{"word": "([^"\\]+)"', line)
            if not match:
                continue
            word = match.group(1)
            if word.lower() not in lemmas:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("lang_code") != "en":
                continue
            parsed += 1
            pos = WIKI_POS.get((entry.get("pos") or "").lower())
            if not pos or pos in {"prefix", "suffix", "abbrev"}:
                continue
            entry_tags = set(entry.get("tags") or [])
            if entry_tags & BAD_SENSE:
                continue
            glosses = []
            for sense in entry.get("senses") or []:
                sense_tags = set(sense.get("tags") or [])
                if sense_tags & BAD_SENSE:
                    continue
                slang = bool(sense_tags & {"slang", "vulgar", "offensive"})
                for gloss in sense.get("glosses") or []:
                    if isinstance(gloss, str):
                        glosses.append({"text": gloss, "slang": slang})
            ipas = []
            for sound in entry.get("sounds") or []:
                ipa = sound.get("ipa")
                if isinstance(ipa, str):
                    ipas.append((ipa_rank(sound), ipa))
            if glosses or ipas:
                bank[word.lower()].append({"pos": pos, "glosses": glosses, "ipas": ipas})
    print(f"wiktionary entries kept for CEFR lemmas: {parsed}; lemmas with data: {len(bank)}")
    return bank


def lookup(bank: dict, variant: str, pos: str) -> list[dict]:
    entries = bank.get(variant.lower(), [])
    exact = [entry for entry in entries if entry["pos"] == pos]
    if exact:
        return exact
    if pos == "particle":
        return [entry for entry in entries if entry["pos"] in {"particle", "prep", "adv"}]
    if " " in variant:
        return [entry for entry in entries if entry["pos"] in {"phrase", "noun", "verb", "prep", "adv", "conj"}]
    return []


def display_word(variant: str) -> str:
    if variant.lower() == "i":
        return "I"
    return variant


def slug(word: str, pos: str) -> str:
    text = word.lower().replace("'", "").replace(" ", "-")
    text = re.sub(r"[^a-z0-9.-]+", "", text)
    text = re.sub(r"-{2,}", "-", text).strip("-.")
    return f"{text}-{pos}" if text else f"word-{pos}"


def build_cards(rows: list[dict], bank: dict) -> list[dict]:
    cards = {}
    missed = defaultdict(int)
    for row in rows:
        level = row["CEFR"]
        pos = CEFR_POS.get((row.get("pos") or "").strip().lower())
        if not pos or level not in LEVEL_RANK:
            missed["bad-pos"] += 1
            continue
        match = None
        matched_variant = None
        alts = []
        for variant in variants(row["headword"]):
            if len(variant) == 1 and variant.lower() not in {"a", "i"}:
                continue
            found = lookup(bank, variant, pos)
            if found and match is None:
                match = found
                matched_variant = variant
            elif variant.lower() != (matched_variant or "").lower():
                alts.append(variant)
        if not match or not matched_variant:
            missed[level] += 1
            continue
        meaning, ipas = pick_meaning(match, matched_variant, pos)
        if not meaning:
            missed[level] += 1
            continue
        word = display_word(matched_variant)
        key = (word.lower(), pos)
        topic_ids = topics_from(row)
        also = []
        for alt in alts:
            shown = display_word(alt)
            if shown.lower() != word.lower() and shown not in also:
                also.append(shown)
        existing = cards.get(key)
        if existing is None:
            cards[key] = {
                "word": word,
                "pos": pos,
                "level": level,
                "meaning": meaning,
                "ipa": pick_ipa(ipas),
                "topics": topic_ids,
                "also": also[:2],
            }
            continue
        if LEVEL_RANK[level] < LEVEL_RANK[existing["level"]]:
            existing["level"] = level
        for topic in topic_ids:
            if topic not in existing["topics"]:
                existing["topics"].append(topic)
        for alt in also:
            if alt not in existing["also"] and alt.lower() != existing["word"].lower():
                existing["also"].append(alt)
        existing["also"] = existing["also"][:2]
    print("unmatched or rejected", dict(missed))
    built = []
    used_ids = set()
    for item in cards.values():
        card_id = slug(item["word"], item["pos"])
        if card_id in used_ids:
            suffix = 2
            while f"{card_id}-{suffix}" in used_ids:
                suffix += 1
            card_id = f"{card_id}-{suffix}"
        used_ids.add(card_id)
        card = {
            "id": card_id,
            "word": item["word"],
            "pos": item["pos"],
            "level": item["level"],
            "meaning": item["meaning"],
        }
        if item["ipa"]:
            card["ipa"] = item["ipa"]
        if item["topics"]:
            card["topics"] = item["topics"]
        if item["also"]:
            card["also"] = item["also"]
        built.append(card)
    return built


def forms_of(lemma: str) -> set[str]:
    lemma = lemma.lower()
    found = {lemma}
    if " " in lemma or len(lemma) < 4:
        return found
    found.update({lemma + "s", lemma + "es", lemma + "ed", lemma + "ing", lemma + "d"})
    if lemma.endswith("e"):
        found.add(lemma[:-1] + "ing")
        found.add(lemma[:-1] + "ed")
    if lemma.endswith("y") and lemma[-2] not in "aeiou":
        found.add(lemma[:-1] + "ies")
        found.add(lemma[:-1] + "ied")
    if (
        len(lemma) > 4
        and lemma[-1] not in "aeiouy"
        and lemma[-2] in "aeiou"
        and lemma[-3] not in "aeiou"
    ):
        found.add(lemma + lemma[-1] + "ed")
        found.add(lemma + lemma[-1] + "ing")
    return {form for form in found if form.isalpha()}


def sentence_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", text.lower())


def load_examples(cards: list[dict]) -> dict[str, dict]:
    needed = {}
    for card in cards:
        for form in forms_of(card["word"]):
            needed.setdefault(form, set()).add(card["id"])
    link_pairs = []
    eng_ids = set()
    with bz2.open(FILES["links"], "rt", encoding="utf-8") as handle:
        for line in handle:
            vie_id, eng_id = line.rstrip("\n").split("\t")[:2]
            link_pairs.append((int(vie_id), int(eng_id)))
            eng_ids.add(int(eng_id))
    vie_text = {}
    with bz2.open(FILES["vie"], "rt", encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            try:
                sid = int(parts[0])
            except ValueError:
                continue
            vie_text[sid] = parts[2]
    eng_rows = {}
    with bz2.open(FILES["eng"], "rt", encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            try:
                sid = int(parts[0])
            except ValueError:
                continue
            if sid not in eng_ids:
                continue
            author = parts[3]
            if author in {"\\N", r"\N", "NULL"}:
                author = None
            eng_rows[sid] = (parts[2], author)
    sentences = []
    index = defaultdict(list)
    for vie_id, eng_id in link_pairs:
        english = eng_rows.get(eng_id)
        vietnamese = vie_text.get(vie_id)
        if not english or not vietnamese:
            continue
        text, author = english
        if not has_diacritic(vietnamese):
            continue
        if "http" in text.lower() or "@" in text or len(text) > 160:
            continue
        if text.isupper():
            continue
        tokens = sentence_tokens(text)
        if not 3 <= len(tokens) <= 18:
            continue
        record = {
            "en": text.strip(),
            "vi": vietnamese.strip(),
            "id": eng_id,
            "author": author,
            "tokens": tokens,
            "n": len(tokens),
        }
        position = len(sentences)
        sentences.append(record)
        for token in set(tokens):
            if token in needed:
                index[token].append(position)
    print(f"tatoeba candidate sentences: {len(sentences)}")
    chosen = {}
    for card in cards:
        lemma = card["word"].lower()
        exact_forms = {lemma}
        extra_forms = forms_of(card["word"]) - exact_forms
        pool = []
        seen = set()
        for form in exact_forms | extra_forms:
            for position in index.get(form, []):
                if position in seen:
                    continue
                seen.add(position)
                pool.append((form in exact_forms, sentences[position]))
        best = None
        best_key = None
        for exact, sentence in pool:
            score = 8 if exact else 3
            if 6 <= sentence["n"] <= 12:
                score += 4
            elif sentence["n"] <= 15:
                score += 1
            if any(ch.isdigit() for ch in sentence["en"]):
                score -= 2
            if sentence["en"].count(",") > 1:
                score -= 1
            key = (score, -sentence["n"], -sentence["id"])
            if best_key is None or key > best_key:
                best_key = key
                best = sentence
        if best and best_key and best_key[0] >= 6:
            payload = {"id": best["id"], "en": best["en"], "vi": best["vi"]}
            if best["author"]:
                payload["author"] = best["author"]
            chosen[card["id"]] = payload
    print(f"cards with a Tatoeba example: {len(chosen)}")
    return chosen


def prune_topics(cards: list[dict]) -> list[dict]:
    counts = defaultdict(int)
    for card in cards:
        for topic in card.get("topics") or []:
            counts[topic] += 1
    kept = {topic for topic, count in counts.items() if count >= 12 and topic in TOPIC_NAMES}
    for card in cards:
        topics = [topic for topic in card.get("topics") or [] if topic in kept]
        if topics:
            card["topics"] = topics
        else:
            card.pop("topics", None)
    ordered = sorted(kept, key=lambda topic: TOPIC_NAMES[topic])
    return [{"id": topic, "name": TOPIC_NAMES[topic], "count": counts[topic]} for topic in ordered]


def main() -> None:
    for key, url in SOURCES.items():
        download(url, FILES[key])
    rows = load_level_rows()
    print(f"level rows: {len(rows)}")
    bank = load_wiktionary(wanted_lemmas(rows))
    cards = build_cards(rows, bank)
    examples = load_examples(cards)
    for card in cards:
        example = examples.get(card["id"])
        if not example:
            continue
        card["example"] = example["en"]
        card["exampleVi"] = example["vi"]
        ref = {"id": example["id"]}
        if example.get("author"):
            ref["author"] = example["author"]
        card["tatoeba"] = ref
    topics = prune_topics(cards)
    cards.sort(key=lambda card: (LEVEL_RANK[card["level"]], card["word"].lower(), card["pos"]))
    counts = {level: 0 for level in LEVEL_RANK}
    ipa_n = example_n = 0
    for card in cards:
        counts[card["level"]] += 1
        ipa_n += "ipa" in card
        example_n += "example" in card
    payload = {
        "generated": date.today().isoformat(),
        "counts": counts,
        "total": len(cards),
        "withIpa": ipa_n,
        "withExample": example_n,
        "levels": list(LEVEL_RANK),
        "topics": topics,
        "cards": cards,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    print("counts", counts, "total", len(cards), "ipa", ipa_n, "examples", example_n)
    print("topics", [(item["id"], item["count"]) for item in topics])
    # Spot-check a few familiar lemmas and a slice of each level.
    wanted = {"abandon", "apple", "water", "development", "beautiful", "because", "run", "significant"}
    print("--- spot check ---")
    for card in cards:
        if card["word"].lower() in wanted:
            print(card["level"], card["pos"], card["word"], card.get("ipa"), "|", card["meaning"][:90])
    by_level = defaultdict(list)
    for card in cards:
        by_level[card["level"]].append(card)
    print("--- samples ---")
    for level, group in by_level.items():
        step = max(1, len(group) // 5)
        for card in group[::step][:5]:
            print(f"{level}\t{card['word']}\t{card['pos']}\t{card['meaning'][:70]}")
    if len(cards) < 1500 or counts["B1"] < 400 or counts["B2"] < 400:
        print("ERROR: coverage below the first-version target", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
