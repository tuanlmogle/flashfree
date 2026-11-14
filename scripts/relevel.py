#!/usr/bin/env python3
"""Reassign levels on the current JSON without changing card ids.

Official CEFR-J / Octanove rows keep that level. Every other card uses
level_from_zipf (C1 from Zipf 2.70, C2 only below that).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from build_vocab import LEVEL_RANK, SOURCE_DATE, relevel_cards
from topics import topic_levels

DATA = Path(__file__).resolve().parents[1] / "data"


def main() -> None:
    cards = []
    for level in LEVEL_RANK:
        payload = json.loads((DATA / f"level-{level.lower()}.json").read_text(encoding="utf-8"))
        cards.extend(payload.get("cards") or [])
    before = {level: 0 for level in LEVEL_RANK}
    for card in cards:
        before[card["level"]] += 1
    moved = relevel_cards(cards)
    cards.sort(key=lambda card: (LEVEL_RANK[card["level"]], card["word"].lower(), card["pos"], card["id"]))
    grouped = {level: [] for level in LEVEL_RANK}
    counts = {level: 0 for level in LEVEL_RANK}
    vi_n = en_n = 0
    for card in cards:
        grouped[card["level"]].append(card)
        counts[card["level"]] += 1
        if card.get("meaningLang") == "en":
            en_n += 1
        else:
            vi_n += 1
    for level, group in grouped.items():
        path = DATA / f"level-{level.lower()}.json"
        path.write_text(json.dumps({"cards": group}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    meta_path = DATA / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["generated"] = SOURCE_DATE
    meta["counts"] = counts
    meta["total"] = len(cards)
    meta["withVi"] = vi_n
    meta["withEn"] = en_n
    meta["levels"] = list(LEVEL_RANK)
    meta["topicLevels"] = topic_levels(cards)
    topic_counts = Counter()
    for card in cards:
        for topic in card.get("topics") or []:
            topic_counts[topic] += 1
    for topic in meta.get("topics") or []:
        topic["count"] = topic_counts.get(topic["id"], 0)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("before", before)
    print("after", counts, "moved", moved)


if __name__ == "__main__":
    main()
