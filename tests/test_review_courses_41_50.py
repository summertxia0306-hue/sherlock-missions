# -*- coding: utf-8 -*-
import hashlib
import json
import os
import unittest

from listening import models as listening_models
from speaking import models as speaking_models


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LISTENING_IDS = ["W01D%02d" % i for i in range(41, 51)]
SPEAKING_IDS = ["S01D%02d" % i for i in range(41, 51)]
ACTIVE_LISTENING_IDS = sorted(["W01D%02d" % i for i in range(39, 51)] +
                              ["L4A-T1-W01-D%02d" % i for i in range(1, 7)])
ACTIVE_SPEAKING_IDS = sorted(["S01D%02d" % i for i in range(39, 51)] +
                             ["S4A-T1-W01-D%02d" % i for i in range(1, 7)])

EXPECTED_SCOPES = {
    41: "M1U1",
    42: "M1U2",
    43: "M1U3",
    44: "M2U1",
    45: "M2U2",
    46: "M2U3",
    47: "M3U1",
    48: "M3U2",
    49: "M1-M2",
    50: "M1-M3U2",
}

LOCKED_JSON_HASHES = {
    "content/listening/W01D39.json": "FA7C641B05B567818795D5D56D69272E6FA51F48CC1C0FD4CF4D0D05E54A1815",
    "content/listening/W01D40.json": "3EC564DB89DA494D3D76625B405526753200EE4C1ABD4FCBCEA5605461623EB5",
    "content/speaking/S01D39.json": "D4DDAF8045ADEB17A4663FDA39824F1A956F247C3B2DB7EBC34E66DEFB0971E6",
    "content/speaking/S01D40.json": "2846810B207AA78F97458EA0983425E4CE2F4C1CAE61BB558C8123B97F305C02",
}

FORBIDDEN_M3U3 = (
    "a packet of",
    "a loaf of",
    "a bowl of",
    "a bar of",
    "a bottle of",
    "shopping list",
    "how much",
)


def _course_text(course):
    return json.dumps(course, ensure_ascii=False).lower()


class ReviewCourseTests(unittest.TestCase):
    def test_only_approved_legacy_and_term_test_json_remain(self):
        listening_ids = [
            os.path.splitext(os.path.basename(path))[0]
            for path in listening_models.list_course_files()
        ]
        speaking_ids = [
            os.path.splitext(os.path.basename(path))[0]
            for path in speaking_models.list_course_files()
        ]
        self.assertEqual(ACTIVE_LISTENING_IDS, listening_ids)
        self.assertEqual(ACTIVE_SPEAKING_IDS, speaking_ids)

    def test_locked_39_40_course_json_is_unchanged(self):
        for rel_path, expected in LOCKED_JSON_HASHES.items():
            with self.subTest(path=rel_path):
                with open(os.path.join(ROOT, *rel_path.split("/")), "rb") as fh:
                    actual = hashlib.sha256(fh.read()).hexdigest().upper()
                self.assertEqual(expected, actual)

    def test_new_listening_courses_follow_fixed_structure(self):
        for day, course_id in enumerate(LISTENING_IDS, 1):
            with self.subTest(course_id=course_id):
                course = listening_models.load_course(course_id, check_audio=False)
                self.assertEqual(6, course["week"])
                self.assertEqual(day, course["day"])
                self.assertEqual(20, len(course["_questions"]))
                self.assertEqual(
                    [
                        "word_discrimination",
                        "sentence_meaning",
                        "question_response",
                        "dialogue",
                        "passage",
                    ],
                    [section["id"] for section in course["sections"]],
                )
                self.assertTrue(all(len(section["questions"]) == 4 for section in course["sections"]))
                expected_type = "weekly_test" if day >= 9 else "training"
                self.assertEqual(expected_type, course["course_type"])

    def test_new_speaking_courses_follow_fixed_structure(self):
        for day, course_id in enumerate(SPEAKING_IDS, 1):
            with self.subTest(course_id=course_id):
                course = speaking_models.load_course(course_id, check_audio=False)
                self.assertEqual(6, course["week"])
                self.assertEqual(day, course["day"])
                self.assertEqual(8, len(course["questions"]))
                self.assertEqual(6, sum(q["type"] == "repeat" for q in course["questions"]))
                self.assertEqual(2, sum(q["type"] == "qa" for q in course["questions"]))
                expected_type = "weekly_review" if day >= 9 else "training"
                self.assertEqual(expected_type, course["course_type"])

    def test_paired_courses_share_the_same_scope(self):
        for number in range(41, 51):
            with self.subTest(number=number):
                listening = listening_models.load_course("W01D%02d" % number, check_audio=False)
                speaking = speaking_models.load_course("S01D%02d" % number, check_audio=False)
                expected = EXPECTED_SCOPES[number]
                self.assertIn(expected, listening["scope"])
                self.assertIn(expected, speaking["scope"])

    def test_new_courses_do_not_introduce_m3u3(self):
        courses = [
            listening_models.load_course(course_id, check_audio=False)
            for course_id in LISTENING_IDS
        ] + [
            speaking_models.load_course(course_id, check_audio=False)
            for course_id in SPEAKING_IDS
        ]
        combined = "\n".join(_course_text(course) for course in courses)
        for phrase in FORBIDDEN_M3U3:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
