"""Exercise every new speaking question with isolated local checkpoints only."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from streamlit.testing.v1 import AppTest
from speaking import models, recorder

ROOT = Path(__file__).resolve().parents[1]


class Unit5ReleaseTests(unittest.TestCase):
    def test_ten_course_pages_have_their_audio_and_mic(self):
        with tempfile.TemporaryDirectory() as runtime, mock.patch.dict(os.environ, {
            "SHERLOCK_RUNTIME_DIR": runtime, "RESULTS_TOKEN": "", "RESULTS_REPO": "",
        }):
            for day in range(31, 36):
                for prefix in ("L", "S"):
                    cid = f"{prefix}4A-T1-W01-D{day}"
                    with self.subTest(course=cid):
                        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
                        app.query_params["course_id"] = cid
                        app.run()
                        if prefix == "S":
                            app.session_state[f"S_formal_{cid}"]["idx"] = 0
                            app.run()
                        self.assertEqual(0, len(app.exception))
                        components = app.get("component_instance")
                        self.assertEqual(1 if prefix == "L" else 2, len(components))
                        args = json.loads(components[0].proto.json_args)
                        self.assertIn(cid, args["local_src"])
                        self.assertIn("?v=", args["local_src"])
                        if prefix == "S":
                            self.assertIn(f"rec_{cid}", components[1].proto.id)

    def test_all_new_speaking_questions_and_route_loss_keep_components(self):
        original = recorder._component
        with tempfile.TemporaryDirectory() as runtime, mock.patch.dict(os.environ, {
            "SHERLOCK_RUNTIME_DIR": runtime, "RESULTS_TOKEN": "", "RESULTS_REPO": "",
        }):
            for day in range(31, 36):
                cid = f"S4A-T1-W01-D{day}"
                course = models.load_course(cid)
                app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
                app.query_params["course_id"] = cid
                app.run()
                state = app.session_state[f"S_formal_{cid}"]
                for idx, q in enumerate(course["questions"]):
                    with self.subTest(course=cid, question=q["id"]):
                        state["idx"] = idx
                        state["q"] = {previous["id"]: {"takes": [{"total": 85}],
                                      "done": True, "recordings": [], "recording_records": []}
                                      for previous in course["questions"][:idx]}
                        app.run()
                        app.query_params.clear()
                        app.run()
                        self.assertEqual(0, len(app.exception))
                        self.assertIs(original, recorder._component)
                        self.assertIn(f"第 {idx+1} 题", " ".join(x.value for x in app.markdown))
                        components = app.get("component_instance")
                        self.assertEqual(2, len(components))
                        self.assertEqual(str(q["id"]), json.loads(components[1].proto.json_args)["qid"])
            self.assertFalse((Path(runtime) / "results.json").exists())


if __name__ == "__main__":
    unittest.main()
