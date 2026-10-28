"""Unit 5 batch: paired scope, answer integrity, safe child copies and assets."""
import json
import unittest
from pathlib import Path

from listening.models import validate_course as validate_listening
from speaking.models import validate_course as validate_speaking

ROOT = Path(__file__).resolve().parents[1]


class Unit5ContentTests(unittest.TestCase):
    def test_five_pairs_and_progressive_structure(self):
        for offset, day in enumerate(range(31, 36)):
            pair = f"4A-T1-W01-D{day}"
            lcourse = json.loads((ROOT / f"content/listening/L{pair}.json").read_text(encoding="utf-8"))
            scourse = json.loads((ROOT / f"content/speaking/S{pair}.json").read_text(encoding="utf-8"))
            with self.subTest(day=day):
                self.assertEqual([], validate_listening(lcourse, check_audio=False))
                self.assertEqual([], validate_speaking(scourse, check_audio=False))
                self.assertEqual(lcourse["scope"], scourse["scope"])
                for course in (lcourse, scourse):
                    self.assertEqual(pair, course["pair_id"])
                    self.assertEqual("formal", course["publication_status"])
                    self.assertNotIn("open_date", course)
                    self.assertIn("Unit 5", course["scope"])
                questions = [q for s in lcourse["sections"] for q in s["questions"]]
                self.assertEqual([20, 20, 20, 25, 25][offset], len(questions))
                self.assertEqual(100, len(questions) * lcourse["scoring"]["per_question"])
                self.assertEqual([10, 10, 12, 12, 12][offset], len(scourse["questions"]))
                self.assertEqual(["repeat"] * 6 + ["qa"] * (len(scourse["questions"]) - 6), [q["type"] for q in scourse["questions"]])
                for q in scourse["questions"]:
                    self.assertLessEqual(len((q.get("text") or q["expected"]).split()), 20)
                    if q["type"] == "qa":
                        self.assertTrue(q["hint"].startswith("用完整句回答："))
                text = json.dumps([lcourse, scourse], ensure_ascii=False)
                self.assertNotIn("Unit 6", text)
                self.assertNotIn("Shenshen likes the park best", text)
                for sec in lcourse["sections"][:4]:
                    if sec["questions"][0]["type"] in ("word_choice", "question_response", "dialogue_choice"):
                        answers = [q["answer"] for q in sec["questions"]]
                        self.assertGreater(len(set(answers)), 1)

    def test_audio_plan_and_child_safety(self):
        batch = ROOT / "content/drafts/4A-T1-W01-UNIT5"
        plan = json.loads((batch / "audio-generation-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(154, len(plan["items"]))
        self.assertEqual(154, len({item["path"] for item in plan["items"]}))
        forbidden = {"answer", "expected", "transcript", "passage_transcript", "tag", "parent_note", "question", "scoring", "score"}
        def check(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden.intersection(value))
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)
        for path in (batch / "child").glob("*/*.json"):
            check(json.loads(path.read_text(encoding="utf-8")))

    def test_early_lessons_do_not_import_later_textbook_facts(self):
        for day, markers in ((31, ("gondola", "venice", "battery", "four hundred")),
                             (32, ("gondola", "venice", "italy", "playground")),
                             (33, ("gondola", "venice", "italy", "playground"))):
            for module, prefix in (("listening", "L"), ("speaking", "S")):
                text = (ROOT / f"content/{module}/{prefix}4A-T1-W01-D{day}.json").read_text(encoding="utf-8").lower()
                for marker in markers:
                    self.assertNotIn(marker, text)

    def test_all_audio_assets_match_planned_content(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import make_audio_v2 as la
        import make_audio_speaking as sa
        lm = la.load_manifest()
        sm = sa.load_manifest()
        for day in range(31, 36):
            for module, prefix, tool, manifest in (("listening", "L", la, lm), ("speaking", "S", sa, sm)):
                course = json.loads((ROOT / f"content/{module}/{prefix}4A-T1-W01-D{day}.json").read_text(encoding="utf-8"))
                check = validate_listening if module == "listening" else validate_speaking
                self.assertEqual([], check(course, check_audio=True))
                if module == "listening":
                    items = [(item["out_rel"], la.content_hash(item)) for item in la.collect_items(course)]
                else:
                    items = [(q["audio"], sa.frag_key(sa.speak_text(q))) for q in course["questions"]]
                for path, expected in items:
                    self.assertGreater((ROOT / path).stat().st_size, 1000)
                    self.assertEqual(expected, manifest["courses"][course["course_id"]][path])


if __name__ == "__main__":
    unittest.main()
