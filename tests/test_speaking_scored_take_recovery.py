"""A rated answer must survive a reconnect before the child taps Next."""
import tempfile
import threading
import time
import unittest
import os
from pathlib import Path
from unittest import mock

from streamlit.testing.v1 import AppTest

from speaking import checkpoint, models, page
from storage import progress


class ScoredTakeRecoveryTests(unittest.TestCase):
    def test_d24_reopen_shows_rated_question_seven_and_next_button(self):
        course = models.load_course("S4A-T1-W01-D24")
        state = {"idx": 6, "attempt": 1, "t0": 1000.0,
                 "submitted": False, "data_kind": "formal", "q": {
                     qid: {"takes": [{"total": 85, "words": []}],
                           "recordings": [], "recording_records": [],
                           "done": qid < 7}
                     for qid in range(1, 8)
                 }}
        with tempfile.TemporaryDirectory() as runtime, \
                mock.patch.dict(os.environ, {"SHERLOCK_RUNTIME_DIR": runtime,
                                             "RESULTS_TOKEN": "", "RESULTS_REPO": ""}):
            progress.save_speaking_checkpoint(
                "sherlock", course["course_id"], "formal",
                checkpoint.snapshot(course, state))
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"),
                                    default_timeout=20)
            app.query_params["course_id"] = course["course_id"]
            app.run()
            self.assertEqual(0, len(app.exception))
            self.assertEqual(6, app.session_state[f"S_formal_{course['course_id']}"]["idx"])
            self.assertIn("第 7 题", " ".join(item.value for item in app.markdown))
            self.assertEqual(1, len([button for button in app.button
                                     if button.key == "snext_7_a1"]))

    def test_checkpoint_does_not_wait_for_private_github_on_question_change(self):
        course = models.load_course("S4A-T1-W01-D24")
        state = {"idx": 7, "attempt": 1, "t0": 1000.0,
                 "submitted": False, "data_kind": "formal", "q": {
                     qid: {"takes": [{"total": 85}], "recordings": [],
                           "recording_records": [], "done": True}
                     for qid in range(1, 8)
                 }}
        remote_started = threading.Event()
        release_remote = threading.Event()

        def slow_remote(*_args):
            remote_started.set()
            release_remote.wait(2)
            return True

        def slow_read(*_args, **_kwargs):
            time.sleep(0.35)
            return {}, None

        with tempfile.TemporaryDirectory() as runtime, \
                mock.patch.object(progress, "_runtime_dir", return_value=runtime), \
                mock.patch.object(progress, "_gh_conf", return_value=("token", "private/repo")), \
                mock.patch.object(progress, "_remote_read", side_effect=slow_read), \
                mock.patch.object(progress, "_remote_write", return_value=True), \
                mock.patch.object(progress, "_sync_remote_speaking_checkpoint",
                                  side_effect=slow_remote, create=True):
            started = time.monotonic()
            page._save_checkpoint(course, state, "sherlock")
            elapsed = time.monotonic() - started
            try:
                self.assertLess(elapsed, 0.2)
                self.assertTrue(remote_started.wait(1))
                local = progress.load_speaking_checkpoint(
                    "sherlock", course["course_id"], "formal")
                self.assertEqual(7, local["idx"])
            finally:
                release_remote.set()

    def test_d24_question_seven_score_is_saved_before_next_button(self):
        course = models.load_course("S4A-T1-W01-D24")
        state = {
            "idx": 6, "attempt": 1, "t0": 1000.0, "submitted": False,
            "data_kind": "formal", "q": {
                qid: {"takes": [{"total": 85}], "recordings": [],
                      "recording_records": [], "done": True}
                for qid in range(1, 7)
            },
        }
        answer = {"qid": 7, "take": 1}

        def score_without_advancing(_course, _q, question_state, _answer, _state):
            question_state["takes"].append({"total": 85, "words": []})
            return True

        with tempfile.TemporaryDirectory() as runtime, \
                mock.patch.object(progress, "_runtime_dir", return_value=runtime), \
                mock.patch.object(progress, "_gh_conf", return_value=(None, None)), \
                mock.patch.object(page, "limited_audio", return_value=None), \
                mock.patch.object(page, "merge_plays"), \
                mock.patch.object(page.recorder, "record", return_value=answer), \
                mock.patch.object(page, "_consume_take", side_effect=score_without_advancing), \
                mock.patch.object(page.st, "markdown"), \
                mock.patch.object(page.st, "caption"), \
                mock.patch.object(page.st, "button", return_value=False), \
                mock.patch.object(page.st, "rerun"):
            page._question_page(course, state, course["questions"][6], "sherlock")
            saved = progress.load_speaking_checkpoint(
                "sherlock", course["course_id"], "formal")

        restored = checkpoint.restore(course, saved)
        self.assertIsNotNone(restored)
        self.assertEqual(6, restored["idx"])
        self.assertEqual(1, len(restored["q"][7]["takes"]))
        self.assertFalse(restored["q"][7]["done"])


if __name__ == "__main__":
    unittest.main()
