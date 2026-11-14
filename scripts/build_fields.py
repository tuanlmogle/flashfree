#!/usr/bin/env python3
"""Add specialised vocabulary and profession topics without changing card ids.

New cards are written to data/fields/<id>.json and loaded by the app only
when that topic is opened (or in the background after the first screen).
Existing cards stay in data/level-*.json. This script only adds topic tags
to them.

Sources, all openly licensed:
  - NGSL, NAWL, BSL, TSL (Browne, Culligan, Phillips), CC BY-SA 4.0
  - English Wikipedia glossary pages, CC BY-SA 4.0
  - English Wiktionary appendix glossaries via the parse API, CC BY-SA
  - Open English WordNet 2024 hyponyms and definitions, CC BY 4.0
  - MeSH 2025 descriptors, US National Library of Medicine, public domain
  - Vietnamese Wiktionary via kaikki.org, CC BY-SA 4.0 and GFDL
  - Tatoeba examples, CC BY 2.0 FR
  - wordfreq Zipf (Robyn Speer), CC BY-SA 4.0, for levels that are not
    already in CEFR-J or Octanove

Official CEFR-J / Octanove levels win. Other terms use the same Zipf bands
as build_vocab.level_from_zipf.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_pictures  # noqa: E402
import build_vocab  # noqa: E402
from topics import SEEDS, topic_levels  # noqa: E402
from wordfreq import zipf_frequency  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
FIELDS_DIR = DATA / "fields"
GLOSS_DIR = RAW / "glossaries"
NGSL_DIR = RAW / "ngsl"
MESH_PATH = RAW / "mesh-d2025.bin"
UA = "FlashFreeBuilder/1.0 (educational vocabulary app; github.com/tuanlmogle/flashfree)"

MAX_TOPICS = 6
# Per existing topic: tag this many hyponyms already in the deck, and add
# this many new lemmas (a mix of common and rarer ones).
TAG_CAP = 450
NEW_PER_TOPIC = 70
NEW_PER_FIELD_SEED = 80
GLOSSARY_CAP = 180
MESH_CAP = {"anatomy": 200, "disease": 200, "pharmacy": 120, "dental": 140, "nursing": 80}

FIELDS = [
    ("field-econ", "Kinh tế"),
    ("field-finance", "Tài chính - ngân hàng"),
    ("field-accounting", "Kế toán"),
    ("field-marketing", "Marketing"),
    ("field-management", "Kinh doanh - quản trị"),
    ("field-hr", "Nhân sự"),
    ("field-realestate", "Bất động sản"),
    ("field-law", "Luật"),
    ("field-health", "Y tế"),
    ("field-nursing", "Điều dưỡng"),
    ("field-pharmacy", "Dược"),
    ("field-dental", "Nha khoa"),
    ("field-physics", "Khoa học · Vật lý"),
    ("field-chemistry", "Khoa học · Hóa học"),
    ("field-biology", "Khoa học · Sinh học"),
    ("field-engineering", "Kỹ thuật chung"),
    ("field-construction", "Xây dựng"),
    ("field-mechanical", "Cơ khí"),
    ("field-electrical", "Điện - điện tử"),
    ("field-it", "Công nghệ thông tin"),
    ("field-logistics", "Logistics - vận tải"),
    ("field-hospitality", "Nhà hàng - khách sạn"),
    ("field-tourism", "Du lịch"),
    ("field-education", "Giáo dục"),
    ("field-agriculture", "Nông nghiệp"),
    ("field-environment", "Môi trường"),
    ("field-media", "Truyền thông - báo chí"),
    ("field-aviation", "Hàng không"),
    ("field-manufacturing", "Sản xuất"),
    ("field-retail", "Bán lẻ"),
    ("field-beauty", "Nail - làm đẹp"),
    ("field-culinary", "Đầu bếp"),
]

# (host, page title, topic ids). Missing pages are skipped.
GLOSSARIES = [
    ("en.wikipedia.org", "Glossary of economics", ["field-econ", "field-finance", "money"]),
    ("en.wikipedia.org", "Glossary of medicine", ["field-health", "medicine", "health"]),
    ("en.wikipedia.org", "Glossary of physics", ["field-physics", "science"]),
    ("en.wikipedia.org", "Glossary of chemistry terms", ["field-chemistry", "science"]),
    ("en.wikipedia.org", "Glossary of biology", ["field-biology", "science"]),
    ("en.wikipedia.org", "Glossary of civil engineering", ["field-construction", "field-engineering"]),
    ("en.wikipedia.org", "Glossary of computer science", ["field-it", "computers"]),
    ("en.wikipedia.org", "Glossary of ecology", ["field-environment", "environment"]),
    ("en.wikipedia.org", "Glossary of electrical and electronics engineering", ["field-electrical", "field-engineering"]),
    ("en.wikipedia.org", "Glossary of journalism", ["field-media", "media"]),
    ("en.wikipedia.org", "Glossary of law", ["field-law", "law"]),
    ("en.wikipedia.org", "Glossary of mechanical engineering", ["field-mechanical", "field-engineering"]),
    ("en.wikipedia.org", "Glossary of engineering", ["field-engineering"]),
    ("en.wikipedia.org", "Glossary of engineering: A–L", ["field-engineering"]),
    ("en.wikipedia.org", "Glossary of engineering: M–Z", ["field-engineering"]),
    ("en.wikipedia.org", "Glossary of structural engineering", ["field-construction", "field-engineering"]),
    ("en.wikipedia.org", "Glossary of education terms (A–C)", ["field-education", "education"]),
    ("en.wikipedia.org", "Glossary of education terms (D–F)", ["field-education", "education"]),
    ("en.wikipedia.org", "Glossary of education terms (G–L)", ["field-education", "education"]),
    ("en.wikipedia.org", "Glossary of education terms (M–O)", ["field-education", "education"]),
    ("en.wikipedia.org", "Glossary of education terms (P–R)", ["field-education", "education"]),
    ("en.wikipedia.org", "Glossary of education terms (S–Z)", ["field-education", "education"]),
    ("en.wikipedia.org", "Glossary of aerospace engineering", ["field-aviation", "field-engineering"]),
    ("en.wikipedia.org", "Glossary of psychiatry", ["field-health", "medicine"]),
    ("en.wikipedia.org", "Glossary of agriculture", ["field-agriculture", "plants"]),
    ("en.wikipedia.org", "Glossary of genetics", ["field-biology", "science"]),
    ("en.wikipedia.org", "Glossary of broadcasting", ["field-media", "media"]),
    ("en.wikipedia.org", "Glossary of meteorology", ["field-environment", "weather"]),
    ("en.wikipedia.org", "Glossary of dentistry", ["field-dental", "field-health"]),
    ("en.wikipedia.org", "Glossary of nursing", ["field-nursing", "field-health", "health"]),
    ("en.wikipedia.org", "Glossary of pharmacology", ["field-pharmacy", "medicine"]),
    ("en.wikipedia.org", "Glossary of accounting", ["field-accounting", "money"]),
    ("en.wikipedia.org", "Glossary of finance", ["field-finance", "money"]),
    ("en.wikipedia.org", "Glossary of marketing", ["field-marketing", "business"]),
    ("en.wikipedia.org", "Glossary of architecture", ["field-construction", "field-engineering"]),
    ("en.wikipedia.org", "Glossary of construction", ["field-construction"]),
    ("en.wikipedia.org", "Glossary of aviation", ["field-aviation"]),
    ("en.wikipedia.org", "Glossary of education", ["field-education", "education"]),
    ("en.wikipedia.org", "Glossary of real estate terms", ["field-realestate"]),
    ("en.wiktionary.org", "Appendix:Glossary of dental terms", ["field-dental", "field-health"]),
    ("en.wiktionary.org", "Appendix:Glossary of legal terms", ["field-law", "law"]),
    ("en.wiktionary.org", "Appendix:Glossary of aviation", ["field-aviation"]),
    ("en.wiktionary.org", "Appendix:Glossary of engineering", ["field-engineering"]),
]

# OEWN synset seeds. snippet must appear in the definition; empty matches the first synset.
FIELD_SEEDS = [
    ("economics", "n", "production and distribution", ["field-econ", "money"]),
    ("finance", "n", "", ["field-finance", "money"]),
    ("accounting", "n", "financial", ["field-accounting", "money"]),
    ("marketing", "n", "", ["field-marketing", "business"]),
    ("management", "n", "", ["field-management", "business"]),
    ("employee", "n", "", ["field-hr", "work"]),
    ("jurisprudence", "n", "", ["field-law", "law"]),
    ("medicine", "n", "treat", ["field-health", "medicine"]),
    ("nurse", "n", "caring for", ["field-nursing", "field-health", "health"]),
    ("drug", "n", "medicine", ["field-pharmacy", "medicine"]),
    ("dentistry", "n", "", ["field-dental", "field-health"]),
    ("physics", "n", "", ["field-physics", "science"]),
    ("chemistry", "n", "", ["field-chemistry", "science"]),
    ("biology", "n", "", ["field-biology", "science"]),
    ("engineering", "n", "", ["field-engineering"]),
    ("building", "n", "roof", ["field-construction", "house"]),
    ("machine", "n", "", ["field-mechanical", "field-engineering"]),
    ("electricity", "n", "", ["field-electrical", "energy"]),
    ("software", "n", "", ["field-it", "computers"]),
    ("freight", "n", "", ["field-logistics", "transport"]),
    ("hotel", "n", "", ["field-hospitality", "hotel"]),
    ("tourism", "n", "", ["field-tourism", "travel"]),
    ("education", "n", "", ["field-education", "education"]),
    ("crop", "n", "cultivated", ["field-agriculture", "plants"]),
    ("pollution", "n", "", ["field-environment", "environment"]),
    ("journalism", "n", "", ["field-media", "media"]),
    ("aircraft", "n", "fly", ["field-aviation", "airport", "transport"]),
    ("manufacturing", "n", "", ["field-manufacturing"]),
    ("retailing", "n", "", ["field-retail", "shopping"]),
    ("cosmetic", "n", "", ["field-beauty"]),
    ("cooking", "n", "", ["field-culinary", "cooking", "food"]),
]

# Whole-word classifiers. Not a copied word list: they only decide which
# openly defined term lands in which profession. Multi-word phrases match
# the full term.
KEYWORDS = {
    "field-econ": "economy economic economics inflation recession gdp supply demand tariff subsidy wage labor labour market monopoly oligopoly fiscal monetary trade deficit surplus macroeconomics microeconomics elasticity scarcity commodity export import",
    "field-finance": "bank banking loan mortgage interest credit debit equity asset liability liquidity capital dividend bond stock shares shareholder investor investment portfolio hedge fund treasury forex currency exchange rate collateral default yield annuity underwriting brokerage fintech insurance premium",
    "field-accounting": "accounting accountant ledger journal debit credit balance sheet income statement cash flow accounts payable receivable accrual depreciation amortization audit auditor invoice receipt bookkeeping equity asset liability trial balance goodwill fiscal tax vat",
    "field-marketing": "marketing brand branding advertisement advertising campaign customer segment targeting promotion slogan logo market research publicity sponsorship conversion funnel seo content social media positioning pricing strategy retail mix",
    "field-management": "management manager strategy planning organization organisation leadership decision stakeholder kpi objective mission vision corporate governance merger acquisition startup entrepreneur profit loss operations project management risk management",
    "field-hr": "recruitment hiring interview resume cv payroll salary wage benefit compensation employee employer staff personnel human resources onboarding training appraisal promotion dismissal resignation retirement union workforce diversity inclusion",
    "field-realestate": "real estate property landlord tenant lease rent rental mortgage deed title escrow zoning appraisal realtor broker condominium apartment housing valuation foreclosure lien easement",
    "field-law": "law legal lawyer attorney court judge jury trial verdict plaintiff defendant contract statute regulation compliance litigation arbitration evidence witness crime criminal civil liability tort negligence damages injunction appeal jurisdiction",
    "field-health": "health hospital clinic patient doctor physician diagnosis symptom treatment therapy disease illness surgery infection virus bacteria vaccine immunity blood pressure heart rate fever pain injury emergency anatomy physiology pathology",
    "field-nursing": "nurse nursing ward bedside care plan vital signs injection dressing bandage hygiene patient chart medication round triage stethoscope cannula catheter wound care bedside handover",
    "field-pharmacy": "pharmacy pharmacist drug medicine medication dose dosage tablet capsule ointment prescription antibiotic analgesic vaccine pharmaceutical compound side effect contraindication generic brand drug interaction",
    "field-dental": "dental dentist tooth teeth gum enamel cavity filling crown bridge implant orthodontic braces plaque tartar root canal extraction wisdom tooth denture oral hygiene",
    "field-physics": "physics force energy mass velocity acceleration gravity momentum inertia friction torque pressure temperature heat wave frequency wavelength optics quantum electron proton neutron atom nuclear relativity",
    "field-chemistry": "chemistry chemical element compound molecule atom reaction acid base solvent solute catalyst oxidation reduction polymer bond ion concentration molar solution periodic",
    "field-biology": "biology cell organism gene genetics dna rna protein enzyme evolution species ecology habitat metabolism photosynthesis respiration chromosome tissue organ bacteria virus",
    "field-engineering": "engineering engineer design specification tolerance prototype stress strain load safety factor material failure analysis technical drawing schematic system component",
    "field-construction": "construction building foundation beam column slab wall roof concrete cement brick mortar rebar reinforcement load-bearing scaffold formwork excavation plumbing hvac masonry carpenter joist truss insulation drywall",
    "field-mechanical": "mechanical mechanics gear shaft bearing engine piston turbine pump compressor hydraulics pneumatics torque welding lathe milling machining lubricant coolant valve",
    "field-electrical": "electrical electricity electronic circuit voltage current resistance capacitor inductor transformer diode transistor motor generator wiring socket fuse breaker semiconductor pcb sensor relay",
    "field-it": "software hardware computer programming code algorithm database server network internet protocol cybersecurity encryption cloud api compiler debugging interface operating system laptop keyboard mouse chip processor memory bandwidth",
    "field-logistics": "logistics freight cargo warehouse shipping shipment supply chain inventory distribution pallet container truck delivery customs import export route tracking consignment forklift dispatch",
    "field-hospitality": "hotel motel hostel restaurant cafe reservation guest receptionist housekeeping lobby check-in checkout room service concierge banquet menu waiter waitress tip hospitality",
    "field-tourism": "tourism tourist travel trip tour guide itinerary destination sightseeing visa passport luggage souvenir attraction booking holiday vacation cruise excursion",
    "field-education": "education school teacher student classroom lesson curriculum syllabus exam homework lecture seminar campus university college scholarship diploma degree pedagogy literacy",
    "field-agriculture": "agriculture farm farmer crop harvest irrigation fertilizer pesticide soil livestock cattle poultry wheat rice corn maize orchard greenhouse tractor cultivation agronomy",
    "field-environment": "environment pollution recycle recycling climate carbon emission ecosystem biodiversity conservation sustainability waste landfill ozone renewable habitat deforestation erosion",
    "field-media": "journalism journalist newspaper magazine broadcast television radio headline editor reporter interview press media podcast newsroom editorial column advertising copy",
    "field-aviation": "aviation aircraft airplane aeroplane airport runway pilot cockpit cabin crew flight takeoff landing altitude airspace navigation radar fuselage wing turbine jet airline boarding gate",
    "field-manufacturing": "manufacturing factory production assembly line quality control raw material inventory machine operator shift lean six sigma prototype batch welding packaging output",
    "field-retail": "retail shop store cashier checkout barcode inventory merchandising customer discount receipt supermarket shelf display point of sale wholesale sku pricing",
    "field-beauty": "nail manicure pedicure polish cuticle acrylic gel salon beauty cosmetic makeup skincare facial spa haircut hairstyle eyebrow lash waxing",
    "field-culinary": "chef cook cooking kitchen recipe ingredient sauce garnish bake fry boil grill roast simmer knife cuisine menu pastry butcher seasoning marinade broth stock",
}

FIELD_HEX = {
    "field-econ": "1f4c8",
    "field-finance": "1f3e6",
    "field-accounting": "1f4ca",
    "field-marketing": "1f4e3",
    "field-management": "1f4bc",
    "field-hr": "1f465",
    "field-realestate": "1f3e0",
    "field-law": "2696",
    "field-health": "1fa7a",
    "field-nursing": "1f9d1",
    "field-pharmacy": "1f48a",
    "field-dental": "1f9b7",
    "field-physics": "269b",
    "field-chemistry": "1f9ea",
    "field-biology": "1f9ec",
    "field-engineering": "1f527",
    "field-construction": "1f3d7",
    "field-mechanical": "2699",
    "field-electrical": "1f50c",
    "field-it": "1f4bb",
    "field-logistics": "1f69a",
    "field-hospitality": "1f3e8",
    "field-tourism": "1f9f3",
    "field-education": "1f4da",
    "field-agriculture": "1f33e",
    "field-environment": "267b",
    "field-media": "1f4f0",
    "field-aviation": "2708",
    "field-manufacturing": "1f3ed",
    "field-retail": "1f6d2",
    "field-beauty": "1f485",
    "field-culinary": "1f373",
}

# Tokens that only belong inside a longer term. "sheet" must not pull the
# verb "to sheet" into accounting; "balance sheet" still matches as a phrase.
SOLO_SKIP = {
    "sheet", "flow", "statement", "income", "line", "rate", "bearing",
    "pressure", "signs", "effect", "interaction", "canal", "hygiene",
}

STOP = {
    "a", "an", "the", "of", "and", "or", "to", "in", "on", "for", "with", "by",
    "from", "at", "as", "is", "be", "it", "its", "this", "that",
}

SKIP_TERM = re.compile(
    r"\b(theorem|paradox|conjecture|hypothesis|equation|lemma|corollary)\b|'s law\b|\bmodel\b",
    re.I,
)


def download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            dest.write_bytes(response.read())
    except Exception as error:
        print(f"skip download {url}: {error}")
        if dest.exists():
            dest.unlink()
        return False
    return dest.exists() and dest.stat().st_size > 0


def fetch_wikitext(host: str, title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    dest = GLOSS_DIR / f"{host.split('.')[0]}-{slug}.txt"
    if dest.exists() and dest.stat().st_size > 40:
        return dest.read_text(encoding="utf-8")
    query = urllib.parse.urlencode({
        "action": "parse",
        "page": title,
        "prop": "wikitext",
        "format": "json",
        "redirects": "1",
    })
    url = f"https://{host}/w/api.php?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        print(f"glossary miss {title}: {error}")
        return ""
    if payload.get("error"):
        print(f"glossary miss {title}: {payload['error'].get('code')}")
        return ""
    text = ((payload.get("parse") or {}).get("wikitext") or {}).get("*") or ""
    if len(text) < 80:
        print(f"glossary short {title}")
        return ""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return text


def strip_wiki(text: str) -> str:
    text = re.sub(r"<ref[^>]*>.*?</ref>", " ", text or "", flags=re.S | re.I)
    text = re.sub(r"<ref[^/]*/>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)

    def link(match: re.Match) -> str:
        inner = match.group(1)
        shown = inner.split("|")[-1]
        return shown.split("#")[-1]

    text = re.sub(r"\[\[([^]]+)\]\]", link, text)
    text = re.sub(r"\{\{[^{}]*\}\}", " ", text)
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"\[https?://[^\]\s]+ ([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[https?://[^\]\s]+\]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \t.;,:—–-|")


def clean_term(raw: str) -> str:
    text = strip_wiki(raw)
    text = re.sub(r"\([^)]*\)", " ", text)
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip(" .;,:—–-/'\"")
    return text


def ok_term(term: str) -> bool:
    # Glossary and MeSH headings are Title Case. Store and test the lowercase form.
    term = (term or "").strip().lower().replace("’", "'")
    if not term or len(term) > 48 or len(term) < 3:
        return False
    words = term.split()
    if not 1 <= len(words) <= 5:
        return False
    if not re.fullmatch(r"[a-z][a-z'./ -]*", term):
        return False
    if any(ch.isdigit() for ch in term):
        return False
    if SKIP_TERM.search(term):
        return False
    if term in build_vocab.BAD_WORD or any(part in build_vocab.BAD_WORD for part in words):
        return False
    return True


def soften(text: str) -> str:
    letters = [ch for ch in text if ch.isalpha()]
    if letters and sum(ch.isupper() for ch in letters) / len(letters) > 0.55:
        return text.lower()
    return text


def definition_ok(text: str) -> str:
    cleaned = build_vocab.tidy_english(soften(text))
    if len(cleaned) < 12:
        return ""
    if cleaned.lower().startswith("see "):
        return ""
    return cleaned


def parse_glossary(wikitext: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    seen = set()

    def add(term_raw: str, def_raw: str) -> None:
        term = clean_term(term_raw)
        if not ok_term(term):
            return
        key = term.lower()
        if key in seen:
            return
        meaning = definition_ok(def_raw)
        if not meaning:
            return
        seen.add(key)
        found.append((key, meaning))

    for part in re.split(r"\{\{\s*term\s*\|", wikitext)[1:]:
        body, _, rest = part.partition("}}")
        content = re.search(r"content\s*=\s*(.+)", body)
        label = content.group(1) if content else re.sub(r"^\s*1\s*=\s*", "", body)
        defn = re.search(r"\{\{\s*defn\s*\|(?:1=|defn=)?(.*?)\}\}", rest, flags=re.S)
        if not defn:
            continue
        add(label, defn.group(1))
    for match in re.finditer(r"^[\*\#]\s*'''(.+?)'''\s*[–—:.\-]+\s*(.+)$", wikitext, re.M):
        add(match.group(1), match.group(2))
    for match in re.finditer(r"^===\s*([^=\n]+?)\s*===\s*\n+(.+)", wikitext, re.M):
        paragraph = match.group(2).split("\n\n", 1)[0]
        add(match.group(1), paragraph)
    for match in re.finditer(r"^;\s*(.+?)\s*:\s*(.+)$", wikitext, re.M):
        add(match.group(1), match.group(2))
    for match in re.finditer(r"^;\s*(.+)\n:\s*(.+)$", wikitext, re.M):
        add(match.group(1), match.group(2))
    return found


def spread(rows: list[dict], cap: int) -> list[dict]:
    if len(rows) <= cap:
        return rows
    ordered = sorted(rows, key=lambda row: (-row["zipf"], row["term"]))
    head_n = cap // 2
    head = ordered[:head_n]
    tail = ordered[head_n:]
    need = cap - head_n
    step = max(1, len(tail) // need)
    rest = tail[::step][:need]
    if len(head) + len(rest) < cap:
        used = {row["term"] for row in head + rest}
        for row in tail:
            if row["term"] in used:
                continue
            rest.append(row)
            if len(head) + len(rest) >= cap:
                break
    return head + rest


class Bag:
    """term -> merged topics, English definition, and a pos hint."""

    def __init__(self) -> None:
        self.topics: dict[str, list[str]] = defaultdict(list)
        self.definition: dict[str, str] = {}
        self.pos: dict[str, str] = {}

    def add(self, term: str, topics: list[str], definition: str = "", pos: str = "") -> None:
        term = term.strip().lower().replace("_", " ")
        term = re.sub(r"\s+", " ", term)
        if not ok_term(term):
            return
        row = self.topics[term]
        for topic in topics:
            if topic and topic not in row and len(row) < MAX_TOPICS:
                row.append(topic)
        if definition and len(definition) > len(self.definition.get(term, "")):
            self.definition[term] = definition
        if pos and term not in self.pos:
            self.pos[term] = pos


def keyword_index() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    words: dict[str, set[str]] = defaultdict(set)
    phrases: dict[str, set[str]] = defaultdict(set)
    for field, text in KEYWORDS.items():
        for part in text.split():
            if " " in part:
                phrases[part.lower()].add(field)
            else:
                words[part.lower()].add(field)
    # Multi-word pieces were split above. Rebuild phrases from the raw text
    # by scanning known two- and three-word sequences that contain a hyphen
    # or were written as separate tokens we care about.
    for field, text in KEYWORDS.items():
        tokens = text.split()
        for size in (2, 3):
            for index in range(len(tokens) - size + 1):
                phrase = " ".join(tokens[index:index + size])
                if phrase in {
                    "balance sheet", "income statement", "cash flow", "accounts payable",
                    "trial balance", "real estate", "blood pressure", "heart rate",
                    "vital signs", "side effect", "drug interaction", "root canal",
                    "wisdom tooth", "oral hygiene", "load-bearing", "supply chain",
                    "check-in", "point of sale", "human resources", "quality control",
                    "raw material", "assembly line", "social media", "market research",
                    "exchange rate", "hedge fund",
                }:
                    phrases[phrase].add(field)
        for token in tokens:
            if "-" in token:
                phrases[token.lower()].add(field)
    return words, phrases


def fields_for(term: str, words: dict[str, set[str]], phrases: dict[str, set[str]]) -> list[str]:
    lowered = term.lower()
    found: list[str] = []
    for phrase, fields in phrases.items():
        if phrase == lowered or f" {phrase} " in f" {lowered} ":
            for field in fields:
                if field not in found:
                    found.append(field)
    exact = []
    for phrase, fields in phrases.items():
        if phrase == lowered:
            for field in fields:
                if field not in exact:
                    exact.append(field)
    if exact:
        return exact
    tokens = set(re.findall(r"[a-z0-9]+", lowered))
    for token in tokens:
        if token in SOLO_SKIP:
            continue
        for field in words.get(token, ()):
            if field not in found:
                found.append(field)
    return found


def read_csv_rows(path: Path):
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    return csv.DictReader(io.StringIO(text))


def read_service_lists(bag: Bag, words, phrases) -> None:
    """Tag NGSL-family lemmas when a profession keyword matches.

    The lists themselves are CC BY-SA 4.0. General words with no field stay
    out, so the profession decks are not a dump of the whole NGSL.
    """
    sources = [
        NGSL_DIR / "NGSL_12_stats.csv",
        NGSL_DIR / "BSL_120_stats.csv",
        NGSL_DIR / "TSL_12_stats.csv",
    ]
    lemmas = []
    for path in sources:
        if not path.exists():
            print("missing", path.name)
            continue
        for row in read_csv_rows(path):
                word = (row.get("Lemma") or row.get("Word") or "").strip().lower()
                if ok_term(word):
                    lemmas.append(word)
    nawl = NGSL_DIR / "NAWL_12_with_en_definitions.csv"
    if nawl.exists():
        for row in read_csv_rows(nawl):
                word = (row.get("Meanings") or "").strip().lower()
                if not ok_term(word):
                    continue
                pos = {
                    "n": "noun", "noun": "noun", "v": "verb", "verb": "verb",
                    "adj": "adj", "adjective": "adj", "adv": "adv", "adverb": "adv",
                }.get((row.get("POS") or "").strip().lower(), "")
                definition = definition_ok(row.get("English Definition") or "")
                fields = fields_for(word, words, phrases)
                if not fields:
                    continue
                bag.add(word, fields + ["education"], definition, pos or "noun")
                lemmas.append(word)
    tagged = 0
    for word in lemmas:
        fields = fields_for(word, words, phrases)
        if not fields:
            continue
        bag.add(word, fields)
        tagged += 1
    print(f"service-list field tags: {tagged}")


def load_glossaries(bag: Bag) -> None:
    for host, title, topics in GLOSSARIES:
        text = fetch_wikitext(host, title)
        if not text:
            continue
        rows = []
        for term, meaning in parse_glossary(text):
            rows.append({"term": term, "meaning": meaning, "zipf": zipf_of(term)})
        chosen = spread(rows, GLOSSARY_CAP)
        for row in chosen:
            bag.add(row["term"], topics, row["meaning"], "noun")
        print(f"glossary {title}: parsed {len(rows)} kept {len(chosen)}")


def load_mesh(bag: Bag) -> None:
    url = "https://nlmpubs.nlm.nih.gov/projects/mesh/2025/asciimesh/d2025.bin"
    if not download(url, MESH_PATH):
        print("MeSH unavailable")
        return
    buckets: dict[str, list[dict]] = defaultdict(list)
    record: dict[str, list[str]] = {}

    def flush() -> None:
        if not record:
            return
        name = " ".join(record.get("MH", [])).strip()
        term = clean_term(name)
        if not ok_term(term) or "," in name:
            record.clear()
            return
        scope = " ".join(record.get("MS", []))
        meaning = definition_ok(scope)
        if not meaning:
            record.clear()
            return
        numbers = record.get("MN", [])
        kinds = set()
        if any(number.startswith("E06") for number in numbers):
            kinds.add("dental")
        if any(number.startswith("D26") for number in numbers):
            kinds.add("pharmacy")
        if any(number.startswith("N02.421.533") or number.startswith("G02.478") for number in numbers):
            kinds.add("nursing")
        if "nursing" in term or term.startswith("nurse"):
            kinds.add("nursing")
        if any(number.startswith("A") for number in numbers):
            kinds.add("anatomy")
        if any(number.startswith("C") for number in numbers):
            kinds.add("disease")
        row = {"term": term.lower(), "meaning": meaning, "zipf": zipf_of(term)}
        for kind in kinds:
            buckets[kind].append(row)
        record.clear()

    with MESH_PATH.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line.startswith("*NEWRECORD"):
                flush()
                record = {}
                continue
            if " = " not in line:
                continue
            key, value = line.split(" = ", 1)
            record.setdefault(key, []).append(value)
        flush()
    topic_for = {
        "anatomy": ["field-health", "body", "medicine"],
        "disease": ["field-health", "medicine"],
        "pharmacy": ["field-pharmacy", "medicine"],
        "dental": ["field-dental", "field-health"],
        "nursing": ["field-nursing", "field-health", "health"],
    }
    for kind, rows in buckets.items():
        # Unique by term inside the bucket.
        unique = {}
        for row in rows:
            unique.setdefault(row["term"], row)
        chosen = spread(list(unique.values()), MESH_CAP[kind])
        for row in chosen:
            bag.add(row["term"], topic_for[kind], row["meaning"], "noun")
        print(f"mesh {kind}: {len(unique)} kept {len(chosen)}")


def zipf_of(term: str) -> float:
    phrase = zipf_frequency(term.lower(), "en")
    if phrase > 0:
        return phrase
    scores = []
    for part in re.findall(r"[a-z]+", term.lower()):
        if part in STOP or len(part) < 3:
            continue
        score = zipf_frequency(part, "en")
        if score > 0:
            scores.append(score)
    if not scores:
        return 0.0
    return min(scores)


def hyponym_lemmas(en, lemma: str, pos: str, snippet: str, limit_synsets: int = 900) -> list[str]:
    queue = []
    for syn in en.synsets(lemma, pos=pos):
        if snippet and snippet.lower() not in (syn.definition() or "").lower():
            continue
        queue.append(syn)
    if not queue:
        queue = list(en.synsets(lemma, pos=pos)[:1])
    visited = set()
    found = []
    seen = set()
    while queue and len(visited) < limit_synsets and len(found) < 700:
        syn = queue.pop(0)
        if syn.id in visited:
            continue
        visited.add(syn.id)
        for name in syn.lemmas():
            if name[:1].isupper():
                continue
            key = name.lower().replace("_", " ")
            if key in seen or not ok_term(key):
                continue
            seen.add(key)
            found.append(key)
        for hypo in syn.hyponyms():
            if hypo.id not in visited:
                queue.append(hypo)
    return found


def add_wordnet(bag: Bag, en) -> None:
    for lemma, pos, snippet, topics in FIELD_SEEDS:
        names = hyponym_lemmas(en, lemma, pos, snippet)
        rows = [{"term": name, "zipf": zipf_of(name)} for name in names]
        chosen = spread(rows, NEW_PER_FIELD_SEED + 220)
        for row in chosen:
            bag.add(row["term"], topics)
        print(f"field seed {lemma}: {len(names)} walk, kept {len(chosen)}")
    for topic, seeds in SEEDS.items():
        if not seeds:
            continue
        names = []
        for lemma, pos, snippet in seeds:
            names.extend(hyponym_lemmas(en, lemma, pos, snippet, limit_synsets=700))
        # de-dupe, keep order
        seen = set()
        unique = []
        for name in names:
            if name in seen:
                continue
            seen.add(name)
            unique.append(name)
        rows = [{"term": name, "zipf": zipf_of(name)} for name in unique]
        chosen = spread(rows, TAG_CAP)
        for row in chosen:
            bag.add(row["term"], [topic])
        print(f"topic seed {topic}: {len(unique)} walk, kept {len(chosen)}")


def guess_pos(term: str, definition: str, hinted: str) -> str:
    if hinted in {"noun", "verb", "adj", "adv"}:
        return hinted
    if " " in term or "-" in term:
        return "noun"
    if definition.lower().startswith("to "):
        return "verb"
    return "noun"


def level_for(term: str, pos: str, official: dict[tuple[str, str], str]) -> str:
    marked = official.get((term.lower(), pos))
    if marked:
        return marked
    return build_vocab.level_from_zipf(zipf_of(term))


def merge_topics(card: dict, extra: list[str]) -> bool:
    topics = list(card.get("topics") or [])
    changed = False
    for topic in extra:
        if not topic or topic in topics:
            continue
        if len(topics) < MAX_TOPICS:
            topics.append(topic)
            changed = True
            continue
        if topic.startswith("field-"):
            for index in range(len(topics) - 1, -1, -1):
                if not str(topics[index]).startswith("field-"):
                    topics[index] = topic
                    changed = True
                    break
    if changed:
        card["topics"] = topics
    return changed


def load_cards() -> tuple[list[dict], dict[str, list[dict]], list[dict]]:
    level_cards = []
    for level in build_vocab.LEVEL_RANK:
        path = DATA / f"level-{level.lower()}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        for card in payload.get("cards") or []:
            card["_origin"] = "level"
            level_cards.append(card)
    field_cards = []
    if FIELDS_DIR.exists():
        for path in sorted(FIELDS_DIR.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for card in payload.get("cards") or []:
                card["_origin"] = "field"
                field_cards.append(card)
    by_word: dict[str, list[dict]] = defaultdict(list)
    for card in level_cards + field_cards:
        by_word[card["word"].lower()].append(card)
    return level_cards, by_word, field_cards


def meaning_for(term: str, pos: str, bank, en, fallback: str) -> tuple[str, str, str | None]:
    entries = build_vocab.lookup(bank, term, pos) if bank else []
    if entries:
        meaning, ipas = build_vocab.pick_meaning(entries, term, pos)
        if meaning:
            return meaning, "vi", build_vocab.pick_ipa(ipas)
    if " " not in term:
        english = build_vocab.english_meaning(en, term, pos)
        if english:
            return english, "en", None
    if fallback:
        return fallback, "en", None
    return "", "", None


def stamp_emoji(cards: list[dict], index: dict[str, str]) -> None:
    for card in cards:
        if card.get("emo") or card.get("img"):
            continue
        tokens = [part for part in re.findall(r"[a-z0-9]+", card["word"].lower()) if part not in STOP]
        hexes = []
        for token in [card["word"].lower(), *tokens]:
            found = index.get(token)
            if found and found not in hexes:
                hexes.append(found)
            if len(hexes) >= 2:
                break
        if not hexes:
            for topic in card.get("topics") or []:
                fallback = FIELD_HEX.get(topic) or build_pictures.TOPIC_HEX.get(topic)
                if fallback:
                    hexes.append(fallback)
                    break
        if hexes:
            card["emo"] = hexes[:2]


def primary_file(card: dict) -> str:
    for topic in card.get("topics") or []:
        if str(topic).startswith("field-"):
            return topic
    for topic in card.get("topics") or []:
        return f"topic-{topic}"
    return "topic-extra"


def write_level_files(level_cards: list[dict]) -> None:
    by_level = {level: [] for level in build_vocab.LEVEL_RANK}
    for card in level_cards:
        card.pop("_origin", None)
        by_level[card["level"]].append(card)
    for level, group in by_level.items():
        path = DATA / f"level-{level.lower()}.json"
        path.write_text(
            json.dumps({"cards": group}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(f"wrote {path.name} {len(group)} {path.stat().st_size}")


def write_field_files(field_cards: list[dict]) -> dict[str, list[str]]:
    if FIELDS_DIR.exists():
        for path in FIELDS_DIR.glob("*.json"):
            path.unlink()
    FIELDS_DIR.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for card in field_cards:
        card.pop("_origin", None)
        grouped[primary_file(card)].append(card)
    sources: dict[str, list[str]] = defaultdict(list)
    for file_id, group in sorted(grouped.items()):
        group.sort(key=lambda card: (build_vocab.LEVEL_RANK[card["level"]], card["word"].lower(), card["pos"]))
        path = FIELDS_DIR / f"{file_id}.json"
        path.write_text(
            json.dumps({"cards": group}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(f"wrote fields/{path.name} {len(group)} {path.stat().st_size}")
        seen = set()
        for card in group:
            for topic in card.get("topics") or []:
                if topic in seen:
                    continue
                seen.add(topic)
        for topic in seen:
            sources[topic].append(file_id)
    return sources


def update_meta(cards: list[dict], sources: dict[str, list[str]]) -> None:
    meta_path = DATA / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    counts = {level: 0 for level in build_vocab.LEVEL_RANK}
    image_counts = {level: 0 for level in build_vocab.LEVEL_RANK}
    ipa_n = example_n = image_n = vi_n = en_n = 0
    topic_counts: dict[str, int] = defaultdict(int)
    for card in cards:
        counts[card["level"]] += 1
        ipa_n += "ipa" in card
        example_n += "example" in card
        if card.get("meaningLang") == "en":
            en_n += 1
        else:
            vi_n += 1
        if card.get("img") or card.get("emo"):
            image_n += 1
            image_counts[card["level"]] += 1
        for topic in card.get("topics") or []:
            topic_counts[topic] += 1
    previous = {item["id"]: item for item in meta.get("topics") or []}
    general = []
    for topic_id, item in previous.items():
        if item.get("group") == "field" or topic_id.startswith("field-"):
            continue
        if topic_counts.get(topic_id, 0) <= 0:
            continue
        general.append({
            "id": topic_id,
            "name": item.get("name") or topic_id,
            "count": topic_counts[topic_id],
        })
    fields = []
    for order, (topic_id, name) in enumerate(FIELDS):
        count = topic_counts.get(topic_id, 0)
        if count <= 0:
            continue
        fields.append({
            "id": topic_id,
            "name": name,
            "count": count,
            "group": "field",
            "order": order,
        })
    meta.update({
        "generated": build_vocab.SOURCE_DATE,
        "counts": counts,
        "total": len(cards),
        "withVi": vi_n,
        "withEn": en_n,
        "withIpa": ipa_n,
        "withExample": example_n,
        "withImage": image_n,
        "imageCounts": image_counts,
        "levels": list(build_vocab.LEVEL_RANK),
        "topics": general + fields,
        "topicLevels": topic_levels(cards),
        "topicFiles": sorted({file_id for ids in sources.values() for file_id in ids}),
        "topicSources": {topic: ids for topic, ids in sorted(sources.items())},
    })
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("total", len(cards), "counts", counts)
    print("fields", [(item["id"], item["count"]) for item in fields])
    print("topics", len(general), "field topics", len(fields), "files", len(meta["topicFiles"]))


def main() -> None:
    level_cards, by_word, old_field = load_cards()
    old_ids = {card["id"] for card in level_cards}
    old_ids.update(card["id"] for card in old_field)
    print(f"loaded level {len(level_cards)} field {len(old_field)}")
    words, phrases = keyword_index()
    bag = Bag()
    read_service_lists(bag, words, phrases)
    load_glossaries(bag)
    load_mesh(bag)
    en = build_vocab.english_wordnet()
    if os.environ.get("FF_SKIP_WORDNET") == "1":
        print("skipping wordnet walk")
    else:
        add_wordnet(bag, en)
    # Keyword pass over words already in the deck, so basic field words
    # that the glossaries never mention still show up.
    tagged_existing = 0
    for word, cards in by_word.items():
        fields = fields_for(word, words, phrases)
        if not fields:
            continue
        for card in cards:
            if merge_topics(card, fields):
                tagged_existing += 1
    print(f"existing cards newly tagged by keyword: {tagged_existing}")

    official = build_vocab.official_levels()
    used_ids = set(old_ids)
    new_cards: list[dict] = []
    reused = 0
    pending = []
    for term, topics in bag.topics.items():
        pos = guess_pos(term, bag.definition.get(term, ""), bag.pos.get(term, ""))
        existing = [card for card in by_word.get(term, []) if card["pos"] == pos]
        if not existing and by_word.get(term) and " " not in term and len(by_word[term]) == 1:
            existing = by_word[term]
        if existing:
            for card in existing:
                merge_topics(card, topics)
            reused += 1
            continue
        pending.append((term, pos, topics))
    print(f"terms reused on existing cards: {reused}; new candidates: {len(pending)}")
    wanted = {term for term, _, _ in pending}
    bank = build_vocab.load_wiktionary(wanted) if wanted else {}
    created_keys = set()
    for term, pos, topics in pending:
        key = (term, pos)
        if key in created_keys:
            continue
        meaning, lang, ipa = meaning_for(term, pos, bank, en, bag.definition.get(term, ""))
        if not meaning:
            continue
        if any(part in build_vocab.BAD_WORD for part in term.split()):
            continue
        card_id = build_vocab.slug(term, pos)
        if card_id in used_ids:
            suffix = 2
            while f"{card_id}-{suffix}" in used_ids:
                suffix += 1
            card_id = f"{card_id}-{suffix}"
        used_ids.add(card_id)
        created_keys.add(key)
        card = {
            "id": card_id,
            "word": build_vocab.display_word(term),
            "pos": pos,
            "level": level_for(term, pos, official),
            "meaning": meaning,
            "topics": topics[:MAX_TOPICS],
            "_origin": "field",
        }
        if lang == "en":
            card["meaningLang"] = "en"
        if ipa:
            card["ipa"] = ipa
        new_cards.append(card)
    print(f"new cards: {len(new_cards)}")
    if new_cards and build_vocab.FILES["eng"].exists():
        examples = build_vocab.load_examples(new_cards)
        attached = 0
        for card in new_cards:
            example = examples.get(card["id"])
            if not example:
                continue
            card["example"] = example["en"]
            card["exampleVi"] = example["vi"]
            ref = {"id": example["id"]}
            if example.get("author"):
                ref["author"] = example["author"]
            card["tatoeba"] = ref
            attached += 1
        print(f"new cards with an example: {attached}")
    try:
        paths = build_pictures.fluent_paths()
        _by_hex, meta_by_folder = build_pictures.load_fluent_meta(paths)
        emoji_words = build_pictures.keyword_index(meta_by_folder)
    except Exception as error:
        print("emoji index skipped", error)
        emoji_words = {}
    stamp_emoji(new_cards, emoji_words)
    # Keep previously shipped field cards even if this run's cap missed them.
    new_keys = {(card["word"].lower(), card["pos"]) for card in new_cards}
    kept_old = []
    for card in old_field:
        if (card["word"].lower(), card["pos"]) in new_keys:
            continue
        kept_old.append(card)
    field_cards = new_cards + kept_old
    all_cards = level_cards + field_cards
    missing = old_ids - {card["id"] for card in all_cards}
    if missing:
        raise SystemExit(f"refusing to drop {len(missing)} ids, e.g. {list(missing)[:5]}")
    write_level_files(level_cards)
    sources = write_field_files(field_cards)
    update_meta(all_cards, sources)
    by_level = defaultdict(int)
    for card in field_cards:
        by_level[card["level"]] += 1
    print("field cards by level", dict(by_level))
    sizes = sorted((path.stat().st_size, path.name) for path in FIELDS_DIR.glob("*.json"))
    print("largest field files", sizes[-8:])
    print("field bytes", sum(size for size, _ in sizes))


if __name__ == "__main__":
    main()
