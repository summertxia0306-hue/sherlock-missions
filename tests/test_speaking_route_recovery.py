"""D23 must not fall to the home page after an unrequested route loss."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = "S4A-T1-W01-D23"


class SpeakingRouteRecoveryTests(unittest.TestCase):
    def test_d24_recovers_when_course_id_drops_but_speaking_list_route_remains(self):
        course_id = "S4A-T1-W01-D24"
        with tempfile.TemporaryDirectory() as runtime, \
                mock.patch.dict(os.environ, {"SHERLOCK_RUNTIME_DIR": runtime,
                                             "RESULTS_TOKEN": "", "RESULTS_REPO": ""}):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
            app.query_params["module"] = "speaking"
            app.query_params["course_id"] = course_id
            app.run()
            state = app.session_state[f"S_formal_{course_id}"]
            state["idx"] = 6
            for qid in range(1, 7):
                state["q"][qid] = {"takes": [{"total": 85}], "done": True,
                                   "recordings": [], "recording_records": []}
            state["q"][7] = {"takes": [{"total": 85}], "done": False,
                              "recordings": [], "recording_records": []}
            app.run()
            del app.query_params["course_id"]
            app.run()
            restored = app.query_params.get("course_id")
            self.assertEqual(course_id, restored[0] if isinstance(restored, list)
                             else restored)
            self.assertIn("第 7 题", " ".join(item.value for item in app.markdown))
            back = [button for button in app.button
                    if button.key == f"sback_formal_{course_id}"]
            self.assertEqual(1, len(back))
            back[0].click().run()
            self.assertNotIn("course_id", app.query_params)
            module = app.query_params.get("module")
            self.assertEqual("speaking", module[0] if isinstance(module, list)
                             else module)
            self.assertNotIn("active_speaking_route", app.session_state)

    def test_d23_keeps_current_question_when_query_route_disappears(self):
        with tempfile.TemporaryDirectory() as runtime, \
                mock.patch.dict(os.environ, {"SHERLOCK_RUNTIME_DIR": runtime,
                                             "RESULTS_TOKEN": "", "RESULTS_REPO": ""}):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
            app.query_params["course_id"] = COURSE_ID
            app.run()
            state = app.session_state[f"S_formal_{COURSE_ID}"]
            state["idx"] = 8
            for qid in range(1, 9):
                state["q"][qid] = {"takes": [{"total": 85}], "done": True,
                                   "recordings": [], "recording_records": []}
            state["q"][9] = {"takes": [{"total": 85}], "done": False,
                             "recordings": [], "recording_records": []}
            app.run()
            next_q = [button for button in app.button if button.key == "snext_9_a1"]
            self.assertEqual(1, len(next_q))
            next_q[0].click().run()  # Exact reported Q9 -> Q10 transition.
            self.assertEqual(9, state["idx"])
            app.query_params.clear()  # Simulate the unwanted route loss.
            app.run()
            self.assertEqual(0, len(app.exception))
            restored_route = app.query_params.get("course_id")
            self.assertEqual(COURSE_ID, restored_route[0] if isinstance(
                restored_route, list) else restored_route)
            self.assertEqual(9, state["idx"])
            self.assertIn("第 10 题", " ".join(item.value for item in app.markdown))

            # A replacement Streamlit session (for example after reconnect)
            # also resumes from the private draft, with no formal result written.
            resumed = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
            resumed.query_params["course_id"] = COURSE_ID
            resumed.run()
            restored = resumed.session_state[f"S_formal_{COURSE_ID}"]
            self.assertEqual(9, restored["idx"])
            self.assertIn("第 10 题", " ".join(
                item.value for item in resumed.markdown))

            back = [button for button in resumed.button
                    if button.key == f"sback_formal_{COURSE_ID}"]
            self.assertEqual(1, len(back))
            back[0].click().run()
            self.assertNotIn("active_speaking_route", resumed.session_state)
            self.assertNotIn("course_id", resumed.query_params)


if __name__ == "__main__":
    unittest.main()
