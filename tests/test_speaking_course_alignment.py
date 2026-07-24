# -*- coding: utf-8 -*-
import unittest

from speaking import models


EXPECTED = {
    "S01D17": {
        "title": "口语练习 · M2U1 family questions",
        "repeat": [
            "Do you have a cousin?",
            "Yes, I do.",
            "No, I don't.",
            "I have one cousin.",
            "Do you have uncles and aunts?",
            "I have one uncle and two aunts.",
        ],
        "qa": [
            ("Do you have uncles and aunts?", "Yes, I do."),
            ("Do you have brothers and sisters?", "No, I don't."),
        ],
    },
    "S01D18": {
        "title": "口语练习 · Photos of Jill's family",
        "repeat": [
            "Come and look at my new photos.",
            "He's my cousin.",
            "His name is Wang Rong.",
            "He's eleven years old.",
            "He can swim very fast.",
            "He's my uncle. He can dive.",
        ],
        "qa": [
            ("Who is Wang Rong?", "He's my cousin."),
            ("What can Wang Rong do?", "He can swim very fast."),
        ],
    },
    "S01D19": {
        "title": "口语练习 · Mid-autumn Day",
        "repeat": [
            "Hello, Grandpa and Grandma!",
            "Come in, please.",
            "Let's have some mooncakes.",
            "Watch the beautiful moon in the garden.",
            "I have a riddle for you.",
            "It's big and bright in the sky.",
        ],
        "qa": [
            ("What is it?", "It's the moon."),
            ("Where is the moon?", "It's in the sky."),
        ],
    },
    "S01D20": {
        "title": "口语周复习 · M2U1 textbook review",
        "repeat": [
            "Who's that girl?",
            "That's my cousin, Bess.",
            "She's in the short black dress.",
            "That's my aunt in the long red skirt.",
            "That's my uncle in the bright green shirt.",
            "Wash the fish.",
        ],
        "qa": [
            ("Who is Bess?", "She's my cousin."),
            ("Who's that man?", "He's my uncle."),
        ],
    },
}


class SpeakingCourseAlignmentTests(unittest.TestCase):
    def test_s01d17_to_s01d20_follow_textbook_progression(self):
        for course_id, expected in EXPECTED.items():
            with self.subTest(course_id=course_id):
                course = models.load_course(course_id, check_audio=False)
                repeats = [q["text"] for q in course["questions"] if q["type"] == "repeat"]
                qa = [
                    (q["question"], q["expected"])
                    for q in course["questions"]
                    if q["type"] == "qa"
                ]
                self.assertEqual(expected["title"], course["title"])
                self.assertEqual(expected["repeat"], repeats)
                self.assertEqual(expected["qa"], qa)
                self.assertEqual(6, len(repeats))
                self.assertEqual(2, len(qa))

    def test_removed_synthetic_phrases_do_not_return(self):
        combined = "\n".join(
            q.get("text", "") + " " + q.get("expected", "")
            for course_id in EXPECTED
            for q in models.load_course(course_id, check_audio=False)["questions"]
        )
        for phrase in (
            "I have a happy family.",
            "My aunt can cook.",
            "She likes reading.",
            "Her name is May.",
        ):
            self.assertNotIn(phrase, combined)

    def test_completed_s01d16_is_unchanged(self):
        course = models.load_course("S01D16", check_audio=False)
        repeats = [q["text"] for q in course["questions"] if q["type"] == "repeat"]
        self.assertEqual(
            [
                "This is my uncle.",
                "This is my aunt.",
                "This is my cousin.",
                "He is a police officer.",
                "I have a cousin.",
                "I have an uncle.",
            ],
            repeats,
        )


if __name__ == "__main__":
    unittest.main()
