# -*- coding: utf-8 -*-
import json
import unittest

from listening import models as listening_models
from speaking import models as speaking_models


PAGE_BY_DAY = {36: 37, 37: 38, 38: 39, 39: 40, 40: 41}

CORE_PHRASES = {
    36: ("Where is your home?", "There are many shops near my home."),
    37: ("supermarket", "between"),
    38: ("Excuse me.", "It's our pleasure."),
    39: (
        "Nanjing Road is in the centre of Shanghai.",
        "The lights are bright and beautiful.",
    ),
    40: ("Where is the school?", "slide"),
}

FORBIDDEN_M3U3 = (
    "a packet of",
    "a loaf of",
    "a bowl of",
    "a bar of",
    "a bottle of",
)


def _flat(course):
    return json.dumps(course, ensure_ascii=False).lower()


def _listening_questions(course):
    return [question for section in course["sections"] for question in section["questions"]]


class Courses3640AlignmentTests(unittest.TestCase):
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
                self.assertEqual(5, course["week"])
                self.assertEqual(day - 35, course["day"])
                self.assertEqual("2026-08-11", course["open_date"])
                self.assertEqual(
                    "weekly_test" if day == 40 else "training",
                    course["course_type"],
                )
                self.assertEqual(expected_sections, [s["id"] for s in course["sections"]])
                self.assertEqual([4, 4, 4, 4, 4], [len(s["questions"]) for s in course["sections"]])
                self.assertEqual(20, len(_listening_questions(course)))
                self.assertIn(f"教材第{page}页", _flat(course))

    def test_speaking_structure_and_metadata(self):
        for day, page in PAGE_BY_DAY.items():
            course_id = f"S01D{day:02d}"
            with self.subTest(course_id=course_id):
                course = speaking_models.load_course(course_id, check_audio=False)
                repeats = [q for q in course["questions"] if q["type"] == "repeat"]
                qa = [q for q in course["questions"] if q["type"] == "qa"]
                self.assertEqual(5, course["week"])
                self.assertEqual(day - 35, course["day"])
                self.assertEqual("2026-08-11", course["open_date"])
                self.assertEqual(
                    "weekly_review" if day == 40 else "training",
                    course["course_type"],
                )
                self.assertEqual(6, len(repeats))
                self.assertEqual(2, len(qa))
                self.assertIn(f"教材第{page}页", _flat(course))

    def test_each_pair_contains_same_page_core_phrases(self):
        for day, phrases in CORE_PHRASES.items():
            listening = _flat(listening_models.load_course(f"W01D{day:02d}", check_audio=False))
            speaking = _flat(speaking_models.load_course(f"S01D{day:02d}", check_audio=False))
            for phrase in phrases:
                with self.subTest(day=day, phrase=phrase, module="listening"):
                    self.assertIn(phrase.lower(), listening)
                with self.subTest(day=day, phrase=phrase, module="speaking"):
                    self.assertIn(phrase.lower(), speaking)

    def test_review_ratio_is_ten_percent(self):
        speaking_review = 0
        for day in PAGE_BY_DAY:
            listening = listening_models.load_course(f"W01D{day:02d}", check_audio=False)
            listening_review = [
                q for q in _listening_questions(listening)
                if q.get("tag", "").startswith("旧坑复现")
            ]
            self.assertEqual(2, len(listening_review), f"W01D{day:02d}")

            speaking = speaking_models.load_course(f"S01D{day:02d}", check_audio=False)
            speaking_review += sum(
                q.get("tag", "").endswith("旧坑复现") for q in speaking["questions"]
            )
        self.assertEqual(4, speaking_review)

    def test_speaking_targets_stay_short(self):
        for day in PAGE_BY_DAY:
            course = speaking_models.load_course(f"S01D{day:02d}", check_audio=False)
            for question in course["questions"]:
                target = question.get("text", question.get("expected", ""))
                with self.subTest(day=day, question=question["id"], target=target):
                    self.assertLessEqual(len(target.split()), 12)

    def test_m3u3_vocabulary_is_not_introduced(self):
        for day in PAGE_BY_DAY:
            combined = "\n".join(
                (
                    _flat(listening_models.load_course(f"W01D{day:02d}", check_audio=False)),
                    _flat(speaking_models.load_course(f"S01D{day:02d}", check_audio=False)),
                )
            )
            for phrase in FORBIDDEN_M3U3:
                with self.subTest(day=day, forbidden=phrase):
                    self.assertNotIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
