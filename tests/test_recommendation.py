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
    def test_cross_term_window_keeps_legacy_50_before_new_starter_courses(self):
        listening_metas = {
            **metas("W01D", count=50),
            **{
                "L4A-T1-W01-D%02d" % day: {
                    "title": "Starter %d" % day,
                    "week": 1,
                    "day": day,
                    "status": "open",
                }
                for day in range(1, 6)
            },
        }
        speaking_metas = {
            **metas("S01D", count=50),
            **{
                "S4A-T1-W01-D%02d" % day: {
                    "title": "Starter %d" % day,
                    "week": 1,
                    "day": day,
                    "status": "open",
                }
                for day in range(1, 6)
            },
        }
        listening_done = {"W01D%02d" % day for day in range(1, 50)}
        speaking_done = {"S01D%02d" % day for day in range(1, 50)}
        listening_shown = listening_page._shown_courses(listening_metas, "2026-09-07")
        speaking_shown = speaking_page._shown_courses(speaking_metas, "2026-09-07")

        self.assertEqual("W01D50", listening_page._recommended_course_id(listening_shown, listening_done))
        self.assertEqual("S01D50", speaking_page._recommended_course_id(speaking_shown, speaking_done))
        self.assertEqual(
            ["W01D48", "W01D49", "W01D50", "L4A-T1-W01-D01", "L4A-T1-W01-D02"],
            [cid for cid, _meta in progress.course_window(listening_shown, listening_done)],
        )
        self.assertEqual(
            ["S01D48", "S01D49", "S01D50", "S4A-T1-W01-D01", "S4A-T1-W01-D02"],
            [cid for cid, _meta in progress.course_window(speaking_shown, speaking_done)],
        )

    def test_recommended_incomplete_course_gets_recommend_start_label(self):
        self.assertEqual("推荐开始", progress.course_action_label("S01D50", set(), "S01D50"))
        self.assertEqual("开始", progress.course_action_label("S4A-T1-W01-D01", set(), "S01D50"))
        self.assertEqual("再做一遍", progress.course_action_label("S01D49", {"S01D49"}, "S01D50"))

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

    def test_reconciled_progress_recommends_only_course_50(self):
        shown = listening_page._shown_courses(metas("W01D", count=50), "2026-07-09")
        rows = [
            {"course_id": "W01D%02d" % i, "student_id": "sherlock", "data_kind": "formal"}
            for i in range(1, 46)
        ]
        reconciliations = [
            {
                "course_id": "W01D%02d" % i,
                "student_id": "sherlock",
                "data_kind": "formal",
                "status": "completed",
            }
            for i in range(46, 50)
        ]

        done = progress.completed_course_ids(
            rows,
            student_id="sherlock",
            reconciliations=reconciliations,
        )
        window = progress.course_window(shown, done)

        self.assertEqual("W01D50", listening_page._recommended_course_id(shown, done))
        self.assertEqual(
            ["W01D46", "W01D47", "W01D48", "W01D49", "W01D50"],
            [course_id for course_id, _meta in window],
        )


if __name__ == "__main__":
    unittest.main()
