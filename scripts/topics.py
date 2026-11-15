"""Assign learner topics with Open English WordNet and hand-checked word lists.

Open English WordNet (oewn:2024) is CC BY 4.0. Closures walk hyponyms of a
specific synset so "dog" lands in animals and "oven" can still be listed
under kitchen when WordNet files it as an appliance.
"""

from __future__ import annotations

TOPIC_NAMES = {
    "food": "Đồ ăn",
    "drinks": "Đồ uống",
    "kitchen": "Nhà bếp",
    "cooking": "Động từ nấu nướng",
    "restaurant": "Nhà hàng",
    "family": "Gia đình",
    "body": "Cơ thể",
    "health": "Sức khỏe",
    "medicine": "Y học",
    "emotions": "Cảm xúc",
    "personality": "Tính cách",
    "appearance": "Ngoại hình",
    "clothes": "Quần áo",
    "house": "Nhà cửa",
    "rooms": "Các phòng",
    "furniture": "Nội thất",
    "city": "Thành phố",
    "places": "Địa điểm và địa lý",
    "travel": "Du lịch",
    "transport": "Phương tiện",
    "airport": "Sân bay",
    "hotel": "Khách sạn",
    "work": "Công việc",
    "office": "Văn phòng",
    "business": "Kinh doanh",
    "money": "Tiền bạc",
    "shopping": "Mua sắm",
    "education": "Trường học",
    "science": "Khoa học",
    "technology": "Công nghệ",
    "computers": "Máy tính",
    "math": "Toán",
    "nature": "Thiên nhiên",
    "animals": "Động vật",
    "plants": "Thực vật",
    "weather": "Thời tiết",
    "environment": "Môi trường",
    "space": "Vũ trụ",
    "sports": "Thể thao",
    "music": "Âm nhạc",
    "art": "Nghệ thuật",
    "movies": "Phim ảnh",
    "books": "Sách",
    "media": "Truyền thông",
    "language": "Ngôn ngữ",
    "communication": "Giao tiếp",
    "law": "Luật pháp",
    "politics": "Chính trị",
    "military": "Quân sự",
    "religion": "Tôn giáo",
    "tools": "Dụng cụ",
    "materials": "Chất liệu",
    "energy": "Năng lượng",
    "shapes": "Hình dạng",
    "colors": "Màu sắc",
    "time": "Thời gian",
    "numbers": "Số đếm",
    "people": "Nghề nghiệp",
    "social": "Quan hệ",
    "daily": "Đời sống hằng ngày",
    "holidays": "Ngày lễ",
    "phrasal": "Cụm động từ & thành ngữ",
    "collocation": "Cụm từ hay đi chung",
    "adjectives": "Tính từ thường gặp",
}

TOPIC_ORDER = list(TOPIC_NAMES)

# If a more specific topic matched, drop the broader one.
PARENT = {
    "drinks": "food",
    "cooking": "food",
    "restaurant": "food",
    "kitchen": "house",
    "furniture": "house",
    "rooms": "house",
    "animals": "nature",
    "plants": "nature",
    "weather": "nature",
    "environment": "nature",
    "computers": "technology",
    "technology": "science",
    "medicine": "health",
    "airport": "travel",
    "hotel": "travel",
    "transport": "travel",
    "office": "work",
    "business": "work",
    "money": "business",
    "movies": "media",
    "music": "art",
    "books": "art",
    "emotions": "personality",
    "space": "science",
}

# (lemma, pos, snippet that must appear in the synset definition)
SEEDS = {
    "animals": [("animal", "n", "living organism")],
    "plants": [("plant", "n", "locomotion")],
    "food": [("food", "n", "solid substance"), ("food", "n", "metabolized")],
    "drinks": [("beverage", "n", "liquid suitable")],
    "furniture": [("furniture", "n", "furnishings")],
    "clothes": [("clothing", "n", "worn on a person")],
    "transport": [("vehicle", "n", "conveyance"), ("aircraft", "n", "can fly")],
    "emotions": [("emotion", "n", "strong feeling")],
    "sports": [("sport", "n", "physical exertion")],
    "music": [("musical instrument", "n", "musical tones"), ("music", "n", "auditory")],
    "weather": [("weather", "n", "atmospheric")],
    "tools": [("tool", "n", "implement used"), ("kitchen utensil", "n", "")],
    "rooms": [("room", "n", "enclosed by walls")],
    "people": [("occupation", "n", "earn money")],
    "colors": [("color", "n", "visual attribute")],
    "body": [("body part", "n", "part of an organism")],
    "medicine": [("illness", "n", "physiological"), ("medicine", "n", "treat")],
    "science": [("science", "n", "scientific knowledge")],
    "computers": [("computer", "n", "calculations")],
    "language": [("language", "n", "communicating")],
    "art": [("art", "n", "human creativity")],
    "movies": [("movie", "n", "sequence of")],
    "education": [("school", "n", "educational institution")],
    "family": [("relative", "n", "blood or marriage")],
    "places": [("city", "n", "densely populated"), ("country", "n", "political state")],
    "cooking": [("cook", "v", "applying heat")],
    "house": [("house", "n", "dwelling"), ("housing", "n", "residing")],
    "money": [("currency", "n", "system of money"), ("money", "n", "medium of exchange")],
    "law": [("law", "n", "collection of rules"), ("jurisprudence", "n", "")],
    "sports_game": [],
}

CEFR_MAP = {
    "work": ["work"],
    "education": ["education"],
    "home": ["house"],
    "news": ["media"],
    "town": ["city", "shopping"],
    "food": ["food"],
    "travel": ["travel"],
    "hobbies": ["sports"],
    "places": ["places"],
    "family": ["family"],
    "clothes": ["clothes"],
    "books": ["books"],
    "media": ["media"],
    "arts": ["art"],
    "colours": ["colors"],
    "technical": ["science", "technology"],
    "holidays": ["holidays"],
    "personal": ["daily"],
    "health": ["health"],
    "people": ["social"],
    "services": ["shopping"],
    "language": ["language"],
    "daily": ["daily"],
    "weather": ["weather"],
}

SPELLING = {
    "colour": "color",
    "grey": "gray",
    "theatre": "theater",
    "favourite": "favorite",
    "honour": "honor",
    "metre": "meter",
    "litre": "liter",
    "practise": "practice",
    "defence": "defense",
    "offence": "offense",
}

PARTICLES = {
    "up", "down", "out", "off", "on", "in", "over", "away", "back", "through",
    "around", "about", "along", "apart", "by", "for", "into", "onto", "after",
    "across", "ahead", "forward", "together", "aside", "round", "upon", "without",
}

NUMBERS = {
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million",
    "billion", "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
    "eighth", "ninth", "tenth", "once", "twice", "double", "triple", "half",
    "quarter", "pair", "dozen", "number", "digit", "percent", "percentage",
}

TIME_WORDS = {
    "time", "second", "minute", "hour", "day", "week", "month", "year", "today",
    "tomorrow", "yesterday", "morning", "afternoon", "evening", "night", "noon",
    "midnight", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday", "january", "february", "march", "april", "june", "july",
    "august", "september", "october", "november", "december", "spring", "summer",
    "autumn", "winter", "season", "weekend", "calendar", "clock", "century",
    "decade", "o'clock", "oclock", "tonight", "dawn", "dusk", "fortnight",
    "weekday", "moment", "daily", "weekly", "monthly", "annual",
}

COLOR_WORDS = {
    "color", "colour", "red", "blue", "green", "yellow", "orange", "purple",
    "pink", "black", "white", "brown", "grey", "gray", "gold", "golden", "silver",
    "beige", "violet", "indigo", "turquoise", "navy", "maroon", "cream", "tan",
    "crimson", "scarlet", "blonde", "blond", "pale", "dark", "bright", "colorful",
    "colourful",
}

# topic -> words. Applied on the lemma regardless of part of speech,
# except cooking, which is verbs only (see COOKING).
MANUAL = {
    "kitchen": "oven stove sink fridge refrigerator freezer microwave toaster kettle pot pan bowl plate dish cup mug glass spoon fork knife chopping board countertop cupboard cabinet drawer faucet tap apron recipe ingredient blender dishwasher saucepan frying whisk ladle colander strainer",
    "cooking": "cook bake fry boil roast grill steam chop slice peel mix stir whisk pour spread melt simmer knead grate dice mince marinate season taste serve barbecue saute stew poach scramble toast blend mash rinse soak thaw freeze heat cool",
    "drinks": "water tea coffee milk juice beer wine soda cola lemonade cocktail whiskey whisky champagne juice soft drink beverage drink thirsty sip straw alcohol cocktail espresso cappuccino latte smoothie shake cider liquor brandy rum vodka gin",
    "restaurant": "restaurant cafe café menu waiter waitress bill tip order reservation buffet diner canteen snack bar takeaway take-away chef table service appetizer dessert main course starter",
    "family": "family mother father parent sister brother son daughter child children aunt uncle cousin grandmother grandfather grandma grandpa wife husband spouse relative nephew niece grandchild baby twin parent in-law sibling mom dad mummy daddy kid",
    "airport": "airport airplane aeroplane plane flight passport luggage suitcase boarding gate terminal runway pilot customs visa ticket departure arrival baggage airline takeoff landing security check-in layover jet aircraft crew cabin trolley",
    "hotel": "hotel motel hostel lobby reception receptionist room key reservation checkout check-in guest single double suite vacancy inn resort concierge housekeeping minibar booking stay",
    "office": "office desk chair computer printer photocopier meeting calendar email e-mail inbox folder file stapler notebook colleague boss manager secretary clerk cubicle stationery paperclip keyboard mouse screen monitor",
    "business": "business company firm client customer contract deal market profit loss strategy manager entrepreneur startup partnership corporate trade commerce industry brand merger investment shareholder",
    "money": "money cash coin note bank banknote wallet purse price cost salary wage income tax fee debt loan credit card budget expensive cheap rich poor afford pay payment receipt invoice discount interest savings account atm currency dollar euro pound",
    "shopping": "shop store shopping mall market supermarket grocery buy sell price sale bargain queue cashier customer basket cart receipt discount brand size fit try on refund exchange customer",
    "education": "school student teacher class lesson homework exam test grade university college classroom subject course lecture seminar campus library scholarship pupil headteacher principal textbook notebook pencil pen ruler homework degree diploma curriculum",
    "computers": "computer laptop keyboard mouse screen monitor software hardware internet website email password program app application file folder download upload browser server data digital click cursor wifi network chip memory processor code coding programmer bug virus backup",
    "technology": "technology device machine engine robot digital electronic electricity battery cable wire sensor camera phone smartphone tablet invention engineer engineering gadget appliance",
    "science": "science scientist experiment laboratory lab theory hypothesis research atom molecule cell energy gravity chemical physics chemistry biology microscope formula discovery evidence sample",
    "math": "math mathematics number add subtract multiply divide plus minus equal equation fraction decimal percent geometry algebra angle triangle square circle graph calculate calculation sum total average",
    "nature": "nature landscape mountain hill valley river lake sea ocean forest wood field island beach desert rock stone cave cliff shore coast countryside wilderness sky earth ground soil",
    "environment": "environment pollution recycle recycling waste climate carbon energy conservation wildlife habitat ecosystem sustainable plastic rubbish garbage landfill emission ozone green",
    "space": "space planet star moon sun earth orbit galaxy astronaut rocket satellite universe comet asteroid solar eclipse telescope gravity mars venus jupiter saturn",
    "weather": "weather rain snow wind cloud storm sun sunny cloudy fog ice thunder lightning temperature hot cold warm cool humid dry wet forecast umbrella rainbow hail mist breeze hurricane typhoon",
    "sports": "sport sports football soccer basketball tennis swim swimming run running gym game match team player coach ball goal score win lose race bicycle cycling ski skiing golf baseball volleyball box boxing yoga marathon referee stadium league champion",
    "music": "music song sing singer band concert guitar piano drum violin flute melody rhythm album lyrics orchestra jazz rock pop classical headphone microphone composer melody",
    "art": "art artist paint painting draw drawing museum gallery sculpture statue sketch canvas colour color brush portrait creative design illustration exhibition",
    "movies": "movie film cinema actor actress director scene screen script camera audience subtitle trailer horror comedy drama series episode character role star cast",
    "books": "book novel story author read reading library page chapter poem poetry literature fiction shelf magazine article paragraph sentence word dictionary",
    "media": "media news newspaper journalist television tv radio broadcast interview headline report reporter press magazine advert advertisement channel program programme podcast",
    "language": "language word sentence grammar vocabulary translate translation meaning pronounce pronunciation alphabet letter phrase idiom dialect tongue speak talk say tell ask answer",
    "communication": "communication talk speak say tell ask answer call phone message text email letter conversation discuss discussion argue argument explain question reply",
    "law": "law legal lawyer court judge jury crime criminal police prison jail fine arrest trial justice right rights contract illegal legal sue witness evidence verdict sentence theft fraud",
    "politics": "politics political government president minister parliament election vote voter party policy democracy citizen state nation law power leader campaign mayor council republic king queen",
    "military": "army soldier war weapon gun battle military navy force attack defend defense defence peace uniform officer general captain troop bomb tank missile",
    "religion": "religion god church temple mosque pray prayer priest faith belief holy bible christmas easter spirit soul worship religious muslim christian buddhist hindu",
    "tools": "tool hammer screwdriver nail screw saw drill wrench pliers brush ladder rope tape measure toolbox spanner bolt nut",
    "materials": "wood metal steel iron gold silver plastic glass paper cloth cotton wool leather rubber stone brick concrete silk nylon copper glass",
    "energy": "energy power electricity electric gas oil petrol fuel coal solar nuclear battery heat light engine watt",
    "shapes": "shape circle square triangle rectangle line round corner edge straight curve oval star diamond pattern size",
    "appearance": "beautiful ugly pretty handsome tall short fat thin slim young old appearance look face hair beard moustache smile eye skin",
    "personality": "kind nice friendly polite rude honest shy brave calm angry patient clever stupid lazy hardworking generous selfish funny serious quiet loud personality character mood",
    "social": "friend friendship relationship marry marriage wedding party invite guest neighbor neighbour community social meet meeting together alone love hate trust respect",
    "daily": "morning routine breakfast lunch dinner sleep wake shower brush teeth housework clean wash iron cook walk everyday daily habit usually always often",
    "holidays": "holiday vacation festival christmas easter birthday party celebrate celebration gift present firework vacation new year halloween wedding anniversary",
    "city": "city town street road square bridge traffic pavement sidewalk downtown suburb building skyscraper station bus stop corner block neighborhood neighbourhood urban village capital",
    "travel": "travel trip journey tour tourist map ticket passport luggage suitcase guide holiday vacation abroad foreign border visit sightseeing camera souvenir backpack",
    "transport": "car bus train taxi bicycle bike motorcycle plane boat ship truck tram subway metro station driver passenger traffic road rail railway vehicle petrol gas station",
    "work": "work job office boss colleague meeting salary employ employee employer career profession occupation task project deadline interview hire fire resign retire worker staff",
    "house": "house home apartment flat room door window wall floor roof garden yard garage stairs kitchen bedroom bathroom living address rent neighbor neighbour building",
    "furniture": "furniture chair table bed sofa couch desk shelf cupboard wardrobe cabinet lamp mirror carpet rug curtain cushion drawer closet stool bench",
    "health": "health healthy sick ill pain hurt doctor nurse hospital clinic medicine exercise diet sleep stress tired energy symptom fever cough cold flu injury bandage",
    "body": "body head hair face eye ear nose mouth tooth teeth neck shoulder arm hand finger leg foot feet knee back skin bone heart blood brain stomach chest lip tongue waist",
    "clothes": "clothes shirt trousers pants dress skirt jacket coat shoe sock hat cap glove scarf jeans sweater jumper tie belt pocket button zip uniform wear fashion size cotton",
    "animals": "animal dog cat bird fish horse cow pig sheep chicken duck mouse lion tiger bear elephant monkey pet zoo farm wild insect bee ant spider snake frog whale dolphin",
    "plants": "plant tree flower grass leaf garden forest wood rose bush seed fruit vegetable farm field crop moss bamboo palm cactus herb",
}

COOKING_POS = {"verb"}


def _words(text: str) -> set[str]:
    return {part.strip().lower() for part in text.split() if part.strip()}


def is_phrasal(word: str, pos: str) -> bool:
    if pos != "verb":
        return False
    parts = word.lower().replace("–", " ").split()
    if len(parts) < 2 or len(parts) > 4:
        return False
    if not parts[0].isalpha():
        return False
    return any(part in PARTICLES for part in parts[1:])


def _resolve_synset(en, lemma: str, pos: str, snippet: str):
    found = en.words(lemma.replace(" ", "_"), pos=pos)
    if not found:
        found = en.words(lemma, pos=pos)
    if not found:
        return None
    senses = found[0].senses()
    if snippet:
        needle = snippet.lower()
        for sense in senses:
            definition = (sense.synset().definition() or "").lower()
            if needle in definition:
                return sense.synset()
        return None
    return senses[0].synset() if senses else None


def _closure(synset, limit: int = 8000) -> set[str]:
    seen: set[str] = set()
    stack = [synset]
    while stack:
        current = stack.pop()
        ident = current.id
        if ident in seen:
            continue
        seen.add(ident)
        if len(seen) >= limit:
            break
        stack.extend(current.hyponyms())
    return seen


def _build_syn_map(en) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for topic, seeds in SEEDS.items():
        if topic == "sports_game":
            continue
        for lemma, pos, snippet in seeds:
            synset = _resolve_synset(en, lemma, pos, snippet)
            if synset is None:
                print(f"topic seed missing: {topic} {lemma} {snippet!r}")
                continue
            print(f"topic seed {topic}: {synset.id} {(synset.definition() or '')[:70]}")
            for ident in _closure(synset):
                mapping.setdefault(ident, set()).add(topic)
    return mapping


def _lookup_topics(en, syn_map: dict[str, set[str]], word: str, pos: str) -> set[str]:
    wn_pos = {"noun": "n", "verb": "v", "adj": "a", "adv": "r"}.get(pos)
    if not wn_pos:
        return set()
    lemma = word.lower().replace(" ", "_").replace("-", "_")
    candidates = [lemma]
    spaced = word.lower().replace("-", " ")
    if " " in spaced:
        candidates.append(spaced.replace(" ", "_"))
    if lemma in SPELLING:
        candidates.append(SPELLING[lemma])
    found = set()
    for candidate in candidates:
        words = en.words(candidate, pos=wn_pos)
        if wn_pos == "a" and not words:
            words = [item for item in en.words(candidate) if item.pos in {"a", "s"}]
        if not words:
            continue
        for sense in words[0].senses()[:2]:
            topics = syn_map.get(sense.synset().id)
            if topics:
                found |= topics
        if found:
            break
    return found


def _prune(found: set[str]) -> list[str]:
    topics = set(found)
    for child, parent in PARENT.items():
        if child in topics and parent in topics:
            topics.discard(parent)
    ordered = [topic for topic in TOPIC_ORDER if topic in topics]
    flags = [topic for topic in ("phrasal", "cooking", "numbers", "time", "colors", "adjectives") if topic in ordered]
    rest = [topic for topic in ordered if topic not in flags]
    return (flags + rest)[:4]


def classify(cards: list[dict]) -> list[dict]:
    import wn

    en = wn.Wordnet("oewn:2024")
    syn_map = _build_syn_map(en)
    manuals = {topic: _words(text) for topic, text in MANUAL.items()}
    for card in cards:
        word = (card.get("word") or "").strip()
        key = word.lower()
        pos = card.get("pos") or ""
        found = _lookup_topics(en, syn_map, word, pos)
        for topic, words in manuals.items():
            if key not in words:
                continue
            if topic == "cooking" and pos not in COOKING_POS:
                continue
            found.add(topic)
        if not found:
            for old in card.get("_src") or []:
                for topic in CEFR_MAP.get(old, []):
                    found.add(topic)
        if is_phrasal(word, pos):
            found.add("phrasal")
        if key in NUMBERS or pos == "num":
            found.add("numbers")
        if key in TIME_WORDS:
            found.add("time")
        if key in COLOR_WORDS:
            found.add("colors")
        if pos == "adj" and card.get("level") in {"A1", "A2", "B1", "B2"}:
            found.add("adjectives")
        kept = _prune(found)
        if kept:
            card["topics"] = kept
        else:
            card.pop("topics", None)
        card.pop("_src", None)
    counts: dict[str, int] = {topic: 0 for topic in TOPIC_ORDER}
    for card in cards:
        for topic in card.get("topics") or []:
            counts[topic] = counts.get(topic, 0) + 1
    kept_ids = {topic for topic, count in counts.items() if count >= 12 and topic in TOPIC_NAMES}
    dropped = [topic for topic in counts if topic not in kept_ids and counts[topic]]
    if dropped:
        print("dropped thin topics", [(topic, counts[topic]) for topic in dropped])
    for card in cards:
        topics = [topic for topic in card.get("topics") or [] if topic in kept_ids]
        if topics:
            card["topics"] = topics
        else:
            card.pop("topics", None)
    return [
        {"id": topic, "name": TOPIC_NAMES[topic], "count": counts[topic]}
        for topic in TOPIC_ORDER
        if topic in kept_ids
    ]


def topic_levels(cards: list[dict]) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = {}
    for card in cards:
        level = card.get("level")
        for topic in card.get("topics") or []:
            row = table.setdefault(topic, {})
            row[level] = row.get(level, 0) + 1
    return table
