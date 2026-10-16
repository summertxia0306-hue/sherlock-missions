"""Exercise every question transition without recording or saving results."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from streamlit.testing.v1 import AppTest

from speaking import models


ROOT = Path(__file__).resolve().parents[1]


class LongSpeakingCourseFlowTests(unittest.TestCase):
    def test_all_published_courses_advance_through_ninth_and_final_question(self):
        course_ids = [
            cid for cid, meta in models.all_courses().items()
            if meta.get("publication_status") == "formal" and meta["status"] == "open"
        ]
        with tempfile.TemporaryDirectory() as runtime, \
                mock.patch.dict(os.environ, {"SHERLOCK_RUNTIME_DIR": runtime,
                                             "RESULTS_TOKEN": "", "RESULTS_REPO": ""}):
            self._assert_all_courses(course_ids)

    def _assert_all_courses(self, course_ids):
        for course_id in sorted(course_ids):
            course = models.load_course(course_id)
            with self.subTest(course_id=course_id):
                app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
                app.query_params["course_id"] = course_id
                app.run()
                self.assertEqual(0, len(app.exception))
                state = app.session_state[f"S_formal_{course_id}"]
                state["idx"] = 0  # Bypass real microphone trial only in local test.

                for index, question in enumerate(course["questions"]):
                    state["q"][question["id"]] = {
                        "takes": [{"total": 85, "is_rejected": False, "words": []}],
                        "recordings": [],
                        "recording_records": [],
                        "done": False,
                    }
                    app.run()
                    self.assertEqual(0, len(app.exception))
                    self.assertEqual(index, state["idx"])
                    next_buttons = [button for button in app.button
                                    if button.key == f"snext_{question['id']}_a1"]
                    self.assertEqual(1, len(next_buttons))
                    next_buttons[0].click().run()
                    self.assertEqual(0, len(app.exception))
                    self.assertEqual(index + 1, state["idx"])

                self.assertIsNotNone(state["result"])
                self.assertFalse(state["submitted"])
                self.assertEqual(len(course["questions"]),
                                 len(state["result"]["question_results"]))


if __name__ == "__main__":
    unittest.main()
