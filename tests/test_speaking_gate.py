# -*- coding: utf-8 -*-
import unittest

from speaking import engine, models


def take(total=None, error=False, rejected=False):
    return {
        "total": total,
        "error": "network" if error else "",
        "is_rejected": rejected,
        "words": [],
    }


class SpeakingGateTests(unittest.TestCase):
    def test_below_three_stars_can_retry_before_third_scored_take(self):
        state = engine.gate_state([take(60), take(70)], models.MAX_TAKES)
        self.assertFalse(state["achieved"])
        self.assertTrue(state["can_retry"])
        self.assertFalse(state["can_skip"])
        self.assertEqual(2, state["scored_takes"])

    def test_third_scored_take_unlocks_skip_when_still_below_three_stars(self):
        state = engine.gate_state([take(60), take(70), take(74)], models.MAX_TAKES)
        self.assertFalse(state["achieved"])
        self.assertFalse(state["can_retry"])
        self.assertTrue(state["can_skip"])
        self.assertEqual(3, state["scored_takes"])

    def test_three_stars_passes_normally_without_skip(self):
        state = engine.gate_state([take(60), take(80)], models.MAX_TAKES)
        self.assertTrue(state["achieved"])
        self.assertFalse(state["can_retry"])
        self.assertFalse(state["can_skip"])

    def test_scoring_failure_does_not_consume_one_of_three_attempts(self):
        state = engine.gate_state(
            [take(60), take(error=True), take(70), take(74)],
            models.MAX_TAKES,
        )
        self.assertEqual(3, state["scored_takes"])
        self.assertTrue(state["can_skip"])


if __name__ == "__main__":
    unittest.main()
