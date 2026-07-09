# -*- coding: utf-8 -*-
import unittest

from listening import page as listening_page
from speaking import page as speaking_page


def metas(prefix, count=20):
    return {
        "%s%02d" % (prefix, i): {
            "title": "%s%02d title" % (prefix, i),
            "week": 2 if i > 10 else 1,
            "day": i,
            "open_date": "2026-07-09",
            "status": "open",
        }
        for i in range(1, count + 1)
    }


class RecommendationTests(unittest.TestCase):
    def test_listening_recommends_first_formal_incomplete_course(self):
        done = {"W01D%02d" % i for i in range(1, 10)}
        shown = listening_page._shown_courses(metas("W01D"), "2026-07-09")

        self.assertEqual(
            "W01D10",
            listening_page._recommended_course_id(shown, done),
        )

    def test_speaking_recommends_first_formal_incomplete_course(self):
        done = {"S01D%02d" % i for i in range(1, 10)}
        shown = speaking_page._shown_courses(metas("S01D"), "2026-07-09")

        self.assertEqual(
            "S01D10",
            speaking_page._recommended_course_id(shown, done),
        )

    def test_recommendation_ignores_closed_courses_and_returns_none_when_done(self):
        listening_metas = metas("W01D", count=3)
        listening_metas["W01D03"]["status"] = "closed"
        shown = listening_page._shown_courses(listening_metas, "2026-07-09")

        self.assertIsNone(
            listening_page._recommended_course_id(shown, {"W01D01", "W01D02"}),
        )


if __name__ == "__main__":
    unittest.main()
