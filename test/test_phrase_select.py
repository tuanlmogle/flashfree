import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from phrase_select import collocations_in, keep_common, phrase_kind, reject_usage


class PhraseSelectTest(unittest.TestCase):
    def test_phrasal_and_idiom_share_a_gate(self):
        self.assertEqual(phrase_kind("give up", "verb", []), "phrasal")
        self.assertEqual(phrase_kind("run out of", "verb", ["phrasal"]), "phrasal")
        self.assertEqual(phrase_kind("break the ice", "phrase", ["idiomatic"]), "idiom")
        self.assertIsNone(phrase_kind("give up", "verb", ["British", "archaic"]))
        self.assertIsNone(phrase_kind("queue up", "verb", ["UK"]))
        self.assertEqual(phrase_kind("figure out", "verb", ["US", "UK"]), "phrasal")
        self.assertIsNone(phrase_kind("be with", "verb", []))
        self.assertIsNone(phrase_kind("as of", "verb", []))
        self.assertIsNone(phrase_kind("in on", "verb", []))
        self.assertIsNone(phrase_kind("at that", "phrase", ["idiomatic"]))
        self.assertIsNone(phrase_kind("you all", "phrase", ["idiomatic"]))
        self.assertIsNone(phrase_kind("and the like", "noun", ["idiomatic"]))
        self.assertEqual(phrase_kind("on hold", "phrase", ["idiomatic"]), "idiom")
        self.assertEqual(phrase_kind("break the ice", "phrase", ["idiomatic"]), "idiom")
        self.assertEqual(phrase_kind("hang out", "verb", ["idiomatic", "slang"]), "phrasal")
        self.assertIsNone(phrase_kind("get it on", "verb", ["phrasal"]))
        self.assertIsNone(phrase_kind("time in", "verb", []))
        self.assertEqual(phrase_kind("hang out", "verb", []), "phrasal")

    def test_british_only_is_rejected(self):
        self.assertTrue(reject_usage(["obsolete"]))
        self.assertTrue(reject_usage(["rare"]))
        self.assertTrue(reject_usage(["British"]))
        self.assertFalse(reject_usage(["American"]))
        self.assertFalse(reject_usage(["US", "British"]))

    def test_collocation_patterns(self):
        self.assertIn("make a decision", collocations_in(["Please", "make", "a", "decision", "now"]))
        self.assertIn("heavy rain", collocations_in(["There", "was", "heavy", "rain"]))
        self.assertIn("pay attention", collocations_in(["pay", "attention", "please"]))
        self.assertIn("take a break", collocations_in(["Let's", "take", "a", "break"]))
        self.assertNotIn("make a of", collocations_in(["make", "a", "of"]))

    def test_keep_common_ranks_by_usage(self):
        rows = [
            {"word": "rare pair", "zipf": 1.2, "count": 1},
            {"word": "give up", "zipf": 5.6, "count": 4},
            {"word": "hang out", "zipf": 4.5, "count": 20},
            {"word": "seen often", "zipf": 2.0, "count": 12},
        ]
        kept = keep_common(rows, cap=2, min_zipf=3.0, min_count=8)
        self.assertEqual([row["word"] for row in kept], ["give up", "hang out"])


if __name__ == "__main__":
    unittest.main()
