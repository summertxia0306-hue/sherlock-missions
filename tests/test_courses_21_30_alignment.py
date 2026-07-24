# -*- coding: utf-8 -*-
import json
import unittest

from listening import models as listening_models
from speaking import models as speaking_models


PAGE_BY_DAY = {
    21: 22,
    22: 23,
    23: 24,
    24: 25,
    25: 26,
    26: 27,
    27: 28,
    28: 29,
    29: 30,
    30: 31,
}

CORE_PHRASES = {
    21: ("Call the fire station.", "Put out the fire!"),
    22: ("What does your father do?", "She is a nurse."),
    23: ("Is she a nurse?", "No, she isn't."),
    24: ("Fire is dangerous.", "You're welcome."),
    25: ("The princess has a dream.", "She buys a pretty dress."),
    26: ("His name's Tom.", "He can skate."),
    27: ("This is a coat.", "These are jeans."),
    28: ("This is a lion.", "The mouse can bite."),
    29: ("They're wearing short shorts today.", "The girls are wearing long jackets."),
    30: ("Bryan likes ice cream.", "He likes bread too."),
}

ACTIVATION_DAY = {
    "doctor": 22,
    "nurse": 22,
    "teacher": 22,
    "cook": 22,
    "bus driver": 22,
    "dangerous": 24,
    "afraid": 24,
    "you're welcome": 24,
    "princess": 25,
    "dream": 25,
    "pretty": 25,
    "price": 25,
    "t-shirt": 26,
    "shorts": 26,
    "skate": 26,
    "bicycle": 26,
    "kite": 26,
    "coat": 27,
    "blouse": 27,
    "sweater": 27,
    "jeans": 27,
    "lion": 28,
    "mouse": 28,
    "sharp": 28,
    "net": 28,
    "bite": 28,
    "teeth": 28,
    "wearing": 29,
    "jacket": 29,
    "socks": 29,
    "bread": 30,
    "ice cream": 30,
    "bryan": 30,
}


def _flat(course):
    return json.dumps(course, ensure_ascii=False).lower()


class Courses2130AlignmentTests(unittest.TestCase):
    def test_listening_structure_and_metadata(self):
        expected_sections = [
            "word_discrimination",
            "sentence_meaning",
            "question_response",
            "dialogue",
            "passage",
        ]
        for day, page in PAGE_BY_DAY.items():
            course_id = f"W01D{day:02d}"
            with self.subTest(course_id=course_id):
                course = listening_models.load_course(course_id, check_audio=False)
                self.assertEqual(3, course["week"])
                self.assertEqual(day - 20, course["day"])
                self.assertEqual("2026-07-24", course["open_date"])
                self.assertEqual(
                    "weekly_test" if day in (25, 30) else "training",
                    course["course_type"],
                )
                self.assertEqual(expected_sections, [s["id"] for s in course["sections"]])
                self.assertEqual([4, 4, 4, 4, 4], [len(s["questions"]) for s in course["sections"]])
                self.assertEqual(20, sum(len(s["questions"]) for s in course["sections"]))
                self.assertIn(f"教材第{page}页", _flat(course))

    def test_speaking_structure_and_metadata(self):
        for day, page in PAGE_BY_DAY.items():
            course_id = f"S01D{day:02d}"
            with self.subTest(course_id=course_id):
                course = speaking_models.load_course(course_id, check_audio=False)
                repeats = [q for q in course["questions"] if q["type"] == "repeat"]
                qa = [q for q in course["questions"] if q["type"] == "qa"]
                self.assertEqual(3, course["week"])
                self.assertEqual(day - 20, course["day"])
                self.assertEqual("2026-07-24", course["open_date"])
                self.assertEqual(
                    "weekly_review" if day in (25, 30) else "training",
                    course["course_type"],
                )
                self.assertEqual(6, len(repeats))
                self.assertEqual(2, len(qa))
                self.assertTrue(
                    all(q.get("parent_note") == f"教材第{page}页" for q in course["questions"])
                )

    def test_each_pair_contains_the_same_page_core_phrases(self):
        for day, phrases in CORE_PHRASES.items():
            listening = _flat(listening_models.load_course(f"W01D{day:02d}", check_audio=False))
            speaking = _flat(speaking_models.load_course(f"S01D{day:02d}", check_audio=False))
            for phrase in phrases:
                with self.subTest(day=day, phrase=phrase, module="listening"):
                    self.assertIn(phrase.lower(), listening)
                with self.subTest(day=day, phrase=phrase, module="speaking"):
                    self.assertIn(phrase.lower(), speaking)

    def test_later_page_vocabulary_does_not_leak_forward(self):
        for day in PAGE_BY_DAY:
            combined = "\n".join(
                (
                    _flat(listening_models.load_course(f"W01D{day:02d}", check_audio=False)),
                    _flat(speaking_models.load_course(f"S01D{day:02d}", check_audio=False)),
                )
            )
            for phrase, activation_day in ACTIVATION_DAY.items():
                if day < activation_day:
                    with self.subTest(day=day, forbidden=phrase):
                        self.assertNotIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
