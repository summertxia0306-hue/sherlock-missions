"""Every published speaking lesson survives the reported Q7 route/reconnect path."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from streamlit.testing.v1 import AppTest

from speaking import checkpoint, models, page
from storage import progress


ROOT = Path(__file__).resolve().parents[1]


class AllSpeakingCoursesRecoveryTests(unittest.TestCase):
    def test_every_formal_course_saves_rated_seventh_answer_before_next(self):
        course_ids = sorted(
            cid for cid, meta in models.all_courses().items()
            if meta.get("publication_status") == "formal" and meta["status"] == "open"
        )
        self.assertTrue(course_ids)
        with tempfile.TemporaryDirectory() as runtime, \
                mock.patch.dict(os.environ, {"SHERLOCK_RUNTIME_DIR": runtime,
                                             "RESULTS_TOKEN": "", "RESULTS_REPO": ""}):
            for course_id in course_ids:
                with self.subTest(course_id=course_id):
                    course = models.load_course(course_id)
                    question = course["questions"][6]
                    qid = question["id"]
                    state = {"idx": 6, "attempt": 1, "t0": 1000.0,
                             "submitted": False, "data_kind": "formal", "q": {
                                 q["id"]: {
                                     "takes": [{"total": 85}], "recordings": [],
                                     "recording_records": [], "done": True,
                                 } for q in course["questions"][:6]
                             }}

                    def scored(_course, _question, qstate, _answer, _state):
                        qstate["takes"].append({"total": 85, "words": []})
                        return True

                    with mock.patch.object(page, "limited_audio", return_value=None), \
                            mock.patch.object(page, "merge_plays"), \
                            mock.patch.object(page.recorder, "record",
                                              return_value={"qid": qid, "take": 1}), \
                            mock.patch.object(page, "_consume_take", side_effect=scored), \
                            mock.patch.object(page.st, "markdown"), \
                            mock.patch.object(page.st, "caption"), \
                            mock.patch.object(page.st, "button", return_value=False), \
                            mock.patch.object(page.st, "rerun"):
                        page._question_page(course, state, question, "sherlock")

                    saved = progress.load_speaking_checkpoint(
                        "sherlock", course_id, "formal")
                    restored = checkpoint.restore(course, saved)
                    self.assertIsNotNone(restored)
                    self.assertEqual(6, restored["idx"])
                    self.assertEqual(1, len(restored["q"][qid]["takes"]))

    def test_every_formal_course_keeps_rated_answer_and_route(self):
        course_ids = sorted(
            cid for cid, meta in models.all_courses().items()
            if meta.get("publication_status") == "formal" and meta["status"] == "open"
        )
        self.assertTrue(course_ids)
        with tempfile.TemporaryDirectory() as runtime, \
                mock.patch.dict(os.environ, {"SHERLOCK_RUNTIME_DIR": runtime,
                                             "RESULTS_TOKEN": "", "RESULTS_REPO": ""}):
            for course_id in course_ids:
                with self.subTest(course_id=course_id):
                    course = models.load_course(course_id)
                    questions = course["questions"]
                    self.assertGreaterEqual(len(questions), 8)
                    state = {"idx": 6, "attempt": 1, "t0": 1000.0,
                             "submitted": False, "data_kind": "formal", "q": {}}
                    for question in questions[:7]:
                        qid = question["id"]
                        state["q"][qid] = {
                            "takes": [{"total": 85, "is_rejected": False,
                                       "words": []}],
                            "recordings": [], "recording_records": [],
                            "done": qid != questions[6]["id"],
                        }
                    self.assertTrue(progress.queue_speaking_checkpoint(
                        "sherlock", course_id, "formal",
                        checkpoint.snapshot(course, state)))

                    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
                    app.query_params["module"] = "speaking"
                    app.query_params["course_id"] = course_id
                    app.run()
                    self.assertEqual(0, len(app.exception))
                    self.assertIn("第 7 题", " ".join(x.value for x in app.markdown))
                    q7 = questions[6]["id"]
                    next_button = [b for b in app.button
                                   if b.key == f"snext_{q7}_a1"]
                    self.assertEqual(1, len(next_button))
                    next_button[0].click().run()
                    self.assertEqual(7, app.session_state[f"S_formal_{course_id}"]["idx"])

                    del app.query_params["course_id"]
                    app.run()
                    restored_route = app.query_params.get("course_id")
                    self.assertEqual(course_id, restored_route[0]
                                     if isinstance(restored_route, list)
                                     else restored_route)
                    self.assertIn("第 8 题", " ".join(x.value for x in app.markdown))

                    resumed = AppTest.from_file(str(ROOT / "app.py"),
                                                default_timeout=20)
                    resumed.query_params["module"] = "speaking"
                    resumed.query_params["course_id"] = course_id
                    resumed.run()
                    self.assertEqual(0, len(resumed.exception))
                    self.assertEqual(7, resumed.session_state[
                        f"S_formal_{course_id}"]["idx"])
                    self.assertIn("第 8 题", " ".join(
                        x.value for x in resumed.markdown))


if __name__ == "__main__":
    unittest.main()
