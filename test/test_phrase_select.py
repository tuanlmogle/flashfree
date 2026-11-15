import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from phrase_select import (
    assign_usage_levels,
    association,
    collocations_in,
    gloss_rank,
    has_placeholder,
    has_pronoun,
    keep_common,
    level_for_rank,
    phrase_kind,
    reject_usage,
    usable_phrase,
)


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

    def test_everyday_phrases_and_the_learner_sense(self):
        self.assertEqual(phrase_kind("of course", "adv", []), "idiom")
        self.assertEqual(phrase_kind("by the way", "prep_phrase", ["idiomatic"]), "idiom")
        self.assertEqual(phrase_kind("run out", "verb", ["phrasal"]), "phrasal")
        everyday = gloss_rank("come on", "intj", [], "Come along with me.", 0)
        slang = gloss_rank("come on", "verb", ["idiomatic"], "To show sexual interest.", 0)
        self.assertLess(everyday, slang)
        first = gloss_rank("get up", "verb", ["literally"], "To move upward.", 0)
        bed = gloss_rank("get up", "verb", [], "To rise from one's bed.", 1)
        self.assertLess(bed, first)
        hang = gloss_rank("hang out", "verb", ["idiomatic", "slang"], "To spend time with somebody.", 0)
        crave = gloss_rank("hang out", "verb", ["informal"], "To crave or desperately want.", 3)
        self.assertLess(hang, crave)
        self.assertTrue(has_pronoun("forget you"))
        self.assertFalse(has_pronoun("give up"))
        chance = association("you think", 50, {"you": 1000, "think": 1000}, 10000)
        bound = association("give up", 80, {"give": 100, "up": 200}, 10000)
        self.assertLess(chance, 0)
        self.assertGreater(bound, 1)

    def test_usage_levels_follow_how_often_the_phrase_occurs(self):
        self.assertEqual(level_for_rank(0, 100), "A2")
        self.assertEqual(level_for_rank(20, 100), "B1")
        self.assertEqual(level_for_rank(40, 100), "B2")
        self.assertEqual(level_for_rank(70, 100), "C1")
        self.assertEqual(level_for_rank(90, 100), "C2")
        self.assertTrue(has_placeholder("what was someone smoking"))
        self.assertFalse(usable_phrase("what was someone smoking", 1, slang=True))
        self.assertFalse(usable_phrase("never said", 0))
        self.assertTrue(usable_phrase("take care of someone", 50))
        rows = assign_usage_levels([
            {"word": f"rare {index}", "count": index} for index in range(1, 9)
        ] + [
            {"word": "give up", "count": 400},
            {"word": "figure out", "count": 200},
        ])
        self.assertEqual(rows[0]["word"], "give up")
        self.assertEqual(rows[0]["level"], "A2")
        self.assertEqual(rows[-1]["level"], "C2")

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
