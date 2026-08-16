# -*- coding: utf-8 -*-
import unittest

from listening import page as listening_page
from speaking import page as speaking_page
from storage import progress


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

    def test_course_window_starts_with_first_course_at_catalogue_start(self):
        shown = listening_page._shown_courses(metas("W01D", count=12), "2026-07-09")

        window = progress.course_window(shown, done=set(), limit=5)

        self.assertEqual(
            ["W01D01", "W01D02", "W01D03", "W01D04", "W01D05"],
            [cid for cid, _meta in window],
        )

    def test_course_window_centres_first_formal_incomplete_course(self):
        shown = listening_page._shown_courses(metas("W01D", count=12), "2026-07-09")

        window = progress.course_window(
            shown,
            done={"W01D%02d" % i for i in range(1, 6)},
            limit=5,
        )

        self.assertEqual(
            ["W01D04", "W01D05", "W01D06", "W01D07", "W01D08"],
            [cid for cid, _meta in window],
        )

    def test_course_window_fills_from_left_near_catalogue_end(self):
        shown = listening_page._shown_courses(metas("W01D", count=12), "2026-07-09")

        window = progress.course_window(
            shown,
            done={"W01D%02d" % i for i in range(1, 12)},
            limit=5,
        )

        self.assertEqual(
            ["W01D08", "W01D09", "W01D10", "W01D11", "W01D12"],
            [cid for cid, _meta in window],
        )

    def test_course_window_shows_latest_five_when_all_complete(self):
        shown = speaking_page._shown_courses(metas("S01D", count=12), "2026-07-09")

        window = progress.course_window(
            shown,
            done={"S01D%02d" % i for i in range(1, 13)},
            limit=5,
        )

        self.assertEqual(
            ["S01D08", "S01D09", "S01D10", "S01D11", "S01D12"],
            [cid for cid, _meta in window],
        )

    def test_course_window_does_not_count_test_results_as_done(self):
        shown = listening_page._shown_courses(metas("W01D", count=8), "2026-07-09")
        results = [
            {"course_id": "W01D01", "data_kind": "formal"},
            {"course_id": "W01D02", "data_kind": "test"},
        ]

        window = progress.course_window(
            shown,
            done=progress.completed_course_ids(results),
            limit=5,
        )

        self.assertEqual(
            "W01D02",
            listening_page._recommended_course_id(window, {"W01D01"}),
        )


if __name__ == "__main__":
    unittest.main()
