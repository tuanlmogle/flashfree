#!/usr/bin/env python3
"""Check the built deck: unique ids, required fields, and no lost progress keys."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
MIN_TOTAL = 40000


def take(card: dict, seen: set[str]) -> None:
    for key in ("id", "word", "pos", "level", "meaning"):
        if not card.get(key):
            print("ERROR: missing", key, card.get("id"), file=sys.stderr)
            sys.exit(1)
    if card["level"] not in LEVELS:
        print("ERROR: bad level", card.get("id"), card.get("level"), file=sys.stderr)
        sys.exit(1)
    if card["id"] in seen:
        print("ERROR: duplicate id", card["id"], file=sys.stderr)
        sys.exit(1)
    seen.add(card["id"])


def main() -> None:
    meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
    cards = []
    seen: set[str] = set()
    per_level = {level: 0 for level in LEVELS}
    for level in LEVELS:
        payload = json.loads((DATA / f"level-{level.lower()}.json").read_text(encoding="utf-8"))
        group = payload.get("cards") or []
        for card in group:
            if card.get("level") != level:
                print("ERROR: card in the wrong level file", card.get("id"), file=sys.stderr)
                sys.exit(1)
            take(card, seen)
            per_level[level] += 1
            cards.append(card)
    field_dir = DATA / "fields"
    disk_files = sorted(path.stem for path in field_dir.glob("*.json")) if field_dir.exists() else []
    for stem in disk_files:
        payload = json.loads((field_dir / f"{stem}.json").read_text(encoding="utf-8"))
        for card in payload.get("cards") or []:
            take(card, seen)
            per_level[card["level"]] += 1
            cards.append(card)
    if sorted(meta.get("topicFiles") or []) != disk_files:
        print("ERROR: meta.topicFiles does not match data/fields", file=sys.stderr)
        sys.exit(1)
    for level in LEVELS:
        if per_level[level] != meta["counts"][level]:
            print(f"ERROR: {level} count {per_level[level]} != meta {meta['counts'][level]}", file=sys.stderr)
            sys.exit(1)
    if len(cards) < MIN_TOTAL:
        print(f"ERROR: only {len(cards)} cards", file=sys.stderr)
        sys.exit(1)
    if meta.get("total") != len(cards):
        print("ERROR: meta total mismatch", file=sys.stderr)
        sys.exit(1)
    previous = DATA / "previous-ids.json"
    if previous.exists():
        old = set(json.loads(previous.read_text(encoding="utf-8")))
        missing = sorted(old - seen)
        if missing:
            print(f"ERROR: {len(missing)} previous ids missing, e.g. {missing[:8]}", file=sys.stderr)
            sys.exit(1)
    en_n = sum(1 for card in cards if card.get("meaningLang") == "en")
    pictured = sum(1 for card in cards if card.get("img") or card.get("emo"))
    print(f"ok {len(cards)} cards, english-only {en_n}, with picture {pictured}")


if __name__ == "__main__":
    main()
