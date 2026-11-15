#!/usr/bin/env python3
"""Rebuild vocabulary JSON from the pinned open sources, then check it.

Reads data/extra-words.txt. Keeps every card id already in data/level-*.json
so spaced-repetition progress stored in the browser still matches.
Does not call the Wikimedia API; photos already saved on a card stay there.
"""

from __future__ import annotations

import json
from pathlib import Path

import build_fields
import build_phrases
import build_pictures
import build_vocab
import validate_vocab

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    previous = build_vocab.load_disk_cards()
    snapshot = ROOT / "data" / "previous-ids.json"
    snapshot.write_text(
        json.dumps(sorted(card["id"] for card in previous), ensure_ascii=False),
        encoding="utf-8",
    )
    try:
        build_vocab.main()
        build_pictures.main()
        build_fields.main()
        build_phrases.main()
        validate_vocab.main()
    finally:
        if snapshot.exists():
            snapshot.unlink()


if __name__ == "__main__":
    main()
