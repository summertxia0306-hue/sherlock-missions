# -*- coding: utf-8 -*-
import json
import unittest

from listening import models as listening_models
from speaking import models as speaking_models


PAGE_BY_DAY = {31: 32, 32: 33, 33: 34, 34: 35, 35: 36}

CORE_PHRASES = {
    31: ("computer lab", "in front of"),
    32: ("There is a library.", "There are some computers."),
    33: ("What's on this floor?", "clean and tidy"),
    34: ("What's the matter?", "Have a try!"),
    35: ("What's in your school?", "Grandpa grows the fruit."),
}

FORBIDDEN_M3U2 = (
    "supermarket",
    "post office",
    "restaurant",
    "street",
    "next to",
    "between",
)


def _flat(course):
    return json.dumps(course, ensure_ascii=False).lower()


class Courses3135AlignmentTests(unittest.TestCase):
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
                self.assertEqual(4, course["week"])
                self.assertEqual(day - 30, course["day"])
                self.assertEqual("2026-08-06", course["open_date"])
                self.assertEqual(
                    "weekly_test" if day == 35 else "training",
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
                self.assertEqual(4, course["week"])
                self.assertEqual(day - 30, course["day"])
                self.assertEqual("2026-08-06", course["open_date"])
                self.assertEqual(
                    "weekly_review" if day == 35 else "training",
                    course["course_type"],
                )
                self.assertEqual(6, len(repeats))
                self.assertEqual(2, len(qa))
                self.assertTrue(
                    all(q.get("parent_note") == f"教材第{page}页" for q in course["questions"])
                )

    def test_each_pair_contains_same_page_core_phrases(self):
        for day, phrases in CORE_PHRASES.items():
            listening = _flat(listening_models.load_course(f"W01D{day:02d}", check_audio=False))
            speaking = _flat(speaking_models.load_course(f"S01D{day:02d}", check_audio=False))
            for phrase in phrases:
                with self.subTest(day=day, phrase=phrase, module="listening"):
                    self.assertIn(phrase.lower(), listening)
                with self.subTest(day=day, phrase=phrase, module="speaking"):
                    self.assertIn(phrase.lower(), speaking)

    def test_m3u2_vocabulary_is_not_introduced(self):
        for day in PAGE_BY_DAY:
            combined = "\n".join(
                (
                    _flat(listening_models.load_course(f"W01D{day:02d}", check_audio=False)),
                    _flat(speaking_models.load_course(f"S01D{day:02d}", check_audio=False)),
                )
            )
            for phrase in FORBIDDEN_M3U2:
                with self.subTest(day=day, forbidden=phrase):
                    self.assertNotIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
