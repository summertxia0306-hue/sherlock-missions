import json
import unittest
from pathlib import Path

from listening.models import validate_course as validate_listening
from speaking.models import validate_course as validate_speaking


ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "content/drafts/4A-T1-W01-UNIT3"
DAYS = range(16, 21)
COUNTS = [20, 20, 20, 25, 25]
SCOPES = ["p23-p24", "p23-p25", "p23-p27", "p23-p29", "p23-p30"]
DIFFICULTIES = ["L1", "L1", "L2", "L2", "L3"]
SPEAKING_COUNTS = [10, 10, 12, 12, 12]
SECTION_IDS = ["word_discrimination", "sentence_meaning", "question_response", "dialogue", "passage"]
SECTION_TYPES = ["word_choice", "sentence_judge", "question_response", "dialogue_choice", "passage_judge"]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def courses(day):
    return (load(ROOT / f"content/listening/L4A-T1-W01-D{day:02d}.json"),
            load(ROOT / f"content/speaking/S4A-T1-W01-D{day:02d}.json"))


class Unit3ContentTests(unittest.TestCase):
    def test_pairing_scope_score_difficulty_and_schema(self):
        for index, day in enumerate(DAYS):
            listening, speaking = courses(day)
            pair = f"4A-T1-W01-D{day:02d}"
            for course in (listening, speaking):
                self.assertEqual("4A-T1-W01", course["weekly_batch_id"])
                self.assertEqual(pair, course["study_pack"])
                self.assertEqual(pair, course["pair_id"])
                self.assertEqual("formal", course["publication_status"])
                self.assertEqual(4, course["week"])
                self.assertEqual(index + 1, course["day"])
                self.assertIn(SCOPES[index], course["scope"])
                self.assertEqual(DIFFICULTIES[index], course["difficulty"])
            self.assertEqual([], validate_listening(listening, check_audio=True))
            self.assertEqual([], validate_speaking(speaking, check_audio=True))
            sections = listening["sections"]
            self.assertEqual(SECTION_IDS, [section["id"] for section in sections])
            self.assertEqual(SECTION_TYPES, [section["questions"][0]["type"] for section in sections])
            self.assertEqual([COUNTS[index] // 5] * 5, [len(section["questions"]) for section in sections])
            questions = [q for section in sections for q in section["questions"]]
            self.assertEqual(list(range(1, COUNTS[index] + 1)), [q["id"] for q in questions])
            self.assertEqual(100, listening["scoring"]["total"])
            self.assertEqual(100, listening["scoring"]["per_question"] * len(questions))
            self.assertEqual(["repeat"] * 6 + ["qa"] * (SPEAKING_COUNTS[index] - 6), [q["type"] for q in speaking["questions"]])
            self.assertEqual("weekly_test" if day == 20 else "training", listening["course_type"])
            self.assertEqual("weekly_review" if day == 20 else "training", speaking["course_type"])

    def test_a_c_ratio_and_textbook_boundary(self):
        total = micro = 0
        all_text = []
        for day in DAYS:
            listening, speaking = courses(day)
            listening_questions = [q for section in listening["sections"] for q in section["questions"]]
            self.assertEqual(2, sum(q["tag"].startswith("C微调") for q in listening_questions))
            self.assertEqual(1, sum(q["tag"].startswith("C微调") for q in speaking["questions"]))
            for question in listening_questions + speaking["questions"]:
                total += 1
                micro += question["tag"].startswith("C微调")
            all_text.extend([json.dumps(listening, ensure_ascii=False), json.dumps(speaking, ensure_ascii=False)])
        self.assertEqual((166, 15), (total, micro))
        corpus = "\n".join(all_text).lower()
        for marker in ("panda", "monkey", "elephant", "sichuan", "guizhou", "yunnan",
                       "the north pole", "thick fur", "seals and fish", "animal card"):
            self.assertIn(marker, corpus)
        for marker in ("our birthday", "birthday invitation", "birthday noodles", "unit 4", "p31"):
            self.assertNotIn(marker, corpus)

    def test_children_plan_and_manifest(self):
        safe_keys = {"answer", "transcript", "tag", "parent_note", "expected", "score", "scoring"}
        plan = load(DRAFT / "audio-generation-plan.json")
        self.assertEqual((98, 56, 154), (plan["expected_listening_outputs"], plan["expected_speaking_outputs"], plan["expected_total_outputs"]))
        self.assertEqual(154, len(plan["items"]))
        manifests = {module: load(ROOT / f"static/audio/{module}/manifest.json") for module in ("listening", "speaking")}
        for item in plan["items"]:
            self.assertTrue((ROOT / item["path"]).is_file(), item["path"])
            self.assertIn(item["path"], manifests[item["module"]]["courses"][item["course_id"]])
        packs = load(DRAFT / "study-packs.json")
        self.assertEqual([f"4A-T1-W01-D{d:02d}" for d in DAYS], [pack["pair_id"] for pack in packs["study_packs"]])
        for module, prefix in (("listening", "L"), ("speaking", "S")):
            catalog = load(DRAFT / "child" / module / "catalog.json")
            self.assertEqual([f"{prefix}4A-T1-W01-D{d:02d}" for d in DAYS], [entry["course_id"] for entry in catalog])
            self.assertTrue(all(entry["visible"] for entry in catalog))
            for day in DAYS:
                child = load(DRAFT / "child" / module / f"{prefix}4A-T1-W01-D{day:02d}.json")
                keys, stack = set(), [child]
                while stack:
                    obj = stack.pop()
                    if isinstance(obj, dict):
                        keys.update(obj)
                        stack.extend(obj.values())
                    elif isinstance(obj, list):
                        stack.extend(obj)
                self.assertFalse(keys & safe_keys)

    def test_parent_documents_and_no_secrets(self):
        paths = list(DRAFT.rglob("*.json"))
        paths.extend(ROOT / f"content/listening/L4A-T1-W01-D{d:02d}.json" for d in DAYS)
        paths.extend(ROOT / f"content/speaking/S4A-T1-W01-D{d:02d}.json" for d in DAYS)
        text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
        for marker in ("api_secret", "api_key", "parent_password", "private_key", "secret_key"):
            self.assertNotIn(marker, text)
        for name in ("教材与课程映射", "家长版答案原文"):
            document = next((ROOT / "docs/course-batches").glob(f"2026-09-17-4A-Unit3-D16-D20{name}.md"))
            content = document.read_text(encoding="utf-8")
            for day in DAYS:
                self.assertIn(f"D{day:02d}", content)


if __name__ == "__main__":
    unittest.main()
