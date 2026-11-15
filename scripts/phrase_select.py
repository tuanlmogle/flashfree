"""Choose common American phrasal verbs, idioms, and collocations.

The functions here do not download anything. build_phrases.py feeds them
text that already comes from openly licensed sources.
"""

from __future__ import annotations

import math

PARTICLES = frozenset({
    "up", "down", "out", "off", "on", "in", "over", "away", "back", "through",
    "around", "about", "along", "apart", "by", "for", "into", "onto", "after",
    "across", "ahead", "forward", "together", "aside", "round", "upon", "of",
    "with", "without", "apart",
})

PHRASAL_VERBS = frozenset({
    "act", "add", "ask", "back", "blow", "break", "bring", "build", "burn",
    "call", "calm", "carry", "catch", "check", "clean", "clear", "close",
    "come", "count", "cross", "cut", "die", "draw", "dress", "drive", "drop",
    "eat", "end", "fall", "figure", "fill", "find", "finish", "fit", "fix",
    "follow", "get", "give", "go", "grow", "hand", "hang", "head", "hear",
    "help", "hold", "hurry", "join", "keep", "kick", "knock", "lay", "leave",
    "let", "lie", "lift", "live", "lock", "log", "look", "make", "mark",
    "mix", "move", "open", "pass", "pay", "pick", "point", "pull", "push",
    "put", "read", "ring", "roll", "run", "send", "set", "settle", "shake",
    "show", "shut", "sign", "sit", "slow", "sort", "speak", "stand", "start",
    "stay", "stick", "stop", "take", "talk", "tear", "think", "throw", "tie",
    "try", "turn", "use", "wake", "walk", "warm", "wash", "watch", "wear",
    "wind", "work", "write", "zip", "back", "blow", "boot", "bottle", "bowl",
    "branch", "break", "bring", "brush", "build", "bump", "buy", "call",
    "care", "carry", "cash", "cast", "catch", "change", "charge", "chase",
    "cheat", "check", "cheer", "chew", "chip", "choke", "chop", "clean",
    "clear", "climb", "clock", "close", "cloud", "come", "cool", "copy",
    "count", "cover", "crack", "crash", "crawl", "cross", "cry", "cut",
    "deal", "die", "dig", "dip", "divide", "do", "drag", "draw", "dream",
    "dress", "drink", "drive", "drop", "dry", "eat", "empty", "end", "enter",
    "even", "face", "fade", "fall", "fasten", "feed", "feel", "fight",
    "figure", "fill", "find", "finish", "fire", "fit", "fix", "flick",
    "flip", "float", "flood", "flow", "fly", "fold", "follow", "fool",
    "force", "forget", "fork", "freeze", "freshen", "frown", "gang", "get",
    "give", "glance", "go", "grind", "grow", "hand", "hang", "happen",
    "head", "hear", "heat", "help", "hide", "hit", "hold", "hook", "hop",
    "hurry", "iron", "jack", "jam", "join", "jot", "jump", "keep", "key",
    "kick", "knock", "land", "lay", "lead", "lean", "leave", "let", "lie",
    "lift", "light", "line", "link", "listen", "live", "lock", "log",
    "look", "loosen", "lose", "make", "map", "mark", "marry", "match",
    "measure", "meet", "melt", "mess", "miss", "mix", "mount", "move",
    "nod", "note", "open", "opt", "own", "pack", "pair", "pan", "pass",
    "patch", "pay", "peel", "phase", "pick", "pile", "pin", "pipe", "place",
    "plan", "play", "plug", "point", "pop", "pour", "press", "print",
    "pull", "pump", "punch", "push", "put", "quiet", "race", "reach",
    "read", "reason", "rein", "rely", "ride", "ring", "rip", "rise", "roll",
    "root", "rough", "round", "rub", "rule", "run", "rush", "scale", "scare",
    "scrape", "screen", "screw", "seal", "search", "see", "sell", "send",
    "serve", "set", "settle", "sew", "shake", "shape", "share", "shave",
    "shell", "shine", "ship", "shoot", "shop", "shorten", "shout", "show",
    "shrug", "shut", "sign", "single", "sink", "sit", "size", "sleep",
    "slice", "slip", "slow", "smash", "smell", "smooth", "snap", "soak",
    "sort", "sound", "space", "speak", "speed", "spell", "spill", "spin",
    "split", "spread", "spring", "sprout", "square", "squeeze", "stack",
    "stamp", "stand", "stare", "start", "stay", "step", "stick", "stir",
    "stop", "store", "storm", "straighten", "stretch", "strike", "string",
    "strip", "sum", "swear", "sweep", "swell", "switch", "tag", "take",
    "talk", "tap", "team", "tear", "tell", "test", "think", "throw", "tick",
    "tide", "tie", "tighten", "tip", "tone", "top", "toss", "touch", "tough",
    "track", "trade", "trail", "train", "treat", "trim", "trip", "try",
    "tuck", "tune", "turn", "type", "use", "vacuum", "vote", "wait", "wake",
    "walk", "warm", "wash", "waste", "watch", "water", "wave", "wear",
    "weed", "weigh", "whip", "wind", "wipe", "work", "wrap", "wrinkle",
    "write", "zip", "zoom",
})

VERBS = frozenset({
    "make", "take", "give", "get", "have", "do", "pay", "keep", "put", "set",
    "hold", "run", "break", "bring", "catch", "lose", "find", "feel", "leave",
    "turn", "come", "go", "look", "call", "raise", "draw", "save", "spend",
    "miss", "pass", "meet", "change", "open", "close", "build", "cut", "fill",
    "cover", "carry", "pick", "drop", "pull", "push", "win", "hit", "play",
    "work", "ask", "tell", "show", "need", "want", "try", "start", "stop",
    "help", "use", "move", "send", "reach", "catch", "hold",
})

ADJECTIVES = frozenset({
    "heavy", "strong", "high", "low", "hard", "soft", "deep", "wide", "close",
    "public", "private", "common", "serious", "final", "full", "empty", "free",
    "fair", "direct", "clear", "main", "major", "minor", "real", "good", "bad",
    "big", "small", "long", "short", "early", "late", "hot", "cold", "warm",
    "dry", "wet", "bright", "dark", "loud", "quiet", "safe", "poor", "rich",
    "fresh", "raw", "sweet", "sharp", "daily", "annual", "national", "local",
    "social", "medical", "legal", "physical", "mental", "personal", "natural",
    "human", "special", "general", "basic", "certain", "whole", "great",
})

DETS = frozenset({"a", "an", "the"})
SKIP_NOUN = frozenset({
    "a", "an", "the", "of", "to", "for", "in", "on", "at", "by", "up", "out",
    "off", "it", "me", "you", "he", "she", "we", "they", "be", "is", "am",
    "are", "was", "were", "been", "being", "not", "no", "this", "that",
    "these", "those", "his", "her", "their", "your", "my", "our", "its",
    "and", "or", "if", "as", "so", "than", "then", "there", "here", "what",
    "when", "who", "how", "which", "with", "from", "into", "about",
})

# One deck for phrasal verbs and idioms, one for collocations.
TOPIC_PHRASE = "phrasal"
TOPIC_COLLOCATION = "collocation"
TOPIC_NAME = {
    TOPIC_PHRASE: "Cụm động từ & thành ngữ",
    TOPIC_COLLOCATION: "Cụm từ hay đi chung",
}

# Fixed phrases learners meet constantly. Wiktionary does not always tag them idiom.
EVERYDAY_PHRASES = frozenset({
    "of course", "by the way", "come on", "make sure", "give up", "figure out",
    "find out", "pick up", "look for", "get up", "run out", "hang out",
    "take care of",
})
PREFERRED_POS = {
    "of course": "adv",
    "come on": "intj",
    "by the way": "prep_phrase",
}


def _tags(tags) -> set[str]:
    return {str(tag).lower().replace("_", " ").strip() for tag in tags or []}


def reject_usage(tags) -> bool:
    """Skip British-only, archaic, obsolete, rare, or dated wording."""
    low = _tags(tags)
    blob = " ".join(sorted(low))
    if any(bit in blob for bit in ("archaic", "obsolete", "rare", "dated", "historical")):
        return True
    uk = bool(low & {"uk", "british", "britain", "commonwealth", "australian"}) or "british" in blob
    us = bool(low & {"us", "u.s.", "american", "america"})
    return uk and not us


CLOSED = PARTICLES | DETS | frozenset({
    "be", "am", "is", "are", "was", "were", "been", "being",
    "do", "does", "did", "done", "have", "has", "had",
    "as", "if", "or", "and", "not", "no", "that", "this", "it",
    "to", "from", "than", "then", "so", "too", "very", "at",
    "you", "your", "all", "can", "will", "may", "might", "shall",
    "should", "would", "could", "just", "even", "much", "many",
    "more", "most", "also", "else", "such", "like", "well",
    "here", "there", "what", "when", "who", "how", "its", "our",
})
NOUN_BLOCK = CLOSED | frozenset({
    "tom", "mary", "john", "him", "her", "them", "any", "some",
    "anything", "something", "nothing", "everything", "enough",
    "lot", "one", "way", "thing", "back", "now", "over", "else",
    "here", "there", "someone", "anyone", "everybody", "somebody",
    "come", "left", "little", "two", "three", "four", "five", "six",
    "seven", "eight", "nine", "ten", "things", "ones", "bit",
    "last", "next", "lots",
})


def phrase_kind(word: str, pos: str, tags) -> str | None:
    """Return 'phrasal' or 'idiom', or None when the entry should be dropped."""
    if reject_usage(tags):
        return None
    text = (word or "").strip().lower()
    parts = text.split()
    if not 2 <= len(parts) <= 6:
        return None
    if any(not part.replace("'", "").replace("-", "").isalpha() for part in parts):
        return None
    lexical = [part for part in parts if part not in CLOSED]
    if not lexical:
        return None
    blob = " ".join(_tags(tags))
    idiomatic = "idiom" in blob or "proverb" in blob
    pronouns = {"it", "me", "him", "her", "them", "us", "one", "someone", "something"}
    phrasal = (
        pos == "verb"
        and parts[0] in PHRASAL_VERBS
        and not any(part in pronouns for part in parts)
        and 2 <= len(parts) <= 4
        and ("phrasal" in blob or any(part in PARTICLES for part in parts[1:]))
    )
    if phrasal:
        return "phrasal"
    long = [part for part in lexical if len(part) >= 4]
    if idiomatic and (len(lexical) >= 2 or long or len(parts) >= 3):
        return "idiom"
    if text in EVERYDAY_PHRASES:
        return "idiom"
    return None


def collocations_in(tokens: list[str]) -> list[str]:
    """Verb+noun and adjective+noun pairs in one sentence."""
    low = [tok.lower() for tok in tokens if tok]
    found: list[str] = []
    seen = set()

    def add(phrase: str) -> None:
        if phrase not in seen:
            seen.add(phrase)
            found.append(phrase)

    for index, tok in enumerate(low):
        if tok not in VERBS:
            continue
        noun_at = index + 1
        if noun_at < len(low) and low[noun_at] in DETS:
            noun_at += 1
        if noun_at >= len(low):
            continue
        noun = low[noun_at]
        if not _noun_ok(noun):
            continue
        if noun_at == index + 2 and low[index + 1] in DETS:
            add(f"{tok} {low[index + 1]} {noun}")
        elif noun_at == index + 1:
            add(f"{tok} {noun}")
    for index, tok in enumerate(low[:-1]):
        if tok in ADJECTIVES and _noun_ok(low[index + 1]):
            add(f"{tok} {low[index + 1]}")
    return found


def _noun_ok(token: str) -> bool:
    return (
        len(token) >= 3
        and token.isalpha()
        and token not in SKIP_NOUN
        and token not in NOUN_BLOCK
        and token not in ADJECTIVES
    )


PLACEHOLDERS = frozenset({
    "someone", "something", "somebody", "one's", "someone's", "somebody's",
})


def gloss_rank(word: str, pos: str, tags, gloss: str, index: int = 0) -> tuple:
    """Lower is better. The first everyday sense beats a later slang or sexual one."""
    blob = " ".join(_tags(tags))
    low = (gloss or "").lower()
    awkward = any(bit in low for bit in ("sexual", "menstruat", "intercourse", "to kill"))
    literal = "literally" in blob and "idiom" not in blob and "phrasal" not in blob
    preferred = PREFERRED_POS.get(word or "")
    return (
        1 if awkward else 0,
        1 if literal else 0,
        0 if preferred and pos == preferred else 1,
        index,
    )


PRONOUNS = frozenset({
    "i", "you", "your", "yours", "me", "my", "mine", "we", "us", "our",
    "he", "she", "him", "her", "his", "they", "them", "their", "it", "its",
})


def has_pronoun(word: str) -> bool:
    return any(part in PRONOUNS for part in (word or "").lower().split())


def association(word: str, count: int, unigram: dict, sentences: int) -> float:
    """How much more often the whole phrase occurs than its words would by chance."""
    parts = (word or "").split()
    if count <= 0 or sentences <= 0 or not parts:
        return -99.0
    expected = float(sentences)
    for part in parts:
        seen = unigram.get(part, 0)
        if seen <= 0:
            return -99.0
        expected *= seen / sentences
    if expected <= 0:
        return -99.0
    return math.log(count / expected)


def has_placeholder(word: str) -> bool:
    parts = (word or "").lower().replace("’", "'").split()
    return any(part in PLACEHOLDERS or part.startswith("someone") or part.startswith("something") for part in parts)


def usable_phrase(word: str, count: int, slang: bool = False, vulgar: bool = False) -> bool:
    """Drop zero-evidence, vulgar, slang-only, and awkward placeholder headwords."""
    if vulgar or count <= 0:
        return False
    if slang and count < 30:
        return False
    if has_placeholder(word) and count < 40:
        return False
    return True


def level_for_rank(index: int, total: int) -> str:
    """Most-used phrases are A2; rarer ones step through B1, B2, C1, and C2."""
    if total <= 1:
        return "A2"
    frac = index / total
    if frac < 0.12:
        return "A2"
    if frac < 0.34:
        return "B1"
    if frac < 0.58:
        return "B2"
    if frac < 0.82:
        return "C1"
    return "C2"


def assign_usage_levels(rows: list[dict]) -> list[dict]:
    ordered = sorted(rows, key=lambda row: (-(row.get("count") or 0), row.get("word") or ""))
    total = len(ordered)
    for index, row in enumerate(ordered):
        row["level"] = level_for_rank(index, total)
        row["freq"] = row.get("count") or 0
    return ordered


def keep_frequent(rows: list[dict], cap: int, min_count: int) -> list[dict]:
    """Tatoeba count first, so a real pair beats a zipf accident."""
    chosen = [row for row in rows if (row.get("count") or 0) >= min_count]
    chosen.sort(key=lambda row: (-(row.get("count") or 0), -(row.get("zipf") or 0), row.get("word") or ""))
    return chosen[:cap]


def keep_common(rows: list[dict], cap: int, min_zipf: float, min_count: int) -> list[dict]:
    """Highest zipf first, then Tatoeba counts. Ties break on the phrase."""
    chosen = [
        row for row in rows
        if (row.get("zipf") or 0) >= min_zipf or (row.get("count") or 0) >= min_count
    ]
    chosen.sort(key=lambda row: (-(row.get("zipf") or 0), -(row.get("count") or 0), row.get("word") or ""))
    return chosen[:cap]
