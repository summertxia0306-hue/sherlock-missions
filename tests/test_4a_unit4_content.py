import json
import re
import unittest
from pathlib import Path

from listening.models import validate_course as validate_listening
from speaking.models import validate_course as validate_speaking

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "content/drafts/4A-T1-W01-UNIT4"
PREFIX = ROOT / "docs/course-batches/2026-10-13-4A-Unit4-D26-D30"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class Unit4ContentTests(unittest.TestCase):
    def test_pairing_schema_counts_score_and_gradient(self):
        for i, day in enumerate(range(26, 31)):
            pair = f"4A-T1-W01-D{day}"
            listening = load(ROOT / f"content/listening/L{pair}.json")
            speaking = load(ROOT / f"content/speaking/S{pair}.json")
            self.assertEqual([], validate_listening(listening, check_audio=True))
            self.assertEqual([], validate_speaking(speaking, check_audio=True))
            for course in (listening, speaking):
                self.assertEqual(pair, course["pair_id"])
                self.assertEqual(pair, course["study_pack"])
                self.assertEqual("formal", course["publication_status"])
                self.assertEqual(6, course["week"])
                self.assertEqual(i+1, course["day"])
                self.assertEqual(["L1", "L1", "L2", "L2", "L3"][i], course["difficulty"])
                self.assertEqual(f"4A Unit 4 p31-p{[32, 33, 35, 37, 38][i]}", course["scope"])
                self.assertNotIn("open_date", course)
            questions = [q for sec in listening["sections"] for q in sec["questions"]]
            count = [20, 20, 20, 25, 25][i]
            self.assertEqual(list(range(1, count+1)), [q["id"] for q in questions])
            self.assertEqual([count//5]*5, [len(sec["questions"]) for sec in listening["sections"]])
            self.assertEqual(["word_choice", "sentence_judge", "question_response", "dialogue_choice", "passage_judge"], [sec["questions"][0]["type"] for sec in listening["sections"]])
            self.assertEqual(100, listening["scoring"]["total"])
            self.assertEqual(100, count*listening["scoring"]["per_question"])
            self.assertEqual(["repeat"]*6+["qa"]*([10, 10, 12, 12, 12][i]-6), [q["type"] for q in speaking["questions"]])
            self.assertEqual("weekly_test" if day == 30 else "training", listening["course_type"])
            self.assertEqual("weekly_review" if day == 30 else "training", speaking["course_type"])

    def test_audio_plan_manifest_and_child_isolation(self):
        plan = load(DRAFT / "audio-generation-plan.json")
        self.assertEqual((98, 56, 154), tuple(plan[k] for k in ("expected_listening_outputs", "expected_speaking_outputs", "expected_total_outputs")))
        self.assertEqual(154, len(set(item["path"] for item in plan["items"])))
        manifests = {module: load(ROOT / f"static/audio/{module}/manifest.json") for module in ("listening", "speaking")}
        for item in plan["items"]:
            audio = ROOT / item["path"]
            self.assertTrue(audio.is_file() and audio.stat().st_size > 1000, item["path"])
            self.assertIn(item["path"], manifests[item["module"]]["courses"][item["course_id"]])
        forbidden = {"answer", "expected", "transcript", "passage_transcript", "tag", "parent_note", "scoring", "score", "question"}
        for module in ("listening", "speaking"):
            catalog = load(DRAFT / "child" / module / "catalog.json")
            self.assertEqual(5, len(catalog))
            self.assertTrue(all(entry["visible"] for entry in catalog))
            for entry in catalog:
                child = load(DRAFT / "child" / module / f"{entry['course_id']}.json")
                stack = [child]
                while stack:
                    obj = stack.pop()
                    if isinstance(obj, dict):
                        self.assertFalse(forbidden & obj.keys())
                        stack.extend(obj.values())
                    elif isinstance(obj, list):
                        stack.extend(obj)

    def test_source_boundary_micro_and_short_recording_targets(self):
        total = micro = 0
        corpus = []
        for day in range(26, 31):
            listening = load(ROOT / f"content/listening/L4A-T1-W01-D{day}.json")
            speaking = load(ROOT / f"content/speaking/S4A-T1-W01-D{day}.json")
            lqs = [q for sec in listening["sections"] for q in sec["questions"]]
            self.assertEqual(2, sum(q["tag"].startswith("C微调") for q in lqs))
            self.assertEqual(1, sum(q["tag"].startswith("C微调") for q in speaking["questions"]))
            for q in lqs + speaking["questions"]:
                total += 1
                micro += q["tag"].startswith("C微调")
            for q in speaking["questions"]:
                target = q.get("text", q.get("expected"))
                self.assertLessEqual(len(target.split()), 18)
                if q["type"] == "qa":
                    self.assertTrue(q["hint"].startswith("用完整句回答："))
            corpus.extend((json.dumps(listening, ensure_ascii=False), json.dumps(speaking, ensure_ascii=False)))
        self.assertEqual((166, 15), (total, micro))
        text = "\n".join(corpus).lower()
        for marker in ("invitation", "noodles", "parents' letters", "tradition", "camera", "soup noodles"):
            self.assertIn(marker, text)
        for marker in ("unit 5", "p39", "p40", "venice", "neighbourhood", "museum", "supermarket"):
            self.assertNotIn(marker, text)
        for marker in ("twenty-seven october", "twenty-eight october", "football player's letter", "shenshen thank her", "she thanks them", "minmin's father says he can"):
            self.assertNotIn(marker, text)
        self.assertIn("the twenty-seventh of october", text)
        self.assertIn("the twenty-eighth of october", text)
        # Later lesson vocabulary cannot silently enter early scope.
        for day, markers in ((26, ("tradition", "tomatoes", "camera", "october")), (27, ("tradition", "tomatoes", "camera")), (28, ("soup noodles", "tomatoes", "camera"))):
            for module, prefix in (("listening", "L"), ("speaking", "S")):
                raw = (ROOT / f"content/{module}/{prefix}4A-T1-W01-D{day}.json").read_text(encoding="utf-8").lower()
                for marker in markers:
                    self.assertNotIn(marker, raw)

    def test_parent_docs_secrets_and_source_claims(self):
        paths = list(DRAFT.rglob("*.json"))
        paths += [ROOT / f"content/{module}/{prefix}4A-T1-W01-D{day}.json" for module, prefix in (("listening", "L"), ("speaking", "S")) for day in range(26, 31)]
        for suffix in ("教材与课程映射", "家长版答案原文", "校验与02交接"):
            path = Path(str(PREFIX)+suffix+".md")
            paths.append(path)
            text = path.read_text(encoding="utf-8")
            for day in range(26, 31):
                self.assertIn(f"D{day}", text)
        text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
        self.assertFalse(re.search(r"api_secret|api_key|parent_password|private_key|secret_key", text))
        mapping = Path(str(PREFIX)+"教材与课程映射.md").read_text(encoding="utf-8")
        for marker in ("自编", "不同教材示例", "不对应真实学校排期", "收信人不猜测", "不读private"):
            self.assertIn(marker, mapping)


if __name__ == "__main__":
    unittest.main()
