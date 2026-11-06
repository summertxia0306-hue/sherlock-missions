"""Check U6 pairing, audio completeness and the student catalogue transition."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from streamlit.testing.v1 import AppTest
from listening import models as listening
from speaking import models as speaking

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "content/drafts/4A-T1-W01-UNIT6"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class Unit6ContentTests(unittest.TestCase):
    def test_five_paired_lessons_within_their_textbook_pages(self):
        end_pages = [49, 50, 51, 53, 54]
        for index, day in enumerate(range(36, 41)):
            pair = f"4A-T1-W01-D{day}"
            lc = read_json(ROOT / f"content/listening/L{pair}.json")
            sc = read_json(ROOT / f"content/speaking/S{pair}.json")
            with self.subTest(day=day):
                self.assertEqual([], listening.validate_course(lc, check_audio=False))
                self.assertEqual([], speaking.validate_course(sc, check_audio=False))
                for course in (lc, sc):
                    self.assertEqual(pair, course["study_pack"])
                    self.assertEqual(f"4A Unit 6 p47-p{end_pages[index]}", course["scope"])
                    self.assertEqual("formal", course["publication_status"])
                    self.assertNotIn("open_date", course)
                self.assertEqual([4] * 5 if day <= 38 else [5] * 5,
                                 [len(section["questions"]) for section in lc["sections"]])
                self.assertEqual(10 if day <= 37 else 12, len(sc["questions"]))
                self.assertEqual(["repeat"] * 6 + ["qa"] * (len(sc["questions"]) - 6),
                                 [q["type"] for q in sc["questions"]])
                for q in sc["questions"]:
                    self.assertLessEqual(len((q.get("text") or q["expected"]).split()), 20)
                    if q["type"] == "qa":
                        self.assertTrue(q["hint"].startswith("用完整句回答："))
                text = json.dumps([lc, sc]).lower()
                self.assertNotIn("unit 7", text)
                self.assertNotIn("when ", text)
                if day <= 38:
                    self.assertNotIn("saihanba", text)
                if day <= 39:
                    self.assertNotIn("cool wind", text)

    def test_child_copies_omit_answers_and_transcripts(self):
        forbidden = {"answer", "expected", "transcript", "passage_transcript",
                     "test_transcript", "tag", "parent_note", "question", "scoring", "score"}

        def check(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden.intersection(value))
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)

        paths = list((BATCH / "child").glob("*/*.json"))
        self.assertEqual(12, len(paths))
        for path in paths:
            check(read_json(path))

    def test_all_planned_audio_has_a_matching_manifest_entry(self):
        from tools import make_audio_speaking, make_audio_v2

        plan = read_json(BATCH / "audio-generation-plan.json")
        self.assertEqual(154, len(plan["items"]))
        self.assertEqual(154, len({item["path"] for item in plan["items"]}))
        manifests = {module: read_json(ROOT / f"static/audio/{module}/manifest.json")
                     for module in ("listening", "speaking")}
        for item in plan["items"]:
            self.assertGreater((ROOT / item["path"]).stat().st_size, 1000)
            manifest = manifests[item["module"]]["courses"][item["course_id"]]
            expected = (make_audio_v2.content_hash(item) if item["module"] == "listening"
                        else make_audio_speaking.frag_key(item["clips"][0][1]))
            self.assertEqual(expected, manifest[item["path"]])

    def test_student_catalogues_recommend_u6_after_u5_with_formal_completion(self):
        # Generated records belong only to this temporary test runtime.
        for module, legacy, prefix in (("listening", "W", "L"), ("speaking", "S", "S")):
            with self.subTest(module=module), tempfile.TemporaryDirectory() as runtime:
                completed = [legacy + f"01D{day:02}" for day in range(39, 51)]
                completed += [prefix + f"4A-T1-W01-D{day:02}" for day in range(1, 36)]
                rows = [{"course_id": cid, "student_id": "sherlock", "data_kind": "formal"}
                        for cid in completed]
                target = prefix + "4A-T1-W01-D36"
                rows.append({"course_id": target, "student_id": "sherlock", "data_kind": "test"})
                (Path(runtime) / "results.json").write_text(json.dumps(rows), encoding="utf-8")
                with mock.patch.dict(os.environ, {"SHERLOCK_RUNTIME_DIR": runtime,
                        "RESULTS_TOKEN": "", "RESULTS_REPO": ""}):
                    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
                    app.query_params["module"] = module
                    app.run()
                    self.assertFalse(app.exception)
                    self.assertTrue(any(target in info.value for info in app.info))
                    displayed = [caption.value.split(" · ")[0] for caption in app.caption
                                 if caption.value.startswith(prefix + "4A-")]
                    self.assertEqual([prefix + f"4A-T1-W01-D{day}" for day in range(34, 39)], displayed)


if __name__ == "__main__":
    unittest.main()
