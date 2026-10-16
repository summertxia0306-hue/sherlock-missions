"""Run the real recorder JavaScript against adversarial async device events."""
import shutil
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from speaking import models, page
from streamlit.testing.v1 import AppTest


class StreamlitRecorderLifecycleTests(unittest.TestCase):
    def test_d25_empty_last_recording_remounts_only_current_microphone(self):
        course_id = "S4A-T1-W01-D25"
        with tempfile.TemporaryDirectory() as runtime, \
                mock.patch.dict(os.environ, {"SHERLOCK_RUNTIME_DIR": runtime,
                                             "RESULTS_TOKEN": "", "RESULTS_REPO": ""}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"),
                                    default_timeout=20)
            app.query_params["course_id"] = course_id
            app.run()
            state = app.session_state[f"S_formal_{course_id}"]
            state["idx"] = 11
            state["q"] = {qid: {"takes": [{"total": 85}], "done": True,
                                "recordings": [], "recording_records": []}
                          for qid in range(1, 12)}
            original_record = page.recorder.record
            injected = False

            def capture(*args, **kwargs):
                nonlocal injected
                if not injected:
                    injected = True
                    return {"qid": "12", "take": 1, "capture_error": "empty_native"}
                return original_record(*args, **kwargs)

            with mock.patch.object(page.recorder, "record", side_effect=capture):
                app.run()
            self.assertEqual(0, len(app.exception))
            self.assertEqual(11, state["idx"])
            self.assertEqual(11, sum(bool(q["done"]) for q in state["q"].values()))
            self.assertEqual([], state["q"][12]["takes"])
            self.assertEqual(1, state["capture_gen"][12])
            components = app.get("component_instance")
            self.assertTrue(any(f"rec_{course_id}_a1_c1" in x.proto.id for x in components))
            self.assertIn("第 12 题", " ".join(x.value for x in app.markdown))
            self.assertFalse((Path(runtime) / "results.json").exists())

    def test_empty_native_recording_rebuilds_last_question_without_scoring_every_course(self):
        for course_id, meta in models.all_courses().items():
            if meta.get("publication_status") != "formal" or meta["status"] != "open":
                continue
            with self.subTest(course_id=course_id):
                course = models.load_course(course_id)
                question = course["questions"][-1]
                qstate = {"takes": [], "recordings": [], "recording_records": [],
                          "done": False}
                state = {"idx": len(course["questions"]) - 1, "data_kind": "formal"}
                with mock.patch.object(page.recorder, "wav_bytes") as decode, \
                        mock.patch.object(page.ise, "evaluate_retry") as evaluate, \
                        mock.patch.object(page.recorder, "upload_recording") as upload:
                    self.assertFalse(page._consume_take(
                        course, question, qstate,
                        {"qid": question["id"], "take": 1, "capture_error": "empty_native"},
                        state))
                decode.assert_not_called()
                evaluate.assert_not_called()
                upload.assert_not_called()
                self.assertEqual([], qstate["takes"])
                self.assertFalse(qstate["done"])
                self.assertEqual(len(course["questions"]) - 1, state["idx"])
                self.assertEqual(1, state["capture_gen"][question["id"]])

    def test_native_recording_lifecycle_and_retry(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for recorder lifecycle validation")
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [node, "--test", "tests/js/streamlit_recorder.test.cjs"],
            cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
