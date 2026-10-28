"""Unit 4 release checks; never record, score, or submit learning data."""
import json
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest
from listening import audio
from speaking import recorder

ROOT = Path(__file__).resolve().parents[1]
REVISION = "a99d4ad37b2e6b6e02f015e638dff3fdd490190a"


class Unit4ReleaseTests(unittest.TestCase):
    def test_new_audio_uses_its_own_immutable_revision(self):
        for day in range(26, 31):
            for module, prefix in (("listening", "L"), ("speaking", "S")):
                path = f"static/audio/{module}/{prefix}4A-T1-W01-D{day}/q01.mp3"
                with self.subTest(path=path):
                    sources = audio.audio_sources(path)
                    self.assertEqual(3, len(sources))
                    self.assertTrue(sources[0].startswith("https://raw.githubusercontent.com/"))
                    self.assertTrue(all(REVISION in source for source in sources))
                    self.assertEqual(sources[0], audio.audio_url(path))
        # Exact day boundaries prevent routing old or future courses to U4.
        self.assertIn("b83a08dd", audio.audio_url("static/audio/speaking/S4A-T1-W01-D25/q01.mp3"))
        self.assertIn("b5dbb07a", audio.audio_url("static/audio/speaking/S4A-T1-W01-D36/q01.mp3"))

    def test_all_listening_pages_render_trial_audio(self):
        for day in range(26, 31):
            with self.subTest(day=day):
                app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
                app.query_params["course_id"] = f"L4A-T1-W01-D{day}"
                app.run()
                self.assertEqual(0, len(app.exception))
                components = app.get("component_instance")
                self.assertEqual(1, len(components))
                self.assertIn(REVISION, components[0].proto.json_args)
                self.assertIn("hello.mp3", components[0].proto.json_args)

    def test_all_speaking_first_questions_keep_audio_and_microphone_stable(self):
        component = recorder._component
        for day in range(26, 31):
            course_id = f"S4A-T1-W01-D{day}"
            with self.subTest(course_id=course_id):
                app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
                app.query_params["course_id"] = course_id
                app.run()
                self.assertEqual(0, len(app.exception))
                app.session_state[f"S_formal_{course_id}"]["idx"] = 0
                for _ in range(5):
                    app.run()
                    self.assertEqual(0, len(app.exception))
                    self.assertIs(component, recorder._component)
                    components = app.get("component_instance")
                    self.assertEqual(2, len(components))
                    self.assertIn(REVISION, components[0].proto.json_args)
                    self.assertIn("q01.mp3", components[0].proto.json_args)
                    self.assertEqual("1", json.loads(components[1].proto.json_args)["qid"])
                    self.assertIn(f"rec_{course_id}", components[1].proto.id)


if __name__ == "__main__":
    unittest.main()
